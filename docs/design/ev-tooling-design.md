# EV Tooling — Unified Play + Inspect + Check

## Purpose

This document is the design authority for plans that unify `ev.py`, the eval harness, and the mechanic rubric system into a single coherent toolchain with shared checker primitives.

## Problem Statement

The current debug/eval toolchain has three disconnected tools with overlapping concerns, duplicate documentation, and no shared primitives:

1. **ev.py** (2254 lines) is a powerful read-only events.jsonl inspector with zero ability to play a game.
2. **The eval harness** (`python -m ccya.eval`) drives the engine in-process but requires authored Python scenarios and runs 4 heavy LLM judges that each bundle 6-12 concerns into a single expensive call.
3. **The ev skill** duplicates documentation that already lives (or could live) in the repo, creating a second source of truth.

An engineer debugging a specific mechanic (e.g., "is momentum updating correctly when I fail a roll?") has no fast path. They must either: write a scenario and run the full eval harness (~30s + 4 LLM judge calls), or manually craft curl commands against the server, then inspect events.jsonl with ev.py. There is no "play one turn and check just the momentum lifecycle" workflow.

The rubrics are the biggest problem. Each domain judge asks a single LLM call to evaluate 6-12 distinct concerns (momentum lifecycle, beat lifecycle, thread lifecycle, condition lifecycle, inventory integrity, state fidelity, narrative chain analysis, NPC coherence, pacing assessment, prompt architecture audit, etc.). This means:
- A failure in one concern can contaminate scores for others.
- You cannot isolate which specific mechanic is failing.
- Each judge is expensive because the LLM must hold all criteria in context for the full turn range.
- The rubrics are large (166-212 lines each) and hard to author/debug.

## Constraints

- **In-process engine calls are preferred over HTTP.** The eval harness already has this pattern with `run_turn()`. HTTP mode is acceptable for interactive use, but the primary API is in-process.
- **No new external dependencies.** Use only what's already in pyproject.toml.
- **Preserve backward compatibility for existing eval config.** Old-style `judge:` config and rubric files continue working. Existing scenarios remain runnable.
- **Single source of truth for documentation.** Repo files, not skill files.
- **ev.py remains a standalone script** (single file, no package deps beyond stdlib + yaml). It can import from ccya.eval for the checker library and from ccya.engine for play.

## Non-goals

- **Rewrite the eval harness judge pipeline from scratch.** The judge pipeline stays; individual checkers become a new option that can supplement or partially replace domain judges, but the old judge flow is not removed.
- **Replace all LLM judges with deterministic checks.** Some concerns (narrative tone, prompt quality) genuinely need LLM judgment. Those stay LLM-based but become narrower.
- **Interactive web UI.** This is a CLI-focused design.
- **Metrics dashboard or trend tracking.** Regressions stay as single-run comparisons.

## Current State — What Exists

### ev.py (`scripts/debug/ev.py`)

Read-only CLI with 15 subcommands: `summary`, `timing`, `turn`, `props`, `compact`, `prompt`, `outputs`, `deltas`, `dice`, `mechanics`, `connectors`, `pacing`, `state`, `diff`, `trace`, `search`. Reads `events.jsonl` directly. No ability to drive the engine.

The main dispatch (`main()`) uses a `match/case` block over the first positional arg. Stream aliases map user-facing names to data-model keys. Default events file is `saves/default/events.jsonl`.

Missing capabilities:
- No way to send a turn input and get a `TurnResult` back.
- No interactive game loop.
- No integration with the eval harness or checker library.

### Eval harness (`ccya/eval/`)

Three-phase pipeline:
1. **Runner** (`runner.py`): loads scenario, iterates turns calling `run_turn()` in-process, captures events.jsonl.
2. **Judge** (`judge.py`): builds filtered traces, calls LLM judges sequentially (3 domain + 1 meta), saves trace.md + judge.md per judge.
3. **Report** (`report.py`): generates REPORT.md with scores, flags, metrics.

Key types:
- `Scenario` (id, pack, turns, seed_overrides, track)
- `Turn` (input, phase, expects, asserts)
- `TurnAssert` (stream, field, expected, min_amount)
- `TurnResult` (turn, trace_id, narrative, state_delta, applied, rejected, actions, scene_tags, diff, changes, metrics, errors, ruling, outcome_summary, gm_beat, outcome_hint)
- `RunResult` (scenario_id, pack, model, temperature, turns[], total_errors, track)

