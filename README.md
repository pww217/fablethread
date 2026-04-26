# ccya

A choose-your-own-adventure game backed by a local Ollama model.

## Setup

1. **Install Ollama** — https://ollama.ai
2. **Pull a model** (e.g. gemma4:26b):
    ```bash
    ollama pull gemma4:26b
    ```
3. **Install dependencies**:
    ```bash
    make install
    ```

## Run

```bash
make run
```

The server starts at `http://127.0.0.1:8765`.

## Mock Mode

Run without Ollama by setting `MOCK_MODE=true`:

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

Smoke tests run entirely offline (no Ollama needed):

```bash
make test
```

Test endpoints via curl:

```bash
# Health check (mock or real)
curl http://127.0.0.1:8765/healthz

# New game (resets state from seed)
curl -X POST http://127.0.0.1:8765/new-game

# Opening scene
curl http://127.0.0.1:8765/opening

# Run a turn (returns SSE stream)
curl -X POST http://127.0.0.1:8765/turn -d "input=I look around"

# Panels (HTMX partial renders)
curl http://127.0.0.1:8765/panels/state
curl http://127.0.0.1:8765/panels/actions
curl http://127.0.0.1:8765/panels/errors
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

## File layout

```
config.yaml            # Server, Ollama, and game config
ccya/                  # Python package
  engine.py            # Turn pipeline (narrate + extract)
  ollama.py            # Thin async Ollama client
  state.py             # YAML + JSONL state I/O
  server.py            # FastAPI routes + SSE
  models.py            # Pydantic models + config loader
  logging_setup.py     # JSONL logging
  prompts/             # Jinja prompt templates
  templates/           # HTMX/Alpine HTML templates
  static/              # CSS + JS
saves/default/         # Game save (state.yaml, events.jsonl, chronicle.md)
packs/hard-scifi-demo/ # Starter content (seed + opening scene)
logs/                  # JSONL turn logs
tests/                 # Smoke tests
```

## Config

Edit `config.yaml` to change the model, port, or other settings. Key sections:

- `ollama` — host, model name, temperatures, context window
- `game` — save slot, setting pack, turn window size
- `server` — bind address and port
- `debug` — toggle debug panel

## Debugging

- Tail the JSONL log: `tail -f logs/llm-g.log | jq .`
- Each turn has a `trace_id` surfaced in the errors panel (click to copy)
- State is hand-editable YAML in `saves/default/state.yaml`
- Full turn history: `saves/default/events.jsonl`
- Narrative chronicle: `saves/default/chronicle.md`
- Debug panel at `http://127.0.0.1:8765/` shows request timing and mock mode status
- Panels at `/panels/state`, `/panels/actions`, `/panels/errors`, `/panels/debug`

## How it works

Each turn fires two Ollama calls:

1. **Narrate** — streams narrative text (SSE, temperature 0.8)
2. **Extract** — parses the narrative into structured state changes (temperature 0.0, schema-constrained)

The extracted delta is validated against current state (reject illegal moves) before applying. Established facts from the narrative are fed back into the next turn's prompt for consistency.
