# Persist

Atomic writes to disk. No LLM calls.

## Event field notes

- `narrate_prompt` is saved at the event level (with `rendered_system`, `rendered_user`, `output`, `context_meta`)
- `ruling_prompt` is saved at the event level (with `rendered_system`, `rendered_user`, `output`, `parse_error`, `context_meta`)
- `storytell_prompt` is NOT saved at the event level — it's available in `extraction.storytell.rendered_user` and `extraction.storytell.rendered_system`
- `pacing_context` is saved at the event level (serialized dict with `directive`, `outcome_hint`, `summary`, `scene_phase`, etc.)
- `state_snapshot` is saved at the event level (full state at end of turn, used by checkers for state-at-turn verification)
- `changes` is saved at the event level (sanitizer output: inventory, player, facts, threads)
- `extraction_context` is NOT saved at the event level — it's an internal dataclass used only during extraction to build the storyteller prompt. Checkers that need this data must parse `extraction.storytell.rendered_user` or use `applied.*`/`state_snapshot`.

### state_snapshot timing

`state_snapshot` is captured at `engine/turn.py:421`, AFTER all turn processing (ruling, narrate, extract, sanitizer, apply_delta). This means:

- Thread resolutions are already reflected (resolved threads moved to `completed_threads`)
- Arc resolutions are already reflected (arc may be resolved with successor)
- Inventory/condition changes are already applied
- Location changes are already applied

**Checker implication:** When validating `arc_resolve.drop_threads` or `thread_resolve` IDs, compare against the **previous** turn's `state_snapshot` (pre-resolution state), not the current turn's. See [`docs/ev/STATE-REFERENCE.md`](../ev/STATE-REFERENCE.md) for the tracking pattern.

### Sanitizer events

When `config.sanitize_every > 0`, the sanitizer runs on turns divisible by `sanitize_every` (default 5). It appends a separate event to `events.jsonl` with `kind=sanitizer` and `turn=N` matching the turn it ran on. This event is written **after** the turn event, so the last event on a sanitizer turn is always the sanitizer event.

**Important for UI panels:** `_recent_turn_metrics()` and `_turn_log_entries()` in `ccya/server/metrics.py` must filter out `kind=sanitizer` events to avoid duplicate turn entries. `_list_saves()` in `ccya/server/routes.py` must also skip sanitizer events when counting turns.

**Important for cancel/delete:** `remove_last_event()` in `ccya/state/chronicle.py` parses the last event's `turn` number and removes **all** events matching that turn number (both turn event and sanitizer event). This prevents orphaned sanitizer events after cancel/delete.

### Cancel and delete workflow

**Cancel** (`/turn/cancel`):
1. Request cancel flag on the running turn
2. Wait for turn to finish (`await_turn_done`)
3. If turn completed (turn number advanced), remove the completed turn's events via `remove_last_event()` and `remove_last_chronicle_turn()`
4. Restore `state_snapshot` from the completed turn's event (pre-sanitizer state)

**Delete** (`/turn/delete`):
1. Load last turn's event to get `state_snapshot`
2. Remove all events for the last turn via `remove_last_event()`
3. Remove the last turn section from `chronicle.md` via `remove_last_chronicle_turn()`
4. Restore `state_snapshot` to `state.yaml`

**Atomicity note:** There is a small window between `remove_last_event()` and `save_state()` where the events are removed but state is not yet restored. If the server crashes in this window, the save is inconsistent. This is considered acceptable — the window is microseconds on fast storage.

## Flowchart

```mermaid
flowchart LR
    classDef storageNode fill:#0f172a,color:#7dd3fc,stroke:#1e40af
    classDef pyNode      fill:#1f2937,color:#9ca3af,stroke:#4b5563

    subgraph IN["Inputs"]
        P1["state (post-apply)"]
        P2["event dict<br>(turn, input, applied, rejected,<br>actions, rules,<br>narrate/extract metrics, extraction<br>with per-stream prompts + attempts,<br>rules_prompt, narrate_prompt,<br>engine_expired_conditions, changes,<br>pacing_context, state_snapshot)"]
        P3["narrative: str"]
        P4["turn number"]
    end

    subgraph WRITES["saves/default/"]
        W1["events.jsonl<br>append — structured event log"]:::storageNode
        W2["state.yaml<br>atomic overwrite — canonical live state"]:::storageNode
        W3["chronicle.md<br>append — '## Turn N — input\n\nnarrative'"]:::storageNode
    end

    READBACK["Feeds Steps 0–2c on the next turn<br>via load_state(), load_last_narration() for recent_turns,<br>prior_history bullets in state.yaml"]:::pyNode

    IN --> W1
    IN --> W2
    IN --> W3
    W3 --> READBACK
    W2 --> READBACK
```
