# Engine Design Reference (EVAL_CONTEXT from ARCHITECTURE.md)

---

# ENGINE DESIGN REFERENCE (read this first — it is what the engine is supposed to do)

The following is extracted from the project's architecture subdocuments under docs/architecture/. It defines the 5-pipeline engine you are judging. Use it to understand which pipeline owns which mechanic, where data flows, and what the design intent is. When you find something the implementation does that contradicts this design, call it out as a mechanical failure.

## OVERVIEW



CCYA is a local-LLM-backed text RPG engine. Every player turn drives a five-step
pipeline (Rules → Narrate → Scene Extract → State Extract → Storytell) with
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
    PERSISTENCE -- "load_state() (incl. prior_history)<br>load_last_narration() (→ recent_turns)" --> ENGINE
```

## Pipeline Quick Reference

| Step | Docs | When it runs | Key inputs | Key outputs | Mechanics it owns |
|---|---|---|---|---|---|
| **Step 0 — Ruling/Intent** | [step0-ruling](./step0-ruling.md) | Every turn (always) | `state.pc`, `state.location`, `recent_turns[-1:]`, `user_input` | `IntentEnvelope`, `RulesOutcome` | Intent classification, impossibility check, scene motion determination, dice roll resolution (1d12 + stat + cond − diff → band), difficulty selection, anti-declare-outcome enforcement. When `impossible=true`, no roll occurs and Python synthesizes a `fail` outcome. |
| **Step 1 — Narrate** | [step1-narrate](./step1-narrate.md) | Every turn (always, streamed) | Full `state`, `prior_history` (last 20 bullets, all but last rendered), `recent_turns[-1:]`, `pacing_context`, `pending_gm_beat`, `npc_roster` (from build_npc_roster()), `world_factions/locations` | `narrative` (prose) | Prose generation, dice-band binding, GM-beat consumption. Scene motion shaped by `PacingContext.outcome_hint`; impossible actions narrated as natural failures. |
| **Step 2a — Scene Extract** | [step2a-scene](./step2a-scene.md) | Every turn (always) | `narrative`, `state.pc/location`, `npc_roster` (from build_npc_roster()), conditions, compendium entries | `SceneExtractResult`: scene_tags, tagline, location_change, compendium_npc_update | NPC presence, location changes, scene tags, durable NPC compendium identity. |
| **Step 2b — State Extract** | [step2b-state](./step2b-state.md) | Every turn (always) | `narrative`, `state.pc/location/inventory`, conditions | `StateExtractResult`: inventory_add/remove/update, pc_condition_add/remove | Inventory delta accuracy, condition lifecycle. |
| **Step 2c — Storytell** | [step2c-storytell](./step2c-storytell.md) | Every turn (always) | `narrative`, `_ExtractionContext` (comp_this_turn, location, inventory, conditions), pacing_context, arc.threads[], recent_turns[-10:], band, npc_roster (from build_npc_roster()), recent_beats | `StorytellerResult`: thread_update/goal_update/arc_resolve/resolve/add, gm_beat, actions, outcome_summary | Storyteller-managed thread lifecycle, arc resolution, beat disposition inference, durable history events. |

After Step 2c: results merge into a `StateDelta`, the validator checks constraints
(e.g. `inventory_remove` IDs exist), `apply_delta()` mutates state in-place, and the
turn is persisted. The next turn's Step 0 reads the new `state.yaml` plus `events.jsonl`.

## Subsystem Docs

| Subsystem | Doc | What it covers |
|---|---|---|
| **Step 0 — Ruling** | [step0-ruling](./step0-ruling.md) | Intent classification, dice resolution flowchart, pacing context computation |
| **Step 1 — Narrate** | [step1-narrate](./step1-narrate.md) | Streaming narration pipeline with all context inputs |
| **Step 2a — Scene Extract** | [step2a-scene](./step2a-scene.md) | Location changes, NPC presence, scene tags |
| **Step 2b — State Extract** | [step2b-state](./step2b-state.md) | Inventory and condition extraction |
| **Step 2c — Storytell** | [step2c-storytell](./step2c-storytell.md) | Pipeline mechanics, GM beat lifecycle, campaign arc system, thread lifecycle mechanics |
| **Delta → Validate → Apply** | [delta-validate](./delta-validate.md) | StateMerge schema, validation rules, apply_delta mutations |
| **Persist** | [persist](./persist.md) | Atomic writes (events.jsonl, state.yaml, chronicle.md), readback |
| **Cross-Pipeline Data Flow** | [cross-pipeline](./cross-pipeline.md) | Full inter-step data flow diagram |
| **Out-of-Band Pipelines** | [out-of-band](./out-of-band.md) | Character Creation pipeline, Generate Seed pipeline, turn viewer status colors |
| **Narration UI** | [narration-ui](./narration-ui.md) | Main game interface: SSE streaming, HTMX sidebar refresh, Alpine.js state machine |
| **Turn Viewer UI** | [turn-viewer-ui](./turn-viewer-ui.md) | Pipeline debug UI: turn cards, stage inspector, diff panel, live updates |
| **Eval Harness** | [eval-harness](./eval-harness.md) | Scenario runner, LLM judges, auto-checkers, REPORT.md generation |

## Key Models Glossary

### Core Result Types

- **IntentEnvelope**: `intent`, `intent_verb`, `target`, `check.required`, `check.skill`, `check.difficulty`, `impossible`, `impossible_reason`, `scene_motion`
- **RulesOutcome**: `rolled`, `skill`, `difficulty`, `stat_value`, `stat_mod`, `diff_mod`, `cond_mod`, `dice`, `raw_total`, `final_total`, `band`, `directive`, `intent`, `intent_verb`, `impossible`, `impossible_reason`
- **SceneExtractResult**: `scene_tags`, `scene_tagline`, `location_change`, `compendium_npc_update`
- **StateExtractResult**: `inventory_add/remove/update`, `pc_condition_add/remove`
- **StorytellerResult**: `thread_update` (list[ThreadUpdate]), `goal_update` (str | None, applied directly to arc dict), `arc_resolve` (ArcResolution | None), `thread_resolve` (with outcome sentence + promote_to_world_state flag), `thread_add`, `gm_beat`, `actions`, `outcome_summary`
- **SeedEnvelope**: `seed_state: GameState`, `opening_narrative`, `actions`, `arc: CampaignArc` (includes `goal_context` — UI-only, not rendered in prompts; unified `threads[]` with `progress: list[ProgressEntry]`, `completed_threads[]`)

  The seed owns first-turn emotional framing, not just world and arc scaffolding. It generates `goal_context` (character-specific stake), NPC `relation` fields (narrative job relative to PC), and action text written from the PC's voice and scene pressure — ensuring the opening feels personal and motivated from the start.

### PacingContext (see [step0-ruling](./step0-ruling.md#pacing-context))

### GMBeat (see [step2c-storytell](./step2c-storytell.md#gm-beat))

### CampaignArc (see [step2c-storytell](./step2c-storytell.md#campaign-arc-system))

### StateDelta (see [delta-validate](./delta-validate.md))

Merges all three extraction results. Contains `scene_tags`, `location_change`, `compendium_npc_update` (NPC changes), `thread_update/arc_resolve/thread_resolve/thread_add`, `inventory_add/remove/update`, `pc_condition_add/remove`. Note: `gm_beat` is NOT in StateDelta — written directly to `state.meta.pending_gm_beat`.

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
    CHRONICLE -- "recent_turns<br>(load_last_narration())" --> STEP1["Step 1<br>Narrate"]:::stageNarrate
    STATE -- "pc, inventory, compendium,<br>prior_history (state.yaml)" --> STEP1
    STEP0 -- "IntentEnvelope<br>RulesOutcome" --> STEP1
    STEP1 -- "narrative: str" --> STEP2A["Step 2a<br>Scene"]:::stageScene
    STEP2A -- "location_change<br>npc_roster" --> STEP2B["Step 2b<br>State"]:::stageState
    STEP1 -- "narrative" --> STEP2B
    STEP2A -- "location_change<br>npc_roster" --> STEP2C["Step 2c<br>Storytell"]:::stageProgress
    STEP1 -- "narrative" --> STEP2C
    STEP2A & STEP2B & STEP2C -- "merge" --> DELTA["StateDelta"]:::mergeNode
    DELTA -- "validate + apply" --> STATE
    DELTA -- "event record" --> EVENTS
    DELTA -- "narrative" --> CHRONICLE
    STEP2C -- "thread_update/goal_update/arc_resolve/resolve/add<br>gm_beat" --> STATE
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

    MERGE["StateDelta<br>──────────────────<br>scene_tags, scene_tagline<br>location_change, location_description<br>compendium_npc_update (NPC changes)<br>arc_update (CampaignArc with threads[], completed_threads[])<br>inventory_add / remove / update<br>pc_condition_add / remove<br><br>(gm_beat NOT in StateDelta —<br>written directly to state.meta.pending_gm_beat)"]:::mergeNode

    VALIDATE["_validate()<br>Check inventory_remove IDs exist<br>→ rejections: list[dict]"]:::pyNode

    APPLY["apply_delta() — mutates state in-place (via delta_builder.py)<br>──────────────────────────────<br>inventory add / remove / update with dedup<br>pc.conditions add / remove (+ added_turn, TTL tracking)<br>location (id, name, description)<br>scene.tagline<br>compendium.npcs upsert (presence='present'→'known' on location change)<br>meta.compendium_touch_order (LRU update)<br><br>_merge_arc_update() — merges CampaignArc into state['arc']<br>──────────────────────<br>threads[]: replaced with arc_update.threads<br>completed_threads[]: replaced with arc_update.completed_threads<br><br>goal_update() — direct dict assignment (NOT through _merge_arc_update)<br>──────────────────────<br>state['arc']['visible_goal'] = storyteller_result.goal_update<br>(bypasses _merge_arc_update because that function replaces<br> threads[] unconditionally — direct assignment is safer)<br><br>(Thread lifecycle managed by storyteller via thread_update/thread_resolve/thread_add;<br> arc_update is set in delta only when thread ops fire — NOT every turn.<br> goal_update fires independently of arc_update.)"]:::pyNode

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
    SSR["Server renders index.html via Jinja2<br>────────────────────────<br>state (state.yaml)<br>history (events.jsonl, last N)<br>last_actions · opening · opening_actions<br>opening_outcome_summary<br>has_narrative · pack_name<br>character_creation_enabled · css_v"]:::ssr

    UI["Browser — Alpine.js app-shell<br>x-data=&quot;game()&quot;"]:::alpine

    SUBMIT["submitTurn()<br>EventSource('GET /turn?input=...')"]:::alpine

    subgraph STREAM["SSE — run_turn() pipeline"]
        TOK["event: narrative_token<br>{ chunk: str }"]:::sse
        PHASE["event: phase<br>{ phase_name, ... }"]:::sse
        DONE["event: turn_complete<br>{ turn, trace_id, narrative, actions,<br>  scene_tags, game_over, rejected,<br>  errors, diff, changes, change_lines,<br>  state, metrics, ruling, ts }"]:::sse
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
    - `phase` — pipeline phase progress (ruling_start, narrate_start, narrate_first_token, narrate_done, extract_start, extract_done, sanitize_start, sanitize_done, persist)
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
- **Reset button** in sidebar footer: restores viewport-aware defaults (left 320px, right 280px) on click
- **Ultrawide override** (≥2561px viewport): `--sidebar-w: min(512px, 38vw)` — sidebar defaults to 2x standard width. Sidebar text scaled ~25% smaller via explicit `.sidebar-card-header`, `.stat-row`, `.npc-notes-inline`, `.inventory-item`, etc. overrides in the ultrawide media query.

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

- **`app.src.css`** — Tailwind + custom styles split by region:
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
- **Fluid typography**: 3-tier `@media` breakpoints set `html { font-size: clamp(...) }`:
  | Viewport | Font size clamp | Applicable to |
  |---|---|---|
  | 769–1400px | `clamp(15px, 1vw, 17px)` | Tablet/small desktop |
  | 1401–2560px | `clamp(22px, 1.56vw, 26px)` | Standard desktop |
  | ≥2561px | `clamp(24px, 1.5vw, 27px)` | Ultrawide (also sets `--sidebar-w: min(512px, 38vw)`) |
  - Font sizes throughout are in `rem` units, scaling proportionally with the base.
- **Location panel fix**: Hardcoded `px` font sizes replaced with `rem` units to respect fluid base.
- Compiled to **`app.css`** with cache-busting via `css_v` query param

## Server Entry Point

`routes.py:57` — `GET /` handler assembles template context from `state.yaml`, `events.jsonl`, pack manifest, and engine config, then renders `ccya/templates/index.html`.

---


## out-of-band



These run only at new-game time or are non-engine concerns. They are excluded from the eval-context region of the main architecture doc.

## Character Creation Pipeline

Triggered by `POST /new-game`. All packs use the Generate Seed pipeline (dynamic). Static packs with pre-built seed_state.yaml exist but are not used by new_game.

```mermaid
flowchart LR
    FORM["New Game Form<br>──────────────────<br>pack_id<br>pc_name, pc_tagline, pc_stats<br>pc_hints, npc_hints<br>location_hints, arc_hints<br>free_form, npc_count"]

    subgraph DYNAMIC["Dynamic Pack — generate_seed()"]
        DS["Build PlayerOverrides<br>  (pc_hints, npc_hints, location_hints,<br>  arc_hints, free_form, npc_count)<br>Pass to generate_seed() LLM pipeline"]
    end

    INIT["init_save_dir(SAVE_DIR, seed)<br>Writes state.yaml<br>Clears chronicle.md + events.jsonl"]

    OPENING["envelope.opening_narrative<br>envelope.actions (suggested first moves)"]

    FORM --> DYNAMIC
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
        G3["PlayerOverrides (optional)<br>  pc_hints, npc_hints<br>  location_hints, arc_hints<br>  free_form, npc_count"]
        G4["npc_name_pool (name locales)"]
        G5["engine_config.generate_seed_temperature (0.9)<br>engine_config.max_llm_retries (1)"]
    end

    subgraph LLM_GS["LLM — generate_seed_system.j2 + generate_seed_user.j2"]
        GL["temp: 0.9<br>output: SeedEnvelope JSON"]:::llmNode
    end

    subgraph OUT["Outputs — SeedEnvelope"]
        O1["seed_state: GameState<br>  pc (name, tagline, bio, stats)<br>  location (id, name, description)<br>  scene (world_state: list[WorldStateFact])<br>  inventory: list[InventoryItem]<br>  compendium.npcs: dict[id] CompendiumEntry<br>    (presence='present' for in-scene NPCs,<br>     presence='known' otherwise)<br>  meta (model, setting_pack, turn=0,<br>       recent_beats: list[dict])"]:::outNode
        O2["arc: CampaignArc<br>  visible_goal, goal_context (personal stakes),<br>  threads[] (unified, with active flag),<br>  completed_threads[]"]:::outNode
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
- **`threads[]`**: Unified list (not split active/latent) where each thread has `{id, summary, urgency, scope}` and an `active` boolean flag managed by the storyteller via `thread_update`, not Python age rules. Threads have a `progress: list[str]` field — append-only log of progress updates set via `thread_update[].progress`, never replaced. Also includes `last_updated_turn: int | None` for urgency decay tracking.

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

    READBACK["Feeds Steps 0–2c on the next turn<br>via load_state(), load_last_narration() for recent_turns,<br>prior_history bullets in state.yaml"]:::pyNode

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
        I3["recent_turns[-1:]<br>(last turn's full narrative from chronicle.md<br>via load_last_narration();<br>ruling user prompt)"]
        I4["user_input"]
    end

    subgraph LLM0["LLM — ruling_system.j2 + ruling_user.j2"]
        L0["temp: 0.2 · max_retries: 1<br>output: IntentEnvelope JSON<br>(intent, impossible, scene_motion, check)"]:::llmNode
    end

    subgraph PYRES["Python — impossible check + rules.resolve_check()"]
        P0["if impossible=true:<br>  synthesize fail outcome<br>  skip roll, apply momentum<br>else:<br>  roll 1d12 + stat_mod + cond_mod − diff_mod<br>  map total → Band"]:::pyNode
    end

    subgraph OUT["Outputs"]
        O1["IntentEnvelope<br>  intent: str<br>  intent_verb: str<br>  target: str<br>  impossible: bool<br>  impossible_reason: str<br>  scene_motion: hold|advance|transition<br>  check.required: bool<br>  check.skill: SkillName<br>  check.difficulty: Difficulty"]:::outNode
        O2["RulesOutcome<br>  rolled: bool<br>  skill, difficulty, stat_value, stat_mod<br>  diff_mod, cond_mod<br>  dice: list[int]<br>  raw_total, final_total: int<br>  band: Band<br>  directive: str<br>  intent, intent_verb: str<br>  impossible: bool<br>  impossible_reason: str"]:::outNode
    end

    IN --> LLM0
    LLM0 -- "IntentEnvelope" --> PYRES
    PYRES --> OUT
```

## Impossibility check

The ruling LLM evaluates whether the described action is impossible given the character's state, inventory, and scene. An action is impossible when:

- It requires an item the character does not have (firing a gun with no ammo, using a key never acquired)
- It requires a capability contradicted by active conditions (climbing with a broken leg, sneaking while armored and noisy)
- It acts on something not present in the scene (targeting an NPC who is not here, opening a door that doesn't exist)

When `impossible=true`: Python sets `check.required=False`, synthesizes a `RulesOutcome` with `band="fail"` and `rolled=False`, applies momentum, and skips the dice roll entirely. The narrator renders the impossible fact and narrates the natural failure.

## Scene motion

The ruling LLM also determines how the scene should progress: `"hold"` (scene continues at current pace), `"advance"` (something significant happens/resolves), or `"transition"` (player is leaving, write the arrival). This feeds into `_compute_pacing_context()` which produces `outcome_hint` for the narrator.

## Key forward dependency

`rules_outcome` feeds into `_compute_pacing_context()` which produces the single authoritative `PacingContext` struct passed to both Narrator and Storytell pipeline.

## Pacing Context

All pacing signals are collapsed into one Python-computed struct (`PacingContext`) passed to both the Narrator and Storytell pipeline. This replaces six independent fields (`narration_directive`, `deescalate`, `narrative_velocity`, `beat_disposition` output, `quest_threshold_directive`, and stale momentum-derived signals). The narrator receives `outcome_hint` (scene motion); Storytell receives the full struct including `directive`.

### Struct definition

```
PacingContext:
  directive: str           # "" | "Breathe" | "Scene Imperative" | "Overwhelm" | "Pressure" | "Tension" | "Scene Pressure" (may include "; Resolve a Threat" secondary when beat_locked); used by Storytell pipeline
  outcome_hint: str | None # "hold" | "advance" | "transition" — narrator's primary scene motion instruction
  beat_locked: bool        # True: consecutive pressure threshold reached or momentum at floor — enables floor relief injection (when not from momentum) and may append "; Resolve a Threat" to directive (except when directive="Breathe")
  gate: str                # "block_escalate" | "allow" (controls thread_add); set independently from beat_locked via deescalate >= 0.5
  summary: str             # human-readable log string, never sent to LLM
```

`beat_locked: True` fires when either `consecutive_pressure_turns >= config.consecutive_pressure_threshold` OR `momentum <= config.momentum_floor`. When locked, `"Resolve a Threat"` is appended to the directive via semicolon (except when directive="Breathe"). The `gate` field prevents Progress from adding new threads during de-escalation windows.

### Computation

`_compute_pacing_context()` in `engine/turn.py` consolidates pacing computation (replacing the former scattered functions: `_compute_narration_directive`, `_compute_narrative_velocity`, `_check_floor_relief`). It takes inputs (`momentum`, `consecutive_pressure_turns` from state meta, `arc.threads[] scope=scene urgency counts`) and returns a single struct with directive derived from a priority stack. It also computes `outcome_hint` from the ruling LLM's `scene_motion` and PacingContext escalation signals: ruling `scene_motion` takes priority (`transition` > `advance` > fallback), then `impossible=true` forces `advance`, then Python escalation signals (`beat_locked`, Overwhelm/Pressure with urgent threads) produce `advance`, defaulting to `hold`.

```mermaid
flowchart TD
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef decision fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    classDef output fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6

    V["narrative_velocity"]:::pyNode
    T["arc.threads[] scope=scene<br>(urgency counts)"]:::pyNode
    SA["effective_scene_age<br>= scene_age + 2 if combat"]:::pyNode

    V --> D1{"velocity < -0.3<br>(deescalation)"}:::decision
    D1 -- yes --> B1["directive='Breathe'"]:::output
    D1 -- no --> D2{"effective_age ≥ 5?"}:::decision
    D2 -- yes --> B2["directive='Scene Imperative'<br>(short-circuits all)"]:::output
    D2 -- no --> D3{"≥ 3 urgent<br>threads?"}:::decision
    D3 -- yes --> B3["directive='Overwhelm'"]:::output
    D3 -- no --> D4{"1-2 urgent<br>threads?"}:::decision
    D4 -- yes --> B4["directive='Pressure'"]:::output
    D4 -- no --> D5{"background urgency<br>threads only?"}:::decision
    D5 -- yes --> B5["directive='Tension'"]:::output
    D5 -- no --> D6["empty directive"]

    SEC2["Scene Pressure (secondary,<br>3 ≤ effective_age < 5)"]

    FINAL["PacingContext<br>directive · outcome_hint · beat_locked · gate"]:::output

    B2 -. "beat_locked appends<br>'; Resolve a Threat'" .-> FINAL
    B3 -. "beat_locked appends<br>'; Resolve a Threat'" .-> FINAL
    B4 -. "beat_locked appends<br>'; Resolve a Threat'" .-> FINAL
    B5 -. "beat_locked appends<br>'; Resolve a Threat'" .-> FINAL
    D6 -. "beat_locked →<br>'; Resolve a Threat'" .-> FINAL

    SEC2 -. "appended to directive" .-> FINAL

    style B2 fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6
```

Priority order (highest to lowest): **Breathe > Scene Imperative > Overwhelm > Pressure > Tension > Scene Pressure**. The `beat_locked` flag fires when either consecutive pressure threshold or momentum floor is reached — `"Resolve a Threat"` is appended to the directive (except when directive="Breathe") and `outcome_hint` is set to `"advance"`. Floor relief injection only fires when beat_locked stems from consecutive_pressure, not from momentum_floor. The gate is NOT affected by beat_locked (set independently by deescalate ≥ 0.5).

**Breathe secondary guard:** The Breathe directive has an additional check beyond velocity: if urgent scene-scoped threads exist, Breathe is NOT emitted even if `narrative_velocity < -0.3`. Low velocity during unresolved tension (tactical avoidance, stealth) does not trigger de-escalation. Once urgent threads resolve, Breathe fires on the next low-velocity turn.

#### Age computation

`_compute_ages(state)` returns only `{"scene_age": scene_age}` — location_age and combat_age removed in Phase 03 pacing overhaul. The ruling phase pre-computes `effective_scene_age = scene_age + 2` when `"combat"` is in scene tags, stored in `ctx._ages["effective_scene_age"]`. This single-age signal drives all directive thresholds:
- Scene Imperative (≥5 effective age): high-priority directive forcing story advancement
- Scene Pressure (3 ≤ effective_age < 5): secondary append to wind down or shift focus

### Wiring

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
    NARRATE_TMPL["narrate_user.j2<br>pacing_context.outcome_hint"]:::prompt

    TURN --> PIPELINE --> EXTRACT_FN --> USER_TMPL
    USER_TMPL --> SYS_TMPL --> EXTRACTOR["Storytell LLM"]:::extractor
    TURN -. "also passed to" .-> NARRATE_TMPL
```

1. **Computed** once in `run_turn()` via `_compute_pacing_context()`.
2. **Passed through** `_run_extraction_pipeline()` → both `_narrate_messages()` and `_storytell_messages()`.
3. **Narrator template** (`narrate_user.j2`) renders `outcome_hint` (scene motion: hold/advance/transition) with value-specific guidance. No Jinja2 pacing computation remains — all pacing computed by Python.
4. **Storytell template** ((`storytell_system.j2` + `user.j2`)) receives the full struct; guidance maps each directive to appropriate thread/beat actions:

| Directive | Thread action | Gate |
|-----------|---------------|-------|
| **"Breathe"** (de-escalation, velocity < -0.3) | Do NOT add new threads. Allow existing scene threads to persist without escalation. | `block_escalate` (set by deescalate ≥ 0.5; beat_locked does NOT force-close gate) |
| **"Scene Imperative"** (effective_age ≥ 5) | Story must advance — introduce new development forcing resolution or movement; do not linger | Varies by context |
| **"Overwhelm"** (3+ urgent threads) | May add scene-scoped threads if gate allows; emit pressure/escalation beat | `allow` |
| **"Pressure"** (1-2 urgent threads) | Advance relevant scene/arc threads. Add new thread only if gate permits. | Varies by context |
| **"Tension"** (background urgency only) | Do NOT add pressures unless concrete threat emerges; prefer advancing existing threads | Allow |
| **"Scene Pressure"** (3 ≤ effective_age < 5, secondary append) | Begin winding down or introduce reason to shift focus: development elsewhere, closing window | Varies by context |
| **"" (empty)** | No action required beyond normal aging of silent threads. | Allow |

**Note:** Directives may include secondary modifiers joined by semicolons (e.g., "Pressure; Resolve a Threat" when beat_locked). The primary directive drives thread/beat logic; the secondary (`; Resolve a Threat`) acts as thematic guidance for beat type selection. "Resolve a Threat" never appears as a standalone primary directive — it is only appended by the `beat_locked` mechanism (except Breathe, which never receives this append regardless of beat_locked state).

### Consecutive pressure counter

`state["meta"]["consecutive_pressure_turns"]` tracks how many consecutive turns have had pressure-type storyteller beats. Re-keyed from directive tracking (which never fired — Pressure/Overwhelm directives were unreachable) to beat-type tracking:

- **Increments** when `storyteller_result.gm_beat.type` is `"pressure"`, `"escalation"`, or `"complication"`.
- **Resets to 0** on any other beat type, null beat, or missing storyteller output.

When this counter reaches `config.consecutive_pressure_threshold` (default 3), it triggers `beat_locked` alongside the momentum floor fallback (`momentum <= -3`). `beat_locked` appends `"; Resolve a Threat"` to the directive (except when directive="Breathe") and enables floor relief injection (when not from momentum).

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
        N1["state (full —<br>pc, location, scene,<br>inventory, compendium)"]
        N2["prior_history<br>(last 20 incremental history bullets, all but last rendered as bullets)"]
        N3["recent_turns[-1:]<br>(single most recent turn as full text)"]
        N4["rules_outcome<br>(band, directive, impossible, dice summary)"]:::xstream
        N6["npc_name_pool (cultural name list)"]
        N7["npc_roster<br>(from build_npc_roster(comp),<br>  presence field: present/nearby/known)"]
        N9["world_factions<br>(immutable trace)"]:::xstream
        N10["pending_gm_beat<br>(type · surface_as metadata)"]
        N11["pacing_context<br>(outcome_hint)<br>from _compute_pacing_context()"]:::xstream
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

- **`goal_context`**: A seed-time field (2–3 sentences) explaining why `visible_goal` matters to the character specifically — inner cost or pressure that makes it emotionally loaded. UI-only (surfaced as tooltip on the arc goal in the sidebar). NOT rendered in prompt context — the narrator works from general early-turn behavioral guidance in the system prompt, not from the raw `goal_context` value.
- **`visible_goal`**: The player-facing objective.
- **`threads[]`**: Unified thread collection filtered by `active` flag. Scene-scope threads provide immediate pressure; arc-scope threads provide medium-term tension.
- **`resolved_arc`**: TTL-filtered list of previously resolved arcs, providing narrative continuity across arc transitions.

### Opening-turn narrative mode

The seed embeds emotional stakes in the initial state — NPC `relation` fields, `motivation/fear/leverage`, and a `goal_context` sidebar entry. The narrator does NOT receive special early-turn prompt guidance or `goal_context` in its context. Instead, the initial scene's NPCs (with rich behavioral drivers), the opening narrative's tone, and the player-facing sidebar create the onboarding experience. The narrator works from its standard behavioral guidance and the richness of seed-generated state.

## Key forward dependency

`narrative` is the primary content input for all three extraction streams below.

### GM Beat consumption

The narrator receives a pending GM beat from `state.meta.pending_gm_beat` (set by Storytell in the previous turn). The beat's `type` and `surface_as` metadata are passed alongside the pacing directive as creative guidance for the narrative. The beat is NOT cleared after narration — it persists through the extraction phase. After extraction completes, Storytell replaces it with a new beat or pops it on null output. Full beat lifecycle is documented in [step2c-storytell](./step2c-storytell.md#gm-beat).

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
        S4["compendium.npcs[presence='present']"]
        S5["state.pc.conditions"]
        S6["npc_roster<br>(from build_npc_roster(), filtered by presence field)"]
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
        O5["compendium_npc_update<br>  durable identity changes (presence, notes, bio upserts)"]:::outNode
    end

    IN --> LLM2A
    LLM2A --> OUT
```

## Key forward dependency

`location_change` flows into `extraction_ctx` (built by `_build_extraction_context`). Step 2c also receives `npc_roster` (from build_npc_roster()) built from comp_this_turn. No forward-facing mechanics (`thread_add`, `gm_beat`) are emitted by this stream — they go through the unified thread lifecycle via Storytell (Step 2c).

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

Step 2c receives `npc_roster` (from build_npc_roster()) and `location_change` from Step 2a. Cross-stream items_gained/lost were removed — extraction_ctx now covers all this-turn derived data.

---


## step2c-storytell



Extracts thread updates, arc actions, and durable NPC compendium changes. World state changes happen only via thread resolution `promote_to_world_state`.

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
        S8["recent_turns[-10:]<br>(prior narration, last 10 turns)"]:::xstream
        S9["prior_history[:-1]<br>(all history bullets except last,<br>already shown as full text)"]:::xstream
        S10["recent_beats<br>(beat history for diversity)"]:::xstream
    end

    subgraph LLM2C["LLM — storytell_system.j2 + storytell_user.j2"]
        SL["temp: 0.4 · max_retries: 1<br>output: StorytellerResult JSON"]:::llmNode
    end

    subgraph OUT["Outputs — StorytellerResult"]
        O1["thread_update: list[ThreadUpdate]<br>  id + urgency/active/summary/progress/progress_kind changes"]:::outNode
        O1b["goal_update: str | None<br>  new visible_goal, mid-arc pivot<br>  applied directly to arc dict"]:::outNode
        O1c["arc_resolve: ArcResolution | None<br>  resolution, visible_goal,<br>goal_context, drop_threads, new_threads"]:::outNode
        O2["thread_resolve: list[ThreadResolution]<br>  id + resolution_state<br>(resolved/failed/abandoned)"]:::outNode
        O3["thread_add: ArcThread | None<br>  new thread, gated by PacingContext.gate"]:::outNode
        O4["actions: list[str]<br>  exactly 4 suggested player choices"]:::outNode
        O5["outcome_summary: str<br>  1–2 sentence narrative recap"]:::outNode
        O6["gm_beat: GMBeat | None<br>  forward-facing storytelling beat"]:::outNode
    end

    IN --> LLM2C
    LLM2C --> OUT
```

## Always runs

Storytell is the post-narration storytelling brain. It always executes every turn (never skipped) and feeds next turn's rules call via `thread_update/goal_update/arc_resolve/thread_resolve/thread_add` (storyteller-managed thread lifecycle), and `gm_beat` (forward-facing beats stored in `state.meta.pending_gm_beat`). World state changes are promotion-only — emitted via `thread_resolve[].promote_to_world_state`.

## GM Beat

Forward-facing storytelling beats that shape scene progression across turns. Beats are emitted by Storytell (Step 2c), consumed by Narrator (Step 1) the following turn, and managed via a write/expiry lifecycle in `state.meta.pending_gm_beat`.

### GMBeat Schema

```
GMBeat
  type: complication | revelation | opportunity | breathing_room | pressure | twist | setback | escalation | callback
  surface_as: ambient | event | npc_behavior | environmental | player_discovery | item (default: ambient)
  beat_expires_turn: int | None — turn number at which the beat expires; set to turn_no + 2 when stored
```

