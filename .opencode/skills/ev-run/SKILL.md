---
name: ev-run
description: Run a full 5-pack evaluation and produce a consolidated report
---

Purpose: Execute the standard 5-pack evaluation. Its only output is the raw run data and per-run auto-reports. After completion, hand off to ev-review for deeper analysis.

## Prerequisites

- Server running on `localhost:8765`
- LLM backend on `localhost:8080` with `mlx-community/gemma-4-26b-a4b-it-mxfp8`
- `.venv/bin/python scripts/debug/ev.py` — never `python3` or `source .venv/bin/activate`
- Set bash timeout to at least 25 × 60000 = 1,500,000ms per run

## Standard 5-Pack Eval

Always run as 5 sequential games. Each scenario uses a fixed persona pairing:

| Scenario | Persona |
|---|---|
| `noir-1930s` | `driven` |
| `space-western` | `speedrunner` |
| `golden-piracy` | `completionist` |
| `zombie-survival` | `cautious` |
| `allied-ww2` | `aggressive` |

**Defaults:** 25 turns, model `mlx-community/gemma-4-26b-a4b-it-mxfp8`, auto-report on.

Available personas: `aggressive`, `cautious`, `absurd`, `explorer`, `driven`, `opportunist`, `completionist`, `speedrunner`, `custom`. Defined in `ccya/ev/personality.py`.

## Execution

**CRITICAL: Sequential only.** One machine. Never parallel. Each run takes ~25 min.

```bash
pairs="noir-1930s:driven space-western:speedrunner golden-piracy:completionist zombie-survival:cautious allied-ww2:aggressive"
for pair in $pairs; do
  pack=${pair%:*}
  persona=${pair#*:}
  .venv/bin/python scripts/debug/ev.py play --llm --turns 25 \
    --pack "$pack" --personality "$persona" --auto-report
done
```

The `--auto-report` flag writes a per-run `report.md` inside each run directory. Alternatively, set `auto_report: true` in the session's `ev.yaml` to enable it without the flag.

## Handoff to ev-review

After all 5 runs complete, invoke `ev-review` to:
1. Scan roadmap for `validating` items and check against current run data
2. Run full rubric against the new runs
3. File new bugs as `new`
4. Write consolidated REPORT.md with validating item status

## Reference Docs

- `docs/ev/COMMANDS.md` — full command reference
- `docs/ev/EVAL-RUNS.md` — eval run storage & workflow
- `docs/ev/CHECKERS.md` — checker library
- `docs/ev/RUBRIC.md` — eval rubric
