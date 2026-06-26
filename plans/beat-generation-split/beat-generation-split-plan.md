# Beat Generation Split — Plan

## Purpose

Split Storytell (Step 2c) into three focused steps: Record (backward-looking scribe), World (async beat-candidate generation), and Ruling (beat selection from candidates). Removes `gm_beat` from StorytellerResult/TurnResult, removes `beat_expires_turn`, and adds an async World step after turn completion.

## Design Reference

`docs/design/beat-generation-split-design.md`

## Constraints

- Design decisions are final. This plan translates them into ordered steps.
- EV-side cleanup is deferred (OQ9). Checkers that read `gm_beat` from event JSON degrade gracefully.
- No backward compatibility for removed fields.
- Tests are suspended per AGENTS.md.

## Non-goals

- EV-side checker cleanup (deferred per OQ9 — `gm_beat.py`, `beat_phase_validity.py`, registries).
- Per-stream temperature split for Record (deferred per D1 future note).
- UI changes for beat display in the game client (turn viewer beat display is removed as cleanup, not replaced).
- Renaming `StorytellerResult` model class (kept; only `gm_beat` field removed). Variable names change but the Pydantic model name stays.
- Changing the SSE route handler (D5 route drain is already satisfied by existing `async for` loop in routes.py:309 — no code change needed).

## Solution

Remove `gm_beat` and `beat_expires_turn` from models. Create Record (Storytell minus beat generation) as new Step 2c. Add beat selection to Ruling (5-tuple return with `selected_beat`). Create World as async Step 2d running after turn completion inside the `_inflight` lock. Move sanitize off the synchronous critical path to its own end-of-turn phase before World. Clean up beat expiry logic from narrate, beat history from turn_state, and beat display from routes/tv.

## Firm decisions

1. `StorytellerResult` model is kept (not renamed); only `gm_beat` field is removed. Variable names change from `storytell_result` to `record_result` at call sites.
2. `GMBeat` is repurposed as validation schema for World candidates and Ruling's `selected_beat`. `beat_expires_turn` field removed from `GMBeat`.
3. Ruling always replaces or pops `pending_gm_beat` each turn — no expiry arithmetic needed.
4. World runs after `yield("complete")` but BEFORE the `finally` that releases `_inflight`. Requires restructuring turn.py's try/finally (see Step 4.4).
5. Sanitize and World are two separate end-of-turn phases. Single `save_state` after both.
6. SSE route already drains the generator via `async for` — no route change needed (D5 already satisfied).

## Risks, Ambiguities, and Blockers

- **Try/finally restructure complexity (Step 4.4).** Moving World inside the try block before `finally` changes the error-handling flow. World failures must not prevent the lock from releasing. The plan specifies a try/except wrapper around the post-complete block.
- **World prompt fidelity.** D2 allocates ~200-250 system tokens but the current beat logic in `storytell_system.j2:77-117` exceeds that. The executor must decide which instructions to keep vs. cut. The plan lists what to include but doesn't prescribe exact wording.
- **`selected_beat` extraction from ruling JSON.** Using `j.pop("selected_beat", None)` before `IntentEnvelope(**j)` avoids relying on Pydantic's default extra-ignore behavior. If `IntentEnvelope` adds `model_config = {"extra": "forbid"}` in the future, the pop approach is safe.

## Phase Summary

6 phases, ordered by dependency:

1. **Model & Config Foundation** — GMBeat/StorytellerResult/TurnResult/EngineConfig changes
2. **Record Step** — New record.py + templates, pipeline swap from storytell to record
3. **Ruling Beat Selection** — 5-tuple return, selected_beat extraction, pending_gm_beat/recent_beats management
4. **World Step + Turn Orchestration** — New world.py + templates, turn.py end-of-turn phases
5. **Cleanup** — narrate.py expiry removal, routes.py/tv.py/turn_state.py gm_beat removal
6. **Documentation** — Architecture docs, repomap updates

---

## Phase 1: Model & Config Foundation

### Context files to load
- `ccya/models/extraction.py` — GMBeat, StorytellerResult models
- `ccya/models/config.py` — TurnResult dataclass
- `ccya/engine/config.py` — EngineConfig dataclass, build_engine_config

### Steps

#### 1.1 — Remove `beat_expires_turn` from GMBeat

**File:** `ccya/models/extraction.py:215`

