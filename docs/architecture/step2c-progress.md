# Step 2c — Storytell

Extracts thread updates, arc actions, world state changes, and durable NPC compendium changes.

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
        S8["recent_turns[-1:]<br>(T-1 prior narration)"]:::xstream
        S9["prior_history[:-1]<br>(all history bullets except last,<br>already shown as full text)"]:::xstream
    end

    subgraph LLM2C["LLM — storytell_system.j2 + storytell_user.j2"]
        SL["temp: 0.4 · max_retries: 1<br>output: StorytellerResult JSON"]:::llmNode
    end

    subgraph OUT["Outputs — StorytellerResult"]
        O1["thread_update: list[ThreadUpdate]<br>  id + urgency/active/summary changes"]:::outNode
        O1b["arc_resolve: ArcResolution | None<br>  resolution, visible_goal,<br>goal_context, thread_directives"]:::outNode
        O2["thread_resolve: list[ThreadResolution]<br>  id + resolution_state<br>(resolved/failed/abandoned)"]:::outNode
        O3["thread_add: ArcThread | None<br>  new thread, gated by PacingContext.gate"]:::outNode
        O4["world_state_add: list[WorldStateFact]<br>  id, text, tier"]:::outNode
        O5["world_state_remove: list[str]<br>  ids to remove from persistent tier"]:::outNode
        O6["actions: list[str]<br>  exactly 4 suggested player choices"]:::outNode
        O7["outcome_summary: str<br>  1–2 sentence narrative recap"]:::outNode
        O8["gm_beat: GMBeat | None<br>  forward-facing storytelling beat"]:::outNode
    end

    IN --> LLM2C
    LLM2C --> OUT
```

## Always runs

Progress is the post-narration storytelling brain. It always executes every turn (never skipped) and feeds next turn's rules call via `world_state_add/remove` (persistent world facts), `thread_update/arc_resolve/thread_resolve/thread_add` (storyteller-managed thread lifecycle), and `gm_beat` (forward-facing beats stored in `state.meta.pending_gm_beat`).

## GM Beat

Forward-facing storytelling beats that shape scene progression across turns. Beats are emitted by Storytell (Step 2c), consumed by Narrator (Step 1) the following turn, and managed via a TTL-based lifecycle in `state.meta.pending_gm_beat`.

### GMBeat Schema

```
GMBeat
  type: complication | revelation | opportunity | breathing_room | pressure | twist | setback | escalation | callback
  surface_as: ambient | event | npc_behavior | environmental | player_discovery | item (default: ambient)
  beat_expires_turn: int | None — turn number at which the beat expires; set to turn_no + 2 when stored
```

**Validation:** Only `type` is validated by `StorytellerResult._nullify_invalid_gm_beat` — nullified if falsy. No validation on `surface_as`. Python accepts whatever gm_beat the LLM emits with no correction or override.

### PacingContext Beat Fields

The beat system intersects with pacing via two fields in `PacingContext` (see [step0-ruling](./step0-ruling.md#pacing-context)):

| Field | Type | Meaning |
|-------|------|---------|
| `directive` | str | Includes secondary modifier `"Resolve a Threat"` (appended by semicolon) when `beat_locked=True`. Drives storytell guidance for beat type selection. |
| `beat_locked` | bool | True when dual-trigger relief fired: either `consecutive_pressure_turns >= config.consecutive_pressure_threshold` OR `momentum <= config.momentum_floor`. When locked, `"Resolve a Threat"` is appended to the directive and gate is force-closed (`block_escalate`). Progress MUST emit a breathing_room beat. |

### Beat Lifecycle — Three Phases Per Turn

```mermaid
flowchart TD
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef decision fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    classDef output fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6

    START["Turn begins"]:::pyNode --> EXPIRY{"beat_expires_turn set<br>AND turn_no > expires?"}:::decision
    EXPIY -- yes --> NULLIFIED["Beat nullified (expired)"]:::output
    EXPIRY -- no --> NARRATE["_narrate_messages(pending_gm_beat=...)<br>Narrator uses type + surface_as<br>as creative guidance"]:::pyNode

    NARRATE --> CLEAR["Narration clears pending_gm_beat from state"]:::pyNode

    CLEAR --> STORYLLM{"Storytell emits gm_beat?"}:::decision
    STORYLLM -- "yes" --> STORED["state.meta.pending_gm_beat = storyteller beat<br>beat_expires_turn = turn_no + 2 (TTL: 2 turns)"]:::output

    STORYLLM -- "no / null" --> REPLACE["state.meta.pending_gm_beat = None"]:::pyNode
    REPLACE --> FLOOR{"beat_locked == True?"}:::decision
    FLOOR -- yes --> BREATHING["Inject breathing_room beat<br>beat_expires_turn = turn_no + 3 (TTL: 3 turns)"]:::output

    FLOOR -- no --> EMPTY["pending_gm_beat remains None<br>No forward-facing beat this turn"]:::pyNode
    NULLIFIED -. "next turn" .-> START
    STORED -. "next turn" .-> NARRATE
    BREATHING -. "next turn" .-> NARRATE

    style EXPIRY fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    style STORYLLM fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    style FLOOR fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
