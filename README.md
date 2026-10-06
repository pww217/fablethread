# ccya

A choose-your-own-adventure game backed by a local **mlx-lm** model served over an OpenAI-compatible API. Each run generates a fresh scenario from a **world pack** — the LLM seeds the character, location, NPCs, quest, and opening narrative from a world bible + scenario constraints.

## License

Licensed under the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0). You may use, modify, and distribute this software for personal, educational, and research purposes. Commercial use — selling, hosting as a paid service, or incorporating into a commercial product — requires a separate license from the copyright holder. This is a source-available license, not an OSI-approved open source license. See `LICENSE` for full terms.

## Quick Start

```bash
# Install dependencies
make install

# Configure your LLM backend
cp config.yaml.example config.yaml
# Edit config.yaml → set llm.host and llm.model for your setup

# Start the server
make run
```

The server starts at `http://127.0.0.1:8765`.

## Setup

### LLM Backend

ccya works with any OpenAI-compatible API server. Popular options:

**LMStudio** (cross-platform):
```bash
pip install lmstudio
lmstudio server --model mlx-community/gemma-4-26b-a4b-it-OptiQ-4bit \
    --host 127.0.0.1 --port 1234
```

**OMLX** (Apple Silicon, MLX):
```bash
# Load a model in OMLX, then:
curl http://127.0.0.1:8000/v1/models  # verify model is loaded
```

Set `llm.host` in `config.yaml` to your backend's URL.

### Configuration

Copy `config.yaml.example` to `config.yaml` and edit:

- `llm.host` — your LLM backend URL (default `http://127.0.0.1:1234/v1`)
- `llm.model` — model identifier (must match what your backend exposes)
- `llm.num_ctx` — context window size (default 16384)
- `llm.*.temperature` — per-phase temperature knobs
- `server.bind_port` — web server port (default 8765)

All template values in `config.yaml.example` are sensible defaults. The example uses LMStudio on port 1234 as the default backend.

## Mock Mode

Run without a model server by setting `MOCK_MODE=true`:

```bash
export MOCK_MODE=true
make run
```

Mock mode returns canned narrative text and synthetic state deltas. Useful for:
- Development without a model loaded
- Testing endpoints and UI changes
- Running `make test` (the smoke tests use mock mode internally)

Confirm mock mode with: `curl http://127.0.0.1:8765/healthz` — look for `"mock": true`.

## Testing

Smoke tests run entirely offline (no model server needed):

```bash
make test
```

Test endpoints via curl:

```bash
# Health check (mock or real). Hits mlx_lm.server's /v1/models under the hood.
curl http://127.0.0.1:8765/healthz

# New game (resets state from seed)
curl -X POST http://127.0.0.1:8765/new-game

# Opening scene
curl http://127.0.0.1:8765/opening

# Run a turn (returns SSE stream)
curl -X POST http://127.0.0.1:8765/turn -d "input=I look around"

# Panels (HTMX partial renders)
curl http://127.0.0.1:8765/panels/state
curl http://127.0.0.1:8765/panels/state-left
curl http://127.0.0.1:8765/panels/state-right
curl http://127.0.0.1:8765/panels/actions
curl http://127.0.0.1:8765/panels/debug
```

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install deps with uv |
| `make run` | Start the server |
| `make dev` | Start with auto-reload |
| `make new-game` | Reset save from seed pack |
| `make test` | Run smoke tests (offline) |
| `make lint` | Run ruff checks |
| `make fmt` | Format code |
| `make css` | Rebuild Tailwind CSS |
| `make clean` | Remove build artifacts |

## Packs

Packs live in `packs/<id>/` and declare their mode in `pack.yaml`.

| Mode | How it works | Files required |
|------|-------------|----------------|
| `dynamic` | LLM generates a fresh seed (character, location, NPCs, quest, opening) on every New Game | `pack.yaml`, `world.md`, `scenario.yaml`, `style.md`, `extract_examples.yaml` |

To switch packs, click **New Game** and select from the picker, or set `game.setting_pack` in `config.yaml`.

See `packs/AUTHORING.md` for the full pack spec.

## File layout

```
config.yaml.example          # Template — copy to config.yaml for your setup
config.yaml                  # Your config (not tracked in git)
ccya/                        # Python package
  engine/                    # Turn pipeline (rules + narrate + extract)
  rules.py                   # Pure-Python dice resolver (1d12 PbtA, no LLM)
  pack.py                    # Pack loader, manifest schema, list_packs()
  llm_client.py              # Thin async OpenAI-compatible client
  state.py                   # YAML + JSONL state I/O
  server.py                  # FastAPI routes + SSE
  models.py                  # Pydantic models + config loader
  logging_setup.py           # JSONL logging
  prompts/                   # Jinja prompt templates (rules, narrate, extract, seed)
  templates/                 # HTMX/Alpine HTML templates
  static/                    # CSS + vendored JS (htmx, alpine, marked)
saves/default/               # Game save (state.yaml, events.jsonl, chronicle.md)
packs/                       # World packs
logs/                        # JSONL turn logs (not tracked)
```

## Config

Edit `config.yaml` (copy from `config.yaml.example`) to change the model, port, or other settings. Key sections:

