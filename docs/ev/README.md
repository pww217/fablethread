# ev.py — CCYA Debug & Eval CLI

```bash
.venv/bin/python scripts/debug/ev.py <command> [args...]
```

## Quick Start

```bash
# Overview of all turns in the latest session
.venv/bin/python scripts/debug/ev.py summary

# Full pipeline dump for turn 5
.venv/bin/python scripts/debug/ev.py turn 5

# Run all checkers
.venv/bin/python scripts/debug/ev.py check --all --save-dir evals/runs/latest

# Play one turn
.venv/bin/python scripts/debug/ev.py play "I search the room." --pack noir-1930s
```

## Documentation

| Topic | File |
|-------|------|
| Full command reference | [COMMANDS.md](COMMANDS.md) |
| Prompt template audit | [PROMPT-AUDIT.md](PROMPT-AUDIT.md) |
| Eval run storage & workflow | [EVAL-RUNS.md](EVAL-RUNS.md) |
| Checker library | [CHECKERS.md](CHECKERS.md) |
| Eval rubric | [RUBRIC.md](RUBRIC.md) |
