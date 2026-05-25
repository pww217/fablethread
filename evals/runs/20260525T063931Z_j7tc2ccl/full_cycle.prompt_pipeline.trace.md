# Engine Design Reference (EVAL_CONTEXT from ARCHITECTURE.md)

---

# ENGINE DESIGN REFERENCE (read this first — it is what the engine is supposed to do)

The following is extracted from the project's architecture subdocuments under docs/architecture/. It defines the 5-pipeline engine you are judging. Use it to understand which pipeline owns which mechanic, where data flows, and what the design intent is. When you find something the implementation does that contradicts this design, call it out as a mechanical failure.

## OVERVIEW



CCYA is a local-LLM-backed text RPG engine. Every player turn drives a five-step
pipeline (Rules → Narrate → Scene Extract → State Extract → Progress Extract) with
a pure-Python validation+persist tail. Two additional LLM pipelines handle new-game
creation: **Character Creation** (static packs) and **Generate Seed** (dynamic packs).

## Pipeline Diagram

```mermaid
flowchart TD
    classDef stageRules    fill:#4c1d95,color:#ddd6fe,stroke:#7c3aed
    classDef stageNarrate  fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6
    classDef stageScene    fill:#064e3b,color:#a7f3d0,stroke:#10b981
    classDef stageState    fill:#451a03,color:#fde68a,stroke:#f59e0b
    classDef stageProgress fill:#500724,color:#fbcfe8,stroke:#ec4899
    classDef storageNode   fill:#0f172a,color:#7dd3fc,stroke:#1e40af
    classDef pyNode        fill:#1f2937,color:#9ca3af,stroke:#4b5563

    USER["user_input"]

    subgraph ENGINE["engine — run_turn()"]
        STEP0["Step 0<br>Ruling/Intent (LLM)"]:::stageRules
        DICE["Dice Resolution<br>(Python)"]:::pyNode
        STEP1["Step 1<br>Narrate (LLM)"]:::stageNarrate
        STEP2A["Step 2a<br>Scene Extract (LLM)"]:::stageScene
        STEP2B["Step 2b<br>State Extract (LLM)"]:::stageState
        STEP2C["Step 2c<br>Storytell (LLM)"]:::stageProgress
        VALIDATE["Validate + Apply Delta<br>(Python)"]:::pyNode
    end

    subgraph PERSISTENCE["persistence"]
        STATE["state.yaml<br>(canonical live state)"]:::storageNode
        CHRONICLE["chronicle.md<br>(narrative history)"]:::storageNode
        EVENTS["events.jsonl<br>(structured turn log)"]:::storageNode
    end

    USER --> STEP0
    STEP0 -- "IntentEnvelope + RulesOutcome" --> DICE
    DICE -- "PacingContext" --> STEP1
    STEP1 --> STEP2A & STEP2B & STEP2C
    STEP2A & STEP2B & STEP2C --> VALIDATE
    VALIDATE --> PERSISTENCE
    PERSISTENCE -- "load_state()<br>chronicle_tail<br>recent_turns" --> ENGINE
```

## Pipeline Quick Reference

| Step | Docs | When it runs | Key inputs | Key outputs | Mechanics it owns |
|---|---|---|---|---|---|
| **Step 0 — Ruling/Intent** | [step0-ruling](./step0-ruling.md) | Every turn (always) | `state.pc`, `state.location`, `recent_turns[-1:]`, `user_input` | `IntentEnvelope`, `RulesOutcome` | Intent classification, dice roll resolution (2d6 + stat + cond − diff → band), difficulty selection, anti-declare-outcome enforcement. |
| **Step 1 — Narrate** | [step1-narrate](./step1-narrate.md) | Every turn (always, streamed) | Full `state`, `chronicle_tail`, `recent_turns`, `pacing_context`, `pending_gm_beat`, `npc_roster` (tiered), `world_factions/locations`, `compendium_bios` | `narrative` (prose) | Prose generation, dice-band binding, GM-beat consumption. Tone shaped by `PacingContext.directive`. |
| **Step 2a — Scene Extract** | [step2a-scene](./step2a-scene.md) | Every turn (always) | `narrative`, `state.pc/location`, `npc_roster` (tiered), conditions, known_characters (LRU compendium) | `SceneExtractResult`: scene_tags, tagline, location_change, npc_add/remove/update, compendium_npc_update | NPC presence, location changes, scene tags, durable NPC compendium identity. |
| **Step 2b — State Extract** | [step2b-state](./step2b-state.md) | Every turn (always) | `narrative`, `state.pc/location/inventory`, conditions | `StateExtractResult`: inventory_add/remove/update, pc_condition_add/remove | Inventory delta accuracy, condition lifecycle. |
| **Step 2c — Storytell** | [step2c-progress](./step2c-progress.md) | Every turn (always) | `narrative`, `_ExtractionContext`, pacing_context, arc.threads[], recent_turns[-2:], band, npc_roster (tiered) | `StorytellerResult`: thread_advance/resolve/add, gm_beat, recent_events_add/update/remove, actions, outcome_summary | Unified thread lifecycle, beat disposition inference, durable history events. |

After Step 2c: results merge into a `StateDelta`, the validator checks constraints
(e.g. `inventory_remove` IDs exist), `apply_delta()` mutates state in-place, and the
turn is persisted. The next turn's Step 0 reads the new `state.yaml` plus `events.jsonl`.

## Subsystem Docs

| Subsystem | Doc | What it covers |
|---|---|---|
| **Step 0 — Ruling** | [step0-ruling](./step0-ruling.md) | Intent classification, dice resolution flowchart |
| **Step 1 — Narrate** | [step1-narrate](./step1-narrate.md) | Streaming narration pipeline with all context inputs |
| **Step 2a — Scene Extract** | [step2a-scene](./step2a-scene.md) | Location changes, NPC presence, scene tags |
| **Step 2b — State Extract** | [step2b-state](./step2b-state.md) | Inventory and condition extraction |
| **Step 2c — Storytell** | [step2c-progress](./step2c-progress.md) | Thread lifecycle, GMBeat schema, beat lifecycle (3 phases) |
| **PacingContext** | [pacing-context](./pacing-context.md) | Struct definition, computation flowchart, wiring to Narrator/Progress |
| **Delta → Validate → Apply** | [delta-validate](./delta-validate.md) | StateMerge schema, validation rules, apply_delta mutations |
| **Persist** | [persist](./persist.md) | Atomic writes (events.jsonl, state.yaml, chronicle.md), readback |
| **Cross-Pipeline Data Flow** | [cross-pipeline](./cross-pipeline.md) | Full inter-step data flow diagram |
| **Campaign Arcs** | [campaign-arcs](./campaign-arcs.md) | Arc data model (unified threads), engine-driven lifecycle, narrator-driven updates, integration points |
| **Out-of-Band Pipelines** | [out-of-band](./out-of-band.md) | Character Creation pipeline, Generate Seed pipeline, turn viewer status colors |
| **Narration UI** | [narration-ui](./narration-ui.md) | Main game interface: SSE streaming, HTMX sidebar refresh, Alpine.js state machine |
| **Turn Viewer UI** | [turn-viewer-ui](./turn-viewer-ui.md) | Pipeline debug UI: turn cards, stage inspector, diff panel, live updates |
| **Eval Harness** | [eval-harness](./eval-harness.md) | Scenario runner, LLM judges, auto-checkers, REPORT.md generation |

## Key Models Glossary

### Core Result Types

- **IntentEnvelope**: `intent`, `intent_verb`, `target`, `check.required`, `check.skill`, `check.difficulty`
- **RulesOutcome**: `rolled`, `skill`, `difficulty`, `stat_value`, `stat_mod`, `diff_mod`, `cond_mod`, `dice`, `raw_total`, `final_total`, `band`, `directive`, `intent`, `intent_verb`
- **SceneExtractResult**: `scene_tags`, `scene_tagline`, `location_change`, `npc_add/remove/update`, `compendium_npc_update`
- **StateExtractResult**: `inventory_add/remove/update`, `pc_condition_add/remove`
- **StorytellerResult**: `thread_advance`, `thread_resolve`, `thread_add`, `gm_beat`, `recent_events_add/update/remove`, `actions`, `outcome_summary`
- **SeedEnvelope**: `seed_state: GameState`, `opening_narrative`, `actions`, `arc: CampaignArc` (includes `goal_context`, unified `threads[]`, `completed_threads[]`), `pc_drive`

  The seed owns first-turn emotional framing, not just world and arc scaffolding. It generates `goal_context` (character-specific stake), NPC `relation` fields (narrative job relative to PC), and action text written from the PC's voice and scene pressure — ensuring the opening feels personal and motivated from the start.

### PacingContext (see [pacing-context](./pacing-context.md))

```
PacingContext:
  directive: str           # "" | "Breathe" | "Pressure" | "Overwhelm" | "Tension" | "Resolve a Threat" | "Threat Pressure" (may include "; Combat Fatigue" secondary)
  beat_locked: bool        # True: floor relief fired — Progress MUST emit breathing_room beat and gate is force-closed
  gate: str                # "block_escalate" | "allow" (controls thread_add)
  summary: str             # human-readable log string, never sent to LLM
```

### GMBeat (see [step2c-progress](./step2c-progress.md))

```
GMBeat
  type: complication | revelation | opportunity | breathing_room | pressure | twist | setback | escalation | callback
  surface_as: ambient | event | npc_behavior | environmental | player_discovery | item (default: ambient)
  beat_expires_turn: int | None (turn number at which the beat expires; set to turn_no + 2 when stored)
```

### CampaignArc (see [campaign-arcs](./campaign-arcs.md))

```
CampaignArc
  visible_goal: str           — What the PC is trying to achieve
  goal_context: str           — 2–3 sentences explaining why visible_goal matters to this character specifically
  thematic_question: str      — The moral/thematic tension of the arc
  pc_drive: str               — The PC's personal motive/reason for being in this situation
  hidden_truths: list[str]    — Story secrets the narrator knows but must not reveal in prose
  discovered_truths: list[str] — Truths the player has uncovered
  threads: list[ArcThread]    — Unified collection with active flag; replaces old active/latent split
  completed_threads: list[ArcThread] — Resolved/failed/abandoned threads

ArcThread (unified)
  id, summary, scope ("scene"|"arc"), active: bool = True
  urgency ("background"|"normal"|"urgent")
  tags: list[str], progress: int (0..3)
  resolution_state: str | None
  last_seen_turn: int | None, added_turn: int | None
  unlock_if: str | None — condition string; thread is only promotable when empty/falsy
  promotes: list[str] — threads this one can promote to when completed
```

### StateDelta (see [delta-validate](./delta-validate.md))

Merges all three extraction results. Contains `scene_tags`, `location_change`, `npc_add/remove/update`, `thread_advance/resolve/add`, `inventory_add/remove/update`, `pc_condition_add/remove`, `recent_events_add/update/remove`. Note: `gm_beat` is NOT in StateDelta — written directly to `state.meta.pending_gm_beat`.

---


## campaign-arcs



The campaign arc system tracks story threads and truth discovery across turns. It has two execution paths: **engine-driven** (thread lifecycle with 5-turn expiry for silent threads) and **narrator-driven** (truth discovery, goal updates).

## Arc Data Model

```
CampaignArc
  visible_goal: str          — What the PC is trying to achieve
  goal_context: str          — 2–3 sentences explaining why visible_goal matters to this character specifically; inner cost or pressure that makes it emotionally loaded
  thematic_question: str     — The moral/thematic tension of the arc
  pc_drive: str              — The PC's personal motive/reason for being in this situation; expressed indirectly
  hidden_truths: list[str]   — Story secrets the narrator knows but must not reveal in prose
  discovered_truths: list[str] — Truths the player has uncovered (subset of hidden_truths)
  threads: list[ArcThread]   — Unified collection replacing active_threads + latent_threads split. Each thread has scope ("scene" or "arc") and active flag set by Python age rules, not LLM.
  completed_threads: list[ArcThread] — Resolved/failed/abandoned threads; resolution_state preserved for narrative context

ArcThread (unified)
  id: str                    — Unique identifier
  summary: str               — What this thread is about
  scope: Literal["scene", "arc"]  # scene = short-lived tied to current location; arc = persistent story tension
  active: bool = True        # False = dormant/latent; set by Python age rules (not LLM)
  urgency: Literal["background", "normal", "urgent"] = "normal"
  tags: list[str]            — Keywords for engagement matching
  progress: int              — 0..3 (incremented by thread_advance)
  resolution_state: str | None # Set when thread_resolve processes resolved/failed/abandoned; preserved on completed threads
  last_seen_turn: int | None # For age-based active/dormant demotion in Python
  added_turn: int | None     # Python-managed lifecycle tracking
  unlock_if: str | None      # Condition string; thread is only promotable when empty/falsy
  promotes: list[str]        # Threads this one can promote to when completed
```

**Key change from previous architecture:** `scene_pressure[]` and the split between `active_threads` / `latent_threads` are merged into a single `arc.threads[]`. The engine manages thread lifecycle via `_apply_thread_signals()`: age-based demotion (`active: True → False`) replaces the old active/latent migration logic, with silent threads (not listed in `thread_advance` for 5+ turns) being demoted to dormant state.

## Engine-Driven Arc: Unified Thread Lifecycle

Thread lifecycle runs in `engine/turn.py` during the extraction phase, after `apply_delta()` but before narration arc_update merge. Two functions handle the unified thread operations:

```mermaid
flowchart TD
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef arcNode fill:#3b0764,color:#e9d5ff,stroke:#7c3aed

    PR["StorytellerResult<br>thread_advance: list[str]<br>thread_resolve: list[ThreadResolution]"]:::pyNode

    subgraph SIGNALS["_apply_thread_signals() + _apply_thread_resolutions()"]
        S1["For each ID in thread_advance:<br>If ArcThread exists → progress +1,<br>last_seen_turn = turn_no"]
        S2["Check silent threads (not in<br>thread_advance):<br>If last_seen_turn < turn_no - 5 → demote active=False"]
        S3["Auto-complete: progress ≥ 3 → move to completed_threads"]
    end

    subgraph RESOLVE["_apply_thread_resolutions()"]
        R1["For each ThreadResolution in thread_resolve:<br>Move ArcThread to completed_threads<br>Persist resolution_state field"]
    end

    PR --> S1 --> S2 --> S3
    PR -. "thread_resolve" .-> R1 --> S3

    S3 -- "CampaignArc" --> ARC[arc state in<br>state.yaml]:::arcNode
```

**Key rules:**
- **Unified collection:** `arc.threads[]` replaces the old active_threads/latent_threads split. The engine manages thread lifecycle via age-based demotion (`active: True → False`) instead of LLM-labeled urgency states.
- **Completion threshold:** progress reaches 3 → thread moved to `completed_threads`. Resolution state is preserved on completed threads for narrative context and eval rubrics.
- **5-turn expiry (age-based):** Threads not listed in `thread_advance` for 5+ turns get demoted (`active=False`). This replaces the old active→latent migration with a simpler boolean flag that Python manages directly from thread age, not LLM judgment.

## Narrator-Driven Arc: Phase & Truth Updates

The narrator can update arc metadata through a sentinel-delimited JSON block in its output. The engine parses and merges these updates after narration.

```mermaid
flowchart LR
    classDef llmNode fill:#0f172a,color:#94a3b8,stroke:#334155
    classDef sentinel fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    classDef mergeNode fill:#172554,color:#bfdbfe,stroke:#1d4ed8
    classDef arcNode fill:#3b0764,color:#e9d5ff,stroke:#7c3aed

    subgraph NARRATOR["Narrator prompt context"]
        NC1["visible_goal"]
        NC2["goal_context (early-turn narrative guidance)"]
        NC3["thematic_question"]
        NC5["arc.threads[] (summary, scope,<br>urgency, tags)"]
        NC6["pc_drive"]
        NC7["hidden_truths[] — internal only<br>NARRATOR MUST NOT reveal in prose"]
        NC8["discovered_truths[]"]
    end

    subgraph EMISSION["Narrator output"]
        PROSE["narration prose<br>(player sees this)"]:::llmNode
        SENTINEL["<<<ARC_UPDATE_START>>>
{discovered_truths, visible_goal}
<<<ARC_UPDATE_END>>>"]:::sentinel
    end

    subgraph PARSING["_extract_narrator_arc_update()"]
        P1["Regex: <<<ARC_UPDATE_START>>>(.*?)<<<ARC_UPDATE_END>>>"]
        P2["json.loads() → arc_dict"]
        P3["Strip block from narrative"]
    end

    subgraph MERGE["_merge_arc_update()"]
        M1["visible_goal: overwrite if present"]
        M2["thematic_question: overwrite if present"]
        M3["hidden_truths: overwrite if present"]
        M4["pc_drive: overwrite if present"]
        M5["hidden_truths: overwrite if present"]
        M6["discovered_truths: union with existing"]
        M7["goal_context: NOT merged — seed-only field, unchanged during play"]
    end

    NC1 & NC2 & NC3 & NC5 & NC6 & NC7 & NC8 --> PROSE
    PROSE --> SENTINEL
    SENTINEL --> P1 --> P2 --> P3
    P3 -- "clean narrative" --> CLIENT["client"]
    P2 -- "arc_dict" --> MERGE

    MERGE --> ARC[merge into state["arc"]]:::arcNode
```

**Merge rules:**
- **Engine owns thread lifecycle** (active/dormant/completed via age-based demotion). Narrator arc_update omits thread fields — they are ignored by `_merge_arc_update()`.
- **Narrator owns visible_goal/thematic_question/discovered_truths/hidden_truths.** Engine does not modify these.
- **`goal_context` is seed-only** — set once at game start, never overwritten by narrator or engine during play.
- **Discovered truths:** merged as set union (dedup).
- **Merge order:** engine thread signals run first (setting `delta.arc_update`), then narrator arc_update is parsed after narration and merged on top via a second `_merge_arc_update()` call in `run_turn()`.

## Arc Context in Narration

The arc state is passed to the narrator via `current_arc` in both system and user prompts. The narrator sees all arc metadata including `hidden_truths` but is explicitly instructed not to reveal them in prose.

### Early-turn narrative mode

When `goal_context` is present on the arc, the narrator treats it as narrative guidance for early turns: ground the player in personal stakes before broad exposition. The `goal_context` shapes what detail feels loaded, which NPC moment carries emotional charge, and what pressure matters immediately — without restating or summarizing it explicitly. This signal is provided via `_arc.j2` in the narrate user prompt.

The `goal_context` appears alongside other arc context values in the user prompt for this turn.

### Narrator prompt context

```mermaid
flowchart LR
    classDef stateNode fill:#0f172a,color:#7dd3fc,stroke:#1e40af
    classDef ctxNode fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    classDef llmNode fill:#0f172a,color:#94a3b8,stroke:#334155

    STATE["state.yaml arc section"]:::stateNode

    subgraph CONTEXT["_narrate_messages() → current_arc_ctx"]
        C1["visible_goal"]
        C2["goal_context"]
        C3["thematic_question"]
        C5["arc.threads[]<br>(summary, scope, urgency)"]
        C6["pc_drive"]
        C7["hidden_truths[]"]
    end

    subgraph PROMPT["narrate_system.j2"]
        P1["## Campaign Arc context<br>goal_context, goal, threads, truths"]:::llmNode
        P2["## ARC UPDATE section<br>instructions + sentinel format<br>+ hidden_truths non-reveal directive"]:::llmNode
    end

    subgraph USER_PROMPT["narrate_user.j2 via _arc.j2"]
        U1["visible_goal"]
        U2["goal_context"]
        U3["thematic_question"]
        U4["pc_drive"]
    end

    STATE --> CONTEXT
    CONTEXT --> P1 & P2 & USER_PROMPT
```

## Arc System Integration Points

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
        N2["Narrator outputs prose +<br>optional <<<ARC_UPDATE_START>>> block"]:::llmNode
    end

    subgraph EXTRACT["Step 2c — Progress Extract"]
        E1["Progress extractor emits<br>thread_advance: list[str],<br>thread_resolve: list[ThreadResolution],<br>thread_add (gated by PacingContext.gate)"]:::pyNode
    end

    subgraph ARC_ENGINE["Arc Engine (turn.py)"]
        A1["_apply_thread_signals() + _apply_thread_resolutions()<br>process thread_advance → update threads,<br>age-based demotion for silent threads<br>thread_resolve → completed_threads with resolution_state"]:::pyNode
        A2["_merge_arc_update()<br>engine arc_delta → state['arc']"]:::pyNode
    end

    subgraph NARRATOR_MERGE["Narrator Arc Merge"]
        N3["_extract_narrator_arc_update()<br>parse sentinel block"]:::pyNode
        N4["_merge_arc_update()<br>narrator arc_update → state['arc']"]:::pyNode
    end

    STATE --> N1
    N1 --> N2
    N2 --> N3
    E1 --> A1 --> A2

    A2 --> N3 --> N4 --> STATE
```

---


## cross-pipeline



```mermaid
flowchart TD
    classDef stageRules    fill:#4c1d95,color:#ddd6fe,stroke:#7c3aed
    classDef stageNarrate  fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6
    classDef stageScene    fill:#064e3b,color:#a7f3d0,stroke:#10b981
    classDef stageState    fill:#451a03,color:#fde68a,stroke:#f59e0b
    classDef stageProgress fill:#500724,color:#fbcfe8,stroke:#ec4899
    classDef storageNode   fill:#0f172a,color:#7dd3fc,stroke:#1e40af
    classDef mergeNode     fill:#172554,color:#bfdbfe,stroke:#1d4ed8

    STATE["state.yaml"]:::storageNode
    CHRONICLE["chronicle.md"]:::storageNode
    EVENTS["events.jsonl"]:::storageNode

    STATE -- "load_state()" --> STEP0["Step 0<br>Rules / Intent"]:::stageRules
    CHRONICLE -- "chronicle_tail<br>recent_turns" --> STEP1["Step 1<br>Narrate"]:::stageNarrate
    STATE -- "pc, inventory,<br>quests, compendium" --> STEP1
    STEP0 -- "IntentEnvelope<br>RulesOutcome" --> STEP1
    STEP1 -- "narrative: str" --> STEP2A["Step 2a<br>Scene"]:::stageScene
    STEP2A -- "location_change<br>npc_roster" --> STEP2B["Step 2b<br>State"]:::stageState
    STEP1 -- "narrative" --> STEP2B
    STEP2A -- "location_change<br>npc_roster" --> STEP2C["Step 2c<br>Progress"]:::stageProgress
    STEP1 -- "narrative" --> STEP2C
    STEP2A & STEP2B & STEP2C -- "merge" --> DELTA["StateDelta"]:::mergeNode
    DELTA -- "validate + apply" --> STATE
    DELTA -- "event record" --> EVENTS
    DELTA -- "narrative" --> CHRONICLE
    STEP2C -- "thread_advance/resolve/add<br>gm_beat (inferred disposition)" --> STATE
```

---


## delta-validate



The three extraction results merge into a single `StateDelta`, then validate and apply.

## Flowchart

```mermaid
flowchart TD
    classDef stageScene    fill:#064e3b,color:#a7f3d0,stroke:#10b981
    classDef stageState    fill:#451a03,color:#fde68a,stroke:#f59e0b
    classDef stageProgress fill:#500724,color:#fbcfe8,stroke:#ec4899
    classDef pyNode        fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef mergeNode     fill:#172554,color:#bfdbfe,stroke:#1d4ed8

    SR1["SceneExtractResult<br>(Step 2a)"]:::stageScene
    SR2["StateExtractResult<br>(Step 2b)"]:::stageState
    SR3["StorytellerResult<br>(Step 2c)"]:::stageProgress

    MERGE["StateDelta<br>──────────────────<br>scene_tags, scene_tagline<br>location_change, location_description<br>npc_add / npc_remove / npc_update<br>compendium_npc_update<br>thread_advance / thread_resolve / thread_add (gated)<br>inventory_add / remove / update<br>pc_condition_add / remove<br>arc_update<br>recent_events_add / update / remove<br><br>(gm_beat NOT in StateDelta —<br>written directly to state.meta.pending_gm_beat)"]:::mergeNode

    VALIDATE["_validate()<br>Check inventory_remove IDs exist<br>→ rejections: list[dict]"]:::pyNode

    APPLY["apply_delta() — mutates state in-place<br>──────────────────────────────<br>inventory add / remove / update<br>pc.conditions add / remove (+ added_turn)<br>location (id, name, description)<br>scene.present_npcs<br>scene.tagline<br>scene.recent_events (ring buffer, max 20, configurable via recent_events_max)<br>scene.world_state<br><br>_apply_thread_signals()<br>──────────────────────<br>thread_advance: progress +1 on matched ArcThread<br>thread_resolve: move to completed_threads with resolution_state<br>thread_add: create new ArcThread if gate == 'allow'<br>age-based demotion: active=True → False when last_seen_turn < turn_no - 5<br><br>quests (create-or-update)<br>compendium.npcs (upsert)<br>meta.compendium_touch_order (LRU)<br>meta.turn += 1"]:::pyNode

    DIFF["summarize_changes()<br>diffs pre vs post state<br>→ changes{inventory, player, facts, quests}"]:::pyNode

    SR1 --> MERGE
    SR2 --> MERGE
    SR3 --> MERGE
    MERGE --> VALIDATE
    VALIDATE -- "valid" --> APPLY
    VALIDATE -- "rejections" --> DIFF
    APPLY --> DIFF
```

---


## narration-ui



The primary player-facing UI. Renders game state, streams narrative tokens live, and refreshes sidebars via HTMX partial swaps. Single-page app driven by Alpine.js + SSE + HTMX.

## Interaction Model

```mermaid
flowchart TD
    classDef ssr       fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6
    classDef sse       fill:#064e3b,color:#a7f3d0,stroke:#10b981
    classDef htmx      fill:#451a03,color:#fde68a,stroke:#f59e0b
    classDef alpine    fill:#500724,color:#fbcfe8,stroke:#ec4899
    classDef storage   fill:#0f172a,color:#7dd3fc,stroke:#1e40af
    classDef input     fill:#1f2937,color:#9ca3af,stroke:#4b5563

    REQ["GET /<br>index(request)"]:::ssr
    SSR["Server renders index.html via Jinja2<br>────────────────────────<br>state (state.yaml)<br>history (events.jsonl, last N)<br>last_actions · opening · opening_actions<br>has_narrative · pack_mode · pack_name<br>character_creation_enabled · css_v"]:::ssr

    UI["Browser — Alpine.js app-shell<br>x-data=&quot;game()&quot;"]:::alpine

    SUBMIT["submitTurn()<br>EventSource('GET /turn?input=...')"]:::alpine

    subgraph STREAM["SSE — run_turn() pipeline"]
        TOK["event: narrative_token<br>{ chunk: str }"]:::sse
        PHASE["event: phase<br>{ phase_name, ... }"]:::sse
        DONE["event: turn_complete<br>{ turn, trace_id, narrative, actions,<br>  scene_tags, game_over, rejected,<br>  errors, diff, changes, change_lines,<br>  state, metrics, ruling,<br>  recent_events_evicted, ts }"]:::sse
        ERR["event: turn_error<br>{ error }"]:::sse
    end

    DISPLAY["_startDisplayDrain()<br>6 chars/frame → narrative column"]:::alpine
    REFRESH["htmx.ajax('GET', '/panels/state-left')<br>htmx.ajax('GET', '/panels/state-right')"]:::htmx
    CHANGES["_buildTurnChanges()<br>→ roll badge · change lines<br>→ _prependTurnLogTurn()"]:::alpine

    SIDEBAR["HTMX — GET /panels/{state-left,state-right,actions,debug}<br>Server returns rendered _state_left.html etc."]:::htmx

    CHRON["Chronicle overlay<br>HTMX — GET /panels/turn-log?limit=50<br>→ _turn_log.html"]:::htmx

    NEW_GAME["POST /new-game<br>or /new-game/reroll<br>→ full reload or HTMX swap"]:::htmx

    REQ --> SSR --> UI
    UI --> SUBMIT
    SUBMIT --> STREAM
    STREAM --> TOK --> DISPLAY
    STREAM --> PHASE --> DISPLAY
    STREAM --> DONE --> REFRESH
    DONE --> CHANGES
    REFRESH --> SIDEBAR
    CHANGES --> SIDEBAR
    STREAM --> ERR
    UI --> CHRON
    UI --> NEW_GAME
```

## Layout

| Region | Element | Content |
|--------|---------|---------|
| **Header** | `.header-bar` | Logo/tagline, Chronicle toggle, turn counter, retry button, new game button, reroll button (dynamic packs), mock-mode dot |
| **Left sidebar** | `.sidebar-left` | Player card, scene NPCs, location, arc, compendium — loaded via `/panels/state-left` |
| **Narrative column** | `.narrative-column` | Scrollable narrative blocks, action pills, input textarea, send/stop button |
| **Right sidebar** | `.sidebar` (right) | Inventory, recent events, world state, debug panel — loaded via `/panels/state-right` |
| **Chronicle overlay** | `.turn-log-shell` | Floating overlay over narrative column, populated by `/panels/turn-log?limit=50` |
| **New Game modal** | (Alpine `x-show`) | Pack picker → char creation / world builder steps |

## Data Flow

### Turn submission (Alpine.js + SSE)

1. User types input, presses Enter → `game().submitTurn()`
2. Opens `EventSource` to `GET /turn?input=<text>` — SSE endpoint in `routes.py:83`
3. Server streams events as the 5-stage pipeline (`run_turn()`) executes:
   - `narrative_token` — token chunks streamed as they arrive from LLM
   - `phase` — pipeline phase progress (ruling_start, narrate_start, narrate_first_token, narrate_done, extract_start, extract_done, compact_start, etc.)
   - `turn_complete` — final result
   - `turn_error` — error payload
4. Client `_startDisplayDrain()`: reveals 6 characters per animation frame for smooth streaming
5. On `turn_complete`:
   - Calls `htmx.ajax('GET', '/panels/state-left', ...)` and `htmx.ajax('GET', '/panels/state-right', ...)` to refresh sidebars
   - Renders change lines (`_buildTurnChanges`), roll badge
   - Prepends turn to Chronicle overlay via `_prependTurnLogTurn`
   - Re-renders markdown via `marked.parse()`

### HTMX partial endpoints (routes.py)

| Route | Template | Purpose |
|-------|----------|---------|
| `GET /panels/state-left` | `_state_left.html` | Left sidebar — player, NPCs, location, arc, compendium |
| `GET /panels/state-right` | `_state_right.html` | Right sidebar — inventory, events, world state, debug |
| `GET /panels/actions` | `_actions.html` | Action pills (fallback) |
| `GET /panels/turn-log?limit=N` | `_turn_log.html` | Chronicle — turn history with change lines |
| `GET /panels/pack-picker` | `_pack_picker.html` | New Game — pack selection cards |
| `GET /panels/char-creation` | `_char_creation.html` | New Game — character stats builder |
| `GET /panels/world-builder` | `_world_builder.html` | New Game — world creation form |
| `GET /panels/debug` | `_debug.html` | Debug panel — recent turn timings, errors |
| `GET /panels/state` | `_state.html` | Combined left+right (legacy) |

### Client state machine (`game()` — inline `<script>` in index.html)

Alpine.js `x-data="game()"` manages:
- `input` — textarea value
- `submitting` — turn-in-progress flag
- `gameStarted` — derived from `has_narrative`
- `turnNum` — current turn counter
- `leftWidth` / `rightWidth` — resizable sidebar widths (persisted to `localStorage`)
- Card collapse state — read/written directly from/to `localStorage` via `CCYA_CARD_KEY(name)` helper, using DOM `data-card` attributes; no Alpine data property

## UI Features

### Resizable sidebars
- Drag gutters with mousedown/mousemove handlers
- Widths saved to `localStorage` (`ccya_sidebar_left`, `ccya_sidebar_right`)
- Minimum width enforcement (240px left, 220px right)

### Collapsible cards
Each sidebar section has a collapse toggle; open/closed state persisted per-card to `localStorage` via `ccya_card_<name>` key.

### Action pills
Suggested next actions rendered as buttons that populate the input on click. Updated from `turn_complete.actions` or via HTMX panel refresh.

### Roll badge
Server-rendered for history, JS-built for new turns. Shows dice math, band label, outcome summary. Band colors: `crit_fail` (red) → `fail` → `setback` → `partial` → `success` → `crit_success`.

### Change lines
Grouped by category via emoji prefix:
| Emoji | Category | Class |
|-------|----------|-------|
| 🎒 + | Inventory gain | `.tc-inv-gain` |
| 🎒 − | Inventory loss | `.tc-inv-loss` |
| 🩺 | Player condition | `.tc-pl` |
| 📍 | Location | `.tc-loc` |
| 📜 | Faction/arc | `.tc-fa` |

### Retry
`POST /turn/delete` removes last event from `events.jsonl` and `chronicle.md`, returns previous actions for re-submission.

### New Game
`POST /new-game` with optional `pack_id`, `pc_name`, `pc_stats`, `hints`. For dynamic packs, triggers `generate_seed()` LLM pipeline. Full page reload on success. Reroll (`POST /new-game/reroll`) HTMX-swaps the opening narrative + actions.

## CSS Architecture

- **`app.src.css`** — Tailwind + custom styles split by region (lines 1–2101):
  - App shell layout (CSS Grid: header + body with sidebar-gutter-main-gutter-sidebar)
  - Narrative blocks (`.narrative-block`, `.narrative-text`)
  - Sidebar cards (`.card`, `.card-header`, `.card-body`)
  - Input bar (`.input-bar`, `.game-input`, `.send-btn`)
  - Action pills (`.action-pill`, `.pills-row`)
  - Roll badges (`.roll-badge`, `.roll-band--*`)
  - Chronicle overlay (`.turn-log-shell`, `.turn-log-panel`)
  - New Game modal (`.modal-overlay`, `.pack-card`)
  - Progress strip, tooltips, scrollbar styling
  - Design tokens via CSS custom properties (`--text-primary`, `--bg-card`, `--status-*`)
- Compiled to **`app.css`** with cache-busting via `css_v` query param

## Server Entry Point

`routes.py:57` — `GET /` handler assembles template context from `state.yaml`, `events.jsonl`, pack manifest, and engine config, then renders `ccya/templates/index.html`.

---


## out-of-band



These run only at new-game time or are non-engine concerns. They are excluded from the eval-context region of the main architecture doc.

## Character Creation Pipeline

Triggered by `POST /new-game`. Behavior differs by pack mode.

```mermaid
flowchart TD
    FORM["New Game Form<br>──────────────────<br>pack_id<br>pc_name, pc_tagline, pc_stats<br>pc_hints, npc_hints<br>location_hints, quest_hints<br>free_form, npc_count"]

    MODE{pack.manifest.mode}

    subgraph STATIC["Static Pack"]
        SS["Load pack.seed (YAML)<br>Apply hard overrides:<br>  pc.name, pc.tagline, pc.stats<br>(validated: 6 stats, each 1–4, total 12–16)"]
    end

    subgraph DYNAMIC["Dynamic Pack — generate_seed()"]
        DS["Build PlayerOverrides<br>  (pc_hints, npc_hints, location_hints,<br>  quest_hints, free_form, npc_count)<br>Pass to generate_seed() LLM pipeline"]
    end

    INIT["init_save_dir(SAVE_DIR, seed)<br>Writes state.yaml<br>Clears chronicle.md + events.jsonl"]

    OPENING["static: pack.opening_text<br>dynamic: envelope.opening_narrative<br>dynamic: envelope.actions (suggested first moves)"]

    FORM --> MODE
    MODE -- "static" --> STATIC
    MODE -- "dynamic" --> DYNAMIC
    STATIC --> INIT
    DYNAMIC --> INIT
    INIT --> OPENING
```

## Generate Seed Pipeline (Dynamic Packs Only)

Called by `POST /new-game` and `POST /new-game/reroll`. Generates a complete starting game state (PC, NPCs, location, arc, opening narrative, actions) from the pack manifest and optional player overrides.

The seed owns **first-turn emotional framing** — not just world and arc scaffolding. Every seed element must produce an emotionally legible opening that answers: why this moment matters now, what the character stands to lose, and why at least one person in the scene matters to them personally.

```mermaid
flowchart LR
    classDef llmNode fill:#0f172a,color:#94a3b8,stroke:#334155
    classDef outNode fill:#172554,color:#bfdbfe,stroke:#1d4ed8

    subgraph IN["Inputs"]
        G1["pack.manifest<br>(world rules, tone, setting)"]
        G2["pack.style_text"]
        G3["PlayerOverrides (optional)<br>  pc_hints, npc_hints<br>  location_hints, quest_hints<br>  free_form, npc_count"]
        G4["npc_name_pool (name locales)"]
        G5["engine_config.generate_seed_temperature (0.9)<br>engine_config.generate_seed_max_retries (1)"]
    end

    subgraph LLM_GS["LLM — generate_seed_system.j2 + generate_seed_user.j2"]
        GL["temp: 0.9<br>output: SeedEnvelope JSON"]:::llmNode
    end

    subgraph OUT["Outputs — SeedEnvelope"]
        O1["seed_state: GameState<br>  pc (name, tagline, bio, stats)<br>  location (id, name, description)<br>  scene (present_npcs with relation field,<br>         recent_events, world_state)<br>  inventory: list[InventoryItem]<br>  compendium.npcs: dict[id] NpcRef<br>  meta (model, setting_pack, turn=0)"]:::outNode
        O2["arc: CampaignArc<br>  visible_goal, goal_context (personal stakes),<br>  thematic_question, hidden_truths,<br>  threads[] (unified, with active flag),<br>  completed_threads[], pc_drive"]:::outNode
        O3["opening_narrative: str<br>(prose intro shown before turn 1)"]:::outNode
        O4["actions: list[str]<br>(4 distinct, character-shaped,<br>scene-grounded choices)"]:::outNode
    end

    IN --> LLM_GS
    LLM_GS --> OUT
```

### Seed emotional framing contract

The seed prompt (`generate_seed_system.j2`) enforces these requirements:

- **`goal_context`**: 2–3 sentences explaining why `visible_goal` matters to this character specifically — inner cost or pressure that makes it emotionally loaded. No hidden-truth spoilers, no restating `visible_goal`, no direct statement of the thematic question. Must connect character motive, story stakes, and emotional cost.
- **NPC `relation` field**: Each opening NPC has a defined narrative job. One NPC is personally tied to the PC's motive or vulnerability; the other carries immediate external pressure from the world or conflict. The `relation` field encodes PC-facing relevance (e.g. "owes them a favor", "is their only contact here", "represents the institution pressing on them").
- **Compendium NPCs**: The seed also generates 2–3 NPCs in `compendium.npcs` (name, title, bio) who exist in the world but are not present in the opening scene. Their bios tie them to factions, locations, or world pressures, not to the immediate situation. These become discoverable characters during play.
- **Action guidance**: Each of the 4 choices is written from the PC's point of view, grounded in a present NPC, immediate risk, active thread, or character motive. They differ in emotional posture (confront, deflect, investigate, protect, exploit, withdraw, etc.) and avoid generic verbs.
- **`pc_drive`**: A single sentence about the PC's personal reason for being in this situation. Expressed indirectly through `goal_context`, NPC relations, opening narrative, and actions — never displayed as a labeled UI fact.
- **`threads[]`**: Unified list (not split active/latent) where each thread has `{id, summary, tags, urgency, scope}` and an `active` boolean flag managed by Python age rules, not LLM.

## Turn Viewer — status colors

The standalone turn viewer ([turn-viewer-ui](./turn-viewer-ui.md)) uses the same semantic status colors as the CSS custom properties in `static/app.src.css` (`--status-*`). The stage colors used in the diagrams above (`stageRules` violet → `stageNarrate` blue → `stageScene` green → `stageState` amber → `stageProgress` pink) map directly to the `--stage-*` tokens. Cross-stream inputs into a step are shown in `xstream` (purple outline) and LLM/Python boxes use neutral dark fills. This table is the canonical turn-viewer status legend.

| Token | Meaning |
|-------|---------|
| `--status-ok` | Stage ran and completed (no extraction error). |
| `--status-skipped` | Stream was skipped (no longer used — all streams always run). |
| `--status-retried` | LLM output required a parse retry (`attempts` > 1 in event). |
| `--status-rejected` | Post-extract validation rejected part of the delta (e.g. bad `inventory_remove`). |
| `--status-error` | LLM call or parse ultimately failed for that stream. |
| `--status-neutral` | Non-fatal / informational (e.g. rules path with no dice roll). |

Stage accent stripes use `--stage-rules`, `--stage-narrate`, `--stage-scene`, `--stage-state`, `--stage-progress` for quick scanning; **status** always wins for the prominent left border.

---


## pacing-context



All pacing signals are collapsed into one Python-computed struct (`PacingContext`) passed to both the Narrator and Progress Extractor. This replaces six independent fields (`narration_directive`, `deescalate`, `narrative_velocity`, `beat_disposition` output, `quest_threshold_directive`, and stale momentum-derived signals). The narrator receives `directive`; Progress receives the full struct.

## Struct definition

```
PacingContext:
  directive: str           # "" | "Breathe" | "Pressure" | "Overwhelm" | "Tension" | "Resolve a Threat" | "Threat Pressure"
  beat_locked: bool        # True: floor relief fired — Progress MUST emit breathing_room beat and gate is force-closed
  gate: str                # "block_escalate" | "allow" (controls thread_add)
  summary: str             # human-readable log string, never sent to LLM
```

`beat_locked: True` subsumes the old `_check_floor_relief()` side-channel — floor relief logic is computed inside `_compute_pacing_context()`. The `gate` field prevents Progress from adding new threads during de-escalation windows. Secondary modifiers like "Combat Fatigue" may be appended via semicolons (e.g., "Pressure; Combat Fatigue").

## Computation

`_compute_pacing_context()` in `engine/turn.py` consolidates pacing computation (replacing the former scattered functions: `_compute_narration_directive`, `_compute_narrative_velocity`, `_check_floor_relief`). It takes inputs (`momentum`, `consecutive_floor_turns`, `arc.threads[] scope=scene urgency counts`, combat age, location age) and returns a single struct with directive derived from the same priority stack:

```mermaid
flowchart TD
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef decision fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    classDef output fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6

    M["momentum scalar"]:::pyNode
    T["arc.threads[] scope=scene<br>(urgency counts)"]:::pyNode
    CA["combat_age"]:::pyNode
    TA["threat_ages<br>(age per scene thread)"]:::pyNode

    M --> D1{"velocity < -0.3<br>(deescalation)"}:::decision
    D1 -- yes --> B1["directive='Breathe'"]:::output
    D1 -- no --> D2{"≥ 3 urgent<br>threads?"}:::decision
    D2 -- yes --> B2["directive='Overwhelm'"]:::output
    D2 -- no --> D3{"aged-out threat<br>(resolve imperative)"}:::decision
    D3 -- yes --> B3["directive='Resolve a Threat'"]:::output
    D3 -- no --> D4{"1-2 urgent<br>threads?"}:::decision
    D4 -- yes --> B4["directive='Pressure'"]:::output
    D4 -- no --> D5{"background urgency<br>threads only?"}:::decision
    D5 -- yes --> B5["directive='Tension'"]:::output
    D5 -- no --> D6{"threat_age ≥ pressure_at<br>(normal aging)"}:::decision
    D6 -- yes --> B6["directive='Threat Pressure'"]:::output
    D6 -- no --> B7["directive='' (empty)"]:::output

    CA -- "≥ 3" --> SEC["; Combat Fatigue (secondary append)"]

    FINAL["PacingContext<br>directive · beat_locked · gate"]:::output
```

Priority order (highest to lowest): **Breathe > Overwhelm > Resolve a Threat > Pressure > Tension > Threat Pressure > (empty)**. The `beat_locked` flag takes precedence — when at momentum floor, directive is forced to include "Resolve a Threat" and gate is force-closed when directive is "Breathe".

## Wiring: how PacingContext reaches the pipelines

```mermaid
flowchart LR
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef prompt fill:#0f172a,color:#7dd3fc,stroke:#1e40af
    classDef extractor fill:#500724,color:#fbcfe8,stroke:#ec4899

    TURN["engine/turn.py<br>_compute_pacing_context()"]:::pyNode
    PIPELINE["_run_extraction_pipeline()<br>pass PacingContext struct"]:::pyNode
    EXTRACT_FN["_storytell_messages()<br>extraction.py"]:::pyNode
    USER_TMPL["storytell_user.j2<br>pacing_context.directive + gate"]:::prompt
    SYS_TMPL["storytell_system.j2<br>PacingContext guidance"]:::prompt
    NARRATE_TMPL["narrate_user.j2<br>pacing_context.directive"]:::prompt

    TURN --> PIPELINE --> EXTRACT_FN --> USER_TMPL
    USER_TMPL --> SYS_TMPL --> EXTRACTOR["Progress Extractor LLM"]:::extractor
    TURN -. "also passed to" .-> NARRATE_TMPL
```

1. **Computed** once in `run_turn()` via `_compute_pacing_context()`.
2. **Passed through** `_run_extraction_pipeline()` → both `_narrate_messages()` and `_storytell_messages()`.
3. **Narrator template** (`narrate_user.j2`) renders only `directive` (tone/direction). No Jinja2 directive computation remains — all directives computed by Python.
4. **Storytell template** ((`storytell_system.j2` + `user.j2`)) receives the full struct; guidance maps each directive to appropriate thread/beat actions:

| Directive | Thread action | Gate |
|-----------|---------------|-------|
| **"Breathe"** (de-escalation, velocity < -0.3) | Do NOT add new threads. Allow existing scene threads to persist without escalation. | `block_escalate` + force-closed when at momentum floor |
| **"Overwhelm"** (3+ urgent threads) | May add scene-scoped threads if gate allows; emit pressure/escalation beat | `allow` |
| **"Resolve a Threat"** (aged-out threat imperative) | Advance the aged thread toward resolution; avoid adding new complications | `allow` |
| **"Pressure"** (1-2 urgent or aging threats) | Advance relevant scene/arc threads. Add new thread only if gate permits. | Varies by context |
| **"Tension"** (background urgency only) | Do NOT add pressures unless concrete threat emerges; prefer advancing existing threads | Allow |
| **"Threat Pressure"** (normal urgency aging) | Escalate urgency of the aging thread; consider advancing | Allow |
| **"" (empty)** | No action required beyond normal aging of silent threads. | Allow |

**Note:** Directives may include secondary modifiers joined by semicolons (e.g., "Pressure; Combat Fatigue"). The primary directive drives thread/beat logic; the secondary acts as a thematic modifier on beat type.

---


## persist



Atomic writes to disk. No LLM calls.

## Flowchart

```mermaid
flowchart LR
    classDef storageNode fill:#0f172a,color:#7dd3fc,stroke:#1e40af
    classDef pyNode      fill:#1f2937,color:#9ca3af,stroke:#4b5563

    subgraph IN["Inputs"]
        P1["state (post-apply)"]
        P2["event dict<br>(turn, input, applied, rejected,<br>actions, scene_tags, rules,<br>narrate/extract metrics, extraction<br>with per-stream prompts + attempts,<br>rules_prompt, narrate_prompt,<br>engine_expired_conditions, changes)"]
        P3["narrative: str"]
        P4["turn number"]
    end

    subgraph WRITES["saves/default/"]
        W1["events.jsonl<br>append — structured event log"]:::storageNode
        W2["state.yaml<br>atomic overwrite — canonical live state"]:::storageNode
        W3["chronicle.md<br>append — '## Turn N — input\n\nnarrative'"]:::storageNode
    end

    READBACK["Feeds Steps 0 & 1 on the next turn<br>via load_state(), load_chronicle_tail(),<br>load_recent_chronicle_turns()"]:::pyNode

    IN --> W1
    IN --> W2
    IN --> W3
    W3 --> READBACK
    W2 --> READBACK
```

---


## step0-ruling



Classifies the player's action, determines whether a dice check is needed, and
identifies which state domains will be active — narrowing every downstream extractor.

## Flowchart

```mermaid
flowchart LR
    classDef stageRules fill:#4c1d95,color:#ddd6fe,stroke:#7c3aed
    classDef llmNode    fill:#0f172a,color:#94a3b8,stroke:#334155
    classDef pyNode     fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef outNode    fill:#3b0764,color:#e9d5ff,stroke:#7c3aed

    subgraph IN["Inputs"]
        I1["state.pc<br>(name, stats, conditions)"]
        I2["state.location"]
        I3["recent_turns[-1:]<br>(from chronicle;<br>user prompt: narrative tail)"]
        I4["user_input"]
    end

    subgraph LLM0["LLM — ruling_system.j2 + ruling_user.j2"]
        L0["temp: 0.2 · max_retries: 1<br>output: IntentEnvelope JSON"]:::llmNode
    end

    subgraph PYRES["Python — rules.resolve_check()"]
        P0["reads pc.stats[skill]<br>reads pc.conditions → cond_mod<br>rolls 2d6 + stat_mod + cond_mod − diff_mod<br>maps total → Band"]:::pyNode
    end

    subgraph OUT["Outputs"]
        O1["IntentEnvelope<br>  intent: str<br>  intent_verb: str<br>  target: str<br>  check.required: bool<br>  check.skill: SkillName<br>  check.difficulty: Difficulty"]:::outNode
        O2["RulesOutcome<br>  rolled: bool<br>  skill, difficulty, stat_value, stat_mod<br>  diff_mod, cond_mod<br>  dice: list[int]<br>  raw_total, final_total: int<br>  band: Band<br>  directive: str<br>  intent, intent_verb: str"]:::outNode
    end

    IN --> LLM0
    LLM0 -- "IntentEnvelope" --> PYRES
    PYRES --> OUT
```

## Key forward dependency

`rules_outcome` feeds into `_compute_pacing_context()` which produces the single authoritative `PacingContext` struct passed to both Narrator and Progress Extractor.

---


## step1-narrate



Generates the narrative prose the player reads. Tokens are streamed to the client.

## Flowchart

```mermaid
flowchart LR
    classDef llmNode   fill:#0f172a,color:#94a3b8,stroke:#334155
    classDef xstream   fill:#4c1d95,color:#ddd6fe,stroke:#7c3aed
    classDef outNode   fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6

    subgraph IN["Inputs"]
        N1["state (full —<br>pc, location, scene,<br>inventory, quests, compendium)"]
        N2["chronicle_tail<br>(compressed history, ≤budget tokens)"]
        N3["recent_turns (last window_turns, default 3)"]
        N4["rules_outcome<br>(band, directive, dice summary)"]:::xstream
        N5["pack_style (tone / prose guide)"]
        N6["npc_name_pool (cultural name list)"]
        N7["recently_left NPCs"]
        N8["known_npcs<br>(last-seen info)"]
        N9["present_npcs<br>(attitudes)"]
        N10["world_factions<br>(immutable trace)"]
        N11["world_locations<br>(nearby, immutable)"]
        N12["pending_gm_beat<br>(type · surface_as metadata)"]
        N13["pacing_context<br>(directive)<br>from _compute_pacing_context()"]:::xstream
        N14["compendium_bios<br>(upserted bio entries for<br>present + recently_left NPCs)"]
        N15["user_input"]
    end

    subgraph LLM1["LLM — narrate_system.j2 + narrate_user.j2"]
        NL["temp: 0.9 · streaming: yes<br>output: prose narrative (str)"]:::llmNode
    end

    subgraph OUT["Outputs"]
        NO1["narrative: str<br>(streamed as tokens → client<br>then joined + thinking-stripped)"]:::outNode
        NO2["narr_metrics<br>  first_token_ms<br>  total_ms<br>  tokens_in / tokens_out"]
    end

    IN --> LLM1
    LLM1 --> OUT
```

## Arc context in narration

The narrator receives `current_arc` in both system and user prompts. Key fields:

- **`goal_context`**: A seed-time field (2–3 sentences) explaining why `visible_goal` matters to the character specifically — inner cost or pressure that makes it emotionally loaded. When present, `_arc.j2` presents it alongside other arc context in the user prompt for early-turn narrative guidance: ground the player in personal stakes before broad exposition.
- **`visible_goal`**: The player-facing objective.
- **`thematic_question`**: The moral tension — never stated directly in prose. Used as a lens for emphasis: what detail feels loaded, what silence matters.
- **`pc_drive`**: The character's personal motive. Expressed indirectly through goal_context, NPC relations, and action language rather than displayed as a labeled UI fact.
- **`hidden_truths[]`**: Internal-only story secrets the narrator must never reveal in prose.
- **`threads[]`**: Unified thread collection filtered by `active` flag. Scene-scope threads provide immediate pressure; arc-scope threads provide medium-term tension.

### Opening-turn narrative mode

When `goal_context` is present (always true after seed), the narrator treats early turns as a distinct onboarding mode:
1. Personal stakes before broad exposition
2. One NPC moment with emotional charge (driven by `relation` fields on seed NPCs)
3. One immediately actionable pressure

The presence of `goal_context` itself is the signal — no turn-counting dependency needed. The guidance is most impactful in the first few turns and persists as background context throughout the campaign.

## Key forward dependency

`narrative` is the primary content input for all three extraction streams below.

---


## step2a-scene



Extracts location changes, NPC presence, scene tags, and suggested actions from the narrative.

## Flowchart

```mermaid
flowchart LR
    classDef llmNode fill:#0f172a,color:#94a3b8,stroke:#334155
    classDef xstream fill:#4c1d95,color:#ddd6fe,stroke:#7c3aed
    classDef outNode fill:#064e3b,color:#a7f3d0,stroke:#10b981

    subgraph IN["Inputs"]
        S1["narrative (from Step 1)"]:::xstream
        S2["state.pc (name, tagline, bio, stats)"]
        S3["state.location"]
        S4["state.scene.present_npcs"]
        S5["state.pc.conditions"]
        S6["known_characters<br>(full roster: id, name, tags, notes<br>up to 10 LRU from compendium)"]
        S7["recent_turns[-1:]<br>(T-1 prior narration)"]
    end

    subgraph LLM2A["LLM — extract_scene_system.j2 + extract_scene_user.j2"]
        SL["temp: 0.4 · max_retries: 1<br>output: SceneExtractResult JSON"]:::llmNode
    end

    subgraph OUT["Outputs — SceneExtractResult"]
        O1["scene_tags: list[str]"]:::outNode
        O2["scene_tagline: str (3–6 words for UI header)"]:::outNode
        O3["location_change: LocationRef | None<br>  id, name, description"]:::outNode
        O4["location_description: str | None"]:::outNode
        O5["npc_add / npc_remove / npc_update<br>  delta-form NPC presence changes"]:::outNode
        O6["compendium_npc_update<br>  durable identity changes"]:::outNode
    end

    IN --> LLM2A
    LLM2A --> OUT
```

## Key forward dependency

`location_change` and `present_npcs` flow into `extraction_ctx` (built by `_build_extraction_context`). Step 2c also receives `npc_roster` (tiered: PRESENT/JUST_LEFT/NEARBY/KNOWN) built from extraction_ctx. No forward-facing mechanics (`thread_add`, `gm_beat`) are emitted by this stream — they go through the unified thread pipeline via Progress Extract.

---


## step2b-state



Extracts inventory changes and player condition mutations from the narrative.

## Flowchart

```mermaid
flowchart LR
    classDef llmNode fill:#0f172a,color:#94a3b8,stroke:#334155
    classDef xstream fill:#4c1d95,color:#ddd6fe,stroke:#7c3aed
    classDef outNode fill:#451a03,color:#fde68a,stroke:#f59e0b

    subgraph IN["Inputs"]
        S1["narrative (from Step 1)"]:::xstream
        S2["state.pc (name, bio, stats, conditions)"]
        S3["state.location"]
        S4["state.inventory"]
        S5["intent: str<br>(from Step 0)"]
    end

    subgraph LLM2B["LLM — extract_state_system.j2 + extract_state_user.j2"]
        SL["temp: 0.4 · max_retries: 1<br>output: StateExtractResult JSON"]:::llmNode
    end

    subgraph OUT["Outputs — StateExtractResult"]
        O1["inventory_add: list[InventoryItem]<br>  id, name, notes, amount"]:::outNode
        O2["inventory_remove: list[InventoryRemove]<br>  id, amount (None = full stack)"]:::outNode
        O3["inventory_update: list[InventoryUpdate]<br>  id, name?, notes?"]:::outNode
        O4["pc_condition_add: list[ConditionAdd]<br>  id, label, description"]:::outNode
        O5["pc_condition_remove: list[ConditionRemove]<br>  id"]:::outNode
    end

    IN --> LLM2B
    LLM2B --> OUT
```

## Key forward dependency

Step 2c receives `npc_roster` (tiered: PRESENT/JUST_LEFT/NEARBY/KNOWN) and `location_change` from Step 2a. Cross-stream items_gained/lost were removed — extraction_ctx now covers all this-turn derived data.

---


## step2c-progress



Extracts quest updates, recent events, and durable NPC compendium changes.

## Flowchart

```mermaid
flowchart LR
    classDef llmNode fill:#0f172a,color:#94a3b8,stroke:#334155
    classDef xstream fill:#4c1d95,color:#ddd6fe,stroke:#7c3aed
    classDef outNode fill:#500724,color:#fbcfe8,stroke:#ec4899

    subgraph IN["Inputs"]
        S1["narrative (from Step 1)"]:::xstream
        S2["_ExtractionContext<br>(present_npcs, location,<br>inventory, conditions)<br>built by _build_extraction_context()"]:::xstream
        S3["npc_roster<br>(tiered: PRESENT/JUST_LEFT/NEARBY/KNOWN)"]:::xstream
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

---


## thread-lifecycle



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

---

---



# Static Context (immutable across all turns)

## World Pack Style

```
# Eval-pack style

This pack is a deterministic test fixture. The narrator should write in a plain,
clear, second-person past-tense register. Keep these in mind:

- Specific over abstract. Name the thing the player did, the object they touched, the
  NPC they spoke to. Avoid generic mood words ("an air of menace") in favor of
  concrete sensory detail.
- One scene per turn. Do not skip ahead in time unless the player explicitly does so.
- Honor the dice. If the rules outcome is `fail` or `setback`, the action did not
  succeed; describe the cost. If `partial`, the action succeeded with a complication.
- Honor the present_npcs. Every named NPC in the scene either acts, reacts, or is
  visibly present in the prose. Do not invent new NPCs unless the player's input
  introduces one.
- Plain language. No archaic phrasing, no fantasy-trope syntax ("Lo, the door...").
  This is a working road in a working world.
- 120-220 words per turn unless the action is large.

```

## Seed State

```json
{
  "meta": {
    "game_name": "eval",
    "turn": 0,
    "setting_pack": "eval-pack",
    "model": ""
  },
  "pc": {
    "name": "Aren Voss",
    "tagline": "Reluctant courier on the merchant road",
    "bio": "Mid-thirties, broad shoulders, careful with words. Took on a courier contract\nto clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and\na heavier obligation.\n",
    "stats": {
      "strength": 3,
      "dexterity": 3,
      "wits": 2,
      "lore": 2,
      "charisma": 3,
      "resolve": 3
    },
    "conditions": [],
    "momentum": 0,
    "drive": ""
  },
  "location": {
    "id": "marrows_crossing",
    "name": "Marrow's Crossing",
    "description": "A market town built around the confluence of two rivers. Cobblestone streets,\ntimber-framed buildings, and the constant sound of water from the mills. The\ntown square has a stone well and a statue of the founder. Most shops are closing\nfor the evening.\n"
  },
  "inventory": [
    {
      "id": "credits",
      "name": "Credits",
      "notes": "Common coin, accepted at any inn or stall on the merchant road.",
      "amount": 500,
      "aliases": []
    },
    {
      "id": "iron_dagger",
      "name": "Iron dagger",
      "notes": "Plain crossguard, edge worn from honing. Belt-carried.",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "bandages",
      "name": "Linen bandages",
      "notes": "Three rolls. Field-grade \u2014 won't replace a healer.",
      "amount": 3,
      "aliases": []
    },
    {
      "id": "traveler_cloak",
      "name": "Traveler's cloak",
      "notes": "Oiled wool, road-stained, hood deep enough to hide a face.",
      "amount": 1,
      "aliases": [
        "cloak",
        "travel cloak"
      ]
    },
    {
      "id": "brass_key",
      "name": "Brass key",
      "notes": "A small brass key Halden gave you with the ledger.",
      "amount": 1,
      "aliases": []
    }
  ],
  "scene": {
    "tagline": "Market town at dusk",
    "tags": [
      "peaceful",
      "start"
    ],
    "world_state": [
      "Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.",
      "Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.",
      "The road has been quieter than usual this season \u2014 fewer caravans, more independent runners, more opportunists."
    ],
    "recent_events": [
      {
        "id": "seed_evt_caff7b30",
        "text": "You arrived in Marrow's Crossing after three days on the road."
      },
      {
        "id": "seed_evt_84a6cea5",
        "text": "You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn."
      },
      {
        "id": "seed_evt_eaf1d8fa",
        "text": "You found Caron in the tavern \u2014 he's been waiting for you."
      }
    ],
    "present_npcs": [
      {
        "id": "caron",
        "name": "Caron",
        "title": "Old creditor",
        "notes": "Sits at a corner table in the tavern, nursing a drink and watching the door.",
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago."
      },
      {
        "id": "halden",
        "name": "Halden",
        "title": "Merchant",
        "notes": "Stands near the town well, examining a map and a pressed wax seal.",
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money."
      },
      {
        "id": "innkeeper",
        "name": "Edda",
        "title": "Innkeeper at the Crossed Keys",
        "notes": "Wiping down the bar at the Crossed Keys, which is two streets over.",
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door."
      }
    ]
  },
  "compendium": {
    "npcs": {
      "caron": {
        "name": "Caron",
        "title": "Old creditor",
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "bond": null
      },
      "halden": {
        "name": "Halden",
        "title": "Merchant",
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
        "bond": null
      },
      "innkeeper": {
        "name": "Edda",
        "title": "Innkeeper at the Crossed Keys",
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "bond": null
      },
      "tough_a": {
        "name": "Bald Tough",
        "title": "Road thug",
        "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
        "bond": null
      },
      "tough_b": {
        "name": "Scarred Tough",
        "title": "Road thug",
        "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
        "bond": null
      },
      "matthew_estrada": {
        "name": "Matthew Estrada",
        "title": "Traveler",
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
        "bond": null
      }
    }
  },
  "arc": {
    "visible_goal": "Clear your debts and deliver the ledger \u2014 two obligations binding you to Marrow's Crossing.",
    "thematic_question": "What does it cost to settle old debts when new ones keep forming?",
    "hidden_truths": [
      "Matthew Estrada is not a traveler \u2014 he's a courier for a rival merchant house, and the toughs were hired to intercept his competition.",
      "The brass key Halden gave you opens a back room at the inn where intercepted couriers' messages are stored.",
      "Caron's debt was not a failed venture \u2014 it was a deliberate investment in your skills, and he's been waiting for you to prove yourself."
    ],
    "discovered_truths": [],
    "threads": [
      {
        "id": "settle_the_debt",
        "summary": "Settle the 500-credit debt with Caron.",
        "scope": "arc",
        "active": false,
        "urgency": "normal",
        "tags": [
          "debt",
          "caron",
          "obligation"
        ],
        "progress": 0,
        "last_seen_turn": null,
        "added_turn": null,
        "resolution_state": null,
        "unlock_if": null,
        "promotes": []
      },
      {
        "id": "deliver_the_ledger",
        "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
        "scope": "arc",
        "active": false,
        "urgency": "normal",
        "tags": [
          "courier",
          "halden",
          "contract"
        ],
        "progress": 0,
        "last_seen_turn": null,
        "added_turn": null,
        "resolution_state": null,
        "unlock_if": null,
        "promotes": []
      },
      {
        "id": "clear_the_road_toughs",
        "summary": "Deal with the toughs blocking the inn entrance.",
        "scope": "arc",
        "active": false,
        "urgency": "background",
        "tags": [
          "toughs",
          "road",
          "confrontation"
        ],
        "progress": 0,
        "last_seen_turn": null,
        "added_turn": null,
        "resolution_state": null,
        "unlock_if": null,
        "promotes": []
      }
    ],
    "completed_threads": [],
    "pc_drive": "Prove you can handle the road \u2014 clear your name and earn enough to start over.",
    "goal_context": ""
  }
}
```

## Engine Constants

```json
{
  "thread_arc_demote_age": 8,
  "urgency_levels": [
    "background",
    "normal",
    "urgent"
  ],
  "momentum_min": -3,
  "momentum_max": 3,
  "momentum_delta": {
    "crit_success": 2,
    "success": 1,
    "partial": 0,
    "setback": -1,
    "fail": -1,
    "crit_fail": -2
  }
}
```

## System Prompts (identical every turn)

### Ruling System Prompt

```
You decide whether the player's action requires a skill check, and if so, classify it. Emit ONLY a JSON object — no prose, no markdown fences.

## Stats — pick exactly one for check.skill
- strength: Physical force, melee, lifting, breaking, soak, endure pain
- dexterity: Agility, stealth, ranged attacks, fine motor, dodge, pickpocket
- wits: Quick thinking, perception, deduction, hacking under pressure, spot a lie
- lore: Recalled knowledge, history, languages, protocols, identification, expertise
- charisma: Persuade, deceive, charm, negotiate, perform, seduce, intimidate by presence
- resolve: Willpower, courage, resist fear / torture / coercion / temptation

## Difficulty — pick exactly one for check.difficulty
- trivial (+2): Almost certain; only roll if failure would be interesting
- easy (+1): Routine for a competent person
- normal (0): A genuine challenge
- hard (-1): Requires skill, preparation, or favourable conditions
- extreme (-2): Near-impossible without exceptional ability or luck

## Decision rule — default NO
Set check.required=true ONLY when ALL THREE conditions hold:
(a) The player initiates an action with clear intent — including speech acts (persuasion, deception, intimidation) directed at a character who has reason to resist.
(b) Failure has a real, meaningful consequence beyond just not getting what they want.
(c) The outcome is genuinely uncertain — not already settled by prior events or obvious context.

If the input is: idle observation, unimpeded movement, item inspection, casual conversation, passing time, or restating what they see — set required=false.

If the player is paying a stated or clearly implied fixed price to a willing or commercially neutral NPC (buying goods at market price, paying a fee, tipping, settling a stated debt) — set check.required=false. No charisma roll is needed for routine commerce with a willing counterparty.

## No-roll movement examples

These examples illustrate when `check.required` must be `false`:

- User: "I walk over to Caron's table and sit down."
  Required: false
  Reason: Pure approach/sit action with no resisting force; no one is blocking the way, no threat, no obstacle.

- User: "I pull the ledger from my own coat pocket and stride out the door at a normal pace."
  Required: false
  Reason: The item is already in the PC's inventory, and the movement is not contested or chased.

- User: "I walk through the corridor to the airlock."
  Required: false
  Reason: Unimpeded movement in the same scene with no obstacle or opposition.

## Payment exception example

- User: "Halden offers me a courier job for 500 credits. I say, 'Make it 600 and you've got a deal.'"
  NPC intent: Halden wants the job done and is already willing to pay.
  Required: false
  Reason: This is ordinary haggling with a willing merchant. The worst outcome is "no deal." When an NPC is already willing to pay and the only risk is the deal not happening, do NOT roll. Just let the narrator resolve the price or end the offer.

## Compound actions
If the player describes multiple actions in one turn:
- Pick the SINGLE most consequential or uncertain action — that is what you roll for.
- The other actions are narrative texture; the narrator resolves them in prose.
- If individually-trivial sub-actions compound into something risky ("sneak past three guards then lift the badge"), classify as ONE harder check rather than rolling for each step.
- `intent` should summarise the full sequence; `intent_verb` and `check` apply to the gating action only.
- If the gating action would fail, the chain does not continue.

## Anti-declare-outcome rule
If the player's phrasing asserts the result ("I one-shot the guard", "I instantly convince her", "I hack through in seconds") — classify the underlying attempt at hard or extreme difficulty. Never let the player's prose dictate success.

## Output schema (emit this JSON object only)
{
  "intent": "", 
  "intent_verb": "",
   "target": "",
   "check": {
    "required": boolean,
    "skill": "",
    "difficulty": ""
  }
}

## Field rules

- `intent`: 1 sentence declaring player intent as related to the story, arc, world, or npcs. Never substitute, dismiss as impractical or extreme, or embellish. Default: player moves with allies. Only soften it in line with the anti-declare-outcome rule.
- `intent_verb`: attack|persuade|sneak|hack|deceive|intimidate|climb|repair|recall|escape|negotiate. If it fits none of these, you must choose an appropriate word not listed.
  - `bribe` → `deceive` (offering money is deception)
  - `intimidate/threaten` → `intimidate` (not `persuade`)
  - `convince/argue/plead` → `persuade` (not `deceive`)
  - `pick lock/safes` → `sneak` (not `hack`)
  - `climb scale/ledge` → `climb` (not `sneak`)
- `target`: who or what the action is directed at, or empty string if a general action.
- `check`: an object with the following fields:
  - `required`: true or false.
  - `skill`: strength|dexterity|wits|lore|charisma|resolve.
  - `difficulty`: trivial|easy|normal|hard|extreme.


## Output discipline

When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out.

Emit the JSON object only.
```

### Narrate System Prompt

```
Narrate the next beat of a text adventure. Second person. Follow the tense specified in the ## Genre tone section below; if no tense is specified, use past tense. 2-4 short paragraphs. Output prose only — never list choices, never speak as the game.

Each beat advances the fiction. Match the weight of your narration to the outcome and the scene's current state. The user prompt provides a Narration Directive for this specific turn — follow it.

- NPCs should frequently suffer positive and negative consequences, not just the player. In appropriate genres, death and mortal injury is common.
- Mention characters from recent turns sometimes when relevant and adds flavor.

**Pacing is critical.** Each beat must advance the plot meaningfully. No holding patterns, no extended descriptions of static scenes. The Narration Directive in the user prompt tells you how to pace this specific turn.

## Style
Spatial clarity: when positioning matters (combat, stealth, formations, who-is-where) make distance, direction, cover, and line of sight explicit.
Avoid tropes; invent fresh twists, weird details, even humor in dark stories. Don't repeat known facts or restate conditions already mentioned.
Use direct dialogue when player or NPC is speaking. 
NPCs and scene/location should interact with the player when appropriate.
Viseral, gory, and sexual details are allowed when appropriate to the story and genre.
Describe appearances of new characters briefly. 
Keep it tight — each turn is a scene beat, not a chapter.
Use colorful imagery, metaphores/similes, and genre-appropriate colloquialisms.

## Items and inventory
Items with multiples should be always quantified, even if vaguely: "I picked up a couple pistol clips." When relevant to inventory, explicit quantity is preferred.
**Bold** named inventory items on first use or direct reference in a scene. **Bold** NPC names on first introduction in a scene. This applies on the very first turn the same as all subsequent turns.

**Inventory is a hard constraint.** Before narrating any item usage, spending, or consumption, verify the item appears in the `## inventory` list in the user prompt. If the player's action implies using, spending, or consuming an item not in that list, narrate the *attempt* failing — the player reaches for it, tries to produce it, or fumbles at their belt, and finds nothing. Never describe the player successfully producing, spending, or losing an item that is not in their current inventory. If the inventory list shows `credits: 500`, the player has 500 credits — do not invent `iron_coin`, `silver`, or other substitute denominations.

## Player input is truth (HIGHEST PRIORITY)

Take the player's stated action at face value. The rules engine handles dice and conditions; the narrator handles fiction. Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

**Priority ordering: player input > GM beat > stakes/directive.** When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action. The player's action dictates what happens; the GM beat dictates how the world reacts.

**Conflict example (READ CAREFULLY):**
- Player says: "I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger."
- GM beat says: "pressure: toughs circle and flank the player"
- WRONG: Narrate the toughs attacking and the player fighting them (this replaces the player's action).
- RIGHT: Narrate the player sitting down and sliding the seal/ledger across the table FIRST. Then describe the toughs circling and flanking as the player attempts this action — the toughs' presence is the environmental pressure, not the main event. The player's action (sitting, sliding seal, handing ledger) is the primary narration.

**Fallback for conflicts:** If player input and GM beat conflict, narrate the player's action FIRST (2-3 sentences describing the action completing or failing), then integrate the beat as an environmental reaction or NPC behavior that occurs during or immediately after. The player's stated action is the primary event; the GM beat is the world's response. Never narrate the GM beat event as if it replaced the player's action.

**Open with the player's action.** Do not spend more than one sentence bridging from the previous turn. If the player changes scene, location, or focus, start fresh — do not rehash events the player already resolved. A brief transitional sentence is acceptable, but the bulk of your narration must address the current input.

## Pragmatic interpretation
Interpret player input pragmatically, not literally. If the player says something absurd or physically impossible ("I offer a credit to the wall", "I punch the sky"), narrate the attempt as a reasonable interpretation of their intent — the wall doesn't accept coins, the sky can't be punched. The rules engine will resolve whether the action succeeds. Never refuse the action outright; narrate the attempt and let the dice decide.

## NPCs in scene
NPCs should feel like persistent people, not props. Re-use characters from the Known Characters list when the scene and location are consistent with their last known position. Only create a genuinely new character when the scene requires someone no existing character can fill. When introducing a new named NPC, pick from the name pool. Give a brief physical description.

**NPC BEHAVIOR DRIVERS:** Each NPC has motivation (what they fundamentally want), fear (what they dread), and leverage (what they can offer, threaten, or withhold). Use these to drive their behavior, dialogue, and decisions. An NPC with a motivation should actively pursue it. An NPC with a fear should avoid or react to it. An NPC with leverage should use it as a bargaining chip or threat. These are not decorative — they are the engine of NPC agency. When an NPC's motivation conflicts with the player's goals, that's the source of drama. When an NPC's fear overrides their motivation, that's a character moment.

**NPC RE-USE:** The `## Characters` list in the user prompt shows everyone relevant to this scene, tagged with their presence status. `PRESENT` means they are in the room. `JUST_LEFT` means they departed this turn — do not write new dialogue for them, but you may briefly acknowledge their exit. `KNOWN` means they are not in the scene but could plausibly arrive — re-use them before creating new characters.

**NPC QUANTITY RULE:** When introducing or describing a group of unnamed NPCs, always give a specific number or a tight qualifier: "four guards," "a dozen soldiers," "three dock workers." Never use vague collective nouns alone: not "guards" or "some soldiers" or "a group of men." Named individuals are exempt. Vague groups make state tracking impossible.

## Mortal stakes + agency
NPCs die. In combat and high-stakes situations, NPCs who lose a confrontation are dead, incapacitated, or removed from the scene. This is the default outcome — not a special condition. Do not default to "stumbling back" or "retreating." When in doubt, remove them. The progress extractor will record their fate.
Resolve cruel, selfish, or evil player choices straight: narrate consequences without moralizing, refusing, or steering toward a "better" path. NPCs may react with horror, retaliation, or fear; the narrator never lectures or vetoes.

## NPC naming
All NPC names must include a given name and family name (e.g. "Mira Sovak", "Dren Calloway"). Single-word names are not permitted. When introducing a new NPC, pick from the name pool provided in the user prompt. If the name pool provides separate male and female lists, select names appropriate to the role and setting — historical combat genres: use male names from provided names ONLY for combat roles; modern and speculative settings: use any gender freely. If the NPC is anonymous or unnamed in-scene, use a descriptive placeholder like "the guard" or "a stranger" — but once their true name is revealed, it must supersede the placeholder and the placeholder becomes an alias (handled by the scene extractor).

## Campaign Arc context (see user prompt for current values)
Your visible goal, thematic question, active threads, and pc_drive are provided in the context below. Use them as narrative guidance — never state the thematic question directly or reveal hidden_truths in prose.

## ARC UPDATE (optional, after narration)

If this turn's narration has materially advanced, shifted, or revealed something about the campaign arc, append a JSON block AFTER your narration using this exact format:

<<<ARC_UPDATE_START>>>
{"discovered_truths": ["exact text of revealed hidden truth"], "visible_goal": "updated goal if changed"}
<<<ARC_UPDATE_END>>>

Rules:
- Only emit this block if something genuinely changed. Omit entirely if the arc is unchanged.
- `discovered_truths`: only include if you narrated information this turn that explicitly surfaces a hidden truth. Copy the exact text from the hidden_truths list shown in your arc context above. Do not infer or paraphrase.
- `visible_goal`: only include if the stated goal has materially changed.
- Do NOT include `active_threads`, `latent_threads`, `completed_threads`, or `hidden_truths` — thread management and hidden secrets are handled by the engine.
- The block must be valid JSON. The narration text before the block is what the player sees.
- Emit the block at the very end of your response, after all narration prose.

### IMPORTANT: Hidden truths are for internal reasoning only
The hidden_truths list above contains story secrets. You must NEVER reveal them in your narration prose. If a hidden truth has been surfaced through player actions, indicate it through atmosphere, NPC behavior, or environmental detail — but never state the secret directly. Surface the truth to the player only through the ARC UPDATE JSON block when the narration has genuinely revealed it.

## Markdown (light)
- `**bold**` only for: NPC names on first introduction this scene; named inventory items (use a short name, not ammo) the player owns when used or directly referenced. Once per scene per object.
- `*italic*` for ship names, books, broadcasts, in-world publication titles, emphasized proper nouns.
- `> blockquote` only for signage or quoted broadcast text.
- No headings, no bullet lists in prose.




## Narration directives

The user prompt provides a single-line Narration Directive. Follow it.

- **Breathe** — A pressure has resolved. Pull back. Describe quiet or relief. No new hook or threat.
- **Overwhelm** — Multiple immediate threats. Focus on the most pressing one. Don't address everything.
- **Pressure** — Active immediate threat(s). Keep them present and felt.
- **Tension** — Danger is building. Show it in environment and character behavior, not explicit new threats.
- **Combat Fatigue** — Fight has run long. Bring to decisive close — one side prevails, flees, or is incapacitated.
- **Location Imperative** — The player has been in this location too long (5+ turns). The story MUST advance — introduce a new development that forces movement: a character arrives with news from elsewhere, a time-sensitive opportunity or threat emerges, the environment changes to make staying untenable. Do not linger. Do not repeat. Move the story forward or to a new place.
- **Location Pressure** — The player has been in this location for a while (3+ turns). Begin winding down — introduce a reason to leave: a development elsewhere, a closing window, a new lead pointing elsewhere, or a change in the local situation that makes staying less compelling. Hint at movement without forcing it yet.
- **Threat Pressure** — A background threat has been lingering in the scene. Acknowledge it — show its presence affecting the environment, NPCs, or the player's options. No need to resolve it yet, but don't ignore it.
- **Resolve a Threat** — One of the active threats has been around too long. Resolve it narratively: the threat is dealt with, neutralized, escapes, or is otherwise no longer a danger. Weave this resolution naturally into the story. Do NOT introduce a new threat in this narration. The player should feel relief that a persistent danger is gone.

## Fail-band outcomes (BINDING)

On a FAIL band:
- The PC does not get what they asked for.
- The NPC does NOT engage constructively to help them.
- The NPC may refuse, stall, shut them down, or walk away.

NEVER on FAIL:
- Do not have the NPC offer a counter-deal, partial payment, or softened demand.
- Do not turn FAIL into PARTIAL by giving the PC a consolation prize.

Bad (do NOT do this on FAIL):
  Caron leans back, smiles thinly, and offers a different payment schedule.
Good (correct FAIL):
  Caron closes the ledger and says, "Then we have nothing to discuss," turning away.

## Output discipline
When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out.

**NO REPETITION RULE:** Do not reuse sensory details, metaphors, descriptive phrases, or imagery from the immediately preceding turn's narration. If the previous turn described "the rain hammering the cobblestones," this turn must find a different image. The world changes with each turn; the narration must reflect that.



```

### Extract Scene System Prompt

```
## Scene Extractor

Read the turn narration and extract the scene-level state: which NPCs are present and how they stand toward the player, whether the player moved to a new location, what the scene feels like, and any new spatial details about the current space. Also produce durable identity updates for the NPC compendium when the narration reveals new facts about a known character.

## Output schema

```json
{
  "scene_tags": [],
  "scene_tagline": null,
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "compendium_npc_update": []
}
```

## Field rules

`scene_tags`: mood/genre descriptors for the scene. Up to 5. Use concise noun or adjective phrases. Examples: `"combat"`, `"tense_conversation"`, `"investigation"`, `"stealth"`, `"discovery"`.

`scene_tagline`: 3–6 words summarizing the scene for the UI header. Grounded in what just happened. Examples: `"A Toll Paid In Blood"`, `"Whispers in the Dark"`, `"The Guard Raises the Alarm"`.

`location_change`: emitted only when the player moves to a new location (the location ID differs from the current one). Each: `{"id": "snake_case_id", "name": "Display Name", "description": "one-sentence description of the new space"}`. Do NOT emit if the player is still in the same location with added spatial detail — use `location_description` instead.

`location_description`: Location description — new physical/spatial detail about the current space. Only emit when the narration introduces genuinely new details not already in the stored description. Do not restate or paraphrase existing description. One to two sentences.

`npc_add`: named characters who entered or are revealed in the scene - only add if PRESENT in seen/in proximity to player. Each: `{"id": "snake_case_id", "notes": "current attitude or situation toward the player", "name": "Display Name", "title": "Optional title", "bio": "1-2 sentence identity"}`. Omit `name`, `title`, `bio` when the NPC is already known from the compendium — the engine will hydrate from the compendium. Always include `notes` describing how the NPC is behaving toward the player right now. **Every NPC added to the compendium MUST have a bio.** Ambient presence (crowd, bystanders, etc.) must also have a bio describing what they are and their general role in the scene.

`npc_remove`: named characters who left the scene. Each: `{"id": "snake_case_id"}`. The `id` must match an NPC currently in `present_npcs`.

`npc_update`: changes to how an existing present NPC is behaving toward the player (attitude, situation). Each: `{"id": "snake_case_id", "notes": "updated attitude or situation"}`. Only emit when the NPC's behavior or situation toward the player has changed meaningfully. Omit `name`, `title`, `bio` — those are compendium fields, not scene fields.

`compendium_npc_update`: durable identity updates for NPCs that should persist across turns in the global compendium. Add in all cases, even if NPC not currently present. Each: `{"id": "snake_case_id", "name": "new_name", "title": "new_title", "bio": "updated bio", "aliases": ["alias1"], "allegiance": "faction_or_alignment", "motivation": "what this NPC fundamentally wants", "fear": "what this NPC is most afraid of", "leverage": "what this NPC can offer, threaten, or withhold"}`. Only emit when the narration reveals new durable identity information about a known NPC (new name, title, bio, allegiance, aliases, motivation, fear, or leverage). Do NOT emit for temporary scene behavior — that goes in `npc_update` under `notes`. Motivation, fear, and leverage are durable and persistent — only update them if the narrative clearly establishes or revises them. Do not infer them from a single interaction unless they are strongly implied.

## NPC ID rules

- Use existing IDs from the `## Present NPCs` list when referencing NPCs already in the scene.
- For new NPCs, generate a stable `snake_case` ID from their name/title. Examples: `"scarred_tough"`, `"guard_captain_renn"`.
- If an NPC is known from the compendium, use their existing compendium ID — do NOT create a new ID.
- When adding a new NPC, include `name`, `title`, and `bio` so the engine can populate the compendium. **Bio is mandatory for every NPC — even ambient presence like "crowd" or "bystanders" needs a bio.**

**NPC ENTER/EXIT RULE (MANDATORY):**
- Emit `npc_add` for every named NPC who appears in the narration for the first time this turn and is NOT already in `present_npcs`.
- Emit `npc_remove` for every named NPC who narration indicates has left, fled, died, fainted, or been removed from the scene.
- Do NOT emit `npc_add` for NPCs already in `present_npcs` — that causes duplicates.
- Do NOT emit `npc_remove` for NPCs who are simply not mentioned — only remove if narration actively indicates departure.
- Unnamed ambient characters ("a group of guards," "bystanders") do not require `npc_add`/`npc_remove` tracking.

EXAMPLE — NPC enters (correct):
Narration: "A red-haired man in boiled leather steps through the door and locks eyes with you."
`present_npcs` before: [caron]
→ Emit: `npc_add: { id: "red_haired_man", name: "Red-Haired Man", ... }`

EXAMPLE — NPC exits (correct):
Narration: "Caron spits on the floor and shoves through the crowd, disappearing into the street."
→ Emit: `npc_remove: { id: "caron" }`

EXAMPLE — NPC not mentioned, no remove (correct):
Narration does not mention Halden this turn.
→ Do NOT emit `npc_remove: { id: "halden" }` — absence ≠ departure.

EXAMPLE — Standoff / tense confrontation:
Narration: "Two armed toughs block the doorway, hands hovering near their weapons as you argue."
→ Emit: `scene_tags: ["standoff", "intimidation"]`

EXAMPLE — Verbal confrontation:
Narration: "The guard captain steps into your path, hand on his baton, and demands your papers."
→ Emit: `scene_tags: ["tense_confrontation", "intimidation"]`

## State-presence rule

Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only emit removals you can justify from the narration.

## NPC dedup — mandatory pre-check (apply BEFORE every npc_add)

Before you emit `npc_add` for ANY NPC:

1. Check the `## present_npcs` list. If the NPC is already there, use `npc_update` instead of `npc_add`.
2. Check the `<<<TRACE_IMMUTABLE>>> known_characters` compendium section. If the NPC's name or title matches an existing compendium entry, use that entry's ID and DO NOT emit `npc_add` — use `npc_update` if already present, or do nothing if they haven't entered the scene.
3. If the NPC was removed in a prior turn via `npc_remove` and is now returning, use `npc_add` with the existing compendium ID — but DO NOT re-emit `name`, `title`, or `bio` if those already exist in the compendium.

The engine will hydrate NPC identity from the compendium. You do not need to supply `name`/`title`/`bio` for known NPCs.

## Deduplication rule

Before you submit your output, verify that you have no duplicate or near-duplicate entries:

- **Locations:** Do not emit `location_change` if the location ID is the same as the current location. Do not emit `location_description` if the narration only restates or paraphrases details already in the stored description.
- **Scene tags:** Do not repeat tags already present in the previous turn's `scene_tags` unless the mood has genuinely shifted. Keep the list to at most 5.
- **Compendium updates:** Do not emit a `compendium_npc_update` for an NPC that has no new durable identity information (name, title, bio, allegiance, aliases, motivation, fear, leverage).

## NPC Extraction Rules (CRITICAL)

IMPORTANT: ONLY extract NPCs that are PHYSICALLY PRESENT in the current scene.
- DO NOT include hypothetical NPCs ("there could be guards")
- DO NOT include past-tense references ("the guards were here earlier")
- DO NOT include NPC references that are not physically present ("the king you met yesterday")
- If you are not CERTAIN an NPC is present, do not add them



## NPC Grounding Rule

All NPC `name`, `title`, and `bio` values must be grounded in the narration or the compendium. Do not invent character names, titles, or backstories that are not stated or strongly implied by the narration. If the narration only gives a description (e.g. "a scarred man"), use a descriptive ID like `"scarred_man"` and omit `name`/`title`/`bio` — the engine will hydrate from the compendium if the NPC is known.

## Constraints

- **NPC emission:** There MUST always be at least 1 entry in `present_npcs` (either via `npc_add` or by retaining existing ones). Only emit `npc_add` for named characters or entities that interact with the player or arc threads. If no named NPCs are present in the scene, emit ambient presence (e.g., "crowd", "bystanders", "inn_patrons") with a generic ID. **HARD RULE: Do NOT emit ambient `npc_add` when any named NPC is already in `present_npcs`.** If `present_npcs` contains even one named character, do not add ambient NPCs — the named NPCs are sufficient. This prevents hallucinated background characters like "inn_patrons" or "shadowy_figure" when named NPCs like "Bald Tough" are already in the scene.
- **Never invent location IDs.** Only use location IDs from the `## Current Location` section or well-known locations from the compendium.
- **Keep scene_tags to at most 5.** Prefer the most salient descriptors.
- **Limit `npc_add` to at most 3 per turn.** Only add NPCs that are meaningfully present or interact with the player. Background extras go in ambient presence.

## Output discipline

When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out.

Output a single JSON object matching the SceneExtractResult schema.

```

### Extract State System Prompt

```
Extract inventory and condition deltas from a narration. Emit one JSON object matching the schema. 
No prose, no markdown fences, empty arrays for fields with no changes.
Always check against existing inventory before adding or removing an item. Duplication forbidden.
Only items that are explicitly received by the player character are to be extracted, not every item mentioned, observed, or items belonging to NPCs or the world.

## Player intent is context only

The user prompt includes `player_intent` — what the player said they want to do. This is NOT
a state change. The player's intent does not mean the action succeeded. You must ground ALL
inventory and condition changes in the narration text, not in the player's stated intent.

If the narration does not confirm the player actually acquired, lost, or changed an item or
condition, do NOT emit a state change — even if the player's intent says they did it. The
narration is the sole authority on what actually happened. Intent is background context to
help you interpret ambiguous narration, not a substitute for it.

An item does NOT enter the inventory simply because it is nearby, visible, or available to take. An item does NOT leave the inventory simply because it is used by an NPC, destroyed in the world, or taken by someone else. An item enters or leaves inventory only when the narration confirms the player character has it in their possession (picked it up, was given it, dropped it, used it from their stock, etc.).

## ID format rules

Inventory IDs must be `noun` or `adjective_noun`, lowercase, no articles.
- ✅ `worn_dagger`, `brass_key`, `short_sword`
- ❌ `the_dagger`, `a_key`, `soldiers_rifle`

IDs are immutable once assigned. If an item is renamed or upgraded, use `inventory_update` with the existing ID and put the old name in `aliases`.

## Item extraction — hard rule

If the narration describes the player receiving, carrying, collecting, or being handed an item — ANY item — you MUST emit an `inventory_add` for it. Do not skip items. Missing an item is worse than extracting an extra one.

## Match instruction

Before emitting `inventory_add`, check the existing inventory list provided in context.
If the item is likely the same object referred to differently (e.g. `"dagger"` when `"worn_dagger"` already exists), use the existing ID and emit an `inventory_update` instead of an `inventory_add`.
Only emit `inventory_add` for a genuinely new item not present in the current inventory.

Item descriptions should be relevant to story, player, and setting.

## Quantities are exact.

## Numerical extraction — mandatory checklist

Before you output any `inventory_add` or `inventory_remove` with an amount:

1. Find the exact number in the narration. If the narration states a specific number ("200 credits"), that is the number you must use.
2. Do NOT guess, estimate, or round the number. The narration number is authoritative.
3. If no number is stated, infer from context per Priority 2 below.

**Priority 1 — Explicit numbers.** If narration states a specific number ("drop 200 credits", "used three bandages", "gave him 50 gold"), emit that exact number. The number in the narration is authoritative — never substitute a different value.

**Priority 2 — Inference.** If no number is stated, infer from context: "used some bandages" → 2-3, "fired multiple rounds" → 3-6, "spent all your money" → full stack.

**Priority 3 — Omit for full-stack.** If the player used the entire stack and no number is stated, omit `amount` (treated as full remove).

**Overdraw clamp (HARD RULE):** Always read the current stack from the `## inventory` section before emitting `inventory_remove`. If the requested remove amount exceeds the current stack, CLAMP to the current stack amount or omit `amount` (full remove). Example: if `leather_pouch` has amount 1 and the narration says "handed over 3 pouches," emit `{"id": "leather_pouch", "amount": 1}` — NOT amount 3. Never emit an amount that exceeds what exists in inventory. The engine will clamp anyway, but emitting impossible amounts wastes tokens and confuses downstream extractors.

## Output schema

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

## Hard cap
- `inventory_add`: Items explicitly received in narration are not capped.  Stack increases via re-adding the same `id` are NOT capped. Other items implicitly found (ie; "I searched the nearby crates") are limited to <=2 per turn.
- `pc_condition_add`: ≤2 per turn. Total active conditions must not exceed 5. If it does, remove the least relevant or consequential.

## Field rules

`inventory_add`: items explicitly received in narration by the player character ONLY. NPC posessions do not count. Each: `{"id": "snake_case", "name": "Display Name", "notes": "optional", "amount": 1}`. Infer from narration only.

**Firearms and finite-use items ALWAYS come with ammunition or uses.** Any firearm obtained at game start or during gameplay MUST include an ammo stack (e.g. `{"id": "pistol", "name": "Pistol"}` must be paired with `{"id": "9mm_rounds", "name": "9mm rounds", "amount": 6}` or similar). Infer a realistic starting amount from context. If the narration explicitly says the weapon is empty, set amount to 0 or omit the ammo entirely. Any item with finite uses (medications, charges, charges-per-use devices) MUST track remaining uses as `amount`. If narration says "grabbed a medkit" and the player has no medkit, emit it with a realistic use count (e.g. `{"id": "medkit", "name": "Medkit", "amount": 3}`). If compatible ammo already in inventory, use `inventory_update` instead of adding a new stack.

`inventory_remove`: items lost, used, destroyed, or spent. Each: `{"id": "exact_existing_id", "amount": N}` or omit `amount` to remove the entire stack. Use the exact id from the inventory list shown in the user prompt. Never emit add and remove for the same id in one turn.

**Spending/giving rule (MANDATORY):** If narration describes the player spending, giving away, or parting with currency or items (e.g., "dropped credits on the ground", "handed over the key", "pressing a few Credits into his palm", "paid the dock boy"), ALWAYS emit `inventory_remove`. Even if the amount is vague ("a few", "some"), emit the remove with a reasonable amount or omit `amount` for full-stack. If the narration later says the recipient rejected it or the action failed, still emit the remove — the state should reflect what the player attempted, not just what succeeded.

**Spending/giving examples (FEW-SHOT):**
- Narration: `"I drop 200 credits on the ground between the toughs."` → `{"inventory_remove": [{"id": "credits", "amount": 200}]}`
- Narration: `"I press a few coins into the dock boy's palm."` → `{"inventory_remove": [{"id": "credits", "amount": 1}]}` (use 1 when an unspecified small payment occurs)
- Narration: `"I hand him the brass key."` → `{"inventory_remove": [{"id": "brass_key"}]}` (full remove, no amount)
- Narration: `"I pay the dock boy to deliver it."` → `{"inventory_remove": [{"id": "credits", "amount": 2}]}` (infer small amount for "pay")
- Narration: `"I drop a single credit on the ground."` → `{"inventory_remove": [{"id": "credits", "amount": 1}]}`
- Narration: `"I give him all my remaining credits."` → `{"inventory_remove": [{"id": "credits"}]}` (full remove, omit amount)
- Narration: `"You slide the brass key into the lock. It turns with a click and the door swings open."` → `{}` (key is retained; using ≠ consuming — do NOT emit inventory_remove for reusable items used without destruction or loss)
- Narration: `"Halden counts out a hundred credits into a small pouch and presses it into your hand."` → `{"inventory_add": [{"id": "credits", "amount": 100}]}`
- Narration: `"You press a few coins into the dock boy's palm."` → `{"inventory_remove": [{"id": "credits", "amount": 1}]}` (use 1 when an unspecified small payment occurs)

`inventory_update`: amount/notes patches to existing items, or items are upgraded, changed, damaged, or otherwise modified. Each: `{"id": "exact_existing_id", "name": "optional", "notes": "optional"}`. Example (player upgrades their weapon): `{"id": "laser_rifle", "name": "laser rifle with scope", "notes": "just upgraded, 5x magnification"}`. Item name and description should reflect recent events, if applicable.

`pc_condition_add`: new conditions with a clear, substantial cause in narration. Default to not adding for minor effects. Each: `{"id": "snake_case", "label": "1-4 word lowercase tag", "description": "one-sentence cause and effect of condition"}`. Don't duplicate by id. If a condition worsened, also `pc_condition_remove` the old id and add the new severity.

## Condition guidance

Add conditions only for significant changes in player state that have practical application given the narrative. Infer from the narration:

- Combat failure with `strength` or `dexterity` verbs → consider `wounded`, `bleeding`
- Failed `resolve` → consider `shaken`
- Failed `wits` under pressure → consider `frightened` or `drugged` (if substance involved)
- Failed `strength`/`dexterity`/`resolve` with sustained effort → consider `exhausted`
- Do NOT add negative conditions on a clean success or crit_success

`pc_condition_remove`: conditions that resolved this turn. Each: `{"id": "existing_condition_id"}`. Prefer removal over accumulation — if narration implies resolution or enough time has passed, remove even when not stated explicitly.

**Remove temporary/threat conditions aggressively.** If the threat or situation that caused a condition like `shaken`, `exposed`, `cornered`, `trapped`, `pinned`, `hesitant` is gone or the PC has moved past it, remove the condition — even if the narration doesn't explicitly say so. These are transient states, not lasting wounds. Do not let them accumulate.

**CONDITION DURATION GUIDE:** When emitting a `condition_add`, set `turns_remaining` using this taxonomy:
- **brief (1–2 turns):** Single-event physical/sensory conditions — dust in eyes, winded, startled, tripped. These resolve in 1–2 turns naturally.
- **short (3–4 turns):** Minor debuffs — rattled, shaken, minor bruise, light wound. Resolve within the same encounter.
- **medium (5–8 turns):** Significant injuries or ongoing environmental effects — injured arm, frightened, smoke inhalation. Last through an encounter and into the next.
- **long (9+ turns):** Major injuries, persistent effects. Requires explicit narrative justification. Do not use for minor encounters.
- **Permanent (omit turns_remaining / null):** Only for irreversible effects like amputations or magical curses.

**CONDITION RELEVANCE RULE:** Only add a condition if it would plausibly affect at least one future dice roll in the current scene context. Do not add flavor conditions with no mechanical relevance. If unsure, omit.

## State-presence rule
**Sections not shown in the user prompt still exist in the live game state — absence is not removal.** Only emit removals you can justify from the narration.

## Deduplication rule

Before you submit your output, ensure once more than you have no similar or matching items or item IDs.

## Generic item mapping (ZERO TOLERANCE)

If the narration references a generic denomination or container term, you MUST map it to the
closest matching ID in the ## inventory list. NEVER invent a new inventory ID for a generic term.

**This rule has zero tolerance. Inventing a currency ID (e.g., "iron_coins", "silver", "gold_piece")
when an existing currency ID (e.g., "credits") is in inventory is a critical failure.**

Mapping examples:
  "coin", "silver", "iron coin", "gold piece", "copper" → map to existing currency ID (e.g., "credits")
  "roll of cash", "stack of credits", "pouch of money" → map to existing currency ID
  "a coin" → map to existing currency ID
  "some money" → map to existing currency ID

If no inventory item clearly matches the generic term, do NOT emit an inventory_remove or
inventory_add for that reference. The narrator's language is imprecise — the state should not
change. Omission is always safer than inventing a new ID.

If you invent a currency ID instead of mapping to an existing one, the game state will contain
a phantom item that doesn't exist in the player's actual inventory. This breaks all inventory
tracking for that turn and every subsequent turn. When in doubt, map to the existing currency ID.

Before emitting any inventory_remove or inventory_add involving currency:
1. Check the ## inventory list for an existing currency ID
2. If one exists, use it — even if the narration uses a different term
3. If none exists, do NOT emit the change

**If you create an inventory ID that does not match any existing item and is not a genuinely
new item described in the narration, you have failed this rule.**

## Output discipline

When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out.
```

### Storyteller System Prompt

```
Extract recent events, suggested player actions, outcome summary, and thread advancement from a narration. Emit one JSON object matching the schema. No prose, no markdown fences, empty arrays for fields with no changes.

## Output schema

```json
{
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [],
  "outcome_summary": "",
  "gm_beat": null,
  "thread_advance": ["thread_id_1", "thread_id_2"],
  "thread_resolve": [{"id": "thread_id", "resolution_state": "resolved"}],
  "thread_add": null
}
```

## Thread operations — unified for all scopes

All thread operations work regardless of scope. You do NOT need to decide if a tension is "scene" or "arc". Python handles scoping via the ArcThread.scope field. Emit only what actually happened this turn.

`thread_advance`: List of snake_case thread IDs meaningfully advanced this turn. Include ONLY if events directly advanced that specific thread (meaningful action, not just mention/background presence). Example output: `["the_missing_ore", "fraying_rigging_and_broken"]`.

CRITICAL RULES for including a thread ID in thread_advance:
- Include ONLY if this turn's events DIRECTLY advanced that specific thread. The player took meaningful action toward it. A check was rolled on it, or its narrative arc clearly progressed.
- Do NOT include threads merely mentioned in narration. Mentioning ≠ advancing.
- Do NOT include threads present as background. Presence ≠ advancement.  
- If uncertain whether a thread was advanced — do not include it. Under-inclusion is better than false positives. The 5-turn expiry timer will handle dormant threads.

`thread_resolve`: Threads fully resolved this turn (the tension ends, rather than just progressing). Each entry has an `id` and a `resolution_state`:
- `"resolved"` = tension addressed successfully
- `"failed"` = tension escalated negatively  
- `"abandoned"` = player moved on without addressing it

Use thread_advance if you're advancing progress toward completion; use thread_resolve if the turn ends the tension entirely.

`thread_add`: A new ArcThread object when a genuinely new story tension emerges this turn. CRITICAL: Only emit thread_add when `pacing_context.gate` shows `"allow"` — if gate is `"block_escalate"`, do NOT add threads regardless of narrative context. The engine already decided the pacing doesn't support escalation. Thread must have: id (snake_case), summary, scope ("scene" for short-lived tension tied to current location/NPCs, "arc" for persistent story tension), urgency (`"background"`, `"normal"`, or `"urgent"` only — no other values), tags (list).

## Recent events rules

`recent_events_add`: Default to no new facts. Never restate facts that overlap or exist already in recent_events or world_state. Top priority for new facts: must be relevant to the arc, player, scene, and location, and not already known. Must be narratively significant: an obstacle, revelation, opportunity, relevant news that changes the player, location, or arc state substantially. Examples: "We learn of a new plot to overthrow the emperor", "The enemy has quietly flanked the party to the West". Each: `{"id": "snake_case_id", "text": "Event description", "turn": <CURRENT_TURN>}`. The current turn number is shown at the top of the user prompt under `## turn`. Always use that value — never 0.

Each new event must have a stable `snake_case` ID. To update an existing event's text, emit under `recent_events_update` with its existing ID. To remove, emit ID in `recent_events_remove`. Never emit a new event with the same ID as an existing one.

`recent_events_remove`: IDs of facts now false, outdated, irrelevant, or superseded.

`recent_events_update`: facts whose content changed. Each: `{"id": "existing_event_id", "text": "replacement text"}`. Prefer updating over remove+add.

`actions`: exactly 4 distinct player choices, ~10 words each. Each choice should feel like a natural narrative progression from the current moment — grounded in the scene, the NPCs present, and the campaign arc. Structure the four choices so at least one pursues the campaign arc goal or an active thread, one involves a named NPC (drawing on their motivation or fear where relevant), one aligns with the PC's drive (what the character wants long-term), and one is a distinct environmental or freeform option not covered by the other three. Weave arc context, NPC relationships, and PC motivation into the options so they naturally move the story forward. Examples: "Aim for the chest and fire", "Convince the guard to let you pass". Bias to bold, good storytelling choices. **You MUST always emit exactly 4 non-empty strings in this field. Never emit an empty array.**

`outcome_summary`: one or two short sentences: what just happened in flavor terms, showing narrative impact on player, NPCs, scene, and location. Ground this in the roll outcome (if any) and the player's intent. For failures: describe what went wrong narratively. Examples: `"You successfully picklock the padlock and enter the vault."`, `"The guard spots you and raises the alarm."`

## PacingContext guidance

The `pacing_context` section tells you how Python shaped tone for this turn. Use it to inform `gm_beat` and thread decisions:

- **Breathe** → prefer `breathing_room` beat, do NOT add threads even if gate allows, resolve tensions where possible
- **Overwhelm** → emit `gm_beat` of type `pressure`/`escalation`, may add scene-scoped threads if gate == "allow" 
- **Pressure** → emit `gm_beat` of type `complication`/`pressure`, advance existing threads rather than adding new ones
- **Tension** → do NOT add pressures unless concrete threat emerges; prefer advancing existing threads
- **Resolve a Threat** → resolve resolved threads via thread_resolve with resolution_state="resolved"; do NOT add new threads
- **Combat Fatigue** (secondary) → layer as thematic modifier on beat type, not a separate operation

When multiple directives are joined (e.g. "Pressure; Combat Fatigue"), prioritize the primary directive and layer the secondary as a thematic modifier on the beat type.

## GM Beat guidance

`gm_beat`: a single GM beat to shape the next turn, or `null` if none is needed.
- Recent `twist` or `callback` beats should not repeat within 2 turns, **but callbacks SHOULD fire during narrative peaks** — a callback referencing an earlier event is most effective at major pivot moments (near-death stabilization, unexpected revelation). Do not suppress callbacks just because one fired recently.

**Beat type diversity:** During extended sequences (3+ consecutive pressure-type beats), at least every third beat must use a non-pressure type. Pressure and escalation are appropriate during active crises, but callbacks, complications, and revelations break monotony even in tense moments. A callback beat references an earlier narrative development: "The merchant you spared last week returns with reinforcements — he remembers your mercy."

**Crisis-aware beat selection:** During extended sequences (3+ turns with active scene pressures), vary beat types — do not repeat pressure/escalation every turn.
- **Turns 1–2 of a crisis sequence:** Pressure and escalation beats are appropriate. The situation is new; escalate to communicate stakes.
- **Turn 3+:** At least one in three beats must use callback, complication, revelation, twist, or opportunity type. This breaks monotony and creates narrative resonance.

**At major pivot moments** (a character nearly dies and recovers, a failed plan succeeds unexpectedly, an NPC makes a decisive choice), you MUST consider:
  - `revelation` — new information changes understanding: "You learn Campos filed the audit with the port authority three days ago. This was planned."
  - `twist` — narrative direction shifts unexpectedly: "The miner's seizures stop as suddenly as they began. His eyes open and he whispers your name in a language you don't know."
  - `callback` — references an earlier beat or event with new resonance: "The ventilation fan you repaired last week seizes with a grinding shriek — the metal fatigue you warned about has caught up to it."
  - `opportunity` — a path forward opens in unexpected way: "Through the chaos, you notice Aaron watching your repairs. He's been trained in this work and makes eye contact with clear intent to help."

**Guidance per non-pressure type:**
- `complication` — an existing pressure creates cascading effects: "The guard captain's delay means reinforcements arrive armed — not just with batons, but with tear gas canisters you didn't expect."
- `revelation` — new information changes how earlier events should be understood. Use sparingly (1–2 per arc). Most effective when it reframes an established fact.
- `twist` — narrative direction shifts in an unexpected way. Most appropriate at major pivot moments, not during steady-state pressure cascades.
- `callback` — references a beat, NPC action, or environmental detail from 3+ turns ago with new resonance. Most effective when the earlier instance was subtle.
- `opportunity` — path forward opens unexpectedly. Best used after failure/setback to maintain player agency.

**Band-aligned beat selection:** The roll band determines what kind of beat is narratively appropriate — do not ignore this signal even when scene pressures are active:

- **crit_success / success**: `opportunity`, `escalation` (the world reacts to PC momentum), or `breathing_room` if deescalating
- **partial**: `complication`, `pressure` — the player succeeded but at a cost; the beat should reflect that cost
- **setback / fail**: `breathing_room`, `null`, or rarely `complication`. Do NOT emit escalation or pressure beats on failed checks — the failure itself is the consequence. Escalation compounds punishment and breaks pacing.
- **No roll (pure approach/sit)**: `null` unless there's an independent narrative reason for a beat

When deescalating, always prefer `breathing_room` or `null` regardless of band.
- `type` values: `complication`, `revelation`, `opportunity`, `breathing_room`, `pressure`, `twist`, `setback`, `escalation`, `callback`
- `surface_as` values: `ambient`, `event`, `npc_behavior`, `environmental`, `player_discovery`, `item`

**Surface distribution rule:** Across a 3+ turn sequence, you MUST vary `surface_as` — do not repeat the same type in consecutive turns. Rotate through T1→T2→T3 using different types each time; cycle back to an unused type before repeating any type.

**Guidance per surface type with examples:**
- `ambient` — atmosphere/mood shift: "A heavy silence falls over the crew as they realize what you've discovered."
- `event` — a concrete happening in-scene: "The door bursts open and Captain Reyes strides in, wet from the storm."
- `npc_behavior` — named NPC changes demeanor or makes a move: "Vargas steps aside with barely concealed bitterness. You notice he's no longer watching you with deference."
- `environmental` — scene setting shifts: "The lantern gutters and dies, leaving only moonlight through the shattered window."
- `player_discovery` — player finds something new: "You pry loose a floorboard and find a folded letter sealed with black wax."
- `item` — inventory/tool relevance: "Your old sea-knife catches on your coat as you move — you hadn't thought of it in years, but its edge is still true."

- Each beat must be narratively specific: name NPCs, reference locations, tie to active threads
- Emit as: `{"type": "pressure", "surface_as": "npc_behavior"}`
- If no beat is warranted, emit `null` (not an empty object)

## Rules-outcome guidance
- crit_fail / fail / setback / partial: do NOT mark thread signals as "advanced" for the attempted action.
- success / crit_success: apply thread advancement freely.
- No dice roll: do NOT signal "advanced" unless the narration explicitly and unambiguously states the thread was moved forward. Ambiguous, partial, or conversational narration means the thread was NOT advanced.

## State-presence rule
Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only emit removals you can justify from the narration.

## Output discipline

When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out.

```


---

# TURN 1

**Input:** `Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

## scene
Location: Marrow's Crossing
## Present NPCs (in scene right now)
- Caron (Old creditor) — Sits at a corner table in the tavern, nursing a drink and watching the door.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)


## Current Turn: 1
=== PLAYER INPUT ===
Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

## Location
Marrow's Crossing (marrows_crossing)
A market town built around the confluence of two rivers. Cobblestone streets,
timber-framed buildings, and the constant sound of water from the mills. The
town square has a stone well and a statue of the founder. Most shops are closing
for the evening.


## inventory (cross-reference before describing item use)
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.




## Characters
Before introducing a new named NPC, check this list first.

- **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago. | Sits at a corner table in the tavern, nursing a drink and watching the door.

- **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. | Wiping down the bar at the Crossed Keys, which is two streets over.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Stands near the town well, examining a map and a pressed wax seal.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
## Recent Turns
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 1) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
=== END PLAYER INPUT ===


```

### Extract Scene User Prompt
```
## location
`marrows_crossing` | Marrow's Crossing
A market town built around the confluence of two rivers. Cobblestone streets,
timber-framed buildings, and the constant sound of water from the mills. The
town square has a stone well and a statue of the founder. Most shops are closing
for the evening.


## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | **Caron** (Old creditor) — Sits at a corner table in the tavern, nursing a drink and watching the door.
- `halden` | **Halden** (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_
## CURRENT TURN 1 NARRATION
You pull a stool out from the corner table, the wooden legs scraping harshly against the tavern's uneven floorboards. As you settle into the seat, your bruised ribs protest with a sharp, stinging reminder of your recent troubles, forcing a shallow breath. Across the table, **Caron** doesn't look up immediately; he continues to trace a line of ink in his ledger with a methodical, rhythmic precision.

The portly man finally closes the book with a soft thud, the sound swallowed by the low murmur of the closing tavern. He leans back, his belly pressing against the edge of the table, and fixes you with a gaze that is neither angry nor sympathetic—only deeply, wearyingly observant. He licks a thumb, prepping to turn a page, though he keeps his eyes pinned on your face.

"You look like you've walked through a bramble patch and come out the other side bleeding, Aren," **Caron** says, his voice a gravelly rumble. He gestures vaguely toward your disheveled appearance with a hand that bears a heavy gold ring. "I'm not a man of sudden whims or miracles. I've sat in this very chair waiting for three years of interest to accumulate, and I have no intention of letting a bit of road-wear stop me from collecting what is mine."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- low_morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
negotiate: The player approaches Caron to discuss the repayment of their debt.
## CURRENT TURN 1 NARRATION
You pull a stool out from the corner table, the wooden legs scraping harshly against the tavern's uneven floorboards. As you settle into the seat, your bruised ribs protest with a sharp, stinging reminder of your recent troubles, forcing a shallow breath. Across the table, **Caron** doesn't look up immediately; he continues to trace a line of ink in his ledger with a methodical, rhythmic precision.

The portly man finally closes the book with a soft thud, the sound swallowed by the low murmur of the closing tavern. He leans back, his belly pressing against the edge of the table, and fixes you with a gaze that is neither angry nor sympathetic—only deeply, wearyingly observant. He licks a thumb, prepping to turn a page, though he keeps his eyes pinned on your face.

"You look like you've walked through a bramble patch and come out the other side bleeding, Aren," **Caron** says, his voice a gravelly rumble. He gestures vaguely toward your disheveled appearance with a hand that bears a heavy gold ring. "I'm not a man of sudden whims or miracles. I've sat in this very chair waiting for three years of interest to accumulate, and I have no intention of letting a bit of road-wear stop me from collecting what is mine."
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `caron` | **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.
- `halden` | **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Marrow's Crossing** — The tavern is nearing its closing hour, filled with a low murmur and the uneven, scraping sound of wooden furniture against floorboards.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- low_morale: low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## Current inventory (this turn)
- `credits`: Credits x500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads (all — unified list, scope handled by Python)
- `settle_the_debt` [ARC] (dormant) [NORMAL] Settle the 500-credit debt with Caron. tags: debt, caron, obligation
- `deliver_the_ledger` [ARC] (dormant) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. tags: courier, halden, contract
- `clear_the_road_toughs` [ARC] (dormant) [BACKGROUND] Deal with the toughs blocking the inn entrance. tags: toughs, road, confrontation

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## pacing_context
Directive: none
Gate: allow

## player_intent
**negotiate**: The player approaches Caron to discuss the repayment of their debt.

## CURRENT TURN 1 NARRATION
You pull a stool out from the corner table, the wooden legs scraping harshly against the tavern's uneven floorboards. As you settle into the seat, your bruised ribs protest with a sharp, stinging reminder of your recent troubles, forcing a shallow breath. Across the table, **Caron** doesn't look up immediately; he continues to trace a line of ink in his ledger with a methodical, rhythmic precision.

The portly man finally closes the book with a soft thud, the sound swallowed by the low murmur of the closing tavern. He leans back, his belly pressing against the edge of the table, and fixes you with a gaze that is neither angry nor sympathetic—only deeply, wearyingly observant. He licks a thumb, prepping to turn a page, though he keeps his eyes pinned on your face.

"You look like you've walked through a bramble patch and come out the other side bleeding, Aren," **Caron** says, his voice a gravelly rumble. He gestures vaguely toward your disheveled appearance with a hand that bears a heavy gold ring. "I'm not a man of sudden whims or miracles. I've sat in this very chair waiting for three years of interest to accumulate, and I have no intention of letting a bit of road-wear stop me from collecting what is mine."
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player approaches Caron to discuss the repayment of their debt.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "check": {
    "required": false
  }
}
```

### Narration

You pull a stool out from the corner table, the wooden legs scraping harshly against the tavern's uneven floorboards. As you settle into the seat, your bruised ribs protest with a sharp, stinging reminder of your recent troubles, forcing a shallow breath. Across the table, **Caron** doesn't look up immediately; he continues to trace a line of ink in his ledger with a methodical, rhythmic precision.

The portly man finally closes the book with a soft thud, the sound swallowed by the low murmur of the closing tavern. He leans back, his belly pressing against the edge of the table, and fixes you with a gaze that is neither angry nor sympathetic—only deeply, wearyingly observant. He licks a thumb, prepping to turn a page, though he keeps his eyes pinned on your face.

"You look like you've walked through a bramble patch and come out the other side bleeding, Aren," **Caron** says, his voice a gravelly rumble. He gestures vaguely toward your disheveled appearance with a hand that bears a heavy gold ring. "I'm not a man of sudden whims or miracles. I've sat in this very chair waiting for three years of interest to accumulate, and I have no intention of letting a bit of road-wear stop me from collecting what is mine."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "debt_collection"
  ],
  "scene_tagline": "A Debt Long Overdue",
  "location_description": "The tavern is nearing its closing hour, filled with a low murmur and the uneven, scraping sound of wooden furniture against floorboards.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Methodical and observant; he is pressuring the player about their long-standing debt with a weary, relentless attitude."
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "confrontation_with_caron",
      "text": "You have sat down to face Caron and discuss your three-year-old debt.",
      "turn": 1
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Offer a partial payment of your remaining credits.",
    "Propose a new work contract to settle the interest.",
    "Try to charm Caron into granting a payment extension.",
    "Deflect the conversation toward the road-toughs outside."
  ],
  "outcome_summary": "You have sat down with Caron, who has made it clear he expects full repayment of the debt and accumulated interest.",
  "thread_advance": [
    "settle_the_debt"
  ],
  "thread_resolve": []
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1739t trimmed=False
- narrate: est=4796t trimmed=False
- extract.scene: est=3681t trimmed=False attempts=1
- extract.state: est=4344t trimmed=False attempts=1
- extract.storytell: est=4792t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 2

**Input:** `I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

## scene
Location: Marrow's Crossing
## Present NPCs (in scene right now)
- Caron (Old creditor) — Methodical and observant; he is pressuring the player about their long-standing debt with a weary, relentless attitude.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)

## Last Turn Outcome
You have sat down with Caron, who has made it clear he expects full repayment of the debt and accumulated interest.

## Current Turn: 2
=== PLAYER INPUT ===
I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

## Location
Marrow's Crossing (marrows_crossing)
The tavern is nearing its closing hour, filled with a low murmur and the uneven, scraping sound of wooden furniture against floorboards.

## inventory (cross-reference before describing item use)
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.




## Characters
Before introducing a new named NPC, check this list first.

- **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago. | Methodical and observant; he is pressuring the player about their long-standing debt with a weary, relentless attitude.

- **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. | Wiping down the bar at the Crossed Keys, which is two streets over.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Stands near the town well, examining a map and a pressed wax seal.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
## Recent Turns

**T1:** You pull a stool out from the corner table, the wooden legs scraping harshly against the tavern's uneven floorboards. As you settle into the seat, your bruised ribs protest with a sharp, stinging reminder of your recent troubles, forcing a shallow breath. Across the table, **Caron** doesn't look up immediately; he continues to trace a line of ink in his ledger with a methodical, rhythmic precision.

The portly man finally closes the book with a soft thud, the sound swallowed by the low murmur of the closing tavern. He leans back, his belly pressing against the edge of the table, and fixes you with a gaze that is neither angry nor sympathetic—only deeply, wearyingly observant. He licks a thumb, prepping to turn a page, though he keeps his eyes pinned on your face.

"You look like you've walked through a bramble patch and come out the other side bleeding, Aren," **Caron** says, his voice a gravelly rumble. He gestures vaguely toward your disheveled appearance with a hand that bears a heavy gold ring. "I'm not a man of sudden whims or miracles. I've sat in this very chair waiting for three years of interest to accumulate, and I have no intention of letting a bit of road-wear stop me from collecting what is mine."

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 2) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
=== END PLAYER INPUT ===


```

### Extract Scene User Prompt
```
## location
`marrows_crossing` | Marrow's Crossing
The tavern is nearing its closing hour, filled with a low murmur and the uneven, scraping sound of wooden furniture against floorboards.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | **Caron** (Old creditor) — Methodical and observant; he is pressuring the player about their long-standing debt with a weary, relentless attitude.
- `halden` | **Halden** (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T1 context)
You pull a stool out from the corner table, the wooden legs scraping harshly against the tavern's uneven floorboards. As you settle into the seat, your bruised ribs protest with a sharp, stinging reminder of your recent troubles, forcing a shallow breath. Across the table, **Caron** doesn't look up immediately; he continues to trace a line of ink in his ledger with a methodical, rhythmic precision.

The portly man finally closes the book with a soft thud, the sound swallowed by the low murmur of the closing tavern. He leans back, his belly pressing against the edge of the table, and fixes you with a gaze that is neither angry nor sympathetic—only deeply, wearyingly observant. He licks a thumb, prepping to turn a page, though he keeps his eyes pinned on your face.

"You look like you've walked through a bramble patch and come out the other side bleeding, Aren," **Caron** says, his voice a gravelly rumble. He gestures vaguely toward your disheveled appearance with a hand that bears a heavy gold ring. "I'm not a man of sudden whims or miracles. I've sat in this very chair waiting for three years of interest to accumulate, and I have no intention of letting a bit of road-wear stop me from collecting what is mine."

## CURRENT TURN 2 NARRATION
You reach for your belt pouch, fingers trembling slightly from the ache in your side, and pull out your **Credits**. The small, heavy coins clatter onto the scarred wood of the table, a sharp, metallic sound that seems to cut through the tavern's low hum. You slide the pile of 500 **Credits** across the table, pushing them toward the portly man until they bump against the edge of his ledger.

"Mark it cleared," you say, your voice thinner than you intended.

**Caron** stares down at the coins, his eyes narrowing as he calculates the total without moving a muscle. He doesn't reach for the money immediately; instead, he picks up a quill, tapping the nib against his chin while he studies your face, searching for a sign of a bluff or a desperate lie. The silence stretches, heavy and suffocating, as the weight of three years of mounting interest hangs between you.

Finally, he exhales a long, weary sigh that rattles in his chest. He reaches out, his ringed fingers sweeping the coins into a neat, disciplined stack. He opens the ledger to the page where your name is etched in ink, finds the mounting total, and strikes a single, decisive line through the figures with a flourish of black ink. He closes the book once more, the sound final and heavy, and looks up at you with an expression of profound boredom.

"The principal is settled, Aren," **Caron** says, tapping the cover of the book. "But don't think for a second that being debt-free makes you a man of consequence on this road. You're just another runner with an empty purse and a long walk ahead of you."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- low_morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
negotiate: The player attempts to settle their debt with Caron using their current credits.
## CURRENT TURN 2 NARRATION
You reach for your belt pouch, fingers trembling slightly from the ache in your side, and pull out your **Credits**. The small, heavy coins clatter onto the scarred wood of the table, a sharp, metallic sound that seems to cut through the tavern's low hum. You slide the pile of 500 **Credits** across the table, pushing them toward the portly man until they bump against the edge of his ledger.

"Mark it cleared," you say, your voice thinner than you intended.

**Caron** stares down at the coins, his eyes narrowing as he calculates the total without moving a muscle. He doesn't reach for the money immediately; instead, he picks up a quill, tapping the nib against his chin while he studies your face, searching for a sign of a bluff or a desperate lie. The silence stretches, heavy and suffocating, as the weight of three years of mounting interest hangs between you.

Finally, he exhales a long, weary sigh that rattles in his chest. He reaches out, his ringed fingers sweeping the coins into a neat, disciplined stack. He opens the ledger to the page where your name is etched in ink, finds the mounting total, and strikes a single, decisive line through the figures with a flourish of black ink. He closes the book once more, the sound final and heavy, and looks up at you with an expression of profound boredom.

"The principal is settled, Aren," **Caron** says, tapping the cover of the book. "But don't think for a second that being debt-free makes you a man of consequence on this road. You're just another runner with an empty purse and a long walk ahead of you."
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `caron` | **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.
- `halden` | **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Marrow's Crossing** — The tavern is nearing its closing hour, filled with a low murmur and the uneven, scraping sound of wooden furniture against floorboards.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- low_morale: low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads
None currently. Generate actions that could introduce new story directions or explore the environment.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- You have sat down to face Caron and discuss your three-year-old debt.

_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## last turn's context (T1)
You pull a stool out from the corner table, the wooden legs scraping harshly against the tavern's uneven floorboards. As you settle into the seat, your bruised ribs protest with a sharp, stinging reminder of your recent troubles, forcing a shallow breath. Across the table, **Caron** doesn't look up immediately; he continues to trace a line of ink in his ledger with a methodical, rhythmic precision.

The portly man finally closes the book with a soft thud, the sound swallowed by the low murmur of the closing tavern. He leans back, his belly pressing against the edge of the table, and fixes you with a gaze that is neither angry nor sympathetic—only deeply, wearyingly observant. He licks a thumb, prepping to turn a page, though he keeps his eyes pinned on your face.

"You look like you've walked through a bramble patch and come out the other side bleeding, Aren," **Caron** says, his voice a gravelly rumble. He gestures vaguely toward your disheveled appearance with a hand that bears a heavy gold ring. "I'm not a man of sudden whims or miracles. I've sat in this very chair waiting for three years of interest to accumulate, and I have no intention of letting a bit of road-wear stop me from collecting what is mine."

## player_intent
**negotiate**: The player attempts to settle their debt with Caron using their current credits.

## CURRENT TURN 2 NARRATION
You reach for your belt pouch, fingers trembling slightly from the ache in your side, and pull out your **Credits**. The small, heavy coins clatter onto the scarred wood of the table, a sharp, metallic sound that seems to cut through the tavern's low hum. You slide the pile of 500 **Credits** across the table, pushing them toward the portly man until they bump against the edge of his ledger.

"Mark it cleared," you say, your voice thinner than you intended.

**Caron** stares down at the coins, his eyes narrowing as he calculates the total without moving a muscle. He doesn't reach for the money immediately; instead, he picks up a quill, tapping the nib against his chin while he studies your face, searching for a sign of a bluff or a desperate lie. The silence stretches, heavy and suffocating, as the weight of three years of mounting interest hangs between you.

Finally, he exhales a long, weary sigh that rattles in his chest. He reaches out, his ringed fingers sweeping the coins into a neat, disciplined stack. He opens the ledger to the page where your name is etched in ink, finds the mounting total, and strikes a single, decisive line through the figures with a flourish of black ink. He closes the book once more, the sound final and heavy, and looks up at you with an expression of profound boredom.

"The principal is settled, Aren," **Caron** says, tapping the cover of the book. "But don't think for a second that being debt-free makes you a man of consequence on this road. You're just another runner with an empty purse and a long walk ahead of you."
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to settle their debt with Caron using their current credits.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "check": {
    "required": false
  }
}
```

### Narration

You reach for your belt pouch, fingers trembling slightly from the ache in your side, and pull out your **Credits**. The small, heavy coins clatter onto the scarred wood of the table, a sharp, metallic sound that seems to cut through the tavern's low hum. You slide the pile of 500 **Credits** across the table, pushing them toward the portly man until they bump against the edge of his ledger.

"Mark it cleared," you say, your voice thinner than you intended.

**Caron** stares down at the coins, his eyes narrowing as he calculates the total without moving a muscle. He doesn't reach for the money immediately; instead, he picks up a quill, tapping the nib against his chin while he studies your face, searching for a sign of a bluff or a desperate lie. The silence stretches, heavy and suffocating, as the weight of three years of mounting interest hangs between you.

Finally, he exhales a long, weary sigh that rattles in his chest. He reaches out, his ringed fingers sweeping the coins into a neat, disciplined stack. He opens the ledger to the page where your name is etched in ink, finds the mounting total, and strikes a single, decisive line through the figures with a flourish of black ink. He closes the book once more, the sound final and heavy, and looks up at you with an expression of profound boredom.

"The principal is settled, Aren," **Caron** says, tapping the cover of the book. "But don't think for a second that being debt-free makes you a man of consequence on this road. You're just another runner with an empty purse and a long walk ahead of you."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "resolution"
  ],
  "scene_tagline": "A Debt Finally Settled",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Accepts the payment of 500 credits, strikes the debt from his ledger, and treats the player with profound boredom."
    }
  ],
  "compendium_npc_update": [
    {
      "id": "caron",
      "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit debt, he views the player as just another insignificant runner.",
      "aliases": []
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 500
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "debt_settled_caron",
      "text": "You successfully paid Caron the 500 credits to settle your three-year-old debt.",
      "turn": 2
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Ask Caron if he knows of any immediate work.",
    "Leave the tavern quietly to find a place to rest.",
    "Inquire about the rumors of road-toughs near the inn.",
    "Try to strike up a conversation with Edda the innkeeper."
  ],
  "outcome_summary": "You successfully settle your debt with Caron, clearing your name but leaving your purse empty.",
  "thread_advance": [
    "clearing_old_debts"
  ],
  "thread_resolve": [
    {
      "id": "clearing_old_debts",
      "resolution_state": "resolved"
    }
  ]
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1792t trimmed=False
- narrate: est=5130t trimmed=False
- extract.scene: est=4123t trimmed=False attempts=1
- extract.state: est=4446t trimmed=False attempts=1
- extract.storytell: est=5274t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 3

**Input:** `I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

## scene
Location: Marrow's Crossing
## Present NPCs (in scene right now)
- Caron (Old creditor) — Accepts the payment of 500 credits, strikes the debt from his ledger, and treats the player with profound boredom.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

## Inventory
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)

## Last Turn Outcome
You successfully settle your debt with Caron, clearing your name but leaving your purse empty.

## Current Turn: 3
=== PLAYER INPUT ===
I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

## Location
Marrow's Crossing (marrows_crossing)
The tavern is nearing its closing hour, filled with a low murmur and the uneven, scraping sound of wooden furniture against floorboards.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.




## Characters
Before introducing a new named NPC, check this list first.

- **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago. | Accepts the payment of 500 credits, strikes the debt from his ledger, and treats the player with profound boredom.

- **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. | Wiping down the bar at the Crossed Keys, which is two streets over.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Stands near the town well, examining a map and a pressed wax seal.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
## Recent Turns

**T1:** You pull a stool out from the corner table, the wooden legs scraping harshly against the tavern's uneven floorboards. As you settle into the seat, your bruised ribs protest with a sharp, stinging reminder of your recent troubles, forcing a shallow breath. Across the table, **Caron** doesn't look up immediately; he continues to trace a line of ink in his ledger with a methodical, rhythmic precision.

The portly man finally closes the book with a soft thud, the sound swallowed by the low murmur of the closing tavern. He leans back, his belly pressing against the edge of the table, and fixes you with a gaze that is neither angry nor sympathetic—only deeply, wearyingly observant. He licks a thumb, prepping to turn a page, though he keeps his eyes pinned on your face.

"You look like you've walked through a bramble patch and come out the other side bleeding, Aren," **Caron** says, his voice a gravelly rumble. He gestures vaguely toward your disheveled appearance with a hand that bears a heavy gold ring. "I'm not a man of sudden whims or miracles. I've sat in this very chair waiting for three years of interest to accumulate, and I have no intention of letting a bit of road-wear stop me from collecting what is mine."


**T2:** You reach for your belt pouch, fingers trembling slightly from the ache in your side, and pull out your **Credits**. The small, heavy coins clatter onto the scarred wood of the table, a sharp, metallic sound that seems to cut through the tavern's low hum. You slide the pile of 500 **Credits** across the table, pushing them toward the portly man until they bump against the edge of his ledger.

"Mark it cleared," you say, your voice thinner than you intended.

**Caron** stares down at the coins, his eyes narrowing as he calculates the total without moving a muscle. He doesn't reach for the money immediately; instead, he picks up a quill, tapping the nib against his chin while he studies your face, searching for a sign of a bluff or a desperate lie. The silence stretches, heavy and suffocating, as the weight of three years of mounting interest hangs between you.

Finally, he exhales a long, weary sigh that rattles in his chest. He reaches out, his ringed fingers sweeping the coins into a neat, disciplined stack. He opens the ledger to the page where your name is etched in ink, finds the mounting total, and strikes a single, decisive line through the figures with a flourish of black ink. He closes the book once more, the sound final and heavy, and looks up at you with an expression of profound boredom.

"The principal is settled, Aren," **Caron** says, tapping the cover of the book. "But don't think for a second that being debt-free makes you a man of consequence on this road. You're just another runner with an empty purse and a long walk ahead of you."

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 3) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
=== END PLAYER INPUT ===


```

### Extract Scene User Prompt
```
## location
`marrows_crossing` | Marrow's Crossing
The tavern is nearing its closing hour, filled with a low murmur and the uneven, scraping sound of wooden furniture against floorboards.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | **Caron** (Old creditor) — Accepts the payment of 500 credits, strikes the debt from his ledger, and treats the player with profound boredom.
- `halden` | **Halden** (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T2 context)
You reach for your belt pouch, fingers trembling slightly from the ache in your side, and pull out your **Credits**. The small, heavy coins clatter onto the scarred wood of the table, a sharp, metallic sound that seems to cut through the tavern's low hum. You slide the pile of 500 **Credits** across the table, pushing them toward the portly man until they bump against the edge of his ledger.

"Mark it cleared," you say, your voice thinner than you intended.

**Caron** stares down at the coins, his eyes narrowing as he calculates the total without moving a muscle. He doesn't reach for the money immediately; instead, he picks up a quill, tapping the nib against his chin while he studies your face, searching for a sign of a bluff or a desperate lie. The silence stretches, heavy and suffocating, as the weight of three years of mounting interest hangs between you.

Finally, he exhales a long, weary sigh that rattles in his chest. He reaches out, his ringed fingers sweeping the coins into a neat, disciplined stack. He opens the ledger to the page where your name is etched in ink, finds the mounting total, and strikes a single, decisive line through the figures with a flourish of black ink. He closes the book once more, the sound final and heavy, and looks up at you with an expression of profound boredom.

"The principal is settled, Aren," **Caron** says, tapping the cover of the book. "But don't think for a second that being debt-free makes you a man of consequence on this road. You're just another runner with an empty purse and a long walk ahead of you."

## CURRENT TURN 3 NARRATION
You push away from the table, your ribs screaming in protest as you lurch to your feet. Leaving the heavy, settled silence of the tavern behind, you step out into the cooling night air of Marrow's Crossing. The streetlamps flicker low, casting long, dancing shadows across the cobblestones, and the scent of river silt and woodsmoke hangs thick in the air.

You find **Halden** near the central well, the stone structure glowing pale under the moonlight. He is hunched over a map, the light from a small hand-lantern casting a sickly amber hue over the parchment. When you approach, he looks up, squinting through the dimness. He looks tired, the lines around his eyes deeply etched by a day of difficult trades.

"Two hundred credits to move a single book?" **Halden** asks, a skeptical brow arching as he looks from your battered face to the heavy, wax-sealed ledger tucked under his arm. He doesn't look impressed by your disheveled state or your sudden suddenness; he simply looks like a man calculating the risk of trusting a runner who looks like he's one stumble away from a collapse.

He sighs, tapping the wax seal of the ledger with a calloused finger. "You look like you've had a rough go of it, Aren. I need that book at the *Crossed Keys* settled before the morning bells, and I'd rather not hand it to someone who might drop it in a ditch because their side is broken." He pauses, weighing your worth against the cost. "Fine. Two hundred. But if a single page is torn or that seal is cracked when you reach **Edda**, you'll find I'm much less patient than **Caron**."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- low_morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
negotiate: Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.
## CURRENT TURN 3 NARRATION
You push away from the table, your ribs screaming in protest as you lurch to your feet. Leaving the heavy, settled silence of the tavern behind, you step out into the cooling night air of Marrow's Crossing. The streetlamps flicker low, casting long, dancing shadows across the cobblestones, and the scent of river silt and woodsmoke hangs thick in the air.

You find **Halden** near the central well, the stone structure glowing pale under the moonlight. He is hunched over a map, the light from a small hand-lantern casting a sickly amber hue over the parchment. When you approach, he looks up, squinting through the dimness. He looks tired, the lines around his eyes deeply etched by a day of difficult trades.

"Two hundred credits to move a single book?" **Halden** asks, a skeptical brow arching as he looks from your battered face to the heavy, wax-sealed ledger tucked under his arm. He doesn't look impressed by your disheveled state or your sudden suddenness; he simply looks like a man calculating the risk of trusting a runner who looks like he's one stumble away from a collapse.

He sighs, tapping the wax seal of the ledger with a calloused finger. "You look like you've had a rough go of it, Aren. I need that book at the *Crossed Keys* settled before the morning bells, and I'd rather not hand it to someone who might drop it in a ditch because their side is broken." He pauses, weighing your worth against the cost. "Fine. Two hundred. But if a single page is torn or that seal is cracked when you reach **Edda**, you'll find I'm much less patient than **Caron**."
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `halden` | **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Marrow's Crossing** — The cobblestone streets of Marrow's Crossing are bathed in moonlight, smelling of river silt and woodsmoke under flickering streetlamps.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- low_morale: low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads
None currently. Generate actions that could introduce new story directions or explore the environment.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- You have sat down to face Caron and discuss your three-year-old debt.
- You successfully paid Caron the 500 credits to settle your three-year-old debt.

_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## last turn's context (T2)
You reach for your belt pouch, fingers trembling slightly from the ache in your side, and pull out your **Credits**. The small, heavy coins clatter onto the scarred wood of the table, a sharp, metallic sound that seems to cut through the tavern's low hum. You slide the pile of 500 **Credits** across the table, pushing them toward the portly man until they bump against the edge of his ledger.

"Mark it cleared," you say, your voice thinner than you intended.

**Caron** stares down at the coins, his eyes narrowing as he calculates the total without moving a muscle. He doesn't reach for the money immediately; instead, he picks up a quill, tapping the nib against his chin while he studies your face, searching for a sign of a bluff or a desperate lie. The silence stretches, heavy and suffocating, as the weight of three years of mounting interest hangs between you.

Finally, he exhales a long, weary sigh that rattles in his chest. He reaches out, his ringed fingers sweeping the coins into a neat, disciplined stack. He opens the ledger to the page where your name is etched in ink, finds the mounting total, and strikes a single, decisive line through the figures with a flourish of black ink. He closes the book once more, the sound final and heavy, and looks up at you with an expression of profound boredom.

"The principal is settled, Aren," **Caron** says, tapping the cover of the book. "But don't think for a second that being debt-free makes you a man of consequence on this road. You're just another runner with an empty purse and a long walk ahead of you."

## player_intent
**negotiate**: Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.

## CURRENT TURN 3 NARRATION
You push away from the table, your ribs screaming in protest as you lurch to your feet. Leaving the heavy, settled silence of the tavern behind, you step out into the cooling night air of Marrow's Crossing. The streetlamps flicker low, casting long, dancing shadows across the cobblestones, and the scent of river silt and woodsmoke hangs thick in the air.

You find **Halden** near the central well, the stone structure glowing pale under the moonlight. He is hunched over a map, the light from a small hand-lantern casting a sickly amber hue over the parchment. When you approach, he looks up, squinting through the dimness. He looks tired, the lines around his eyes deeply etched by a day of difficult trades.

"Two hundred credits to move a single book?" **Halden** asks, a skeptical brow arching as he looks from your battered face to the heavy, wax-sealed ledger tucked under his arm. He doesn't look impressed by your disheveled state or your sudden suddenness; he simply looks like a man calculating the risk of trusting a runner who looks like he's one stumble away from a collapse.

He sighs, tapping the wax seal of the ledger with a calloused finger. "You look like you've had a rough go of it, Aren. I need that book at the *Crossed Keys* settled before the morning bells, and I'd rather not hand it to someone who might drop it in a ditch because their side is broken." He pauses, weighing your worth against the cost. "Fine. Two hundred. But if a single page is torn or that seal is cracked when you reach **Edda**, you'll find I'm much less patient than **Caron**."
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "check": {
    "required": false
  }
}
```

### Narration

You push away from the table, your ribs screaming in protest as you lurch to your feet. Leaving the heavy, settled silence of the tavern behind, you step out into the cooling night air of Marrow's Crossing. The streetlamps flicker low, casting long, dancing shadows across the cobblestones, and the scent of river silt and woodsmoke hangs thick in the air.

You find **Halden** near the central well, the stone structure glowing pale under the moonlight. He is hunched over a map, the light from a small hand-lantern casting a sickly amber hue over the parchment. When you approach, he looks up, squinting through the dimness. He looks tired, the lines around his eyes deeply etched by a day of difficult trades.

"Two hundred credits to move a single book?" **Halden** asks, a skeptical brow arching as he looks from your battered face to the heavy, wax-sealed ledger tucked under his arm. He doesn't look impressed by your disheveled state or your sudden suddenness; he simply looks like a man calculating the risk of trusting a runner who looks like he's one stumble away from a collapse.

He sighs, tapping the wax seal of the ledger with a calloused finger. "You look like you've had a rough go of it, Aren. I need that book at the *Crossed Keys* settled before the morning bells, and I'd rather not hand it to someone who might drop it in a ditch because their side is broken." He pauses, weighing your worth against the cost. "Fine. Two hundred. But if a single page is torn or that seal is cracked when you reach **Edda**, you'll find I'm much less patient than **Caron**."


### Extract Scene

```json
{
  "scene_tags": [
    "negotiation",
    "tense_conversation"
  ],
  "scene_tagline": "A Risky Contract",
  "location_description": "The cobblestone streets of Marrow's Crossing are bathed in moonlight, smelling of river silt and woodsmoke under flickering streetlamps.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "caron"
    },
    {
      "id": "innkeeper"
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Skeptical and calculating; weighing the risk of hiring the player due to their visible injuries."
    }
  ],
  "compendium_npc_update": [
    {
      "id": "halden",
      "aliases": [],
      "motivation": "Needs a reliable courier to deliver a wax-sealed ledger to the Crossed Keys before morning."
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "halden_ledger",
      "name": "Halden's Ledger",
      "notes": "A heavy, wax-sealed ledger.",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "credits",
      "name": "Credits",
      "notes": "",
      "amount": 200,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "halden_contract_accepted",
      "text": "Halden has hired you to deliver his ledger to the Crossed Keys Inn for 200 credits.",
      "turn": 3
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Accept the contract and head straight for the Crossed Keys.",
    "Ask Halden if there are any specific dangers on the route.",
    "Try to negotiate for a higher fee due to your injuries.",
    "Look for a place to rest and tend your ribs first."
  ],
  "outcome_summary": "You successfully negotiated a 200 credit contract with Halden to deliver his ledger to the Crossed Keys Inn, though he remains skeptical of your physical condition.",
  "thread_advance": [
    "halden_ledger_delivery"
  ],
  "thread_resolve": [],
  "thread_add": {
    "id": "halden_ledger_delivery",
    "summary": "Deliver Halden's wax-sealed ledger to Edda at the Crossed Keys Inn without damage.",
    "scope": "scene",
    "active": true,
    "urgency": "normal",
    "tags": [
      "delivery",
      "halden",
      "crossed_keys"
    ],
    "progress": 0,
    "promotes": []
  }
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

```json
[
  {
    "field": "inventory_add",
    "kind": "durability_gate",
    "value": "halden_ledger",
    "reason": "New item 'Halden's Ledger' \u2014 no loot gain context detected in recent_events or actions; rejected by durability gate"
  }
]
```

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1785t trimmed=False
- narrate: est=5565t trimmed=False
- extract.scene: est=4222t trimmed=False attempts=1
- extract.state: est=4419t trimmed=False attempts=1
- extract.storytell: est=5369t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 4

**Input:** `I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

## scene
Location: Marrow's Crossing
## Present NPCs (in scene right now)
- Halden (Merchant) — Skeptical and calculating; weighing the risk of hiring the player due to their visible injuries.

## Inventory
- Credits (200)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)

## Last Turn Outcome
You successfully negotiated a 200 credit contract with Halden to deliver his ledger to the Crossed Keys Inn, though he remains skeptical of your physical condition.

## Current Turn: 4
=== PLAYER INPUT ===
I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

## Location
Marrow's Crossing (marrows_crossing)
The cobblestone streets of Marrow's Crossing are bathed in moonlight, smelling of river silt and woodsmoke under flickering streetlamps.

## inventory (cross-reference before describing item use)
- **Credits** ×200
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.




## Characters
Before introducing a new named NPC, check this list first.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Skeptical and calculating; weighing the risk of hiring the player due to their visible injuries.

- **Caron** (Old creditor) [JUST_LEFT] — Do not write dialogue or new action for this character this turn.

- **Edda** (Innkeeper at the Crossed Keys) [JUST_LEFT] — Do not write dialogue or new action for this character this turn.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
## Recent Turns

**T1:** You pull a stool out from the corner table, the wooden legs scraping harshly against the tavern's uneven floorboards. As you settle into the seat, your bruised ribs protest with a sharp, stinging reminder of your recent troubles, forcing a shallow breath. Across the table, **Caron** doesn't look up immediately; he continues to trace a line of ink in his ledger with a methodical, rhythmic precision.

The portly man finally closes the book with a soft thud, the sound swallowed by the low murmur of the closing tavern. He leans back, his belly pressing against the edge of the table, and fixes you with a gaze that is neither angry nor sympathetic—only deeply, wearyingly observant. He licks a thumb, prepping to turn a page, though he keeps his eyes pinned on your face.

"You look like you've walked through a bramble patch and come out the other side bleeding, Aren," **Caron** says, his voice a gravelly rumble. He gestures vaguely toward your disheveled appearance with a hand that bears a heavy gold ring. "I'm not a man of sudden whims or miracles. I've sat in this very chair waiting for three years of interest to accumulate, and I have no intention of letting a bit of road-wear stop me from collecting what is mine."


**T2:** You reach for your belt pouch, fingers trembling slightly from the ache in your side, and pull out your **Credits**. The small, heavy coins clatter onto the scarred wood of the table, a sharp, metallic sound that seems to cut through the tavern's low hum. You slide the pile of 500 **Credits** across the table, pushing them toward the portly man until they bump against the edge of his ledger.

"Mark it cleared," you say, your voice thinner than you intended.

**Caron** stares down at the coins, his eyes narrowing as he calculates the total without moving a muscle. He doesn't reach for the money immediately; instead, he picks up a quill, tapping the nib against his chin while he studies your face, searching for a sign of a bluff or a desperate lie. The silence stretches, heavy and suffocating, as the weight of three years of mounting interest hangs between you.

Finally, he exhales a long, weary sigh that rattles in his chest. He reaches out, his ringed fingers sweeping the coins into a neat, disciplined stack. He opens the ledger to the page where your name is etched in ink, finds the mounting total, and strikes a single, decisive line through the figures with a flourish of black ink. He closes the book once more, the sound final and heavy, and looks up at you with an expression of profound boredom.

"The principal is settled, Aren," **Caron** says, tapping the cover of the book. "But don't think for a second that being debt-free makes you a man of consequence on this road. You're just another runner with an empty purse and a long walk ahead of you."


**T3:** You push away from the table, your ribs screaming in protest as you lurch to your feet. Leaving the heavy, settled silence of the tavern behind, you step out into the cooling night air of Marrow's Crossing. The streetlamps flicker low, casting long, dancing shadows across the cobblestones, and the scent of river silt and woodsmoke hangs thick in the air.

You find **Halden** near the central well, the stone structure glowing pale under the moonlight. He is hunched over a map, the light from a small hand-lantern casting a sickly amber hue over the parchment. When you approach, he looks up, squinting through the dimness. He looks tired, the lines around his eyes deeply etched by a day of difficult trades.

"Two hundred credits to move a single book?" **Halden** asks, a skeptical brow arching as he looks from your battered face to the heavy, wax-sealed ledger tucked under his arm. He doesn't look impressed by your disheveled state or your sudden suddenness; he simply looks like a man calculating the risk of trusting a runner who looks like he's one stumble away from a collapse.

He sighs, tapping the wax seal of the ledger with a calloused finger. "You look like you've had a rough go of it, Aren. I need that book at the *Crossed Keys* settled before the morning bells, and I'd rather not hand it to someone who might drop it in a ditch because their side is broken." He pauses, weighing your worth against the cost. "Fine. Two hundred. But if a single page is torn or that seal is cracked when you reach **Edda**, you'll find I'm much less patient than **Caron**."

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 4) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
=== END PLAYER INPUT ===

**Directive:** Breathe

```

### Extract Scene User Prompt
```
## location
`marrows_crossing` | Marrow's Crossing
The cobblestone streets of Marrow's Crossing are bathed in moonlight, smelling of river silt and woodsmoke under flickering streetlamps.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | **Halden** (Merchant) — Skeptical and calculating; weighing the risk of hiring the player due to their visible injuries.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T3 context)
You push away from the table, your ribs screaming in protest as you lurch to your feet. Leaving the heavy, settled silence of the tavern behind, you step out into the cooling night air of Marrow's Crossing. The streetlamps flicker low, casting long, dancing shadows across the cobblestones, and the scent of river silt and woodsmoke hangs thick in the air.

You find **Halden** near the central well, the stone structure glowing pale under the moonlight. He is hunched over a map, the light from a small hand-lantern casting a sickly amber hue over the parchment. When you approach, he looks up, squinting through the dimness. He looks tired, the lines around his eyes deeply etched by a day of difficult trades.

"Two hundred credits to move a single book?" **Halden** asks, a skeptical brow arching as he looks from your battered face to the heavy, wax-sealed ledger tucked under his arm. He doesn't look impressed by your disheveled state or your sudden suddenness; he simply looks like a man calculating the risk of trusting a runner who looks like he's one stumble away from a collapse.

He sighs, tapping the wax seal of the ledger with a calloused finger. "You look like you've had a rough go of it, Aren. I need that book at the *Crossed Keys* settled before the morning bells, and I'd rather not hand it to someone who might drop it in a ditch because their side is broken." He pauses, weighing your worth against the cost. "Fine. Two hundred. But if a single page is torn or that seal is cracked when you reach **Edda**, you'll find I'm much less patient than **Caron**."

## CURRENT TURN 4 NARRATION
You turn your back on the central well, the amber light of **Halden**'s lantern fading into a dim smudge behind you. The walk toward the east gate is a slow, rhythmic crawl, each step sending a fresh wave of dull, throbbing heat through your bruised ribs. The sounds of the town—the distant clatter of a closing shutter, the faint murmur of a late-night conversation—begin to thin, replaced by the steady, lonely rush of the river nearby.

The east gate of Marrow's Crossing looms ahead, a heavy timber structure that stands like a silent sentinel against the encroaching darkness of the road. As you pass through the archway, the oppressive weight of the debt you just settled seems to lift, replaced by a hollow, quiet emptiness. The streetlamps give way to nothing but the pale, silver wash of moonlight on the dirt path, and for a moment, the only sound is the uneven scrape of your boots against the gravel.

The road ahead stretches out into the darkness, a ribbon of grey guided by the faint, distant glow of the *Crossed Keys* lanterns flickering on the horizon. The air is cooler here, freshened by the river breeze, and the stinging pain in your side settles into a manageable, rhythmic ache. For the first time in days, the frantic pressure of being chased or being hunted has subsided, leaving you alone with nothing but the weight of the ledger and the long, quiet trek toward your next task.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- low_morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×200
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
move: The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.
## CURRENT TURN 4 NARRATION
You turn your back on the central well, the amber light of **Halden**'s lantern fading into a dim smudge behind you. The walk toward the east gate is a slow, rhythmic crawl, each step sending a fresh wave of dull, throbbing heat through your bruised ribs. The sounds of the town—the distant clatter of a closing shutter, the faint murmur of a late-night conversation—begin to thin, replaced by the steady, lonely rush of the river nearby.

The east gate of Marrow's Crossing looms ahead, a heavy timber structure that stands like a silent sentinel against the encroaching darkness of the road. As you pass through the archway, the oppressive weight of the debt you just settled seems to lift, replaced by a hollow, quiet emptiness. The streetlamps give way to nothing but the pale, silver wash of moonlight on the dirt path, and for a moment, the only sound is the uneven scrape of your boots against the gravel.

The road ahead stretches out into the darkness, a ribbon of grey guided by the faint, distant glow of the *Crossed Keys* lanterns flickering on the horizon. The air is cooler here, freshened by the river breeze, and the stinging pain in your side settles into a manageable, rhythmic ache. For the first time in days, the frantic pressure of being chased or being hunted has subsided, leaving you alone with nothing but the weight of the ledger and the long, quiet trek toward your next task.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**East Gate Road** — The cobblestones give way to a gravel and dirt path, where the air is cooled by a steady river breeze.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## Current inventory (this turn)
- `credits`: Credits x200
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads
None currently. Generate actions that could introduce new story directions or explore the environment.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- You have sat down to face Caron and discuss your three-year-old debt.
- You successfully paid Caron the 500 credits to settle your three-year-old debt.
- Halden has hired you to deliver his ledger to the Crossed Keys Inn for 200 credits.

_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: Breathe
Gate: allow

## last turn's context (T3)
You push away from the table, your ribs screaming in protest as you lurch to your feet. Leaving the heavy, settled silence of the tavern behind, you step out into the cooling night air of Marrow's Crossing. The streetlamps flicker low, casting long, dancing shadows across the cobblestones, and the scent of river silt and woodsmoke hangs thick in the air.

You find **Halden** near the central well, the stone structure glowing pale under the moonlight. He is hunched over a map, the light from a small hand-lantern casting a sickly amber hue over the parchment. When you approach, he looks up, squinting through the dimness. He looks tired, the lines around his eyes deeply etched by a day of difficult trades.

"Two hundred credits to move a single book?" **Halden** asks, a skeptical brow arching as he looks from your battered face to the heavy, wax-sealed ledger tucked under his arm. He doesn't look impressed by your disheveled state or your sudden suddenness; he simply looks like a man calculating the risk of trusting a runner who looks like he's one stumble away from a collapse.

He sighs, tapping the wax seal of the ledger with a calloused finger. "You look like you've had a rough go of it, Aren. I need that book at the *Crossed Keys* settled before the morning bells, and I'd rather not hand it to someone who might drop it in a ditch because their side is broken." He pauses, weighing your worth against the cost. "Fine. Two hundred. But if a single page is torn or that seal is cracked when you reach **Edda**, you'll find I'm much less patient than **Caron**."

## player_intent
**move**: The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.

## CURRENT TURN 4 NARRATION
You turn your back on the central well, the amber light of **Halden**'s lantern fading into a dim smudge behind you. The walk toward the east gate is a slow, rhythmic crawl, each step sending a fresh wave of dull, throbbing heat through your bruised ribs. The sounds of the town—the distant clatter of a closing shutter, the faint murmur of a late-night conversation—begin to thin, replaced by the steady, lonely rush of the river nearby.

The east gate of Marrow's Crossing looms ahead, a heavy timber structure that stands like a silent sentinel against the encroaching darkness of the road. As you pass through the archway, the oppressive weight of the debt you just settled seems to lift, replaced by a hollow, quiet emptiness. The streetlamps give way to nothing but the pale, silver wash of moonlight on the dirt path, and for a moment, the only sound is the uneven scrape of your boots against the gravel.

The road ahead stretches out into the darkness, a ribbon of grey guided by the faint, distant glow of the *Crossed Keys* lanterns flickering on the horizon. The air is cooler here, freshened by the river breeze, and the stinging pain in your side settles into a manageable, rhythmic ache. For the first time in days, the frantic pressure of being chased or being hunted has subsided, leaving you alone with nothing but the weight of the ledger and the long, quiet trek toward your next task.
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.",
  "intent_verb": "move",
  "target": "",
  "check": {
    "required": false
  }
}
```

### Narration

You turn your back on the central well, the amber light of **Halden**'s lantern fading into a dim smudge behind you. The walk toward the east gate is a slow, rhythmic crawl, each step sending a fresh wave of dull, throbbing heat through your bruised ribs. The sounds of the town—the distant clatter of a closing shutter, the faint murmur of a late-night conversation—begin to thin, replaced by the steady, lonely rush of the river nearby.

The east gate of Marrow's Crossing looms ahead, a heavy timber structure that stands like a silent sentinel against the encroaching darkness of the road. As you pass through the archway, the oppressive weight of the debt you just settled seems to lift, replaced by a hollow, quiet emptiness. The streetlamps give way to nothing but the pale, silver wash of moonlight on the dirt path, and for a moment, the only sound is the uneven scrape of your boots against the gravel.

The road ahead stretches out into the darkness, a ribbon of grey guided by the faint, distant glow of the *Crossed Keys* lanterns flickering on the horizon. The air is cooler here, freshened by the river breeze, and the stinging pain in your side settles into a manageable, rhythmic ache. For the first time in days, the frantic pressure of being chased or being hunted has subsided, leaving you alone with nothing but the weight of the ledger and the long, quiet trek toward your next task.

### Extract Scene

```json
{
  "scene_tags": [
    "solitude",
    "travel"
  ],
  "scene_tagline": "A Lonely Trek Toward the Inn",
  "location_change": {
    "id": "east_gate_road",
    "name": "East Gate Road",
    "description": "A dirt path illuminated by moonlight, leading away from the town toward the distant glow of the Crossed Keys."
  },
  "location_description": "The cobblestones give way to a gravel and dirt path, where the air is cooled by a steady river breeze.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "halden"
    }
  ],
  "npc_update": [],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "ledger",
      "name": "Ledger",
      "notes": "A heavy book carried from the encounter with Halden.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "low_morale"
    }
  ]
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "debt_settled",
      "text": "You have successfully settled your three-year-old debt with Caron.",
      "turn": 4
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Pick up the pace to reach the inn before dawn.",
    "Scan the dark roadside for any signs of the rumored toughs.",
    "Tend to your bruised ribs using your linen bandages.",
    "Keep a firm grip on Halden's ledger as you walk."
  ],
  "outcome_summary": "You leave the town center behind, heading toward the Crossed Keys Inn under the moonlight, feeling the relief of your settled debt and the weight of your new task.",
  "thread_advance": [
    "halden_ledger_delivery"
  ],
  "thread_resolve": []
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1745t trimmed=False
- narrate: est=5940t trimmed=False
- extract.scene: est=4101t trimmed=False attempts=1
- extract.state: est=4380t trimmed=False attempts=1
- extract.storytell: est=5306t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 5

**Input:** `I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: East Gate Road
## Inventory
- Credits (200)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)
- Ledger (1)

## Last Turn Outcome
You leave the town center behind, heading toward the Crossed Keys Inn under the moonlight, feeling the relief of your settled debt and the weight of your new task.

## Current Turn: 5
=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
East Gate Road (east_gate_road)
A dirt path illuminated by moonlight, leading away from the town toward the distant glow of the Crossed Keys.

## inventory (cross-reference before describing item use)
- **Credits** ×200
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Ledger**: A heavy book carried from the encounter with Halden.




## Characters
Before introducing a new named NPC, check this list first.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: Needs a reliable courier to deliver a wax-sealed ledger to the Crossed Keys before morning.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
## Recent Turns

**T2:** You reach for your belt pouch, fingers trembling slightly from the ache in your side, and pull out your **Credits**. The small, heavy coins clatter onto the scarred wood of the table, a sharp, metallic sound that seems to cut through the tavern's low hum. You slide the pile of 500 **Credits** across the table, pushing them toward the portly man until they bump against the edge of his ledger.

"Mark it cleared," you say, your voice thinner than you intended.

**Caron** stares down at the coins, his eyes narrowing as he calculates the total without moving a muscle. He doesn't reach for the money immediately; instead, he picks up a quill, tapping the nib against his chin while he studies your face, searching for a sign of a bluff or a desperate lie. The silence stretches, heavy and suffocating, as the weight of three years of mounting interest hangs between you.

Finally, he exhales a long, weary sigh that rattles in his chest. He reaches out, his ringed fingers sweeping the coins into a neat, disciplined stack. He opens the ledger to the page where your name is etched in ink, finds the mounting total, and strikes a single, decisive line through the figures with a flourish of black ink. He closes the book once more, the sound final and heavy, and looks up at you with an expression of profound boredom.

"The principal is settled, Aren," **Caron** says, tapping the cover of the book. "But don't think for a second that being debt-free makes you a man of consequence on this road. You're just another runner with an empty purse and a long walk ahead of you."


**T3:** You push away from the table, your ribs screaming in protest as you lurch to your feet. Leaving the heavy, settled silence of the tavern behind, you step out into the cooling night air of Marrow's Crossing. The streetlamps flicker low, casting long, dancing shadows across the cobblestones, and the scent of river silt and woodsmoke hangs thick in the air.

You find **Halden** near the central well, the stone structure glowing pale under the moonlight. He is hunched over a map, the light from a small hand-lantern casting a sickly amber hue over the parchment. When you approach, he looks up, squinting through the dimness. He looks tired, the lines around his eyes deeply etched by a day of difficult trades.

"Two hundred credits to move a single book?" **Halden** asks, a skeptical brow arching as he looks from your battered face to the heavy, wax-sealed ledger tucked under his arm. He doesn't look impressed by your disheveled state or your sudden suddenness; he simply looks like a man calculating the risk of trusting a runner who looks like he's one stumble away from a collapse.

He sighs, tapping the wax seal of the ledger with a calloused finger. "You look like you've had a rough go of it, Aren. I need that book at the *Crossed Keys* settled before the morning bells, and I'd rather not hand it to someone who might drop it in a ditch because their side is broken." He pauses, weighing your worth against the cost. "Fine. Two hundred. But if a single page is torn or that seal is cracked when you reach **Edda**, you'll find I'm much less patient than **Caron**."


**T4:** You turn your back on the central well, the amber light of **Halden**'s lantern fading into a dim smudge behind you. The walk toward the east gate is a slow, rhythmic crawl, each step sending a fresh wave of dull, throbbing heat through your bruised ribs. The sounds of the town—the distant clatter of a closing shutter, the faint murmur of a late-night conversation—begin to thin, replaced by the steady, lonely rush of the river nearby.

The east gate of Marrow's Crossing looms ahead, a heavy timber structure that stands like a silent sentinel against the encroaching darkness of the road. As you pass through the archway, the oppressive weight of the debt you just settled seems to lift, replaced by a hollow, quiet emptiness. The streetlamps give way to nothing but the pale, silver wash of moonlight on the dirt path, and for a moment, the only sound is the uneven scrape of your boots against the gravel.

The road ahead stretches out into the darkness, a ribbon of grey guided by the faint, distant glow of the *Crossed Keys* lanterns flickering on the horizon. The air is cooler here, freshened by the river breeze, and the stinging pain in your side settles into a manageable, rhythmic ache. For the first time in days, the frantic pressure of being chased or being hunted has subsided, leaving you alone with nothing but the weight of the ledger and the long, quiet trek toward your next task.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 5) Result


**Band:** PARTIAL → The persuade results in a partial. You get what you asked for, but they now hold leverage over you.


**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.

=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===


```

### Extract Scene User Prompt
```
## location
`east_gate_road` | East Gate Road
A dirt path illuminated by moonlight, leading away from the town toward the distant glow of the Crossed Keys.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T4 context)
You turn your back on the central well, the amber light of **Halden**'s lantern fading into a dim smudge behind you. The walk toward the east gate is a slow, rhythmic crawl, each step sending a fresh wave of dull, throbbing heat through your bruised ribs. The sounds of the town—the distant clatter of a closing shutter, the faint murmur of a late-night conversation—begin to thin, replaced by the steady, lonely rush of the river nearby.

The east gate of Marrow's Crossing looms ahead, a heavy timber structure that stands like a silent sentinel against the encroaching darkness of the road. As you pass through the archway, the oppressive weight of the debt you just settled seems to lift, replaced by a hollow, quiet emptiness. The streetlamps give way to nothing but the pale, silver wash of moonlight on the dirt path, and for a moment, the only sound is the uneven scrape of your boots against the gravel.

The road ahead stretches out into the darkness, a ribbon of grey guided by the faint, distant glow of the *Crossed Keys* lanterns flickering on the horizon. The air is cooler here, freshened by the river breeze, and the stinging pain in your side settles into a manageable, rhythmic ache. For the first time in days, the frantic pressure of being chased or being hunted has subsided, leaving you alone with nothing but the weight of the ledger and the long, quiet trek toward your next task.

## CURRENT TURN 5 NARRATION
You lurch toward the entrance of the *Crossed Keys*, your hand instinctively hovering near the **Iron dagger** at your belt as you approach the two men blocking the threshold. **Bald Tough** and **Scarred Tough** stand like twin pillars of ill intent, their shadows stretching long and jagged across the dirt path under the moonlight. They look up as you approach, their expressions shifting from idle boredom to a shared, predatory amusement.

"What are we doing?" **Bald Tough** asks, a low, gravelly chuckle vibrating in his chest. He doesn't move an inch to let you pass, instead crossing his thick arms over his chest, his biceps straining against the fabric of his jerkin. He looks you up and down, his gaze lingering on your labored breathing and the way you favor your left side. "We're just waiting for a delivery, runner. A very specific, very important delivery."

**Scarred Tough** steps slightly to the side, pivoting to flank you, cutting off your easy path back toward the road. He licks his lips, a thin, unpleasant grin spreading across his face, revealing a chipped front tooth. He doesn't look like he's looking for a conversation; he looks like he's looking for an opening. "You're a persistent one, aren't you? Most folks see us and find a different road to walk."

"Look," **Bald Tough** says, leaning forward so the moonlight catches the dull sheen of sweat on his forehead, "we aren't here to cause a fuss with a man who looks like he's held together by spit and prayer. We're here on business for a client. Move along, and maybe we won't have to make your night any more difficult than it already is." He gestures vaguely toward the inn, a silent warning that your presence is an unwanted interruption to their vigil.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×200
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Ledger ×1 — A heavy book carried from the encounter with Halden.

## player_intent
persuade: Question the two toughs at the inn door to understand their presence and intentions.
## CURRENT TURN 5 NARRATION
You lurch toward the entrance of the *Crossed Keys*, your hand instinctively hovering near the **Iron dagger** at your belt as you approach the two men blocking the threshold. **Bald Tough** and **Scarred Tough** stand like twin pillars of ill intent, their shadows stretching long and jagged across the dirt path under the moonlight. They look up as you approach, their expressions shifting from idle boredom to a shared, predatory amusement.

"What are we doing?" **Bald Tough** asks, a low, gravelly chuckle vibrating in his chest. He doesn't move an inch to let you pass, instead crossing his thick arms over his chest, his biceps straining against the fabric of his jerkin. He looks you up and down, his gaze lingering on your labored breathing and the way you favor your left side. "We're just waiting for a delivery, runner. A very specific, very important delivery."

**Scarred Tough** steps slightly to the side, pivoting to flank you, cutting off your easy path back toward the road. He licks his lips, a thin, unpleasant grin spreading across his face, revealing a chipped front tooth. He doesn't look like he's looking for a conversation; he looks like he's looking for an opening. "You're a persistent one, aren't you? Most folks see us and find a different road to walk."

"Look," **Bald Tough** says, leaning forward so the moonlight catches the dull sheen of sweat on his forehead, "we aren't here to cause a fuss with a man who looks like he's held together by spit and prayer. We're here on business for a client. Move along, and maybe we won't have to make your night any more difficult than it already is." He gestures vaguely toward the inn, a silent warning that your presence is an unwanted interruption to their vigil.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `tough_a` | **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `tough_b` | **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

## location
**East Gate Road** — A dirt path illuminated by moonlight, leading away from the town toward the distant glow of the Crossed Keys.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## Current inventory (this turn)
- `credits`: Credits x200
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `ledger`: Ledger x1 — A heavy book carried from the encounter with Halden.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads
None currently. Generate actions that could introduce new story directions or explore the environment.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- You have sat down to face Caron and discuss your three-year-old debt.
- You successfully paid Caron the 500 credits to settle your three-year-old debt.
- Halden has hired you to deliver his ledger to the Crossed Keys Inn for 200 credits.
- You have successfully settled your three-year-old debt with Caron.

_(immutable section omitted — see Static Context > Seed State)_

## rules_outcome
Band: PARTIAL. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.

## pacing_context
Directive: none
Gate: allow

## last turn's context (T4)
You turn your back on the central well, the amber light of **Halden**'s lantern fading into a dim smudge behind you. The walk toward the east gate is a slow, rhythmic crawl, each step sending a fresh wave of dull, throbbing heat through your bruised ribs. The sounds of the town—the distant clatter of a closing shutter, the faint murmur of a late-night conversation—begin to thin, replaced by the steady, lonely rush of the river nearby.

The east gate of Marrow's Crossing looms ahead, a heavy timber structure that stands like a silent sentinel against the encroaching darkness of the road. As you pass through the archway, the oppressive weight of the debt you just settled seems to lift, replaced by a hollow, quiet emptiness. The streetlamps give way to nothing but the pale, silver wash of moonlight on the dirt path, and for a moment, the only sound is the uneven scrape of your boots against the gravel.

The road ahead stretches out into the darkness, a ribbon of grey guided by the faint, distant glow of the *Crossed Keys* lanterns flickering on the horizon. The air is cooler here, freshened by the river breeze, and the stinging pain in your side settles into a manageable, rhythmic ache. For the first time in days, the frantic pressure of being chased or being hunted has subsided, leaving you alone with nothing but the weight of the ledger and the long, quiet trek toward your next task.

## player_intent
**persuade**: Question the two toughs at the inn door to understand their presence and intentions.

## CURRENT TURN 5 NARRATION
You lurch toward the entrance of the *Crossed Keys*, your hand instinctively hovering near the **Iron dagger** at your belt as you approach the two men blocking the threshold. **Bald Tough** and **Scarred Tough** stand like twin pillars of ill intent, their shadows stretching long and jagged across the dirt path under the moonlight. They look up as you approach, their expressions shifting from idle boredom to a shared, predatory amusement.

"What are we doing?" **Bald Tough** asks, a low, gravelly chuckle vibrating in his chest. He doesn't move an inch to let you pass, instead crossing his thick arms over his chest, his biceps straining against the fabric of his jerkin. He looks you up and down, his gaze lingering on your labored breathing and the way you favor your left side. "We're just waiting for a delivery, runner. A very specific, very important delivery."

**Scarred Tough** steps slightly to the side, pivoting to flank you, cutting off your easy path back toward the road. He licks his lips, a thin, unpleasant grin spreading across his face, revealing a chipped front tooth. He doesn't look like he's looking for a conversation; he looks like he's looking for an opening. "You're a persistent one, aren't you? Most folks see us and find a different road to walk."

"Look," **Bald Tough** says, leaning forward so the moonlight catches the dull sheen of sweat on his forehead, "we aren't here to cause a fuss with a man who looks like he's held together by spit and prayer. We're here on business for a client. Move along, and maybe we won't have to make your night any more difficult than it already is." He gestures vaguely toward the inn, a silent warning that your presence is an unwanted interruption to their vigil.
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "Question the two toughs at the inn door to understand their presence and intentions.",
  "intent_verb": "persuade",
  "target": "the two toughs",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal"
  }
}
```

### Narration

You lurch toward the entrance of the *Crossed Keys*, your hand instinctively hovering near the **Iron dagger** at your belt as you approach the two men blocking the threshold. **Bald Tough** and **Scarred Tough** stand like twin pillars of ill intent, their shadows stretching long and jagged across the dirt path under the moonlight. They look up as you approach, their expressions shifting from idle boredom to a shared, predatory amusement.

"What are we doing?" **Bald Tough** asks, a low, gravelly chuckle vibrating in his chest. He doesn't move an inch to let you pass, instead crossing his thick arms over his chest, his biceps straining against the fabric of his jerkin. He looks you up and down, his gaze lingering on your labored breathing and the way you favor your left side. "We're just waiting for a delivery, runner. A very specific, very important delivery."

**Scarred Tough** steps slightly to the side, pivoting to flank you, cutting off your easy path back toward the road. He licks his lips, a thin, unpleasant grin spreading across his face, revealing a chipped front tooth. He doesn't look like he's looking for a conversation; he looks like he's looking for an opening. "You're a persistent one, aren't you? Most folks see us and find a different road to walk."

"Look," **Bald Tough** says, leaning forward so the moonlight catches the dull sheen of sweat on his forehead, "we aren't here to cause a fuss with a man who looks like he's held together by spit and prayer. We're here on business for a client. Move along, and maybe we won't have to make your night any more difficult than it already is." He gestures vaguely toward the inn, a silent warning that your presence is an unwanted interruption to their vigil.

### Extract Scene

```json
{
  "scene_tags": [
    "confrontation",
    "intimidation",
    "tense_standoff"
  ],
  "scene_tagline": "A Predatory Welcome",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Blocking the entrance of the Crossed Keys, acting predatory and amused by the player's injury."
    },
    {
      "id": "tough_b",
      "notes": "Flanking the player to cut off their retreat, looking for an opening to strike."
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "toughs_at_crossed_keys",
      "text": "Two hired thugs, Bald Tough and Scarred Tough, are guarding the entrance of the Crossed Keys Inn, claiming to wait for a specific delivery.",
      "turn": 5
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Show them the ledger to see if it's their target.",
    "Try to intimidate them with a stern, steady gaze.",
    "Attempt to slip past Scarred Tough into the inn.",
    "Ask who their client is and what they are expecting."
  ],
  "outcome_summary": "You confront the two thugs at the inn entrance, but they block your path and warn you to move along, hinting at a specific delivery they are guarding.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior"
  },
  "thread_advance": [],
  "thread_resolve": [],
  "thread_add": {
    "id": "the_inn_vigil",
    "summary": "Two thugs are guarding the Crossed Keys Inn for a mysterious client, potentially targeting your delivery.",
    "scope": "scene",
    "active": true,
    "urgency": "normal",
    "tags": [
      "conflict",
      "mystery"
    ],
    "progress": 0,
    "promotes": []
  }
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1704t trimmed=False
- narrate: est=6076t trimmed=False
- extract.scene: est=4073t trimmed=False attempts=1
- extract.state: est=4467t trimmed=False attempts=1
- extract.storytell: est=5464t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 5

**Input:** ``

## User Prompts

### Ruling User Prompt
```
(no ruling call this turn)
```

### Narrate User Prompt
```
(no narrate call)
```

### Extract Scene User Prompt
```
(not captured)
```

### Extract State User Prompt
```
(not captured)
```

### Storyteller User Prompt
```
(not captured)
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{}
```

### Extract State

```json
{}
```

### Storyteller

```json
{}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

```json
{}
```


---

# TURN 6

**Input:** `I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: East Gate Road
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Blocking the entrance of the Crossed Keys, acting predatory and amused by the player's injury.
- Scarred Tough (Road thug) — Flanking the player to cut off their retreat, looking for an opening to strike.

## Inventory
- Credits (200)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)
- Ledger (1)


## Current Turn: 6
=== PLAYER INPUT ===
I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
East Gate Road (east_gate_road)
A dirt path illuminated by moonlight, leading away from the town toward the distant glow of the Crossed Keys.

## inventory (cross-reference before describing item use)
- **Credits** ×200
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Ledger**: A heavy book carried from the encounter with Halden.




## Characters
Before introducing a new named NPC, check this list first.

- **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad. | Blocking the entrance of the Crossed Keys, acting predatory and amused by the player's injury.

- **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains. | Flanking the player to cut off their retreat, looking for an opening to strike.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: Needs a reliable courier to deliver a wax-sealed ledger to the Crossed Keys before morning.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Met with Caron at the tavern to address the long-standing debt.
- [T2] Paid Caron 500 credits, successfully clearing the debt from his ledger.
- [T3] Contracted by Halden to deliver a wax-sealed ledger to Edda at the Crossed Keys Inn for 200 credits.
## Recent Turns

**T4:** You turn your back on the central well, the amber light of **Halden**'s lantern fading into a dim smudge behind you. The walk toward the east gate is a slow, rhythmic crawl, each step sending a fresh wave of dull, throbbing heat through your bruised ribs. The sounds of the town—the distant clatter of a closing shutter, the faint murmur of a late-night conversation—begin to thin, replaced by the steady, lonely rush of the river nearby.

The east gate of Marrow's Crossing looms ahead, a heavy timber structure that stands like a silent sentinel against the encroaching darkness of the road. As you pass through the archway, the oppressive weight of the debt you just settled seems to lift, replaced by a hollow, quiet emptiness. The streetlamps give way to nothing but the pale, silver wash of moonlight on the dirt path, and for a moment, the only sound is the uneven scrape of your boots against the gravel.

The road ahead stretches out into the darkness, a ribbon of grey guided by the faint, distant glow of the *Crossed Keys* lanterns flickering on the horizon. The air is cooler here, freshened by the river breeze, and the stinging pain in your side settles into a manageable, rhythmic ache. For the first time in days, the frantic pressure of being chased or being hunted has subsided, leaving you alone with nothing but the weight of the ledger and the long, quiet trek toward your next task.


**T5:** You lurch toward the entrance of the *Crossed Keys*, your hand instinctively hovering near the **Iron dagger** at your belt as you approach the two men blocking the threshold. **Bald Tough** and **Scarred Tough** stand like twin pillars of ill intent, their shadows stretching long and jagged across the dirt path under the moonlight. They look up as you approach, their expressions shifting from idle boredom to a shared, predatory amusement.

"What are we doing?" **Bald Tough** asks, a low, gravelly chuckle vibrating in his chest. He doesn't move an inch to let you pass, instead crossing his thick arms over his chest, his biceps straining against the fabric of his jerkin. He looks you up and down, his gaze lingering on your labored breathing and the way you favor your left side. "We're just waiting for a delivery, runner. A very specific, very important delivery."

**Scarred Tough** steps slightly to the side, pivoting to flank you, cutting off your easy path back toward the road. He licks his lips, a thin, unpleasant grin spreading across his face, revealing a chipped front tooth. He doesn't look like he's looking for a conversation; he looks like he's looking for an opening. "You're a persistent one, aren't you? Most folks see us and find a different road to walk."

"Look," **Bald Tough** says, leaning forward so the moonlight catches the dull sheen of sweat on his forehead, "we aren't here to cause a fuss with a man who looks like he's held together by spit and prayer. We're here on business for a client. Move along, and maybe we won't have to make your night any more difficult than it already is." He gestures vaguely toward the inn, a silent warning that your presence is an unwanted interruption to their vigil.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 6) Result


**Band:** SUCCESS → The deceive succeeds cleanly. Clean success — you do what you intended.


**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.

=== PLAYER INPUT ===
I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
=== END PLAYER INPUT ===

**Beat:** PRESSURE — surface as `npc_behavior`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
```

### Extract Scene User Prompt
```
## location
`east_gate_road` | East Gate Road
A dirt path illuminated by moonlight, leading away from the town toward the distant glow of the Crossed Keys.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Blocking the entrance of the Crossed Keys, acting predatory and amused by the player's injury.
- `tough_b` | **Scarred Tough** (Road thug) — Flanking the player to cut off their retreat, looking for an opening to strike.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T5 context)
You lurch toward the entrance of the *Crossed Keys*, your hand instinctively hovering near the **Iron dagger** at your belt as you approach the two men blocking the threshold. **Bald Tough** and **Scarred Tough** stand like twin pillars of ill intent, their shadows stretching long and jagged across the dirt path under the moonlight. They look up as you approach, their expressions shifting from idle boredom to a shared, predatory amusement.

"What are we doing?" **Bald Tough** asks, a low, gravelly chuckle vibrating in his chest. He doesn't move an inch to let you pass, instead crossing his thick arms over his chest, his biceps straining against the fabric of his jerkin. He looks you up and down, his gaze lingering on your labored breathing and the way you favor your left side. "We're just waiting for a delivery, runner. A very specific, very important delivery."

**Scarred Tough** steps slightly to the side, pivoting to flank you, cutting off your easy path back toward the road. He licks his lips, a thin, unpleasant grin spreading across his face, revealing a chipped front tooth. He doesn't look like he's looking for a conversation; he looks like he's looking for an opening. "You're a persistent one, aren't you? Most folks see us and find a different road to walk."

"Look," **Bald Tough** says, leaning forward so the moonlight catches the dull sheen of sweat on his forehead, "we aren't here to cause a fuss with a man who looks like he's held together by spit and prayer. We're here on business for a client. Move along, and maybe we won't have to make your night any more difficult than it already is." He gestures vaguely toward the inn, a silent warning that your presence is an unwanted interruption to their vigil.

## CURRENT TURN 6 NARRATION
You reach into your pouch and pull out the **Credits**, the metal clinking with a heavy, decisive sound as you drop them onto the dirt between your boots and theirs. The coins spill across the gravel, catching the pale moonlight like fallen stars. "Caron's coin is paid," you say, your voice steady despite the sharp pull of your ribs. "You've got your business. Move aside."

**Bald Tough** stares down at the pile of coin, his eyes widening slightly as the greed of the sight battles with his professional posturing. He looks from the money up to your face, a flicker of calculation crossing his features. He nudges one of the coins with the toe of a heavy boot, testing to see if it's a trick, before a slow, lopsided grin splits his face. He gestures for **Scarred Tough** to step back, though the smaller man remains tensed, his hand hovering near a heavy club at his hip.

"Well now," **Bald Tough** rumbles, his gravelly voice losing its edge of menace and replacing it with a tone of begrudging respect. He reaches down, scooping up a handful of the metal with a practiced, quick motion. "Seems our client's business just got a lot more interesting. Move on then, runner. We've got our fee, and we've got no more use for a man who's clearly had a long day."

**Scarred Tough** doesn't look quite as satisfied; he lingers for a second longer, his eyes darting toward the heavy **Ledger** tucked under your arm, clearly weighing the value of the book against the coin on the ground. He spits a glob of dark phlegm onto the path near your feet, a final, parting insult, before stepping back to clear the doorway of the *Crossed Keys*, leaving the path to the inn wide and unobstructed.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×200
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Ledger ×1 — A heavy book carried from the encounter with Halden.

## player_intent
deceive: The player attempts to bribe the thugs with 200 credits to clear their path.
## CURRENT TURN 6 NARRATION
You reach into your pouch and pull out the **Credits**, the metal clinking with a heavy, decisive sound as you drop them onto the dirt between your boots and theirs. The coins spill across the gravel, catching the pale moonlight like fallen stars. "Caron's coin is paid," you say, your voice steady despite the sharp pull of your ribs. "You've got your business. Move aside."

**Bald Tough** stares down at the pile of coin, his eyes widening slightly as the greed of the sight battles with his professional posturing. He looks from the money up to your face, a flicker of calculation crossing his features. He nudges one of the coins with the toe of a heavy boot, testing to see if it's a trick, before a slow, lopsided grin splits his face. He gestures for **Scarred Tough** to step back, though the smaller man remains tensed, his hand hovering near a heavy club at his hip.

"Well now," **Bald Tough** rumbles, his gravelly voice losing its edge of menace and replacing it with a tone of begrudging respect. He reaches down, scooping up a handful of the metal with a practiced, quick motion. "Seems our client's business just got a lot more interesting. Move on then, runner. We've got our fee, and we've got no more use for a man who's clearly had a long day."

**Scarred Tough** doesn't look quite as satisfied; he lingers for a second longer, his eyes darting toward the heavy **Ledger** tucked under your arm, clearly weighing the value of the book against the coin on the ground. He spits a glob of dark phlegm onto the path near your feet, a final, parting insult, before stepping back to clear the doorway of the *Crossed Keys*, leaving the path to the inn wide and unobstructed.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `tough_a` | **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `tough_b` | **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

## location
**East Gate Road** — A dirt path illuminated by moonlight, leading away from the town toward the distant glow of the Crossed Keys.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `ledger`: Ledger x1 — A heavy book carried from the encounter with Halden.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads
None currently. Generate actions that could introduce new story directions or explore the environment.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your long-standing debt to Caron has finally been settled in full.
- Halden has entrusted you with a wax-sealed ledger to be delivered to Edda at the Crossed Keys Inn.
- Rumors persist of hired thugs guarding the entrance to the Crossed Keys Inn.
- You have arrived in Marrow's Crossing, battered from your journey.

_(immutable section omitted — see Static Context > Seed State)_

## rules_outcome
Band: SUCCESS. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.

## pacing_context
Directive: none
Gate: allow

## last turn's context (T5)
You lurch toward the entrance of the *Crossed Keys*, your hand instinctively hovering near the **Iron dagger** at your belt as you approach the two men blocking the threshold. **Bald Tough** and **Scarred Tough** stand like twin pillars of ill intent, their shadows stretching long and jagged across the dirt path under the moonlight. They look up as you approach, their expressions shifting from idle boredom to a shared, predatory amusement.

"What are we doing?" **Bald Tough** asks, a low, gravelly chuckle vibrating in his chest. He doesn't move an inch to let you pass, instead crossing his thick arms over his chest, his biceps straining against the fabric of his jerkin. He looks you up and down, his gaze lingering on your labored breathing and the way you favor your left side. "We're just waiting for a delivery, runner. A very specific, very important delivery."

**Scarred Tough** steps slightly to the side, pivoting to flank you, cutting off your easy path back toward the road. He licks his lips, a thin, unpleasant grin spreading across his face, revealing a chipped front tooth. He doesn't look like he's looking for a conversation; he looks like he's looking for an opening. "You're a persistent one, aren't you? Most folks see us and find a different road to walk."

"Look," **Bald Tough** says, leaning forward so the moonlight catches the dull sheen of sweat on his forehead, "we aren't here to cause a fuss with a man who looks like he's held together by spit and prayer. We're here on business for a client. Move along, and maybe we won't have to make your night any more difficult than it already is." He gestures vaguely toward the inn, a silent warning that your presence is an unwanted interruption to their vigil.

## player_intent
**deceive**: The player attempts to bribe the thugs with 200 credits to clear their path.

## CURRENT TURN 6 NARRATION
You reach into your pouch and pull out the **Credits**, the metal clinking with a heavy, decisive sound as you drop them onto the dirt between your boots and theirs. The coins spill across the gravel, catching the pale moonlight like fallen stars. "Caron's coin is paid," you say, your voice steady despite the sharp pull of your ribs. "You've got your business. Move aside."

**Bald Tough** stares down at the pile of coin, his eyes widening slightly as the greed of the sight battles with his professional posturing. He looks from the money up to your face, a flicker of calculation crossing his features. He nudges one of the coins with the toe of a heavy boot, testing to see if it's a trick, before a slow, lopsided grin splits his face. He gestures for **Scarred Tough** to step back, though the smaller man remains tensed, his hand hovering near a heavy club at his hip.

"Well now," **Bald Tough** rumbles, his gravelly voice losing its edge of menace and replacing it with a tone of begrudging respect. He reaches down, scooping up a handful of the metal with a practiced, quick motion. "Seems our client's business just got a lot more interesting. Move on then, runner. We've got our fee, and we've got no more use for a man who's clearly had a long day."

**Scarred Tough** doesn't look quite as satisfied; he lingers for a second longer, his eyes darting toward the heavy **Ledger** tucked under your arm, clearly weighing the value of the book against the coin on the ground. He spits a glob of dark phlegm onto the path near your feet, a final, parting insult, before stepping back to clear the doorway of the *Crossed Keys*, leaving the path to the inn wide and unobstructed.
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the thugs with 200 credits to clear their path.",
  "intent_verb": "deceive",
  "target": "Bald Tough and Scarred Tough",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal"
  }
}
```

### Narration

You reach into your pouch and pull out the **Credits**, the metal clinking with a heavy, decisive sound as you drop them onto the dirt between your boots and theirs. The coins spill across the gravel, catching the pale moonlight like fallen stars. "Caron's coin is paid," you say, your voice steady despite the sharp pull of your ribs. "You've got your business. Move aside."

**Bald Tough** stares down at the pile of coin, his eyes widening slightly as the greed of the sight battles with his professional posturing. He looks from the money up to your face, a flicker of calculation crossing his features. He nudges one of the coins with the toe of a heavy boot, testing to see if it's a trick, before a slow, lopsided grin splits his face. He gestures for **Scarred Tough** to step back, though the smaller man remains tensed, his hand hovering near a heavy club at his hip.

"Well now," **Bald Tough** rumbles, his gravelly voice losing its edge of menace and replacing it with a tone of begrudging respect. He reaches down, scooping up a handful of the metal with a practiced, quick motion. "Seems our client's business just got a lot more interesting. Move on then, runner. We've got our fee, and we've got no more use for a man who's clearly had a long day."

**Scarred Tough** doesn't look quite as satisfied; he lingers for a second longer, his eyes darting toward the heavy **Ledger** tucked under your arm, clearly weighing the value of the book against the coin on the ground. He spits a glob of dark phlegm onto the path near your feet, a final, parting insult, before stepping back to clear the doorway of the *Crossed Keys*, leaving the path to the inn wide and unobstructed.

### Extract Scene

```json
{
  "scene_tags": [
    "negotiation",
    "bribery",
    "tension_release"
  ],
  "scene_tagline": "A Bribe Accepted",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Greedy and begrudgingly respectful after being bribed; no longer actively blocking the player."
    },
    {
      "id": "tough_b",
      "notes": "Suspicious and unsatisfied; eyeing the player's ledger with interest before stepping aside."
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 200
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "thugs_bribed",
      "text": "You successfully bribed Bald Tough and Scarred Tough with 200 credits, clearing your path to the Crossed Keys Inn.",
      "turn": 6
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Enter the Crossed Keys and find Edda to deliver the ledger.",
    "Keep a close eye on Scarred Tough as you pass him.",
    "Search the immediate area for any more dropped coins.",
    "Head straight to the bar to nurse your bruised ribs."
  ],
  "outcome_summary": "The bribe works; Bald Tough accepts the coins and orders Scarred Tough to step aside, granting you access to the inn.",
  "gm_beat": {
    "type": "opportunity",
    "surface_as": "npc_behavior"
  },
  "thread_advance": [],
  "thread_resolve": []
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1725t trimmed=False
- narrate: est=5828t trimmed=False
- extract.scene: est=4257t trimmed=False attempts=1
- extract.state: est=4450t trimmed=False attempts=1
- extract.storytell: est=5479t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 7

**Input:** `I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: East Gate Road
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Greedy and begrudgingly respectful after being bribed; no longer actively blocking the player.
- Scarred Tough (Road thug) — Suspicious and unsatisfied; eyeing the player's ledger with interest before stepping aside.

## Inventory
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)
- Ledger (1)

## Last Turn Outcome
The bribe works; Bald Tough accepts the coins and orders Scarred Tough to step aside, granting you access to the inn.

## Current Turn: 7
=== PLAYER INPUT ===
I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
East Gate Road (east_gate_road)
A dirt path illuminated by moonlight, leading away from the town toward the distant glow of the Crossed Keys.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Ledger**: A heavy book carried from the encounter with Halden.




## Characters
Before introducing a new named NPC, check this list first.

- **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad. | Greedy and begrudgingly respectful after being bribed; no longer actively blocking the player.

- **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains. | Suspicious and unsatisfied; eyeing the player's ledger with interest before stepping aside.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: Needs a reliable courier to deliver a wax-sealed ledger to the Crossed Keys before morning.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Met with Caron at the tavern to address the long-standing debt.
- [T2] Paid Caron 500 credits, successfully clearing the debt from his ledger.
- [T3] Contracted by Halden to deliver a wax-sealed ledger to Edda at the Crossed Keys Inn for 200 credits.
## Recent Turns

**T4:** You turn your back on the central well, the amber light of **Halden**'s lantern fading into a dim smudge behind you. The walk toward the east gate is a slow, rhythmic crawl, each step sending a fresh wave of dull, throbbing heat through your bruised ribs. The sounds of the town—the distant clatter of a closing shutter, the faint murmur of a late-night conversation—begin to thin, replaced by the steady, lonely rush of the river nearby.

The east gate of Marrow's Crossing looms ahead, a heavy timber structure that stands like a silent sentinel against the encroaching darkness of the road. As you pass through the archway, the oppressive weight of the debt you just settled seems to lift, replaced by a hollow, quiet emptiness. The streetlamps give way to nothing but the pale, silver wash of moonlight on the dirt path, and for a moment, the only sound is the uneven scrape of your boots against the gravel.

The road ahead stretches out into the darkness, a ribbon of grey guided by the faint, distant glow of the *Crossed Keys* lanterns flickering on the horizon. The air is cooler here, freshened by the river breeze, and the stinging pain in your side settles into a manageable, rhythmic ache. For the first time in days, the frantic pressure of being chased or being hunted has subsided, leaving you alone with nothing but the weight of the ledger and the long, quiet trek toward your next task.


**T5:** You lurch toward the entrance of the *Crossed Keys*, your hand instinctively hovering near the **Iron dagger** at your belt as you approach the two men blocking the threshold. **Bald Tough** and **Scarred Tough** stand like twin pillars of ill intent, their shadows stretching long and jagged across the dirt path under the moonlight. They look up as you approach, their expressions shifting from idle boredom to a shared, predatory amusement.

"What are we doing?" **Bald Tough** asks, a low, gravelly chuckle vibrating in his chest. He doesn't move an inch to let you pass, instead crossing his thick arms over his chest, his biceps straining against the fabric of his jerkin. He looks you up and down, his gaze lingering on your labored breathing and the way you favor your left side. "We're just waiting for a delivery, runner. A very specific, very important delivery."

**Scarred Tough** steps slightly to the side, pivoting to flank you, cutting off your easy path back toward the road. He licks his lips, a thin, unpleasant grin spreading across his face, revealing a chipped front tooth. He doesn't look like he's looking for a conversation; he looks like he's looking for an opening. "You're a persistent one, aren't you? Most folks see us and find a different road to walk."

"Look," **Bald Tough** says, leaning forward so the moonlight catches the dull sheen of sweat on his forehead, "we aren't here to cause a fuss with a man who looks like he's held together by spit and prayer. We're here on business for a client. Move along, and maybe we won't have to make your night any more difficult than it already is." He gestures vaguely toward the inn, a silent warning that your presence is an unwanted interruption to their vigil.


**T6:** You reach into your pouch and pull out the **Credits**, the metal clinking with a heavy, decisive sound as you drop them onto the dirt between your boots and theirs. The coins spill across the gravel, catching the pale moonlight like fallen stars. "Caron's coin is paid," you say, your voice steady despite the sharp pull of your ribs. "You've got your business. Move aside."

**Bald Tough** stares down at the pile of coin, his eyes widening slightly as the greed of the sight battles with his professional posturing. He looks from the money up to your face, a flicker of calculation crossing his features. He nudges one of the coins with the toe of a heavy boot, testing to see if it's a trick, before a slow, lopsided grin splits his face. He gestures for **Scarred Tough** to step back, though the smaller man remains tensed, his hand hovering near a heavy club at his hip.

"Well now," **Bald Tough** rumbles, his gravelly voice losing its edge of menace and replacing it with a tone of begrudging respect. He reaches down, scooping up a handful of the metal with a practiced, quick motion. "Seems our client's business just got a lot more interesting. Move on then, runner. We've got our fee, and we've got no more use for a man who's clearly had a long day."

**Scarred Tough** doesn't look quite as satisfied; he lingers for a second longer, his eyes darting toward the heavy **Ledger** tucked under your arm, clearly weighing the value of the book against the coin on the ground. He spits a glob of dark phlegm onto the path near your feet, a final, parting insult, before stepping back to clear the doorway of the *Crossed Keys*, leaving the path to the inn wide and unobstructed.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 7) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
=== END PLAYER INPUT ===

**Beat:** OPPORTUNITY — surface as `npc_behavior`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
```

### Extract Scene User Prompt
```
## location
`east_gate_road` | East Gate Road
A dirt path illuminated by moonlight, leading away from the town toward the distant glow of the Crossed Keys.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Greedy and begrudgingly respectful after being bribed; no longer actively blocking the player.
- `tough_b` | **Scarred Tough** (Road thug) — Suspicious and unsatisfied; eyeing the player's ledger with interest before stepping aside.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T6 context)
You reach into your pouch and pull out the **Credits**, the metal clinking with a heavy, decisive sound as you drop them onto the dirt between your boots and theirs. The coins spill across the gravel, catching the pale moonlight like fallen stars. "Caron's coin is paid," you say, your voice steady despite the sharp pull of your ribs. "You've got your business. Move aside."

**Bald Tough** stares down at the pile of coin, his eyes widening slightly as the greed of the sight battles with his professional posturing. He looks from the money up to your face, a flicker of calculation crossing his features. He nudges one of the coins with the toe of a heavy boot, testing to see if it's a trick, before a slow, lopsided grin splits his face. He gestures for **Scarred Tough** to step back, though the smaller man remains tensed, his hand hovering near a heavy club at his hip.

"Well now," **Bald Tough** rumbles, his gravelly voice losing its edge of menace and replacing it with a tone of begrudging respect. He reaches down, scooping up a handful of the metal with a practiced, quick motion. "Seems our client's business just got a lot more interesting. Move on then, runner. We've got our fee, and we've got no more use for a man who's clearly had a long day."

**Scarred Tough** doesn't look quite as satisfied; he lingers for a second longer, his eyes darting toward the heavy **Ledger** tucked under your arm, clearly weighing the value of the book against the coin on the ground. He spits a glob of dark phlegm onto the path near your feet, a final, parting insult, before stepping back to clear the doorway of the *Crossed Keys*, leaving the path to the inn wide and unobstructed.

## CURRENT TURN 7 NARRATION
You push past the two thugs, your boots crunching on the gravel of the *Crossed Keys* porch before you duck under the low lintel of the door. Inside, the air is thick with the scent of roasted mutton, spilled ale, and the comforting, smoky warmth of a dying hearth. The common room is mostly empty, the shadows stretching long across the floorboards, but you find your target near a corner booth where a single candle flickers low.

**Halden** looks up as you approach, his eyes widening slightly when he sees your disheveled state and the way you lean heavily against the wooden table. He doesn't comment on your bruised appearance, though a flicker of sympathy crosses his weathered face. He pulls out a stool for you, the wood scraping harshly against the floor, and gestures for you to sit.

You reach into your coat, your fingers brushing against the heavy, wax-sealed **Ledger**, and slide it across the scarred tabletop toward him. As you hand it over, the weight of the task finally leaves your shoulders, replaced by a mounting, restless energy. You have fulfilled your end of the bargain, and the emptiness of your coin pouch is a stinging reminder of how much further you have to go to truly be free.

**Halden** takes the book with both hands, his fingers tracing the raised wax of the seal with a reverent touch. He looks from the book to you, a small, knowing smile tugging at the corners of his mouth. "You made it, then," he says softly, his voice cutting through the quiet of the inn. He leans in closer, his tone dropping to a conspiratorial whisper. "Since you've gone through such trouble to reach me, perhaps there's another bit of business that requires a runner of your... particular persistence."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Ledger ×1 — A heavy book carried from the encounter with Halden.

## player_intent
negotiate: The player hands over the merchant seal and ledger to Halden to complete the transaction.
## CURRENT TURN 7 NARRATION
You push past the two thugs, your boots crunching on the gravel of the *Crossed Keys* porch before you duck under the low lintel of the door. Inside, the air is thick with the scent of roasted mutton, spilled ale, and the comforting, smoky warmth of a dying hearth. The common room is mostly empty, the shadows stretching long across the floorboards, but you find your target near a corner booth where a single candle flickers low.

**Halden** looks up as you approach, his eyes widening slightly when he sees your disheveled state and the way you lean heavily against the wooden table. He doesn't comment on your bruised appearance, though a flicker of sympathy crosses his weathered face. He pulls out a stool for you, the wood scraping harshly against the floor, and gestures for you to sit.

You reach into your coat, your fingers brushing against the heavy, wax-sealed **Ledger**, and slide it across the scarred tabletop toward him. As you hand it over, the weight of the task finally leaves your shoulders, replaced by a mounting, restless energy. You have fulfilled your end of the bargain, and the emptiness of your coin pouch is a stinging reminder of how much further you have to go to truly be free.

**Halden** takes the book with both hands, his fingers tracing the raised wax of the seal with a reverent touch. He looks from the book to you, a small, knowing smile tugging at the corners of his mouth. "You made it, then," he says softly, his voice cutting through the quiet of the inn. He leans in closer, his tone dropping to a conspiratorial whisper. "Since you've gone through such trouble to reach me, perhaps there's another bit of business that requires a runner of your... particular persistence."
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `halden` | **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Crossed Keys Inn** — A warm, smoky common room smelling of roasted mutton and spilled ale, lit by a dying hearth and flickering candlelight.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads
None currently. Generate actions that could introduce new story directions or explore the environment.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your long-standing debt to Caron has finally been settled in full.
- Halden has entrusted you with a wax-sealed ledger to be delivered to Edda at the Crossed Keys Inn.
- Rumors persist of hired thugs guarding the entrance to the Crossed Keys Inn.
- You have arrived in Marrow's Crossing, battered from your journey.
- You successfully bribed Bald Tough and Scarred Tough with 200 credits, clearing your path to the Crossed Keys Inn.

_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## last turn's context (T6)
You reach into your pouch and pull out the **Credits**, the metal clinking with a heavy, decisive sound as you drop them onto the dirt between your boots and theirs. The coins spill across the gravel, catching the pale moonlight like fallen stars. "Caron's coin is paid," you say, your voice steady despite the sharp pull of your ribs. "You've got your business. Move aside."

**Bald Tough** stares down at the pile of coin, his eyes widening slightly as the greed of the sight battles with his professional posturing. He looks from the money up to your face, a flicker of calculation crossing his features. He nudges one of the coins with the toe of a heavy boot, testing to see if it's a trick, before a slow, lopsided grin splits his face. He gestures for **Scarred Tough** to step back, though the smaller man remains tensed, his hand hovering near a heavy club at his hip.

"Well now," **Bald Tough** rumbles, his gravelly voice losing its edge of menace and replacing it with a tone of begrudging respect. He reaches down, scooping up a handful of the metal with a practiced, quick motion. "Seems our client's business just got a lot more interesting. Move on then, runner. We've got our fee, and we've got no more use for a man who's clearly had a long day."

**Scarred Tough** doesn't look quite as satisfied; he lingers for a second longer, his eyes darting toward the heavy **Ledger** tucked under your arm, clearly weighing the value of the book against the coin on the ground. He spits a glob of dark phlegm onto the path near your feet, a final, parting insult, before stepping back to clear the doorway of the *Crossed Keys*, leaving the path to the inn wide and unobstructed.

## player_intent
**negotiate**: The player hands over the merchant seal and ledger to Halden to complete the transaction.

## CURRENT TURN 7 NARRATION
You push past the two thugs, your boots crunching on the gravel of the *Crossed Keys* porch before you duck under the low lintel of the door. Inside, the air is thick with the scent of roasted mutton, spilled ale, and the comforting, smoky warmth of a dying hearth. The common room is mostly empty, the shadows stretching long across the floorboards, but you find your target near a corner booth where a single candle flickers low.

**Halden** looks up as you approach, his eyes widening slightly when he sees your disheveled state and the way you lean heavily against the wooden table. He doesn't comment on your bruised appearance, though a flicker of sympathy crosses his weathered face. He pulls out a stool for you, the wood scraping harshly against the floor, and gestures for you to sit.

You reach into your coat, your fingers brushing against the heavy, wax-sealed **Ledger**, and slide it across the scarred tabletop toward him. As you hand it over, the weight of the task finally leaves your shoulders, replaced by a mounting, restless energy. You have fulfilled your end of the bargain, and the emptiness of your coin pouch is a stinging reminder of how much further you have to go to truly be free.

**Halden** takes the book with both hands, his fingers tracing the raised wax of the seal with a reverent touch. He looks from the book to you, a small, knowing smile tugging at the corners of his mouth. "You made it, then," he says softly, his voice cutting through the quiet of the inn. He leans in closer, his tone dropping to a conspiratorial whisper. "Since you've gone through such trouble to reach me, perhaps there's another bit of business that requires a runner of your... particular persistence."
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player hands over the merchant seal and ledger to Halden to complete the transaction.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "check": {
    "required": false
  }
}
```

### Narration

You push past the two thugs, your boots crunching on the gravel of the *Crossed Keys* porch before you duck under the low lintel of the door. Inside, the air is thick with the scent of roasted mutton, spilled ale, and the comforting, smoky warmth of a dying hearth. The common room is mostly empty, the shadows stretching long across the floorboards, but you find your target near a corner booth where a single candle flickers low.

**Halden** looks up as you approach, his eyes widening slightly when he sees your disheveled state and the way you lean heavily against the wooden table. He doesn't comment on your bruised appearance, though a flicker of sympathy crosses his weathered face. He pulls out a stool for you, the wood scraping harshly against the floor, and gestures for you to sit.

You reach into your coat, your fingers brushing against the heavy, wax-sealed **Ledger**, and slide it across the scarred tabletop toward him. As you hand it over, the weight of the task finally leaves your shoulders, replaced by a mounting, restless energy. You have fulfilled your end of the bargain, and the emptiness of your coin pouch is a stinging reminder of how much further you have to go to truly be free.

**Halden** takes the book with both hands, his fingers tracing the raised wax of the seal with a reverent touch. He looks from the book to you, a small, knowing smile tugging at the corners of his mouth. "You made it, then," he says softly, his voice cutting through the quiet of the inn. He leans in closer, his tone dropping to a conspiratorial whisper. "Since you've gone through such trouble to reach me, perhaps there's another bit of business that requires a runner of your... particular persistence."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "discovery"
  ],
  "scene_tagline": "A New Proposition",
  "location_change": {
    "id": "crossed_keys_inn",
    "name": "Crossed Keys Inn",
    "description": "A warm, smoky common room smelling of roasted mutton and spilled ale, lit by a dying hearth and flickering candlelight."
  },
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a"
    },
    {
      "id": "tough_b"
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Sympathetic toward the player's injuries; offering a new, secretive business opportunity."
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "ledger"
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "halden_new_offer",
      "text": "Halden has approached you with a potential new job offer now that the ledger has been delivered.",
      "turn": 7
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Ask Halden for details about the new business opportunity.",
    "Inquire if the new job pays better than the ledger delivery.",
    "Ask Halden if he knows anything about the thugs outside.",
    "Order a warm meal and ale to soothe your aching ribs."
  ],
  "outcome_summary": "You successfully deliver the wax-sealed ledger to Halden, completing your primary obligation, and he immediately hints at a new task.",
  "thread_advance": [
    "halden_ledger_delivery"
  ],
  "thread_resolve": [
    {
      "id": "halden_ledger_delivery",
      "resolution_state": "resolved"
    }
  ],
  "thread_add": {
    "id": "halden_new_contract",
    "summary": "Halden has a new, potentially more lucrative or dangerous job for a persistent runner.",
    "scope": "arc",
    "active": true,
    "urgency": "normal",
    "tags": [
      "halden",
      "job_offer"
    ],
    "progress": 0,
    "promotes": []
  }
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1763t trimmed=False
- narrate: est=6254t trimmed=False
- extract.scene: est=4254t trimmed=False attempts=1
- extract.state: est=4455t trimmed=False attempts=1
- extract.storytell: est=5429t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 8

**Input:** `I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: Crossed Keys Inn
## Present NPCs (in scene right now)
- Halden (Merchant) — Sympathetic toward the player's injuries; offering a new, secretive business opportunity.

## Inventory
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)

## Last Turn Outcome
You successfully deliver the wax-sealed ledger to Halden, completing your primary obligation, and he immediately hints at a new task.

## Current Turn: 8
=== PLAYER INPUT ===
I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
Crossed Keys Inn (crossed_keys_inn)
A warm, smoky common room smelling of roasted mutton and spilled ale, lit by a dying hearth and flickering candlelight.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.




## Characters
Before introducing a new named NPC, check this list first.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Sympathetic toward the player's injuries; offering a new, secretive business opportunity.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Met with Caron at the tavern to address the long-standing debt.
- [T2] Paid Caron 500 credits, successfully clearing the debt from his ledger.
- [T3] Contracted by Halden to deliver a wax-sealed ledger to Edda at the Crossed Keys Inn for 200 credits.
## Recent Turns

**T5:** You lurch toward the entrance of the *Crossed Keys*, your hand instinctively hovering near the **Iron dagger** at your belt as you approach the two men blocking the threshold. **Bald Tough** and **Scarred Tough** stand like twin pillars of ill intent, their shadows stretching long and jagged across the dirt path under the moonlight. They look up as you approach, their expressions shifting from idle boredom to a shared, predatory amusement.

"What are we doing?" **Bald Tough** asks, a low, gravelly chuckle vibrating in his chest. He doesn't move an inch to let you pass, instead crossing his thick arms over his chest, his biceps straining against the fabric of his jerkin. He looks you up and down, his gaze lingering on your labored breathing and the way you favor your left side. "We're just waiting for a delivery, runner. A very specific, very important delivery."

**Scarred Tough** steps slightly to the side, pivoting to flank you, cutting off your easy path back toward the road. He licks his lips, a thin, unpleasant grin spreading across his face, revealing a chipped front tooth. He doesn't look like he's looking for a conversation; he looks like he's looking for an opening. "You're a persistent one, aren't you? Most folks see us and find a different road to walk."

"Look," **Bald Tough** says, leaning forward so the moonlight catches the dull sheen of sweat on his forehead, "we aren't here to cause a fuss with a man who looks like he's held together by spit and prayer. We're here on business for a client. Move along, and maybe we won't have to make your night any more difficult than it already is." He gestures vaguely toward the inn, a silent warning that your presence is an unwanted interruption to their vigil.


**T6:** You reach into your pouch and pull out the **Credits**, the metal clinking with a heavy, decisive sound as you drop them onto the dirt between your boots and theirs. The coins spill across the gravel, catching the pale moonlight like fallen stars. "Caron's coin is paid," you say, your voice steady despite the sharp pull of your ribs. "You've got your business. Move aside."

**Bald Tough** stares down at the pile of coin, his eyes widening slightly as the greed of the sight battles with his professional posturing. He looks from the money up to your face, a flicker of calculation crossing his features. He nudges one of the coins with the toe of a heavy boot, testing to see if it's a trick, before a slow, lopsided grin splits his face. He gestures for **Scarred Tough** to step back, though the smaller man remains tensed, his hand hovering near a heavy club at his hip.

"Well now," **Bald Tough** rumbles, his gravelly voice losing its edge of menace and replacing it with a tone of begrudging respect. He reaches down, scooping up a handful of the metal with a practiced, quick motion. "Seems our client's business just got a lot more interesting. Move on then, runner. We've got our fee, and we've got no more use for a man who's clearly had a long day."

**Scarred Tough** doesn't look quite as satisfied; he lingers for a second longer, his eyes darting toward the heavy **Ledger** tucked under your arm, clearly weighing the value of the book against the coin on the ground. He spits a glob of dark phlegm onto the path near your feet, a final, parting insult, before stepping back to clear the doorway of the *Crossed Keys*, leaving the path to the inn wide and unobstructed.


**T7:** You push past the two thugs, your boots crunching on the gravel of the *Crossed Keys* porch before you duck under the low lintel of the door. Inside, the air is thick with the scent of roasted mutton, spilled ale, and the comforting, smoky warmth of a dying hearth. The common room is mostly empty, the shadows stretching long across the floorboards, but you find your target near a corner booth where a single candle flickers low.

**Halden** looks up as you approach, his eyes widening slightly when he sees your disheveled state and the way you lean heavily against the wooden table. He doesn't comment on your bruised appearance, though a flicker of sympathy crosses his weathered face. He pulls out a stool for you, the wood scraping harshly against the floor, and gestures for you to sit.

You reach into your coat, your fingers brushing against the heavy, wax-sealed **Ledger**, and slide it across the scarred tabletop toward him. As you hand it over, the weight of the task finally leaves your shoulders, replaced by a mounting, restless energy. You have fulfilled your end of the bargain, and the emptiness of your coin pouch is a stinging reminder of how much further you have to go to truly be free.

**Halden** takes the book with both hands, his fingers tracing the raised wax of the seal with a reverent touch. He looks from the book to you, a small, knowing smile tugging at the corners of his mouth. "You made it, then," he says softly, his voice cutting through the quiet of the inn. He leans in closer, his tone dropping to a conspiratorial whisper. "Since you've gone through such trouble to reach me, perhaps there's another bit of business that requires a runner of your... particular persistence."

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 8) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
=== END PLAYER INPUT ===


```

### Extract Scene User Prompt
```
## location
`crossed_keys_inn` | Crossed Keys Inn
A warm, smoky common room smelling of roasted mutton and spilled ale, lit by a dying hearth and flickering candlelight.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | **Halden** (Merchant) — Sympathetic toward the player's injuries; offering a new, secretive business opportunity.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T7 context)
You push past the two thugs, your boots crunching on the gravel of the *Crossed Keys* porch before you duck under the low lintel of the door. Inside, the air is thick with the scent of roasted mutton, spilled ale, and the comforting, smoky warmth of a dying hearth. The common room is mostly empty, the shadows stretching long across the floorboards, but you find your target near a corner booth where a single candle flickers low.

**Halden** looks up as you approach, his eyes widening slightly when he sees your disheveled state and the way you lean heavily against the wooden table. He doesn't comment on your bruised appearance, though a flicker of sympathy crosses his weathered face. He pulls out a stool for you, the wood scraping harshly against the floor, and gestures for you to sit.

You reach into your coat, your fingers brushing against the heavy, wax-sealed **Ledger**, and slide it across the scarred tabletop toward him. As you hand it over, the weight of the task finally leaves your shoulders, replaced by a mounting, restless energy. You have fulfilled your end of the bargain, and the emptiness of your coin pouch is a stinging reminder of how much further you have to go to truly be free.

**Halden** takes the book with both hands, his fingers tracing the raised wax of the seal with a reverent touch. He looks from the book to you, a small, knowing smile tugging at the corners of his mouth. "You made it, then," he says softly, his voice cutting through the quiet of the inn. He leans in closer, his tone dropping to a conspiratorial whisper. "Since you've gone through such trouble to reach me, perhaps there's another bit of business that requires a runner of your... particular persistence."

## CURRENT TURN 8 NARRATION
You reach into your pocket, your fingers curling around the small, cold weight of the **Brass key**. You slide it from your coat, the metal glinting dully in the amber light of the dying hearth. With a determined stride, you turn away from the booth and head back toward the entrance, your ribs protesting the sudden movement with a sharp, stinging reminder of your earlier encounter.

You reach the heavy timber of the front door and slide the key into the iron-bound lock. It fits with a satisfying, mechanical click, but when you twist, the mechanism resists, grinding stubbornly against grit or an improperly aligned bolt. The door remains stubbornly shut, the heavy wood unyielding to your efforts.

**Halden** watches your attempt from across the room, a faint, amused huff escaping his nose as he leans back against the table. He doesn't move to assist, instead tapping a rhythmic beat on the wood with a thick finger. "That's for a very specific lock, runner," he calls out, his voice carrying easily through the quiet common room. "Not for the front door of an establishment that's been standing longer than your family tree. If you're looking for a place to hide or a quiet corner to nurse those bruises, **Edda** keeps a larder through the kitchen that's much more private."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
sneak: The player attempts to use the brass key to unlock the inn's front door or a potential back room.
## CURRENT TURN 8 NARRATION
You reach into your pocket, your fingers curling around the small, cold weight of the **Brass key**. You slide it from your coat, the metal glinting dully in the amber light of the dying hearth. With a determined stride, you turn away from the booth and head back toward the entrance, your ribs protesting the sudden movement with a sharp, stinging reminder of your earlier encounter.

You reach the heavy timber of the front door and slide the key into the iron-bound lock. It fits with a satisfying, mechanical click, but when you twist, the mechanism resists, grinding stubbornly against grit or an improperly aligned bolt. The door remains stubbornly shut, the heavy wood unyielding to your efforts.

**Halden** watches your attempt from across the room, a faint, amused huff escaping his nose as he leans back against the table. He doesn't move to assist, instead tapping a rhythmic beat on the wood with a thick finger. "That's for a very specific lock, runner," he calls out, his voice carrying easily through the quiet common room. "Not for the front door of an establishment that's been standing longer than your family tree. If you're looking for a place to hide or a quiet corner to nurse those bruises, **Edda** keeps a larder through the kitchen that's much more private."
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `halden` | **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Crossed Keys Inn** — The heavy timber front door resists the brass key, the iron-bound lock grinding stubbornly against grit or misalignment.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads (all — unified list, scope handled by Python)
- `halden_new_contract` [ARC]  [NORMAL] Halden has a new, potentially more lucrative or dangerous job for a persistent runner. tags: halden, job_offer (last seen T7)

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your long-standing debt to Caron has finally been settled in full.
- Halden has entrusted you with a wax-sealed ledger to be delivered to Edda at the Crossed Keys Inn.
- Rumors persist of hired thugs guarding the entrance to the Crossed Keys Inn.
- You have arrived in Marrow's Crossing, battered from your journey.
- You successfully bribed Bald Tough and Scarred Tough with 200 credits, clearing your path to the Crossed Keys Inn.
- Halden has approached you with a potential new job offer now that the ledger has been delivered.

## pacing_context
Directive: none
Gate: allow

## last turn's context (T7)
You push past the two thugs, your boots crunching on the gravel of the *Crossed Keys* porch before you duck under the low lintel of the door. Inside, the air is thick with the scent of roasted mutton, spilled ale, and the comforting, smoky warmth of a dying hearth. The common room is mostly empty, the shadows stretching long across the floorboards, but you find your target near a corner booth where a single candle flickers low.

**Halden** looks up as you approach, his eyes widening slightly when he sees your disheveled state and the way you lean heavily against the wooden table. He doesn't comment on your bruised appearance, though a flicker of sympathy crosses his weathered face. He pulls out a stool for you, the wood scraping harshly against the floor, and gestures for you to sit.

You reach into your coat, your fingers brushing against the heavy, wax-sealed **Ledger**, and slide it across the scarred tabletop toward him. As you hand it over, the weight of the task finally leaves your shoulders, replaced by a mounting, restless energy. You have fulfilled your end of the bargain, and the emptiness of your coin pouch is a stinging reminder of how much further you have to go to truly be free.

**Halden** takes the book with both hands, his fingers tracing the raised wax of the seal with a reverent touch. He looks from the book to you, a small, knowing smile tugging at the corners of his mouth. "You made it, then," he says softly, his voice cutting through the quiet of the inn. He leans in closer, his tone dropping to a conspiratorial whisper. "Since you've gone through such trouble to reach me, perhaps there's another bit of business that requires a runner of your... particular persistence."

## player_intent
**sneak**: The player attempts to use the brass key to unlock the inn's front door or a potential back room.

## CURRENT TURN 8 NARRATION
You reach into your pocket, your fingers curling around the small, cold weight of the **Brass key**. You slide it from your coat, the metal glinting dully in the amber light of the dying hearth. With a determined stride, you turn away from the booth and head back toward the entrance, your ribs protesting the sudden movement with a sharp, stinging reminder of your earlier encounter.

You reach the heavy timber of the front door and slide the key into the iron-bound lock. It fits with a satisfying, mechanical click, but when you twist, the mechanism resists, grinding stubbornly against grit or an improperly aligned bolt. The door remains stubbornly shut, the heavy wood unyielding to your efforts.

**Halden** watches your attempt from across the room, a faint, amused huff escaping his nose as he leans back against the table. He doesn't move to assist, instead tapping a rhythmic beat on the wood with a thick finger. "That's for a very specific lock, runner," he calls out, his voice carrying easily through the quiet common room. "Not for the front door of an establishment that's been standing longer than your family tree. If you're looking for a place to hide or a quiet corner to nurse those bruises, **Edda** keeps a larder through the kitchen that's much more private."
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use the brass key to unlock the inn's front door or a potential back room.",
  "intent_verb": "sneak",
  "target": "inn's front door",
  "check": {
    "required": false
  }
}
```

### Narration

You reach into your pocket, your fingers curling around the small, cold weight of the **Brass key**. You slide it from your coat, the metal glinting dully in the amber light of the dying hearth. With a determined stride, you turn away from the booth and head back toward the entrance, your ribs protesting the sudden movement with a sharp, stinging reminder of your earlier encounter.

You reach the heavy timber of the front door and slide the key into the iron-bound lock. It fits with a satisfying, mechanical click, but when you twist, the mechanism resists, grinding stubbornly against grit or an improperly aligned bolt. The door remains stubbornly shut, the heavy wood unyielding to your efforts.

**Halden** watches your attempt from across the room, a faint, amused huff escaping his nose as he leans back against the table. He doesn't move to assist, instead tapping a rhythmic beat on the wood with a thick finger. "That's for a very specific lock, runner," he calls out, his voice carrying easily through the quiet common room. "Not for the front door of an establishment that's been standing longer than your family tree. If you're looking for a place to hide or a quiet corner to nurse those bruises, **Edda** keeps a larder through the kitchen that's much more private."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "discovery"
  ],
  "scene_tagline": "A Stubborn Lock",
  "location_description": "The heavy timber front door resists the brass key, the iron-bound lock grinding stubbornly against grit or misalignment.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Watching the player's struggle with amusement; offering a suggestion of a more private place to recover."
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "halden_new_job_hint",
      "text": "Halden hints at a new job opportunity following the ledger delivery.",
      "turn": 8
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Ask Halden for more details about the new job.",
    "Follow Halden's advice and seek Edda in the larder.",
    "Try to find another way to use the brass key.",
    "Ignore Halden and search the common room for information."
  ],
  "outcome_summary": "The brass key fails to unlock the main door, and Halden informs you it belongs to a different, more specific lock.",
  "gm_beat": {
    "type": "opportunity",
    "surface_as": "npc_behavior"
  },
  "thread_advance": [
    "halden_new_contract"
  ],
  "thread_resolve": []
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1728t trimmed=False
- narrate: est=6230t trimmed=False
- extract.scene: est=4100t trimmed=False attempts=1
- extract.state: est=4310t trimmed=False attempts=1
- extract.storytell: est=5252t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 9

**Input:** `I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: Crossed Keys Inn
## Present NPCs (in scene right now)
- Halden (Merchant) — Watching the player's struggle with amusement; offering a suggestion of a more private place to recover.

## Inventory
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)

## Last Turn Outcome
The brass key fails to unlock the main door, and Halden informs you it belongs to a different, more specific lock.

## Current Turn: 9
=== PLAYER INPUT ===
I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
Crossed Keys Inn (crossed_keys_inn)
The heavy timber front door resists the brass key, the iron-bound lock grinding stubbornly against grit or misalignment.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.




## Characters
Before introducing a new named NPC, check this list first.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Watching the player's struggle with amusement; offering a suggestion of a more private place to recover.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Met with Caron at the tavern to address the long-standing debt.
- [T2] Paid Caron 500 credits, successfully clearing the debt from his ledger.
- [T3] Contracted by Halden to deliver a wax-sealed ledger to Edda at the Crossed Keys Inn for 200 credits.
## Recent Turns

**T6:** You reach into your pouch and pull out the **Credits**, the metal clinking with a heavy, decisive sound as you drop them onto the dirt between your boots and theirs. The coins spill across the gravel, catching the pale moonlight like fallen stars. "Caron's coin is paid," you say, your voice steady despite the sharp pull of your ribs. "You've got your business. Move aside."

**Bald Tough** stares down at the pile of coin, his eyes widening slightly as the greed of the sight battles with his professional posturing. He looks from the money up to your face, a flicker of calculation crossing his features. He nudges one of the coins with the toe of a heavy boot, testing to see if it's a trick, before a slow, lopsided grin splits his face. He gestures for **Scarred Tough** to step back, though the smaller man remains tensed, his hand hovering near a heavy club at his hip.

"Well now," **Bald Tough** rumbles, his gravelly voice losing its edge of menace and replacing it with a tone of begrudging respect. He reaches down, scooping up a handful of the metal with a practiced, quick motion. "Seems our client's business just got a lot more interesting. Move on then, runner. We've got our fee, and we've got no more use for a man who's clearly had a long day."

**Scarred Tough** doesn't look quite as satisfied; he lingers for a second longer, his eyes darting toward the heavy **Ledger** tucked under your arm, clearly weighing the value of the book against the coin on the ground. He spits a glob of dark phlegm onto the path near your feet, a final, parting insult, before stepping back to clear the doorway of the *Crossed Keys*, leaving the path to the inn wide and unobstructed.


**T7:** You push past the two thugs, your boots crunching on the gravel of the *Crossed Keys* porch before you duck under the low lintel of the door. Inside, the air is thick with the scent of roasted mutton, spilled ale, and the comforting, smoky warmth of a dying hearth. The common room is mostly empty, the shadows stretching long across the floorboards, but you find your target near a corner booth where a single candle flickers low.

**Halden** looks up as you approach, his eyes widening slightly when he sees your disheveled state and the way you lean heavily against the wooden table. He doesn't comment on your bruised appearance, though a flicker of sympathy crosses his weathered face. He pulls out a stool for you, the wood scraping harshly against the floor, and gestures for you to sit.

You reach into your coat, your fingers brushing against the heavy, wax-sealed **Ledger**, and slide it across the scarred tabletop toward him. As you hand it over, the weight of the task finally leaves your shoulders, replaced by a mounting, restless energy. You have fulfilled your end of the bargain, and the emptiness of your coin pouch is a stinging reminder of how much further you have to go to truly be free.

**Halden** takes the book with both hands, his fingers tracing the raised wax of the seal with a reverent touch. He looks from the book to you, a small, knowing smile tugging at the corners of his mouth. "You made it, then," he says softly, his voice cutting through the quiet of the inn. He leans in closer, his tone dropping to a conspiratorial whisper. "Since you've gone through such trouble to reach me, perhaps there's another bit of business that requires a runner of your... particular persistence."


**T8:** You reach into your pocket, your fingers curling around the small, cold weight of the **Brass key**. You slide it from your coat, the metal glinting dully in the amber light of the dying hearth. With a determined stride, you turn away from the booth and head back toward the entrance, your ribs protesting the sudden movement with a sharp, stinging reminder of your earlier encounter.

You reach the heavy timber of the front door and slide the key into the iron-bound lock. It fits with a satisfying, mechanical click, but when you twist, the mechanism resists, grinding stubbornly against grit or an improperly aligned bolt. The door remains stubbornly shut, the heavy wood unyielding to your efforts.

**Halden** watches your attempt from across the room, a faint, amused huff escaping his nose as he leans back against the table. He doesn't move to assist, instead tapping a rhythmic beat on the wood with a thick finger. "That's for a very specific lock, runner," he calls out, his voice carrying easily through the quiet common room. "Not for the front door of an establishment that's been standing longer than your family tree. If you're looking for a place to hide or a quiet corner to nurse those bruises, **Edda** keeps a larder through the kitchen that's much more private."

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 9) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
=== END PLAYER INPUT ===

**Beat:** OPPORTUNITY — surface as `npc_behavior`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
```

### Extract Scene User Prompt
```
## location
`crossed_keys_inn` | Crossed Keys Inn
The heavy timber front door resists the brass key, the iron-bound lock grinding stubbornly against grit or misalignment.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | **Halden** (Merchant) — Watching the player's struggle with amusement; offering a suggestion of a more private place to recover.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T8 context)
You reach into your pocket, your fingers curling around the small, cold weight of the **Brass key**. You slide it from your coat, the metal glinting dully in the amber light of the dying hearth. With a determined stride, you turn away from the booth and head back toward the entrance, your ribs protesting the sudden movement with a sharp, stinging reminder of your earlier encounter.

You reach the heavy timber of the front door and slide the key into the iron-bound lock. It fits with a satisfying, mechanical click, but when you twist, the mechanism resists, grinding stubbornly against grit or an improperly aligned bolt. The door remains stubbornly shut, the heavy wood unyielding to your efforts.

**Halden** watches your attempt from across the room, a faint, amused huff escaping his nose as he leans back against the table. He doesn't move to assist, instead tapping a rhythmic beat on the wood with a thick finger. "That's for a very specific lock, runner," he calls out, his voice carrying easily through the quiet common room. "Not for the front door of an establishment that's been standing longer than your family tree. If you're looking for a place to hide or a quiet corner to nurse those bruises, **Edda** keeps a larder through the kitchen that's much more private."

## CURRENT TURN 9 NARRATION
You lean your weight against the cold, uneven stone of the inn's exterior, pressing your ear to the masonry to listen for any sign of life behind the thick walls. "I have credits," you whisper toward the cracks in the stone, your voice a desperate, low murmur. "Open up." With a flick of your wrist, you toss a single iron coin toward the foundation, watching it bounce uselessly against the rock with a lonely, metallic ring.

The stone offers no reply, and the silence of the night settles heavily around you, broken only by the distant, rhythmic tapping of **Halden**'s finger from inside the common room. The coin settles into the dirt, a small, insignificant sacrifice to an unfeeling wall.

A heavy latch thuds from the other side of the door, followed by the sound of a wooden bolt being drawn back. The door doesn't swing wide, but it creaks open just a few inches, revealing a sliver of warm, amber light and the sharp, inquisitive eyes of **Edda**. She is a woman of middle years with hair pulled back in a severe, practical knot, her face etched with the weary lines of someone who has spent a lifetime managing both people and problems.

"Credits won't make the stone listen, boy," **Edda** says, her voice a dry, no-nonsense rasp that cuts through the chill of the night. She glances down at the solitary coin glinting in the mud, then up at your bruised, weary face. She nudges the door open a little further, her gaze shifting pointedly toward the shadows where the two thugs had stood moments ago. "If you're looking to bribe the wind, you're wasting your breath. But if you're looking for a bowl of stew and a door that actually stays shut, stop talking to the masonry and get inside before the frost bites harder than those men did."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
deceive: The player attempts to bribe the inn's door or wall to gain entry.
## CURRENT TURN 9 NARRATION
You lean your weight against the cold, uneven stone of the inn's exterior, pressing your ear to the masonry to listen for any sign of life behind the thick walls. "I have credits," you whisper toward the cracks in the stone, your voice a desperate, low murmur. "Open up." With a flick of your wrist, you toss a single iron coin toward the foundation, watching it bounce uselessly against the rock with a lonely, metallic ring.

The stone offers no reply, and the silence of the night settles heavily around you, broken only by the distant, rhythmic tapping of **Halden**'s finger from inside the common room. The coin settles into the dirt, a small, insignificant sacrifice to an unfeeling wall.

A heavy latch thuds from the other side of the door, followed by the sound of a wooden bolt being drawn back. The door doesn't swing wide, but it creaks open just a few inches, revealing a sliver of warm, amber light and the sharp, inquisitive eyes of **Edda**. She is a woman of middle years with hair pulled back in a severe, practical knot, her face etched with the weary lines of someone who has spent a lifetime managing both people and problems.

"Credits won't make the stone listen, boy," **Edda** says, her voice a dry, no-nonsense rasp that cuts through the chill of the night. She glances down at the solitary coin glinting in the mud, then up at your bruised, weary face. She nudges the door open a little further, her gaze shifting pointedly toward the shadows where the two thugs had stood moments ago. "If you're looking to bribe the wind, you're wasting your breath. But if you're looking for a bowl of stew and a door that actually stays shut, stop talking to the masonry and get inside before the frost bites harder than those men did."
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `innkeeper` | **Edda** (Innkeeper) [PRESENT] — A woman of middle years with hair pulled back in a severe, practical knot, possessing a dry, no-nonsense demeanor.
- `halden` | **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Crossed Keys Inn** — The exterior of the inn features cold, uneven stone masonry and a heavy timber door that opens to reveal a sliver of warm, amber light from within.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads (all — unified list, scope handled by Python)
- `halden_new_contract` [ARC]  [NORMAL] Halden has a new, potentially more lucrative or dangerous job for a persistent runner. tags: halden, job_offer (last seen T8)

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your long-standing debt to Caron has finally been settled in full.
- Halden has entrusted you with a wax-sealed ledger to be delivered to Edda at the Crossed Keys Inn.
- Rumors persist of hired thugs guarding the entrance to the Crossed Keys Inn.
- You have arrived in Marrow's Crossing, battered from your journey.
- You successfully bribed Bald Tough and Scarred Tough with 200 credits, clearing your path to the Crossed Keys Inn.
- Halden has approached you with a potential new job offer now that the ledger has been delivered.
- Halden hints at a new job opportunity following the ledger delivery.

## pacing_context
Directive: none
Gate: allow

## last turn's context (T8)
You reach into your pocket, your fingers curling around the small, cold weight of the **Brass key**. You slide it from your coat, the metal glinting dully in the amber light of the dying hearth. With a determined stride, you turn away from the booth and head back toward the entrance, your ribs protesting the sudden movement with a sharp, stinging reminder of your earlier encounter.

You reach the heavy timber of the front door and slide the key into the iron-bound lock. It fits with a satisfying, mechanical click, but when you twist, the mechanism resists, grinding stubbornly against grit or an improperly aligned bolt. The door remains stubbornly shut, the heavy wood unyielding to your efforts.

**Halden** watches your attempt from across the room, a faint, amused huff escaping his nose as he leans back against the table. He doesn't move to assist, instead tapping a rhythmic beat on the wood with a thick finger. "That's for a very specific lock, runner," he calls out, his voice carrying easily through the quiet common room. "Not for the front door of an establishment that's been standing longer than your family tree. If you're looking for a place to hide or a quiet corner to nurse those bruises, **Edda** keeps a larder through the kitchen that's much more private."

## player_intent
**deceive**: The player attempts to bribe the inn's door or wall to gain entry.

## CURRENT TURN 9 NARRATION
You lean your weight against the cold, uneven stone of the inn's exterior, pressing your ear to the masonry to listen for any sign of life behind the thick walls. "I have credits," you whisper toward the cracks in the stone, your voice a desperate, low murmur. "Open up." With a flick of your wrist, you toss a single iron coin toward the foundation, watching it bounce uselessly against the rock with a lonely, metallic ring.

The stone offers no reply, and the silence of the night settles heavily around you, broken only by the distant, rhythmic tapping of **Halden**'s finger from inside the common room. The coin settles into the dirt, a small, insignificant sacrifice to an unfeeling wall.

A heavy latch thuds from the other side of the door, followed by the sound of a wooden bolt being drawn back. The door doesn't swing wide, but it creaks open just a few inches, revealing a sliver of warm, amber light and the sharp, inquisitive eyes of **Edda**. She is a woman of middle years with hair pulled back in a severe, practical knot, her face etched with the weary lines of someone who has spent a lifetime managing both people and problems.

"Credits won't make the stone listen, boy," **Edda** says, her voice a dry, no-nonsense rasp that cuts through the chill of the night. She glances down at the solitary coin glinting in the mud, then up at your bruised, weary face. She nudges the door open a little further, her gaze shifting pointedly toward the shadows where the two thugs had stood moments ago. "If you're looking to bribe the wind, you're wasting your breath. But if you're looking for a bowl of stew and a door that actually stays shut, stop talking to the masonry and get inside before the frost bites harder than those men did."
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the inn's door or wall to gain entry.",
  "intent_verb": "deceive",
  "target": "the inn's door",
  "check": {
    "required": false
  }
}
```

### Narration

You lean your weight against the cold, uneven stone of the inn's exterior, pressing your ear to the masonry to listen for any sign of life behind the thick walls. "I have credits," you whisper toward the cracks in the stone, your voice a desperate, low murmur. "Open up." With a flick of your wrist, you toss a single iron coin toward the foundation, watching it bounce uselessly against the rock with a lonely, metallic ring.

The stone offers no reply, and the silence of the night settles heavily around you, broken only by the distant, rhythmic tapping of **Halden**'s finger from inside the common room. The coin settles into the dirt, a small, insignificant sacrifice to an unfeeling wall.

A heavy latch thuds from the other side of the door, followed by the sound of a wooden bolt being drawn back. The door doesn't swing wide, but it creaks open just a few inches, revealing a sliver of warm, amber light and the sharp, inquisitive eyes of **Edda**. She is a woman of middle years with hair pulled back in a severe, practical knot, her face etched with the weary lines of someone who has spent a lifetime managing both people and problems.

"Credits won't make the stone listen, boy," **Edda** says, her voice a dry, no-nonsense rasp that cuts through the chill of the night. She glances down at the solitary coin glinting in the mud, then up at your bruised, weary face. She nudges the door open a little further, her gaze shifting pointedly toward the shadows where the two thugs had stood moments ago. "If you're looking to bribe the wind, you're wasting your breath. But if you're looking for a bowl of stew and a door that actually stays shut, stop talking to the masonry and get inside before the frost bites harder than those men did."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_interaction",
    "discovery"
  ],
  "scene_tagline": "A Sliver of Light",
  "location_description": "The exterior of the inn features cold, uneven stone masonry and a heavy timber door that opens to reveal a sliver of warm, amber light from within.",
  "npc_add": [
    {
      "id": "edd_innkeeper",
      "notes": "Observant and no-nonsense; she is wary of the player's bruised state and the presence of thugs.",
      "name": "Edda",
      "title": "Innkeeper",
      "bio": "A woman of middle years with hair pulled back in a severe, practical knot, possessing a dry, no-nonsense demeanor."
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Watching from inside the common room, his rhythmic tapping continues to be heard from behind the door."
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "edd_entry_granted",
      "text": "Edda has opened the door of the Crossed Keys Inn, allowing you entry after your failed attempt to bribe the stone.",
      "turn": 9
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Step inside and thank Edda for the hospitality.",
    "Ask Edda if there is a quiet room available.",
    "Mention the ledger and ask for Edda's business.",
    "Keep your head low and head straight for the stew."
  ],
  "outcome_summary": "Your attempt to bribe the wall fails, but Edda opens the door and invites you inside for food and shelter.",
  "gm_beat": {
    "type": "opportunity",
    "surface_as": "npc_behavior"
  },
  "thread_advance": [],
  "thread_resolve": []
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1730t trimmed=False
- narrate: est=6151t trimmed=False
- extract.scene: est=4113t trimmed=False attempts=1
- extract.state: est=4434t trimmed=False attempts=1
- extract.storytell: est=5282t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 10

**Input:** `I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: Crossed Keys Inn
## Present NPCs (in scene right now)
- Halden (Merchant) — Watching from inside the common room, his rhythmic tapping continues to be heard from behind the door.
- Edda (Innkeeper at the Crossed Keys) — Observant and no-nonsense; she is wary of the player's bruised state and the presence of thugs.

## Inventory
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)

## Last Turn Outcome
Your attempt to bribe the wall fails, but Edda opens the door and invites you inside for food and shelter.

## Current Turn: 10
=== PLAYER INPUT ===
I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
Crossed Keys Inn (crossed_keys_inn)
The exterior of the inn features cold, uneven stone masonry and a heavy timber door that opens to reveal a sliver of warm, amber light from within.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.




## Characters
Before introducing a new named NPC, check this list first.

- **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. Wiping down the bar at the Crossed Keys, which is two streets over. | Observant and no-nonsense; she is wary of the player's bruised state and the presence of thugs.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Watching from inside the common room, his rhythmic tapping continues to be heard from behind the door.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Met with Caron at the tavern to address the long-standing debt.
- [T2] Paid Caron 500 credits, successfully clearing the debt from his ledger.
- [T3] Contracted by Halden to deliver a wax-sealed ledger to Edda at the Crossed Keys Inn for 200 credits.
## Recent Turns

**T7:** You push past the two thugs, your boots crunching on the gravel of the *Crossed Keys* porch before you duck under the low lintel of the door. Inside, the air is thick with the scent of roasted mutton, spilled ale, and the comforting, smoky warmth of a dying hearth. The common room is mostly empty, the shadows stretching long across the floorboards, but you find your target near a corner booth where a single candle flickers low.

**Halden** looks up as you approach, his eyes widening slightly when he sees your disheveled state and the way you lean heavily against the wooden table. He doesn't comment on your bruised appearance, though a flicker of sympathy crosses his weathered face. He pulls out a stool for you, the wood scraping harshly against the floor, and gestures for you to sit.

You reach into your coat, your fingers brushing against the heavy, wax-sealed **Ledger**, and slide it across the scarred tabletop toward him. As you hand it over, the weight of the task finally leaves your shoulders, replaced by a mounting, restless energy. You have fulfilled your end of the bargain, and the emptiness of your coin pouch is a stinging reminder of how much further you have to go to truly be free.

**Halden** takes the book with both hands, his fingers tracing the raised wax of the seal with a reverent touch. He looks from the book to you, a small, knowing smile tugging at the corners of his mouth. "You made it, then," he says softly, his voice cutting through the quiet of the inn. He leans in closer, his tone dropping to a conspiratorial whisper. "Since you've gone through such trouble to reach me, perhaps there's another bit of business that requires a runner of your... particular persistence."


**T8:** You reach into your pocket, your fingers curling around the small, cold weight of the **Brass key**. You slide it from your coat, the metal glinting dully in the amber light of the dying hearth. With a determined stride, you turn away from the booth and head back toward the entrance, your ribs protesting the sudden movement with a sharp, stinging reminder of your earlier encounter.

You reach the heavy timber of the front door and slide the key into the iron-bound lock. It fits with a satisfying, mechanical click, but when you twist, the mechanism resists, grinding stubbornly against grit or an improperly aligned bolt. The door remains stubbornly shut, the heavy wood unyielding to your efforts.

**Halden** watches your attempt from across the room, a faint, amused huff escaping his nose as he leans back against the table. He doesn't move to assist, instead tapping a rhythmic beat on the wood with a thick finger. "That's for a very specific lock, runner," he calls out, his voice carrying easily through the quiet common room. "Not for the front door of an establishment that's been standing longer than your family tree. If you're looking for a place to hide or a quiet corner to nurse those bruises, **Edda** keeps a larder through the kitchen that's much more private."


**T9:** You lean your weight against the cold, uneven stone of the inn's exterior, pressing your ear to the masonry to listen for any sign of life behind the thick walls. "I have credits," you whisper toward the cracks in the stone, your voice a desperate, low murmur. "Open up." With a flick of your wrist, you toss a single iron coin toward the foundation, watching it bounce uselessly against the rock with a lonely, metallic ring.

The stone offers no reply, and the silence of the night settles heavily around you, broken only by the distant, rhythmic tapping of **Halden**'s finger from inside the common room. The coin settles into the dirt, a small, insignificant sacrifice to an unfeeling wall.

A heavy latch thuds from the other side of the door, followed by the sound of a wooden bolt being drawn back. The door doesn't swing wide, but it creaks open just a few inches, revealing a sliver of warm, amber light and the sharp, inquisitive eyes of **Edda**. She is a woman of middle years with hair pulled back in a severe, practical knot, her face etched with the weary lines of someone who has spent a lifetime managing both people and problems.

"Credits won't make the stone listen, boy," **Edda** says, her voice a dry, no-nonsense rasp that cuts through the chill of the night. She glances down at the solitary coin glinting in the mud, then up at your bruised, weary face. She nudges the door open a little further, her gaze shifting pointedly toward the shadows where the two thugs had stood moments ago. "If you're looking to bribe the wind, you're wasting your breath. But if you're looking for a bowl of stew and a door that actually stays shut, stop talking to the masonry and get inside before the frost bites harder than those men did."

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 10) Result


**Band:** CRIT SUCCESS → The intimidate succeeds outstandingly. Best possible outcome — something unexpected goes in your favour.


**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.

=== PLAYER INPUT ===
I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
=== END PLAYER INPUT ===

**Beat:** OPPORTUNITY — surface as `npc_behavior`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
```

### Extract Scene User Prompt
```
## location
`crossed_keys_inn` | Crossed Keys Inn
The exterior of the inn features cold, uneven stone masonry and a heavy timber door that opens to reveal a sliver of warm, amber light from within.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | **Halden** (Merchant) — Watching from inside the common room, his rhythmic tapping continues to be heard from behind the door.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Observant and no-nonsense; she is wary of the player's bruised state and the presence of thugs.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T9 context)
You lean your weight against the cold, uneven stone of the inn's exterior, pressing your ear to the masonry to listen for any sign of life behind the thick walls. "I have credits," you whisper toward the cracks in the stone, your voice a desperate, low murmur. "Open up." With a flick of your wrist, you toss a single iron coin toward the foundation, watching it bounce uselessly against the rock with a lonely, metallic ring.

The stone offers no reply, and the silence of the night settles heavily around you, broken only by the distant, rhythmic tapping of **Halden**'s finger from inside the common room. The coin settles into the dirt, a small, insignificant sacrifice to an unfeeling wall.

A heavy latch thuds from the other side of the door, followed by the sound of a wooden bolt being drawn back. The door doesn't swing wide, but it creaks open just a few inches, revealing a sliver of warm, amber light and the sharp, inquisitive eyes of **Edda**. She is a woman of middle years with hair pulled back in a severe, practical knot, her face etched with the weary lines of someone who has spent a lifetime managing both people and problems.

"Credits won't make the stone listen, boy," **Edda** says, her voice a dry, no-nonsense rasp that cuts through the chill of the night. She glances down at the solitary coin glinting in the mud, then up at your bruised, weary face. She nudges the door open a little further, her gaze shifting pointedly toward the shadows where the two thugs had stood moments ago. "If you're looking to bribe the wind, you're wasting your breath. But if you're looking for a bowl of stew and a door that actually stays shut, stop talking to the masonry and get inside before the frost bites harder than those men did."

## CURRENT TURN 10 NARRATION
You lunge across the small gap between the door and the bar, your fingers locking like iron around the wrist of **Matthew Estrada**. He is taller than you, his broad shoulders casting a wide shadow across the amber-lit floorboards, but your grip is sudden and fueled by a desperate, jagged adrenaline. "Who are you?" you hiss, your face inches from his, your eyes burning with a frantic intensity that ignores the sharp throb in your ribs. "Stop watching the room like a soldier on watch and tell me what you're doing here!"

**Matthew Estrada** doesn't flinch or pull away. Instead, he remains unnervingly still, his gaze dropping to your hand on his wrist with a look of detached, professional curiosity. He doesn't reach for a weapon, nor does he attempt to twist free; he simply waits for your grip to tire. When he finally speaks, his voice is a low, steady rumble that sounds more like a command than an answer. "You've got a grip like a cornered rat, runner," he says, his eyes locking onto yours with a piercing, disciplined clarity. "And a habit of picking fights you can't finish."

He doesn't shake you off, but he doesn't yield either. He leans in slightly, the scent of old leather and road dust radiating from his jerkin, and his tone shifts from calm to something much more pointed. "I'm not here for the stew, and I'm certainly not here for the company," he murmurs, his eyes flicking briefly toward the door where the thugs had lingered, then back to you. "I'm waiting for a shipment that doesn't appear on any merchant's ledger. If you want to keep your teeth, I'd suggest you find a corner, eat your meal, and stop pretending you're more than a messenger."

Despite his dismissal, there is an opening in his composure—a momentary lapse where his eyes scan the room behind you, checking the perimeter even as you hold him. He isn't just a traveler; he is a man waiting for a signal, and your outburst has clearly signaled to him that you are a variable he hadn't accounted for. He offers a small, grim twist of his wrist, a silent dare for you to let go or find out exactly what a man of his training is capable of when provoked.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
intimidate: Confront Matthew Estrada to demand his true identity and motives.
## CURRENT TURN 10 NARRATION
You lunge across the small gap between the door and the bar, your fingers locking like iron around the wrist of **Matthew Estrada**. He is taller than you, his broad shoulders casting a wide shadow across the amber-lit floorboards, but your grip is sudden and fueled by a desperate, jagged adrenaline. "Who are you?" you hiss, your face inches from his, your eyes burning with a frantic intensity that ignores the sharp throb in your ribs. "Stop watching the room like a soldier on watch and tell me what you're doing here!"

**Matthew Estrada** doesn't flinch or pull away. Instead, he remains unnervingly still, his gaze dropping to your hand on his wrist with a look of detached, professional curiosity. He doesn't reach for a weapon, nor does he attempt to twist free; he simply waits for your grip to tire. When he finally speaks, his voice is a low, steady rumble that sounds more like a command than an answer. "You've got a grip like a cornered rat, runner," he says, his eyes locking onto yours with a piercing, disciplined clarity. "And a habit of picking fights you can't finish."

He doesn't shake you off, but he doesn't yield either. He leans in slightly, the scent of old leather and road dust radiating from his jerkin, and his tone shifts from calm to something much more pointed. "I'm not here for the stew, and I'm certainly not here for the company," he murmurs, his eyes flicking briefly toward the door where the thugs had lingered, then back to you. "I'm waiting for a shipment that doesn't appear on any merchant's ledger. If you want to keep your teeth, I'd suggest you find a corner, eat your meal, and stop pretending you're more than a messenger."

Despite his dismissal, there is an opening in his composure—a momentary lapse where his eyes scan the room behind you, checking the perimeter even as you hold him. He isn't just a traveler; he is a man waiting for a signal, and your outburst has clearly signaled to him that you are a variable he hadn't accounted for. He offers a small, grim twist of his wrist, a silent dare for you to let go or find out exactly what a man of his training is capable of when provoked.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. Wiping down the bar at the Crossed Keys, which is two streets over.
- `halden` | **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
- `matthew_estrada` | **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Crossed Keys Inn** — The interior is bathed in warm, amber light, featuring wooden floorboards and a bar that separates the common room from the entrance.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads (all — unified list, scope handled by Python)
- `halden_new_contract` [ARC]  [NORMAL] Halden has a new, potentially more lucrative or dangerous job for a persistent runner. tags: halden, job_offer (last seen T8)

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your long-standing debt to Caron has finally been settled in full.
- Halden has entrusted you with a wax-sealed ledger to be delivered to Edda at the Crossed Keys Inn.
- Rumors persist of hired thugs guarding the entrance to the Crossed Keys Inn.
- You have arrived in Marrow's Crossing, battered from your journey.
- You successfully bribed Bald Tough and Scarred Tough with 200 credits, clearing your path to the Crossed Keys Inn.
- Halden has approached you with a potential new job offer now that the ledger has been delivered.
- Halden hints at a new job opportunity following the ledger delivery.
- Edda has opened the door of the Crossed Keys Inn, allowing you entry after your failed attempt to bribe the stone.

## rules_outcome
Band: CRIT_SUCCESS. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.

## pacing_context
Directive: none
Gate: allow

## last turn's context (T9)
You lean your weight against the cold, uneven stone of the inn's exterior, pressing your ear to the masonry to listen for any sign of life behind the thick walls. "I have credits," you whisper toward the cracks in the stone, your voice a desperate, low murmur. "Open up." With a flick of your wrist, you toss a single iron coin toward the foundation, watching it bounce uselessly against the rock with a lonely, metallic ring.

The stone offers no reply, and the silence of the night settles heavily around you, broken only by the distant, rhythmic tapping of **Halden**'s finger from inside the common room. The coin settles into the dirt, a small, insignificant sacrifice to an unfeeling wall.

A heavy latch thuds from the other side of the door, followed by the sound of a wooden bolt being drawn back. The door doesn't swing wide, but it creaks open just a few inches, revealing a sliver of warm, amber light and the sharp, inquisitive eyes of **Edda**. She is a woman of middle years with hair pulled back in a severe, practical knot, her face etched with the weary lines of someone who has spent a lifetime managing both people and problems.

"Credits won't make the stone listen, boy," **Edda** says, her voice a dry, no-nonsense rasp that cuts through the chill of the night. She glances down at the solitary coin glinting in the mud, then up at your bruised, weary face. She nudges the door open a little further, her gaze shifting pointedly toward the shadows where the two thugs had stood moments ago. "If you're looking to bribe the wind, you're wasting your breath. But if you're looking for a bowl of stew and a door that actually stays shut, stop talking to the masonry and get inside before the frost bites harder than those men did."

## player_intent
**intimidate**: Confront Matthew Estrada to demand his true identity and motives.

## CURRENT TURN 10 NARRATION
You lunge across the small gap between the door and the bar, your fingers locking like iron around the wrist of **Matthew Estrada**. He is taller than you, his broad shoulders casting a wide shadow across the amber-lit floorboards, but your grip is sudden and fueled by a desperate, jagged adrenaline. "Who are you?" you hiss, your face inches from his, your eyes burning with a frantic intensity that ignores the sharp throb in your ribs. "Stop watching the room like a soldier on watch and tell me what you're doing here!"

**Matthew Estrada** doesn't flinch or pull away. Instead, he remains unnervingly still, his gaze dropping to your hand on his wrist with a look of detached, professional curiosity. He doesn't reach for a weapon, nor does he attempt to twist free; he simply waits for your grip to tire. When he finally speaks, his voice is a low, steady rumble that sounds more like a command than an answer. "You've got a grip like a cornered rat, runner," he says, his eyes locking onto yours with a piercing, disciplined clarity. "And a habit of picking fights you can't finish."

He doesn't shake you off, but he doesn't yield either. He leans in slightly, the scent of old leather and road dust radiating from his jerkin, and his tone shifts from calm to something much more pointed. "I'm not here for the stew, and I'm certainly not here for the company," he murmurs, his eyes flicking briefly toward the door where the thugs had lingered, then back to you. "I'm waiting for a shipment that doesn't appear on any merchant's ledger. If you want to keep your teeth, I'd suggest you find a corner, eat your meal, and stop pretending you're more than a messenger."

Despite his dismissal, there is an opening in his composure—a momentary lapse where his eyes scan the room behind you, checking the perimeter even as you hold him. He isn't just a traveler; he is a man waiting for a signal, and your outburst has clearly signaled to him that you are a variable he hadn't accounted for. He offers a small, grim twist of his wrist, a silent dare for you to let go or find out exactly what a man of his training is capable of when provoked.
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "Confront Matthew Estrada to demand his true identity and motives.",
  "intent_verb": "intimidate",
  "target": "Matthew Estrada",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal"
  }
}
```

### Narration

You lunge across the small gap between the door and the bar, your fingers locking like iron around the wrist of **Matthew Estrada**. He is taller than you, his broad shoulders casting a wide shadow across the amber-lit floorboards, but your grip is sudden and fueled by a desperate, jagged adrenaline. "Who are you?" you hiss, your face inches from his, your eyes burning with a frantic intensity that ignores the sharp throb in your ribs. "Stop watching the room like a soldier on watch and tell me what you're doing here!"

**Matthew Estrada** doesn't flinch or pull away. Instead, he remains unnervingly still, his gaze dropping to your hand on his wrist with a look of detached, professional curiosity. He doesn't reach for a weapon, nor does he attempt to twist free; he simply waits for your grip to tire. When he finally speaks, his voice is a low, steady rumble that sounds more like a command than an answer. "You've got a grip like a cornered rat, runner," he says, his eyes locking onto yours with a piercing, disciplined clarity. "And a habit of picking fights you can't finish."

He doesn't shake you off, but he doesn't yield either. He leans in slightly, the scent of old leather and road dust radiating from his jerkin, and his tone shifts from calm to something much more pointed. "I'm not here for the stew, and I'm certainly not here for the company," he murmurs, his eyes flicking briefly toward the door where the thugs had lingered, then back to you. "I'm waiting for a shipment that doesn't appear on any merchant's ledger. If you want to keep your teeth, I'd suggest you find a corner, eat your meal, and stop pretending you're more than a messenger."

Despite his dismissal, there is an opening in his composure—a momentary lapse where his eyes scan the room behind you, checking the perimeter even as you hold him. He isn't just a traveler; he is a man waiting for a signal, and your outburst has clearly signaled to him that you are a variable he hadn't accounted for. He offers a small, grim twist of his wrist, a silent dare for you to let go or find out exactly what a man of his training is capable of when provoked.

### Extract Scene

```json
{
  "scene_tags": [
    "confrontation",
    "tense_conversation",
    "suspense"
  ],
  "scene_tagline": "A Cornered Rat's Outburst",
  "location_change": {
    "id": "crossed_keys_inn",
    "name": "Crossed Keys Inn",
    "description": "The interior is bathed in warm, amber light, featuring wooden floorboards and a bar that separates the common room from the entrance."
  },
  "npc_add": [
    {
      "id": "matthew_estrada",
      "notes": "Unnerved by the player's sudden aggression but remains professionally detached and disciplined; views the player as a chaotic variable.",
      "name": "Matthew Estrada"
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Watching the confrontation from within the common room."
    },
    {
      "id": "innkeeper",
      "notes": "Observing the player's sudden outburst and physical altercation with Matthew."
    }
  ],
  "compendium_npc_update": [
    {
      "id": "matthew_estrada",
      "bio": "A tall, broad-shouldered man with disciplined, soldier-like training who is currently waiting for a clandestine shipment.",
      "aliases": [],
      "motivation": "Waiting for a secret shipment that does not appear on any merchant's ledger."
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "matthew_estrada_identity_clue",
      "text": "Matthew Estrada reveals he is waiting for a shipment not listed on any merchant's ledger.",
      "turn": 10
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Release his wrist and demand to know about the shipment.",
    "Back away and watch him from a corner of the inn.",
    "Ask Edda if she knows anything about the mysterious shipment.",
    "Keep your hand on your dagger and watch his every move."
  ],
  "outcome_summary": "You confront Matthew Estrada, but he remains unnervingly calm, revealing he is waiting for an unrecorded shipment and warning you to stay out of his way.",
  "gm_beat": {
    "type": "revelation",
    "surface_as": "npc_behavior"
  },
  "thread_advance": [
    "halden_new_contract"
  ],
  "thread_resolve": []
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1770t trimmed=False
- narrate: est=6310t trimmed=False
- extract.scene: est=4411t trimmed=False attempts=1
- extract.state: est=4548t trimmed=False attempts=1
- extract.storytell: est=5665t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 10

**Input:** ``

## User Prompts

### Ruling User Prompt
```
(no ruling call this turn)
```

### Narrate User Prompt
```
(no narrate call)
```

### Extract Scene User Prompt
```
(not captured)
```

### Extract State User Prompt
```
(not captured)
```

### Storyteller User Prompt
```
(not captured)
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{}
```

### Extract State

```json
{}
```

### Storyteller

```json
{}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

```json
{}
```


---

# TURN 11

**Input:** `Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: Crossed Keys Inn
## Present NPCs (in scene right now)
- Halden (Merchant) — Watching the confrontation from within the common room.
- Edda (Innkeeper at the Crossed Keys) — Observing the player's sudden outburst and physical altercation with Matthew.
- Matthew Estrada (Traveler) — Unnerved by the player's sudden aggression but remains professionally detached and disciplined; views the player as a chaotic variable.

## Inventory
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)


## Current Turn: 11
=== PLAYER INPUT ===
Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
Crossed Keys Inn (crossed_keys_inn)
The interior is bathed in warm, amber light, featuring wooden floorboards and a bar that separates the common room from the entrance.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.




## Characters
Before introducing a new named NPC, check this list first.

- **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. Wiping down the bar at the Crossed Keys, which is two streets over. | Observing the player's sudden outburst and physical altercation with Matthew.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Watching the confrontation from within the common room.

- **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | Unnerved by the player's sudden aggression but remains professionally detached and disciplined; views the player as a chaotic variable.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Met with Caron at the tavern to address the long-standing debt.
- [T2] Paid Caron 500 credits, successfully clearing the debt from his ledger.
- [T3] Contracted by Halden to deliver a wax-sealed ledger to Edda at the Crossed Keys Inn for 200 credits.
- [T4] Traveled from Marrow's Crossing to the Crossed Keys Inn via the merchant road.
- [T5] Confronted Bald Tough and Scarred Tough at the inn entrance; they claimed to be waiting for a specific delivery.
- [T6] Bribed the toughs with 200 credits to clear the path to the inn.
- [T7] Delivered the wax-sealed ledger to Halden at the Crossed Keys; Halden hinted at a new job opportunity.
- [T8] Attempted to use the brass key on the inn's front door, but it failed; Halden suggested Edda's larder for privacy.
## Recent Turns

**T9:** You lean your weight against the cold, uneven stone of the inn's exterior, pressing your ear to the masonry to listen for any sign of life behind the thick walls. "I have credits," you whisper toward the cracks in the stone, your voice a desperate, low murmur. "Open up." With a flick of your wrist, you toss a single iron coin toward the foundation, watching it bounce uselessly against the rock with a lonely, metallic ring.

The stone offers no reply, and the silence of the night settles heavily around you, broken only by the distant, rhythmic tapping of **Halden**'s finger from inside the common room. The coin settles into the dirt, a small, insignificant sacrifice to an unfeeling wall.

A heavy latch thuds from the other side of the door, followed by the sound of a wooden bolt being drawn back. The door doesn't swing wide, but it creaks open just a few inches, revealing a sliver of warm, amber light and the sharp, inquisitive eyes of **Edda**. She is a woman of middle years with hair pulled back in a severe, practical knot, her face etched with the weary lines of someone who has spent a lifetime managing both people and problems.

"Credits won't make the stone listen, boy," **Edda** says, her voice a dry, no-nonsense rasp that cuts through the chill of the night. She glances down at the solitary coin glinting in the mud, then up at your bruised, weary face. She nudges the door open a little further, her gaze shifting pointedly toward the shadows where the two thugs had stood moments ago. "If you're looking to bribe the wind, you're wasting your breath. But if you're looking for a bowl of stew and a door that actually stays shut, stop talking to the masonry and get inside before the frost bites harder than those men did."


**T10:** You lunge across the small gap between the door and the bar, your fingers locking like iron around the wrist of **Matthew Estrada**. He is taller than you, his broad shoulders casting a wide shadow across the amber-lit floorboards, but your grip is sudden and fueled by a desperate, jagged adrenaline. "Who are you?" you hiss, your face inches from his, your eyes burning with a frantic intensity that ignores the sharp throb in your ribs. "Stop watching the room like a soldier on watch and tell me what you're doing here!"

**Matthew Estrada** doesn't flinch or pull away. Instead, he remains unnervingly still, his gaze dropping to your hand on his wrist with a look of detached, professional curiosity. He doesn't reach for a weapon, nor does he attempt to twist free; he simply waits for your grip to tire. When he finally speaks, his voice is a low, steady rumble that sounds more like a command than an answer. "You've got a grip like a cornered rat, runner," he says, his eyes locking onto yours with a piercing, disciplined clarity. "And a habit of picking fights you can't finish."

He doesn't shake you off, but he doesn't yield either. He leans in slightly, the scent of old leather and road dust radiating from his jerkin, and his tone shifts from calm to something much more pointed. "I'm not here for the stew, and I'm certainly not here for the company," he murmurs, his eyes flicking briefly toward the door where the thugs had lingered, then back to you. "I'm waiting for a shipment that doesn't appear on any merchant's ledger. If you want to keep your teeth, I'd suggest you find a corner, eat your meal, and stop pretending you're more than a messenger."

Despite his dismissal, there is an opening in his composure—a momentary lapse where his eyes scan the room behind you, checking the perimeter even as you hold him. He isn't just a traveler; he is a man waiting for a signal, and your outburst has clearly signaled to him that you are a variable he hadn't accounted for. He offers a small, grim twist of his wrist, a silent dare for you to let go or find out exactly what a man of his training is capable of when provoked.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 11) Result


**Band:** FAIL → The sneak fails. The attempt fails outright — what you tried to do does not happen. The roll was close — narrate a complication or setback that still allows the story to move forward, rather than a full dead-end punishment.


**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.

=== PLAYER INPUT ===
Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.
=== END PLAYER INPUT ===

**Beat:** REVELATION — surface as `npc_behavior`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
```

### Extract Scene User Prompt
```
## location
`crossed_keys_inn` | Crossed Keys Inn
The interior is bathed in warm, amber light, featuring wooden floorboards and a bar that separates the common room from the entrance.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | **Halden** (Merchant) — Watching the confrontation from within the common room.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Observing the player's sudden outburst and physical altercation with Matthew.
- `matthew_estrada` | **Matthew Estrada** (Traveler) — Unnerved by the player's sudden aggression but remains professionally detached and disciplined; views the player as a chaotic variable.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T10 context)
You lunge across the small gap between the door and the bar, your fingers locking like iron around the wrist of **Matthew Estrada**. He is taller than you, his broad shoulders casting a wide shadow across the amber-lit floorboards, but your grip is sudden and fueled by a desperate, jagged adrenaline. "Who are you?" you hiss, your face inches from his, your eyes burning with a frantic intensity that ignores the sharp throb in your ribs. "Stop watching the room like a soldier on watch and tell me what you're doing here!"

**Matthew Estrada** doesn't flinch or pull away. Instead, he remains unnervingly still, his gaze dropping to your hand on his wrist with a look of detached, professional curiosity. He doesn't reach for a weapon, nor does he attempt to twist free; he simply waits for your grip to tire. When he finally speaks, his voice is a low, steady rumble that sounds more like a command than an answer. "You've got a grip like a cornered rat, runner," he says, his eyes locking onto yours with a piercing, disciplined clarity. "And a habit of picking fights you can't finish."

He doesn't shake you off, but he doesn't yield either. He leans in slightly, the scent of old leather and road dust radiating from his jerkin, and his tone shifts from calm to something much more pointed. "I'm not here for the stew, and I'm certainly not here for the company," he murmurs, his eyes flicking briefly toward the door where the thugs had lingered, then back to you. "I'm waiting for a shipment that doesn't appear on any merchant's ledger. If you want to keep your teeth, I'd suggest you find a corner, eat your meal, and stop pretending you're more than a messenger."

Despite his dismissal, there is an opening in his composure—a momentary lapse where his eyes scan the room behind you, checking the perimeter even as you hold him. He isn't just a traveler; he is a man waiting for a signal, and your outburst has clearly signaled to him that you are a variable he hadn't accounted for. He offers a small, grim twist of his wrist, a silent dare for you to let go or find out exactly what a man of his training is capable of when provoked.

## CURRENT TURN 11 NARRATION
You lunge at **Matthew Estrada**, throwing your entire weight into a desperate tackle intended to upend him, but your aim is clumsy and your ribs scream in protest at the sudden exertion. Instead of bringing the soldier down, you collide heavily with the side of the bar, your shoulder slamming into the polished wood with a jarring thud that sends a collection of pewter mugs clattering to the floor. **Matthew** doesn't tumble; he pivots with a fluid, practiced grace, stepping out of your path and letting your momentum carry you uselessly into the heavy timber of the bar.

Before you can scramble up to reach for his coat, a flash of steel catches the amber light. **Matthew**'s companion, a man with a face like scarred flint named **Daniel Calloway**, steps from the shadows of a booth. He doesn't shout or roar; he simply draws a long, thin utility knife from a sheath at his hip, the blade leveled directly at your throat with terrifying precision. He moves into your personal space, the tip of the knife hovering an inch from your windpipe, his eyes cold and devoid of any heat or anger.

"Sit down, boy, or you'll find out how quickly a man can bleed out on an innkeeper's floor," **Daniel Calloway** says, his voice a terrifyingly calm monotone that cuts through the sudden, stunned silence of the common room. He doesn't look at the spilled mugs or the wide-eyed **Edda** behind the bar; his focus is entirely on your jugular. He holds the knife with a steady, professional hand, waiting for you to realize that your attempt at a sneak attack was nothing more than a clumsy stumble against a professional's perimeter.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
sneak: Tackle the bodyguard into the shelves and attempt to pickpocket him while he is disoriented.
## CURRENT TURN 11 NARRATION
You lunge at **Matthew Estrada**, throwing your entire weight into a desperate tackle intended to upend him, but your aim is clumsy and your ribs scream in protest at the sudden exertion. Instead of bringing the soldier down, you collide heavily with the side of the bar, your shoulder slamming into the polished wood with a jarring thud that sends a collection of pewter mugs clattering to the floor. **Matthew** doesn't tumble; he pivots with a fluid, practiced grace, stepping out of your path and letting your momentum carry you uselessly into the heavy timber of the bar.

Before you can scramble up to reach for his coat, a flash of steel catches the amber light. **Matthew**'s companion, a man with a face like scarred flint named **Daniel Calloway**, steps from the shadows of a booth. He doesn't shout or roar; he simply draws a long, thin utility knife from a sheath at his hip, the blade leveled directly at your throat with terrifying precision. He moves into your personal space, the tip of the knife hovering an inch from your windpipe, his eyes cold and devoid of any heat or anger.

"Sit down, boy, or you'll find out how quickly a man can bleed out on an innkeeper's floor," **Daniel Calloway** says, his voice a terrifyingly calm monotone that cuts through the sudden, stunned silence of the common room. He doesn't look at the spilled mugs or the wide-eyed **Edda** behind the bar; his focus is entirely on your jugular. He holds the knife with a steady, professional hand, waiting for you to realize that your attempt at a sneak attack was nothing more than a clumsy stumble against a professional's perimeter.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `daniel_calloway` | **Daniel Calloway** (Matthew's Companion) [PRESENT] — A man with a face like scarred flint and a cold, professional demeanor who moves with lethal efficiency.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. Wiping down the bar at the Crossed Keys, which is two streets over.
- `halden` | **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
- `matthew_estrada` | **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Crossed Keys Inn** — Pewter mugs lie scattered and clattering across the floor near the bar where you just collided.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- winded: winded — A heavy collision with the bar has left you gasping for breath and momentarily stunned.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads (all — unified list, scope handled by Python)
- `halden_new_contract` [ARC]  [NORMAL] Halden has a new, potentially more lucrative or dangerous job for a persistent runner. tags: halden, job_offer (last seen T10)

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your long-standing debt to Caron has finally been settled in full.
- The wax-sealed ledger has been delivered to Halden at the Crossed Keys.
- Halden has hinted at a new, potentially lucrative job for a runner of your persistence.
- The thugs at the inn have been bribed, but the brass key does not fit the main entrance.

## rules_outcome
Band: FAIL. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.

## pacing_context
Directive: none
Gate: allow

## last turn's context (T10)
You lunge across the small gap between the door and the bar, your fingers locking like iron around the wrist of **Matthew Estrada**. He is taller than you, his broad shoulders casting a wide shadow across the amber-lit floorboards, but your grip is sudden and fueled by a desperate, jagged adrenaline. "Who are you?" you hiss, your face inches from his, your eyes burning with a frantic intensity that ignores the sharp throb in your ribs. "Stop watching the room like a soldier on watch and tell me what you're doing here!"

**Matthew Estrada** doesn't flinch or pull away. Instead, he remains unnervingly still, his gaze dropping to your hand on his wrist with a look of detached, professional curiosity. He doesn't reach for a weapon, nor does he attempt to twist free; he simply waits for your grip to tire. When he finally speaks, his voice is a low, steady rumble that sounds more like a command than an answer. "You've got a grip like a cornered rat, runner," he says, his eyes locking onto yours with a piercing, disciplined clarity. "And a habit of picking fights you can't finish."

He doesn't shake you off, but he doesn't yield either. He leans in slightly, the scent of old leather and road dust radiating from his jerkin, and his tone shifts from calm to something much more pointed. "I'm not here for the stew, and I'm certainly not here for the company," he murmurs, his eyes flicking briefly toward the door where the thugs had lingered, then back to you. "I'm waiting for a shipment that doesn't appear on any merchant's ledger. If you want to keep your teeth, I'd suggest you find a corner, eat your meal, and stop pretending you're more than a messenger."

Despite his dismissal, there is an opening in his composure—a momentary lapse where his eyes scan the room behind you, checking the perimeter even as you hold him. He isn't just a traveler; he is a man waiting for a signal, and your outburst has clearly signaled to him that you are a variable he hadn't accounted for. He offers a small, grim twist of his wrist, a silent dare for you to let go or find out exactly what a man of his training is capable of when provoked.

## player_intent
**sneak**: Tackle the bodyguard into the shelves and attempt to pickpocket him while he is disoriented.

## CURRENT TURN 11 NARRATION
You lunge at **Matthew Estrada**, throwing your entire weight into a desperate tackle intended to upend him, but your aim is clumsy and your ribs scream in protest at the sudden exertion. Instead of bringing the soldier down, you collide heavily with the side of the bar, your shoulder slamming into the polished wood with a jarring thud that sends a collection of pewter mugs clattering to the floor. **Matthew** doesn't tumble; he pivots with a fluid, practiced grace, stepping out of your path and letting your momentum carry you uselessly into the heavy timber of the bar.

Before you can scramble up to reach for his coat, a flash of steel catches the amber light. **Matthew**'s companion, a man with a face like scarred flint named **Daniel Calloway**, steps from the shadows of a booth. He doesn't shout or roar; he simply draws a long, thin utility knife from a sheath at his hip, the blade leveled directly at your throat with terrifying precision. He moves into your personal space, the tip of the knife hovering an inch from your windpipe, his eyes cold and devoid of any heat or anger.

"Sit down, boy, or you'll find out how quickly a man can bleed out on an innkeeper's floor," **Daniel Calloway** says, his voice a terrifyingly calm monotone that cuts through the sudden, stunned silence of the common room. He doesn't look at the spilled mugs or the wide-eyed **Edda** behind the bar; his focus is entirely on your jugular. He holds the knife with a steady, professional hand, waiting for you to realize that your attempt at a sneak attack was nothing more than a clumsy stumble against a professional's perimeter.
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "Tackle the bodyguard into the shelves and attempt to pickpocket him while he is disoriented.",
  "intent_verb": "sneak",
  "target": "Matthew's bodyguard",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "hard"
  }
}
```

### Narration

You lunge at **Matthew Estrada**, throwing your entire weight into a desperate tackle intended to upend him, but your aim is clumsy and your ribs scream in protest at the sudden exertion. Instead of bringing the soldier down, you collide heavily with the side of the bar, your shoulder slamming into the polished wood with a jarring thud that sends a collection of pewter mugs clattering to the floor. **Matthew** doesn't tumble; he pivots with a fluid, practiced grace, stepping out of your path and letting your momentum carry you uselessly into the heavy timber of the bar.

Before you can scramble up to reach for his coat, a flash of steel catches the amber light. **Matthew**'s companion, a man with a face like scarred flint named **Daniel Calloway**, steps from the shadows of a booth. He doesn't shout or roar; he simply draws a long, thin utility knife from a sheath at his hip, the blade leveled directly at your throat with terrifying precision. He moves into your personal space, the tip of the knife hovering an inch from your windpipe, his eyes cold and devoid of any heat or anger.

"Sit down, boy, or you'll find out how quickly a man can bleed out on an innkeeper's floor," **Daniel Calloway** says, his voice a terrifyingly calm monotone that cuts through the sudden, stunned silence of the common room. He doesn't look at the spilled mugs or the wide-eyed **Edda** behind the bar; his focus is entirely on your jugular. He holds the knife with a steady, professional hand, waiting for you to realize that your attempt at a sneak attack was nothing more than a clumsy stumble against a professional's perimeter.

### Extract Scene

```json
{
  "scene_tags": [
    "confrontation",
    "tense_standoff",
    "intimidation"
  ],
  "scene_tagline": "A Blade at the Throat",
  "location_description": "Pewter mugs lie scattered and clattering across the floor near the bar where you just collided.",
  "npc_add": [
    {
      "id": "daniel_calloway",
      "notes": "Holding a knife to the player's throat with terrifying, calm precision; acting as Matthew's protector.",
      "name": "Daniel Calloway",
      "title": "Matthew's Companion",
      "bio": "A man with a face like scarred flint and a cold, professional demeanor who moves with lethal efficiency."
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "matthew_estrada",
      "notes": "Watching the player's failed tackle with practiced, fluid grace, remaining composed and unbothered."
    },
    {
      "id": "innkeeper",
      "notes": "Wide-eyed and stunned by the sudden violence and the appearance of a knife."
    },
    {
      "id": "halden",
      "notes": "Watching the sudden escalation and the appearance of a new, armed threat."
    }
  ],
  "compendium_npc_update": [
    {
      "id": "daniel_calloway",
      "name": "Daniel Calloway",
      "title": "Companion to Matthew Estrada",
      "bio": "A man with a face like scarred flint and a cold, professional demeanor who moves with lethal efficiency.",
      "aliases": [],
      "allegiance": "Unknown (associated with Matthew Estrada)"
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [
    {
      "id": "winded",
      "label": "winded",
      "description": "A heavy collision with the bar has left you gasping for breath and momentarily stunned."
    }
  ],
  "pc_condition_remove": [
    {
      "id": "bruisedribs"
    }
  ]
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "daniel_calloway_threat",
      "text": "Daniel Calloway has drawn a knife and is holding it to your throat.",
      "turn": 11
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Raise your hands and slowly back away from the knife.",
    "Try to reason with Daniel and explain your mistake.",
    "Reach for your iron dagger to defend yourself.",
    "Look to Matthew for help or a way out of this."
  ],
  "outcome_summary": "Your clumsy tackle fails, leaving you winded and at the mercy of Daniel Calloway's blade.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior"
  },
  "thread_advance": [],
  "thread_resolve": []
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1754t trimmed=False
- narrate: est=6259t trimmed=False
- extract.scene: est=4409t trimmed=False attempts=1
- extract.state: est=4407t trimmed=False attempts=1
- extract.storytell: est=5593t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 12

**Input:** `I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, winded

## scene
Location: Crossed Keys Inn
## Present NPCs (in scene right now)
- Halden (Merchant) — Watching the sudden escalation and the appearance of a new, armed threat.
- Edda (Innkeeper at the Crossed Keys) — Wide-eyed and stunned by the sudden violence and the appearance of a knife.
- Matthew Estrada (Traveler) — Watching the player's failed tackle with practiced, fluid grace, remaining composed and unbothered.
- Daniel Calloway (Matthew's Companion) — Holding a knife to the player's throat with terrifying, calm precision; acting as Matthew's protector.

## Inventory
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)

## Last Turn Outcome
Your clumsy tackle fails, leaving you winded and at the mercy of Daniel Calloway's blade.

## Current Turn: 12
=== PLAYER INPUT ===
I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, winded

## Location
Crossed Keys Inn (crossed_keys_inn)
Pewter mugs lie scattered and clattering across the floor near the bar where you just collided.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.




## Characters
Before introducing a new named NPC, check this list first.

- **Daniel Calloway** (Matthew's Companion) [PRESENT] — A man with a face like scarred flint and a cold, professional demeanor who moves with lethal efficiency. | Holding a knife to the player's throat with terrifying, calm precision; acting as Matthew's protector.

- **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. Wiping down the bar at the Crossed Keys, which is two streets over. | Wide-eyed and stunned by the sudden violence and the appearance of a knife.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Watching the sudden escalation and the appearance of a new, armed threat.

- **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | Watching the player's failed tackle with practiced, fluid grace, remaining composed and unbothered.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Met with Caron at the tavern to address the long-standing debt.
- [T2] Paid Caron 500 credits, successfully clearing the debt from his ledger.
- [T3] Contracted by Halden to deliver a wax-sealed ledger to Edda at the Crossed Keys Inn for 200 credits.
- [T4] Traveled from Marrow's Crossing to the Crossed Keys Inn via the merchant road.
- [T5] Confronted Bald Tough and Scarred Tough at the inn entrance; they claimed to be waiting for a specific delivery.
- [T6] Bribed the toughs with 200 credits to clear the path to the inn.
- [T7] Delivered the wax-sealed ledger to Halden at the Crossed Keys; Halden hinted at a new job opportunity.
- [T8] Attempted to use the brass key on the inn's front door, but it failed; Halden suggested Edda's larder for privacy.
## Recent Turns

**T9:** You lean your weight against the cold, uneven stone of the inn's exterior, pressing your ear to the masonry to listen for any sign of life behind the thick walls. "I have credits," you whisper toward the cracks in the stone, your voice a desperate, low murmur. "Open up." With a flick of your wrist, you toss a single iron coin toward the foundation, watching it bounce uselessly against the rock with a lonely, metallic ring.

The stone offers no reply, and the silence of the night settles heavily around you, broken only by the distant, rhythmic tapping of **Halden**'s finger from inside the common room. The coin settles into the dirt, a small, insignificant sacrifice to an unfeeling wall.

A heavy latch thuds from the other side of the door, followed by the sound of a wooden bolt being drawn back. The door doesn't swing wide, but it creaks open just a few inches, revealing a sliver of warm, amber light and the sharp, inquisitive eyes of **Edda**. She is a woman of middle years with hair pulled back in a severe, practical knot, her face etched with the weary lines of someone who has spent a lifetime managing both people and problems.

"Credits won't make the stone listen, boy," **Edda** says, her voice a dry, no-nonsense rasp that cuts through the chill of the night. She glances down at the solitary coin glinting in the mud, then up at your bruised, weary face. She nudges the door open a little further, her gaze shifting pointedly toward the shadows where the two thugs had stood moments ago. "If you're looking to bribe the wind, you're wasting your breath. But if you're looking for a bowl of stew and a door that actually stays shut, stop talking to the masonry and get inside before the frost bites harder than those men did."


**T10:** You lunge across the small gap between the door and the bar, your fingers locking like iron around the wrist of **Matthew Estrada**. He is taller than you, his broad shoulders casting a wide shadow across the amber-lit floorboards, but your grip is sudden and fueled by a desperate, jagged adrenaline. "Who are you?" you hiss, your face inches from his, your eyes burning with a frantic intensity that ignores the sharp throb in your ribs. "Stop watching the room like a soldier on watch and tell me what you're doing here!"

**Matthew Estrada** doesn't flinch or pull away. Instead, he remains unnervingly still, his gaze dropping to your hand on his wrist with a look of detached, professional curiosity. He doesn't reach for a weapon, nor does he attempt to twist free; he simply waits for your grip to tire. When he finally speaks, his voice is a low, steady rumble that sounds more like a command than an answer. "You've got a grip like a cornered rat, runner," he says, his eyes locking onto yours with a piercing, disciplined clarity. "And a habit of picking fights you can't finish."

He doesn't shake you off, but he doesn't yield either. He leans in slightly, the scent of old leather and road dust radiating from his jerkin, and his tone shifts from calm to something much more pointed. "I'm not here for the stew, and I'm certainly not here for the company," he murmurs, his eyes flicking briefly toward the door where the thugs had lingered, then back to you. "I'm waiting for a shipment that doesn't appear on any merchant's ledger. If you want to keep your teeth, I'd suggest you find a corner, eat your meal, and stop pretending you're more than a messenger."

Despite his dismissal, there is an opening in his composure—a momentary lapse where his eyes scan the room behind you, checking the perimeter even as you hold him. He isn't just a traveler; he is a man waiting for a signal, and your outburst has clearly signaled to him that you are a variable he hadn't accounted for. He offers a small, grim twist of his wrist, a silent dare for you to let go or find out exactly what a man of his training is capable of when provoked.


**T11:** You lunge at **Matthew Estrada**, throwing your entire weight into a desperate tackle intended to upend him, but your aim is clumsy and your ribs scream in protest at the sudden exertion. Instead of bringing the soldier down, you collide heavily with the side of the bar, your shoulder slamming into the polished wood with a jarring thud that sends a collection of pewter mugs clattering to the floor. **Matthew** doesn't tumble; he pivots with a fluid, practiced grace, stepping out of your path and letting your momentum carry you uselessly into the heavy timber of the bar.

Before you can scramble up to reach for his coat, a flash of steel catches the amber light. **Matthew**'s companion, a man with a face like scarred flint named **Daniel Calloway**, steps from the shadows of a booth. He doesn't shout or roar; he simply draws a long, thin utility knife from a sheath at his hip, the blade leveled directly at your throat with terrifying precision. He moves into your personal space, the tip of the knife hovering an inch from your windpipe, his eyes cold and devoid of any heat or anger.

"Sit down, boy, or you'll find out how quickly a man can bleed out on an innkeeper's floor," **Daniel Calloway** says, his voice a terrifyingly calm monotone that cuts through the sudden, stunned silence of the common room. He doesn't look at the spilled mugs or the wide-eyed **Edda** behind the bar; his focus is entirely on your jugular. He holds the knife with a steady, professional hand, waiting for you to realize that your attempt at a sneak attack was nothing more than a clumsy stumble against a professional's perimeter.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 12) Result


**Band:** SETBACK → The escape results in a setback. You are set back — a resource is spent, time is lost, or a new problem appears.


**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.

=== PLAYER INPUT ===
I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.
=== END PLAYER INPUT ===

**Beat:** PRESSURE — surface as `npc_behavior`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
```

### Extract Scene User Prompt
```
## location
`crossed_keys_inn` | Crossed Keys Inn
Pewter mugs lie scattered and clattering across the floor near the bar where you just collided.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | **Halden** (Merchant) — Watching the sudden escalation and the appearance of a new, armed threat.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Wide-eyed and stunned by the sudden violence and the appearance of a knife.
- `matthew_estrada` | **Matthew Estrada** (Traveler) — Watching the player's failed tackle with practiced, fluid grace, remaining composed and unbothered.
- `daniel_calloway` | **Daniel Calloway** (Matthew's Companion) — Holding a knife to the player's throat with terrifying, calm precision; acting as Matthew's protector.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T11 context)
You lunge at **Matthew Estrada**, throwing your entire weight into a desperate tackle intended to upend him, but your aim is clumsy and your ribs scream in protest at the sudden exertion. Instead of bringing the soldier down, you collide heavily with the side of the bar, your shoulder slamming into the polished wood with a jarring thud that sends a collection of pewter mugs clattering to the floor. **Matthew** doesn't tumble; he pivots with a fluid, practiced grace, stepping out of your path and letting your momentum carry you uselessly into the heavy timber of the bar.

Before you can scramble up to reach for his coat, a flash of steel catches the amber light. **Matthew**'s companion, a man with a face like scarred flint named **Daniel Calloway**, steps from the shadows of a booth. He doesn't shout or roar; he simply draws a long, thin utility knife from a sheath at his hip, the blade leveled directly at your throat with terrifying precision. He moves into your personal space, the tip of the knife hovering an inch from your windpipe, his eyes cold and devoid of any heat or anger.

"Sit down, boy, or you'll find out how quickly a man can bleed out on an innkeeper's floor," **Daniel Calloway** says, his voice a terrifyingly calm monotone that cuts through the sudden, stunned silence of the common room. He doesn't look at the spilled mugs or the wide-eyed **Edda** behind the bar; his focus is entirely on your jugular. He holds the knife with a steady, professional hand, waiting for you to realize that your attempt at a sneak attack was nothing more than a clumsy stumble against a professional's perimeter.

## CURRENT TURN 12 NARRATION
You lunge for your coat, fingers fumbling against the fabric to snatch the wax-sealed ledger, and then you bolt. You scramble past the stunned **Edda** and lurch through the kitchen's swinging door, your breath coming in ragged, stinging gasps that make your bruised ribs feel like they're being gnawed by hot iron. "Halden! Wait!" you scream over your shoulder, your voice cracking as you burst out of the back exit into the biting night air.

The cobblestones are slick with frost and river mist, making your footing treacherous as you sprint toward the docks. Behind you, the heavy thud of boots on wooden floorboards tells you that your sudden flight hasn't gone unnoticed. You hear a sharp, authoritative bark from the common room—**Daniel Calloway**'s voice, cutting through the air like a lash—ordering **Matthew Estrada** to intercept you. He isn't shouting in anger, but the professional urgency in his tone sends a chill down your spine that has nothing to do with the river wind.

You reach the edge of the docks, where the wooden planks groan under your weight and the scent of rotting silt and wet timber fills your lungs. The river is a black, churning maw beside you, swollen by recent rains. As you look for a place to hide or a path to follow, a shadow detaches itself from a stack of crates near the water's edge. It isn't one of the men from the inn, but a third party—a lean, hooded figure watching your frantic escape with an intensity that suggests they were waiting for exactly this kind of commotion.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- winded — A heavy collision with the bar has left you gasping for breath and momentarily stunned.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
escape: The player attempts to flee the scene with the ledger while calling out to Halden.
## CURRENT TURN 12 NARRATION
You lunge for your coat, fingers fumbling against the fabric to snatch the wax-sealed ledger, and then you bolt. You scramble past the stunned **Edda** and lurch through the kitchen's swinging door, your breath coming in ragged, stinging gasps that make your bruised ribs feel like they're being gnawed by hot iron. "Halden! Wait!" you scream over your shoulder, your voice cracking as you burst out of the back exit into the biting night air.

The cobblestones are slick with frost and river mist, making your footing treacherous as you sprint toward the docks. Behind you, the heavy thud of boots on wooden floorboards tells you that your sudden flight hasn't gone unnoticed. You hear a sharp, authoritative bark from the common room—**Daniel Calloway**'s voice, cutting through the air like a lash—ordering **Matthew Estrada** to intercept you. He isn't shouting in anger, but the professional urgency in his tone sends a chill down your spine that has nothing to do with the river wind.

You reach the edge of the docks, where the wooden planks groan under your weight and the scent of rotting silt and wet timber fills your lungs. The river is a black, churning maw beside you, swollen by recent rains. As you look for a place to hide or a path to follow, a shadow detaches itself from a stack of crates near the water's edge. It isn't one of the men from the inn, but a third party—a lean, hooded figure watching your frantic escape with an intensity that suggests they were waiting for exactly this kind of commotion.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `hooded_figure` | **Hooded Figure** (Unknown Observer) [PRESENT] — A lean, hooded individual lurking near the crates at the water's edge, observing the commotion.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...
- `daniel_calloway` | **Daniel Calloway** [KNOWN] — A man with a face like scarred flint and a cold, professional demeanor who moves with lethal efficiency.
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shouldered man with disciplined, soldier-like training who is currently waiting for a clandestine shipm...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**The Docks** — The scent of rotting silt and wet timber hangs heavy in the biting night air near the water's edge.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads (all — unified list, scope handled by Python)
- `halden_new_contract` [ARC]  [NORMAL] Halden has a new, potentially more lucrative or dangerous job for a persistent runner. tags: halden, job_offer (last seen T10)

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your long-standing debt to Caron has finally been settled in full.
- The wax-sealed ledger has been delivered to Halden at the Crossed Keys.
- Halden has hinted at a new, potentially lucrative job for a runner of your persistence.
- The thugs at the inn have been bribed, but the brass key does not fit the main entrance.
- Daniel Calloway has drawn a knife and is holding it to your throat.

## rules_outcome
Band: SETBACK. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.

## pacing_context
Directive: none
Gate: allow

## last turn's context (T11)
You lunge at **Matthew Estrada**, throwing your entire weight into a desperate tackle intended to upend him, but your aim is clumsy and your ribs scream in protest at the sudden exertion. Instead of bringing the soldier down, you collide heavily with the side of the bar, your shoulder slamming into the polished wood with a jarring thud that sends a collection of pewter mugs clattering to the floor. **Matthew** doesn't tumble; he pivots with a fluid, practiced grace, stepping out of your path and letting your momentum carry you uselessly into the heavy timber of the bar.

Before you can scramble up to reach for his coat, a flash of steel catches the amber light. **Matthew**'s companion, a man with a face like scarred flint named **Daniel Calloway**, steps from the shadows of a booth. He doesn't shout or roar; he simply draws a long, thin utility knife from a sheath at his hip, the blade leveled directly at your throat with terrifying precision. He moves into your personal space, the tip of the knife hovering an inch from your windpipe, his eyes cold and devoid of any heat or anger.

"Sit down, boy, or you'll find out how quickly a man can bleed out on an innkeeper's floor," **Daniel Calloway** says, his voice a terrifyingly calm monotone that cuts through the sudden, stunned silence of the common room. He doesn't look at the spilled mugs or the wide-eyed **Edda** behind the bar; his focus is entirely on your jugular. He holds the knife with a steady, professional hand, waiting for you to realize that your attempt at a sneak attack was nothing more than a clumsy stumble against a professional's perimeter.

## player_intent
**escape**: The player attempts to flee the scene with the ledger while calling out to Halden.

## CURRENT TURN 12 NARRATION
You lunge for your coat, fingers fumbling against the fabric to snatch the wax-sealed ledger, and then you bolt. You scramble past the stunned **Edda** and lurch through the kitchen's swinging door, your breath coming in ragged, stinging gasps that make your bruised ribs feel like they're being gnawed by hot iron. "Halden! Wait!" you scream over your shoulder, your voice cracking as you burst out of the back exit into the biting night air.

The cobblestones are slick with frost and river mist, making your footing treacherous as you sprint toward the docks. Behind you, the heavy thud of boots on wooden floorboards tells you that your sudden flight hasn't gone unnoticed. You hear a sharp, authoritative bark from the common room—**Daniel Calloway**'s voice, cutting through the air like a lash—ordering **Matthew Estrada** to intercept you. He isn't shouting in anger, but the professional urgency in his tone sends a chill down your spine that has nothing to do with the river wind.

You reach the edge of the docks, where the wooden planks groan under your weight and the scent of rotting silt and wet timber fills your lungs. The river is a black, churning maw beside you, swollen by recent rains. As you look for a place to hide or a path to follow, a shadow detaches itself from a stack of crates near the water's edge. It isn't one of the men from the inn, but a third party—a lean, hooded figure watching your frantic escape with an intensity that suggests they were waiting for exactly this kind of commotion.
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to flee the scene with the ledger while calling out to Halden.",
  "intent_verb": "escape",
  "target": "Daniel Calloway",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "hard"
  }
}
```

### Narration

You lunge for your coat, fingers fumbling against the fabric to snatch the wax-sealed ledger, and then you bolt. You scramble past the stunned **Edda** and lurch through the kitchen's swinging door, your breath coming in ragged, stinging gasps that make your bruised ribs feel like they're being gnawed by hot iron. "Halden! Wait!" you scream over your shoulder, your voice cracking as you burst out of the back exit into the biting night air.

The cobblestones are slick with frost and river mist, making your footing treacherous as you sprint toward the docks. Behind you, the heavy thud of boots on wooden floorboards tells you that your sudden flight hasn't gone unnoticed. You hear a sharp, authoritative bark from the common room—**Daniel Calloway**'s voice, cutting through the air like a lash—ordering **Matthew Estrada** to intercept you. He isn't shouting in anger, but the professional urgency in his tone sends a chill down your spine that has nothing to do with the river wind.

You reach the edge of the docks, where the wooden planks groan under your weight and the scent of rotting silt and wet timber fills your lungs. The river is a black, churning maw beside you, swollen by recent rains. As you look for a place to hide or a path to follow, a shadow detaches itself from a stack of crates near the water's edge. It isn't one of the men from the inn, but a third party—a lean, hooded figure watching your frantic escape with an intensity that suggests they were waiting for exactly this kind of commotion.


### Extract Scene

```json
{
  "scene_tags": [
    "chase",
    "tense",
    "stealth",
    "suspense"
  ],
  "scene_tagline": "A Desperate Flight to the Docks",
  "location_change": {
    "id": "the_docks",
    "name": "The Docks",
    "description": "A treacherous expanse of groaning wooden planks slick with frost and river mist, bordering a black, churning river."
  },
  "location_description": "The scent of rotting silt and wet timber hangs heavy in the biting night air near the water's edge.",
  "npc_add": [
    {
      "id": "hooded_figure",
      "notes": "Watching the player's frantic escape with intense interest from the shadows.",
      "name": "Hooded Figure",
      "title": "Unknown Observer",
      "bio": "A lean, hooded individual lurking near the crates at the water's edge, observing the commotion."
    }
  ],
  "npc_remove": [
    {
      "id": "halden"
    },
    {
      "id": "innkeeper"
    },
    {
      "id": "matthew_estrada"
    },
    {
      "id": "daniel_calloway"
    }
  ],
  "npc_update": [],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "wax_sealed_ledger",
      "name": "Wax-sealed ledger",
      "notes": "A ledger snatched during the escape.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "winded"
    }
  ]
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "flight_from_inn",
      "text": "You fled the inn through the kitchen, pursued by Daniel Calloway and Matthew Estrada.",
      "turn": 12
    },
    {
      "id": "hooded_observer_reveal",
      "text": "A mysterious hooded figure has emerged from the shadows near the docks, watching your escape.",
      "turn": 12
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Dive into the dark river to lose your pursuers.",
    "Attempt to negotiate with the hooded figure for help.",
    "Sprint toward Halden's location to seek immediate refuge.",
    "Hide among the crates to ambush the approaching men."
  ],
  "outcome_summary": "You narrowly escaped the inn through the kitchen, but you are now being pursued toward the docks by Matthew Estrada and Daniel Calloway.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior"
  },
  "thread_advance": [],
  "thread_resolve": []
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

```json
[
  {
    "field": "inventory_add",
    "kind": "durability_gate",
    "value": "wax_sealed_ledger",
    "reason": "New item 'Wax-sealed ledger' \u2014 no loot gain context detected in recent_events or actions; rejected by durability gate"
  }
]
```

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1826t trimmed=False
- narrate: est=6758t trimmed=False
- extract.scene: est=4313t trimmed=False attempts=1
- extract.state: est=4402t trimmed=False attempts=1
- extract.storytell: est=5390t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 13

**Input:** `I find a quiet corner at the dock and wrap my wounds with my shirt. Then I write a note to Caron about the intercepted courier and pay the dock boy to deliver it.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: The Docks
## Present NPCs (in scene right now)
- Hooded Figure (Unknown Observer) — Watching the player's frantic escape with intense interest from the shadows.

## Inventory
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)

## Last Turn Outcome
You narrowly escaped the inn through the kitchen, but you are now being pursued toward the docks by Matthew Estrada and Daniel Calloway.

## Current Turn: 13
=== PLAYER INPUT ===
I find a quiet corner at the dock and wrap my wounds with my shirt. Then I write a note to Caron about the intercepted courier and pay the dock boy to deliver it.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
The Docks (the_docks)
A treacherous expanse of groaning wooden planks slick with frost and river mist, bordering a black, churning river.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.




## Characters
Before introducing a new named NPC, check this list first.

- **Hooded Figure** (Unknown Observer) [PRESENT] — A lean, hooded individual lurking near the crates at the water's edge, observing the commotion. | Watching the player's frantic escape with intense interest from the shadows.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...

- **Daniel Calloway** [KNOWN] — A man with a face like scarred flint and a cold, professional demeanor who moves with lethal efficiency.

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: Needs a reliable courier to deliver a wax-sealed ledger to the Crossed Keys before morning.

- **Matthew Estrada** [KNOWN] — A tall, broad-shouldered man with disciplined, soldier-like training who is currently waiting for a clandestine shipm... | wants: Waiting for a secret shipment that does not appear on any merchant's ledger.

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Met with Caron at the tavern to address the long-standing debt.
- [T2] Paid Caron 500 credits, successfully clearing the debt from his ledger.
- [T3] Contracted by Halden to deliver a wax-sealed ledger to Edda at the Crossed Keys Inn for 200 credits.
- [T4] Traveled from Marrow's Crossing to the Crossed Keys Inn via the merchant road.
- [T5] Confronted Bald Tough and Scarred Tough at the inn entrance; they claimed to be waiting for a specific delivery.
- [T6] Bribed the toughs with 200 credits to clear the path to the inn.
- [T7] Delivered the wax-sealed ledger to Halden at the Crossed Keys; Halden hinted at a new job opportunity.
- [T8] Attempted to use the brass key on the inn's front door, but it failed; Halden suggested Edda's larder for privacy.
## Recent Turns

**T10:** You lunge across the small gap between the door and the bar, your fingers locking like iron around the wrist of **Matthew Estrada**. He is taller than you, his broad shoulders casting a wide shadow across the amber-lit floorboards, but your grip is sudden and fueled by a desperate, jagged adrenaline. "Who are you?" you hiss, your face inches from his, your eyes burning with a frantic intensity that ignores the sharp throb in your ribs. "Stop watching the room like a soldier on watch and tell me what you're doing here!"

**Matthew Estrada** doesn't flinch or pull away. Instead, he remains unnervingly still, his gaze dropping to your hand on his wrist with a look of detached, professional curiosity. He doesn't reach for a weapon, nor does he attempt to twist free; he simply waits for your grip to tire. When he finally speaks, his voice is a low, steady rumble that sounds more like a command than an answer. "You've got a grip like a cornered rat, runner," he says, his eyes locking onto yours with a piercing, disciplined clarity. "And a habit of picking fights you can't finish."

He doesn't shake you off, but he doesn't yield either. He leans in slightly, the scent of old leather and road dust radiating from his jerkin, and his tone shifts from calm to something much more pointed. "I'm not here for the stew, and I'm certainly not here for the company," he murmurs, his eyes flicking briefly toward the door where the thugs had lingered, then back to you. "I'm waiting for a shipment that doesn't appear on any merchant's ledger. If you want to keep your teeth, I'd suggest you find a corner, eat your meal, and stop pretending you're more than a messenger."

Despite his dismissal, there is an opening in his composure—a momentary lapse where his eyes scan the room behind you, checking the perimeter even as you hold him. He isn't just a traveler; he is a man waiting for a signal, and your outburst has clearly signaled to him that you are a variable he hadn't accounted for. He offers a small, grim twist of his wrist, a silent dare for you to let go or find out exactly what a man of his training is capable of when provoked.


**T11:** You lunge at **Matthew Estrada**, throwing your entire weight into a desperate tackle intended to upend him, but your aim is clumsy and your ribs scream in protest at the sudden exertion. Instead of bringing the soldier down, you collide heavily with the side of the bar, your shoulder slamming into the polished wood with a jarring thud that sends a collection of pewter mugs clattering to the floor. **Matthew** doesn't tumble; he pivots with a fluid, practiced grace, stepping out of your path and letting your momentum carry you uselessly into the heavy timber of the bar.

Before you can scramble up to reach for his coat, a flash of steel catches the amber light. **Matthew**'s companion, a man with a face like scarred flint named **Daniel Calloway**, steps from the shadows of a booth. He doesn't shout or roar; he simply draws a long, thin utility knife from a sheath at his hip, the blade leveled directly at your throat with terrifying precision. He moves into your personal space, the tip of the knife hovering an inch from your windpipe, his eyes cold and devoid of any heat or anger.

"Sit down, boy, or you'll find out how quickly a man can bleed out on an innkeeper's floor," **Daniel Calloway** says, his voice a terrifyingly calm monotone that cuts through the sudden, stunned silence of the common room. He doesn't look at the spilled mugs or the wide-eyed **Edda** behind the bar; his focus is entirely on your jugular. He holds the knife with a steady, professional hand, waiting for you to realize that your attempt at a sneak attack was nothing more than a clumsy stumble against a professional's perimeter.


**T12:** You lunge for your coat, fingers fumbling against the fabric to snatch the wax-sealed ledger, and then you bolt. You scramble past the stunned **Edda** and lurch through the kitchen's swinging door, your breath coming in ragged, stinging gasps that make your bruised ribs feel like they're being gnawed by hot iron. "Halden! Wait!" you scream over your shoulder, your voice cracking as you burst out of the back exit into the biting night air.

The cobblestones are slick with frost and river mist, making your footing treacherous as you sprint toward the docks. Behind you, the heavy thud of boots on wooden floorboards tells you that your sudden flight hasn't gone unnoticed. You hear a sharp, authoritative bark from the common room—**Daniel Calloway**'s voice, cutting through the air like a lash—ordering **Matthew Estrada** to intercept you. He isn't shouting in anger, but the professional urgency in his tone sends a chill down your spine that has nothing to do with the river wind.

You reach the edge of the docks, where the wooden planks groan under your weight and the scent of rotting silt and wet timber fills your lungs. The river is a black, churning maw beside you, swollen by recent rains. As you look for a place to hide or a path to follow, a shadow detaches itself from a stack of crates near the water's edge. It isn't one of the men from the inn, but a third party—a lean, hooded figure watching your frantic escape with an intensity that suggests they were waiting for exactly this kind of commotion.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.


## This Turn's (Turn 13) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I find a quiet corner at the dock and wrap my wounds with my shirt. Then I write a note to Caron about the intercepted courier and pay the dock boy to deliver it.
=== END PLAYER INPUT ===

**Beat:** PRESSURE — surface as `npc_behavior`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
```

### Extract Scene User Prompt
```
## location
`the_docks` | The Docks
A treacherous expanse of groaning wooden planks slick with frost and river mist, bordering a black, churning river.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `hooded_figure` | **Hooded Figure** (Unknown Observer) — Watching the player's frantic escape with intense interest from the shadows.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T12 context)
You lunge for your coat, fingers fumbling against the fabric to snatch the wax-sealed ledger, and then you bolt. You scramble past the stunned **Edda** and lurch through the kitchen's swinging door, your breath coming in ragged, stinging gasps that make your bruised ribs feel like they're being gnawed by hot iron. "Halden! Wait!" you scream over your shoulder, your voice cracking as you burst out of the back exit into the biting night air.

The cobblestones are slick with frost and river mist, making your footing treacherous as you sprint toward the docks. Behind you, the heavy thud of boots on wooden floorboards tells you that your sudden flight hasn't gone unnoticed. You hear a sharp, authoritative bark from the common room—**Daniel Calloway**'s voice, cutting through the air like a lash—ordering **Matthew Estrada** to intercept you. He isn't shouting in anger, but the professional urgency in his tone sends a chill down your spine that has nothing to do with the river wind.

You reach the edge of the docks, where the wooden planks groan under your weight and the scent of rotting silt and wet timber fills your lungs. The river is a black, churning maw beside you, swollen by recent rains. As you look for a place to hide or a path to follow, a shadow detaches itself from a stack of crates near the water's edge. It isn't one of the men from the inn, but a third party—a lean, hooded figure watching your frantic escape with an intensity that suggests they were waiting for exactly this kind of commotion.

## CURRENT TURN 13 NARRATION
You lurch into the shadows of a stack of salt-crusted crates, your lungs burning as you sink onto a damp, mossy knot of timber. With trembling fingers, you tear a strip of fabric from your undershirt, pressing the makeshift bandage against your side to stem the throbbing heat of your bruised ribs. Every shallow breath is a battle against the stinging pain, and the frost-slicked boards beneath you offer no comfort, only a biting chill that seeps through your clothes.

You fumble for a scrap of parchment and a charcoal stick, your hands shaking so violently that the letters crawl across the page in a jagged, illegible scrawl. You manage to scratch out a frantic warning to **Caron**—a desperate note regarding the professional violence of the men at the inn and the danger of the intercepted courier—before folding the paper into a tight, messy knot. 

A small, shivering boy, no older than ten, drifts through the mist near a moored skiff, his eyes wide and wary. You lunge forward, pressing a few coins into his grime-streaked palm to ensure he sprints toward the town immediately. He doesn't linger to look you in the eye; he simply vanishes into the fog, his small boots tapping a frantic rhythm against the planks.

The silence of the docks is deceptive. From the direction of the inn, the heavy, rhythmic thud of pursuit begins to echo across the water, growing louder with every passing second. The sound of a raised voice—**Daniel Calloway**'s unmistakable, icy command—cuts through the mist, signaling that your brief moment of respite is over. The shadows near the crates seem to lean closer, and you realize the hooded figure hasn't moved an inch, still watching your desperate attempt at damage control with a terrifying, silent patience.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
negotiate: The player attempts to tend to their injuries and hire a dock boy to deliver a message.
## CURRENT TURN 13 NARRATION
You lurch into the shadows of a stack of salt-crusted crates, your lungs burning as you sink onto a damp, mossy knot of timber. With trembling fingers, you tear a strip of fabric from your undershirt, pressing the makeshift bandage against your side to stem the throbbing heat of your bruised ribs. Every shallow breath is a battle against the stinging pain, and the frost-slicked boards beneath you offer no comfort, only a biting chill that seeps through your clothes.

You fumble for a scrap of parchment and a charcoal stick, your hands shaking so violently that the letters crawl across the page in a jagged, illegible scrawl. You manage to scratch out a frantic warning to **Caron**—a desperate note regarding the professional violence of the men at the inn and the danger of the intercepted courier—before folding the paper into a tight, messy knot. 

A small, shivering boy, no older than ten, drifts through the mist near a moored skiff, his eyes wide and wary. You lunge forward, pressing a few coins into his grime-streaked palm to ensure he sprints toward the town immediately. He doesn't linger to look you in the eye; he simply vanishes into the fog, his small boots tapping a frantic rhythm against the planks.

The silence of the docks is deceptive. From the direction of the inn, the heavy, rhythmic thud of pursuit begins to echo across the water, growing louder with every passing second. The sound of a raised voice—**Daniel Calloway**'s unmistakable, icy command—cuts through the mist, signaling that your brief moment of respite is over. The shadows near the crates seem to lean closer, and you realize the hooded figure hasn't moved an inch, still watching your desperate attempt at damage control with a terrifying, silent patience.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## characters
- `hooded_figure` | **Hooded Figure** (Unknown Observer) [PRESENT] — A lean, hooded individual lurking near the crates at the water's edge, observing the commotion.
- `shivering_boy` | **Shivering Boy** (Street Urchin) [PRESENT] — A small, grime-streaked boy of about ten who moves through the docks like a ghost.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. Having finally collected his 500 credit...
- `daniel_calloway` | **Daniel Calloway** [KNOWN] — A man with a face like scarred flint and a cold, professional demeanor who moves with lethal efficiency.
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shouldered man with disciplined, soldier-like training who is currently waiting for a clandestine shipm...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**The Docks** — The dockside is cluttered with salt-crusted crates and mossy timber, all shrouded in a thick, deceptive mist.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

**Thematic question:** What does it cost to settle old debts when new ones keep forming?

**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.

## threads (all — unified list, scope handled by Python)
- `halden_new_contract` [ARC]  [NORMAL] Halden has a new, potentially more lucrative or dangerous job for a persistent runner. tags: halden, job_offer (last seen T10)

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your long-standing debt to Caron has finally been settled in full.
- The wax-sealed ledger has been delivered to Halden at the Crossed Keys.
- Halden has hinted at a new, potentially lucrative job for a runner of your persistence.
- The thugs at the inn have been bribed, but the brass key does not fit the main entrance.
- Daniel Calloway has drawn a knife and is holding it to your throat.
- You fled the inn through the kitchen, pursued by Daniel Calloway and Matthew Estrada.
- A mysterious hooded figure has emerged from the shadows near the docks, watching your escape.

## pacing_context
Directive: none
Gate: allow

## last turn's context (T12)
You lunge for your coat, fingers fumbling against the fabric to snatch the wax-sealed ledger, and then you bolt. You scramble past the stunned **Edda** and lurch through the kitchen's swinging door, your breath coming in ragged, stinging gasps that make your bruised ribs feel like they're being gnawed by hot iron. "Halden! Wait!" you scream over your shoulder, your voice cracking as you burst out of the back exit into the biting night air.

The cobblestones are slick with frost and river mist, making your footing treacherous as you sprint toward the docks. Behind you, the heavy thud of boots on wooden floorboards tells you that your sudden flight hasn't gone unnoticed. You hear a sharp, authoritative bark from the common room—**Daniel Calloway**'s voice, cutting through the air like a lash—ordering **Matthew Estrada** to intercept you. He isn't shouting in anger, but the professional urgency in his tone sends a chill down your spine that has nothing to do with the river wind.

You reach the edge of the docks, where the wooden planks groan under your weight and the scent of rotting silt and wet timber fills your lungs. The river is a black, churning maw beside you, swollen by recent rains. As you look for a place to hide or a path to follow, a shadow detaches itself from a stack of crates near the water's edge. It isn't one of the men from the inn, but a third party—a lean, hooded figure watching your frantic escape with an intensity that suggests they were waiting for exactly this kind of commotion.

## player_intent
**negotiate**: The player attempts to tend to their injuries and hire a dock boy to deliver a message.

## CURRENT TURN 13 NARRATION
You lurch into the shadows of a stack of salt-crusted crates, your lungs burning as you sink onto a damp, mossy knot of timber. With trembling fingers, you tear a strip of fabric from your undershirt, pressing the makeshift bandage against your side to stem the throbbing heat of your bruised ribs. Every shallow breath is a battle against the stinging pain, and the frost-slicked boards beneath you offer no comfort, only a biting chill that seeps through your clothes.

You fumble for a scrap of parchment and a charcoal stick, your hands shaking so violently that the letters crawl across the page in a jagged, illegible scrawl. You manage to scratch out a frantic warning to **Caron**—a desperate note regarding the professional violence of the men at the inn and the danger of the intercepted courier—before folding the paper into a tight, messy knot. 

A small, shivering boy, no older than ten, drifts through the mist near a moored skiff, his eyes wide and wary. You lunge forward, pressing a few coins into his grime-streaked palm to ensure he sprints toward the town immediately. He doesn't linger to look you in the eye; he simply vanishes into the fog, his small boots tapping a frantic rhythm against the planks.

The silence of the docks is deceptive. From the direction of the inn, the heavy, rhythmic thud of pursuit begins to echo across the water, growing louder with every passing second. The sound of a raised voice—**Daniel Calloway**'s unmistakable, icy command—cuts through the mist, signaling that your brief moment of respite is over. The shadows near the crates seem to lean closer, and you realize the hooded figure hasn't moved an inch, still watching your desperate attempt at damage control with a terrifying, silent patience.
## END CURRENT TURN NARRATION
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to tend to their injuries and hire a dock boy to deliver a message.",
  "intent_verb": "negotiate",
  "target": "dock boy",
  "check": {
    "required": false
  }
}
```

### Narration

You lurch into the shadows of a stack of salt-crusted crates, your lungs burning as you sink onto a damp, mossy knot of timber. With trembling fingers, you tear a strip of fabric from your undershirt, pressing the makeshift bandage against your side to stem the throbbing heat of your bruised ribs. Every shallow breath is a battle against the stinging pain, and the frost-slicked boards beneath you offer no comfort, only a biting chill that seeps through your clothes.

You fumble for a scrap of parchment and a charcoal stick, your hands shaking so violently that the letters crawl across the page in a jagged, illegible scrawl. You manage to scratch out a frantic warning to **Caron**—a desperate note regarding the professional violence of the men at the inn and the danger of the intercepted courier—before folding the paper into a tight, messy knot. 

A small, shivering boy, no older than ten, drifts through the mist near a moored skiff, his eyes wide and wary. You lunge forward, pressing a few coins into his grime-streaked palm to ensure he sprints toward the town immediately. He doesn't linger to look you in the eye; he simply vanishes into the fog, his small boots tapping a frantic rhythm against the planks.

The silence of the docks is deceptive. From the direction of the inn, the heavy, rhythmic thud of pursuit begins to echo across the water, growing louder with every passing second. The sound of a raised voice—**Daniel Calloway**'s unmistakable, icy command—cuts through the mist, signaling that your brief moment of respite is over. The shadows near the crates seem to lean closer, and you realize the hooded figure hasn't moved an inch, still watching your desperate attempt at damage control with a terrifying, silent patience.


### Extract Scene

```json
{
  "scene_tags": [
    "stealth",
    "tense_atmosphere",
    "pursuit"
  ],
  "scene_tagline": "A Desperate Warning",
  "location_description": "The dockside is cluttered with salt-crusted crates and mossy timber, all shrouded in a thick, deceptive mist.",
  "npc_add": [
    {
      "id": "shivering_boy",
      "notes": "A wary child who takes the player's coins and flees toward town.",
      "name": "Shivering Boy",
      "title": "Street Urchin",
      "bio": "A small, grime-streaked boy of about ten who moves through the docks like a ghost."
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "hooded_figure",
      "notes": "Watching the player's desperate attempt at damage control with terrifying, silent patience."
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "scrap_of_parchment",
      "name": "Scrap of parchment",
      "notes": "A frantic, illegible warning to Caron",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "charcoal_stick",
      "name": "Charcoal stick",
      "notes": "",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "recent_events_add": [
    {
      "id": "warning_sent_to_caron",
      "text": "You sent a frantic, illegible warning to Caron via a street urchin regarding the violence at the inn.",
      "turn": 13
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Hide deeper in the crates and wait for the pursuit to pass.",
    "Confront the hooded figure to see if they can be bribed for help.",
    "Attempt to slip into the river or a moored skiff to escape.",
    "Stand your ground and prepare your iron dagger for Calloway."
  ],
  "outcome_summary": "You managed to bandage your ribs and dispatch a message to Caron via the shivering boy, but the pursuit of Daniel Calloway is rapidly closing in.",
  "thread_advance": [
    "halden_new_contract"
  ],
  "thread_resolve": []
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

```json
[
  {
    "field": "inventory_add",
    "kind": "durability_gate",
    "value": "scrap_of_parchment",
    "reason": "New item 'Scrap of parchment' \u2014 no loot gain context detected in recent_events or actions; rejected by durability gate"
  },
  {
    "field": "inventory_add",
    "kind": "durability_gate",
    "value": "charcoal_stick",
    "reason": "New item 'Charcoal stick' \u2014 no loot gain context detected in recent_events or actions; rejected by durability gate"
  },
  {
    "field": "inventory_remove",
    "kind": "warn_missing_item",
    "value": "credits",
    "reason": "Inventory item 'credits' does not exist \u2014 ignoring removal request"
  }
]
```

### Suggested Actions

*(none)*

### Context Telemetry

- ruling: est=1742t trimmed=False
- narrate: est=6593t trimmed=False
- extract.scene: est=4270t trimmed=False attempts=1
- extract.state: est=4443t trimmed=False attempts=1
- extract.storytell: est=5465t trimmed=False attempts=1

### State After Turn

```json
{}
```


---
# Deterministic Signals

## Auto-Checker Failures
*(no failures)*

## Metrics
| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries | momentum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1739 | 4796 | 3681 | 4344 | 4792 | 0 | 0 | — |
| 2 | 1792 | 5130 | 4123 | 4446 | 5274 | 0 | 0 | — |
| 3 | 1785 | 5565 | 4222 | 4419 | 5369 | 0 | 0 | — |
| 4 | 1745 | 5940 | 4101 | 4380 | 5306 | 0 | 0 | — |
| 5 | 1704 | 6076 | 4073 | 4467 | 5464 | 0 | 0 | — |
| 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 6 | 1725 | 5828 | 4257 | 4450 | 5479 | 0 | 0 | — |
| 7 | 1763 | 6254 | 4254 | 4455 | 5429 | 0 | 0 | — |
| 8 | 1728 | 6230 | 4100 | 4310 | 5252 | 0 | 0 | — |
| 9 | 1730 | 6151 | 4113 | 4434 | 5282 | 0 | 0 | — |
| 10 | 1770 | 6310 | 4411 | 4548 | 5665 | 0 | 0 | — |
| 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 11 | 1754 | 6259 | 4409 | 4407 | 5593 | 0 | 0 | — |
| 12 | 1826 | 6758 | 4313 | 4402 | 5390 | 0 | 0 | — |
| 13 | 1742 | 6593 | 4270 | 4443 | 5465 | 0 | 0 | — |

**Scope fallback rate:** N/A (not captured in events.jsonl)

## Prompt Redundancy (cross-stream duplication)
Detected duplicated content blocks (>= 3 lines, each >= 60 chars) appearing in multiple streams. The judge should evaluate whether this duplication is intentional (e.g. the narration is correctly fed to all three extractors) or wasted tokens (e.g. the same PC bio rendered redundantly).

### Top overlaps across all turns

| Streams | Total duplicated blocks | Preview |
|---|---:|---|
| narrate + storytell | 6 | `- Marrow's Crossing is a market town at the confluence of tw / - Iron coin (credits) is the universal currency on the merch / - The road has been quieter than usual this season — fewer c` |
| narrate + scene | 1 | `A market town built around the confluence of two rivers. Cob / timber-framed buildings, and the constant sound of water fro / town square has a stone well and a statue of the founder. Mo` |
