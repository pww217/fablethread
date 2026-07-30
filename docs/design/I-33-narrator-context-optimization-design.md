# I-33: Optimize Narrator Context — Design Document

> **Status:** reviewed
> **Related tickets:**
> - [I-33: Optimize narrator context](../../roadmap/improvements/I-33-optimize-narrator-context-world-inspiration-arc.md)

## Problem

Two narrator systems have asymmetric, incomplete context from the world pack, leading to under-informed narration:

**Seed narrator** (`narrate_seed()`, turn 0) generates ~700 words of opening prose but lacks:
- `world_facts` (3-8 baseline canon strings) — no world anchoring
- `narrator_rules` (up to 12 tone rules) — no genre tone consistency
- `factions` (up to 6 power groups) — no world structure awareness
- Arc threads/urgency — only receives `arc.objective` string, cannot reference active motivations or campaign pressure

**Regular narrator** (`_narrate_messages()`, per-turn) receives richer context but lacks:
- `inspiration` blocks (`pc`/`npcs`/`inventory` creative direction from `pack.scenario.inspiration`) — no creative direction anchoring for beat generation and action choices
- `world_facts` as explicit canon — only available via `world_state` which degrades as LLM-added facts accumulate

**World state degradation:** Baseline `world_facts` are injected as `WorldStateFact(permanent=True)` at seed time (`seed.py:372-379`), but the `_world_state.j2` template renders all facts equally with no distinction between baseline canon and LLM-added facts. The narrator's world anchoring weakens over time as the fact list grows.

**Specificity requirements (2026-07-26 playtest):** The narrator underutilizes opportunities for world-building detail. Characters feel lifeless because they lack concrete motivations. Factions and entities are described at the abstraction level rather than through individual character goals. This is a prompt quality issue, not a context availability issue, but it compounds the context gaps above.

## Firm Decisions

1. **Seed narrator receives `world_facts`, `narrator_rules`, `factions`, and arc threads** — rationale: the opening narrator must anchor the player in the world's canon, tone, power structure, and active motivations. Without these, opening prose feels generic and disconnected from the campaign's stakes. Truncated to 5 facts, 8 rules, 4 factions, 5 threads to minimize token bloat.

2. **Regular narrator receives `inspiration` blocks and explicit `world_facts`** — rationale: per-turn narration and beat generation should be grounded in the world's creative direction (what kind of PC/NPCs/inventory the world expects) and always have baseline canon visible, not just what survived into `world_state`. Truncated to 5 facts to minimize token bloat.

3. **`world_facts` are injected explicitly into both narrator contexts, separate from `world_state`** — rationale: baseline canon must remain visible even as `world_state` accumulates LLM-added facts. This prevents the anchoring degradation problem.

4. **Arc threads are passed to seed narrator with urgency and summary (non-dormant only)** — rationale: the opening should reference active motivations and campaign pressure, not just the end goal. Threads carry urgency signals that the seed narrator can use to prioritize which threads to surface. Only non-dormant threads are passed to minimize token bloat.

5. **No changes to `WorldState` or `Pack` models** — rationale: all required data already exists in `pack.scenario` (`world_facts`, `narrator_rules`, `world_rules`, `factions`, `inspiration`) and `state.long_term_objective.threads`. This is purely a context-routing change, not a schema change.

6. **`_world_state.j2` template is unchanged** — rationale: the template renders all facts equally by design. The fix is to inject `world_facts` separately in the prompt, not to modify the template to distinguish baseline vs LLM-added facts. This keeps the template simple and avoids coupling it to seed-time logic.

7. **Token budget constraints enforced via truncation** — rationale: added context increases prompt length. Seed narrator adds ~480-820 tokens (one-time at turn 0). Regular narrator adds ~250-450 tokens per turn. Truncation limits (5 facts, 8 rules, 4 factions, 5 threads) prevent bloat while preserving essential context.

## Design Principles

- **Baseline canon is always visible:** `world_facts` are injected directly into narrator prompts, not just via `world_state`. This ensures the narrator always has the pack's canonical facts, even if `world_state` is overwritten or diluted over time.

- **Each narrator gets what its role requires:** The seed narrator's job is to establish the world and anchor the player in the campaign's stakes. The regular narrator's job is to generate per-turn prose grounded in the world's creative direction. Each receives the context it needs for its specific role, not a uniform context dump.

- **No backwards compatibility:** Old saves and prompts are not migrated. The new context routing applies to all new games and turns going forward.

- **Token budget awareness:** Adding context increases prompt length. The design must stay within the token budget enforced by `trim_messages()` (`narrate.py:550`, `seed.py:550`). If prompts exceed the budget, the oldest non-system messages are dropped. The design assumes the added context is small enough to fit within typical budgets, but this must be verified during implementation.

