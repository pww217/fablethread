# Logging Standards

## Log levels

| Level | When to use | Required extra context |
|---|---|---|
| `DEBUG` | Detailed trace: per-step timing, LLM call start/end, token counts, conditional branches, truncation details | Pipeline: `trace_id`, `turn` |
| `INFO` | Phase boundaries: pipeline start/end per turn, compaction trigger, state save/load, server startup | Pipeline: `trace_id`, `turn`; State: `save_dir`; Server: `save`, `turn` |
| `WARNING` | Recoverable anomalies: malformed data skipped, non-critical parse failures, deprecated paths, LLM retries | Pipeline: `trace_id`, `turn`, `error_kind`; State: `save_dir`; Server: `save`, `turn`, `error_kind` |
| `ERROR` | Definitive failures: LLM call hard failure, state load failure, migration failure, critical parse failures | Same as WARNING + `exc_info` |
| `EXCEPTION` | Use `_log.exception()` in `except` blocks where we cannot recover | Same as WARNING |

See `docs/design/complete/observability-design.md` for the full design authority on logging and error classification.
