# Compaction Lifecycle Analysis — T1 to T10

**Date:** 2025-05-26  
**Scope:** Single game save (`saves/default/`) covering turns T1–T10  
**Status:** Completed investigation  

---

## Executive Summary

Compaction **triggered on schedule and successfully produced work** on both occasions. T5 compaction turns T1–T3 into 3 bullets; T10 compaction turns T4–T8 into 5 bullets. Both compaction events are fully recorded in `events.jsonl` with bullet previews, sanitization metadata, token counts, and timing. The COMPACTED block in `chronicle.md` containing T1–T8 bullets was created by these two compaction runs, not by initialization or a prior session.

The `last_compacted_turn` field evolved naturally: started at 0 (game init), updated to 3 after T5 compaction, and updated to 8 after T10 compaction. No observability gap exists.

---

## Evidence Sources

| Source | Size | What It Contains |
|--------|------|------------------|
| `saves/default/events.jsonl` | 876 KB, 12 events | Per-turn state mutations + 2 compaction records with full bullet data |
| `saves/default/state.yaml` | 12 KB | Full persisted game state: meta, inventory, PC, scene, arc, compendium |
| `saves/default/chronicle.md` | 5.3 KB, 34 lines | Narrative history with COMPACTED block (T1–T3 from T5 compact, T4–T8 from T10 compact) + Turn headers for T9 and T10 |
| `ccya/engine/config.py` | Source | EngineConfig defaults: `compact_every=0`, `window_turns=3`, `recent_turns_min=2` |
| `ccya/engine/compactor.py` | 455 lines | Compaction logic: trigger check, turn extraction, LLM call, bullet writing, state update |

---

## Configuration Values

### Defaults (config.py)

```python
compact_every: int = 0          # disabled by default
window_turns: int = 3           # number of turns to retain in window  
recent_turns_min: int = 2       # minimum recent turns before compaction fires
```

### This Game's Values

`compact_every = 5` — inferred from compaction firing on T5 and T10 (`turn % 5 == 0`). All other settings at defaults.

---

## Compaction Events in events.jsonl

Two compaction records exist with full metadata:

### T5 compaction (compacted T1–T3, 3 bullets)
- `compact_start=1, compact_end=3, bullets_count=3`
- `bullets_preview`: first 3 bullets shown
- `sanitization`: 4 recent events compacted, no NPC merges/inventory removes
- `tokens_in=3885, tokens_out=470, ms=10744`

### T10 compaction (compacted T4–T8, 5 bullets)
- `compact_start=4, compact_end=8, bullets_count=5`
- `bullets_preview`: first 3 bullets shown
- `sanitization`: multitool_kit removed from inventory, 5 recent events compacted
- `tokens_in=4790, tokens_out=674, ms=15064`

Both records contain `kind=compaction` with compaction-specific fields: `compact_start`, `compact_end`, `bullets_count`, `bullets_preview`, `sanitization`, `ms`, `tokens_in`, `tokens_out`. They do NOT have `data` or `applied` keys — those are regular turn event fields, not compaction fields.

---

## State.yaml Analysis

### Key Fields (meta section)

| Field | Value | Notes |
|-------|-------|-------|
| `turn` | 10 | Current turn completed |
| `last_compacted_turn` | **8** | Set to 3 after T5 compact (compact_end=3), then to 8 after T10 compact (compact_end=8) |

### State Transitions

- `last_compacted_turn`: not tracked in `applied` mutations (direct state mutation by compactor), so not visible in `applied` arrays. Final value 8 confirms T10 compaction completed successfully.
- No other compaction-related state fields appeared in event `applied` arrays.

### Turns Since Last Compaction (at end of run)

```
T10 - T8 = 2 turns remaining before next potential compaction trigger
```

---

## Chronicle.md Structure

```markdown
## COMPACTED                                          ← One block (appended twice)
- [T1] Clifford Williamson refuses a bribe...         ← From T5 compact
- [T2] Robert Gonzalez reports the attackers are breaching...
- [T3] Robert Gonzalez identifies the attackers as Coalition...

                                                        ← Extra blank line (formatting quirk)
- [T4] Attempting to stabilize the docking clamps...   ← From T10 compact
- [T5] A shot from Low Yield Blaster unjammed...
- [T6] Multitool Kit confirmed non-functional...
- [T7] Visual inspection confirms ship's hull is intact...
- [T8] Player successfully boarded ship...

## Turn 9 — Try to get the ship into the air.         ← Full narrative prose
...

## Turn 10 — Stabilize the ship and get TF out here   ← Full narrative prose
...
```

### Coverage Analysis

| Turns | Format | Count |
|-------|--------|-------|
| T1–T3 | COMPACTED bullets (T5 compact) | 3 |
| T4–T8 | COMPACTED bullets (T10 compact) | 5 |
| T9–T10 | Full Turn headers + narrative prose | 2 |
| **Total** | Complete, no gaps | **10/10** |

No missing turns. The extra blank line between T3 and T4 is a formatting quirk from appending the second compact batch.

---

## Source Code Trace (compactor.py)

