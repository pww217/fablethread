# Prompts Architecture — template structure, rendering flow

## Template systems

Two entirely separate template systems exist — do not conflate them:

| System | Location | Purpose | Engine |
|---|---|---|---|
| **Prompt templates** | `ccya/prompts/` (`.j2`) | Render LLM messages (system/user prompts) | Jinja2 via `_render()` in `narrate.py` / `extraction.py` |
| **UI templates** | `ccya/templates/` (`.html`) | Render browser HTML (sidebars, modals, character sheets) | Jinja2 via FastAPI `_render()` in `server/routes.py` |

## Prompt template hierarchy

### Narrator system prompt (`ccya/prompts/narrate_system.j2`)

- Restructured into 4-section hierarchy: (1) Task/role, (2) Hard rules (Player Input Is Truth, Inventory, Never Repeat Prior Narration, Fail-Band Outcomes), (3) Behavioral guidance (NPCs merged single section, Style, Pragmatic Interpretation, Pacing, Campaign arc context), (4) Formatting/output (Markdown). Output discipline section removed (narrator emits only prose after ARC UPDATE removal). Dynamic sections (Universe rules, Genre tone) remain at end.
- ARC UPDATE section (former lines 70-87) removed entirely — narrator never emits the block, extraction code removed from turn.py
- Directives section: removed Combat Fatigue, Location Pressure, Location Imperative definitions; added Scene Pressure (≥3 effective scene age, intermediate signal to wind down or shift focus) and Scene Imperative (≥5 effective scene age, high-priority directive forcing story advancement); new directives use scene-level language reflecting single-age signal from collapsed _compute_ages()
- Null-beat fallback: when no GM beat is present, narrate purely from outcome hint and player input — no added pressure or relief beyond what the scene demands
- Anti-repetition: consolidated three scattered rules into a prominent "Never repeat prior narration" section in Hard rules; covers plot/event rehashing and includes self-check instruction
- NPC favoring: soft guidance after NPC BEHAVIOR DRIVERS to favor NPCs with motivation/fear/leverage set and treat empty-driver NPCs as background
- NPC re-use consolidated: three scattered rules (general intro RE-USE, NPC RE-USE section, non-present NPC mentions) merged into one RE-USE section
- Group NPC introduction: when introducing new groups, describe at least one distinguishing feature per individual in the narration (appearance, demeanor, visible trait). The scene extractor captures these into the group's compendium bio.
- Group NPC reintroduction: when an existing group NPC reappears, reference their distinguishing features from the compendium bio rather than collapsing to the generic type. Makes reuse feel like the same people, not any two sailors.

### Narrator user prompt (`ccya/prompts/narrate_user.j2`)

- Sections reordered by recency: Player Character → Inventory → Location → Characters → World State → Immutable Reference → Scene Context → Scene phase → Prior History (renamed from Prior Turns) → Recent Turns → Campaign Arc → This Turn's Result → PLAYER INPUT → directives (most important signal last)
- Thread rendering code extracted to shared `sections/_thread_list.j2` include (eliminated duplicated for-loop in if/elif branches)
- Renders ALL threads (active + dormant, scene-scoped + arc-scoped) with scope tags and [DORMANT] markers; completed_threads rendered as "### Past Resolutions" section after _arc.j2 include for full narrative continuity
- Impossible action block: when `rules_outcome.impossible=true`, renders `**IMPOSSIBLE:**` fact with reason before the band/no-roll section
- `outcome_hint` replaces `directive` as narrator's scene-motion signal: renders `**Outcome:** hold/advance/transition` with value-specific guidance
- Scene phase display added after Scene Context section: `## Scene phase: {{ state.scene.scene_phase }}` for narrator tone calibration

### Storyteller system prompt (`ccya/prompts/storytell_system.j2`)

- Restructured into 4-section hierarchy: (1) Task/role, (2) Hard rules (Output schema, Output discipline, State-presence rule), (3) Behavioral guidance (Actions, Outcome summary, Thread operations, Rules-outcome, World state rules, Latent threads, PacingContext), (4) GM Beat guidance (longest section, placed last for recency benefit)
- Contradiction fixed: "empty arrays for fields with no changes" removed from task line (conflicted with Output discipline "omit null or empty fields")
- Duplicate beat diversity rules (Beat type diversity + Crisis-aware beat selection) coalesced into single Crisis-aware beat diversity section
- Phase→beat constraints table replaces old directive→beat mapping: phase table (SETUP/RISING/CLIMAX/RESOLUTION/BREATHER) with allowed beat types per phase, driven by `scene_phase` and `allowed_beat_types` context variables. Roll-band table becomes secondary constraint. Phase overrides roll band.
- Choice momentum section added: instructs LLM to escalate from prior turns, connect pacing context to choice urgency, and avoid passive options

