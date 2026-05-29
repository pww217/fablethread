# Ruling Mechanic Evaluation — Turn 1-10

## Overview

The ruling engine parses player intent and resolves skill checks using a dice-roll system (2d6 + modifiers vs difficulty). It produces an `intent_verb`, optional check parameters, band result, and momentum delta.

---

## Intent Parsing

### Intent verbs observed

| Verb | Count | Examples |
|------|-------|---------|
| `repair` | 6 | Fix clamps, use blaster on component, assess systems, restart engines, vent thruster |
| `recall` | 2 | Ask Robert about battle status, ask about factions/crew |
| `deceive` | 1 | Bribe militia |
| `pilot` | 1 | Get ship airborne with crew aboard |

### Assessment

- **6 out of 10 turns** are `repair`. This is a heavily repair-focused game session — the player spends most time trying to fix/assess their ship. Not inherently wrong, but suggests either: (a) narrow gameplay loop, or (b) limited intent verb coverage in the ruling prompt for non-combat actions.
- `recall` checks correctly have no skill/difficulty and produce no dice roll — these are information-gathering with automatic success. This is correct behavior.
- No verbs observed for socialize, fight, stealth, move, or other common action types. The verb taxonomy appears limited in this dataset.

### Intent accuracy (qualitative)

All parsed intents match player input reasonably well:

| Turn | Player Input | Parsed Intent | Quality |
|------|-------------|---------------|---------|
| 1 | "Attempt to bribe the militia..." | "Offer money to the militia to prevent impoundment" | Good — adds context ("prevent impoundment") |
| 2 | "Who is battling... condition of ship?" | "Timothy asks Robert for information regarding battle and ship status" | Accurate but verbose (uses PC name) |
| 3 | "But who is fighting? What factions?" | "Timothy asks for info on combatants, factions, ship/crew details" | Accurate but verbose |
| 4 | "Help Clifford stabilize clamps..." | "Assist Clifford in stabilizing docking bay clamps" | Good — captures NPC involvement |
| 5 | "Use blaster to short out jammed component" | "Timothy attempts to use blaster's energy discharge..." | Accurate but verbose |

**Issue:** When `recall` checks have no check required, the intent still includes a target (e.g., "Robert Gonzalez"). This is harmless but unnecessary for automatic-success recalls.

---

## Dice Roll Resolution

### Check results summary

| Turn | Skill | Difficulty | Dice | Stat Mod | Diff Mod | Cond Mod | Total | Band |
|------|-------|-----------|------|----------|----------|----------|-------|------|
| 1 | charisma | normal | [1,3] | +2 | 0 | 0 | **6** | fail |
| 4 | strength | normal | [3,3] | +0 | 0 | 0 | **6** | fail |
| 5 | dexterity | hard | [2,6] | +1 | -1 | 0 | **8** | partial |
| 6 | lore | normal | [3,5] | +0 | 0 | 0 | **8** | partial |
| 7 | — | — | [] | — | — | — | **0** | (no check) |
| 8 | wits | normal | [3,5] | +1 | 0 | 0 | **9** | partial |
| 9 | dexterity | normal | [2,6] | +1 | 0 | 0 | **9** | partial |
| 10 | dexterity | hard | [2,4] | +1 | -1 | 0 | **6** | fail |

### Band distribution (7 checks only)

| Band | Count | Percentage |
|------|-------|-----------|
| Partial | 4 | 57% |
| Fail | 3 | 43% |
| Hit | 0 | 0% |
| Crit success | 0 | 0% |

### Assessment

- **Zero hits or crits in 10 turns.** This is notable. The band thresholds appear to be: fail ≤6, partial =7-8 (normal), hit ≥9? Turn 5 and 6 both rolled 8 on different difficulties and got "partial." Turns 8 and 9 rolled 9 and also got "partial" — so the threshold for "hit" may be higher than 9.
- **Partial is very common** (4 of 7 checks). This means most actions succeed partially but with a cost or complication, which drives narrative forward without full success. This seems to be working as designed for tension-building.
- **Difficulty modifiers work correctly:** Hard difficulty applies -1 modifier (Turns 5 and 10 both show `diff_mod=-1`). Turn 5's [2+6]+1-1=8 → partial is correct math. Turn 10's [2+4]+1-1=6 → fail is also correct.
- **Stat mods vary:** PC has +2 charisma (turn 1), +1 dexterity and wits (turns 5,8,9). Strength and lore have no stat bonus. This suggests a spread across stats but with some gaps.

---

## Momentum Tracking

### Turn-by-turn momentum

| Turn | Before | After | Delta | Trigger |
|------|--------|-------|-------|---------|
| 1 | 0 | -1 | -1 | fail (charisma check) |
| 2-3 | -1 | -1 | +0 | no checks |
| 4 | -1 | -2 | -1 | fail (strength check) |
| 5 | -2 | -2 | +0 | partial |
| 6 | -2 | -2 | +0 | partial |
| 7 | -2 | -2 | +0 | no check (recall, momentum stable — top-level event fields show correct continuity) |
| 8 | -2 | -2 | +0 | partial |
| 9 | -2 | -2 | +0 | partial |
| 10 | -2 | -3 | -1 | fail (dexterity hard) |

