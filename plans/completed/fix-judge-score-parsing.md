# fix-judge-score-parsing

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Relax front-matter regex anchor | Fix `_FM_RE` to tolerate leading whitespace/text before the `---` delimiter so judge responses that emit preamble before front matter are parsed correctly |
| 02 | Add EVAL_CONTEXT markers to ARCHITECTURE.md | Insert `<!-- EVAL_CONTEXT_START -->` / `<!-- EVAL_CONTEXT_END -->` markers so `load_architecture_context()` returns content instead of empty string |

## Objective
Every domain judge and the meta judge returned `scores={}` in this run (`[eval] judge[X] complete: scores={}`). The `parse_judge_response` function requires the response to begin with `---` at position 0 after `strip_thinking()` and `strip()`. Qwen3.6-35B frequently emits a short prose introduction or blank lines before the YAML front matter block, causing the anchored regex `_FM_RE` to fail and return `({}, body)`. With `scores={}` from all judges, `merge_judge_scores` returns `{}`, so `mechanical_score=?` and no REPORT.md scores are populated. Separately, `load_architecture_context()` always returns `""` because `ARCHITECTURE.md` contains no `<!-- EVAL_CONTEXT_START -->` / `<!-- EVAL_CONTEXT_END -->` markers, meaning judges receive no engine design context.

## Non-goals
- No changes to judge rubrics or prompt templates.
- No changes to the YAML schema of judge responses (score keys, allowed values).
- No changes to how scores are used downstream in `report.py`.
- No addition of EVAL_CONTEXT content to ARCHITECTURE.md beyond the markers themselves (that is a separate editorial task; this plan only inserts the markers so the file can be populated later).

---

## Implementation — Phase 01: Relax front-matter regex anchor

### Files to pull for context
- `ccya/eval/judge.py` — `_FM_RE`, `parse_judge_response`, `_normalize_scores`

### Detailed steps

#### Step 1.1 — Replace `_FM_RE` with a search-based pattern

**File:** `ccya/eval/judge.py`

**What:** Replace the compile-time constant `_FM_RE` and the `_FM_RE.match(s)` call in `parse_judge_response` with a `re.search` pattern that finds the first `---` front matter block anywhere in the string. Extract front matter text and body correctly regardless of leading content.

**Why:** The current pattern:
```python
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL | re.MULTILINE)
```
uses `re.match` (anchored at position 0) and a `\Z` end-anchor. If the model outputs even one blank line before `---`, the match returns `None` and `parse_judge_response` returns `({}, full_text)`. The fix is to use `re.search` with a pattern that locates the first `---` block anywhere, then captures everything after the closing `---` as the body.

**Code Snippet**
```python
_FM_RE = re.compile(
    r"---\s*\n(.*?)\n---\s*\n(.*)",
    re.DOTALL,
)


def parse_judge_response(raw: str) -> tuple[dict[str, Any], str]:
    """Strip thinking tags, then split YAML front matter from markdown body.

    Returns (scores, body_md). If no front matter present, scores is empty dict
    and body_md is the entire (think-stripped) response.
    """
    s = strip_thinking(raw or "").strip()
    if s.startswith("```"):
        s = "\n".join(s.splitlines()[1:])
        if s.endswith("```"):
            s = "\n".join(s.splitlines()[:-1])
    m = _FM_RE.search(s)
    if not m:
        return {}, s
    fm_text = m.group(1)
    body = m.group(2).strip()
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        _log.warning("judge front matter YAML parse failed: %s", exc)
        return {}, s
    if not isinstance(fm, dict):
        return {}, s
    return _normalize_scores(fm), body
