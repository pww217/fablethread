---
status: implemented
reviewed: 2026-06-25
---

# Beat Generation Split — Design Doc

> **Source:** `roadmap/features/ruling-engine-gm-beat-architecture.md`

## Problem Statement

Storytell (Step 2c) is overloaded. It handles backward-looking tasks (thread lifecycle, arc resolution, actions, outcome_summary) AND forward-looking tasks (GM beat generation). This creates two problems:

1. **Cognitive disconnect:** Beat generation decides what happens next *before* knowing player intent for the upcoming turn. The narrator must reconcile a beat with player input even when they don't fit together.

2. **Latency and error surface:** Storytell is the heaviest LLM call in the pipeline. Adding beat generation to it increases both turn latency and error rate.

Ruling engine currently does its job well (intent classification, impossibility check, difficulty adjustment, dice resolution). Adding beat generation to ruling would overload it with forward-looking creative work.

## Target State

Split Storytell into three focused steps with clear responsibilities:

| Step | Direction | Timing | Temperature | Role |
|------|-----------|--------|-------------|------|
| **Record** | Backward-looking | Sync (turn) | 0.4 (= `extract_temperature`) | Post-narration scribe. Records what changed. |
| **World** | Forward-looking | Async (~5s) | 0.55 | Post-persist world simulation. Generates beat candidates. |
| **Ruling** | Forward-looking (intent-aware) | Sync (turn) | 0.2 (unchanged) | Pre-narration selector. Picks best beat for player intent. |

### Pipeline Overview

```
CURRENT PIPELINE (before split):

  USER INPUT
     │
     ▼
  Step 0: Ruling ─────┐
     │                │ intent + outcome
     ▼                │
  Step 1: Narrate     │
     │                │
     ▼                │
  Step 2a: Scene ─────┤
     │                │
     ▼                │
  Step 2b: State ─────┤
     │                │
     ▼                │
  Step 2c: Storytell  │ ← handles threads + beats (overloaded)
     │                │
     ▼                │
  Validate → Apply → Persist
     │
     ▼
  Turn complete → UI shows narration + beat for NEXT turn


NEW PIPELINE (after split):

  USER INPUT
     │
     ▼
  Step 0: Ruling ───────┐
     │                   │ intent + outcome
     │                   │ beat_candidates ← from state.meta (prev turn's World)
     │                   │ selected_beat ← ruling's new output
     │                   │ pending_gm_beat ← set here (replaces extract-phase)
     │                   │ recent_beats ← appended here (replaces turn_state.py)
     ▼                   │
  Step 1: Narrate        │ ← consumes pending_gm_beat from prev turn
     │                   │
     ▼                   │
  Step 2a: Scene ────────┤
     │                   │
     ▼                   │
  Step 2b: State ────────┤
     │                   │
     ▼                   │
  Step 2c: Record ───────┤ ← threads only (no beats)
     │                   │
     ▼                   │
  Validate → Apply → Persist
     │                   │
     ▼                   │
  Turn complete ─────────┤ ← UI shows narration + actions
     │                   │
     ▼                   │
  Step 2d: World (async) │ ← runs while player reads (~5s)
     │                   │
     ▼                   │
  beat_candidates ← state.meta ← available for NEXT turn's ruling
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TURN N FLOW                                  │
└─────────────────────────────────────────────────────────────────────┘

  Turn N-1 World output                    Turn N sync phases
  ┌──────────────────┐
  │ beat_candidates  │──────────────────────────────────────────────┐
  │ in state.meta    │                                              │
  └──────────────────┘                                              │
                                                                    ▼
  ┌─────────────┐    beat_candidates    ┌─────────────┐
  │   Ruling    │←─────────────────────│   Ruling    │
  │   Phase     │  (from state.meta)   │   Phase     │
  │             │                      │             │
  │ selects     │                      │ outputs     │
  │ selected_beat│                     │ JSON with   │
  │             │                      │ selected_beat│
  │ sets        │                      │             │
  │ pending_gm_ │                      │ sets        │
  │ beat        │                      │ pending_gm_beat
  │ + recent_beats│                    │ in state.meta
  └──────┬──────┘                      └──────┬──────┘
         │                                     │
         │                                     ▼
         │                            ┌─────────────┐
         │                            │   Narrate   │
         │                            │   Phase     │
         │                            │             │
         │                            │ consumes    │
         │                            │ pending_gm_beat
         │                            │ from prev turn
         │                            └──────┬──────┘
         │                                   │
         │                                   ▼ narration
         │                            ┌─────────────┐
         │                            │   Record    │ ← replaces Storytell
         │                            │   Phase     │
         │                            │             │
         │                            │ threads only│
         │                            │ (no beats)  │
         │                            └──────┬──────┘
         │                                   │
         │                                   ▼
         │                            ┌─────────────┐
         │                            │  Persist    │
         │                            └──────┬──────┘
         │                                   │
         │                                   ▼
         │                            ┌─────────────┐
         │                            │   World     │ ← NEW async step
         │                            │   (async)   │
         │                            │             │
         │                            │ generates   │
         │                            │ 2-3 beat    │
         │                            │ candidates  │
         │                            └──────┬──────┘
         │                                   │
         │                                   ▼ beat_candidates
         │                            ┌─────────────┐
         │                            │ state.meta  │ ← available for
         │                            │ beat_candidates │ Turn N+1
         │                            └─────────────┘
         │
         ▼
  Turn N+1 Ruling reads beat_candidates ←──────┘
```

### Beat Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BEAT CANDIDATE LIFECYCLE                          │
└─────────────────────────────────────────────────────────────────────┘

  World (async, turn N)
       │
       │ generates 2-3 candidates
       ▼
  ┌─────────────────────┐
  │ beat_candidates     │
  │ [                   │
  │   {type, effect,   │
  │    npc_id, driver}, │
  │   {type, effect,   │
  │    npc_id, driver}, │
  │   ...               │
  │ ]                   │
  │ stored in           │
  │ state.meta          │
  └─────────┬───────────┘
            │
            │ Turn N+1 starts
            ▼
  ┌─────────────────────┐
  │ Ruling reads        │
  │ beat_candidates     │
  │ + player intent     │
  └─────────┬───────────┘
            │
            │ ruling selects ONE or NONE
            ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │ Ruling ALWAYS discards all beat_candidates and either sets a      │
   │ new pending_gm_beat or clears it. No "keep current beat" path.    │
   │                                                                   │
   │ IF selected_beat present:                                         │
   │   → set pending_gm_beat (expires turn+2)                          │
   │   → append to recent_beats                                        │
   │   → discard all beat_candidates                                   │
   │                                                                   │
   │ IF no selected_beat:                                              │
   │   → pop pending_gm_beat (null-clear)                              │
   │   → discard all beat_candidates                                   │
   └───────────────────────────────────────────────────────────────────┘
             │
             │ Turn N+2 or N+3: pending_gm_beat expires
             │ (consumed by Narrate on turn N+1, expires turn N+3)
             ▼
   beat_candidates = [] (cleared, World regenerates next turn)
