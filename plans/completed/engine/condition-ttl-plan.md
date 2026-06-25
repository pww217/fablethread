# Plan: Condition TTL System

**Status: completed**

## Design Reference

Discussed in chat — TTL system re-implemented with duration bands:
- **Sensory (1-2 turns):** Fleeting effects from a single action. Examples: winded from sprinting, ears ringing, dust in eyes, momentary disorientation
- **Minor (3-4 turns):** Light discomfort that resolves with brief rest. Examples: bruised ribs, muscle strain, sprained ankle, minor cut, rattled by surprise, smoke inhalation, dehydration, mild headache
- **Significant (5-6 turns):** Real wounds that heal on their own without intervention. Examples: deep bruising, serious laceration (not requiring stitches), broken nose, moderate burns, concussion symptoms
- **Major (7+ turns):** Long-term threats that persist and may escalate without treatment. Examples: severe poisoning, radiation sickness, progressive disease, gangrenous wound
- **Permanent:** Won't heal without professional/story intervention. Examples: broken bone, severe internal bleeding, amputated limb, permanent disfigurement, cursed, lost eye, severe burns, deep laceration requiring stitches

## Purpose

Re-introduce TTL-based auto-expiration for player conditions. Conditions with `turns_remaining` decrement each turn and are auto-removed when hitting 0. `"permanent"` = permanent (never expires). Engine assigns a default TTL when the LLM omits it.

**Origin:** Eval 5-Pack 2026-06-24 (`roadmap/bugs/eval-5pack-2026-06-24.md`), Bug #2 — Duplicate Condition Adds. Without TTL, conditions persist forever because the extractor almost never removes them. The cognitive load of tracking expiration for every condition is too high. TTL is the **primary** mechanism for condition lifecycle — the engine auto-expires sensory/minor/significant conditions. The extractor only needs to reason about major (7+) and permanent conditions.

## Constraints

