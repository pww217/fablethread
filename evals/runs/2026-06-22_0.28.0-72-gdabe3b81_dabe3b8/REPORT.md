# Eval Cycle 1 — Report

**Date:** 2026-06-22
**Git SHA:** 9805376 (pre-fix)
**Runs:** 5 packs × 25 turns
**Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8`
**Personas:** noir-driven, space-speedrunner, piracy-completionist, zombie-cautious, ww2-aggressive

---

## Scores

| Pack | Checkers | Score | Failing |
|------|----------|-------|---------|
| noir-1930s | 23/25 (92.0%) | 0.92 | arc_resolution_validity, extraction_retry_rates |
| space-western | 24/25 (96.0%) | 0.96 | extraction_retry_rates |
| golden-piracy | 23/25 (92.0%) | 0.92 | thread_lifecycle, extraction_retry_rates |
| zombie-survival | 24/25 (96.0%) | 0.96 | extraction_retry_rates |
| allied-ww2 | 23/25 (92.0%) | 0.92 | ruling_reason_quality, extraction_retry_rates |

---

## Issues Not Surfaced by Checkers

### 1. GM Beat Null Rate (HIGH)

The storyteller generates null beats (no GM beat) on 20-56% of turns:

| Pack | Null Beats | Rate |
|------|-----------|------|
| noir-1930s | 5/25 | 20% |
| space-western | 7/25 | 28% |
| golden-piracy | 10/25 | 40% |
| zombie-survival | 10/25 | 40% |
| allied-ww2 | 14/25 | 56% |

Null beats are concentrated during BREATHER and RESOLUTION phases. This means the game state has no GM beat for those turns, breaking the beat-driven pacing system.

### 2. Scene NPC Candidates vs Beat Quality (HIGH)

**Cross-tabulation (beats vs candidates):**

| Pack | beat+cands | null+no-cands | beat+no-cands | null+has-cands |
|------|-----------|--------------|--------------|---------------|
| noir | 8 | 10 | 8 | 4 |
| space | 11 | 6 | 8 | 4 |
| piracy | 0 | 11 | 12 | 7 |
| zombie | 7 | 8 | 8 | 6 |
| ww2 | 13 | 3 | 1 | 11 |

**Key findings:**

- **Golden-piracy has ZERO turns with both a beat and candidates.** The scene pipeline generates candidates but the storyteller never uses them to inform beats.
- **Candidate types are extremely repetitive:** `motivation` (51), `fear` (41), `leverage` (9), `bond` (3), `personality` (1). Only 5 types across 105 candidate entries.
- **Candidates persist turn-to-turn with identical types.** E.g., noir T1-T5: `detective_clark` is always `fear` or `leverage` or `bond` or `motivation` — never evolving.
- **Null beats correlate with empty candidate lists** in noir, space, and piracy, but not in zombie or ww2 (which have many null-beat turns with candidates present).
- **Candidates do not inform beat quality.** Turns with rich candidate data (ww2 T1-T9) still produce null beats. The storyteller ignores scene candidate data.

### 3. Phase Machine — CLIMAX Hard-Forced, Convergence Starved (MEDIUM)

**The report's original claim of "1 RESOLUTION per pack" is incorrect.** The actual data shows the phase machine IS working — all 5 phases appear in all packs with correct transitions:

**Actual RESOLUTION counts** (not 1 per pack):

| Pack | RESOLUTION turns |
|------|-----------------|
| noir | 3 |
| space | 2 |
| piracy | 4 |
| zombie | 2 |
| ww2 | 3 |

**Phase transitions are correct** across all packs:
```
SETUP → RISING → CLIMAX → RESOLUTION → BREATHER → RISING → CLIMAX → ...
```

**But CLIMAX is stuck at exactly 4 turns** — the hard limit (`climax_turn_limit`). Every CLIMAX block is exactly 4 turns long. Convergence isn't reaching threshold 3 early enough to trigger CLIMAX naturally — the hard limit is doing all the work.

**Convergence score breakdown** (avg across packs):

| Component | Noir | Space | Piracy | Zombie | WW2 | Avg |
|-----------|------|-------|--------|--------|-----|-----|
| `scene_age` | 13 | 12 | 16 | 13 | 16 | 14.0 |
| `beat_streak` | 10 | 13 | 12 | 14 | 12 | 12.2 |
| `threat_thread` | 18 | 16 | 17 | 17 | 21 | 17.8 |
| `urgent_thread` | 12 | 15 | 21 | 13 | 19 | 16.0 |
| `dice_weight` | 2 | 2 | 8 | 0 | 7 | 3.8 |

**Avg convergence per pack** (threshold = 3): noir 2.20, space 2.32, piracy 2.96, zombie 2.28, ww2 3.00. Most packs average ~2.2-2.3 — below the 3.0 threshold needed for natural RISING→CLIMAX transitions.

**Component 5 (`dice_weight`) is nearly dead** — requires BOTH an urgent thread AND a failed roll simultaneously. Fires only 0-8 times across 125 turns. This component is too restrictive.

**Root cause — feedback loop with player monotony:** convergence depends heavily on `beat_streak` (60%+ of last 5 beats must be pressure types). Hiding/waiting players produce null beats or relief beats instead of pressure beats. This starves convergence below threshold 3, preventing natural CLIMAX transitions. The phase machine cycles through CLIMAX only because the hard limit forces it after 4 turns.

**Connection to #4:** Hiding player → no pressure beats → low convergence → stuck in RISING or stuck in CLIMAX until hard limit → RESOLUTION → BREATHER → back to RISING. It's a self-reinforcing loop.

**Fix direction:** Lower convergence_threshold from 3 to 2, make `dice_weight` less restrictive (remove the urgent_thread requirement), or increase beat_streak sensitivity.

### 4. Player Behavior Monotony (MEDIUM)

The "cautious" and "speedrunner" personas are nearly indistinguishable — both default to hiding/stealth/waiting:

- **Space-western:** 8/25 turns are "hide/wait/hold breath" variants
- **Zombie:** 7/25 turns are "hide/wait/hold breath" variants
- **Allied-ww2:** 6/25 turns are "hide/wait/hold breath" variants
- **Noir:** 4/25 turns are "hide/wait" variants

**Root causes:**

- **`cautious`** literally says "retreat to regroup" — instructs the LLM to retreat
- **`speedrunner`** has no positive action vocabulary — "skip optional content. Minimize dialogue." tells the player what NOT to do but gives no guidance on what TO do when the environment is dangerous
- **`aggressive`** fails in practice — ww2-aggressive still produced 6/25 hide/wait turns despite "bold, confrontational, risk-taking" text. The LLM over-weights environmental danger signals over persona instructions
- **`driven`** is too abstract — "Every action must advance toward the goal" is directionless — it doesn't specify HOW to advance
- **No persona has "engagement" vocabulary** — none mention combat, confrontation, negotiation as valid actions. `opportunist` is the only one that does ("Use whatever works — diplomacy, stealth, combat, items") but it is never used in the standard 5-pack
- **Dead `avoidance_keywords`** config in `ccya/engine/config.py:152` — `["retreat", "run", "flee", "hide", "rest", "escape", "back away", "disengage", "withdraw", "surrender", "concede", "leave", "get out"]` is defined but never read or used anywhere
- **No action scaffolding** in the user prompt — `narrate_user.j2` ends with `=== PLAYER INPUT ===\n{{ user_input }}\n=== END PLAYER INPUT ===`. No suggested action list, no action vocabulary guidance, no constraint against defensive behaviors
- **Zombie pack's "cautious" pairing** is the worst offender — the pack's world rules emphasize fungal infection, airborne spores, and lethal infection within hours. Combined with the cautious persona's "retreat to regroup" instruction, this creates a feedback loop where hiding is the only rational choice — resulting in only 5/25 turns with any state change at all

**Fix applied:** Rewrote all 5 persona prompts in `ccya/ev/personality.py` to command action, never inaction. Even cautious is now active — "active scouting," "secure your position before advancing," "never stand still." Removed "retreat to regroup," "assess risks," "skip optional content," "push through obstacles." Added concrete action verbs: "confront threats head-on," "question witnesses," "examine every object," "move directly toward the goal."

### 5. Thread Resolution Rate (MEDIUM)

Threads accumulate but rarely get resolved:

| Pack | Created | Resolved | Rate |
|------|---------|----------|------|
| noir | 17 | 1 | 5.9% |
| space-western | 15 | 4 | 26.7% |
| golden-piracy | 24 | 3 | 12.5% |
| zombie | 16 | 3 | 18.8% |
| ww2 | 18 | 3 | 16.7% |

### 6. Beat Effect Duplication (LOW)

The storyteller regenerates identical beat text across turns:

- **Golden-piracy T15 & T16:** Both say "A heavy timber beam snaps under the pressure, striking Gabriel Vance and pinning him against the rising sludge."
- **Space-western T7 & T8:** Both say "A flickering overhead light reveals a loose floor grating near Scott Parker's hiding spot."

### 7. Ruling Intent Verb Mismatch (LOW)

The ruling LLM classifies defensive/stealth actions as "sneak" when they're more accurately "take cover" or "hide":

- Allied-ww2 T25: intent_verb="sneak" for "reach for my medic kit and try to slide toward a dark corner"
- Space-western T25: intent_verb="sneak" for "draw my sidearm and crouch behind the nearest turbine housing"
- Zombie T25: intent_verb="sneak" for "draw my pistol and duck back into the shadows"

### 8. Convergence Score Dead Spots (LOW)

Multiple turns across packs have convergence score ≤ 1 (dead game states with no active elements):

- Space-western T21: score = 0 (no threads, no depth, no age, no beat, no dice)
- Noir T3, T10-T11, T18-T20: score ≤ 1
- Zombie T3, T9-T15: score ≤ 2

### 9. Duplicate Turns (MEDIUM)

Every pack has duplicate turn entries in events.jsonl (same turn number appears twice):

| Pack | Duplicate Turns |
|------|----------------|
| noir | T5, T10, T15, T20, T25 |
| space | T5, T15, T20, T25 |
| piracy | T5, T10, T15, T20, T25 |
| zombie | T10, T15, T20, T25 |
| ww2 | T10, T15, T20 |

The pattern is regular — every 5 turns. The second occurrence of each turn has `phase=?` and `beat=null` with empty candidates. This suggests a retry or reconciliation event being logged as a separate turn.

### 10. No Arc Resolutions (MEDIUM)

Zero arc resolutions across all 5 packs. Despite 105 total threads created, none are ever resolved via `arc_resolution`. Threads are only updated or left pending. This means the game never closes its narrative arcs.

### 11. Sparse State Changes (LOW)

State changes (conditions/inventory) are sparse relative to turn count:

| Pack | Turns with Changes | Rate |
|------|-------------------|------|
| noir | 11/25 | 44% |
| space | 9/25 | 36% |
| piracy | 16/25 | 64% |
| zombie | 5/25 | 20% |
| ww2 | 7/25 | 28% |

Zombie (cautious) has only 5 turns with any state change — the player never takes meaningful actions that alter conditions or inventory.

---

## Tooling Issues

### All Fixed

The following issues have been resolved:

1. **`eval --help`** — Added `eval` to `skip_events` set and commands that don't need events loaded upfront.
2. **`eval compare`** — Same fix. `cmd_eval_compare()` loads events itself via `_load_run_events()`.
3. **ALL `[save-path]` positional args** — COMMANDS.md replaced all `[save-path]` with `--save-dir <path>`.
4. **`--auto-report` from ev.yaml** — Added `auto_report` field to `ev.yaml` session config. Resolution: CLI flag > session_config > default False.
5. **`--eval` flag for play** — Added `eval` to `_BOOL_FLAGS`. Now `ev.py play --eval` runs checkers after the session.

### Null GM Beats — No Checker Enforces 50% Threshold

No checker enforces a null gm_beat threshold. The prompt (`ccya/prompts/storytell_system.j2:80,93,106`) explicitly allows null beats. The "20-56% null rate" finding from ev-review is qualitative, not from a checker.

---

## Summary

The biggest non-checker issues are:

1. **Null GM beats** — storyteller fails to generate beats ~30-50% of the time
2. **Scene candidates don't inform beats** — rich candidate data (up to 2 NPCs per turn) is consistently ignored by the storyteller; golden-piracy has 0 turns where candidates and beats coexist
3. **Phase machine convergence starved** — convergence averages ~2.2-2.3 across packs (threshold 3.0), CLIMAX transitions are hard-forced after 4 turns instead of natural. Root cause: hiding players produce no pressure beats → convergence stays below threshold → feedback loop.
4. **Player behavior monotony** — personas funnel everything into hiding/stealth, which starves convergence and creates the feedback loop in #3
5. **Thread accumulation** — threads created but never resolved
6. **No arc resolutions** — zero arc resolutions across all 5 packs
7. **Duplicate turns** — every pack has regular duplicate turn entries (every 5 turns)
8. **Beat effect duplication** — same text regenerated across turns