```

### Pending GM Beat Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                  PENDING_GM_BEAT LIFECYCLE                           │
└─────────────────────────────────────────────────────────────────────┘

   Turn N (ruling phase):
     Ruling reads beat_candidates (from Turn N-1's World).
     IF a candidate fits (and Ruling chooses to commit one) →
        pending_gm_beat = {type, effect, npc_id, driver}    ← NO beat_expires_turn
     ELSE (no candidate / Ruling declines) →
        pop pending_gm_beat from state.meta (null-clear).

   Turn N (narrate phase, same turn — runs immediately after ruling):
     Narrate reads pending_gm_beat ← integrates into narration.
     Narrate does NOT clear pending_gm_beat after consuming it
     (the next turn's Ruling owns the clear/replace).

   Turn N+1 (ruling phase):
     Ruling always either sets a new pending_gm_beat or null-clears it.
     → pending_gm_beat from Turn N is overwritten either way.

No expiry arithmetic. beat_expires_turn is REMOVED. State hygiene is the
Ruling phase's "always replace or pop" rule — every turn unconditionally
resolves pending_gm_beat one way or the other, so no orphan can survive
a turn boundary.


  TIMELINE EXAMPLE:

  Turn 10: Ruling selects "complication"
    pending_gm_beat = {type: "complication", effect: "...", npc_id: "..."}
    → Narrate integrates it (same turn).

  Turn 11: Ruling says "no fit" (or World produced [] last turn)
    → pop pending_gm_beat → None.
    → Narrate runs with no GM beat this turn.

  Turn 12: Ruling selects "revelation"
    → pending_gm_beat = {type: "revelation", ...}, overwriting whatever was there.
```

**Narrate change (consequent):** `narrate.py` (lines ~169-174) currently reads `pending_gm_beat`, checks `beat_expires_turn`, and **nulls it if expired**. With no expiry, that block collapses to "read pending_gm_beat if present." The plan must remove the `beat_expires_turn` check + the `state.setdefault("meta", {})["pending_gm_beat"] = None` clear-on-expiry branch. Narrate becomes purely a *reader* of `pending_gm_beat`; it never mutates it.

## Decisions

### D1: Record replaces Storytell

Record is Storytell with beat generation removed. It handles backward-looking tasks only:

**Tasks:**
- `thread_update`, `thread_resolve`, `thread_add`
- `goal_update`, `arc_resolve`
- `actions` (4 suggestions)
- `outcome_summary` (1-2 sentence recap)

**Removed from Record:** `gm_beat` field entirely.

**Record inputs (trimmed):**

| Input | Kept? | Reason |
|-------|-------|--------|
| `narration` | Yes | Needed for thread analysis, actions, outcome_summary |
| `arc.threads[]` | Yes | Core domain for thread operations |
| `rules_outcome.band` | Yes | Thread advancement guidance |
| `recent_turns[-10:]` | Yes | Context for thread analysis |
| `prior_history[:-1]` | Yes | Context for thread analysis |
| ~~`pacing_context`~~ | **No** | Not needed for backward-looking documentation |
| ~~`candidate_npcs`~~ | **No** | Moved to World |
| ~~`npc_roster`~~ | **No** | No beat generation needed |
| ~~`inventory`~~ | **No** | Not needed for thread/arc operations |
| ~~`conditions`~~ | **No** | Not needed for thread/arc operations |
| ~~`intent`~~ | **No** | Not needed for backward-looking analysis |
| ~~`recent_beats`~~ | **No** | Moved to World |

**Record outputs:**

| Output | Present? |
|--------|----------|
| `thread_update` | Yes |
| `goal_update` | Yes |
| `arc_resolve` | Yes |
| `thread_resolve` | Yes |
| `thread_add` | Yes |
| `actions` | Yes |
| `outcome_summary` | Yes |
| ~~`gm_beat`~~ | **No** |

**Record temperature:** `extract_temperature` (`0.4`) — unchanged from current Storytell. Record goes through the shared `_call_stream` (extraction/utils.py:230) which hardcodes `config.extract_temperature`, so no new config field is introduced.

**Future note — per-stream temperatures:** the design does *not* add `record_temperature` now. If Record quality suggests 0.4 is too high for deterministic scribe work, a follow-up should split the extraction streams' temperatures (e.g. `scene_temperature` / `state_temperature` / `record_temperature`) by threading a temperature override through `_call_stream` or giving Record its own call path. Deferred — not in scope for this design.

**Record system prompt:** Current `storytell_system.j2` minus the GM Beat section (~40 lines of beat generation instructions).

**Record user prompt:** Current `storytell_user.j2` minus beat-related sections (pending_beat, recent_beats, candidate_npcs, pending_gm_beat). Keeps narration, threads, inventory, conditions, arc, recent_turns, prior_history.

**Record token estimate:** ~450-500 system tokens, ~1000-2500 user tokens (highly variable based on narration/threads).

### D2: World is a new async step

World generates 2-3 candidate GM beats for the next turn. It runs asynchronously after persist completes, while the player reads the current turn's narration.

**Tasks:**
- Generate 2-3 candidate GM beats
- Each candidate: `type`, `effect`, `npc_id`, `driver` (no `beat_expires_turn` — see Pending GM Beat Lifecycle: expiry is removed)

**World inputs:**

| Input | Source |
|-------|--------|
| `candidate_npcs` | Scene Extract (stream 1) |
| `arc.threads[]` | State (urgency counts, active threads) |
| `narration` | Step 1 (full narration) |
| `pacing_context` | PacingContext (directive, outcome_hint, scene_phase) |
| `recent_beats` | `state.meta.recent_beats` |
| `allowed_beat_types` | Phase-derived constraints |

**World outputs:**

| Output | Storage |
|--------|---------|
| `beat_candidates: list[dict]` (2-3 candidates) | `state.meta.beat_candidates` |