### Assessment

- **Fail → momentum_delta = -1** is consistent across turns 1, 4, and 10. This is correct design behavior — failing a check costs narrative control to the GM.
- **Partial → momentum_delta = +0** is consistent across all partial results (turns 5,6,8,9). The player keeps their momentum but doesn't gain it back.
- **Turn 7 (no anomaly):** Top-level event fields show correct momentum continuity: -2 → -2 (delta 0). The original concern was based on querying `ruling.momentum_before` which is absent on non-roll turns, not top-level `event['momentum_before']`. No anomaly exists — momentum persists correctly through non-roll turns.
- Momentum never exceeds 0 in this dataset — the PC has been on the defensive throughout all 10 turns.

---

## Check Requirements

### Distribution

| Required | Count | Percentage |
|----------|-------|-----------|
| True (roll required) | 7 | 70% |
| False (auto-success) | 3 | 30% |

All `recall` checks have `required: false`. All action verbs (`repair`, `deceive`, `pilot`) require rolls. This is correct — information gathering should be automatic, while physical/social actions need resolution.

### Skills used

| Skill | Count |
|-------|-------|
| dexterity | 3 |
| charisma | 1 |
| strength | 1 |
| lore | 1 |
| wits | 1 |

Dexterity is the most-used skill (repairing ship systems, piloting). The PC appears to be a pilot/mechanic type character. No `charisma` or `strength` checks after turn 4 — social and brute force actions were underutilized in this session.

---

## Pacing Integration

### Directive evolution

| Turns | Directive | Gate | Beat Locked |
|-------|-----------|------|-------------|
| 1-3 | Pressure | allow | false |
| 4-9 | Breathe | allow | false |
| 10 | "Breathe; Resolve a Threat" | allow | true |

### Assessment

- The ruling engine correctly transitions from **Pressure** (turns 1-3, high-tension opening) to **Breathe** (turns 4-9, ship repair sequence). This matches the narrative arc — after initial crisis, player focuses on getting functional.
- Turn 10 shows a compound directive "Breathe; Resolve a Threat" with `beat_locked=true`. The ruling engine is signaling that this turn should resolve an ongoing threat while maintaining breathing room for resolution. This is correct escalation behavior.

---

## Performance

### Tokens and latency per ruling call

| Metric | Min | Max | Average |
|--------|-----|-----|---------|
| tokens_in | 1492 | 1562 | ~1538 |
| tokens_out | 60 | 86 | ~76 |
| ms | 2508 | 2897 | ~2770ms (~2.8s) |

### Assessment

- **Consistent token usage** across all turns (1492-1562 in, 60-86 out). The ruling prompt is stable and doesn't grow with game state — good design.
- **Latency is consistent** at ~2.7-2.9s per call. No degradation over time despite increasing context in other streams. This suggests the ruling system prompt is well-contained and not accumulating unnecessary data.

---

## Issues Found

### 1. Turn 7 intent classification (low)
Turn 7 ("Check the status of the ship and it's flight readiness") was classified as `repair` but with no check required — unlike turn 6 which had nearly identical intent and got `lore/normal`. The ruling engine decided no further check was needed since turn 6 already established the ship's systems were fried/isolated. This is arguably correct behavior (avoiding redundant rolls), but it means "assess flight readiness" wasn't distinguished from "check status." If assessing flight capability should be a separate action, the intent parser needs to differentiate these two types of assessment.

**Note:** The report originally flagged this as a momentum anomaly because `ruling.momentum_before` was queried instead of top-level event fields. Top-level `momentum_before=-2` exists for all turns (including non-roll ones) and correctly carries forward from turn 6. Use `ev.py pacing <turn>` or query top-level `event['momentum_before']`, not `ruling.momentum_before`, to avoid misleading defaults on non-roll turns.

### 2. No hits/crits in dataset (low concern)
All 7 checks resulted in fail or partial only. This could indicate:
- The band thresholds are too aggressive for the PC's stats, or
- The player simply had bad luck across 10 turns (probability of zero hits on a fair system is low but possible), or
- Band thresholds need calibration review against actual dice distributions.

### 3. Verbose intent text with PC name (low concern)
Several intents use "Timothy attempts..." instead of just describing the action ("Attempt to..."). This adds unnecessary verbosity and couples ruling output to a specific character name that may not be needed for game logic.

---

## Summary

The ruling engine is functioning correctly across its core responsibilities: intent parsing, skill check resolution with dice rolls + modifiers, band assignment, momentum tracking (top-level event fields always carry forward; `ruling` dict only includes them when `rolled=True`), and pacing directive integration. The main areas of concern are the complete absence of hit/crit results in this dataset and turn 7's intent classification ambiguity — both warrant further investigation but don't indicate critical failures.
