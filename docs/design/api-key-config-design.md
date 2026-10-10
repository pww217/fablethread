# API Key Configuration — Design Document

> **Status:** implemented
> **Related tickets:**

## Problem

The README documents two caveats that block users from using hosted LLM providers:

1. **Features section** (line 17): "API-key auth isn't configurable yet, so hosted providers that require keys aren't supported out of the box."
2. **Requirements table** (line 60): "No API-key config yet (hardcoded placeholder), so keyless servers only."

The root cause is `api_key="local"` hardcoded in `llm_client.py:512` when constructing the `AsyncOpenAI` client. This prevents any provider that requires authentication (OpenAI, Anthropic, Together, Fireworks, etc.) from being used.

## Firm Decisions

1. **api_key becomes a config field** — It will be read from `llm.api_key` in config.yaml, defaulting to `"local"` for backward compatibility with existing local setups.
2. **Single source of truth** — `EngineConfig` is the canonical place for the value; `llm_client.py` reads it from there. No separate config layer.
3. **Client cache key includes api_key** — `_get_client()` caches by `(base_url, api_key)` tuple so different API keys for the same host get separate clients.
4. **config.yaml.example updated** — The example file gets `api_key: ""` with a comment explaining the default.

## Design Principles

- **Minimal diff:** Add one config field, one mapping in `build_engine_config()`, one change to `_get_client()`. No restructuring.
- **Backward compatible default:** `"local"` preserves existing behavior for every user who hasn't set an api_key.
- **No secret management:** This is config.yaml, not a vault. No encryption, no `.env` file, no secret injection.

## Target State

### Config Changes

`config.yaml.example` gains one field:

```yaml
llm:
  api_key: ""
```

Empty string or `"local"` means no auth (local servers). Any other string is passed as-is to the OpenAI SDK.

### Model Changes

`EngineConfig` gains one field:

```python
api_key: str = "local"
```

`build_engine_config()` maps it from `llm.api_key` in the raw config dict.

### Client Changes

`_get_client()` in `llm_client.py` changes from:

```python
def _get_client(base_url: str) -> AsyncOpenAI:
```

to:

```python
def _get_client(base_url: str, api_key: str = "local") -> AsyncOpenAI:
```

The cache key becomes `(base_url, api_key)` instead of just `base_url`. The hardcoded `"local"` in the `AsyncOpenAI()` constructor is replaced with the parameter.

All callers (`_try_host`, `_try_host_stream`, `_chat_openai_compat`) pass `api_key` through the chain. Since they already receive `host` and `model` from config, `api_key` flows alongside them.

### README Changes

- **Features section** (line 17): Remove the parenthetical caveat about API-key auth.
- **Requirements table** (line 60): Remove the parenthetical caveat. Update to note that API keys are configurable via `config.yaml`.

### Collision / Interaction Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| `_chat_with_fallback` / `_chat_stream_with_fallback` | Both call `_get_client(host)` and need api_key | api_key flows through `chat_with_config` → `_try_host` / `_try_host_stream` → `_get_client` alongside host |
| Client cache | Same host, different keys would collide | Cache key is `(base_url, api_key)` tuple |
| Fallback host | Uses same `_get_client(host)` path | Fallback host gets the same api_key (providers typically use one key) |

### Risks

1. **Risk:** Cache grows if users cycle many different API keys for the same host. **Mitigation:** Unlikely in practice; the cache is per-session and cleared on server restart. No eviction needed.
2. **Risk:** Users accidentally commit `config.yaml` with a real API key. **Mitigation:** `config.yaml` is in `.gitignore` (it's a user-local file copied from `config.yaml.example`).

### Rejected Alternatives

1. **Read api_key from environment variable** — Adds a second config surface. Config.yaml is the single source of truth for all settings; keeping it there is simpler.
2. **Make api_key required (no default)** — Breaks every existing local setup. `"local"` default preserves zero-config behavior.
3. **Support multiple api_keys per host** — Over-engineering. A single key per host covers all real use cases.

### Deferred Items

- **Secret encryption** — Not needed for a local config file.
- **Per-endpoint api_keys** — One key per host is sufficient. Different providers don't share hosts.

### What an Implementer Needs to Read

- `fablethread/llm_client.py` — `_get_client()`, `_try_host()`, `_try_host_stream()`, `_chat_openai_compat()`, `chat_with_config()`
- `fablethread/engine/config.py` — `EngineConfig` dataclass, `build_engine_config()`
- `config.yaml.example` — Add the new field
- `README.md` — Remove caveats

### Dependencies on Other Designs

- None
