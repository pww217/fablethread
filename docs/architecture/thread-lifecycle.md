# Thread Lifecycle — Mechanics Reference

## Scope

This doc covers the internal mechanics of arc thread lifecycle management in `turn.py`.
It complements `campaign-arcs.md` (data model, high-level flow)
by detailing the exact rules, order of operations, and edge cases.

## Thread State Management

Thread state is **storyteller-managed**. The LLM explicitly controls urgency and active/dormant state via `thread_update` directives. The engine applies these without enforcement of caps, cooldowns, or silent timers.

## Two Thread Scopes

Threads have a `scope` field (`"scene"` or `"arc"`) that determines narrative treatment:

| Scope | Narrative role | LLM instructions |
|---|---|---|
| `scene` | Short-lived tension tied to current location/NPCs | Tied to current location/NPCs |
| `arc` | Persistent story tension across scenes | Persistent story tension |

Both scopes are managed identically by the engine — no scope-based lifecycle differences.

## Entry Points

Three call sites in `run_turn()` process threads (order matters):

1. **`_apply_thread_updates()`** — apply storyteller's explicit state changes
2. **`_apply_arc_resolve()`** — resolve arc, store in resolved_arcs, create successor
3. **`_apply_thread_resolutions()`** — resolve/fail/abandon → completed

All three run after `apply_delta()` but before `save_state()`.

## Step-by-Step: `_apply_thread_updates()`

Processes `storyteller_result.thread_update` (list of `ThreadUpdate` with `id`, optional `active`, `urgency`, `summary`).

For each ThreadUpdate:
1. Find matching thread by ID in `arc.threads[]`
2. If not found → log WARNING, skip
3. Apply non-None fields (`active`, `urgency`, `summary`) via `model_copy`
4. Log applied changes at INFO level

No caps, cooldowns, or silent timers are enforced. The storyteller decides which threads to update.

## Step-by-Step: `_apply_arc_resolve()`

Processes `storyteller_result.arc_resolve` (optional `ArcResolution` with `resolution`, `visible_goal`, `goal_context`, optional `thematic_question`, `thread_directives`).

1. If `arc_resolve` is None → return None
2. Validate arc from state; if missing/invalid → log WARNING, return None
3. Store current arc in `state["resolved_arcs"]` with `resolved_turn` for TTL tracking
4. Process `thread_directives`:
   - `drop` → remove thread from arc
   - `move_latent` → set `active = False`
   - Threads not mentioned carry over as-is
5. Create successor arc with new `visible_goal`, `goal_context`, inherited `thematic_question`, surviving threads
6. Replace `state["arc"]` with successor

## Step-by-Step: Thread Creation (inline in `run_turn()`)

New threads (`storyteller_result.thread_add`) are gated by:

1. **Pacing gate**: `_pc is None or _pc.gate == "allow"` — blocks escalation when pacing context says so
2. **Key collision**: exact match on thread `key` → reject with WARNING log
3. **Fuzzy auto-merge**: ≥70% token overlap on `key` → update existing thread summary/tags instead of creating new thread

No cooldown or cap checks. The storyteller is trusted to manage thread count.

## Step-by-Step: `_apply_thread_resolutions()`

Processes `storyteller_result.thread_resolve` (list of `ThreadResolution` with `id`, `resolution_state`, `outcome`).

1. Find matching thread by ID in `arc.threads[]`
2. If not found → log warning, skip
3. If found → move to `arc.completed_threads[]`, set `resolution_state`, `outcome`, and `resolved_turn`
4. Deduplicate completed_threads entries: existing ID gets updated, not duplicated

## Step-by-Step: Pacing Context Gate

`_compute_pacing_context()` sets `gate` based on deescalation:

```
gate = "allow" by default
gate = "block_escalate" when deescalate >= 0.5
```

The gate blocks thread creation (in `run_turn()`). The LLM is instructed not to emit `thread_add` when gate != "allow".

## Constants Reference

| Constant | Value | Effect |
|---|---|---|
| `config.resolved_arc_ttl` | 3 (default) | Turns to keep resolved arcs in prompt context |
| `config.completed_thread_ttl` | 3 (default) | Turns to keep completed threads in prompt context |

No active/latent caps, no cooldowns, no expiry timers, no promotion cooldowns.

## Validation Edge Cases

1. **Empty arc state** — No arc in state → log DEBUG, return None (no crash)
2. **Validation failure** — Arc fails Pydantic validation → log WARNING, return None
3. **Unknown thread ID in update** — Log WARNING, skip — does not block valid updates
4. **Unknown resolution ID** — Log WARNING, skip — does not block valid resolutions
5. **Duplicate thread ID in creation** — Checked against existing + completed IDs
6. **Key collision in creation** — Exact match rejects; fuzzy match auto-merges
