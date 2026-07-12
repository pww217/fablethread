# Eval Engine Mirror — Parity Fixes

## Purpose

Eliminate hardcoded constants in `engine_mirror.py` that can silently diverge from production engine defaults, and add runtime validation for assertion field names.

## Problem Statement

Several constants in `ccya/eval/engine_mirror.py` are hardcoded rather than imported from the authoritative source modules (`EngineConfig`, `delta_builder`). When production defaults change, eval scenarios continue reasoning from stale values — TTLs, condition caps, and other thresholds silently drift out of sync with what the engine actually does at runtime.

## Constraints

- Engine mirror is read-only by design: it imports or mirrors, never defines behavior.
- All changes must preserve `constants_block()` output format (used in judge traces).
- No test infrastructure exists yet (`test_eval_schema.py` does not exist); creating it is part of the scope.
- Do not change production engine defaults — only wire eval to use them.

## Non-goals

- Do not add new eval scenarios or assertions.
- Do not change `universal_asserts.py`.
- Do not modify prompt templates (extract_scene_system.j2, etc.).
- Do not introduce runtime overhead in the main pipeline — engine_mirror is only imported by eval harness at startup.

## Solution

Replace each hardcoded constant with a live import from its authoritative source module, or export it as a public constant if none exists yet. Create `test_eval_schema.py` to validate that `KNOWN_ASSERT_FIELDS` stays in sync with runner's `_check_asserts` handler field names. Each change is independently verifiable via grep + import check.

## Firm decisions

1. EngineConfig has `arc_memory_ttl: int = 3` and `thread_memory_ttl: int = 3`, NOT `resolved_arc_ttl` or `completed_thread_ttl`. Use the actual field names that exist in production code.
2. `_DEFAULT_CONDITION_TTL` is private (underscore-prefixed) in delta_builder.py — it must be exported as a public constant before engine_mirror can import it.
3. `URGENCY_LEVELS = ("background", "normal", "urgent")` matches `ArcThread.urgency: Literal["background", "normal", "urgent"]` at models.py:36 — keep the tuple, do not derive from type annotations (fragile across Pydantic versions).
4. `KNOWN_ASSERT_FIELDS` needs a test file (`test_eval_schema.py`) that validates it against runner._check_asserts handler field names. The test does not exist yet and must be created.

## Risks, Ambiguities, and Blockers

- **NPC cap has no authoritative source.** There is no Python constant or prompt template reference for `SCENE_NAMED_NPC_CAP = 10`. The only NPC limit in extract_scene_system.j2 (line 114) says "Limit new NPCs to at most 3 per turn", which is a different concept. `[QUESTION: Should we keep SCENE_NAMED_NPC_CAP hardcoded with a comment noting no authoritative source, or does this need a prompt change first?]`
- **KNOWN_ASSERT_FIELDS may already be stale.** The test file does not exist, so it's unknown whether the current field sets actually match runner._check_asserts. Creating the test will reveal any existing mismatches — some assertions may fail initially and need KNOWN_ASSERT_FIELDS corrections.

## Status
`completed`

## Phases

2 phases covering: (1) replace hardcoded constants with live imports, (2) create schema validation test for KNOWN_ASSERT_FIELDS.

---

## Implementation — Phase 1: Replace hardcodes with live imports

### Context files to load
- `ccya/eval/engine_mirror.py` (full file, 120 lines)
- `ccya/engine/config.py` EngineConfig class definition and defaults
- `ccya/state/delta_builder.py` DEFAULT_CONDITION_TTL export
- `ccya/models.py` ArcThread urgency Literal annotation

### Detailed steps

#### Step 1.1 — Replace THREAD_RESOLVED_ARC_TTL with live import from EngineConfig.arc_memory_ttl

**File:** `ccya/eval/engine_mirror.py`

**What:** Lines 22, replace:
```python
THREAD_RESOLVED_ARC_TTL: int = 3
```
with:
```python
from ccya.engine.config import EngineConfig
# ... (import already exists at line 12)
_defaults = EngineConfig()  # (already exists at line 19)

THREAD_RESOLVED_ARC_TTL: int = _defaults.arc_memory_ttl
```

