# Simplify Beat Pipeline — Plan

## Status: completed

## Purpose

Remove dead fields (`npc_id`, `driver`) from the beat pipeline and switch to index-based beat selection. The beat lifecycle works end-to-end; this eliminates over-specified data passing between stages.

## Design Reference

`roadmap/bugs/beat-candidates-disconnect.md` — "Follow-up: Simplify Beat Pipeline (Post-Merge)" section

## Decisions (already made)

1. **Index-based selection.** Ruling picks index 0/1/2 into beat_candidates. Not full object matching.
2. **Remove `npc_id` and `driver` from GMBeat entirely.** Not just stop populating — delete from model.
3. **Scene unchanged.** Still produces `[{id, type, effect}]`. World reads `id` to identify NPC but just passes `type` + `effect` downstream.
4. **Narrate unchanged.** Already just reads `pending_beat.effect`.
5. **0-based indexing.** Matches Python convention and world's list output.

## Non-goals

- Changing scene extraction (still produces `id` + `type` + `effect`)
- Changing world's candidate generation logic (still reads `candidate_npcs`, still produces 2-3 candidates)
- Changing diversity enforcement (already fixed in world_system.j2)
- Changing ruling's intent/checking logic (only beat selection changes)
- Changing record step (no beat involvement)

## Phase Summary

3 phases, ordered by dependency:

1. **Model cleanup** — Remove `npc_id` and `driver` from GMBeat model, remove driver validator
2. **World + Ruling prompts and code** — Simplify world to just type+effect, switch ruling to index-based selection
3. **Checker updates** — Update llm_checkers to drop npc_id/driver references

---

## Phase 1: Model Cleanup

### Context files to load
- `ccya/models/extraction.py` — GMBeat model definition (lines 181-225)

### Steps

#### 1.1 — Remove `npc_id` and `driver` from GMBeat

**File:** `ccya/models/extraction.py:181-225`

**What:** Delete these fields and the driver validator from `GMBeat`:
- `npc_id: str | None = None` (line 213)
- `driver: Literal["motivation", "fear", "leverage", "bond", "personality"] | None = None` (line 214)
- `_coerce_gm_beat_driver` method (lines 216-224)

Keep: `type`, `effect`, `_coerce_gm_beat_type`.

**Why:** `npc_id` and `driver` are never used downstream. World just passes `type` + `effect`. Ruling just picks by index. Narrate just reads `effect`. Record just reads `type` + `effect`.

**Validation:** `grep "npc_id\|_coerce_gm_beat_driver" ccya/models/extraction.py` returns 0 matches for `npc_id` and `_coerce_gm_beat_driver` (type coercion stays).

---

## Phase 2: World + Ruling Prompts and Code

### Context files to load
- `ccya/prompts/world_system.j2` — world system template
- `ccya/prompts/ruling_system.j2` — ruling system template
- `ccya/prompts/ruling_user.j2` — ruling user template
- `ccya/engine/world.py` — world step function
- `ccya/engine/ruling.py` — ruling phase function

### Dependencies
- Phase 1 (GMBeat model simplified)

### Steps

#### 2.1 — Simplify `world_system.j2` schema and rules

**File:** `ccya/prompts/world_system.j2`

**What:**
1. Schema block (lines 7-11): Change from `{"type": "...", "effect": "...", "npc_id": "...", "driver": "..."}` to just `{"type": "...", "effect": "..."}`
2. Generation rules (lines 15-21): Remove driver instruction (line 19: "Set `driver` to the psychological field..."). Remove "Blend, don't pick" instruction's reference to driver types — keep just the concept of combining psychological hints.
3. Diversity section (line 28): Remove "Vary drivers across candidates" — just keep "pick types that are NOT in the last 2 entries of `recent_beats`."

**Why:** World just produces `type` + `effect`. No driver or npc_id to instruct.

**Validation:** Template renders. No references to `driver` or `npc_id` in world_system.j2.

#### 2.2 — Simplify `ruling_system.j2` schema and beat selection

**File:** `ccya/prompts/ruling_system.j2`

**What:**
1. Schema block (lines 72): Change `"selected_beat": {"type": "...", "effect": "...", "npc_id": "...", "driver": "..."}` to just `"selected_beat": 0`
2. Beat Selection section (lines 87-95): Replace with index-based instructions:

```
## Beat Selection

The world has prepared 2-3 candidate beats for the next turn. Choose ONE by index.

- `beat_candidates` is provided in the user prompt (variable data).
- Pick ONE beat by its index (0-based): `0`, `1`, or `2`.
- If no beat fits well, omit `selected_beat` (emit null).
```

Remove lines 94-95 (the `selected_beat` must include all four fields + driver constraint lines).

**Why:** Ruling just picks an index. No full object to construct.

**Validation:** Template renders. Schema shows `selected_beat: 0`. Beat selection section has index instructions only.

#### 2.3 — Simplify `ruling_user.j2` beat candidates display