**What:** Delete the `beat_expires_turn: int | None = None` field from `GMBeat`. Keep `type`, `effect`, `npc_id`, `driver` fields and both `_coerce_gm_beat_type`/`_coerce_gm_beat_driver` validators.

**Why:** TTL removed entirely. Ruling's per-turn always-replace-or-pop makes expiry vestigial (D1/D3/OQ5).

**Validation:** `grep "beat_expires_turn" ccya/models/extraction.py` returns 0 matches.

#### 1.2 — Remove `gm_beat` from StorytellerResult

**File:** `ccya/models/extraction.py:232`

**What:** Delete `gm_beat: GMBeat | None = None` field from `StorytellerResult`.

**Why:** Beat generation moves out of Storytell/Record. `GMBeat` is repurposed for World candidates and Ruling's `selected_beat` (D1).

**Validation:** `grep "gm_beat" ccya/models/extraction.py` returns 0 matches.

#### 1.3 — Remove `_nullify_invalid_gm_beat` validator

**File:** `ccya/models/extraction.py:254-259`

**What:** Delete the `_nullify_invalid_gm_beat` model_validator method from `StorytellerResult`. Its logic moves inline into Ruling's `if beat and beat.type:` check (D3).

**Why:** `StorytellerResult` no longer carries `gm_beat`. The validator references a nonexistent field.

**Validation:** `grep "_nullify_invalid_gm_beat" ccya/models/extraction.py` returns 0 matches.

#### 1.4 — Remove `gm_beat` from TurnResult

**File:** `ccya/models/config.py:43`

**What:** Delete `gm_beat: dict[str, str] | None = None` from the `TurnResult` dataclass.

**Why:** Beat is no longer produced by the extraction pipeline. Beat lifecycle moves to ruling phase (D3).

**Validation:** `grep "gm_beat" ccya/models/config.py` returns 0 matches.

#### 1.5 — Add `world_temperature` to EngineConfig

**File:** `ccya/engine/config.py`

**What:** Add `world_temperature: float = 0.55` field to `EngineConfig` dataclass (after `extract_temperature`). Add `world_temperature=float(game.get("world_temperature", 0.55))` to `build_engine_config`.

**Why:** World step needs its own temperature for constrained creative generation (D2).

**Validation:** `grep "world_temperature" ccya/engine/config.py` shows field definition + build mapping.

---

## Phase 2: Record Step

### Context files to load
- `ccya/engine/extraction/storytell.py` — current Storytell message building
- `ccya/engine/extraction/pipeline.py` — extraction pipeline orchestration
- `ccya/engine/extraction/utils.py` — `_call_stream` shared utility
- `ccya/prompts/storytell_system.j2` — current system template
- `ccya/prompts/storytell_user.j2` — current user template

### Dependencies
- Phase 1 (StorytellerResult.gm_beat removed)

### Steps

#### 2.1 — Create `record_system.j2`

**File:** `ccya/prompts/record_system.j2` (new)

**What:** Copy `storytell_system.j2` and remove the entire `## GM Beat` section (lines 77-117, ~40 lines). Remove `"gm_beat"` from the JSON schema block (line 16). Keep all thread, arc, outcome_summary, actions, and Curtain Call sections unchanged.

**Why:** Record is Storytell minus beat generation (D1).

**Validation:** `grep -c "gm_beat\|GM Beat\|beat" ccya/prompts/record_system.j2` returns 0. Template renders without error via `ev.py prompt-eval dump`.

#### 2.2 — Create `record_user.j2`

**File:** `ccya/prompts/record_user.j2` (new)

**What:** Copy `storytell_user.j2` and remove these sections:
- `{% include "sections/_inventory.j2" %}` (line 4)
- `{% include "sections/_conditions.j2" %}` (line 6)
- `{% include "sections/_npc_roster.j2" %}` (line 8)
- `## Scene Input` / candidate_npcs block (lines 10-21)
- `{% include "sections/_location.j2" %}` (line 23)
- `## pacing_context` block (lines 43-47)
- `## Scene phase` / allowed_beat_types block (lines 49-51)
- `## GM Beat` / pending_beat block (lines 55-65)
- `## Recent Beats` block (lines 66-71)
- `## player_intent` block (lines 83-86)
- `## REMINDER: gm_beat.type` block (lines 90-92)

