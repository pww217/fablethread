# ARCHITECTURE

CCYA is a local-LLM-backed text RPG engine. Every player turn drives a five-step
pipeline (Rules → Narrate → Scene Extract → State Extract → Progress Extract) with
a pure-Python validation+persist tail. Two additional LLM pipelines handle new-game
creation: **Character Creation** (static packs) and **Generate Seed** (dynamic packs).

---

## High-Level Overview

```mermaid
flowchart TD
    BROWSER["🌐 Browser<br>(HTMX + SSE)"]

    subgraph SERVER["server.py — FastAPI"]
        TURN["GET /turn<br>SSE EventSourceResponse"]
        NEWGAME["POST /new-game<br>+ /new-game/reroll"]
        PANELS["GET /panels/*<br>HTMX fragments"]
    end

    subgraph ENGINE["engine.py — run_turn()"]
        STEP0["Step 0<br>Rules / Intent (LLM)"]
        DICE["Dice Resolution<br>(Python)"]
        STEP1["Step 1<br>Narrate (LLM, streaming)"]
        STEP2A["Step 2a<br>Scene Extract (LLM)"]
        STEP2B["Step 2b<br>State Extract (LLM)"]
        STEP2C["Step 2c<br>Progress Extract (LLM)"]
        VALIDATE["Validate + Apply Delta<br>(Python)"]
    end

    subgraph SEED_ENGINE["engine.py — generate_seed()"]
        GS["Generate Seed (LLM)<br>dynamic packs only"]
    end

    subgraph CHAR_CREATION["server.py — /new-game"]
        CC["Character Creation<br>(form fields → static seed<br>or LLM-generated seed)"]
    end

    subgraph PERSISTENCE["saves/default/"]
        STATE["state.yaml<br>(canonical live state)"]
        CHRONICLE["chronicle.md<br>(narrative history)"]
        EVENTS["events.jsonl<br>(structured turn log)"]
    end

    subgraph LLM["Local LLM<br>(OpenAI-compatible API)"]
        LLM_HOST["host: config.yaml<br>model: config.yaml"]
    end

    BROWSER -- "user_input (GET /turn?input=...)" --> TURN
    TURN --> ENGINE
    NEWGAME --> CC
    CC -- "static seed" --> STATE
    CC -- "dynamic" --> SEED_ENGINE
    GS --> STATE
    ENGINE --> VALIDATE
    VALIDATE --> PERSISTENCE
    PERSISTENCE -- "load_state()<br>chronicle_tail<br>recent_turns" --> ENGINE
    ENGINE -- "SSE: narrative_token<br>phase / turn_complete" --> BROWSER
    STEP0 & STEP1 & STEP2A & STEP2B & STEP2C --> LLM
    GS --> LLM
    PANELS -- "load_state()" --> STATE
```

---

## Step 0 — Rules / Intent Classification

Classifies the player's action, determines whether a dice check is needed, and
identifies which state domains will be active — narrowing every downstream extractor.

```mermaid
flowchart LR
    subgraph IN["Inputs"]
        I1["state.pc<br>(name, stats, conditions)"]
        I2["state.location"]
        I3["state.scene.present_npcs"]
        I4["recent_turns[-2:]<br>(from chronicle)"]
        I5["user_input"]
    end

    subgraph LLM0["LLM — rules_system.j2 + rules_user.j2"]
        L0["temp: 0.2 · max_retries: 1<br>output: IntentEnvelope JSON"]
    end

    subgraph PYRES["Python — rules.resolve_check()"]
        P0["reads pc.stats[skill]<br>reads pc.conditions → cond_mod<br>rolls 2d6 + stat_mod + cond_mod − diff_mod<br>maps total → Band"]
    end

    subgraph OUT["Outputs"]
        O1["IntentEnvelope<br>  intent: str<br>  intent_verb: str<br>  target: str<br>  check.required: bool<br>  check.skill: SkillName<br>  check.difficulty: Difficulty<br>  scope.active_domains: list[str]<br>  scope.skip_domains: list[str]"]
        O2["RulesOutcome<br>  rolled: bool<br>  skill, stat_value, stat_mod<br>  diff_mod, cond_mod<br>  dice: list[int]<br>  final_total: int<br>  band: Band<br>  directive: str"]
    end

    IN --> LLM0
    LLM0 -- "IntentEnvelope" --> PYRES
    PYRES --> OUT
```

