# Eval Runs — Storage & Workflow

Save directories for automated/CI evals live in `evals/runs/`. (Web UI saves remain in `saves/`.)

## Directory layout

```
evals/runs/
├── 2026-06-16--fix-pack-loading--a1b2c3d4/
│   ├── 0930--noir-1930s--aggressive--10t/
│   │   ├── events.jsonl
│   │   ├── state.yaml
│   │   ├── ev.yaml
│   │   └── run-meta.yaml
│   └── 0945--zombie-survival--explorer--5t/
│       ├── events.jsonl
│       └── ...
├── 2026-06-17--arc-refactor--e5f6g7h8/
│   └── ...
└── latest -> 2026-06-17--arc-refactor--e5f6g7h8/0930--.../
```

## Run metadata (`run-meta.yaml`)

Auto-generated on `play --llm` or `play` with a pack:

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

# Generate eval report
.venv/bin/python scripts/debug/ev.py check --all \
    --save-dir evals/runs/latest --report results.md
```

## Generating reports

Eval reports are rendered from `evals/ev-tooling/templates/report.md.j2`. The template groups checkers by rubric area. Rubric section numbers map to the corresponding checker lists for focused evals.

```bash
# Focused eval: only rubric area 3 (Inventory)
.venv/bin/python scripts/debug/ev.py check --rubric 3 \
    --save-dir evals/runs/latest
```

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
      --save-dir evals/runs/latest --report \
      "evals/reports/${pack}--${persona}.md"
  done
done

# Load a run in the UI
# → localhost:8765, check "Show eval runs", select from dropdown
```

## Comparison with saves/

| Aspect | `saves/` | `evals/runs/` |
|--------|----------|---------------|
| Created by | Web UI gameplay | CLI/ev.py play/prompt-eval |
| Naming | User chooses | Auto: `{timestamp}--{tag}--{sha:8}` |
| Metadata | No | `run-meta.yaml` |
| Turn count | Unlimited | Fixed (`--turns N`) |
| Checkers | Manual | Auto with `--eval` flag |
| Web UI visibility | Always | Only with "Show eval runs" checked |
| Git-tracked | No (gitignored) | `ev-tooling/` tracked, `runs/` not |

## Future work

- `--rubric` flag for focused checker suites
- CI integration: auto-run on PR, report as comment
- Cross-run comparison: `ev.py compare runA runB`