Keep: `_arc.j2`, threads, world_state, `_recent_turns.j2`, `prior_history`, `rules_outcome` (band), Curtain Call, narration block.

**Why:** Record drops forward-looking and beat-related inputs (D1). Keeps narration, threads, arc, recent_turns, prior_history, band.

**Validation:** Template renders without error. No references to `candidate_npcs`, `pending_beat`, `recent_beats`, `allowed_beat_types`, `intent`, `pacing_context`, `inventory`, `conditions`, `npc_roster`.

#### 2.3 — Create `ccya/engine/extraction/record.py`

**File:** `ccya/engine/extraction/record.py` (new)

**What:** Create `_record_messages()` function based on `_storytell_messages()` from `storytell.py`. Signature:

```python
def _record_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    extraction_ctx: _ExtractionContext,
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    band: str = "",
    arc_ttl: int = 3,
    config: EngineConfig | None = None,
) -> list[dict[str, str]]:
```

Differences from `_storytell_messages`:
- Remove parameters: `intent`, `pacing_context`
- System template: `record_system.j2` (no `recent_beats` context variable needed)
- User template: `record_user.j2`
- Remove from user context: `npc_roster`, `candidate_npcs`, `location`, `inventory`, `conditions`, `intent`, `pacing_context`, `pending_beat`, `recent_beats`, `allowed_beat_types`, `scene_phase`, `curtain_call` (keep if needed for thread context), `arc_pressure_score`, `arc_hint_text`
- Keep in user context: `narration`, `current_objective` (arc), `all_threads`, `world_state`, `resolved_arcs`, `recent_turns`, `prior_history`, `turn_no`, `band`, `pc_name`
- Remove imports: `derive_allowed_beat_types`, `build_npc_roster`, `compute_arc_pressure_score`, `ARCHETYPES`
- Keep imports: `_ExtractionContext`, `_filter_evicted_threads`, `_get_resolved_arcs`, `_fmt_progress`, `_filter_completed_threads`, `_render`

**Why:** Record message building is Storytell minus beat-related inputs (D1).

**Validation:** `python -c "from ccya.engine.extraction.record import _record_messages"` imports without error.

#### 2.4 — Swap pipeline from Storytell to Record

**File:** `ccya/engine/extraction/pipeline.py`

**What:**
1. Replace `from ccya.engine.extraction.storytell import _storytell_messages` with `from ccya.engine.extraction.record import _record_messages`
2. Replace `_storytell_messages(...)` call (~line 201) with `_record_messages(...)` using trimmed parameters (no `intent`, no `pacing_context`)
3. Replace `StorytellerResult` references with `RecordResult` — but since `StorytellerResult` still has the right fields (minus `gm_beat`), rename is optional. **Decision:** Keep using `StorytellerResult` model for now (it has the right fields after Phase 1 removes `gm_beat`). Rename the variable references from `storytell_result` to `record_result` and `storytell_msgs` to `record_msgs` etc. for clarity. Update log messages from `storytell` to `record`. Update extraction_event key from `"storytell"` to `"record"`.
4. Remove the beat retry logic block (lines 225-261): the `if storytell_result.gm_beat and storytell_result.gm_beat.npc_id and not storytell_result.gm_beat.effect:` block and its retry. This validation is no longer needed since Record produces no beats.
5. Remove `gm_beat=%s` from debug log (line 315).
6. Remove NOTE comment about gm_beat (lines 383-385).
7. Update `_SKIPPED` references and stream key from `"storytell"` to `"record"` in metrics/phase events.
8. Update `turn.py` metrics rollup tuples that reference `"storytell"` as a stream key: lines 289, 293, 297, 312, 316, 457 — change `"storytell"` to `"record"` in each `("scene", "state", "storytell", ...)` tuple. Without this, metrics will silently report zeros for the record stream.
9. Update `ccya/engine/extraction/__init__.py` docstring: change `"storytell"` to `"record"`.

**Why:** Pipeline must call Record instead of Storytell. Beat retry logic is dead code without `gm_beat`. Metrics rollup keys must match the new extraction_event key.

**Validation:** `grep '"storytell"' ccya/engine/extraction/pipeline.py ccya/engine/turn.py` returns 0 matches. Pipeline runs end-to-end via `ev.py play --turns 1`.

#### 2.5 — Keep `storytell.py` as dead file (or delete)