### Universal asserts (`ccya/eval/universal_asserts.py`)

1037 lines, 24 deterministic checkers. Each takes `(event, prev_event)` and returns a result dict with keys: `assertion`, `passed`, `detail`, `scope`, `severity`. These are cheap, focused, run on every event, and are the closest thing to individual mechanic checks currently.

Checkers cover: pending_gm_beat consumed/lifecycle, location_change applied, condition dedup, inventory remove existence, inventory add/remove no negative amounts, inventory overdraw, consecutive pressure tracking, beat-locked dual trigger, floor relief injection, momentum delta, action count/distinctness, NPC extraction, ring buffer bounds, scene NPC cap, goal_update application, thread_add application, thread_update ID validity, ArcThread key dedup, beat type variety, surface_as consistency, removed directives/states check.

### Rubrics (`evals/rubrics/`)

| File | Lines | Concerns Bundled |
|---|---|---|
| `state_correctness.md` | 166 | Momentum lifecycle, GM beat lifecycle, arc goal updates, unified threads, conditions, inventory evolution, state fidelity, auto-checker analysis, extraction accuracy |
| `narrative_interplay.md` | 212 | Rules directive→tone match, GM beat→narrative effect, surface_as consistency, beat generation quality, unified thread tension/chains, thread resolution, goal_update, condition callback, NPC entry/exit, player intent fidelity, NPC coherence, pacing assessment (tension arc, momentum, beat variety, intent verb variety, skill coverage, escape paths) |
| `prompt_pipeline.md` | 156 | 9 criteria (P1-P9) per pipeline, mechanic ownership, cross-pipeline I/O, redundancy, prompt adherence rate |
| `meta.md` | 90 | Score synthesis, inter-judge contradiction check, 12-mechanic trace quality synthesis, final verdict |
| `default.md` | 642 | Legacy single-judge (not used in multi-judge config) |

### Skill (`~/.config/opencode/skills/ev/SKILL.md`)

Contains the full event shape reference, all command descriptions, state format modes, diff section filters, trace tracked fields, search expressions, mechanics sections reference — approximately 300 lines of reference material that also exists (partially) in `scripts/debug/README.md` (122 lines). The two documents have already diverged.

### Problems with Current State

1. **No play capability in the debug tool.** ev.py can only read past events. To test "what happens if I say X", you must either hit the server with curl or run a full eval scenario.

2. **Monolithic rubrics contaminate scores.** The LLM must evaluate 6-12 distinct concerns in a single call. A failure in one area (e.g., inventory extraction) can emotionally bias the judge's assessment of another (e.g., narrative tone), even with careful rubric wording.

3. **Cannot isolate individual mechanics.** If a run scores 3/5 on `mechanic_lifecycle_score`, you don't know which specific lifecycle failed — momentum, beats, threads, conditions, or inventory. The meta judge tries to synthesize, but it's a separate expensive LLM call doing its own 12-mechanic analysis.

4. **Duplicate documentation between skill and repo.** The ev skill has ~300 lines of reference docs. `scripts/debug/README.md` has 122 lines and covers roughly the same ground. They drift independently.

5. **Eval harness is the only path to automated checking.** If you want to verify a specific mechanic behavior, you must write a full scenario, run 4 judges, and read the report. There's no single-command "check this turn for momentum correctness."

## Proposed Solution

### Core Changes

#### 1. ev.py grows `play` and `game` subcommands

Two new subcommands in ev.py:

```
ev.py play <input>                  # Play one turn via in-process engine
  --save-dir <path>                 # Save dir (creates fresh if needed, default: temp)
  --http                           # Use HTTP POST to /turn instead of in-process
  --show state,mechanics,deltas     # What to display (default: all)
  --model <name>                    # LLM model override

ev.py game                          # Interactive session: read→play→show→repeat
  --llm <prompt>                    # LLM-driven: give a strategy prompt, LLM chooses inputs
  --turns <N>                       # Max turns (default: unlimited for interactive, 20 for LLM)
  --save-dir <path>
```

`play` uses the same `run_turn()` import path as the eval harness (`from ccya.engine import run_turn`). It initializes a fresh or existing save dir, calls `run_turn(save_dir, input, ...)`, collects the first `("complete", TurnResult)` yield, and prints a structural summary.

