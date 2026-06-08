# Tech Debt: Dead Code Removal (7 items)

## Purpose

Remove 28 dead dataclass fields, 3 unused parameters, 1 identity stub function, 1 unused Jinja filter registration, 1 vestigible config export, and 2 never-consumed event dict fields — reducing code surface area with zero behavioral change.

## Problem Statement

The engine contains accumulated dead code from refactors: a dataclass (`TurnContext`) with 28 fields that are written to defaults but never read back, three unused function parameters accepted at call sites, an identity stub function called once for no effect, and two event dict entries written every turn but consumed by zero server handlers. These items inflate the codebase, confuse future readers about what's alive vs dead, and bloat events.jsonl with unnecessary data.

## Constraints

- **Zero behavioral change.** Every removal must be provably safe — no attribute access (direct or via `getattr`), no dict-style access (`ctx["field"]`), no template consumption of the removed event fields.
- **No tests to run** — test suite is temporarily disabled per AGENTS.md lint workflow rules.
- **Trust the exploration validation.** All 28 TurnContext deadness claims were validated by a thorough codebase search (no getattr, no dict access, templates reference `TurnResult` not `TurnContext`).

## Non-goals

- Fixing `_cancel_requested` Event objects never created — cancel signal dead (`config.py:36`)
- Fixing `momentum_ceiling` config setting silently ignored (`config.py:121,150-213`)
- Consolidating 5 identical `_strip_non_ascii` definitions across files (higher effort, different concern)
- Removing the entire TurnContext dataclass — only dead fields are removed; alive ones stay
- Fixing overly long functions (`run_turn`, `_run_extraction_pipeline`, `summarize_changes`)

## Solution

Surgical deletions organized into 4 phases by shared file: (1) config.py removes unused Jinja filter and vestigible export, (2) extraction.py removes identity stub function and its call site plus one unused parameter, (3) turn.py removes two never-consumed event dict fields then the 28 dead TurnContext dataclass fields, (4) changes.py removes one unused parameter with updated call site. Each phase is independently executable with no cross-phase dependencies except that they're all independent surgical fixes within their respective files.

## Firm decisions

1. All 28 flagged TurnContext fields are confirmed dead by exhaustive search — safe to delete from the dataclass definition only (not from templates/routes which reference `TurnResult`, not `TurnContext`).
2. `_check_npc_ghost_cycle` is a pure identity function (`return scene_result`) called once at extraction.py:457 — deletion of both definition and call site has zero behavioral impact.
3. The ellipsis truncation bug (`changes.py:40`) was already fixed by prior refactoring — code no longer exists in current source. Not included in this plan.

## Risks, Ambiguities, and Blockers

- **TurnContext alive fields must be preserved.** The dataclass has 12+ alive fields (`state`, `user_input`, `_rendered_ruling_system`, etc.) that are written to AND read from later phases of the same turn. Must carefully distinguish dead vs alive before deletion.
- **`_applied` parameter name collides with helper function.** The private helper `_summarize_applied()` at changes.py:15 uses `applied` as its own local parameter — this is unrelated to the unused `_applied` parameter in `summarize_changes()`. Must not confuse them.
- **No rollback path needed** since each change is a deletion with zero behavioral impact, but git history preserves everything if something breaks.

## Status

`completed`

---

# Phases: 4 phases — config.py cleanup, extraction.py cleanup, turn.py cleanup (event fields + TurnContext dead fields), changes.py parameter removal

---

## Implementation — Phase 1: Remove unused Jinja filter and vestigible export from config.py

### Context files to load
- `ccya/engine/config.py` (lines 61-78 for `pop_persist_started`, lines 291-302 for `_strip_turn_prefix`)
- `ccya/engine/__init__.py` (line 10 import, line 29 export)

### Detailed steps

#### Step 1.1 — Remove `_strip_turn_prefix` Jinja filter registration

**File:** `ccya/engine/config.py`

