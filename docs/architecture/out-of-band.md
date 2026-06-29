# Out-of-Band Pipelines

These run only at new-game time or are non-engine concerns. They are excluded from the eval-context region of the main architecture doc.

## Character Creation Pipeline

Triggered by `POST /new-game`. Always uses the Generate Seed pipeline (dynamic LLM generation) with optional player overrides.

```mermaid
flowchart LR
    FORM["New Game Form<br>──────────────────<br>pack_id<br>pc_name, pc_tagline, pc_stats<br>pc_hints, npc_hints<br>location_hints, arc_hints<br>free_form, npc_count"]

    subgraph CHECK["Hint Detection"]
        H["Build PlayerOverrides<br>  (pc_hints, npc_hints, location_hints,<br>  arc_hints, free_form, npc_count)<br>Check overrides.is_empty()"]
    end

    subgraph DYNAMIC["Dynamic Pack — prepare_seed() → narrate_seed()"]
        DS["1. prepare_seed() at temp 0.4 → SeedStateEnvelope<br>2. narrate_seed() at temp 0.9 → opening_narrative, actions<br>3. Assemble final SeedEnvelope<br>overrides injected if non-empty"]
    end

    INIT["init_save_dir(SAVE_DIR, seed)<br>Writes state.yaml<br>Clears chronicle.md + events.jsonl<br>_pack_source: pack ID"]

    FORM --> CHECK
    CHECK --> DYNAMIC
    DYNAMIC --> INIT
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
        G3["PlayerOverrides (optional)<br>  pc_hints, npc_hints<br>  location_hints, arc_hints<br>  free_form, npc_count"]
        G4["npc_name_pool (name locales)"]
        G5["engine_config.prepare_seed_temperature (0.4)<br>engine_config.narrate_temperature (0.9)<br>engine_config.max_llm_retries (1)"]
    end

    subgraph LLM_TWO_STEP["Two-step LLM pipeline"]
        direction TB
        PS["prepare_seed()<br>temp: 0.4<br>output: SeedStateEnvelope JSON"]:::llmNode
        NS["narrate_seed()<br>temp: 0.9<br>output: opening_narrative, actions, outcome_summary"]:::llmNode
        PS --> NS
    end

    subgraph OUT["Outputs — SeedEnvelope"]
        O1["seed_state: GameState<br>  pc (name, tagline, bio, stats)<br>  location (id, name, description)<br>  scene (world_state: list[WorldStateFact])<br>  compendium.npcs: dict[id] CompendiumEntry<br>    (presence='present' for in-scene NPCs,<br>     presence='known' otherwise)<br>  meta (model, setting_pack, turn=0,<br>       recent_beats: list[dict])"]:::outNode
        O2["arc: CampaignArc<br>  long_term_objective,<br>  threads[] (unified, with dormant flag),<br>  completed_threads[]"]:::outNode
        O3["opening_narrative: str<br>(prose intro shown before turn 1)"]:::outNode
        O4["actions: list[str]<br>(4 distinct, character-shaped,<br>scene-grounded choices)"]:::outNode
    end

    IN --> LLM_TWO_STEP
    LLM_TWO_STEP --> OUT
```

### Post-generation processing

After the LLM generates the SeedStateEnvelope, `prepare_seed()` in `seed.py` runs post-generation processing:
- Merges baseline world facts from `scenario.world_facts` with any existing world state facts from the seed
- Clears engine-managed `compendium_touch_order` from seeded compendium NPCs
- **Injects pack currency**: if `scenario.currency_id` is set and no inventory item with that ID exists, appends an `InventoryItem` with the pack's `starting_currency_amount`
- **Assigns NPC personalities**: iterates over all NPCs in `state_envelope.seed_state.compendium.npcs`; for any without a `personality` attribute, calls `ccya.personality.assign_personality()` using the NPC's `motivation` and `fear` fields; validates any LLM-provided personality ids via `validate_and_resolve()`; unknown ids fall back to `assign_personality()`

### Seed emotional framing contract

The seed prompt (`prepare_seed_system.j2`) enforces these requirements:

- **`arc_origin`**: 2–3 sentences in past tense answering "how did the PC end up here?" Seed-time field only, never regenerated. Surfaces in the sidebar.
- **NPC `relation` field**: Each opening NPC has a defined narrative job. One NPC is personally tied to the PC's motive or vulnerability; the other carries immediate external pressure from the world or conflict. The `relation` field encodes PC-facing relevance (e.g. "owes them a favor", "is their only contact here", "represents the institution pressing on them").
- **Compendium NPCs**: The seed also generates 2–3 NPCs in `compendium.npcs` (name, title, bio) who exist in the world but are not present in the opening scene. Their bios tie them to factions, locations, or world pressures, not to the immediate situation. These become discoverable characters during play.
- **Action guidance**: Each of the 4 choices is written from the PC's point of view, grounded in a present NPC, immediate risk, active thread, or character motive. They differ in emotional posture (confront, deflect, investigate, protect, exploit, withdraw, etc.) and avoid generic verbs.
- **`threads[]`**: Unified list (not split active/latent) where each thread has `{id, summary, urgency, scope, type}` and a `dormant` boolean flag managed by Record (formerly Storytell) via `thread_update`, not Python age rules. Threads have a `progress: list[str]` field — append-only log of progress updates set via `thread_update[].progress`, never replaced. Also includes `last_updated_turn: int | None` for urgency decay tracking.
- **Opening narrative**: The ~700-word opening prose weaves seed data naturally rather than listing it. World state facts are shown through effect (a checkpoint implying border closure, not stating it). NPC personal ties are revealed through action or dialogue, not exposition. Compendium NPCs not present in the scene are referenced naturally (a phone call, a rumor, a memory). Four distinct actions are grounded in present NPCs, immediate risks, active threads, or character motives.
- **Inventory**: 3–6 items appropriate to the opening scene and PC concept. Every item has a specific, proper name. Firearms paired with ammo. No exotic/legendary weapons at start.

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