**World candidate validation (repurposed `GMBeat`):** each candidate dict is validated with `GMBeat(**candidate)`; on `ValidationError` the candidate is dropped (not retried). Invalid `type`/`driver` are silently coerced to `None` by the existing `GMBeat` validators, and a candidate whose `type` ends up empty is dropped. Storage is `beat.model_dump(exclude_none=True)` per surviving candidate — so `state.meta.beat_candidates` holds the same validated shape Ruling will later ingest. This keeps `GMBeat`'s enum guardrail active at the World boundary even though `StorytellerResult.gm_beat` is gone.

**World temperature:** `0.55`. Medium temperature for constrained creative generation. This is a new config field: `world_temperature`.

**World system prompt:** New template `world_system.j2`. Contains beat schema, generation rules, diversity constraints, phase-beat alignment. ~40-50 lines, ~200-250 tokens.

**World user prompt:** New template `world_user.j2`. Contains candidate_npcs, thread urgency counts, pacing_context, recent_beats, allowed_beat_types, narration. ~40-50 lines, ~1000-2000 tokens.

**World timing & failure handling:** see D5 (placement, `_inflight` gate) and D8 (Sanitize→World ordering, single end-of-turn `save_state`). If World's LLM call fails/returns invalid JSON, log a warning, set `beat_candidates = []`, still persist + emit `world_done` + return.

**beat_expires_turn:** **Removed entirely.** World does not emit it; Ruling does not set it. See "Pending GM Beat Lifecycle" — Ruling's always-replace-or-pop rule makes expiry arithmetic vestigial. (Narrate's old expiry check is deleted as a consequence.)

### D3: Ruling selects beats from candidates

Ruling reads beat candidates prepared by World. It picks the best beat for the player's actual intent using narration + user input + candidates.

**New ruling task:** Beat selection — pick best beat from `beat_candidates` based on player intent.

**Ruling inputs (new):**

| Input | Source |
|-------|--------|
| `beat_candidates` | `state.meta.beat_candidates` (prepared by World) |

**Ruling outputs (new):**

| Output | Mechanism |
|--------|-----------|
| `selected_beat` | Added to ruling's JSON output alongside intent/ruling JSON |

**Ruling JSON schema change:** Add optional `selected_beat` field to ruling's JSON output:

```json
{
  "intent": "...",
  "intent_verb": "...",
  "target": "...",
  "impossible": true,
  "reason": "...",
  "scene_motion": "hold",
  "check": {
    "required": true,
    "skill": "...",
    "difficulty": "trivial|easy|normal|hard|extreme"
  },
  "selected_beat": {
    "type": "...",
    "effect": "...",
    "npc_id": "...",
    "driver": "..."
  }
}
```

**Ruling system prompt change:** Add ~4-5 lines of beat selection instructions to `ruling_system.j2`:

```
## Beat Selection

The world has prepared 2-3 candidate beats for the next turn. Choose the one that best fits the player's intent and the current narration.

- `beat_candidates` is provided in the user prompt (variable data).
- Pick ONE beat that meshes with the player's intent.
- If no beat fits well, omit `selected_beat` (emit null).
```

**Ruling user prompt change:** Add beat_candidates section to `ruling_user.j2`:

```
## Beat Candidates
{% if beat_candidates %}
{% for b in beat_candidates %}- **{{ b.type }}**: {{ b.effect }}{% if b.npc_id %} (NPC: {{ b.npc_id }}){% endif %}
{% endfor %}
{% else %}
No beat candidates prepared.
{% endif %}
```

**Ruling temperature:** Unchanged (0.2). Beat selection is a constrained choice problem, not creative generation.

**Ruling token estimate:** ~450-475 system tokens (+~25 for selection instructions), ~1000-1700 user tokens (+~10-15 lines for beat_candidates section).

**selected_beat extraction:** In `_call_ruling()`, extract `selected_beat` from JSON dict *before* constructing `IntentEnvelope`:

```python
# In _call_ruling(), after _find_json():
j = _find_json(cleaned)
selected_beat = j.get("selected_beat") if j else None  # before IntentEnvelope construction
intent = IntentEnvelope(**j)
return intent, usage, raw, parse_error, selected_beat
```

**pending_gm_beat and recent_beats:** Set in `_ruling_phase()` after `_call_ruling()` returns:

```python
# In _ruling_phase(), after _call_ruling():
intent, ruling_usage, ruling_raw_response, ruling_parse_error, selected_beat = await _call_ruling(...)

beat = None
if selected_beat:
    try:
        beat = GMBeat(**selected_beat)          # validates type/driver enums, coerces bad → None
    except ValidationError:
        beat = None                             # malformed → null path (no retry)

if beat and beat.type:                          # _nullify_invalid_gm_beat logic now inline here
    beat_dict = beat.model_dump(exclude_none=True)   # NO beat_expires_turn field on GMBeat anymore
    state.setdefault("meta", {})["pending_gm_beat"] = beat_dict
    # Append to recent_beats (replaces turn_state.py logic)
    meta = state.setdefault("meta", {})
    meta.setdefault("recent_beats", []).append({
        "turn": turn_no,
        "type": beat.type,
        "effect": beat.effect,
    })
    max_beats = config.recent_beats_max or 5
    if len(meta["recent_beats"]) > max_beats:
        meta["recent_beats"] = meta["recent_beats"][-max_beats:]
else:
    # Null-clear: "no beat fits" path is preserved (some turns deserve no GM intrusion).
    state.get("meta", {}).pop("pending_gm_beat", None)
```

**Why `GMBeat` survives the `gm_beat` removal:** `GMBeat` is **repurposed** as the typed validation schema for `selected_beat` (Ruling) and for each World candidate. Its `type`/`driver` `Literal` validators + `_coerce_gm_beat_type`/`_coerce_gm_beat_driver` silently coerce out-of-enum values to `None`, preserving the guardrail that currently protects the pipeline. The `beat_expires_turn` field is removed from `GMBeat` (see Pending GM Beat Lifecycle). `StorytellerResult` loses its `gm_beat` field, but `GMBeat` is reused at the new ingestion boundary.

**beat_candidates cleanup:** Ruling always discards `beat_candidates` after selection (or non-selection):

```python
# In _ruling_phase(), after pending_gm_beat/recent_beats handling:
state.get("meta", {}).pop("beat_candidates", None)
```

