# Prompts Architecture — template structure, rendering flow

## Template systems

Two entirely separate template systems exist — do not conflate them:

| System | Location | Purpose | Engine |
|---|---|---|---|
| **Prompt templates** | `fablethread/prompts/` (`.j2`) | Render LLM messages (system/user prompts) | Jinja2 via `_render()` in `narrate.py` / `extraction.py` |
| **UI templates** | `fablethread/templates/` (`.html`) | Render browser HTML (sidebars, modals, character sheets) | Jinja2 via FastAPI `_render()` in `server/routes.py` |

## Prompt template hierarchy

### Narrator system prompt (`fablethread/prompts/narrate_system.j2`)

- Restructured into 4-section hierarchy: (1) Task/role, (2) Hard rules (Player Input Is Truth, Inventory, Never Repeat Prior Narration, Fail-Band Outcomes), (3) Behavioral guidance (NPCs merged single section, Style, Pragmatic Interpretation, Pacing, Campaign arc context), (4) Formatting/output (Markdown). Output discipline section removed (narrator emits only prose after ARC UPDATE removal). Dynamic sections (Universe rules, Genre tone) remain at end.
- Beat mechanism tags: narrator reads mechanism tags as creative brief — generates prose grounded in actual NPC fields in the roster. No quote/prose in mechanism tags; narrator generates the prose itself.
- Null-beat fallback: when no GM beat is present, narrate purely from outcome hint and player input — no added pressure or relief beyond what the scene demands
- Anti-repetition: consolidated three scattered rules into a prominent "Never repeat prior narration" section in Hard rules; covers plot/event rehashing and includes self-check instruction
- NPC favoring: soft guidance after NPC BEHAVIOR DRIVERS to favor NPCs with motivation/fear/leverage set and treat empty-driver NPCs as background
- NPC re-use consolidated: three scattered rules (general intro RE-USE, NPC RE-USE section, non-present NPC mentions) merged into one RE-USE section
- Group NPC introduction: when introducing new groups, describe at least one distinguishing feature per individual in the narration (appearance, demeanor, visible trait). The scene extractor captures these into the group's compendium bio.
- Group NPC reintroduction: when an existing group NPC reappears, reference their distinguishing features from the compendium bio rather than collapsing to the generic type. Makes reuse feel like the same people, not any two sailors.

### Narrator user prompt (`fablethread/prompts/narrate_user.j2`)

- Sections reordered by recency: Player Character → Conditions → PC Situation → Inventory → Location → Characters → World State → Immutable Reference → Scene Context → Scene phase → Prior History (renamed from Prior Turns) → Recent Turns → Campaign Arc → This Turn's Result → PLAYER INPUT → directives (most important signal last)
- Beat mechanism tags rendered as creative guidance: mechanism tags tell the narrator WHAT to blend, narrator generates the prose itself grounded in the actual NPC fields in the roster
- Thread rendering code extracted to shared `sections/_thread_list.j2` include (eliminated duplicated for-loop in if/elif branches)
- Renders ALL threads (active + dormant, scene-scoped + arc-scoped) with scope tags and [DORMANT] markers; completed_threads rendered as "### Past Resolutions" section after _arc.j2 include for full narrative continuity
- Impossible action block: when `rules_outcome.impossible=true`, renders `**IMPOSSIBLE:**` fact with reason before the band/no-roll section
- `outcome_hint` replaces `directive` as narrator's scene-motion signal: renders `**Outcome:** hold/advance/transition` with value-specific guidance
- Scene phase display added after Scene Context section: `## Scene phase: {{ state.scene.scene_phase }}` for narrator tone calibration

### Record system prompt (`fablethread/prompts/record_system.j2`)

- Replaces `storytell_system.j2` (deleted in the beat generation split). 4-section hierarchy preserved: (1) Task/role, (2) Hard rules (Output schema, Output discipline, State-presence rule), (3) Behavioral guidance (Actions, Outcome summary, Thread operations, Rules-outcome, World state rules, Latent threads), (4) Campaign arc system. **The GM Beat guidance section is gone** — beat generation moved to World (Step 2d).
- The `gm_beat` field has been removed from the `StorytellerResult` schema; Record no longer emits beats. Thread management (update/resolve/add) and action/outcome_summary generation remain in Record.
- No curtain call logic — thread resolution driven by thread urgency and phase context only.
- **Thread urgency interpretation rules** (I-32): instructs Record to translate narrator portrayal into urgency labels. Escalate to urgent when threat is immediate/imminent, background thread resurfaces, or phase is CLIMAX. Demote to background when thread is faded/distant/past, associated NPC departed, or dormant 6+ turns. CLIMAX phase awareness: at least one thread MUST be urgent in CLIMAX.
- **Matching threads to narration** (I-32): instructs Record to match narration events to thread summaries by people, places, and actions (concrete event-mappable criteria, not abstract implications).

### Record user prompt (`fablethread/prompts/record_user.j2`)

- Replaces `storytell_user.j2` (deleted in the beat generation split). Threads and arc context still render; the prompt is now significantly slimmer — forward-looking sections removed:
  - ~~`pacing_context`~~ — moved to World
  - ~~`candidate_npcs`~~ — moved to World
  - ~~`allowed_beat_types`~~ — moved to World
  - ~~`pending_beat` / `recent_beats`~~ — moved to World
  - ~~`player_intent`~~ — not needed for backward-looking analysis
- Sections retained from original: `scene_phase` (still passed from record.py:93)
- Sections reordered for record's backward-looking scope: arc/threads → world_state → band → scene_phase → prior_history → recent_turns → CURRENT TURN NARRATION

