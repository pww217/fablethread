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
