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

The server starts at `http://127.0.0.1:8765` (terminal may show a clickable OSC 8 link when using `python -m ccya`).

### Recommended Ollama setup (Apple Silicon)

These variables apply to the **Ollama server process** (`ollama serve` or Ollama.app). Set them before starting Ollama; changing them from the ccya Python process has no effect on an already-running server.

| Variable | Suggested | Purpose |
|----------|-----------|---------|
| `OLLAMA_FLASH_ATTENTION` | `1` | Lower KV memory for long contexts; enables KV cache quantization. |
| `OLLAMA_KV_CACHE_TYPE` | `q8_0` | Smaller KV cache (needs flash attention). |
| `OLLAMA_NUM_PARALLEL` | `1` | One in-flight request — best for large models + long context. |
| `OLLAMA_MAX_LOADED_MODELS` | `1` | Avoid loading multiple huge models on unified memory. |
| `OLLAMA_KEEP_ALIVE` | `10m` | How long to keep a model loaded when idle (ccya also sends `keep_alive` per request). |
| `OLLAMA_MLX` | `1` | Prefer MLX backend on Apple Silicon when the build supports it. |

**CLI (terminal):** from this directory,

```bash
make ollama-launch    # runs scripts/ollama-launch.sh → ollama serve
```

**Print suggested exports / launchctl lines:**

```bash
make ollama-env
```

**GUI (Ollama.app):** macOS does not inherit your shell `export`. Use `launchctl setenv` once, then quit and reopen Ollama.app:

```bash
launchctl setenv OLLAMA_FLASH_ATTENTION 1
launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0
launchctl setenv OLLAMA_NUM_PARALLEL 1
launchctl setenv OLLAMA_MAX_LOADED_MODELS 1
launchctl setenv OLLAMA_KEEP_ALIVE 10m
launchctl setenv OLLAMA_MLX 1
```

`OLLAMA_GPU_OVERHEAD` and `OLLAMA_NUM_GPU=999` are not recommended on macOS unified memory (little benefit).

Uncomment `OLLAMA_DEBUG=1` in `scripts/ollama-launch.sh` if you need offload / memory diagnostics in server logs.

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
| `make ollama-launch` | Start `ollama serve` with recommended Apple Silicon env |
| `make ollama-env` | Print suggested `export` / `launchctl setenv` lines |
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
scripts/               # ollama-launch.sh helper
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
- Each turn has a `trace_id` surfaced in the Debug panel (click to copy)
- State is hand-editable YAML in `saves/default/state.yaml`
- Full turn history: `saves/default/events.jsonl`
- Narrative chronicle: `saves/default/chronicle.md`
- Debug panel at `http://127.0.0.1:8765/` shows request timing and mock mode status
- Panels at `/panels/state`, `/panels/state-left`, `/panels/state-right`, `/panels/actions`, `/panels/debug` (errors are shown inside Debug)

## How it works

Each turn fires two Ollama calls:

1. **Narrate** — streams narrative text (SSE, temperature 0.8)
2. **Extract** — parses the narrative into structured state changes (temperature 0.0, schema-constrained)

The extracted delta is validated against current state (e.g. impossible inventory removals) before applying.

**Narrative storage** — Full turn-by-turn prose lives in **`chronicle.md`** only. The narrator’s “recent turns” context and browser reload history read from there (full text per turn). **`events.jsonl`** is a **state-change / timing log** — new rows do **not** duplicate narrative text.

**Facts & PC conditions (deltas)** — The extract prompt lists current established facts and conditions. The model emits **`established_facts_add`**, **`established_facts_update`** (`old` → `new`, keeps list order), **`established_facts_remove`**, and **`pc_condition_add`** / **`pc_condition_remove`** — not full-list replacement. **`location_description`** nudges the current place each turn without changing `location_change`.

**Inventory** uses transactional add/remove deltas; ids are **normalized** on apply so `water-filter` and `Water_Filter` stack together.

Typical extract latency stays similar to before. Historical rows in `events.jsonl` keep whatever JSON shape they were written with; only new applies use the updated schema.
