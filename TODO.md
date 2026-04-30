# TODO

## Fixes

- [x] **Inventory removal bug** — when removing an item with quantity 1, it should be removed entirely rather than going to 0. This is a common bug with item # I've seen.
- [x] **Tooltip dismiss** — tooltips should disappear when the cursor leaves the trigger element, not the tooltip itself
- [x] **Better scrolling** — scroll to bottom when input is submitted, but suppress scroll on extract (second inference) completing

---

## Improvements

### UI / UX

- [x] **Pop-up banner** — redesign as a larger, cleaner banner; omit status checks that haven't changed. Have it findable in a drop-down log collapsed by default. 
- [x] **Pre-made choice → text box** — selecting a pre-made option inserts it into the input and lets the player append before submitting
- [x] **NPC current state** — surface NPC state directly below the scene element instead of inside a tooltip
- [x] **Stop button** — allow the player to cancel an in-progress inference, which resets to where they were before they submitted with same options.

### Context & Performance

- [x] **Inference timestamps** — show time-taken for narration and extraction at the end of each respective output
- [x] **Expanded metrics** — include token in/out counts for narrate (and extract) alongside timer for each in narrative window.
- [ ] **Model parameter tuning** — separate temperature for narrator vs. extractor; explore `top_p` and other params
- [ ] **Pre-narrate context step** — load rules engine, NPC inventories, motivations, and relationships before narration to better manage context window

### Narrative Quality

- [ ] **Pacing** — story should progress meaningfully between player actions; avoid scenes that stall (e.g. "standing around waiting to start" when the player says "start the trip")
- [x] **Established facts flavor** — facts should reflect *this* world specifically: less genre trope, more quirky, story-specific detail
- [ ] **Ephemeral vs. persistent facts** — recent or in-progress events don't need to be stored as facts; reserve facts for long-term conditions, permanent effects, and things that matter to the main character
- [ ] **Unpredictability** — introduce randomness (e.g. pre-narration dice rolls) to keep outcomes less predictable
- [ ] **Weirdness** — add a weirdness dial (setting) that injects strangeness into narration tone and events
- [ ] **Anti-repetition** — detect and penalize recycling of information the player already knows
- [ ] **Anti-repetition** - Clean up prompt templates for narrate and extract - extract especially should tie top level direct to specific fields below.
---

## Features

### Quest System

- [ ] **Secondary objectives** — quests get optional secondary objectives; once the primary is completed, failed, or abandoned the quest moves to resolved
- [ ] **Dynamic objectives** — quest objectives can evolve mid-quest based on story events

### Characters & NPCs

- [ ] **Character traits** — assign each character a set of traits (positive, negative, and quirky/weird) plus relationships to other characters
- [ ] **Character avatars** — generate images/avatars for characters
- [ ] **NPC context** — include NPC inventories, motivations, and inter-character relations as structured context for narration

### World Building

- [ ] **Top-level narrative prompt** — a global narrative directive that applies across all packs (tone, style, world rules)

### Scene

- [ ] **Scene icons** — place small generated icons inside scene boxes (optimize for low generation time) OR Python Pillow for small sprites (convert natural language to parameters?)
- [ ] **Auto Scroll** - Automatically move the text down slowly as the user reads, configurable

### Tooling

- [ ] **QA / diagnostics** — tooling for measuring and surfacing latency and narrative quality metrics
