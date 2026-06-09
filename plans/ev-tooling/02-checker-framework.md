# Plan 02 — Checker framework + deterministic checker port

## Purpose

Build the checker library (`ccya/ev/checkers/`) with `@register_checker` decorator, `CheckerResult` type, event filtering, state access, and port all 11 deterministic checkers from the old `universal_asserts.py`.

## Problem Statement

The old eval harness has 24 ad-hoc assertion functions in `universal_asserts.py` (1051 lines) that return unstructured dicts with no standard interface, no registration, no field requirements declaration, and no cross-event filtering. Every checker re-implements the same event plumbing.

## Constraints

- Checker interface uses `@register_checker` decorator with metadata
- Checkers import engine constants directly (`ccya.engine.config`, `ccya.rules`) — no engine mirror
- Framework pre-filters events to turn-only unless checker opts in via `needs_non_turn_events=True`
- Checkers needing state access declare `needs_state=True` and receive `save_dir`
- Missing required fields: framework warns and skips that checker, doesn't crash
- Checker discovery: explicit imports in `checkers/__init__.py`

## Non-goals

- LLM-based checkers — phase 5
- `play`, `check`, `eval` commands — phase 3/4
- Deleting old universal_asserts.py — phase 6

## Solution

Create `ccya/ev/checkers/__init__.py` with the registry, decorator, `CheckerResult`, and `run_checker()`/`run_checkers()`. Create individual checker modules for each of the 11 deterministic checkers. Port logic from `universal_asserts.py` into the new interface.

## Firm decisions

- Explicit imports: `checkers/__init__.py` imports all checker modules
- Missing field behavior: framework pre-validates, warns, skips — does not crash
- Event filtering: turn-only by default; `needs_non_turn_events=True` for sanitizer_lifecycle
- State access: `needs_state=True` passes `save_dir` to checker; checker calls `load_current_state()`

## Risks, Ambiguities, and Blockers

- The old `universal_asserts.py` functions take `(event, prev_event)` and return dict. The new checkers take `(events: list[dict])` and return `CheckerResult`. Porting each checker requires understanding what `prev_event` means in the new multi-event context. For checkers that compare consecutive turns, the events list provides the full sequence.
- The old `event_window` parameter (used by some checkers for extended context) may not map cleanly to the new interface. Handle per-checker.

## Status

`open`

## Implementation

### Context files to load

- `ccya/eval/universal_asserts.py` (entire file — source for porting)
- `ccya/engine/config.py` line 86 (`EngineConfig` — engine constants for direct import)
- `ccya/rules.py` (momentum band mapping, VALID_SKILLS)
- `ccya/state/momentum.py` (MOMENTUM_MIN, MOMENTUM_MAX)
- `ccya/state/delta_builder.py` (PC_CONDITIONS_MAX, DEFAULT_CONDITION_TTL)
- `ccya/engine/turn.py` lines near PRESSURE_BEAT_TYPES import
- `ccya/engine/extraction.py` lines 62–101 (extraction_context shape)
- `docs/design/ev-tooling-design.md` sections 4 (Checker library) and New Model Shapes

### Detailed steps

#### Step 2.1 — Create `ccya/ev/checkers/__init__.py`

**File:** `ccya/ev/checkers/__init__.py`

**What:** Checker framework with:

