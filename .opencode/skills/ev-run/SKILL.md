---
name: ev-run
description: Run a full 5-pack evaluation and produce a consolidated report
---

Purpose: Execute the standard 5-pack evaluation, run the full rubric against each run, and produce a consolidated report using `docs/ev/consolidated-report-template.md`.

**Critical constraints:**
1. Write findings into the report as you discover them — do not buffer findings until the end.
2. Work through rubric sections one at a time. Write findings to the report file before moving to the next section. The context window cannot hold all checkers + all findings.
3. The Executive Summary is written LAST, after all rubric sections are complete.

## Prerequisites

- Server running on `localhost:8765`
- LLM backend on `localhost:8080` with `mlx-community/gemma-4-26b-a4b-it-mxfp8`
- `.venv/bin/python scripts/debug/ev.py` — never `python3` or `source .venv/bin/activate`
- Set bash timeout to at least 25 × 60000 = 1,500,000ms per run

## Before Running

1. **Read the template:** `docs/ev/consolidated-report-template.md` — understand the structure before you start.
2. **Read architectural docs:**
   - `docs/architecture/OVERVIEW.md`
   - `docs/architecture/pacing-systems.md`
   - `docs/architecture/step0-ruling.md`
   - `docs/architecture/step2a-scene.md`
   - `docs/architecture/step2b-state.md`
   - `docs/architecture/step2c-storytell.md`
   - `docs/architecture/delta-validate.md`
   - `docs/architecture/state-models.md`
   - `docs/architecture/cross-module-contracts.md`
3. **Find the prior eval group:** locate the newest full 5-pack eval group in `evals/runs/` before the current one.

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

## After Running: Fill the Consolidated Report

The report file is your **long-term memory**. You cannot hold all checkers + all findings in context at once. Work through the template section by section. After each section, write findings to the report file before continuing. If context runs low, stop, write what you have, and resume from the report file on the next invocation.

### Step 1: Testing Tickets

Scan `roadmap/bugs/*.md` for `status: testing`. List them in the report. For each:
- Run targeted checkers against relevant runs
- Assess: confirmed fixed / regressed / inconclusive
- Update the bug file directly:
  - Confirmed fixed → `status: done`, `completed: YYYY-MM-DD`
  - Regressed or still broken → `status: up-next`
  - Inconclusive → leave as `testing`
- After updating all bug files, run `make roadmap` to regenerate the backlog/done indices

### Step 2: Changes Since Last Eval

```bash
git log --oneline <prior_sha>..<current_sha> -- ccya/
```

Focus on engine/prompt areas. Report a brief summary.

### Step 3: Rubric Sections 1–13 — SEQUENTIALLY, ONE AT A TIME

Work through sections **one at a time**. Do not run all checkers for all sections and then write findings. The context window will not hold everything. You must write findings back to the report file as long-term memory after each section.

**The loop:**
1. Pick ONE rubric section (e.g., "Ruling Engine")
2. Run all targeted `ev.py` commands for that section across all 5 runs
3. Parse output, assess findings
4. **Write findings into the report file immediately** — this is your long-term memory
5. Only then move to the next rubric section

**Critical reminders:**
- **Do not run all checkers for all sections first.** You will exceed context.
- **Write findings after every single section.** Treat the report file as persistent memory.
- **If context is getting low, stop and summarize what you've done so far in the report.** Resume from the report after the break.
- **Use the report file itself as your working notes.** Overwrite sections as you refine them.

If you are interrupted or lose context, resume by re-reading the report file (which contains your previous findings) and continue from where you stopped.

### Step 4: Checker Scores

Compile pass/fail table across all rubric areas and all 5 runs.

### Step 5: Executive Summary (LAST)

After all rubric sections are complete, write a concise (5-10 item) summary at the top of the report:
- Largest failures
- Major fix progressions
- Anything that can be said concisely but matters

Do not start with this. Do not let it distract from systematic rubric review.

## Output Location

Write the consolidated report at:
```
evals/runs/<group>/REPORT.md
```

Where `<group>` is the directory created by the 5-pack run (format: `YYYY-MM-DD_{tag}_{sha:8}`).

## Reference Docs

- `docs/ev/consolidated-report-template.md` — report skeleton
- `docs/ev/COMMANDS.md` — full command reference
- `docs/ev/EVAL-RUNS.md` — eval run storage & workflow
- `docs/ev/CHECKERS.md` — checker library
- `docs/ev/RUBRIC.md` — eval rubric checklist (detailed mechanics)
