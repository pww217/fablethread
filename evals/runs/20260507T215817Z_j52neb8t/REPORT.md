# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-07T21:58:17.090668+00:00 · **Finished:** 2026-05-07T21:58:47.883351+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260507T215817Z_j52neb8t`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260507T215150Z_kqhjvsi_`

## Judge Summary

**Mechanical:** ?/5  
**Narrative:** ?/5  
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`

**Verdict:** Mechanical score is dragged down by a critical scope/domain mismatch: the rules pipeline skips quest_updates, but the progress extractor produces and the engine applies them anyway. This breaks the contract between intent classification and state mutation. Additionally, the recent_events_add turn stamp is hardcoded to 0 instead of the current turn, which will cause temporal tracking failures. The narration and scene extraction are strong, delivering a compelling partial-band outcome with appropriate tension. Fixing the scope enforcement and turn stamping will resolve the mechanical failures.

**Narrative recap:** The player approaches Caron to negotiate the debt. Through a partial success, they reduce the interest but are coerced into spying on Halden's northern pass shipment. The debt quest advances with the first objective completed, and a new investigation quest is introduced. Caron's demeanor shifts from passive to calculating, establishing immediate tension and a morally gray path forward.

## ✅ No flags

No regressions, retries, failures, or judge score drops detected.


## Auto-Checker

**0 passed, 1 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ❌ | rolled=True |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | Walk over to Caron's table and sit down across f… | 1211 (+0) | 1996 (+15) | 2004 (-18) | — | 3219 (-26) | 0 | 0 | 30.79 |
|  | TOTALS | 1211 | 1996 | 2004 | 0 | 3219 | 0 | 0 | 30.79 |

**Total turns:** 1 · **Total duration:** 30.79s · **Avg/turn:** 30.79s
**Total tokens in:** 8,430 · **Total tokens out:** 7,489 · **Total LLM time:** 30.7s
**Total retries:** 0 · **Total parse failures:** 0

