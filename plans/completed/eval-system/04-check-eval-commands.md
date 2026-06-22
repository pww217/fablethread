# Plan 04 — `check` + `eval` commands

## Purpose

Implement `ev.py check` (run checkers against existing events) and `ev.py eval` (batch scenario runner with YAML scenarios and TurnAssert support).

## Problem Statement

Running a checker currently requires writing a Python scenario and running the full eval harness. There is no `ev.py check 5 momentum_lifecycle` — the only path is a 30s+ eval run with 4 LLM calls. Similarly, batch evaluations require authored Python scenario files with no YAML option.

## Constraints

- `check` uses the checker library from phase 2
- `eval` uses `play_turn()` from phase 3 for game execution
- YAML scenarios with optional `asserts` (structured assertions per-turn)
- `check` commands run deterministically by default; `--llm` flag includes LLM checkers
- Data flow: `check` reads existing events.jsonl; `eval` plays a scenario then checks

## Non-goals

- LLM-based checkers — phase 5
- Multi-run trend tracking (time-series dashboards)
- Web UI for results

## Solution

Implement `cmd_check()` in `ccya/ev/check.py` and `cmd_eval()` in `ccya/ev/eval.py`. The check command iterates the checker registry and runs requested checkers against specified turns. The eval command parses YAML, plays each turn, runs all checkers, and produces a Markdown report.

## Firm decisions

- `check <turn> --all` runs all deterministic checkers on one turn
- `check <turn> <checker>` runs specific checkers on one turn
- `check --all` runs all deterministic checkers on all turns
- `--llm` flag includes LLM-based checkers (loaded in phase 5)
- YAML scenarios support optional `asserts` per-turn with `stream`, `field`, `expected`, and `min_amount`
- Structured assertions are validated by a built-in `turn_assert` checker, not custom checker code

## Risks, Ambiguities, and Blockers

- `check --all` on all turns could be slow if there are many turns. Each checker iterates all events. With 11 checkers and 25 turns, that's 275 checker-event evaluations, each doing field extraction and logic. Should still be sub-second for deterministic checkers.
- The `turn_assert` checker needs to understand the event shape and the dotpath extraction system built in phase 1. It must correctly map stream names to event fields.

## Status

`completed`

## Implementation

### Context files to load

- `ccya/ev/checkers/__init__.py` (registry, run_checker, run_checkers — from phase 2)
- `ccya/ev/events.py` (load_events, filter_turn_events — from phase 1)
- `ccya/ev/play.py` (play_turn — from phase 3)
- `ccya/eval/scenario.py` (old Scenario/Turn/TurnAssert dataclasses — reference for YAML schema)
- `ccya/models.py` line 508 (TurnResult — for event persistence from play_turn)

### Detailed steps

#### Step 4.1 — Create `ccya/ev/check.py`

**File:** `ccya/ev/check.py`

**What:** Check command implementation.

`cmd_check(events, turn=None, checker_ids=None, all_checkers=False, include_llm=False, save_dir=None)`:

1. Determine which checkers to run:
   - If `checker_ids` provided: use those
   - If `all_checkers=True`: use `list_checkers(type="deterministic")` (plus LLM if `include_llm=True`)
2. Determine which turns to check:
   - If `turn` provided: filter events to that turn (use `find_turn`)
   - If `turn` is None and `check —all`: iterate all turn events
3. For each (checker, turn_event) pair:
   - Build events list for the checker: `[turn_event]` (single turn context for most checkers) or the full event sequence for checkers that need cross-turn context
   - Call `run_checker(checker_id, events, save_dir)`
   - Collect results
4. Format results as Markdown

Output format (per design doc):
```
$ ev.py check 5 momentum_lifecycle
## momentum_lifecycle: PASS (score: 1.0)

| Turn | Finding | Detail |
|------|---------|--------|
| 5 | correct_direction | band=success, momentum +1->+2 |

$ ev.py check 5 --all
## momentum_lifecycle: PASS (score: 1.0)
## gm_beat_lifecycle:  PASS (score: 1.0)
## inventory_integrity: FAIL (score: 0.0)

| Turn | Finding | Detail |
|------|---------|--------|
| 5 | overdraw | inventory_remove lockpick_set x1 but only x0 available |
```

CLI interface:
```
ev.py check <turn> <checker> [<checker> ...]       # Specific checkers on one turn
  --events <path>                                   # Events file (default: saves/default/events.jsonl)

ev.py check <turn> --all                            # All deterministic checkers on one turn
  --llm                                             # Include LLM-based checkers

ev.py check --all                                   # All deterministic checkers on all turns
```

**Why:** The check command is the lightweight path to mechanical verification. It's the primary debugging tool for "did this mechanic work correctly?"

**Validation:**
1. `ev.py check 5 momentum_lifecycle` against known-good data → PASS
2. `ev.py check 5 --all` → all checkers run, output shows each result
3. `ev.py check --all` → runs against all turns, shows per-checker summary

#### Step 4.2 — Create YAML scenario parser

**File:** `ccya/ev/scenario.py`