The structural summary includes:
- Turn number, trace_id
- Ruling: intent, band, skill, difficulty, outcome_summary
- Narrative: first 200 chars + char count
- State: momentum (before→after), actions, scene_tags
- Deltas: applied fields + rejected list
- Metrics: tokens_in, tokens_out, total_ms
- Errors: extraction parse failures, retries

`--http` mode POSTs `{"input": input}` to the server's `/turn` endpoint (assumes `localhost:8000`). The SSE stream is consumed to produce the same structural summary. This mode requires the server to be running but allows testing with the full server stack (chronicle, panels, etc.).

`game --llm` creates an LLM-driven game loop. The "player LLM" receives the previous turn's structural summary + any accumulated state, and produces the next input. This is implemented as a simple loop:

```
state = init_save_dir()
for i in range(max_turns):
    prev_summary_or_zero_state = summarize(state)
    next_input = player_llm(prev_summary_or_state, strategy_prompt)  # single LLM call, no tool use
    result = run_turn(save_dir, next_input, ...)
    state = result.state_delta
    print(structural_summary(result))
    if player_decides_to_stop(result):
        break
```

The "player LLM" is a separate concern from the engine LLMs. It uses a simple prompt: "You are playing a text adventure. Here's what happened. What do you do next?" The strategy prompt (`--llm "play until we find the key"`) provides goal-oriented behavior.

#### 2. Checker library (`ccya/eval/checkers/`)

A new module at `ccya/eval/checkers/` containing individual mechanic checkers. Each checker implements a simple interface:

```python
# ccya/eval/checkers/__init__.py
from typing import Any, Callable, Protocol

class CheckerResult:
    checker_id: str            # e.g. "momentum_lifecycle"
    passed: bool | None        # None = inconclusive (no data to check)
    score: float | None        # 0.0-1.0 or None if inconclusive
    detail: str                # human-readable finding
    findings: list[dict]       # structured findings per potential issue

CheckerFn = Callable[[list[dict], dict], CheckerResult]
# Args: list of events (one per turn), static context (seed state, config)
# Returns: CheckerResult

_ALL_CHECKERS: dict[str, CheckerFn] = {}
# Registered at import time via decorator or explicit registration
```

Each checker lives in its own file within `ccya/eval/checkers/`:

| File | Checker ID | Type | Source | What it checks |
|---|---|---|---|---|
| `momentum.py` | `momentum_lifecycle` | deterministic | Port from universal_asserts | Momentum delta correctness, floor/ceiling clamping, band→delta mapping |
| `gm_beat.py` | `gm_beat_lifecycle` | deterministic | Port from universal_asserts | pending_gm_beat consumed, lifecycle respected, floor relief injection |
| `location.py` | `location_change` | deterministic | Port from universal_asserts | location_change applied correctly |
| `inventory.py` | `inventory_integrity` | deterministic | Port from universal_asserts | No overdraw, no negative amounts, remove existence |
| `conditions.py` | `conditions_lifecycle` | deterministic | Port from universal_asserts | Dedup, cap, TTL |
| `threads.py` | `thread_lifecycle` | deterministic | Port from universal_asserts | Thread_add applied, thread_update IDs valid, thread_resolve, dedup |
| `arc.py` | `arc_goal_updates` | deterministic | New | goal_update overwrites visible_goal, narration responds |
| `npcs.py` | `npc_presence` | deterministic | Port from universal_asserts | NPC extraction, presence tags, scene NPC cap |
| `pacing.py` | `pacing_directives` | deterministic | Port from universal_asserts | Directive rendering, known values, beat-locked dual trigger |
| `actions.py` | `action_quality` | deterministic | Port from universal_asserts | Action count, distinctness, variety |
| `state_fidelity.py` | `state_fidelity` | LLM-based | Split from state_correctness | "Does extraction match what narration describes?" (narrow: single question) |
| `directive_tone.py` | `directive_tone_match` | LLM-based | Split from narrative_interplay | "Does narration tone match the rules directive?" (narrow: per-turn check) |
| `beat_narrative.py` | `beat_narrative_chain` | LLM-based | Split from narrative_interplay | "Does the GM beat produce observable narrative consequence?" |
| `prompt_audit.py` | `prompt_architecture` | LLM-based | Split from prompt_pipeline | "Are prompts well-structured per P1-P9?" (narrow: one pipeline at a time) |
| `prompt_adherence.py` | `prompt_adherence` | LLM-based | Split from prompt_pipeline | "Did pipeline outputs follow their system prompt?" |

