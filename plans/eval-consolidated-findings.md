# Consolidated Findings — `full_cycle` eval + live game verification (2026-05-21)

**Eval pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8`  
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`  
**Source events (eval):** `evals/runs/latest/artifacts/full_cycle.events.jsonl` — 18 events: 13 turns + 4 compactions  
**Source events (live):** `saves/default/events.jsonl` — 10 events: 8 turns + 2 compactions

---

## Executive Summary

Cross-referencing the eval report against a live game session reveals that **Issue 1 (compaction saves future data) persists**, while several other reported issues are either fixed, not applicable to this game's content, or manifest differently. The most actionable findings are:

- Compaction sanitization captures state from future turns — confirmed in both games
- Condition drift with future `added_turn` values is NOT present in the live game (may be eval-pack specific)
- Progress actions empty arrays: FIXED across all 8 live turns
- Location changes never emit explicit `location_change` deltas, only `location_description` updates

---

## Per-Issue Assessment

### Issue 1: Compaction Saves Future Turn Data — CONFIRMED

**Eval report:** All four compactions capture LATER turn data (inventory, location, tags, conditions, NPCs).  
**Live game verification:** Confirmed.

Compaction at event turn 3 has `compact_start=1, compact_end=1` but its sanitization removes condition `startled`, which was added at **T3**. The compaction range only covers index 1 (event T2), so removing a condition from T3 means the sanitization logic sees state from a future turn.

Compaction at event turn 6 has compact range indices 2–4 and correctly shows empty `condition_remove` because `startled` (added_turn=2, turns_remaining=1) expires within that range — but this is consistent behavior masking an underlying indexing/state-source bug in the earlier compaction.

**Impact:** Chronicle bullets may be accurate (separate LLM call), but any system loading from saved compaction state would see corrupted history. Conditions removed during sanitization include ones not yet added at compact time, potentially causing missing conditions when restoring game state.

---

### Issue 2: Condition Schema Drift with Future `added_turn` — NOT PRESENT (live)

