# Plan: Fix Meta Judge — Score Parsing & Report Placement

## Problem

The REPORT.md has `—/5` for all scores and empty domain judge breakdown table. The meta judge verdict at the bottom has synthesized scores from text (0.60, 0.65) rather than from domain judge YAML scores, because **no scores are being parsed**.

### Root causes

1. **`_FM_RE` expects `---` delimiters but all rubrics use `***`** — `judge.py:768-771` has `_FM_RE = re.compile(r"---\s*\n(.*?)\n---\s*\n(.*)")` but every rubric file uses `***` as delimiters. The regex never matches.

2. **Domain judges produce ```yaml code fences, not `---` delimiters** — The LLMs wrap scores in ```yaml fences. `parse_judge_response()` tolerates a leading code fence but then looks for `---` inside, which fails.

3. **Meta judge produces no YAML front matter at all** — Its rubric uses `***` delimiters but the LLM output has no YAML block. Scores end up only in the markdown table body.

4. **Empty scores cascade** — `_build_meta_judge_input()` at line 324 checks `if jr.scores:` — empty dict is falsy, so meta judge gets `{}` as domain scores and synthesizes from text summaries alone.

5. **Meta verdict is at bottom of report** — `finalize_report()` appends meta judge body_md after domain judges (line 884-887). User wants it at top but running last.

## Changes

### 1. Fix `_FM_RE` to match `***` delimiters (`judge.py`)

Update the regex to accept both `---` and `***` as YAML front matter delimiters, matching what all rubrics specify:

```python
_FM_RE = re.compile(
    r"(?:---|\\*\\*\\*)\\s*\\n(.*?)\\n(?:---|\\*\\*\\*)\\s*\\n(.*)",
    re.DOTALL,
)
```

This makes `parse_judge_response()` correctly extract scores from rubric-formatted output.

### 2. Update meta judge rubric (`evals/rubrics/meta.md`)

Add explicit instruction that scores MUST be in YAML front matter at the top of the response, using `***` delimiters. Also expand the meta judge's scope to include top-level assessments of every key mechanic and failure pattern:

- Add to rubric: "Place YAML front matter with all 7 scores at the very top of your response, delimited by `***`."
- Expand Section 3 (Trace Quality Synthesis) to require explicit assessment of: momentum lifecycle, GM beat narration, scene pressure chains, condition deduplication, arc thread progression, inventory extraction accuracy, location change application, NPC mention extraction, and progress actions pipeline.
- This ensures the meta judge synthesizes concrete mechanic-level findings, not just cross-judge score mapping.

### 3. Move meta judge verdict to top of report (`report.py`)

In `finalize_report()`, insert the meta judge verdict section after the flag block (before domain judge verdicts):

Current order:
1. Header
2. Judge Summary
3. Flag block
4. Domain judge verdicts
5. Meta judge verdict ← move this up
6. Auto-Checker
7. Turn Metrics

New order:
1. Header
2. Judge Summary
3. Flag block
4. **Meta Judge Verdict** ← inserted here
5. Domain judge verdicts
6. Auto-Checker
7. Turn Metrics

The meta judge still runs last (execution order unchanged in `run_judges()`), but its output is placed at the top of the report during assembly.

### 4. Verify domain judge score parsing

After fix #1, confirm that `state_correctness.judge.md` scores (`state_fidelity_rate: 0.0`, `extraction_accuracy_score: 1`, `mechanic_lifecycle_score: 2`) are correctly parsed and appear in the domain judge breakdown table and merged scores.

## Files changed

| File | Change |
|------|--------|
| `ccya/eval/judge.py:768-771` | Update `_FM_RE` to match `***` delimiters |
| `evals/rubrics/meta.md` | Add YAML front matter requirement + expand mechanic assessments |
| `ccya/eval/report.py:874-887` | Insert meta judge verdict after flag block, before domain verdicts |

## Testing

- Run the eval again and verify:
  - Judge Summary shows actual scores (not `—/5`)
  - Domain judge breakdown table shows scores per judge
  - Meta judge synthesizes from YAML scores, not text
  - Meta judge verdict appears after flag block, before domain verdicts
  - Meta judge output includes assessments of all key mechanics