### `maybe_compact()` Flow

```
Line 37-39:   if compact_every <= 0 → disabled, return False
Line 42-45:   current_turn == 0 → skip, return False  
Line 47-49:   current_turn % config.compact_every != 0 → not due, return False
Line 51:      last_compacted = meta.last_compacted_turn (read from state)
Line 52:      retain_from = max(1, current - recent_turns_min + 1)
Line 53:      compact_end = retain_from - 1
Line 54:      compact_start = last_compacted + 1
Line 56-62:   if compact_start > compact_end → EARLY RETURN (nothing to do)
Lines 64+:   compact_start <= compact_end → extract turns, call LLM, write bullets
```

### Range Calculation at Each Trigger

**`recent_turns_min = 2`. `last_compacted_turn` starts at 0 (game init), becomes 3 after T5 compact, then 8 after T10 compact.**

| Turn | last_compacted | retain_from | compact_end | compact_start | Range valid? | Action |
|------|---------------|-------------|-------------|---------------|-------------|--------|
| T5 | 0 | max(1,5-2+1)=**4** | 3 | 0+1=**1** | start(1) <= end(3) | **YES — compact T1–T3** |
| T10 | 3 | max(1,10-2+1)=**9** | 8 | 3+1=**4** | start(4) <= end(8) | **YES — compact T4–T8** |

Both triggers passed the range check and proceeded to compaction. The early return at line 56-62 was NOT hit.

### What Happened

1. **T5**: `compact_every=5`, turn 5 % 5 = 0 → trigger. `last_compacted_turn=0`. `compact_end=3`, `compact_start=1`. 1 <= 3 → proceed. Extracts turns 1-3 from chronicle, compacts via LLM into 3 bullets, writes to chronicle.md, sets `last_compacted_turn=3`.
2. **T10**: turn 10 % 5 = 0 → trigger. `last_compacted_turn=3`. `compact_end=8`, `compact_start=4`. 4 <= 8 → proceed. Extracts turns 4-8 from chronicle, compacts via LLM into 5 bullets, appends to COMPACTED block, sets `last_compacted_turn=8`.

---

## Issues Found

### Issue 1: COMPACTED block formatting quirk (low concern)
The LLM bullet output from T10 compaction left an extra blank line between the T1–T3 and T4–T8 sections within the COMPACTED block. This is cosmetic — no content lost.

### Issue 2: last_compacted_turn not tracked in applied mutations (low concern)
The `last_compacted_turn` update is a direct state mutation within the compactor and does not appear in turn `applied` arrays. Verification requires reading state.yaml or compaction event records.

### Issue 3: No early-return event logging (low concern, edge case)
The early return at line 56-62 does not write an event to events.jsonl. If `last_compacted_turn` were ever > retain_from (e.g., in a stretched session), the skipped trigger would be invisible in event logs. Not an issue for this dataset.

---

## Recommendations

### Priority 1: Log early-return compaction triggers (optional)
Consider writing a `kind=compaction, reason="nothing_to_compact"` event when the early return fires, to make skipped triggers visible. Not needed for this dataset but good practice.

### Priority 2: Verify recent_turns_min config
With `recent_turns_min=2`, only T9 (the turn before the compact window) is retained as full prose for T10's compact. This is within design expectations but worth confirming during session planning.

### Priority 3: Add Compaction Health Check (low priority)
Consider a `/health` endpoint reporting `last_compacted_turn`, compaction enabled status, and turns until next trigger. Useful for debugging but not required.

---

## Summary Table: Compaction Lifecycle T1–T10

```
Turn | Trigger? | last_compacted | compact_range | Action Taken                    | Events Recorded
-----|----------|---------------|---------------|---------------------------------|-------------------------------
  1  |          | 0             |               | No trigger                      | -
  2  |          | 0             |               | No trigger                      | -
  3  |          | 0             |               | No trigger                      | -
  4  |          | 0             |               | No trigger                      | -
  5  | YES      | 0             | [1, 3]        | Compacted T1–T3 → 3 bullets     | kind=compaction, bullets_count=3, tokens_in=3885
  6  |          | 3             |               | No trigger                      | -
  7  |          | 3             |               | No trigger                      | -
  8  |          | 3             |               | No trigger                      | -
  9  |          | 3             |               | No trigger                      | -
 10  | YES      | 3             | [4, 8]        | Compacted T4–T8 → 5 bullets     | kind=compaction, bullets_count=5, tokens_in=4790

last_compacted_turn at end of run: 8 (set by T10 compact)
Turns since last compaction: T10 - T8 = 2
```

---

## Conclusion

Compaction is **working correctly**. Both scheduled triggers (T5, T10) successfully compacted their respective turn ranges, wrote bullet summaries to chronicle.md, updated `last_compacted_turn`, and recorded full event data in events.jsonl. The COMPACTED block in chronicle.md containing T1–T8 bullets was created entirely by this run's two compaction events. The only minor issue is a cosmetic blank line between the two bullet batches.

No fundamental bugs, observability gaps, or design flaws were found in the compaction lifecycle for this dataset.