**Failure mode — malformed selected_beat:** If ruling parses `IntentEnvelope` successfully but `selected_beat` is malformed (e.g., missing `type`), treat it as absent. No retry — ruling has already succeeded. The beat generation diversity guidance will simply not advance for this turn.

### D4: Beat candidates lifecycle

All candidates are discarded after ruling selects one. World regenerates fresh candidates each turn.

**Storage:** `state.meta.beat_candidates` — list of dicts (simplified schema, no `beat_expires_turn`).

**Schema for World output (simplified):**

```json
[
  {
    "type": "complication",
    "effect": "The guard captain arrives with reinforcements.",
    "npc_id": "captain_miller",
    "driver": "motivation"
  },
  ...
]
```

**TTL:** Candidates expire at end of turn when ruling selects (or discards) them. No persistence across turns.

**State model change:**

| Field | Scope | Type | Owner |
|-------|-------|------|-------|
| `meta.beat_candidates` | Add | `list[dict]`, default `[]` | `world.py` — written by World step; read by ruling |

### D5: World runs at the very end of the turn, async — before the next turn begins

World runs **after** the turn is completely over (narration + actions already shown to the player) and **before** the next turn's submission is accepted. It is genuinely async with respect to the player: the player reads the narration while World generates candidates in the background (~4-5s). World's output (`beat_candidates` in `state.meta`) is only consumed by the *next* turn's Ruling.

**Placement:** World is the last phase of `run_turn`. It runs after `yield ("complete", result_obj)` (turn.py:529). The UI receives narration immediately on `complete`; World yields its own `("phase", {"phase": "world_start"})` / `("phase", {"phase": "world_done"})` events and writes `state.meta.beat_candidates`.

**Mechanism — reuse `_inflight` as the gate (no new flag):** The submit guard is `is_turn_in_progress()`, which checks the existing `_inflight` lock. If World runs *inside* `run_turn`'s body after `yield ("complete")`, the lock is NOT released until `run_turn`'s generator fully returns (the `finally` at turn.py:568 only fires when the generator is closed/exhausted). Therefore the submit guard stays asserted for the full World window automatically — provided the SSE consumer **iterates the async generator to exhaustion** instead of breaking after `complete`. Implementation requirements:

1. The route handler must keep calling `__anext__()` past `("complete", ...)` until `StopAsyncIteration` (i.e., until the generator returns). Events emitted after `complete` (`world_start`/`world_done`) are informational; the UI may ignore their payload but the route must drain them.
2. `run_turn` yields `("complete")` first (UI shows narration), then runs World, then returns — at which point `finally` releases `_inflight`.
3. The next turn's `run_turn` calls `await _inflight.acquire()` (turn.py:87) and blocks if World is still running.

```python
# In turn.py, after yield ("complete", result_obj) — World is the terminal phase:
yield ("phase", {"phase": "world_start"})
beat_candidates = await _run_world_step(env, state, narration, scene_result, pacing_context, config, trace_id, turn_no)
state.setdefault("meta", {})["beat_candidates"] = beat_candidates or []
yield ("phase", {"phase": "world_done"})
# then return → finally releases _inflight
```

**Route change (required):** the SSE turn route must drain the generator past `complete` rather than `break`-ing. This is the one cross-module change D5 introduces; the plan must specify it.

**Failure mode:** if World times out or returns invalid JSON, log a warning, set `beat_candidates = []`, and still emit `world_done` + return (the lock releases, next turn proceeds with no candidates → Ruling selects null). World resolves one way or another before the lock lifts.

**Rationale:** World will grow beyond beat generation (e.g. sanitizer — see D8). Allowing the next turn to start before World completes would create an unreliable pipeline dependency. Reusing `_inflight` avoids a second flag and keeps the submit guard a single source of truth.

### D6: Beat selection mechanism — ruling JSON includes selected_beat

Ruling's JSON output includes a `selected_beat` field alongside intent/ruling JSON. This is the cleanest approach — ruling outputs everything in one JSON.

**Python handling:** After ruling JSON is parsed (in `_call_ruling()`):
1. Extract `selected_beat` from JSON dict before `IntentEnvelope` construction
2. Return as 5th element of tuple: `(IntentEnvelope, usage, raw, parse_error, selected_beat)`

**In `_ruling_phase()`:**
1. If `selected_beat` is present and valid → set `state.meta.pending_gm_beat` (**no `beat_expires_turn`** — expiry removed)
2. If `selected_beat` is absent/null → pop `pending_gm_beat` from state (null-clear behavior unchanged)
3. Always pop `beat_candidates` from state (cleanup)

### D7: Record keeps actions and outcome_summary

Record still generates `actions` (4 suggestions) and `outcome_summary` (1-2 sentence recap). These are natural outputs of reviewing what happened narratively.

**Rationale:** Actions and outcome_summary are backward-looking — they summarize what just happened and suggest what the player could do next. They don't require forward-looking beat generation.

### D8: Sanitize and World are two separate end-of-turn async steps

The thread sanitizer (`sanitize_threads`, currently synchronous in `turn.py` ~490-500 before persist) moves off the synchronous critical path as its own end-of-turn phase — **separate from World, not bundled into it.** Sanitize and World do different jobs: Sanitize is backward-looking scribe work over thread state (kin to Record — dedup, id normalization, latent-thread collapse); World is forward-looking beat generation. The separation also future-proofs Sanitize, whose role is expected to expand.

**Placement:** two distinct phases inside `run_turn`, both after `yield ("complete", result_obj)` and both within the `_inflight`-held window (D5):

```
yield ("complete", result_obj)        # ← player sees narration
# --- end-of-turn async window (lock held) ---
yield ("phase", {"phase": "sanitize_start"})
if config.sanitize_every > 0:
    state, _ = await sanitize_threads(save_dir, state, config, trace_id=trace_id)
yield ("phase", {"phase": "sanitize_done"})
yield ("phase", {"phase": "world_start"})
beat_candidates = await _run_world_step(env, state, narration, scene_result, pacing_context, config, trace_id, turn_no)
state.setdefault("meta", {})["beat_candidates"] = beat_candidates or []
save_state(save_dir, state)            # ← second/single persist of end-of-turn state
yield ("phase", {"phase": "world_done"})
# return → finally releases _inflight
```

