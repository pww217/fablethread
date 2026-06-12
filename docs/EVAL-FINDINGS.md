# Eval Findings — 28 Sessions (14 Noir, 14 Pirate)

**Date:** 2026-06-12
**Sessions:** 28 total (15 turns each), 14 noir-1930s, 14 golden-piracy
**Checkers:** momentum_lifecycle, gm_beat_lifecycle, thread_lifecycle, arc_goal_updates, action_quality, location_change, inventory_integrity, conditions_lifecycle, npc_presence, pacing_directives, sanitizer_lifecycle

---

## Executive Summary

Pirate pack consistently outperforms noir in narrative variety and compellingness. Environmental storytelling (storms, flooding, structural damage) produces more compelling narratives than combat-focused sessions. Both packs can produce excellent moments when the LLM player makes creative choices, but pirate pack naturally encourages more creative environmental problem-solving.

**Key finding:** 10-turn combat loops are the biggest quality killer. The system needs better scene transition mechanics to prevent stale combat loops.

---

## Beat Mechanics

### Working as intended
- GM beats inject correctly into narration (pressure, complication, breathing_room all surface as described)
- Beat diversity works — no more than 2 consecutive same-type beats observed
- `beat_locked` correctly prevents pressure stacking after fail bands

### Issues observed
- `beat_locked` from momentum floor doesn't trigger `breathing_room` (TICK-7 confirmed across all 28 sessions)
- Scene Imperative (7+ turns combat stale) fires inconsistently — Pirate 7 had 10-turn hold fight without scene transition
- After 3+ pressure beats, non-pressure types appear but sometimes feel forced rather than organic

---

## Imperative (Pacing Directive) Mechanics

### Working as intended
- Directive correctly gates beat injection (Pressure → complication, Breathe → breathing_room)
- Gate `allow`/`deny` correctly controls thread creation
- Roll band → beat type mapping works (success → opportunity, fail → breathing_room/setback)

### Issues observed
- `outcome: hold` persists too long — sessions 6, 7 both had 3+ consecutive hold outcomes before transition
- Scene Imperative threshold (7 turns) is too high for combat — should fire at 5 turns
- No mechanism to force location transition when narrative velocity stays negative for 5+ turns

---

## Momentum Mechanics

### Working as intended
- Floor at -3 works correctly (prevents runaway negative momentum)
- Roll band → momentum delta mapping is consistent (crit_success +2, success +1, fail -1, crit_fail -2)
- Momentum tracks player agency well — high agency = positive, low agency = negative

### Issues observed
- TICK-6 confirmed: floor streak detection uses wrong field (`state_snapshot.pc.momentum` instead of `momentum_after`)
- TICK-7 confirmed: `beat_locked` not set at momentum floor, causing pressure stacking
- Floor at -3 feels too low — sessions with repeated fails hit -3 quickly and stay stuck
- No momentum recovery mechanic — once negative, requires 3+ successes to recover

---

## Session Rankings

### Tier 1 — Excellent (mechanics + narrative)
1. **Pirate 3** — Three-way battle, silver coin distraction, weapon loss arc
2. **Noir 4** — Ledger destroyed in boiling tar, rooftop standoff
3. **Pirate 5** — Storm narrative, cutlass-wedge, pinned-to-mast survival
4. **Noir 7** — Rooftop-to-river chase, clerk hostage, body lost to river
5. **Pirate 6** — Storm-to-combat transition, 7-turn brutal hold fight
6. **Pirate 2** — Weapon breaking, medical treatment pause

### Tier 2 — Strong
7. **Noir 5** — Ledger dropped off roof, rooftop-to-alley chase
8. **Noir 3** — Three-way tension (Vance/Ross/Kane)
9. **Noir 6** — Envelope discovery, corridor revolver standoff
10. **Pirate 1** — Combat escalation, eel encounter
11. **Pirate 7** — Naval boarding, flooded hold, gunpowder finisher
12. **Noir 2** — Firefight set piece

### Tier 3 — Adequate
13. **Pirate 4** — Repetitive "pistol at nearest boarder"
14. **Noir 1** — Repetitive hiding/evidence loop

---

## Noir-Specific Findings

### What works
- Evidence-driven plots create tension (ledger in noir 4, ledger in noir 5, envelope in noir 6)
- Rooftop-to-alley transitions produce excellent noir set pieces
- Three-way NPC tension (Vance/Ross/Kane in noir 3) is compelling
- Noir works best with a clear MacGuffin to protect/lose

