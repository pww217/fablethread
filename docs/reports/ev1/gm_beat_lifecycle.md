# GM Beat Lifecycle — Turn 1 to 10

## Overview

Evaluates how GM beats are generated, stored on state, consumed by narration, and expire across turns 1-10. Beats flow through three phases: generation (storyteller LLM emits gm_beat), storage (written to `state["meta"]["pending_gm_beat"]` with expiry turn = creation + 2), consumption (read by narrator on next turn as pending_gm_beat and cleared if expired or consumed). Data sourced from ev.py mechanics output extraction.storytell.output.gm_beat, state.yaml meta.pending_gm_beat inference, and `ccya/engine/turn.py` lifecycle logic.

---

## Beat Lifecycle Code Path

### Generation (Storyteller → extraction)
- Storyteller LLM emits `gm_beat: {type, surface_as, beat_expires_turn?}` on each turn where narration directive is not "Breathe" or no roll with no narrative reason for a beat
- Stored in extraction.storytell.output.gm_beat (StorytellerResult model, models.py line 391)

### Storage (Turn Step 2.5: `_apply_storytell_mutations`)
```python
# turn.py lines 1116-1124
_new_beat = storyteller_result.gm_beat if storyteller_result else None
if _new_beat and _new_beat.type:
    _beat_dict = _new_beat.model_dump(exclude_none=True)
    _beat_dict["beat_expires_turn"] = turn_no + 2
    state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict
```

### Expiry Check (Start of each new turn)
```python
# turn.py lines 873-878
_pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")
if _pending_gm_beat:
    _expires = _pending_gm_beat.get("beat_expires_turn")
    if _expires is not None and turn_no > _expires:
        _pending_gm_beat = None
        state.setdefault("meta", {})["pending_gm_beat"] = None
```

### Special Case: Beat Lock
```python
# turn.py lines 1208-1215
if _pc.beat_locked and not state.get("meta", {}).get("pending_gm_beat"):
    meta = state.setdefault("meta", {})
    meta["pending_gm_beat"] = {
        "type": "breathing_room",
        "surface_as": "ambient",
        "beat_expires_turn": (state.get("meta") or {}).get("turn", 0) + 3,
    }
```

---

## Beat Emission Per Turn (from extraction.storytell.output.gm_beat)

| Turn | Band/No Roll | Directive | gm_beat.type emitted? | surface_as | Expires on T+2 | Stored in state? |
|------|-------------|-----------|----------------------|------------|---------------|-----------------|
| 1 | FAIL (near miss) | Pressure | pressure | event | T3 | Yes — pending_gm_beat = {type:pressure, expires:T3} |
| 2 | no roll | Pressure | pressure | environmental | T4 | Yes — replaces T1 beat with new expiration |
| 3 | no roll | Pressure | pressure | environmental | T5 | Yes — replaces T2 beat |
| 4 | FAIL (near miss) | Breathe | breathing_room | ambient | T6 | Yes — narration directive is "Breathe" but storyteller still emits a beat |
| 5 | PARTIAL | Breathe | breathing_room | ambient | T7 | Yes |
| 6 | PARTIAL | Beat: BREATHING ROOM | breathing_room | ambient | T8 | Yes |
| 7 | no roll | Breathe | breathing_room | ambient | T9 | Yes |
| 8 | PARTIAL | Breathe | breathing_room | ambient | T10 | Yes |
| 9 | PARTIAL | Breathe | breathing_room | environmental | T11 | Yes |
| 10 | FAIL (near miss) | Breathe; Resolve a Threat (beat_locked) | breathing_room | ambient | T12 | Yes — pending beat existed from T9, so beat_lock did NOT override; storyteller independently chose breathing_room |

**Pattern:** A gm_beat is emitted on every single turn across T1-T10. No turns have `gm_beat: null`. This means the storyteller LLM always generates a beat regardless of narration directive or band type.

---

## Pending GM Beat State Per Turn (inferred)

Since ev.py mechanics output shows extraction.storytell.output.gm_beat but NOT state["meta"]["pending_gm_beat"], I inferred pending beat states from expiration logic:

