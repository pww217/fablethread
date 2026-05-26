# Step 2c — Progress Extract

Extracts quest updates, recent events, and durable NPC compendium changes.

## Flowchart

```mermaid
flowchart LR
    classDef llmNode fill:#0f172a,color:#94a3b8,stroke:#334155
    classDef xstream fill:#4c1d95,color:#ddd6fe,stroke:#7c3aed
    classDef outNode fill:#500724,color:#fbcfe8,stroke:#ec4899

    subgraph IN["Inputs"]
        S1["narrative (from Step 1)"]:::xstream
        S2["_ExtractionContext<br>(comp_this_turn, location,<br>inventory, conditions)<br>built by _build_extraction_context()"]:::xstream
        S3["npc_roster<br>(from build_npc_roster())"]:::xstream
        S4["pacing_context<br>(directive · gate · beat_locked)"]:::xstream
        S5["arc.threads[]<br>(unified scope=scene + scope=arc)"]:::xstream
        S6["rules_outcome"]:::xstream
        S7["intent (from Step 0)"]:::xstream
        S8["recent_turns[-2:]<br>(T-1 + T-2 prior narration<br>for outcome_summary context)"]
    end

    subgraph LLM2C["LLM — storytell_system.j2 + storytell_user.j2"]
        SL["temp: 0.4 · max_retries: 1<br>output: StorytellerResult JSON"]:::llmNode
    end

    subgraph OUT["Outputs — StorytellerResult"]
        O1["thread_advance: list[str]<br>  ids of threads to increment progress"]:::outNode
        O2["thread_resolve: list[ThreadResolution]<br>  id + resolution_state<br>(resolved/failed/abandoned)"]:::outNode
        O3["thread_add: ArcThread | None<br>  new thread, gated by PacingContext.gate"]:::outNode
        O4["recent_events_add: list[RecentEvent]<br>  id, text, turn"]:::outNode
        O5["recent_events_update: list[RecentEventUpdate]<br>  id, text"]:::outNode
        O6["recent_events_remove: list[str]"]:::outNode
        O7["actions: list[str]<br>  exactly 4 suggested player choices"]:::outNode
        O8["outcome_summary: str<br>  1–2 sentence narrative recap"]:::outNode
        O9["gm_beat: GMBeat | None<br>  forward-facing storytelling beat"]:::outNode
    end

    IN --> LLM2C
    LLM2C --> OUT
```

## Always runs

Progress is the post-narration storytelling brain. It always executes every turn (never skipped) and feeds next turn's rules call via `recent_events_add` (durable narrative facts), `thread_advance/resolve/add` (unified thread lifecycle with scope-aware age demotion), and `gm_beat` (forward-facing beats stored in `state.meta.pending_gm_beat`).

## GMBeat schema

```
GMBeat
  type: complication | revelation | opportunity | breathing_room | pressure | twist | setback | escalation | callback
  surface_as: ambient | event | npc_behavior | environmental | player_discovery | item (default: ambient)
  beat_expires_turn: int | None (turn number at which the beat expires; set to turn_no + 2 when stored)
```

## Beat lifecycle

The beat flows through three phases per turn:

**Phase 1 — Pre-narration expiry check.** At the start of each turn, the engine reads `state.meta.pending_gm_beat` from the previous turn. If `beat_expires_turn` is set and the current turn number exceeds it, the beat is nullified. Otherwise it proceeds to narration.

**Phase 2 — Narration consumption.** The beat is passed to the narrator via `_narrate_messages(pending_gm_beat=...)`. The narrator uses the beat's type and surface_as metadata as creative guidance alongside the pacing directive. After narration completes, the pending beat is cleared from state — it is not restored for storyteller consumption.

**Phase 3 — Extraction disposition (inferred).** The storyteller receives no pending beat context in its prompt — it decides beats based solely on current extraction data (scene state, threads, pacing context, band). Unlike the previous architecture, there is no explicit `beat_disposition` field. Instead:
- If Progress emits a new `gm_beat`, it replaces the old one (`state.meta.pending_gm_beat = gm_beat` with `beat_expires_turn = turn_no + 2`)
- If Progress emits nothing and the beat's `expires_at` hasn't passed, the engine preserves the existing beat unchanged (carry)
- The engine stores beats with `beat_expires_turn = turn_no + 2` as a hard TTL ceiling. Beats past their expiry are discarded automatically on load.

## Floor relief injection priority

The floor relief mechanism fires when `_pc.beat_locked=True` AND no beat exists in `state.meta.pending_gm_beat` at extraction completion time (`turn.py:1263`). It injects a `breathing_room` beat with TTL of 3 turns (one more than storyteller-emitted beats' TTL of 2).

Floor relief beats are **fallback only** — they inject a recovery beat when the LLM didn't already provide one. If the storyteller emits any gm_beat during extraction, floor relief does NOT fire because `pending_gm_beat` is already set. The LLM's beat takes priority over Python-injected recovery signals.

```mermaid
flowchart TD
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef decision fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    classDef output fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6

    NARR["Narration clears pending_gm_beat"]:::pyNode
    
    NARR --> STORYLLM["Storytell extracts gm_beat?"]:::decision
    STORYLLM -- "yes" --> STORED["state.meta.pending_gm_beat = storyteller beat<br>TTL: turn_no + 2"]:::output
    STORYLLM -- "no / null" --> NULL["state.meta.pending_gm_beat = None"]:::pyNode
    
    NULL --> FLOOR{"beat_locked == True?"}:::decision
    FLOOR -- yes --> BREATHING["Inject breathing_room beat<br>TTL: turn_no + 3 (extra recovery margin)"]:::output
    FLOOR -- no --> EMPTY["pending_gm_beat remains None<br>No forward-facing beat this turn"]:::pyNode
    
    STORED -. "next turn" .-> NARR
    BREATHING -. "next turn" .-> NARR
```

## Directive-beat alignment

The storyteller prompt (`storytell_system.j2:54-65`) maps each PacingContext directive to recommended beat types (e.g., "Breathe" → breathing_room; "Overwhelm" → pressure/escalation). This alignment is **guidance only** — Python accepts whatever gm_beat the LLM emits with no validation, correction, or override. Design rationale: forcing directive-beat alignment would constrain storytelling flexibility and create brittleness if the LLM makes contextually appropriate but directive-divergent beat choices.