## Target State

### Model Changes

None. All required data already exists in `pack.scenario` and `state.long_term_objective`.

### Prompt Changes

#### Seed Narrator (`narrate_seed_system.j2`)

**Current context** (from `seed.py:499-514`):
- `pc` (name, tagline, situation)
- `location` (name only)
- `arc_origin` (world-level context)
- `arc.objective` (goal string only)
- `compendium_npcs` (present ones only)
- `setting_info` (genre, universe_rules, creative_direction/inspiration)
- `pool_selection` (archetypes/bundles)

**Added context:**
- `world_facts` (max 5 strings) — rendered as a "World Canon" section after "Setting constraints"
- `narrator_rules` (max 8 strings) — rendered as "Genre Tone" section, same format as `narrate_system.j2`
- `factions` (max 4 Faction objects) — rendered as "Known Factions" section, same format as `narrate_user.j2`
- `arc_threads` (max 5 non-dormant thread dicts with `summary`, `urgency`, `type`) — rendered as "Active Threads" section after arc objective

**Template changes:**
- Add `{% if world_facts %}## World Canon{% for fact in world_facts %}- {{ fact }}{% endfor %}{% endif %}` after "Setting constraints" section
- Add `{% if narrator_rules %}## Genre Tone{% for rule in narrator_rules %}- {{ rule }}{% endfor %}{% endif %}` after world canon
- Add `{% if factions %}## Known Factions{% for f in factions %}- **{{ f.name }}** ({{ f.disposition }}){% endfor %}{% endif %}` after genre tone
- Add `{% if arc_threads %}### Active Threads{% for t in arc_threads %}- [{{ t.type }}{% if t.urgency %} - {{ t.urgency }}{% endif %}] {{ t.summary }}{% endfor %}{% endif %}` after arc objective

**Truncation in engine:**
- In `_build_narrate_seed_messages()`, truncate: `world_facts[:5]`, `narrator_rules[:8]`, `factions[:4]`, `arc_threads[:5]`

#### Regular Narrator (`narrate_user.j2`)

**Current context** (from `narrate.py:99-124`):
- Full `state`, `pc_situation`, `prior_history`, `recent_turns[-1:]`, `rules_outcome`, `conditions`, `inventory`, `location`, `npc_name_pool`, `npc_roster`, `narrator_rules` (system prompt), `world_rules` (system prompt), `world_factions`, `pending_gm_beat`, `pacing_context`, `current_objective` (arc with threads including urgency), `arc_pressure_score`, `arc_hint_text`, `resolved_arcs`, `ages`, `pc_allegiance`, `turn_no`, `scene`

**Added context:**
- `inspiration` (Inspiration object with `pc`, `npcs`, `inventory` strings) — rendered as "Creative Direction" section after "Immutable Reference"
- `world_facts` (max 5 strings) — rendered as "World Canon" section after "Immutable Reference" and before "Creative Direction"

**Template changes:**
- Add `{% if world_facts %}## World Canon{% for fact in world_facts %}- {{ fact }}{% endfor %}{% endif %}` after "Immutable Reference" section
- Add `{% if inspiration %}## Creative Direction (guidance only — do not borrow phrasing){% if inspiration.pc %}### PC\n{{ inspiration.pc }}{% endif %}{% if inspiration.npcs %}### NPCs\n{{ inspiration.npcs }}{% endif %}{% if inspiration.inventory %}### Inventory\n{{ inspiration.inventory }}{% endif %}{% endif %}` after world canon

**Truncation in engine:**
- In `_narrate_messages()`, truncate: `world_facts[:5]`

**Note:** `inspiration` is already passed to seed narrator via `setting_info.creative_direction`. For the regular narrator, it's passed as a top-level `inspiration` dict.

### Engine Changes

#### `seed.py:_build_narrate_seed_messages()`

**Current** (lines 451-521):
- Extracts `setting_info` from `pack.scenario` (genre, universe_rules, creative_direction)
- Extracts arc data as `{objective: long_term_objective}` only
- Builds context dict with `pc`, `location`, `arc_origin`, `setting_info`, `compendium_npcs`, `arc`, `pool_selection`

**Changes:**
- Extract `world_facts` from `pack.scenario.world_facts` (if present)
- Extract `narrator_rules` from `pack.scenario.narrator_rules` (if present)
- Extract `factions` from `pack.scenario.factions` (if present, convert to list of dicts with `name`, `disposition`)
- Extract arc threads from `seed_state.long_term_objective.threads` as list of dicts with `summary`, `urgency`, `type` (filter out dormant threads)
- Add `world_facts`, `narrator_rules`, `factions`, `arc_threads` to context dict