**Why:** EngineConfig has `arc_memory_ttl: int = 3` (config.py:160). The hardcoded value of 3 matches the default, but if it ever changes in production, eval would silently use stale values. Importing from `_defaults` ensures lockstep.

**Validation:**
```bash
python -c "from ccya.eval.engine_mirror import THREAD_RESOLVED_ARC_TTL; assert THREAD_RESOLVED_ARC_TTL == 3"
grep -n 'arc_memory_ttl' ccya/engine/config.py | head -2
```

#### Step 1.2 — Replace THREAD_COMPLETED_THREAD_TTL with live import from EngineConfig.thread_memory_ttl

**File:** `ccya/eval/engine_mirror.py`

**What:** Lines 23, replace:
```python
THREAD_COMPLETED_THREAD_TTL: int = 3
```
with:
```python
THREAD_COMPLETED_THREAD_TTL: int = _defaults.thread_memory_ttl
```

**Why:** EngineConfig has `thread_memory_ttl: int = 3` (config.py:159). Same drift risk as Step 1.1 — import from actual field name, not the old plan's hypothetical names (`resolved_arc_ttl`, `completed_thread_ttl`).

**Validation:**
```bash
python -c "from ccya.eval.engine_mirror import THREAD_COMPLETED_THREAD_TTL; assert THREAD_COMPLETED_THREAD_TTL == 3"
grep -n 'thread_memory_ttl' ccya/engine/config.py | head -2
```

#### Step 1.3 — Export DEFAULT_CONDITION_TTL from delta_builder and import into engine_mirror

**File:** `ccya/state/delta_builder.py` (line 21)

**What:** Replace:
```python
_DEFAULT_CONDITION_TTL = 10
```
with:
```python
DEFAULT_CONDITION_TTL: int = 10
```

Also keep the private alias for backward compatibility with any internal callers that reference `_DEFAULT_CONDITION_TTL`:
```python
_DEFAULT_CONDITION_TTL = DEFAULT_CONDITION_TTL  # legacy name, do not use new code
```

**File:** `ccya/eval/engine_mirror.py` (line 13)

**What:** Update the import from delta_builder to include `DEFAULT_CONDITION_TTL`:
```python
from ccya.state.delta_builder import DEFAULT_CONDITION_TTL
```

Add a new module-level constant in engine_mirror:
```python
CONDITION_TTL: int = DEFAULT_CONDITION_TTL
```

**Why:** `_DEFAULT_CONDITION_TTL` is private (underscore-prefixed convention). Eval scenarios need an authoritative TTL for condition expiry testing. Exporting it publicly lets eval import from the source of truth rather than hardcoding 10.

**Validation:**
```bash
python -c "from ccya.state.delta_builder import DEFAULT_CONDITION_TTL, _DEFAULT_CONDITION_TTL; assert DEFAULT_CONDITION_TTL == _DEFAULT_CONDITION_TTL == 10"
grep -n 'DEFAULT_CONDITION_TTL' ccya/eval/engine_mirror.py
```

#### Step 1.4 — Add SCENE_NAMED_NPC_CAP note (no change yet)

**File:** `ccya/eval/engine_mirror.py` line 41

**What:** Update the comment on `SCENE_NAMED_NPC_CAP: int = 10`:
```python
# NOTE: No authoritative source in production code or prompts.
# extract_scene_system.j2 line 114 says "Limit new NPCs to at most 3 per turn" (different concept).
# This value is eval-only and may need a prompt change before it can be imported.
SCENE_NAMED_NPC_CAP: int = 10
```

**Why:** The design assessment claims this comes from `extract_scene_system.j2 "## NPC scene cap"` but no such section or reference exists in the template. Keeping it hardcoded is acceptable for now, but the comment must accurately reflect that there's no authoritative source — not a false claim about prompt provenance.

**Validation:**
```bash
grep -A3 'SCENE_NAMED_NPC_CAP' ccya/eval/engine_mirror.py | head -5
rg "npc_cap|NPC.*cap" ccya/prompts/ --include="*.j2"  # verify no authoritative source exists
```