**Stale-input invariant (critical):** World receives the **same live `state` Python reference** Sanitize just mutated — never a reload or a snapshot. Sanitize mutates `state["arc"]["threads"]` in place; World's `_run_world_step` reads that exact dict, so it sees sanitized threads by construction. The plan must pass the same `state` object through both calls; no intermediate `save_state`+`load_state`, no `copy.deepcopy`. (This is why the single `save_state` is deferred to after **both** steps — persisting between them would force World to reload and risk stale reads.)

**Persistence:** a single `save_state(save_dir, state)` at the very end persists sanitizer edits + `beat_candidates` together. The first `save_state` (before `yield("complete")`) still happens — it persists the completed-turn state the UI shows. The end-of-turn `save_state` overwrites it with the post-sanitize + candidate-bearing state; the next turn's `load_state` always picks up the merged result.

**`sanitize_every` cadence unchanged** — only its placement moves. The `world_start`/`world_done` / `sanitize_start`/`sanitize_done` events are informational; the UI ignores post-`complete` events but the route still drains them (D5).

**World failure handling:** if World times out or returns invalid JSON, log a warning, set `beat_candidates = []`, still run `save_state` + emit `world_done` + return. Sanitize and World resolve one way or another before the lock lifts. Sanitize failure leaves `state` as-is (it already mutates in place or not at all).

## Prompt Template Changes

### New templates

| Template | Purpose | Lines | Est. Tokens |
|----------|---------|-------|-------------|
| `world_system.j2` | Beat generation instructions | ~40-50 | ~200-250 |
| `world_user.j2` | Beat generation inputs | ~40-50 | ~1000-2000 |

### Modified templates

| Template | Change | Lines | Est. Tokens |
|----------|--------|-------|-------------|
| `storytell_system.j2` → `record_system.j2` | Remove GM Beat section (~40 lines) | ~100 | ~450-500 |
| `storytell_user.j2` → `record_user.j2` | Remove pending_beat, recent_beats, candidate_npcs sections | ~75 | ~1000-2500 |
| `ruling_system.j2` | Add beat selection instructions (~4-5 lines) | ~90 | ~450-475 |
| `ruling_user.j2` | Add beat_candidates section (~10-15 lines) | ~45 | ~1000-1700 |

### Template rename

`storytell_system.j2` → `record_system.j2`
`storytell_user.j2` → `record_user.j2`

The extraction pipeline code references these by name. Update references in `extraction/storytell.py` or rename the files.

## Model Changes

### New config fields

| Key | Default | Type | Purpose |
|-----|---------|------|---------|
| `world_temperature` | `0.55` | `float` | Temperature for World beat generation |

### New state fields

| Field | Scope | Type | Owner |
|-------|-------|------|-------|
| `meta.beat_candidates` | Add | `list[dict]`, default `[]` | `world.py` — written by World step; read by ruling |

### StorytellerResult model change

Remove `gm_beat` field from `StorytellerResult`. This is a breaking change for the extraction pipeline.

**File:** `ccya/models/extraction.py`

```python
class StorytellerResult(BaseModel):
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""
    goal_update: dict[str, Any] | None = None
    # gm_beat: GMBeat | None = None  ← REMOVED
    thread_resolve: list[ThreadResolution] = Field(default_factory=list)
    thread_add: ArcThread | None = None
    thread_update: list[ThreadUpdate] = Field(default_factory=list)
    arc_resolve: ArcResolution | None = None
```

### TurnResult model change

Remove `gm_beat` field from `TurnResult`.

**File:** `ccya/models/config.py`

```python
@dataclass
class TurnResult:
    turn: int
    trace_id: str
    narrative: str
    state_delta: dict[str, Any]
    applied: dict[str, Any] = field(default_factory=dict)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    diff: list[str] = field(default_factory=list)
    changes: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    ruling: dict[str, Any] = field(default_factory=dict)
    outcome_summary: str = field(default="")
    # gm_beat: dict[str, str] | None = None  ← REMOVED
    outcome_hint: str | None = None
    scene_phase: str = field(default="")
    summary: str = field(default="")
    ts: str = field(default="")
```

### Ruling JSON schema change

Add optional `selected_beat` field to ruling's JSON output. This is validated by ruling's system prompt instructions, not by a Pydantic model (ruling JSON is parsed manually in `_call_ruling`).

### _call_ruling return signature change

Extend return tuple from 4-tuple to 5-tuple:

```python
# Before:
async def _call_ruling(...) -> tuple[IntentEnvelope, dict[str, int], str, str]:
    ...
    return intent, usage, raw, parse_error

# After:
async def _call_ruling(...) -> tuple[IntentEnvelope, dict[str, int], str, str, dict | None]:
    ...
    j = _find_json(cleaned)
    selected_beat = j.get("selected_beat") if j else None
    intent = IntentEnvelope(**j)
    return intent, usage, raw, parse_error, selected_beat
```

### _ruling_phase signature change

Update callers to unpack 5-tuple:

```python
# In _ruling_phase():
intent, ruling_usage, ruling_raw_response, ruling_parse_error, selected_beat = await _call_ruling(...)
```

## Cascade: Files to update for gm_beat removal

Removing `gm_beat` from `StorytellerResult` and `TurnResult` requires updates to these files:

