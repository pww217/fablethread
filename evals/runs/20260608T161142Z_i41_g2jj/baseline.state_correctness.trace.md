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
(not captured this run)
```

### Narrate System Prompt

```
(not captured this run)
```

### Extract Scene System Prompt

```
(not captured this run)
```

### Extract State System Prompt

```
(not captured this run)
```

### Storyteller System Prompt

```
(not captured this run)
```


---

# TURN 1

**Input:** `I ride into Dustfall and tie my horse at the livery. The sun is hot and the main street is quiet. I head for the saloon.`

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
{
  "intent_verb": "transition",
  "intent": "The player travels to a new location and enters a specific establishment.",
  "rolled": false,
  "total_ms": 11494.5,
  "tokens_in": 1117,
  "tokens_out": 75,
  "outcome_summary": ""
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "tense_atmosphere",
    "discovery"
  ],
  "scene_tagline": "A Quiet Arrival in Dustfall",
  "location_change": {
    "id": "dustfall_saloon",
    "name": "Dustfall Saloon",
    "description": "A dim taproom filled with the scent of stale ale and unwashed wool. Patrons sit hunched over small tables in the shadows."
  },
  "location_description": "The main street is unusually quiet, lacking the typical bustle of a waypoint town.",
  "compendium_npc_update": [
    {
      "id": "saloon_patrons",
      "name": "Saloon Patrons",
      "bio": "A small group of locals huddled over drinks in the dim light. They are wary of strangers and maintain a watchful silence.",
      "aliases": [],
      "presence": "present",
      "notes": "watching player with cautious interest"
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
      "id": "dusty_throat",
      "label": "Dusty Throat",
      "description": "The dust from the merchant road has coated your throat, making it scratchy.",
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
    "Order a drink to soothe your dusty throat.",
    "Scan the patrons for news of the road.",
    "Approach the bar to find Edda's information.",
    "Keep your hood low and watch the room."
  ],
  "outcome_summary": "",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [
    {
      "id": "clear_the_road_toughs",
      "resolution_state": "abandoned",
      "outcome": "The player has entered the town, bypassing the road blockade.",
      "promote_to_world_state": false
    }
  ],
  "thread_update": [
    {
      "id": "deliver_the_ledger",
      "active": true,
      "urgency": "normal",
      "progress": "Arrived in Dustfall toward destination",
      "progress_kind": "advancement"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "dustfall_saloon",
    "name": "Dustfall Saloon",
    "description": "A dim taproom filled with the scent of stale ale and unwashed wool. Patrons sit hunched over small tables in the shadows."
  },
  "location_description": "The main street is unusually quiet, lacking the typical bustle of a waypoint town.",
  "pc_condition_add": [
    {
      "id": "dusty_throat",
      "label": "Dusty Throat",
      "description": "The dust from the merchant road has coated your throat, making it scratchy.",
      "turns_remaining": 2
    }
  ],
  "pc_condition_remove": [],
  "scene_tags": [
    "tense_atmosphere",
    "discovery"
  ],
  "scene_tagline": "A Quiet Arrival in Dustfall",
  "compendium_npc_update": [
    {
      "id": "saloon_patrons",
      "name": "Saloon Patrons",
      "bio": "A small group of locals huddled over drinks in the dim light. They are wary of strangers and maintain a watchful silence.",
      "aliases": [],
      "presence": "present",
      "notes": "watching player with cautious interest"
    }
  ],
  "actions": [
    "Order a drink to soothe your dusty throat.",
    "Scan the patrons for news of the road.",
    "Approach the bar to find Edda's information.",
    "Keep your hood low and watch the room."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

```json
{
  "arc": {
    "completed_threads": [],
    "goal_context": "",
    "last_thread_created_turn": 0,
    "resolution": null,
    "threads": [
      {
        "active": false,
        "added_turn": null,
        "id": "settle_the_debt",
        "last_updated_turn": null,
        "outcome": null,
        "progress": [],
        "resolution_state": null,
        "resolved_turn": null,
        "scope": "arc",
        "summary": "Settle the 500-credit debt with Caron.",
        "urgency": "normal",
        "urgency_set_turn": null
      },
      {
        "active": false,
        "added_turn": null,
        "id": "deliver_the_ledger",
        "last_updated_turn": null,
        "outcome": null,
        "progress": [],
        "resolution_state": null,
        "resolved_turn": null,
        "scope": "arc",
        "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
        "urgency": "normal",
        "urgency_set_turn": null
      },
      {
        "active": false,
        "added_turn": null,
        "id": "clear_the_road_toughs",
        "last_updated_turn": null,
        "outcome": null,
        "progress": [],
        "resolution_state": null,
        "resolved_turn": null,
        "scope": "arc",
        "summary": "Deal with the toughs blocking the inn entrance.",
        "urgency": "background",
        "urgency_set_turn": null
      }
    ],
    "visible_goal": "Clear your debts and deliver the ledger \u2014 two obligations binding you to Marrow's Crossing."
  },
  "compendium": {
    "npcs": {
      "caron": {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "bond": null,
        "fear": null,
        "leverage": null,
        "motivation": null,
        "name": "Caron",
        "notes": null,
        "presence": null,
        "title": "Old creditor"
      },
      "halden": {
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
        "bond": null,
        "fear": null,
        "leverage": null,
        "motivation": null,
        "name": "Halden",
        "notes": null,
        "presence": null,
        "title": "Merchant"
      },
      "innkeeper": {
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "bond": null,
        "fear": null,
        "leverage": null,
        "motivation": null,
        "name": "Edda",
        "notes": null,
        "presence": null,
        "title": "Innkeeper at the Crossed Keys"
      },
      "matthew_estrada": {
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
        "bond": null,
        "fear": null,
        "leverage": null,
        "motivation": null,
        "name": "Matthew Estrada",
        "notes": null,
        "presence": null,
        "title": "Traveler"
      },
      "tough_a": {
        "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
        "bond": null,
        "fear": null,
        "leverage": null,
        "motivation": null,
        "name": "Bald Tough",
        "notes": null,
        "presence": null,
        "title": "Road thug"
      },
      "tough_b": {
        "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
        "bond": null,
        "fear": null,
        "leverage": null,
        "motivation": null,
        "name": "Scarred Tough",
        "notes": null,
        "presence": null,
        "title": "Road thug"
      }
    }
  },
  "inventory": [
    {
      "aliases": [],
      "amount": 500,
      "id": "credits",
      "name": "Credits",
      "notes": "Common coin, accepted at any inn or stall on the merchant road."
    },
    {
      "aliases": [],
      "amount": 1,
      "id": "iron_dagger",
      "name": "Iron dagger",
      "notes": "Plain crossguard, edge worn from honing. Belt-carried."
    },
    {
      "aliases": [],
      "amount": 3,
      "id": "bandages",
      "name": "Linen bandages",
      "notes": "Three rolls. Field-grade \u2014 won't replace a healer."
    },
    {
      "aliases": [
        "cloak",
        "travel cloak"
      ],
      "amount": 1,
      "id": "traveler_cloak",
      "name": "Traveler's cloak",
      "notes": "Oiled wool, road-stained, hood deep enough to hide a face."
    },
    {
      "aliases": [],
      "amount": 1,
      "id": "brass_key",
      "name": "Brass key",
      "notes": "A small brass key Halden gave you with the ledger."
    }
  ],
  "location": {
    "description": "A market town built around the confluence of two rivers. Cobblestone streets,\ntimber-framed buildings, and the constant sound of water from the mills. The\ntown square has a stone well and a statue of the founder. Most shops are closing\nfor the evening.\n",
    "id": "marrows_crossing",
    "name": "Marrow's Crossing"
  },
  "meta": {
    "game_name": "eval",
    "model": "",
    "setting_pack": "eval-pack",
    "turn": 0
  },
  "pc": {
    "bio": "Mid-thirties, broad shoulders, careful with words. Took on a courier contract\nto clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and\na heavier obligation.\n",
    "conditions": [],
    "drive": "",
    "momentum": 0,
    "name": "Aren Voss",
    "stats": {
      "charisma": 3,
      "dexterity": 3,
      "strength": 3,
      "wits": 2
    },
    "tagline": "Reluctant courier on the merchant road"
  },
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
  "schema_version": 1
}
```


---

# TURN 2

**Input:** `I step up to the bar and ask for a glass of water and whatever news there is. The bartender is wiping a glass and eyeing me.`

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
{
  "intent_verb": "persuade",
  "intent": "The player seeks information from the bartender while ordering a drink.",
  "rolled": false,
  "total_ms": 2221.1,
  "tokens_in": 1278,
  "tokens_out": 68,
  "outcome_summary": "The player learns from Elara Vance that caravans are increasingly fleeing the crossing."
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "investigation"
  ],
  "scene_tagline": "Bad News at the Bar",
  "location_description": "The bar is made of scarred, heavy wood, and a chipped ceramic mug sits prominently on its surface.",
  "compendium_npc_update": [
    {
      "id": "elara_vance",
      "name": "Elara Vance",
      "title": "Bartender",
      "bio": "A woman with calloused hands and a sharp, discerning gaze. Her voice is raspy from years of breathing dust and shouting over tavern din.",
      "aliases": [],
      "presence": "present",
      "notes": "leaning in to whisper secrets"
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "ceramic_mug",
      "name": "ceramic mug",
      "notes": "chipped",
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
    "Pay Elara extra credits for more specific road news.",
    "Inquire if any specific caravans have gone missing lately.",
    "Scan the saloon patrons for anyone looking particularly nervous.",
    "Finish the water and head toward the Crossed Keys."
  ],
  "outcome_summary": "The player learns from Elara Vance that caravans are increasingly fleeing the crossing.",
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "deliver_the_ledger",
      "active": true,
      "urgency": "normal",
      "progress": "Arrived in Dustfall to find news of trouble",
      "progress_kind": "advancement"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "ceramic_mug",
      "name": "Ceramic mug",
      "notes": "chipped",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The bar is made of scarred, heavy wood, and a chipped ceramic mug sits prominently on its surface.",
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "tense_conversation",
    "investigation"
  ],
  "scene_tagline": "Bad News at the Bar",
  "compendium_npc_update": [
    {
      "id": "elara_vance",
      "name": "Elara Vance",
      "title": "Bartender",
      "bio": "A woman with calloused hands and a sharp, discerning gaze. Her voice is raspy from years of breathing dust and shouting over tavern din.",
      "aliases": [],
      "presence": "present",
      "notes": "leaning in to whisper secrets"
    }
  ],
  "actions": [
    "Pay Elara extra credits for more specific road news.",
    "Inquire if any specific caravans have gone missing lately.",
    "Scan the saloon patrons for anyone looking particularly nervous.",
    "Finish the water and head toward the Crossed Keys."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "completed_threads": {
      "added": [
        {
          "active": false,
          "id": "clear_the_road_toughs",
          "outcome": "The player has entered the town, bypassing the road blockade.",
          "progress": [],
          "resolution_state": "abandoned",
          "resolved_turn": 1,
          "scope": "arc",
          "summary": "Deal with the toughs blocking the inn entrance.",
          "urgency": "background"
        }
      ]
    },
    "threads": {
      "removed": [
        {
          "active": false,
          "added_turn": null,
          "id": "clear_the_road_toughs",
          "last_updated_turn": null,
          "outcome": null,
          "progress": [],
          "resolution_state": null,
          "resolved_turn": null,
          "scope": "arc",
          "summary": "Deal with the toughs blocking the inn entrance.",
          "urgency": "background",
          "urgency_set_turn": null
        }
      ],
      "changed": [
        {
          "from": {
            "active": false,
            "added_turn": null,
            "id": "settle_the_debt",
            "last_updated_turn": null,
            "outcome": null,
            "progress": [],
            "resolution_state": null,
            "resolved_turn": null,
            "scope": "arc",
            "summary": "Settle the 500-credit debt with Caron.",
            "urgency": "normal",
            "urgency_set_turn": null
          },
          "to": {
            "active": false,
            "id": "settle_the_debt",
            "progress": [],
            "scope": "arc",
            "summary": "Settle the 500-credit debt with Caron.",
            "urgency": "normal"
          }
        },
        {
          "from": {
            "active": false,
            "added_turn": null,
            "id": "deliver_the_ledger",
            "last_updated_turn": null,
            "outcome": null,
            "progress": [],
            "resolution_state": null,
            "resolved_turn": null,
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal",
            "urgency_set_turn": null
          },
          "to": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 1,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "saloon_patrons": {
        "from": null,
        "to": {
          "bio": "A small group of locals huddled over drinks in the dim light. They are wary of strangers and maintain a watchful silence.",
          "first_seen_turn": 0,
          "last_seen": {
            "location_id": "dustfall_saloon",
            "location_name": "Dustfall Saloon",
            "turn": 1
          },
          "name": "Saloon Patrons",
          "notes": "watching player with cautious interest",
          "presence": "present"
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "A market town built around the confluence of two rivers. Cobblestone streets,\ntimber-framed buildings, and the constant sound of water from the mills. The\ntown square has a stone well and a statue of the founder. Most shops are closing\nfor the evening.\n",
      "to": "A dim taproom filled with the scent of stale ale and unwashed wool. Patrons sit hunched over small tables in the shadows."
    },
    "id": {
      "from": "marrows_crossing",
      "to": "dustfall_saloon"
    },
    "name": {
      "from": "Marrow's Crossing",
      "to": "Dustfall Saloon"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "from": null,
      "to": [
        "saloon_patrons"
      ]
    },
    "consecutive_pressure_turns": {
      "from": null,
      "to": 1
    },
    "pending_gm_beat": {
      "from": null,
      "to": {
        "beat_expires_turn": 3,
        "surface_as": "npc_behavior",
        "type": "pressure"
      }
    },
    "recent_beats": {
      "from": null,
      "to": [
        {
          "surface_as": "npc_behavior",
          "turn": 1,
          "type": "pressure"
        }
      ]
    },
    "turn": {
      "from": 0,
      "to": 1
    }
  },
  "pc": {
    "actions": {
      "from": null,
      "to": [
        "Order a drink to soothe your dusty throat.",
        "Scan the patrons for news of the road.",
        "Approach the bar to find Edda's information.",
        "Keep your hood low and watch the room."
      ]
    },
    "conditions": {
      "added": [
        {
          "added_turn": 0,
          "description": "The dust from the merchant road has coated your throat, making it scratchy.",
          "id": "dusty_throat",
          "label": "Dusty Throat",
          "turns_remaining": 2
        }
      ]
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": null,
      "to": 0
    },
    "tagline": {
      "from": "Market town at dusk",
      "to": "A Quiet Arrival in Dustfall"
    },
    "tags": {
      "added": [
        "discovery",
        "tense_atmosphere"
      ],
      "removed": [
        "start",
        "peaceful"
      ]
    },
    "turn_entered": {
      "from": null,
      "to": 0
    }
  }
}
```


---