Deterministic checkers are fast and always-on when the data is available. LLM-based checkers are triggered on demand or in batch.

**Relationship to existing universal_asserts**: The universal_asserts module is the implementation source for the deterministic checkers. The new checker files wrap the existing logic (or port it) into the unified `CheckerResult` interface. The `run_all_universal_asserts()` function remains for backward compatibility with the eval harness, but is also callable through the new `run_checker("momentum_lifecycle", events)` path.

**Relationship to existing domain judges**: The LLM-based checkers are narrower versions of what the domain judges already do. A domain judge can be constructed by running a set of checkers and aggregating results. For backward compatibility, the existing rubric-based judge flow remains, but a new `checker-based` judge mode is available:

```
python -m ccya.eval run scenario --checkers          # Use checker aggregation instead of domain judges
python -m ccya.eval run scenario --judge state_correctness  # Traditional rubric judge (unchanged)
```

#### 3. `ev.py check` subcommand

```
ev.py check <turn> <checker> [<checker> ...]          # Run specific checkers
  --events <path>                                      # Events file (default: saves/default/events.jsonl)
  --state <path>                                       # State file override

ev.py check <turn> --all                               # Run all applicable checkers
  --llm-checkers                                       # Include LLM-based checkers (requires LLM)
```

This connects the checker library to ev.py's read capability. For example: `ev.py check 5 momentum_lifecycle` loads events, extracts the relevant turn and its predecessor, and prints a structured result. Deterministic checkers complete instantly. LLM checkers make a single focused call.

The output format:

```
$ ev.py check 5 momentum_lifecycle
momentum_lifecycle: PASS (score: 1.0)
  Turn 5: band=success, delta=-1→0, WRONG_DIR (band=success should give +1, got -1)
  Detail: Momentum moved opposite to band direction on turn 5
```

#### 4. Documentation centralization

All reference material moves from the skill to repo files:

- **`scripts/debug/README.md`**: Canonical reference for ev.py commands, event shape, stream names, mechanics sections, format modes, diff filters, trace fields, search syntax. Expand to include the new `play`, `game`, and `check` commands.
- **`evals/CHECKERS.md`**: Documents the checker library: each checker's ID, what it checks, what events it reads, whether it's deterministic or LLM-based, and how to run it from ev.py or the eval harness.
- **`docs/architecture/eval-harness.md`**: Add a section on checker integration.
- **The ev skill** becomes a thin loader that reads these three files.

The skill file becomes:

```markdown
# Skill: ev

Read these repo files before using this skill:
- `scripts/debug/README.md` — ev.py command reference, event shape, mechanics sections
- `evals/CHECKERS.md` — checker library documentation
- `docs/architecture/eval-harness.md` — eval harness architecture (checkers section)
```

This eliminates duplication and ensures documentation is visible to humans reading the repo.

#### 5. Checker aggregation in the eval harness

The eval harness gains a new judge mode. Instead of calling 4 LLM judges sequentially, it can run all applicable checkers and aggregate results into scores:

```python
# In judge.py or a new checker_runner.py
def run_checkers(
    events: list[dict],
    checker_ids: list[str] | None = None,  # None = all applicable
    static_context: dict,
) -> dict[str, CheckerResult]:
    """Run specified (or all) checkers against the event list."""
    results = {}
    for cid in (checker_ids or _ALL_CHECKERS):
        checker_fn = _ALL_CHECKERS[cid]
        results[cid] = checker_fn(events, static_context)
    return results

def aggregate_checker_scores(
    results: dict[str, CheckerResult],
) -> dict[str, float]:
    """Aggregate individual checker scores into the 7 final eval scores."""
    # Maps checker IDs to final score keys
    # e.g., momentum_lifecycle + gm_beat_lifecycle + thread_lifecycle → mechanic_lifecycle_score
    ...
```

The `--checkers` flag in the eval CLI enables checker-based judging instead of rubric-based. The meta judge is optionally replaced by `aggregate_checker_scores()`.

### Alternatives Considered and Rejected

1. **Add `play` to a separate script (e.g., `scripts/debug/play.py`).**
   Rejected: Creates yet another entry point. ev.py is already the canonical CLI for debug tooling. Adding play/game to ev.py keeps everything in one place.

2. **Replace universal_asserts entirely with the new checker module.**
   Rejected: universal_asserts has 24 checkers and is used by the eval harness. Replacing it would require touching the report generator, runner, and judge pipeline. Instead, port the logic to checkers/ and have universal_asserts call the new checkers (or co-exist temporarily).

