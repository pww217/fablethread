---
title: "pending_gm_beat has no TTL enforcement — persists unchanged across turns"
status: done
completed: 2026-07-09
urgency: 2
size: small
created: 2026-07-07
ticket_id: B-39
labels:
  - engine
  - gm-beats
---

# B-39: pending_gm_beat TTL not enforced

## Symptom

`pending_gm_beat` persists unchanged across multiple turns in noir-1930s run. The beat `pressure` with effect `[npcs: silas] [highlight: fear]` persisted from T4 through T8 without being consumed or expiring.

## Evidence

From noir-1930s events:
```
T4:  pending_gm_beat={type: 'pressure', effect: '[npcs: silas] [highlight: fear]'}
T6:  pending_gm_beat={type: 'pressure', effect: '[npcs: silas] [highlight: fear]'}  (unchanged)
T8:  pending_gm_beat={type: 'pressure', effect: '[npcs: silas] [highlight: fear]'}  (unchanged)
T10: pending_gm_beat={type: 'complication', effect: '[thread: heist_trail] [environment]'}  (changed)
```

The checker `gm_beat_lifecycle` flags `beat_consumed` when the beat persists unchanged across turns (line 36 of `gm_beat.py`).

## Root Cause

`state.meta.pending_gm_beat` is set by the ruling step when a beat is selected. It is cleared when the player acts on it or when a new beat is selected. However, there is no TTL mechanism to expire stale beats.

## Evidence (ev-review 2026-07-09, noir-1930s 15t)

- No pending_gm_beat found in any last_turn_state across all 15 turns (verified via events.jsonl scan)
- Beats selected at T6, T8, T9, T12 (selected_beat=1) — all cleared after narrate, never persist to next turn
- state.set_pending_beat(None) at turn.py:170 after narrate completes, before extract begins
- gm_beat_lifecycle checker passes 5/5, 15/15, 15/15, 15/15 across all four runs

## Fix

`pending_gm_beat` is now cleared after narration reads it (single-turn commitment). A `state.set_pending_beat(None)` call was added in `turn.py` after the narrate phase completes, before the extract phase begins. This ensures the beat is not visible in `last_turn_state` for the next turn's checker comparison.