# TURN 3

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

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "threads": {
      "changed": [
        {
          "from": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 1,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 3,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Gathering local rumors about Harker's disappearance"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "elara_vance": {
        "from": null,
        "to": {
          "bio": "A woman with calloused hands and a sharp, discerning gaze. Her voice is raspy from years of breathing dust and shouting over tavern din.",
          "first_seen_turn": 1,
          "last_seen": {
            "location_id": "dustfall_saloon",
            "location_name": "Dustfall Saloon",
            "turn": 3
          },
          "name": "Elara Vance",
          "notes": "leaning closer, whispering nervously",
          "presence": "present",
          "title": "Bartender"
        }
      },
      "saloon_patrons": {
        "notes": {
          "from": "watching player with cautious interest",
          "to": null
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "ceramic_mug",
        "name": "Ceramic mug",
        "notes": "chipped"
      }
    ]
  },
  "location": {
    "description": {
      "from": "A dim taproom filled with the scent of stale ale and unwashed wool. Patrons sit hunched over small tables in the shadows.",
      "to": "The atmosphere in the saloon grows heavy as Elara's frantic wiping rhythm breaks the silence."
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "elara_vance"
      ],
      "removed": []
    },
    "consecutive_pressure_turns": {
      "from": 1,
      "to": 0
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 3,
        "to": 5
      },
      "surface_as": {
        "from": "npc_behavior",
        "to": "ambient"
      },
      "type": {
        "from": "pressure",
        "to": "revelation"
      }
    },
    "prior_history": {
      "from": null,
      "to": [
        "- [T2] The player learns from Elara Vance that caravans are increasingly fleeing the crossing.",
        "- [T3] Elara reveals that Old Man Harker's wagon was found empty near the river crossing, leaving behind his coin pouch."
      ]
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            2
          ],
          [
            "type",
            "complication"
          ]
        ],
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            3
          ],
          [
            "type",
            "revelation"
          ]
        ]
      ],
      "removed": []
    },
    "turn": {
      "from": 1,
      "to": 3
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Offer Elara extra credits for more specific details.",
        "Question the patrons in the corner about the wagon.",
        "Search the saloon for anyone looking too interested.",
        "Investigate the river crossing where the wagon was found."
      ],
      "removed": [
        "Order a drink to soothe your dusty throat.",
        "Scan the patrons for news of the road.",
        "Approach the bar to find Edda's information.",
        "Keep your hood low and watch the room."
      ]
    },
    "conditions": {
      "removed": [
        {
          "added_turn": 0,
          "description": "The dust from the merchant road has coated your throat, making it scratchy.",
          "id": "dusty_throat",
          "label": "Dusty Throat",
          "turns_remaining": 2
        }
      ]
    },
    "momentum": {
      "from": 0,
      "to": 2
    }
  },
  "scene": {
    "tagline": {
      "from": "A Quiet Arrival in Dustfall",
      "to": "Whispers of a Vanishing"
    },
    "tags": {
      "added": [
        "mystery",
        "tense_conversation"
      ],
      "removed": [
        "discovery",
        "tense_atmosphere"
      ]
    }
  }
}
```


---

# TURN 3

**Input:** `I lean on the bar and ask what happened to Old Man Harker. The bartender seems reluctant but starts talking.`

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
{
  "intent_verb": "persuade",
  "intent": "The player seeks information regarding the disappearance or status of Old Man Harker from Elara Vance.",
  "rolled": true,
  "total_ms": 2718.3,
  "tokens_in": 1356,
  "tokens_out": 93,
  "outcome_summary": "Elara reveals that Old Man Harker's wagon was found empty near the river crossing, leaving behind his coin pouch.",
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    11
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "raw_total": 11,
  "final_total": 12,
  "band": "crit_success",
  "momentum_before": 0,
  "momentum_after": 2,
  "momentum_delta": 2
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "mystery"
  ],
  "scene_tagline": "Whispers of a Vanishing",
  "location_description": "The atmosphere in the saloon grows heavy as Elara's frantic wiping rhythm breaks the silence.",
  "compendium_npc_update": [
    {
      "id": "elara_vance",
      "aliases": [],
      "notes": "leaning closer, whispering nervously"
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
      "id": "dusty_throat"
    }
  ]
}
```

### Storyteller

```json
{
  "actions": [
    "Offer Elara extra credits for more specific details.",
    "Question the patrons in the corner about the wagon.",
    "Investigate the river crossing where the wagon was found.",
    "Search the saloon for anyone looking too interested."
  ],
  "outcome_summary": "Elara reveals that Old Man Harker's wagon was found empty near the river crossing, leaving behind his coin pouch.",
  "gm_beat": {
    "type": "revelation",
    "surface_as": "ambient"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "deliver_the_ledger",
      "active": true,
      "urgency": "normal",
      "progress": "Gathering local rumors about Harker's disappearance",
      "progress_kind": "advancement"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The atmosphere in the saloon grows heavy as Elara's frantic wiping rhythm breaks the silence.",
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "dusty_throat"
    }
  ],
  "scene_tags": [
    "tense_conversation",
    "mystery"
  ],
  "scene_tagline": "Whispers of a Vanishing",
  "compendium_npc_update": [
    {
      "id": "elara_vance",
      "aliases": [],
      "notes": "leaning closer, whispering nervously"
    }
  ],
  "actions": [
    "Offer Elara extra credits for more specific details.",
    "Question the patrons in the corner about the wagon.",
    "Investigate the river crossing where the wagon was found.",
    "Search the saloon for anyone looking too interested."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "threads": {
      "changed": [
        {
          "from": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 3,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Gathering local rumors about Harker's disappearance"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 2,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "elara_vance": {
        "last_seen": {
          "turn": {
            "from": 3,
            "to": 2
          }
        },
        "notes": {
          "from": "leaning closer, whispering nervously",
          "to": "leaning in to whisper secrets"
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The atmosphere in the saloon grows heavy as Elara's frantic wiping rhythm breaks the silence.",
      "to": "The bar is made of scarred, heavy wood, and a chipped ceramic mug sits prominently on its surface."
    }
  },
  "meta": {
    "consecutive_pressure_turns": {
      "from": 0,
      "to": 2
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 5,
        "to": 4
      },
      "surface_as": {
        "from": "ambient",
        "to": "npc_behavior"
      },
      "type": {
        "from": "revelation",
        "to": "complication"
      }
    },
    "prior_history": {
      "added": [],
      "removed": [
        "- [T3] Elara reveals that Old Man Harker's wagon was found empty near the river crossing, leaving behind his coin pouch."
      ]
    },
    "recent_beats": {
      "added": [],
      "removed": [
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            3
          ],
          [
            "type",
            "revelation"
          ]
        ]
      ]
    },
    "turn": {
      "from": 3,
      "to": 2
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Scan the saloon patrons for anyone looking particularly nervous.",
        "Pay Elara extra credits for more specific road news.",
        "Finish the water and head toward the Crossed Keys.",
        "Inquire if any specific caravans have gone missing lately."
      ],
      "removed": [
        "Offer Elara extra credits for more specific details.",
        "Question the patrons in the corner about the wagon.",
        "Search the saloon for anyone looking too interested.",
        "Investigate the river crossing where the wagon was found."
      ]
    },
    "conditions": {
      "added": [
        {
          "added_turn": 0,
          "description": "The dust from the merchant road has coated your throat, making it scratchy.",
          "id": "dusty_throat",
          "label": "Dusty Throat",
          "turns_remaining": 1
        }
      ]
    },
    "momentum": {
      "from": 2,
      "to": 0
    }
  },
  "scene": {
    "tagline": {
      "from": "Whispers of a Vanishing",
      "to": "Bad News at the Bar"
    },
    "tags": {
      "added": [
        "investigation"
      ],
      "removed": [
        "mystery"
      ]
    }
  }
}
```


---

# TURN 4

**Input:** `I head over to the assay office to see if Harker filed any claims recently. I knock on the door and introduce myself.`

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
{
  "intent_verb": "persuade",
  "intent": "The player seeks information about Old Man Harker by visiting the assay office and introducing themselves.",
  "rolled": true,
  "total_ms": 2752.4,
  "tokens_in": 1358,
  "tokens_out": 93,
  "outcome_summary": "The player discovered a discarded ledger page with a familiar signature near the Assay Office entrance.",
  "skill": "charisma",
  "difficulty": "easy",
  "dice": [
    12
  ],
  "stat_mod": 1,
  "diff_mod": 1,
  "cond_mod": 0,
  "raw_total": 12,
  "final_total": 14,
  "band": "crit_success",
  "momentum_before": 2,
  "momentum_after": 3,
  "momentum_delta": 1
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "investigation",
    "discovery"
  ],
  "scene_tagline": "A Clue in the Dust",
  "location_change": {
    "id": "assay_office",
    "name": "Assay Office",
    "description": "A squat stone structure with heavy iron bars over its single window, resembling a small fortress."
  },
  "location_description": "The entrance features a thick oak door with a narrow viewing slit and a threshold partially buried in silt.",
  "compendium_npc_update": [
    {
      "id": "assay_clerk",
      "name": "Assay Clerk",
      "title": "Office Attendant",
      "bio": "A weary individual with bloodshot eyes peering through a viewing port. Speaks with a raspy, disinterested tone.",
      "aliases": [],
      "presence": "present",
      "notes": "peering through door slit"
    },
    {
      "id": "elara_vance",
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
  "inventory_add": [
    {
      "id": "ledger_page",
      "name": "ledger page",
      "notes": "A discarded scrap of parchment with a frantic signature.",
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
    "Show the signed ledger page to the clerk through the slit.",
    "Wait for sunset to confront the clerk about the signature.",
    "Search the silt around the threshold for more discarded documents.",
    "Confront the clerk about Harker's disappearance using the page."
  ],
  "outcome_summary": "The player discovered a discarded ledger page with a familiar signature near the Assay Office entrance.",
  "gm_beat": {
    "type": "revelation",
    "surface_as": "item"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "deliver_the_ledger",
      "active": true,
      "urgency": "normal",
      "progress": "Found a signed ledger page near Assay Office",
      "progress_kind": "advancement"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "ledger_page",
      "name": "Ledger page",
      "notes": "A discarded scrap of parchment with a frantic signature.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "assay_office",
    "name": "Assay Office",
    "description": "A squat stone structure with heavy iron bars over its single window, resembling a small fortress."
  },
  "location_description": "The entrance features a thick oak door with a narrow viewing slit and a threshold partially buried in silt.",
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "investigation",
    "discovery"
  ],
  "scene_tagline": "A Clue in the Dust",
  "compendium_npc_update": [
    {
      "id": "assay_clerk",
      "name": "Assay Clerk",
      "title": "Office Attendant",
      "bio": "A weary individual with bloodshot eyes peering through a viewing port. Speaks with a raspy, disinterested tone.",
      "aliases": [],
      "presence": "present",
      "notes": "peering through door slit"
    },
    {
      "id": "elara_vance",
      "aliases": [],
      "presence": "known"
    },
    {
      "id": "saloon_patrons",
      "aliases": [],
      "presence": "known"
    }
  ],
  "actions": [
    "Show the signed ledger page to the clerk through the slit.",
    "Wait for sunset to confront the clerk about the signature.",
    "Search the silt around the threshold for more discarded documents.",
    "Confront the clerk about Harker's disappearance using the page."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "threads": {
      "changed": [
        {
          "from": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 2,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 3,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Gathering local rumors about Harker's disappearance"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "elara_vance": {
        "last_seen": {
          "turn": {
            "from": 2,
            "to": 3
          }
        },
        "notes": {
          "from": "leaning in to whisper secrets",
          "to": "leaning closer, whispering nervously"
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The bar is made of scarred, heavy wood, and a chipped ceramic mug sits prominently on its surface.",
      "to": "The atmosphere in the saloon grows heavy as Elara's frantic wiping rhythm breaks the silence."
    }
  },
  "meta": {
    "consecutive_pressure_turns": {
      "from": 2,
      "to": 0
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 4,
        "to": 5
      },
      "surface_as": {
        "from": "npc_behavior",
        "to": "ambient"
      },
      "type": {
        "from": "complication",
        "to": "revelation"
      }
    },
    "prior_history": {
      "added": [
        "- [T3] Elara reveals that Old Man Harker's wagon was found empty near the river crossing, leaving behind his coin pouch."
      ],
      "removed": []
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            3
          ],
          [
            "type",
            "revelation"
          ]
        ]
      ],
      "removed": []
    },
    "turn": {
      "from": 2,
      "to": 3
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Offer Elara extra credits for more specific details.",
        "Question the patrons in the corner about the wagon.",
        "Search the saloon for anyone looking too interested.",
        "Investigate the river crossing where the wagon was found."
      ],
      "removed": [
        "Scan the saloon patrons for anyone looking particularly nervous.",
        "Pay Elara extra credits for more specific road news.",
        "Finish the water and head toward the Crossed Keys.",
        "Inquire if any specific caravans have gone missing lately."
      ]
    },
    "conditions": {
      "removed": [
        {
          "added_turn": 0,
          "description": "The dust from the merchant road has coated your throat, making it scratchy.",
          "id": "dusty_throat",
          "label": "Dusty Throat",
          "turns_remaining": 1
        }
      ]
    },
    "momentum": {
      "from": 0,
      "to": 2
    }
  },
  "scene": {
    "tagline": {
      "from": "Bad News at the Bar",
      "to": "Whispers of a Vanishing"
    },
    "tags": {
      "added": [
        "mystery"
      ],
      "removed": [
        "investigation"
      ]
    }
  }
}
```


---

# TURN 5

**Input:** `I walk to the sheriff's office and ask if he's filed a missing person report for Harker. I want to see if the law is involved.`

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
{
  "intent_verb": "persuade",
  "intent": "The player wants to inquire at the sheriff's office regarding whether a missing person report has been filed for Harker to determine if law enforcement is investigating his disappearance.",
  "rolled": true,
  "total_ms": 2964.3,
  "tokens_in": 1372,
  "tokens_out": 106,
  "outcome_summary": "Silas Thorne informs the player that no official report has been filed for Harker's disappearance.",
  "skill": "charisma",
  "difficulty": "easy",
  "dice": [
    1
  ],
  "stat_mod": 1,
  "diff_mod": 1,
  "cond_mod": 0,
  "raw_total": 1,
  "final_total": 3,
  "band": "fail",
  "momentum_before": 3,
  "momentum_after": 2,
  "momentum_delta": -1
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "investigation",
    "tense_conversation"
  ],
  "scene_tagline": "No Report for Harker",
  "location_change": {
    "id": "sheriffs_office",
    "name": "Sheriff's Office",
    "description": "An imposing timber and stone structure located near the town square, centered around a high wooden desk."
  },
  "compendium_npc_update": [
    {
      "id": "silas_thorne",
      "name": "Silas Thorne",
      "title": "Sheriff's Officer",
      "bio": "A stern-faced veteran with eyes as hard and unimpressed as his demeanor. Speaks with a voice like grinding gravel and maintains a no-nonsense, bureaucratic attitude.",
      "aliases": [],
      "presence": "present",
      "notes": "leaning over desk, dismissive of inquiry"
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
    "Press Silas Thorne for any recent suspicious traveler reports.",
    "Show him the signed ledger page found near the assay office.",
    "Search the town square for witnesses to Harker's last known location.",
    "Leave the office to find Caron and discuss your debts."
  ],
  "outcome_summary": "Silas Thorne informs the player that no official report has been filed for Harker's disappearance.",
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "deliver_the_ledger",
      "active": true,
      "urgency": "normal",
      "progress": "Inquired with law enforcement regarding Harker",
      "progress_kind": "shift"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "sheriffs_office",
    "name": "Sheriff's Office",
    "description": "An imposing timber and stone structure located near the town square, centered around a high wooden desk."
  },
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "investigation",
    "tense_conversation"
  ],
  "scene_tagline": "No Report for Harker",
  "compendium_npc_update": [
    {
      "id": "silas_thorne",
      "name": "Silas Thorne",
      "title": "Sheriff's Officer",
      "bio": "A stern-faced veteran with eyes as hard and unimpressed as his demeanor. Speaks with a voice like grinding gravel and maintains a no-nonsense, bureaucratic attitude.",
      "aliases": [],
      "presence": "present",
      "notes": "leaning over desk, dismissive of inquiry"
    }
  ],
  "actions": [
    "Press Silas Thorne for any recent suspicious traveler reports.",
    "Show him the signed ledger page found near the assay office.",
    "Search the town square for witnesses to Harker's last known location.",
    "Leave the office to find Caron and discuss your debts."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "threads": {
      "changed": [
        {
          "from": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 3,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Gathering local rumors about Harker's disappearance"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 4,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Gathering local rumors about Harker's disappearance"
              },
              {
                "kind": "advancement",
                "text": "Found a signed ledger page near Assay Office"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "assay_clerk": {
        "from": null,
        "to": {
          "bio": "A weary individual with bloodshot eyes peering through a viewing port. Speaks with a raspy, disinterested tone.",
          "first_seen_turn": 3,
          "last_seen": {
            "location_id": "assay_office",
            "location_name": "Assay Office",
            "turn": 4
          },
          "name": "Assay Clerk",
          "notes": "peering through door slit",
          "presence": "present",
          "title": "Office Attendant"
        }
      },
      "elara_vance": {
        "last_seen": {
          "location_id": {
            "from": "dustfall_saloon",
            "to": "assay_office"
          },
          "location_name": {
            "from": "Dustfall Saloon",
            "to": "Assay Office"
          },
          "turn": {
            "from": 3,
            "to": 4
          }
        },
        "notes": {
          "from": "leaning closer, whispering nervously",
          "to": null
        },
        "presence": {
          "from": "present",
          "to": "known"
        }
      },
      "saloon_patrons": {
        "last_seen": {
          "location_id": {
            "from": "dustfall_saloon",
            "to": "assay_office"
          },
          "location_name": {
            "from": "Dustfall Saloon",
            "to": "Assay Office"
          },
          "turn": {
            "from": 1,
            "to": 4
          }
        },
        "presence": {
          "from": "present",
          "to": "known"
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "ledger_page",
        "name": "Ledger page",
        "notes": "A discarded scrap of parchment with a frantic signature."
      }
    ]
  },
  "location": {
    "description": {
      "from": "The atmosphere in the saloon grows heavy as Elara's frantic wiping rhythm breaks the silence.",
      "to": "A squat stone structure with heavy iron bars over its single window, resembling a small fortress."
    },
    "id": {
      "from": "dustfall_saloon",
      "to": "assay_office"
    },
    "name": {
      "from": "Dustfall Saloon",
      "to": "Assay Office"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "assay_clerk"
      ],
      "removed": []
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 5,
        "to": 6
      },
      "surface_as": {
        "from": "ambient",
        "to": "item"
      }
    },
    "prior_history": {
      "added": [
        "- [T4] The player discovered a discarded ledger page with a familiar signature near the Assay Office entrance."
      ],
      "removed": []
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            "item"
          ],
          [
            "turn",
            4
          ],
          [
            "type",
            "revelation"
          ]
        ]
      ],
      "removed": []
    },
    "turn": {
      "from": 3,
      "to": 4
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Show the signed ledger page to the clerk through the slit.",
        "Wait for sunset to confront the clerk about the signature.",
        "Confront the clerk about Harker's disappearance using the page.",
        "Search the silt around the threshold for more discarded documents."
      ],
      "removed": [
        "Offer Elara extra credits for more specific details.",
        "Question the patrons in the corner about the wagon.",
        "Search the saloon for anyone looking too interested.",
        "Investigate the river crossing where the wagon was found."
      ]
    },
    "momentum": {
      "from": 2,
      "to": 3
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 0,
      "to": 3
    },
    "tagline": {
      "from": "Whispers of a Vanishing",
      "to": "A Clue in the Dust"
    },
    "tags": {
      "added": [
        "discovery",
        "investigation"
      ],
      "removed": [
        "mystery",
        "tense_conversation"
      ]
    },
    "turn_entered": {
      "from": 0,
      "to": 3
    }
  }
}
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

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "last_thread_created_turn": {
      "from": 0,
      "to": 5
    },
    "threads": {
      "added": [
        {
          "active": true,
          "id": "investigate_harker_disappearance",
          "last_updated_turn": 7,
          "progress": [
            {
              "kind": "setback",
              "text": "Officer Thorne denies any official missing person report"
            },
            {
              "kind": "advancement",
              "text": "Found map of Red Canyon cliffs"
            }
          ],
          "scope": "arc",
          "summary": "Investigate the mysterious disappearance of Old Man Harker.",
          "urgency": "normal"
        }
      ],
      "changed": [
        {
          "from": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 4,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Gathering local rumors about Harker's disappearance"
              },
              {
                "kind": "advancement",
                "text": "Found a signed ledger page near Assay Office"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 5,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Learned Harker's wagon was found empty"
              },
              {
                "kind": "advancement",
                "text": "Found signed ledger page near Assay Office"
              },
              {
                "kind": "advancement",
                "text": "Confirmed no missing person report filed"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "assay_clerk": {
        "notes": {
          "from": "peering through door slit",
          "to": null
        },
        "presence": {
          "from": "present",
          "to": "known"
        }
      },
      "silas_thorne": {
        "from": null,
        "to": {
          "bio": "A stern-faced veteran with eyes as hard and unimpressed as his demeanor. Speaks with a voice like grinding gravel and maintains a no-nonsense, bureaucratic attitude.",
          "first_seen_turn": 4,
          "last_seen": {
            "location_id": "sheriffs_office",
            "location_name": "Sheriff's Office",
            "turn": 7
          },
          "name": "Silas Thorne",
          "notes": "rising from chair with cold command",
          "presence": "present",
          "title": "Sheriff's Officer"
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "hand_drawn_map",
        "name": "Hand-drawn map",
        "notes": "A thick parchment with charcoal markings concentrated near the Red Canyon cliffs."
      }
    ]
  },
  "location": {
    "description": {
      "from": "A squat stone structure with heavy iron bars over its single window, resembling a small fortress.",
      "to": "The desk is cluttered with stacks of tax receipts and various bureaucratic tools, now disturbed by your theft."
    },
    "id": {
      "from": "assay_office",
      "to": "sheriffs_office"
    },
    "name": {
      "from": "Assay Office",
      "to": "Sheriff's Office"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "silas_thorne"
      ],
      "removed": []
    },
    "consecutive_pressure_turns": {
      "from": 0,
      "to": 3
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 6,
        "to": 9
      },
      "surface_as": {
        "from": "item",
        "to": "npc_behavior"
      },
      "type": {
        "from": "revelation",
        "to": "escalation"
      }
    },
    "prior_history": {
      "added": [
        "- [T5] Silas Thorne informs the player that no official report has been filed for Harker's disappearance.",
        "- [T7] The player successfully stole a map of Red Canyon from Thorne's desk but was caught in the act.",
        "- [T6] Silas Thorne rebuffs the attempt to obtain a key and threatens the player with arrest for harassment."
      ],
      "removed": []
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            7
          ],
          [
            "type",
            "escalation"
          ]
        ],
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            6
          ],
          [
            "type",
            "pressure"
          ]
        ],
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            5
          ],
          [
            "type",
            "complication"
          ]
        ]
      ],
      "removed": [
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            1
          ],
          [
            "type",
            "pressure"
          ]
        ],
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            2
          ],
          [
            "type",
            "complication"
          ]
        ]
      ]
    },
    "turn": {
      "from": 4,
      "to": 7
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Grab the tin box and bolt toward the office exit.",
        "Stand your ground and claim you were searching for a quill.",
        "Drop the dagger and apologize profusely to de-escalate Thorne's anger.",
        "Conceal the map quickly and feign accidental contact with the desk."
      ],
      "removed": [
        "Show the signed ledger page to the clerk through the slit.",
        "Wait for sunset to confront the clerk about the signature.",
        "Confront the clerk about Harker's disappearance using the page.",
        "Search the silt around the threshold for more discarded documents."
      ]
    },
    "momentum": {
      "from": 3,
      "to": 2
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 3,
      "to": 4
    },
    "tagline": {
      "from": "A Clue in the Dust",
      "to": "Caught Red-Handed"
    },
    "tags": {
      "added": [
        "tense_interaction",
        "stealth_fail"
      ],
      "removed": [
        "investigation"
      ]
    },
    "turn_entered": {
      "from": 3,
      "to": 4
    }
  }
}
```


