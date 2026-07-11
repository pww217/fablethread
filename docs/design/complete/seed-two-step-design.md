# Seed Two-Step Design

> **Status:** implemented
> **Discovery:** [Seed Generation Temperature and Reliability](../discovery/seed-generation-temperature-and-reliability.md)
> **Related designs:**
> - [03-Seed Worldbuilding Redesign](./complete/03-seed-worldbuilding-redesign.md) — funnel ordering, pc_situation_schema, arc_origin, world state lifecycle
>
> **Related tickets:**
> - [Spread pc_situation over multiple turns](../../roadmap/features/pc-situation-reveal-over-time.md) — gradual reveal prereq decision (implemented on top of two-step pipeline)

## Problem Statement

Seed generation makes a single LLM call that produces both structured game state (world facts, locations, PC situation, arc, NPCs, inventory) and creative prose (opening_narrative, actions, outcome_summary). These two outputs have opposite temperature requirements:

- **Structured JSON:** needs low temperature (0.2–0.5) for reliable schema conformance — no malformed keys, no truncated arrays, no missing fields.
- **Creative prose:** needs high temperature (0.7–0.9) for vivid, non-generic narration — sensory richness, natural weaving of facts, character-appropriate voice.

At any single temperature, one output is compromised. At 0.9, ~50% of first attempts fail with "No JSON found" due to malformed JSON. At 0.65, reliability improves to ~80% but narration becomes more formulaic. The fundamental tension cannot be resolved within one call.

**Hypothesis (confirmed in discovery):** Splitting into two LLM calls — `prepare_seed` (low temp, structured game state) and `narrate_seed` (high temp, creative prose only) — solves both problems simultaneously without additional complexity.

> **Prereq decision:** The gradual pc_situation reveal over turns 0–3 ([roadmap/features/pc-situation-reveal-over-time.md](../../roadmap/features/pc-situation-reveal-over-time.md)) is a prerequisite decision. The design below was evaluated against two alternatives:
>
> 1. **Unified pipeline:** Skip `narrate_seed` entirely. Pass full SeedState through the existing turn pipeline on turn 0. The narrator gates situation reveal via a directive in the system prompt. Turn 0 ruling runs with placeholder input and no-roll outcome.
> 2. **Separate narrate_seed:** The approach described in the problem statement — a dedicated `narrate_seed` call.
>
> **Decision: separate narrate_seed.** A dedicated `narrate_seed` call gives us prompt control (tightly scoped opening prose prompt), latency savings (one call vs ruling+narrate+extract), and simplicity (no fake ruling input, no directive gating). The gradual reveal design (directive-based gating, 3-turn schedule, tension entries → arc threads) is implemented on top of the two-step pipeline.

## Design Principles

**Temperature separation.** Structured JSON and creative prose have fundamentally different temperature requirements. One LLM call cannot optimize both. Two calls, each at its optimal temperature, is the correct solution.

**Strict output boundaries.** `prepare_seed` produces only structured JSON (SeedState). `narrate_seed` produces only prose (opening_narrative, actions, outcome_summary). No cross-contamination. No structured output from narrate_seed, no prose from prepare_seed.

**Clean break.** No backward compatibility with existing config keys or prompt templates. `generate_seed` fully replaced by `prepare_seed`. `generate_seed_system.j2` renamed and cleaned. New `narrate_seed_system.j2` created.

**SeedStateEnvelope as new type.** `prepare_seed` cannot return `SeedEnvelope` — Pydantic min_length constraints on narrative fields would fail when those fields are empty. New `SeedStateEnvelope` model wraps `SeedState` without narrative constraints.

**Hard fail safety.** If either prepare_seed or narrate_seed fails (each gets 1 retry), the game fails to start rather than booting into a stateless void. Clear log message on hard fail.

## Target State

### New Pipeline

