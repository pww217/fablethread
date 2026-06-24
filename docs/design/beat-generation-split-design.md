---
status: reviewed
reviewed: 2026-06-24
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
| **Record** | Backward-looking | Sync (turn) | 0.2 | Post-narration scribe. Records what changed. |
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
  ┌───────────────────────────────────────────┐
  │ IF selected_beat present:                 │
  │   → set pending_gm_beat (expires turn+2)  │
  │   → append to recent_beats                │
  │   → discard all beat_candidates           │
  │                                           │
  │ IF no selected_beat:                      │
  │   → pop pending_gm_beat (null-clear)      │
  │   → discard all beat_candidates           │
  └───────────────────────────────────────────┘
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

  Turn N:
    Ruling selects beat → pending_gm_beat = {type, effect, ..., beat_expires_turn=N+2}
    │
    │ (beat_expires_turn = turn_no + 2)
    ▼
  Turn N+1:
    Narrate reads pending_gm_beat ← integrates into narration
    │
    │ beat_expires_turn check: if turn_no > expires_turn → clear
    │ (beat expires AFTER being consumed once)
    ▼
  Turn N+2 or N+3:
    pending_gm_beat expires → cleared from state.meta
    │
    │ (beat was consumed on turn N+1, expires on turn N+3)
    ▼
  pending_gm_beat = None


  TIMELINE EXAMPLE:

  Turn 10: Ruling selects beat of type "complication"
    pending_gm_beat = {type: "complication", beat_expires_turn: 12}

  Turn 11: Narrate consumes pending_gm_beat
    → narration integrates "complication" beat
    → pending_gm_beat still in state (expires_turn=12, not yet expired)

  Turn 12: pending_gm_beat still valid (12 <= 12)
    → Narrate could consume again if not cleared

  Turn 13: pending_gm_beat expired (13 > 12)
    → cleared from state.meta
```

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

**Record temperature:** `0.2`. Low temperature for deterministic scribe work. This is a new config field: `record_temperature`.

**Record system prompt:** Current `storytell_system.j2` minus the GM Beat section (~40 lines of beat generation instructions).

**Record user prompt:** Current `storytell_user.j2` minus beat-related sections (pending_beat, recent_beats, candidate_npcs, pending_gm_beat). Keeps narration, threads, inventory, conditions, arc, recent_turns, prior_history.

**Record token estimate:** ~450-500 system tokens, ~1000-2500 user tokens (highly variable based on narration/threads).

### D2: World is a new async step

World generates 2-3 candidate GM beats for the next turn. It runs asynchronously after persist completes, while the player reads the current turn's narration.

**Tasks:**
- Generate 2-3 candidate GM beats
- Each candidate: `type`, `effect`, `npc_id`, `driver` (no `beat_expires_turn` — ruling sets this)

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

**World temperature:** `0.55`. Medium temperature for constrained creative generation. This is a new config field: `world_temperature`.

**World system prompt:** New template `world_system.j2`. Contains beat schema, generation rules, diversity constraints, phase-beat alignment. ~40-50 lines, ~200-250 tokens.

**World user prompt:** New template `world_user.j2`. Contains candidate_npcs, thread urgency counts, pacing_context, recent_beats, allowed_beat_types, narration. ~40-50 lines, ~1000-2000 tokens.

**World timing:** Runs async after persist completes. Player can type input but cannot submit until World completes (~4-5s). This extends the existing "no submit while turn is running" mechanism.

**World failure handling:** If World's LLM call times out or returns invalid JSON, log a warning and set `beat_candidates = []`. Ruling proceeds without beat selection (no `selected_beat` in JSON).

**beat_expires_turn:** World does NOT set `beat_expires_turn` on candidates. This field is relative to the turn when the beat is *used*, not when generated. Ruling sets `beat_expires_turn = turn_no + 2` when selecting a beat.

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

if selected_beat and selected_beat.get("type"):
    beat_dict = {k: v for k, v in selected_beat.items() if v}  # exclude_none
    beat_dict["beat_expires_turn"] = turn_no + 2
    state.setdefault("meta", {})["pending_gm_beat"] = beat_dict
    # Append to recent_beats (replaces turn_state.py logic)
    meta = state.setdefault("meta", {})
    meta.setdefault("recent_beats", []).append({
        "turn": turn_no,
        "type": selected_beat.get("type"),
        "effect": selected_beat.get("effect"),
    })
    max_beats = config.recent_beats_max or 5
    if len(meta["recent_beats"]) > max_beats:
        meta["recent_beats"] = meta["recent_beats"][-max_beats:]
else:
    state.get("meta", {}).pop("pending_gm_beat", None)
```

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

### D5: Async timing — extension of existing submit guard

