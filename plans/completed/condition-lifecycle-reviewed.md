# Condition Lifecycle: Duration, Relevance, and NPC Enter/Exit

## Status
`completed`

## Part of
standalone

## Dependencies
- none (can run in parallel with all other plans)

## Affected Files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/models.py` | modify | Add `turns_remaining: int | None = None` field to `Condition` model |
| `ccya/engine/turn.py` | modify | Add condition age pass: decrement `turns_remaining`, remove expired conditions, log `condition_expired` event via `append_event` |
| `ccya/prompts/extract_state_system.j2` | modify | Add condition duration guidance (short/medium/long taxonomy) and relevance rule |
| `ccya/prompts/extract_scene_system.j2` | modify | Add explicit NPC enter/exit tracking rules and few-shot examples |
| `tests/test_turn.py` | modify (or create) | Condition expiry and persistence tests |
| `tests/test_prompts.py` | create | Prompt rendering tests for duration/NPC rules |
| `docs/REPOMAP/engine.md` | update | Document condition age pass |
| `docs/REPOMAP/models.md` | update | Document `turns_remaining` field on `Condition` |
| `docs/REPOMAP/prompts.md` | update | Document condition duration taxonomy and NPC tracking rules |

## Overview
Conditions are the least-audited mechanic in the current system. Three specific failures appear across runs: (1) conditions last too long — a `rattled` condition applied at T3 persists through T12 with no decay, despite the player having had multiple successful turns since; (2) conditions are irrelevant to actual gameplay — conditions like `dust_in_eyes` appear and are never referenced in narration or checked by any dice roll, making them dead state entries; (3) NPCs enter and leave scenes without corresponding `npc_add`/`npc_remove` events — the extractor fails to track NPC scene presence, so `present_npcs` drifts from the narration's actual cast. This plan adds condition duration enforcement, a relevance check, and NPC scene entry/exit audit to the extraction prompts.

## Non-goals
- Does not change how conditions affect dice rolls — that is the rules pipeline's domain.
- Does not change NPC compendium entries or bios — only `present_npcs` tracking.
- Does not add new condition types.

## Firm decisions

1. Condition duration is enforced by the engine, not the extractor. The extractor proposes conditions with an initial `turns_remaining`; the engine decrements each turn and removes at 0.
2. Duration taxonomy (for the extractor prompt, to guide initial `turns_remaining` values):
    - `brief` (1–2 turns): physical/sensory conditions from a single event (dust in eyes, winded, startled)
    - `short` (3–4 turns): minor injuries, social discomforts, light debuffs (rattled, shaken, minor wound)
    - `medium` (5–8 turns): significant injuries, fear, ongoing environmental effects (injured arm, frightened, burning building)
    - `long` (9+ turns): major injuries, persistent debuffs, magical/curse effects — must have explicit narrative justification
3. Relevance rule: a condition should only be added if it would plausibly affect at least one future dice roll. `dust_in_eyes` is only valid if the player might attempt a perception or ranged action. If the condition has no plausible mechanical relevance given the current scene, the extractor should not emit it.
4. NPC enter/exit: `npc_add` must be emitted whenever a named NPC is introduced in narration and is not already in `present_npcs`. `npc_remove` must be emitted whenever narration indicates a named NPC has left the scene (departed, fled, died, was rendered unconscious). Ambient/unnamed characters do not require tracking.
5. Condition age decrement runs in `turn.py` after extractor delta application, alongside the pressure aging pass from mechanics-pressure-decay.md.

## Ambiguities resolved before execution

1. **`turns_remaining` does NOT exist on the `Condition` model.** The `Condition` model (`ccya/models.py:18`) has fields: `id`, `label`, `description`, `added_turn`. **The executor must add `turns_remaining: int | None = None` to the `Condition` model before implementing the age pass.** The duration guide should note: "Omit `turns_remaining` (null) only for permanent effects like amputations or magical curses."
2. **Conditions are stored at `state["pc"]["conditions"]`, NOT `state.active_conditions`.** The age pass must iterate `state["pc"]["conditions"]` (a `list[dict]`), not `state.active_conditions`. The REPOMAP (engine.md:154) confirms: `pc.conditions` is `list[Condition]` (`id`, `label`, `description`, `added_turn`).
3. **`log_event` does not exist.** The codebase uses `append_event(save_dir, event)` from `ccya.state` (imported at `ccya/engine/turn.py:47`). The age pass must call `append_event()` to log `condition_expired` events.

---

## Phases

### Phase 0: Add `turns_remaining` to Condition model

#### Step 0.1 — Add `turns_remaining` field to `Condition` model

**File:** `ccya/models.py` (line 18)

**Current model:**
```python
class Condition(BaseModel):
    id: str
    label: str
    description: str = ""
    added_turn: int = 0
```

**Change:** Add `turns_remaining: int | None = None` field. `None` means permanent (no decay).

```python
class Condition(BaseModel):
    id: str
    label: str
    description: str = ""
    added_turn: int = 0
    turns_remaining: int | None = None
```