```

**Phase 1 — Pre-narration expiry check.** At the start of each turn, the engine reads `state.meta.pending_gm_beat` from the previous turn. If `beat_expires_turn` is set and the current turn number exceeds it, the beat is nullified. Otherwise it proceeds to narration.

**Phase 2 — Narration consumption.** The beat is passed to the narrator via `_narrate_messages(pending_gm_beat=...)`. The narrator uses the beat's `type` and `surface_as` metadata as creative guidance alongside the pacing directive. After narration completes, the pending beat is cleared from state — it is not restored for storyteller consumption.

**Phase 3 — Extraction disposition (inferred).** The storyteller receives no pending beat context in its prompt — it decides beats based solely on current extraction data (scene state, threads, pacing context, band). There is no explicit `beat_disposition` field. Instead:
- If Progress emits a new `gm_beat`, it replaces the old one (`state.meta.pending_gm_beat = gm_beat` with `beat_expires_turn = turn_no + 2`)
- If Progress emits nothing and the beat's TTL hasn't passed, the engine preserves the existing beat unchanged (carry) — though narration already cleared pending state in Phase 2, so this effectively means a new beat is written or None is set

### Floor Relief Injection

The floor relief mechanism fires when `_pc.beat_locked=True` AND no beat exists in `state.meta.pending_gm_beat` at extraction completion time (`turn.py:1263`). It injects a `breathing_room` beat with TTL of 3 turns (one more than storyteller-emitted beats' TTL of 2).

Floor relief beats are **fallback only** — they inject a recovery beat when the LLM didn't already provide one. If Storytell emits any gm_beat during extraction, floor relief does NOT fire because `pending_gm_beat` is already set. The LLM's beat takes priority over Python-injected recovery signals.

### Directive-Beat Alignment

The storyteller prompt (`storytell_system.j2`, pacing context guidance section) maps each PacingContext directive to recommended beat types (e.g., "Breathe" → breathing_room; "Overwhelm" → pressure/escalation). This alignment is **guidance only** — Python accepts whatever gm_beat the LLM emits with no validation, correction, or override. Design rationale: forcing directive-beat alignment would constrain storytelling flexibility and create brittleness if the LLM makes contextually appropriate but directive-divergent beat choices.

### TTL Mechanics Summary

| Source | Default TTL | Expiry Calculation |
|--------|-------------|-------------------|
| Storytell-emitted beat | 2 turns | `beat_expires_turn = turn_no + 2` |
| Floor relief (Python-injected) | 3 turns | `beat_expires_turn = turn_no + 3` (extra recovery margin) |

Beats past their expiry are discarded automatically on load. Both unconditional clears were removed from turn.py — beats survive until replacement, explicit nullification, or TTL expiry. Beat write logic in Progress step only writes if `beat_locked` AND no existing pending_gm_beat exists, preventing overwrites during locked windows.

## Campaign Arc System

The campaign arc system tracks story threads across turns. Thread state is **storyteller-managed** — the LLM explicitly controls urgency and active/dormant state via `thread_update` directives. The engine applies these without enforcement of caps, cooldowns, or silent timers.

### Arc Data Model

```
CampaignArc
  visible_goal: str          — What the PC is trying to achieve
  goal_context: str          — 2–3 sentences explaining why visible_goal matters to this character specifically
  thematic_question: str     — The moral/thematic tension of the arc
  threads: list[ArcThread]   — Unified collection with active flag; storyteller controls state via thread_update
  completed_threads: list[ArcThread] — Resolved/failed/abandoned threads
  resolution: str | None     — Set when arc is resolved via arc_resolve
  last_thread_created_turn: int — Tracks when a thread was last created for pacing