```
prepare_seed (temp: ~0.55)
    ↓
SeedStateEnvelope (validated SeedState, no narrative constraints)
    ↓
narrate_seed (temp: ~0.9)
    ↓
complete SeedEnvelope (seed_state + opening_narrative + actions + outcome_summary)
```

### Step Definitions

#### `prepare_seed`

**Purpose:** Generate all structured game state fields in a single validated JSON output. No prose generation.

**Inputs:**
- `pack: Pack` (scenario.yaml + manifest)
- `config: EngineConfig`
- `overrides: PlayerOverrides | None`

**Temperature:** 0.55 (initial). Lower to 0.2–0.3 if JSON syntax errors appear.

**Output:** `SeedStateEnvelope` — a new Pydantic model wrapping `SeedState` without narrative constraints:

```python
class SeedStateEnvelope(BaseModel):
    seed_state: SeedState
    opening_narrative: str = ""
    actions: list[str] = []
    outcome_summary: str = ""
    arc: LongTermObjective | None = None
    arc_origin: str = ""
    pool_selection: dict[str, Any] | None = None
```

No `min_length` constraints on narrative fields. `seed_state` validates against the full `SeedState` Pydantic model. `arc` and `arc_origin` are stored inside `seed_state.arc` and `seed_state.arc_origin` (funnel general → specific, consistent with existing SeedState structure).

**Fields written to `SeedState`:**
- `meta` — turn: 0, model, setting_pack, session_name
- `pc` — name, tagline, bio, stats, conditions[], situation{pack keys}
- `location` — id, name, description
- `inventory` — items (including currency injection)
- `scene.world_state` — facts (baseline + generated, tier/valence/permanent)
- `compendium.npcs` — all NPCs including pc_situation handoff
- `arc` — long_term_objective, threads
- `arc_origin` — string
- `world.locations` — key locations array

**Post-generation processing (unchanged from current):**
- `_sanitize_envelope()` — strip non-ASCII, assign surnames, ensure 1+ present NPC
- `_validate_seed_envelope()` — PC name length check
- Personality assignment — fill `personality` field from archetype table
- Thread limits — cap non-dormant at 2, dormants at 3, total 4–5
- Baseline facts prepend — inject `scenario.world_facts` into world_state
- Currency injection — add pack currency to inventory if missing

**Retries:** Separate counter, default `max_llm_retries: 1`. At low temperature, JSON failure is rare, so the retry almost never fires.

**Prompt changes:**
1. Rename `generate_seed_system.j2` → `prepare_seed_system.j2`
2. Remove narrative prose instructions (these go to `narrate_seed_system.j2`):
   - Opening narrative instructions (3-movement structure, sensory detail, second person) — j2 lines 197–219
   - Actions section (4 choices, posture requirements) — j2 lines 221–231
   - Outcome summary section — j2 lines 233–236
   - All "weave in pc_situation / arc_origin / world facts / key locations" prose instructions
3. Keep generation rules (these tell the LLM what JSON fields to produce):
   - Generation order 1–6 (world facts → key locations → arc origin → pc situation → campaign arc → NPCs → inventory)
   - Schema definition (rewritten to show only `SeedState` shape, not `SeedEnvelope`)
   - Field requirements
   - Personality archetype table
   - Thread rules
   - NPC field requirements (including pc_situation handoff as step 7b)
   - PC field rules
   - Key locations rules
   - PC situation rules
   - Inventory rules
   - World state rules
4. Change output format to expect JSON for `SeedState` only (not full `SeedEnvelope`)
5. Schema shows `arc` and `arc_origin` only inside `seed_state` (not at top level). Funnel general → specific maintained.

#### `narrate_seed`

**Purpose:** Generate opening narrative, actions, and outcome summary given a fully validated `SeedState`.

**Inputs:**
- `seed_state: SeedState` (the validated model from `prepare_seed`)
- `config: EngineConfig`
- `pack: Pack` (for scenario context, pool_selection for scene bundle)

