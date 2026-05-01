# Ollama → mlx-lm migration — complete

Canonical location: **`/Users/pwilson/Repos/ccya/MIGRATION-TODO.md`** (this file).

## Done

- [x] `ccya/server.py` — `_debug_context()` no longer references `num_ctx` or schema flags
- [x] `ccya/templates/_debug.html` — `num_ctx` row and "Schema enforced" row removed
- [x] `ccya/server.py` — `/healthz` now hits `mlx_lm.server`'s `/v1/models` endpoint (OpenAI-compatible) and reports `available` based on whether the configured model is loaded
- [x] `ccya/engine.py` — `generate_seed()` and `warmup()` ported to `llm_chat` / OpenAI shape
- [x] `ccya/ccya/ollama.py` — deleted
- [x] `ccya/scripts/ollama-launch.sh` — deleted (`scripts/` directory removed; was empty afterwards)
- [x] `ccya/tests/test_engine_smoke.py` — `_FakeOllama` → `_FakeLLM`; patches `ccya.engine.llm_chat` / `llm_chat_stream`; `TestOllamaBodyShape` (Ollama options-shape + `format=` grammar enforcement assertions) deleted; thinking-toggle tests rewritten for the new Qwen3 `/think` soft-switch and `<think>` strip regex
- [x] `ccya/tests/test_generate_seed.py` — patches `ccya.engine.llm_chat`; `EngineConfig(ollama_host=...)` → `EngineConfig(host=...)`
- [x] `ccya/Makefile` — `ollama-launch` and `ollama-env` targets removed (and from `.PHONY`)
- [x] `ccya/README.md` — rewritten for `mlx_lm.server`, `http://127.0.0.1:8080/v1`, `llm:` config block, removed-keys note (`keep_alive`, `num_ctx`, schema flags), file-layout updated (`ollama.py` → `llm_client.py`)
- [x] `ccya/AGENTS.md` — module table now lists `llm_client.py`; "Adding a new config flag" section references `llm` block; testing note updated to "mocks the LLM client"

## Cleanup pass (post-migration tech-debt sweep)

- [x] Renamed `EngineConfig.num_ctx` → `EngineConfig.prompt_token_budget` (it was always a local trim budget, never an LLM API knob; new name + comment make that explicit)
- [x] Removed `_unwrap()` in `engine.py` — both branches `return j` (pure no-op); inlined the 3 call sites
- [x] Removed `_REQUEST_LOG` + `_add_timing()` in `server.py` — written but never read; also dropped the now-unused `import time`
- [x] Removed `_MOCK_EXTRACT_DEFAULT` in `llm_client.py` — defined but never referenced
- [x] Removed unused `import re` in `engine.py`
- [x] Removed `should_fail` parameter from `_FakeLLM` in `tests/test_engine_smoke.py` — no test uses it (the one schema-failure-retry test builds raw fakes)
- [x] Removed `_strip_thinking()` engine wrapper — was a 1-line passthrough to `llm_client.strip_thinking`; engine and tests now call `strip_thinking` directly
- [x] Deleted `ccya/prompts/narrate.j2` and `ccya/prompts/extract.j2` — explicitly tagged "Deprecated shim"; engine uses the `*_system.j2` + `*_user.j2` pair directly

## Verify (offline only — does not touch a real model server)

- [x] `make test` → 108 passed in 0.66s (after cleanup)
- [x] `uv run ruff check ccya tests` → All checks passed
- [x] Boot smoke (`MOCK_MODE` unset, no `mlx_lm.server` running): server starts in ~2s, `/healthz` returns `{"llm":"fail","available":false}` (graceful), `/`, `/panels/state`, `/panels/debug` all 200, `/turn` SSE emits `narrate_start` then `turn_complete` with a connection-error fallback narrative

## Manual follow-ups (require a running model server — not done in this pass)

- [ ] Boot ccya against a live `mlx_lm.server --host 127.0.0.1 --port 8080`; confirm `curl http://127.0.0.1:8765/healthz` reports `"llm": "ok"` and `"available": true` for the configured model
- [ ] Click through New Game on a dynamic pack (e.g. `zombie-survival`) and confirm `generate_seed` produces a valid envelope end-to-end