### Storyteller user prompt (`ccya/prompts/storytell_user.j2`)

- Renders all threads in unified list with scope tags ([SCENE]/[ARC]), dormant markers for threads with dormant=True, urgency levels; completed_threads rendered via `_arc.j2` include as "### Completed Threads" section (for continuity — do not re-open resolved tensions)
- Sections reordered by recency: inventory → conditions → characters → location → arc/threads → past resolutions → world_state → pacing_context → scene_phase → rules_outcome → player_intent → CURRENT TURN NARRATION (most important signal last)
- `pacing_context` section no longer renders `gate` field (always "allow" after Plan 2); `scene_phase` and `allowed_beat_types` rendered as separate section after pacing_context

### Seed system prompt (`ccya/prompts/generate_seed_system.j2`)

- Generation order: PC → World state → Campaign arc → Opening scene/NPCs → Inventory (5 steps)
- Opening narrative instructions: weave world state facts naturally (show effect, not statement), show NPC personal ties through action/dialogue (not exposition), reference compendium NPCs naturally in narration (phone call, rumor, memory)
- CompendiumEntry model has explicit motivation/fear/leverage/personality optional string fields alongside existing name/title/bio/bond/presence/notes; seed prompt schema includes `personality` as `archetype_id` (required for named NPCs) alongside `motivation`/`fear`/`leverage`/`bond` as optional strings; seed prompt has tiered field requirements (named NPCs get `personality` + 2+ fields, unnamed NPCs get `bio` only) and a 12-archetype reference table
- Scene ideal: 1–4 present NPCs; narrative pressure for exits above that (soft guidance only, engine does NOT track or enforce NPC count at runtime — hard cap removed per Phase 01)
- Group NPC bio: must describe individuals in the group with at least one distinguishing feature per person (appearance, demeanor, visible trait). Name stays short with quantity + type; bio carries identity. Prevents generic "Two sailors" with no distinguishing features.

## Shared includes

### NPC roster template (`ccya/prompts/sections/_npc_roster.j2`)

- Shared include rendered by narrate_user.j2, storytell_user.j2, extract_scene_user.j2; renders personality block (`| personality: **Label** (traits). Speech: hint.`) when `build_npc_roster()` resolves archetype data via `personality_registry` parameter; backward compatible — old saves without `personality` key render without the block

### Thread list include (`ccya/prompts/sections/_thread_list.j2`)

- Shared include rendering thread entries with type label, urgency, dormant marker, and summary
- Used by narrate_user.j2 Scene Context section (eliminates duplicated for-loop in if/elif branches)
- Gate block (`**Gate: blocked** — new threads will not be added this turn`) removed — gate is always "allow" after Plan 2, phase-derived `allowed_beat_types` is the gating mechanism

## Latent thread handling in system prompts

- narrate_system.j2: instructs narrator to push players toward latent threads through narration, environmental detail, NPC behaviour — show don't tell (NPC glancing at locked door, torchlight from tunnel, curious sounds); build 4 choices toward discovery; increase pressure for unsurfaced threads
- storytell_system.j2: instructs storyteller to use dormant thread knowledge when generating suggestions and beats — craft situations where dormant threads naturally surface (character's past catching up, long-silent threat stirring); steer player via choices/suggestions/complications without exposing dormant content directly

## Prompt rendering flow

1. **System prompt rendered** once per pipeline stage (ruling, narrate, scene extract, state extract, storytell) via `_render()` in `narrate.py` / `extraction.py`
2. **User prompt rendered** per turn with live state data (state, recent_turns, pacing_context, etc.)
3. **Shared includes** (`_npc_roster.j2`, `_thread_list.j2`) rendered via Jinja2 `{% include %}`
4. **Messages assembled** into OpenAI-compatible format (system + user messages)
5. **Token budget applied** via `llm_client.trim_messages()` — drops oldest non-system messages when budget exceeded
6. **LLM called** with assembled messages (streaming for narrate, non-streaming for others)

## Prompt-eval system

Fast prompt testing via `ev.py prompt-eval`:
- `cmd_prompt_eval_dump()` — renders prompts (no LLM)
- `cmd_prompt_eval_call()` — renders + LLM + check
- `build_prompt_context()` — builds context dict from `state_snapshot` for prompt rendering (scene, storytell streams)
- Three inline checkers: `_run_golden_match()`, `_run_prose_quality()`, `_run_extraction_format()`
- Supports `scene` and `storytell` streams
- Uses `state_snapshot` (post-turn) as context
