# Plan 03 — `play` command

## Purpose

Implement `ev.py play` — single-turn, `--interactive` REPL, and `--llm`-driven game play via in-process engine calls.

## Problem Statement

There is no fast path to test "what happens if I say X" without curl + events.jsonl inspection, or writing a full eval scenario. An engineer debugging a mechanic needs `ev.py play "kick the door down"` followed by `ev.py check 1 momentum_lifecycle`, not a 14-file eval harness.

## Constraints

- `run_turn()` is async — must wrap with synchronous interface
- In-process engine calls only (no HTTP, no server dependency)
- Events persist to `saves/ev/<session>/events.jsonl`
- Error handling: structured output with errors section, never raw traceback
- Player LLM in `--llm` mode is the engine model (Gemma), not a separate model
- Thread sanitizer runs as part of `run_turn()` — `--no-sanitize` flag to disable

## Non-goals

- `check` integration — `--check` flag is a simple pass-through to checker lib; full checker orchestration in phase 4
- `eval` batch runner — phase 4
- LLM-based checkers — phase 5

## Solution

Implement `cmd_play()` in `ccya/ev/play.py` with async wrapper, session management, and structured output. Single-turn calls use `asyncio.run()`. Interactive/LLM sessions use a persistent event loop. All sessions write events to `saves/ev/<session>/`.

## Firm decisions

- Async wrapper: `asyncio.run()` per single play call; persistent loop for `--interactive`/`--llm`
- Events directory: `saves/ev/<session>/events.jsonl` with `saves/ev/latest` symlink
- Error handling: always produce output with errors section + non-zero exit
- Player LLM: same model as engine (Gemma), no separate player model

## Risks, Ambiguities, and Blockers

- `run_turn()` is an async generator that yields phase events, token streams, and the final result. The wrapper must iterate all yields, collect tokens, and return the `TurnResult`.
- The LLM client is initialized inside `run_turn()` via `config`. Each `asyncio.run()` creates a new event loop. If the LLM client uses `asyncio` resources tied to the loop, reconnection may be needed. Test with actual engine model before assuming it works.
- `--interactive` mode needs a persistent event loop. Use a module-level loop variable to avoid recreating it each turn.

## Status

`completed`

## Implementation

### Context files to load

- `ccya/engine/turn.py` lines 898–1510 (`run_turn()` async generator — yield types, error handling)
- `ccya/models.py` line 508 (`TurnResult` fields)
- `ccya/engine/config.py` line 86 (`EngineConfig` — how to build config for in-process calls)
- `ccya/pack.py` (pack loading for `--pack` flag)
- `ccya/state/io.py` line 95 (`load_state`, `save_state` for session persistence)

### Detailed steps

#### Step 3.1 — Create `ccya/ev/play.py`

**File:** `ccya/ev/play.py`

**What:** Play command implementation with four functions:

```python
# Module-level event loop for --interactive/--llm
_play_loop: asyncio.AbstractEventLoop | None = None

def _get_play_loop() -> asyncio.AbstractEventLoop:
    """Get or create a persistent event loop for interactive/LLM sessions."""

def play_turn(
    input_text: str,
    state: dict,
    config: EngineConfig,
    save_dir: Path,
) -> dict:
    """Run one turn synchronously. Returns structured output dict.
    
    Internally:
    1. Creates a fresh event loop (single call) or reuses persistent loop (interactive)
    2. Iterates run_turn() async generator
    3. Collects all ("token", str) yields into a buffer
    4. Handles ("phase", dict) yields for progress tracking (not shown to user)
    5. Returns TurnResult from ("complete", TurnResult) yield
    6. On exception: catches LlmcTimeout, LlmcError, Exception
       Returns structured error dict instead of crashing
    
    The output dict has keys matching the play output structure:
    {
        "turn": int,
        "trace_id": str,
        "ruling": dict,        # intent, skill, difficulty, band, dice
        "narrative": str,      # full narration text
        "momentum_before": float,
        "momentum_after": float,
        "momentum_delta": float,
        "actions": list[str],
        "scene": dict,         # scene info from state
        "applied": dict,       # state mutations applied this turn
        "errors": list[dict],  # empty if no errors
        "tokens_in": int,
        "tokens_out": int,
        "ms": float,
    }
    """
```

Error handling details:
- `LlmcTimeout`: output dict has `errors=[{"kind": "timeout", "message": str(exc)}]`, narrative is engine's fallback text
- `LlmcError`: output dict has `errors=[{"kind": "llmc_error", "message": str(exc)}]`, narrative is engine's fallback text
- Generic `Exception`: output dict has `errors=[{"kind": "internal_error", "message": f"{type(exc).__name__}: {exc}"}]`, narrative is fallback
- Non-zero exit via `sys.exit(1)` after printing output