---

# TURN 6

**Input:** `The sheriff gives me Harker's cabin key. I walk to the edge of town and let myself in. The place is dusty and cold.`

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
{
  "intent_verb": "persuade",
  "intent": "The player attempts to obtain a key from Silas Thorne and then enter Harker's cabin.",
  "rolled": false,
  "total_ms": 3272.7,
  "tokens_in": 1372,
  "tokens_out": 122,
  "outcome_summary": "Silas Thorne rebuffs the attempt to obtain a key and threatens the player with arrest for harassment."
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "confrontation"
  ],
  "scene_tagline": "A Warning from the Desk",
  "location_description": "The air in the office feels heavy and stagnant, thick with the scent of old parchment and drying ink.",
  "compendium_npc_update": [
    {
      "id": "silas_thorne",
      "aliases": [],
      "notes": "leaning forward with a dangerous growl"
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
      "id": "rattled",
      "label": "Rattled",
      "description": "The officer's sudden aggression and threat has left you feeling unsettled.",
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
    "Apologize profusely to de-escalate Thorne's immediate hostility.",
    "Demand to know why no report was filed for Harker.",
    "Search the office quietly while Thorne is distracted by paperwork.",
    "Leave the office and seek information from other town officials."
  ],
  "outcome_summary": "Silas Thorne rebuffs the attempt to obtain a key and threatens the player with arrest for harassment.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "ambient"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "Officer Thorne denies any official missing person report",
      "progress_kind": "setback"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The air in the office feels heavy and stagnant, thick with the scent of old parchment and drying ink.",
  "pc_condition_add": [
    {
      "id": "rattled",
      "label": "Rattled",
      "description": "The officer's sudden aggression and threat has left you feeling unsettled.",
      "turns_remaining": 3
    }
  ],
  "pc_condition_remove": [],
  "scene_tags": [
    "tense_conversation",
    "confrontation"
  ],
  "scene_tagline": "A Warning from the Desk",
  "compendium_npc_update": [
    {
      "id": "silas_thorne",
      "aliases": [],
      "notes": "leaning forward with a dangerous growl"
    }
  ],
  "actions": [
    "Apologize profusely to de-escalate Thorne's immediate hostility.",
    "Demand to know why no report was filed for Harker.",
    "Search the office quietly while Thorne is distracted by paperwork.",
    "Leave the office and seek information from other town officials."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "completed_threads": {
      "changed": [
        {
          "from": {
            "active": false,
            "id": "clear_the_road_toughs",
            "outcome": "The player has entered the town, bypassing the road blockade.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 1,
            "scope": "arc",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "urgency": "background"
          },
          "to": {
            "active": false,
            "added_turn": null,
            "id": "clear_the_road_toughs",
            "last_updated_turn": null,
            "outcome": "The player has entered the town, bypassing the road blockade.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 1,
            "scope": "arc",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "urgency": "background",
            "urgency_set_turn": null
          }
        }
      ]
    },
    "threads": {
      "changed": [
        {
          "from": {
            "active": false,
            "id": "settle_the_debt",
            "progress": [],
            "scope": "arc",
            "summary": "Settle the 500-credit debt with Caron.",
            "urgency": "normal"
          },
          "to": {
            "active": false,
            "added_turn": null,
            "id": "settle_the_debt",
            "last_updated_turn": null,
            "outcome": null,
            "progress": [],
            "resolution_state": null,
            "resolved_turn": null,
            "scope": "arc",
            "summary": "Settle the 500-credit debt with Caron.",
            "urgency": "normal",
            "urgency_set_turn": null
          }
        },
        {
          "from": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 5,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Learned Harker's wagon was found empty"
              },
              {
                "kind": "advancement",
                "text": "Found signed ledger page near Assay Office"
              },
              {
                "kind": "advancement",
                "text": "Confirmed no missing person report filed"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "added_turn": null,
            "id": "deliver_the_ledger",
            "last_updated_turn": 5,
            "outcome": null,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Learned Harker's wagon was found empty"
              },
              {
                "kind": "advancement",
                "text": "Found signed ledger page near Assay Office"
              },
              {
                "kind": "advancement",
                "text": "Confirmed no missing person report filed"
              }
            ],
            "resolution_state": null,
            "resolved_turn": null,
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal",
            "urgency_set_turn": null
          }
        },
        {
          "from": {
            "active": true,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 7,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              },
              {
                "kind": "advancement",
                "text": "Found map of Red Canyon cliffs"
              }
            ],
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "added_turn": null,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": null,
            "outcome": null,
            "progress": [],
            "resolution_state": null,
            "resolved_turn": null,
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal",
            "urgency_set_turn": null
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "silas_thorne": {
        "last_seen": {
          "turn": {
            "from": 7,
            "to": 5
          }
        },
        "notes": {
          "from": "rising from chair with cold command",
          "to": "leaning over desk, dismissive of inquiry"
        }
      }
    }
  },
  "inventory": {
    "removed": [
      {
        "amount": 1,
        "id": "hand_drawn_map",
        "name": "Hand-drawn map",
        "notes": "A thick parchment with charcoal markings concentrated near the Red Canyon cliffs."
      }
    ]
  },
  "location": {
    "description": {
      "from": "The desk is cluttered with stacks of tax receipts and various bureaucratic tools, now disturbed by your theft.",
      "to": "An imposing timber and stone structure located near the town square, centered around a high wooden desk."
    }
  },
  "meta": {
    "consecutive_pressure_turns": {
      "from": 3,
      "to": 1
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 9,
        "to": 7
      },
      "type": {
        "from": "escalation",
        "to": "complication"
      }
    },
    "prior_history": {
      "added": [],
      "removed": [
        "- [T7] The player successfully stole a map of Red Canyon from Thorne's desk but was caught in the act.",
        "- [T6] Silas Thorne rebuffs the attempt to obtain a key and threatens the player with arrest for harassment."
      ]
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            1
          ],
          [
            "type",
            "pressure"
          ]
        ],
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            2
          ],
          [
            "type",
            "complication"
          ]
        ]
      ],
      "removed": [
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            7
          ],
          [
            "type",
            "escalation"
          ]
        ],
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            6
          ],
          [
            "type",
            "pressure"
          ]
        ]
      ]
    },
    "turn": {
      "from": 7,
      "to": 5
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Show him the signed ledger page found near the assay office.",
        "Leave the office to find Caron and discuss your debts.",
        "Press Silas Thorne for any recent suspicious traveler reports.",
        "Search the town square for witnesses to Harker's last known location."
      ],
      "removed": [
        "Grab the tin box and bolt toward the office exit.",
        "Stand your ground and claim you were searching for a quill.",
        "Drop the dagger and apologize profusely to de-escalate Thorne's anger.",
        "Conceal the map quickly and feign accidental contact with the desk."
      ]
    }
  },
  "scene": {
    "tagline": {
      "from": "Caught Red-Handed",
      "to": "No Report for Harker"
    },
    "tags": {
      "added": [
        "investigation",
        "tense_conversation"
      ],
      "removed": [
        "discovery",
        "tense_interaction",
        "stealth_fail"
      ]
    }
  }
}
```


---

# TURN 7

**Input:** `I look through Harker's desk and find a locked tin box. I pry it open with my knife and find a map with markings near Red Canyon.`

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
{
  "intent_verb": "sneak",
  "intent": "The player attempts to surreptitiously search the desk and force open a locked container while being watched by the Sheriff's Officer.",
  "rolled": true,
  "total_ms": 2965.8,
  "tokens_in": 1377,
  "tokens_out": 107,
  "outcome_summary": "The player successfully stole a map of Red Canyon from Thorne's desk but was caught in the act.",
  "skill": "dexterity",
  "difficulty": "hard",
  "dice": [
    10
  ],
  "stat_mod": 1,
  "diff_mod": -1,
  "cond_mod": 0,
  "raw_total": 10,
  "final_total": 10,
  "band": "success",
  "momentum_before": 1,
  "momentum_after": 2,
  "momentum_delta": 1
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "tense_interaction",
    "stealth_fail",
    "discovery"
  ],
  "scene_tagline": "Caught Red-Handed",
  "location_description": "The desk is cluttered with stacks of tax receipts and various bureaucratic tools, now disturbed by your theft.",
  "compendium_npc_update": [
    {
      "id": "silas_thorne",
      "aliases": [],
      "presence": "present",
      "notes": "rising from chair with cold command"
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "hand_drawn_map",
      "name": "Hand-drawn map",
      "notes": "A thick parchment with charcoal markings concentrated near the Red Canyon cliffs.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "rattled"
    }
  ]
}
```

### Storyteller

```json
{
  "actions": [
    "Conceal the map quickly and feign accidental contact with the desk.",
    "Stand your ground and claim you were searching for a quill.",
    "Grab the tin box and bolt toward the office exit.",
    "Drop the dagger and apologize profusely to de-escalate Thorne's anger."
  ],
  "outcome_summary": "The player successfully stole a map of Red Canyon from Thorne's desk but was caught in the act.",
  "gm_beat": {
    "type": "escalation",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "Found map of Red Canyon cliffs",
      "progress_kind": "advancement"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "hand_drawn_map",
      "name": "Hand-drawn map",
      "notes": "A thick parchment with charcoal markings concentrated near the Red Canyon cliffs.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The desk is cluttered with stacks of tax receipts and various bureaucratic tools, now disturbed by your theft.",
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "rattled"
    }
  ],
  "scene_tags": [
    "tense_interaction",
    "stealth_fail",
    "discovery"
  ],
  "scene_tagline": "Caught Red-Handed",
  "compendium_npc_update": [
    {
      "id": "silas_thorne",
      "aliases": [],
      "presence": "present",
      "notes": "rising from chair with cold command"
    }
  ],
  "actions": [
    "Conceal the map quickly and feign accidental contact with the desk.",
    "Stand your ground and claim you were searching for a quill.",
    "Grab the tin box and bolt toward the office exit.",
    "Drop the dagger and apologize profusely to de-escalate Thorne's anger."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "completed_threads": {
      "changed": [
        {
          "from": {
            "active": false,
            "added_turn": null,
            "id": "clear_the_road_toughs",
            "last_updated_turn": null,
            "outcome": "The player has entered the town, bypassing the road blockade.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 1,
            "scope": "arc",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "urgency": "background",
            "urgency_set_turn": null
          },
          "to": {
            "active": false,
            "id": "clear_the_road_toughs",
            "outcome": "The player has entered the town, bypassing the road blockade.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 1,
            "scope": "arc",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "urgency": "background"
          }
        }
      ]
    },
    "threads": {
      "changed": [
        {
          "from": {
            "active": false,
            "added_turn": null,
            "id": "settle_the_debt",
            "last_updated_turn": null,
            "outcome": null,
            "progress": [],
            "resolution_state": null,
            "resolved_turn": null,
            "scope": "arc",
            "summary": "Settle the 500-credit debt with Caron.",
            "urgency": "normal",
            "urgency_set_turn": null
          },
          "to": {
            "active": false,
            "id": "settle_the_debt",
            "progress": [],
            "scope": "arc",
            "summary": "Settle the 500-credit debt with Caron.",
            "urgency": "normal"
          }
        },
        {
          "from": {
            "active": true,
            "added_turn": null,
            "id": "deliver_the_ledger",
            "last_updated_turn": 5,
            "outcome": null,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Learned Harker's wagon was found empty"
              },
              {
                "kind": "advancement",
                "text": "Found signed ledger page near Assay Office"
              },
              {
                "kind": "advancement",
                "text": "Confirmed no missing person report filed"
              }
            ],
            "resolution_state": null,
            "resolved_turn": null,
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal",
            "urgency_set_turn": null
          },
          "to": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 5,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Learned Harker's wagon was found empty"
              },
              {
                "kind": "advancement",
                "text": "Found signed ledger page near Assay Office"
              },
              {
                "kind": "advancement",
                "text": "Confirmed no missing person report filed"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          }
        },
        {
          "from": {
            "active": true,
            "added_turn": null,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": null,
            "outcome": null,
            "progress": [],
            "resolution_state": null,
            "resolved_turn": null,
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal",
            "urgency_set_turn": null
          },
          "to": {
            "active": true,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 6,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              }
            ],
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "silas_thorne": {
        "last_seen": {
          "turn": {
            "from": 5,
            "to": 6
          }
        },
        "notes": {
          "from": "leaning over desk, dismissive of inquiry",
          "to": "leaning forward with a dangerous growl"
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "An imposing timber and stone structure located near the town square, centered around a high wooden desk.",
      "to": "The air in the office feels heavy and stagnant, thick with the scent of old parchment and drying ink."
    }
  },
  "meta": {
    "consecutive_pressure_turns": {
      "from": 1,
      "to": 2
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 7,
        "to": 8
      },
      "surface_as": {
        "from": "npc_behavior",
        "to": "ambient"
      },
      "type": {
        "from": "complication",
        "to": "pressure"
      }
    },
    "prior_history": {
      "added": [
        "- [T6] Silas Thorne rebuffs the attempt to obtain a key and threatens the player with arrest for harassment."
      ],
      "removed": []
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            6
          ],
          [
            "type",
            "pressure"
          ]
        ]
      ],
      "removed": [
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            1
          ],
          [
            "type",
            "pressure"
          ]
        ]
      ]
    },
    "turn": {
      "from": 5,
      "to": 6
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Demand to know why no report was filed for Harker.",
        "Apologize profusely to de-escalate Thorne's immediate hostility.",
        "Leave the office and seek information from other town officials.",
        "Search the office quietly while Thorne is distracted by paperwork."
      ],
      "removed": [
        "Show him the signed ledger page found near the assay office.",
        "Leave the office to find Caron and discuss your debts.",
        "Press Silas Thorne for any recent suspicious traveler reports.",
        "Search the town square for witnesses to Harker's last known location."
      ]
    },
    "conditions": {
      "added": [
        {
          "added_turn": 5,
          "description": "The officer's sudden aggression and threat has left you feeling unsettled.",
          "id": "rattled",
          "label": "Rattled",
          "turns_remaining": 3
        }
      ]
    },
    "momentum": {
      "from": 2,
      "to": 1
    }
  },
  "scene": {
    "tagline": {
      "from": "No Report for Harker",
      "to": "A Warning from the Desk"
    },
    "tags": {
      "added": [
        "confrontation"
      ],
      "removed": [
        "investigation"
      ]
    }
  }
}
```


---

# TURN 8

**Input:** `I head back to the general store to buy supplies — dried meat, water canteen, rope. The clerk rings me up.`

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
{
  "intent_verb": "transition",
  "intent": "The player attempts to leave the Sheriff's Office and purchase survival supplies at a general store.",
  "rolled": false,
  "total_ms": 2489.3,
  "tokens_in": 1365,
  "tokens_out": 80,
  "outcome_summary": "The player enters the general store to buy supplies but is immediately targeted by two aggressive men."
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "tense_confrontation",
    "suspense"
  ],
  "scene_tagline": "Predators in the Market District",
  "location_change": {
    "id": "general_store",
    "name": "General Store",
    "description": "A cramped shop filled with the scent of cured leather and dust, featuring a counter stacked with iron pots."
  },
  "location_description": "The air is thick with the smell of dried goods and old dust; a small bell hangs above the entrance.",
  "compendium_npc_update": [
    {
      "id": "silas_thorne",
      "aliases": [],
      "presence": "known"
    },
    {
      "id": "assay_clerk",
      "aliases": [],
      "presence": "present",
      "notes": "watching with wide-eyed alarm"
    },
    {
      "id": "tough_a",
      "aliases": [],
      "presence": "present",
      "notes": "scanning you with predatory focus"
    },
    {
      "id": "tough_b",
      "aliases": [],
      "presence": "present",
      "notes": "scanning you with predatory focus"
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
      "notes": "",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "water_canteen",
      "name": "Water canteen",
      "notes": "",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "hempen_rope",
      "name": "Hempen rope",
      "notes": "",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 60
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [
    {
      "id": "threatened",
      "label": "Threatened",
      "description": "Two aggressive men are staring you down with predatory focus.",
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
    "Pay the clerk quickly and exit through the side door.",
    "Draw your iron dagger and face the thugs directly.",
    "Attempt to de-escalate by offering credits to the men.",
    "Grab the heavy iron pot to use as a weapon."
  ],
  "outcome_summary": "The player enters the general store to buy supplies but is immediately targeted by two aggressive men.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [],
  "thread_add": {
    "id": "street_confrontation",
    "summary": "Avoid or resolve sudden roadside aggression",
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
      "progress": "Arrived in Dustfall toward destination",
      "progress_kind": "advancement"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "dried_meat",
      "name": "Dried meat",
      "notes": "",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "water_canteen",
      "name": "Water canteen",
      "notes": "",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "hempen_rope",
      "name": "Hempen rope",
      "notes": "",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 60
    }
  ],
  "inventory_update": [],
  "location_change": {
    "id": "general_store",
    "name": "General Store",
    "description": "A cramped shop filled with the scent of cured leather and dust, featuring a counter stacked with iron pots."
  },
  "location_description": "The air is thick with the smell of dried goods and old dust; a small bell hangs above the entrance.",
  "pc_condition_add": [
    {
      "id": "threatened",
      "label": "Threatened",
      "description": "Two aggressive men are staring you down with predatory focus.",
      "turns_remaining": 3
    }
  ],
  "pc_condition_remove": [],
  "scene_tags": [
    "tense_confrontation",
    "suspense"
  ],
  "scene_tagline": "Predators in the Market District",
  "compendium_npc_update": [
    {
      "id": "silas_thorne",
      "aliases": [],
      "presence": "known"
    },
    {
      "id": "assay_clerk",
      "aliases": [],
      "presence": "present",
      "notes": "watching with wide-eyed alarm"
    },
    {
      "id": "tough_a",
      "aliases": [],
      "presence": "present",
      "notes": "scanning you with predatory focus"
    },
    {
      "id": "tough_b",
      "aliases": [],
      "presence": "present",
      "notes": "scanning you with predatory focus"
    }
  ],
  "actions": [
    "Pay the clerk quickly and exit through the side door.",
    "Draw your iron dagger and face the thugs directly.",
    "Attempt to de-escalate by offering credits to the men.",
    "Grab the heavy iron pot to use as a weapon."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "threads": {
      "changed": [
        {
          "from": {
            "active": true,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 6,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              }
            ],
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 7,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              },
              {
                "kind": "advancement",
                "text": "Found map of Red Canyon cliffs"
              }
            ],
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "silas_thorne": {
        "last_seen": {
          "turn": {
            "from": 6,
            "to": 7
          }
        },
        "notes": {
          "from": "leaning forward with a dangerous growl",
          "to": "rising from chair with cold command"
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "hand_drawn_map",
        "name": "Hand-drawn map",
        "notes": "A thick parchment with charcoal markings concentrated near the Red Canyon cliffs."
      }
    ]
  },
  "location": {
    "description": {
      "from": "The air in the office feels heavy and stagnant, thick with the scent of old parchment and drying ink.",
      "to": "The desk is cluttered with stacks of tax receipts and various bureaucratic tools, now disturbed by your theft."
    }
  },
  "meta": {
    "consecutive_pressure_turns": {
      "from": 2,
      "to": 3
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 8,
        "to": 9
      },
      "surface_as": {
        "from": "ambient",
        "to": "npc_behavior"
      },
      "type": {
        "from": "pressure",
        "to": "escalation"
      }
    },
    "prior_history": {
      "added": [
        "- [T7] The player successfully stole a map of Red Canyon from Thorne's desk but was caught in the act."
      ],
      "removed": []
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            7
          ],
          [
            "type",
            "escalation"
          ]
        ]
      ],
      "removed": [
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            2
          ],
          [
            "type",
            "complication"
          ]
        ]
      ]
    },
    "turn": {
      "from": 6,
      "to": 7
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Grab the tin box and bolt toward the office exit.",
        "Stand your ground and claim you were searching for a quill.",
        "Drop the dagger and apologize profusely to de-escalate Thorne's anger.",
        "Conceal the map quickly and feign accidental contact with the desk."
      ],
      "removed": [
        "Demand to know why no report was filed for Harker.",
        "Apologize profusely to de-escalate Thorne's immediate hostility.",
        "Leave the office and seek information from other town officials.",
        "Search the office quietly while Thorne is distracted by paperwork."
      ]
    },
    "conditions": {
      "removed": [
        {
          "added_turn": 5,
          "description": "The officer's sudden aggression and threat has left you feeling unsettled.",
          "id": "rattled",
          "label": "Rattled",
          "turns_remaining": 3
        }
      ]
    },
    "momentum": {
      "from": 1,
      "to": 2
    }
  },
  "scene": {
    "tagline": {
      "from": "A Warning from the Desk",
      "to": "Caught Red-Handed"
    },
    "tags": {
      "added": [
        "discovery",
        "tense_interaction",
        "stealth_fail"
      ],
      "removed": [
        "confrontation",
        "tense_conversation"
      ]
    }
  }
}
```


