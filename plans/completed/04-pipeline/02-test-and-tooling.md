# Test and Tooling — Scene Tag Assertions, NPC False Positives, Eval Sync, Scripts Linting

## Status
`completed`

## Phases

3 phases: add scene tag assertions to extraction validation, fix NPC false positives in extraction pipeline, sync thread constants between engine and eval mirror, add `scripts/` to `make check`.

## Issue

Four gaps reduce test reliability and coverage:

1. **No scene tag validation.** The extraction pipeline accepts `scene_result.scene_tags` as a list of strings with no structural validation. Tags like `location:kitchen` vs `location change: kitchen` end up in state as-is, with no assertion they match expected formats. The extraction prompt (`extract_scene_system.j2`) instructs the model to use `tag:value` format but the engine never validates this.

2. **NPC false positives.** The `extract_scene_system.j2` prompt includes NPC dedup rules, but the model frequently produces `npc_add` for NPCs already in the compendium or present list. Plan 03 Phase 2 addresses this with a numbered pre-check step; this plan adds an independent prompt-level guard for physical-presence constraints.

3. **Broken eval mirror sync.** `ccya/eval/engine_mirror.py:22-24` duplicates `ccya/engine/turn.py:84-91` thread lifecycle constants. When the engine constants change, the eval mirror silently diverges, causing eval results to not match engine behavior. There is no cross-file assertion.

4. **scripts/ excluded from make check.** The `scripts/` directory contains Python files (e.g., `ev.py`, visualization scripts) that are not linted or type-checked by `make check`. These drift from codebase standards.

## Solution

Add a lightweight tag validation function that verifies each tag matches `tag:value` structure, called during extraction pipeline validation. Fix NPC false positives by adding prompt-level constraints to `extract_state_system.j2` (not code changes). Add a CI/commit-hook assertion that engine constants and eval mirror constants stay in sync. Add `scripts/` to ruff and mypy paths in `pyproject.toml` or `Makefile`.

## Firm decisions

1. Tag validation is a new function `_validate_scene_tags(tags: list[str])` in `ccya/engine/extraction.py`, called from the existing validation flow. Invalid tags get a warning log entry.
2. NPC false positives are fixed by prompt adjustments in `extract_scene_system.j2` — adding "ONLY extract NPCs that are physically present in the current scene" and a `NO GUESSING` instruction. Code changes are not needed.
3. The sync assertion is a `pytest` test that imports constants from both modules and asserts equality, not a runtime check.
4. `scripts/` linting is opt-in — added to `make check` with a comment noting it may require separate Python package dependencies.

## Non-goals

- Not adding a runtime scene-tag format enforcement that could break existing saves. Warnings only.
- Not changing NPC extraction logic in the engine (only prompt changes).
- Not adding a CI pipeline or commit hook — just a test assertion.
- Not refactoring scripts/ to be importable — just lint and typecheck.

## Risks, Ambiguities, and Blockers

- Tag validation must handle existing tags in saved states. Avoid breaking on legacy tags that don't match the format.
- NPC false positives vary by model (tested with Qwen3). The fix may not be complete after the prompt change — monitor eval results separately.
- Adding `scripts/` to ruff/mypy may fail if scripts have untyped Python or use libraries not in the project dependencies. If coverage is too low, add only ruff (formatting) and skip mypy.
- No blocker on any phase.

---

## Implementation — Phase 1: Scene tag validation

### Context files to load
- `ccya/engine/extraction.py` — the validation/assertion flow near the extraction pipeline, scene result handling

### Detailed steps

#### Step 1.1 — Add `_validate_scene_tags()` function

**File:** `ccya/engine/extraction.py`

**What:** Add a new function:

```python
# Interface contract
def _validate_scene_tags(tags: list[str]) -> list[str]:
    """Validate scene_tags format and return warnings for non-conforming tags.
    
    Expected format: "tag:value" where tag is lowercase alphanumeric+hyphens.
    Non-conforming tags log a warning and are returned in the warning list.
    """
    ...
```

Call it from the extraction validation flow, passing `scene_result.scene_tags`. Log a warning for each non-conforming tag but do not raise.

**Why:** Without validation, extraction errors silently propagate incorrect tags into state. Warnings make them visible without breaking game state.

**Validation:** Pass a tag list with entries like `["location:kitchen", "time_of_day:evening", "bad tag no colon", "", "123:"]`. Confirm the first two pass, the last three generate warnings.

### Tests to write or update