#### `narrate.py:_narrate_messages()`

**Current** (lines 32-140):
- Receives `narrator_rules`, `world_rules`, `world_factions` as parameters
- Builds `user_ctx` dict with full state context
- Renders `narrate_system.j2` with `narrator_rules`, `world_rules`
- Renders `narrate_user.j2` with `user_ctx`

**Changes:**
- Add `inspiration: Inspiration | None = None` parameter
- Add `world_facts: list[str] | None = None` parameter
- Add `inspiration` and `world_facts` to `user_ctx` dict
- Pass `inspiration` and `world_facts` from caller (`_narrate_setup()`)

#### `turn.py:run_turn()` signature

**Current** (lines 74-88):
- Accepts `pack_name_locales`, `pack_narrator_rules`, `pack_world_rules`, `pack_factions` as optional parameters
- Builds `ctx.packing` dict with these values (lines 113-118)

**Changes:**
- Add `pack_inspiration: Inspiration | None = None` parameter
- Add `pack_world_facts: list[str] | None = None` parameter
- Add `"inspiration": pack_inspiration` and `"world_facts": pack_world_facts` to `ctx.packing` dict (lines 113-118)

#### `server/routes.py:run_turn()` caller

**Current** (lines 262-265):
- Extracts `pack_name_locales`, `pack_narrator_rules`, `pack_world_rules`, `pack_factions` from `_app_mod._active_pack.scenario`
- Passes these to `run_turn()`

**Changes:**
- Extract `pack_inspiration` from `_app_mod._active_pack.scenario.inspiration` (if scenario exists)
- Extract `pack_world_facts` from `_app_mod._active_pack.scenario.world_facts` (if scenario exists)
- Pass these to `run_turn()`

#### `ev/play.py:run_turn()` callers

**Current** (lines 42-84, 464-467, 582-585, 825-828):
- Multiple callers pass `pack_name_locales`, `pack_narrator_rules`, `pack_world_rules`, `pack_factions` to `run_turn()`

**Changes:**
- Update all callers to pass `pack_inspiration` and `pack_world_facts` (extract from pack or pass `None` if not available)

#### `narrate.py:_narrate_setup()`

**Current** (lines 154-254):
- Extracts `narrator_rules`, `world_rules`, `world_factions` from `ctx.packing`
- Calls `_narrate_messages()` with these parameters

**Changes:**
- Extract `inspiration` from `ctx.packing.get("inspiration")` (if present)
- Extract `world_facts` from `ctx.packing.get("world_facts")` (if present)
- Pass `inspiration` and `world_facts` to `_narrate_messages()`

**Prerequisite:** `inspiration` and `world_facts` must be added to `ctx.packing` in `turn.py:113-118` (see `turn.py` changes above).

#### `turn.py:_narrate_phase()`

**Current:** Calls `_narrate_setup()` which builds context from `ctx.packing`. The packing dict is built in `turn.py:113-118` with keys: `name_locales`, `narrator_rules`, `world_rules`, `factions`, `inventory`.

**Changes:** Add `inspiration` and `world_facts` keys to the packing dict. These must be extracted from the pack's `ScenarioBrief` and passed to `run_turn()` as parameters (following the existing pattern for `pack_narrator_rules`, `pack_world_rules`, `pack_factions`).

## Collision / Interaction Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| **Token budget** | Adding `world_facts` (max 5), `narrator_rules` (max 8), `factions` (max 4), `arc_threads` (max 5), and `inspiration` (3 strings) increases prompt length. Seed narrator adds ~480-820 tokens (one-time at turn 0). Regular narrator adds ~250-450 tokens per turn. If prompts exceed the context window, `trim_messages()` drops oldest non-system messages. | Truncation limits enforced in engine code. Monitor token counts during implementation. If prompts still exceed budget, consider further truncation or removing lower-priority context. The added context is reference material, not critical for turn-by-turn operation. |
| **Prompt quality** | More context could dilute the narrator's focus or cause it to over-index on canon/creative direction at the expense of player input. | The added context is reference material, not binding instructions. The narrator's priority hierarchy (player input > GM beat > outcome hint) remains unchanged. The context is available for grounding, not for overriding scene-level signals. |
| **Seed narrator output** | The seed narrator now has more context, which could change the style/quality of opening prose. | This is the intended outcome. The opening should be more grounded in world canon, tone, and campaign stakes. Eval runs should verify that opening quality improves, not degrades. |
| **Regular narrator output** | The regular narrator now has creative direction and baseline canon, which could change per-turn prose quality. | This is the intended outcome. Per-turn narration should be more grounded in the world's creative direction and baseline canon. Eval runs should verify that narration quality improves, especially for beat generation and action anchoring. |

