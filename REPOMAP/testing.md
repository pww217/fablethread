# Testing

## Test files

Located in `tests/` at repo root. Run with `make test` (uses `uv run pytest -q`).

- `test_engine_smoke.py` — full turn pipeline smoke test
- `test_rules.py` — dice resolution tests
- `test_pack_loader.py` — pack loading tests
- `test_generate_seed.py` — seed generation tests
- `test_names.py` — name generation tests
- `test_prompt_audit.py` — prompt template tests
- `test_char_creation.py` — character creation tests

## Mocking

- Tests mock the LLM client (`ccya.engine.llm_chat` / `ccya.engine.llm_chat_stream`) — do not call a real model server in tests.
- `_FakeLLM` in `test_engine_smoke.py` handles the 5-call turn structure: rules (chat 1), narrate (stream), scene extract (chat 2), state extract (chat 3), progress extract (chat 4). Construct with keyword args `narrative=`, `scene_response=`, `state_response=`, `progress_response=` or pass a legacy positional list.

## Test conventions

- When adding a new `EngineConfig` field or `StateDelta` sub-type, add a smoke test that: (a) verifies the toggle round-trips correctly, and (b) confirms the prompt template renders the expected content.
- Per-stream prompt tests call `_extract_scene_messages`, `_extract_state_messages`, `_extract_progress_messages` directly — import from `ccya.engine`.
- State mutation tests should exercise `apply_delta` directly (not through the full turn pipeline) for speed and isolation.

## Commands

| Command | Description |
|---|---|
| `make install` | Install deps with `uv sync` |
| `make run` | Start server (no reload, uses `__main__.py`) |
| `make dev` | Start with auto-reload (`uvicorn --reload`) |
| `make test` | Run smoke tests (offline, mocks the LLM client) |
| `make lint` | Run ruff checks |
| `make fmt` | Format code with ruff |
| `make css` | Rebuild Tailwind CSS |
| `make new-game` | Reset save from seed pack |

Use `make dev` for active development. `make run` is for production-like starts.
