# TODO

## Fixes

- [x] **Inventory removal bug** — when removing an item with quantity 1, it should be removed entirely rather than going to 0.
- [x] **Tooltip dismiss** — tooltips should disappear when the cursor leaves the trigger element, not the tooltip itself.
- [x] **Better scrolling** — scroll to bottom when input is submitted, but suppress scroll on extract completing.
- [ ] **Ammo depletion on use** — using a ranged weapon should deplete the corresponding ammo stack in inventory.

---

## Improvements

### UI / UX

- [x] **Pop-up banner** — redesign as a larger, cleaner banner; omit status checks that haven't changed. Have it findable in a drop-down log collapsed by default.
- [x] **Pre-made choice → text box** — selecting a pre-made option inserts it into the input and lets the player append before submitting.
- [x] **NPC current state** — surface NPC state directly below the scene element instead of inside a tooltip.
- [x] **Stop button** — allow the player to cancel an in-progress inference, which resets to where they were before they submitted with same options.
- [ ] **Scene icons** — place small generated icons inside scene boxes (optimize for low generation time) OR Python Pillow for small sprites.
- [ ] **Auto-scroll** — automatically scroll narrative down slowly as the user reads, configurable speed.
- [ ] **Color-coded dice outcomes** — gradient color coding for dice bands (crit fail → crit success) instead of discrete colors.
- [ ] **Quest objective tooltips** — hover tooltips on quest objectives showing status, progress, and related context.
- [ ] **Reroll last narration** — button to re-generate the last narration if it gets borked, without changing the rules outcome or state.
- [ ] **Human-readable event logs** — turn events.jsonl and other structured data into a running, browsable log in the UI.

### Context & Performance

- [x] **Inference timestamps** — show time-taken for narration and extraction at the end of each respective output.
- [x] **Expanded metrics** — include token in/out counts for narrate and extract alongside timers.
- [x] **Pre-narrate rules step** — Call 0 (rules/intent) classifies player intent before narration.
- [ ] **Model parameter tuning** — separate temperature for narrator vs. extractor; explore `top_p` and other params.
- [ ] **Pre-narrate context step** — load NPC inventories, motivations, and relationships as structured context before narration to better manage context window.
- [ ] **Context window tuning** — adjust number of recent narrations included; experiment with context saving strategies.
- [ ] **Multi-call extraction** — explore breaking extraction into multiple focused calls for improved accuracy.

### Narrative Quality

- [x] **Established facts flavor** — facts should reflect *this* world specifically: less genre trope, more quirky, story-specific detail.
- [x] **Ephemeral vs. persistent facts** — prompt guidance reserves facts for long-term conditions and permanent effects; temporary events left out.
- [x] **Fact duplication reduction** — consolidation rule prevents near-duplicate facts; aim for 0-2 net-new facts per turn.
- [ ] **Pacing** — story should progress meaningfully between player actions; avoid scenes that stall (e.g. "standing around" when player says "start the trip").
- [ ] **Unpredictability** — introduce randomness (e.g. pre-narration dice rolls) to keep outcomes less predictable.
- [ ] **Weirdness dial** — add a setting that injects strangeness into narration tone and events.
- [ ] **Anti-repetition** — detect and penalize recycling of information the player already knows.
- [ ] **Prompt cleanup** — clean up narrate and extract templates; extract especially should tie top-level directives to specific field guidance.

---

## Features

### Quest System

- [ ] **Secondary objectives** — quests get optional secondary objectives; once the primary is completed, failed, or abandoned the quest moves to resolved.
- [ ] **Dynamic objectives** — quest objectives can evolve mid-quest based on story events.
- [ ] **Starting quest stakes** — starting quests tend to be too paperwork-oriented; raise the stakes, make them action-oriented.

### Characters & NPCs

- [ ] **Character traits** — assign each character a set of traits (positive, negative, quirky/weird) plus relationships to other characters.
- [ ] **Character avatars** — generate images/avatars for characters.
- [ ] **NPC context** — include NPC inventories, motivations, and inter-character relations as structured context for narration.
- [ ] **Character creation** — character creation screen on top of world/genre selection.

### World & Facts

- [ ] **Top-level narrative prompt** — a global narrative directive that applies across all packs (tone, style, world rules).
- [ ] **Fact rotation strategy** — separate hardcoded/global facts from local/transient ones; evict transient facts first, preserve global canon.

### Rules & Mechanics

