# Eval Runs — Storage & Workflow

Save directories for automated/CI evals live in `evals/runs/`. (Web UI saves remain in `saves/`.)

Run data (events, state, chronicle, metadata) is gitignored. Reports (group-level `REPORT.md` and per-run `report.md`) are gittracked.

## Directory layout

```
evals/runs/
├── .gitkeep
├── 2026-06-16_fix-pack-loading_a1b2c3d4/
│   ├── .gitkeep
│   ├── REPORT.md                          ← group-level consolidated report (gittracked)
│   ├── 0930_noir-1930s_aggressive_10t/
│   │   ├── .gitkeep
│   │   ├── report.md                      ← per-run report (gittracked, optional)
│   │   ├── events.jsonl                   ← gitignored
│   │   ├── prompts.jsonl                  ← gitignored
│   │   ├── state.yaml                     ← gitignored
│   │   ├── chronicle.md                   ← gitignored
│   │   └── run-meta.yaml                  ← gitignored
│   └── 0945_zombie-survival_explorer_5t/
│       ├── .gitkeep
│       ├── report.md
│       └── ...
├── 2026-06-17_arc-refactor_e5f6g7h8/
│   └── ...
└── latest -> 2026-06-17_arc-refactor_e5f6g7h8/0930_noir-1930s_aggressive_10t/
```

## Report files

- **`REPORT.md`** (group-level): Written at the group directory level (`evals/runs/<group>/REPORT.md`). Contains a consolidated report for all runs in the group.
- **`report.md`** (per-run): Written inside each run directory (`evals/runs/<group>/<run>/report.md`). Optional — only generated if the user requests a per-run report (via `--auto-report` or `--report`).

## Run metadata (`run-meta.yaml`)

Auto-generated on `play --llm` or `play` with a pack (gitignored):

```yaml
run:
  timestamp: "2026-06-16T09:30:00"
  git_sha: "a1b2c3d4"
  git_branch: "feature/arc-refactor"
  tag: "fix-pack-loading"
  pack: "noir-1930s"
  persona: "aggressive"
  turns: 10
  model: "mlx-community/gemma-4-26b-a4b-it-mxfp8"
  temperature: 0.7
```

## Creating runs

```bash
# New session with all metadata
.venv/bin/python scripts/debug/ev.py play --llm --turns 10 \
    --pack noir-1930s --personality aggressive

# Different persona
.venv/bin/python scripts/debug/ev.py play --llm --turns 10 \
    --pack noir-1930s --personality cautious
```

## Running checkers

```bash
# After the session completes
.venv/bin/python scripts/debug/ev.py check --all \
    --save-dir evals/runs/latest

# Generate report from eval run (not from check)
.venv/bin/python scripts/debug/ev.py eval run <scenario.yaml> --auto-report
```

## Generating reports

```bash
# Per-run report (auto after eval run)
.venv/bin/python scripts/debug/ev.py eval run <scenario.yaml> --auto-report

# Per-run report (explicit path)
.venv/bin/python scripts/debug/ev.py eval run <scenario.yaml> --report report.md

# Per-run report (play mode)
.venv/bin/python scripts/debug/ev.py play --llm --turns 10 --pack noir-1930s --auto-report
```

Reports are rendered from `evals/ev-tooling/templates/report.md.j2`. The template groups checkers by rubric area. Rubric section numbers map to the corresponding checker lists for focused evals.

## Viewing in web UI

1. Open the game at `localhost:8765`
2. In the save picker, check **"Show eval runs"**
3. Eval runs appear with a `runs/` prefix in the dropdown
4. Switch to one to browse its turns in the turn log

## Practical workflow

```bash
# Single-shot debug
.venv/bin/python scripts/debug/ev.py play --llm --turns 3 \
    --pack noir-1930s
.venv/bin/python scripts/debug/ev.py check --all \
    --save-dir evals/runs/latest

# Multi-persona eval (3 packs × 3 personas = 9 runs)
for pack in noir-1930s zombie-survival fantasy-quest; do
  for persona in aggressive cautious explorer; do
    .venv/bin/python scripts/debug/ev.py play --llm --turns 10 \
      --pack "$pack" --personality "$persona"
    .venv/bin/python scripts/debug/ev.py check --all \
      --save-dir evals/runs/latest
  done
done
```

## Git tracking

Only reports are gittracked:
- `evals/runs/.gitkeep` (directory placeholder)
- `evals/runs/<group>/.gitkeep` (directory placeholder)
- `evals/runs/<group>/REPORT.md` (group-level consolidated report)
- `evals/runs/<group>/<run>/.gitkeep` (directory placeholder)
- `evals/runs/<group>/<run>/report.md` (per-run report, optional)

Everything else (events.jsonl, prompts.jsonl, state.yaml, chronicle.md, run-meta.yaml) is gitignored.

## Comparison with saves/

| Aspect | `saves/` | `evals/runs/` |
|--------|----------|---------------|
| Created by | Web UI gameplay | CLI/ev.py play/prompt-eval |
| Naming | User chooses | Auto: `{YYYY-MM-DD}_{tag}_{sha:8}` (run: `{HHMM}_{pack}_{persona}_{turns}t`) |
| Metadata | No | `run-meta.yaml` (gitignored) |
| Turn count | Unlimited | Fixed (`--turns N`) |
| Checkers | Manual | Auto with `--eval` flag |
| Web UI visibility | Always | Only with "Show eval runs" checked |
| Git-tracked | No (gitignored) | Reports only (`.gitkeep`, `REPORT.md`, `report.md`) |

## Future work

- `--rubric` flag for focused checker suites
- CI integration: auto-run on PR, report as comment
- Cross-run comparison: `ev.py compare runA runB`