**File:** `ccya/engine/extraction/storytell.py`

**What:** Delete `storytell.py`. Record replaces it entirely.

**Why:** No remaining references after pipeline swap.

**Validation:** `grep -r "from ccya.engine.extraction.storytell" ccya/` returns 0 matches.

---

## Phase 3: Ruling Beat Selection

### Context files to load
- `ccya/engine/ruling.py` — `_call_ruling`, `_ruling_phase`, `_ruling_messages`
- `ccya/prompts/ruling_system.j2` — ruling system template
- `ccya/prompts/ruling_user.j2` — ruling user template
- `ccya/models/extraction.py` — GMBeat model (for validation)

### Dependencies
- Phase 1 (GMBeat repurposed, beat_expires_turn removed)

### Steps

#### 3.1 — Add beat selection instructions to `ruling_system.j2`

**File:** `ccya/prompts/ruling_system.j2`

**What:** Append ~5 lines before the final "Omit empty fields" line:

```
## Beat Selection

The world has prepared 2-3 candidate beats for the next turn. Choose the one that best fits the player's intent and the current narration.

- `beat_candidates` is provided in the user prompt (variable data).
- Pick ONE beat that meshes with the player's intent.
- If no beat fits well, omit `selected_beat` (emit null).
```

Also add `"selected_beat": {"type": "...", "effect": "...", "npc_id": "...", "driver": "..."}` to the JSON schema block (as an optional field).

**Why:** Ruling needs instructions to select from beat candidates (D3).

**Validation:** Template renders. `grep -c "Beat Selection" ccya/prompts/ruling_system.j2` returns 1.

#### 3.2 — Add beat_candidates section to `ruling_user.j2`

**File:** `ccya/prompts/ruling_user.j2`

**What:** Add before `## Current Turn`:

```
{% if beat_candidates %}
## Beat Candidates
{% for b in beat_candidates %}- **{{ b.type }}**: {{ b.effect }}{% if b.npc_id %} (NPC: {{ b.npc_id }}){% endif %}

{% endfor %}
{% else %}
## Beat Candidates
No beat candidates prepared.
{% endif %}
```

**Why:** Ruling needs to see the candidates in its user prompt (D3).

**Validation:** Template renders with both empty and populated `beat_candidates`.

#### 3.3 — Update `_ruling_messages` to pass beat_candidates

**File:** `ccya/engine/ruling.py:26-74`

**What:** Add `beat_candidates: list[dict[str, Any]] | None = None` parameter to `_ruling_messages`. Pass it to the `ruling_user.j2` render context.

In `_ruling_phase` (~line 214), read `beat_candidates` from `state.meta.beat_candidates` and pass to `_ruling_messages`:

```python
beat_candidates = (state.get("meta") or {}).get("beat_candidates") or []
ruling_messages = _ruling_messages(
    ctx._env, state, ctx.user_input,
    turn_no=turn_no,
    npc_roster=...,
    inventory=...,
    recent_turns=...,
    scene_phase=...,
    beat_candidates=beat_candidates,
)
```

**Why:** Ruling must receive beat candidates from state (D3).

**Validation:** `_ruling_messages` accepts and passes `beat_candidates`.

#### 3.4 — Extend `_call_ruling` return to 5-tuple

**File:** `ccya/engine/ruling.py:77-158`

**What:** Change return type from `tuple[IntentEnvelope, dict[str, int], str, str]` to `tuple[IntentEnvelope, dict[str, int], str, str, dict[str, Any] | None]`.

After `_find_json(cleaned)` succeeds (~line 124), extract `selected_beat` before `IntentEnvelope` construction:

```python
j = _find_json(cleaned)
if j is None:
    raise ValueError("No JSON found in ruling response")
selected_beat = j.pop("selected_beat", None)  # pop before IntentEnvelope to avoid extra-key reliance
intent = IntentEnvelope(**j)
```

Return `selected_beat` as 5th element. On failure path (line 158), return `None` as 5th element.

**Why:** Ruling outputs `selected_beat` alongside intent JSON (D3/D6). Using `j.pop` ensures `IntentEnvelope` doesn't see the extra key (review ambiguity: explicit pop vs. relying on Pydantic extra-ignore default).

**Validation:** `_call_ruling` returns 5-tuple. `grep "selected_beat" ccya/engine/ruling.py` shows extraction + return.