## Token Budget Constraints

The added context increases prompt length. To minimize token bloat:

**Seed narrator additions** (one-time at turn 0):
- `world_facts`: max 5 facts (truncate if pack has more), ~100-200 tokens
- `narrator_rules`: max 8 rules (truncate if pack has more), ~200-300 tokens
- `factions`: max 4 factions (truncate if pack has more), ~80-120 tokens
- `arc_threads`: non-dormant threads only, max 5 threads, ~100-200 tokens
- **Total seed narrator addition: ~480-820 tokens**

**Regular narrator additions** (per-turn):
- `world_facts`: max 5 facts, ~100-200 tokens
- `inspiration`: 3 strings (pc, npcs, inventory), ~150-250 tokens
- **Total regular narrator addition: ~250-450 tokens per turn**

**Truncation strategy:**
- In `_build_narrate_seed_messages()`, truncate `world_facts[:5]`, `narrator_rules[:8]`, `factions[:4]`, `arc_threads[:5]`
- In `_narrate_messages()`, truncate `world_facts[:5]`
- Template rendering should be terse: single-line per item, no extra whitespace

**Token budget monitoring:**
- If prompts exceed context window, `trim_messages()` drops oldest non-system messages
- The added context is reference material, not critical for turn-by-turn operation
- Eval runs should verify that token counts stay within budget and that added context improves quality without bloat

## Risks

1. **Risk:** Token budget overflow causes `trim_messages()` to drop critical context (e.g., recent turns, arc threads). **Mitigation:** Monitor token counts during implementation. If prompts exceed budget, truncate added context (world_facts, narrator_rules, factions) to fit. The added context is reference material, not critical for turn-by-turn operation.

2. **Risk:** Seed narrator over-indexes on world canon and produces opening prose that feels like a lore dump rather than an immersive scene. **Mitigation:** The template instructions already emphasize "weave in naturally, only what fits" and "do not repeat stats/bio/inventory." The added context is reference material for grounding, not a checklist to exhaustively cover. Eval runs should verify that opening prose remains scene-focused and immersive.

3. **Risk:** Regular narrator over-indexes on creative direction and produces per-turn prose that feels constrained by the pack's inspiration blocks rather than responsive to player input. **Mitigation:** The creative direction is labeled "guidance only — do not borrow phrasing" (same as seed narrator). The narrator's priority hierarchy (player input > GM beat > outcome hint) remains unchanged. The creative direction is for grounding, not for overriding scene-level signals.

4. **Risk:** World facts injected separately from world_state create redundancy and confusion about which is authoritative. **Mitigation:** The prompt should clarify that "World Canon" is baseline pack canon (always true), while "World State" is evolving facts (may change over time). The narrator should treat both as authoritative, with world_state taking precedence for recent changes.

## Rejected Alternatives

1. **Rely solely on `world_state` for baseline canon** — rejected because `world_state` degrades over time as LLM-added facts accumulate. Baseline canon must remain visible even if `world_state` is overwritten or diluted.

2. **Modify `_world_state.j2` to distinguish baseline vs LLM-added facts** — rejected because it couples the template to seed-time logic and adds complexity. The simpler solution is to inject `world_facts` separately in the prompt, keeping the template agnostic to fact origins.

3. **Add `inspiration` and `world_facts` to `WorldState` model** — rejected because the data already exists in `pack.scenario`. Adding it to `WorldState` would duplicate data and create synchronization issues. The pack is the source of truth for pack-level context; the state is the source of truth for game-level context.

4. **Pass all pack context to both narrators uniformly** — rejected because each narrator has a specific role and context needs. The seed narrator needs world canon and campaign stakes for opening anchoring. The regular narrator needs creative direction and baseline canon for per-turn grounding. Uniform context would bloat prompts without improving quality.

