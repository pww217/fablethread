# Pacing Gate Misdirection

## The Bug

At T10 of cordyceps, the storyteller emits `thread_add` with id `creature_ambush_threat`, but this thread never appears in any `state_snapshot.arc.threads`. The sanitizer independently adds `creature_ambush` at the same turn, which IS what the game uses from T11 onwards.

## What Actually Happened at T10

1. **Ruling phase:** Player rolls `crit_success` (final_total=13, dice=12, stat_mod=1). There are urgent threads active (`smuggling_run_execution`).
2. **De-escalation fires:** `deescalate = 1.0` because `crit_success` + urgent threads exist.
3. **Gate fires:** `deescalate >= 0.5` → `gate = "block_escalate"`.
4. **Narration:** Describes the creature ambush — the ambush already happened in the fiction.
5. **Storyteller extraction:** Emits `thread_add` with id `creature_ambush_threat` (retroactive — this is what the narration just described).
6. **Gate check at `turn.py:1236-1241`:** `gate_ok = False` because `gate == "block_escalate"`. The storyteller's `thread_add` is silently blocked — never applied to in-memory state.
7. **Sanitizer runs at T10:** Reads in-memory state (post-T10, pre-sanitizer). Sees no creature_ambush thread. Sanitizer's LLM independently decides to add `creature_ambush` (different ID, no `_threat` suffix).
8. **Result:** `creature_ambush_threat` is an orphan reference in extraction output only. `creature_ambush` is what the game actually uses from T11 onwards.

## The Root Cause: Gate Applied to Retroactive Operations

The pacing gate at `turn.py:1236-1241` blocks `thread_add` when `gate == "block_escalate"`. But `thread_add` is **retroactive** — it describes what *already happened* in the narration, not what will happen next.

The storyteller prompt says: "Only emit when this turn's events changed the thread's trajectory." This is post-mortem analysis, not forward planning. The narration is already written. You can't retroactively say "oh, you got a crit, so that ambush didn't happen."

## How the Gate Was Designed vs How It Works

### Designed intent (from `turn.py:104` comment)
> "Progress may only add threads when allow"

The gate is supposed to prevent "unfair piling on" — when the player fails, you don't want to compound the failure with new threads.

### How it actually fires (from `turn.py:711-717`)
```python
deescalate = 0.0
if config.thread_deescalate_on_success and outcome.rolled and outcome.band in ("success", "crit_success"):
    if any(t.get("urgency") == "urgent" for t in arc.threads):
        deescalate = 1.0 if crit_success else 0.6
```

`deescalate` fires when the player **succeeds** against urgent threads. Then at `turn.py:567-570`:
```python
gate = "allow"
if deescalate >= 0.5:
    gate = "block_escalate"
```

So the gate fires on **success**, not failure. This is backwards — it's blocking thread creation when the player succeeds, which is exactly when you'd want to record what the success/escalation created narratively.

## The Inversion Bug

The condition is inverted. The gate should fire on **failure**, not success:

- **When player fails/setbacks:** The narration already describes the consequence. Don't compound it with "and also, this created a new thread." This is when you want to block escalation.
- **When player succeeds:** The narration describes what the success created. You want to record this in threads. This is when you want to allow thread creation.

The current logic says: "You succeeded, so you're de-escalating, don't add threads." But de-escalation is about momentum, not about thread creation. A critical success against urgent threads means the player resolved tension — you want to record that in threads, not block it.

## What the Gate Should Do

The gate's singular purpose should be: **prevent future escalation and unfair piling on.**

This means it should fire when the player **fails** against urgent threads, not when they succeed. The condition at `turn.py:712` should check for `fail`/`setback` bands, not `success`/`crit_success`.

## Related Bug: Storyteller→Sanitizer ID Mismatch

Even if the gate were fixed, there's still a coordination problem: the storyteller and sanitizer are two independent LLM calls making two independent decisions about thread IDs at the same turn. If both fire, they could create duplicate threads with different IDs (`creature_ambush_threat` vs `creature_ambush`).

The sanitizer should be aware of the storyteller's `thread_add` (or at least its ID) so it can check for collisions before adding new threads. This is a separate issue from the gate misdirection, but it's visible in this same event.

## Files Involved

- `ccya/engine/turn.py:711-717` — deescalate logic (inverted condition)
- `ccya/engine/turn.py:567-570` — gate assignment based on deescalate
- `ccya/engine/turn.py:1236-1241` — storyteller thread_add blocked by gate
- `ccya/engine/thread_sanitizer.py:441-463` — sanitizer adds new threads (no awareness of storyteller's blocked thread_add)
- `ccya/engine/turn.py:104` — gate type hint says `block_escalate` but fires on success, not escalation

## Evidence

- Save: `saves/cordyceps-year-twenty-2026-06-11/events.jsonl`
- T10 pacing_context: `{"directive": "Scene Imperative", "gate": "block_escalate", "outcome_hint": "advance"}`
- T10 storyteller output: `thread_add.id = "creature_ambush_threat"` (in `extraction.storytell.output`)
- T10 sanitizer output: `threads_added = ["creature_ambush"]` (in `sanitizer` event)
- `creature_ambush_threat` never appears in any `state_snapshot.arc.threads`
- `creature_ambush` appears in `state_snapshot.arc.threads` from T11 onwards