**Validation:** `pytest tests/ -k condition --no-header -q` (15s killswitch) — confirm no model validation errors.

---

### Phase 1: Condition Age Pass in turn.py

#### Step 1.1 — Add condition age pass to turn.py

**File:** `ccya/engine/turn.py`

**Context:** Conditions are stored at `state["pc"]["conditions"]` (a `list[dict]`). The variable for the current turn number is `turn_no` (set at line 296). The event logging function is `append_event` (imported at line 47). The age pass runs after `apply_delta()` and after the pressure aging pass.

**Placement:** After the pressure aging pass (lines 611–617 in `run_turn`, lines 1157–1163 in `run_turn_retry`), and before the metrics section (line 619 in `run_turn`).

**Corrected code snippet for `run_turn`:**
```python
# After pressure aging pass (after line 617 in run_turn):
# Condition age pass: decrement turns_remaining, remove expired
updated_conds = []
for c in (state.get("pc") or {}).get("conditions") or []:
    tr = c.get("turns_remaining")
    if tr is None:
        # Permanent condition — do not age
        updated_conds.append(c)
        continue
    new_remaining = tr - 1
    if new_remaining <= 0:
        append_event(save_dir, {
            "kind": "condition_expired",
            "condition_id": c.get("id"),
            "turn": turn_no,
        })
        # do not append — condition removed
    else:
        updated_conds.append({**c, "turns_remaining": new_remaining})

(state.setdefault("pc", {})["conditions"])[:] = updated_conds
```

**Corrected code snippet for `run_turn_retry`:** (same logic, placed after line 1163)
```python
# After pressure aging pass (after line 1163 in run_turn_retry):
# Condition age pass: decrement turns_remaining, remove expired
updated_conds = []
for c in (state.get("pc") or {}).get("conditions") or []:
    tr = c.get("turns_remaining")
    if tr is None:
        updated_conds.append(c)
        continue
    new_remaining = tr - 1
    if new_remaining <= 0:
        append_event(save_dir, {
            "kind": "condition_expired",
            "condition_id": c.get("id"),
            "turn": turn_no,
        })
    else:
        updated_conds.append({**c, "turns_remaining": new_remaining})

(state.setdefault("pc", {})["conditions"])[:] = updated_conds
```

**Validation:** Apply a condition with `turns_remaining: 2`. Run 2 turns. Confirm condition is absent from `state["pc"]["conditions"]` on turn 3. Confirm `condition_expired` event in `events.jsonl`.

---

### Phase 2: Condition Duration and Relevance in extract_state_system.j2

#### Step 2.1 — Add condition duration taxonomy and relevance rule

**File:** `ccya/prompts/extract_state_system.j2`

**Placement:** After the existing `## Condition guidance` section (line 83), before `## State-presence rule` (line 97).

**Add this block:**
```
**CONDITION DURATION GUIDE:** When emitting a `condition_add`, set `turns_remaining` using this taxonomy:
- **brief (1–2 turns):** Single-event physical/sensory conditions — dust in eyes, winded, startled, tripped. These resolve in 1–2 turns naturally.
- **short (3–4 turns):** Minor debuffs — rattled, shaken, minor bruise, light wound. Resolve within the same encounter.
- **medium (5–8 turns):** Significant injuries or ongoing environmental effects — injured arm, frightened, smoke inhalation. Last through an encounter and into the next.
- **long (9+ turns):** Major injuries, persistent effects. Requires explicit narrative justification. Do not use for minor encounters.
- **Permanent (omit turns_remaining / null):** Only for irreversible effects like amputations or magical curses.

**CONDITION RELEVANCE RULE:** Only add a condition if it would plausibly affect at least one future dice roll in the current scene context. Do not add flavor conditions with no mechanical relevance. If unsure, omit.
```

**Validation:** In the next eval run, check conditions added by `extract_state`. Confirm `turns_remaining` values align with the taxonomy. Confirm no flavor-only conditions with 0 mechanical relevance.

---

### Phase 3: NPC Enter/Exit in extract_scene_system.j2

#### Step 3.1 — Add NPC enter/exit rules and few-shots

**File:** `ccya/prompts/extract_scene_system.j2`

**Placement:** After the `## NPC ID rules` section (line 38), before `## State-presence rule` (line 45).

**Add this block:**
```
**NPC ENTER/EXIT RULE (MANDATORY):**
- Emit `npc_add` for every named NPC who appears in the narration for the first time this turn and is NOT already in `present_npcs`.
- Emit `npc_remove` for every named NPC who narration indicates has left, fled, died, fainted, or been removed from the scene.
- Do NOT emit `npc_add` for NPCs already in `present_npcs` — that causes duplicates.
- Do NOT emit `npc_remove` for NPCs who are simply not mentioned — only remove if narration actively indicates departure.
- Unnamed ambient characters ("a group of guards," "bystanders") do not require `npc_add`/`npc_remove` tracking.

EXAMPLE — NPC enters (correct):
Narration: "A red-haired man in boiled leather steps through the door and locks eyes with you."
`present_npcs` before: [caron]
→ Emit: `npc_add: { id: "red_haired_man", name: "Red-Haired Man", ... }`

EXAMPLE — NPC exits (correct):
Narration: "Caron spits on the floor and shoves through the crowd, disappearing into the street."
→ Emit: `npc_remove: { id: "caron" }`

EXAMPLE — NPC not mentioned, no remove (correct):
Narration does not mention Halden this turn.
→ Do NOT emit `npc_remove: { id: "halden" }` — absence ≠ departure.
```