```

The only changes from the current implementation:
1. `_FM_RE` loses the `^` anchor and `\Z` anchor, and switches from `re.MULTILINE` to plain `re.DOTALL`.
2. `_FM_RE.match(s)` → `_FM_RE.search(s)`.
3. `body = m.group(2)` → `body = m.group(2).strip()` to clean leading newlines.

**Validation:** After the change, run `make eval --no-judge` to get a fresh events file, then `make eval judge-only <run_dir>`. Confirm `[eval] judge[state_correctness] complete: scores={'state_fidelity_rate': ..., ...}` — i.e., scores are non-empty. Also run:
```python
from ccya.eval.judge import parse_judge_response
scores, body = parse_judge_response("""
Here is my analysis.

---
mechanical_score: 3
narrative_score: 4
---
## Key Findings
All good.
""")
assert scores == {"mechanical_score": 3, "narrative_score": 4}
```

### Tests to write or update

**File:** `tests/test_eval_judge.py` (create if absent)

Test function: `test_parse_judge_response_with_leading_preamble`
- Input: `"Here is my analysis.\n\n---\nmechanical_score: 3\n---\n## Body"`
- Assert `scores == {"mechanical_score": 3}`.
- Assert `"Body" in body`.

Test function: `test_parse_judge_response_no_front_matter`
- Input: `"No YAML here."`
- Assert `scores == {}` and `body == "No YAML here."`.

Test function: `test_parse_judge_response_front_matter_at_start`
- Input: `"---\nmechanical_score: 5\n---\n## Body"`
- Assert `scores == {"mechanical_score": 5}`.

Test function: `test_parse_judge_response_strips_thinking`
- Input: `"<think>Reasoning.</think>\n---\nmechanical_score: 2\n---\n## Body"`
- Assert `scores == {"mechanical_score": 2}`.

Test function: `test_parse_judge_response_blank_lines_before_fm`
- Input: `"\n\n\n---\nmechanical_score: 4\n---\n## Body"`
- Assert `scores == {"mechanical_score": 4}`.

### REPOMAP and architecture updates
`docs/REPOMAP/eval.md` — update note on `parse_judge_response`: regex is now search-based, tolerates leading preamble.

### Risks
1. If a judge response body itself contains a `---\n...\n---` block (e.g., a markdown HR or YAML fence), `re.search` will match the *first* such block. This is correct behaviour — the front matter must be the first `---` block. If no scores are in the first block, `_normalize_scores` returns `{}` and the body is everything after it, which is the same outcome as before.
2. The `\Z` removal means the regex no longer asserts it consumes the whole string. This is intentional and safe — `m.group(2)` captures everything after the closing `---\n` to end of string via `(.*)` with `re.DOTALL`.

---

## Implementation — Phase 02: Add EVAL_CONTEXT markers to ARCHITECTURE.md

### Files to pull for context
- `docs/ARCHITECTURE.md` — current content
- `ccya/eval/architecture_context.py` — `_START`, `_END` marker constants

### Detailed steps

#### Step 2.1 — Insert marker comments into ARCHITECTURE.md

**File:** `docs/ARCHITECTURE.md`

**What:** Wrap the section(s) of `ARCHITECTURE.md` that describe the engine's pipeline design — the parts most useful for a judge evaluating mechanical correctness — with the exact marker strings `<!-- EVAL_CONTEXT_START -->` and `<!-- EVAL_CONTEXT_END -->`. The content between the markers should include: the pipeline overview (rules → narrate → extract), the three extraction streams (scene, state, progress), state shape summary, and any invariants the engine enforces. Do not add new content — only add the two marker comment lines around existing content.

**Why:** `load_architecture_context()` searches for these exact strings:
```python
_START = "<!-- EVAL_CONTEXT_START -->"
_END   = "<!-- EVAL_CONTEXT_END -->"
```
Without them, `s < 0 or e < 0` is always true and the function returns `""`. Every judge invocation then has `arch_context = ""`, so the rubric system prompt contains no engine design reference. The warning `architecture context: markers not found or malformed` fires every run.

**Code Snippet**

The executor must read `docs/ARCHITECTURE.md` in full, identify the section(s) covering the turn pipeline and extraction streams, then insert the two marker lines:

```markdown
<!-- EVAL_CONTEXT_START -->
[existing pipeline/extraction content here — do not paraphrase, use exact existing text]
<!-- EVAL_CONTEXT_END -->
```

The markers must be on their own lines. The `<!-- EVAL_CONTEXT_START -->` line goes immediately before the first relevant section heading. The `<!-- EVAL_CONTEXT_END -->` line goes immediately after the last relevant section's content, before any unrelated sections.

If `docs/ARCHITECTURE.md` contains no pipeline description yet (the file may be a stub), add a minimal stub section between the markers:

```markdown
<!-- EVAL_CONTEXT_START -->
## Turn Pipeline

Each turn runs five sequential LLM calls:
1. **rules** — intent parsing, skill check resolution, band assignment
2. **narrate** — narrative prose generation from rules outcome
3. **extract_scene** — NPC presence, location changes, scene tags
4. **extract_state** — inventory and PC condition changes
5. **extract_progress** — thread signals, drift analysis, recent events, GM beats, scene pressure

State is mutated only by `apply_delta` in `state/delta.py` after all extraction streams complete.
<!-- EVAL_CONTEXT_END -->
```

**Validation:** After the change:
```python
from ccya.eval.architecture_context import load_architecture_context
result = load_architecture_context()
assert result != ""
assert "ENGINE DESIGN REFERENCE" in result
```
Also confirm the warning `architecture context: markers not found or malformed` no longer appears in `make eval` output.

### Tests to write or update

**File:** `tests/test_eval_architecture_context.py` (create if absent)

Test function: `test_load_architecture_context_returns_nonempty`
- Call `load_architecture_context()` with the real `ARCHITECTURE.md` (no mocking — this is a file read test).
- Assert result is a non-empty string.
- Assert `"ENGINE DESIGN REFERENCE"` in result.

Test function: `test_load_architecture_context_missing_markers` (uses `tmp_path`)
- Write a temp `ARCHITECTURE.md` with no markers.
- Patch `_ARCH_PATH` to point to temp file.
- Assert `load_architecture_context()` returns `""`.

### REPOMAP and architecture updates
`docs/REPOMAP/eval.md` — note that `ARCHITECTURE.md` now contains `EVAL_CONTEXT_START`/`END` markers and that `load_architecture_context()` will return non-empty content.

### Risks
1. If `ARCHITECTURE.md` is a near-empty stub, the minimal pipeline description added here will be the only content between the markers. That is fine — even a stub gives judges something. The content can be expanded later without touching this plan.
2. The executor must read `docs/ARCHITECTURE.md` before inserting markers to avoid placing them in the wrong location. The "Files to pull for context" section above mandates this.

## Ambiguities requiring resolution before execution
1. **Phase 02, Step 2.1** — Is `docs/ARCHITECTURE.md` a complete document or a stub? Options: A) Complete document with pipeline sections already written — wrap the relevant existing sections. B) Stub or near-empty — insert the minimal pipeline description provided above between the markers. The executor must read the file and choose accordingly; do not assume either.