| File | Lines | Change |
|------|-------|--------|
| `ccya/models/extraction.py` | 232 | Remove `gm_beat: GMBeat \| None = None` from `StorytellerResult` |
| `ccya/models/extraction.py` | 255-259 | Remove `_nullify_invalid_gm_beat` validator |
| `ccya/models/extraction.py` | 215 | Remove `beat_expires_turn: int \| None = None` from `GMBeat` (TTL dropped — see Pending GM Beat Lifecycle) |
| `ccya/models/extraction.py` | 181-225 | `GMBeat` **repurposed** (not removed): drop `beat_expires_turn` field; keep `type`/`driver` `Literal` + `_coerce_*` validators. Now validates World's candidates and Ruling's `selected_beat` (see D2/D3). |
| `ccya/models/config.py` | 43 | Remove `gm_beat: dict[str, str] \| None = None` from `TurnResult` |
| `ccya/engine/narrate.py` | 169-174 | Remove the `beat_expires_turn` expiry check + the `pending_gm_beat = None` clear-on-expiry branch. Narrate becomes a pure *reader* of `pending_gm_beat`. |
| `ccya/engine/extraction/pipeline.py` | 225-261 | Remove beat retry logic (npc_id-without-effect) |
| `ccya/engine/extraction/pipeline.py` | 315 | Remove `gm_beat=%s` from debug log |
| `ccya/engine/extraction/pipeline.py` | 383-385 | Remove NOTE comment about gm_beat |
| `ccya/engine/turn.py` | 269-279 | Remove beat lifecycle (moved to ruling phase) |
| `ccya/engine/turn.py` | 490-500 | Remove synchronous `sanitize_threads` call (moved to World phase — see D8) |
| `ccya/engine/turn.py` | 520-523 | Remove `gm_beat=` from `TurnResult` construction |
| `ccya/engine/turn.py` | after 529 | Add two end-of-turn phases: after `yield ("complete", result_obj)`, run Sanitize (`sanitize_threads`, own `sanitize_start`/`sanitize_done` events) then World (`_run_world_step`, `world_start`/`world_done`), then a single end-of-turn `save_state`. See D5/D8. |
| `ccya/engine/ruling.py` | 234 | Unpack 5-tuple from `_call_ruling` |
| `ccya/engine/ruling.py` | after _call_ruling | Set `pending_gm_beat` (no `beat_expires_turn`) + `recent_beats` + cleanup `beat_candidates` |
| `ccya/engine/turn_state.py` | 480-494 | Remove beat history append (moved to ruling phase) |
| `ccya/server/routes.py` | 384 | Remove `"gm_beat": result.gm_beat` |
| `ccya/server/routes.py` | SSE turn route | **Drain the `run_turn` async generator to exhaustion** past `("complete", ...)` so the World phase runs and `_inflight` stays held until World returns (see D5) |
| `ccya/server/tv.py` | 546-594 | Remove `gm_beat_type`/`gm_beat_effect` from turn viewer data |
| `ccya/templates/_turn_viewer.html` | 288-302 | Remove beat display HTML |
| **(new)** `ccya/engine/extraction/record.py` | — | Record message building (current `storytell.py` minus beat sections) |
| **(new)** `ccya/engine/world.py` | — | World: beat-candidate generation (validates each candidate via `GMBeat`). End-of-turn async phase, runs after Sanitize. |
| **(new)** `ccya/prompts/world_system.j2` / `world_user.j2` | — | World templates |
| `ccya/ev/state_tools.py` | 349-352 | **DEFERRED (EV)** — stop reading `storytell.gm_beat` from event data |
| `ccya/ev/deltas.py` | 169-191 | **DEFERRED (EV)** — remove beat display from compact delta view |
| `ccya/ev/audit.py` | 346-360 | **DEFERRED (EV)** — remove gm_beat format check |
| `ccya/ev/prompt_context.py` | 171, 250 | **DEFERRED (EV)** — reconcile `pending_beat` with new ruling-set lifecycle |
| `ccya/ev/checkers/gm_beat.py` | — | **DEFERRED (EV)** — remove (reads `storytell.gm_beat` which is no longer emitted) |
| `ccya/ev/checkers/beat_phase_validity.py` | — | **DEFERRED (EV)** — remove/replace for new World→Ruling lifecycle |
| `ccya/ev/checkers/__init__.py` | 124 | **DEFERRED (EV)** — remove the two checker imports |
| `ccya/ev/check.py` | 19 | **DEFERRED (EV)** — remove `gm_beat_lifecycle`/`beat_phase_validity` from `"Beats"` registry |
| `ccya/ev/eval.py` | 93 | **DEFERRED (EV)** — remove `gm_beat_lifecycle`/`beat_phase_validity` from `"GM Beats"` registry |

## Pipeline Changes

### Current pipeline

```
USER INPUT → Step 0: Ruling → Dice → Phase → Step 1: Narrate → Step 2a: Scene → Step 2b: State → Step 2c: Storytell → Validate → Apply → Persist
```

### New pipeline

```
USER INPUT → Step 0: Ruling → Dice → Phase → Step 1: Narrate → Step 2a: Scene → Step 2b: State → Step 2c: Record → Validate → Apply → Persist → Step 2d: World (async)
```

**Ruling change:** Ruling reads `beat_candidates` from `state.meta` and outputs `selected_beat` in JSON. Sets `pending_gm_beat` and `recent_beats` in ruling phase (replaces extract-phase logic).

**Record change:** Record is called from extraction pipeline (replaces Storytell). It uses trimmed inputs (no pacing_context, no candidate_npcs, no npc_roster, no inventory, no conditions, no intent, no recent_beats).

**World change:** World is called after persist completes. It runs async while player reads. It writes `beat_candidates` to `state.meta`.

### Extraction pipeline changes

**File:** `ccya/engine/extraction/pipeline.py`

The extraction pipeline currently calls `_storytell_messages()` and `_call_stream()` for stream 3. This needs to be replaced with `_record_messages()` and `_call_stream()` for Record.

**New file:** `ccya/engine/extraction/record.py` — Record message building (based on current `storytell.py` minus beat generation sections).

**New file:** `ccya/engine/world.py` — World beat generation (new).

### Turn orchestration changes

**File:** `ccya/engine/turn.py`

After `yield ("complete", result_obj)` (line 529), append two end-of-turn async phases (Sanitize then World), then a single end-of-turn `save_state`. The `_inflight` lock stays held until the generator returns (D5/D8):

```python
# After yield ("complete", result_obj) — end-of-turn async window (lock held):
# 1. Sanitize (own phase events)
yield ("phase", {"phase": "sanitize_start"})
if config.sanitize_every > 0:
    state, _ = await sanitize_threads(save_dir, state, config, trace_id=trace_id)
yield ("phase", {"phase": "sanitize_done"})
# 2. World (beat candidates — receives the same live `state` Sanitize just mutated)
yield ("phase", {"phase": "world_start"})
beat_candidates = await _run_world_step(env, state, narration, scene_result, pacing_context, config, trace_id, turn_no)
state.setdefault("meta", {})["beat_candidates"] = beat_candidates or []
save_state(save_dir, state)              # single end-of-turn persist (Sanitize + candidates)
yield ("phase", {"phase": "world_done"})
# return → finally releases _inflight
```

Ruling phase change (line ~107): Unpack 5-tuple from `_call_ruling()`, validate `selected_beat` via `GMBeat`, set `pending_gm_beat` (no `beat_expires_turn`) + `recent_beats` + cleanup `beat_candidates` (see D3 snippet).

Beat lifecycle change (line ~270): Remove Storytell beat handling entirely (moved to ruling phase).

Sanitizer change (line ~490-500): Remove the synchronous `sanitize_threads` block — it now runs as the first end-of-turn async phase (above).