#### 3.5 — Update `_ruling_phase` to handle beat selection

**File:** `ccya/engine/ruling.py:200-343`

**What:** After `_call_ruling` returns (~line 234), unpack 5-tuple and handle beat lifecycle:

```python
intent, ruling_usage, ruling_raw_response, ruling_parse_error, selected_beat = await _call_ruling(
    ruling_messages, config, trace_id,
)

beat = None
if selected_beat:
    try:
        beat = GMBeat(**selected_beat)
    except ValidationError:
        beat = None

if beat and beat.type:
    beat_dict = beat.model_dump(exclude_none=True)
    state.setdefault("meta", {})["pending_gm_beat"] = beat_dict
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
    state.get("meta", {}).pop("pending_gm_beat", None)

# Always discard candidates
state.get("meta", {}).pop("beat_candidates", None)
```

Add imports: `from ccya.models.extraction import GMBeat`, `from pydantic import ValidationError`.

**Why:** Ruling owns pending_gm_beat + recent_beats + beat_candidates cleanup (D3/OQ2/OQ6).

**Validation:** After ruling phase, `state.meta` has `pending_gm_beat` set or popped, `recent_beats` appended (if selected), `beat_candidates` removed.

---

## Phase 4: World Step + Turn Orchestration

### Context files to load
- `ccya/engine/turn.py` — run_turn orchestrator
- `ccya/engine/thread_sanitizer.py` — sanitize_threads
- `ccya/engine/_pacing.py` — derive_allowed_beat_types
- `ccya/engine/extraction/context.py` — _ExtractionContext (for candidate_npcs)
- `ccya/engine/npc_roster.py` — not needed (World uses candidate_npcs directly)

### Dependencies
- Phase 1 (GMBeat for validation, world_temperature config)
- Phase 3 (ruling sets pending_gm_beat, so turn.py no longer needs beat lifecycle)

### Steps

#### 4.1 — Create `world_system.j2`

**File:** `ccya/prompts/world_system.j2` (new)

**What:** New template. ~40-50 lines. Contains:
- Beat schema (type, effect, npc_id, driver) — emit a JSON array of 2-3 candidates
- Generation rules: blend candidate_npcs psychological hints, prefer NPC-driven beats
- Beat flavor by driver (motivation/fear/leverage/bond/personality) — same mapping as current storytell_system.j2 lines 98-104
- Diversity: don't repeat same type more than twice consecutively (use `recent_beats` for history)
- Phase-beat alignment: use `allowed_beat_types` constraint
- Action rule: every beat must show NPC/world taking action
- Roll band guidance (same as current lines 109-113)

**Why:** World needs its own system prompt for beat candidate generation (D2).

**Validation:** Template renders. `grep -c "candidate" ccya/prompts/world_system.j2` > 0.

#### 4.2 — Create `world_user.j2`

**File:** `ccya/prompts/world_user.j2` (new)

**What:** New template. ~40-50 lines. Contains:
- `candidate_npcs` section (from Scene Extract)
- Thread urgency counts (active/urgent thread summaries)
- `pacing_context` (directive, outcome_hint, scene_phase)
- `recent_beats` (beat history for diversity)
- `allowed_beat_types` (phase-derived constraints)
- `narration` (full narration from Step 1)

**Why:** World needs these inputs for beat candidate generation (D2).

**Validation:** Template renders with all variables populated.

#### 4.3 — Create `ccya/engine/world.py`

**File:** `ccya/engine/world.py` (new)

**What:** New module with `_run_world_step()` async function. Signature:

```python
async def _run_world_step(
    env: Environment,
    state: dict[str, Any],
    narration: str,
    scene_result: Any,
    pacing_context: Any | None,
    config: EngineConfig,
    trace_id: str,
    turn_no: int,
) -> list[dict[str, Any]]:
```

Implementation:
1. Build messages using `_render(env, "world_system.j2", {...})` and `_render(env, "world_user.j2", {...})` with inputs from D2
2. Call `llm_chat()` with `temperature=config.world_temperature`
3. Parse JSON response (list of 2-3 candidate dicts)
4. Validate each candidate via `GMBeat(**candidate)`; drop invalid candidates (no retry)
5. Return `[beat.model_dump(exclude_none=True) for beat in valid_beats]`
6. On any failure (timeout, parse error, invalid JSON): log warning, return `[]`