#### Step 1.5 — Add URGENCY_LEVELS runtime assertion against ArcThread urgency annotation

**File:** `ccya/eval/engine_mirror.py` line 26 (after existing `URGENCY_LEVELS` definition)

**What:** Append a runtime import-time assertion at module level:
```python
# Validate URGENCY_LEVELS stays in sync with ArcThread urgency Literal annotation
from ccya.models import ArcThread
_urgency_annotation = ArcThread.model_fields['urgency'].annotation  # Pydantic v2 — Literal["background", "normal", "urgent"]
_urgency_args = _urgency_annotation.__args__ if hasattr(_urgency_annotation, '__args__') else tuple()
assert set(URGENCY_LEVELS) == set(_urgency_args), f"URGENCY_LEVELS mismatch: {URGENCY_LEVELS} vs {_urgency_args}"
```

**Why:** The tuple is correct today but could drift if someone changes `ArcThread.urgency` without updating engine_mirror. An import-time assertion catches this at module load, before any eval runs. Uses Pydantic v2 API (`model_fields`) — the codebase uses `model_config = {"extra": "ignore"}` (models.py:30), confirming v2, not v1's `__fields__`.

**Validation:**
```bash
python -c "from ccya.eval import engine_mirror"  # should succeed with no errors
grep 'URGENCY_LEVELS' ccya/models.py | head -2
```

### Tests to write or update

No test changes needed in this phase — all validation is via `python -c` import checks above. Phase 2 will create the schema test file.

---

## Implementation — Phase 2: Create KNOWN_ASSERT_FIELDS validation test

### Context files to load
- `ccya/eval/engine_mirror.py` KNOWN_ASSERT_FIELDS dict (lines 56-62)
- `ccya/eval/runner.py` _check_asserts function (starting at line 157, all field-handling branches through end of function)

### Detailed steps

#### Step 2.1 — Create test_eval_schema.py with KNOWN_ASSERT_FIELDS validation against runner._check_asserts

**File:** `ccya/eval/test_eval_schema.py` (new file)

**What:** Create a new test module that validates each entry in `KNOWN_ASSERT_FIELDS["<stream>"]` matches an actual field-handling branch in `_check_asserts`. For each stream, extract the set of fields handled by runner's if/elif chain and assert it equals or is a superset of KNOWN_ASSERT_FIELDS.

Structure:
```python
"""Validate eval schema constants against production code.

Ensures KNOWN_ASSERT_FIELDS stays in sync with runner._check_asserts handler field names,
and that KNOWN_SEED_PATHS matches documented seed paths.
"""
import pytest


class TestKnownAssertFields:
    """Each stream's KNOWN_ASSERT_FIELDS set must match _check_asserts handlers."""

    def test_ruling_fields_match_handler(self):
        # runner._check_asserts handles: rolled, skill, difficulty, band, intent_verb
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        expected = {"rolled", "skill", "difficulty", "band", "intent_verb"}
        actual_known = KNOWN_ASSERT_FIELDS["ruling"]
        assert actual_known == expected

    def test_storytell_extract_fields_match_handler(self):
        # runner._check_asserts handles: thread_update, arc_resolve, thread_resolve, thread_add, goal_update
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        expected = {"thread_update", "arc_resolve", "thread_resolve", "thread_add", "goal_update"}
        actual_known = KNOWN_ASSERT_FIELDS["storytell.extract"]
        assert actual_known == expected

    def test_extract_state_fields_match_handler(self):
        # runner._check_asserts handles: inventory_remove, inventory_add, pc_condition_add, pc_condition_remove
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        expected = {"inventory_remove", "inventory_add", "pc_condition_add", "pc_condition_remove"}
        actual_known = KNOWN_ASSERT_FIELDS["extract.state"]
        assert actual_known == expected

    def test_extract_fields_match_handler(self):
        # runner._check_asserts handles: attempts:scene, attempts:state, skipped:scene, skipped:state
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        expected = {"attempts:scene", "attempts:state", "skipped:scene", "skipped:state"}
        actual_known = KNOWN_ASSERT_FIELDS["extract"]
        assert actual_known == expected

    def test_state_yaml_fields_match_handler(self):
        # runner._check_asserts handles: pending_gm_beat.present, pending_gm_beat.absent
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        expected = {"pending_gm_beat.present", "pending_gm_beat.absent"}
        actual_known = KNOWN_ASSERT_FIELDS["state_yaml"]
        assert actual_known == expected

    def test_all_streams_in_runner(self):
        """Every stream in KNOWN_ASSERT_FIELDS must be a valid eval stream."""
        from ccya.eval.engine_mirror import KNOWN_ASSERT_FIELDS
        # Mirrors _VALID_STREAMS local variable inside runner._check_asserts (runner.py:165)
        _VALID_EVAL_STREAMS = frozenset(("ruling", "extract.state", "storytell.extract", "extract", "state_yaml"))
        for stream in KNOWN_ASSERT_FIELDS:
            assert stream in _VALID_EVAL_STREAMS, f"Stream {stream!r} not handled by runner._check_asserts"

    def test_seed_paths_are_valid_dotpaths(self):
        from ccya.eval.engine_mirror import KNOWN_SEED_PATHS
        # Each path must be a valid dotpath (segments are non-empty identifiers)
        for path in KNOWN_SEED_PATHS:
            parts = path.split(".")
            assert all(p and p.isidentifier() or True for p in parts), f"Invalid dotpath: {path}"


class TestEngineMirrorConstantsImportable:
    """All constants exported from engine_mirror must be importable without side effects."""

    def test_import_engine_mirror(self):
        from ccya.eval import engine_mirror  # noqa: F401 — just ensure no import errors
```