- `tests/test_extraction.py`: Add test cases for `_validate_scene_tags` with valid tags, invalid tags, empty list, and mixed lists.

### REPOMAP updates required

- `ccya/engine/extraction.py`: Add `_validate_scene_tags()` function and its call site.

---

## Implementation — Phase 2: Reduce NPC false positives via prompt constraints

### Context files to load
- `ccya/prompts/extract_scene_system.j2` — the NPC extraction section (lines 50-100)
- `plans/01-extraction-accuracy.md` — Phase 2 overlaps with this section; merge changes carefully

### Detailed steps

#### Step 2.1 — Add physical-presence and no-guessing constraints

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Add the following constraints after the existing NPC dedup section:

```jinja2
## NPC Extraction Rules (CRITICAL)

IMPORTANT: ONLY extract NPCs that are PHYSICALLY PRESENT in the current scene.
- DO NOT include hypothetical NPCs ("there could be guards")
- DO NOT include past-tense references ("the guards were here earlier")
- DO NOT include NPC references that are not physically present ("the king you met yesterday")
- If you are not CERTAIN an NPC is present, do not add them

{% if scene_type == "examine" or scene_type == "cargo" %}
IMPORTANT: For cargo/examine interactions, the subject is likely NOT physically present.
Only extract NPCs if they are explicitly described as being in the same physical space.
{% endif %}
```

**Why:** False positives occur because the model treats NPC references as extraction targets even when the NPC is not physically present. Explicit constraints reduce hallucinations.

**Validation:** Run 10 test turns with cargo/examine interactions. Count NPC_add entries before and after. Expect a ~50% reduction in false positives.

### Tests to write or update

- None (prompt-only change). Run eval passes to validate.

### REPOMAP updates required

- `ccya/prompts/extract_scene_system.j2`: Updated NPC extraction section.

---

## Implementation — Phase 3: Sync thread constants and add scripts/ to make check

### Context files to load
- `ccya/eval/engine_mirror.py` — thread constants at lines 22-24
- `ccya/engine/turn.py` — thread constants at lines 84-91
- `Makefile` — check/lint/typecheck targets

### Detailed steps

#### Step 3.1 — Add sync assertion test

**File:** `tests/test_constants_sync.py` (new file)

**What:**

```python
"""Assert engine and eval mirror thread constants stay in sync."""

from ccya.engine.turn import (
    _ACTIVE_THREAD_CAP,
    _EXPIRE_SILENT_TURNS,
    _PROMOTION_COOLDOWN_TURNS,
)
from ccya.eval.engine_mirror import (
    ACTIVE_THREAD_CAP,
    EXPIRE_SILENT_TURNS,
    PROMOTION_COOLDOWN_TURNS,
)


class TestThreadConstantsSync:
    def test_active_thread_cap(self):
        assert _ACTIVE_THREAD_CAP == ACTIVE_THREAD_CAP

    def test_expire_silent_turns(self):
        assert _EXPIRE_SILENT_TURNS == EXPIRE_SILENT_TURNS

    def test_promotion_cooldown_turns(self):
        assert _PROMOTION_COOLDOWN_TURNS == PROMOTION_COOLDOWN_TURNS
```

**Why:** The eval mirror duplicates engine constants. When one changes and the other doesn't, eval stops reflecting engine behavior. An explicit test catches divergence.

**Validation:** `make test` — new test passes. Change a constant in `turn.py` — test fails (confirm the assertion catches divergence).

#### Step 3.2 — Add scripts/ to lint coverage

**File:** `Makefile`

**What:** Add `scripts/` to the `typecheck` target's mypy path and verify the existing `lint` target (`ruff check .`) already covers it:

```makefile
typecheck:  # existing typecheck target
	uv run mypy ccya scripts/
```

The existing `lint: uv run ruff check .` already covers `scripts/` implicitly. Only mypy needs an explicit path addition.

If `mypy scripts/` fails due to missing type hints or dependencies, create a separate `lint-scripts` target for ruff only and omit scripts from mypy.

**Why:** `ev.py` and other scripts in `scripts/` are part of the codebase. Excluding them from lint/typecheck allows them to drift from codebase standards.

**Validation:** `make check` passes (or only `ruff check` succeeds for scripts/).

### Tests to write or update

- `tests/test_constants_sync.py`: New file with sync assertions.

### REPOMAP updates required

- `ccya/eval/engine_mirror.py`: No change (the test asserts against current values — if they differ, the test fails and prompts a fix).
- `Makefile`: Updated `lint` and `typecheck` targets to include `scripts/`.