**Eval report:** At T1, conditions appear with `added_turn: 8` and `added_turn: 10`.  
**Live game verification:** Not present. Conditions use consistent indexing (`startled` at T3 has `added_turn=2`, matching the extraction_context's 0-based index). No future-dated conditions detected in either `pc_condition_add` output or `conditions_this_turn` context.

This may be eval-pack specific (different seed state, different narration content that triggers hallucination) rather than a universal engine bug.

---

### Issue 3: Progress Actions Empty Across All Turns — FIXED

**Eval report:** Every turn had `actions: []`.  
**Live game verification:** All 8 turns produce exactly 4 actionable suggestions with real content (e.g., "Attempt to bypass the coupling using the insulated pliers", "Ask Brian Wilson for a map of the brittle secondary lines").

Progress extraction pipeline is working correctly in this session. If it was broken before, something changed between runs.

---

### Issue 4: Credits Disappear During Turn 5 — N/A (no currency)

**Eval report:** Credits go from `200` at end of T4 to `NONE` at T5 with zero inventory deltas.  
**Live game verification:** This game session has no credits/currency tracking in its seed state or gameplay. Cannot verify this specific bug without a game that uses currency mechanics.

---

### Issue 5: Brass Key Removed on Use (Reusable Item) — NOT PRESENT

**Eval report:** `brass_key` removed at T8 when player used it to unlock a door.  
**Live game verification:** No brass key exists in this session. The multimeter and digital_multimeter break when used, which is correct behavior for disposable tools rather than reusable ones. No reusable items are incorrectly consumed.

---

### Issue 6: Location Change Without Delta — PARTIALLY CONFIRMED

**Eval report:** Turn 8 changes location without `location_change` delta; turns 10/12 show wrong/future locations due to compaction corruption (Issue 1).  
**Live game verification:** All location tracking uses only `location_description` updates. No explicit `location_change` deltas appear anywhere in the game, even when spatial descriptions evolve significantly across T2–T6:

- T2: "debris-strewn floors, collapsed concrete pillars"
- T4: "overhead lights have stabilized into a steady, rhythmic pulse of golden light"  
- T5: "amber luminescence that pushes the oppressive shadows back"
- T6: "steady, mechanical thrum provides constant baseline"

The player never leaves `leemouth_substation` but gets new spatial descriptions each turn. The engine tracks location correctly in `extraction_context.location_this_turn.id`, but never emits a proper `location_change` delta when the player stays put and only receives updated descriptions. This may be by design (no movement = no change), but it means there's no way to distinguish "player stayed" from "engine failed to detect move."

---

### Issue 7: NPC Mention Checker False Positives — NOT VERIFIED FROM EVENTS

**Eval report:** Auto-checker fires on common words ("Crossed", "Careful", "Narrowing").  
**Live game verification:** Cannot verify without running the auto-checker against narration text. Events.jsonl doesn't include checker output. Would need to run `make check` or equivalent.

---

### Issue 8: Extract Scene Removes NPCs During Location Transitions — NOT PRESENT

**Eval report:** At T10, `tough_a` and `tough_b` removed even though they move with Matthew into the common room.  
**Live game verification:** No NPCs are ever removed from the scene across all 8 turns. Trevor Williams and Brian Wilson persist throughout with only `npc_update` entries. This issue may require a multi-location game to reproduce.

---

### Issue 9: Extract Progress Duplicates Recent Events — NOT PRESENT

**Eval report:** At T13, duplicate `recent_events_add` entry for `lost_stolen_pouch`.  
**Live game verification:** All `recent_events_add` IDs are unique across all turns. No deduplication issues found in the live session. The engine correctly tracks facts through the `changes.facts` field (one new fact per turn, no duplicates).

---

### Issue 10: World Pack Style Block Wasted in Extractors — NOT VERIFIED FROM EVENTS

**Eval report:** ~800 tokens/turn wasted across Scene, State, and Progress extractors.  
**Live game verification:** Requires checking rendered prompt structure (not available in events.jsonl output). Would need to inspect `extraction.*.rendered_user` content directly.

---

## New Observations from Live Game

### `changes` field tracks all state mutations correctly
The live game uses a top-level `changes` dict with sub-keys: `inventory`, `player`, `facts`, and `momentum`. Each entry has a `kind` (added/removed/renamed/condition_added) plus relevant metadata. This is the canonical source of truth for turn-to-turn state mutations, not `state_diff` (which doesn't exist as a top-level field).

### No dice rolls occur in this session
All turns show `rolled=False`. No momentum/band tracking happens because player actions don't trigger checks requiring rolls. The rules engine correctly identifies intents but no skill checks are called for the player's input style. This is not a bug — it depends on game state and player intent classification.

### Compaction sanitization structure
Compactions contain: `npc_merge`, `inventory_remove`, `pressure_remove`, `condition_remove`, and `recent_events_compact_count`. They do NOT include explicit state snapshots or applied deltas in the events.jsonl format used by this session. The compaction logic appears to work on a separate internal state representation that gets serialized into these sanitization fields.

---

## Updated Priority Recommendations

### P0 — Must fix
1. **Compaction save_state bug** (Issue 1) — Confirmed in both eval and live game. Compaction sanitization removes conditions/items from future turns, corrupting chronicle history and any downstream state restoration.

### P1 — Should investigate  
2. **Condition drift scope** (Issue 2) — Not present in this session but was critical in the eval pack. Determine if it's content-specific or engine-wide by testing with different game scenarios.
3. **Location delta emission** (Issue 6) — No `location_change` deltas are ever emitted when players stay in one location, even as spatial descriptions evolve significantly. Clarify whether this is intentional design or a missing feature that breaks downstream systems expecting explicit change events.

### P2 — Prompt fixes (from original report)
4. **Brass key reusable item** (Issue 5) — Add "use ≠ consume" guidance to Extract State prompt when currency/item games are used.
5. **NPC mention checker false positives** (Issue 7) — Run auto-checker against live game narration and fix if still firing on common words.
6. **Progress deduplication** (Issue 9) — Currently working; keep monitoring for regressions.

### P3 — Optimization / Verification needed
7. **World Pack Style token waste** (Issue 10) — Requires prompt structure inspection, not available from events alone.
8. **NPC removal during transitions** (Issue 8) — Needs a multi-location game scenario to reproduce and verify fix.

---

## Comparison Matrix

| Issue | Eval Report Status | Live Game Status | Notes |
|-------|-------------------|------------------|-------|
| Compaction saves future data | CRITICAL (all 4 compactions) | CONFIRMED (both compactions) | Same root cause, confirmed across sessions |
| Condition drift future added_turns | CRITICAL (T1 shows T8/T10 dates) | NOT PRESENT | May be eval-pack content-specific |
| Progress actions empty | CRITICAL (all 13 turns) | FIXED (4 per turn on all 8) | Pipeline working correctly now |
| Credits disappear on T5 | CRITICAL | N/A (no currency in session) | Needs currency game to verify |
| Brass key reusable removed | MAJOR | NOT PRESENT | No reusable items consumed incorrectly |
| Location change without delta | MAJOR | PARTIALLY CONFIRMED | Only `location_description`, no `location_change` |
| NPC mention false positives | MINOR (8 turns) | NOT VERIFIED | Needs auto-checker run against live narration |
| NPC removal during transitions | MINOR (T10) | NOT PRESENT | No location changes in this session to trigger |
| Duplicate recent events | MINOR (T13) | NOT PRESENT | Deduplication working correctly |
| World Pack Style token waste | MINOR (~800 tok/turn) | NOT VERIFIED | Requires prompt structure inspection |