**Temperature:** `config.narrate_temperature` (currently 0.9). Reuses the existing narrate temperature knob — no new config key. Inherits narrate's `top_p` (0.95) and `frequency_penalty` (0.5).

**Output:** A dict containing exactly:
```python
{
  "opening_narrative": string,  # min_length=50
  "actions": list[string],      # min_length=4, max_length=4
  "outcome_summary": string
}
```

These three fields are assembled into the final `SeedEnvelope` alongside the existing `SeedState`.

**What goes in the prompt:**
- `pc.name`, `pc.tagline`, `pc.bio`, `pc.stats`, `pc.conditions`, `pc.situation` — character grounding
- `location.id`, `location.name`, `location.description` — scene setting
- `arc_origin` — backstory context for weaving
- `world.locations` (key locations) — constraint: scene must be set in/near one
- `inventory.items` — only if relevant to opening moment (e.g., currency, distinctive items)
- `pool_selection` — scene bundle ingredients (items, conditions, sensory)
- Opening narrative instructions (3-movement structure, second person, present tense) — moved from prepare_seed prompt
- Instructions to weave in pc_situation, arc_origin, key locations naturally — moved from prepare_seed prompt
- Actions section (4 choice requirements) — moved from prepare_seed prompt
- Outcome summary instructions — moved from prepare_seed prompt
- The **scene must be set in or near a key location** constraint

**What does NOT go in the prompt:**
- All schema definitions (world fact structure, NPC field requirements, thread rules, inventory rules, etc.)
- Generation order (already done in `prepare_seed`)

**Retries:** Separate counter, default `max_llm_retries: 1`. Higher temp means retries are more likely but cheap — only three fields to validate. Hard fail if either prepare_seed or narrate_seed fails (each gets 1 retry). Clear log message on hard fail.

### Handoff Contract

`prepare_seed` returns `SeedStateEnvelope` — a new Pydantic model wrapping `SeedState` without narrative constraints. `narrate_seed` receives `seed_state` (the `SeedState` model) and returns a dict with the three narrative fields. The caller assembles the final `SeedEnvelope`:

```python
partial = await prepare_seed(pack, config, overrides=overrides)
# partial: SeedStateEnvelope(seed_state=SeedState, opening_narrative="", actions=[], pool_selection=...)
narrate_fields = await narrate_seed(partial.seed_state, config, pack=pack, pool_selection=partial.pool_selection)
# narrate_fields: {"opening_narrative": "...", "actions": [...], "outcome_summary": "..."}
final_envelope = SeedEnvelope(
    seed_state=partial.seed_state,
    opening_narrative=narrate_fields["opening_narrative"],
    actions=narrate_fields["actions"],
    outcome_summary=narrate_fields["outcome_summary"],
    arc=partial.seed_state.arc,
    arc_origin=partial.seed_state.arc_origin,
)
```

`SeedEnvelope` model is unchanged (still has `min_length` constraints on narrative fields). `SeedStateEnvelope` is a new type — has `seed_state: SeedState`, `opening_narrative: str = ""`, `actions: list[str] = []`, `outcome_summary: str = ""`, `arc: LongTermObjective | None = None`, `arc_origin: str = ""`, `pool_selection: dict[str, Any] | None = None`. No `min_length` constraints on the narrative fields.

### Config Changes

Replace the current `generate_seed` block:

```yaml
# BEFORE
generate_seed:
  temperature: 0.65
  top_p: 0.95

# AFTER
prepare_seed:
  temperature: 0.55
  top_p: 0.95
```

No backward compatibility — no fallback, no migration path. Existing config.yaml files must be updated.

`narrate_seed` reuses the existing `narrate` temperature block — no new config key. (The narrate block is the narrator's temperature for ongoing turns; `narrate_seed` uses the same temp because it's the same kind of prose generation.)

