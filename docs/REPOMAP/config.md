# Config — config.yaml and EngineConfig

## config.yaml sections

### `llm`
- `host` — LLM server URL (e.g. `http://127.0.0.1:8080/v1`)
- `model` — model identifier
- `request_timeout_s` — timeout in seconds (default 180)
- `narrate_temperature` — temperature for narrate call (default 0.9)
- `extract_temperature` — temperature for extract calls (default 0.4)
- `max_extract_retries` — max parse retries for extractors (default 1)
- `enable_extract_thinking` — enable thinking for extractors
- `enable_narrate_thinking` — enable thinking for narrate
- `prompt_token_budget` — max tokens for prompt trimming (default 32768)

### `rules`
- `temperature` — temperature for rules/intent call (default 0.2)
- `max_retries` — max retries for rules call (default 1)

### `game`
- `default_save` — default save directory name
- `setting_pack` — default pack to use
- `window_turns` — number of turns to show in window
- `chronicle_prefix_budget_tokens` — tokens for chronicle prefix (default 1500)
- `recent_events_max` — rolling window size for recent events (default 20)
- `warmup_on_start` — pre-load model on server start
- `character_creation_enabled` — allow character creation UI
- `scene_pressure_building_at` — background → building urgency threshold (turns, default 6)
- `scene_pressure_immediate_at` — building → immediate urgency threshold (turns, default 10)
- `compact_every` — compress narrative history every N turns (0 = disabled, default 4)
- `compact_temperature` — temperature for compaction LLM call (default 0.1)

### `server`
- `bind_host` — bind address (default 127.0.0.1)
- `bind_port` — bind port (default 8765)

### `logging`
- `file` — log file path (default `logs/llm-g.log`)
- `level` — log level (default INFO; DEBUG required for log_llm_io)
- `log_llm_io` — log full prompts + raw responses
- `log_llm_io_max_chars` — truncate per field to keep log readable (default 4000)
- `log_prompts` — log fully formatted prompts to `logs/prompts.log`

### `debug`
- `panel` — enable debug panel

## EngineConfig dataclass

Mirrors config.yaml sections. Fields: temps, timeouts, token budget, thinking toggles, compaction settings (`compact_every`, `compact_temperature`), scene pressure thresholds.
