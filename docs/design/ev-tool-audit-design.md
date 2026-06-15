# EV Audit Findings & Convergence Design Mapping

**Date:** 2026-06-15
**Scope:** Cross-reference all EV session findings (combat-duration eval + 3-pair persona/scenario eval) against the convergence scoring design to identify what it fixes, what it misses, and what three supporting changes are needed.

---

## Source Evaluations

### Combat Duration Eval (2026-06-14)
- **Run:** `ev.py play --llm --personality aggressive_plan --turns 20`
- **Events:** `saves/ev/20260614_210345_c56485/events.jsonl`
- **Turns:** 17 total, combat from ~turn 8 through turn 17 (10 turns)
- **Fix tested:** `outcome_hint` override changed from `crisis_turn_count >= crisis_turn_limit` to `effective_scene_age >= scene_imperative_threshold`
- **Result:** Fix #1 working but insufficient alone — combat doom spiral persists because bugs #2 and #3 remain

### Three-Pair Persona/Scenario Eval (2026-06-15)
- **Runs:** 3 × 20 turns (zombie-survival/explorer, space-western/driven, sengoku-japan/aggressive)
- **Flags:** `--no-sanitize`
- **Results:** Run 1 (explorer): 6 failures | Run 2 (driven): 1 failure | Run 3 (aggressive): 2 failures

---

## Condition Distribution (81 turns across all runs)

| Metric | Value |
|---|---|
| Total rolls | 56 (69% of turns) |
| Hard difficulty calls | 31 (55% of rolls) |
| Condition-related reasons | 36 (64% of roll reasons explicitly cite a condition) |
| Positive condition types | 1 (chemically_stimulated) |
| Negative condition types | 18 |
| Positive:Negative ratio | 1:18 |
| Turns with 0 active conditions | 37 (46%) |
| Turns with 1 active condition | 23 (28%) |
| Turns with 2+ active conditions | 21 (26%, max 3) |
| Average active per turn | ~0.93 |
| Net condition accumulation | +4, +10, +6 (all positive) |

**Key insight:** Conditions are overwhelmingly negative (18:1) and accumulate over time. The LLM correctly factors conditions into difficulty — 28 of 31 hard calls mention a condition in the reason field. This creates a feedback loop: roll → fail → gain negative condition → hard difficulty on next roll → more failures. The typical effective mod from conditions alone is -0.5 to -1.0.

---

## Convergence Design: What It Directly Addresses

### 1. Premature CLIMAX entry (binary urgency threshold)
**Finding:** Phase machine enters CRISIS with just 2 urgent threads, ignoring all other context. This was the primary driver of combat spirals — the phase machine oscillates between CLIMAX and RESOLUTION/BREATHER without ever escaping combat.

**Design solution:** Convergence score replaces binary `crisis_urgency_threshold`. Score computed fresh each turn from 5 components (thread weight, urgency depth, scene age, beat streak, dice weight), each worth +1, threshold 3. Never persisted.

**Assessment:** Meaningful improvement. The old system entered CLIMAX with any 2 urgent threads regardless of scene age, beat patterns, or dice results. The new score requires multiple independent systems to agree before CLIMAX fires. The dice weight component (fail/crit_fail + urgent thread) is now less likely to fire because the three supporting changes (fewer rolls, balanced bands, more positive conditions) reduce the effective fail rate.

### 2. Scene Imperative has no resolution beats
**Finding:** The allowed list for Scene Imperative is `["revelation", "twist", "hazard", "callback", "opportunity"]` — zero beats that end a scene.

**Design solution:** Scene Imperative allowed list replaces `twist` with `setback`. New list: `[revelation, hazard, callback, opportunity, setback]`. `twist` excluded because it was "the primary source of infinite escalation."

### 3. `outcome_hint` never becomes `"transition"` (dead code)
**Finding:** `_compute_pacing_context()` checks `crisis_turn_count >= crisis_turn_limit` but the counter has already been reset to 0 by `_compute_scene_phase()`. The condition never evaluates to True. `outcome_hint` was never `"transition"` across 17 turns.

**Design solution:** The convergence design's hard cutoff with `outcome_hint = "transition"` is a proper fix — computed before the counter is reset.

### 4. `derive_enforce_relief` dead code (0/49 turns)
**Finding:** Fired zero times across two evals. The logic is correct but the pressure threshold never triggers.

**Design solution:** Deleted with no replacement. Replaced by `recent_beats` streak in convergence score.

### 5. Thread stays URGENT forever, locks phase cycle
**Finding:** Thread `clear_the_road_toughs` was updated every turn for 10 turns, keeping it URGENT. The phase machine cycles CRISIS→RESOLUTION→BREATHER→RISING→CRISIS endlessly.

**Design solution:** Thread sanitizer unchanged. Hard cutoff at `climax_turn_limit` forces transition regardless, mitigating the worst of the cycling.

---

## Convergence Design: What It Doesn't Address

### 1. Overwhelm directive stripping
Out of scope — directive was already removed from engine. Checker needs update.

