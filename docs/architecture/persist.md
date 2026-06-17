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

`state_snapshot` is captured at `engine/turn.py:1423`, AFTER all turn processing (ruling, narrate, extract, sanitizer, apply_delta). This means:

- Thread resolutions are already reflected (resolved threads moved to `completed_threads`)
- Arc resolutions are already reflected (arc may be resolved with successor)
- Inventory/condition changes are already applied
- Location changes are already applied

**Checker implication:** When validating `arc_resolve.drop_threads` or `thread_resolve` IDs, compare against the **previous** turn's `state_snapshot` (pre-resolution state), not the current turn's. See [`docs/ev/STATE-REFERENCE.md`](../ev/STATE-REFERENCE.md) for the tracking pattern.

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
