# Meta Report — Eval Process Improvements

**Date:** 2026-06-20
**Scope:** Observations on the eval process itself, not the game engine.

---

## CLI Issues

### 1. `--pack` vs positional arg confusion
- `zombie-survival` run created as `1901--unknown--custom--30t` in June 18 eval due to `--pack` vs positional arg confusion.
- **Status:** Appears fixed in June 20 runs (all 5 have correct theme names).

### 2. Incomplete run detection
- `0140--space-western--custom--30t/` exists with only `run-meta.yaml` (no events).
- **Impact:** Requires manual filtering to exclude incomplete runs from analysis.
- **Recommendation:** Add `--validate` flag to `ev.py eval` that checks for complete events.jsonl before declaring success.

### 3. Sequential execution enforced
- Only one machine to share — evaluations must run sequentially.
- Each 30-turn eval takes ~20-30 minutes.
- **Total wall time:** ~2.5 hours for 5 packs.
- **Recommendation:** Document expected wall time in `docs/ev/COMMANDS.md` so users can plan accordingly.

---

## Output Usefulness

### What works well:
1. **`ev.py check --all --verbose`** — Clean, scannable output. Category breakdown (Beats/Goals/Pacing/State/Threads) is intuitive.
2. **Per-failure detail** — Each failure shows turn number, checker name, and specific reason (e.g., "removed non-existent item(s): ['lead_rounds']").
3. **Retry tracking** — `ev.py warnings` table clearly shows which turns had retries and why.

### What needs improvement:

#### 1. Warning gaps are invisible
Three warning types are produced but not stored in events:
- `generate_seed soft-check` (seed.py:421-424)
- `Thread update dedup` (turn.py:161-168)
- `Compendium NPC dedup` (extraction.py:720-743)

**Impact:** These warnings are logged to console but lost after the run. They cannot be analyzed in eval reports.

**Recommendation:** Store warnings as events with `kind="warning"` so they appear in `events.jsonl` and are accessible to `ev.py warnings` and checkers.

#### 2. LLM checkers separated from deterministic checkers
- June 18: 26 checkers total (23 deterministic + 3 LLM).
- June 20: 23 deterministic + 3 LLM reported separately.
- **Issue:** The total score denominator changes depending on whether LLM checkers are included, making cross-run comparison confusing.

**Recommendation:** Always report both totals: "23/23 deterministic (100%) + 3/3 LLM (100%) = 26/26 (100%)" for clarity.

#### 3. No baseline comparison in automated output
- Each eval run produces raw scores but no comparison to previous runs.
- Users must manually compare `REPORT.md` files across commits.

**Recommendation:** Add `ev.py eval compare --baseline <commit>` that diffs checker results between two runs and highlights regressions/improvements.

#### 4. Retry errors not surfaced in checker output
- `ev.py check --verbose` shows pass/fail per checker but doesn't mention retries.
- Retry data is only visible via `ev.py warnings`.
- **Impact:** A run with 5 retries (golden-piracy) looks "clean" in checker output despite having stability issues.

**Recommendation:** Add retry count to checker summary output, e.g., "23/23 PASS (5 retries across 30 turns)".

---

## Report Generation

### Current state:
- Reports are manually written markdown files in `evals/runs/<commit>/`.
- Template exists at `evals/ev-tooling/templates/report.md.j2` but is not used automatically.
- Each eval session requires manual report writing.

### Recommendations:
1. **Automate report generation** — Run `ev.py eval run <scenario> --report auto` at end of each eval session.
2. **Use the existing Jinja2 template** — `report.md.j2` is already defined but not integrated.
3. **Add cross-commit comparison** — `evals/runs/<commit>/COMPARISON.md` comparing to previous commit's results.

---

## Eval Process Improvements Summary

| Issue | Priority | Effort | Impact | Status |
|-------|----------|--------|--------|--------|
| Store warnings in events | High | Low | Makes hidden warnings analyzable | DONE (thread dedup, compendium dedup, seed soft-check) |
| inventory_integrity false positives | High | Low | 3 packs failing due to ID resolution bug | DONE (checker now uses resolve_inventory_remove_target) |
| Retry count in checker output | Medium | Low | Surfaces stability issues | TODO |
| Baseline comparison command | Medium | Medium | Automated regression detection | TODO |
| Incomplete run detection | Low | Low | Prevents stale run directories | TODO |
| Report automation | Medium | Medium | Reduces manual effort | TODO |
| LLM/deterministic score clarity | Low | Low | Improves report readability | DONE (reports now show total scores) |
