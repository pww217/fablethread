---
name: ev
description: ev.py — CLI for turn data, checkers, play, and eval
---

Read these before using:
- `scripts/debug/README.md` — full command reference
- `docs/ev/CHECKERS.md` — checker library

Invocation:
```
.venv/bin/python scripts/debug/ev.py <command> [args...]
```

Key modules:
- `ccya/ev/` — command implementations
- `ccya/ev/checkers/` — checker plugins (26 registered)

**CRITICAL: Sequential execution only.** Only one machine to share. Never run multiple `play --llm --turns N` commands in parallel. Always run sequentially with `&&` or one at a time. Each takes ~20 minutes for 20 turns.
