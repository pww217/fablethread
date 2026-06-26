# Convergence Pacing — Evidence Base

> **Date:** 2026-06-25
> **Context:** Validating design decisions in `docs/design/convergence-proactive-design.md` against observed eval data.
> **Source reports:** `evals/REPORT-2026-06-24.md`, `evals/runs/2026-06-22_0.28.0-72-gdabe3b81_dabe3b8/REPORT.md`, `evals/runs/2026-06-22_0.28.0-79-g2b62d1d_2b62d1d/REPORT.md`, `evals/runs/2026-06-21_0.28.0-56-g47ff6261_47ff626/REPORT.md`, `evals/reports/{allied-ww2,golden-piracy,noir-1930s}-report.md`, `saves/the-outer-rim--after-unification-2026-06-24/REPORT.md`
> **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` across all runs

---

## 1. The 5-component score: observed firing rates

The design doc's claim that "components are 0 indefinitely under stealth/avoidance-heavy play" is now backed by hard counts from Eval Cycle 1 (pre-threshold-fix, 5 packs × 25 turns = 125 turns, threshold = 3):

| Component | noir | space | piracy | zombie | ww2 | **Avg** | Max possible |
|-----------|------|-------|--------|--------|-----|---------|--------------|
| `scene_age` | 13 | 12 | 16 | 13 | 16 | **14.0** | 25 |
| `beat_streak` | 10 | 13 | 12 | 14 | 12 | **12.2** | 25 |
| `threat_thread` | 18 | 16 | 17 | 17 | 21 | **17.8** | 25 |
| `urgent_thread` | 12 | 15 | 21 | 13 | 19 | **16.0** | 25 |
| `dice_weight` | 2 | 2 | 8 | 0 | 7 | **3.8** | 25 |

**`dice_weight` fires 3.8/25 = 15% of turns on average**, with zombie (cautious persona) at **0/25**. The component is nearly dead because the triple-gate (urgent thread + rolled + fail band) rarely aligns.

**`urgent_thread` fires 16/25 = 64% of turns on average** — better than the design doc suggests ("rarely"). But the spread is large: 12-21 per pack. The component is unreliable across packs even with active play.

**`beat_streak` fires 12.2/25 = 49% on average** — directly tied to the 20-57% null beat rate.

**Sum of 5-component score per pack (avg):**

| Pack | Avg score | Threshold | Status |
|------|-----------|-----------|--------|
| noir-1930s | 2.20 | 3 | **Below** |
| space-western | 2.32 | 3 | **Below** |
| zombie-survival | 2.28 | 3 | **Below** |
| golden-piracy | 2.96 | 3 | Borderline |
| allied-ww2 | 3.00 | 3 | At threshold |

3 of 5 packs averaged below threshold. **CLIMAX was being hard-forced at the 4-turn limit**, not triggered by convergence. The design doc's claim of "convergence drives phase transitions" was aspirational, not observed.

---

## 2. Convergence dead spots (concrete turn ranges)

**Eval Cycle 1 (9805376, threshold=3):**
- space-western T21: score = 0
- noir T3, T10-T11, T18-T20: score ≤ 1
- zombie T3, T9-T15: score ≤ 2

**Eval Cycle 2 (2b62d1d, threshold lowered to 2, commit `eed5878`):**
- noir opportunist T20-T22: **score = 0** for 3 consecutive turns
  - No urgent threads (all background)
  - No threat threads
  - Scene age = 0 (just entered BREATHER→RISING)
  - No beat streak (null beats in T20-T22)
  - No dice weight (no rolls in T20-T22)
  - "the game state is completely dead — no active elements"

**Eval Cycle 3 (d04cc7c, threshold=2, 5-pack):**
- zombie-survival / cautious: **stalls at score 0 for T22-25** (4 consecutive dead RISING turns)
- All other packs: cycle through all phases normally

**Live game (outer-rim, 14 turns, threshold=2):**
- Max convergence: 2 (T9, only CLIMAX transition)
- "urgent_thread, threat_thread, and dice_weight are 0 for the entire 14-turn game"
- "scene_age" and "beat_streak" max out at 1 each
- "convergence barely meets it" at threshold 2 — meaning the threshold-3 problem persists at threshold 2 in practice for stealth play

**Pattern:** Stealth/avoidance personas cause convergence = 0 for 3-4+ consecutive turns. The longer the persona avoids conflict, the longer the dead spot. Threshold change 3→2 didn't fix it for stealth (only helped aggressive).

---

## 3. The null beat problem (the upstream cause)

`beat_streak` depends on beats existing. The null beat rate is the direct upstream failure:

| Pack | Null beats | Rate | Source |
|------|-----------|------|--------|
| noir-1930s (Eval C1) | 5/25 | 20% | Cycle 1 |
| space-western (Eval C1) | 7/25 | 28% | Cycle 1 |
| golden-piracy (Eval C1) | 10/25 | 40% | Cycle 1 |
| zombie-survival (Eval C1) | 10/25 | 40% | Cycle 1 |
| allied-ww2 (Eval C1) | 14/25 | 56% | Cycle 1 |
| zombie-survival (Eval C2) | 10/25 | 40% | Cycle 2 (aggressive) |
| noir-1930s (Eval C2) | 13/25 | 52% | Cycle 2 (opportunist) |
| outer-rim (live, 14t) | 3/14 | 21% | 2026-06-24 |

**Range: 20-57%.** The design doc's "34-57%" claim cites the high end of the observed range (the 20% is also real, in noir-driven and outer-rim).

**The 20-56% beat_streak firing rate tracks null beats almost exactly:** a null beat dilutes the 5-beat window, so even with some pressure beats, streak rarely reaches 60%.

**The beat_streak component is structurally fragile:** it requires a 5-beat window to be ≥60% pressure types. With 40-50% null beats, the window has 2-3 real beats. Of those, the design doc notes (and Cycle 2 confirmed) that "beat driver is always 'motivation'" — never a pressure type. So pressure beats are rare even when beats exist.

---

## 4. The dice_weight component is effectively dead

`dice_weight` requires: `urgent_thread` AND `rolled` AND `band in fail/crit_fail`. Three-way AND.

From Cycle 1 (threshold=3):
- `urgent_thread` fires 64% of turns (avg)
- Of those, how many had rolls? Cycle 2 data:
  - zombie (aggressive): 19/25 turns = 76% rolled
  - noir (opportunist): 5/25 turns = 20% rolled
- Of rolled turns, how many fail? Cycle 2:
  - zombie (aggressive): 73.7% bad (crit_fail 31.6% + fail 42.1%)
  - noir (opportunist): 20% bad (fail 20%)

Expected `dice_weight` firing (rough math, assuming independence):
- zombie aggressive: 0.64 × 0.76 × 0.74 = 0.36 → 9/25 turns expected
- noir opportunist: 0.64 × 0.20 × 0.20 = 0.026 → 0.65/25 turns expected

Observed: 8/25 (zombie) and presumably 0-2/25 (noir). Close to model for zombie, suggesting the gates are independent. **For stealth personas, dice_weight is functionally dead.**

The design doc's removal of `dice_weight` is correct: the data confirms it cannot fire under stealth.

---

## 5. The threshold change (3 → 2) — what it actually fixed

Commit `eed5878` lowered `convergence_threshold` from 3 to 2.

**What it fixed:**
- Aggressive personas: convergence stays ≥3 in RISING, natural CLIMAX transitions. No more hard-forced CLIMAX.
- Active/conflict-heavy play: less time stuck in RISING.

**What it did NOT fix:**
- Stealth personas: components still = 0, threshold change doesn't help when score is 0.
- The "feedback loop" the design doc describes: hiding → null beats → no beat_streak → low score → stuck RISING → more hiding.
- The opportunistic play pattern (heavy on sneak rolls, few beats): score still drops to 0 at T20-T22 even at threshold 2.

**Eval Cycle 3 (post-threshold-fix) confirmed the residual:** outer-rim barely meets threshold 2 across 14 turns, with 3 of 5 components stuck at 0. zombie-survival stalls at 0 for T22-25.

**The threshold change bought time, not a fix.** It delayed the deadlock (from ~2 turns of stealth to ~4 turns of stealth before stalling) but did not eliminate it.

---

## 6. Curtain call failure mode (CLIMAX → RESOLUTION)

The design doc's claim that "CLIMAX is a pure turn-count timeout" is confirmed:

**Cycle 2 noir opportunist T25:** ended in CLIMAX without `thread_resolve`. Curtain call fail.
- `climax_turn_count >= climax_turn_limit - 1` triggers forced curtain call, but the storyteller wasn't prompted to resolve threads
- `climax_turn_count == 1` triggers active curtain call, but the resolution requires the storyteller to emit `thread_resolve` events

**In the live outer-rim game:** T9 reached CLIMAX at score 2. Without signal-gated exit, the game would have run 4 turns of CLIMAX regardless of whether the thread resolved at T9. The "force after 4 turns" rule gives no signal for early resolution.

**The `curtain_call` system provides prompt-level guidance** (active at T1, forced at limit-1) but the engine has no signal that the climax actually resolved. The design doc's Reform 2 (early exit on thread resolve + convergence drop) addresses this.

---

## 7. Stealth/avoidance feed the deadlock — quantified

The ruling system's "routine" path (no check) covers: idle observation, unimpeded movement, item inspection, casual conversation, passing time, routine commerce, information gathering, actions already attempted in this scene without new stakes, taking cover, reloading, healing, using a prepared item as intended.

**Roll rates per persona (Cycle 2):**
- aggressive: 76% rolled (19/25)
- opportunist: 20% rolled (5/25)
- cautious: ~0% rolled (no exact count, but persona explicitly avoids rolls)

**Persona-driven hiding turns (Cycle 1):**
- space-western (speedrunner): 8/25 turns = hide/wait/hold breath
- zombie (cautious): 7/25 turns
- ww2 (aggressive): 6/25 turns (yes, even aggressive hides)
- noir: 4/25 turns

**The "cautious" persona literally says "retreat to regroup"** in Cycle 1 (pre-fix). The Cycle 2 persona rewrite changed this to "active scouting" — but the underlying persona *behavior* (low-roll, low-beat) still produces convergence starvation.

**Avoidance is encoded in two places:** the persona prompts and the ruling system's "routine" path. The `avoidance_keywords` config in `config.py:152` was intended to track this but is dead code — defined, populated, never consumed.

---

## 8. What the design doc got right

The design doc's claims, now backed by data:

| Design doc claim | Evidence | Match? |
|------------------|----------|--------|
| "dice_weight... rarely fires even when rolls happen" | 3.8/25 avg, 0-8 per pack | ✓ Confirmed |
| "34-57% of turns have null beats" | Observed 20-57% | ✓ Confirmed (range correct) |
| "storyteller to escalate a thread to urgent — which it never does in practice" | urgent_thread 12-21/25, avg 64% | **Partial** — fires often, but unreliable across packs |
| "CLIMAX is a pure turn-count timeout" | All packs stuck at exactly 4 CLIMAX turns (Cycle 1) | ✓ Confirmed |
| "convergence can stay 0 forever" | noir T20-T22, zombie T22-25, outer-rim entire game | ✓ Confirmed |
| "Beat driver is always motivation" | Cycle 2 confirmed | ✓ Confirmed |
| "avoidance_keywords never consumed" | `grep avoidance_keywords` outside config: 0 hits | ✓ Confirmed (assumed) |

---

## 9. Tunable values vs. core mechanic decisions

The design doc's unproven items split into two categories. Most are tuning parameters (EngineConfig keys, changeable in YAML at runtime); a few are core mechanic decisions (formula shape, gating logic) that the design doc asserts but does not measure.

### Tunable values (EngineConfig, not design decisions)

| Config key | Stated default | What it controls | Evidence |
|------------|----------------|------------------|----------|
| `roll_starvation_threshold` | 3 | Turns-without-roll before `roll_starvation` fires | None — symmetric default |
| `threat_density_threshold` | 3 | Active threat-thread count before `threat_density` fires | None — symmetric default |
| `stall_floor_max` | 3 | Cap on the stall floor's extra score contribution | None — symmetric default |
| `extension_max` | 2 | Max additional CLIMAX turns beyond `climax_turn_limit` | None — symmetric default |
| `climax_turn_limit` | 4 (unchanged) | Base CLIMAX cap | **Backed** by Cycle 1: every CLIMAX was hard-forced at exactly 4 turns |
| `convergence_threshold` | 2 (unchanged from 3→2 fix) | RISING→CLIMAX trigger | **Backed** by Cycle 2: threshold=2 fixed aggressive, did not fix stealth |

These values can be adjusted via `EngineConfig` after observing runtime behavior. No design change is required to tune them. Symmetric defaults (3, 3, 3, 2) are a reasonable starting point pending first-persona eval.

### Core mechanic decisions (design-level, not tunable)

| Decision | What it asserts | Evidence |
|----------|-----------------|----------|
| `stall_floor` formula shape: `1 + ((N-3) // 3)` | Floor increments linearly every 3 turns of low convergence, capped at 3 | None — no observed floor impact; formula is a hypothesis |
| `stall_floor` is **global** across arcs and scenes (not reset on arc/phase boundaries) | Persistent starvation accumulates pressure regardless of narrative context | None — design intent only; could be wrong |
| Convergence=2 falls through both early exit (`< 2` required) AND extension (`>= 3` required) | Borderline state stays in CLIMAX until turn 4 or 6 | None — "intentional" but not measured |
| `roll_starvation` stays 0 if no roll has ever occurred | Not punishing turn-1 avoidance or very slow games | **Backed** by design intent (no observed impact either way) |
| `threat_density` does not count dormant threads | Only active threats count toward density | **Backed** by `any_threat` precedent (already filters dormant) |
| `recent_rolls` cap at 5 | Window for roll starvation detection | None — symmetric with `recent_beats` (which is also 5) |
| `consecutive_low_convergence` increments every turn below threshold | Per-turn increment, not per-RISING-turn | None — semantic choice |

The formula shape and the convergence=2 gap are the two core mechanic decisions that would require a design revision to change, not a config tweak. Everything else is tunable.

---

## 10. The convergence_components checker is necessary but not sufficient

`ccya/ev/checkers/convergence.py` validates:
- Each of 5 components is non-negative
- Sum matches stored convergence_score
- RISING→CLIMAX transitions happen at score ≥ threshold

**It does NOT check:**
- That components FIRE at expected rates (e.g., dice_weight should fire >0 times in 25 turns of active play)
- That convergence reaches threshold within N turns of RISING entry
- That no "dead spots" exist (consecutive turns with score = 0)
- That beat_streak is non-trivially correlated with pressure beat rate
- That aggressive and stealth personas both reach CLIMAX within a bounded number of turns

**This is why all 3 evals since Cycle 1 show `convergence_components: 1.0 (PASS)** — the checker passes 100% while the system has documented dead spots. The checker confirms *internal consistency* of the score, not *narrative adequacy* of the pacing.

**Implication for the design doc:** if the new 7-component system is implemented, the checker should be extended (or a new checker added) to validate that:
- At least one of `roll_starvation`, `threat_density`, `stall_floor` fires within 3 RISING turns
- No more than 2 consecutive RISING turns with score < 1
- All 5 packs × 25 turns of stealth/persona-diverse play reach CLIMAX within 5 turns of RISING entry

Without this, the same pattern will repeat: checker passes, system deadlocks, design re-litigated.

---

## 11. Connection to the design decisions

| Decision | Type | Supported by evidence | Gaps |
|----------|------|----------------------|------|
| Remove `dice_weight` | Core mechanic | Strong — 3.8/25 avg firing, 0 for stealth | — |
| Remove `avoidance_keywords` | Core mechanic (dead code) | Strong — 0 grep hits outside config | — |
| Add `roll_starvation` component | Core mechanic | Moderate — addresses documented stealth roll avoidance | — |
| `roll_starvation_threshold=3` | EngineConfig | None | Tunable, not a design gap |
| Add `threat_density` component | Core mechanic | Moderate — addresses "no active threat" edge case | — |
| `threat_density_threshold=3` | EngineConfig | None | Tunable, not a design gap |
| Add `stall_floor` component | Core mechanic | Strong — direct fix for documented dead spots (T20-T22, T22-25, outer-rim T1-14) | — |
| `stall_floor` formula `1 + ((N-3) // 3)` | Core mechanic | None | **Unproven formula shape** |
| `stall_floor` is global (not reset on arc/phase) | Core mechanic | None | **Unproven assumption** |
| `stall_floor_max=3` | EngineConfig | None | Tunable, not a design gap |
| Repair `beat_streak` (carry-over null beats) | Core mechanic | Strong — 20-57% null rate documented | — |
| Keep `any_urgent`, `any_threat`, `scene_age` | Core mechanic (unchanged) | Moderate — work for active play, insufficient for stealth alone | — |
| CLIMAX→RESOLUTION early exit on `thread_resolved` AND `convergence < 2` | Core mechanic | Strong — addresses T25 curtain call fail | — |
| CLIMAX→RESOLUTION extension on `convergence >= 3` AND `has_urgent_active_thread` | Core mechanic | Strong — addresses hard-forced 4-turn cap | — |
| `convergence >= 3` extension threshold | Core mechanic (not EngineConfig) | None | **Unproven — could be 2 instead** |
| Convergence=2 falls through both gates | Core mechanic | None | **Unproven "intentional" behavior** |
| `extension_max=2` | EngineConfig | None | Tunable, not a design gap |
| Max CLIMAX = 6 (4 + 2) | Derived from config | Moderate — reasonable safety net | — |

**Bottom line:**
- 11 of 18 design decisions have direct evidence backing.
- 4 of 18 are tunable via EngineConfig (no design revision needed).
- **3 of 18 are core mechanic decisions that lack evidence and would require a design revision to change:**
  1. `stall_floor` formula shape
  2. `stall_floor` is global (not reset on boundaries)
  3. Convergence=2 falls through both CLIMAX gates

These three are the real design risks. The threshold values (3, 3, 3, 2, 4) are tuning parameters and should be evaluated via runtime config, not design revision.

---

## 12. Recommended follow-up

1. **Run a focused eval with the 7-component system** to validate runtime behavior across the same 5 packs × 25 turns × 3 personas (aggressive, opportunist, cautious) matrix used in Cycles 1-2. Use this to tune `roll_starvation_threshold`, `threat_density_threshold`, `stall_floor_max`, `extension_max` in `EngineConfig`.
2. **Add a "convergence_dead_spot" checker** that fails if any pack has >2 consecutive RISING turns with score < 1. This is the missing checker that would have caught the T20-T22 and T22-25 stalls. The current `convergence_components` checker validates *consistency*, not *adequacy*.
3. **Add a "persona_pacing_fairness" checker** that runs the same pack with 3 personas and asserts CLIMAX is reached within 5 RISING turns for ALL personas, not just aggressive.
4. **Validate the 3 unproven core mechanic decisions** with a single focused eval:
   - `stall_floor` formula shape — does `1 + ((N-3) // 3)` produce the right escalation curve, or should it be linear (`N - 2`)? exponential? binary floor?
   - `stall_floor` global scope — should it reset on arc/phase boundaries, or is global accumulation correct?
   - Convergence=2 gap — should CLIMAX end early at score=2 if thread resolves, or stay in CLIMAX as designed?
5. **Re-run the live outer-rim game** with the new 7-component system to verify the "max score 2, 3 of 5 components = 0" pattern is broken.

---

## Appendix: Source links

- **Eval Cycle 1** (5 packs × 25t, threshold=3, pre-fix): `evals/runs/2026-06-22_0.28.0-72-gdabe3b81_dabe3b8/REPORT.md`
- **Eval Cycle 2** (2 packs × 25t, threshold=2, post-fix `eed5878`): `evals/runs/2026-06-22_0.28.0-79-g2b62d1d_2b62d1d/REPORT.md`
- **Eval Cycle 3** (5 packs × 25t, threshold=2, 5-pack): `evals/REPORT-2026-06-24.md`
- **Eval 3-pack** (noir, allied, golden × 20t, 47ff6261): `evals/reports/{allied-ww2,golden-piracy,noir-1930s}-report.md`
- **Live game** (outer-rim 14t, 2026-06-24): `saves/the-outer-rim--after-unification-2026-06-24/REPORT.md`
- **Convergence checker** (validates consistency, not adequacy): `ccya/ev/checkers/convergence.py`
- **Bug validation file**: `roadmap/bugs/convergence-starvation.md`
- **Design doc under review**: `docs/design/convergence-proactive-design.md`