World runs async after persist completes. The player can type input but cannot submit until World completes (~4-5s). This extends the existing "no submit while turn is running" mechanism.

**Mechanism:** The UI already prevents submitting while a turn is in progress (tracked by `_inflight`). Extend this with a `beat_generation_in_progress` flag:

```python
# In turn.py, after persist (line ~476):
beat_generation_in_progress = True
yield ("phase", {"phase": "beat_generation_start"})
beat_candidates = await _run_world_step(env, state, narration, scene_result, pacing_context, config, trace_id, turn_no)
beat_generation_in_progress = False
state.setdefault("meta", {})["beat_candidates"] = beat_candidates or []
```

The UI blocks submission while `beat_generation_in_progress` is `True`. If the player somehow submits during this window, ruling proceeds without beat selection (no `selected_beat` in JSON).

**Fallback:** If the player submits before World completes (beat_candidates not ready), ruling proceeds without beat selection (no `selected_beat` in JSON). Narrate receives no beat for that turn.

### D6: Beat selection mechanism — ruling JSON includes selected_beat

Ruling's JSON output includes a `selected_beat` field alongside intent/ruling JSON. This is the cleanest approach — ruling outputs everything in one JSON.

**Python handling:** After ruling JSON is parsed (in `_call_ruling()`):
1. Extract `selected_beat` from JSON dict before `IntentEnvelope` construction
2. Return as 5th element of tuple: `(IntentEnvelope, usage, raw, parse_error, selected_beat)`

**In `_ruling_phase()`:**
1. If `selected_beat` is present and valid → set `state.meta.pending_gm_beat` with `beat_expires_turn = turn_no + 2`
2. If `selected_beat` is absent/null → pop `pending_gm_beat` from state (null-clear behavior unchanged)
3. Always pop `beat_candidates` from state (cleanup)

### D7: Record keeps actions and outcome_summary

Record still generates `actions` (4 suggestions) and `outcome_summary` (1-2 sentence recap). These are natural outputs of reviewing what happened narratively.

**Rationale:** Actions and outcome_summary are backward-looking — they summarize what just happened and suggest what the player could do next. They don't require forward-looking beat generation.

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
| `record_temperature` | `0.2` | `float` | Temperature for Record (replaces extract_temperature for record stream) |

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
| `ccya/models/extraction.py` | 232 | Remove `gm_beat: GMBeat | None = None` from `StorytellerResult` |
| `ccya/models/extraction.py` | 255-259 | Remove `_nullify_invalid_gm_beat` validator |
| `ccya/models/config.py` | 43 | Remove `gm_beat: dict[str, str] | None = None` from `TurnResult` |
| `ccya/engine/extraction/pipeline.py` | 185-215 | Remove beat retry logic |
| `ccya/engine/extraction/pipeline.py` | 274 | Remove `gm_beat=%s` from debug log |
| `ccya/engine/extraction/pipeline.py` | 334-336 | Remove NOTE comment about gm_beat |
| `ccya/engine/turn.py` | 270-279 | Remove beat lifecycle (moved to ruling phase) |
| `ccya/engine/turn.py` | 521-524 | Remove `gm_beat=` from `TurnResult` construction |
| `ccya/engine/ruling.py` | 234 | Unpack 5-tuple from `_call_ruling` |
| `ccya/engine/ruling.py` | after _call_ruling | Set `pending_gm_beat` + `recent_beats` + cleanup `beat_candidates` |
| `ccya/engine/turn_state.py` | 419-433 | Remove beat history append (moved to ruling phase) |
| `ccya/server/routes.py` | 379 | Remove `"gm_beat": result.gm_beat` |
| `ccya/server/tv.py` | 546-594 | Remove `gm_beat_type`/`gm_beat_effect` from turn viewer data |
| `ccya/templates/_turn_viewer.html` | 288-302 | Remove beat display HTML |
| `ccya/ev/state_tools.py` | 349-352 | Remove storytell.gm_beat reading |
| `ccya/ev/deltas.py` | 169-191 | Remove beat display from compact delta view |
| `ccya/ev/audit.py` | 346-360 | Remove gm_beat format check |
| `ccya/ev/prompt_context.py` | 171, 250 | Keep `pending_beat` if still needed for ruling context |
| `ccya/ev/checkers/gm_beat.py` | — | **Remove** — checker reads `storytell.gm_beat` which no longer exists |
| `ccya/ev/checkers/beat_phase_validity.py` | — | **Remove** — phase validity is now World's concern |

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

After persist completes (line ~476), add async World step:

```python
# After persist
beat_generation_in_progress = True
yield ("phase", {"phase": "beat_generation_start"})
beat_candidates = await _run_world_step(env, state, narration, scene_result, pacing_context, config, trace_id, turn_no)
beat_generation_in_progress = False
state.setdefault("meta", {})["beat_candidates"] = beat_candidates or []
```