- [x] **Mortal stakes** — PC death is real, game over is possible with game over popup and new game button.
- [x] **Conditions in roll outcome** — condition modifiers shown in dice math breakdown.
- [x] **Stat tooltips** — hover tooltips on the six stat tags showing what each covers.
- [x] **Player title/tagline** — PC has a tagline (role and defining trait) shown in sidebar.
- [x] **Dark choices allowed** — player may freely pursue cruel, immoral, or evil actions without narrator moralizing.
- [x] **Weapons require ammo** — adding a ranged weapon must include a matching ammo stack.
- [x] **Max 2 inventory items/turn** — hard cap on new inventory additions per turn.
- [x] **Conditions cap** — max 5 active conditions; no duplicates; least relevant dropped when full.

### Prompt Engineering
- [x] **Bolding rules** — bold only on first introduction of NPCs, inventory items, quest targets; not every mention.
- [x] **Highlights scoped** — bolding limited to inventory, NPCs, and quest objects only.
- [x] **Spatial position in NPC notes** — positional prefix in notes when spatial arrangement matters.
- [x] **Lower quest barrier** — when no active quests, lower the bar for what counts as a quest.
- [x] **Real places from lore** — use real locations from the setting's lore or real world.
- [x] **More recent narrations** — window_turns increased to 6 for richer context.
- [x] **First narration bolding** — bolding rules apply from the first scene onward.
- [ ] **World gen no streaming** — disable streaming for world generation calls (generate_seed) since it's a single JSON output.

### Tooling

- [ ] **QA / diagnostics** — tooling for measuring and surfacing latency and narrative quality metrics.

---

## LLM Pipeline Accuracy

Full plans: [plans/llm-pipeline-accuracy.md](./plans/llm-pipeline-accuracy.md) · Checklist: [plans/llm-pipeline-todos.md](./plans/llm-pipeline-todos.md)

### A — Context Block Labeling
*Templates only. Zero latency. Fixes stale-fact extraction and narration continuity.*

- [ ] Add `PRIOR HISTORY` label wrapper to `_chronicle.j2`
- [ ] Add `RECENT TURNS` label wrapper to `_recent.j2`
- [ ] Add `CURRENT TURN NARRATION` label in `extract_user.j2` around narration input

### B — Reasoning Field in Extractor
*Schema + 2-line Python strip. ~30–60 extra output tokens. Fixes quest/inventory misclassification.*

- [x] Add `_reasoning` as first key in `extract_system.j2` schema with field guidance
- [x] Add `failed` as second key (populated by Plan C)
- [x] Verify `actions` is last key in schema definition order (removed — moved to narrate)
- [x] Strip `_reasoning` in Python engine before applying delta

### C — Scope Boundaries via Rules Call
*Extends existing rules call output. Fixes spurious cross-domain extraction and silent precondition failures.*

- [x] Add `scope` object to `rules_system.j2` output schema
- [x] Add domain-mapping guidance to `rules_system.j2`
- [x] Inject scope block at top of `extract_user.j2` from `rules_outcome.scope`
- [x] Add SKIP DOMAINS enforcement instruction to `extract_system.j2`
- [x] Log `failed` in engine; pass to next narration as `last_turn_failed`

### D — Active-Domain State Slicing
*Python engine only. Depends on C. Reduces extractor input tokens on simple turns.*

- [x] Build `build_state_slice()` helper in Python engine
- [x] Pass sliced state into `extract_user.j2` instead of full state
- [x] Keep full state in `narrate_system.j2`

### E — `actions` Generation Placement
*Abandoned — actions stay in extractor. Narrator outputs prose only; extractor outputs structured data (state_delta + actions).*

- [x] Remove ACTIONS_JSON marker from narrate call
- [x] Restore actions to extract_system.j2 schema with guidance to draw from current narration only
- [x] Add actions field to ExtractResult model

### F — Compaction Redesign
*New prompt files + Python logic. Fixes fixed-cadence trigger.*

- [ ] Replace fixed turn-count trigger with token-threshold check
- [ ] Create `compact_system.j2` (preserve/discard rules + output schema)
- [ ] Create `compact_user.j2` (inventory + established_facts + recent turns input)
- [ ] Update engine: archive to chronicle, clear recent_turns, merge new_facts
- [ ] Ensure `_chronicle.j2` renders chronicle entries with `PRIOR HISTORY` label (Plan A)
