# ev.py Debug Tool Enhancement — Plan Set

3 phases, independently executable. Zero engine changes.

| Phase | What | Depends on |
|---|---|---|
| [01-state-and-diff.md](01-state-and-diff.md) | `state` command (reads state.yaml) + `diff` command (compare two turns) | None |
| [02-trace-and-search.md](02-trace-and-search.md) | `trace` command (field across turns) + `search` command (find matching turns) | Phase 1 (shared helpers) |
| [03-mechanics-enhancements.md](03-mechanics-enhancements.md) | Narrative output in mechanics, regex section extraction, stream aliases, summary --format json, legacy script deprecation | None |

All changes are to `scripts/debug/ev.py` and `scripts/debug/get-*.sh` only.