#### Step 3.2 — Session management

**File:** `ccya/ev/play.py` (add functions)

**What:**

```python
def _create_play_session() -> Path:
    """Create a timestamped session dir at saves/ev/<timestamp>/.
    Creates saves/ev/ if it doesn't exist.
    Updates saves/ev/latest symlink to point to new session.
    Returns the session directory path.
    """
```

Session dir format: `saves/ev/YYYYMMDD_HHMMSS_<random>/` (e.g., `saves/ev/20260608_ev_debug/`).

On session creation:
1. Create `saves/ev/` if missing
2. Create `saves/ev/<timestamp>_<random>/`
3. Copy initial state from default pack or specified `--pack`
4. Symlink `saves/ev/latest → <timestamp>_<random>/`
5. Initialize `events.jsonl` (empty)

On each turn in a session:
1. Call `play_turn()` which writes to state in the session dir
2. Append the turn event to `saves/ev/<session>/events.jsonl`
3. Return the output dict for display

#### Step 3.3 — `cmd_play()` entry point

**File:** `ccya/ev/__init__.py` (update dispatch to call `ccya/ev/play`)

**What:** The `play` case in main dispatch:

```
play <input>           → play_turn(input_text, state, config, save_dir) → print formatted output
play --interactive     → REPL loop: readline → play_turn() → print → repeat
play --llm "strategy"  → LLM loop: engine model generates inputs → play_turn() → repeat (max --turns)
```

For single-turn play:
1. Load state from save_dir (or create new session)
2. Build EngineConfig from defaults + --model/--temp/--pack overrides
3. Call `play_turn(input_text, state, config, save_dir)`
4. Format output dict as structured Markdown (matching the output template in the design doc)
5. If `--check` flags passed, call `run_checkers(checker_ids, events, save_dir)` and append results
6. Print to stdout
7. Exit 0 if no errors, 1 if errors present

For `--interactive`:
1. Create session, enter REPL loop
2. Each iteration: prompt for input, call play_turn, print output, append to events.jsonl
3. Exit loop on EOF (Ctrl+D) or "quit" / "exit"
4. On exit, print session summary (turns played, trace IDs, event file path)

For `--llm`:
1. Same as interactive but the LLM generates inputs based on a curated summary of previous turns
2. The player LLM prompt includes: last 3 narrative summaries, current scene, available actions
3. Default max turns: 20. `--turns N` overrides.
4. After each turn, the LLM sees the output summary and decides the next input

#### Step 3.4 — Output formatting

**File:** `ccya/ev/play.py` or `ccya/ev/output.py`

**What:**

```python
def format_play_output(result: dict) -> str:
    """Format play_turn() result dict as structured Markdown.
    Matches the output template in the design doc (section 3).
    """
```

The output format (from design doc):
```
Turn 3  |  trace: a1b2c3d4
------------------------------------------------------
Ruling:    ATTACK (skill: strength, diff: 12)
           Roll: 7 -> Band: SUCCESS (+1 momentum)
Narrative: "You slam your boot against the oak door. It
            groans but holds..." (347 chars)

Momentum:   -1 -> 0  (+1)
Actions:   Force the door, Look for another way, Call for help
Scene:     dusty_hallway, locked_door

Deltas:
  inventory_remove: lockpick_set x1
  npc_update: trevor_riddle -> angry

Errors:    none
Tokens:    in=5241  out=892  ms=3421
```

Error output format:
```
Turn 3  |  trace: a1b2c3d4
------------------------------------------------------
Errors:
  - LlmcTimeout: LLM call timed out after 30s
  - Fallback narrative: "*An error occurred...*"

Tokens:    in=3241  out=0  ms=30000
```

#### Step 3.5 — Wire into `ccya/ev/__init__.py` dispatch

Update the `play` case in the dispatch to:
1. Import `ccya.ev.play` lazily (only when `play` subcommand is invoked)
2. Parse play-specific flags (`--save-dir`, `--no-sanitize`, `--check`, `--model`, `--temp`, `--pack`, `--interactive`, `--llm`, `--turns`)
3. Route to play_turn, _interactive_session, or _llm_session

### Tests to write or update

Manual verification:

1. `ev.py play "kick the door down"` — run 3 turns, verify output matches expected format, verify `saves/ev/latest/events.jsonl` exists and has 3 events
2. `ev.py play "bad input" --no-sanitize` — verify no sanitizer LLM call between turns (check events.jsonl for sanitizer events)
3. `ev.py play --interactive` — type a few inputs, Ctrl+D to exit, verify output and event file
4. Run `ev.py play "input"` against a scenario that produces a known engine error (e.g., malformed pack). Verify structured error output (not a traceback).
5. `ev.py play "input" --check momentum_lifecycle` — verify check results appended to play output