> **Key forward dependency:** `scope.active_domains` / `scope.skip_domains` flow into all
> three extraction streams. `rules_outcome.directive` shapes the narrator's creative latitude.

---

## Step 1 — Narrate (Streaming)

Generates the narrative prose the player reads. Tokens stream live to the browser via SSE.

```mermaid
flowchart LR
    subgraph IN["Inputs"]
        N1["state (full —<br>pc, location, scene,<br>inventory, quests, compendium)"]
        N2["chronicle_tail<br>(compressed history, ≤budget tokens)"]
        N3["recent_turns (last window_turns=6)"]
        N4["rules_outcome<br>(band, directive, dice summary)"]
        N5["pack_style (tone / prose guide)"]
        N6["npc_name_pool (cultural name list)"]
        N7["last_turn_failed<br>(precondition failures from prev turn)"]
        N8["recently_left NPCs"]
        N9["recent_narrative_tail<br>(last turn's narrative for continuity)"]
        N10["user_input"]
    end

    subgraph LLM1["LLM — narrate_system.j2 + narrate_user.j2"]
        NL["temp: 0.9 · streaming: yes<br>output: prose narrative (str)"]
    end

    subgraph OUT["Outputs"]
        NO1["narrative: str<br>(streamed as tokens → SSE<br>then joined + thinking-stripped)"]
        NO2["narr_metrics<br>  first_token_ms<br>  total_ms<br>  tokens_in / tokens_out"]
    end

    IN --> LLM1
    LLM1 --> OUT
```

> **Key forward dependency:** `narrative` is the primary content input for all three
> extraction streams below.

---

## Step 2a — Scene Extract

Extracts location changes, NPC presence, scene tags, and suggested actions from the narrative.

```mermaid
flowchart LR
    subgraph IN["Inputs"]
        S1["narrative (from Step 1)"]
        S2["state.pc (name, tagline, bio, stats)"]
        S3["state.location"]
        S4["state.scene.present_npcs"]
        S5["state.pc.conditions"]
        S6["known_characters<br>(compact: id+name, up to 10 LRU<br>from compendium)"]
        S7["rules_outcome"]
        S8["scope.active_domains<br>(from Step 0)"]
    end

    subgraph LLM2A["LLM — extract_scene_system.j2 + extract_scene_user.j2"]
        SL["temp: 0.4 · max_retries: 1<br>output: SceneExtractResult JSON"]
    end

    subgraph OUT["Outputs — SceneExtractResult"]
        O1["scene_tags: list[str]"]
        O2["scene_tagline: str (3–6 words for UI header)"]
        O3["location_change: LocationRef | None<br>  id, name, description"]
        O4["location_description: str | None"]
        O5["present_npcs: list[NpcRef]<br>  id, name, title, notes, bio"]
        O6["actions: list[str] (suggested next actions)"]
        O7["outcome_summary: str"]
    end

    IN --> LLM2A
    LLM2A --> OUT
```

> **Key forward dependency:** `location_change` and `present_npcs` are passed into
> Steps 2b and 2c.

---

## Step 2b — State Extract

Extracts inventory changes and player condition mutations from the narrative.

