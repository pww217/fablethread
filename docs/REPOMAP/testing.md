# Testing

## Test files

Located in `tests/` at repo root. Run with `make test` (uses `uv run pytest -q`).

- `test_engine_pipeline.py` — Multi-turn invariants, scope-gating tests (Tier 1 eval harness)
- `test_engine_smoke.py` — Full turn pipeline smoke test
- `test_rules.py` — Dice resolution tests
- `test_pack_loader.py` — Pack loading tests
- `test_generate_seed.py` — Seed generation tests
- `test_names.py` — Name generation tests
- `test_prompt_audit.py` — Prompt template tests
- `test_char_creation.py` — Character creation tests
- `test_server_routes.py` — Server route tests
- `test_eval.py` — Eval harness tests
- `test_eval_schema.py` — Tier 1 schema validation: TurnAssert paths against live engine, engine_mirror self-consistency, seed_override path validation
- `test_compactor.py` — Compactor overhaul tests: config validation, prior_history migration, compaction math, prompt contract (PART 1/2/3), recent_events compaction (consolidation, empty input, full replacement), sanitization (NPC merge, inventory remove, quest close, pressure remove, condition remove), response parsing

## Mocking

- Tests mock the LLM client (`ccya.engine.rules._call_rules` / `ccya.engine.narrate._narrate_messages` / `ccya.engine.extraction._call_stream`) — do not call a real model server in tests.
- `_FakeLLM` in `test_engine_smoke.py` handles the 5-call turn structure: rules (chat 1), narrate (stream), scene extract (chat 2), state extract (chat 3), progress extract (chat 4). Construct with keyword args `narrative=`, `scene_response=`, `state_response=`, `progress_response=` or pass a legacy positional list.

## Test conventions

- When adding a new `EngineConfig` field or `StateDelta` sub-type, add a smoke test that: (a) verifies the toggle round-trips correctly, and (b) confirms the prompt template renders the expected content.
- Per-stream prompt tests call `_extract_scene_messages`, `_extract_state_messages`, `_extract_progress_messages` directly — import from `ccya.engine.extraction`.
- State mutation tests should exercise `apply_delta` directly (not through the full turn pipeline) for speed and isolation.
- Tier 1 eval harness tests (`test_engine_pipeline.py`) use `_FakeLLM` and enforce multi-turn invariants.

## Commands

| Command | Description |
|---|---|
| `make install` | Install deps with `uv sync` |
| `make run` | Start server (no reload, uses `__main__.py`) |
| `make dev` | Start with auto-reload (`uvicorn --reload`) |
| `make test` | Run smoke tests (offline, mocks the LLM client) |
| `make test-v` | Verbose output (full tracebacks, test names). For debugging. |
| `make test-x` | Stop on first failure, verbose. CI-style run. |
| `make check` | Run ruff checks + mypy typecheck |
| `make lint` | Run ruff checks |
| `make fmt` | Format code with ruff |
| `make css` | Rebuild Tailwind CSS |
| `make new-game` | Reset save from seed pack |
| `make eval` | Run Tier 2 eval harness (in-process driver → LLM judge → REPORT.md) |

Use `make dev` for active development. `make run` is for production-like starts.
