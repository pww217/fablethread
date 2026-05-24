# Thread Lifecycle — Mechanics Reference

## Scope

This doc covers the internal mechanics of arc thread lifecycle management in `turn.py`.
It complements `campaign-arcs.md` (data model, narrator arc updates, high-level flow)
by detailing the exact rules, order of operations, constants, and edge cases.

## Two Thread Scopes

Threads have a `scope` field (`"scene"` or `"arc"`) that determines lifecycle treatment:

| Scope | Active management | Expiration | LLM instructions |
|---|---|---|---|
| `scene` | None — no engine processing | Via scene age rules (indirect) | Tied to current location/NPCs |
| `arc` | Full lifecycle: advance, demote, promote, complete | 5 silent turns → demote to latent | Persistent story tension |

Scene-scoped threads exist in `arc.threads[]` alongside arc-scoped threads. They are
excluded from engine processing by the `scope == "arc"` filter at `turn.py:203-205`.

## Entry Points

Three call sites in `run_turn()` process threads (order matters):

1. **`_apply_thread_signals()`** — advance, expire, demote, promote, complete
2. **`_apply_thread_resolutions()`** — resolve/fail/abandon → completed
3. **Inline thread_add logic** — create new threads (gated by pacing context)

All three run after `apply_delta()` but before `save_state()`.

## Step-by-Step: `_apply_thread_signals()`

### Phase A — Advance or Expire (per active thread)

For each arc-scoped active thread:

| Condition | Action |
|---|---|
| ID in `storyteller_result.thread_advance` | `progress += 1`, update `last_seen_turn = turn_no` |
| Not advanced AND `turn_no - last_seen_turn >= _EXPIRE_SILENT_TURNS` (5) | Demote: `active = False`, `last_seen_turn = None` |
| Not advanced AND still within expiry window | Carry forward unchanged |
| Progress >= `config.thread_completion_threshold` (default 3) | Move to `completed_threads[]` |

All three outcomes (advance, demote, unchanged) accumulate into `still_active[]`.
Advancing a thread is treated as a mutation. Only threads NOT advanced AND expired
are demoted — normal carry-forward does not count as a mutation.

### Phase B — Enforce Latent Cap

After Phase A, the post-demotion latent count is:

```
latent_count = len(latent_by_id) + len(demoted_to_latent)
```

If `latent_count > _LATENT_THREAD_CAP (4)`, excess threads are dropped from
the **newly demoted** pool (oldest by `added_turn` first — `added_turn=9999`
sentinel sorts unset last). Promotions in Phase D may further reduce the count,
so this cap is conservative (may drop more than strictly necessary).

### Phase C — Rebuild Thread List

Active threads (`really_still_active`), surviving newly-demoted threads, and
unprocessed threads (scene-scoped, already-completed) are merged into a single
`all_updated_arc_threads` list.

### Phase D — Immediate Promotion (unknown advanced_ids)

Any ID in `storyteller_result.thread_advance` that is NOT currently in `active_by_id`
but IS in `latent_by_id` is promoted immediately: `active = True`, `progress = 0`,
`last_seen_turn = turn_no`.

This bypasses the cooldown check — it is the primary path for activating a
latent thread. The LLM activates it by listing it in `thread_advance`.

### Phase E — Cooldown-Gated Promotion

Promotion of eligible latent threads that were NOT explicitly advanced by the LLM:

**Conditions (both must be met):**

1. `turn_no - arc_last_promotion_turn >= _PROMOTION_COOLDOWN_TURNS (3)` OR no active threads exist
2. Available slot: `_ACTIVE_THREAD_CAP (3) - len(really_still_active) > 0`

**Eligibility (latent thread must satisfy ALL):**
- Not already active
- Not already completed
- `unlock_if` is empty/falsy (if set, thread is locked and won't auto-promote)

**Selection:** Eligible threads sorted by `added_turn` (oldest first). Up to
`available_slots` are promoted. Sets `arc_last_promotion_turn = turn_no`.

This path fires at most once per 3 turns and fills gaps left by the
LLM's thread_advance omissions.

## Step-by-Step: Thread Creation (inline in `run_turn()`)

New threads (`storyteller_result.thread_add`) are **not** handled inside
`_apply_thread_signals()`. They are gated by three checks in sequence:

```
gate_ok = _pc is None or _pc.gate == "allow"
cooldown_ok = last_creation_turn is None or
              (current_turn - last_creation_turn >= config.thread_creation_cooldown)
cap_ok = active_count < _ACTIVE_THREAD_CAP (3)
```

| Gate | Cooldown | Cap | Result |
|---|---|---|---|
| ✅ | ✅ | ✅ | Thread created, `last_thread_creation_turn` updated |
| ❌ | — | — | Logged: "blocked by pacing gate" |
| ✅ | ❌ | — | Logged: "blocked by cooldown" |
| ✅ | ✅ | ❌ | Logged: "blocked by active cap" |

Scene-scoped threads are silently ignored (they are handled by age rules, not
engine lifecycle).

## Step-by-Step: `_apply_thread_resolutions()`

Processes `storyteller_result.thread_resolve` (list of `ThreadResolution`
with `id`, `resolution_state`). For each resolution:

1. Find matching thread by ID in `arc.threads[]`
2. If not found → log warning, skip
3. If found → move to `arc.completed_threads[]`, set `resolution_state`
4. Deduplicate completed_threads entries: existing ID gets updated, not duplicated

## Step-by-Step: Pacing Context Gate

`_compute_pacing_context()` at `turn.py:594` sets `gate` based on deescalation:

```
gate = "allow" by default
gate = "block_escalate" when deescalate >= 0.5
```

The gate is exclusively Python-computed — the LLM never sets it directly.
`block_escalate` blocks both thread creation (in `run_turn()`) and thread
escalation (pacing context sent to Progress Extract, but the LLM is instructed
not to emit thread_add when gate != "allow").

## Constants Reference

| Constant | Value | Location | Effect |
|---|---|---|---|
| `_ACTIVE_THREAD_CAP` | 3 | `turn.py:149` | Max concurrent active threads |
| `_LATENT_THREAD_CAP` | 4 | `turn.py:152` | Max latent (inactive) threads |
| `_EXPIRE_SILENT_TURNS` | 5 | `turn.py:155` | Turns of silence before demotion |
| `_PROMOTION_COOLDOWN_TURNS` | 3 | `turn.py:158` | Min turns between auto-promotions |
| `config.thread_completion_threshold` | 3 (default in config.yaml) | config | Progress needed to auto-complete |
| `config.thread_creation_cooldown` | configurable | config | Min turns between LLM thread creation |

## Validation Edge Cases

1. **Empty arc state** — No arc in state → log DEBUG, return None (no crash)
2. **Validation failure** — Arc fails Pydantic validation → log WARNING, return None
3. **Unknown resolution ID** — Log WARNING, skip — does not block valid resolutions
4. **Latent cap excess** — Drops oldest newly-demoted; continues without error
5. **Active cap exceeded in thread_add** — Blocks creation; no rollback needed
6. **Duplicate thread ID in creation** — Checked against existing + completed IDs
