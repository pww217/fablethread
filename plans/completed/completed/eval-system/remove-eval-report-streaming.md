# Remove eval report streaming plumbing

## Status
`completed`

## Phases

2 phases: Eliminate dead streaming infrastructure from the eval report pipeline and simplify to a single-pass synchronous report write.

## Issue

The eval report system includes streaming plumbing (`append_judge_chunk()`, sentinel blocks, `on_chunk` callbacks) that was designed for live token-by-token append into REPORT.md but never wired up. The callback defaults to `_noop_chunk` everywhere. This adds ~150 lines of dead code across 3 files plus cognitive overhead from the two-phase write pattern (skeleton → finalize).

## Solution

Remove all streaming artifacts: delete `append_judge_chunk()`, sentinel constants, and `on_chunk` parameter; merge `finalize_report()` into a single `write_full_report()` that writes the complete report in one pass after judges finish. The CLI flow becomes: run scenario → run judges → write full report once. No behavioral change — the output is identical since finalize already does this today.

## Firm decisions

1. Keep `chat_stream()` in llm_client.py — it's used by the game engine UI and must stay.
2. Keep `_run_single_judge()` collecting chunks into a list internally; just remove the callback parameter.
3. The two-phase write (skeleton then finalize) is replaced with one phase: run judges first, then write full report once. This means REPORT.md won't exist until after judges complete — acceptable since it's not consumed by any other system mid-run.

## Non-goals

- No changes to judge scoring logic or output format.
- No changes to the game engine SSE streaming (`/turn`, `/pack/generate/stream`).
- No test updates (tests are temporarily removed per AGENTS.md).
- No backward compatibility for old REPORT.md skeleton format.

## Risks, Ambiguities, and Blockers

1. **REPORT.md not visible until judges finish**: The old flow wrote a partial report immediately after the runner phase. If any external tool watches REPORT.md during execution (e.g., live dashboard), it will see nothing until judges complete. Unlikely given eval runs are batch jobs, but worth confirming no such consumer exists.
2. **`--no-judge` flag**: The CLI supports `--no-judge` which skips judge calls. After this change, the report still needs to be written once (without judge section). This is handled by having `write_full_report()` accept an optional empty judges list and render without a Judge Summary block.
3. **`judge-only` subcommand**: It already runs judges then writes the report via skeleton+finalize. After merge, it becomes one call — no behavioral change.

## Implementation — Phase 1: Remove streaming from report.py

### Context files to load
- `ccya/eval/report.py` (entire file)
- `docs/architecture/eval-harness.md` lines 180-190 (for context on documented behavior)

### Detailed steps

#### Step 1.1 — Delete streaming sentinel constants and `append_judge_chunk()`

**File:** `ccya/eval/report.py`

**What:** Remove these items:
- `_JUDGE_STREAM_SENTINEL_OPEN = "<!-- JUDGE_STREAM_OPEN -->\n"` (line 715)
- `_JUDGE_STREAM_SENTINEL_CLOSE = "<!-- JUDGE_STREAM_CLOSE -->\n"` (line 716)
- `append_judge_chunk()` function entirely (lines 803–820)

**Why:** This is dead code. The sentinel constants are only referenced by `write_report_skeleton` and `finalize_report`. `append_judge_chunk` is never called anywhere in the codebase. Removing them eliminates the streaming concept from report.py.

**Validation:** Run `grep -n "JUDGE_STREAM\|append_judge" ccya/eval/report.py` — should return no matches. Run `grep -rn "append_judge_chunk" ccya/` across entire repo — should only find comments/docstrings referencing it (none expected).

#### Step 1.2 — Rewrite `write_report_skeleton()` into `write_full_report()`

**File:** `ccya/eval/report.py`

**What:** Replace the two functions (`write_report_skeleton` + `finalize_report`) with a single function:

```python
def write_full_report(
    run_result: RunResult,
    *,
    eval_cfg: EvalConfig,
    judge_results: list[JudgeResult] | None = None,
    runs_dir: Path | None = None,
) -> Path:
```

The implementation merges the body of both functions. Key differences from each original:
- From `write_report_skeleton`: remove the streaming placeholder section (`## Judge (streaming…)`, sentinel blocks, fenced code block). Instead render a normal "## Judge Summary" section if judges are provided.
- From `finalize_report`: keep the atomically-written output (`tmp.replace()`), flag computation with judge data, and full verdict rendering.
- If `judge_results` is None or empty: skip all judge-related sections (Judge Summary, Meta Judge Verdict, domain judge verdicts) but still render flags, auto-checker, assertions, pacing, turn metrics. This supports the `--no-judge` flag path.

Critical guard: convert None/missing to an empty list BEFORE any downstream processing — use `judges = judge_results if isinstance(judge_results, list) and len(judge_results) > 0 else []`. The old finalize_report pattern (`judge_result if isinstance(...) else [judge_result]`) produces `[None]` when given None, which crashes on `.scores`/`.judge_id` access.

