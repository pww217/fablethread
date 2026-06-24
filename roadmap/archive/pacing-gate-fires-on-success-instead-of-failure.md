---
title: "Pacing gate fires on success instead of failure — blocks retroactive thread_add when it should block escalation on failure"
status: canceled
urgency: 2
size: medium
created: 2026-06-13
labels:
  - Improvement
  - World Building
---

## Problem

The pacing gate at `turn.py:1236-1241` blocks storyteller `thread_add` when `gate == "block_escalate"`, but the gate fires on **success** instead of **failure**.

## How it fires (inverted condition)

`turn.py:711-717`:

```python
deescalate = 0.0
if config.thread_deescalate_on_success and outcome.rolled and outcome.band in ("success", "crit_success"):
    if any(t.get("urgency") == "urgent" for t in arc.threads):
        deescalate = 1.0 if crit_success else 0.6
```

`turn.py:567-570`:

```python
gate = "allow"
if deescalate >= 0.5:
    gate = "block_escalate"
```

So the gate fires when the player **succeeds** against urgent threads. This is backwards — it blocks thread creation when the player succeeds, which is exactly when you want to record what the success created narratively.

## How it should fire

The gate's singular purpose is to prevent **unfair piling on** — when the player fails, you don't want to compound the failure with new threads. It should fire on `fail`/`setback`, not `success`.

## Evidence

T10 of cordyceps: player rolls `crit_success`, gate fires, storyteller's `thread_add` (`creature_ambush_threat`) is silently blocked, sanitizer independently adds `creature_ambush` at the same turn with a different ID.

Storyteller `thread_add` is **retroactive** — it describes what already happened in the narration, not what will happen next. The narration is already written. You can't retroactively say "oh, you got a crit, so that ambush didn't happen."

## Fix options

1. **Invert the condition** — fire gate on `fail`/`setback` instead of `success`/`crit_success`
2. **Remove the gate from** `thread_add` — all three storyteller operations (`thread_add`, `thread_update`, `thread_resolve`) are retroactive, not forward-looking
3. **Both** — invert the condition AND remove the gate from `thread_add`, keeping it only on `thread_update` if that's ever forward-looking (it isn't)

## Related

* TICK-44: Storyteller→sanitizer ID mismatch (same root cause — gate blocks storyteller, sanitizer adds different ID)
* `docs/findings/pacing-gate-misdirection.md`