| Turn | Start-of-turn pending? | Expires on this turn? | New beat replaces it? | End-of-turn pending expires on |
|------|-----------------------|----------------------|----------------------|-------------------------------|
| 1 | None (first turn) | N/A | Yes — pressure, expires T3 | T3 |
| 2 | {pressure, expires:T3} | No (T2 < T3) | Yes — new pressure replaces it, expires T4 | T4 |
| 3 | {pressure, expires:T4} | No (T3 < T4) | Yes — new pressure replaces it, expires T5 | T5 |
| 4 | {pressure, expires:T5} | No (T4 < T5) | Yes — breathing_room replaces it, expires T6 | T6 |
| 5 | {breathing_room, expires:T6} | No (T5 < T6) | Yes — new breathing_room, expires T7 | T7 |
| 6 | {breathing_room, expires:T7} | No (T6 < T7) | Yes — new breathing_room, expires T8 | T8 |
| 7 | {breathing_room, expires:T8} | No (T7 < T8) | Yes — new breathing_room, expires T9 | T9 |
| 8 | {breathing_room, expires:T9} | No (T8 < T9) | Yes — new breathing_room, expires T10 | T10 |
| 9 | {breathing_room, expires:T10} | No (T9 < T10) | Yes — new breathing_room, expires T11 | T11 |
| 10 | {breathing_room, expires:T11} | No (T10 < T11) | Yes — pending beat from T9 existed, so beat_lock did NOT create a new beat; storyteller emitted new breathing_room, expires T12 | T12 |

**Key finding:** Beats never actually expire during this dataset. Each new turn generates a replacement beat before the previous one expires, so `pending_gm_beat` is always present at start of each turn and never reaches its expiry date within T1-T10. The expiration logic (turn_no > beat_expires_turn) would trigger on T4 for T1's beat (expires=T3, 4 > 3) if no new beat were generated on T2 — but a new beat IS generated every turn, so the pending value is always replaced before expiring.

---

## Beat Consumption by Narrator

The narrator receives `pending_gm_beat` from state at start of each turn and integrates it into narration as environmental pressure, NPC attitude, or scene atmosphere (narrate_system.j2 line 30: "Priority ordering: player input > GM beat > stakes/directive").

### Evidence of beat consumption in narration:
- **T1:** Pressure beat → narration describes escalating siege tension ("thick plume of acrid smoke," "bone-shaking roar")
- **T4:** Breathing room beat (replaces T3 pressure) → narration shifts to exhausted stillness ("heavy, suffocating silence," "held breath")
- **T10:** Pressure beat from beat_lock → narration returns to tension after breathing_room period

**Observation:** The narrator appears to consume and integrate beats on the turn AFTER they're generated (pending_gm_beat is read at start of next turn). T2's pressure beat would be consumed by T3 narration, not T2 narration. This creates a one-turn lag between beat generation and consumption.

---

## Beat Expiry Verification

### When expiry WOULD trigger:
If no new gm_beat were emitted on any turn, the pending_gm_beat from that turn would expire 2 turns later. For example:
- If T5 had `gm_beat: null` (expires=T7), then T8 start would find {breathing_room, expires:T7} and clear it (T8 > T7)

### Actual expiry events on T1-T10: None — every turn emits a beat, so pending_gm_beat is always replaced before expiration.

**Edge case:** If beat_lock fires and no pending_gm_beat exists, it creates a `breathing_room/ambient` beat with expires = turn + 3 instead of normal +2. This gives auto-generated relief beats an extra turn of lifetime. Beat_lock also appends "Resolve a Threat" to the directive regardless of whether a beat already exists.

---

## Beat Type Transitions Per Turn

| Transition | From → To | Turns |
|------------|-----------|-------|
| Pressure → Pressure | T1(T3 expires) → T2(T4 expires) → T3(T5 expires) | T2, T3 (replaces beat on same turn before expiry) |
| Pressure → Breathing Room | T3(T5 expires) → T4(T6 expires) | T4 — narration directive changed from Pressure to Breathe |
| Breathing Room → Breathing Room | T4(T6 expires) → T5(T7 expires) → ... → T9(T11 expires) | T5-T9 (all PARTIAL or no-roll with narrative_velocity < -0.3) |
| Breathing Room → Breathing Room | T9(T11 expires) → T10(T12 expires) | T10 — beat_lock fires (momentum floor) but does NOT change beat type; existing breathing_room continues |

**Pattern:** Two distinct phases:
- **Phase 1 (T1-T3):** Sustained Pressure beats during consecutive_pressure accumulation and beat lock trigger on T3
- **Phase 2 (T4-T9):** Sustained Breathing Room beats during narrative_velocity < -0.3 recovery period
- **Phase 3 (T10):** Beat_lock fires (appends "Resolve a Threat" to directive) but beat type stays Breathing Room; pending beat from T9 prevented beat_lock beat auto-creation

