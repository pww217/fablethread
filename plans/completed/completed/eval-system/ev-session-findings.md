# Zombie-Driven vs Santa Monica: Consolidated Findings

## Session Overview

| Metric | Zombie-Driven | Santa Monica |
|--------|---------------|--------------|
| **Source** | `saves/ev/20260615_225837_35b68a` | `saves/santa-monica-zero-hour-2026-06-15` |
| **Type** | 20-turn automated eval (driven persona) | 24-turn human session |
| **Pack** | zombie-survival | santa-monica-zero-hour |
| **Checkers pass** | 20/23 (87%) | 18/23 (78%) |
| **Avg score** | 0.87 | 0.78 |
| **Phase progression** | SETUP x20 (0 transitions) | All 6 phases (14 transitions) |
| **Convergence >=3** | 0 times | 10 times |
| **Rolls** | 9 (35%) | 22 (58%) |
| **Fail rate** | 55.6% | 68.2% |
| **Empty extraction** | 4/26 (15%) | 14/38 (37%) |
| **Inventory changes** | 0 total | 6 add, 4 remove, 6 update |
| **Condition changes** | 4 add, 4 remove | 14 add, 10 remove |
| **NPC updates** | 46 total | 66 total |
| **Location changes** | 3 | 6 |
| **Threads created** | 0 (only updates) | 13 |
| **Threads resolved** | 1 | 2 |
| **Goal updates** | 0 | 4 |
| **Warnings** | 22 total | 0 |

---

## What We Learned

### 1. The Engine Works Correctly

Santa Monica proves the engine functions as designed: full phase cycling through all 6 phases, 22 dice rolls, 13 thread creations, 4 goal updates, 66 NPC updates. The engine is not broken.

### 2. The Zombie Session Wasn't Broken — It Was Valid

The zombie session built a living world through revelations:
- `resource_scarcity_coverup` thread → world lore about supply chain issues
- `militia_expansion_agenda` thread → political landscape emerging
- 66 NPC updates → characters being established
- 4 condition changes → environmental effects on the player
- 3 location changes → world exploration

Passive gameplay (playing The Sims) is valid. The engine shouldn't force stakes onto a player who doesn't want them.

### 3. The Engine Is Too Passive

A zombie survival game where nothing happens for 20 turns is boring. The engine waits for the player to create stakes, but:
- The storyteller got stuck in a revelation loop instead of balancing revelations with escalation
- The thread system produced no urgency because nothing was escalating
- The convergence scoring has a bootstrap problem: it requires urgent threads to score, but urgent threads require phase escalation

### 4. The Storyteller Had All the Tools It Needed

BEAT_PHASE_MAP for SETUP includes all 9 beat types: `pressure`, `complication`, `escalation`, `revelation`, `twist`, `opportunity`, `callback`, `breathing_room`, `hazard`. They're not locked behind RISING.

The storyteller prompt receives:
- `scene_phase` (SETUP/RISING/CLIMAX/RESOLUTION/BREATHER)
- `allowed_beat_types` (derived from phase)
- `pacing_context` (directive, outcome_hint)
- `pending_beat` (current active beat)
- `recent_beats` (last 5 beats)
- `all_threads` (active threads)
- `world_state` (read-only)
- `prior_history` (recent outcomes)
- `intent` (player intent)
- `band` (roll outcome)

The storyteller chose `revelation` 43% of the time instead of pressure beats. The prompt has diversity rules but no rule about injecting stakes when the player is passive.

### 5. The Convergence Scoring Has a Bootstrap Problem

The scoring components:

| Component | Zombie | Santa |
|-----------|--------|-------|
| thread_weight | 0 (no urgent threads) | Variable (urgent threads present) |
| urgency_depth | 0 (no urgency) | Variable (thread urgency present) |
| scene_age | 0-1 (stuck in SETUP) | 0-2 (scenes progressed) |
| beat_streak | 0-1 (pressure beats) | 0-2 (escalation beats) |
| dice_weight | 0 (fails without urgent threads) | Variable (fails with urgent threads) |

The chicken-and-egg problem:
```
No urgent threads -> thread_weight=0 -> score<3 -> no phase escalation -> no urgency -> no urgent threads
```