```mermaid
flowchart LR
    subgraph IN["Inputs"]
        S1["narrative (from Step 1)"]
        S2["state.pc (name, bio, stats, conditions)"]
        S3["state.location"]
        S4["state.inventory"]
        S5["rules_outcome"]
        S6["scope.active_domains (from Step 0)"]
        S7["engine_expired_conditions<br>(TTL-expired, engine pre-removed)"]
        S8["scene_result.location_change<br>(from Step 2a)"]
        S9["scene_result.present_npcs<br>(from Step 2a)"]
    end

    subgraph LLM2B["LLM — extract_state_system.j2 + extract_state_user.j2"]
        SL["temp: 0.4 · max_retries: 1<br>output: StateExtractResult JSON"]
    end

    subgraph OUT["Outputs — StateExtractResult"]
        O1["inventory_add: list[InventoryItem]<br>  id, name, notes, amount"]
        O2["inventory_remove: list[InventoryRemove]<br>  id, amount (None = full stack)"]
        O3["inventory_update: list[InventoryUpdate]<br>  id, name?, notes?"]
        O4["pc_condition_add: list[ConditionAdd]<br>  id, label, description"]
        O5["pc_condition_remove: list[ConditionRemove]<br>  id"]
        O6["failed: list[str]<br>  (unmet preconditions this turn)"]
    end

    IN --> LLM2B
    LLM2B --> OUT
```

> **Key forward dependency:** `inventory_add` / `inventory_remove` flow into Step 2c
> for quest item linkage.

---

## Step 2c — Progress Extract

Extracts quest updates, recent events, and durable NPC compendium changes.

```mermaid
flowchart LR
    subgraph IN["Inputs"]
        S1["narrative (from Step 1)"]
        S2["state.pc (name, bio, stats)"]
        S3["state.scene.recent_events"]
        S4["state.scene.world_state"]
        S5["active_quests (status=active only)"]
        S6["known_characters<br>(full: id, name, title, bio_preview,<br>up to 10 LRU from compendium)"]
        S7["rules_outcome"]
        S8["scope.active_domains (from Step 0)"]
        S9["scene_result.present_npcs<br>(from Step 2a)"]
        S10["state_result.inventory_add<br>state_result.inventory_remove<br>(from Step 2b — quest item linkage)"]
    end

    subgraph LLM2C["LLM — extract_progress_system.j2 + extract_progress_user.j2"]
        SL["temp: 0.4 · max_retries: 1<br>output: ProgressExtractResult JSON"]
    end

    subgraph OUT["Outputs — ProgressExtractResult"]
        O1["quest_updates: list[QuestUpdate]<br>  id, title, status,<br>  objectives[]: index, description,<br>  done, failed"]
        O2["recent_events_add: list[str]"]
        O3["recent_events_update: list[RecentEventUpdate]<br>  old, new"]
        O4["recent_events_remove: list[str]"]
        O5["compendium_npc_update: list[CompendiumNpcUpdate]<br>  id, name?, title?, bio?"]
    end

    IN --> LLM2C
    LLM2C --> OUT
```

---

## Delta Merge → Validate → Apply

The three extraction results merge into a single `StateDelta`, then validate and apply.

```mermaid
flowchart TD
    SR1["SceneExtractResult<br>(Step 2a)"]
    SR2["StateExtractResult<br>(Step 2b)"]
    SR3["ProgressExtractResult<br>(Step 2c)"]

    MERGE["StateDelta<br>──────────────────<br>scene_tags, scene_tagline<br>location_change, location_description<br>present_npcs<br>inventory_add / remove / update<br>pc_condition_add / remove<br>quest_updates<br>recent_events_add / update / remove<br>compendium_npc_update"]

    VALIDATE["_validate()<br>Check inventory_remove IDs exist<br>→ rejections: list[dict]"]

    APPLY["apply_delta() — mutates state in-place<br>──────────────────────────────<br>inventory add / remove / update<br>pc.conditions add / remove (+ added_turn)<br>location (id, name, description)<br>scene.present_npcs<br>scene.tagline<br>scene.recent_events (ring buffer, max 15)<br>scene.world_state<br>quests (create-or-update)<br>compendium.npcs (upsert)<br>meta.compendium_touch_order (LRU)<br>meta.turn += 1"]

    DIFF["summarize_changes()<br>diffs pre vs post state<br>→ changes{inventory, player, facts, quests}"]

    SR1 --> MERGE
    SR2 --> MERGE
    SR3 --> MERGE
    MERGE --> VALIDATE
    VALIDATE -- "valid" --> APPLY
    VALIDATE -- "rejections" --> DIFF
    APPLY --> DIFF
```