### Ruling phase changes

**File:** `ccya/engine/ruling.py`

In `_ruling_messages()`: Add `beat_candidates` to user prompt context (read from `state.meta.beat_candidates`).

In `_call_ruling()`: Extract `selected_beat` from JSON before `IntentEnvelope` construction. Return 5-tuple.

In `_ruling_phase()`: After `_call_ruling()` returns, set `pending_gm_beat` + `recent_beats` + cleanup `beat_candidates`.

## What is unchanged

- **Ruling core logic:** Intent classification, impossibility check, difficulty adjustment, dice resolution — all unchanged.
- **Narrate:** Step 1 code is mostly unchanged but **not literally unchanged**: it still reads `pending_gm_beat` from `state.meta`, but now consumes the beat Ruling selected *the same turn* (not one prepared a full turn ahead), and the `beat_expires_turn` expiry-check/clear branch (`narrate.py:169-174`) is removed — Narrate becomes a pure reader of `pending_gm_beat` and no longer mutates it.
- **Scene Extract (2a):** Unchanged. Still produces `candidate_npcs`.
- **State Extract (2b):** Unchanged. Still produces inventory/conditions/location deltas.
- **Phase Engine:** Unchanged. Still computes `scene_phase`, `convergence_score`, `PacingContext`.
- **Beat schema:** `GMBeat` model's `type`/`effect`/`npc_id`/`driver` fields are preserved and **repurposed** as the validation schema for World's candidates and Ruling's `selected_beat` (D2/D3). **`beat_expires_turn` field is REMOVED.** The two `_coerce_gm_beat_*` validators stay. The `_nullify_invalid_gm_beat` `StorytellerResult` validator is removed (that model no longer carries `gm_beat`); its logic moves inline into Ruling's `if beat and beat.type:` check.
- **Beat TTL mechanics:** `beat_expires_turn` removed. State hygiene is Ruling's per-turn "always replace or pop" rule — no orphan survives a turn boundary. Beats are single-turn commitments.
- **Beat null-clear behavior:** When no beat selected, `pending_gm_beat` is popped from state.
- **Thread lifecycle:** `_apply_thread_updates()`, `_apply_thread_resolutions()`, `_apply_arc_resolve()` — all unchanged.
- **Thread sanitizer:** **Changed** — moves off the synchronous critical path to its own end-of-turn async phase (see D8). `sanitize_threads` itself is unchanged; only its call site and timing change.
- **Persist:** Atomic writes (events.jsonl, state.yaml, chronicle.md) — unchanged.
- **EV checkers:** EV-side cleanup deferred to a follow-up (see OQ9). `gm_beat.py` and `beat_phase_validity.py` will be removed/rewritten then; for now they read event JSON dicts and degrade gracefully (no crashes, just vacuous output) until `gm_beat` reappears via `selected_beat`.

## Token Summary

| Step | System tokens | User tokens | Total |
|------|--------------|-------------|-------|
| **Record** | ~450-500 | ~1000-2500 | ~1450-3000 |
| **World** | ~200-250 | ~1000-2000 | ~1200-2250 |
| **Ruling** | ~450-475 | ~1000-1700 | ~1450-2175 |
| **Total** | **~1100-1225** | **~3000-6200** | **~4100-7425** |

**vs. current total:** ~1000-1150 system + ~2300-5500 user = ~3300-6650

The total token count increases modestly (~40-60% more system tokens due to duplication of instructions across Record and World system prompts). User prompt total stays roughly similar or decreases since Record's user prompt drops significantly.

**Key difference:** Record's system prompt drops by ~30% (beat generation instructions removed). World's system prompt is very lightweight since beat generation is a constrained task. Ruling's system prompt barely changes (+~25 tokens for selection instructions).

## Open Questions — Resolved

### OQ1: Record actions without inventory/conditions

**Decision:** Actions generated by Record are arc and thread-focused. They suggest what the player could do next in terms of narrative momentum, not item usage or NPC interaction. Inventory and NPC inputs were removed deliberately — not just for token economy, but because actions should reflect story direction. If action quality proves insufficient without those inputs, they can be re-added, but the default scope is intentionally narrow.

### OQ2: Recent beats ownership

**Decision:** Ruling owns appending `recent_beats`. `recent_beats` records what beat was actually *used* in narration (the ruling-selected beat), not what World prepared. This keeps diversity guidance accurate — the history reflects what actually happened.

### OQ3: World template location

**Decision:** `world_system.j2` and `world_user.j2` in `ccya/prompts/`. Same level as all current templates. No subdirectory.

### OQ4: Ruling JSON parsing approach

**Decision:** Keep manual parsing. `selected_beat` is optional and small. Manual dict check in `_call_ruling()` after `_find_json()` extends the existing pattern without adding a new Pydantic model.

### OQ5: beat_expires_turn ownership

**Decision:** **Removed entirely** (supersedes the earlier "Ruling sets turn_no+2" decision). Under the new model Ruling always either replaces or pops `pending_gm_beat` each turn, so no orphan can outlive a turn boundary — expiry arithmetic is vestigial. Narrate's setup-time expiry check is deleted as a consequence (Narrate becomes a pure reader of `pending_gm_beat`).

### OQ6: beat_candidates cleanup

**Decision:** Ruling always pops `beat_candidates` from `state.meta` after selection (or non-selection). Candidates never persist across turns.

### OQ6b: Beats are single-turn commitments

**Decision:** Beats are single-turn commitments. World generates fresh candidates each turn; Ruling always discards all candidates and either sets a new `pending_gm_beat` or null-clears it (no "keep current beat" path). `beat_expires_turn` is removed — Ruling's per-turn replace-or-pop is the sole hygiene mechanism. The "no beat fits → null" path is preserved (some turns legitimately have no GM intrusion).

### OQ7: World failure handling

**Decision:** If World's LLM call times out or returns invalid JSON, log a warning and set `beat_candidates = []`. This happens before submission is re-enabled — the turn completes (World resolves one way or another), then the submit guard lifts. Ruling proceeds without beat selection (no `selected_beat` in JSON) on the next turn if candidates are empty.

### OQ8: malformed selected_beat handling

**Decision:** If ruling parses `IntentEnvelope` successfully but `selected_beat` is malformed (e.g., missing `type`), treat it as absent. No retry — ruling has already succeeded. The beat generation diversity guidance will simply not advance for this turn.

### OQ9: EV checkers