The system works fine once in RISING/CLIMAX (Santa proves this), but has no mechanism to escape SETUP without external urgency generation.

### 6. The Ruling Pipeline Correctly Classified Passive Inputs

The ruling pipeline classified ~60% of zombie turns as `routine` or `trivial` with reasons like:
- "routine: non-confrontational movement and compliance"
- "trivial: non-threatening gesture is a routine social de-escalation"
- "routine: complying with a command is not a pivot"
- "routine movement; no immediate risk or narrative pivot"

This is not a bug — it's a behavioral mismatch. The driven persona produces inputs that the ruling pipeline correctly classifies as low-stakes. The engine works as designed; the persona doesn't create stakes.

### 7. The Thread System Degraded in the Zombie Session

The zombie session's thread lifecycle:
```
T1:  update resource_scarcity_coverup
T6:  update militia_expansion_agenda, resolve resource_scarcity_coverup
T7-19: update militia_expansion_agenda (13 consecutive turns, same thread)
```

This is a dead thread — one thread updated 13 times without resolution or new thread creation. The storyteller stopped creating threads after T6 and kept updating the same thread.

Santa Monica: 13 threads created, 2 resolved, 11 pending. Active lifecycle with adds, updates, and resolves.

### 8. The Extraction Pipeline Produced Silent Failures

The zombie session's state extractor produced 0 inventory changes across 26 events (Santa had 16). The scene extractor produced empty tags and NPCs. The storyteller extractor produced only thread updates, no new threads, no goal updates.

This suggests the zombie session's extraction pipeline is working but producing degenerate output — not crashing, but generating empty/useful results.

---

## Recommendations

### A. Auto-Escalation (Not Timer-Based)

Instead of a simple timer, inject stakes through:
- **Random seed events** — `randint`-based probability tables for environmental threats, NPC actions, world state changes
- **Thread auto-escalation** — threads that haven't been resolved after N turns should escalate (urgency bump, new thread spawn)
- **Passive input detection** — when the player provides passive inputs (compliance, movement, observation), the engine should inject stakes through world events, not force phase escalation

The goal: make the world feel alive even when the player is playing The Sims. The player can still choose to be passive, but the world should respond with consequences.

### B. Storyteller Prompt Enhancement

Add instructions to the storyteller prompt:
- When player input is passive (compliance, observation, movement), inject pressure beats through environmental threats, NPC actions, or world state changes
- Balance revelation with escalation — don't let revelation dominate for more than 2 consecutive turns
- When no threads are active, create new threads through environmental or NPC-driven events

### C. Thread Diversity Enforcement

Add constraints to prevent thread degradation:
- Same thread can't be updated more than 2-3 times without creating a new thread or resolving one
- Threads should auto-escalate urgency after N turns without resolution
- Dead threads should be resolved or demoted automatically

### D. Convergence Scoring Time Pressure

Add a `time_pressure` component to convergence scoring that increases over time, encouraging phase transitions even without urgent threads. This isn't forcing escalation — it's making the world feel like it's moving forward even when the player is passive.

### E. Extraction Pipeline Tuning

Investigate why the state extractor produced 0 inventory changes across 26 zombie events. The extraction prompts may not be effectively detecting meaningful state mutations. This needs prompt tuning or extraction logic changes.

---

## Actionable Next Steps

1. **Write a plan doc for auto-escalation mechanics** — random seed events, thread auto-escalation, passive input detection
2. **Enhance storyteller prompt** — add instructions for injecting stakes when player input is passive
3. **Add thread diversity enforcement** — prevent same-thread update loops
4. **Investigate extraction silent failures** — state extractor producing 0 inventory changes

---

## Files

- `docs/ev/reports/zombie-driven-2026-06-15.md` — full zombie eval report
- `docs/ev/reports/santa-monica-2026-06-15.md` — full Santa Monica eval report
- `docs/ev/RUBRIC.md` — evaluation rubric used for checkers
- `docs/ev/CHECKERS.md` — checker documentation
- `saves/ev/20260615_225837_35b68a/events.jsonl` — zombie-driven session data
- `saves/santa-monica-zero-hour-2026-06-15/events.jsonl` — Santa Monica human session data