### World system prompt (`fablethread/prompts/world_system.j2`)

- New template added in the beat generation split. Constrained beat-candidate generation instructions: mechanism-only tags (no quote/prose), beat priority order (NPC+NPC → NPC+thread → single NPC → single thread, never environmental), diversity ban (5-beat window: ban types/NPCs/threads appearing 2+ times), phase-beat alignment (`allowed_beat_types` constraint), roll-band guidance, dormant thread revival guidance.
- ~200-250 system tokens, lightweight.

### World user prompt (`fablethread/prompts/world_user.j2`)

- New template. Renders present NPC roster (from compendium, filtered to `presence == 'present'`), active threads, `pacing_context`, `recent_beats`, `allowed_beat_types`, roll band, and the most recent narration. ~1000-2000 user tokens.

### Prepare seed system prompt (`fablethread/prompts/prepare_seed_system.j2`)

- Generation order: World facts → Key locations → Arc origin → PC situation → Campaign arc → Opening scene/NPCs → Inventory (8 steps)
- Schema shows only `SeedState` shape (not full `SeedEnvelope`) — narrative fields (opening_narrative, actions, outcome_summary) are generated separately by narrate_seed
- CompendiumEntry model has explicit motivation/fear/leverage/personality optional string fields alongside existing name/title/bio/presence/notes; seed prompt schema includes `personality` as `archetype_id` (required for named NPCs) alongside `motivation`/`fear`/`leverage`/`bond` as optional strings; seed prompt has tiered field requirements (named NPCs get `personality` + 2+ fields, unnamed NPCs get `bio` only) and a 12-archetype reference table; runtime code uses `tie` (CompendiumNpcUpdate.tie), seed-time model uses `bond` (CompendiumEntry.bond)

### Narrate seed system prompt (`fablethread/prompts/narrate_seed_system.j2`)

- Generates opening_narrative (~700 words, second person, present tense, 3 movements), actions (exactly 4, 7-10 words each), and outcome_summary (one sentence, 10-20 words)
- Receives filtered context: pc (name, tagline, situation), location.name only, arc_origin, arc.objective, present NPCs (name/title/bio/presence), setting_info (genre, universe rules, creative direction)
- NOT passed: location.description, bio, stats, conditions, inventory, world_locations, pool_selection/scene_bundles, compendium.npcs beyond present NPCs
- Opening narrative weaving: pc.situation is ground truth — weave in specific details (unit, theater, chain of command, family ties, residence, reputation) so the player feels their circumstances, not a dossier. Arc_origin as background pressure. Arc objective surfaced through observation, not announcement. Environmental details derived from situation and arc, not a catalog. Present NPCs shown through action/dialogue, not introduction.
- Scene ideal: 1–4 present NPCs; narrative pressure for exits above that (soft guidance only, engine does NOT track or enforce NPC count at runtime — hard cap removed per Phase 01)
- Group NPC bio: must describe individuals in the group with at least one distinguishing feature per person (appearance, demeanor, visible trait). Name stays short with quantity + type; bio carries identity. Prevents generic "Two sailors" with no distinguishing features.

## Shared includes

### NPC roster template (`fablethread/prompts/sections/_npc_roster.j2`)

- Shared include rendered by narrate_user.j2, record_user.j2, extract_scene_user.j2; does NOT render personality block (personality_registry removed from `build_npc_roster()` in I-24)

### Thread list include (`fablethread/prompts/sections/_thread_list.j2`)

- Shared include rendering thread entries with type label, urgency, dormant marker, and summary
- Used by narrate_user.j2 Scene Context section (eliminates duplicated for-loop in if/elif branches)
- Gate block (`**Gate: blocked** — new threads will not be added this turn`) removed — gate is always "allow" after Plan 2, phase-derived `allowed_beat_types` is the gating mechanism

## Latent thread handling in system prompts

- narrate_system.j2: instructs narrator to push players toward latent threads through narration, environmental detail, NPC behaviour — show don't tell (NPC glancing at locked door, torchlight from tunnel, curious sounds); build 4 choices toward discovery; increase pressure for unsurfaced threads
- record_system.j2: instructs record to use dormant thread knowledge when generating actions and outcome_summary — craft situations where dormant threads naturally surface (character's past catching up, long-silent threat stirring); steer player via choices/suggestions/complications without exposing dormant content directly. Note: beat generation is no longer in Record's scope.

## Prompt rendering flow

1. **System prompt rendered** once per pipeline stage (ruling, narrate, scene extract, state extract, record, world) via `_render()` in `narrate.py` / `extraction.py` / `world.py`
2. **User prompt rendered** per turn with live state data (state, recent_turns, pacing_context, etc.)
3. **Shared includes** (`_npc_roster.j2`, `_thread_list.j2`) rendered via Jinja2 `{% include %}`
4. **Messages assembled** into OpenAI-compatible format (system + user messages)
5. **Token budget applied** via `llm_client.trim_messages()` — drops oldest non-system messages when budget exceeded
6. **LLM called** with assembled messages (streaming for narrate, non-streaming for others)

## Prompt-eval system

Fast prompt testing via `ev.py prompt-eval`:
- `cmd_prompt_eval_dump()` — renders prompts (no LLM)
- `cmd_prompt_eval_call()` — renders + LLM + check
- `build_prompt_context()` — builds context dict from `last_turn_state` for prompt rendering (scene, record streams)
- Three inline checkers: `_run_golden_match()`, `_run_prose_quality()`, `_run_extraction_format()`
- Supports `scene` and `record` streams (record replaces the old `storytell` stream key)
- Uses `last_turn_state` (post-turn) as context