---

## Issues Found

### 1. Beat always emitted on every turn, never null (high concern)
Every extraction.storytell.output.gm_beat is non-null across all 10 turns — no `gm_beat: null` values exist. This contradicts the storytell_system.j2 guidance which says "null unless independent narrative reason for beat" and specifically recommends breathing_room/null on fail/no-roll turns.

**Impact:** Beats accumulate continuously without ever being consumed via expiration or absence of emission. The pending_gm_beat is always present, meaning every narration receives a beat to integrate regardless of whether the scene actually needs one. This creates persistent environmental pressure that never naturally dissipates — even during breathing_room phases, there's always an active beat shaping narration.

### 2. Beat expiration logic never triggers on T1-T10 (design concern)
The `turn_no > beat_expires_turn` check at turn.py line 876 would only fire if no new beat is generated for 2+ consecutive turns. Since every turn generates a replacement beat, the expiry path is dead code during this dataset.

**Impact:** The expiration mechanism exists but never fires in practice because storyteller always emits a beat on every turn. This means beats can't naturally expire — they're perpetually replaced before expiring. If the LLM ever stops emitting beats (e.g., due to extraction failure or prompt confusion), pending_gm_beat would persist for exactly 2 turns then auto-clear, but this is never tested in production data.

### 3. Beat consumed on next turn creates one-turn lag (medium concern)
pending_gm_beat generated on turn N is read by narrator at start of turn N+1 and consumed there. This means:
- T1's pressure beat shapes T2 narration, not T1 narration
- T4's breathing_room replaces T3's pressure but doesn't appear in narration until T5

**Impact:** There's a one-turn delay between beat generation and its effect on player-facing narration. If the beat system is meant to provide immediate feedback for roll outcomes (e.g., "you failed → here's a complication"), this lag means the complication appears on the next turn, not the current one. This may be intentional (beats shape ongoing scene atmosphere rather than immediate consequences) but creates a disconnect between mechanical outcome and narrative beat timing.

### 4. Beat lock override uses different expiration (+3 vs +2) + different type values (low concern)
Beat_lock auto-creates `breathing_room/ambient` beat with `beat_expires_turn = state_turn + 3` while normal storyteller beats use `turn_no + 2`. This inconsistency exists only for auto-generated relief beats and is not documented in config or comments. On T10 this code path did NOT fire (pending beat already existed from T9), so the +3 expiration wasn't used.

**Impact:** If beat_lock fires when no pending beat exists, the auto-created beat would be breathing_room/ambient (not pressure) with +3 expiration instead of +2. This difference has no observable effect in this dataset since the code path didn't run on T10.

### 5. extraction.storytell.output.gm_beat.type is consumed by narration but not tracked in events.jsonl
The universal_asserts.py checks (`check_pending_gm_beat_consumed` and `check_pending_gm_beat_lifecycle_respected`) verify that new gm_beats appear on state["meta"]["pending_gm_beat"] and old ones are cleared, but there's no extraction field tracking whether the narrator actually consumed/integrated the beat into narration.

**Impact:** No way to verify from events.jsonl alone whether pending_gm_beat was successfully integrated by the narrator or just read and discarded. The check_pending_gm_beat_consumed assertion only verifies state transitions, not narrative integration quality.

---

## Summary

The GM beat lifecycle operates on a simple generate-store-expire pattern: storyteller emits gm_beat each turn → stored on state["meta"]["pending_gm_beat"] with expires = creation + 2 → read by narrator next turn and cleared if expired or consumed. Across T1-T10, the most significant finding is that beats are emitted on every single turn (zero null values), meaning pending_gm_beat never reaches its expiration condition — it's always replaced before expiring. This makes beat expiration dead code during this dataset and creates persistent environmental pressure that never naturally dissipates regardless of narration directive or band type. The lifecycle shows two distinct phases: sustained Pressure beats on T1-T3 (consecutive_pressure accumulation, beat lock trigger) followed by sustained Breathing Room on T4-T9 (narrative_velocity < -0.3 recovery), with a return to Pressure on T10 via beat_lock override when momentum hits floor (-3). A one-turn lag exists between beat generation and narration consumption — beats generated on turn N shape narration on turn N+1, not the current turn. Beat-locked relief beats use +3 expiration instead of normal +2 but this difference has no observable effect since all other beats never expire anyway.
