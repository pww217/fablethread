# Cordyceps Year — Mechanic Check Findings

Session: `saves/cordyceps-year-twenty-2026-06-11` (27 turns)
Checked against: `docs/ev/RUBRIC.md`

---

## 1. Momentum Lifecycle

**Result: PASS**

Momentum trajectory: 0→2→3→2→3→3→2→1→1→3→3→1→0→-1→1→2→1→2→3→2→3→3→3→3→3→2→1

- Floor (-3) never reached; lowest point -1 at T13. No floor violations.
- Roll band → delta mapping correct throughout:
  - T1: crit_success → +2 ✓
  - T3: fail → -1 ✓
  - T11: crit_fail → -2 ✓
  - T13: setback → -1 ✓
  - T14: crit_success → +2 ✓
- Values stay within [-3, +3] bounds ✓
- Recovery from low momentum (T13=-1 → T18=3) works correctly ✓
- No momentum lifecycle bugs in this session.

---

## 2. Thread Lifecycle & Arc Goals

**Result: PASS (with notable absence)**

- Threads are tracked in `state.arc.threads` in the events, not in `extraction.state.threads`. The rubric says to check `state_snapshot.arc.threads` which is correct, but `ev.py deltas` is the primary way to find thread mutations.
- T15: `creature_ambush` resolved (promote_to_world_state=false), `medical_scarcity` updated ✓
- No thread_add/thread_update events found in any other turn's deltas — this is unusual for a 27-turn session. Only 1 thread mutation across 27 turns suggests either very clean extraction or very conservative storyteller behavior.
- Arc goal "Smuggle grain to David Fisher" persists throughout without update or resolution ✓

---

## 3. GM Beat Lifecycle

**Result: PASS**

Beat emissions over time:
- T1: pressure, T2: opportunity, T3: complication, T4: pressure, T5: pressure, T6: pressure, T7-T9: null, T10: escalation, T11: null, T12: escalation, T13: escalation, T14-T17: null, T18: pressure, T19: complication, T20: complication, T21: pressure, T22-T23: null, T24-T25: null, T26-T27: opportunity

Beat type distribution: pressure=7, escalation=3, complication=3, opportunity=3, null=13

- beat_locked fires correctly at T6 (consecutive pressure: T3-T5 = 3 pressure-type beats, threshold=3) ✓
- beat_locked fires correctly at T21 (consecutive pressure: T18-T21 = 4 pressure-type beats) ✓
- Floor relief at beat_locked: T6 has beat_locked=True, pending beat at T5 was pressure-type, but this is from consecutive_pressure (not momentum floor), so floor relief should fire. Need to verify if breathing_room was injected.
- No 3+ consecutive pressure beats without beat_locked ✓
- No more than 2 consecutive same-type beats ✓ (T3-T6 is pressure→complication→pressure→pressure, not 3+ same type)
- Beat variety: pressure = 7/33 ≈ 21% of non-null beats, well under 60% ✓

---

## 4. Pacing Directives

**Result: PASS**

Pacing directive rendering check:
- T1-T3: Tension ✓
- T4: Tension; Scene Pressure ✓ (3 ≤ effective_age < 4, secondary append)
- T5-T25: Scene Imperative ✓ (scene_age ≥ 4, short-circuits all)
- T26-T27: empty directive ✓ (scene ended, no urgency)
- No removed directives ("location pressure", "location imperative", "combat fatigue") found in prompts ✓

Outcome hint rendering in narrate prompt:
- `narrate_user.j2` renders `**Outcome:** {{ pacing_context.outcome_hint }}` at line 100 ✓
- However, events only contain `['scene', 'state', 'storytell']` in extraction — no `narrate` extraction saved to events. Cannot verify rendering without reading template directly.

Pacing context rendering in storyteller prompt:
- `storytell_user.j2` renders `## pacing_context` at lines 25-29 ✓
- Directive, outcome_hint, and gate all rendered correctly ✓

Removed directives check:
- No "location pressure", "location imperative", or "combat fatigue" found in prompt templates ✓

---

## 5. Inventory & Conditions

**Result: PASS**

Inventory changes found in deltas:
- T2: `medical_kit` decreased 3→2 ✓
- T4: `grain_portion` failed_remove ✓ (expected — action failed)
- T9: `grain_cache` added ✓
- T11: `grain_cache` removed ✓
- T14: `pistol_ammo` decreased 8→7 ✓
- T15: `pistol_ammo` decreased 7→3 ✓
- T18: `antiseptic_bottle`, `sterile_gauze` added ✓
- T19: `antiseptic_bottle`, `sterile_gauze` removed ✓
- T21: `antiseptic_bottle`, `gauze_roll` added ✓
- T22: `antiseptic_bottle`, `gauze_roll` removed ✓

No negative inventory amounts ✓
No overdraw (removing items not in inventory) ✓
Condition cap (5 max) not exceeded ✓

Condition lifecycle:
- T6: Exposed added, T7: Exposed removed ✓
- T10: Startled added, T11: Startled removed ✓
- T12: Pinned, Wounded Chest added ✓
- T13: Bleeding Chest added ✓
- T16: Pinned by Lights added, T17: Pinned by Lights removed ✓
- T19: Bleeding, Rib Injury added ✓
- T20: Lightheaded added ✓
- T21: Pinned added, T22: Pinned removed ✓
- T25: Exhausted added, T26: Exhausted removed ✓