Ruling phase change (line ~107): Unpack 5-tuple from `_call_ruling()`, set `pending_gm_beat` + `recent_beats` + cleanup `beat_candidates`.

Beat lifecycle change (line ~270): Remove Storytell beat handling entirely (moved to ruling phase).

### Ruling phase changes

**File:** `ccya/engine/ruling.py`

In `_ruling_messages()`: Add `beat_candidates` to user prompt context (read from `state.meta.beat_candidates`).

In `_call_ruling()`: Extract `selected_beat` from JSON before `IntentEnvelope` construction. Return 5-tuple.

In `_ruling_phase()`: After `_call_ruling()` returns, set `pending_gm_beat` + `recent_beats` + cleanup `beat_candidates`.

## What is unchanged

- **Ruling core logic:** Intent classification, impossibility check, difficulty adjustment, dice resolution — all unchanged.
- **Narrate:** Step 1 unchanged. Still consumes `pending_gm_beat` from previous turn.
- **Scene Extract (2a):** Unchanged. Still produces `candidate_npcs`.
- **State Extract (2b):** Unchanged. Still produces inventory/conditions/location deltas.
- **Phase Engine:** Unchanged. Still computes `scene_phase`, `convergence_score`, `PacingContext`.
- **Beat schema:** `GMBeat` model unchanged (type, effect, npc_id, driver, beat_expires_turn).
- **Beat TTL mechanics:** `beat_expires_turn = turn_no + 2` unchanged.
- **Beat null-clear behavior:** When no beat selected, `pending_gm_beat` is popped from state.
- **Thread lifecycle:** `_apply_thread_updates()`, `_apply_thread_resolutions()`, `_apply_arc_resolve()` — all unchanged.
- **Thread sanitizer:** Unchanged.
- **Persist:** Atomic writes (events.jsonl, state.yaml, chronicle.md) — unchanged.
- **EV checkers:** `gm_beat.py` removed (no longer reads storytell.gm_beat). `beat_phase_validity.py` removed (phase validity is now World's concern).

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

**Decision:** Record generates actions from narration alone. Narration describes what's in the scene — it's richer than inventory lists. Actions are grounded in narration text, not separate inventory/conditions sections.

### OQ2: Recent beats ownership

**Decision:** Ruling owns appending `recent_beats`. `recent_beats` records what beat was actually *used* in narration (the ruling-selected beat), not what World prepared. This keeps diversity guidance accurate — the history reflects what actually happened.

### OQ3: World template location

**Decision:** `world_system.j2` and `world_user.j2` in `ccya/prompts/`. Same level as all current templates. No subdirectory.

### OQ4: Ruling JSON parsing approach

**Decision:** Keep manual parsing. `selected_beat` is optional and small. Manual dict check in `_call_ruling()` after `_find_json()` extends the existing pattern without adding a new Pydantic model.

### OQ5: beat_expires_turn ownership

**Decision:** Ruling sets `beat_expires_turn = turn_no + 2` when selecting a beat. World does NOT set this field on candidates — it's relative to the turn when the beat is *used*, not when generated.

### OQ6: beat_candidates cleanup

**Decision:** Ruling always pops `beat_candidates` from `state.meta` after selection (or non-selection). Candidates never persist across turns.

### OQ7: World failure handling

**Decision:** If World's LLM call times out or returns invalid JSON, log a warning and set `beat_candidates = []`. Ruling proceeds without beat selection (no `selected_beat` in JSON).

### OQ8: malformed selected_beat handling

**Decision:** If ruling parses `IntentEnvelope` successfully but `selected_beat` is malformed (e.g., missing `type`), treat it as absent. No retry — ruling has already succeeded. The beat generation diversity guidance will simply not advance for this turn.

### OQ9: EV checkers

**Decision:** Remove `ev/checkers/gm_beat.py` and `ev/checkers/beat_phase_validity.py`. Both read `storytell.gm_beat` which no longer exists. `beat_phase_validity.py` is removed because phase validity is now World's concern, not ruling's. `gm_beat.py` is removed because beat lifecycle is no longer tracked through storytell output.

## Benefits

1. **Lower turn latency** — Record is lighter without beat generation; World runs async (~5s while player reads)
2. **Fewer errors** — Record's focused scribe role reduces error surface; no more overloaded LLM call
3. **Intent-aware beats** — Ruling selects from candidates using actual player intent, solving the disconnect problem
4. **Evenly distributed load** — Three focused steps, each with clear responsibility
5. **Better temperatures** — Record at low temp for reliability, World at medium for creativity, Ruling unchanged