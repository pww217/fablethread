# AGENTS.md — ccya coding guidance

## Module responsibilities — don't cross them

| Module | Owns | Does NOT own |
|---|---|---|
| `engine.py` | `run_turn()` generator, `generate_seed()`, retry logic, metrics, cross-stream message building | state file I/O, HTTP |
| `state.py` | `load_state`, `save_state`, `apply_delta`, `append_event`, `append_chronicle`, `_migrate_state`, `summarize_changes` | LLM calls, HTTP |
| `models.py` | all Pydantic models, `TurnResult` dataclass, `load_config()` | business logic |
| `server.py` | FastAPI routes, SSE streaming, `EngineConfig` wiring, active pack management, `/new-game` | game logic |
| `pack.py` | `Pack`, `PackManifest`, `SeedEnvelope`, `load_pack()`, `list_packs()`, `parse_world_facts()` | state mutation |
| `rules.py` | `resolve_check()` (2d6 + stat + cond − diff → Band), `SkillName`, `Difficulty`, `Band` | LLM calls, state |
| `llm_client.py` | `chat()`, `chat_stream()` (OpenAI-compatible → `mlx_lm.server`), thinking helpers, token-budget trim | prompt construction |

If you find logic in the wrong layer, move it rather than pile on.

## Prompt rules

- **Do not alter prompts unless explicitly asked to** — if you must, preserve the spirit of the existing wording and intent.

## Clean code rules

- **No dead config keys.** If you remove a feature, remove its `config.yaml` key, `EngineConfig` field, and wiring in `server.py` in the same PR.
- **No commented-out code.** If something is deferred, track it in `TODO.md` or the plan file; delete it from source.
- **No silent fallbacks that hide bugs.** Prefer an explicit `if key not in state: raise` or a visible warning over silently inventing a default mid-turn.
- **One source of truth per concept.** `meta.turn` is the turn counter. `chronicle.md` is narrative history. `compendium.npcs` is durable NPC identity. Don't replicate these elsewhere.
- **Minimize LLM input tokens.** Every extra token is latency. Audit prompts for: redundant schema duplication, stale context sections, examples that overlap, large narrative echoes.

## Repo map

Detailed file/function/directory info lives in `REPOMAP/`. Read the relevant files using your Read tool when the task requires it:

| Working on... | Read |
|---|---|
| turn pipeline, extractors, retry | `@REPOMAP/engine.md` |
| state.yaml, apply_delta, persistence | `@REPOMAP/state.md` |
| FastAPI routes, SSE, HTMX | `@REPOMAP/server.md` |
| Pydantic models, TurnResult | `@REPOMAP/models.md` |
| pack loading, pack modes, name gen | `@REPOMAP/pack.md` |
| dice, 2d6, bands | `@REPOMAP/rules.md` |
| LLM client, streaming, mock | `@REPOMAP/llm_client.md` |
| prompt templates | `@REPOMAP/prompts.md` |
| frontend, CSS, JS, templates | `@REPOMAP/frontend.md` |
| testing, FakeLLM, commands | `@REPOMAP/testing.md` |
| config.yaml, EngineConfig | `@REPOMAP/config.md` |
| directory layout | `@REPOMAP/directory.md` |

Cross-cutting tasks (read multiple):
- Modify turn pipeline → `engine.md` + `state.md` + `models.md`
- Add new config option → `config.md` + `engine.md` + `server.md`
- Debug extraction → `engine.md` + `prompts.md` + `state.md`
- New pack → `pack.md` + `models.md`