ArcThread
  id: str                    — Unique identifier
  summary: str               — What this thread is about
  scope: Literal["scene", "arc"]  # scene = short-lived tied to current location; arc = persistent story tension
  active: bool = True        # Storyteller-controlled via thread_update
  urgency: Literal["background", "normal", "urgent"] = "normal"  # Storyteller-controlled
  tags: list[str]            — Keywords for engagement matching
  resolution_state: str | None # Set when thread_resolve processes resolved/failed/abandoned
  outcome: str | None        # Set from ThreadResolution.outcome when moved to completed_threads
  resolved_turn: int | None  — Turn when thread was resolved; used for TTL filtering in prompts
  key: str | None            — Optional canonical concept label; enables engine-side dedup auto-merge
```

### Engine-Driven Arc

Thread lifecycle runs in `engine/turn.py` during the extraction phase. Three functions handle thread operations in order:

```mermaid
flowchart TD
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef arcNode fill:#3b0764,color:#e9d5ff,stroke:#7c3aed

    PR["StorytellerResult<br>thread_update: list[ThreadUpdate]<br>arc_resolve: ArcResolution | None<br>thread_resolve: list[ThreadResolution]"]:::pyNode

    subgraph UPDATES["_apply_thread_updates()"]
        U1["For each ThreadUpdate:<br>Find thread by id → apply<br>active/urgency/summary changes"]
    end

    subgraph RESOLVE["_apply_arc_resolve()"]
        R1["Store current arc in resolved_arcs<br>with resolved_turn for TTL tracking"]
        R2["Process thread_directives:<br>drop → remove thread<br>move_latent → active=False"]
        R3["Create successor arc with<br>new visible_goal, goal_context,<br>inherited thematic_question"]
    end

    subgraph RESOLUTIONS["_apply_thread_resolutions()"]
        S1["For each ThreadResolution:<br>Move ArcThread to completed_threads<br>Set resolution_state, outcome, resolved_turn"]
    end

    PR --> UPDATES --> RESOLVE --> RESOLUTIONS

    RESOLUTIONS -- "CampaignArc" --> ARC[arc state in<br>state.yaml]:::arcNode
```

**Pipeline order:** thread updates → arc resolution → thread resolutions.

**Key rules:**
- **Storyteller-controlled:** No caps, cooldowns, or silent timers. The storyteller decides which threads to update via `thread_update` and when to resolve the arc via `arc_resolve`.
- **Arc resolution:** When `arc_resolve` is emitted, the current arc is stored in `state["resolved_arcs"]` with `resolved_turn` for TTL tracking. A successor arc is created with the new `visible_goal`, `goal_context`, and inherited `thematic_question`. Threads not mentioned in `thread_directives` carry over.
- **TTL-based cleanup:** Completed threads and resolved arcs are pruned from prompt context after `completed_thread_ttl` / `resolved_arc_ttl` turns (default 3).

### Arc Context in Narration

The arc state is passed to the narrator via `current_arc` in both system and user prompts. The narrator sees all arc metadata including resolved arcs (TTL-filtered) and completed threads.

When `goal_context` is present on the arc, the narrator treats it as narrative guidance for early turns: ground the player in personal stakes before broad exposition. When resolved arcs are present in the context, the narrator uses them to inform how the new arc relates narratively to what was resolved before — creating continuity across arc transitions.

### Arc System Integration Points

```mermaid
flowchart TD
    classDef stageRules fill:#4c1d95,color:#ddd6fe,stroke:#7c3aed
    classDef stageNarrate fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6
    classDef stageProgress fill:#500724,color:#fbcfe8,stroke:#ec4899
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef arcNode fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    classDef storageNode fill:#0f172a,color:#7dd3fc,stroke:#1e40af

    STATE["state.yaml<br>arc section"]:::storageNode

    subgraph NARRATE["Step 1 — Narrate"]
        N1["_narrate_messages() reads state['arc']<br>→ current_arc_ctx in system prompt"]:::pyNode
    end

    subgraph EXTRACT["Step 2c — Storytell Extract"]
        E1["Storyteller emits<br>thread_update: list[ThreadUpdate],<br>arc_resolve: ArcResolution | None,<br>thread_resolve: list[ThreadResolution],<br>thread_add (gated by PacingContext.gate)"]:::pyNode
    end

    subgraph ARC_ENGINE["Arc Engine (turn.py)"]
        A1["_apply_thread_updates()<br>apply storyteller's explicit state changes"]:::pyNode
        A2["_apply_arc_resolve()<br>resolve arc, store in resolved_arcs,<br>create successor arc"]:::pyNode
        A3["_apply_thread_resolutions()<br>thread_resolve → completed_threads<br>with resolution_state, outcome, resolved_turn"]:::pyNode
        A4["_merge_arc_update()<br>engine arc_delta → state['arc']"]:::pyNode
    end

    STATE --> N1
    N1 --> E1
    E1 --> A1 --> A2 --> A3 --> A4

    A4 --> STATE
