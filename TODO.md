# TODO

## Improvements

### UI / UX

- [ ] **Scene icons** — place small generated icons inside scene boxes (optimize for low generation time) OR Python Pillow for small sprites.
- [ ] **Auto-scroll** — automatically scroll narrative down slowly as the user reads, configurable speed.
- [ ] **Reroll last narration** — button to re-generate the last narration if it gets borked, without changing the rules outcome or state.

### Context & Performance

- [ ] **Model parameter tuning** — separate temperature for narrator vs. extractor; explore `top_p` and other params.
- [ ] **Pre-narrate context step** — load NPC inventories, motivations, and relationships as structured context before narration to better manage context window.
- [ ] **Context window tuning** — adjust number of recent narrations included; experiment with context saving strategies.

### Narrative Quality

- [ ] **Pacing** — story should progress meaningfully between player actions; avoid scenes that stall (e.g. "standing around" when player says "start the trip").
- [ ] **Unpredictability** — introduce randomness (e.g. pre-narration dice rolls) to keep outcomes less predictable.
- [ ] **Weirdness dial** — add a setting that injects strangeness into narration tone and events.
- [ ] **Anti-repetition** — detect and penalize recycling of information the player already knows.

---

## Features

### Mechanics
- [ ] Allow multiple actions in one turn, and roll/skill check for each independently.
- [ ] A condition update parameters, not just add and remove.
- [ ] Scene tag basically not used except for Game Over tag
- [ ] Scene prompt - NPCs probably don't need to be re-omitted each time if already present
- [ ] Narration - default is that allies and friendly relations move with player/are nearby unless removed from scene in narration
- [ ] More pre-made character creation options that add up to ceiling. Maybe generate from a top-level prompts, allow player to change.
- [ ] Rework rules too. Inputs aren't terribly useful or too truncated. Hard to get intention. Irrelevant things, too.
- [ ] Things that are always emitted like the scene and recent_facts domains by rule engine can be omitted from prompt.
- [ ] Nearby locations - list 2-3 locations nearby the player can go to next. Perhaps tie NPCs to locations if it's helpful.
- [ ] **Collapse `mixed`/`boon` bands** — merge the two middle bands into a single `partial` band ("success at a cost") to sharpen narrative outcomes. See `plans/band-collapse.md`.
- [ ] **Momentum track** — add a `momentum` integer (-3..+3) to PC state; increments on success/crit, decrements on fail/setback; exposed to narrator as a pacing signal. See `plans/momentum-track.md`.
- [ ] **Band-differentiated directives by intent_verb** — `build_directive()` should branch on `intent_verb` so a `setback` on `fight` produces a different directive than a `setback` on `persuade`. See `plans/band-collapse.md`.
- [ ] **Remove condition TTL** — delete `CONDITION_TTL_TURNS` engine-side auto-expiry; conditions should only be removed when the extractor sees narrative justification (rest, treatment, resolution). See `plans/condition-overhaul.md`.
- [ ] **Condition→skill feedback loop** — pass the resolved `skill` and `band` from the current `RulesOutcome` into the state extraction prompt so the extractor knows *which skill just failed* when deciding whether to add a condition. See `plans/condition-overhaul.md`.
- [ ] **`recent_events` ID-keyed deduplication** — replace `_fact_in_list` string normalization with stable ID-keyed events; prevents false merges and enables reliable edits. See `plans/recent-events-overhaul.md`.
- [ ] **`scene_pressure` split from `world_state`** — add a `scene_pressure` list to scene state for active threats/timers, separate from permanent `world_state` lore. See `plans/scene-pressure.md`.
- [ ] **New-NPC compendium guarantee** — NPCs in the current `present_npcs` list always get full compendium rows surfaced to the extractor (even if empty), so newly-introduced characters aren't invisible to extraction.

### Quest System

