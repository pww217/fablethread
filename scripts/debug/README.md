# Debug Scripts

Quick CLI tools for inspecting turn data from `saves/default/events.jsonl`.

All scripts are thin wrappers around `ev.py` which reads events.jsonl directly — no server required.

**Stream name aliases:** `ruling` (also `rules`), `narrate`, `scene`, `state`, `storytell` (also `progress`).

## Quick reference

| Command | Purpose |
|---------|---------|
| `ev.py summary` | One-line overview of all turns |
| `ev.py timing` | Token counts and timing per stream |
| `ev.py turn` | Full prompts + outputs for all streams on a turn (`--json` for raw JSON) |
| `ev.py prompt` | Single field: system, user, or output (merged `props`/`compact`/`prompt`) |
| `ev.py outputs` | JSON outputs from all streams |
| `ev.py deltas` | State diffs, rejections, sanitizer events, extraction context (merged `deltas`/`connectors`) |
| `ev.py mechanics` | Rules intent + beats + pressures + arcs + connectors + pacing + dice (merged `mechanics`/`pacing`/`dice`) |
| `ev.py state` | Current game state (reads state.yaml) |
| `ev.py diff` | State comparison between two turns |
| `ev.py trace` | Track a field across turns |
| `ev.py search` | Find turns matching criteria |
| `ev.py play` | Play a turn via the engine (sync or LLM mode) |
| `ev.py check` | Run checkers against existing events |
| `ev.py eval run` | Run a YAML scenario through the engine |
| `ev.py eval list` | List available YAML scenarios |

## Usage

Every script (and `ev.py`) takes a turn number as the first argument.
Optionally pass a path to events.jsonl as the last argument to use a different save directory.

```bash
# Summary of all turns
./ev.py summary

# Timing breakdown
./ev.py timing

# Full pipeline for turn 5
./ev.py turn 5

# Turn as raw JSON
./ev.py turn 5 --json

# Just the progress/storytell stream on turn 5
./ev.py prompt 5 progress user

# State mutations
./ev.py deltas 5

# Mechanics with pacing and dice info
./ev.py mechanics 5 --pacing --dice

# Using a different save directory
./ev.py turn 5 saves/another-game/events.jsonl

# Legacy script names still work (forward to ev.py)
./get-turn.sh 5
./get-deltas.sh 5
```

## Play command

```bash
# Play a single turn with default model
./ev.py play 5 "I attack the goblin."

# Play with a specific model
./ev.py play 5 "I attack the goblin." --model "some-model"

# Play in interactive mode (prompt for input)
./ev.py play --interactive

# Play with LLM-generated input
./ev.py play --llm
```

## Check command

```bash
# Run specific checkers on a turn
./ev.py check 5 momentum_lifecycle gm_beat_lifecycle

# Run all checkers on a turn
./ev.py check 5 --all

# Include LLM-based checkers
./ev.py check 5 --all --llm

# Override checker model
./ev.py check 5 --all --checker-model "some-model"

# Specify save directory (needed for sanitizer_lifecycle)
./ev.py check 5 --all --save-dir saves/another-game
```

## Eval command

```bash
# List available scenarios
./ev.py eval list

# Run a scenario
./ev.py eval run scenarios/my-scenario.yaml

# Run with specific model and temperature
./ev.py eval run scenarios/my-scenario.yaml --model "some-model" --temp 0.7

# Run with specific checkers only
./ev.py eval run scenarios/my-scenario.yaml --checkers "momentum_lifecycle,inventory_integrity"

# Save report to file
./ev.py eval run scenarios/my-scenario.yaml --report report.md
```

## When to use which

- **Debugging beats/pressures/arcs**: `ev.py mechanics <turn>` — beats, deescalate, pressures, arc, threads
- **Debugging a bad output**: `ev.py prompt <turn> <stream> user` to see prompts + outputs
- **Checking state mutations**: `ev.py deltas <turn>` to see what changed
- **Reviewing prompt quality**: `ev.py prompt <turn> <stream> user` to see system + user prompts
- **Token budget analysis**: `ev.py timing`
- **Validating game mechanics**: `ev.py check <turn> --all` or specific checkers
- **Running a scenario test**: `ev.py eval run scenarios/<name>.yaml`

## Data structure reference

Events are stored as one JSON line per turn in `saves/default/events.jsonl`.

### Raw event keys (events.jsonl)

- `.turn` — turn number
- `.input` — player's text input
- `.rules_prompt` — rules stream prompts
  - `.rendered_system`, `.rendered_user`, `.output` (JSON string)
- `.narrate_prompt` — narrate stream prompts
  - `.rendered_system`, `.rendered_user`, `.output` (prose string)
- `.extraction.scene` — scene extractor
  - `.rendered_system`, `.rendered_user`, `.output` (JSON string)
- `.extraction.state` — state extractor
  - `.rendered_system`, `.rendered_user`, `.output` (JSON string)
- `.extraction.storytell` — storyteller
  - `.rendered_system`, `.rendered_user`, `.output` (JSON string)
- `.rules` — rules metrics (total_ms, tokens_in, tokens_out, etc.)
- `.narrate` — narrate metrics
- `.extract` — extraction metrics with per-stream breakdown
- `.applied` — state deltas that were applied
- `.rejected` — state deltas that were rejected with reasons
- `.actions` — actions taken during the turn
- `.changes` — change summary lines
- `.state_diff` — flat list of state mutations (added by turn viewer)
- `.connectors` — inter-stream data flow (added by turn viewer)
- `.momentum_before` — PC momentum before ruling
- `.momentum_after` — PC momentum after ruling
- `.momentum_delta` — computed momentum change
- `.narrative_velocity` — pacing metric rounded to 2 decimal places
- `.pacing_context` — computed pacing context (directive, beat_locked, outcome_hint, scene_motion)
- `.state_snapshot` — full state at end of turn
- `.post_turn_pending_beat` — pending_gm_beat after turn processing
- `.post_extraction_consecutive_pressure_turns` — consecutive pressure counter after extraction
- `.post_turn_location_id` — location ID after turn processing
- `.extraction_context` — extraction-derived context for this turn (scene_tags_this_turn, inventory_this_turn, conditions_this_turn, location_this_turn)
- `.ruling_event` — ruling event record
- `.ruling` — ruling metrics and outcome
- `.narrate` — narration prose text
- `.sanitizer` — thread sanitizer events (kind: "sanitizer", non-turn event)
  - `.threads_updated`, `.threads_removed`, `.threads_resolved`, `.threads_added`
  - `.goal_changed`, `.changes_detail`

### Non-turn entries

Non-turn events (kind != "turn") have no prompts and are automatically filtered by summary/timing/turn commands. The sanitizer events (kind: "sanitizer") are non-turn events that log thread cleanup operations. They are required by the `sanitizer_lifecycle` checker which sets `needs_non_turn_events=true`.

### Mechanics sections in prompts

The following sections are embedded in `.extraction.storytell.rendered_user` as text headers:

- `## gm_beat` — beats generated by ruling step (may be empty)
- `## deescalate` — pressure resolution info (only when a pressure resolves)
- `## Current Pressures` — active scene pressures
- `## rules_stakes` — band result and at-risk costs
- `## pending_beat` — beats carried forward from previous turns

In `.extraction.storytell.rendered_user`:

- `### Campaign Arc` — goal, phase, thematic question, PC drive, active threads

## Session directory

The `play` command saves session data in `saves/ev/<session>/` where `<session>` is a timestamped directory name. A symlink `saves/ev/latest` points to the most recent session. This is separate from the main game saves in `saves/default/`.