Inputs sourced from:
- `candidate_npcs`: from `scene_result.candidate_npcs` (`SceneExtractResult.candidate_npcs` — `list[dict]`, max 3 entries). `scene_result` is passed as a parameter.
- `arc.threads[]`: from `state["arc"]["threads"]`
- `narration`: passed in
- `pacing_context`: passed in
- `recent_beats`: from `state.meta.recent_beats`
- `allowed_beat_types`: from `derive_allowed_beat_types(scene_phase, directive, spiral_detected)`

**Why:** World is the new async beat-candidate generation step (D2).

**Validation:** `python -c "from ccya.engine.world import _run_world_step"` imports. Function returns `list[dict]` on success and `[]` on failure.

#### 4.4 — Restructure try/finally and add end-of-turn phases to `turn.py`

**File:** `ccya/engine/turn.py`

**What:** This step has two parts: (A) restructure the try/finally so the lock stays held through World, and (B) add the Sanitize + World phases.

**Problem:** Currently the synchronous `sanitize_threads` runs at lines 487-497 (before persist at 500-502). The plan moves sanitize + World to after persist but before `yield("complete")`. The `finally` at lines 565-567 releases `_inflight` immediately after `yield("complete")` resumes — so World must be INSIDE the try block, before `yield("complete")`, to keep the lock held.

**Insertion point:** After the persist block (`save_state(save_dir, state)` at line 502) and BEFORE `TurnResult` construction (line 504). The existing sanitize block at lines 487-497 is deleted (Step 4.5).

**Fix (A):** Move the World/Sanitize block INSIDE the try, BEFORE `yield("complete")`. The generator flow becomes:

```
try:
    ... all existing pipeline code ...
    # End-of-turn async window (lock still held)
    yield ("phase", {"phase": "sanitize_start"})
    ... sanitize ...
    yield ("phase", {"phase": "sanitize_done"})
    yield ("phase", {"phase": "world_start"})
    ... world ...
    save_state(...)
    yield ("phase", {"phase": "world_done"})
    yield ("complete", result_obj)    # ← UI sees narration AFTER world completes
    # fall through to end of try → finally releases lock
except ...
finally:
    await _inflight.release(...)
```

The SSE route's `async for` loop (routes.py:309) receives phase events during World (informational), then receives `complete` (UI shows narration), then the generator returns → `StopAsyncIteration` → `finally` releases lock. The lock is held for the entire World window.

**Fix (B):** After the persist block (after `event["last_turn_state"] = state` / `append_event` / `save_state` at lines 500-502) and BEFORE `TurnResult` construction (line 504), insert:

```python
# --- End-of-turn async window (lock held) ---
# 1. Sanitize (moved from synchronous critical path)
yield ("phase", {"phase": "sanitize_start"})
if config.sanitize_every > 0:
    state, _ = await sanitize_threads(save_dir, state, config, trace_id=trace_id)
yield ("phase", {"phase": "sanitize_done"})

# 2. World (beat candidates — receives same live `state` Sanitize just mutated)
yield ("phase", {"phase": "world_start"})
try:
    beat_candidates = await _run_world_step(
        env, state, narrative, scene_result, _pc, config, trace_id, turn_no,
    )
except Exception as exc:
    _log.warning("world step failed: %s", exc, extra={"trace_id": trace_id})
    beat_candidates = []
state.setdefault("meta", {})["beat_candidates"] = beat_candidates or []
save_state(save_dir, state)  # single persist of sanitize + candidates
yield ("phase", {"phase": "world_done"})
```

**Variable scope at insertion point** (all defined earlier in the same try block):
- `env` (line 75), `state` (line 80), `save_dir` (parameter), `config` (parameter)
- `narrative` (line 197), `scene_result` (line 268), `_pc` (line 153)
- `trace_id` (line 77), `turn_no` (line 120)

Add import: `from ccya.engine.world import _run_world_step`.

**Stale-input invariant:** World receives the same live `state` Python reference Sanitize just mutated. No reload, no snapshot, no intermediate `save_state`.

**Why:** World runs async after turn completion, gated by `_inflight` (D5/D8). Single end-of-turn `save_state` persists both sanitizer edits and beat candidates. The try/finally restructure ensures the lock stays held.