```

### Thread Mechanics

#### Two Thread Scopes

Threads have a `scope` field (`"scene"` or `"arc"`) that determines narrative treatment:

| Scope | Narrative role | Engine lifecycle |
|---|---|---|
| `scene` | Short-lived tension tied to current location/NPCs | **Purged on location change** — removed from `arc.threads[]` when player moves to a new location (delta_builder.py:243-248). The LLM creates arc-scoped threads for persistent story lines. |
| `arc` | Persistent story tension across scenes | Persists across location changes. Only removed via `thread_resolve` or `thread_update` with `active=False`. |

#### Entry Points

Three call sites in `run_turn()` process threads in order:
1. **`_apply_thread_updates()`** — apply storyteller's explicit state changes
2. **`_apply_arc_resolve()`** — resolve arc, store in resolved_arcs, create successor
3. **`_apply_thread_resolutions()`** — resolve/fail/abandon → completed

All three run after `apply_delta()` but before `save_state()`.

#### Step-by-Step: `_apply_thread_updates()`

Processes `storyteller_result.thread_update` (list of `ThreadUpdate` with `id`, optional `active`, `urgency`, `summary`).

For each ThreadUpdate:
1. Find matching thread by ID in `arc.threads[]`
2. If not found → log WARNING, skip
3. Apply non-None fields (`active`, `urgency`, `summary`) via `model_copy`
4. Log applied changes at INFO level

#### Step-by-Step: `_apply_arc_resolve()`

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

#### Thread Creation (inline in `run_turn()`)

New threads (`storyteller_result.thread_add`) are gated by:

1. **Pacing gate**: `_pc is None or _pc.gate == "allow"` — blocks escalation when pacing context says so
2. **Key collision**: exact match on thread `key` → reject with WARNING log
3. **Fuzzy auto-merge**: ≥70% token overlap on `key` → update existing thread summary/tags instead of creating new thread

#### Step-by-Step: `_apply_thread_resolutions()`

Processes `storyteller_result.thread_resolve` (list of `ThreadResolution` with `id`, `resolution_state`, `outcome`).

1. Find matching thread by ID in `arc.threads[]`
2. If not found → log warning, skip
3. If found → move to `arc.completed_threads[]`, set `resolution_state`, `outcome`, and `resolved_turn`
4. Deduplicate completed_threads entries: existing ID gets updated, not duplicated

#### Pacing Context Gate

`_compute_pacing_context()` sets `gate` based on deescalation:

```
gate = "allow" by default
gate = "block_escalate" when deescalate >= 0.5
```

The gate blocks thread creation (in `run_turn()`). The LLM is instructed not to emit `thread_add` when gate != "allow".

#### Constants Reference

| Constant | Value (default) | Effect |
|---|---|---|
| `config.resolved_arc_ttl` | 3 | Turns to keep resolved arcs in prompt context |
| `config.completed_thread_ttl` | 3 | Turns to keep completed threads in prompt context |

#### Validation Edge Cases

1. **Empty arc state** — No arc in state → log DEBUG, return None (no crash)
2. **Validation failure** — Arc fails Pydantic validation → log WARNING, return None
3. **Unknown thread ID in update** — Log WARNING, skip — does not block valid updates
4. **Unknown resolution ID** — Log WARNING, skip — does not block valid resolutions
5. **Duplicate thread ID in creation** — Checked against existing + completed IDs
6. **Key collision in creation** — Exact match rejects; fuzzy match auto-merges