**Decision:** **Out of scope for this design — all EV-side cleanup is deferred to a follow-up.** Removing `gm_beat` from `StorytellerResult` means the event JSON (`storytell_result.model_dump()`) will no longer carry a `gm_beat` key. EV code (`state_tools.py`, `deltas.py`, `audit.py`, the two checkers, the registries) reads via dict `.get("gm_beat")` / `output.get("gm_beat")`, so the **live turn pipeline will not break** — EV just reports no beats until it's updated. The deferred EV work is enumerated in the cascade table (rows marked **DEFERRED (EV)**). It must be done as a tracked follow-up; running EV against the new pipeline before that follow-up will produce empty/vacuous beat diagnostics but not crashes.

## Benefits

1. **Lower turn latency** — Record is lighter without beat generation; World runs async (~5s while player reads)
2. **Fewer errors** — Record's focused scribe role reduces error surface; no more overloaded LLM call
3. **Intent-aware beats** — Ruling selects from candidates using actual player intent, solving the disconnect problem
4. **Evenly distributed load** — Three focused steps, each with clear responsibility
5. **Better temperatures** — World at medium temp (0.55) for constrained creativity; Ruling unchanged (0.2). Record stays at `extract_temperature` for now (per-stream temperature split is a future refinement).

## Review

### Key Blockers

- **[RESOLVED] Async timing was self-contradictory in the first pass.** D5 now states World runs *after* the turn fully completes (after `yield("complete")`) and is gated by the reused `_inflight` lock held until the generator returns; the route must drain the generator past `complete`. One residual dependency: the route handler's iteration behavior must change (drain to exhaustion instead of breaking on `complete`). The plan must specify that route edit; see D5.
- **[RESOLVED] `GMBeat` model repurposed.** Decided (Option B): `GMBeat` loses `beat_expires_turn` but keeps `type`/`driver` `Literal` + `_coerce_*` validators and now validates World's candidates and Ruling's `selected_beat` at the new ingestion boundaries. The enum guardrail stays active; the `_nullify_invalid_gm_beat` `StorytellerResult` validator is removed (logic moves inline into Ruling's `if beat and beat.type:`). See D2/D3.
- **[RESOLVED] TTL vs. force-a-beat-every-turn.** Decision: keep Ruling's null path (no forced beat), drop `beat_expires_turn` entirely. Ruling's per-turn always-replace-or-pop makes expiry vestigial, so the complexity is gone but the "no beat fits" narrative optionality remains. Narrate's expiry-check branch is deleted (it becomes a pure reader of `pending_gm_beat`).

### Design Ambiguities

- **"Narrate unchanged" is misleading.** Narrate consumes a beat Ruling selected *moments earlier the same turn* (not one prepared a full turn ahead by Storytell), and the `beat_expires_turn` expiry-check/clear block (`narrate.py:169-174`) is deleted. Narrate becomes a pure reader of `pending_gm_beat` and no longer mutates it. The plan must include that narrate.py edit even though the design's "unchanged" sections don't flag it.
- **World system-prompt fidelity.** D2 allocates only ~200-250 tokens / 40-50 lines, calling World "very lightweight," but the current beat logic in `storytell_system.j2:77-117` already exceeds that before candidate-blend rules, driver-flavor mapping, roll-band guidance, and diversity constraints. Enumerate which instructions migrate vs. which are intentionally cut, or grow the budget.
- **`selected_beat` extraction relies on Pydantic's implicit extra-ignore.** `IntentEnvelope(**j)` passes a dict that still contains the `selected_beat` key. `IntentEnvelope` has no explicit `model_config = {"extra": "ignore"}`; it only works because Pydantic v2's *default* is extra-ignore (confirmed at runtime). Either pop `selected_beat` from `j` before construction, or add the explicit `model_config` — don't lean on the default.
- **Sanitizer re-persistence (D8).** `save_state` already ran before `yield("complete")`; the sanitizer must trigger a *second* `save_state` at the end of the World phase so the next turn loads sanitized threads. The `_inflight` gate guarantees the next turn waits for this second save, but the plan must order: sanitizer → beat candidates → `save_state` → return.
- **Checker registration sites are deferred, not deleted.** The DEFERRED (EV) rows include `ev/checkers/__init__.py:124`, `ev/check.py:19`, `ev/eval.py:93`. Until the follow-up, those registries still name two checkers whose assertions no longer fit the new lifecycle — vacuous but non-crashing.

### Suggested Improvements

- **[RESOLVED] Repurpose `GMBeat`.** Done — `GMBeat` validates candidates + `selected_beat` at both new boundaries. Enum coercion preserved permanently at ~6 lines/call-site cost; raw-dict option rejected as weaker.
- **[WARN] Specify a successor checker later (deferred).** The new World→Ruling→Narrate beat lifecycle deserves a successor to `gm_beat_lifecycle` ("`selected_beat` present ⟹ `pending_gm_beat` set on same turn; `beat_candidates` empty after ruling.") and to `beat_phase_validity`. Track as EV follow-up; not in scope now.
- **Ruling cognitive-load concern — withdrawn.** Per review discussion, Ruling's beat selection is near-arbitrary (World does the heavy thinking; Ruling picks one of the offered candidates). The original cognitive-load warning is not a real risk and is dropped from blockers.
- **Record temperature — deferred per decision.** Record stays at `extract_temperature` (0.4); a per-stream temperature split is noted as a future refinement (see D1 / "Future note").

### Minor Notes

- **[MINOR] Several cascade line references were stale** and have been corrected in-place: pipeline.py beat-retry 185-215 → 225-261; debug log 274 → 315; NOTE 334-336 → 383-385; turn_state.py 419-433 → 480-494; routes.py 379 → 384; turn.py 521-524 → 520-523. The design was written against an older revision — the planner should re-verify any remaining line numbers against current `main` before executing.
- **[MINOR] `tests/test_schema.py:511-517`** asserts a `surface_as` field that does not exist on `GMBeat` (silently ignored as extra). Tests are suspended per AGENTS.md; flag once tests return — that assertion is dead once `GMBeat` is repurposed/removed.
- **[MINOR] `_call_ruling` return type hint** should be `dict[str, Any] | None`, not bare `dict | None`, to match codebase style.
- **[MINOR] Pipeline diagram** still labels Narrate as "consumes pending_gm_beat from prev turn" — after the split it's same-turn (selected by Ruling moments earlier). Cosmetic.