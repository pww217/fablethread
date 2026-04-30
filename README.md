# ccya

A choose-your-own-adventure game backed by a local Ollama model. Each run generates a fresh scenario from a **world pack** — the LLM seeds the character, location, NPCs, quest, and opening narrative from a world bible + scenario constraints.

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

## Packs

Packs live in `packs/<id>/` and declare their mode in `pack.yaml`.

| Mode | How it works | Files required |
|------|-------------|----------------|
| `dynamic` | LLM generates a fresh seed (character, location, NPCs, quest, opening) on every New Game | `pack.yaml`, `world.md`, `scenario.yaml`, `style.md`, `extract_examples.yaml` |
| `static` | Hand-authored seed loaded directly | `pack.yaml`, `seed_state.yaml`, `opening_scene.md` (optional `style.md`, `extract_examples.yaml`) |

**Included packs:**

| Pack | Mode | Description |
|------|------|-------------|
| `zombie-survival` | dynamic | Six months into the H7N9-X collapse. Every run is a different survivor, location, and opening crisis. |
| `expanse-belter` | dynamic | Hard sci-fi Belt freight operator in 2351. Fresh ship, fresh debt, fresh complication each run. |

To switch packs, click **New Game** and select from the picker, or set `game.setting_pack` in `config.yaml`.

See `packs/AUTHORING.md` for the full pack spec.

## File layout

```
config.yaml              # Server, Ollama, and game config
ccya/                    # Python package
  engine.py              # Turn pipeline (narrate + extract + generate_seed)
  pack.py                # Pack loader, manifest schema, list_packs()
  ollama.py              # Thin async Ollama client
  state.py               # YAML + JSONL state I/O
  server.py              # FastAPI routes + SSE
  models.py              # Pydantic models + config loader
  logging_setup.py       # JSONL logging
  prompts/               # Jinja prompt templates (narrate, extract, generate_seed)
  templates/             # HTMX/Alpine HTML templates
  static/                # CSS + vendored JS (htmx, alpine, marked)
saves/default/           # Game save (state.yaml, events.jsonl, chronicle.md)
packs/                   # World packs
  zombie-survival/       # Dynamic — H7N9-X outbreak
  expanse-belter/        # Dynamic — Belt freight / smuggling
  AUTHORING.md           # Pack authoring spec
scripts/                 # ollama-launch.sh helper
logs/                    # JSONL turn logs
tests/                   # Smoke tests
```

## Config

Edit `config.yaml` to change the model, port, or other settings. Key sections:

- `ollama` — host, model name, temperatures, context window; **`enforce_extract_schema`** toggles Ollama JSON grammar (slower); **`enable_extract_thinking`** enables a `<thinking>` block before extract JSON (extra tokens/latency; default off); **`enable_narrate_thinking`** enables an optional `<thinking>` block before narrative prose (stripped before chronicle and extract; default off)
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

When you click **New Game** and select a pack, the server calls `generate_seed()` — a single LLM call that produces a `SeedEnvelope` containing the full initial state (character, location, NPCs, inventory, quest, established facts) plus an opening narrative. The world bible (`world.md`) and scenario constraints (`scenario.yaml`) shape what the model generates; `style.md` and `extract_examples.yaml` carry over into the regular turn pipeline.

### Turn flow

Each turn fires two Ollama calls:

1. **Narrate** — streams narrative text token-by-token via SSE (temperature 0.8). Chronicle tail + recent turns injected as context.
2. **Extract** — parses the narrative into a structured `StateDelta` (temperature 0.0). Optional JSON grammar via `enforce_extract_schema`.

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
- **Debug panel:** recent turn timing (narrate/extract seconds + token in/out), status (model, context window, mock/schema flags), errors.

**Markdown** — Narrative and sidebar snippets rendered with **marked** (GitHub-flavored); narrator/extractor instructed to use light markup.

Historical rows in `events.jsonl` keep whatever JSON shape they were written with; only new rows use the updated schema.