5. **Add specificity enforcement rules to narrator prompts** — rejected because this is a separate concern from context availability. The specificity requirements (describe what's happening, name individuals with motivations, avoid faction-level abstractions) are prompt quality improvements that should be addressed in a separate design focused on narrator instructions, not context routing.

## Deferred Items

- **Specificity requirements enforcement:** The ticket mentions playtest feedback about lack of world-building detail and character motivations. This is a prompt quality issue that should be addressed in a separate design focused on narrator instructions and behavioral guidance, not context routing. The context routing in I-33 provides the raw material (world_facts, inspiration, factions, threads) that the narrator can use to generate specific prose, but enforcing specificity requires prompt engineering and eval runs, not just context availability.

- **Dynamic faction context:** The ticket mentions factions as static context. Future work could make faction context dynamic (e.g., only pass factions relevant to the current scene or threads). This is deferred because the current design passes all factions (up to 4, truncated), which is small enough to fit within token budgets. Dynamic faction filtering is an optimization, not a requirement.

## What an Implementer Needs to Read

**Source files:**
- `ccya/engine/seed.py:451-521` — `_build_narrate_seed_messages()` context building
- `ccya/engine/narrate.py:32-140` — `_narrate_messages()` context building
- `ccya/engine/narrate.py:154-254` — `_narrate_setup()` context extraction from packing
- `ccya/engine/turn.py:74-88, 113-118` — `run_turn()` signature and packing dict construction
- `ccya/server/routes.py:262-265` — `run_turn()` caller (pack parameter extraction)
- `ccya/ev/play.py:42-84, 464-467, 582-585, 825-828` — `run_turn()` callers (eval CLI)
- `ccya/pack.py:115-194` — `Faction`, `Inspiration`, `ScenarioBrief` models

**Prompt templates:**
- `ccya/prompts/narrate_seed_system.j2` — seed narrator system prompt
- `ccya/prompts/narrate_system.j2` — regular narrator system prompt
- `ccya/prompts/narrate_user.j2` — regular narrator user prompt

**Architecture docs:**
- `docs/architecture/step1-narrate.md` — narrator pipeline overview
- `docs/architecture/prompts-architecture.md` — prompt template hierarchy and rendering flow
- `docs/architecture/prompt-variable-contracts.md` — context variable contracts for each template

**Related design:**
- `docs/design/complete/03-seed-worldbuilding-redesign.md` — seed worldbuilding redesign (completed, provides context on seed generation and world_facts injection)

## Review Summary

**Verdict:** tighten

**TL;DR:** Design is sound after fixing one critical blocker about `ctx.packing` structure. The core approach (inject `world_facts`, `narrator_rules`, `factions`, `inspiration`, arc threads into narrator contexts) is correct and addresses the stated problem. Token budget constraints are reasonable and enforceable.

**Key Blockers:** 1 fixed (see below)

**Design Ambiguities:** None

**Auto-fixed:** 1
- [CRITICAL] `docs/design/I-33-narrator-context-optimization-design.md:148` — Design doc incorrectly claimed `ctx.packing` already contains `inspiration` and `world_facts`. Verified against source: `ctx.packing` only contains `name_locales`, `narrator_rules`, `world_rules`, `factions`, `inventory` (turn.py:113-118). Fixed by adding explicit `turn.py:run_turn()` signature changes and `server/routes.py`/`ev/play.py` caller changes to extract and pass these values.

**Non-blocking concerns:**

### Suggested Improvements
- [WARN] Token budget estimates are rough (~480-820 for seed, ~250-450 for regular). Actual token counts depend on pack content length. Eval runs should measure actual token usage and adjust truncation limits if needed.
- [WARN] The design assumes `trim_messages()` dropping non-critical context is acceptable. If critical context (e.g., recent turns, arc threads) is dropped, narration quality could degrade. Mitigation: monitor which messages are dropped during eval runs and prioritize critical context if trimming becomes frequent.

### Minor Notes
- [MINOR] The design doc mentions "arc urgency signals" in the problem statement but doesn't explicitly address what these are beyond `threads[].urgency`. This is fine — the urgency field already exists and is passed to both narrators (seed via arc_threads, regular via current_objective.threads). No additional work needed.
- [MINOR] The design defers "specificity requirements enforcement" to a separate design. This is correct — it's a prompt quality issue, not a context routing issue. The context provided in I-33 (world_facts, inspiration, factions, threads) gives the narrator the raw material for specific prose, but enforcing specificity requires prompt engineering and behavioral guidance, not just context availability.

## Dependencies on Other Designs

- **03-Seed Worldbuilding Redesign** — I-33 depends on the seed worldbuilding redesign's implementation of `world_facts` injection into `world_state` at seed time. The redesign is marked "scoping" but the `world_facts` injection logic is already implemented in `seed.py:372-379`.

- **Arc System Redesign** — I-33 passes arc threads to the seed narrator, which depends on the arc system's thread model (`ArcThread` with `summary`, `urgency`, `type` fields). The arc system is already implemented and stable.

- **Prompt Testing (ev.py)** — I-33 should be validated using `ev.py prompt-eval` to render prompts with live data and verify that the added context is rendered correctly and fits within token budgets. The prompt-eval system is already implemented and documented in `docs/ev/STATE-REFERENCE.md`.