- `turns_remaining: int | Literal["permanent"]` on `Condition` and `ConditionAdd`
- `"permanent"` means never expires (explicit string, not `null`/`None`)
- Engine-side default TTL from config (default 10) when the LLM omits it
- TTL decrement pass runs after delta application, before persist
- Prompt guidance uses the duration bands above
- No backward compatibility for old saves (they won't have `turns_remaining`)
- `_DEFAULT_CONDITION_TTL` constant replaced by `config.condition_default_ttl`

## Phase Summary

One phase touching four concerns in order: models → config → delta builder → turn state → prompts. Each step is independently verifiable.

## Phase 1: TTL system

**Files:** `ccya/models/state.py`, `ccya/engine/config.py`, `ccya/state/delta_builder.py`, `ccya/engine/turn_state.py`, `ccya/prompts/extract_state_system.j2`, `ccya/prompts/extract_state_user.j2`, `ccya/prompts/sections/_conditions.j2`

**Dependencies:** None

### Step 1.1 — Add `turns_remaining` to Condition and ConditionAdd models

**File:** `ccya/models/state.py`

**What:**
- Add `turns_remaining: int | Literal["permanent"] = 0` to the `Condition` class (line 75-79)
- Add `turns_remaining: int | Literal["permanent"] = 0` to the `ConditionAdd` class (line 92-100)
- Import `Literal` from `typing` (already imported at line 7)

**Why:** The TTL system needs a field to track remaining turns. `"permanent"` is an explicit string (not `null`/`None`), so the LLM must actively choose permanent. The default of `0` is a sentinel — it means "not yet assigned" and will be replaced by the engine default in `apply_delta()`.

**Model shapes after change:**
```python
from typing import Literal

class Condition(BaseModel):
    id: str
    label: str
    description: str = ""
    added_turn: int = 0
    turns_remaining: int | Literal["permanent"] = 0

class ConditionAdd(BaseModel):
    id: str
    label: str
    description: str = ""
    turns_remaining: int | Literal["permanent"] = 0
```

**Validation:** `grep -n "turns_remaining" ccya/models/state.py` returns 2 matches (one per class).

### Step 1.2 — Add `condition_default_ttl` to EngineConfig

**File:** `ccya/engine/config.py`

**What:**
- Add `condition_default_ttl: int = 10` to the `EngineConfig` dataclass (around line 192, near other TTL configs like `nearby_decay_ttl`)
- Add `condition_default_ttl=int(game.get("condition_default_ttl", 10))` to `build_engine_config()` (around line 310, after `departed_archive_ttl`)

**Why:** Makes the default TTL configurable via `game.yaml` instead of a hardcoded constant.

**Validation:** `grep -n "condition_default_ttl" ccya/engine/config.py` returns 2 matches.

### Step 1.3 — Apply TTL in delta_builder when adding conditions

**File:** `ccya/state/delta_builder.py`

**What:**
- Add `_DEFAULT_CONDITION_TTL = 10` module constant (line 21, near top)
- In `apply_delta()`, in the condition add loop (around line 256-267), after building `cond_dict`:
  - If `ca.turns_remaining == 0` (default/sentinel): assign `_DEFAULT_CONDITION_TTL`
  - If `ca.turns_remaining == "permanent"`: store `"permanent"`
  - If `ca.turns_remaining` is an int > 0: use the LLM-provided value

**Logic:**
```python
cond_dict = {
    "id": cid,
    "label": ca.label,
    "description": ca.description,
    "added_turn": current_turn,
}
if ca.turns_remaining == 0:
    cond_dict["turns_remaining"] = _DEFAULT_CONDITION_TTL
elif ca.turns_remaining == "permanent":
    cond_dict["turns_remaining"] = "permanent"
else:
    cond_dict["turns_remaining"] = ca.turns_remaining
existing_conds.append(cond_dict)
```

**Why:** Distinguishes three cases cleanly:
- `0` (default) → engine assigns default TTL
- `"permanent"` → explicit permanent
- `int >= 1` → LLM-specified TTL

**Validation:** `grep -n "_DEFAULT_CONDITION_TTL" ccya/state/delta_builder.py` returns 2 matches. Conditions added without explicit TTL get 10 turns.

### Step 1.4 — Add TTL decrement pass to turn_state.py

**File:** `ccya/engine/turn_state.py`

**What:**
- Add a `_expire_conditions()` function that:
  - Iterates all conditions in `state["pc"]["conditions"]`
  - For each condition: check `turns_remaining`
    - If `"permanent"`: skip (never expires)
    - If `int`: decrement by 1
    - When `turns_remaining` reaches 0 or below: remove the condition and log `condition_expired`
  - Returns the updated conditions list

- Call `_expire_conditions()` in `_apply_state_updates()` after `apply_delta()` (around line 408), before the beat history logic

- Import `append_event` from `ccya.state.chronicle` in `turn_state.py`

**Function signature:**
```python
def _expire_conditions(state: dict[str, Any], turn_no: int, trace_id: str) -> list[dict[str, Any]]:
    """Decrement turns_remaining on all conditions. Remove expired ones. Log events."""
```

**Implementation logic:**
```python
updated_conds = []
for c in (state.get("pc") or {}).get("conditions") or []:
    tr = c.get("turns_remaining")
    if tr == "permanent":
        updated_conds.append(c)
        continue
    if isinstance(tr, int):
        new_remaining = tr - 1
        if new_remaining <= 0:
            append_event(save_dir, {
                "kind": "condition_expired",
                "condition_id": c.get("id"),
                "turn": turn_no,
            })
            _log.info(
                "condition expired: %s at turn %d",
                c.get("id"), turn_no,
                extra={"turn": turn_no},
            )
            # do not append — condition removed
        else:
            updated_conds.append({**c, "turns_remaining": new_remaining})
    else:
        # Unknown type — keep as-is with warning
        _log.warning(
            "condition unknown turns_remaining type: %s for %s",
            type(tr).__name__, c.get("id"),
            extra={"turn": turn_no},
        )
        updated_conds.append(c)

(state.setdefault("pc", {})["conditions"])[:] = updated_conds
```

**Why:** This is the engine-side TTL decrement pass, moved from the old `turn.py` logic (turn.py:1065-1089 in the pre-redesign codebase).

**Validation:** `grep -n "_expire_conditions\|condition_expired" ccya/engine/turn_state.py` returns matches. TTL decrement runs after delta application.

### Step 1.5 — Add duration guidance to extract_state_system.j2

**File:** `ccya/prompts/extract_state_system.j2`

**What:**
- Add duration guidance section after the `pc_condition_add` guidance (around line 110), before the stat-to-condition heuristics
- Add `turns_remaining` to the JSON schema example for `pc_condition_add`

**Duration guidance text:**
```
**Duration guidance for `turns_remaining`:**
- 1–2 turns: sensory/transient — winded, ears ringing, dust in eyes, momentary disorientation
- 3–4 turns: minor discomfort — bruised ribs, muscle strain, sprained ankle, minor cut, rattled, smoke inhalation, dehydration
- 5–6 turns: significant wounds — deep bruising, serious laceration (no stitches needed), broken nose, moderate burns, concussion symptoms
- 7+ turns: major long-term threats — severe poisoning, radiation sickness, progressive disease, gangrenous wound
- "permanent": won't heal without professional/story intervention. Broken bone, amputated limb, permanent disfigurement, cursed, lost eye, severe burns requiring stitches

When in doubt, assign a longer duration rather than a shorter one.
```

**Schema example change:** Update the `pc_condition_add` example in the JSON schema (line 73) from:
```json
"pc_condition_add": [{"id": "...", "label": "...", "description": "..."}]
```
to:
```json
"pc_condition_add": [{"id": "...", "label": "...", "description": "...", "turns_remaining": 5}]
```

**Validation:** Prompt includes all 5 duration bands. Schema example includes `turns_remaining`.

### Step 1.6 — Show condition age and TTL in extract_state_user.j2

**Files:** `ccya/prompts/sections/_conditions.j2`, `ccya/prompts/extract_state_user.j2`

**What:**
- Update `_conditions.j2` to also show TTL alongside age:
  - Current: `- {{ c.id }} (age: N turns): label — description`
  - New: `- {{ c.id }} (age: N turns, TTL: M turns): label — description`
  - For permanent conditions: `- {{ c.id }} (age: N turns, TTL: permanent): label — description`

**File:** `ccya/prompts/sections/_conditions.j2`

**What:**
- Update the condition rendering line (line 9) to conditionally show TTL:
```jinja
- {{ c.id if c is mapping else c }}{% if show_age %} (age: {{ turn_no - (c.added_turn if c is mapping else 0) }} turns){% endif %}{% if c is mapping and c.get('turns_remaining') is not none %}, TTL: {{ c.turns_remaining if c.turns_remaining == "permanent" else (c.turns_remaining if c.turns_remaining is number else "?") }} turns{% endif %}{% if c is mapping and c.get('label') %}: {{ c.label }}{% endif %}{% if c is mapping and c.get('description') %} — {{ c.description }}{% endif %}
```

**Validation:** Conditions in the extractor prompt show both age and TTL.

### Step 1.7 — Update documentation

**Files:** `docs/architecture/state-models.md`, `docs/architecture/step2b-state.md`, `docs/repomap.md`, `docs/architecture/cross-module-contracts.md`

**What:**
- **state-models.md:** Add `turns_remaining: int | Literal["permanent"]` to the Condition model description (line 71). Add `turns_remaining` to the state.yaml condition shape (line 27). Add a new section documenting the TTL system: decrement pass, permanent conditions, default TTL.
- **step2b-state.md:** Add `turns_remaining` to the `pc_condition_add` output description (line 30). Add a note about TTL assignment in the delta builder.
- **repomap.md:** Add `turns_remaining` to the Condition/ConditionAdd entries in the models section. Note the TTL decrement pass in turn_state.py.
- **cross-module-contracts.md:** Add a contract entry for the TTL system: "Conditions with `turns_remaining` decrement each turn in `_expire_conditions()` in `turn_state.py`. `"permanent"` = never expires. Default TTL from `config.condition_default_ttl` (default 10) applied in `delta_builder.py` when LLM omits it."

**Validation:** All docs reference `turns_remaining` on conditions. TTL mechanics are documented.