**What:** Delete the function definition at lines 291-294 (`def _strip_turn_prefix(s: str) -> str:` through its body) and delete line 302 (`env.filters["strip_turn_prefix"] = _strip_turn_prefix`). No `.j2` template in `ccya/prompts/` uses `|strip_turn_prefix`.

**Why:** The filter is registered but never invoked — no Jinja templates use it, no Python code calls it as a plain function. Dead registration inflates the module and confuses future readers about what's alive.

**Validation:** Verify no template references:
```bash
grep -r 'strip_turn_prefix' ccya/prompts/ 2>/dev/null; echo "exit: $?"
# Expected exit code 1 (no matches)
```

#### Step 1.2 — Remove `pop_persist_started` from config.py and __init__.py

**File:** `ccya/engine/config.py`, line 61-62 (`def pop_persist_started(...)`)

**What:** Delete the function definition at lines 61-62 (`def pop_persist_started(save_dir: str) -> bool:`). Also delete its call at line 78 inside `signal_turn_done()` — this is vestigible because the cancel endpoint now reads `state_snapshot` from events instead of using this flag. The return value was already discarded at the sole call site (`signal_turn_done`).

**File:** `ccya/engine/__init__.py`, lines 10 and 29

**What:** Remove `pop_persist_started,` from the import block (line 10) and from `__all__` (line 29). No external consumer reads its value.

**Why:** The cancel endpoint was rewritten to read state_snapshot directly from events.jsonl (see completed plan `event-based-state-restore.md`). This function's return is never consumed — it was a vestige of the old snapshot-restore approach that remains after the rewrite.

**Validation:** Verify no external usage:
```bash
grep -r 'pop_persist_started' --include='*.py' ccya/ | grep -v '__pycache__'
# Expected output: only config.py (definition) and __init__.py (import/export) — no routes.py, server/, or other consumers
```

---

## Implementation — Phase 2: Remove identity stub function and unused parameter from extraction.py

### Context files to load
- `ccya/engine/extraction.py` (lines 105-112 for `_check_npc_ghost_cycle`, line 457 for call site, lines 228-233 for `_storytell_messages` signature)

### Detailed steps

#### Step 2.1 — Remove `_check_npc_ghost_cycle` identity stub function and its single call site

**File:** `ccya/engine/extraction.py`, lines 105-112 (`def _check_npc_ghost_cycle(...)`)

**What:** Delete the entire function definition (lines 105-112). Then delete line 457 (`scene_result = _check_npc_ghost_cycle(scene_result, state, trace_id=trace_id, turn_no=turn_no)`) — this is a no-op assignment since the function returns its input unchanged.

**Why:** The function accepts `scene_result`, `state`, `trace_id`, and `turn_no` but never reads any of them — it just returns `scene_result`. Ghost-cycle detection was never implemented (per TECH-DEBT.md). Deleting both definition and call site has zero behavioral impact: the variable already holds the correct value from `_call_stream()` at line 454.

**Validation:** Verify no other callers exist:
```bash
grep -n '_check_npc_ghost_cycle' ccya/engine/extraction.py
# Expected output: only lines 105 (definition) and 457 (call site) — both being deleted
```

#### Step 2.2 — Remove unused `state_result` parameter from `_storytell_messages`

**File:** `ccya/engine/extraction.py`, line 233 (`state_result: StateExtractResult | None = None,`)

**What:** Delete the `state_result: StateExtractResult | None = None,` parameter from the function signature at lines 228-241. Then delete the argument at call site line 540 (`state_result=state_result,`).

**Why:** The parameter is accepted in the signature and passed at the call site (line 539) but never referenced anywhere inside the function body (lines 242-287+). It's a stale parameter from an earlier design. Removing it reduces API surface with no behavioral change.

**Validation:** Verify `state_result` is not used in `_storytell_messages`:
```bash
# Check that state_result only appears at lines 233 (param) and 540 (call site) within this file
grep -n 'state_result' ccya/engine/extraction.py | grep -E '^2[2-9][0-9]:|^3[0-9][0-9]:' || echo "No usage in function body"
# Expected: no matches between lines 242-287+ (function body)
```

