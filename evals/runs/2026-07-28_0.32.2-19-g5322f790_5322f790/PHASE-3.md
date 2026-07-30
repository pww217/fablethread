---
title: Phase 3 Report — 5 games × 25 turns
group: 2026-07-28_0.32.2-19-g5322f790_5322f790
date: 2026-07-28
sha: 5322f790
---

# Phase 3 Report: 5 games × 25 turns

## Runs Executed

1. **space-western:speedrunner** — 25 turns
2. **golden-piracy:completionist** — 25 turns
3. **noir-1930s:driven** — 25 turns (run in prior group: 2026-07-27_0.32.2-19-g5322f790_5322f790/2341_noir-1930s_25t)
4. **zombie-survival:cautious** — 25 turns
5. **allied-ww2:aggressive** — 25 turns

## Gate Check: PASS

No critical bugs found. No intermediate bugs requiring refactor. Pre-existing failures unchanged. All 5 runs proceed to full rubric analysis.

## Checker Results

### Overall Pass Rates

| Pack | Pass/Fail | Average Score |
|------|-----------|--------------|
| space-western:speedrunner | 38/42 (90.5%) | 0.90 |
| golden-piracy:completionist | 37/42 (88.1%) | 0.88 |
| noir-1930s:driven | 37/42 (88.1%) | 0.88 |
| zombie-survival:cautious | 38/42 (90.5%) | 0.90 |
| allied-ww2:aggressive | 37/42 (88.1%) | 0.88 |

### Consistent Failures (all 5 runs)

- **ruling_reason_quality** — Ruling reasons have 3-4 words, checker requires minimum 5. Prompt conflict: ruling system says "HARD CAP: 7 words max" but checker enforces minimum 5.
- **convergence_recompute** — Independently recomputed convergence differs from stored value by ~1.0 on many turns.
- **convergence_ema** — Components sum doesn't match stored convergence_score.
- **location_description_consistency** — Some extracted location descriptions are empty or too short.

### Occasional Failures (3/5 runs)

- **thread_urgency_decay** — Fails on noir, golden-piracy, allied. Thread `family_legacy` stays "normal" urgency for 14+ turns without demotion to "background".

## Subjective Examination

### Ruling Engine
- Intent classification is accurate (ruling_intent_match: PASS)
- Dice band distribution is well-distributed (ruling_band_distribution: PASS)
- Structured reason format is enforced (difficulty; condition/inventory)
- Reason length is the only quality issue — LLM produces brief reasons (3-4 words)

### Phase Engine
- Space-western is in BREATHER phase (breather_turn_count=2), all others in RISING
- No runs have entered CLIMAX (climax_turn_count=0 for all)
- Convergence scores range from 0.80 (space-western) to 2.98 (zombie)
- Convergence_threshold_context: PASS — gate thresholds use correct config values

### Convergence Score
- Both convergence_recompute and convergence_ema fail consistently
- Stored values don't match independently recomputed values
- This is a pre-existing bug in convergence calculation

### Thread Lifecycle
- Thread resolution rates: 66-100% across runs
- No hallucinated threads
- Thread cap/culling/cooldown all pass
- Avg turns to resolve: 5.4-8.2

### NPC Compendium (F-30)
- All new NPC Add operations include disposition field
- Add/Update routing is correct
- No write-once mutations detected
- Disposition values are descriptive prose

### Name Pool (I-42)
- Name pool IS rendered in prompts with Faker names (Giacinto Gotti, Logan Hicks, etc.)
- Pool changes each turn with different Faker names
- LLM IGNORES the directive — generates generic Anglo names (Adam Brooks, Dustin Hill, Ryan Benson)
- I-42 is NOT fixed

### Warning Signals
- 0 extraction retries across all runs
- Allied run: 8 rejected inventory_remove operations (LLM tries to remove non-existent items)
- 0 reconcile_warnings across all runs

### Prompt Size
- Ruling prompts: ~320-380 chars
- Narrate prompts: ~16-17k chars (stable growth)

## Fixes Applied During Eval

1. **LLM model name fix** — `config.yaml`: changed `gemma-4-26b-a4b-it` to `mlx-community--gemma-4-26B-A4B-it-OptiQ-4bit` (fallback server model name mismatch)

## Next Steps

1. Complete rubric Sections 10.5, 14 (remaining)
2. Deep-dive I-36 (choice grounding)
3. Deep-dive ruling structured reason enforcement
4. Write REPORT.md
5. Update I-42 ticket (confirmed NOT fixed)
6. Update F-30 ticket (confirmed fixed)