**Config code changes:**
- `EngineConfig.generate_seed_temperature` → `EngineConfig.prepare_seed_temperature` (default 0.55)
- `EngineConfig.generate_seed_top_p` → `EngineConfig.prepare_seed_top_p` (default 0.95)
- `build_engine_config()` reads `llm.prepare_seed` instead of `llm.generate_seed`
- `config.yaml` top-level key changes from `generate_seed` to `prepare_seed`
- `temperature_override` in `build_engine_config` does NOT apply to `prepare_seed_temperature` (seed steps are excluded from override). The override (used by `ev.py play --temperature` for runtime testing) applies only to `ruling`, `extract`, and `narrate`. `prepare_seed` and `narrate_seed` always use their config defaults.
- Remove `generate_seed` from the eval config override list (replace with `prepare_seed`)

### Engine Changes

`ccya/engine/seed.py`:
- Rename `generate_seed()` → `prepare_seed()` with new signature returning `SeedStateEnvelope`
- Add `narrate_seed()` function alongside it
- `_build_generate_seed_messages()` → `_build_prepare_seed_messages()` (excludes narrative weaving instructions, keeps generation rules)
- `_build_narrate_seed_messages()` — new function, builds prompt from SeedState context
- Prompt template: `generate_seed_system.j2` → `prepare_seed_system.j2` (renamed, cleaned) + `narrate_seed_system.j2` (new)
- `_soft_validate_seed()` — remove cliché check and min_length checks (opening_narrative doesn't exist at prepare_seed time). Hard fail if either prepare_seed or narrate_seed fails (each gets 1 retry). Clear log message on hard fail.
- `_validate_seed_envelope()` — PC name length check stays (unchanged)
- Arc/thread limit enforcement: read from `seed_state.arc` directly (not `envelope.arc` top-level). Remove the copy logic at seed.py:381-385.

`ccya/engine/__init__.py`:
- Update exports (add `narrate_seed`)

`ccya/server/routes.py`:
- `new_game` route: call `prepare_seed()` then `narrate_seed()` sequentially
- `new_game_reroll` route: same

`ccya/ev/play.py`:
- `_ensure_seed_generated()`: call `prepare_seed()` then `narrate_seed()` sequentially
- Rename config read from `generate_seed` to `prepare_seed`

`ccya/ev/eval.py`:
- Remove `generate_seed` from eval config override sections (replace with `prepare_seed`)

### File Changes Summary

| File | Change |
|---|---|
| `ccya/engine/seed.py` | Rename `generate_seed` → `prepare_seed` (returns `SeedStateEnvelope`). Add `narrate_seed()`. Split message builders. Remove arc copy logic. Update `_soft_validate_seed`. |
| `ccya/pack.py` | Add `SeedStateEnvelope` model (new). |
| `ccya/engine/config.py` | `generate_seed_temperature` → `prepare_seed_temperature`. New default 0.4. Exclude seed from `temperature_override`. |
| `config.yaml` | `generate_seed` → `prepare_seed`. Temp changes to 0.4. |
| `ccya/prompts/generate_seed_system.j2` | Rename to `prepare_seed_system.j2`. Remove narrative weaving instructions (keep generation rules). Rewrite schema to show `SeedState` only. |
| `ccya/prompts/generate_seed_user.j2` | Rename to `prepare_seed_user.j2`. Update JSON output discipline section for narrower output. |
| `ccya/prompts/narrate_seed_system.j2` | **New file.** Prose generation with SeedState context. |
| `ccya/server/routes.py` | New call sequence: prepare → narrate. |
| `ccya/ev/play.py` | New call sequence. Config key rename. |
| `ccya/ev/eval.py` | Config override cleanup. |
| `ccya/engine/__init__.py` | Add `narrate_seed` export. |

### What Stays the Same

- `SeedEnvelope` Pydantic model — unchanged (still has `min_length` constraints on narrative fields)
- `SeedState` Pydantic model — unchanged
- `_sanitize_envelope()` — unchanged (operates on `SeedEnvelope`, called after `narrate_seed`)
- `_validate_seed_envelope()` — unchanged (PC name length check)
- Personality assignment logic — unchanged
- Thread limit enforcement — unchanged (reads from `seed_state.arc` directly)
- Baseline fact prepend — unchanged
- Currency injection — unchanged
- `_apply_seed_to_save_dir()` — unchanged (receives the same final `SeedEnvelope` as today)
- `_build_seed_prompt` pool/template rendering — unchanged (same context variables, pool pre-selection stays in `prepare_seed`)
- NPC generation from pc_situation — unchanged (still part of `prepare_seed`, same 7b instruction)

### Why This Works

- **`prepare_seed` at 0.4 temp:** JSON is near-deterministic. No "No JSON found" errors. No schema violations. No missing fields. Retries almost never fire. The 10–15 seconds this takes are predictable.
- **`narrate_seed` at 0.9 temp:** The LLM focuses entirely on prose quality — sensory richness, natural weaving of facts, character-appropriate voice. No cognitive load from maintaining JSON schema. Higher temp makes retries more likely but the output is only 3 fields (string, string[], string) so validation is trivial.
- **Hard fail safety:** If either prepare_seed or narrate_seed fails (each gets 1 retry), the game fails to start rather than booting into a stateless void. Clear log message on hard fail.
- **Total latency:** Two sequential LLM calls instead of one. Each call is faster than the current single merged call (shorter prompts, simpler output schemas). Net latency is roughly 1.3–1.5× the current single call — acceptable for a one-time operation at game start.

## Decisions

- **Temperature for `prepare_seed`: 0.55.** Start here. If JSON reliability issues surface, lower to 0.2–0.3 on a sliding scale. Configurable via `prepare_seed_temperature` in EngineConfig, read from `llm.prepare_seed` in config.yaml.
- **Temperature for `narrate_seed`: `narrate_temperature`.** Reuses the existing narrate config key (currently 0.9). Not a separate config entry — the narrate_seed call is the same kind of prose generation as ongoing turns. Inherits narrate's `top_p` (0.95) and `frequency_penalty` (0.5).
- **Actions in `narrate_seed`.** Actions derive from the narrative scene context, not the raw structured state. Generating them alongside prose is a single concern. The one JSON field (actions array) at high temp has negligible failure risk.
- **Context passed to `narrate_seed`.** Filtered subset: pc (name, tagline, bio, stats, conditions, situation), location, arc_origin, world.locations (key locations), inventory (only if relevant), pool_selection. NOT passed: world_state, compendium.npcs, arc threads/objective, meta. Opening narrative establishes PC + setting; world facts, NPC rosters, and arc threads belong in ongoing turns.
- **Separate retry counters with hard fail.** `prepare_seed` retries are cheap and unlikely. `narrate_seed` retries are slightly more likely but validate only 3 fields. Each gets 1 retry. If either fails (after retries), hard fail — game does not start. Clear log message on hard fail.
- **`SeedStateEnvelope` as new type.** New Pydantic model wrapping `SeedState` without narrative constraints. `prepare_seed` returns it. `narrate_seed` returns dict. Caller assembles final `SeedEnvelope`.
- **Arc/arc_origin in prompt schema.** Only inside `seed_state` (not at top level). Funnel general → specific maintained. Post-processing reads from `seed_state.arc` directly (no copy from envelope.arc).
- **`pool_selection` in `narrate_seed`:** Yes, pass the full `pool_selection` dict via `SeedStateEnvelope.pool_selection`. The scene bundle is 3 small arrays (items, conditions, sensory) — negligible context cost, simpler than subsetting. Pool pre-selection stays in `prepare_seed` (same code path as current `_build_generate_seed_messages`).
- **Standalone functions:** Confirmed. `prepare_seed()` and `narrate_seed()` are two standalone async functions called sequentially by route handlers and the eval harness. No wrapper.
- **`temperature_override`:** Seed steps are excluded. The override (used by `ev.py play --temperature` for runtime testing) applies only to `ruling`, `extract`, and `narrate`. `prepare_seed` and `narrate_seed` always use their config defaults.
- **Prompt cleanup scope:** Generation rules (what to produce) stay in `prepare_seed` prompt. Weaving instructions (how to write prose) move to `narrate_seed_system.j2`. The "Opening narrative" section (j2 lines 197-219), "Actions" section (j2 lines 221-231), and "Outcome summary" section (j2 lines 233-236) move to narrate_seed prompt.
- **Prompt schema rewrite:** `prepare_seed` prompt schema shows only `SeedState` shape (no `opening_narrative`, `actions`, `outcome_summary` at top level). `arc` and `arc_origin` only inside `seed_state`.
- **Config migration:** No backward compatibility — no fallback, no migration path. Existing config.yaml files must be updated. `build_engine_config()` reads `llm.prepare_seed` instead of `llm.generate_seed`.

## Open Questions

### `narrate_seed` prompt rendering

The design says `narrate_seed` prompt should include "The full structured `SeedState` rendered as context" — but how? The current narrate prompt uses a Jinja2 template that renders game state from a context dict. Should `narrate_seed_system.j2` follow the same pattern?

**Recommendation:** Yes, follow the same Jinja2 template pattern as existing narrate prompts. The plan author should design the template rendering approach.

### Context filtering for `narrate_seed` prompt

The prompt should receive:
- `pc.name`, `pc.tagline`, `pc.bio`, `pc.stats`, `pc.conditions`, `pc.situation` — character grounding
- `location.id`, `location.name`, `location.description` — scene setting
- `arc_origin` — backstory context for weaving
- `world.locations` (key locations) — constraint: scene must be set in/near one
- `inventory.items` — only if relevant to opening moment (e.g., currency, distinctive items)
- `pool_selection` — scene bundle ingredients (items, conditions, sensory)

The prompt should NOT receive:
- `scene.world_state` — world facts are background texture, not opening narrative material
- `compendium.npcs` — NPCs exist for later turns; opening focuses on PC + setting
- `arc.long_term_objective`, `arc.threads` — arc context belongs in ongoing turns, not opening
- `meta` — turn/model info irrelevant to prose generation

**Rationale:** Opening narrative's job is to establish the PC, their situation, and the immediate scene. World facts, NPC rosters, and arc threads are context for the *ongoing* narrator, not for bootstrapping the opening prose. Passing them bloats the prompt without improving the opening.

## Scope

This design covers:
- Splitting `generate_seed` into `prepare_seed` + `narrate_seed`
- New `SeedStateEnvelope` model in `ccya/pack.py`
- Config migration (`generate_seed` → `prepare_seed`)
- Prompt template changes (rename, clean, create new)
- Route handler updates (`new_game`, `new_game_reroll`)
- Eval harness updates (`play.py`, `eval.py`)
- Engine exports (`__init__.py`)

## Non-Goals

- **Changing `SeedEnvelope` or `SeedState` model shapes.** No field renames, no new fields, no deletions in existing models. The split is purely a pipeline change. (Exception: `SeedStateEnvelope` is a new model — see Handoff Contract.)
- **Changing NPC generation.** `pc_situation` handoff and all NPC rules stay in `prepare_seed`. No change.
- **Changing world state schema.** World facts, tier, valence, permanence are all unchanged.
- **Adding narrative to `prepare_seed`** or structured output to `narrate_seed`. The boundary is strict.
- **Supporting per-step retry counts in config.** Both steps use `max_llm_retries` from the top level. If per-step counts are needed later, add them then.
- **Pack parity.** Generated and custom packs are out of scope. This redesign targets default packs only.
- **Location tracking system.** `world.locations` is a worldbuilding reference list, not a movement or state-change system.

## Dependencies on Other Designs

- **03-Seed Worldbuilding Redesign** — funnel ordering, pc_situation_schema, arc_origin, world state lifecycle
- **Spread pc_situation over multiple turns** — gradual reveal prereq decision (implemented on top of two-step pipeline)
