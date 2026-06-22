# Fix: Eval Pipeline Bugs (ArcThread Unhashable + Judge YAML Parse)

## Status
`completed`
**Created**: 2026-05-19  
**Commits**: 
- `0b11fcc` — ArcThread unhashable fix (turn.py)
- `03cf25c` — Judge YAML parse robustness with regex fallback (judge.py)
- `0c2d327` — All judge response format patterns handled (judge.py) 
- `32a5eb0` — String npc_add coercion + missing inventory removal non-blocking (extraction.py, turn.py)  

## Problem Summary

Two bugs caused all 13 eval turns to fail with errors:
1. **TypeError: unhashable type 'ArcThread'** — consistent crash on every turn (structural bug)
2. **Judge front matter YAML parse failed** — PyYAML fails when LLM responses contain markdown formatting (`|`, `**bold**`, bare numbers, prose paragraphs) inside YAML front matter blocks; additionally judges output scores in 3 different format patterns that `_FM_RE` only matched one of

Two additional bugs found during eval runs:
3. **extract_scene parse failed (npc_add validation error)** — LLM returns strings like `["bystanders"]` instead of dicts, causing Pydantic model_type errors
4. **Delta validation failures on turns 12-13** — LLM tries to remove inventory items that don't exist in state; treated as fatal rejection → entire turn failed

## Root Causes & Fixes

### Bug 1: ArcThread Unhashable Type Error

**Location**: `/ccya/engine/turn.py:190` in `_apply_thread_signals()`  
**Cause**: Set comprehension `{tid for tid in all_arc_threads}` iterates over `ArcThread` objects (Pydantic BaseModel) directly. Pydantic models without custom `__hash__` are unhashable by default and cannot be used as set members or dict keys.

```python
# Before (bug):
other_threads = [t for t in arc.threads if t.id not in {tid for tid in all_arc_threads}]

# After (fix) — uses .id strings consistent with rest of file:
other_threads = [t for t in arc.threads if t.id not in {t2.id for t2 in all_arc_threads}]
```

**Verification**: Tested with CampaignArc.model_validate() + _apply_thread_signals() call path simulating actual run_turn execution. Returns CampaignArc (was crashing before).

### Bug 2: Judge YAML Parse Failure on Markdown Tables

**Location**: `/ccya/eval/judge.py:814` in `parse_judge_response()`  
**Cause**: LLM responses contain markdown table rows inside YAML front matter (e.g., `| Criterion | Score | Evidence ...`). PyYAML treats leading `|` as a literal block scalar indicator and fails with "expected <block end>, but found '<scalar>'" error.

Additional failure modes discovered during fix:
- Bold text after block scalars (`**Momentum Arc Assessment:**`) causes 'while scanning an alias' error when prose breaks out of YAML block scalar context  
- Bare numbers (`0.8`) in front matter cause 'expected <document start>' error
- LLMs often put structured score fields (state_fidelity_rate, etc.) in body text after `---` delimiter rather than inside the YAML front matter block

Two-layer fix:

**Layer 1** (`_sanitize_fm_for_yaml`, new function): Strip non-YAML content from fm_text before parsing:
- Markdown table rows (`| Criterion | Score | Evidence |`)  
- Column separators like `-|-|-` or `---` with pipes
- LLM prose patterns (`**Heading:**`, `# Heading`, `__underline__`) converted to YAML comments

```python
def _sanitize_fm_for_yaml(fm_text: str) -> str:
    # Strips table rows, column separators, and LLM prose patterns from fm_text
    ...
```

**Layer 2** (`_extract_scores_by_regex`, new function): When yaml.safe_load still fails after sanitization, fall back to extracting structured key-value pairs from both fm_text AND body text using regex patterns that match all recognized judge output fields (mechanical_score, etc.). This handles cases where LLMs put scores in the response body rather than inside YAML.

```python
def _extract_scores_by_regex(fm_text: str) -> dict[str, Any] | None:
    # Extracts structured key-value pairs from LLM-generated front matter using regex patterns
    ...
```

**Verification**: Tested with realistic LLM response containing markdown table rows and bold text inside YAML front matter. parse_judge_response() now extracts scores via regex fallback (was returning empty {} and logging warning). state_correctness judge correctly extracts extraction_accuracy_score=3, mechanic_lifecycle_score=2, state_fidelity_rate from previously-failing responses.

## Files Changed

- `ccya/engine/turn.py` — 2 lines changed (set comprehension fix + missing inventory removal non-blocking) [commits: `0b11fcc`, `32a5eb0`]
- `ccya/eval/judge.py` — +86/-22 → then +77/-18 in follow-up commits. Total judge changes: YAML parse robustness with regex fallback, format pattern detection for 3 LLM response patterns [commits: `03cf25c`, `0c2d327`]
- `ccya/engine/extraction.py` — +40/-1 lines (string npc_add → NpcAdd coercion) [commit: `32a5eb0`]

## Testing

Both fixes verified with targeted integration tests simulating actual run_turn and judge evaluation paths. `make check` passes (ruff linting + mypy type checking).
