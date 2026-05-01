# ccya

A choose-your-own-adventure game backed by a local **mlx-lm** model served over an OpenAI-compatible API. Each run generates a fresh scenario from a **world pack** — the LLM seeds the character, location, NPCs, quest, and opening narrative from a world bible + scenario constraints.

## Setup

1. **Install mlx-lm** (Apple Silicon required):
    ```bash
    pip install --user mlx-lm
    # or via uv:
    uv tool install mlx-lm
    ```
2. **Start the server** in another terminal — pick any model, the default config expects `mlx-community/Qwen3.6-27B-4bit`:
    ```bash
    mlx_lm.server \
        --model mlx-community/Qwen3.6-27B-4bit \
        --host 127.0.0.1 --port 8080
    ```
    The model loads once and stays resident; ccya talks to `http://127.0.0.1:8080/v1` (OpenAI shape).

    **Recommended:** use [llama-swap](https://github.com/mostlygeek/llama-swap) as a model-routing proxy so multiple tools can share `:8080` without restarting anything:
    ```bash
    brew tap mostlygeek/llama-swap && brew install llama-swap
    mkdir -p ~/.llm/logs && mv ~/mlx-env ~/.llm/mlx_env
    # config lives at ~/.llm/llama-swap.yaml
    make llama-swap   # or just: make run (starts it automatically)
    ```
3. **Install ccya dependencies**:
    ```bash
    make install
    ```

To pick a different model, edit `llm.model` in `config.yaml` — the value must match a key in `~/.llm/llama-swap.yaml`.

## Run

```bash
make run
```

The server starts at `http://127.0.0.1:8765` (terminal may show a clickable OSC 8 link when using `python -m ccya`).

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
| `static` | Hand-authored seed loaded directly | `pack.yaml`, `seed_state.yaml`, `opening_scene.md` (optional `style.md`, `extract_examples.yaml`) |

To switch packs, click **New Game** and select from the picker, or set `game.setting_pack` in `config.yaml`.

See `packs/AUTHORING.md` for the full pack spec.

## File layout

```
config.yaml              # Server, LLM, and game config
ccya/                    # Python package
  engine.py              # Turn pipeline (narrate + extract + generate_seed)
  pack.py                # Pack loader, manifest schema, list_packs()
  llm_client.py          # Thin async OpenAI-compatible client (mlx_lm.server)
  state.py               # YAML + JSONL state I/O
  server.py              # FastAPI routes + SSE
  models.py              # Pydantic models + config loader
  logging_setup.py       # JSONL logging
  prompts/               # Jinja prompt templates (narrate, extract, generate_seed)
  templates/             # HTMX/Alpine HTML templates
  static/                # CSS + vendored JS (htmx, alpine, marked)
saves/default/           # Game save (state.yaml, events.jsonl, chronicle.md)
packs/                   # World packs
logs/                    # JSONL turn logs
tests/                   # Smoke tests
```

## Config

Edit `config.yaml` to change the model, port, or other settings. Key sections:

- `llm` — `host` (e.g. `http://127.0.0.1:8080/v1`), `model`, request timeout, narrate/extract temperatures, retry budget, optional `enable_extract_thinking` / `enable_narrate_thinking` toggles for the Qwen3.x `/think` `/no_think` soft switches
- `game` — save slot, setting pack, turn window size
- `server` — bind address and port
- `debug` — toggle debug panel

**Notes on the Ollama → mlx-lm migration:**
- The config block was renamed from `ollama:` → `llm:`.
- `keep_alive`, `num_ctx`, and any `enforce_extract_schema`/grammar flags are gone — `mlx_lm.server` keeps the model resident on its own and does not expose JSON-grammar enforcement. The extract pipeline relies on prompt discipline + a single retry instead.

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

Each turn fires two LLM calls (OpenAI `/v1/chat/completions`):

1. **Narrate** — streams narrative text token-by-token via SSE. Chronicle tail + recent turns injected as context.
2. **Extract** — parses the narrative into a structured `StateDelta`. JSON validity is enforced through prompting + a single retry on parse failure.

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
