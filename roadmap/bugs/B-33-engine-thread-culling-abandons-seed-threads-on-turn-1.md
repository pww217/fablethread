---
title: "Engine thread culling abandons seed threads on turn 1"
status: done
completed: 2026-07-06
urgency: 2
size: small
created: 2026-07-06
ticket_id: B-33
labels:
  - threads
  - seed
  - engine
---

## Symptom

Every game session ends up with a thread marked `resolution_state: "abandoned"` on turn 1 or 2. This happens before the player has interacted with the game.

## Evidence

Checked all eval runs across 6 eval groups (2026-06-24 through 2026-07-05). Found **32 abandoned threads resolved on turn 1 or 2**:

- 28 resolved on turn 1
- 1 resolved on turn 2
- 3 resolved on turn 2 (smuggling_network in 0027_noir-1930s_driven_15t)

All 32 have the same outcome string: `"Thread faded from relevance — no narrative activity in X turns."` which is the **engine culling mechanism's** string, not the sanitizer's.

All 32 have `last_updated_turn=None` and `added_turn=None` (or `added_turn=0`), confirming they were seed-generated threads that were never updated.

## Root Cause

**Engine thread culling mechanism** in `ccya/engine/turn_state.py:589-617` fires when `>= 3 dormant threads` exist.

The seed can generate up to 3 dormant threads (4-6 total threads, 1-2 non-dormant per `prepare_seed_system.j2:151-157`). When the seed generates exactly 3 dormant threads, the engine culling mechanism immediately fires on turn 1.

The culling mechanism picks the oldest dormant thread:
```python
to_cull = min(dormant_threads, key=lambda t: t.last_updated_turn or 0)
```

Since seed threads never get `last_updated_turn` set (it's `None`), the `or 0` makes them sort as turn 0 — the "oldest" — causing them to be culled immediately.

## Why This Is Wrong

1. **Premature abandonment:** Threads are abandoned before the player has had a chance to interact with them. This is narratively nonsensical — a thread can't "fade from relevance" in 0 turns.
2. **Mechanical outcome:** The abandoned threads get the mechanical fallback outcome string instead of a narrative justification, which breaks the expected thread lifecycle.
3. **Prompt confusion:** The abandoned thread appears in `completed_threads` on turn 1, giving the player confusing context about threads that never had a chance to develop.

## Proposed Fixes (pick one)

**Option A: Raise the culling threshold.** Change the threshold from `>= 3` to `>= 4` dormant threads. This gives the seed's max 3 dormant threads room without triggering culling. The sanitizer can still cull threads that genuinely need to be dropped.

**Option B: Set `last_updated_turn` on seed threads.** In `seed.py`, set `last_updated_turn` on all seed threads to the seed turn number. This ensures the culling mechanism compares threads fairly (by actual update activity, not by None vs set).

**Option C: Exclude seed threads from culling.** Add a flag or use `added_turn` vs `last_updated_turn` to distinguish seed threads from player-discovered threads. Seed threads that were never touched shouldn't be culled.

**Option D: Reduce seed thread count.** Lower the seed's max dormant threads from 3 to 2, giving a buffer before the culling threshold. This reduces the total thread count which may affect game depth.

## Recommended

**Option A** is the simplest and safest — just change the threshold. The culling mechanism exists as a safety net for genuinely stale threads; giving the seed's dormant threads a chance to develop first is the right behavior.

## Files to Touch

- `ccya/engine/turn_state.py:593` — the `>= 3` threshold
- Optionally `ccya/engine/seed.py` — ensure `last_updated_turn` is set on seed threads
- `docs/architecture/pacing-systems.md` — update the culling mechanism description if threshold changes

## Eval Runs Affected

Checked across 6 eval groups, 32 instances found. Representative runs:
- `2026-06-28_0.30.0-38-gd67ef9ca_d67ef9c/2014_noir-1930s_driven_25t` — political_extortion abandoned at turn 25 (sanitizer, different mechanism)
- `2026-06-28_0.30.0-53-ge6b746b4_e6b746b/2026_golden-piracy_completionist_25t` — crew_unrest abandoned at turn 15 (sanitizer)
- `2026-07-01_0.30.0-81-g75d76eaa_75d76ea/0027_noir-1930s_driven_15t` — smuggling_network abandoned at turn 2 (engine culling)
- Multiple space-western, noir-1930s, golden-piracy, allied-ww2, zombie-survival runs with turn-1 abandonments