---

## Persist

Atomic writes to disk. No LLM calls.

```mermaid
flowchart LR
    subgraph IN["Inputs"]
        P1["state (post-apply)"]
        P2["event dict<br>(turn, input, applied, rejected,<br>actions, scene_tags, rules,<br>narrate/extract metrics,<br>changes, failed)"]
        P3["narrative: str"]
        P4["turn number"]
    end

    subgraph WRITES["saves/default/"]
        W1["events.jsonl<br>append — structured event log"]
        W2["state.yaml<br>atomic overwrite — canonical live state"]
        W3["chronicle.md<br>append — '## Turn N — input\n\nnarrative'"]
    end

    READBACK["Feeds Steps 0 & 1 on the next turn<br>via load_state(), load_chronicle_tail(),<br>load_recent_chronicle_turns()"]

    IN --> W1
    IN --> W2
    IN --> W3
    W3 --> READBACK
    W2 --> READBACK
```

---

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

---

## Generate Seed Pipeline (Dynamic Packs Only)

Called by `POST /new-game` and `POST /new-game/reroll`. Generates a complete
starting game state (PC, NPCs, location, quests, opening narrative) from the pack
manifest and optional player overrides.

```mermaid
flowchart LR
    subgraph IN["Inputs"]
        G1["pack.manifest<br>(world rules, tone, setting)"]
        G2["pack.style_text"]
        G3["PlayerOverrides (optional)<br>  pc_hints, npc_hints<br>  location_hints, quest_hints<br>  free_form, npc_count"]
        G4["npc_name_pool (name locales)"]
        G5["engine_config.generate_seed_temperature (0.9)<br>engine_config.generate_seed_max_retries (1)"]
    end

    subgraph LLM_GS["LLM — seed_system.j2 + seed_user.j2"]
        GL["temp: 0.9<br>output: SeedEnvelope JSON"]
    end

    subgraph OUT["Outputs — SeedEnvelope"]
        O1["seed_state: GameState<br>  pc (name, tagline, bio, stats)<br>  location (id, name, description)<br>  scene (present_npcs, recent_events)<br>  inventory: list[InventoryItem]<br>  quests: list[Quest]<br>  compendium.npcs: list[NpcRef]<br>  meta (model, setting_pack, turn=0)"]
        O2["opening_narrative: str<br>(prose intro shown before turn 1)"]
        O3["actions: list[str]<br>(suggested first player moves)"]
    end

    IN --> LLM_GS
    LLM_GS --> OUT
```

---

## Cross-Pipeline Data Flow

```mermaid
flowchart TD
    STATE["state.yaml"]
    CHRONICLE["chronicle.md"]
    EVENTS["events.jsonl"]

    STATE -- "load_state()" --> STEP0["Step 0<br>Rules / Intent"]
    CHRONICLE -- "chronicle_tail<br>recent_turns" --> STEP1["Step 1<br>Narrate"]
    STATE -- "pc, inventory,<br>quests, compendium" --> STEP1
    STEP0 -- "IntentEnvelope<br>RulesOutcome" --> STEP1
    STEP1 -- "narrative: str" --> STEP2A["Step 2a<br>Scene"]
    STEP0 -- "scope<br>rules_outcome" --> STEP2A
    STEP2A -- "location_change<br>present_npcs" --> STEP2B["Step 2b<br>State"]
    STEP1 -- "narrative" --> STEP2B
    STEP0 -- "scope<br>rules_outcome" --> STEP2B
    STEP2B -- "inventory delta" --> STEP2C["Step 2c<br>Progress"]
    STEP2A -- "present_npcs" --> STEP2C
    STEP1 -- "narrative" --> STEP2C
    STEP0 -- "scope<br>rules_outcome" --> STEP2C
    STEP2A & STEP2B & STEP2C -- "merge" --> DELTA["StateDelta"]
    DELTA -- "validate + apply" --> STATE
    DELTA -- "event record" --> EVENTS
    DELTA -- "narrative" --> CHRONICLE
```