### 2. Thread resolution bugs (Run 1: unknown threads)
Out of scope — extraction/storyteller compliance issue.

### 3. tension_delta has zero useful variance

**Finding:** Across all 80 EV turns, the ruling LLM emitted:
- `escalates`: 55 (68.8%)
- `maintains`: 25 (31.2%)
- `de-escalates`: 0 (0%)

The prompt guidance prevents de-escalation in CRISIS (most phases), and BREATHER phases always have urgent threads active, triggering the escalation exception. The field is effectively binary and always signals "not resolved" — it carries no actionable information.

**Design solution:** `tension_delta` removed from phase logic entirely. The convergence score subsumes any useful tension signal.

**Assessment:** Correct call. A signal that never varies is worse than no signal — it creates false confidence.

### 4. Tension monotonicity failure (Run 3: BREATHER with escalates)
`tension_delta` removed from phase logic in convergence design. Ruling prompt still emits it but it no longer drives transitions.

### 4. Context bloat (Run 3: 70-109s per turn)
Out of scope — needs separate design.

### 5. Doom spiral detection (EV tool gap)
Out of scope — EV tooling, not pipeline.

### 6. Extraction format inconsistency
Out of scope — EV tooling.

### 7. Beat repetition risk (revelation x4, x6)
Scene Imperative list change helps (removes `twist`), but `revelation` remains. Beat diversity in storytell prompt (already exists at line 91) covers this.

---

## Three Supporting Changes

All three were informed by the condition and roll distribution data above. They work alongside the convergence design to reduce spiral pressure.

### Change 1: Dice Roll Frequency (ruling_system.j2 + ruling_user.j2)

**Before:** `check.required=true` when (a) clear intent, (b) meaningful consequence, (c) genuine uncertainty. 69% roll rate.

**After:** `check.required=true` when ALL THREE:
- (a) Action occurs at a major narrative pivot — scene transition, decisive confrontation, or gamble that alters the story's trajectory. Actions in scenes with urgent threads are more likely to qualify.
- (b) Failure has a real, irreversible consequence
- (c) Outcome is genuinely uncertain

No-roll list expanded: idle observation, unimpeded movement, item inspection, casual conversation, passing time, routine commerce, information gathering, actions already attempted in this scene without new stakes, taking cover, reloading, healing, using a prepared item as intended.

**Thread context added to ruling_user.j2** (~50-100 tokens):
```
## Urgent Threads
- {{ thread.id }} — {{ thread.summary }}
    T12: advancement — "Bald Tough confronts courier in the street"
    T13: setback — "negotiation fails, Bald Tough rejects bribe"
```

Only urgent threads (typically 1-2). Last 3 progress entries in chronological order with turn number. No arc goal — longer-term context not helpful for per-turn roll decisions.

**Expected impact:** ~69% → ~35-45% roll rate. Fewer bands feeding convergence score's dice weight component.

### Change 2: Band Rebalancing (rules.py)

**One-line change:**
```python
# Old: partial on ≤8, success on ≥9
# New: partial on ≤7, success on ≥8
```

| Band | Old (0 mod) | New (0 mod) | New (-1 mod) |
|---|---|---|---|
| crit_fail | 8.3% | 8.3% | 16.7% |
| fail | 33.3% | 33.3% | 33.3% |
| setback | 8.3% | 8.3% | 8.3% |
| partial | 16.7% | 8.3% | 0% |
| success | 25% | 33.3% | 25% |
| crit_success | 8.3% | 8.3% | 16.7% |

At neutral mod, bad/good stays 50/50. At typical condition load (-1), success rate stays at 25% with overall good at 41.7% — much closer to 50/50 than before. Partial outcomes halve, making outcomes more decisive.

### Change 3: Positive Condition Extraction (extract_state_system.j2)

**Before:** Only negative heuristics. Last line actively discourages positives:
```
- Clean success or crit_success → no negative conditions
```

**After:** Add success-guarded positive heuristics:
```
- After a decisive success or critical success → consider a short-lived positive condition (focused, determined, elated, second_wind, protected). Max 1 per turn.
- When an ally or circumstance actively aids the player → consider a brief positive condition (guided, fortified, inspired). Max 1 per turn.
```

5-cap unchanged — limits negative stacking, creates space for positives. Expected: ~5% → ~25% positive ratio.

---

## Scope Summary

### In scope for convergence design
- Convergence score replacing binary urgency threshold ✓
- Scene Imperative allowed list changes ✓
- Curtain Call soft-close mechanism ✓
- Hard cutoff with `outcome_hint = "transition"` ✓
- Removing `tension_delta` from phase logic ✓
- Deleting dead code ✓

### Supporting changes (new, alongside convergence)
1. Roll frequency reduction — ruling_system.j2 + ruling_user.j2 (thread context)
2. Band rebalancing — rules.py (partial ≤8 → ≤7)
3. Positive condition extraction — extract_state_system.j2

### Out of scope
- Overwhelm checker (needs update, engine already changed)
- Thread resolution bugs (separate fix)
- Context bloat (separate design)
- EV tool gaps (separate from pipeline)