```python
@dataclass
class CheckerResult:
    checker_id: str
    passed: bool | None        # None = inconclusive
    score: float | None        # 0.0-1.0
    detail: str
    findings: list[dict] = field(default_factory=list)
    ms: float = 0.0

CHECKER_META = "__checker_meta__"
class CheckerMeta(TypedDict):
    id: str
    type: Literal["deterministic", "llm"]
    requires_fields: list[str]
    description: str
    needs_non_turn_events: bool
    needs_state: bool

_checker_registry: dict[str, Callable] = {}

def register_checker(
    id: str,
    type: Literal["deterministic", "llm"],
    requires_fields: list[str],
    description: str,
    needs_non_turn_events: bool = False,
    needs_state: bool = False,
) -> Callable:
    """Decorator that registers a checker function.
    Attaches CheckerMeta to the function and adds it to _checker_registry."""

def run_checker(checker_id: str, events: list[dict], save_dir: Path | None = None) -> CheckerResult:
    """Run a single checker. Pre-filters events, validates required fields,
    loads state if needed, times execution, returns CheckerResult."""

def run_checkers(checker_ids: list[str], events: list[dict], save_dir: Path | None = None) -> dict[str, CheckerResult]:
    """Run multiple checkers, return {checker_id: result}."""

def list_checkers(checker_type: str | None = None) -> list[CheckerMeta]:
    """Return metadata for all registered checkers, optionally filtered by type."""
```

Key behaviors in `run_checker()`:
1. Look up checker in registry. If not found, return `CheckerResult(passed=None, detail=f"unknown checker: {checker_id}")`.
2. If `needs_non_turn_events=False`, filter events to turn-only using `events.filter_turn_events()`.
3. Validate required fields: for each field in `requires_fields`, check that at least one event has a non-None value at that dotpath. If a field is entirely absent, log warning and return `CheckerResult(passed=None, detail="required field '{field}' not found in any event")`.
4. If `needs_state=True`, load state via `events.load_current_state(save_dir)`. If `save_dir is None`, return error result.
5. Call the checker function with `(events)` or `(events, state)` depending on `needs_state`.
6. Measure wall-clock time (`ms` field).
7. Return the `CheckerResult`.

Explicit imports at module bottom:
```python
from . import momentum, gm_beat, inventory, conditions, threads, arc_goals, npc_presence, pacing, action_quality, sanitizer
```

**Why:** The registry pattern decouples checker registration from discovery. The framework pre-filtering and field validation reduces boilerplate in every checker. Explicit imports prevent silent failures.

**Validation:** `python -c "from ccya.ev.checkers import list_checkers; print([c['id'] for c in list_checkers()])"` lists all 11 checkers.

#### Step 2.2 — Port `momentum_lifecycle` checker

**File:** `ccya/ev/checkers/momentum.py`

**What:**

```python
@register_checker(
    "momentum_lifecycle", "deterministic",
    requires_fields=["ruling.band", "momentum_before", "momentum_after", "applied"],
    description="Verify momentum delta matches roll band",
)
def momentum_lifecycle(events: list[dict]) -> CheckerResult:
```

Port from `universal_asserts.py`:
- `check_momentum_band_delta()` — verify delta matches momentum_delta[band]
- `check_momentum_floor_no_relief()` — verify no floor-relief when not beat_locked and momentum is not at floor
- Also verify momentum stays within [MOMENTUM_MIN, MOMENTUM_MAX]

Import constants: `from ccya.rules import MOMENTUM_DELTA`, `from ccya.state.momentum import MOMENTUM_MIN, MOMENTUM_MAX`.

**Why:** Momentum correctness is the highest-signal mechanical invariant. Catching a bad delta or floor violation catches the most common engine bugs.

**Validation:** Run against current events file. Verify it passes on known-good data. Manually corrupt a momentum value in a test event and verify it fails.

#### Step 2.3 — Port `gm_beat_lifecycle` checker

**File:** `ccya/ev/checkers/gm_beat.py`

**What:**

```python
@register_checker(
    "gm_beat_lifecycle", "deterministic",
    requires_fields=["state_snapshot", "momentum_before", "momentum_after",
                     "ruling", "narrate_prompt"],
    description="Verify pending_gm_beat is consumed, floor relief injected, binding present on roll",
)
def gm_beat_lifecycle(events: list[dict]) -> CheckerResult:
```