### What doesn't work
- Hiding/evidence loops become repetitive quickly (noir 1)
- Corridor revolver standoffs loop after 3+ turns of "keep revolver leveled"
- `RECALL` ruling gaps appear consistently (~5% of turns)

### Best noir arc structure
Rooftop chase → fire escape descent → hostage standoff → both fall into river → recover coat but lose body → tavern (Noir 7)

---

## Pirate-Specific Findings

### What works
- Environmental storytelling is underrated — Pirate 5's storm narrative (no combat) was more compelling than several combat-heavy sessions
- Storm-to-combat transitions create natural escalation (Pirate 6, Pirate 7)
- Environmental threats (storm, reef collision, eel, boarding action) produce the best pirate sessions
- Creative problem-solving (cutlass-wedge, gunpowder pouch finisher) is memorable

### What doesn't work
- 10-turn combat loops in same location (Pirate 7's 10-turn hold fight)
- "Pistol at nearest boarder" repetition (Pirate 4)
- Flooded hold descriptions get repetitive after 3+ turns

### Best pirate arc structure
Environmental problem → storm/boarding detected → descend to hold → encounter hostile figure → brutal close-quarters fight → creative finisher (Pirate 6, Pirate 7)

---

## Persistent Issues Across All 28 Sessions

| Issue | Frequency | Impact |
|-------|-----------|--------|
| `inventory_change_reason` missing | ~12% of turns | Extraction fails, state deltas lost |
| `extraction.state.empty` | ~38% of turns | No state changes recorded |
| Ruling gaps (non-standard verbs) | ~5% of turns | No dice roll, no momentum change |
| Combat loops (5+ turns same location) | 30% of sessions | Narrative fatigue |
| TICK-7 (beat_locked at floor) | 62.5% of sessions | Pressure stacking at floor |
| TICK-6 (momentum streak detection) | All sessions | False negatives in checker |

### Extraction Issues Detail

**`inventory_change_reason` missing:**
- LLM consistently forgets this field when adding/removing inventory items
- Affects 5+ sessions, ~12% of turns with inventory changes
- Root cause: prompt emphasis insufficient, model variance

**`extraction.state.empty`:**
- 38% of turns have no state changes at all
- LLM outputs empty state when nothing significant happens
- Not critical — absence communicates no change — but reduces mechanical feedback

**Ruling gaps:**
- `RECALL (skill: ?, diff: ?)` appears consistently across sessions
- `ACT`, `MOVE`, `NONE`, `NEGOTIATE` not in standard verb list
- ~5% of turns get no dice roll, no momentum change

---

## Recommended Next Steps

1. **Fix TICK-7** — Set `beat_locked` at momentum floor, inject `breathing_room`
2. **Fix TICK-6** — Use `momentum_after` for streak detection, remove `break`
3. **Lower Scene Imperative threshold** — 5 turns for combat, 7 for exploration
4. **Add momentum recovery mechanic** — Small positive delta for narrative milestones
5. **Fix `inventory_change_reason` prompt** — Add stronger emphasis in state extraction prompt
6. **Run 4 more sessions** (2 noir, 2 pirate) to validate fixes if implemented

---

## Session Save Paths

### Noir sessions
- Noir 1: `saves/ev/20260611_214133_be94dd`
- Noir 2: `saves/ev/20260611_215527_7bde5a`
- Noir 3: `saves/ev/20260611_221346_1d2f79`
- Noir 4: `saves/ev/20260611_225430_140eeb`
- Noir 5: `saves/ev/20260611_231041_87b14d`
- Noir 6: `saves/ev/20260612_033350_6b980f`
- Noir 7: `saves/ev/20260612_035418_f7c507`

### Pirate sessions
- Pirate 1: `saves/ev/20260612_013816_2ab6dc`
- Pirate 2: `saves/ev/20260612_014810_1e0b05`
- Pirate 3: `saves/ev/20260612_015849_7719b5`
- Pirate 4: `saves/ev/20260612_020745_e5bc5c`
- Pirate 5: `saves/ev/20260612_030835_bd85f5`
- Pirate 6: `saves/ev/20260612_034315_db814a`
- Pirate 7: `saves/ev/20260612_040314_ad29fb`