- [ ] **Secondary objectives** — quests get optional secondary objectives; once the primary is completed, failed, or abandoned the quest moves to resolved.
- [ ] **Dynamic objectives** — quest objectives can evolve mid-quest based on story events.
- [ ] **Starting quest stakes** — starting quests tend to be too paperwork-oriented; raise the stakes, make them action-oriented.
- [ ] **Pre-made narrative options** — longer, more action-oriented choices surfaced to the player.

### Characters & NPCs

- [ ] **Character traits** — assign each character a set of traits (positive, negative, quirky/weird) plus relationships to other characters (minimum 2+).
- [ ] **Character avatars** — generate images/avatars for characters.
- [ ] **Physical descriptions** — generate a physical description for every NPC once at introduction; persist in bio.
- [ ] **NPC compendium overhaul** — only inject NPC details when that NPC is present or relevant; inject only the fields needed for the current context (bio, notes, motivations, inventory) rather than the full compendium. Scope injection by domain (scene NPCs get full context; distant/compendium NPCs get summary only).
- [ ] **Silence aging-out announcements** — recent events expiring from context should not be surfaced to the player as in-narrative announcements.

### World & Facts

- [ ] **Top-level narrative prompt** — a global narrative directive that applies across all packs (tone, style, world rules).
- [ ] **Fact rotation strategy** — separate hardcoded/global facts from local/transient ones; evict transient facts first, preserve global canon.

### Prompt Engineering

- [ ] **Intent expansion** — extend the rules/intent call (Call 0) to output domain scope boundaries (`active_domains` / `skip_domains`) and ambiguity flags; wire into extractor and narrator. Improves extraction accuracy by making player intent machine-readable for scoping. See `plans/intent-expansion.md`.
<<<<<<< HEAD
- [ ] **Prompt trimming through pipeline** - State and other pipelines receive a lot of information they really don't need. If it can't be templated, cut it with Python directly to improve accuracy and input tokens. We already do domains but often too many end up going.
=======
- [ ] **Band-scoped extract examples** — pack `ExtractExample` entries should be tagged by outcome band; surface only examples matching the current roll band to the extractor. Improves extraction accuracy for failure/partial states.
>>>>>>> d378ad4e32b005d4e7badf8b9a586fc269228b14

### Inference Infrastructure

- [ ] **Model-agnostic thinking infra** — `apply_thinking` / `strip_thinking` in `llm_client.py` are Qwen3-flavored. Detect dialect from `config.model` or a new `engine_config.thinking_dialect` field; support Gemma 4 chat-template tags, Qwen3 soft-switches, and a generic prompt-prefix fallback. Re-enable for `extract_state` and `extract_progress` only after measuring quality + latency on a fixture set.
- [ ] **Per-stream KV-cache pinning (mlx_lm)** — once system prompts are byte-stable across turns, use `mlx_lm.cache_prompt` to pre-compute one persistent KV cache file per stream system prompt; pass via `--prompt-cache-file`. Estimated 50-80% prefill latency reduction on extract calls.
- [ ] **Multi-slot prefix caching / vLLM future** — track upstream mlx-lm automatic prefix caching; evaluate vLLM with `--enable-prefix-caching` (lacks Apple Silicon support) or SGLang (Mac support landing).

---

## LLM Pipeline

### A — Context Block Labeling
*Templates only. Zero latency. Fixes stale-fact extraction and narration continuity.*

- [ ] Add `PRIOR HISTORY` label wrapper to `_chronicle.j2`
- [ ] Add `RECENT TURNS` label wrapper to `_recent.j2`
- [ ] Add `CURRENT TURN NARRATION` label in `extract_user.j2` around narration input

### F — Compaction Redesign
*New prompt files + Python logic. Fixes fixed-cadence trigger. See `plans/compaction-strategy.md`.*

- [ ] Replace fixed turn-count trigger with token-threshold check
- [ ] Create `compact_system.j2` (preserve/discard rules + output schema)
- [ ] Create `compact_user.j2` (inventory + established_facts + recent turns input)
- [ ] Update engine: archive to chronicle, clear recent_turns, merge new_facts
- [ ] Ensure `_chronicle.j2` renders chronicle entries with `PRIOR HISTORY` label (Plan A)