3. **Remove domain judges entirely and use only checkers.**
   Rejected: LLM-based narrative and prompt quality assessment is inherently fuzzy and benefits from a holistic prompt. Individual LLM checkers (directive_tone_match, beat_narrative_chain) are better than a monolithic rubric, but a single LLM call that evaluates "does the beat narrative chain work across all 13 turns" is more coherent than 13 per-turn LLM calls. The design keeps both paths available.

4. **Make the skill a symlink to repo docs.**
   Rejected: Skills are opencode-internal files. The skill reference material is what gets injected into the LLM's context. The skill should be a thin pointer (as proposed), not a symlink, because the skill loading mechanism reads the file content directly.

5. **HTTP-only play mode.**
   Rejected: HTTP requires the server to be running, adds latency, and changes the behavior slightly (SSE streaming vs direct result). In-process mode (like the eval harness) is the default. HTTP is a `--http` flag.

## Decision Table

| Decision | What | Why |
|---|---|---|
| ev.py gets play/game/check subcommands | A single CLI tool for play, inspect, and check workflows | One entry point instead of three; natural progression (play→inspect→check) |
| Checker library at `ccya/eval/checkers/` | Individual mechanic checkers with a shared `CheckerResult` interface | Decomposes monolithic rubrics; shareable between ev.py and eval harness |
| In-process engine calls default | `from ccya.engine import run_turn` | Same pattern as eval harness; no server dependency |
| HTTP play mode via `--http` flag | POST to `/turn`, consume SSE stream | Useful for testing server-specific behavior (panels, SSE timing) |
| LLM-driven game via `--llm` | Separate "player LLM" with simple prompt; loop: summarize→query LLM→play→repeat | Allows automated gameplay without authored scenarios; useful for broad regression testing |
| Documentation moves to repo | `scripts/debug/README.md`, `evals/CHECKERS.md` become canonical | Single source of truth; visible to humans reading the repo |
| Skill becomes a thin pointer | Reads the three repo docs instead of containing inline reference | Eliminates duplication; skill stays as entry point for opencode agents |
| Eval harness supports checker mode | `--checkers` flag replaces rubric judges with checker aggregation | Incremental adoption; old rubric path remains for backward compatibility |
| Universal asserts co-exist with new checkers | Existing `run_all_universal_asserts()` stays; new checkers wrap or extend the same logic | Zero disruption to existing eval pipeline; migration can happen incrementally |

## Failure Modes and Risks

1. **Checker library becomes as complex as the rubrics it replaces.** If each tracked field gets its own checker file, the checker directory could grow to 30+ files. Mitigation: group related concerns (inventory checkers in one file, thread checkers in another). The interface is small — the complexity is in the number of concerns, not the framework.

2. **LLM-based checkers still cost tokens.** Splitting a 166-line rubric into 3 focused LLM checkers of 30 lines each may cost *more* tokens overall because of repeated context (each narrow checker needs the event data). Mitigation: deterministic checkers are preferred for anything that can be checked in Python. LLM-based checkers are only used for genuinely fuzzy evaluations. The checker library's LLM checkers are invoked per-turn rather than per-run, so they check one turn at a time with minimal context.

3. **`play --llm` loops amplify engine bugs.** If the engine produces a bad state (e.g., momentum stuck at -3), the player LLM sees that and may act on it, potentially masking or amplifying the bug. Mitigation: the `--llm` mode is labeled as experimental and the structural summary shown to the player LLM is curated (deltas, not raw state). The player LLM gets a simplified, high-level view.