---

## Implementation — Phase 3: Remove never-consumed event fields and TurnContext dead dataclass fields from turn.py

### Context files to load
- `ccya/engine/turn.py` (lines 1435-1452 for event dict entries, lines 72-126 for TurnContext dataclass)

### Detailed steps

#### Step 3.1 — Remove never-consumed `narrate_summary` and `extraction_context` from events.jsonl writes

**File:** `ccya/engine/turn.py`, lines 1440-1452 (`"narrate_summary": {...}` through `"extraction_context": {...},`)

**What:** Delete the two event dict entries at lines 1439-1452:
```python
# narrate_summary block (lines 1438-1445) — delete comment + key-value pair
# extraction_context block (lines 1446-1452) — delete entire key-value pair
```

**Why:** These two fields are written into every turn event dict in events.jsonl. No server code reads them: `tv.py`, `routes.py`, `metrics.py`, and `panels.py` all checked (per TECH-DEBT.md). They bloat the JSONL files with ~20 lines of unnecessary data per turn, increasing file size without providing any downstream value.

**Validation:** Verify no server code consumes these fields:
```bash
grep -rn 'narrate_summary\|extraction_context' --include='*.py' ccya/server/ 2>/dev/null || echo "No server consumers found"
# Expected: no matches (or only comments)
```

#### Step 3.2 — Remove 28 dead dataclass fields from TurnContext

**File:** `ccya/engine/turn.py`, lines 92-126 (`TurnContext` dataclass body after alive constructor args and alive internal tracking fields)

**What:** Delete the following dead fields from the `TurnContext` dataclass (lines 92-126). Keep only the **alive** fields:
- Lines 74-82: Constructor args (`state`, `user_input`, `turn_no`, `trace_id`, `config`, `recent_turns`, `save_dir`, `packing`) — KEEP ALL
- Line 84: `_env` — KEEP (set at ~line 930, read later)
- Lines 85-86: `_rendered_ruling_system`, `_rendered_ruling_user` — KEEP (written + read in ruling phase)
- Lines 87-90: `_ruling_raw_response`, `_ruling_parse_error`, `_ruling_trimmed`, `_ruling_trimmed_chars` — KEEP (all written at lines 734-737, read at lines 999-1002)
- Line 97: `_avoidance` — KEEP (written line 703, read line 891)
- Line 100: `_ages` — KEEP (written line 809, read lines 915, 929)
- Line 103: `_deescalate` — KEEP (written line 993, read line 889)

**Delete these dead fields:**
```python
# Lines 92-94 — DEAD
_narr_system: str = ""
_narr_user: str = ""
_narr_trimmed: bool = False
_narr_trimmed_chars: int = 0

# Line 95-96 — DEAD (set at lines 1018-1019, never read)
_rendered_narr_system: str = ""
_rendered_narr_user: str = ""

# Lines 98-99 — DEAD (never written or read; momentum is accessed via state.get())
_momentum_before: float | None = None
_momentum_after: float | None = None

# Line 101 — DEAD (set at line 878, never read)
_npc_name_pool: dict[str, list[str]] | None = None

# Lines 102-103 — DEAD (_pending_gm_beat set at line 879 but pending_gm_beat lives in state.meta now)
_pending_gm_beat: dict[str, Any] | None = None

# Line 106 — DEAD (moved to game state; TurnContext field is remnant)
pending_gm_beat: dict[str, Any] | None = None

# Lines 110-126 — ALL DEAD (phase output fields never assigned or read from ctx)
narrative: str | None = None
narrative_chunks: list[str] | None = None
extraction_result: Any = None
delta: StateDelta | None = None
actions: list[str] | None = None
outcome_summary: str | None = None
extraction_event: dict[str, Any] | None = None
storyteller_result: StorytellerResult | None = None
scene_result: SceneExtractResult | None = None
extraction_ctx: Any = None
errors: list[dict[str, Any]] | None = None
metrics: dict[str, Any] | None = None
ruling_metrics: dict[str, Any] | None = None
narr_metrics: dict[str, Any] | None = None
ext_metrics: dict[str, Any] | None = None
applied: dict[str, Any] | None = None
rejected: list[dict[str, Any]] | None = None
```

