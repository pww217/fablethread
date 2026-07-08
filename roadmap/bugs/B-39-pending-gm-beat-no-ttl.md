---
title: "pending_gm_beat has no TTL enforcement — persists unchanged across turns"
status: testing
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

## Fix

`pending_gm_beat` is now cleared after narration reads it (single-turn commitment). A `state.set_pending_beat(None)` call was added in `turn.py` after the narrate phase completes, before the extract phase begins. This ensures the beat is not visible in `last_turn_state` for the next turn's checker comparison.