---

# TURN 9

**Input:** `I saddle up and ride out to Red Canyon. The trail is rough and the sun is starting to set. I keep an eye on the canyon walls.`

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
{
  "intent_verb": "escape",
  "intent": "The player attempts to leave the general store and travel toward Red Canyon while remaining vigilant of their surroundings.",
  "rolled": false,
  "total_ms": 3310.3,
  "tokens_in": 1429,
  "tokens_out": 126,
  "outcome_summary": "The player escaped the thugs in the market and reached the base of the Red Canyon cliffs."
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "escape",
    "tense",
    "pursuit",
    "discovery"
  ],
  "scene_tagline": "Escape to the Red Canyon",
  "location_change": {
    "id": "red_canyon_cliffs",
    "name": "Red Canyon Cliffs",
    "description": "Jagged canyon walls loom overhead like teeth against a bruised purple sky, with long shadows stretching across an uneven trail."
  },
  "location_description": "The terrain is uneven and rocky, filled with darkening crevices and looming cliffs under a twilight sky.",
  "compendium_npc_update": [
    {
      "id": "assay_clerk",
      "aliases": [],
      "presence": "known"
    },
    {
      "id": "tough_a",
      "aliases": [],
      "presence": "known"
    },
    {
      "id": "tough_b",
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
  "pc_condition_add": [
    {
      "id": "exhausted",
      "label": "exhausted",
      "description": "Breathless from a frantic escape through market alleys.",
      "turns_remaining": 3
    }
  ],
  "pc_condition_remove": [
    {
      "id": "threatened"
    }
  ]
}
```

### Storyteller

```json
{
  "actions": [
    "Climb the canyon walls to find a vantage point.",
    "Search the nearby crevices for signs of Harker's wagon.",
    "Set up a concealed camp before total darkness falls.",
    "Follow the charcoal markings on the hand-drawn map."
  ],
  "outcome_summary": "The player escaped the thugs in the market and reached the base of the Red Canyon cliffs.",
  "thread_resolve": [
    {
      "id": "street_confrontation",
      "resolution_state": "abandoned",
      "outcome": "The player successfully evaded the thugs by fleeing through market alleys.",
      "promote_to_world_state": false
    }
  ],
  "thread_add": {
    "id": "canyon_exploration_danger",
    "summary": "Navigate hazards of the Red Canyon cliffs",
    "scope": "scene",
    "active": true,
    "urgency": "normal",
    "progress": []
  },
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "Reached Red Canyon cliffs near disappearance site",
      "progress_kind": "advancement"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "red_canyon_cliffs",
    "name": "Red Canyon Cliffs",
    "description": "Jagged canyon walls loom overhead like teeth against a bruised purple sky, with long shadows stretching across an uneven trail."
  },
  "location_description": "The terrain is uneven and rocky, filled with darkening crevices and looming cliffs under a twilight sky.",
  "pc_condition_add": [
    {
      "id": "exhausted",
      "label": "exhausted",
      "description": "Breathless from a frantic escape through market alleys.",
      "turns_remaining": 3
    }
  ],
  "pc_condition_remove": [
    {
      "id": "threatened"
    }
  ],
  "scene_tags": [
    "escape",
    "tense",
    "pursuit",
    "discovery"
  ],
  "scene_tagline": "Escape to the Red Canyon",
  "compendium_npc_update": [
    {
      "id": "assay_clerk",
      "aliases": [],
      "presence": "known"
    },
    {
      "id": "tough_a",
      "aliases": [],
      "presence": "known"
    },
    {
      "id": "tough_b",
      "aliases": [],
      "presence": "known"
    }
  ],
  "actions": [
    "Climb the canyon walls to find a vantage point.",
    "Search the nearby crevices for signs of Harker's wagon.",
    "Set up a concealed camp before total darkness falls.",
    "Follow the charcoal markings on the hand-drawn map."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "last_thread_created_turn": {
      "from": 5,
      "to": 8
    },
    "threads": {
      "added": [
        {
          "active": true,
          "added_turn": 8,
          "id": "street_confrontation",
          "progress": [],
          "scope": "scene",
          "summary": "Avoid or resolve sudden roadside aggression",
          "urgency": "urgent",
          "urgency_set_turn": 8
        }
      ],
      "changed": [
        {
          "from": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 5,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Learned Harker's wagon was found empty"
              },
              {
                "kind": "advancement",
                "text": "Found signed ledger page near Assay Office"
              },
              {
                "kind": "advancement",
                "text": "Confirmed no missing person report filed"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "id": "deliver_the_ledger",
            "last_updated_turn": 8,
            "progress": [
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "advancement",
                "text": "Learned Harker's wagon was found empty"
              },
              {
                "kind": "advancement",
                "text": "Found signed ledger page near Assay Office"
              },
              {
                "kind": "advancement",
                "text": "Confirmed no missing person report filed"
              },
              {
                "kind": "advancement",
                "text": "Arrived in Dustfall toward destination"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "assay_clerk": {
        "last_seen": {
          "location_id": {
            "from": "assay_office",
            "to": "general_store"
          },
          "location_name": {
            "from": "Assay Office",
            "to": "General Store"
          },
          "turn": {
            "from": 4,
            "to": 8
          }
        },
        "notes": {
          "from": null,
          "to": "watching with wide-eyed alarm"
        },
        "presence": {
          "from": "known",
          "to": "present"
        }
      },
      "silas_thorne": {
        "last_seen": {
          "location_id": {
            "from": "sheriffs_office",
            "to": "general_store"
          },
          "location_name": {
            "from": "Sheriff's Office",
            "to": "General Store"
          },
          "turn": {
            "from": 7,
            "to": 8
          }
        },
        "notes": {
          "from": "rising from chair with cold command",
          "to": null
        },
        "presence": {
          "from": "present",
          "to": "known"
        }
      },
      "tough_a": {
        "last_seen": {
          "from": null,
          "to": {
            "location_id": "general_store",
            "location_name": "General Store",
            "turn": 8
          }
        },
        "notes": {
          "from": null,
          "to": "scanning you with predatory focus"
        },
        "presence": {
          "from": null,
          "to": "present"
        }
      },
      "tough_b": {
        "last_seen": {
          "from": null,
          "to": {
            "location_id": "general_store",
            "location_name": "General Store",
            "turn": 8
          }
        },
        "notes": {
          "from": null,
          "to": "scanning you with predatory focus"
        },
        "presence": {
          "from": null,
          "to": "present"
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "dried_meat",
        "name": "Dried meat",
        "notes": ""
      },
      {
        "amount": 1,
        "id": "water_canteen",
        "name": "Water canteen",
        "notes": ""
      },
      {
        "amount": 1,
        "id": "hempen_rope",
        "name": "Hempen rope",
        "notes": ""
      }
    ],
    "changed": [
      {
        "from": {
          "aliases": [],
          "amount": 500,
          "id": "credits",
          "name": "Credits",
          "notes": "Common coin, accepted at any inn or stall on the merchant road."
        },
        "to": {
          "aliases": [],
          "amount": 440,
          "id": "credits",
          "name": "Credits",
          "notes": "Common coin, accepted at any inn or stall on the merchant road."
        }
      }
    ]
  },
  "location": {
    "description": {
      "from": "The desk is cluttered with stacks of tax receipts and various bureaucratic tools, now disturbed by your theft.",
      "to": "A cramped shop filled with the scent of cured leather and dust, featuring a counter stacked with iron pots."
    },
    "id": {
      "from": "sheriffs_office",
      "to": "general_store"
    },
    "name": {
      "from": "Sheriff's Office",
      "to": "General Store"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "tough_a",
        "tough_b"
      ],
      "removed": []
    },
    "consecutive_pressure_turns": {
      "from": 3,
      "to": 0
    },
    "last_thread_created_turn": {
      "from": null,
      "to": 8
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 9,
        "to": 10
      },
      "surface_as": {
        "from": "npc_behavior",
        "to": "ambient"
      },
      "type": {
        "from": "escalation",
        "to": "breathing_room"
      }
    },
    "prior_history": {
      "added": [
        "- [T8] The player enters the general store to buy supplies but is immediately targeted by two aggressive men."
      ],
      "removed": []
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            8
          ],
          [
            "type",
            "breathing_room"
          ]
        ]
      ],
      "removed": [
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            3
          ],
          [
            "type",
            "revelation"
          ]
        ]
      ]
    },
    "turn": {
      "from": 7,
      "to": 8
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Attempt to de-escalate by offering credits to the men.",
        "Grab the heavy iron pot to use as a weapon.",
        "Draw your iron dagger and face the thugs directly.",
        "Pay the clerk quickly and exit through the side door."
      ],
      "removed": [
        "Grab the tin box and bolt toward the office exit.",
        "Stand your ground and claim you were searching for a quill.",
        "Drop the dagger and apologize profusely to de-escalate Thorne's anger.",
        "Conceal the map quickly and feign accidental contact with the desk."
      ]
    },
    "conditions": {
      "added": [
        {
          "added_turn": 7,
          "description": "Two aggressive men are staring you down with predatory focus.",
          "id": "threatened",
          "label": "Threatened",
          "turns_remaining": 3
        }
      ]
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 4,
      "to": 7
    },
    "tagline": {
      "from": "Caught Red-Handed",
      "to": "Predators in the Market District"
    },
    "tags": {
      "added": [
        "suspense",
        "tense_confrontation"
      ],
      "removed": [
        "discovery",
        "tense_interaction",
        "stealth_fail"
      ]
    },
    "turn_entered": {
      "from": 4,
      "to": 7
    }
  }
}
```


---

# TURN 10

**Input:** `I find a camp at the base of the canyon wall. Two men are sitting by a fire, and I see Harker's hat on one of them. I step into the firelight.`

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
{
  "intent_verb": "persuade",
  "intent": "The player approaches a campfire where two men are resting, one of whom appears to be wearing Harker's hat.",
  "rolled": true,
  "total_ms": 3267.0,
  "tokens_in": 1368,
  "tokens_out": 108,
  "outcome_summary": "The player confronts two suspicious men at a campfire, one of whom appears to be wearing Harker's hat.",
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    9
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "raw_total": 9,
  "final_total": 10,
  "band": "success",
  "momentum_before": 1,
  "momentum_after": 2,
  "momentum_delta": 1
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "tense_confrontation",
    "discovery"
  ],
  "scene_tagline": "Shadows by the Campfire",
  "location_description": "A small campfire flickers at the base of the cliffs, casting dancing orange light against the surrounding rocks.",
  "compendium_npc_update": [
    {
      "id": "tough_a",
      "aliases": [],
      "presence": "present",
      "notes": "coiled like a spring"
    },
    {
      "id": "tough_b",
      "aliases": [],
      "presence": "present",
      "notes": "watching player's belt"
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
      "id": "exhausted"
    }
  ]
}
```

### Storyteller

```json
{
  "actions": [
    "Demand they return the hat and explain their presence",
    "Offer credits to learn about the man who owned it",
    "Draw your iron dagger and threaten them for answers",
    "Attempt to de-escalate by claiming you are just passing through"
  ],
  "outcome_summary": "The player confronts two suspicious men at a campfire, one of whom appears to be wearing Harker's hat.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [],
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "Located men wearing Harker's hat",
      "progress_kind": "advancement"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "A small campfire flickers at the base of the cliffs, casting dancing orange light against the surrounding rocks.",
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "exhausted"
    }
  ],
  "scene_tags": [
    "tense_confrontation",
    "discovery"
  ],
  "scene_tagline": "Shadows by the Campfire",
  "compendium_npc_update": [
    {
      "id": "tough_a",
      "aliases": [],
      "presence": "present",
      "notes": "coiled like a spring"
    },
    {
      "id": "tough_b",
      "aliases": [],
      "presence": "present",
      "notes": "watching player's belt"
    }
  ],
  "actions": [
    "Demand they return the hat and explain their presence",
    "Offer credits to learn about the man who owned it",
    "Draw your iron dagger and threaten them for answers",
    "Attempt to de-escalate by claiming you are just passing through"
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "last_thread_created_turn": {
      "from": 8,
      "to": 9
    },
    "threads": {
      "added": [
        {
          "active": true,
          "added_turn": 9,
          "id": "canyon_exploration_danger",
          "progress": [],
          "scope": "scene",
          "summary": "Navigate hazards of the Red Canyon cliffs",
          "urgency": "normal",
          "urgency_set_turn": 9
        }
      ],
      "removed": [
        {
          "active": true,
          "added_turn": 8,
          "id": "street_confrontation",
          "progress": [],
          "scope": "scene",
          "summary": "Avoid or resolve sudden roadside aggression",
          "urgency": "urgent",
          "urgency_set_turn": 8
        }
      ],
      "changed": [
        {
          "from": {
            "active": true,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 7,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              },
              {
                "kind": "advancement",
                "text": "Found map of Red Canyon cliffs"
              }
            ],
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 9,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              },
              {
                "kind": "advancement",
                "text": "Found map of Red Canyon cliffs"
              },
              {
                "kind": "advancement",
                "text": "Reached Red Canyon cliffs near disappearance site"
              }
            ],
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "assay_clerk": {
        "last_seen": {
          "location_id": {
            "from": "general_store",
            "to": "red_canyon_cliffs"
          },
          "location_name": {
            "from": "General Store",
            "to": "Red Canyon Cliffs"
          },
          "turn": {
            "from": 8,
            "to": 9
          }
        },
        "notes": {
          "from": "watching with wide-eyed alarm",
          "to": null
        },
        "presence": {
          "from": "present",
          "to": "known"
        }
      },
      "tough_a": {
        "last_seen": {
          "location_id": {
            "from": "general_store",
            "to": "red_canyon_cliffs"
          },
          "location_name": {
            "from": "General Store",
            "to": "Red Canyon Cliffs"
          },
          "turn": {
            "from": 8,
            "to": 9
          }
        },
        "notes": {
          "from": "scanning you with predatory focus",
          "to": null
        },
        "presence": {
          "from": "present",
          "to": "known"
        }
      },
      "tough_b": {
        "last_seen": {
          "location_id": {
            "from": "general_store",
            "to": "red_canyon_cliffs"
          },
          "location_name": {
            "from": "General Store",
            "to": "Red Canyon Cliffs"
          },
          "turn": {
            "from": 8,
            "to": 9
          }
        },
        "notes": {
          "from": "scanning you with predatory focus",
          "to": null
        },
        "presence": {
          "from": "present",
          "to": "known"
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "A cramped shop filled with the scent of cured leather and dust, featuring a counter stacked with iron pots.",
      "to": "Jagged canyon walls loom overhead like teeth against a bruised purple sky, with long shadows stretching across an uneven trail."
    },
    "id": {
      "from": "general_store",
      "to": "red_canyon_cliffs"
    },
    "name": {
      "from": "General Store",
      "to": "Red Canyon Cliffs"
    }
  },
  "meta": {
    "last_thread_created_turn": {
      "from": 8,
      "to": 9
    },
    "pending_gm_beat": {
      "from": {
        "beat_expires_turn": 10,
        "surface_as": "ambient",
        "type": "breathing_room"
      },
      "to": null
    },
    "prior_history": {
      "added": [
        "- [T9] The player escaped the thugs in the market and reached the base of the Red Canyon cliffs."
      ],
      "removed": []
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            null
          ],
          [
            "turn",
            9
          ],
          [
            "type",
            null
          ]
        ]
      ],
      "removed": [
        [
          [
            "surface_as",
            "item"
          ],
          [
            "turn",
            4
          ],
          [
            "type",
            "revelation"
          ]
        ]
      ]
    },
    "turn": {
      "from": 8,
      "to": 9
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Set up a concealed camp before total darkness falls.",
        "Follow the charcoal markings on the hand-drawn map.",
        "Climb the canyon walls to find a vantage point.",
        "Search the nearby crevices for signs of Harker's wagon."
      ],
      "removed": [
        "Attempt to de-escalate by offering credits to the men.",
        "Grab the heavy iron pot to use as a weapon.",
        "Draw your iron dagger and face the thugs directly.",
        "Pay the clerk quickly and exit through the side door."
      ]
    },
    "conditions": {
      "added": [
        {
          "added_turn": 8,
          "description": "Breathless from a frantic escape through market alleys.",
          "id": "exhausted",
          "label": "exhausted",
          "turns_remaining": 3
        }
      ],
      "removed": [
        {
          "added_turn": 7,
          "description": "Two aggressive men are staring you down with predatory focus.",
          "id": "threatened",
          "label": "Threatened",
          "turns_remaining": 3
        }
      ]
    },
    "momentum": {
      "from": 2,
      "to": 1
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 7,
      "to": 8
    },
    "tagline": {
      "from": "Predators in the Market District",
      "to": "Escape to the Red Canyon"
    },
    "tags": {
      "added": [
        "tense",
        "discovery",
        "escape",
        "pursuit"
      ],
      "removed": [
        "suspense",
        "tense_confrontation"
      ]
    },
    "turn_entered": {
      "from": 7,
      "to": 8
    }
  }
}
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

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "completed_threads": {
      "added": [
        {
          "active": false,
          "id": "settle_the_debt",
          "outcome": "The player has pivoted focus entirely to the Harker investigation.",
          "progress": [],
          "resolution_state": "abandoned",
          "resolved_turn": 10,
          "scope": "arc",
          "summary": "Settle the 500-credit debt with Caron.",
          "urgency": "normal"
        },
        {
          "active": true,
          "added_turn": 9,
          "id": "canyon_exploration_danger",
          "outcome": "Thugs intimidated and Harker rescued from cave",
          "progress": [],
          "resolution_state": "resolved",
          "resolved_turn": 11,
          "scope": "scene",
          "summary": "Navigate hazards of the Red Canyon cliffs",
          "urgency": "normal",
          "urgency_set_turn": 9
        },
        {
          "active": false,
          "id": "deliver_the_ledger",
          "last_updated_turn": 8,
          "outcome": "Arrived in Dustfall with Harker; ledger delivery pending.",
          "progress": [
            {
              "kind": "shift",
              "text": "Arrived in Dustfall toward destination"
            },
            {
              "kind": "shift",
              "text": "Learned Harker's wagon was empty"
            },
            {
              "kind": "shift",
              "text": "Found signed ledger page near office"
            },
            {
              "kind": "shift",
              "text": "Confirmed no missing person report filed"
            }
          ],
          "resolution_state": "resolved",
          "resolved_turn": 12,
          "scope": "arc",
          "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
          "urgency": "normal"
        }
      ]
    },
    "goal_context": {
      "from": "",
      "to": "The player has moved from town-based investigation to a direct confrontation at Red Canyon."
    },
    "threads": {
      "removed": [
        {
          "active": false,
          "id": "settle_the_debt",
          "progress": [],
          "scope": "arc",
          "summary": "Settle the 500-credit debt with Caron.",
          "urgency": "normal"
        },
        {
          "active": true,
          "id": "deliver_the_ledger",
          "last_updated_turn": 8,
          "progress": [
            {
              "kind": "advancement",
              "text": "Arrived in Dustfall toward destination"
            },
            {
              "kind": "advancement",
              "text": "Learned Harker's wagon was found empty"
            },
            {
              "kind": "advancement",
              "text": "Found signed ledger page near Assay Office"
            },
            {
              "kind": "advancement",
              "text": "Confirmed no missing person report filed"
            },
            {
              "kind": "advancement",
              "text": "Arrived in Dustfall toward destination"
            }
          ],
          "scope": "arc",
          "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
          "urgency": "normal"
        },
        {
          "active": true,
          "added_turn": 9,
          "id": "canyon_exploration_danger",
          "progress": [],
          "scope": "scene",
          "summary": "Navigate hazards of the Red Canyon cliffs",
          "urgency": "normal",
          "urgency_set_turn": 9
        }
      ],
      "changed": [
        {
          "from": {
            "active": true,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 9,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              },
              {
                "kind": "advancement",
                "text": "Found map of Red Canyon cliffs"
              },
              {
                "kind": "advancement",
                "text": "Reached Red Canyon cliffs near disappearance site"
              }
            ],
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 13,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              },
              {
                "kind": "advancement",
                "text": "Found map of Red Canyon cliffs"
              },
              {
                "kind": "advancement",
                "text": "Reached Red Canyon cliffs near disappearance site"
              },
              {
                "kind": "advancement",
                "text": "Located men wearing Harker's hat"
              },
              {
                "kind": "advancement",
                "text": "Rescued Harker from canyon cave"
              },
              {
                "kind": "advancement",
                "text": "Harker rescued and brought to clinic"
              }
            ],
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal"
          }
        }
      ]
    },
    "visible_goal": {
      "from": "Clear your debts and deliver the ledger \u2014 two obligations binding you to Marrow's Crossing.",
      "to": "Investigate Harker's disappearance and survive the canyon encounter."
    }
  },
  "compendium": {
    "npcs": {
      "elara_vance": {
        "last_seen": {
          "location_id": {
            "from": "assay_office",
            "to": "dustfall_outskirts"
          },
          "location_name": {
            "from": "Assay Office",
            "to": "Dustfall Outskirts"
          },
          "turn": {
            "from": 4,
            "to": 13
          }
        },
        "notes": {
          "from": null,
          "to": "serving whiskey with a solemn nod"
        },
        "presence": {
          "from": "known",
          "to": "present"
        }
      },
      "old_man_harker": {
        "from": null,
        "to": {
          "bio": "An elderly man with a face marked by fresh bruises and dried blood. He appears physically weakened and traumatized after being held captive.",
          "first_seen_turn": 10,
          "last_seen": {
            "location_id": "dustfall_outskirts",
            "location_name": "Dustfall Outskirts",
            "turn": 13
          },
          "name": "Old Man Harker",
          "notes": "stumbling toward clinic",
          "presence": "known",
          "title": "Victim"
        }
      },
      "saloon_patrons": {
        "last_seen": {
          "location_id": {
            "from": "assay_office",
            "to": "dustfall_outskirts"
          },
          "location_name": {
            "from": "Assay Office",
            "to": "Dustfall Outskirts"
          },
          "turn": {
            "from": 4,
            "to": 13
          }
        },
        "notes": {
          "from": null,
          "to": "whispering warily in the corner"
        },
        "presence": {
          "from": "known",
          "to": "present"
        }
      },
      "tough_a": {
        "last_seen": {
          "turn": {
            "from": 9,
            "to": 11
          }
        }
      },
      "tough_b": {
        "last_seen": {
          "turn": {
            "from": 9,
            "to": 11
          }
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "whiskey_glass",
        "name": "Whiskey glass",
        "notes": "A single serving of whiskey provided by Elara Vance."
      }
    ],
    "removed": [
      {
        "amount": 1,
        "id": "hempen_rope",
        "name": "Hempen rope",
        "notes": ""
      }
    ]
  },
  "location": {
    "description": {
      "from": "Jagged canyon walls loom overhead like teeth against a bruised purple sky, with long shadows stretching across an uneven trail.",
      "to": "The tavern is thick with the scent of stale ale and heat, where dim lighting casts long shadows over scarred wooden surfaces."
    },
    "id": {
      "from": "red_canyon_cliffs",
      "to": "dustfall_outskirts"
    },
    "name": {
      "from": "Red Canyon Cliffs",
      "to": "Dustfall Outskirts"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "old_man_harker"
      ],
      "removed": []
    },
    "consecutive_pressure_turns": {
      "from": 0,
      "to": 2
    },
    "pending_gm_beat": {
      "from": null,
      "to": {
        "beat_expires_turn": 15,
        "surface_as": "npc_behavior",
        "type": "complication"
      }
    },
    "prior_history": {
      "added": [
        "- [T11] The player intimidated the thugs and successfully freed Old Man Harker from his bindings in the canyon cave.",
        "- [T13] The player delivers Harker to the clinic and seeks refuge in the saloon.",
        "- [T10] The player confronts two suspicious men at a campfire, one of whom appears to be wearing Harker's hat.",
        "- [T12] The player successfully guides a traumatized Harker from the Red Canyon cliffs into the outskirts of Dustfall."
      ],
      "removed": []
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            null
          ],
          [
            "turn",
            11
          ],
          [
            "type",
            null
          ]
        ],
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            10
          ],
          [
            "type",
            "pressure"
          ]
        ],
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            12
          ],
          [
            "type",
            "pressure"
          ]
        ],
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            13
          ],
          [
            "type",
            "complication"
          ]
        ]
      ],
      "removed": [
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            7
          ],
          [
            "type",
            "escalation"
          ]
        ],
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            8
          ],
          [
            "type",
            "breathing_room"
          ]
        ],
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            6
          ],
          [
            "type",
            "pressure"
          ]
        ],
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            5
          ],
          [
            "type",
            "complication"
          ]
        ]
      ]
    },
    "turn": {
      "from": 9,
      "to": 13
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Question Elara about any suspicious activity near the canyon.",
        "Listen to the patrons' whispers for rumors of the thugs.",
        "Order another whiskey to observe the room more closely.",
        "Search for a local healer willing to treat Harker."
      ],
      "removed": [
        "Set up a concealed camp before total darkness falls.",
        "Follow the charcoal markings on the hand-drawn map.",
        "Climb the canyon walls to find a vantage point.",
        "Search the nearby crevices for signs of Harker's wagon."
      ]
    },
    "conditions": {
      "removed": [
        {
          "added_turn": 8,
          "description": "Breathless from a frantic escape through market alleys.",
          "id": "exhausted",
          "label": "exhausted",
          "turns_remaining": 3
        }
      ]
    },
    "momentum": {
      "from": 1,
      "to": 3
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 8,
      "to": 11
    },
    "tagline": {
      "from": "Escape to the Red Canyon",
      "to": "A Drink in the Gloom"
    },
    "tags": {
      "added": [
        "social_interaction",
        "tense_atmosphere"
      ],
      "removed": [
        "tense",
        "discovery",
        "escape",
        "pursuit"
      ]
    },
    "turn_entered": {
      "from": 8,
      "to": 11
    }
  }
}
```


---

# TURN 11

**Input:** `The men surrender. I find Harker tied up in a nearby cave. He's bruised but alive. I cut him loose and give him water.`

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
{
  "intent_verb": "intimidate",
  "intent": "The player attempts to force the thugs into surrendering and then rescues Old Man Harker from a cave.",
  "rolled": true,
  "total_ms": 2914.1,
  "tokens_in": 1394,
  "tokens_out": 98,
  "outcome_summary": "The player intimidated the thugs and successfully freed Old Man Harker from his bindings in the canyon cave.",
  "skill": "charisma",
  "difficulty": "hard",
  "dice": [
    10
  ],
  "stat_mod": 1,
  "diff_mod": -1,
  "cond_mod": 0,
  "raw_total": 10,
  "final_total": 10,
  "band": "success",
  "momentum_before": 2,
  "momentum_after": 3,
  "momentum_delta": 1
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "tense_rescue",
    "discovery"
  ],
  "scene_tagline": "A Fragile Rescue in the Dark",
  "location_description": "The mouth of a narrow cave, where damp stone walls provide a cold contrast to the flickering campfire outside.",
  "compendium_npc_update": [
    {
      "id": "tough_a",
      "aliases": [],
      "notes": "backing away toward shadows"
    },
    {
      "id": "tough_b",
      "aliases": [],
      "notes": "exchanging wary looks"
    },
    {
      "id": "old_man_harker",
      "name": "Old Man Harker",
      "title": "Victim",
      "bio": "An elderly man with a face marked by fresh bruises and dried blood. He appears physically weakened and traumatized after being held captive.",
      "aliases": [],
      "presence": "present",
      "notes": "clinging to canteen greedily"
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
      "id": "hempen_rope",
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
  "actions": [
    "Question Harker about what specifically the thugs were searching for.",
    "Threaten the retreating thugs to reveal their employer's identity.",
    "Secure the cave entrance to protect the wounded Harker.",
    "Search the surrounding campsite for any stolen goods or ledgers."
  ],
  "outcome_summary": "The player intimidated the thugs and successfully freed Old Man Harker from his bindings in the canyon cave.",
  "thread_resolve": [
    {
      "id": "canyon_exploration_danger",
      "resolution_state": "resolved",
      "outcome": "Thugs intimidated and Harker rescued from cave",
      "promote_to_world_state": false
    }
  ],
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "Located and freed Old Man Harker",
      "progress_kind": "advancement"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "hempen_rope",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "location_description": "The mouth of a narrow cave, where damp stone walls provide a cold contrast to the flickering campfire outside.",
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "tense_rescue",
    "discovery"
  ],
  "scene_tagline": "A Fragile Rescue in the Dark",
  "compendium_npc_update": [
    {
      "id": "tough_a",
      "aliases": [],
      "notes": "backing away toward shadows"
    },
    {
      "id": "tough_b",
      "aliases": [],
      "notes": "exchanging wary looks"
    },
    {
      "id": "old_man_harker",
      "name": "Old Man Harker",
      "title": "Victim",
      "bio": "An elderly man with a face marked by fresh bruises and dried blood. He appears physically weakened and traumatized after being held captive.",
      "aliases": [],
      "presence": "present",
      "notes": "clinging to canteen greedily"
    }
  ],
  "actions": [
    "Question Harker about what specifically the thugs were searching for.",
    "Threaten the retreating thugs to reveal their employer's identity.",
    "Secure the cave entrance to protect the wounded Harker.",
    "Search the surrounding campsite for any stolen goods or ledgers."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "completed_threads": {
      "removed": [
        {
          "active": true,
          "added_turn": 9,
          "id": "canyon_exploration_danger",
          "outcome": "Thugs intimidated and Harker rescued from cave",
          "progress": [],
          "resolution_state": "resolved",
          "resolved_turn": 11,
          "scope": "scene",
          "summary": "Navigate hazards of the Red Canyon cliffs",
          "urgency": "normal",
          "urgency_set_turn": 9
        },
        {
          "active": false,
          "id": "deliver_the_ledger",
          "last_updated_turn": 8,
          "outcome": "Arrived in Dustfall with Harker; ledger delivery pending.",
          "progress": [
            {
              "kind": "shift",
              "text": "Arrived in Dustfall toward destination"
            },
            {
              "kind": "shift",
              "text": "Learned Harker's wagon was empty"
            },
            {
              "kind": "shift",
              "text": "Found signed ledger page near office"
            },
            {
              "kind": "shift",
              "text": "Confirmed no missing person report filed"
            }
          ],
          "resolution_state": "resolved",
          "resolved_turn": 12,
          "scope": "arc",
          "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
          "urgency": "normal"
        }
      ],
      "changed": [
        {
          "from": {
            "active": false,
            "id": "clear_the_road_toughs",
            "outcome": "The player has entered the town, bypassing the road blockade.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 1,
            "scope": "arc",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "urgency": "background"
          },
          "to": {
            "active": false,
            "added_turn": null,
            "id": "clear_the_road_toughs",
            "last_updated_turn": null,
            "outcome": "The player has entered the town, bypassing the road blockade.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 1,
            "scope": "arc",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "urgency": "background",
            "urgency_set_turn": null
          }
        },
        {
          "from": {
            "active": false,
            "id": "settle_the_debt",
            "outcome": "The player has pivoted focus entirely to the Harker investigation.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 10,
            "scope": "arc",
            "summary": "Settle the 500-credit debt with Caron.",
            "urgency": "normal"
          },
          "to": {
            "active": false,
            "added_turn": null,
            "id": "settle_the_debt",
            "last_updated_turn": null,
            "outcome": "The player has pivoted focus entirely to the Harker investigation.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 10,
            "scope": "arc",
            "summary": "Settle the 500-credit debt with Caron.",
            "urgency": "normal",
            "urgency_set_turn": null
          }
        }
      ]
    },
    "threads": {
      "added": [
        {
          "active": false,
          "added_turn": null,
          "id": "deliver_the_ledger",
          "last_updated_turn": 8,
          "outcome": null,
          "progress": [
            {
              "kind": "shift",
              "text": "Arrived in Dustfall toward destination"
            },
            {
              "kind": "shift",
              "text": "Learned Harker's wagon was empty"
            },
            {
              "kind": "shift",
              "text": "Found signed ledger page near office"
            },
            {
              "kind": "shift",
              "text": "Confirmed no missing person report filed"
            }
          ],
          "resolution_state": null,
          "resolved_turn": null,
          "scope": "arc",
          "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
          "urgency": "normal",
          "urgency_set_turn": null
        },
        {
          "active": true,
          "added_turn": 9,
          "id": "canyon_exploration_danger",
          "last_updated_turn": null,
          "outcome": null,
          "progress": [],
          "resolution_state": null,
          "resolved_turn": null,
          "scope": "scene",
          "summary": "Navigate hazards of the Red Canyon cliffs",
          "urgency": "normal",
          "urgency_set_turn": 9
        }
      ],
      "changed": [
        {
          "from": {
            "active": true,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 13,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              },
              {
                "kind": "advancement",
                "text": "Found map of Red Canyon cliffs"
              },
              {
                "kind": "advancement",
                "text": "Reached Red Canyon cliffs near disappearance site"
              },
              {
                "kind": "advancement",
                "text": "Located men wearing Harker's hat"
              },
              {
                "kind": "advancement",
                "text": "Rescued Harker from canyon cave"
              },
              {
                "kind": "advancement",
                "text": "Harker rescued and brought to clinic"
              }
            ],
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal"
          },
          "to": {
            "active": true,
            "added_turn": null,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 10,
            "outcome": null,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              },
              {
                "kind": "advancement",
                "text": "Found map of Red Canyon cliffs"
              },
              {
                "kind": "advancement",
                "text": "Reached Red Canyon cliffs near disappearance site"
              },
              {
                "kind": "advancement",
                "text": "Located men wearing Harker's hat"
              }
            ],
            "resolution_state": null,
            "resolved_turn": null,
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal",
            "urgency_set_turn": null
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "elara_vance": {
        "last_seen": {
          "location_id": {
            "from": "dustfall_outskirts",
            "to": "assay_office"
          },
          "location_name": {
            "from": "Dustfall Outskirts",
            "to": "Assay Office"
          },
          "turn": {
            "from": 13,
            "to": 4
          }
        },
        "notes": {
          "from": "serving whiskey with a solemn nod",
          "to": null
        },
        "presence": {
          "from": "present",
          "to": "known"
        }
      },
      "old_man_harker": {
        "from": {
          "bio": "An elderly man with a face marked by fresh bruises and dried blood. He appears physically weakened and traumatized after being held captive.",
          "first_seen_turn": 10,
          "last_seen": {
            "location_id": "dustfall_outskirts",
            "location_name": "Dustfall Outskirts",
            "turn": 13
          },
          "name": "Old Man Harker",
          "notes": "stumbling toward clinic",
          "presence": "known",
          "title": "Victim"
        },
        "to": null
      },
      "saloon_patrons": {
        "last_seen": {
          "location_id": {
            "from": "dustfall_outskirts",
            "to": "assay_office"
          },
          "location_name": {
            "from": "Dustfall Outskirts",
            "to": "Assay Office"
          },
          "turn": {
            "from": 13,
            "to": 4
          }
        },
        "notes": {
          "from": "whispering warily in the corner",
          "to": null
        },
        "presence": {
          "from": "present",
          "to": "known"
        }
      },
      "tough_a": {
        "last_seen": {
          "turn": {
            "from": 11,
            "to": 10
          }
        },
        "notes": {
          "from": null,
          "to": "coiled like a spring"
        },
        "presence": {
          "from": "known",
          "to": "present"
        }
      },
      "tough_b": {
        "last_seen": {
          "turn": {
            "from": 11,
            "to": 10
          }
        },
        "notes": {
          "from": null,
          "to": "watching player's belt"
        },
        "presence": {
          "from": "known",
          "to": "present"
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "hempen_rope",
        "name": "Hempen rope",
        "notes": ""
      }
    ],
    "removed": [
      {
        "amount": 1,
        "id": "whiskey_glass",
        "name": "Whiskey glass",
        "notes": "A single serving of whiskey provided by Elara Vance."
      }
    ]
  },
  "location": {
    "description": {
      "from": "The tavern is thick with the scent of stale ale and heat, where dim lighting casts long shadows over scarred wooden surfaces.",
      "to": "A small campfire flickers at the base of the cliffs, casting dancing orange light against the surrounding rocks."
    },
    "id": {
      "from": "dustfall_outskirts",
      "to": "red_canyon_cliffs"
    },
    "name": {
      "from": "Dustfall Outskirts",
      "to": "Red Canyon Cliffs"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [],
      "removed": [
        "old_man_harker"
      ]
    },
    "consecutive_pressure_turns": {
      "from": 2,
      "to": 1
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 15,
        "to": 12
      },
      "type": {
        "from": "complication",
        "to": "pressure"
      }
    },
    "prior_history": {
      "added": [],
      "removed": [
        "- [T11] The player intimidated the thugs and successfully freed Old Man Harker from his bindings in the canyon cave.",
        "- [T13] The player delivers Harker to the clinic and seeks refuge in the saloon.",
        "- [T12] The player successfully guides a traumatized Harker from the Red Canyon cliffs into the outskirts of Dustfall."
      ]
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            7
          ],
          [
            "type",
            "escalation"
          ]
        ],
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            8
          ],
          [
            "type",
            "breathing_room"
          ]
        ],
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            6
          ],
          [
            "type",
            "pressure"
          ]
        ]
      ],
      "removed": [
        [
          [
            "surface_as",
            null
          ],
          [
            "turn",
            11
          ],
          [
            "type",
            null
          ]
        ],
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            12
          ],
          [
            "type",
            "pressure"
          ]
        ],
        [
          [
            "surface_as",
            "npc_behavior"
          ],
          [
            "turn",
            13
          ],
          [
            "type",
            "complication"
          ]
        ]
      ]
    },
    "turn": {
      "from": 13,
      "to": 10
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Demand they return the hat and explain their presence",
        "Attempt to de-escalate by claiming you are just passing through",
        "Draw your iron dagger and threaten them for answers",
        "Offer credits to learn about the man who owned it"
      ],
      "removed": [
        "Question Elara about any suspicious activity near the canyon.",
        "Listen to the patrons' whispers for rumors of the thugs.",
        "Order another whiskey to observe the room more closely.",
        "Search for a local healer willing to treat Harker."
      ]
    },
    "momentum": {
      "from": 3,
      "to": 2
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 11,
      "to": 8
    },
    "tagline": {
      "from": "A Drink in the Gloom",
      "to": "Shadows by the Campfire"
    },
    "tags": {
      "added": [
        "discovery",
        "tense_confrontation"
      ],
      "removed": [
        "social_interaction",
        "tense_atmosphere"
      ]
    },
    "turn_entered": {
      "from": 11,
      "to": 8
    }
  }
}
```


---

# TURN 12

**Input:** `Harker and I ride back to Dustfall together. He's quiet but grateful. The town lights come into view as dusk settles.`

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
{
  "intent_verb": "transition",
  "intent": "The player intends to travel from the Red Canyon Cliffs to the town of Dustfall with Old Man Harker.",
  "rolled": false,
  "total_ms": 2648.9,
  "tokens_in": 1440,
  "tokens_out": 83,
  "outcome_summary": "The player successfully guides a traumatized Harker from the Red Canyon cliffs into the outskirts of Dustfall."
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "travel",
    "somber",
    "gloaming"
  ],
  "scene_tagline": "Entering the Dim Streets of Dustfall",
  "location_change": {
    "id": "dustfall_outskirts",
    "name": "Dustfall Outskirts",
    "description": "The outskirts of a settlement where boarded-up storefronts line the road and flickering lanterns begin to pierce the evening gloom."
  },
  "location_description": "The town center near the river crossing is brightly lit, contrasting with the stifled, uneasy atmosphere of the surrounding streets.",
  "compendium_npc_update": [
    {
      "id": "old_man_harker",
      "aliases": [],
      "presence": "present",
      "notes": "clinging to rider's waist"
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
      "id": "exhausted",
      "label": "Exhausted",
      "description": "The physical strain of guiding a horse through canyon terrain while carrying an extra passenger has left you weary.",
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
    "Seek medical aid for Harker at the Crossed Keys inn.",
    "Confront Elara Vance about the thugs seen near the canyon.",
    "Search for Caron to settle debts and find information.",
    "Hide Harker in a dark alley to avoid local scrutiny."
  ],
  "outcome_summary": "The player successfully guides a traumatized Harker from the Red Canyon cliffs into the outskirts of Dustfall.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior"
  },
  "thread_resolve": [
    {
      "id": "deliver_the_ledger",
      "resolution_state": "resolved",
      "outcome": "Arrived in Dustfall with Harker; ledger delivery pending.",
      "promote_to_world_state": false
    }
  ],
  "thread_update": [
    {
      "id": "investigate_harker_disappearance",
      "active": true,
      "urgency": "normal",
      "progress": "Rescued Harker from canyon cave",
      "progress_kind": "advancement"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "dustfall_outskirts",
    "name": "Dustfall Outskirts",
    "description": "The outskirts of a settlement where boarded-up storefronts line the road and flickering lanterns begin to pierce the evening gloom."
  },
  "location_description": "The town center near the river crossing is brightly lit, contrasting with the stifled, uneasy atmosphere of the surrounding streets.",
  "pc_condition_add": [
    {
      "id": "exhausted",
      "label": "Exhausted",
      "description": "The physical strain of guiding a horse through canyon terrain while carrying an extra passenger has left you weary.",
      "turns_remaining": 3
    }
  ],
  "pc_condition_remove": [],
  "scene_tags": [
    "travel",
    "somber",
    "gloaming"
  ],
  "scene_tagline": "Entering the Dim Streets of Dustfall",
  "compendium_npc_update": [
    {
      "id": "old_man_harker",
      "aliases": [],
      "presence": "present",
      "notes": "clinging to rider's waist"
    }
  ],
  "actions": [
    "Seek medical aid for Harker at the Crossed Keys inn.",
    "Confront Elara Vance about the thugs seen near the canyon.",
    "Search for Caron to settle debts and find information.",
    "Hide Harker in a dark alley to avoid local scrutiny."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "completed_threads": {
      "added": [
        {
          "active": true,
          "added_turn": 9,
          "id": "canyon_exploration_danger",
          "outcome": "Thugs intimidated and Harker rescued from cave",
          "progress": [],
          "resolution_state": "resolved",
          "resolved_turn": 11,
          "scope": "scene",
          "summary": "Navigate hazards of the Red Canyon cliffs",
          "urgency": "normal",
          "urgency_set_turn": 9
        }
      ],
      "changed": [
        {
          "from": {
            "active": false,
            "added_turn": null,
            "id": "clear_the_road_toughs",
            "last_updated_turn": null,
            "outcome": "The player has entered the town, bypassing the road blockade.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 1,
            "scope": "arc",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "urgency": "background",
            "urgency_set_turn": null
          },
          "to": {
            "active": false,
            "id": "clear_the_road_toughs",
            "outcome": "The player has entered the town, bypassing the road blockade.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 1,
            "scope": "arc",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "urgency": "background"
          }
        },
        {
          "from": {
            "active": false,
            "added_turn": null,
            "id": "settle_the_debt",
            "last_updated_turn": null,
            "outcome": "The player has pivoted focus entirely to the Harker investigation.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 10,
            "scope": "arc",
            "summary": "Settle the 500-credit debt with Caron.",
            "urgency": "normal",
            "urgency_set_turn": null
          },
          "to": {
            "active": false,
            "id": "settle_the_debt",
            "outcome": "The player has pivoted focus entirely to the Harker investigation.",
            "progress": [],
            "resolution_state": "abandoned",
            "resolved_turn": 10,
            "scope": "arc",
            "summary": "Settle the 500-credit debt with Caron.",
            "urgency": "normal"
          }
        }
      ]
    },
    "threads": {
      "removed": [
        {
          "active": true,
          "added_turn": 9,
          "id": "canyon_exploration_danger",
          "last_updated_turn": null,
          "outcome": null,
          "progress": [],
          "resolution_state": null,
          "resolved_turn": null,
          "scope": "scene",
          "summary": "Navigate hazards of the Red Canyon cliffs",
          "urgency": "normal",
          "urgency_set_turn": 9
        }
      ],
      "changed": [
        {
          "from": {
            "active": false,
            "added_turn": null,
            "id": "deliver_the_ledger",
            "last_updated_turn": 8,
            "outcome": null,
            "progress": [
              {
                "kind": "shift",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "shift",
                "text": "Learned Harker's wagon was empty"
              },
              {
                "kind": "shift",
                "text": "Found signed ledger page near office"
              },
              {
                "kind": "shift",
                "text": "Confirmed no missing person report filed"
              }
            ],
            "resolution_state": null,
            "resolved_turn": null,
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal",
            "urgency_set_turn": null
          },
          "to": {
            "active": false,
            "id": "deliver_the_ledger",
            "last_updated_turn": 8,
            "progress": [
              {
                "kind": "shift",
                "text": "Arrived in Dustfall toward destination"
              },
              {
                "kind": "shift",
                "text": "Learned Harker's wagon was empty"
              },
              {
                "kind": "shift",
                "text": "Found signed ledger page near office"
              },
              {
                "kind": "shift",
                "text": "Confirmed no missing person report filed"
              }
            ],
            "scope": "arc",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "urgency": "normal"
          }
        },
        {
          "from": {
            "active": true,
            "added_turn": null,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 10,
            "outcome": null,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              },
              {
                "kind": "advancement",
                "text": "Found map of Red Canyon cliffs"
              },
              {
                "kind": "advancement",
                "text": "Reached Red Canyon cliffs near disappearance site"
              },
              {
                "kind": "advancement",
                "text": "Located men wearing Harker's hat"
              }
            ],
            "resolution_state": null,
            "resolved_turn": null,
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal",
            "urgency_set_turn": null
          },
          "to": {
            "active": true,
            "id": "investigate_harker_disappearance",
            "last_updated_turn": 11,
            "progress": [
              {
                "kind": "setback",
                "text": "Officer Thorne denies any official missing person report"
              },
              {
                "kind": "advancement",
                "text": "Found map of Red Canyon cliffs"
              },
              {
                "kind": "advancement",
                "text": "Reached Red Canyon cliffs near disappearance site"
              },
              {
                "kind": "advancement",
                "text": "Located men wearing Harker's hat"
              }
            ],
            "scope": "arc",
            "summary": "Investigate the mysterious disappearance of Old Man Harker.",
            "urgency": "normal"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "old_man_harker": {
        "from": null,
        "to": {
          "bio": "An elderly man with a face marked by fresh bruises and dried blood. He appears physically weakened and traumatized after being held captive.",
          "first_seen_turn": 10,
          "last_seen": {
            "location_id": "red_canyon_cliffs",
            "location_name": "Red Canyon Cliffs",
            "turn": 11
          },
          "name": "Old Man Harker",
          "notes": "clinging to canteen greedily",
          "presence": "present",
          "title": "Victim"
        }
      },
      "tough_a": {
        "last_seen": {
          "turn": {
            "from": 10,
            "to": 11
          }
        },
        "notes": {
          "from": "coiled like a spring",
          "to": "backing away toward shadows"
        }
      },
      "tough_b": {
        "last_seen": {
          "turn": {
            "from": 10,
            "to": 11
          }
        },
        "notes": {
          "from": "watching player's belt",
          "to": "exchanging wary looks"
        }
      }
    }
  },
  "inventory": {
    "removed": [
      {
        "amount": 1,
        "id": "hempen_rope",
        "name": "Hempen rope",
        "notes": ""
      }
    ]
  },
  "location": {
    "description": {
      "from": "A small campfire flickers at the base of the cliffs, casting dancing orange light against the surrounding rocks.",
      "to": "The mouth of a narrow cave, where damp stone walls provide a cold contrast to the flickering campfire outside."
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "old_man_harker"
      ],
      "removed": []
    },
    "consecutive_pressure_turns": {
      "from": 1,
      "to": 0
    },
    "pending_gm_beat": {
      "from": {
        "beat_expires_turn": 12,
        "surface_as": "npc_behavior",
        "type": "pressure"
      },
      "to": null
    },
    "prior_history": {
      "added": [
        "- [T11] The player intimidated the thugs and successfully freed Old Man Harker from his bindings in the canyon cave."
      ],
      "removed": []
    },
    "recent_beats": {
      "added": [
        [
          [
            "surface_as",
            null
          ],
          [
            "turn",
            11
          ],
          [
            "type",
            null
          ]
        ]
      ],
      "removed": [
        [
          [
            "surface_as",
            "ambient"
          ],
          [
            "turn",
            6
          ],
          [
            "type",
            "pressure"
          ]
        ]
      ]
    },
    "turn": {
      "from": 10,
      "to": 11
    }
  },
  "pc": {
    "actions": {
      "added": [
        "Secure the cave entrance to protect the wounded Harker.",
        "Question Harker about what specifically the thugs were searching for.",
        "Threaten the retreating thugs to reveal their employer's identity.",
        "Search the surrounding campsite for any stolen goods or ledgers."
      ],
      "removed": [
        "Demand they return the hat and explain their presence",
        "Attempt to de-escalate by claiming you are just passing through",
        "Draw your iron dagger and threaten them for answers",
        "Offer credits to learn about the man who owned it"
      ]
    },
    "momentum": {
      "from": 2,
      "to": 3
    }
  },
  "scene": {
    "tagline": {
      "from": "Shadows by the Campfire",
      "to": "A Fragile Rescue in the Dark"
    },
    "tags": {
      "added": [
        "tense_rescue"
      ],
      "removed": [
        "tense_confrontation"
      ]
    }
  }
}
```


---

# TURN 13

**Input:** `I walk Harker to the doc's office and then head to the saloon. The bartender sets a whiskey on the bar and nods. I drink it slow.`

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
{
  "intent_verb": "advance",
  "intent": "The player intends to transport the injured Harker to medical care and then consume alcohol at the saloon.",
  "rolled": false,
  "total_ms": 2561.3,
  "tokens_in": 1384,
  "tokens_out": 83,
  "outcome_summary": "The player delivers Harker to the clinic and seeks refuge in the saloon."
}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{
  "scene_tags": [
    "tense_atmosphere",
    "social_interaction"
  ],
  "scene_tagline": "A Drink in the Gloom",
  "location_description": "The tavern is thick with the scent of stale ale and heat, where dim lighting casts long shadows over scarred wooden surfaces.",
  "compendium_npc_update": [
    {
      "id": "old_man_harker",
      "aliases": [],
      "presence": "known",
      "notes": "stumbling toward clinic"
    },
    {
      "id": "elara_vance",
      "aliases": [],
      "presence": "present",
      "notes": "serving whiskey with a solemn nod"
    },
    {
      "id": "saloon_patrons",
      "aliases": [],
      "presence": "present",
      "notes": "whispering warily in the corner"
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
      "notes": "A single serving of whiskey provided by Elara Vance.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "exhausted"
    }
  ]
}
```

### Storyteller

```json
{
  "actions": [
    "Question Elara about any suspicious activity near the canyon.",
    "Listen to the patrons' whispers for rumors of the thugs.",
    "Order another whiskey to observe the room more closely.",
    "Search for a local healer willing to treat Harker."
  ],
  "outcome_summary": "The player delivers Harker to the clinic and seeks refuge in the saloon.",
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
      "progress": "Harker rescued and brought to clinic",
      "progress_kind": "advancement"
    }
  ]
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "whiskey_glass",
      "name": "Whiskey glass",
      "notes": "A single serving of whiskey provided by Elara Vance.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The tavern is thick with the scent of stale ale and heat, where dim lighting casts long shadows over scarred wooden surfaces.",
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "exhausted"
    }
  ],
  "scene_tags": [
    "tense_atmosphere",
    "social_interaction"
  ],
  "scene_tagline": "A Drink in the Gloom",
  "compendium_npc_update": [
    {
      "id": "old_man_harker",
      "aliases": [],
      "presence": "known",
      "notes": "stumbling toward clinic"
    },
    {
      "id": "elara_vance",
      "aliases": [],
      "presence": "present",
      "notes": "serving whiskey with a solemn nod"
    },
    {
      "id": "saloon_patrons",
      "aliases": [],
      "presence": "present",
      "notes": "whispering warily in the corner"
    }
  ],
  "actions": [
    "Question Elara about any suspicious activity near the canyon.",
    "Listen to the patrons' whispers for rumors of the thugs.",
    "Order another whiskey to observe the room more closely.",
    "Search for a local healer willing to treat Harker."
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

```json
{
  "arc": {
    "completed_threads": [
      {
        "active": false,
        "id": "clear_the_road_toughs",
        "outcome": "The player has entered the town, bypassing the road blockade.",
        "progress": [],
        "resolution_state": "abandoned",
        "resolved_turn": 1,
        "scope": "arc",
        "summary": "Deal with the toughs blocking the inn entrance.",
        "urgency": "background"
      },
      {
        "active": false,
        "id": "settle_the_debt",
        "outcome": "The player has pivoted focus entirely to the Harker investigation.",
        "progress": [],
        "resolution_state": "abandoned",
        "resolved_turn": 10,
        "scope": "arc",
        "summary": "Settle the 500-credit debt with Caron.",
        "urgency": "normal"
      },
      {
        "active": true,
        "added_turn": 9,
        "id": "canyon_exploration_danger",
        "outcome": "Thugs intimidated and Harker rescued from cave",
        "progress": [],
        "resolution_state": "resolved",
        "resolved_turn": 11,
        "scope": "scene",
        "summary": "Navigate hazards of the Red Canyon cliffs",
        "urgency": "normal",
        "urgency_set_turn": 9
      },
      {
        "active": false,
        "id": "deliver_the_ledger",
        "last_updated_turn": 8,
        "outcome": "Arrived in Dustfall with Harker; ledger delivery pending.",
        "progress": [
          {
            "kind": "shift",
            "text": "Arrived in Dustfall toward destination"
          },
          {
            "kind": "shift",
            "text": "Learned Harker's wagon was empty"
          },
          {
            "kind": "shift",
            "text": "Found signed ledger page near office"
          },
          {
            "kind": "shift",
            "text": "Confirmed no missing person report filed"
          }
        ],
        "resolution_state": "resolved",
        "resolved_turn": 12,
        "scope": "arc",
        "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
        "urgency": "normal"
      }
    ],
    "goal_context": "The player has moved from town-based investigation to a direct confrontation at Red Canyon.",
    "last_thread_created_turn": 9,
    "resolution": null,
    "threads": [
      {
        "active": true,
        "id": "investigate_harker_disappearance",
        "last_updated_turn": 12,
        "progress": [
          {
            "kind": "setback",
            "text": "Officer Thorne denies any official missing person report"
          },
          {
            "kind": "advancement",
            "text": "Found map of Red Canyon cliffs"
          },
          {
            "kind": "advancement",
            "text": "Reached Red Canyon cliffs near disappearance site"
          },
          {
            "kind": "advancement",
            "text": "Located men wearing Harker's hat"
          },
          {
            "kind": "advancement",
            "text": "Rescued Harker from canyon cave"
          }
        ],
        "scope": "arc",
        "summary": "Investigate the mysterious disappearance of Old Man Harker.",
        "urgency": "normal"
      }
    ],
    "visible_goal": "Investigate Harker's disappearance and survive the canyon encounter."
  },
  "compendium": {
    "npcs": {
      "assay_clerk": {
        "bio": "A weary individual with bloodshot eyes peering through a viewing port. Speaks with a raspy, disinterested tone.",
        "first_seen_turn": 3,
        "last_seen": {
          "location_id": "red_canyon_cliffs",
          "location_name": "Red Canyon Cliffs",
          "turn": 9
        },
        "name": "Assay Clerk",
        "presence": "known",
        "title": "Office Attendant"
      },
      "caron": {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "bond": null,
        "fear": null,
        "leverage": null,
        "motivation": null,
        "name": "Caron",
        "presence": null,
        "title": "Old creditor"
      },
      "elara_vance": {
        "bio": "A woman with calloused hands and a sharp, discerning gaze. Her voice is raspy from years of breathing dust and shouting over tavern din.",
        "first_seen_turn": 1,
        "last_seen": {
          "location_id": "assay_office",
          "location_name": "Assay Office",
          "turn": 4
        },
        "name": "Elara Vance",
        "presence": "known",
        "title": "Bartender"
      },
      "halden": {
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
        "bond": null,
        "fear": null,
        "leverage": null,
        "motivation": null,
        "name": "Halden",
        "presence": null,
        "title": "Merchant"
      },
      "innkeeper": {
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "bond": null,
        "fear": null,
        "leverage": null,
        "motivation": null,
        "name": "Edda",
        "presence": null,
        "title": "Innkeeper at the Crossed Keys"
      },
      "matthew_estrada": {
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
        "bond": null,
        "fear": null,
        "leverage": null,
        "motivation": null,
        "name": "Matthew Estrada",
        "presence": null,
        "title": "Traveler"
      },
      "old_man_harker": {
        "bio": "An elderly man with a face marked by fresh bruises and dried blood. He appears physically weakened and traumatized after being held captive.",
        "first_seen_turn": 10,
        "last_seen": {
          "location_id": "dustfall_outskirts",
          "location_name": "Dustfall Outskirts",
          "turn": 12
        },
        "name": "Old Man Harker",
        "notes": "clinging to rider's waist",
        "presence": "present",
        "title": "Victim"
      },
      "saloon_patrons": {
        "bio": "A small group of locals huddled over drinks in the dim light. They are wary of strangers and maintain a watchful silence.",
        "first_seen_turn": 0,
        "last_seen": {
          "location_id": "assay_office",
          "location_name": "Assay Office",
          "turn": 4
        },
        "name": "Saloon Patrons",
        "presence": "known"
      },
      "silas_thorne": {
        "bio": "A stern-faced veteran with eyes as hard and unimpressed as his demeanor. Speaks with a voice like grinding gravel and maintains a no-nonsense, bureaucratic attitude.",
        "first_seen_turn": 4,
        "last_seen": {
          "location_id": "general_store",
          "location_name": "General Store",
          "turn": 8
        },
        "name": "Silas Thorne",
        "presence": "known",
        "title": "Sheriff's Officer"
      },
      "tough_a": {
        "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
        "bond": null,
        "fear": null,
        "last_seen": {
          "location_id": "red_canyon_cliffs",
          "location_name": "Red Canyon Cliffs",
          "turn": 11
        },
        "leverage": null,
        "motivation": null,
        "name": "Bald Tough",
        "presence": "known",
        "title": "Road thug"
      },
      "tough_b": {
        "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
        "bond": null,
        "fear": null,
        "last_seen": {
          "location_id": "red_canyon_cliffs",
          "location_name": "Red Canyon Cliffs",
          "turn": 11
        },
        "leverage": null,
        "motivation": null,
        "name": "Scarred Tough",
        "presence": "known",
        "title": "Road thug"
      }
    }
  },
  "inventory": [
    {
      "aliases": [],
      "amount": 440,
      "id": "credits",
      "name": "Credits",
      "notes": "Common coin, accepted at any inn or stall on the merchant road."
    },
    {
      "aliases": [],
      "amount": 1,
      "id": "iron_dagger",
      "name": "Iron dagger",
      "notes": "Plain crossguard, edge worn from honing. Belt-carried."
    },
    {
      "aliases": [],
      "amount": 3,
      "id": "bandages",
      "name": "Linen bandages",
      "notes": "Three rolls. Field-grade \u2014 won't replace a healer."
    },
    {
      "aliases": [
        "cloak",
        "travel cloak"
      ],
      "amount": 1,
      "id": "traveler_cloak",
      "name": "Traveler's cloak",
      "notes": "Oiled wool, road-stained, hood deep enough to hide a face."
    },
    {
      "aliases": [],
      "amount": 1,
      "id": "brass_key",
      "name": "Brass key",
      "notes": "A small brass key Halden gave you with the ledger."
    },
    {
      "amount": 1,
      "id": "ceramic_mug",
      "name": "Ceramic mug",
      "notes": "chipped"
    },
    {
      "amount": 1,
      "id": "ledger_page",
      "name": "Ledger page",
      "notes": "A discarded scrap of parchment with a frantic signature."
    },
    {
      "amount": 1,
      "id": "hand_drawn_map",
      "name": "Hand-drawn map",
      "notes": "A thick parchment with charcoal markings concentrated near the Red Canyon cliffs."
    },
    {
      "amount": 1,
      "id": "dried_meat",
      "name": "Dried meat",
      "notes": ""
    },
    {
      "amount": 1,
      "id": "water_canteen",
      "name": "Water canteen",
      "notes": ""
    }
  ],
  "location": {
    "description": "The outskirts of a settlement where boarded-up storefronts line the road and flickering lanterns begin to pierce the evening gloom.",
    "id": "dustfall_outskirts",
    "name": "Dustfall Outskirts"
  },
  "meta": {
    "compendium_touch_order": [
      "saloon_patrons",
      "elara_vance",
      "silas_thorne",
      "assay_clerk",
      "tough_a",
      "tough_b",
      "old_man_harker"
    ],
    "consecutive_pressure_turns": 1,
    "game_name": "eval",
    "last_thread_created_turn": 9,
    "model": "",
    "pending_gm_beat": {
      "beat_expires_turn": 14,
      "surface_as": "npc_behavior",
      "type": "pressure"
    },
    "prior_history": [
      "- [T2] The player learns from Elara Vance that caravans are increasingly fleeing the crossing.",
      "- [T3] Elara reveals that Old Man Harker's wagon was found empty near the river crossing, leaving behind his coin pouch.",
      "- [T4] The player discovered a discarded ledger page with a familiar signature near the Assay Office entrance.",
      "- [T5] Silas Thorne informs the player that no official report has been filed for Harker's disappearance.",
      "- [T6] Silas Thorne rebuffs the attempt to obtain a key and threatens the player with arrest for harassment.",
      "- [T7] The player successfully stole a map of Red Canyon from Thorne's desk but was caught in the act.",
      "- [T8] The player enters the general store to buy supplies but is immediately targeted by two aggressive men.",
      "- [T9] The player escaped the thugs in the market and reached the base of the Red Canyon cliffs.",
      "- [T10] The player confronts two suspicious men at a campfire, one of whom appears to be wearing Harker's hat.",
      "- [T11] The player intimidated the thugs and successfully freed Old Man Harker from his bindings in the canyon cave.",
      "- [T12] The player successfully guides a traumatized Harker from the Red Canyon cliffs into the outskirts of Dustfall."
    ],
    "recent_beats": [
      {
        "surface_as": "ambient",
        "turn": 8,
        "type": "breathing_room"
      },
      {
        "surface_as": null,
        "turn": 9,
        "type": null
      },
      {
        "surface_as": "npc_behavior",
        "turn": 10,
        "type": "pressure"
      },
      {
        "surface_as": null,
        "turn": 11,
        "type": null
      },
      {
        "surface_as": "npc_behavior",
        "turn": 12,
        "type": "pressure"
      }
    ],
    "setting_pack": "eval-pack",
    "turn": 12
  },
  "pc": {
    "actions": [
      "Seek medical aid for Harker at the Crossed Keys inn.",
      "Confront Elara Vance about the thugs seen near the canyon.",
      "Search for Caron to settle debts and find information.",
      "Hide Harker in a dark alley to avoid local scrutiny."
    ],
    "bio": "Mid-thirties, broad shoulders, careful with words. Took on a courier contract\nto clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and\na heavier obligation.\n",
    "conditions": [
      {
        "added_turn": 11,
        "description": "The physical strain of guiding a horse through canyon terrain while carrying an extra passenger has left you weary.",
        "id": "exhausted",
        "label": "Exhausted",
        "turns_remaining": 3
      }
    ],
    "drive": "",
    "momentum": 3,
    "name": "Aren Voss",
    "stats": {
      "charisma": 3,
      "dexterity": 3,
      "strength": 3,
      "wits": 2
    },
    "tagline": "Reluctant courier on the merchant road"
  },
  "scene": {
    "location_entered_turn": 11,
    "tagline": "Entering the Dim Streets of Dustfall",
    "tags": [
      "travel",
      "somber",
      "gloaming"
    ],
    "turn_entered": 11,
    "world_state": [
      "Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.",
      "Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.",
      "The road has been quieter than usual this season \u2014 fewer caravans, more independent runners, more opportunists."
    ]
  },
  "schema_version": 1
}
```


---
# Deterministic Signals

## Auto-Checker Failures
| Turn | Assertion | Detail |
|---|---|---|
| 1 | `universal.pacing.consecutive_pressure_tracking` | gm_beat.type='pressure' (pressure type) but consecutive_pressure_turns=0 (expected >= 1) |
| 2 | `universal.conditions.orphan` | conditions with no CONDITION_MODS entry: ['dusty_throat'] |
| 3 | `universal.storytell.actions_quality` | actions has 0 entries (expected 4) |
| 3 | `universal.pacing.consecutive_pressure_tracking` | gm_beat.type='revelation' (not pressure) but consecutive_pressure_turns=2 (expected 0) |
| 3 | `universal.conditions.orphan` | conditions with no CONDITION_MODS entry: ['dusty_throat'] |
| 5 | `universal.pacing.consecutive_pressure_tracking` | gm_beat.type='complication' (pressure type) but consecutive_pressure_turns=0 (expected >= 1) |
| 5 | `universal.storytell.actions_quality` | actions has 0 entries (expected 4) |
| 5 | `universal.pacing.consecutive_pressure_tracking` | gm_beat.type=None (not pressure) but consecutive_pressure_turns=3 (expected 0) |
| 7 | `universal.conditions.orphan` | conditions with no CONDITION_MODS entry: ['rattled'] |
| 9 | `universal.conditions.orphan` | conditions with no CONDITION_MODS entry: ['threatened'] |
| 10 | `universal.pacing.consecutive_pressure_tracking` | gm_beat.type='pressure' (pressure type) but consecutive_pressure_turns=0 (expected >= 1) |
| 10 | `universal.storytell.actions_quality` | actions has 0 entries (expected 4) |
| 10 | `universal.pacing.consecutive_pressure_tracking` | gm_beat.type=None (not pressure) but consecutive_pressure_turns=2 (expected 0) |
| 11 | `universal.pacing.consecutive_pressure_tracking` | gm_beat.type=None (not pressure) but consecutive_pressure_turns=1 (expected 0) |
| 11 | `universal.inventory.remove_existence` | removed non-existent item(s): ['hempen_rope'] |
| 12 | `universal.pacing.consecutive_pressure_tracking` | gm_beat.type='pressure' (pressure type) but consecutive_pressure_turns=0 (expected >= 1) |

## Metrics
| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries | momentum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1289 | 4055 | 3309 | 1848 | 3055 | 0 | 0 | — |
| 2 | 1501 | 4324 | 3615 | 1958 | 3474 | 0 | 0 | — |
| 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 3 | 1587 | 4547 | 3746 | 1974 | 3591 | 0 | 0 | — |
| 4 | 1583 | 4600 | 3768 | 1970 | 3759 | 0 | 0 | — |
| 5 | 1615 | 4721 | 3846 | 2015 | 3936 | 0 | 0 | — |
| 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 6 | 1609 | 4856 | 3915 | 1980 | 3958 | 0 | 0 | — |
| 7 | 1608 | 4920 | 3902 | 2019 | 4073 | 0 | 0 | — |
| 8 | 1601 | 4912 | 3913 | 2028 | 4144 | 0 | 0 | — |
| 9 | 1651 | 5101 | 3909 | 2059 | 4180 | 0 | 0 | — |
| 10 | 1601 | 5101 | 3881 | 2047 | 4184 | 0 | 0 | — |
| 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 11 | 1602 | 5150 | 3937 | 2085 | 4281 | 0 | 0 | — |
| 12 | 1669 | 5115 | 3964 | 2045 | 4246 | 0 | 0 | — |
| 13 | 1629 | 5119 | 3972 | 2121 | 4253 | 0 | 0 | — |

**Scope fallback rate:** N/A (not captured in events.jsonl)
