# Phase 3 Report — 25 turns

- **Date:** 2026-07-18
- **Git SHA:** 2e3d018
- **Goal:** Validate engine stability, balance, and long-term mechanics across 5 packs at 25 turns each

## Results

| Pack | Persona | Turns | Deterministic Checkers | Status |
|------|---------|-------|----------------------|--------|
| noir-1930s | driven | 25 | 42/43 PASS (97.7%) | WARN |
| space-western | speedrunner | 25 | 43/43 PASS (100%) | PASS |
| space-western | explorer | 25 | 43/43 PASS (100%) | PASS |
| golden-piracy | completionist | 25 | 43/43 PASS (100%) | PASS |
| zombie-survival | cautious | 25 | 43/43 PASS (100%) | PASS |
| allied-ww2 | aggressive | 25 | 43/43 PASS (100%) | PASS |

## Findings

### noir-1930s:driven — 97.7% (1 warning)
- **Turn 17 ruling_reason_quality:** Narration reason was 11 words, exceeding 10-word max. Minor wording issue, no mechanical impact.
- Seed 1 generation crashed (LLM generated `pc.conditions` as string `"exhausted"` instead of empty array). Retry with seed 2 succeeded.

### space-western:speedrunner — 100%
- All 43 checkers passed. Clean run.

### space-western:explorer — 100%
- All 43 checkers passed. Clean run.

### golden-piracy:completionist — 100%
- All 43 checkers passed. Clean run.

### zombie-survival:cautious — 100%
- All 43 checkers passed. Clean run.

### allied-ww2:aggressive — 100%
- All 43 checkers passed. Clean run.

## Notes

- All inference routed through OMLX fallback (LMStudio primary down)
- noir-1930s seed generation crash may indicate edge case in LLM prompt formatting for character conditions
- No regressions from Phase 2