Port from `universal_asserts.py`:
- `check_pending_gm_beat_consumed()` — pending_gm_beat from prior turn must be absent or replaced this turn
- `check_pending_gm_beat_lifecycle_respected()` — pending_gm_beat should appear/clear correctly
- `check_floor_relief_injection()` — floor relief injects breathing_room when conditions are met
- `check_beat_locked_dual_trigger()` — beat_locked flag and pending_gm_beat interplay
- `check_rolled_implies_binding()` — if `ruling.rolled=true`, `narrate_prompt.rendered_user` must contain "rules_outcome (BINDING" block

**Validation:** Run against events file. Verify beat lifecycle checks pass.

#### Step 2.4 — Port `location_change` checker

**File:** `ccya/ev/checkers/gm_beat.py` (same file — location is part of GM beat mechanics) or its own file `ccya/ev/checkers/inventory.py` (keep with other state checkers)

**Decision: Put in `ccya/ev/checkers/inventory.py`** — location is a state mutation, closer to inventory than GM beat.

```python
@register_checker(
    "location_change", "deterministic",
    requires_fields=["applied.location_change", "extraction_context.location_this_turn"],
    description="Verify location changes are applied correctly",
)
def location_change(events: list[dict]) -> CheckerResult:
```

Port from `universal_asserts.py`:
- `check_location_change_applied()` — if applied has location_change, extraction_context should reflect it

#### Step 2.5 — Port `inventory_integrity` checker

**File:** `ccya/ev/checkers/inventory.py`

**What:**

```python
@register_checker(
    "inventory_integrity", "deterministic",
    requires_fields=["applied.inventory_add", "applied.inventory_remove",
                     "extraction_context.inventory_this_turn"],
    description="No overdraw, no negative amounts, remove existence",
)
def inventory_integrity(events: list[dict]) -> CheckerResult:
```

Port from `universal_asserts.py`:
- `check_zero_stack_overdraw()` — inventory_remove where amount would go below 0
- `check_no_negative_inventory()` — no negative amounts
- `check_inventory_remove_existence()` — remove references an item that existed

#### Step 2.6 — Port `conditions_lifecycle` checker

**File:** `ccya/ev/checkers/conditions.py`

**What:**

```python
@register_checker(
    "conditions_lifecycle", "deterministic",
    requires_fields=["applied.pc_condition_add", "applied.pc_condition_remove",
                     "extraction_context.conditions_this_turn"],
    description="Dedup, cap, TTL for PC conditions",
)
def conditions_lifecycle(events: list[dict]) -> CheckerResult:
```

Port from `universal_asserts.py`:
- `check_conditions_in_reason()` — conditions referenced in outcome_summary reasons
- Dedup check — no duplicate condition IDs
- Cap check — conditions_this_turn <= PC_CONDITIONS_MAX

Import: `from ccya.state.delta_builder import PC_CONDITIONS_MAX, DEFAULT_CONDITION_TTL`.

#### Step 2.7 — Port `thread_lifecycle` checker

**File:** `ccya/ev/checkers/threads.py`

**What:**

```python
@register_checker(
    "thread_lifecycle", "deterministic",
    requires_fields=["extraction.storytell", "state_snapshot"],
    description="thread_add applied, thread_update IDs valid",
)
def thread_lifecycle(events: list[dict]) -> CheckerResult:
```

Port from `universal_asserts.py`:
- `check_thread_add_applied()` — thread_add in extraction should appear in state_snapshot
- `check_thread_update_id_valid()` — thread_update references valid thread IDs

#### Step 2.8 — Port `arc_goal_updates` checker

**File:** `ccya/ev/checkers/arc_goals.py`

**What:**

```python
@register_checker(
    "arc_goal_updates", "deterministic",
    requires_fields=["extraction.storytell", "state_snapshot"],
    description="goal_update overwrites visible_goal",
)
def arc_goal_updates(events: list[dict]) -> CheckerResult:
```

Port from `universal_asserts.py`:
- `check_goal_update_applied()` — if extraction has goal_update, state_snapshot should reflect it

#### Step 2.9 — Port `npc_presence` checker

**File:** `ccya/ev/checkers/npc_presence.py`

**What:**