**Why:** All 28 fields are confirmed dead by exhaustive search — no direct attribute access (`ctx.field`), no `getattr()` calls, no dict-style access (`ctx["field"]`). Templates and routes reference `TurnResult` (the return value from `run_turn`) or recent-turns dicts, not `TurnContext` instances. These were accumulated over multiple refactors where the data was moved to local variables but the dataclass fields remained as defaults.

**Validation:** Verify no attribute access on TurnContext for deleted fields:
```bash
# Check that none of these field names appear after a dot in ctx/turn_ctx variable usage patterns
grep -n '\._narr_system\|\.narrative_chunks\|\.extraction_result\|\.delta\b\.\|\.actions\b\.\|\.outcome_summary\|\.storyteller_result\|\.scene_result\|\.extraction_ctx\|\.ruling_metrics\|\.narr_metrics\|\.ext_metrics\|\.applied\b\.\|\.rejected\b' ccya/engine/turn.py || echo "No attribute access found"
# Expected: no matches (grep may find false positives in dataclass definitions themselves)

# Verify alive fields are still present after deletion
grep -n '_rendered_ruling_system\|_avoidance\|_ages\|_deescalate\|intent\b\|outcome\b\|pacing_ctx' ccya/engine/turn.py | head -20
# Expected: all alive fields still referenced in the file
```

---

## Implementation — Phase 4: Remove unused parameter from summarize_changes and update call site

### Context files to load
- `ccya/engine/changes.py` (lines 71-76 for function signature)
- `ccya/engine/turn.py` (line 1381 for call site)

### Detailed steps

#### Step 4.1 — Remove unused `_applied` parameter from summarize_changes and update call site

**File:** `ccya/engine/changes.py`, line 74 (`_applied: dict[str, Any],`)

**What:** Delete the `_applied: dict[str, Any],` parameter from the function signature at lines 71-76. The helper function `_summarize_applied()` at changes.py:15 uses `applied` as its own local parameter — this is unrelated and must NOT be touched.

**File:** `ccya/engine/turn.py`, line 1381 (`changes = summarize_changes(state_pre_apply, state, applied, rejected)`)

**What:** Remove the third positional argument (`applied`) from the call site:
```python
# Before:
changes = summarize_changes(state_pre_apply, state, applied, rejected)
# After:
changes = summarize_changes(state_pre_apply, state, rejected)
```

Wait — this changes the parameter order. Let me re-check the signature to determine if it's positional or keyword at the call site. The function is `summarize_changes(pre, post, _applied, rejected)` with 4 parameters. At the call site it passes 4 args positionally: `(state_pre_apply, state, applied, rejected)`. After removing `_applied`, the new signature becomes `summarize_changes(pre, post, rejected)` — so the call must change from 4 to 3 positional arguments.

**Why:** The parameter is accepted at lines 71-76 but never referenced anywhere inside the function body (confirmed by grep showing only two hits: line 15 for unrelated helper `_summarize_applied`, and line 74 in the signature). This reduces API surface with no behavioral change.

**Validation:** Verify `_applied` is not used in `summarize_changes`:
```bash
# Check that _applied only appears at changes.py:74 (signature) — nowhere else in the function body
grep -n '_applied' ccya/engine/changes.py
# Expected output: line 15 (_summarize_applied helper, unrelated), line 74 (parameter being removed)

# Verify call site after change:
grep -n 'summarize_changes(' ccya/engine/turn.py | grep -v '#'
# Expected: exactly one match at turn.py:1381 with 3 args instead of 4
```

---

## Tests to write or update

None — test suite is temporarily disabled per AGENTS.md lint workflow rules (`Tests are temporarily removed during refactor. Do not write or reference tests until this phase is complete.`).

Run `make check` (lint + typecheck) as a final step after all 4 phases are complete, per AGENTS.md instructions.