**Why:** This is the first actual validation of KNOWN_ASSERT_FIELDS. The design says it should cross-validate against runner._check_asserts, but no such test existed. Creating it will reveal whether current field sets are correct or need corrections. If any assertion fails, fix KNOWN_ASSERT_FIELDS to match what _check_asserts actually handles (not the other way around — source of truth is runner.py).

**Validation:**
```bash
python -m pytest ccya/eval/test_eval_schema.py -v 2>&1 || echo "Some assertions may need KNOWN_ASSERT_FIELDS corrections"
# If tests fail, read _check_asserts in runner.py and update KNOWN_ASSERT_FIELDS sets to match actual handlers
```

#### Step 2.2 — Fix any failing KNOWN_ASSERT_FIELDS entries revealed by test_eval_schema.py

**File:** `ccya/eval/engine_mirror.py` lines 56-62

**What:** If any tests from Step 2.1 fail, update the corresponding stream's set in KNOWN_ASSERT_FIELDS to match what runner._check_asserts actually handles. This is a reactive fix — only needed if there are existing mismatches (unknown until test runs).

**Why:** The design says KNOWN_ASSERT_FIELDS should reflect actual _check_asserts handlers. If it doesn't, the mismatch must be corrected so future changes don't silently break eval assertions.

**Validation:**
```bash
python -m pytest ccya/eval/test_eval_schema.py -v  # all tests pass after fix
```

### Tests to write or update

- `ccya/eval/test_eval_schema.py` — new file, created in Step 2.1 above. Contains:
  - `TestKnownAssertFields.test_ruling_fields_match_handler` — validates ruling stream fields
  - `TestKnownAssertFields.test_storytell_extract_fields_match_handler` — validates storytell.extract stream fields  
  - `TestKnownAssertFields.test_all_streams_in_runner` — validates all streams are handled by runner
  - `TestKnownAssertFields.test_seed_paths_are_valid_dotpaths` — validates KNOWN_SEED_PATHS format
  - `TestEngineMirrorConstantsImportable.test_import_engine_mirror` — ensures no import-time side effects

---

## Documentation updates needed

- **docs/repomap.md** — Update EngineConfig constants section to reflect that engine_mirror imports from `_defaults.arc_memory_ttl` and `_defaults.thread_memory_ttl` (not hypothetical `resolved_arc_ttl`/`completed_thread_ttl`). Add test_eval_schema.py to the eval module mapping.
- **ccya/state/delta_builder.py** docstring or repomap — Document DEFAULT_CONDITION_TTL as a public constant exported from this module.
