# Phase 2 Review Findings

## Bug: `build_trace` truncation can cut the constants block in half

**File:** `ccya/eval/judge.py:164-166`

```python
_TRUNC_MARKER = "\n\n[... trace truncated to fit judge window ...]\n\n"
head_keep = int(max_chars * 0.6)
tail_keep = max_chars - head_keep - len(_TRUNC_MARKER)
```

`head_keep` and `tail_keep` are computed from `max_chars` without accounting for the constants block length. If the constants block is ~300 chars and `max_chars` is 30000, the truncation splits the combined string at arbitrary positions. The constants block (which the judge needs to reason from current values) could be partially cut off, leaving the judge with a truncated header.

**Fix:** Set `head_keep = max(int(max_chars * 0.6), len(lines[0]) + 1)` so the constants block is always preserved in the head portion.

**Status:** ✅ Fixed — `ccya/eval/judge.py:164`

---

## Bug: `build_trace` concatenation has no separator between constants block and first turn

**File:** `ccya/eval/judge.py:161`

```python
trace = "\n".join(lines) + full
```

`lines` contains one element (`constants_block()`), so `"\n".join(lines)` is just the constants block string with no trailing newline. `full` starts with `TURN 1 ...`. The result is:

```
## Engine Constants (live ...)\n\n- Scene pressure: ...TURN 1 — ...
```

The constants block ends with a `\n\n` from `constants_block()`, so this actually works — the constants block's own trailing newlines provide the separator. This is fine, just worth noting the dependency on `constants_block()`'s internal formatting.

---

## Minor: `_context_line` iterates over events that may lack `extraction` key

**File:** `ccya/eval/judge.py:90-96`

```python
extraction = event.get("extraction") or {}
for stream in ("scene", "state", "progress"):
    ex = extraction.get(stream) or {}
    cm = ex.get("context_meta") or {}
```

This is defensive and correct — old events without `extraction` or without `context_meta` will produce `"(no context telemetry)"`. No bug here, just confirming the guard is adequate.

---

## Minor: `trim_messages` callers in `turn.py` — `run_turn_retry` doesn't add `context_meta` to `rules_prompt`

**File:** `ccya/engine/turn.py:1033-1037`

In `run_turn_retry`, the `rules_prompt` event is set to empty strings:

```python
"rules_prompt": {
    "rendered_system": "",
    "rendered_user": "",
    "output": "",
},
```

This is correct — `run_turn_retry` skips the rules call, so there's no rules prompt to log. No `context_meta` needed.

---

## Minor: Rubric example JSON shows `"turns": [3, 7]` for `extraction_consistency` but `"turns": []` for narrative criteria

**File:** `evals/rubrics/default.md`

The example JSON in the rubric shows mixed `turns` values — some criteria have turn numbers, others have empty arrays. This is intentional per the plan (mechanical criteria get turns, narrative criteria get `[]`). The plan says:

> For mechanical criteria, populate `turns` with turn numbers where the issue was observed. Leave `turns` as `[]` for narrative criteria.

The example is illustrative, not prescriptive. This is fine.

---

## Summary

| # | Severity | Issue | Status |
|---|----------|-------|--------|
| 1 | **Bug** | `build_trace` truncation doesn't reserve space for constants block — can cut it in half | ✅ Fixed |
| 2 | Minor | Constants block separator depends on `constants_block()` internal formatting (works, but fragile) | ✅ No fix needed — `constants_block()` ends with `\n\n` |

Only issue #1 was a real bug. The rest are observations.
