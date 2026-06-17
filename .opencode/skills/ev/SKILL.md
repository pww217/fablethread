---
name: ev
description: ev.py — CLI for turn data, checkers, play, and eval
---

Read these before using:
- `scripts/debug/README.md` — full command reference
- `docs/ev/CHECKERS.md` — checker library
- `plans/completed/05-eval/prompt-eval.md` — prompt-eval implementation plan

Invocation:
```
.venv/bin/python scripts/debug/ev.py <command> [args...]
```

Key modules:
- `ccya/ev/` — command implementations
- `ccya/ev/checkers/` — checker plugins (26 registered)
- `ccya/ev/prompt_eval.py` — fast prompt testing (dump/call subcommands)
- `ccya/ev/scenario.py` — scenario YAML loader for prompt-eval

**CRITICAL: Sequential execution only.** Only one machine to share. Never run multiple `play --llm --turns N` commands in parallel. Always run sequentially with `&&` or one at a time. Each takes ~20 minutes for 20 turns.

**prompt-eval:** Two subcommands — `dump` renders prompts from event data (no LLM), `call` renders + LLM + check. LLM calls take ~65s for full storytell prompts. Use `dump` for template iteration.