4. **Documentation drift between repo docs and skill.** If someone updates a repo doc but not the skill, the skill still reads the repo doc (it's a pointer), so no drift. If someone updates the skill with inline content that contradicts the repo doc, that's a problem — but the skill explicitly says "read these files" and should not contain inline reference material.

## Open Questions

[OPEN: Should `play --llm` use the same model config as the engine or a separate config? The player LLM is a different role (text adventure player) and may want a different model/temperature.]

[OPEN: Should checker aggregation in the eval harness replace the meta judge entirely, or supplement it? The meta judge's inter-judge contradiction check is valuable. Checker results provide scores but no cross-checker synthesis.]

[OPEN: How granular should LLM-based checkers be? For example, `directive_tone_match` could check one turn per LLM call (narrow, many calls) or all turns in one call (broader, fewer calls). The design favors per-turn for narrow concerns, per-run for synthetic concerns like prompt_architecture.]

[OPEN: Should ev.py gain a `serve` subcommand that starts a temporary server for testing HTTP play mode? Currently requires the user to start the server separately.]

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| Inline reference docs | `.opencode/skills/ev/SKILL.md` | Moved to `scripts/debug/README.md` and `evals/CHECKERS.md` |
| (Nothing else removed — all existing features preserved) | | |

## What Is Unchanged

- All existing ev.py read-only subcommands (`summary`, `timing`, `turn`, `props`, etc.)
- The eval harness three-phase pipeline (runner → judge → report)
- The 4 existing domain rubrics and the meta rubric (still usable via `--judge` flag)
- The universal_asserts module and its 24 checkers (still used by default in the eval runner)
- The scenario system (scenario.py, TurnAssert, etc.)
- The eval report generator (report.py)
- The server routes (routes.py)
- The engine pipeline (turn.py, run_turn() API)
- The state system (state/*.py)
- The pack system

## New Model Shapes

```python
# ccya/eval/checkers/__init__.py

@dataclass
class CheckerResult:
    checker_id: str
    passed: bool | None             # None = inconclusive (insufficient data)
    score: float | None             # 0.0-1.0 or None
    detail: str                     # Human-readable summary
    findings: list[dict] = field(default_factory=list)
    """Structured findings. Each dict has at minimum:
       - turn: int
       - finding: str  (machine-readable ID, e.g., "wrong_direction")
       - detail: str   (human-readable explanation)
    """
    ms: float = 0.0                 # Wall time to run checker

# Checker function signature
# events: list of event dicts from events.jsonl (one per turn)
# static_context: dict with seed_state, engine_constants, pack info (matches harness)
CheckerFn = Callable[[list[dict], dict], CheckerResult]
```

```python
# New fields on RunResult (or a parallel result type for play)

@dataclass
class TurnPlayResult:
    """Result of ev.py play <input> — lightweight version of eval RunResult."""
    turn: int
    trace_id: str
    input: str
    ruling: dict                          # intent, band, skill, difficulty, outcome_summary
    narrative_preview: str                # first 200 chars
    narrative_chars: int
    momentum_before: int
    momentum_after: int
    actions: list[str]
    scene_tags: list[str]
    applied: dict[str, Any]
    rejected: list[dict]
    metrics: dict[str, Any]               # tokens_in, tokens_out, total_ms
    errors: list[dict]
    checker_results: dict[str, CheckerResult] = field(default_factory=dict)
    """Results of --check flags run after play."""
```

## Context for Implementing LLMs

- `scripts/debug/ev.py` — The existing CLI tool. Read the full dispatch (`main()`), the `load_events()` function, and the current subcommand implementations. Pay attention to the stream alias system and how events are parsed. New subcommands follow the existing `case "name":` pattern.

- `ccya/eval/runner.py` — The in-process engine driver. Read `run_scenario()` (line ~353) and `_build_engine_config()` (line ~107). This is the template for `ev.py play --in-process`. Key import: `from ccya.engine import run_turn`.

- `ccya/models.py` — `TurnResult` dataclass (line 507). The output of `run_turn()`. Read all fields — this is what `ev.py play` receives and summarizes.

- `ccya/engine/turn.py` — `run_turn()` async generator (line ~904). Read the yield types: `("phase", dict)`, `("token", str)`, `("complete", TurnResult)`. The play command collects only the `"complete"` yield.

- `ccya/eval/universal_asserts.py` — 24 deterministic checkers. The implementation source for porting to `ccya/eval/checkers/`. Each function takes `(event, prev_event)` and returns a result dict. The new checker interface generalizes this.

- `ccya/eval/judge.py` — Current judge pipeline. Read `build_trace()`, `run_judges()`, `_JUDGE_EVENT_FIELDS` (field masks per judge). The checker aggregation replaces `run_judges()` when `--checkers` is set.

- `ccya/server/routes.py` — `/turn` GET endpoint (line ~137). The SSE stream format for HTTP play mode. Read the `event_stream()` inner coroutine to understand SSE event names and payloads.

- `evals/rubrics/` — All 5 rubric files. Reference for what each domain judge currently checks. Each section header maps to a potential individual checker.

- `ccya/eval/scenario.py` — Scenario, Turn, TurnAssert dataclasses. Reference for the existing eval data model (unchanged).