**Validation:** After turn completes, `state.meta.beat_candidates` contains 0-3 candidate dicts. Next turn's ruling reads them. `_inflight` lock is held during World (verify: submitting during World window returns "Turn already in progress").

#### 4.5 — Remove synchronous sanitize from critical path

**File:** `ccya/engine/turn.py:487-497`

**What:** Delete the synchronous `sanitize_threads` block (lines 487-497). It now runs as the first end-of-turn async phase (Step 4.4).

**Why:** Sanitize moves off the synchronous critical path (D8).

**Validation:** `grep -n "sanitize_threads" ccya/engine/turn.py` shows only the end-of-turn call (after persist, before `yield("complete")`).

#### 4.6 — Remove beat lifecycle from turn.py

**File:** `ccya/engine/turn.py:269-279`

**What:** Delete the beat lifecycle block:

```python
# Beat lifecycle: beat_disposition removed — ...
_new_beat = storyteller_result.gm_beat if storyteller_result else None
if _new_beat and _new_beat.type:
    _beat_dict = _new_beat.model_dump(exclude_none=True)
    _beat_dict["beat_expires_turn"] = turn_no + 2
    state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict
else:
    state.get("meta", {}).pop("pending_gm_beat", None)
```

**Why:** Beat lifecycle moved to ruling phase (D3). `storyteller_result` (now `record_result`) no longer has `gm_beat`.

**Validation:** `grep "beat_expires_turn\|_new_beat\|storyteller_result.gm_beat" ccya/engine/turn.py` returns 0 matches.

#### 4.7 — Remove `gm_beat` from TurnResult construction

**File:** `ccya/engine/turn.py:518-521`

**What:** Remove the `gm_beat={...}` argument from `TurnResult(...)` construction.

**Why:** `TurnResult.gm_beat` removed in Phase 1 (Step 1.4).

**Validation:** `grep "gm_beat" ccya/engine/turn.py` returns 0 matches.

#### 4.8 — Update extraction pipeline return variable names

**File:** `ccya/engine/turn.py:268`

**What:** Update the unpack from `_extract_result` (line 268) to use `record_result` instead of `storyteller_result`. Update ALL downstream references to `storyteller_result` in turn.py:
- Line 230: initialization `storyteller_result = None` → `record_result = None`
- Line 268: unpack variable name
- Line 335: `_apply_state_updates(state, delta, storyteller_result, ...)` → `record_result`
- Lines 519-521: `gm_beat` construction (removed entirely in Step 4.7)

