---
name: ev-run
description: Run a full 5-pack evaluation and produce a consolidated report
---

Purpose: Launch eval scenarios, run them sequentially, generate automated per-run reports, and synthesize a consolidated group-level report with regression detection.

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

## Consolidated Report (`REPORT.md`)

After all 5 runs complete, synthesize a consolidated `REPORT.md` at the group directory level (`evals/runs/YYYY-MM-DD_{tag}_{sha:8}/REPORT.md`):

- **Checker scores** — read each per-run `report.md`, compile pass/fail table across all 5 scenarios
- **LLM qualitative analysis** — narrative flow, pacing, thread resolution, convergence, character consistency
- **Regression detection** — compare against the most recent prior eval group (see below)
- **Recommendations** — per-scenario notes on what to investigate or fix

**Model:** `evals/runs/2026-06-17_0.27.0-31-g07266252_0726625/consolidated-narrative-eval-2026-06-17.md`

## Regression Detection

1. Find the newest group directory before the current one in `evals/runs/`
2. Read its `REPORT.md` for baseline checker scores and qualitative notes
3. For each scenario, delta: checker pass count, known failure modes, narrative quality
4. Run `git log --oneline <prior_sha>..HEAD` to identify what changed between the two eval dates
5. In the consolidated report, call out: improvements, regressions, and changes worth investigating

## Reference Docs

- `docs/ev/COMMANDS.md` — full command reference
- `docs/ev/EVAL-RUNS.md` — eval run storage & workflow
- `docs/ev/CHECKERS.md` — checker library
- `docs/ev/RUBRIC.md` — eval rubric
