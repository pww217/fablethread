# Arc-Thread Conflation — Eval Findings

## Problem

The LLM resolves arcs every 1-6 turns when thread IDs change, ignoring the prompt's
"target cadence: 8-15 turns" guidance. Arc resolution fires on thread lifecycle events
rather than genuine chapter-ending moments.

## Evidence

### WW2 NEW (aggressive persona, 25 turns)
- Turn 3: arc_resolve (5 turns after seed, too early)
- Turn 5: arc_resolve (2 turns later)
- Turn 9: arc_resolve (4 turns later)
- Turn 15: arc_resolve (6 turns later)
- Goal barely changes: "Evacuate the wounded and secure the captured intelligence before the enemy patrol closes in" → "Evacuate the wounded and secure the captured intelligence."

### Rim NEW (driven persona, 25 turns)
- Turn 10: arc_resolve (9 turns, acceptable)
- Turn 13: arc_resolve (3 turns later)
- Turn 14: arc_resolve (**1 turn later**)
- Turn 15: goal_update (mid-arc shift, good)

### WW2 OLD (driven persona, 25 turns)
- Turn 15: arc_resolve with **empty fields** (resolution="", visible_goal="")
- Turn 19-21: 3 arc_resolves in 3 turns (clustered)
- Goals: 4 changes in 4 turns (rapid churn)

### Rim OLD (explorer persona, 25 turns)
- Turn 15: arc_resolve (14 turns, good)
- Turn 20: arc_resolve (5 turns later)

## Root Cause

**`drop_threads` only exists inside `arc_resolve`.** The LLM has no way to drop stale
threads without resolving an arc. It's forced to conflate thread management with chapter
ending.

The prompt says:
> `arc_resolve` ends the current narrative chapter. Emit when: all arc threads are resolved/moot; the story's center of gravity has fundamentally shifted; the core conflict was decisively won or lost; the arc has coasted 8+ turns on the same goal.

But the LLM sees: "I need to drop thread A and add thread B" → "arc_resolve with drop_threads: [A], new_threads: [B]" → arc resets with same goal.

### The mechanics force conflation

1. LLM emits `arc_resolve` with `drop_threads: ["old_thread"]` and `new_threads: [{"id": "new_thread"}]`
2. `_apply_arc_resolve()` drops the old thread, adds the new one, creates a new `CampaignArc`
3. The new arc has the same `visible_goal` (or a slightly reworded version)
4. Cycle repeats 1-5 turns later

The LLM is responding rationally to the prompt structure — it's using arc_resolve as
the only available thread management tool.

## Arcs vs Threads

They're related but distinct:

- **Threads**: tracking specific tensions (patrol_encirclement, secure_intelligence_extraction)
- **Arc**: the chapter-level goal (Evacuate wounded, secure intelligence)

The thread is a *subset* of the arc. When the thread resolves, the arc doesn't necessarily
end — it just loses one tension point.

Mechanically they should be:
- Threads resolve independently when their tension dissipates
- Arcs resolve independently when the core goal genuinely shifts or chapter ends
- The arc contains threads, but thread lifecycle doesn't drive arc lifecycle

The prompt tries to enforce this separation but fails because the mechanics force conflation.

## Proposed Fixes

### 1. Independent thread resolution (highest leverage)

Currently:
- `thread_resolve` only marks a thread as resolved in state
- `drop_threads` only exists inside `arc_resolve`
- To *actually* remove a thread from state, you must resolve an arc

Change: let `thread_resolve` with `drop: true` actually remove the thread from the arc
without requiring arc resolution.

### 2. Arc resolution as a separate signal

Currently: `arc_resolve` = "chapter ending + thread management"

Change: add `chapter_end: true` as a separate field. Arc resolution would only fire when:
- `chapter_end: true` is explicitly set, AND
- One of: core goal shifted, 8+ turns passed, all threads resolved

The LLM would use `thread_resolve` for thread lifecycle and `chapter_end` for arc lifecycle.

### 3. Engine-enforced arc duration minimum

Not a hard minimum, but: when `_apply_arc_resolve` runs, check
`turn_no - arc.last_arc_resolve_turn < 8`. If so, log a warning but still apply.
The warning would surface in evals as a signal that the LLM is resolving too early.

## Impact

- Arc state resets every 1-6 turns, losing thread history
- Goals barely change across arc resets (just shortening/rewording)
- Thread resolution rate drops to 0% (both new evals) because arcs keep resetting
- The game feels like it's constantly restarting its chapter without actually ending

## Related

- Prompt: `ccya/prompts/storytell_system.j2` lines 42-46 (arc resolution guidance)
- Engine: `ccya/engine/turn.py:248` (`_apply_arc_resolve`)
- Model: `ccya/models.py:470` (`StorytellerResult` — `arc_resolve` field)
- Eval: `ccya/ev/checkers/arc_resolution_validity.py`