**Validation:** Only `type` is validated by `StorytellerResult._nullify_invalid_gm_beat` — nullified if type is falsy or not in the valid set. No validation on `surface_as`. Python accepts whatever gm_beat the LLM emits with no correction or override.

### PacingContext Beat Fields

The beat system intersects with pacing via two fields in `PacingContext` (see [step0-ruling](./step0-ruling.md#pacing-context)):

| Field | Type | Meaning |
|-------|------|---------|
| `directive` | str | May include secondary modifier `"; Resolve a Threat"` when `beat_locked=True` (except Breathe). Drives storytell guidance for beat type selection. |
| `beat_locked` | bool | True when either `consecutive_pressure_turns >= threshold` OR `momentum <= momentum_floor`. When locked, `"Resolve a Threat"` is appended to the directive (except Breathe). Enables floor relief to inject a breathing_room beat if the storyteller is stuck in a pressure-type loop (only when not from momentum floor). |

### Beat Lifecycle — Turn Sequence

```mermaid
flowchart TD
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef decision fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    classDef output fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6

    START["Turn begins"]:::pyNode --> EXPIRY{"beat_expires_turn set<br>AND turn_no > expires?"}:::decision
    EXPIRY -- yes --> NULLIFIED["Beat nullified (expired)<br>state.meta.pending_gm_beat = None"]:::output
    EXPIRY -- no --> KEEPBEAT["Beat kept<br>stays in state"]:::pyNode

    NULLIFIED --> NARRATE["Narrate receives pending_gm_beat<br>(None if expired, beat dict if kept)"]
    KEEPBEAT --> NARRATE

    NARRATE --> EXTRACTION["Extraction pipeline (scene → state → storytell)<br>pending_gm_beat persists unchanged<br>through this phase"]:::pyNode

    EXTRACTION --> STORYLLM{"Storytell emits gm_beat<br>with non-null type?"}:::decision
    STORYLLM -- "yes" --> STORED["state.meta.pending_gm_beat = storyteller beat<br>beat_expires_turn = turn_no + 2 (TTL: 2 turns)"]:::output

    STORYLLM -- "no / null" --> POPPED["state.meta.pending_gm_beat = None<br>(key popped from meta)"]:::pyNode
    POPPED --> FLOOR{"beat_locked == True<br>AND (pending_gm_beat is None<br>    OR type in pressure types)<br>AND NOT triggered_by_momentum?"}:::decision
    STORED --> FLOOR

    FLOOR -- yes --> BREATHING["Inject breathing_room beat<br>overrides any pressure-type pending beat<br>beat_expires_turn = turn_no + 3"]:::output

    FLOOR -- no --> APPEND_BEATS["recent_beats.append(snapshot)"]:::pyNode
    BREATHING --> APPEND_BEATS

    APPEND_BEATS --> COUNTER["consecutive_pressure counter<br>updated from gm_beat.type"]:::pyNode
    COUNTER --> DONE["Turn ends"]:::pyNode

    STORED -. "next turn" .-> START
    BREATHING -. "next turn" .-> START

    style EXPIRY fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    style STORYLLM fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    style FLOOR fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
```

**Step 1 — Pre-narration expiry check.** At the start of each turn, the engine reads `state.meta.pending_gm_beat` from the previous turn. If `beat_expires_turn` is set and the current turn number exceeds it, the beat is nullified (key set to None). Otherwise it proceeds to narration.

Note: This expiry runs early enough that the beat is gone before the extraction phase begins. This is intentional — it creates clean state for floor relief to inject breathing_room if `beat_locked` is active and storyteller doesn't provide its own non-pressure beat. Without the pre-narration expiry, a stale expired beat could block floor relief's null check.

**Step 2 — Narration consumption.** The beat is passed to the narrator via `_narrate_messages(pending_gm_beat=...)`. The narrator uses the beat's `type` and `surface_as` metadata as creative guidance alongside the pacing directive. The beat is NOT cleared after narration — it persists through the extraction phase.

**Step 3 — Storytell writes or clears the beat.** After extraction completes:
- If Storytell emits a valid `gm_beat` (non-null `type`): replaces `pending_gm_beat` with `beat_expires_turn = turn_no + 2`.
- If Storytell emits `null` or an invalid beat: pops `pending_gm_beat` from state (null-clear). The old beat does NOT carry forward.

**Step 4 — Floor relief injection.** After delta apply, if `beat_locked=True` AND the current `pending_gm_beat` is either `None` or a pressure-type (`pressure`, `escalation`, `complication`) AND the beat was NOT triggered by momentum floor: injects a `breathing_room` beat with `beat_expires_turn = turn_no + 3`. This overrides pressure-type beats that would otherwise continue the pressure cycle, but does NOT override non-pressure beats the storyteller independently produced (e.g., `revelation`, `opportunity`, `breathing_room`).

**Step 5 — Beat history snapshot.** `pending_gm_beat` is appended to `state.meta.recent_beats` (capped at 5 entries). The snapshot is taken after any floor relief override, so it reflects the beat the next turn's narrator will consume.

**Step 6 — Consecutive pressure counter update.** The counter increments on pressure-type beats and resets to 0 otherwise.

### Floor Relief Injection

The floor relief mechanism fires after delta apply when `_pc.beat_locked=True` AND the current `pending_gm_beat` is either `None` or a pressure-type beat (`pressure`, `escalation`, `complication`) AND NOT triggered by momentum floor. It injects a `breathing_room` beat with TTL of 3 turns (one more than storyteller-emitted beats' TTL of 2).

Floor relief is a **fallback override** — it breaks a pressure-type run by force-injecting recovery:
- If Storytell emitted a pressure-type beat → floor relief overrides it with breathing_room.
- If Storytell emitted a non-pressure beat (revelation, opportunity, breathing_room, etc.) → floor relief lets it stand. Relief is already being achieved.
- If Storytell emitted nothing (null) → floor relief injects breathing_room. This is appropriate: after a null turn with beat_locked active, relief is needed.

### Directive-Beat Alignment

The storyteller prompt (`storytell_system.j2`, pacing context guidance section) maps each PacingContext directive to recommended beat types (e.g., "Breathe" → breathing_room; "Scene Imperative" → advance story; "Overwhelm" → pressure/escalation). This alignment is **guidance only** — Python accepts whatever gm_beat the LLM emits with no validation, correction, or override. Design rationale: forcing directive-beat alignment would constrain storytelling flexibility and create brittleness if the LLM makes contextually appropriate but directive-divergent beat choices.

### Beat History

`state.meta.recent_beats` stores the last 5 beats (including null entries) with `turn`, `type`, and `surface_as`. This history is rendered in both the storyteller system prompt (behavioral guidance) and the user prompt (current-turn context, more salient). Each entry shows `T{N}: {BEAT TYPE} (surface)` or `T{N}: No beat emitted this turn`.

The LLM uses this history to follow beat diversity guidance: avoid repeating the same type more than twice in a sequence; at least one in three beats should be a non-pressure type.

### TTL Mechanics Summary

| Source | Default TTL | Expiry Calculation |
|--------|-------------|-------------------|
| Storytell-emitted beat | 2 turns | `beat_expires_turn = turn_no + 2` |
| Floor relief (Python-injected) | 3 turns | `beat_expires_turn = turn_no + 3` (extra recovery margin) |

### Null-Clear Behavior

When Storytell emits a null beat (or an invalid beat whose type is nullified), `pending_gm_beat` is popped from `state.meta`. The beat does NOT carry forward. This replaced the old carryover behavior where stale beats persisted through null turns.

The storyteller user prompt always renders the GM Beat section — on null-following turns it shows "No beat currently carried over from the previous turn. Choose freely." This ensures the LLM has consistent beat awareness on every turn.

### GM Beat Section in UI

The storyteller user prompt renders the `## GM Beat` section unconditionally:
- **Beat present:** Shows type, surface_as, expiration turn.
- **No beat:** Shows fallback text — "No beat currently carried over from the previous turn. Choose freely."

This was changed from the previous conditional rendering (where the section vanished on ~38% of turns), ensuring full beat awareness coverage.

## Campaign Arc System

The campaign arc system tracks story threads across turns. Thread state is **storyteller-managed** — the LLM explicitly controls urgency, progress, and goal direction via `thread_update` and `goal_update` directives. The engine applies these without enforcement of caps, cooldowns, or silent timers.

### Arc Data Model

```
CampaignArc
  visible_goal: str          — What the PC is trying to achieve
  goal_context: str          — 2–3 sentences explaining why visible_goal matters (UI-only; not rendered in prompts)
  threads: list[ArcThread]   — Unified collection with active flag
  completed_threads: list[ArcThread] — Resolved/failed/abandoned threads
  resolution: str | None     — Set when arc is resolved via arc_resolve
  last_thread_created_turn: int — Tracks when a thread was last created for pacing

ProgressEntry
  kind: Literal["advancement", "setback", "shift"] = "advancement"
  text: str

ArcThread
  id: str                    — Unique identifier
  summary: str               — What this thread is about
  scope: Literal["scene", "arc"]  # scene = short-lived, purged on location change; arc = persistent story tension
  active: bool = True        # Storyteller-controlled via thread_update; engine may auto-demote via auto-latent or decay to latent/removed
  urgency: Literal["background", "normal", "urgent"] = "normal"  # Storyteller-controlled; Python enforces stepwise decay (urgent→normal→background) after N turns at same level
  progress: list[ProgressEntry] = []   — Append-only log of structured progress updates
  resolution_state: str | None # Set when thread_resolve processes resolved/failed/abandoned
  outcome: str | None        # Set from ThreadResolution.outcome when moved to completed_threads
  resolved_turn: int | None  — Turn when thread was resolved; used for TTL filtering in prompts
  last_updated_turn: int | None — Turn when thread was last updated via thread_update; used for auto-latent demotion and staleness display
  added_turn: int | None     — Turn when thread was created (thread_add or seed); enables age calculations for decay/expiration passes
  urgency_set_turn: int | None — Turn when urgency was last set; enables Python-side urgency decay pass to measure how long a thread has been at its current level
```

### Engine-Driven Arc

Thread lifecycle runs in `engine/turn.py` during the extraction phase. Seven operations handle arc/thread state in strict order:

```mermaid
flowchart TD
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef arcNode fill:#3b0764,color:#e9d5ff,stroke:#7c3aed

    PR["StorytellerResult<br>thread_update: list[ThreadUpdate]<br>goal_update: str | None<br>arc_resolve: ArcResolution | None<br>thread_resolve: list[ThreadResolution]"]:::pyNode

    subgraph UPDATES["_apply_thread_updates(config)"]
        U1["For each ThreadUpdate:<br>Find thread by id → apply<br>active/urgency/summary/progress changes<br>progress is append-only (list[ProgressEntry])<br>Progress dedup via difflib (≥50% overlap → reject)<br>Sets last_updated_turn = current turn"]
        U2["Auto-latent demotion:<br>threads untouched for thread_stale_threshold turns<br>→ active: false"]
        U3["Urgency decay pass:<br>for each active thread with urgency_set_turn,<br>If age >= thread_urgency_max_age:<br>  urgent → normal, then normal → background<br>Sets urgency_set_turn = current turn on demotion"]
        U4["Scene-scoped two-stage lifecycle:<br>(a) Active scene threads silent ≥ threshold turns → latent (active: false; urgency handled by decay pass above)<br>(b) Latent scene threads unsurfaced ≥ 2× threshold turns → removed from arc.threads[]<br>Only applies to scope=scene threads"]
    end

    subgraph GOAL["goal_update (direct dict assignment)"]
        G1["If storyteller_result.goal_update is set:<br>state['arc']['visible_goal'] = value<br>Direct assignment, NOT through _merge_arc_update<br>(which would wipe threads[])"]
    end

    subgraph CONFLICT["Same-turn conflict detection"]
        C1["If same thread id appears in both<br>thread_update and thread_resolve:<br>log WARNING (LLM error)<br>resolution wins (fires after update)"]
    end

    subgraph RESOLVE["_apply_arc_resolve()"]
        R1["Store current arc in resolved_arcs<br>with resolved_turn for TTL tracking"]
        R2["Auto-close arc-scoped threads with 'superseded' state<br>Carry forward scene-scoped threads (minus drop_threads)"]
        R3["Add new_threads from resolution"]
        R4["Create successor arc with<br>new visible_goal, goal_context,<br>surviving scene-scoped + new threads"]
    end

    subgraph RESOLUTIONS["_apply_thread_resolutions()"]
        S1["For each ThreadResolution:<br>Move ArcThread to completed_threads<br>Set resolution_state, outcome, resolved_turn"]
    end

    subgraph GATE["Thread add gate (with cap eviction)"]
        T1["PacingContext.gate == 'allow'?<br>If blocked: log debug, skip add<br>Gate status rendered in prompt<br>(no silent drops)"]
        T2["ID collision? Thread id in existing_ids<br>or completed_ids → reject"]
        T3["Thread cap: if active > thread_max_active<br>→ evict oldest active thread (set active: false)"]
    end

    PR --> UPDATES --> GOAL --> CONFLICT --> RESOLVE --> RESOLUTIONS --> GATE

    GATE -- "CampaignArc" --> ARC[arc state in<br>state.yaml]:::arcNode
```

**Pipeline order:** thread updates → goal_update (dict assignment) → conflict detection → arc resolution → thread resolutions → thread_add gate.

**Key rules:**
- **Engine-enforced thread governance:** The engine enforces five controls that constrain storyteller thread management:
  - **Auto-latent demotion:** Threads untouched for `config.thread_stale_threshold` turns (default 3) are automatically set to `active: false`. This prevents stale threads from lingering as active prompts. Fires every turn after thread_updates loop completes (not gated on mutation).
  - **Thread cap eviction:** After thread_add, if active thread count exceeds `config.thread_max_active` (default 5), the oldest active thread (by `last_updated_turn`) is evicted to `active: false`. This prevents unbounded thread accumulation.
  - **Progress dedup:** New progress entries are compared against the last entry via `difflib.SequenceMatcher`. ≥50% textual overlap causes rejection with a WARNING log. This filters out near-duplicate LLM output.
  - **Urgency decay (Python-side floor):** Threads that have been at their current urgency level for >= `thread_urgency_max_age` turns (default 8) are demoted stepwise: urgent → normal, then normal → background. Only applies to active threads with `urgency_set_turn` set. Does not send signals to the LLM — it is a structural floor preventing indefinite stagnation at any urgency level.
   - **Scene-scoped two-stage expiration:** Scene-scoped (`scope=scene`) threads follow an additional lifecycle: (a) after `scene_thread_expire_silent_turns` turns (default 5) without being advanced, they go latent (`active: false`; urgency handled by the decay pass above). (b) If a latent scene thread remains unsurfaced for another `scene_thread_expire_silent_turns` turns (total 2× threshold), it is removed entirely from `arc.threads[]`. This gives scene threads a soft landing — visible to prompts while latent, then purged if never discovered.
- **goal_update:** A bare string applied directly to `state["arc"]["visible_goal"]` via dict assignment. Does NOT route through `_merge_arc_update` (which replaces `threads[]` unconditionally — passing a bare CampaignArc would wipe the thread list). Applied before arc_resolve; if both fire on the same turn, arc_resolve wins (ending the arc supersedes a mid-arc update).
- **Same-turn conflict detection:** When the same thread id appears in both `thread_update` and `thread_resolve` in a single output, a WARNING is logged. The processing order (update before resolve) means resolution takes precedence — correct behavior, but this is always an LLM error worth monitoring.
- **Arc resolution:** When `arc_resolve` is emitted, the current arc is stored in `state["resolved_arcs"]` with `resolved_turn` for TTL tracking. Arc-scoped threads are auto-closed with 'superseded' state; scene-scoped threads carry forward (minus any in drop_threads). The successor arc starts with empty `threads[]`.
- **Scene-scoped threads:** Purged from state on location change (delta_builder.py) before the arc director re-derives.
- **TTL-based cleanup:** Completed threads and resolved arcs are pruned from prompt context after `completed_thread_ttl` / `resolved_arc_ttl` turns (default 3). The `arc_ttl` is wired from `config.arc_memory_ttl` (not hardcoded).

### Arc Context in Narration

The arc state is passed to the narrator via `current_arc` in both system and user prompts. `goal_context` is present in the model but only surfaced in the player UI (tooltip/description text) — the pipeline and prompts never read it directly. The narrator sees arc metadata including resolved arcs (TTL-filtered) and completed threads.

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
        E1["Storyteller emits<br>thread_update: list[ThreadUpdate],<br>goal_update: str | None,<br>arc_resolve: ArcResolution | None,<br>thread_resolve: list[ThreadResolution],<br>thread_add (gated by PacingContext.gate)"]:::pyNode
    end

    subgraph ARC_ENGINE["Arc Engine (turn.py)"]
        A1["_apply_thread_updates()<br>apply storyteller's explicit state changes"]:::pyNode
        A2["goal_update → direct dict assignment<br>state['arc']['visible_goal'] = value"]:::pyNode
        A3["Same-turn conflict detection<br>update + resolve for same id → WARNING"]:::pyNode
        A4["_apply_arc_resolve()<br>resolve arc, store in resolved_arcs,<br>create successor arc"]:::pyNode
        A5["_apply_thread_resolutions()<br>thread_resolve → completed_threads<br>with resolution_state, outcome, resolved_turn"]:::pyNode
        A6["_merge_arc_update()<br>engine arc_delta → state['arc']"]:::pyNode
    end

    STATE --> N1
    N1 --> E1
    E1 --> A1 --> A2 --> A3 --> A4 --> A5 --> A6

    A6 --> STATE
```

### Thread Mechanics

#### Two Thread Scopes

Threads have a `scope` field (`"scene"` or `"arc"`) that determines narrative treatment:

| Scope | Narrative role | Engine lifecycle |
|---|---|---|
| `scene` | Short-lived tension tied to current location/NPCs | **Purged on location change** — removed from `arc.threads[]` when player moves to a new location (delta_builder.py). **Two-stage expiration:** active→latent after 5 silent turns (`active: false`; urgency handled by decay pass above); latent→removed entirely after 10 total unsurfaced turns. |
| `arc` | Persistent story tension across scenes | Persists across location changes. Only removed via `thread_resolve` or auto-closed on arc_resolve (state `"superseded"`). Subject to auto-latent demotion and urgency decay like all threads. |

#### Entry Points

Seven call sites in `run_turn()` process arc/thread operations in order:
1. **`_apply_thread_updates()`** — apply storyteller's explicit state changes; progress is append-only (`list[ProgressEntry]`); sets `last_updated_turn`; auto-latent demotion when untouched past threshold; urgency decay (stepwise urgent→normal→background after N turns at same level); scene-scoped two-stage expiration (active→latent, latent→removed). Progress dedup via SequenceMatcher
2. **`goal_update`** — direct dict assignment to `state["arc"]["visible_goal"]`
3. **Same-turn conflict detection** — warn if same thread id in both update and resolve
4. **`_apply_arc_resolve()`** — resolve arc, store in resolved_arcs, create successor
5. **`_apply_thread_resolutions()`** — resolve/fail/abandon → completed
6. **Thread add gate** — pacing gate + ID collision checks + thread cap eviction
7. **`_merge_arc_update()`** — apply the final CampaignArc delta to state

All seven run after `apply_delta()` but before `save_state()`.

#### Step-by-Step: `_apply_thread_updates(config)`

Processes `storyteller_result.thread_update` (list of `ThreadUpdate` with `id`, optional `active`, `urgency`, `summary`, `progress`, `progress_kind`).

For each ThreadUpdate:
1. Find matching thread by ID in `arc.threads[]`
2. If not found → log WARNING, skip
3. If found:
   - Apply non-None fields (`active`, `urgency`, `summary`) via `model_copy`
   - If `progress` is non-None: wrap in `ProgressEntry(kind=update.progress_kind or "advancement", text=update.progress)`. If thread already has progress, compare against last entry via `difflib.SequenceMatcher` — ≥50% overlap rejects with WARNING. Otherwise append.
    - Set `last_updated_turn` to current turn number
 4. Log applied changes at INFO level
 5. **Auto-latent demotion** (post-loop, after every thread_updates loop): For each active thread whose `last_updated_turn` is ≥ `config.thread_stale_threshold` turns ago, set `active: false`.
 6. **Urgency decay pass**: For each active thread with `urgency_set_turn` set, if age (`turn_no - urgency_set_turn`) >= `thread_urgency_max_age`, demote stepwise (urgent→normal, normal→background). Sets `urgency_set_turn = current turn` on demotion. Skips threads without `urgency_set_turn` (pre-existing data degrades gracefully).
  7. **Scene-scoped two-stage expiration**: For each scene-scoped (`scope=scene`) thread: (a) If active and silent for >= `scene_thread_expire_silent_turns` turns, set `active=False`. Urgency is handled by the urgency decay pass above — this step does not override it. (b) If latent and unsurfaced for >= 2× threshold total, remove from `arc.threads[]`. Skips threads without turn context (`last_seen_turn` or `added_turn`).

**Progress model:** Every progress entry is a `ProgressEntry` with `kind` field (`"advancement"`, `"setback"`, or `"shift"`) and `text`. The `progress_kind` field on `ThreadUpdate` tags each emitted progress entry; default is `"advancement"`. Progress is rendered to prompts as `[KIND] text` by `_fmt_progress()` (module-level function in `ccya/prompts/context.py` — relocated from a static method on `ArcThreadBlock` and from `ccya/engine/narrate.py`).

**Progress dedup:** Uses `difflib.SequenceMatcher.ratio()` against the last entry to reject near-duplicate progress (≥50% textual overlap). This filters out LLM outputs that rephrase the same progress update without advancing the narrative. A WARNING is logged on rejection.

**Auto-latent demotion:** Prevents stale threads from accumulating as active prompts. Threads that haven't been touched by `thread_update` for `config.thread_stale_threshold` turns (default 3) are automatically demoted to `active: false`. This is engine-enforced, not storyteller-managed — the storyteller can re-activate a thread by issuing a `thread_update` with `active: true`, but the engine will demote it again if it goes untouched. Fires every turn (not gated on mutation) so stale active threads reliably get `active=false` after 3 turns of no updates.

#### Step-by-Step: `_apply_arc_resolve()`

Processes `storyteller_result.arc_resolve` (optional `ArcResolution` with `resolution`, `visible_goal`, `goal_context`, `drop_threads: list[str]`, `new_threads: list[ArcThread]`).

1. If `arc_resolve` is None → return None
2. Validate arc from state; if missing/invalid → log WARNING, return None
3. Store current arc in `state["resolved_arcs"]` with `resolved_turn` for TTL tracking
4. Auto-close all arc-scoped threads: move to completed_threads with resolution_state="superseded"
5. Carry forward scene-scoped threads minus any IDs listed in drop_threads
6. Add new_threads from the ArcResolution model
7. Create successor arc with new `visible_goal`, `goal_context`, and combined surviving + new threads
8. Replace `state["arc"]` with successor

#### Thread Creation (gated in `run_turn()` with cap eviction)

New threads (`storyteller_result.thread_add`) are gated by:

1. **Pacing gate**: `PacingContext.gate == "allow"` — blocks escalation when pacing context says so. Gate status is rendered in the prompt (`_thread_list.j2`) so the storyteller has awareness instead of silent drops.
2. **ID collision**: thread `id` already exists in `arc.threads[]` or `arc.completed_threads[]` → reject with WARNING log. Id-based dedup only — no key field or fuzzy merge.
3. **Thread cap eviction** (post-add, only if config provided): If active thread count exceeds `config.thread_max_active` (default 5), evict the oldest active thread (by `last_updated_turn`) — set `active: false`. This prevents unbounded thread accumulation while the storyteller can still add new threads when pacing context permits.

**Thread creation via thread_update (ungoverned):** Threads can also be created implicitly by appearing in `thread_update` without a prior `thread_add`. This is the dominant creation path in practice — the LLM introduces new thread IDs directly via updates.

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

The gate blocks thread creation. The LLM is instructed not to emit `thread_add` when `gate != "allow"`, and the gate status is explicitly rendered in the prompt to provide awareness.

#### Constants Reference

| Constant | Value (default) | Effect |
|---|---|---|
| `config.arc_memory_ttl` | 3 | Turns to keep resolved arcs in prompt context (wired to `_storytell_messages(arc_ttl=...)`) |
| `config.thread_memory_ttl` | 3 | Turns to keep completed threads in prompt context |
| `config.thread_stale_threshold` | 3 | Turns of inactivity before auto-latent demotion (`active: false`) |
| `config.thread_max_active` | 5 | Max active threads; oldest evicted when exceeded on thread_add |
| `config.thread_urgency_max_age` | 8 | Turns at same urgency level before Python-side stepwise decay (urgent→normal→background) |
| `config.scene_thread_expire_silent_turns` | 5 | Scene-scoped thread expiration threshold: active→latent after this many silent turns; latent→removed after 2× this value unsurfaced |
| `config.track_scene_thread_progress` | True | Whether scene-scoped threads receive progress tracking (enables completion via Python) |

#### Validation Edge Cases

1. **Empty arc state** — No arc in state → log DEBUG, return None (no crash)
2. **Validation failure** — Arc fails Pydantic validation → log WARNING, return None
3. **Unknown thread ID in update** — Log WARNING, skip — does not block valid updates
4. **Unknown resolution ID** — Log WARNING, skip — does not block valid resolutions
5. **Duplicate thread ID in creation** — Checked against existing + completed IDs
6. **Same-turn update+resolve conflict** — Same thread id in both `thread_update` and `thread_resolve` → log WARNING, resolution wins (fires after update)
7. **Progress type migration** — Old saves with `progress: "str"` or `progress: list[str]` are coerced via `field_validator("progress", mode="wrap")`: bare strings wrapped in `[{"text": v, "kind": "advancement"}]`; string lists converted to `[{"text": s, "kind": "advancement"} for s in list]`.
8. **Progress dedup rejection** — New progress with ≥50% textual overlap against last entry → log WARNING, skip entry (does not block rest of update)
9. **Thread cap eviction** — After thread_add, if active count > `thread_max_active`, oldest active thread evicted to `active: false` — log INFO with evicted thread id

### Progress Migration

`ArcThread.progress` has migrated through two versions:
- **v1:** `str` — single progress string
- **v2:** `list[str]` — append-only list of progress strings
- **v3 (current):** `list[ProgressEntry]` — structured entries with `kind` + `text`

A Pydantic `field_validator("progress", mode="wrap")` on `ArcThread` handles all legacy shapes:
- Bare `str`: wraps in `[{"text": v, "kind": "advancement"}]`
- `list[str]`: converts to `[{"text": s, "kind": "advancement"} for s in list]`
- `list[ProgressEntry]`: passes through

---

---

**Track:** baseline

# Static Context (immutable across all turns)

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
      "charisma": 3
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
    ]
  },
  "compendium": {
    "npcs": {
      "caron": {
        "name": "Caron",
        "title": "Old creditor",
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "bond": null,
        "presence": null,
        "notes": null,
        "motivation": null,
        "fear": null,
        "leverage": null
      },
      "halden": {
        "name": "Halden",
        "title": "Merchant",
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
        "bond": null,
        "presence": null,
        "notes": null,
        "motivation": null,
        "fear": null,
        "leverage": null
      },
      "innkeeper": {
        "name": "Edda",
        "title": "Innkeeper at the Crossed Keys",
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "bond": null,
        "presence": null,
        "notes": null,
        "motivation": null,
        "fear": null,
        "leverage": null
      },
      "tough_a": {
        "name": "Bald Tough",
        "title": "Road thug",
        "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
        "bond": null,
        "presence": null,
        "notes": null,
        "motivation": null,
        "fear": null,
        "leverage": null
      },
      "tough_b": {
        "name": "Scarred Tough",
        "title": "Road thug",
        "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
        "bond": null,
        "presence": null,
        "notes": null,
        "motivation": null,
        "fear": null,
        "leverage": null
      },
      "matthew_estrada": {
        "name": "Matthew Estrada",
        "title": "Traveler",
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
        "bond": null,
        "presence": null,
        "notes": null,
        "motivation": null,
        "fear": null,
        "leverage": null
      }
    }
  },
  "arc": {
    "visible_goal": "Clear your debts and deliver the ledger \u2014 two obligations binding you to Marrow's Crossing.",
    "goal_context": "",
    "threads": [
      {
        "id": "settle_the_debt",
        "summary": "Settle the 500-credit debt with Caron.",
        "scope": "arc",
        "active": false,
        "urgency": "normal",
        "progress": [],
        "resolution_state": null,
        "outcome": null,
        "resolved_turn": null,
        "last_updated_turn": null,
        "added_turn": null,
        "urgency_set_turn": null
      },
      {
        "id": "deliver_the_ledger",
        "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
        "scope": "arc",
        "active": false,
        "urgency": "normal",
        "progress": [],
        "resolution_state": null,
        "outcome": null,
        "resolved_turn": null,
        "last_updated_turn": null,
        "added_turn": null,
        "urgency_set_turn": null
      },
      {
        "id": "clear_the_road_toughs",
        "summary": "Deal with the toughs blocking the inn entrance.",
        "scope": "arc",
        "active": false,
        "urgency": "background",
        "progress": [],
        "resolution_state": null,
        "outcome": null,
        "resolved_turn": null,
        "last_updated_turn": null,
        "added_turn": null,
        "urgency_set_turn": null
      }
    ],
    "completed_threads": [],
    "resolution": null,
    "last_thread_created_turn": 0
  }
}
```

## Engine Constants

```json
{
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
Decide whether the player's action requires a skill check and classify it. Emit ONLY a JSON object — no prose, no markdown fences.

## Stats
- `strength`: Physical force, melee, lifting, breaking, enduring pain
- `dexterity`: Agility, stealth, ranged attacks, fine motor, dodge, pickpocket
- `wits`: Perception, deduction, quick thinking, hacking under pressure, spotting a lie
- `charisma`: Persuade, deceive, charm, negotiate, intimidate by presence

## Difficulty
- `trivial` (+2): Almost certain; only roll if failure would be interesting
- `easy` (+1): Routine for a competent person
- `normal` (0): A genuine challenge
- `hard` (-1): Requires skill, preparation, or favorable conditions
- `extreme` (-2): Near-impossible without exceptional ability or luck

## Decision rule — default NO

Set `check.required=true` only when ALL THREE hold:
- (a) The player initiates an action with clear intent — including speech acts directed at a character who has reason to resist
- (b) Failure has a real, meaningful consequence
- (c) The outcome is genuinely uncertain

Set `required=false` for: idle observation, unimpeded movement, item inspection, casual conversation, passing time, routine commerce with a willing counterparty (buying at market price, paying a stated fee, settling a known debt).

## Compound actions

Pick the single most consequential or uncertain action — that is what you roll for. Other actions are narrative texture. If individually trivial sub-actions compound into something risky (sneak past guards then lift a badge), classify as ONE harder check. If the gating action fails, the chain doesn't continue.

## Anti-declare-outcome rule

If the player's phrasing asserts the result ("I one-shot the guard," "I instantly convince her") — classify the underlying attempt at hard or extreme difficulty. Never let the player's prose dictate success.

## Impossibility check

After classifying intent, evaluate whether the action is physically impossible given the character's state, inventory, and scene:
- Requires an item the character doesn't have
- Requires a capability contradicted by an active condition
- Acts on something not present in the scene

If merely difficult or unlikely — set `impossible=false` and classify normally. Only mark impossible when it literally cannot happen. If impossible: set `impossible=true`, write a brief reason in `impossible_reason`, set `check.required=false`.

## Scene motion

- `hold`: Action doesn't move the story to a new situation. Most routine actions.
- `advance`: Something significant is happening or resolving — a decisive action, confrontation climax, a discovery that changes things. Narrator should write through to the outcome.
- `transition`: Player is leaving this location or situation entirely. Narrator writes the arrival, not the departure.

## Schema

```json
{
  "intent": "...",
  "intent_verb": "...",
  "target": "...",
  "impossible": true,
  "scene_motion": "hold|advance|transition",
  "check": {
    "required": true,
    "skill": "...",
    "difficulty": "trivial|easy|normal|hard|extreme"
  }
}
```

## Field rules

- `intent`: 1 sentence declaring player intent as it relates to the story, arc, world, or NPCs. Never substitute, dismiss, or embellish. Only soften in line with the anti-declare-outcome rule.
- `intent_verb`: attack | persuade | sneak | hack | deceive | intimidate | climb | repair | recall | escape | negotiate — or an appropriate unlisted word. Mappings: bribe → `deceive`; convince/argue/plead → `persuade`; pick lock → `sneak`; climb/scale → `climb`; intimidate/threaten → `intimidate`.
- `target`: who or what the action is directed at, or omit if a general action.
- `impossible_reason`: only when `impossible=true`.
- `scene_motion`: hold | advance | transition.
- `check.required`: true or false.
- `check.skill`: only when `required=true`.
- `check.difficulty`: only when `required=true`.

Omit fields with no value to communicate. Empty strings are never valid.

```

### Narrate System Prompt

```
Narrate the next beat of a text adventure. Second person. If the genre tone section below specifies a tense, use it; otherwise use past tense. 2-3 paragraphs, ~180 words. Hard ceiling: 250 words. If your draft exceeds 250 words, reduce it — every sentence must advance the beat; delete the rest. Output prose only — never list choices, never speak as the game.

## Player input is truth (HIGHEST PRIORITY)

Take the player's stated action at face value. The rules engine handles dice and conditions; the narrator handles fiction. Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

**Priority ordering: player input > GM beat > pacing directive.** When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action. The player's action dictates what happens; the GM beat dictates how the world reacts. If no GM beat is present, narrate purely from the pacing directive and player input — no added pressure or relief beyond what the scene demands.

**Conflict example (READ CAREFULLY):**
- Player says: "I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger."
- GM beat says: "pressure: toughs circle and flank the player"
- WRONG: Narrate the toughs attacking and the player fighting them (this replaces the player's action).
- RIGHT: Narrate the player sitting down and sliding the seal/ledger across the table FIRST. Then describe the toughs circling and flanking as the player attempts this action — the toughs' presence is the environmental pressure, not the main event. The player's action (sitting, sliding seal, handing ledger) is the primary narration.

**Fallback for conflicts:** If player input and GM beat conflict, narrate the player's action FIRST (2-3 sentences describing the action completing or failing), then integrate the beat as an environmental reaction or NPC behavior that occurs during or immediately after. The player's stated action is the primary event; the GM beat is the world's response. Never narrate the GM beat event as if it replaced the player's action.

## Open with the player's action (BINDING)

First sentence addresses what the player does this turn. No establishing shots, no "you scan the room," no throat-clearing. If location or focus changed, start at the arrival — never narrate the journey there.

## Inventory

Items have proper names — use them as given in the inventory list (e.g., "Kestrel M4" not "the rifle", "The Merchant's Ledger" not "the book"). Do not replace specific item names with generic descriptors like "standard issue rifle" or "random book." Books, lore artifacts, and sentimental items carry narrative weight — their names tie to the story world or reflect emotional attachment; never reduce them to generics. Quantify item multiples specifically: "four pistol clips" not "some clips." When exact count is unknown, a tight qualifier is acceptable ("a couple," "several") — but prefer exact quantity.

**Inventory is a hard constraint.** Before narrating any item usage, spending, or consumption, verify the item appears in the `## inventory` list in the user prompt. If the player's action implies using, spending, or consuming an item not in that list, narrate the *attempt* failing — the player reaches for it, tries to produce it, or fumbles at their belt, and finds nothing. Never describe the player successfully producing, spending, or losing an item that is not in their current inventory. If the inventory list shows `credits: 500`, the player has 500 credits — do not invent `iron_coin`, `silver`, or other substitute denominations.

## Never repeat prior narration

The player has already read every prior turn. Do not re-describe events they witnessed, restate conditions already established, or rehash dialogue from earlier scenes. Each turn must advance — never circle back to what the player already knows.

BEFORE OUTPUTTING: scan every sentence. If it restates information from a prior turn — an NPC's attitude, a room's atmosphere, a known condition — delete it. Replace with what is NEW this turn. If two sentences say the same thing, keep the tighter one.

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

## NPCs

NPCs should feel like persistent people, not props. Give a brief physical description on first appearance. NPCs should frequently suffer positive and negative consequences, not just the player.
Mention characters from recent turns sometimes when relevant.

**NPC RE-USE:** The `## Characters` list shows everyone relevant to this scene. `PRESENT` means in the room; `KNOWN` means they could plausibly arrive — re-use them before creating new characters. `KNOWN` NPCs may also appear in dialogue, backstory, or plot-relevant narration: a known ally providing information remotely, an antagonist making moves elsewhere, a mentor calling for help. Mentioning known NPCs adds depth and continuity.

**NPC BEHAVIOR DRIVERS:** Each NPC has motivation (what they fundamentally want), fear (what they dread), and leverage (what they can offer, threaten, or withhold). Use these to drive their behavior, dialogue, and decisions. An NPC with a motivation should actively pursue it. An NPC with a fear should avoid or react to it. An NPC with leverage should use it as a bargaining chip or threat. These are not decorative — they are the engine of NPC agency. When an NPC's motivation conflicts with the player's goals, that's the source of drama. When an NPC's fear overrides their motivation, that's a character moment.

Favor NPCs who have at least one of these drivers set. NPCs with empty motivation, fear, and leverage are background — mention them only when setting or continuity requires it, never as scene focal points.

**NPC QUANTITY RULE:** When introducing or describing a group of unnamed NPCs, always give a specific number or a tight qualifier: "four guards," "a dozen soldiers," "three dock workers." Never use vague collective nouns alone: not "guards" or "some soldiers" or "a group of men." Named individuals are exempt. Vague groups make state tracking impossible.

NPCs die. In any scene with stakes, losing a confrontation means death, incapacitation, or removal from the scene. If you find yourself writing "stumbles back" or "retreats" in a high-stakes beat, replace it with a decisive outcome. The narrator and storyteller adjust — preserving plot by keeping characters alive is forbidden.
Resolve cruel, selfish, or evil player choices straight: narrate consequences without moralizing, refusing, or steering toward a "better" path. NPCs may react with horror, retaliation, or fear; the narrator never lectures or vetoes.

**NPC NAMING:** Every NPC must be referred to by a given name and family name (e.g. "Mira Sovak", "Dren Calloway"). Titles are optional. Descriptive labels like "scarred veteran" are aliases, not names — use the NPC's real name.

## Style
- Keep it tight — each turn is a scene beat, not a chapter. Every sentence must advance.
- Subvert the obvious. If the reader can predict the next sentence, rewrite it.
- Prefer direct dialogue over summarized speech. When a character speaks, write the quote.
  When the player reads a book, sign, or terminal, show the text verbatim in `> blockquote`.
- One simile per turn maximum. If it doesn't earn its place, cut it.
- Describe new characters briefly on first appearance.
- No sensory templates. "The air smells of" is banned. If a smell matters to the action, say it in 3 words. If it doesn't, cut it.
- Concrete phrases observed repeating 20+ times across recorded sessions — treat them as a signal the model is falling back on trained patterns: "The air smells of", "rhythmic", "sudden", "like a". If you catch yourself writing these, cut or replace.
- Spatial clarity when positioning matters (combat, stealth, formations). Say where things are relative to each other.

## Pragmatic interpretation

Interpret player input pragmatically, not literally. If the player says something absurd or physically impossible ("I offer a credit to the wall", "I punch the sky"), narrate the attempt as a reasonable interpretation of their intent — the wall doesn't accept coins, the sky can't be punched. The rules engine will resolve whether the action succeeds. Never refuse the action outright; narrate the attempt and let the dice decide.

## Pacing

Each beat must advance the plot meaningfully. No holding patterns, no extended descriptions of static scenes.

Override rule: The Outcome directive and pending GM beat are authoritative scene signals. Do not override them because the prose feels like it should go a different direction.

## Campaign arc context

Your visible goal is provided in the context below. Use it as narrative guidance. If an arc resolution is present, use it to inform how this new arc relates narratively to what was resolved before.

You have visibility into all threads — active, latent, and completed — plus their resolutions. Use this knowledge actively. Latent threads represent narrative threads the party has not yet discovered. Your job is to push the player gently towards them through narration, environmental detail, and NPC behaviour — without explicitly exposing the thread content. Show, don't tell. An NPC glancing nervously at a locked door, a flicker of torchlight from an unexplored tunnel, a curious sound carried on the wind. Introduce narrative elements that hint at the latent thread's existence and invite investigation. If a latent thread has gone unsurfaced for many turns, increase the pressure — make the hints less subtle.

## Markdown

- `**bold**` only for: NPC names on first introduction this scene; named inventory items (use a short name, not ammo) the player owns when used or directly referenced. Once per scene per object.
- `*italic*` for ship names, books, broadcasts, in-world publication titles, emphasized proper nouns.
- `> blockquote` for signage, broadcasts, and any text the player reads verbatim (books, terminals, letters).
- No headings, no bullet lists in prose.



```

### Extract Scene System Prompt

```
## Scene Extractor

Read the turn narration and extract the scene-level state: which NPCs are present and how they stand toward the player, whether the player moved to a new location, what the scene feels like, and any new spatial details about the current space. Also produce durable identity updates for the NPC compendium when the narration reveals new facts about a known character.

## Output schema

```json
{
  "scene_tags": ["..."],
  "scene_tagline": "...",
  "location_change": {"id": "...", "name": "...", "description": "..."},
  "location_description": "...",
  "compendium_npc_update": [{"id": "...", "name": "...", "title": "...", "bio": "...", "presence": "present|known", "notes": "..."}]
}
```

## Field rules

`scene_tags`: mood/genre descriptors for the scene. Up to 5. Use concise noun or adjective phrases. Examples: `"combat"`, `"tense_conversation"`, `"investigation"`, `"stealth"`, `"discovery"`.

`scene_tagline`: 3–6 words summarizing the scene for the UI header. Grounded in what just happened. Examples: `"A Toll Paid In Blood"`, `"Whispers in the Dark"`, `"The Guard Raises the Alarm"`.

`location_change`: emitted only when the player moves to a new location (the location ID differs from the current one). Do NOT emit if the player is still in the same location with added spatial detail — use `location_description` instead.

`location_description`: Location description — new physical/spatial detail about the current space. Only emit when the narration introduces genuinely new details not already in the stored description. Do not restate or paraphrase existing description. One to two sentences.

`compendium_npc_update`: **UNIVERSAL NPC CHANNEL** — use for ALL NPC changes. Each update carries the full set of fields that have new information:

```json
{
  "id": "snake_case_id",
  "name": "Display Name (omit if unchanged)",
  "title": "Optional title (omit if unchanged)",
  "bio": "TWO SENTENCES: (1) appearance and demeanor — how they are physically presented, bearing/posture/expression. (2) personality traits or tangible facts about who they are as a person — background details, habits, reputation that define them. Must be relevant to the story, not generic filler like 'is a merchant'. Omit if unchanged.",
  "aliases": ["alias1"],
  "allegiance": "faction_or_alignment",
  "motivation": "what this NPC fundamentally wants",
  "fear": "what this NPC is most afraid of",
  "leverage": "what this NPC can offer, threaten, or withhold",
  "presence": "present|known",
  "notes": "5–8 words max describing the NPC's current stance or action in this scene. No clauses, no conjunctions. Not plot-critical — quick situational cue only."
}

### How to use compendium_npc_update

- **NPC enters scene:** Set `presence: "present"` and provide context in `notes`. For first-time NPCs, include `name`, `bio` (mandatory — even for ambient NPCs like "crowd"), and optionally `title`. For known NPCs, omit `name`/`title`/`bio` and only set `presence`/`notes`.
- **NPC leaves scene:** Set `presence: "known"` — the engine clears notes automatically. Do NOT remove the NPC from state.
- **NPC behavior changes:** Update `notes` with a brief situational cue reflecting their current stance toward the player.
- **Durable identity updates:** Update `name`, `title`, `bio`, `aliases`, `allegiance`, `motivation`, `fear`, `leverage` when the narration reveals new facts.
- **NPC unchanged:** Omit entirely — do not emit an update for NPCs that have no changes.

## NPC ID rules

- Use existing IDs from the `## known_characters` compendium section when referencing known NPCs.
- For new NPCs, generate a stable `snake_case` ID from their name/title. Examples: `"scarred_tough"`, `"guard_captain_renn"`.
- If an NPC is known from the compendium, use their existing compendium ID — do NOT create a new ID.
- When adding a new NPC, include `name`, `title`, and `bio` so the engine can populate the compendium. **Bio is mandatory for every NPC — even ambient presence like "crowd" or "bystanders" needs a bio.**

### Bio and notes examples (READ CAREFULLY)

**Correct bio extraction:**
- Narration: "A scarred woman in a grease-stained apron wipes her hands on a rag, eyes narrowing at you as she approaches the counter." → `bio: "Tall with a jagged burn scar running from jaw to collarbone; carries herself like someone used to being obeyed. Served five years in the militia before going civilian — knows how to handle weapons and doesn't flinch under pressure."`
- Narration: "A young man in faded academy robes fumbles with his satchel, nearly dropping it as he stammers a greeting." → `bio: "Lean frame, sharp features, perpetually disheveled dark hair. Earned top marks in tactical theory but has never held a weapon — book-smart, eager to prove himself beyond the classroom."`

**Incorrect bio extraction (too generic / missing one dimension):**
- Narration: "A merchant approaches your table with a smile." → `bio: "Is a traveling trader who sells various goods."` ❌ Missing appearance entirely; second sentence is just restating their role, not giving personality or tangible facts.

**Correct notes extraction:**
- Narration: Caron slides into the seat across from you and taps his fingers on the table. → `notes: "tapping table — restless, waiting for move."`
- Narration: The guard steps between you and the door, hand resting on his baton. → `notes: "blocking exit with body angled toward handle."`

**Incorrect notes extraction (too long):**
- ❌ `"He noticed that you were looking at him suspiciously so he crossed his arms defensively and looked away for a moment before turning back to watch you closely as you talked to Caron about what was going on."` — multi-clause narration transcript, not a quick situational cue.

**Incorrect notes extraction (generic):**
- ❌ `"is suspicious of the player"` — vague attitude without any scene context or action reference. Does not tell the player anything useful about what is happening right now.

**Maximum 8 words for notes. Count them.**

**NPC ENTER/EXIT RULE (MANDATORY):**
- Emit `compendium_npc_update { presence: "present" }` for every named NPC who appears in the narration for the first time this turn and is not already marked as present.
- Emit `compendium_npc_update { presence: "known" }` for every named NPC who narration indicates has left, fled, died, fainted, or been removed from the scene.
- Do NOT emit presence changes for NPCs who are simply not mentioned — only remove if narration actively indicates departure.
- Unnamed ambient characters ("a group of guards," "bystanders") do not require per-turn tracking.

EXAMPLE — NPC enters (correct):
Narration: "A red-haired man in boiled leather steps through the door and locks eyes with you."
Known NPCs in scene: [caron (present)]
→ Emit: `compendium_npc_update: { id: "red_haired_man", name: "Red-Haired Man", presence: "present", notes: "locks eyes aggressively", bio: "..." }`

EXAMPLE — NPC exits (correct):
Narration: "Caron spits on the floor and shoves through the crowd, disappearing into the street."
→ Emit: `compendium_npc_update: { id: "caron", presence: "known" }`

EXAMPLE — NPC not mentioned, no change (correct):
Narration does not mention Halden this turn.
→ Do NOT emit any update for Halden — absence ≠ departure.

## State-presence rule

Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only emit presence changes you can justify from the narration.

## NPC dedup — mandatory pre-check (apply BEFORE every compendium_npc_update)

Before you emit `compendium_npc_update` for ANY NPC:

1. Check the `<<<TRACE_IMMUTABLE>>> known_characters` compendium section. If the NPC's name or title matches an existing compendium entry, use that entry's ID.
2. If the NPC was previously known but had `presence: "known"` and is now present, set `presence: "present"` and add `notes`.
3. If the NPC is already in the compendium, do NOT re-emit `name`, `title`, or `bio` unless the narration reveals new information.

## Constraints

- **NPC presence:** There MUST always be at least 1 NPC with `presence: "present"`. If no named NPCs are present, emit ambient presence (e.g., "crowd", "bystanders", "inn_patrons") with a generic ID. **HARD RULE: Do NOT emit ambient presence when any named NPC is already marked present.** Named NPCs are sufficient — this prevents hallucinated background characters.
- **Location IDs:** For `location_change`, derive a stable snake_case ID from narration context (e.g., "perimeter_ruins", "trench_area"). Do NOT invent new IDs for other purposes — only use existing location IDs from the current section or well-known locations.
- **Keep scene_tags to at most 5.** Prefer the most salient descriptors.
- **Limit new NPCs to at most 3 per turn.** Background extras go in ambient presence.

## Output discipline

When emitting structured data (JSON, scope tags, any machine-readable output), omit fields entirely when there is no change — do not include empty arrays (`[]`), empty objects (`{}`), or empty strings. Only emit the keys you actually need to communicate a value or instruction. Omitting a field means "no change" — it does NOT mean deletion of existing state (see State-presence rule).

Output a single JSON object matching the SceneExtractResult schema.

```

### Extract State System Prompt

```
Extract inventory and condition deltas from the narration. Emit one JSON object. No prose, no markdown fences. Omit fields with no changes — empty arrays are never valid.

## Narration is the sole authority

`player_intent` is context only — it does not mean the action succeeded. Ground all changes in what the narration confirms. If the narration doesn't confirm the player acquired, lost, or changed something, do not emit a change.

- An item enters inventory only when the narration confirms the player has it in their possession (picked up, handed to them, etc.)
- An item leaves inventory only when the narration confirms the player no longer has it (used up, given away, destroyed, dropped)
- An item does NOT enter inventory because it is nearby, visible, or available to take
- An item does NOT leave inventory because it is used by an NPC or destroyed in the world

## ID rules

IDs are `noun` or `adjective_noun`, lowercase, no articles.
- ✅ `worn_dagger`, `brass_key`, `short_sword`
- ❌ `the_dagger`, `a_key`, `soldiers_rifle`

IDs are immutable once assigned. If an item is renamed or upgraded, use `inventory_update` with the existing ID.

## Before emitting any inventory change

1. Check the `## inventory` list. If the item likely matches an existing entry (e.g. narration says "dagger" and `worn_dagger` exists), use the existing ID and emit `inventory_update` instead of `inventory_add`.
2. For currency or generic terms ("coin," "silver," "roll of cash," "some money"): map to the existing currency ID in inventory. Never invent a new currency ID. If no currency ID exists, omit the change entirely.
3. Clamp all remove amounts to the current stack. Never emit a remove amount exceeding what exists in inventory.

## Quantities

If the narration states a specific number, use it exactly. If no number is stated, infer from context (e.g. "fired multiple rounds" → 3-6). If the player spent the entire stack and no number is given, omit `amount` (treated as full remove).

## Schema

```json
{
  "inventory_update": [{"id": "...", "name": "...", "notes": "..."}],
  "inventory_remove": [{"id": "..."}],
  "inventory_add": [{"id": "...", "name": "...", "notes": "...", "amount": 1}],
  "pc_condition_remove": [{"id": "..."}],
  "pc_condition_add": [{"id": "...", "label": "...", "description": "...", "turns_remaining": 3}]
}
```

## Field rules

`inventory_update`: patches to existing items — name changes, notes updates, damage, upgrades. Does not support amount changes — use `inventory_remove` instead. `name` and `notes` are optional within an update entry.

`inventory_remove`: items lost, used up, destroyed, or spent. Set `amount` to the count consumed (e.g. `"amount": 1` for one pistol_round). Omit `amount` to remove the entire stack.
- If narration describes spending, giving away, or parting with an item — even if the amount is vague — emit the remove. If the recipient later rejects it or the action fails, still emit the remove.
- Using a reusable item (unlocking a door with a key, reading a book) does NOT consume it. Only emit remove when the item is actually lost or used up.

`inventory_add`: items explicitly received by the player character.
- Do not cap items explicitly received. Items found incidentally (e.g. "searched the crates") are limited to ≤2 per turn.
- Firearms and finite-use items always come with ammo or uses. Infer a realistic starting amount from context. If compatible ammo already exists in inventory, use `inventory_add` — it merges with the existing stack.
- Never emit `inventory_add` and `inventory_remove` for the same ID in one turn.

`pc_condition_remove`: conditions resolved this turn. Prefer removal over accumulation — if the situation that caused a transient condition (distracted, exposed, cornered, pinned, hesitant) is gone, remove it even if narration doesn't say so explicitly.

`pc_condition_add`: new conditions with a clear, substantial cause in the narration. Max 2 per turn. Total active conditions must not exceed 5 — if at cap, remove the least relevant before adding.

Only add a condition if it would plausibly affect at least one future dice roll. Do not add flavor conditions with no mechanical relevance.

**Duration guidance for `turns_remaining`:**
- 1–2 turns: single-event sensory/physical — winded, startled, dust in eyes
- 3–4 turns: minor debuffs within an encounter — rattled, pinned, light wound
- 5–8 turns: significant injuries or ongoing effects — injured arm, frightened, smoke inhalation
- 9+: major injuries; requires explicit narrative justification
- Omit / null: permanent, irreversible effects only

**Stat-to-condition heuristics:**
- Combat failure with strength/dexterity → consider `wounded`, `bleeding`
- Failed wits under pressure → consider `frightened` or `drugged`
- Failed strength/dexterity with sustained effort → consider `exhausted`
- Clean success or crit_success → no negative conditions

## State-presence rule

Sections not shown in the user prompt still exist in live game state. Absence is not removal. Only emit removals you can justify from the narration.

```

### Storyteller System Prompt

```
Emit one JSON object from the narration below. No prose, no markdown fences.

Omit any field with no change to communicate — no empty arrays, objects, or strings. Omitting means "no change," not deletion. Absence is not removal: state not shown in the user prompt still exists.

## Schema

```json
{
  "thread_resolve": [{"id": "...", "resolution_state": "resolved|failed|abandoned", "outcome": "...", "promote_to_world_state": true}],
  "thread_update": [{"id": "...", "progress": "...", "progress_kind": "advancement|setback|shift", "urgency": "background|normal|urgent", "active": true}],
  "thread_add": {"id": "...", "summary": "...", "scope": "scene|arc", "urgency": "normal"},
  "arc_resolve": {"resolution": "...", "visible_goal": "...", "goal_context": "...", "drop_threads": ["..."], "new_threads": [{"id": "...", "summary": "...", "scope": "arc", "urgency": "normal"}]},
   "goal_update": "...",
   "gm_beat": {"type": "...", "surface_as": "..."},
  "outcome_summary": "...",
  "actions": ["...", "...", "...", "..."]
}
```

## Threads

**Default: emit nothing.** Most turns produce zero thread operations. Do NOT emit an update because a thread was mentioned in the narration. Only emit when this turn's events changed the thread's trajectory — the tension advanced, pivoted, or resolved. A character acting within a thread is not a change. If the same tension would exist without this turn's events, omit.

**Thread IDs are 2–4 word broad conceptual buckets.** No proper nouns. If your ID contains a character name, location, or object name, it is too narrow. `enemy_contact_advance` ✓ — `naval_boarding_action` ✗ (it is a scene), `the_missing_ledger` ✗ (one object).

**`thread_resolve`:** Use when a thread concluded, failed, was absorbed into a broader thread, or urgency fully decayed. `promote_to_world_state: true` only when the outcome is a permanent world fact. Do NOT resolve threads still meaningfully active — prefer `active: false` for threads that might resurface. If a thread went unaddressed for 3+ turns, resolve or demote rather than update.

**`thread_update`:** Only `progress` (5–7 words max) — factual, confirmed by this turn's events, no speculation or forecast. `progress_kind` classifies the change. Do NOT restate what narration already showed. If the thread is no longer relevant, resolve it (thread_resolve) or set active: false, then create a new thread via thread_add — do not repurpose with progress that contradicts the summary.

**Before emitting `thread_add`:** scan all active AND latent threads for conceptual overlap. If the same tension is already tracked, use `thread_update` instead. Only create a new thread for genuinely distinct tension. Target: 2 arc threads + 1 scene thread at any time. Soft cap: 3 arc threads + 2 scene threads (5 total). Arc threads are tied explicitly to the campaign arc goal and persist across locations. Scene threads are localized, removed on location change, very short-term — if a thread would resolve after one scene, it belongs in `scene` scope or in the narration, not as an arc thread. Thread summaries: 5–7 words, a very broad conceptual bucket for the tension — not a detailed description. A good summary fits 3–4+ progress updates over the thread's lifetime.

**Scope:** `scene` threads auto-delete on location change. `arc` threads persist until arc resolution or explicit resolve. Choose deliberately. Broad buckets only — if your thread would resolve after one scene, it belongs in `scene` scope or in the narration, not in the arc.

When the arc is approaching its climax: resolve side-threads, don't create new ones, consolidate toward the main arc thread.

## Arc resolution

`arc_resolve` ends the current narrative chapter. Emit when: all arc threads are resolved/moot; the story's center of gravity has fundamentally shifted; the core conflict was decisively won or lost; the arc has coasted 8+ turns on the same goal. Do NOT emit to clean up — use thread operations for maintenance. Target cadence: 8–15 turns per arc. Prefer climactic pacing moments; avoid Breathe turns.

`goal_update` — the arc's direction shifted but the arc isn't over. Use this; reserve `arc_resolve` for chapter endings.

## GM Beat

`gm_beat`: one beat to shape the next turn, or `null`. Emit as `{"type": "...", "surface_as": "..."}`. Must be narratively specific — name NPCs, reference locations, tie to active threads. Never generic.

**Types:** `complication`, `revelation`, `opportunity`, `breathing_room`, `pressure`, `twist`, `setback`, `escalation`, `callback`
**Surfaces:** `ambient`, `event`, `npc_behavior`, `environmental`, `player_discovery`, `item`

**Pacing directive takes precedence** (from `pacing_context` in user turn):

| Directive | Beat |
|---|---|
| Breathe | `breathing_room` or `null` — do not add threads |
| Pressure | `complication` or `pressure` — update threads, don't add |
| Overwhelm | `pressure` or `escalation` — may add scene threads if gate allows |
| Tension | Follow roll band; no new threads unless concrete threat |
| Scene Imperative | Advance the story — choices that move forward or force a decision |

**Roll band** (when directive is Tension or absent):

| Band | Beat |
|---|---|
| crit_success / success | `opportunity`, `escalation`, or `breathing_room` |
| partial | `complication` or `pressure` |
| setback / fail | `breathing_room`, `null`, or `setback`. Never `escalation` or `pressure` — failure is the consequence. |
| No roll | `null` unless independent narrative reason |

Fail near-miss (final_total within 2 of threshold): `complication` acceptable. When deescalating, always prefer `breathing_room` or `null`.

**Diversity:** Don't repeat the same `type` more than twice consecutively. Vary `surface_as` turn to turn. After 3+ consecutive pressure beats, use a non-pressure type. `twist` and `callback` don't repeat within 2 turns except at major pivot moments.

**At major pivot moments** (near-death, failed plan succeeds, NPC decisive choice): prefer `revelation`, `twist`, or `callback` over another `complication`.

## Outcome summary

One sentence, third person, PC's name. What happened, what changed, what consequence followed. Facts only — no flavor. Omit if nothing of narrative significance occurred.

## Actions

Emit exactly 4 choices, ~10 words each. Every choice must begin with an active verb. Each choice must escalate, force a decision, or change things irreversibly. No meandering ("look at that", "talk to them"), no passive options (wait, observe), nothing generic enough for any protagonist in any setting. Span different postures — not variations of the same approach.

```


---

# TURN 1

**Input:** `I ride into Dustfall and tie my horse at the livery. The sun is hot and the main street is quiet. I head for the saloon.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## scene
Location: Marrow's Crossing
## Present NPCs (in scene right now)







## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)



## Current Turn: 1
=== PLAYER INPUT ===
I ride into Dustfall and tie my horse at the livery. The sun is hot and the main street is quiet. I head for the saloon.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## Inventory
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


## Location
Marrow's Crossing (marrows_crossing)
A market town built around the confluence of two rivers. Cobblestone streets,
timber-framed buildings, and the constant sound of water from the mills. The
town square has a stone well and a statue of the founder. Most shops are closing
for the evening.





## Characters

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (3 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.
- `clear_the_road_toughs` [ARC] (latent) [BACKGROUND] Deal with the toughs blocking the inn entrance.





## Prior History
## Recent Turns
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 1) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I ride into Dustfall and tie my horse at the livery. The sun is hot and the main street is quiet. I head for the saloon.
=== END PLAYER INPUT ===

**Outcome:** transition
Write the arrival at the new location, not the departure from this one. The scene moves forward.


```

### Extract Scene User Prompt
```
## location
`marrows_crossing` | Marrow's Crossing
A market town built around the confluence of two rivers. Cobblestone streets,
timber-framed buildings, and the constant sound of water from the mills. The
town square has a stone well and a statue of the founder. Most shops are closing
for the evening.


_(immutable section omitted — see Static Context > Seed State)_
## CURRENT TURN 1 NARRATION
You ride into Dustfall, the dry heat of the canyon pressing against your skin as you lead your horse to the livery. You tie the reins to a weathered hitching post and step toward the saloon, a low-slung building of sun-bleached timber that sits at the edge of the main thoroughfare. The street is unnervingly quiet, the midday sun baking the dust into a fine, choking powder that clings to your **Traveler's cloak**.

The heavy swinging doors of the saloon creak as you push through them, momentarily blocking out the glare. Inside, the air is thick with the scent of stale ale and unwashed bodies. A few patrons sit at shadowed tables, their eyes tracking your entrance with a practiced, wary indifference. At a corner table, a man in a stained leather jerkin sits alone, his broad shoulders hunched over a wooden tankard as he stares at nothing. He doesn't look up when you enter, but the sudden silence of the room makes the rhythmic thud of your boots feel far too loud.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
transition: The player travels to a new location and enters a specific establishment.
## CURRENT TURN 1 NARRATION
You ride into Dustfall, the dry heat of the canyon pressing against your skin as you lead your horse to the livery. You tie the reins to a weathered hitching post and step toward the saloon, a low-slung building of sun-bleached timber that sits at the edge of the main thoroughfare. The street is unnervingly quiet, the midday sun baking the dust into a fine, choking powder that clings to your **Traveler's cloak**.

The heavy swinging doors of the saloon creak as you push through them, momentarily blocking out the glare. Inside, the air is thick with the scent of stale ale and unwashed bodies. A few patrons sit at shadowed tables, their eyes tracking your entrance with a practiced, wary indifference. At a corner table, a man in a stained leather jerkin sits alone, his broad shoulders hunched over a wooden tankard as he stares at nothing. He doesn't look up when you enter, but the sudden silence of the room makes the rhythmic thud of your boots feel far too loud.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.


## Characters

- `matthew_estrada` | **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | hunched over tankard staring at nothing

- `saloon_patrons` | **Saloon Patrons** [PRESENT] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | watching entrance with wary indifference | last seen: Dustfall Saloon

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.



## location
**Dustfall Saloon** — The interior is dim and shadowed, contrasting with the baking heat outside; a heavy silence hangs over the patrons.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (3 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (3 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.
- `clear_the_road_toughs` [ARC] (latent) [BACKGROUND] Deal with the toughs blocking the inn entrance.


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## GM Beat
No beat currently carried over from the previous turn. Choose freely.

## player_intent
**transition**: The player travels to a new location and enters a specific establishment.

## CURRENT TURN 1 NARRATION
You ride into Dustfall, the dry heat of the canyon pressing against your skin as you lead your horse to the livery. You tie the reins to a weathered hitching post and step toward the saloon, a low-slung building of sun-bleached timber that sits at the edge of the main thoroughfare. The street is unnervingly quiet, the midday sun baking the dust into a fine, choking powder that clings to your **Traveler's cloak**.

The heavy swinging doors of the saloon creak as you push through them, momentarily blocking out the glare. Inside, the air is thick with the scent of stale ale and unwashed bodies. A few patrons sit at shadowed tables, their eyes tracking your entrance with a practiced, wary indifference. At a corner table, a man in a stained leather jerkin sits alone, his broad shoulders hunched over a wooden tankard as he stares at nothing. He doesn't look up when you enter, but the sudden silence of the room makes the rhythmic thud of your boots feel far too loud.
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
  "intent": "The player travels to a new location and enters a specific establishment.",
  "intent_verb": "transition",
  "target": "Dustfall saloon",
  "impossible": false,
  "scene_motion": "transition",
  "check": {
    "required": false
  }
}
```

### Narration

You ride into Dustfall, the dry heat of the canyon pressing against your skin as you lead your horse to the livery. You tie the reins to a weathered hitching post and step toward the saloon, a low-slung building of sun-bleached timber that sits at the edge of the main thoroughfare. The street is unnervingly quiet, the midday sun baking the dust into a fine, choking powder that clings to your **Traveler's cloak**.

The heavy swinging doors of the saloon creak as you push through them, momentarily blocking out the glare. Inside, the air is thick with the scent of stale ale and unwashed bodies. A few patrons sit at shadowed tables, their eyes tracking your entrance with a practiced, wary indifference. At a corner table, a man in a stained leather jerkin sits alone, his broad shoulders hunched over a wooden tankard as he stares at nothing. He doesn't look up when you enter, but the sudden silence of the room makes the rhythmic thud of your boots feel far too loud.

### Extract Scene

```json
{
  "scene_tags": [
    "tense_atmosphere",
    "discovery"
  ],
  "scene_tagline": "Entering the Dustfall Saloon",
  "location_change": {
    "id": "dustfall_saloon",
    "name": "Dustfall Saloon",
    "description": "A low-slung building of sun-bleached timber where the air is thick with stale ale and unwashed bodies."
  },
  "location_description": "The interior is dim and shadowed, contrasting with the baking heat outside; a heavy silence hangs over the patrons.",
  "compendium_npc_update": [
    {
      "id": "matthew_estrada",
      "aliases": [],
      "presence": "present",
      "notes": "hunched over tankard staring at nothing"
    },
    {
      "id": "saloon_patrons",
      "name": "Saloon Patrons",
      "bio": "A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers.",
      "aliases": [],
      "presence": "present",
      "notes": "watching entrance with wary indifference"
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [
    {
      "id": "traveler_cloak",
      "name": "Traveler's cloak",
      "notes": "Oiled wool, road-stained, covered in fine choking dust."
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "actions": [
    "Approach the hunched man to seek information about Caron.",
    "Order a drink and listen for rumors of the thugs.",
    "Scan the room for any sign of Halden's contact.",
    "Pay Edda for a room to plan your next move."
  ],
  "outcome_summary": "Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "clear_the_road_toughs",
      "active": true,
      "urgency": "background",
      "progress": "arrived at Dustfall Saloon",
      "progress_kind": "shift"
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

- ruling: est=1289t trimmed=False
- narrate: est=4055t trimmed=False
- extract.scene: est=3392t trimmed=False attempts=1
- extract.state: est=1930t trimmed=False attempts=1
- extract.storytell: est=3121t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 2

**Input:** `I step up to the bar and ask for a glass of water and whatever news there is. The bartender is wiping a glass and eyeing me.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## scene
Location: Dustfall Saloon
## Present NPCs (in scene right now)
- Matthew Estrada (Traveler)
- Saloon Patrons






## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)


## Last Turn Narrative (T1)
You ride into Dustfall, the dry heat of the canyon pressing against your skin as you lead your horse to the livery. You tie the reins to a weathered hitching post and step toward the saloon, a low-slung building of sun-bleached timber that sits at the edge of the main thoroughfare. The street is unnervingly quiet, the midday sun baking the dust into a fine, choking powder that clings to your **Traveler's cloak**.

The heavy swinging doors of the saloon creak as you push through them, momentarily blocking out the glare. Inside, the air is thick with the scent of stale ale and unwashed bodies. A few patrons sit at shadowed tables, their eyes tracking your entrance with a practiced, wary indifference. At a corner table, a man in a stained leather jerkin sits alone, his broad shoulders hunched over a wooden tankard as he stares at nothing. He doesn't look up when you enter, but the sudden silence of the room makes the rhythmic thud of your boots feel far too loud.


## Current Turn: 2
=== PLAYER INPUT ===
I step up to the bar and ask for a glass of water and whatever news there is. The bartender is wiping a glass and eyeing me.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## Inventory
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.


## Location
Dustfall Saloon (dustfall_saloon)
A low-slung building of sun-bleached timber where the air is thick with stale ale and unwashed bodies.




## Characters

- `matthew_estrada` | **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Dustfall Saloon

- `saloon_patrons` | **Saloon Patrons** [PRESENT] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Dustfall Saloon

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (3 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.
- `clear_the_road_toughs` [ARC] [BACKGROUND] Deal with the toughs blocking the inn entrance. (1 turns ago)   - [SHIFT] arrived at Dustfall Saloon





## Prior History
## Recent Turns

**T1:** You ride into Dustfall, the dry heat of the canyon pressing against your skin as you lead your horse to the livery. You tie the reins to a weathered hitching post and step toward the saloon, a low-slung building of sun-bleached timber that sits at the edge of the main thoroughfare. The street is unnervingly quiet, the midday sun baking the dust into a fine, choking powder that clings to your **Traveler's cloak**.

The heavy swinging doors of the saloon creak as you push through them, momentarily blocking out the glare. Inside, the air is thick with the scent of stale ale and unwashed bodies. A few patrons sit at shadowed tables, their eyes tracking your entrance with a practiced, wary indifference. At a corner table, a man in a stained leather jerkin sits alone, his broad shoulders hunched over a wooden tankard as he stares at nothing. He doesn't look up when you enter, but the sudden silence of the room makes the rhythmic thud of your boots feel far too loud.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 2) Result


**Band:** SUCCESS → The persuade succeeds cleanly. Clean success — you do what you intended.
**Roll:** d12: 9 + 1 (Charisma) → 11


**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.

=== PLAYER INPUT ===
I step up to the bar and ask for a glass of water and whatever news there is. The bartender is wiping a glass and eyeing me.
=== END PLAYER INPUT ===

**Beat:** PRESSURE — surface as `npc_behavior`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.**Outcome:** hold
Continue the current scene at its natural pace.


```

### Extract Scene User Prompt
```
## location
`dustfall_saloon` | Dustfall Saloon
A low-slung building of sun-bleached timber where the air is thick with stale ale and unwashed bodies.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T1 context)
You ride into Dustfall, the dry heat of the canyon pressing against your skin as you lead your horse to the livery. You tie the reins to a weathered hitching post and step toward the saloon, a low-slung building of sun-bleached timber that sits at the edge of the main thoroughfare. The street is unnervingly quiet, the midday sun baking the dust into a fine, choking powder that clings to your **Traveler's cloak**.

The heavy swinging doors of the saloon creak as you push through them, momentarily blocking out the glare. Inside, the air is thick with the scent of stale ale and unwashed bodies. A few patrons sit at shadowed tables, their eyes tracking your entrance with a practiced, wary indifference. At a corner table, a man in a stained leather jerkin sits alone, his broad shoulders hunched over a wooden tankard as he stares at nothing. He doesn't look up when you enter, but the sudden silence of the room makes the rhythmic thud of your boots feel far too loud.

## CURRENT TURN 2 NARRATION
You step up to the bar, your boots thudding against the floorboards as you request a glass of water and any news worth hearing. The bartender, a wiry man with sun-cracked skin, stops wiping a grime-streaked glass and leans his weight onto the counter. He eyes you with a slow, calculating gaze that lingers on your **Traveler's cloak** before meeting your eyes.

"Water's easy enough," he says, his voice a low rasp that barely carries over the settling dust of the room. He reaches for a ceramic mug, but doesn't move to fill it yet. "News? Most folks coming through Marrow's Crossing are looking to forget what they saw on the road, not find more of it."

He leans closer, lowering his voice as a couple of **Saloon Patrons** at a nearby table shift in their seats, their eyes darting toward you. "**Matthew Estrada** was asking after travelers earlier, but he didn't mention anyone looking for work or trouble. Most of the caravans are staying north of the confluence to avoid the dust storms, but there's talk of more riders than usual near the Crossed Keys."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
persuade: The player seeks information from the bartender while ordering a drink.
## CURRENT TURN 2 NARRATION
You step up to the bar, your boots thudding against the floorboards as you request a glass of water and any news worth hearing. The bartender, a wiry man with sun-cracked skin, stops wiping a grime-streaked glass and leans his weight onto the counter. He eyes you with a slow, calculating gaze that lingers on your **Traveler's cloak** before meeting your eyes.

"Water's easy enough," he says, his voice a low rasp that barely carries over the settling dust of the room. He reaches for a ceramic mug, but doesn't move to fill it yet. "News? Most folks coming through Marrow's Crossing are looking to forget what they saw on the road, not find more of it."

He leans closer, lowering his voice as a couple of **Saloon Patrons** at a nearby table shift in their seats, their eyes darting toward you. "**Matthew Estrada** was asking after travelers earlier, but he didn't mention anyone looking for work or trouble. Most of the caravans are staying north of the confluence to avoid the dust storms, but there's talk of more riders than usual near the Crossed Keys."
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.


## Characters

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [PRESENT] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | leaning on counter, eyeing your cloak | last seen: Dustfall Saloon

- `matthew_estrada` | **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | hunched over tankard at corner table | last seen: Dustfall Saloon

- `saloon_patrons` | **Saloon Patrons** [PRESENT] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Dustfall Saloon

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.



## location
**Dustfall Saloon** — The bar counter is grime-streaked and worn, providing a narrow barrier between you and the wiry bartender.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (3 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (3 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.
- `clear_the_road_toughs` [ARC] [BACKGROUND] Deal with the toughs blocking the inn entrance. (1 turns ago)   - [SHIFT] arrived at Dustfall Saloon


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## GM Beat
Type: **PRESSURE**
Surface: `npc_behavior`
Expires: Turn 3

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.

## Recent Beats
T1: PRESSURE (npc_behavior)


## rules_outcome
Band: SUCCESS. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.

## prior turn context

**T1:** You ride into Dustfall, the dry heat of the canyon pressing against your skin as you lead your horse to the livery. You tie the reins to a weathered hitching post and step toward the saloon, a low-slung building of sun-bleached timber that sits at the edge of the main thoroughfare. The street is unnervingly quiet, the midday sun baking the dust into a fine, choking powder that clings to your **Traveler's cloak**.

The heavy swinging doors of the saloon creak as you push through them, momentarily blocking out the glare. Inside, the air is thick with the scent of stale ale and unwashed bodies. A few patrons sit at shadowed tables, their eyes tracking your entrance with a practiced, wary indifference. At a corner table, a man in a stained leather jerkin sits alone, his broad shoulders hunched over a wooden tankard as he stares at nothing. He doesn't look up when you enter, but the sudden silence of the room makes the rhythmic thud of your boots feel far too loud.


## player_intent
**persuade**: The player seeks information from the bartender while ordering a drink.

## CURRENT TURN 2 NARRATION
You step up to the bar, your boots thudding against the floorboards as you request a glass of water and any news worth hearing. The bartender, a wiry man with sun-cracked skin, stops wiping a grime-streaked glass and leans his weight onto the counter. He eyes you with a slow, calculating gaze that lingers on your **Traveler's cloak** before meeting your eyes.

"Water's easy enough," he says, his voice a low rasp that barely carries over the settling dust of the room. He reaches for a ceramic mug, but doesn't move to fill it yet. "News? Most folks coming through Marrow's Crossing are looking to forget what they saw on the road, not find more of it."

He leans closer, lowering his voice as a couple of **Saloon Patrons** at a nearby table shift in their seats, their eyes darting toward you. "**Matthew Estrada** was asking after travelers earlier, but he didn't mention anyone looking for work or trouble. Most of the caravans are staying north of the confluence to avoid the dust storms, but there's talk of more riders than usual near the Crossed Keys."
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
  "intent": "The player seeks information from the bartender while ordering a drink.",
  "intent_verb": "persuade",
  "target": "the bartender",
  "scene_motion": "hold",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "easy"
  }
}
```

### Narration

You step up to the bar, your boots thudding against the floorboards as you request a glass of water and any news worth hearing. The bartender, a wiry man with sun-cracked skin, stops wiping a grime-streaked glass and leans his weight onto the counter. He eyes you with a slow, calculating gaze that lingers on your **Traveler's cloak** before meeting your eyes.

"Water's easy enough," he says, his voice a low rasp that barely carries over the settling dust of the room. He reaches for a ceramic mug, but doesn't move to fill it yet. "News? Most folks coming through Marrow's Crossing are looking to forget what they saw on the road, not find more of it."

He leans closer, lowering his voice as a couple of **Saloon Patrons** at a nearby table shift in their seats, their eyes darting toward you. "**Matthew Estrada** was asking after travelers earlier, but he didn't mention anyone looking for work or trouble. Most of the caravans are staying north of the confluence to avoid the dust storms, but there's talk of more riders than usual near the Crossed Keys."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "investigation"
  ],
  "scene_tagline": "Whispers Behind the Bar",
  "location_description": "The bar counter is grime-streaked and worn, providing a narrow barrier between you and the wiry bartender.",
  "compendium_npc_update": [
    {
      "id": "bartender_dustfall",
      "name": "Bartender",
      "title": "Saloon Bartender",
      "bio": "A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements.",
      "aliases": [],
      "presence": "present",
      "notes": "leaning on counter, eyeing your cloak"
    },
    {
      "id": "matthew_estrada",
      "name": "Matthew Estrada",
      "aliases": [],
      "presence": "present",
      "notes": "hunched over tankard at corner table"
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [
    {
      "id": "traveler_cloak",
      "name": "Traveler's cloak",
      "notes": "Oiled wool, road-stained, covered in fine choking dust."
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "actions": [
    "Ask the bartender for more details on the riders.",
    "Approach Matthew Estrada at his corner table.",
    "Pay for the water and head toward the inn.",
    "Scan the saloon patrons for any suspicious movement."
  ],
  "outcome_summary": "The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.",
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "clear_the_road_toughs",
      "active": true,
      "urgency": "normal",
      "progress": "investigating rumors near the inn",
      "progress_kind": "shift"
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

- ruling: est=1589t trimmed=False
- narrate: est=4466t trimmed=False
- extract.scene: est=3732t trimmed=False attempts=1
- extract.state: est=1954t trimmed=False attempts=1
- extract.storytell: est=3654t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 3

**Input:** `I lean on the bar and ask what happened to Old Man Harker. The bartender seems reluctant but starts talking.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## scene
Location: Dustfall Saloon
## Present NPCs (in scene right now)
- Bartender (Saloon Bartender)
- Matthew Estrada (Traveler)
- Saloon Patrons






## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)


## Last Turn Narrative (T2)
You step up to the bar, your boots thudding against the floorboards as you request a glass of water and any news worth hearing. The bartender, a wiry man with sun-cracked skin, stops wiping a grime-streaked glass and leans his weight onto the counter. He eyes you with a slow, calculating gaze that lingers on your **Traveler's cloak** before meeting your eyes.

"Water's easy enough," he says, his voice a low rasp that barely carries over the settling dust of the room. He reaches for a ceramic mug, but doesn't move to fill it yet. "News? Most folks coming through Marrow's Crossing are looking to forget what they saw on the road, not find more of it."

He leans closer, lowering his voice as a couple of **Saloon Patrons** at a nearby table shift in their seats, their eyes darting toward you. "**Matthew Estrada** was asking after travelers earlier, but he didn't mention anyone looking for work or trouble. Most of the caravans are staying north of the confluence to avoid the dust storms, but there's talk of more riders than usual near the Crossed Keys."


## Current Turn: 3
=== PLAYER INPUT ===
I lean on the bar and ask what happened to Old Man Harker. The bartender seems reluctant but starts talking.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## Inventory
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.


## Location
Dustfall Saloon (dustfall_saloon)
The bar counter is grime-streaked and worn, providing a narrow barrier between you and the wiry bartender.




## Characters

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [PRESENT] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Dustfall Saloon

- `matthew_estrada` | **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Dustfall Saloon

- `saloon_patrons` | **Saloon Patrons** [PRESENT] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Dustfall Saloon

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (3 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.
- `clear_the_road_toughs` [ARC] [NORMAL] Deal with the toughs blocking the inn entrance. (1 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn





## Prior History
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

## Recent Turns

**T2:** You step up to the bar, your boots thudding against the floorboards as you request a glass of water and any news worth hearing. The bartender, a wiry man with sun-cracked skin, stops wiping a grime-streaked glass and leans his weight onto the counter. He eyes you with a slow, calculating gaze that lingers on your **Traveler's cloak** before meeting your eyes.

"Water's easy enough," he says, his voice a low rasp that barely carries over the settling dust of the room. He reaches for a ceramic mug, but doesn't move to fill it yet. "News? Most folks coming through Marrow's Crossing are looking to forget what they saw on the road, not find more of it."

He leans closer, lowering his voice as a couple of **Saloon Patrons** at a nearby table shift in their seats, their eyes darting toward you. "**Matthew Estrada** was asking after travelers earlier, but he didn't mention anyone looking for work or trouble. Most of the caravans are staying north of the confluence to avoid the dust storms, but there's talk of more riders than usual near the Crossed Keys."

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 3) Result


**Band:** SUCCESS → The persuade succeeds cleanly. Clean success — you do what you intended.
**Roll:** d12: 9 + 1 (Charisma) → 10


**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.

=== PLAYER INPUT ===
I lean on the bar and ask what happened to Old Man Harker. The bartender seems reluctant but starts talking.
=== END PLAYER INPUT ===

**Beat:** COMPLICATION — surface as `npc_behavior`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.**Outcome:** hold
Continue the current scene at its natural pace.


```

### Extract Scene User Prompt
```
## location
`dustfall_saloon` | Dustfall Saloon
The bar counter is grime-streaked and worn, providing a narrow barrier between you and the wiry bartender.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T2 context)
You step up to the bar, your boots thudding against the floorboards as you request a glass of water and any news worth hearing. The bartender, a wiry man with sun-cracked skin, stops wiping a grime-streaked glass and leans his weight onto the counter. He eyes you with a slow, calculating gaze that lingers on your **Traveler's cloak** before meeting your eyes.

"Water's easy enough," he says, his voice a low rasp that barely carries over the settling dust of the room. He reaches for a ceramic mug, but doesn't move to fill it yet. "News? Most folks coming through Marrow's Crossing are looking to forget what they saw on the road, not find more of it."

He leans closer, lowering his voice as a couple of **Saloon Patrons** at a nearby table shift in their seats, their eyes darting toward you. "**Matthew Estrada** was asking after travelers earlier, but he didn't mention anyone looking for work or trouble. Most of the caravans are staying north of the confluence to avoid the dust storms, but there's talk of more riders than usual near the Crossed Keys."

## CURRENT TURN 3 NARRATION
You lean your weight against the grime-streaked bar, lowering your voice to match his. "What happened to Old Man Harker?"

The **Bartender** pauses, his hand hovering over a ceramic mug. He glances toward the shadowed corner where two **Saloon Patrons** sit, their silence suddenly heavy. He wipes a stray bead of sweat from his forehead with a calloused thumb, his calculating gaze flickering toward the door before settling back on you.

"Harker?" he rasps, leaning in so close you can smell the stale ale on his breath. "He's gone to ground. Most folks say he just decided to skip town without paying his tabs, but the word near the mills is different." He taps a rhythmic, nervous beat against the wood of the counter. "They say he was seen near the Crossed Keys right before those riders started circling. Now, no one's seen him since that dust storm rolled through, and nobody's talking about it if they want to keep their teeth."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
persuade: The player seeks information regarding the fate of Old Man Harker from a reluctant bartender.
## CURRENT TURN 3 NARRATION
You lean your weight against the grime-streaked bar, lowering your voice to match his. "What happened to Old Man Harker?"

The **Bartender** pauses, his hand hovering over a ceramic mug. He glances toward the shadowed corner where two **Saloon Patrons** sit, their silence suddenly heavy. He wipes a stray bead of sweat from his forehead with a calloused thumb, his calculating gaze flickering toward the door before settling back on you.

"Harker?" he rasps, leaning in so close you can smell the stale ale on his breath. "He's gone to ground. Most folks say he just decided to skip town without paying his tabs, but the word near the mills is different." He taps a rhythmic, nervous beat against the wood of the counter. "They say he was seen near the Crossed Keys right before those riders started circling. Now, no one's seen him since that dust storm rolled through, and nobody's talking about it if they want to keep their teeth."
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.


## Characters

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [PRESENT] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | tapping counter nervously — sharing secrets | last seen: Dustfall Saloon

- `matthew_estrada` | **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Dustfall Saloon

- `saloon_patrons` | **Saloon Patrons** [PRESENT] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Dustfall Saloon

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.



## location
**Dustfall Saloon** — The air in the saloon feels heavier, thick with the smell of stale ale and the unspoken tension of the patrons watching from the shadows.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (3 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (3 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.
- `clear_the_road_toughs` [ARC] [NORMAL] Deal with the toughs blocking the inn entrance. (1 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## GM Beat
Type: **COMPLICATION**
Surface: `npc_behavior`
Expires: Turn 4

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.

## Recent Beats
T1: PRESSURE (npc_behavior)
T2: COMPLICATION (npc_behavior)


## rules_outcome
Band: SUCCESS. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.

## Recent Outcomes
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

## prior turn context

**T2:** You step up to the bar, your boots thudding against the floorboards as you request a glass of water and any news worth hearing. The bartender, a wiry man with sun-cracked skin, stops wiping a grime-streaked glass and leans his weight onto the counter. He eyes you with a slow, calculating gaze that lingers on your **Traveler's cloak** before meeting your eyes.

"Water's easy enough," he says, his voice a low rasp that barely carries over the settling dust of the room. He reaches for a ceramic mug, but doesn't move to fill it yet. "News? Most folks coming through Marrow's Crossing are looking to forget what they saw on the road, not find more of it."

He leans closer, lowering his voice as a couple of **Saloon Patrons** at a nearby table shift in their seats, their eyes darting toward you. "**Matthew Estrada** was asking after travelers earlier, but he didn't mention anyone looking for work or trouble. Most of the caravans are staying north of the confluence to avoid the dust storms, but there's talk of more riders than usual near the Crossed Keys."


## player_intent
**persuade**: The player seeks information regarding the fate of Old Man Harker from a reluctant bartender.

## CURRENT TURN 3 NARRATION
You lean your weight against the grime-streaked bar, lowering your voice to match his. "What happened to Old Man Harker?"

The **Bartender** pauses, his hand hovering over a ceramic mug. He glances toward the shadowed corner where two **Saloon Patrons** sit, their silence suddenly heavy. He wipes a stray bead of sweat from his forehead with a calloused thumb, his calculating gaze flickering toward the door before settling back on you.

"Harker?" he rasps, leaning in so close you can smell the stale ale on his breath. "He's gone to ground. Most folks say he just decided to skip town without paying his tabs, but the word near the mills is different." He taps a rhythmic, nervous beat against the wood of the counter. "They say he was seen near the Crossed Keys right before those riders started circling. Now, no one's seen him since that dust storm rolled through, and nobody's talking about it if they want to keep their teeth."
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
  "intent": "The player seeks information regarding the fate of Old Man Harker from a reluctant bartender.",
  "intent_verb": "persuade",
  "target": "Bartender",
  "scene_motion": "hold",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal"
  }
}
```

### Narration

You lean your weight against the grime-streaked bar, lowering your voice to match his. "What happened to Old Man Harker?"

The **Bartender** pauses, his hand hovering over a ceramic mug. He glances toward the shadowed corner where two **Saloon Patrons** sit, their silence suddenly heavy. He wipes a stray bead of sweat from his forehead with a calloused thumb, his calculating gaze flickering toward the door before settling back on you.

"Harker?" he rasps, leaning in so close you can smell the stale ale on his breath. "He's gone to ground. Most folks say he just decided to skip town without paying his tabs, but the word near the mills is different." He taps a rhythmic, nervous beat against the wood of the counter. "They say he was seen near the Crossed Keys right before those riders started circling. Now, no one's seen him since that dust storm rolled through, and nobody's talking about it if they want to keep their teeth."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "investigation"
  ],
  "scene_tagline": "Whispers of a Vanished Man",
  "location_description": "The air in the saloon feels heavier, thick with the smell of stale ale and the unspoken tension of the patrons watching from the shadows.",
  "compendium_npc_update": [
    {
      "id": "bartender_dustfall",
      "aliases": [],
      "notes": "tapping counter nervously \u2014 sharing secrets"
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
  "actions": [
    "Bribe the bartender for specific details on the riders.",
    "Confront the silent patrons to see if they know more.",
    "Leave the saloon immediately to investigate the Crossed Keys.",
    "Search the saloon for any sign of Harker's belongings."
  ],
  "outcome_summary": "Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.",
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "clear_the_road_toughs",
      "active": true,
      "urgency": "normal",
      "progress": "investigating rumors near the inn",
      "progress_kind": "advancement"
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

- ruling: est=1619t trimmed=False
- narrate: est=4604t trimmed=False
- extract.scene: est=3795t trimmed=False attempts=1
- extract.state: est=1924t trimmed=False attempts=1
- extract.storytell: est=3703t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 4

**Input:** `I head over to the assay office to see if Harker filed any claims recently. I knock on the door and introduce myself.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## scene
Location: Dustfall Saloon
## Present NPCs (in scene right now)
- Bartender (Saloon Bartender)
- Matthew Estrada (Traveler)
- Saloon Patrons






## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)


## Last Turn Narrative (T3)
You lean your weight against the grime-streaked bar, lowering your voice to match his. "What happened to Old Man Harker?"

The **Bartender** pauses, his hand hovering over a ceramic mug. He glances toward the shadowed corner where two **Saloon Patrons** sit, their silence suddenly heavy. He wipes a stray bead of sweat from his forehead with a calloused thumb, his calculating gaze flickering toward the door before settling back on you.

"Harker?" he rasps, leaning in so close you can smell the stale ale on his breath. "He's gone to ground. Most folks say he just decided to skip town without paying his tabs, but the word near the mills is different." He taps a rhythmic, nervous beat against the wood of the counter. "They say he was seen near the Crossed Keys right before those riders started circling. Now, no one's seen him since that dust storm rolled through, and nobody's talking about it if they want to keep their teeth."


## Current Turn: 4
=== PLAYER INPUT ===
I head over to the assay office to see if Harker filed any claims recently. I knock on the door and introduce myself.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## Inventory
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.


## Location
Dustfall Saloon (dustfall_saloon)
The air in the saloon feels heavier, thick with the smell of stale ale and the unspoken tension of the patrons watching from the shadows.




## Characters

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [PRESENT] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Dustfall Saloon

- `matthew_estrada` | **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Dustfall Saloon

- `saloon_patrons` | **Saloon Patrons** [PRESENT] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Dustfall Saloon

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (3 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.
- `clear_the_road_toughs` [ARC] [NORMAL] Deal with the toughs blocking the inn entrance. (1 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn





## Prior History
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.

## Recent Turns

**T3:** You lean your weight against the grime-streaked bar, lowering your voice to match his. "What happened to Old Man Harker?"

The **Bartender** pauses, his hand hovering over a ceramic mug. He glances toward the shadowed corner where two **Saloon Patrons** sit, their silence suddenly heavy. He wipes a stray bead of sweat from his forehead with a calloused thumb, his calculating gaze flickering toward the door before settling back on you.

"Harker?" he rasps, leaning in so close you can smell the stale ale on his breath. "He's gone to ground. Most folks say he just decided to skip town without paying his tabs, but the word near the mills is different." He taps a rhythmic, nervous beat against the wood of the counter. "They say he was seen near the Crossed Keys right before those riders started circling. Now, no one's seen him since that dust storm rolled through, and nobody's talking about it if they want to keep their teeth."

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 4) Result


**Band:** SETBACK → The persuade results in a setback. They're listening, but now they want something in return.
**Roll:** d12: 4 + 1 (Charisma) → 6


**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.

=== PLAYER INPUT ===
I head over to the assay office to see if Harker filed any claims recently. I knock on the door and introduce myself.
=== END PLAYER INPUT ===

**Beat:** COMPLICATION — surface as `npc_behavior`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.**Outcome:** transition
Write the arrival at the new location, not the departure from this one. The scene moves forward.


```

### Extract Scene User Prompt
```
## location
`dustfall_saloon` | Dustfall Saloon
The air in the saloon feels heavier, thick with the smell of stale ale and the unspoken tension of the patrons watching from the shadows.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T3 context)
You lean your weight against the grime-streaked bar, lowering your voice to match his. "What happened to Old Man Harker?"

The **Bartender** pauses, his hand hovering over a ceramic mug. He glances toward the shadowed corner where two **Saloon Patrons** sit, their silence suddenly heavy. He wipes a stray bead of sweat from his forehead with a calloused thumb, his calculating gaze flickering toward the door before settling back on you.

"Harker?" he rasps, leaning in so close you can smell the stale ale on his breath. "He's gone to ground. Most folks say he just decided to skip town without paying his tabs, but the word near the mills is different." He taps a rhythmic, nervous beat against the wood of the counter. "They say he was seen near the Crossed Keys right before those riders started circling. Now, no one's seen him since that dust storm rolled through, and nobody's talking about it if they want to keep their teeth."

## CURRENT TURN 4 NARRATION
You arrive at the assay office, a squat stone building tucked between two mills near the riverbank. You step up to the heavy oak door and knock, announcing your name as you wait. 

The door creaks open to reveal **Silas Vance**, a man with ink-stained fingers and spectacles perched precariously on a sharp nose. He peers at you through thick lenses, his eyes narrowing with suspicion as he grips the edge of the doorframe. He doesn't step aside to let you in; instead, he leans out into the street, blocking the threshold.

"We aren't taking visitors today," **Silas Vance** says, his voice thin and defensive. He glances over your shoulder toward the road, his posture stiffening as if expecting someone to follow you. "Unless you're here to pay a filing fee or settle a discrepancy, move along. I've got no time for idle curiosity or travelers looking for trouble."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
persuade: The player seeks information regarding Old Man Harker's recent activities by visiting the assay office.
## CURRENT TURN 4 NARRATION
You arrive at the assay office, a squat stone building tucked between two mills near the riverbank. You step up to the heavy oak door and knock, announcing your name as you wait. 

The door creaks open to reveal **Silas Vance**, a man with ink-stained fingers and spectacles perched precariously on a sharp nose. He peers at you through thick lenses, his eyes narrowing with suspicion as he grips the edge of the doorframe. He doesn't step aside to let you in; instead, he leans out into the street, blocking the threshold.

"We aren't taking visitors today," **Silas Vance** says, his voice thin and defensive. He glances over your shoulder toward the road, his posture stiffening as if expecting someone to follow you. "Unless you're here to pay a filing fee or settle a discrepancy, move along. I've got no time for idle curiosity or travelers looking for trouble."
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.


## Characters

- `silas_vance` | **Silas Vance** (Assay Clerk) [PRESENT] — A man with ink-stained fingers and spectacles perched precariously on a sharp nose. He possesses a thin, defensive voice and appears perpetually on edge. | blocking the threshold defensively | last seen: Assay Office

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Dustfall Saloon

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Dustfall Saloon

- `saloon_patrons` | **Saloon Patrons** [KNOWN] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Dustfall Saloon

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.



## location
**Assay Office** — A squat stone building situated between two mills near the riverbank.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (3 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (3 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.
- `clear_the_road_toughs` [ARC] [NORMAL] Deal with the toughs blocking the inn entrance. (1 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: Scene Pressure; Resolve a Threat
Gate: allow

## GM Beat
Type: **COMPLICATION**
Surface: `npc_behavior`
Expires: Turn 5

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.

## Recent Beats
T1: PRESSURE (npc_behavior)
T2: COMPLICATION (npc_behavior)
T3: COMPLICATION (npc_behavior)


## rules_outcome
Band: SETBACK. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.

## Recent Outcomes
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.
- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.

## prior turn context

**T3:** You lean your weight against the grime-streaked bar, lowering your voice to match his. "What happened to Old Man Harker?"

The **Bartender** pauses, his hand hovering over a ceramic mug. He glances toward the shadowed corner where two **Saloon Patrons** sit, their silence suddenly heavy. He wipes a stray bead of sweat from his forehead with a calloused thumb, his calculating gaze flickering toward the door before settling back on you.

"Harker?" he rasps, leaning in so close you can smell the stale ale on his breath. "He's gone to ground. Most folks say he just decided to skip town without paying his tabs, but the word near the mills is different." He taps a rhythmic, nervous beat against the wood of the counter. "They say he was seen near the Crossed Keys right before those riders started circling. Now, no one's seen him since that dust storm rolled through, and nobody's talking about it if they want to keep their teeth."


## player_intent
**persuade**: The player seeks information regarding Old Man Harker's recent activities by visiting the assay office.

## CURRENT TURN 4 NARRATION
You arrive at the assay office, a squat stone building tucked between two mills near the riverbank. You step up to the heavy oak door and knock, announcing your name as you wait. 

The door creaks open to reveal **Silas Vance**, a man with ink-stained fingers and spectacles perched precariously on a sharp nose. He peers at you through thick lenses, his eyes narrowing with suspicion as he grips the edge of the doorframe. He doesn't step aside to let you in; instead, he leans out into the street, blocking the threshold.

"We aren't taking visitors today," **Silas Vance** says, his voice thin and defensive. He glances over your shoulder toward the road, his posture stiffening as if expecting someone to follow you. "Unless you're here to pay a filing fee or settle a discrepancy, move along. I've got no time for idle curiosity or travelers looking for trouble."
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
  "intent": "The player seeks information regarding Old Man Harker's recent activities by visiting the assay office.",
  "intent_verb": "persuade",
  "target": "Assay Office Clerk",
  "scene_motion": "transition",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "easy"
  }
}
```

### Narration

You arrive at the assay office, a squat stone building tucked between two mills near the riverbank. You step up to the heavy oak door and knock, announcing your name as you wait. 

The door creaks open to reveal **Silas Vance**, a man with ink-stained fingers and spectacles perched precariously on a sharp nose. He peers at you through thick lenses, his eyes narrowing with suspicion as he grips the edge of the doorframe. He doesn't step aside to let you in; instead, he leans out into the street, blocking the threshold.

"We aren't taking visitors today," **Silas Vance** says, his voice thin and defensive. He glances over your shoulder toward the road, his posture stiffening as if expecting someone to follow you. "Unless you're here to pay a filing fee or settle a discrepancy, move along. I've got no time for idle curiosity or travelers looking for trouble."

### Extract Scene

```json
{
  "scene_tags": [
    "investigation",
    "tense_conversation"
  ],
  "scene_tagline": "A Closed Door at the Assay Office",
  "location_change": {
    "id": "assay_office",
    "name": "Assay Office",
    "description": "A squat stone building situated between two mills near the riverbank."
  },
  "compendium_npc_update": [
    {
      "id": "silas_vance",
      "name": "Silas Vance",
      "title": "Assay Clerk",
      "bio": "A man with ink-stained fingers and spectacles perched precariously on a sharp nose. He possesses a thin, defensive voice and appears perpetually on edge.",
      "aliases": [],
      "presence": "present",
      "notes": "blocking the threshold defensively"
    },
    {
      "id": "bartender_dustfall",
      "aliases": [],
      "presence": "known"
    },
    {
      "id": "matthew_estrada",
      "aliases": [],
      "presence": "known"
    },
    {
      "id": "saloon_patrons",
      "aliases": [],
      "presence": "known"
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
  "actions": [
    "Offer a filing fee to gain entry into the office.",
    "Press Silas for information about Harker's recent activities.",
    "Show the brass key to provoke a reaction from Silas.",
    "Leave the office to find another source of information."
  ],
  "outcome_summary": "Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.",
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [],
  "thread_add": {
    "id": "investigate_harker_disappearance",
    "summary": "Find truth behind Harker's disappearance",
    "scope": "scene",
    "active": true,
    "urgency": "normal",
    "progress": []
  },
  "thread_update": [
    {
      "id": "deliver_the_ledger",
      "active": true,
      "urgency": "normal",
      "progress": "Approaching the Assay Office to investigate",
      "progress_kind": "shift"
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

- ruling: est=1585t trimmed=False
- narrate: est=4637t trimmed=False
- extract.scene: est=3748t trimmed=False attempts=1
- extract.state: est=1907t trimmed=False attempts=1
- extract.storytell: est=3750t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 5

**Input:** `I walk to the sheriff's office and ask if he's filed a missing person report for Harker. I want to see if the law is involved.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## scene
Location: Assay Office
## Present NPCs (in scene right now)
- Silas Vance (Assay Clerk)









## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)


## Last Turn Narrative (T4)
You arrive at the assay office, a squat stone building tucked between two mills near the riverbank. You step up to the heavy oak door and knock, announcing your name as you wait. 

The door creaks open to reveal **Silas Vance**, a man with ink-stained fingers and spectacles perched precariously on a sharp nose. He peers at you through thick lenses, his eyes narrowing with suspicion as he grips the edge of the doorframe. He doesn't step aside to let you in; instead, he leans out into the street, blocking the threshold.

"We aren't taking visitors today," **Silas Vance** says, his voice thin and defensive. He glances over your shoulder toward the road, his posture stiffening as if expecting someone to follow you. "Unless you're here to pay a filing fee or settle a discrepancy, move along. I've got no time for idle curiosity or travelers looking for trouble."


## Current Turn: 5
=== PLAYER INPUT ===
I walk to the sheriff's office and ask if he's filed a missing person report for Harker. I want to see if the law is involved.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## Inventory
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.


## Location
Assay Office (assay_office)
A squat stone building situated between two mills near the riverbank.




## Characters

- `silas_vance` | **Silas Vance** (Assay Clerk) [PRESENT] — A man with ink-stained fingers and spectacles perched precariously on a sharp nose. He possesses a thin, defensive voice and appears perpetually on edge. | last seen: Assay Office

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office

- `saloon_patrons` | **Saloon Patrons** [KNOWN] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Assay Office

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (1 turns ago)   - [SHIFT] Approaching the Assay Office to investigate
- `clear_the_road_toughs` [ARC] [NORMAL] Deal with the toughs blocking the inn entrance. (2 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [SCENE] [NORMAL] Find truth behind Harker's disappearance





## Prior History
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.

- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.

## Recent Turns

**T4:** You arrive at the assay office, a squat stone building tucked between two mills near the riverbank. You step up to the heavy oak door and knock, announcing your name as you wait. 

The door creaks open to reveal **Silas Vance**, a man with ink-stained fingers and spectacles perched precariously on a sharp nose. He peers at you through thick lenses, his eyes narrowing with suspicion as he grips the edge of the doorframe. He doesn't step aside to let you in; instead, he leans out into the street, blocking the threshold.

"We aren't taking visitors today," **Silas Vance** says, his voice thin and defensive. He glances over your shoulder toward the road, his posture stiffening as if expecting someone to follow you. "Unless you're here to pay a filing fee or settle a discrepancy, move along. I've got no time for idle curiosity or travelers looking for trouble."

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 5) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I walk to the sheriff's office and ask if he's filed a missing person report for Harker. I want to see if the law is involved.
=== END PLAYER INPUT ===

**Beat:** BREATHING ROOM — surface as `ambient`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.**Outcome:** transition
Write the arrival at the new location, not the departure from this one. The scene moves forward.


```

### Extract Scene User Prompt
```
## location
`assay_office` | Assay Office
A squat stone building situated between two mills near the riverbank.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T4 context)
You arrive at the assay office, a squat stone building tucked between two mills near the riverbank. You step up to the heavy oak door and knock, announcing your name as you wait. 

The door creaks open to reveal **Silas Vance**, a man with ink-stained fingers and spectacles perched precariously on a sharp nose. He peers at you through thick lenses, his eyes narrowing with suspicion as he grips the edge of the doorframe. He doesn't step aside to let you in; instead, he leans out into the street, blocking the threshold.

"We aren't taking visitors today," **Silas Vance** says, his voice thin and defensive. He glances over your shoulder toward the road, his posture stiffening as if expecting someone to follow you. "Unless you're here to pay a filing fee or settle a discrepancy, move along. I've got no time for idle curiosity or travelers looking for trouble."

## CURRENT TURN 5 NARRATION
You step away from the stone walls of the Assay Office and make your way toward the sheriff's station, a low-slung building with a heavy iron-reinforced door located near the town square. The midday sun beats down on the dust-choked streets, but the air remains heavy with a restless energy as travelers move between the mills.

You push through the entrance of the station to find a small, cluttered room smelling of old parchment and stale tobacco. Behind a sturdy wooden desk sits **Kaelen Vance**, a woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She doesn't look up from her ledger immediately, her quill scratching rhythmically against the page.

"I'm looking to see if a missing person report has been filed for Harker," you say.

**Kaelen Vance** pauses, her quill hovering just above the paper. She looks up, her gaze steady and unreadable as she leans back in her chair. "Harker? No report on my desk yet," she says, her voice low and level. "Men go missing near the mills all the time when they've had too much ale or a bad run of luck. Unless a family comes knocking with a name and a reason to worry, we don't waste ink on ghosts."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
persuade: The player wants to inquire at the sheriff's office regarding whether a missing person report has been filed for Harker to determine law enforcement involvement.
## CURRENT TURN 5 NARRATION
You step away from the stone walls of the Assay Office and make your way toward the sheriff's station, a low-slung building with a heavy iron-reinforced door located near the town square. The midday sun beats down on the dust-choked streets, but the air remains heavy with a restless energy as travelers move between the mills.

You push through the entrance of the station to find a small, cluttered room smelling of old parchment and stale tobacco. Behind a sturdy wooden desk sits **Kaelen Vance**, a woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She doesn't look up from her ledger immediately, her quill scratching rhythmically against the page.

"I'm looking to see if a missing person report has been filed for Harker," you say.

**Kaelen Vance** pauses, her quill hovering just above the paper. She looks up, her gaze steady and unreadable as she leans back in her chair. "Harker? No report on my desk yet," she says, her voice low and level. "Men go missing near the mills all the time when they've had too much ale or a bad run of luck. Unless a family comes knocking with a name and a reason to worry, we don't waste ink on ghosts."
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.

## PC conditions (this turn)
- dusty: Dusty — Fine dust from the streets clings to your clothes and skin.


## Characters

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [PRESENT] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | leaning back, scanning player | last seen: Sheriff's Station

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office

- `saloon_patrons` | **Saloon Patrons** [KNOWN] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Assay Office

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

- `silas_vance` | **Silas Vance** (Assay Clerk) [KNOWN] — A man with ink-stained fingers and spectacles perched precariously on a sharp nose. He possesses a thin, defensive voice and appears perpetually on edge. | last seen: Assay Office



## location
**Sheriff's Station** — The interior is a cramped space dominated by a sturdy wooden desk and the rhythmic scratching of a quill.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (4 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (1 turns ago)   - [SHIFT] Approaching the Assay Office to investigate
- `clear_the_road_toughs` [ARC] [NORMAL] Deal with the toughs blocking the inn entrance. (2 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [SCENE] [NORMAL] Find truth behind Harker's disappearance


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## GM Beat
Type: **BREATHING ROOM**
Surface: `ambient`
Expires: Turn 6

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.

## Recent Beats
T1: PRESSURE (npc_behavior)
T2: COMPLICATION (npc_behavior)
T3: COMPLICATION (npc_behavior)
T4: BREATHING ROOM (ambient)


## Recent Outcomes
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.
- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.
- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.

## prior turn context

**T4:** You arrive at the assay office, a squat stone building tucked between two mills near the riverbank. You step up to the heavy oak door and knock, announcing your name as you wait. 

The door creaks open to reveal **Silas Vance**, a man with ink-stained fingers and spectacles perched precariously on a sharp nose. He peers at you through thick lenses, his eyes narrowing with suspicion as he grips the edge of the doorframe. He doesn't step aside to let you in; instead, he leans out into the street, blocking the threshold.

"We aren't taking visitors today," **Silas Vance** says, his voice thin and defensive. He glances over your shoulder toward the road, his posture stiffening as if expecting someone to follow you. "Unless you're here to pay a filing fee or settle a discrepancy, move along. I've got no time for idle curiosity or travelers looking for trouble."


## player_intent
**persuade**: The player wants to inquire at the sheriff's office regarding whether a missing person report has been filed for Harker to determine law enforcement involvement.

## CURRENT TURN 5 NARRATION
You step away from the stone walls of the Assay Office and make your way toward the sheriff's station, a low-slung building with a heavy iron-reinforced door located near the town square. The midday sun beats down on the dust-choked streets, but the air remains heavy with a restless energy as travelers move between the mills.

You push through the entrance of the station to find a small, cluttered room smelling of old parchment and stale tobacco. Behind a sturdy wooden desk sits **Kaelen Vance**, a woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She doesn't look up from her ledger immediately, her quill scratching rhythmically against the page.

"I'm looking to see if a missing person report has been filed for Harker," you say.

**Kaelen Vance** pauses, her quill hovering just above the paper. She looks up, her gaze steady and unreadable as she leans back in her chair. "Harker? No report on my desk yet," she says, her voice low and level. "Men go missing near the mills all the time when they've had too much ale or a bad run of luck. Unless a family comes knocking with a name and a reason to worry, we don't waste ink on ghosts."
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
  "intent": "The player wants to inquire at the sheriff's office regarding whether a missing person report has been filed for Harker to determine law enforcement involvement.",
  "intent_verb": "persuade",
  "target": "Sheriff's Office / Law Enforcement",
  "scene_motion": "transition",
  "check": {
    "required": false
  }
}
```

### Narration

You step away from the stone walls of the Assay Office and make your way toward the sheriff's station, a low-slung building with a heavy iron-reinforced door located near the town square. The midday sun beats down on the dust-choked streets, but the air remains heavy with a restless energy as travelers move between the mills.

You push through the entrance of the station to find a small, cluttered room smelling of old parchment and stale tobacco. Behind a sturdy wooden desk sits **Kaelen Vance**, a woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She doesn't look up from her ledger immediately, her quill scratching rhythmically against the page.

"I'm looking to see if a missing person report has been filed for Harker," you say.

**Kaelen Vance** pauses, her quill hovering just above the paper. She looks up, her gaze steady and unreadable as she leans back in her chair. "Harker? No report on my desk yet," she says, her voice low and level. "Men go missing near the mills all the time when they've had too much ale or a bad run of luck. Unless a family comes knocking with a name and a reason to worry, we don't waste ink on ghosts."

### Extract Scene

```json
{
  "scene_tags": [
    "investigation",
    "tense_conversation"
  ],
  "scene_tagline": "No Report for Harker",
  "location_change": {
    "id": "sheriffs_station",
    "name": "Sheriff's Station",
    "description": "A low-slung building with a heavy iron-reinforced door, containing a small, cluttered room smelling of old parchment and stale tobacco."
  },
  "location_description": "The interior is a cramped space dominated by a sturdy wooden desk and the rhythmic scratching of a quill.",
  "compendium_npc_update": [
    {
      "id": "kaelen_vance",
      "name": "Kaelen Vance",
      "title": "Sheriff",
      "bio": "A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze.",
      "aliases": [],
      "presence": "present",
      "notes": "leaning back, scanning player"
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
      "id": "dusty",
      "label": "Dusty",
      "description": "Fine dust from the streets clings to your clothes and skin.",
      "turns_remaining": 2
    }
  ],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "actions": [
    "Offer information about the rumors heard at the saloon.",
    "Inquire if any recent crimes occurred near the mills.",
    "Bribe the Sheriff to look into the matter privately.",
    "Ask which families typically report missing persons in town."
  ],
  "outcome_summary": "Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.",
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "Sheriff confirms no official report filed",
      "progress_kind": "shift"
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

- ruling: est=1554t trimmed=False
- narrate: est=4674t trimmed=False
- extract.scene: est=3870t trimmed=False attempts=1
- extract.state: est=2022t trimmed=False attempts=1
- extract.storytell: est=3982t trimmed=False attempts=1

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

**Input:** `The sheriff gives me Harker's cabin key. I walk to the edge of town and let myself in. The place is dusty and cold.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** Dusty

## scene
Location: Sheriff's Station
## Present NPCs (in scene right now)
- Kaelen Vance (Sheriff)










## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)


## Last Turn Narrative (T5)
You step away from the stone walls of the Assay Office and make your way toward the sheriff's station, a low-slung building with a heavy iron-reinforced door located near the town square. The midday sun beats down on the dust-choked streets, but the air remains heavy with a restless energy as travelers move between the mills.

You push through the entrance of the station to find a small, cluttered room smelling of old parchment and stale tobacco. Behind a sturdy wooden desk sits **Kaelen Vance**, a woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She doesn't look up from her ledger immediately, her quill scratching rhythmically against the page.

"I'm looking to see if a missing person report has been filed for Harker," you say.

**Kaelen Vance** pauses, her quill hovering just above the paper. She looks up, her gaze steady and unreadable as she leans back in her chair. "Harker? No report on my desk yet," she says, her voice low and level. "Men go missing near the mills all the time when they've had too much ale or a bad run of luck. Unless a family comes knocking with a name and a reason to worry, we don't waste ink on ghosts."


## Current Turn: 6
=== PLAYER INPUT ===
The sheriff gives me Harker's cabin key. I walk to the edge of town and let myself in. The place is dusty and cold.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** Dusty

## Inventory
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.


## Location
Sheriff's Station (sheriffs_station)
A low-slung building with a heavy iron-reinforced door, containing a small, cluttered room smelling of old parchment and stale tobacco.




## Characters

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [PRESENT] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Sheriff's Station

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office

- `saloon_patrons` | **Saloon Patrons** [KNOWN] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Assay Office

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

- `silas_vance` | **Silas Vance** (Assay Clerk) [KNOWN] — A man with ink-stained fingers and spectacles perched precariously on a sharp nose. He possesses a thin, defensive voice and appears perpetually on edge. | last seen: Assay Office




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (2 turns ago)   - [SHIFT] Investigated the local assay office.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (3 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker.





## Prior History
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.

- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.

- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.

## Recent Turns

**T5:** You step away from the stone walls of the Assay Office and make your way toward the sheriff's station, a low-slung building with a heavy iron-reinforced door located near the town square. The midday sun beats down on the dust-choked streets, but the air remains heavy with a restless energy as travelers move between the mills.

You push through the entrance of the station to find a small, cluttered room smelling of old parchment and stale tobacco. Behind a sturdy wooden desk sits **Kaelen Vance**, a woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She doesn't look up from her ledger immediately, her quill scratching rhythmically against the page.

"I'm looking to see if a missing person report has been filed for Harker," you say.

**Kaelen Vance** pauses, her quill hovering just above the paper. She looks up, her gaze steady and unreadable as she leans back in her chair. "Harker? No report on my desk yet," she says, her voice low and level. "Men go missing near the mills all the time when they've had too much ale or a bad run of luck. Unless a family comes knocking with a name and a reason to worry, we don't waste ink on ghosts."

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 6) Result


**IMPOSSIBLE:** This action cannot succeed — The sheriff has not given the player the key; she only stated no report had been filed. The player is attempting to take an item that was not granted in the narrative..
Narrate the attempt and its natural failure. Do NOT write a version where the action succeeds.



=== PLAYER INPUT ===
The sheriff gives me Harker's cabin key. I walk to the edge of town and let myself in. The place is dusty and cold.
=== END PLAYER INPUT ===

**Outcome:** transition
Write the arrival at the new location, not the departure from this one. The scene moves forward.


```

### Extract Scene User Prompt
```
## location
`sheriffs_station` | Sheriff's Station
A low-slung building with a heavy iron-reinforced door, containing a small, cluttered room smelling of old parchment and stale tobacco.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T5 context)
You step away from the stone walls of the Assay Office and make your way toward the sheriff's station, a low-slung building with a heavy iron-reinforced door located near the town square. The midday sun beats down on the dust-choked streets, but the air remains heavy with a restless energy as travelers move between the mills.

You push through the entrance of the station to find a small, cluttered room smelling of old parchment and stale tobacco. Behind a sturdy wooden desk sits **Kaelen Vance**, a woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She doesn't look up from her ledger immediately, her quill scratching rhythmically against the page.

"I'm looking to see if a missing person report has been filed for Harker," you say.

**Kaelen Vance** pauses, her quill hovering just above the paper. She looks up, her gaze steady and unreadable as she leans back in her chair. "Harker? No report on my desk yet," she says, her voice low and level. "Men go missing near the mills all the time when they've had too much ale or a bad run of luck. Unless a family comes knocking with a name and a reason to worry, we don't waste ink on ghosts."

## CURRENT TURN 6 NARRATION
You reach toward the desk, your hand outstretched to claim a key that isn't there. **Kaelen Vance** doesn't move to assist you; instead, she simply stares at your empty palm with a look of profound boredom. "I don't have any keys to give out, courier," she says, her voice dropping an octave. "If you're looking for property records or ownership rights, go find Silas at the assay office. I deal in crimes, not locksmithing."

The heavy iron-reinforced door thuds shut behind you as you exit the station, leaving the scent of stale tobacco far behind. You trek toward the outskirts of Marrow's Crossing, where the manicured streets give way to scrub brush and skeletal trees. Tucked against a rise in the earth sits a small, weather-beaten cabin, its timber grayed by years of exposure.

The door yields with a groan of protesting wood, revealing a room swallowed by shadows. A thick layer of grit coats every surface, from the crooked tabletop to the lone chair pulled near a dead hearth. The air inside is stagnant and biting, holding a chill that seems to seep directly from the floorboards.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- dusty — Fine dust from the streets clings to your clothes and skin.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
sneak: The player attempts to enter Harker's cabin using a key provided by the sheriff.
## CURRENT TURN 6 NARRATION
You reach toward the desk, your hand outstretched to claim a key that isn't there. **Kaelen Vance** doesn't move to assist you; instead, she simply stares at your empty palm with a look of profound boredom. "I don't have any keys to give out, courier," she says, her voice dropping an octave. "If you're looking for property records or ownership rights, go find Silas at the assay office. I deal in crimes, not locksmithing."

The heavy iron-reinforced door thuds shut behind you as you exit the station, leaving the scent of stale tobacco far behind. You trek toward the outskirts of Marrow's Crossing, where the manicured streets give way to scrub brush and skeletal trees. Tucked against a rise in the earth sits a small, weather-beaten cabin, its timber grayed by years of exposure.

The door yields with a groan of protesting wood, revealing a room swallowed by shadows. A thick layer of grit coats every surface, from the crooked tabletop to the lone chair pulled near a dead hearth. The air inside is stagnant and biting, holding a chill that seems to seep directly from the floorboards.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.


## Characters

- `cabin_dweller` | **Cabin Dweller** [PRESENT] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | absent but looming | last seen: Weather-Beaten Cabin

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | staring with profound boredom | last seen: Sheriff's Station

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office

- `saloon_patrons` | **Saloon Patrons** [KNOWN] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Assay Office

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.



## location
**Weather-Beaten Cabin** — The air inside is stagnant and biting, holding a chill that seems to seep directly from the floorboards.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (4 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (2 turns ago)   - [SHIFT] Investigated the local assay office.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (3 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker.


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## GM Beat
No beat currently carried over from the previous turn. Choose freely.

## Recent Beats
T1: PRESSURE (npc_behavior)
T2: COMPLICATION (npc_behavior)
T3: COMPLICATION (npc_behavior)
T4: BREATHING ROOM (ambient)
T5: No beat emitted this turn


## Recent Outcomes
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.
- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.
- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.
- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.

## prior turn context

**T5:** You step away from the stone walls of the Assay Office and make your way toward the sheriff's station, a low-slung building with a heavy iron-reinforced door located near the town square. The midday sun beats down on the dust-choked streets, but the air remains heavy with a restless energy as travelers move between the mills.

You push through the entrance of the station to find a small, cluttered room smelling of old parchment and stale tobacco. Behind a sturdy wooden desk sits **Kaelen Vance**, a woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She doesn't look up from her ledger immediately, her quill scratching rhythmically against the page.

"I'm looking to see if a missing person report has been filed for Harker," you say.

**Kaelen Vance** pauses, her quill hovering just above the paper. She looks up, her gaze steady and unreadable as she leans back in her chair. "Harker? No report on my desk yet," she says, her voice low and level. "Men go missing near the mills all the time when they've had too much ale or a bad run of luck. Unless a family comes knocking with a name and a reason to worry, we don't waste ink on ghosts."


## player_intent
**sneak**: The player attempts to enter Harker's cabin using a key provided by the sheriff.

## CURRENT TURN 6 NARRATION
You reach toward the desk, your hand outstretched to claim a key that isn't there. **Kaelen Vance** doesn't move to assist you; instead, she simply stares at your empty palm with a look of profound boredom. "I don't have any keys to give out, courier," she says, her voice dropping an octave. "If you're looking for property records or ownership rights, go find Silas at the assay office. I deal in crimes, not locksmithing."

The heavy iron-reinforced door thuds shut behind you as you exit the station, leaving the scent of stale tobacco far behind. You trek toward the outskirts of Marrow's Crossing, where the manicured streets give way to scrub brush and skeletal trees. Tucked against a rise in the earth sits a small, weather-beaten cabin, its timber grayed by years of exposure.

The door yields with a groan of protesting wood, revealing a room swallowed by shadows. A thick layer of grit coats every surface, from the crooked tabletop to the lone chair pulled near a dead hearth. The air inside is stagnant and biting, holding a chill that seems to seep directly from the floorboards.
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
  "intent": "The player attempts to enter Harker's cabin using a key provided by the sheriff.",
  "intent_verb": "sneak",
  "target": "Harker's cabin",
  "impossible": true,
  "impossible_reason": "The sheriff has not given the player the key; she only stated no report had been filed. The player is attempting to take an item that was not granted in the narrative.",
  "scene_motion": "transition",
  "check": {
    "required": false
  }
}
```

### Narration

You reach toward the desk, your hand outstretched to claim a key that isn't there. **Kaelen Vance** doesn't move to assist you; instead, she simply stares at your empty palm with a look of profound boredom. "I don't have any keys to give out, courier," she says, her voice dropping an octave. "If you're looking for property records or ownership rights, go find Silas at the assay office. I deal in crimes, not locksmithing."

The heavy iron-reinforced door thuds shut behind you as you exit the station, leaving the scent of stale tobacco far behind. You trek toward the outskirts of Marrow's Crossing, where the manicured streets give way to scrub brush and skeletal trees. Tucked against a rise in the earth sits a small, weather-beaten cabin, its timber grayed by years of exposure.

The door yields with a groan of protesting wood, revealing a room swallowed by shadows. A thick layer of grit coats every surface, from the crooked tabletop to the lone chair pulled near a dead hearth. The air inside is stagnant and biting, holding a chill that seems to seep directly from the floorboards.

### Extract Scene

```json
{
  "scene_tags": [
    "investigation",
    "discovery",
    "tense"
  ],
  "scene_tagline": "A Shadowed Cabin",
  "location_change": {
    "id": "weather_beaten_cabin",
    "name": "Weather-Beaten Cabin",
    "description": "A small, grayed timber structure tucked against a rise in the earth. The interior is shadowed and grit-coated, containing a crooked tabletop and a lone chair near a dead hearth."
  },
  "location_description": "The air inside is stagnant and biting, holding a chill that seems to seep directly from the floorboards.",
  "compendium_npc_update": [
    {
      "id": "kaelen_vance",
      "aliases": [],
      "presence": "known",
      "notes": "staring with profound boredom"
    },
    {
      "id": "cabin_dweller",
      "name": "Cabin Dweller",
      "bio": "A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows.",
      "aliases": [],
      "presence": "present",
      "notes": "absent but looming"
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
  "pc_condition_remove": [
    {
      "id": "dusty"
    }
  ]
}
```

### Storyteller

```json
{
  "actions": [
    "Search the grit-covered surfaces for hidden compartments or papers.",
    "Inspect the dead hearth for signs of recent activity.",
    "Examine the floorboards for loose planks or hollow sounds.",
    "Peer into the deep shadows for any lingering presence."
  ],
  "outcome_summary": "Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.",
  "gm_beat": {
    "type": "revelation",
    "surface_as": "environmental"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "reached Harker's abandoned cabin",
      "progress_kind": "advancement"
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

- ruling: est=1650t trimmed=False
- narrate: est=4915t trimmed=False
- extract.scene: est=4035t trimmed=False attempts=1
- extract.state: est=1991t trimmed=False attempts=1
- extract.storytell: est=3966t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 7

**Input:** `I look through Harker's desk and find a locked tin box. I pry it open with my knife and find a map with markings near Red Canyon.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## scene
Location: Weather-Beaten Cabin
## Present NPCs (in scene right now)
- Cabin Dweller










## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)


## Last Turn Narrative (T6)
You reach toward the desk, your hand outstretched to claim a key that isn't there. **Kaelen Vance** doesn't move to assist you; instead, she simply stares at your empty palm with a look of profound boredom. "I don't have any keys to give out, courier," she says, her voice dropping an octave. "If you're looking for property records or ownership rights, go find Silas at the assay office. I deal in crimes, not locksmithing."

The heavy iron-reinforced door thuds shut behind you as you exit the station, leaving the scent of stale tobacco far behind. You trek toward the outskirts of Marrow's Crossing, where the manicured streets give way to scrub brush and skeletal trees. Tucked against a rise in the earth sits a small, weather-beaten cabin, its timber grayed by years of exposure.

The door yields with a groan of protesting wood, revealing a room swallowed by shadows. A thick layer of grit coats every surface, from the crooked tabletop to the lone chair pulled near a dead hearth. The air inside is stagnant and biting, holding a chill that seems to seep directly from the floorboards.


## Current Turn: 7
=== PLAYER INPUT ===
I look through Harker's desk and find a locked tin box. I pry it open with my knife and find a map with markings near Red Canyon.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## Inventory
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.


## Location
Weather-Beaten Cabin (weather_beaten_cabin)
A small, grayed timber structure tucked against a rise in the earth. The interior is shadowed and grit-coated, containing a crooked tabletop and a lone chair near a dead hearth.




## Characters

- `cabin_dweller` | **Cabin Dweller** [PRESENT] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office

- `saloon_patrons` | **Saloon Patrons** [KNOWN] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Assay Office

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (3 turns ago)   - [SHIFT] Investigated the local assay office.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (4 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (1 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin





## Prior History
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.

- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.

- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.

- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.

## Recent Turns

**T6:** You reach toward the desk, your hand outstretched to claim a key that isn't there. **Kaelen Vance** doesn't move to assist you; instead, she simply stares at your empty palm with a look of profound boredom. "I don't have any keys to give out, courier," she says, her voice dropping an octave. "If you're looking for property records or ownership rights, go find Silas at the assay office. I deal in crimes, not locksmithing."

The heavy iron-reinforced door thuds shut behind you as you exit the station, leaving the scent of stale tobacco far behind. You trek toward the outskirts of Marrow's Crossing, where the manicured streets give way to scrub brush and skeletal trees. Tucked against a rise in the earth sits a small, weather-beaten cabin, its timber grayed by years of exposure.

The door yields with a groan of protesting wood, revealing a room swallowed by shadows. A thick layer of grit coats every surface, from the crooked tabletop to the lone chair pulled near a dead hearth. The air inside is stagnant and biting, holding a chill that seems to seep directly from the floorboards.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 7) Result


**Band:** CRIT SUCCESS → The sneak succeeds outstandingly. Best possible outcome — something unexpected goes in your favour.
**Roll:** d12: 11 + 1 (Strength) → 12


**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.

=== PLAYER INPUT ===
I look through Harker's desk and find a locked tin box. I pry it open with my knife and find a map with markings near Red Canyon.
=== END PLAYER INPUT ===

**Beat:** REVELATION — surface as `environmental`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.**Outcome:** advance
Narrate through to the resolution. Do not linger on preparation or setup. Something significant happens this turn.


```

### Extract Scene User Prompt
```
## location
`weather_beaten_cabin` | Weather-Beaten Cabin
A small, grayed timber structure tucked against a rise in the earth. The interior is shadowed and grit-coated, containing a crooked tabletop and a lone chair near a dead hearth.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T6 context)
You reach toward the desk, your hand outstretched to claim a key that isn't there. **Kaelen Vance** doesn't move to assist you; instead, she simply stares at your empty palm with a look of profound boredom. "I don't have any keys to give out, courier," she says, her voice dropping an octave. "If you're looking for property records or ownership rights, go find Silas at the assay office. I deal in crimes, not locksmithing."

The heavy iron-reinforced door thuds shut behind you as you exit the station, leaving the scent of stale tobacco far behind. You trek toward the outskirts of Marrow's Crossing, where the manicured streets give way to scrub brush and skeletal trees. Tucked against a rise in the earth sits a small, weather-beaten cabin, its timber grayed by years of exposure.

The door yields with a groan of protesting wood, revealing a room swallowed by shadows. A thick layer of grit coats every surface, from the crooked tabletop to the lone chair pulled near a dead hearth. The air inside is stagnant and biting, holding a chill that seems to seep directly from the floorboards.

## CURRENT TURN 7 NARRATION
You wedge the tip of your **Iron dagger** into the seam of a heavy tin box hidden within the depths of the desk. With a sharp, rhythmic grunt of effort, you lever the metal lid upward; it yields with a sudden, violent snap that echoes too loudly in the cramped cabin. Inside, resting atop a bed of dust-coated lint, lies a tightly rolled parchment.

You unfurl the paper to reveal a hand-drawn map of the surrounding territory, its edges brittle and yellowed. Your eyes lock onto a series of frantic, charcoal markings clustered near the jagged cliffs of Red Canyon. A small, crimson ink blot sits directly over a canyon pass, looking less like a landmark and more like a fresh wound on the landscape.

As you study the route, a floorboard creaks sharply behind you—not from your own movement, but from the shadowed corner near the dead hearth. The heavy silence of the cabin is broken by a low, rhythmic scraping sound, as if something heavy is being dragged slowly across the grit-coated floorboards toward your back.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
sneak: The player attempts to force open a locked tin box using an iron dagger to search for information.
## CURRENT TURN 7 NARRATION
You wedge the tip of your **Iron dagger** into the seam of a heavy tin box hidden within the depths of the desk. With a sharp, rhythmic grunt of effort, you lever the metal lid upward; it yields with a sudden, violent snap that echoes too loudly in the cramped cabin. Inside, resting atop a bed of dust-coated lint, lies a tightly rolled parchment.

You unfurl the paper to reveal a hand-drawn map of the surrounding territory, its edges brittle and yellowed. Your eyes lock onto a series of frantic, charcoal markings clustered near the jagged cliffs of Red Canyon. A small, crimson ink blot sits directly over a canyon pass, looking less like a landmark and more like a fresh wound on the landscape.

As you study the route, a floorboard creaks sharply behind you—not from your own movement, but from the shadowed corner near the dead hearth. The heavy silence of the cabin is broken by a low, rhythmic scraping sound, as if something heavy is being dragged slowly across the grit-coated floorboards toward your back.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `parchment_map`: parchment map x1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.

## PC conditions (this turn)
- startled: startled — The sudden noise and scraping sound have broken your concentration.


## Characters

- `cabin_dweller` | **Cabin Dweller** [PRESENT] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | dragging something heavy across floorboards | last seen: Weather-Beaten Cabin

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office

- `saloon_patrons` | **Saloon Patrons** [KNOWN] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Assay Office

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.



## location
**Weather-Beaten Cabin** — The air remains stagnant and biting, with a sudden scraping sound echoing from the dark corner near the dead hearth.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (4 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (3 turns ago)   - [SHIFT] Investigated the local assay office.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (4 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (1 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## GM Beat
Type: **REVELATION**
Surface: `environmental`
Expires: Turn 8

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.

## Recent Beats
T2: COMPLICATION (npc_behavior)
T3: COMPLICATION (npc_behavior)
T4: BREATHING ROOM (ambient)
T5: No beat emitted this turn
T6: REVELATION (environmental)


## rules_outcome
Band: CRIT_SUCCESS. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.

## Recent Outcomes
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.
- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.
- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.
- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.
- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.

## prior turn context

**T6:** You reach toward the desk, your hand outstretched to claim a key that isn't there. **Kaelen Vance** doesn't move to assist you; instead, she simply stares at your empty palm with a look of profound boredom. "I don't have any keys to give out, courier," she says, her voice dropping an octave. "If you're looking for property records or ownership rights, go find Silas at the assay office. I deal in crimes, not locksmithing."

The heavy iron-reinforced door thuds shut behind you as you exit the station, leaving the scent of stale tobacco far behind. You trek toward the outskirts of Marrow's Crossing, where the manicured streets give way to scrub brush and skeletal trees. Tucked against a rise in the earth sits a small, weather-beaten cabin, its timber grayed by years of exposure.

The door yields with a groan of protesting wood, revealing a room swallowed by shadows. A thick layer of grit coats every surface, from the crooked tabletop to the lone chair pulled near a dead hearth. The air inside is stagnant and biting, holding a chill that seems to seep directly from the floorboards.


## player_intent
**sneak**: The player attempts to force open a locked tin box using an iron dagger to search for information.

## CURRENT TURN 7 NARRATION
You wedge the tip of your **Iron dagger** into the seam of a heavy tin box hidden within the depths of the desk. With a sharp, rhythmic grunt of effort, you lever the metal lid upward; it yields with a sudden, violent snap that echoes too loudly in the cramped cabin. Inside, resting atop a bed of dust-coated lint, lies a tightly rolled parchment.

You unfurl the paper to reveal a hand-drawn map of the surrounding territory, its edges brittle and yellowed. Your eyes lock onto a series of frantic, charcoal markings clustered near the jagged cliffs of Red Canyon. A small, crimson ink blot sits directly over a canyon pass, looking less like a landmark and more like a fresh wound on the landscape.

As you study the route, a floorboard creaks sharply behind you—not from your own movement, but from the shadowed corner near the dead hearth. The heavy silence of the cabin is broken by a low, rhythmic scraping sound, as if something heavy is being dragged slowly across the grit-coated floorboards toward your back.
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
  "intent": "The player attempts to force open a locked tin box using an iron dagger to search for information.",
  "intent_verb": "sneak",
  "target": "locked tin box",
  "impossible": false,
  "scene_motion": "advance",
  "check": {
    "required": true,
    "skill": "strength",
    "difficulty": "normal"
  }
}
```

### Narration

You wedge the tip of your **Iron dagger** into the seam of a heavy tin box hidden within the depths of the desk. With a sharp, rhythmic grunt of effort, you lever the metal lid upward; it yields with a sudden, violent snap that echoes too loudly in the cramped cabin. Inside, resting atop a bed of dust-coated lint, lies a tightly rolled parchment.

You unfurl the paper to reveal a hand-drawn map of the surrounding territory, its edges brittle and yellowed. Your eyes lock onto a series of frantic, charcoal markings clustered near the jagged cliffs of Red Canyon. A small, crimson ink blot sits directly over a canyon pass, looking less like a landmark and more like a fresh wound on the landscape.

As you study the route, a floorboard creaks sharply behind you—not from your own movement, but from the shadowed corner near the dead hearth. The heavy silence of the cabin is broken by a low, rhythmic scraping sound, as if something heavy is being dragged slowly across the grit-coated floorboards toward your back.

### Extract Scene

```json
{
  "scene_tags": [
    "discovery",
    "tense",
    "suspense"
  ],
  "scene_tagline": "A Presence in the Shadows",
  "location_description": "The air remains stagnant and biting, with a sudden scraping sound echoing from the dark corner near the dead hearth.",
  "compendium_npc_update": [
    {
      "id": "cabin_dweller",
      "aliases": [],
      "presence": "present",
      "notes": "dragging something heavy across floorboards"
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "parchment_map",
      "name": "parchment map",
      "notes": "Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [
    {
      "id": "startled",
      "label": "startled",
      "description": "The sudden noise and scraping sound have broken your concentration.",
      "turns_remaining": 2
    }
  ],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "actions": [
    "Spin around and drive your dagger toward the scraping sound.",
    "Dive behind the desk for cover while clutching the parchment.",
    "Freeze completely to listen for the source of the noise.",
    "Shout a challenge into the darkness to demand identification."
  ],
  "outcome_summary": "Matthew successfully pries open a hidden tin box to find a map marked with crimson ink, only to hear something dragging itself through the shadows behind him.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "environmental"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "found map with canyon markings",
      "progress_kind": "advancement"
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

- ruling: est=1619t trimmed=False
- narrate: est=5001t trimmed=False
- extract.scene: est=3986t trimmed=False attempts=1
- extract.state: est=1948t trimmed=False attempts=1
- extract.storytell: est=4162t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 8

**Input:** `I head back to the general store to buy supplies — dried meat, water canteen, rope. The clerk rings me up.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** startled

## scene
Location: Weather-Beaten Cabin
## Present NPCs (in scene right now)
- Cabin Dweller










## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)
- Parchment map (1)


## Last Turn Narrative (T7)
You wedge the tip of your **Iron dagger** into the seam of a heavy tin box hidden within the depths of the desk. With a sharp, rhythmic grunt of effort, you lever the metal lid upward; it yields with a sudden, violent snap that echoes too loudly in the cramped cabin. Inside, resting atop a bed of dust-coated lint, lies a tightly rolled parchment.

You unfurl the paper to reveal a hand-drawn map of the surrounding territory, its edges brittle and yellowed. Your eyes lock onto a series of frantic, charcoal markings clustered near the jagged cliffs of Red Canyon. A small, crimson ink blot sits directly over a canyon pass, looking less like a landmark and more like a fresh wound on the landscape.

As you study the route, a floorboard creaks sharply behind you—not from your own movement, but from the shadowed corner near the dead hearth. The heavy silence of the cabin is broken by a low, rhythmic scraping sound, as if something heavy is being dragged slowly across the grit-coated floorboards toward your back.


## Current Turn: 8
=== PLAYER INPUT ===
I head back to the general store to buy supplies — dried meat, water canteen, rope. The clerk rings me up.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** startled

## Inventory
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Parchment map**: Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.


## Location
Weather-Beaten Cabin (weather_beaten_cabin)
The air remains stagnant and biting, with a sudden scraping sound echoing from the dark corner near the dead hearth.




## Characters

- `cabin_dweller` | **Cabin Dweller** [PRESENT] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office

- `saloon_patrons` | **Saloon Patrons** [KNOWN] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Assay Office

- `tough_b` | **Scarred Tough** (Road thug) [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (1 turns ago)   - [SHIFT] Investigated the local assay office.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (5 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (1 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings





## Prior History
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.

- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.

- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.

- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.

- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.

## Recent Turns

**T7:** You wedge the tip of your **Iron dagger** into the seam of a heavy tin box hidden within the depths of the desk. With a sharp, rhythmic grunt of effort, you lever the metal lid upward; it yields with a sudden, violent snap that echoes too loudly in the cramped cabin. Inside, resting atop a bed of dust-coated lint, lies a tightly rolled parchment.

You unfurl the paper to reveal a hand-drawn map of the surrounding territory, its edges brittle and yellowed. Your eyes lock onto a series of frantic, charcoal markings clustered near the jagged cliffs of Red Canyon. A small, crimson ink blot sits directly over a canyon pass, looking less like a landmark and more like a fresh wound on the landscape.

As you study the route, a floorboard creaks sharply behind you—not from your own movement, but from the shadowed corner near the dead hearth. The heavy silence of the cabin is broken by a low, rhythmic scraping sound, as if something heavy is being dragged slowly across the grit-coated floorboards toward your back.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 8) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I head back to the general store to buy supplies — dried meat, water canteen, rope. The clerk rings me up.
=== END PLAYER INPUT ===

**Beat:** PRESSURE — surface as `environmental`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.**Outcome:** transition
Write the arrival at the new location, not the departure from this one. The scene moves forward.


```

### Extract Scene User Prompt
```
## location
`weather_beaten_cabin` | Weather-Beaten Cabin
The air remains stagnant and biting, with a sudden scraping sound echoing from the dark corner near the dead hearth.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T7 context)
You wedge the tip of your **Iron dagger** into the seam of a heavy tin box hidden within the depths of the desk. With a sharp, rhythmic grunt of effort, you lever the metal lid upward; it yields with a sudden, violent snap that echoes too loudly in the cramped cabin. Inside, resting atop a bed of dust-coated lint, lies a tightly rolled parchment.

You unfurl the paper to reveal a hand-drawn map of the surrounding territory, its edges brittle and yellowed. Your eyes lock onto a series of frantic, charcoal markings clustered near the jagged cliffs of Red Canyon. A small, crimson ink blot sits directly over a canyon pass, looking less like a landmark and more like a fresh wound on the landscape.

As you study the route, a floorboard creaks sharply behind you—not from your own movement, but from the shadowed corner near the dead hearth. The heavy silence of the cabin is broken by a low, rhythmic scraping sound, as if something heavy is being dragged slowly across the grit-coated floorboards toward your back.

## CURRENT TURN 8 NARRATION
You arrive at the general store, the bell above the door clattering with a sharp ring that cuts through the midday dust of Marrow's Crossing. You approach the counter to request dried meat, a water canteen, and a length of rope. 

The clerk, a wiry man named Silas Vance with ink-stained fingers, pulls several items from the shelves and thumps them onto the wood. He doesn't bother with a greeting, his eyes tracking your movement with a practiced, wary indifference common to the town's merchants. He begins totaling the cost, his movements brisk and mechanical.

As he rings you up, a sudden gust of wind rattles the storefront windows, sending a swirl of grit dancing across the floorboards. Outside, the rhythmic clatter of horse hooves on stone approaches from the direction of the main thoroughfare, growing louder with every second. Silas pauses mid-calculation, his gaze flickering toward the door as the heavy thud of boots nears the entrance.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- startled — The sudden noise and scraping sound have broken your concentration.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `parchment_map` | Parchment map ×1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.

## player_intent
negotiate: The player intends to leave the cabin and purchase essential survival supplies at a general store.
## CURRENT TURN 8 NARRATION
You arrive at the general store, the bell above the door clattering with a sharp ring that cuts through the midday dust of Marrow's Crossing. You approach the counter to request dried meat, a water canteen, and a length of rope. 

The clerk, a wiry man named Silas Vance with ink-stained fingers, pulls several items from the shelves and thumps them onto the wood. He doesn't bother with a greeting, his eyes tracking your movement with a practiced, wary indifference common to the town's merchants. He begins totaling the cost, his movements brisk and mechanical.

As he rings you up, a sudden gust of wind rattles the storefront windows, sending a swirl of grit dancing across the floorboards. Outside, the rhythmic clatter of horse hooves on stone approaches from the direction of the main thoroughfare, growing louder with every second. Silas pauses mid-calculation, his gaze flickering toward the door as the heavy thud of boots nears the entrance.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `parchment_map`: Parchment map x1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.
- `dried_meat`: Dried meat x1 — Rations for travel.
- `water_canteen`: Water canteen x1 — Filled with fresh water.
- `rope`: Rope x1 — A length of sturdy hemp rope.

## PC conditions (this turn)
- startled: startled — The sudden noise and scraping sound have broken your concentration.


## Characters

- `silas_vance` | **Silas Vance** (General Store Clerk) [PRESENT] — A wiry man with ink-stained fingers and a brisk, mechanical manner of movement. He possesses a practiced, wary indifference toward customers and focuses intently on his calculations. | calculating costs with brisk movements | last seen: Assay Office

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `cabin_dweller` | **Cabin Dweller** [KNOWN] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office

- `saloon_patrons` | **Saloon Patrons** [KNOWN] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Assay Office



## location
**Marrow's Crossing General Store** — A dusty storefront filled with shelves of supplies, where the sound of a clattering bell and rattling windows punctuates the midday heat.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (4 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (1 turns ago)   - [SHIFT] Investigated the local assay office.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (5 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (1 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## GM Beat
Type: **PRESSURE**
Surface: `environmental`
Expires: Turn 9

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.

## Recent Beats
T3: COMPLICATION (npc_behavior)
T4: BREATHING ROOM (ambient)
T5: No beat emitted this turn
T6: REVELATION (environmental)
T7: PRESSURE (environmental)


## Recent Outcomes
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.
- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.
- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.
- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.
- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.
- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.

## prior turn context

**T7:** You wedge the tip of your **Iron dagger** into the seam of a heavy tin box hidden within the depths of the desk. With a sharp, rhythmic grunt of effort, you lever the metal lid upward; it yields with a sudden, violent snap that echoes too loudly in the cramped cabin. Inside, resting atop a bed of dust-coated lint, lies a tightly rolled parchment.

You unfurl the paper to reveal a hand-drawn map of the surrounding territory, its edges brittle and yellowed. Your eyes lock onto a series of frantic, charcoal markings clustered near the jagged cliffs of Red Canyon. A small, crimson ink blot sits directly over a canyon pass, looking less like a landmark and more like a fresh wound on the landscape.

As you study the route, a floorboard creaks sharply behind you—not from your own movement, but from the shadowed corner near the dead hearth. The heavy silence of the cabin is broken by a low, rhythmic scraping sound, as if something heavy is being dragged slowly across the grit-coated floorboards toward your back.


## player_intent
**negotiate**: The player intends to leave the cabin and purchase essential survival supplies at a general store.

## CURRENT TURN 8 NARRATION
You arrive at the general store, the bell above the door clattering with a sharp ring that cuts through the midday dust of Marrow's Crossing. You approach the counter to request dried meat, a water canteen, and a length of rope. 

The clerk, a wiry man named Silas Vance with ink-stained fingers, pulls several items from the shelves and thumps them onto the wood. He doesn't bother with a greeting, his eyes tracking your movement with a practiced, wary indifference common to the town's merchants. He begins totaling the cost, his movements brisk and mechanical.

As he rings you up, a sudden gust of wind rattles the storefront windows, sending a swirl of grit dancing across the floorboards. Outside, the rhythmic clatter of horse hooves on stone approaches from the direction of the main thoroughfare, growing louder with every second. Silas pauses mid-calculation, his gaze flickering toward the door as the heavy thud of boots nears the entrance.
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
  "intent": "The player intends to leave the cabin and purchase essential survival supplies at a general store.",
  "intent_verb": "negotiate",
  "target": "clerk",
  "scene_motion": "transition",
  "check": {
    "required": false
  }
}
```

### Narration

You arrive at the general store, the bell above the door clattering with a sharp ring that cuts through the midday dust of Marrow's Crossing. You approach the counter to request dried meat, a water canteen, and a length of rope. 

The clerk, a wiry man named Silas Vance with ink-stained fingers, pulls several items from the shelves and thumps them onto the wood. He doesn't bother with a greeting, his eyes tracking your movement with a practiced, wary indifference common to the town's merchants. He begins totaling the cost, his movements brisk and mechanical.

As he rings you up, a sudden gust of wind rattles the storefront windows, sending a swirl of grit dancing across the floorboards. Outside, the rhythmic clatter of horse hooves on stone approaches from the direction of the main thoroughfare, growing louder with every second. Silas pauses mid-calculation, his gaze flickering toward the door as the heavy thud of boots nears the entrance.

### Extract Scene

```json
{
  "scene_tags": [
    "investigation",
    "tense_atmosphere"
  ],
  "scene_tagline": "A Wary Merchant's Gaze",
  "location_change": {
    "id": "marrows_crossing_general_store",
    "name": "Marrow's Crossing General Store",
    "description": "A dusty storefront filled with shelves of supplies, where the sound of a clattering bell and rattling windows punctuates the midday heat."
  },
  "compendium_npc_update": [
    {
      "id": "silas_vance",
      "name": "Silas Vance",
      "title": "General Store Clerk",
      "bio": "A wiry man with ink-stained fingers and a brisk, mechanical manner of movement. He possesses a practiced, wary indifference toward customers and focuses intently on his calculations.",
      "aliases": [],
      "presence": "present",
      "notes": "calculating costs with brisk movements"
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "dried_meat",
      "name": "Dried meat",
      "notes": "Rations for travel.",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "water_canteen",
      "name": "Water canteen",
      "notes": "Filled with fresh water.",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "rope",
      "name": "Rope",
      "notes": "A length of sturdy hemp rope.",
      "amount": 1,
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
  "actions": [
    "Purchase the requested supplies and exit before the riders arrive.",
    "Question Silas about the identity of the approaching horsemen.",
    "Scan the storefront for a quick escape route if tension rises.",
    "Pay for the goods and linger to observe the newcomers."
  ],
  "outcome_summary": "Matthew arrives at the general store to purchase supplies just as approaching riders draw Silas Vance's attention.",
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "discovered map with canyon markings",
      "progress_kind": "advancement"
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

- ruling: est=1598t trimmed=False
- narrate: est=4948t trimmed=False
- extract.scene: est=3928t trimmed=False attempts=1
- extract.state: est=1999t trimmed=False attempts=1
- extract.storytell: est=4194t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 9

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

# TURN 9

**Input:** `I saddle up and ride out to Red Canyon. The trail is rough and the sun is starting to set. I keep an eye on the canyon walls.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** startled

## scene
Location: Marrow's Crossing General Store
## Present NPCs (in scene right now)
- Silas Vance (General Store Clerk)










## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)
- Parchment map (1)
- Dried meat (1)
- Water canteen (1)
- Rope (1)


## Last Turn Narrative (T8)
You arrive at the general store, the bell above the door clattering with a sharp ring that cuts through the midday dust of Marrow's Crossing. You approach the counter to request dried meat, a water canteen, and a length of rope. 

The clerk, a wiry man named Silas Vance with ink-stained fingers, pulls several items from the shelves and thumps them onto the wood. He doesn't bother with a greeting, his eyes tracking your movement with a practiced, wary indifference common to the town's merchants. He begins totaling the cost, his movements brisk and mechanical.

As he rings you up, a sudden gust of wind rattles the storefront windows, sending a swirl of grit dancing across the floorboards. Outside, the rhythmic clatter of horse hooves on stone approaches from the direction of the main thoroughfare, growing louder with every second. Silas pauses mid-calculation, his gaze flickering toward the door as the heavy thud of boots nears the entrance.


## Current Turn: 9
=== PLAYER INPUT ===
I saddle up and ride out to Red Canyon. The trail is rough and the sun is starting to set. I keep an eye on the canyon walls.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** startled

## Inventory
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Parchment map**: Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.
- **Dried meat**: Rations for travel.
- **Water canteen**: Filled with fresh water.
- **Rope**: A length of sturdy hemp rope.


## Location
Marrow's Crossing General Store (marrows_crossing_general_store)
A dusty storefront filled with shelves of supplies, where the sound of a clattering bell and rattling windows punctuates the midday heat.




## Characters

- `silas_vance` | **Silas Vance** (General Store Clerk) [PRESENT] — A wiry man with ink-stained fingers and a brisk, mechanical manner of movement. He possesses a practiced, wary indifference toward customers and focuses intently on his calculations. | last seen: Marrow's Crossing General Store

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `cabin_dweller` | **Cabin Dweller** [KNOWN] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office

- `saloon_patrons` | **Saloon Patrons** [KNOWN] — A small group of locals and travelers sitting in the shadows. They possess a practiced, wary indifference toward newcomers. | last seen: Assay Office




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (2 turns ago)   - [SHIFT] Investigated the local assay office.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (6 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (1 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings





## Prior History
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.

- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.

- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.

- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.

- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.

- [T7] Matthew successfully pries open a hidden tin box to find a map marked with crimson ink, only to hear something dragging itself through the shadows behind him.

## Recent Turns

**T8:** You arrive at the general store, the bell above the door clattering with a sharp ring that cuts through the midday dust of Marrow's Crossing. You approach the counter to request dried meat, a water canteen, and a length of rope. 

The clerk, a wiry man named Silas Vance with ink-stained fingers, pulls several items from the shelves and thumps them onto the wood. He doesn't bother with a greeting, his eyes tracking your movement with a practiced, wary indifference common to the town's merchants. He begins totaling the cost, his movements brisk and mechanical.

As he rings you up, a sudden gust of wind rattles the storefront windows, sending a swirl of grit dancing across the floorboards. Outside, the rhythmic clatter of horse hooves on stone approaches from the direction of the main thoroughfare, growing louder with every second. Silas pauses mid-calculation, his gaze flickering toward the door as the heavy thud of boots nears the entrance.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 9) Result


**IMPOSSIBLE:** This action cannot succeed — The player has not acquired a horse or saddle from the merchant; they are currently on foot in a general store..
Narrate the attempt and its natural failure. Do NOT write a version where the action succeeds.



=== PLAYER INPUT ===
I saddle up and ride out to Red Canyon. The trail is rough and the sun is starting to set. I keep an eye on the canyon walls.
=== END PLAYER INPUT ===

**Beat:** COMPLICATION — surface as `npc_behavior`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.**Outcome:** transition
Write the arrival at the new location, not the departure from this one. The scene moves forward.


```

### Extract Scene User Prompt
```
## location
`marrows_crossing_general_store` | Marrow's Crossing General Store
A dusty storefront filled with shelves of supplies, where the sound of a clattering bell and rattling windows punctuates the midday heat.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T8 context)
You arrive at the general store, the bell above the door clattering with a sharp ring that cuts through the midday dust of Marrow's Crossing. You approach the counter to request dried meat, a water canteen, and a length of rope. 

The clerk, a wiry man named Silas Vance with ink-stained fingers, pulls several items from the shelves and thumps them onto the wood. He doesn't bother with a greeting, his eyes tracking your movement with a practiced, wary indifference common to the town's merchants. He begins totaling the cost, his movements brisk and mechanical.

As he rings you up, a sudden gust of wind rattles the storefront windows, sending a swirl of grit dancing across the floorboards. Outside, the rhythmic clatter of horse hooves on stone approaches from the direction of the main thoroughfare, growing louder with every second. Silas pauses mid-calculation, his gaze flickering toward the door as the heavy thud of boots nears the entrance.

## CURRENT TURN 9 NARRATION
You reach for a saddle and a mount to begin your journey toward Red Canyon, but find nothing but the dust-coated floorboards of Marrow's Crossing General Store. You stand amidst the shelves of supplies, empty-handed and on foot, while **Silas Vance** stares at you with a blank, mechanical expression, waiting for you to pay for the **Dried Meat**, **Water Canteen**, and **Rope** he just laid upon the counter.

The rhythmic clatter of hooves outside reaches a crescendo as two riders pull up to the storefront. The heavy thud of boots strikes the porch, and a tall man with a jagged scar across his nose—**Victor Drax**—pushes the door open. He doesn't step toward the counter; instead, he leans against the frame, blocking the exit with a casual, predatory stance. He eyes your **Traveler's Cloak** and the heavy rucksack at your hip, a slow, mocking grin spreading across his face as he signals to a companion waiting in the street.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- startled — The sudden noise and scraping sound have broken your concentration.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `parchment_map` | Parchment map ×1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.
- `dried_meat` | Dried meat ×1 — Rations for travel.
- `water_canteen` | Water canteen ×1 — Filled with fresh water.
- `rope` | Rope ×1 — A length of sturdy hemp rope.

## player_intent
transition: The player intends to travel from Marrow's Crossing toward Red Canyon while remaining vigilant of their surroundings.
## CURRENT TURN 9 NARRATION
You reach for a saddle and a mount to begin your journey toward Red Canyon, but find nothing but the dust-coated floorboards of Marrow's Crossing General Store. You stand amidst the shelves of supplies, empty-handed and on foot, while **Silas Vance** stares at you with a blank, mechanical expression, waiting for you to pay for the **Dried Meat**, **Water Canteen**, and **Rope** he just laid upon the counter.

The rhythmic clatter of hooves outside reaches a crescendo as two riders pull up to the storefront. The heavy thud of boots strikes the porch, and a tall man with a jagged scar across his nose—**Victor Drax**—pushes the door open. He doesn't step toward the counter; instead, he leans against the frame, blocking the exit with a casual, predatory stance. He eyes your **Traveler's Cloak** and the heavy rucksack at your hip, a slow, mocking grin spreading across his face as he signals to a companion waiting in the street.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Payment for supplies.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `parchment_map`: Parchment map x1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.


## Characters

- `silas_vance` | **Silas Vance** (General Store Clerk) [PRESENT] — A wiry man with ink-stained fingers and a brisk, mechanical manner of movement. He possesses a practiced, wary indifference toward customers and focuses intently on his calculations. | staring blankly waiting for payment | last seen: Marrow's Crossing General Store

- `victor_drax` | **Victor Drax** (Scarred Rider) [PRESENT] — Tall man with a jagged scar cutting across the bridge of his nose; carries himself with a casual, predatory confidence. He possesses a mocking demeanor and seems to actively seek out targets for intimidation. | blocking exit with predatory stance | last seen: Marrow's Crossing General Store

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `cabin_dweller` | **Cabin Dweller** [KNOWN] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office



## location
**Marrow's Crossing General Store** — The storefront feels smaller now, the air heavy with the sudden tension of a stranger blocking the only exit.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (4 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (2 turns ago)   - [SHIFT] Investigated the local assay office.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (6 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (1 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## GM Beat
Type: **COMPLICATION**
Surface: `npc_behavior`
Expires: Turn 10

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.

## Recent Beats
T4: BREATHING ROOM (ambient)
T5: No beat emitted this turn
T6: REVELATION (environmental)
T7: PRESSURE (environmental)
T8: COMPLICATION (npc_behavior)


## Recent Outcomes
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.
- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.
- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.
- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.
- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.
- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.
- [T7] Matthew successfully pries open a hidden tin box to find a map marked with crimson ink, only to hear something dragging itself through the shadows behind him.

## prior turn context

**T8:** You arrive at the general store, the bell above the door clattering with a sharp ring that cuts through the midday dust of Marrow's Crossing. You approach the counter to request dried meat, a water canteen, and a length of rope. 

The clerk, a wiry man named Silas Vance with ink-stained fingers, pulls several items from the shelves and thumps them onto the wood. He doesn't bother with a greeting, his eyes tracking your movement with a practiced, wary indifference common to the town's merchants. He begins totaling the cost, his movements brisk and mechanical.

As he rings you up, a sudden gust of wind rattles the storefront windows, sending a swirl of grit dancing across the floorboards. Outside, the rhythmic clatter of horse hooves on stone approaches from the direction of the main thoroughfare, growing louder with every second. Silas pauses mid-calculation, his gaze flickering toward the door as the heavy thud of boots nears the entrance.


## player_intent
**transition**: The player intends to travel from Marrow's Crossing toward Red Canyon while remaining vigilant of their surroundings.

## CURRENT TURN 9 NARRATION
You reach for a saddle and a mount to begin your journey toward Red Canyon, but find nothing but the dust-coated floorboards of Marrow's Crossing General Store. You stand amidst the shelves of supplies, empty-handed and on foot, while **Silas Vance** stares at you with a blank, mechanical expression, waiting for you to pay for the **Dried Meat**, **Water Canteen**, and **Rope** he just laid upon the counter.

The rhythmic clatter of hooves outside reaches a crescendo as two riders pull up to the storefront. The heavy thud of boots strikes the porch, and a tall man with a jagged scar across his nose—**Victor Drax**—pushes the door open. He doesn't step toward the counter; instead, he leans against the frame, blocking the exit with a casual, predatory stance. He eyes your **Traveler's Cloak** and the heavy rucksack at your hip, a slow, mocking grin spreading across his face as he signals to a companion waiting in the street.
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
  "intent": "The player intends to travel from Marrow's Crossing toward Red Canyon while remaining vigilant of their surroundings.",
  "intent_verb": "transition",
  "target": "Red Canyon",
  "impossible": true,
  "impossible_reason": "The player has not acquired a horse or saddle from the merchant; they are currently on foot in a general store.",
  "scene_motion": "transition",
  "check": {
    "required": false
  }
}
```

### Narration

You reach for a saddle and a mount to begin your journey toward Red Canyon, but find nothing but the dust-coated floorboards of Marrow's Crossing General Store. You stand amidst the shelves of supplies, empty-handed and on foot, while **Silas Vance** stares at you with a blank, mechanical expression, waiting for you to pay for the **Dried Meat**, **Water Canteen**, and **Rope** he just laid upon the counter.

The rhythmic clatter of hooves outside reaches a crescendo as two riders pull up to the storefront. The heavy thud of boots strikes the porch, and a tall man with a jagged scar across his nose—**Victor Drax**—pushes the door open. He doesn't step toward the counter; instead, he leans against the frame, blocking the exit with a casual, predatory stance. He eyes your **Traveler's Cloak** and the heavy rucksack at your hip, a slow, mocking grin spreading across his face as he signals to a companion waiting in the street.

### Extract Scene

```json
{
  "scene_tags": [
    "tense_confrontation",
    "suspense"
  ],
  "scene_tagline": "A Predatory Presence Arrives",
  "location_description": "The storefront feels smaller now, the air heavy with the sudden tension of a stranger blocking the only exit.",
  "compendium_npc_update": [
    {
      "id": "silas_vance",
      "aliases": [],
      "presence": "present",
      "notes": "staring blankly waiting for payment"
    },
    {
      "id": "victor_drax",
      "name": "Victor Drax",
      "title": "Scarred Rider",
      "bio": "Tall man with a jagged scar cutting across the bridge of his nose; carries himself with a casual, predatory confidence. He possesses a mocking demeanor and seems to actively seek out targets for intimidation.",
      "aliases": [],
      "presence": "present",
      "notes": "blocking exit with predatory stance"
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
      "id": "dried_meat",
      "amount": 1
    },
    {
      "id": "water_canteen",
      "amount": 1
    },
    {
      "id": "rope",
      "amount": 1
    }
  ],
  "inventory_update": [
    {
      "id": "credits",
      "name": "Credits",
      "notes": "Payment for supplies."
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "startled"
    }
  ]
}
```

### Storyteller

```json
{
  "actions": [
    "Pay Silas Vance immediately to secure your supplies and exit.",
    "Confront Victor Drax directly to demand passage through the door.",
    "Draw your iron dagger and prepare for a sudden ambush.",
    "Attempt to de-escalate by offering credits to the scarred rider."
  ],
  "outcome_summary": "Matthew is cornered in the general store by Victor Drax while attempting to purchase supplies.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "ambient"
  },
  "thread_resolve": [],
  "thread_add": {
    "id": "confront_predatory_rider",
    "summary": "Avoid or resolve confrontation with Victor Drax",
    "scope": "scene",
    "active": true,
    "urgency": "urgent",
    "progress": []
  },
  "thread_update": [
    {
      "id": "deliver_the_ledger",
      "active": true,
      "urgency": "normal",
      "progress": "traveling toward Red Canyon on foot",
      "progress_kind": "shift"
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

- ruling: est=1607t trimmed=False
- narrate: est=5126t trimmed=False
- extract.scene: est=3959t trimmed=False attempts=1
- extract.state: est=2048t trimmed=False attempts=1
- extract.storytell: est=4171t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 10

**Input:** `I find a camp at the base of the canyon wall. Two men are sitting by a fire, and I see Harker's hat on one of them. I step into the firelight.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## scene
Location: Marrow's Crossing General Store
## Present NPCs (in scene right now)
- Silas Vance (General Store Clerk)
- Victor Drax (Scarred Rider)









## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)
- Parchment map (1)


## Last Turn Narrative (T9)
You reach for a saddle and a mount to begin your journey toward Red Canyon, but find nothing but the dust-coated floorboards of Marrow's Crossing General Store. You stand amidst the shelves of supplies, empty-handed and on foot, while **Silas Vance** stares at you with a blank, mechanical expression, waiting for you to pay for the **Dried Meat**, **Water Canteen**, and **Rope** he just laid upon the counter.

The rhythmic clatter of hooves outside reaches a crescendo as two riders pull up to the storefront. The heavy thud of boots strikes the porch, and a tall man with a jagged scar across his nose—**Victor Drax**—pushes the door open. He doesn't step toward the counter; instead, he leans against the frame, blocking the exit with a casual, predatory stance. He eyes your **Traveler's Cloak** and the heavy rucksack at your hip, a slow, mocking grin spreading across his face as he signals to a companion waiting in the street.


## Current Turn: 10
=== PLAYER INPUT ===
I find a camp at the base of the canyon wall. Two men are sitting by a fire, and I see Harker's hat on one of them. I step into the firelight.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## Inventory
- **Credits** ×500: Payment for supplies.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Parchment map**: Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.


## Location
Marrow's Crossing General Store (marrows_crossing_general_store)
The storefront feels smaller now, the air heavy with the sudden tension of a stranger blocking the only exit.




## Characters

- `silas_vance` | **Silas Vance** (General Store Clerk) [PRESENT] — A wiry man with ink-stained fingers and a brisk, mechanical manner of movement. He possesses a practiced, wary indifference toward customers and focuses intently on his calculations. | last seen: Marrow's Crossing General Store

- `victor_drax` | **Victor Drax** (Scarred Rider) [PRESENT] — Tall man with a jagged scar cutting across the bridge of his nose; carries himself with a casual, predatory confidence. He possesses a mocking demeanor and seems to actively seek out targets for intimidation. | last seen: Marrow's Crossing General Store

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `cabin_dweller` | **Cabin Dweller** [KNOWN] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (5 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (1 turns ago)   - [SHIFT] Investigated the local assay office.   - [SHIFT] traveling toward Red Canyon on foot
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (7 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (2 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings
- `confront_predatory_rider` [SCENE] [URGENT] Avoid or resolve confrontation with Victor Drax





## Prior History
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.

- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.

- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.

- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.

- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.

- [T7] Matthew successfully pries open a hidden tin box to find a map marked with crimson ink, only to hear something dragging itself through the shadows behind him.

- [T8] Matthew arrives at the general store to purchase supplies just as approaching riders draw Silas Vance's attention.

## Recent Turns

**T9:** You reach for a saddle and a mount to begin your journey toward Red Canyon, but find nothing but the dust-coated floorboards of Marrow's Crossing General Store. You stand amidst the shelves of supplies, empty-handed and on foot, while **Silas Vance** stares at you with a blank, mechanical expression, waiting for you to pay for the **Dried Meat**, **Water Canteen**, and **Rope** he just laid upon the counter.

The rhythmic clatter of hooves outside reaches a crescendo as two riders pull up to the storefront. The heavy thud of boots strikes the porch, and a tall man with a jagged scar across his nose—**Victor Drax**—pushes the door open. He doesn't step toward the counter; instead, he leans against the frame, blocking the exit with a casual, predatory stance. He eyes your **Traveler's Cloak** and the heavy rucksack at your hip, a slow, mocking grin spreading across his face as he signals to a companion waiting in the street.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 10) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I find a camp at the base of the canyon wall. Two men are sitting by a fire, and I see Harker's hat on one of them. I step into the firelight.
=== END PLAYER INPUT ===

**Beat:** PRESSURE — surface as `ambient`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.**Outcome:** transition
Write the arrival at the new location, not the departure from this one. The scene moves forward.


```

### Extract Scene User Prompt
```
## location
`marrows_crossing_general_store` | Marrow's Crossing General Store
The storefront feels smaller now, the air heavy with the sudden tension of a stranger blocking the only exit.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T9 context)
You reach for a saddle and a mount to begin your journey toward Red Canyon, but find nothing but the dust-coated floorboards of Marrow's Crossing General Store. You stand amidst the shelves of supplies, empty-handed and on foot, while **Silas Vance** stares at you with a blank, mechanical expression, waiting for you to pay for the **Dried Meat**, **Water Canteen**, and **Rope** he just laid upon the counter.

The rhythmic clatter of hooves outside reaches a crescendo as two riders pull up to the storefront. The heavy thud of boots strikes the porch, and a tall man with a jagged scar across his nose—**Victor Drax**—pushes the door open. He doesn't step toward the counter; instead, he leans against the frame, blocking the exit with a casual, predatory stance. He eyes your **Traveler's Cloak** and the heavy rucksack at your hip, a slow, mocking grin spreading across his face as he signals to a companion waiting in the street.

## CURRENT TURN 10 NARRATION
You step into the flickering orange light of a campfire nestled against the sheer, red-streaked base of the canyon wall. The warmth of the flames offers little comfort against the biting chill creeping up from the canyon floor. Two men sit hunched over the embers, their silhouettes jagged and dark against the stone. One man, a wiry figure with a nervous habit of picking at his fingernails, stares intently into the coals, while the other leans back against a supply crate, his eyes half-closed in a drunken stupor.

The firelight catches a familiar shape resting on the second man's knee: a sweat-stained, wide-brimmed hat with a distinctive frayed edge. It is Old Man Harker's hat. The crackle of burning cedar fills the silence between you, punctuated only by the low, rhythmic murmur of their conversation. As your shadow stretches long and distorted across the canyon floor toward them, both men freeze. The wiry man looks up, his eyes widening as they lock onto yours, while the other slowly shifts his weight, his hand drifting toward a heavy iron poker resting near the fire.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Payment for supplies.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `parchment_map` | Parchment map ×1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.

## player_intent
persuade: The player approaches a campfire where two men are sitting to confront or interact with someone wearing Harker's hat.
## CURRENT TURN 10 NARRATION
You step into the flickering orange light of a campfire nestled against the sheer, red-streaked base of the canyon wall. The warmth of the flames offers little comfort against the biting chill creeping up from the canyon floor. Two men sit hunched over the embers, their silhouettes jagged and dark against the stone. One man, a wiry figure with a nervous habit of picking at his fingernails, stares intently into the coals, while the other leans back against a supply crate, his eyes half-closed in a drunken stupor.

The firelight catches a familiar shape resting on the second man's knee: a sweat-stained, wide-brimmed hat with a distinctive frayed edge. It is Old Man Harker's hat. The crackle of burning cedar fills the silence between you, punctuated only by the low, rhythmic murmur of their conversation. As your shadow stretches long and distorted across the canyon floor toward them, both men freeze. The wiry man looks up, his eyes widening as they lock onto yours, while the other slowly shifts his weight, his hand drifting toward a heavy iron poker resting near the fire.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Payment for supplies.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `parchment_map`: Parchment map x1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.

## PC conditions (this turn)
- exposed: Exposed — The biting chill of the canyon floor is beginning to seep through your clothing.


## Characters

- `drunken_camp_dweller` | **Drunken Camp Dweller** (Campfire Resident) [PRESENT] — A man prone to drunken stupors who leans heavily against supply crates. He carries Old Man Harker's distinctive frayed hat on his knee. | reaching for iron poker | last seen: Canyon Base Camp

- `nervous_camp_dweller` | **Nervous Camp Dweller** (Campfire Resident) [PRESENT] — A wiry man with a nervous habit of picking at his fingernails. He appears jumpy and hyper-aware of his surroundings. | staring into coals, eyes widening | last seen: Canyon Base Camp

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `cabin_dweller` | **Cabin Dweller** [KNOWN] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office



## location
**Canyon Base Camp** — A campfire flickers against a sheer, red-streaked canyon wall, casting long shadows across the cold floor.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (5 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (5 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (1 turns ago)   - [SHIFT] Investigated the local assay office.   - [SHIFT] traveling toward Red Canyon on foot
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (7 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (2 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings
- `confront_predatory_rider` [SCENE] [URGENT] Avoid or resolve confrontation with Victor Drax


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: Pressure; Resolve a Threat
Gate: allow

## GM Beat
Type: **PRESSURE**
Surface: `ambient`
Expires: Turn 11

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.

## Recent Beats
T5: No beat emitted this turn
T6: REVELATION (environmental)
T7: PRESSURE (environmental)
T8: COMPLICATION (npc_behavior)
T9: PRESSURE (ambient)


## Recent Outcomes
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.
- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.
- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.
- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.
- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.
- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.
- [T7] Matthew successfully pries open a hidden tin box to find a map marked with crimson ink, only to hear something dragging itself through the shadows behind him.
- [T8] Matthew arrives at the general store to purchase supplies just as approaching riders draw Silas Vance's attention.

## prior turn context

**T9:** You reach for a saddle and a mount to begin your journey toward Red Canyon, but find nothing but the dust-coated floorboards of Marrow's Crossing General Store. You stand amidst the shelves of supplies, empty-handed and on foot, while **Silas Vance** stares at you with a blank, mechanical expression, waiting for you to pay for the **Dried Meat**, **Water Canteen**, and **Rope** he just laid upon the counter.

The rhythmic clatter of hooves outside reaches a crescendo as two riders pull up to the storefront. The heavy thud of boots strikes the porch, and a tall man with a jagged scar across his nose—**Victor Drax**—pushes the door open. He doesn't step toward the counter; instead, he leans against the frame, blocking the exit with a casual, predatory stance. He eyes your **Traveler's Cloak** and the heavy rucksack at your hip, a slow, mocking grin spreading across his face as he signals to a companion waiting in the street.


## player_intent
**persuade**: The player approaches a campfire where two men are sitting to confront or interact with someone wearing Harker's hat.

## CURRENT TURN 10 NARRATION
You step into the flickering orange light of a campfire nestled against the sheer, red-streaked base of the canyon wall. The warmth of the flames offers little comfort against the biting chill creeping up from the canyon floor. Two men sit hunched over the embers, their silhouettes jagged and dark against the stone. One man, a wiry figure with a nervous habit of picking at his fingernails, stares intently into the coals, while the other leans back against a supply crate, his eyes half-closed in a drunken stupor.

The firelight catches a familiar shape resting on the second man's knee: a sweat-stained, wide-brimmed hat with a distinctive frayed edge. It is Old Man Harker's hat. The crackle of burning cedar fills the silence between you, punctuated only by the low, rhythmic murmur of their conversation. As your shadow stretches long and distorted across the canyon floor toward them, both men freeze. The wiry man looks up, his eyes widening as they lock onto yours, while the other slowly shifts his weight, his hand drifting toward a heavy iron poker resting near the fire.
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
  "intent": "The player approaches a campfire where two men are sitting to confront or interact with someone wearing Harker's hat.",
  "intent_verb": "persuade",
  "target": "the men by the fire",
  "impossible": false,
  "scene_motion": "transition",
  "check": {
    "required": false
  }
}
```

### Narration

You step into the flickering orange light of a campfire nestled against the sheer, red-streaked base of the canyon wall. The warmth of the flames offers little comfort against the biting chill creeping up from the canyon floor. Two men sit hunched over the embers, their silhouettes jagged and dark against the stone. One man, a wiry figure with a nervous habit of picking at his fingernails, stares intently into the coals, while the other leans back against a supply crate, his eyes half-closed in a drunken stupor.

The firelight catches a familiar shape resting on the second man's knee: a sweat-stained, wide-brimmed hat with a distinctive frayed edge. It is Old Man Harker's hat. The crackle of burning cedar fills the silence between you, punctuated only by the low, rhythmic murmur of their conversation. As your shadow stretches long and distorted across the canyon floor toward them, both men freeze. The wiry man looks up, his eyes widening as they lock onto yours, while the other slowly shifts his weight, his hand drifting toward a heavy iron poker resting near the fire.

### Extract Scene

```json
{
  "scene_tags": [
    "tense_encounter",
    "discovery"
  ],
  "scene_tagline": "Shadows by the Campfire",
  "location_change": {
    "id": "red_streaked_canyon_base",
    "name": "Canyon Base Camp",
    "description": "A campfire flickers against a sheer, red-streaked canyon wall, casting long shadows across the cold floor."
  },
  "compendium_npc_update": [
    {
      "id": "nervous_camp_dweller",
      "name": "Nervous Camp Dweller",
      "title": "Campfire Resident",
      "bio": "A wiry man with a nervous habit of picking at his fingernails. He appears jumpy and hyper-aware of his surroundings.",
      "aliases": [],
      "presence": "present",
      "notes": "staring into coals, eyes widening"
    },
    {
      "id": "drunken_camp_dweller",
      "name": "Drunken Camp Dweller",
      "title": "Campfire Resident",
      "bio": "A man prone to drunken stupors who leans heavily against supply crates. He carries Old Man Harker's distinctive frayed hat on his knee.",
      "aliases": [],
      "presence": "present",
      "notes": "reaching for iron poker"
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
      "id": "exposed",
      "label": "Exposed",
      "description": "The biting chill of the canyon floor is beginning to seep through your clothing.",
      "turns_remaining": 3
    }
  ],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "actions": [
    "Demand to know how they obtained Harker's frayed hat.",
    "Offer credits to the drunken man for information.",
    "Draw your iron dagger to intimidate the nervous camper.",
    "Sit by the fire to de-escalate the sudden tension."
  ],
  "outcome_summary": "Matthew approaches the campfire and discovers a man wearing Old Man Harker's distinctive hat, causing the campers to react defensively.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [],
  "thread_add": {
    "id": "harker_hat_connection",
    "summary": "Investigate the men holding Harker's hat",
    "scope": "scene",
    "active": true,
    "urgency": "normal",
    "progress": []
  },
  "thread_update": [
    {
      "id": "confront_predatory_rider",
      "active": false,
      "urgency": "normal",
      "progress": "lost sight of rider in canyon camp",
      "progress_kind": "shift"
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

- ruling: est=1600t trimmed=False
- narrate: est=5122t trimmed=False
- extract.scene: est=4022t trimmed=False attempts=1
- extract.state: est=2000t trimmed=False attempts=1
- extract.storytell: est=4274t trimmed=False attempts=1

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

**Input:** `The men surrender. I find Harker tied up in a nearby cave. He's bruised but alive. I cut him loose and give him water.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** Exposed

## scene
Location: Canyon Base Camp
## Present NPCs (in scene right now)
- Drunken Camp Dweller (Campfire Resident)
- Nervous Camp Dweller (Campfire Resident)









## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)
- Parchment map (1)


## Last Turn Narrative (T10)
You step into the flickering orange light of a campfire nestled against the sheer, red-streaked base of the canyon wall. The warmth of the flames offers little comfort against the biting chill creeping up from the canyon floor. Two men sit hunched over the embers, their silhouettes jagged and dark against the stone. One man, a wiry figure with a nervous habit of picking at his fingernails, stares intently into the coals, while the other leans back against a supply crate, his eyes half-closed in a drunken stupor.

The firelight catches a familiar shape resting on the second man's knee: a sweat-stained, wide-brimmed hat with a distinctive frayed edge. It is Old Man Harker's hat. The crackle of burning cedar fills the silence between you, punctuated only by the low, rhythmic murmur of their conversation. As your shadow stretches long and distorted across the canyon floor toward them, both men freeze. The wiry man looks up, his eyes widening as they lock onto yours, while the other slowly shifts his weight, his hand drifting toward a heavy iron poker resting near the fire.


## Current Turn: 11
=== PLAYER INPUT ===
The men surrender. I find Harker tied up in a nearby cave. He's bruised but alive. I cut him loose and give him water.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** Exposed

## Inventory
- **Credits** ×500: Payment for supplies.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Parchment map**: Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.


## Location
Canyon Base Camp (red_streaked_canyon_base)
A campfire flickers against a sheer, red-streaked canyon wall, casting long shadows across the cold floor.




## Characters

- `drunken_camp_dweller` | **Drunken Camp Dweller** (Campfire Resident) [PRESENT] — A man prone to drunken stupors who leans heavily against supply crates. He carries Old Man Harker's distinctive frayed hat on his knee. | last seen: Canyon Base Camp

- `nervous_camp_dweller` | **Nervous Camp Dweller** (Campfire Resident) [PRESENT] — A wiry man with a nervous habit of picking at his fingernails. He appears jumpy and hyper-aware of his surroundings. | last seen: Canyon Base Camp

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `cabin_dweller` | **Cabin Dweller** [KNOWN] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (5 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (2 turns ago)   - [SHIFT] Investigated the local assay office.   - [SHIFT] Traveled toward Red Canyon on foot.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (8 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (3 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings
- `harker_hat_connection` [SCENE] [NORMAL] Investigate the men holding Harker's hat





## Prior History
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.

- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.

- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.

- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.

- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.

- [T7] Matthew successfully pries open a hidden tin box to find a map marked with crimson ink, only to hear something dragging itself through the shadows behind him.

- [T8] Matthew arrives at the general store to purchase supplies just as approaching riders draw Silas Vance's attention.

- [T9] Matthew is cornered in the general store by Victor Drax while attempting to purchase supplies.

## Recent Turns

**T10:** You step into the flickering orange light of a campfire nestled against the sheer, red-streaked base of the canyon wall. The warmth of the flames offers little comfort against the biting chill creeping up from the canyon floor. Two men sit hunched over the embers, their silhouettes jagged and dark against the stone. One man, a wiry figure with a nervous habit of picking at his fingernails, stares intently into the coals, while the other leans back against a supply crate, his eyes half-closed in a drunken stupor.

The firelight catches a familiar shape resting on the second man's knee: a sweat-stained, wide-brimmed hat with a distinctive frayed edge. It is Old Man Harker's hat. The crackle of burning cedar fills the silence between you, punctuated only by the low, rhythmic murmur of their conversation. As your shadow stretches long and distorted across the canyon floor toward them, both men freeze. The wiry man looks up, his eyes widening as they lock onto yours, while the other slowly shifts his weight, his hand drifting toward a heavy iron poker resting near the fire.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 11) Result


**Band:** FAIL → The intimidate fails. The attempt fails outright — what you tried to do does not happen.
**Roll:** d12: 1 + 1 (Charisma) → 2


**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.

=== PLAYER INPUT ===
The men surrender. I find Harker tied up in a nearby cave. He's bruised but alive. I cut him loose and give him water.
=== END PLAYER INPUT ===

**Beat:** BREATHING ROOM — surface as `ambient`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.**Outcome:** advance
Narrate through to the resolution. Do not linger on preparation or setup. Something significant happens this turn.


```

### Extract Scene User Prompt
```
## location
`red_streaked_canyon_base` | Canyon Base Camp
A campfire flickers against a sheer, red-streaked canyon wall, casting long shadows across the cold floor.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T10 context)
You step into the flickering orange light of a campfire nestled against the sheer, red-streaked base of the canyon wall. The warmth of the flames offers little comfort against the biting chill creeping up from the canyon floor. Two men sit hunched over the embers, their silhouettes jagged and dark against the stone. One man, a wiry figure with a nervous habit of picking at his fingernails, stares intently into the coals, while the other leans back against a supply crate, his eyes half-closed in a drunken stupor.

The firelight catches a familiar shape resting on the second man's knee: a sweat-stained, wide-brimmed hat with a distinctive frayed edge. It is Old Man Harker's hat. The crackle of burning cedar fills the silence between you, punctuated only by the low, rhythmic murmur of their conversation. As your shadow stretches long and distorted across the canyon floor toward them, both men freeze. The wiry man looks up, his eyes widening as they lock onto yours, while the other slowly shifts his weight, his hand drifting toward a heavy iron poker resting near the fire.

## CURRENT TURN 11 NARRATION
You step toward the fire, voice low and threatening, but your words lack the weight to cow them. The wiry man, **Nervous Camp Dweller**, scoffs at your posturing, his eyes darting to the iron poker as he grips it tighter. Beside him, the **Drunken Camp Dweller** merely blinks sleepily, clutching Old Man Harker's hat to his chest with a dismissive grunt. They show no sign of surrender; instead, they settle deeper into their defensive stances, watching you with growing contempt.

The intimidation fails to break their resolve or yield any answers about the missing man. The fire continues to crackle, indifferent to your attempt at dominance, while the two men remain stubbornly entrenched in their camp. The silence of the canyon floor feels heavier now, pressing against your ears as the two residents wait to see if you will actually draw your **Iron dagger** or simply retreat into the dark.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- exposed — The biting chill of the canyon floor is beginning to seep through your clothing.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Payment for supplies.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `parchment_map` | Parchment map ×1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.

## player_intent
intimidate: The player attempts to intimidate the two camp dwellers into surrendering so they can find Old Man Harker.
## CURRENT TURN 11 NARRATION
You step toward the fire, voice low and threatening, but your words lack the weight to cow them. The wiry man, **Nervous Camp Dweller**, scoffs at your posturing, his eyes darting to the iron poker as he grips it tighter. Beside him, the **Drunken Camp Dweller** merely blinks sleepily, clutching Old Man Harker's hat to his chest with a dismissive grunt. They show no sign of surrender; instead, they settle deeper into their defensive stances, watching you with growing contempt.

The intimidation fails to break their resolve or yield any answers about the missing man. The fire continues to crackle, indifferent to your attempt at dominance, while the two men remain stubbornly entrenched in their camp. The silence of the canyon floor feels heavier now, pressing against your ears as the two residents wait to see if you will actually draw your **Iron dagger** or simply retreat into the dark.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Payment for supplies.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `parchment_map`: Parchment map x1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.


## Characters

- `drunken_camp_dweller` | **Drunken Camp Dweller** (Campfire Resident) [PRESENT] — A man prone to drunken stupors who leans heavily against supply crates. He carries Old Man Harker's distinctive frayed hat on his knee. | clutching hat with a grunt | last seen: Canyon Base Camp

- `nervous_camp_dweller` | **Nervous Camp Dweller** (Campfire Resident) [PRESENT] — A wiry man with a nervous habit of picking at his fingernails. He appears jumpy and hyper-aware of his surroundings. | gripping iron poker defensively | last seen: Canyon Base Camp

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `cabin_dweller` | **Cabin Dweller** [KNOWN] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office



## location
**Canyon Base Camp** — The silence of the canyon floor feels heavier, pressing against your ears as the fire crackles indifferently.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (5 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (5 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (2 turns ago)   - [SHIFT] Investigated the local assay office.   - [SHIFT] Traveled toward Red Canyon on foot.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (8 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (3 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings
- `harker_hat_connection` [SCENE] [NORMAL] Investigate the men holding Harker's hat


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: Breathe
Gate: allow

## GM Beat
Type: **BREATHING ROOM**
Surface: `ambient`
Expires: Turn 12

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.

## Recent Beats
T6: REVELATION (environmental)
T7: PRESSURE (environmental)
T8: COMPLICATION (npc_behavior)
T9: PRESSURE (ambient)
T10: BREATHING ROOM (ambient)


## rules_outcome
Band: FAIL. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.

## Recent Outcomes
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.
- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.
- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.
- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.
- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.
- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.
- [T7] Matthew successfully pries open a hidden tin box to find a map marked with crimson ink, only to hear something dragging itself through the shadows behind him.
- [T8] Matthew arrives at the general store to purchase supplies just as approaching riders draw Silas Vance's attention.
- [T9] Matthew is cornered in the general store by Victor Drax while attempting to purchase supplies.

## prior turn context

**T10:** You step into the flickering orange light of a campfire nestled against the sheer, red-streaked base of the canyon wall. The warmth of the flames offers little comfort against the biting chill creeping up from the canyon floor. Two men sit hunched over the embers, their silhouettes jagged and dark against the stone. One man, a wiry figure with a nervous habit of picking at his fingernails, stares intently into the coals, while the other leans back against a supply crate, his eyes half-closed in a drunken stupor.

The firelight catches a familiar shape resting on the second man's knee: a sweat-stained, wide-brimmed hat with a distinctive frayed edge. It is Old Man Harker's hat. The crackle of burning cedar fills the silence between you, punctuated only by the low, rhythmic murmur of their conversation. As your shadow stretches long and distorted across the canyon floor toward them, both men freeze. The wiry man looks up, his eyes widening as they lock onto yours, while the other slowly shifts his weight, his hand drifting toward a heavy iron poker resting near the fire.


## player_intent
**intimidate**: The player attempts to intimidate the two camp dwellers into surrendering so they can find Old Man Harker.

## CURRENT TURN 11 NARRATION
You step toward the fire, voice low and threatening, but your words lack the weight to cow them. The wiry man, **Nervous Camp Dweller**, scoffs at your posturing, his eyes darting to the iron poker as he grips it tighter. Beside him, the **Drunken Camp Dweller** merely blinks sleepily, clutching Old Man Harker's hat to his chest with a dismissive grunt. They show no sign of surrender; instead, they settle deeper into their defensive stances, watching you with growing contempt.

The intimidation fails to break their resolve or yield any answers about the missing man. The fire continues to crackle, indifferent to your attempt at dominance, while the two men remain stubbornly entrenched in their camp. The silence of the canyon floor feels heavier now, pressing against your ears as the two residents wait to see if you will actually draw your **Iron dagger** or simply retreat into the dark.
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
  "intent": "The player attempts to intimidate the two camp dwellers into surrendering so they can find Old Man Harker.",
  "intent_verb": "intimidate",
  "target": "Drunken Camp Dweller and Nervous Camp Dweller",
  "scene_motion": "advance",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal"
  }
}
```

### Narration

You step toward the fire, voice low and threatening, but your words lack the weight to cow them. The wiry man, **Nervous Camp Dweller**, scoffs at your posturing, his eyes darting to the iron poker as he grips it tighter. Beside him, the **Drunken Camp Dweller** merely blinks sleepily, clutching Old Man Harker's hat to his chest with a dismissive grunt. They show no sign of surrender; instead, they settle deeper into their defensive stances, watching you with growing contempt.

The intimidation fails to break their resolve or yield any answers about the missing man. The fire continues to crackle, indifferent to your attempt at dominance, while the two men remain stubbornly entrenched in their camp. The silence of the canyon floor feels heavier now, pressing against your ears as the two residents wait to see if you will actually draw your **Iron dagger** or simply retreat into the dark.

### Extract Scene

```json
{
  "scene_tags": [
    "tense_confrontation",
    "hostility"
  ],
  "scene_tagline": "A Failed Show of Force",
  "location_description": "The silence of the canyon floor feels heavier, pressing against your ears as the fire crackles indifferently.",
  "compendium_npc_update": [
    {
      "id": "nervous_camp_dweller",
      "aliases": [],
      "notes": "gripping iron poker defensively"
    },
    {
      "id": "drunken_camp_dweller",
      "aliases": [],
      "notes": "clutching hat with a grunt"
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
  "pc_condition_remove": [
    {
      "id": "exposed"
    }
  ]
}
```

### Storyteller

```json
{
  "actions": [
    "Draw your iron dagger to force a confrontation.",
    "Offer credits to buy information about Harker.",
    "Retreat from the camp to find another lead.",
    "Sit by the fire to de-escalate the tension."
  ],
  "outcome_summary": "Matthew's attempt to intimidate the camp dwellers failed, leaving them defensive and uncooperative.",
  "gm_beat": {
    "type": "breathing_room",
    "surface_as": "ambient"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "harker_hat_connection",
      "active": true,
      "urgency": "normal",
      "progress": "confronted camp dwellers holding hat",
      "progress_kind": "advancement"
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

- ruling: est=1639t trimmed=False
- narrate: est=5224t trimmed=False
- extract.scene: est=3968t trimmed=False attempts=1
- extract.state: est=1977t trimmed=False attempts=1
- extract.storytell: est=4310t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 12

**Input:** `Harker and I ride back to Dustfall together. He's quiet but grateful. The town lights come into view as dusk settles.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## scene
Location: Canyon Base Camp
## Present NPCs (in scene right now)
- Drunken Camp Dweller (Campfire Resident)
- Nervous Camp Dweller (Campfire Resident)









## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)
- Parchment map (1)


## Last Turn Narrative (T11)
You step toward the fire, voice low and threatening, but your words lack the weight to cow them. The wiry man, **Nervous Camp Dweller**, scoffs at your posturing, his eyes darting to the iron poker as he grips it tighter. Beside him, the **Drunken Camp Dweller** merely blinks sleepily, clutching Old Man Harker's hat to his chest with a dismissive grunt. They show no sign of surrender; instead, they settle deeper into their defensive stances, watching you with growing contempt.

The intimidation fails to break their resolve or yield any answers about the missing man. The fire continues to crackle, indifferent to your attempt at dominance, while the two men remain stubbornly entrenched in their camp. The silence of the canyon floor feels heavier now, pressing against your ears as the two residents wait to see if you will actually draw your **Iron dagger** or simply retreat into the dark.


## Current Turn: 12
=== PLAYER INPUT ===
Harker and I ride back to Dustfall together. He's quiet but grateful. The town lights come into view as dusk settles.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## Inventory
- **Credits** ×500: Payment for supplies.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Parchment map**: Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.


## Location
Canyon Base Camp (red_streaked_canyon_base)
The silence of the canyon floor feels heavier, pressing against your ears as the fire crackles indifferently.




## Characters

- `drunken_camp_dweller` | **Drunken Camp Dweller** (Campfire Resident) [PRESENT] — A man prone to drunken stupors who leans heavily against supply crates. He carries Old Man Harker's distinctive frayed hat on his knee. | last seen: Canyon Base Camp

- `nervous_camp_dweller` | **Nervous Camp Dweller** (Campfire Resident) [PRESENT] — A wiry man with a nervous habit of picking at his fingernails. He appears jumpy and hyper-aware of his surroundings. | last seen: Canyon Base Camp

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `cabin_dweller` | **Cabin Dweller** [KNOWN] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (5 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (3 turns ago)   - [SHIFT] Investigated the local assay office.   - [SHIFT] Traveled toward Red Canyon on foot.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (9 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] (latent) [NORMAL] Find out what happened to Old Man Harker. (1 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings
- `harker_hat_connection` [SCENE] [NORMAL] Investigate the men holding Harker's hat (1 turns ago)   - [ADVANCEMENT] confronted camp dwellers holding hat





## Prior History
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.

- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.

- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.

- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.

- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.

- [T7] Matthew successfully pries open a hidden tin box to find a map marked with crimson ink, only to hear something dragging itself through the shadows behind him.

- [T8] Matthew arrives at the general store to purchase supplies just as approaching riders draw Silas Vance's attention.

- [T9] Matthew is cornered in the general store by Victor Drax while attempting to purchase supplies.

- [T10] Matthew approaches the campfire and discovers a man wearing Old Man Harker's distinctive hat, causing the campers to react defensively.

## Recent Turns

**T11:** You step toward the fire, voice low and threatening, but your words lack the weight to cow them. The wiry man, **Nervous Camp Dweller**, scoffs at your posturing, his eyes darting to the iron poker as he grips it tighter. Beside him, the **Drunken Camp Dweller** merely blinks sleepily, clutching Old Man Harker's hat to his chest with a dismissive grunt. They show no sign of surrender; instead, they settle deeper into their defensive stances, watching you with growing contempt.

The intimidation fails to break their resolve or yield any answers about the missing man. The fire continues to crackle, indifferent to your attempt at dominance, while the two men remain stubbornly entrenched in their camp. The silence of the canyon floor feels heavier now, pressing against your ears as the two residents wait to see if you will actually draw your **Iron dagger** or simply retreat into the dark.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 12) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
Harker and I ride back to Dustfall together. He's quiet but grateful. The town lights come into view as dusk settles.
=== END PLAYER INPUT ===

**Beat:** BREATHING ROOM — surface as `ambient`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.**Outcome:** transition
Write the arrival at the new location, not the departure from this one. The scene moves forward.


```

### Extract Scene User Prompt
```
## location
`red_streaked_canyon_base` | Canyon Base Camp
The silence of the canyon floor feels heavier, pressing against your ears as the fire crackles indifferently.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T11 context)
You step toward the fire, voice low and threatening, but your words lack the weight to cow them. The wiry man, **Nervous Camp Dweller**, scoffs at your posturing, his eyes darting to the iron poker as he grips it tighter. Beside him, the **Drunken Camp Dweller** merely blinks sleepily, clutching Old Man Harker's hat to his chest with a dismissive grunt. They show no sign of surrender; instead, they settle deeper into their defensive stances, watching you with growing contempt.

The intimidation fails to break their resolve or yield any answers about the missing man. The fire continues to crackle, indifferent to your attempt at dominance, while the two men remain stubbornly entrenched in their camp. The silence of the canyon floor feels heavier now, pressing against your ears as the two residents wait to see if you will actually draw your **Iron dagger** or simply retreat into the dark.

## CURRENT TURN 12 NARRATION
You ride back toward Dustfall with Old Man Harker, the rhythmic clatter of hooves against the canyon floor filling the silence between you. He remains a man of few words, his eyes fixed on the darkening horizon, though he offers a brief, solemn nod of gratitude when you pass a particularly treacherous stretch of trail. As dusk settles over the red-streaked canyon, the distant, flickering amber lights of Dustfall emerge from the gloom like low-hanging stars.

The town appears as a cluster of dim silhouettes against the deepening violet sky. The familiar scent of woodsmoke and dust drifts toward you on a cooling breeze, signaling your return to the edge of civilization. As the outskirts of the settlement come into view, the distant murmur of voices and the occasional clink of iron tools drift through the air, breaking the heavy stillness that had gripped the canyon floor. You approach the main thoroughfare, where the shadows of the buildings stretch long and thin across the dirt road.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Payment for supplies.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `parchment_map` | Parchment map ×1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.

## player_intent
transition: The player intends to travel with Harker from the Canyon Base Camp back to the town of Dustfall.
## CURRENT TURN 12 NARRATION
You ride back toward Dustfall with Old Man Harker, the rhythmic clatter of hooves against the canyon floor filling the silence between you. He remains a man of few words, his eyes fixed on the darkening horizon, though he offers a brief, solemn nod of gratitude when you pass a particularly treacherous stretch of trail. As dusk settles over the red-streaked canyon, the distant, flickering amber lights of Dustfall emerge from the gloom like low-hanging stars.

The town appears as a cluster of dim silhouettes against the deepening violet sky. The familiar scent of woodsmoke and dust drifts toward you on a cooling breeze, signaling your return to the edge of civilization. As the outskirts of the settlement come into view, the distant murmur of voices and the occasional clink of iron tools drift through the air, breaking the heavy stillness that had gripped the canyon floor. You approach the main thoroughfare, where the shadows of the buildings stretch long and thin across the dirt road.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Payment for supplies.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `parchment_map`: Parchment map x1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.


## Characters

- `old_man_harker` | **Old Man Harker** (Traveling Companion) [PRESENT] — A man of few words with a solemn demeanor and eyes fixed on the horizon. He travels with a quiet dignity and shows gratitude through subtle gestures. | riding beside player in silence | last seen: Dustfall Outskirts

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `cabin_dweller` | **Cabin Dweller** [KNOWN] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `drunken_camp_dweller` | **Drunken Camp Dweller** (Campfire Resident) [KNOWN] — A man prone to drunken stupors who leans heavily against supply crates. He carries Old Man Harker's distinctive frayed hat on his knee. | last seen: Canyon Base Camp

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office



## location
**Dustfall Outskirts** — A cluster of dim silhouettes against a violet sky, where the scent of woodsmoke and dust meets the cooling breeze.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (5 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (5 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (3 turns ago)   - [SHIFT] Investigated the local assay office.   - [SHIFT] Traveled toward Red Canyon on foot.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (9 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] (latent) [NORMAL] Find out what happened to Old Man Harker. (1 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings
- `harker_hat_connection` [SCENE] [NORMAL] Investigate the men holding Harker's hat (1 turns ago)   - [ADVANCEMENT] confronted camp dwellers holding hat


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## GM Beat
Type: **BREATHING ROOM**
Surface: `ambient`
Expires: Turn 13

This beat is active in the scene. The narrator integrated it into this turn's narration. Consider it when selecting this turn's beat — avoid repeating the same type unless the narrative momentum demands it.

## Recent Beats
T7: PRESSURE (environmental)
T8: COMPLICATION (npc_behavior)
T9: PRESSURE (ambient)
T10: BREATHING ROOM (ambient)
T11: BREATHING ROOM (ambient)


## Recent Outcomes
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.
- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.
- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.
- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.
- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.
- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.
- [T7] Matthew successfully pries open a hidden tin box to find a map marked with crimson ink, only to hear something dragging itself through the shadows behind him.
- [T8] Matthew arrives at the general store to purchase supplies just as approaching riders draw Silas Vance's attention.
- [T9] Matthew is cornered in the general store by Victor Drax while attempting to purchase supplies.
- [T10] Matthew approaches the campfire and discovers a man wearing Old Man Harker's distinctive hat, causing the campers to react defensively.

## prior turn context

**T11:** You step toward the fire, voice low and threatening, but your words lack the weight to cow them. The wiry man, **Nervous Camp Dweller**, scoffs at your posturing, his eyes darting to the iron poker as he grips it tighter. Beside him, the **Drunken Camp Dweller** merely blinks sleepily, clutching Old Man Harker's hat to his chest with a dismissive grunt. They show no sign of surrender; instead, they settle deeper into their defensive stances, watching you with growing contempt.

The intimidation fails to break their resolve or yield any answers about the missing man. The fire continues to crackle, indifferent to your attempt at dominance, while the two men remain stubbornly entrenched in their camp. The silence of the canyon floor feels heavier now, pressing against your ears as the two residents wait to see if you will actually draw your **Iron dagger** or simply retreat into the dark.


## player_intent
**transition**: The player intends to travel with Harker from the Canyon Base Camp back to the town of Dustfall.

## CURRENT TURN 12 NARRATION
You ride back toward Dustfall with Old Man Harker, the rhythmic clatter of hooves against the canyon floor filling the silence between you. He remains a man of few words, his eyes fixed on the darkening horizon, though he offers a brief, solemn nod of gratitude when you pass a particularly treacherous stretch of trail. As dusk settles over the red-streaked canyon, the distant, flickering amber lights of Dustfall emerge from the gloom like low-hanging stars.

The town appears as a cluster of dim silhouettes against the deepening violet sky. The familiar scent of woodsmoke and dust drifts toward you on a cooling breeze, signaling your return to the edge of civilization. As the outskirts of the settlement come into view, the distant murmur of voices and the occasional clink of iron tools drift through the air, breaking the heavy stillness that had gripped the canyon floor. You approach the main thoroughfare, where the shadows of the buildings stretch long and thin across the dirt road.
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
  "intent": "The player intends to travel with Harker from the Canyon Base Camp back to the town of Dustfall.",
  "intent_verb": "transition",
  "target": "Dustfall",
  "impossible": false,
  "scene_motion": "transition",
  "check": {
    "required": false
  }
}
```

### Narration

You ride back toward Dustfall with Old Man Harker, the rhythmic clatter of hooves against the canyon floor filling the silence between you. He remains a man of few words, his eyes fixed on the darkening horizon, though he offers a brief, solemn nod of gratitude when you pass a particularly treacherous stretch of trail. As dusk settles over the red-streaked canyon, the distant, flickering amber lights of Dustfall emerge from the gloom like low-hanging stars.

The town appears as a cluster of dim silhouettes against the deepening violet sky. The familiar scent of woodsmoke and dust drifts toward you on a cooling breeze, signaling your return to the edge of civilization. As the outskirts of the settlement come into view, the distant murmur of voices and the occasional clink of iron tools drift through the air, breaking the heavy stillness that had gripped the canyon floor. You approach the main thoroughfare, where the shadows of the buildings stretch long and thin across the dirt road.

### Extract Scene

```json
{
  "scene_tags": [
    "travel",
    "dusk",
    "approaching_town"
  ],
  "scene_tagline": "Returning to Dustfall",
  "location_change": {
    "id": "dustfall_outskirts",
    "name": "Dustfall Outskirts",
    "description": "A cluster of dim silhouettes against a violet sky, where the scent of woodsmoke and dust meets the cooling breeze."
  },
  "compendium_npc_update": [
    {
      "id": "old_man_harker",
      "name": "Old Man Harker",
      "title": "Traveling Companion",
      "bio": "A man of few words with a solemn demeanor and eyes fixed on the horizon. He travels with a quiet dignity and shows gratitude through subtle gestures.",
      "aliases": [],
      "presence": "present",
      "notes": "riding beside player in silence"
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [
    {
      "id": "traveler_cloak",
      "name": "Traveler's cloak",
      "notes": "Oiled wool, road-stained, covered in fine choking dust."
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "actions": [
    "Seek out Edda at the Crossed Keys for rumors.",
    "Locate Caron to negotiate the outstanding debt.",
    "Visit the Assay Office to press Silas Vance.",
    "Find Matthew Estrada to exchange information."
  ],
  "outcome_summary": "Matthew returns to the outskirts of Dustfall accompanied by Old Man Harker.",
  "thread_resolve": [
    {
      "id": "harker_hat_connection",
      "resolution_state": "abandoned",
      "outcome": "The hat was recovered/confronted without resolving Harker's fate.",
      "promote_to_world_state": false
    }
  ],
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "returned to Dustfall outskirts with Harker",
      "progress_kind": "advancement"
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

- ruling: est=1584t trimmed=False
- narrate: est=5154t trimmed=False
- extract.scene: est=3943t trimmed=False attempts=1
- extract.state: est=1970t trimmed=False attempts=1
- extract.storytell: est=4284t trimmed=False attempts=1

### State After Turn

```json
{}
```


---

# TURN 13

**Input:** `I walk Harker to the doc's office and then head to the saloon. The bartender sets a whiskey on the bar and nods. I drink it slow.`

## User Prompts

### Ruling User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## scene
Location: Dustfall Outskirts
## Present NPCs (in scene right now)
- Old Man Harker (Traveling Companion)










## Inventory
- Credits (500)
- Iron dagger (1)
- Linen bandages (3)
- Traveler's cloak (1)
- Brass key (1)
- Parchment map (1)


## Last Turn Narrative (T12)
You ride back toward Dustfall with Old Man Harker, the rhythmic clatter of hooves against the canyon floor filling the silence between you. He remains a man of few words, his eyes fixed on the darkening horizon, though he offers a brief, solemn nod of gratitude when you pass a particularly treacherous stretch of trail. As dusk settles over the red-streaked canyon, the distant, flickering amber lights of Dustfall emerge from the gloom like low-hanging stars.

The town appears as a cluster of dim silhouettes against the deepening violet sky. The familiar scent of woodsmoke and dust drifts toward you on a cooling breeze, signaling your return to the edge of civilization. As the outskirts of the settlement come into view, the distant murmur of voices and the occasional clink of iron tools drift through the air, breaking the heavy stillness that had gripped the canyon floor. You approach the main thoroughfare, where the shadows of the buildings stretch long and thin across the dirt road.


## Current Turn: 13
=== PLAYER INPUT ===
I walk Harker to the doc's office and then head to the saloon. The bartender sets a whiskey on the bar and nods. I drink it slow.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 strength=3 wits=2

**Conditions:** none

## Inventory
- **Credits** ×500: Payment for supplies.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, covered in fine choking dust.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Parchment map**: Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.


## Location
Dustfall Outskirts (dustfall_outskirts)
A cluster of dim silhouettes against a violet sky, where the scent of woodsmoke and dust meets the cooling breeze.




## Characters

- `old_man_harker` | **Old Man Harker** (Traveling Companion) [PRESENT] — A man of few words with a solemn demeanor and eyes fixed on the horizon. He travels with a quiet dignity and shows gratitude through subtle gestures. | last seen: Dustfall Outskirts

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [KNOWN] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | last seen: Assay Office

- `cabin_dweller` | **Cabin Dweller** [KNOWN] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `drunken_camp_dweller` | **Drunken Camp Dweller** (Campfire Resident) [KNOWN] — A man prone to drunken stupors who leans heavily against supply crates. He carries Old Man Harker's distinctive frayed hat on his knee. | last seen: Canyon Base Camp

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office




## World State
- Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.
- Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.
- The road has been quieter than usual this season — fewer caravans, more independent runners, more opportunists.

_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

### Current Threads


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (4 turns ago)   - [SHIFT] Investigated the local assay office.   - [SHIFT] Traveled toward Red Canyon on foot.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (10 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (1 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings   - [ADVANCEMENT] returned to Dustfall outskirts with Harker





## Prior History
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.

- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.

- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.

- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.

- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.

- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.

- [T7] Matthew successfully pries open a hidden tin box to find a map marked with crimson ink, only to hear something dragging itself through the shadows behind him.

- [T8] Matthew arrives at the general store to purchase supplies just as approaching riders draw Silas Vance's attention.

- [T9] Matthew is cornered in the general store by Victor Drax while attempting to purchase supplies.

- [T10] Matthew approaches the campfire and discovers a man wearing Old Man Harker's distinctive hat, causing the campers to react defensively.

- [T11] Matthew's attempt to intimidate the camp dwellers failed, leaving them defensive and uncooperative.

## Recent Turns

**T12:** You ride back toward Dustfall with Old Man Harker, the rhythmic clatter of hooves against the canyon floor filling the silence between you. He remains a man of few words, his eyes fixed on the darkening horizon, though he offers a brief, solemn nod of gratitude when you pass a particularly treacherous stretch of trail. As dusk settles over the red-streaked canyon, the distant, flickering amber lights of Dustfall emerge from the gloom like low-hanging stars.

The town appears as a cluster of dim silhouettes against the deepening violet sky. The familiar scent of woodsmoke and dust drifts toward you on a cooling breeze, signaling your return to the edge of civilization. As the outskirts of the settlement come into view, the distant murmur of voices and the occasional clink of iron tools drift through the air, breaking the heavy stillness that had gripped the canyon floor. You approach the main thoroughfare, where the shadows of the buildings stretch long and thin across the dirt road.

### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.




## This Turn's (Turn 13) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



=== PLAYER INPUT ===
I walk Harker to the doc's office and then head to the saloon. The bartender sets a whiskey on the bar and nods. I drink it slow.
=== END PLAYER INPUT ===

**Outcome:** transition
Write the arrival at the new location, not the departure from this one. The scene moves forward.


```

### Extract Scene User Prompt
```
## location
`dustfall_outskirts` | Dustfall Outskirts
A cluster of dim silhouettes against a violet sky, where the scent of woodsmoke and dust meets the cooling breeze.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T12 context)
You ride back toward Dustfall with Old Man Harker, the rhythmic clatter of hooves against the canyon floor filling the silence between you. He remains a man of few words, his eyes fixed on the darkening horizon, though he offers a brief, solemn nod of gratitude when you pass a particularly treacherous stretch of trail. As dusk settles over the red-streaked canyon, the distant, flickering amber lights of Dustfall emerge from the gloom like low-hanging stars.

The town appears as a cluster of dim silhouettes against the deepening violet sky. The familiar scent of woodsmoke and dust drifts toward you on a cooling breeze, signaling your return to the edge of civilization. As the outskirts of the settlement come into view, the distant murmur of voices and the occasional clink of iron tools drift through the air, breaking the heavy stillness that had gripped the canyon floor. You approach the main thoroughfare, where the shadows of the buildings stretch long and thin across the dirt road.

## CURRENT TURN 13 NARRATION
You guide **Old Man Harker** toward the doctor's office, his gait heavy and uneven against the settling dust of the outskirts. He offers no protest to the assistance, merely leaning into your stride with a grim, silent determination as you reach the clinic's door. Once he is settled within, you turn toward the dim glow of the saloon, the rhythmic thud of your boots echoing against the packed earth.

The heavy doors of the saloon swing open to reveal a haze of tobacco smoke and low-light amber. The **Bartender**, a wiry man with sun-cracked skin, eyes your arrival with a calculating gaze before sliding a glass of whiskey across the scarred wood of the bar. He offers a single, curt nod as the liquid settles into a shallow pool in the glass.

You drink the whiskey slow, letting the burn coat your throat and settle the tension in your chest. Around you, the low murmur of voices continues, a constant backdrop to the clink of iron coins and the shifting of stools. The air is thick with the scent of stale ale and woodsmoke, a stark contrast to the cooling canyon breeze you left behind.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Payment for supplies.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `parchment_map` | Parchment map ×1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.

## player_intent
transition: The player moves from the outskirts of Dustfall to the doctor's office and then to the saloon to consume a drink.
## CURRENT TURN 13 NARRATION
You guide **Old Man Harker** toward the doctor's office, his gait heavy and uneven against the settling dust of the outskirts. He offers no protest to the assistance, merely leaning into your stride with a grim, silent determination as you reach the clinic's door. Once he is settled within, you turn toward the dim glow of the saloon, the rhythmic thud of your boots echoing against the packed earth.

The heavy doors of the saloon swing open to reveal a haze of tobacco smoke and low-light amber. The **Bartender**, a wiry man with sun-cracked skin, eyes your arrival with a calculating gaze before sliding a glass of whiskey across the scarred wood of the bar. He offers a single, curt nod as the liquid settles into a shallow pool in the glass.

You drink the whiskey slow, letting the burn coat your throat and settle the tension in your chest. Around you, the low murmur of voices continues, a constant backdrop to the clink of iron coins and the shifting of stools. The air is thick with the scent of stale ale and woodsmoke, a stark contrast to the cooling canyon breeze you left behind.
## END CURRENT TURN NARRATION

```

### Storyteller User Prompt
```
## Current inventory (this turn)
- `credits`: Credits x500 — Payment for supplies.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, covered in fine choking dust.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `parchment_map`: Parchment map x1 — Hand-drawn map with charcoal markings near Red Canyon and a crimson ink blot over a canyon pass.
- `whiskey_glass`: whiskey glass x1 — A single glass of whiskey.

## PC conditions (this turn)
- relaxed: relaxed — The burn of the whiskey has settled the tension in your chest.


## Characters

- `bartender_dustfall` | **Bartender** (Saloon Bartender) [PRESENT] — A wiry man with sun-cracked skin and a low, rasping voice. He possesses a calculating gaze and seems well-versed in the local rumors and traveler movements. | slides whiskey across the bar | last seen: Assay Office

- `tough_a` | **Bald Tough** (Road thug) [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- `cabin_dweller` | **Cabin Dweller** [KNOWN] — A silent presence felt through the stillness of the abandoned room. No physical form is currently visible in the shadows. | last seen: Weather-Beaten Cabin

- `caron` | **Caron** (Old creditor) [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.

- `drunken_camp_dweller` | **Drunken Camp Dweller** (Campfire Resident) [KNOWN] — A man prone to drunken stupors who leans heavily against supply crates. He carries Old Man Harker's distinctive frayed hat on his knee. | last seen: Canyon Base Camp

- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.

- `halden` | **Halden** (Merchant) [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.

- `kaelen_vance` | **Kaelen Vance** (Sheriff) [KNOWN] — A woman with salt-and-pepper hair pulled into a tight braid and eyes that scan the room with practiced efficiency. She possesses a low, level voice and maintains a steady, unreadable gaze. | last seen: Weather-Beaten Cabin

- `matthew_estrada` | **Matthew Estrada** (Traveler) [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | last seen: Assay Office

- `nervous_camp_dweller` | **Nervous Camp Dweller** (Campfire Resident) [KNOWN] — A wiry man with a nervous habit of picking at his fingernails. He appears jumpy and hyper-aware of his surroundings. | last seen: Canyon Base Camp



## location
**Dustfall Outskirts** — The saloon interior is filled with a haze of tobacco smoke and dim amber light, smelling strongly of stale ale and woodsmoke.
### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.

## threads (4 total — unified list; [SCENE] threads are auto-removed on location change)


### Active Threads (4 active — target: 2-3 arc, 1-2 scene, ~5 total)
- `settle_the_debt` [ARC] [NORMAL] Settle the 500-credit debt with Caron.
- `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (4 turns ago)   - [SHIFT] Investigated the local assay office.   - [SHIFT] Traveled toward Red Canyon on foot.
- `clear_the_road_toughs` [ARC] (latent) [NORMAL] Deal with the toughs blocking the inn entrance. (10 turns ago)   - [SHIFT] arrived at Dustfall Saloon   - [SHIFT] investigating rumors near the inn
- `investigate_harker_disappearance` [ARC] [NORMAL] Find out what happened to Old Man Harker. (1 turns ago)   - [ADVANCEMENT] reached Harker's abandoned cabin   - [ADVANCEMENT] found map with canyon markings   - [ADVANCEMENT] returned to Dustfall outskirts with Harker


_(immutable section omitted — see Static Context > Seed State)_

## pacing_context
Directive: none
Gate: allow

## GM Beat
No beat currently carried over from the previous turn. Choose freely.

## Recent Beats
T8: COMPLICATION (npc_behavior)
T9: PRESSURE (ambient)
T10: BREATHING ROOM (ambient)
T11: BREATHING ROOM (ambient)
T12: No beat emitted this turn


## Recent Outcomes
- [T1] Matthew enters the Dustfall Saloon, drawing wary attention from the silent patrons.
- [T2] The player inquired about local news and learned of Matthew Estrada's inquiries and unusual rider activity near the Crossed Keys.
- [T3] Matthew learns from the bartender that Old Man Harker disappeared near the Crossed Keys amidst rumors of circling riders.
- [T4] Matthew arrives at the Assay Office but is met with defensive hostility from Silas Vance.
- [T5] Matthew learns from Sheriff Kaelen Vance that no missing person report has been filed for Harker.
- [T6] Matthew reaches Harker's weather-beaten cabin after being rebuffed by Sheriff Vance.
- [T7] Matthew successfully pries open a hidden tin box to find a map marked with crimson ink, only to hear something dragging itself through the shadows behind him.
- [T8] Matthew arrives at the general store to purchase supplies just as approaching riders draw Silas Vance's attention.
- [T9] Matthew is cornered in the general store by Victor Drax while attempting to purchase supplies.
- [T10] Matthew approaches the campfire and discovers a man wearing Old Man Harker's distinctive hat, causing the campers to react defensively.
- [T11] Matthew's attempt to intimidate the camp dwellers failed, leaving them defensive and uncooperative.

## prior turn context

**T12:** You ride back toward Dustfall with Old Man Harker, the rhythmic clatter of hooves against the canyon floor filling the silence between you. He remains a man of few words, his eyes fixed on the darkening horizon, though he offers a brief, solemn nod of gratitude when you pass a particularly treacherous stretch of trail. As dusk settles over the red-streaked canyon, the distant, flickering amber lights of Dustfall emerge from the gloom like low-hanging stars.

The town appears as a cluster of dim silhouettes against the deepening violet sky. The familiar scent of woodsmoke and dust drifts toward you on a cooling breeze, signaling your return to the edge of civilization. As the outskirts of the settlement come into view, the distant murmur of voices and the occasional clink of iron tools drift through the air, breaking the heavy stillness that had gripped the canyon floor. You approach the main thoroughfare, where the shadows of the buildings stretch long and thin across the dirt road.


## player_intent
**transition**: The player moves from the outskirts of Dustfall to the doctor's office and then to the saloon to consume a drink.

## CURRENT TURN 13 NARRATION
You guide **Old Man Harker** toward the doctor's office, his gait heavy and uneven against the settling dust of the outskirts. He offers no protest to the assistance, merely leaning into your stride with a grim, silent determination as you reach the clinic's door. Once he is settled within, you turn toward the dim glow of the saloon, the rhythmic thud of your boots echoing against the packed earth.

The heavy doors of the saloon swing open to reveal a haze of tobacco smoke and low-light amber. The **Bartender**, a wiry man with sun-cracked skin, eyes your arrival with a calculating gaze before sliding a glass of whiskey across the scarred wood of the bar. He offers a single, curt nod as the liquid settles into a shallow pool in the glass.

You drink the whiskey slow, letting the burn coat your throat and settle the tension in your chest. Around you, the low murmur of voices continues, a constant backdrop to the clink of iron coins and the shifting of stools. The air is thick with the scent of stale ale and woodsmoke, a stark contrast to the cooling canyon breeze you left behind.
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
  "intent": "The player moves from the outskirts of Dustfall to the doctor's office and then to the saloon to consume a drink.",
  "intent_verb": "transition",
  "target": "Dustfall town center",
  "scene_motion": "transition",
  "check": {
    "required": false
  }
}
```

### Narration

You guide **Old Man Harker** toward the doctor's office, his gait heavy and uneven against the settling dust of the outskirts. He offers no protest to the assistance, merely leaning into your stride with a grim, silent determination as you reach the clinic's door. Once he is settled within, you turn toward the dim glow of the saloon, the rhythmic thud of your boots echoing against the packed earth.

The heavy doors of the saloon swing open to reveal a haze of tobacco smoke and low-light amber. The **Bartender**, a wiry man with sun-cracked skin, eyes your arrival with a calculating gaze before sliding a glass of whiskey across the scarred wood of the bar. He offers a single, curt nod as the liquid settles into a shallow pool in the glass.

You drink the whiskey slow, letting the burn coat your throat and settle the tension in your chest. Around you, the low murmur of voices continues, a constant backdrop to the clink of iron coins and the shifting of stools. The air is thick with the scent of stale ale and woodsmoke, a stark contrast to the cooling canyon breeze you left behind.

### Extract Scene

```json
{
  "scene_tags": [
    "atmosphere",
    "social_interaction"
  ],
  "scene_tagline": "Whiskey and Smoke in the Saloon",
  "location_description": "The saloon interior is filled with a haze of tobacco smoke and dim amber light, smelling strongly of stale ale and woodsmoke.",
  "compendium_npc_update": [
    {
      "id": "old_man_harker",
      "aliases": [],
      "presence": "known",
      "notes": "settled in the clinic"
    },
    {
      "id": "bartender_dustfall",
      "aliases": [],
      "presence": "present",
      "notes": "slides whiskey across the bar"
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "whiskey_glass",
      "name": "whiskey glass",
      "notes": "A single glass of whiskey.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [
    {
      "id": "relaxed",
      "label": "relaxed",
      "description": "The burn of the whiskey has settled the tension in your chest.",
      "turns_remaining": 3
    }
  ],
  "pc_condition_remove": []
}
```

### Storyteller

```json
{
  "actions": [
    "Question the bartender about recent rider activity near the inn.",
    "Scan the saloon patrons for anyone wearing local militia colors.",
    "Search for Caron to discuss the outstanding debt.",
    "Listen for rumors regarding the crimson ink on Harker's map."
  ],
  "outcome_summary": "Matthew brings Old Man Harker to the doctor's office before settling into the saloon for a drink.",
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "found Harker and brought him to town",
      "progress_kind": "advancement"
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

- ruling: est=1603t trimmed=False
- narrate: est=5155t trimmed=False
- extract.scene: est=4006t trimmed=False attempts=1
- extract.state: est=2003t trimmed=False attempts=1
- extract.storytell: est=4338t trimmed=False attempts=1

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
| 1 | 1289 | 4055 | 3392 | 1930 | 3121 | 0 | 0 | — |
| 2 | 1589 | 4466 | 3732 | 1954 | 3654 | 0 | 0 | — |
| 3 | 1619 | 4604 | 3795 | 1924 | 3703 | 0 | 0 | — |
| 4 | 1585 | 4637 | 3748 | 1907 | 3750 | 0 | 0 | — |
| 5 | 1554 | 4674 | 3870 | 2022 | 3982 | 0 | 0 | — |
| 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 6 | 1650 | 4915 | 4035 | 1991 | 3966 | 0 | 0 | — |
| 7 | 1619 | 5001 | 3986 | 1948 | 4162 | 0 | 0 | — |
| 8 | 1598 | 4948 | 3928 | 1999 | 4194 | 0 | 0 | — |
| 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 9 | 1607 | 5126 | 3959 | 2048 | 4171 | 0 | 0 | — |
| 10 | 1600 | 5122 | 4022 | 2000 | 4274 | 0 | 0 | — |
| 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 11 | 1639 | 5224 | 3968 | 1977 | 4310 | 0 | 0 | — |
| 12 | 1584 | 5154 | 3943 | 1970 | 4284 | 0 | 0 | — |
| 13 | 1603 | 5155 | 4006 | 2003 | 4338 | 0 | 0 | — |

**Scope fallback rate:** N/A (not captured in events.jsonl)

## Prompt Redundancy (cross-stream duplication)
Detected duplicated content blocks (>= 3 lines, each >= 60 chars) appearing in multiple streams. The judge should evaluate whether this duplication is intentional (e.g. the narration is correctly fed to all three extractors) or wasted tokens (e.g. the same PC bio rendered redundantly).

### Top overlaps across all turns

| Streams | Total duplicated blocks | Preview |
|---|---:|---|
| narrate + storytell | 38 | `### Active Threads (3 active — target: 2-3 arc, 1-2 scene, ~ / - `settle_the_debt` [ARC] (latent) [NORMAL] Settle the 500-c / - `deliver_the_ledger` [ARC] (latent) [NORMAL] Deliver Halde` |
| narrate + scene | 1 | `A market town built around the confluence of two rivers. Cob / timber-framed buildings, and the constant sound of water fro / town square has a stone well and a statue of the founder. Mo` |