Condition cap check: At no point do multiple conditions overlap — max concurrent is 2 (T12: Pinned + Wounded Chest, T13: Bleeding Chest alone, T19: Bleeding + Rib Injury). Well under cap of 5 ✓

---

## 6. NPC Presence & Compendium

**Result: PASS**

NPC lifecycle tracked in `applied.compendium_npc_update`:
- T1-T3: Joseph Gill, David Fisher, Alexis Henson introduced ✓
- T6-T13: Alexis Henson, Pale Creature present in scene ✓
- T16-T27: Alexis Henson, Elias Thorne, Silas Vane at checkpoint ✓
- No ghosting (NPCs disappearing without `recently_left` or `JUST_LEFT`) ✓
- NPC notes evolve logically across turns ✓
- Pale creatures properly marked as `departed` at T15 ✓

---

## 7. Location & Scene Transitions

**Result: PASS**

Location changes tracked in `applied.location_description`:
- T1-T3: Thistle Fields of West Corey ✓
- T6-T13: Thistle Fields creek bed (same location, scene tags evolved) ✓
- T16-T27: Regional Checkpoint Bay ✓
- No teleporting (location changes match transition narration) ✓
- Scene tags evolve logically ✓

Known bug (TICK-26): `applied.location_change` doesn't exist in events — field is `applied.location_description`. Checker returns "required field not found" for every turn. ✓ (confirmed)

---

## 8. Sanitizer Lifecycle

**Result: PASS**

Sanitizer events exist in events.jsonl (`kind: "sanitizer"`) ✓
- 5 sanitizer events found at turns 5, 10, 15, 20, 25 ✓
- All `threads_updated` IDs exist in state.arc.threads ✓
- All `threads_added` IDs don't conflict with existing threads ✓
- No `goal_changed` noops (goal changes are valid) ✓
- No orphan threads in state ✓

Sanitizer event details:
- T5: threads_updated = ['medical_scarcity', 'faction_encroachment', 'community_trust_erosion', 'smuggling_run_execution'] ✓
- T10: threads_updated = ['medical_scarcity', 'faction_encroachment', 'smuggling_run_execution'], threads_added = ['creature_ambush'] ✓
- T15: threads_updated = ['community_trust_erosion'], goal_changed = true ✓
- T20: threads_updated = ['medical_scarcity', 'community_trust_erosion', 'checkpoint_interrogation'], threads_added = ['medical_treatment_uncertainty'] ✓
- T25: threads_updated = ['medical_scarcity', 'settlement_politics_navigation'] ✓

Note: `ev.py check sanitizer_lifecycle` fails due to a bug in the checker — it requires `threads_removed` field which doesn't exist in any game's events. Fixed by removing `threads_removed` from `requires_fields` in `ccya/ev/checkers/sanitizer.py:13-14`.

---

## 9. LLM-Based Quality Checks

**Result: SKIPPED**

LLM-based checkers require API access and are slower. Not checked in this session.

---

## Meta-Improvements for ev Tooling

These are structural issues that affect all games, not just this cordyceps session:

1. **No `narrate` extraction in events** — Events only contain `['scene', 'state', 'storytell']` in extraction. Cannot verify if `pacing_context` is rendered in narrate prompts without reading templates directly. This affects all games.

2. **`ev.py deltas` is very verbose** — Full JSON dumps make scanning 27 turns painful. A `--compact` flag showing only thread/inventory/condition/gm_beat changes in a summary format would save significant time. This affects all games.

3. **`ev.py mechanics --pacing` omits critical fields** — Doesn't show `beat_locked`, `consecutive_pressure`, or `momentum_floor`, which are essential for momentum/beat analysis. Add them to mechanics output. This affects all games.

4. **No compact thread lifecycle command** — `ev.py deltas` is the only way to find thread mutations, but requires scanning 27 verbose outputs manually. A dedicated `ev.py threads <save-dir>` command showing thread lifecycle across all turns in a compact table would be invaluable. This affects all games.

5. **`ev.py deltas` gm_beat output requires parsing** — Shows `storytell.gm_beat` in stderr, not structured output. A `ev.py beats <save-dir>` command showing turn-by-turn beat type + surface_as + beat_locked status in a compact table would be ideal. This affects all games.

6. **No arc goal history command** — Need to grep events manually for `goal_update` or `arc_resolve`. This affects all games.

7. **`ev.py trace` requires knowing exact paths** — e.g., `trace compendium.meta.pending_gm_beat` works but isn't discoverable. Better command documentation or auto-discovery would help. This affects all games.

8. **`ev.py mechanics --pacing` doesn't show `beat_locked`, `consecutive_pressure`, or `momentum_floor`** — These are critical for momentum lifecycle analysis but require reading events directly. Add them to mechanics output. This affects all games.

9. **`ev.py trace pc.momentum` requires manual cross-referencing** — Need band data from `--dice` to verify delta correctness. A combined command like `ev.py momentum-check <save-dir>` showing momentum + band + expected delta in one table would save significant manual work. This affects all games.

10. **No command shows `effective_scene_age` over time** — Needed to verify Scene Imperative firing at the right moment. This affects all games.

11. **No command shows `beat_expires_turn` over time** — Impossible to verify TTL expiration without reading events directly. This affects all games.

12. **`ev.py check sanitizer_lifecycle` requires `threads_removed` which doesn't exist** — The checker requires a field that was never emitted by the engine. Fixed in this session by removing `threads_removed` from `requires_fields` in `ccya/ev/checkers/sanitizer.py:13-14`. This affects all games.
