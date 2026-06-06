# Cordyceps v3 EV Findings — June 6

**Source:** `saves/cordyceps-year-twenty-2026-06-06/events.jsonl` (8 turns)
**Comparison:** vs `CONSOLIDATED-EV-FINDINGS.md` (noir 17 + v1 34 + v2 26 = 77 turns)

---

## Improvements (New Behaviors Not Seen in Prior Saves)

### Conditions system works (contradicts F5.3)
`bleeding arm` condition appeared at T5 and persisted through T8 after Mark was hit by shrapnel. First save across all analyses where conditions are used for combat consequences. The system is functional when the LLM chooses to use it.

### Thread count stable, no bloat (F2.8 fixed)
4 threads across all 8 turns — zero growth. No thread_add emitted after seed time. The seed-time hard limits (commit 1ddf22bf) plus prompt restraint examples (59c39e9) are working for thread_add frequency.

### beat_locked fires for the first time (F1.3 partially addressed)
T6-T7 show directive suffix "Resolve a Threat" which only appends when beat_locked=True. This was 0 out of 77 prior turns. Something made it trigger — either momentum floor or a change in consecutive_pressure tracking.

### Beat diversity improved (F1.1 modest improvement)
Storytell output: opportunity, pressure, complication across 5 beat-emitting turns (T1, T3, T4, T5, T6). 3 types vs 2 max in noir/v1. Recent Beats section even shows BREATHING ROOM (ambient) at T6 — but that may be beat_locked override, not LLM self-governance.

### Good pacing ramp
Directives escalate naturally: Breathe(T1) → none(T2) → Scene Pressure(T3) → Scene Imperative(T4-T8) with beat_locked at T6-T7. Narrative progresses: hide → prep → combat → destroy → drone fight → retreat.

### LLM restraint on thread_add and world_state remove
Zero thread_add across 8 turns. Zero world_state_remove (not adding wonky removals). The restraint examples are being followed for "don't add" but not for "don't update."

---

## Same Problems (Confirmed in This Save)

### Thread_update every turn (F2.1, F2.5)
Exactly 1 thread_update every turn, always for `bounty_escalation`, with progress text overwriting previous turn's entry. T6 and T7 both say "convoy engagement has escalated into a three-way crossfire involving automated drone patrols" — identical text in consecutive turns. Progress overwrite means no investigative trail accumulates.

### Zero arc resolution (F4.1)
0 arc_resolve in 8 turns. Visible goal and thematic question unchanged from seed despite narrative progression from hidden ambush → open combat → retreat.

### Zero goal_update (F4.1)
No goal_update despite the game state shifting dramatically (hiding → fighting → retreating). Arc system completely static.

### Beat types still limited (F1.1)
Only opportunity, pressure, complication from storytell output. No breathing_room, revelation, twist, setback, escalation, or callback. The LLM still repeats pressure/complication in sequences (T3 + T5 pressure, T4 + T5 complication).

### "Breathe" directive fires during active tension (F3.2)
T1 directive is Breathe while player is actively preparing for combat convoy. Same pattern as noir/v1/v2.

### Null beats on ~38% of turns (F1.6)
T2, T7, T8 have null storytell gm_beat. Null beats don't clear stale pending_gm_beat value (still confirmed). T7-T8 don't generate a new beat through 2 consecutive null turns.

### World state overlap (new variant of F5.2)
`highway_combat_engagement` (T3) → `highway_sector_seven_combat` (T7) → `sector_seven_skirmish_aftermath` (T8) are all different IDs for essentially the same fact. LLM isn't checking existing entries before adding. Also `technical_wreckage_sector_seven` emitted twice (T4 and T5) with same ID — wasted token emission.

### Scene-scoped threads absent
All 4 threads are ARC-scoped. No scene-scoped threads at all. While this prevents F2.6's "arc-scoped threads never resolve" problem, zero scene threads means zero short-term narrative tension tracking. The pendulum may have swung too far from bloat to starvation.

---

## New Observations (Not in Consolidated Findings)

### beat_locked mechanism uncertain
"Resolve a Threat" fires at T6-T7 but mechanism is unclear. Momentum never hit floor (min 0, floor -3). Directives never included "Pressure"/"Overwhelm" (all Scene Imperative). Needs investigation: possibly engine_mirror.py commit e5af4b8 changed how beat_locked computes, or momentum_floor was lowered in config.

### Conditions ARE functional
`bleeding arm` persists across 4 turns (T5-T8) with proper TTL handling. When the LLM uses conditions, they work. The conclusion in F5.3 ("conditions are dead code") should be updated to "conditions are underutilized."

### Pacing feels organic
Despite the same structural bugs, this save's pacing actually works well. Combat scenes naturally escalate → resolve → retreat. The LLM's independent beat generation + directive system produces decent results when the narrative is simple and physics-driven.