**What:** YAML-based scenario loading with structured assertions.

Data model:
```python
@dataclass
class TurnAssert:
    stream: str          # e.g. "ruling", "extract.state", "extraction_context"
    field: str           # e.g. "skill", "inventory_remove"
    expected: str | None = None
    min_amount: int | None = None

@dataclass
class ScenarioTurn:
    input: str
    expects: list[str] = field(default_factory=list)
    asserts: list[TurnAssert] = field(default_factory=list)

@dataclass
class Scenario:
    id: str
    pack: str
    description: str
    seed_overrides: dict = field(default_factory=dict)
    turns: list[ScenarioTurn]
```

YAML format:
```yaml
id: momentum_basics
pack: eval-pack
description: Verify momentum moves correctly through a sequence
seed_overrides:
  meta.momentum: 0
turns:
  - input: "Try to kick the door down"
    expects: "roll with strength"
    asserts:
      - stream: ruling
        field: skill
        expected: strength
      - stream: extract.state
        field: inventory_remove
        expected: lockpick_set
        min_amount: 1
  - input: "Look around the room"
    expects: "no roll, explore"
```

`load_scenario(path: Path) -> Scenario` — parse YAML, validate structure, return Scenario.

`discover_scenarios(scenarios_dir: str = "evals/scenarios") -> list[Path]` — find YAML files.

**Why:** YAML scenarios replace the old Python scenario files. They're simpler to write and don't require Python expertise. The `asserts` field bridges the gap between reusable mechanic checkers and one-off scenario expectations.

**Validation:** Load a test YAML scenario. Verify all fields parse correctly. Verify missing fields raise clear errors.

#### Step 4.3 — Create `ccya/ev/eval.py`

**File:** `ccya/ev/eval.py`

**What:** Eval command implementation.

`cmd_eval_run(scenario_path, model=None, temp=None, checkers=None, report=None)`:

1. Load scenario YAML via `load_scenario(path)`
2. Create session dir at `saves/ev/eval_<scenario_id>_<timestamp>/`
3. Initialize state with `seed_overrides` applied
4. For each turn in scenario:
   - Call `play_turn(turn.input, state, config, session_dir)`
   - Append event to `events.jsonl`
   - Store `TurnAssert` list for later checking
5. After all turns played, load events from session_dir
6. Run all requested checkers against the events
7. Also run a built-in `turn_assert` checker against stored assertions
8. Aggregate results
9. Format as Markdown report
10. If `--report <path>`: write report to file. Otherwise print to stdout.

`cmd_eval_list()`:
- Call `discover_scenarios()`
- Print available scenarios with id, description, turn count

CLI interface:
```
ev.py eval run <scenario.yaml>                    # Run scenario and check all turns
  --model <name>  --temp <float>
  --checkers <id> [--checkers <id>]               # Run specific checkers (default: all)
  --report <path>                                  # Write report to file

ev.py eval list                                    # List available scenario files
```

#### Step 4.4 — Implement `turn_assert` built-in checker

**File:** `ccya/ev/checkers/turn_assert.py`

**What:** A generic checker that validates per-turn `TurnAssert` expectations.

```python
@register_checker(
    "turn_assert", "deterministic",
    requires_fields=[],  # Dynamic — depends on the assert being checked
    description="Validate per-turn structured assertions (stream/field/expected)",
)
def turn_assert(events: list[dict], asserts: list[TurnAssert]) -> CheckerResult:
```

This checker is not in the default registry — it's called programmatically by the eval runner with the specific assertions for each scenario. It maps each TurnAssert to an event field extraction and comparison:

1. Match the assert's `stream` to an event section (e.g., "ruling" → `event["ruling"]`, "extract.state" → `event["applied"]`, "extraction_context" → `event["extraction_context"]`)
2. Extract the `field` from that section
3. Compare with `expected` (string match or exact equality)
4. If `min_amount` is specified, verify the field value >= min_amount
5. Return CheckerResult with individual findings per assert

**Validation:** Create a scenario with TurnAssert that intentionally expects the wrong value. Verify the eval report shows it as FAIL.

#### Step 4.5 — Wire into `ccya/ev/__init__.py` dispatch

Update the `check` and `eval` cases in main dispatch:
- `check`: parse turn number, checker IDs, --all, --llm, --events path. Call `cmd_check()`.
- `eval run`: parse scenario path, --model, --temp, --checkers, --report. Call `cmd_eval_run()`.
- `eval list`: call `cmd_eval_list()`.

Lazy imports: `from ccya.ev.check import cmd_check` and `from ccya.ev.eval import cmd_eval_run, cmd_eval_list`.

### Tests to write or update

1. `ev.py check 5 momentum_lifecycle` — pass on known-good data
2. `ev.py check 5 --all` — all deterministic checkers run, output readable
3. `ev.py eval list` — lists available scenarios
4. `ev.py eval run evals/scenarios/momentum_basics.yaml` — runs scenario, produces report
5. Verify that a YAML scenario with intentional assertion failure produces FAIL in report