**Validation:** Run a turn where Halden is in `present_npcs` but is not mentioned in narration. Confirm no `npc_remove` for Halden. Run a turn where narration explicitly says Caron leaves. Confirm `npc_remove` for Caron is emitted.

---

## Tests to write or update

### `tests/test_turn.py` — Condition expiry tests

**Test 1: condition expiry**
```python
async def test_condition_expiry():
    """Condition with turns_remaining: 1 expires after one turn, condition_expired event emitted."""
    # Setup: create save dir with a condition that has turns_remaining=1
    # Run one turn (mocked LLM)
    # Assert: condition no longer in state["pc"]["conditions"]
    # Assert: events.jsonl contains a condition_expired event for that condition_id
```

**Test 2: condition persistence**
```python
async def test_condition_persistence():
    """Condition with turns_remaining: 3 decrements correctly over 3 turns."""
    # Setup: condition with turns_remaining=3
    # Run 2 turns (mocked LLM)
    # Assert: condition still present with turns_remaining=1
    # Run 1 more turn (mocked LLM)
    # Assert: condition removed, condition_expired event emitted
```

### `tests/test_prompts.py` — Prompt rendering tests (new file)

**Test 3: extract_state_system.j2 renders duration guide**
```python
def test_extract_state_system_has_duration_guide():
    """Confirm CONDITION DURATION GUIDE and CONDITION RELEVANCE RULE present in rendered prompt."""
    env = _build_jinja_env(template_dir)
    text = env.get_template("extract_state_system.j2").render(...)
    assert "CONDITION DURATION GUIDE" in text
    assert "CONDITION RELEVANCE RULE" in text
    assert "brief (1–2 turns)" in text
    assert "short (3–4 turns)" in text
    assert "medium (5–8 turns)" in text
    assert "long (9+ turns)" in text
```

**Test 4: extract_scene_system.j2 renders NPC enter/exit rules**
```python
def test_extract_scene_system_has_npc_enter_exit():
    """Confirm NPC ENTER/EXIT RULE with all three examples present."""
    env = _build_jinja_env(template_dir)
    text = env.get_template("extract_scene_system.j2").render(...)
    assert "NPC ENTER/EXIT RULE" in text
    assert "absence ≠ departure" in text or "absence != departure" in text
    assert "npc_add" in text
    assert "npc_remove" in text
```

---

## REPOMAP updates required

- **`docs/REPOMAP/engine.md`:** Under `turn.py` section, add:
  > `_age_conditions(state, save_dir, turn_no)` — decrements `turns_remaining` on all active conditions, removes expired ones (≤0), logs `condition_expired` event via `append_event`. Runs after delta application and pressure aging. Permanent conditions (turns_remaining=None) are skipped.

- **`docs/REPOMAP/models.md`:** Under `Condition` model, add:
  > `turns_remaining: int | None = None` — number of turns until condition expires. `None` means permanent (no decay). Set by extractor, decremented by engine.

- **`docs/REPOMAP/prompts.md`:** Under `extract_state_system.j2` — add: CONDITION DURATION GUIDE (brief/short/medium/long/Permanent taxonomy) and CONDITION RELEVANCE RULE. Under `extract_scene_system.j2` — add: NPC ENTER/EXIT RULE with three examples (enter, exit, no-mention).

---

## Risks

1. **Permanent conditions compatibility:** The `turns_remaining is None` guard handles permanent conditions, but existing conditions in saved state files won't have this field. The Pydantic model default (`None`) handles this for new conditions, but dict-based conditions loaded from state files (as in `delta.py:300-322`) will simply not have the key. The age pass uses `.get("turns_remaining")` which returns `None` for missing keys, so this is safe.

2. **Compactor condition removal interaction:** The compactor already has `condition_remove` in `CompactorSanitizationResult` (models.py:47). The compactor's condition removal and the age pass removal are orthogonal — compactor runs on a schedule and removes based on LLM assessment, while age pass runs every turn and removes based on counter. No conflict.

3. **State delta coercion for `turns_remaining`:** The `StateDelta.pc_condition_add` uses `ConditionAdd` model (models.py:35) which does NOT have `turns_remaining`. The extractor prompt will emit `turns_remaining` in the JSON, but Pydantic will reject it unless `ConditionAdd` also has the field. **The executor must add `turns_remaining: int | None = None` to `ConditionAdd` model as well**, or the extractor will fail on parse.