The function body follows this order of sections in REPORT.md:
1. Header metadata (scenario id, pack, model, timestamps, output dir, comparison target)
2. Judge Summary block (only if judge_results provided and non-empty)
3. Flag block
4. Meta Judge Verdict (if meta judge present)
5. Domain Judge Verdicts (each in its own ## section)
6. Auto-Checker table
7. Universal Assert Results table
8. Pacing Metrics
9. Turn Metrics combined table
10. Warnings subsection (only if regressions exist with "warn" severity)

**Why:** Consolidates the two-phase write into one pass. Eliminates the need for `finalize_report()` entirely and removes the streaming placeholder from skeleton output. The function is idempotent — calling it once produces the same REPORT.md that finalize_report produced today.

**Validation:** Run `grep -n "write_report_skeleton\|finalize_report" ccya/eval/report.py` — only the new `def write_full_report` should appear, no old functions. Check that `_render_flag_block`, `_collect_flags`, `_compute_regressions`, and all render helpers are still referenced by `write_full_report`.

#### Step 1.3 — Remove unused import if any results from consolidation

**File:** `ccya/eval/report.py`

**What:** Review imports at top of file. If removing functions eliminates need for any imported symbol (unlikely given the heavy usage of RunResult, JudgeResult, EvalConfig), remove it. Otherwise leave as-is.

**Why:** Clean code rule — no unused imports.

**Validation:** `grep -c "from ccya.eval" ccya/eval/report.py` and verify each import is referenced in remaining functions.

### Tests to write or update
None per AGENTS.md (tests temporarily removed during refactor).

### REPOMAP updates required
- If `docs/repomap.md` documents the two-phase report pipeline, remove references to `write_report_skeleton`, `finalize_report`, and `append_judge_chunk`. Add entry for new `write_full_report()` function.
- Update `docs/architecture/eval-harness.md` lines 184-185: replace the two-function description with a single-pass `write_full_report(run_result, eval_cfg, judge_results=None)` that writes REPORT.md in one step after judges complete.

## Implementation — Phase 2: Wire up CLI and clean judge.py

### Context files to load
- `ccya/eval/cli.py` (entire file)
- `ccya/eval/judge.py` lines 1015–1096 (`_run_single_judge`)
- `ccya/eval/judge.py` lines 1203–1284 (`run_judges`, `_noop_chunk`)

### Detailed steps

#### Step 2.1 — Remove `on_chunk` parameter from `_run_single_judge()`

**File:** `ccya/eval/judge.py`

**What:** In the `_run_single_judge()` function signature (around line 1027), remove:
- The `on_chunk: Callable[[str, str], None]` parameter
- Both calls to `on_chunk(spec.id, chunk)` inside the two async for loops (lines 1063 and 1074)

Keep the `chunks: list[str] = []` collection — chunks are still needed because they form the raw judge response. Just don't emit them via callback anymore.

**Why:** The callback is never used (`_noop_chunk`). Removing it simplifies `_run_single_judge()` and eliminates a no-op loop iteration overhead per token chunk.

**Validation:** Run `grep -n "on_chunk" ccya/eval/judge.py` — should return zero matches. Then run `grep -rn "Callable\[" ccya/eval/judge.py` to check if Callable remains referenced elsewhere; remove the import from top of file if it was only used for on_chunk.

#### Step 2.2 — Remove `_noop_chunk` local function from `run_judges()`

**File:** `ccya/eval/judge.py`

**What:** Delete:
- The `_noop_chunk` local function definition (line 1203)
- All three call sites passing `on_chunk=_noop_chunk`: lines 1237, 1277. Note that the first one is in domain judge loop and second/third are for meta judge — remove from both paths.

Update `_run_single_judge()` calls to not pass `on_chunk` (since it's removed from signature).

**Why:** Dead code cleanup. The local function exists only because `_run_single_judge` required a callback parameter that was always no-op.

**Validation:** Run `grep -n "_noop_chunk" ccya/eval/judge.py` — should return zero matches. Run `grep -rn "on_chunk\|_noop_chunk" ccya/` across entire repo — only hits in comments/docstrings expected (none expected).

#### Step 2.3 — Update CLI: replace skeleton+finalize with single write_full_report call

**File:** `ccya/eval/cli.py`

**What:** Change the import on line 31 from:
```python
from ccya.eval.report import write_report_skeleton, finalize_report
```
to:
```python
from ccya.eval.report import write_full_report
```

In `_run_one_scenario()` (lines 119–162): remove the `write_report_skeleton` call on line 119. Move it to after judge execution — replace lines 157-162 with a single:
```python
report_path = write_full_report(
    rr, eval_cfg=eval_cfg, judge_results=judge_results if not args.no_judge else None,
)
print(f"[eval] report written: {report_path}", file=sys.stderr)
```

If `args.no_judge` is True or judges are disabled, pass `judge_results=None`. The function handles rendering without judge sections.

In `_cmd_judge_only()` (lines 247-248): replace the two calls with one:
```python
report_path = write_full_report(
    rr, eval_cfg=eval_cfg, judge_results=judge_results, runs_dir=runs_dir,
)
print(f"[eval] report written: {report_path}", file=sys.stderr)
```

Also remove the print on line 120 (`[eval] skeleton written`). Update the print on line 162 to say "report written" instead of "report finalized".

**Why:** The CLI flow becomes simpler: runner → judges → one report write. No intermediate partial file is created. This matches the new single-pass design in report.py.

**Validation:** Run `grep -n "write_report_skeleton\|finalize_report" ccya/eval/cli.py` — should return zero matches. Verify both `_run_one_scenario` and `_cmd_judge_only` call only `write_full_report`.

### Tests to write or update
None per AGENTS.md (tests temporarily removed during refactor).

### REPOMAP updates required
- If `docs/repomap.md` documents the pipeline flow, update: remove "skeleton → finalize" two-phase description; replace with single-pass `write_full_report()`. Remove `_noop_chunk` and `on_chunk` from judge.py API surface.
