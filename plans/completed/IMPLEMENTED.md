# IMPLEMENTED

Completed work extracted from TODO. Moved here to keep TODO focused on what's left.

---

## Fixes

- **Inventory removal bug** — when removing an item with quantity 1, it is removed entirely rather than going to 0.
- **Tooltip dismiss** — tooltips disappear when the cursor leaves the trigger element, not the tooltip itself.
- **Better scrolling** — scroll to bottom when input is submitted; scroll suppressed on extract completing.

---

## UI / UX

- **Pop-up banner** — redesigned as a larger, cleaner banner; omits status checks that haven't changed; findable in a drop-down log collapsed by default.
- **Pre-made choice → text box** — selecting a pre-made option inserts it into the input and lets the player append before submitting.
- **NPC current state** — NPC state surfaced directly below the scene element instead of inside a tooltip.
- **Stop button** — player can cancel an in-progress inference, resetting to the pre-submit state with same options.
- **Inference timestamps** — time-taken for narration and extraction shown at end of each respective output.
- **Expanded metrics** — token in/out counts for narrate and extract alongside timers.

---

## Context & Performance

- **Pre-narrate rules step** — Call 0 (rules/intent) classifies player intent before narration.

---

## Narrative Quality

- **Established facts flavor** — facts reflect this world specifically; less genre trope, more story-specific detail.
- **Ephemeral vs. persistent facts** — prompt guidance reserves facts for long-term conditions and permanent effects; temporary events excluded.
- **Fact duplication reduction** — consolidation rule prevents near-duplicate facts; 0-2 net-new facts per turn.

---

## Rules & Mechanics

- **Mortal stakes** — PC death is real; game over popup with new game button.
- **Conditions in roll outcome** — condition modifiers shown in dice math breakdown.
- **Stat tooltips** — hover tooltips on the six stat tags showing what each covers.
- **Player title/tagline** — PC has a tagline (role and defining trait) shown in sidebar.
- **Dark choices allowed** — player may freely pursue cruel, immoral, or evil actions without narrator moralizing.
- **Weapons require ammo** — adding a ranged weapon must include a matching ammo stack.
- **Max 2 inventory items/turn** — hard cap on new inventory additions per turn.
- **Conditions cap** — max 5 active conditions; no duplicates; least relevant dropped when full.

---

## Prompt Engineering

- **Bolding rules** — bold only on first introduction of NPCs, inventory items, quest targets; not every mention.
- **Highlights scoped** — bolding limited to inventory, NPCs, and quest objects only.
- **Spatial position in NPC notes** — positional prefix in notes when spatial arrangement matters.
- **Lower quest barrier** — when no active quests, lower the bar for what counts as a quest.
- **Real places from lore** — real locations from the setting's lore or real world used (not faker placeholders).
- **More recent narrations** — `window_turns` increased to 6 for richer context.
- **First narration bolding** — bolding rules apply from the first scene onward.

---

## LLM Pipeline (Plans B / C / D / E)

### B — Reasoning Field in Extractor
- Added `_reasoning` as first key in `extract_system.j2` schema with field guidance.
- Added `failed` as second key (populated by Plan C).
- Verified `actions` is last key in schema definition order (removed — moved to narrate).
- Strip `_reasoning` in Python engine before applying delta.

### C — Scope Boundaries via Rules Call
- Added `scope` object to `rules_system.j2` output schema.
- Added domain-mapping guidance to `rules_system.j2`.
- Injected scope block at top of `extract_user.j2` from `rules_outcome.scope`.
- Added SKIP DOMAINS enforcement instruction to `extract_system.j2`.
- Log `failed` in engine; pass to next narration as `last_turn_failed`.

### D — Active-Domain State Slicing
- Built `build_state_slice()` helper in Python engine.
- Pass sliced state into `extract_user.j2` instead of full state.
- Full state kept in `narrate_system.j2`.

### E — `actions` Generation Placement *(Abandoned — actions stay in extractor)*
- Removed ACTIONS_JSON marker from narrate call.
- Restored actions to `extract_system.j2` schema with guidance to draw from current narration only.
- Added actions field to `ExtractResult` model.

---

## Features (Completed)

- **Character creation** — character creation screen on top of world/genre selection.
- **Extraction stream split (Plan G)** — extraction split into scene / state / progress streams with skip logic, feature flag, and per-domain context builders.
- **Turn Inspector Debug UI (Plan H)** — FastAPI debug server + single-page UI with three-column layout; feature-flagged; reads events.jsonl.
- **Extractor prompt redesign** — extractor prompt cleaned up; top-level directives tied to specific field guidance.

---

*Completed plans archived in `plans/completed/`.*