**File:** `ccya/prompts/ruling_user.j2:25-32`

**What:** Change beat candidates section from:
```
{% for b in beat_candidates %}- **{{ b.type }}**: {{ b.effect }}{% if b.npc_id %} (NPC: {{ b.npc_id }}){% endif %}
{% endfor %}
```
To:
```
{% for b in beat_candidates %}{{ loop.index0 }}. **{{ b.type }}** — {{ b.effect }}
{% endfor %}
```

**Why:** Numbered list with 0-based indices matches ruling's index-based selection. No npc_id to display.

**Validation:** Template renders with both empty and populated `beat_candidates`. Shows `0. type — effect`, `1. type — effect`, etc.

#### 2.4 — Simplify `ruling.py` beat lifecycle code

**File:** `ccya/engine/ruling.py:250-275`

**What:** Replace the beat lifecycle block (lines 252-275) with index-based logic:

```python
# Beat lifecycle: index-based selection from beat_candidates
beat_candidates = (state.get("meta") or {}).get("beat_candidates") or []
beat: dict[str, Any] | None = None
if selected_beat is not None and isinstance(selected_beat, int) and 0 <= selected_beat < len(beat_candidates):
    beat = beat_candidates[selected_beat]

if beat and beat.get("type"):
    state.setdefault("meta", {})["pending_gm_beat"] = {
        "type": beat["type"],
        "effect": beat.get("effect", ""),
    }
    meta = state.setdefault("meta", {})
    meta.setdefault("recent_beats", []).append({
        "turn": turn_no,
        "type": beat["type"],
        "effect": beat.get("effect", ""),
    })
    max_beats = config.recent_beats_max or 5
    if len(meta["recent_beats"]) > max_beats:
        meta["recent_beats"] = meta["recent_beats"][-max_beats:]
else:
    state.get("meta", {}).pop("pending_gm_beat", None)

# Always discard candidates
state.get("meta", {}).pop("beat_candidates", None)
```

Remove: `from ccya.models.extraction import GMBeat` import (no longer needed for beat validation). Remove: `from pydantic import ValidationError` import (no longer needed).

**Why:** Index lookup instead of full object construction. Just stores `type` + `effect` as `pending_gm_beat`.

**Validation:** After ruling phase, `state.meta.pending_gm_beat` has just `{type, effect}`. `recent_beats` appended with just `{turn, type, effect}`.

#### 2.5 — Simplify `world.py` output

**File:** `ccya/engine/world.py:130-145`

**What:** After validating candidates via `GMBeat(**entry)` (line 135), strip `npc_id` and `driver` from the output. Change line 140 from:
```python
valid_beats.append(beat.model_dump(exclude_none=True))
```
To:
```python
valid_beats.append({"type": beat.type, "effect": beat.effect})
```

**Why:** GMBeat no longer has `npc_id` or `driver` fields (Phase 1). Just pass `type` + `effect` to ruling.

**Validation:** `world.py` returns `list[dict]` where each dict has just `type` and `effect` keys.

---

## Phase 3: Checker Updates

### Context files to load
- `ccya/ev/checkers/llm_checkers.py` — `beat_narrative_chain` checker (lines 95-160)

### Dependencies
- Phase 1 (GMBeat model simplified)

### Steps

#### 3.1 — Update `beat_narrative_chain` checker

**File:** `ccya/ev/checkers/llm_checkers.py:104-159`

**What:**
1. System prompt template (lines 104-114): Remove `NPC: {npc_id}` and `Driver: {driver}` lines from the GM Beat section.
2. `beat_narrative_chain` function (lines 136-137): Remove `npc_id = pending_beat.get("npc_id", "")` and `driver = pending_beat.get("driver", "")`.
3. User prompt (lines 145-149): Remove `NPC: {npc_id}` and `Driver: {driver}` lines.

**Why:** `pending_gm_beat` no longer has `npc_id` or `driver` fields. Checker should just use `type` + `effect`.

**Validation:** `grep "npc_id\|driver" ccya/ev/checkers/llm_checkers.py` returns 0 matches for beat-related references (other `npc_id` references in the file are for NPC compendium, not beats).

---

## Verification

After all phases:
1. `make check` passes (lint + typecheck)
2. `ev.py play --turns 3` runs without errors — produces narration and `state.meta.beat_candidates` after each turn
3. `state.meta.pending_gm_beat` has just `{type, effect}` — no `npc_id` or `driver`
4. `state.meta.beat_candidates` has just `{type, effect}` — no `npc_id` or `driver`
5. `grep "npc_id\|driver" ccya/models/extraction.py` returns 0 matches for GMBeat
6. `grep "npc_id\|driver" ccya/prompts/world_system.j2 ccya/prompts/ruling_system.j2` returns 0 matches for beat-related references
7. `grep "npc_id\|driver" ccya/ev/checkers/llm_checkers.py` returns 0 matches for beat-related references