Note: `_apply_state_updates` in `turn_state.py` keeps its parameter name `storyteller_result` (it's a local parameter name, not a contract). Only the call-site variable in turn.py changes.

**Why:** Consistency with Phase 2 rename.

**Validation:** `grep "storyteller_result" ccya/engine/turn.py` returns 0 matches.

---

## Phase 5: Cleanup

### Context files to load
- `ccya/engine/narrate.py` — beat expiry check
- `ccya/server/routes.py` — SSE turn route, gm_beat in turn_complete
- `ccya/server/tv.py` — turn viewer beat display
- `ccya/templates/_turn_viewer.html` — beat display HTML
- `ccya/engine/turn_state.py` — beat history append

### Dependencies
- Phase 1 (fields removed from models)
- Phase 3 (ruling owns beat lifecycle)

### Steps

#### 5.1 — Remove beat expiry check from narrate.py

**File:** `ccya/engine/narrate.py:169-174`

**What:** Replace the expiry check block:

```python
_pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")
if _pending_gm_beat:
    _expires = _pending_gm_beat.get("beat_expires_turn")
    if _expires is not None and turn_no > _expires:
        _pending_gm_beat = None
        state.setdefault("meta", {})["pending_gm_beat"] = None
```

With:

```python
_pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")
```

Narrate becomes a pure reader of `pending_gm_beat` — no mutation.

**Why:** `beat_expires_turn` removed. Narrate no longer owns beat lifecycle (D1/OQ5).

**Validation:** `grep "beat_expires_turn" ccya/engine/narrate.py` returns 0 matches. Narrate still reads `pending_gm_beat` for prompt context.

#### 5.2 — Remove `gm_beat` from routes.py turn_complete event

**File:** `ccya/server/routes.py:384`

**What:** Delete `"gm_beat": result.gm_beat,` from the turn_complete SSE event payload.

**Why:** `TurnResult.gm_beat` removed.

**Validation:** `grep "gm_beat" ccya/server/routes.py` returns 0 matches.

#### 5.3 — Remove beat display from tv.py

**File:** `ccya/server/tv.py:546-594`

**What:** Remove the `gm_beat_dict` extraction block (lines 546-551) and the `gm_beat_type`, `gm_beat_effect`, `gm_beat_allowed_beat_types` keys from the row dict (lines 592-594). Replace with `selected_beat` extraction from ruling event data if desired, or remove entirely (EV follow-up per OQ9).

**Decision:** Remove beat display entirely. The new `selected_beat` lifecycle is tracked via `state.meta.pending_gm_beat` and `state.meta.beat_candidates`, not via extraction event output. A successor checker/display will come in the EV follow-up.

**Why:** `gm_beat` no longer exists in storytell extraction output.

**Validation:** `grep "gm_beat" ccya/server/tv.py` returns 0 matches.

#### 5.4 — Remove beat display HTML from turn viewer

**File:** `ccya/templates/_turn_viewer.html:288-310`

**What:** Remove the `<template x-if="t.gm_beat_type || t.gm_beat_effect || t.gm_beat_allowed_beat_types">` block and its contents.

**Why:** Beat display data no longer produced by tv.py.

**Validation:** `grep "gm_beat" ccya/templates/_turn_viewer.html` returns 0 matches.

#### 5.5 — Remove beat history append from turn_state.py

**File:** `ccya/engine/turn_state.py:475-486`

**What:** Delete the beat history block:

```python
_history_beat = state.get("meta", {}).get("pending_gm_beat")
meta = state.setdefault("meta", {})
meta.setdefault("recent_beats", []).append({
    "turn": turn_no,
    "type": _history_beat.get("type") if _history_beat else None,
    "effect": _history_beat.get("effect") if _history_beat else None,
})
max_beats = config.recent_beats_max if config else 5
if len(meta["recent_beats"]) > max_beats:
    meta["recent_beats"] = meta["recent_beats"][-max_beats:]
```

**Why:** `recent_beats` ownership moved to ruling phase (D3/OQ2). turn_state.py no longer appends beat history.

**Validation:** `grep "recent_beats" ccya/engine/turn_state.py` returns 0 matches.

---

## Phase 6: Documentation

### Dependencies
- All previous phases complete

### Steps

#### 6.1 — Update architecture docs

**Files:** `docs/architecture/OVERVIEW.md`, `docs/architecture/step2c-storytell.md`

**What:**
- `OVERVIEW.md`: Update pipeline diagram to show Record (not Storytell) as Step 2c, add Step 2d World (async). Update data flow description.
- `step2c-storytell.md`: Rename to `step2c-record.md` or update content to describe Record. Document that beat generation moved to World (Step 2d) and beat selection moved to Ruling (Step 0).

**Why:** Pipeline changed. Docs must reflect new architecture.

**Validation:** Pipeline diagram matches implementation. No references to `storytell` as a pipeline step.

#### 6.2 — Update repomap

**File:** `docs/repomap.md`

**What:**
- Update `ccya/engine/extraction/` entry: replace "storytell" with "record" in description
- Add `ccya/engine/world.py` entry: "World: async beat-candidate generation (Step 2d)"
- Update `ccya/engine/turn.py` entry: mention end-of-turn async phases (Sanitize + World)
- Update `ccya/engine/ruling.py` entry: mention beat selection
- Update pipeline entry: "5-call pipeline" → "Record + World pipeline" or similar

**Why:** Module boundaries changed.

**Validation:** All new/renamed modules listed. Signposts accurate.

#### 6.3 — Update AGENTS.md if needed

**File:** `AGENTS.md`

**What:** Update any references to Storytell/beat generation if present. Add signpost to `step2c-record.md` and World step if relevant.

**Why:** Conventions may reference old step names.

**Validation:** `grep -i "storytell" AGENTS.md` returns 0 matches (or only historical references).

---

## Verification

After all phases:
1. `make check` passes (lint + typecheck)
2. `ev.py play --turns 3` runs without errors — produces narration, actions, and `state.meta.beat_candidates` after each turn
3. `state.meta.pending_gm_beat` is set/popped correctly by ruling each turn
4. No references to `gm_beat` in pipeline code (EV deferred per OQ9)
5. No references to `beat_expires_turn` anywhere in engine code
