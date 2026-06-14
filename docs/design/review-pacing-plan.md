## Review: pacing-directive-beat-constraint.md

### Summary
Plan is structurally sound with clear phases and dependency ordering. Three issues found and fixed. Two maintainability concerns flagged. Verdict: **approved with notes**.

### Fixes applied

1. **Step 1.4 — `PacingContext.neutral()` reference** — Source shows no `neutral()` factory exists on `PacingContext`. Replaced with "just add the field with a default value; all existing construction sites (e.g., `_compute_pacing_context()` at line 480) will continue to work."

2. **Phase count (line 52)** — Stated "4 phases" but Phase 5 (close plan) exists. Changed to "5 phases."

3. **Step 2.3 — Missing second call site** — `derive_allowed_beat_types()` is called at two places: `extraction.py:275-282` (storytell prompt) and `turn.py:1349-1356` (event logging). The plan only mentioned extraction.py. Expanded Step 2.3 to cover both sites, plus added `spiral_detected` to the event log's `pacing_context` dict at `turn.py:1339-1342`.

4. **Phase 5 format** — Missing "Context files to load" and "Tests to write or update" sections. Added both.

5. **Step 1.2 — Missing import** — `detect_spiral()` uses `dict[str, Any]` but `_pacing.py` only imports `EngineConfig`. Added a note: "Add `from typing import Any` to imports."

### Findings requiring user input

- **maintainability** Config field `spiral_decay_turns` has no consumer. `detect_spiral()` doesn't accept it — the rolling window is the implicit decay mechanism (old hard rolls fall off the 5-entry window as new non-hard rolls come in). The config field will silently do nothing. Options: (a) keep it as reserved/forward-looking, (b) remove it until a consumer exists. `[QUESTION: keep spiral_decay_turns as dead config or remove from Step 1.1?]`

- **maintainability** Checker `ccya/ev/checkers/pacing.py:119` calls `derive_allowed_beat_types(scene_phase)` without directive/spiral params. It will still compile (default params), but it won't validate directive/spiral constraints — checks will pass when they shouldn't. Should be updated to read `directive` and `spiral_detected` from the event's `pacing_context` dict (which Step 2.3 now populates). Scope question: this touches the ev/checkers module which is outside the explicitly stated non-goals but is necessary for correctness of the checkers.

### Contract checks

- [x] `derive_allowed_beat_types()` signature change (additive keyword params) — call sites: `extraction.py:275`, `turn.py:1349`, `ev/checkers/pacing.py:119`. All use keyword-only args with defaults — backward compatible. ✅
- [x] `PacingContext` new field `spiral_detected: bool = False` — construction site at `turn.py:480` uses positional args (no spiral_detected), but it has a default, so unchanged. Dict access in event logging at `turn.py:1340-1342` cherry-picks fields explicitly — needs manual addition (covered in Step 2.3 fix). ✅
- [x] Template variables — `narrate_user.j2` and `storytell_user.j2` both receive `pacing_context` dict with full `PacingContext` fields. New field flows through automatically. `storytell_system.j2` does not receive pacing_context (uses fixed guidance text). ✅
- [x] `_narrate_messages()` signature — already accepts `pacing_context`, no change needed. ✅
- [x] `_run_extraction_pipeline()` — already accepts `pacing_context`, passes to `_storytell_messages()`. ✅
- [ ] `spiral_decay_turns` config field — **no consumer exists**. `detect_spiral()` doesn't reference it. See finding above.

### Scope violations
None. All changes stay within pacing/beat constraint system. Checker update would be scope-adjacent but is flagged as a question, not a step.

### Format issues
All resolved (phase count, Phase 5 section headers, missing import note).