```python
@register_checker(
    "npc_presence", "deterministic",
    requires_fields=["extraction_context", "applied.compendium_npc_update"],
    description="NPC extraction, presence tags, scene cap",
)
def npc_presence(events: list[dict]) -> CheckerResult:
```

Port from `universal_asserts.py`:
- Check NPC presence extraction matches applied compendium_npc_update
- Check for unreasonable NPC count per scene
- `check_no_removed_npc_states()` — removed NPC states (JUST_LEFT, recently_left) must not reappear in state_snapshot or narrate prompt

#### Step 2.10 — Port `pacing_directives` checker

**File:** `ccya/ev/checkers/pacing.py`

**What:**

```python
@register_checker(
    "pacing_directives", "deterministic",
    requires_fields=["ruling", "narrate_prompt", "extraction_context"],
    description="Directive rendering, known values",
)
def pacing_directives(events: list[dict]) -> CheckerResult:
```

Port from `universal_asserts.py`:
- `check_consecutive_pressure_tracking()` — consecutive_pressure counter increments correctly
- `check_outcome_hint_rendered()` — outcome_hint from ruling appears in narrate prompt
- `check_directive_rendered_storytell()` — directive from pacing context appears in storytell
- `check_no_removed_directives()` — no directives that aren't recognized
- `check_beat_type_variety()` — beat types don't repeat monotonously
- `check_surface_as_consistency()` — surface_as doesn't flip without directive change

#### Step 2.11 — Port `action_quality` checker

**File:** `ccya/ev/checkers/pacing.py` (same file — closely related to pacing) or its own file

**Decision: Put in `ccya/ev/checkers/pacing.py`**

```python
@register_checker(
    "action_quality", "deterministic",
    requires_fields=["actions", "ruling"],
    description="Action count, distinctness, variety",
)
def action_quality(events: list[dict]) -> CheckerResult:
```

Port from `universal_asserts.py`:
- `check_actions_count_and_distinct()` — at least 1 action, actions are distinct, no duplicates

#### Step 2.12 — Port `sanitizer_lifecycle` checker

**File:** `ccya/ev/checkers/sanitizer.py`

**What:**

```python
@register_checker(
    "sanitizer_lifecycle", "deterministic",
    requires_fields=["threads_updated", "threads_removed", "threads_resolved",
                    "threads_added", "goal_changed", "changes_detail"],
    needs_non_turn_events=True,
    needs_state=True,
    description="Verify sanitizer thread operations are valid against current state",
)
def sanitizer_lifecycle(events: list[dict], state: dict) -> CheckerResult:
```

This checker receives the full unfiltered event list (including sanitizer events) and the current state dict. It:
1. Filters to `kind: "sanitizer"` events
2. For each sanitizer event, verifies:
   - `threads_updated` IDs exist in `state.arc.threads`
   - `threads_removed` IDs exist in `state.arc.threads` (before removal)
   - `threads_resolved` threads have resolution data
   - `threads_added` IDs don't conflict with existing threads
   - `goal_changed`: verify `changes_detail.goal.after` is different from `changes_detail.goal.before`
3. No orphan threads after sanitizer operations

This checker has no direct counterpart in `universal_asserts.py` — it's new logic that inspects sanitizer event data and cross-references it against live state.

**Validation:** Run against events file with known sanitizer events. Verify pass/fail correctly reports thread validity.

### Tests to write or update

Manual verification (no test automation in this phase):

1. `python -c "from ccya.ev.checkers import list_checkers; print(len(list_checkers()))"` → 11
2. `python -c "from ccya.ev.checkers import run_checker; r = run_checker('momentum_lifecycle', events); print(r.passed)"` → True on known-good data
3. Create a temporary test events file with a deliberate momentum error (e.g., incorrect delta for band). Run `momentum_lifecycle` checker against it. Verify it FAILs.
4. Create a temporary test events file with a sanitizer event that references a non-existent thread ID. Run `sanitizer_lifecycle` checker. Verify it FAILs.
