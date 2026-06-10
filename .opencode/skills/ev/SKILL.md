---
name: ev
description: ev.py is the primary CLI for reading turn data, running checkers, playing game turns, and debugging mechanics. Reads events.jsonl directly — no server needed (except `play` which needs the LLM backend).
---

Read these repo files before using this skill:
- `scripts/debug/README.md` — ev.py command reference, event shape, mechanics sections
- `docs/ev/CHECKERS.md` — checker library documentation
- `docs/architecture/ev-tooling.md` — architecture overview

## CRITICAL: Python invocation

**Always use this exact form — no exceptions:**

```bash
.venv/bin/python scripts/debug/ev.py <command> [args...]
```

- **Never** use `python3 scripts/debug/ev.py` — system Python is 3.9, ev.py requires 3.13+
- **Never** use `source .venv/bin/activate && python3` — the activate script doesn't work reliably in this environment
- **Never** use `--help` — ev.py has no help command. See `scripts/debug/README.md` for the full command reference.
- **Always** run from the repo root (`/Users/pwilson/Repos/ccya`)

## Capabilities

- **Inspect**: `summary`, `turn`, `prompt`, `outputs`, `timing` — see what happened in any turn
- **Debug mechanics**: `mechanics`, `deltas`, `state`, `diff`, `trace`, `search` — track momentum, beats, NPCs, state mutations across turns
- **Play**: `play` — run new turns via the engine into existing or new save directories
- **Validate**: `check` — run checker plugins against events; `eval run` — run YAML scenarios end-to-end

## Key files

| File | Purpose |
|------|---------|
| `scripts/debug/ev.py` | CLI entry point (thin wrapper) |
| `scripts/debug/README.md` | Full command reference, workflows, pitfalls |
| `ccya/ev/` | Command implementations (inspect, play, check, eval) |
| `ccya/ev/checkers/` | Checker plugins (momentum, beats, inventory, NPCs, etc.) |
| `docs/ev/CHECKERS.md` | Checker documentation |
| `docs/architecture/ev-tooling.md` | Architecture overview of ev tooling |
| `ccya/ev/play.py` | Play command implementation (play_turn function) |
| `saves/` | Game save directories (each has state.yaml + events.jsonl) |

## Save path convention

Commands that read events take the events.jsonl path as the **last positional arg**.
Commands that need full state also accept `--save-dir DIR`.

```
ev.py turn 5                               # reads saves/default/events.jsonl
ev.py turn 5 saves/my-game/events.jsonl    # reads specific save
ev.py check 5 --all --save-dir saves/my-game  # reads state from directory
ev.py play "action" --save-dir saves/my-game saves/my-game/events.jsonl  # play into existing save
```