- `llm` — `host` (default `http://127.0.0.1:1234/v1` for LMStudio), `model`, request timeout, narrate/extract temperatures, retry budget, optional `fallback_host` for secondary LLM
- `rules` — `temperature` (default 0.2) and `max_retries` (default 1) for the rules/intent Call 0
- `game` — save slot, setting pack, turn window size
- `server` — bind address and port
- `debug` — toggle debug panel

## Debugging

- Tail the JSONL log: `tail -f logs/llm-g.log | jq .`
- Each turn has a `trace_id` surfaced in the Debug panel (click to copy)
- State is hand-editable YAML in `saves/default/state.yaml`
- Full turn history: `saves/default/events.jsonl`
- Narrative chronicle: `saves/default/chronicle.md`
- Debug panel at `http://127.0.0.1:8765/` shows request timing and mock mode status
- Panels at `/panels/state`, `/panels/state-left`, `/panels/state-right`, `/panels/actions`, `/panels/debug` (errors are shown inside Debug)

## How it works

### New game flow (dynamic packs)

When you click **New Game** and select a pack, the server calls `prepare_seed()` (temp 0.4) to generate structured game state, then `narrate_seed()` (temp 0.9) to generate opening prose — a two-step pipeline that resolves the temperature tension where low temp gives reliable JSON but formulaic narration, and high temp gives vivid prose but malformed JSON. The world bible (`world.md`) and scenario constraints (`scenario.yaml`) shape what the model generates; `style.md` and `extract_examples.yaml` carry over into the regular turn pipeline.

### Rules engine

Every turn runs a **1d12 + modifier PbtA dice system** before narration.

| Raw die | Band | Result |
|---------|------|--------|
| 1 | **CRITICAL FAIL** | Catastrophic regardless of modifiers |
| ≤ 5 | **FAIL** | Attempt fails; complication arises |
| 6 | **SETBACK** | Set back; resource lost, time wasted |
| 7–8 | **PARTIAL** | Yes, but at a cost |
| ≥ 9 | **SUCCESS** | Clean success |
| 12 | **CRITICAL SUCCESS** | Outstanding regardless of modifiers |

Final roll = 1d12 + (stat − 2) + difficulty_mod + condition_mod. The outcome is displayed in the UI as a roll badge and is passed to the narrator as a **binding constraint**. Checks only fire when the action is active, has real consequences, and is genuinely uncertain.

### Turn flow

Each turn fires three LLM calls (OpenAI `/v1/chat/completions`):

1. **Rules / intent** (fast, non-streaming) — classifies what the player is attempting and whether a dice roll is required. Returns an `IntentEnvelope`; the Python engine resolves the dice deterministically. Displays as **"Determining Outcome"** in the UI.
2. **Narrate** — streams narrative text token-by-token via SSE. Chronicle tail + recent turns injected as context. If a roll occurred, a BINDING outcome block constrains the narrator. Displays the roll badge between rules and narrative text.
3. **Extract** — parses the narrative into a structured `StateDelta`. Rules-outcome hint prepended for accuracy on fail/mixed/success. Displays as **"Updating Game State"** in the UI.

The extracted delta is validated against current state (e.g. impossible inventory removals) before applying. Rejected removes surface in the turn summary modal.

### Storage

- **`chronicle.md`** — full turn-by-turn prose. Narrator context and browser reload history read from here.
- **`events.jsonl`** — state-change + timing log per turn (narrate/extract ms + tokens in/out, `changes` diff, no raw narrative).
- **`state.yaml`** — current world state (hand-editable between turns).

### State model

- **Facts (deltas):** `established_facts_add` / `established_facts_update` (`old`→`new`, position-preserving) / `established_facts_remove`. Not full-list replacement.
- **PC conditions:** `pc_condition_add` / `pc_condition_remove`.
- **Inventory:** normalized-id merge on add; partial-stack subtract on remove; `inventory_update` for name/notes changes without re-adding.
- **NPCs:** `present_npcs` replaces the full list each turn. Returning NPCs can emit `{id, notes}` only — the engine hydrates name/title/bio from the compendium.
- **Location:** `location_description` nudges description in place; `location_change` moves to a new id/name.

### UI

- **Header:** scene tagline (or `PC @ location`) on the left; **📖 Chronicle** pill (turn log) centered; status/controls on the right.
- **Chronicle overlay:** opens over the narrative column showing per-turn change summaries; closes without affecting the narrative panel layout.
- **Turn summary modal:** appears after each turn with emoji-categorized changes (inventory / player / facts / quests). Dismiss via Enter, Escape, or click.
- **Send → Stop:** while inference runs, the Send button turns red with a spinner; clicking cancels the SSE and restores the previous input and action pills.
- **Action pills:** clicking a choice inserts it into the input with a trailing space (no auto-submit).
- **Debug panel:** recent turn timing (narrate/extract seconds + token in/out), status (model, mock mode), errors.

**Markdown** — Narrative and sidebar snippets rendered with **marked** (GitHub-flavored); narrator/extractor instructed to use light markup.

Historical rows in `events.jsonl` keep whatever JSON shape they were written with; only new rows use the updated schema.
