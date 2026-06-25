# Seed Two-Step Design

> **Status:** reviewed (partially superseded — see prereq decision below)
> **Review date:** 2026-06-24
> **Discovery:** [Seed Generation Temperature and Reliability](../discovery/seed-generation-temperature-and-reliability.md)
> **Related designs:**
> - [03-Seed Worldbuilding Redesign](./complete/03-seed-worldbuilding-redesign.md) — funnel ordering, pc_situation_schema, arc_origin, world state lifecycle
> **Related tickets:**
> - [Spread pc_situation over multiple turns](../../roadmap/features/pc-situation-reveal-over-time.md) — gradual reveal prereq decision (supersedes narrate_seed portion)

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
> **Decision: unified pipeline.** A separate `narrate_seed` duplicates the narrator prompt, creates dual retry logic, and adds complexity. The gradual reveal design (directive-based gating, 3-turn schedule, tension entries → arc threads) is implemented on top of the unified pipeline. **The `narrate_seed` portion of this design is superseded by the unified pipeline approach.** Only `prepare_seed` (low-temp structured generation) remains. The prose generation happens in the existing narrator on turn 0.

## Target State

### New Pipeline

```
prepare_seed (temp: ~0.4)
    ↓
SeedState (validated dict)
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

**Temperature:** 0.4–0.5 (initial). Lower to 0.2–0.3 if JSON syntax errors appear.

**Output** (partial `SeedState`, minus the narrative fields that narrate_seed will set on the final envelope):

```python
{
  "seed_state": SeedState  # full SeedState: meta, pc, location, inventory, scene/world_state, compendium, arc, arc_origin, world/locations
}
```

No `opening_narrative`, `actions`, `outcome_summary` in the output. The output validates against `SeedState` Pydantic model directly.

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
2. Remove all narrative prose content from the prompt:
   - Opening narrative instructions (3-movement structure, sensory detail, second person)
   - Actions section (4 choices, posture requirements)
   - Outcome summary section
   - All "weave in pc_situation / arc_origin / world facts / key locations" instructions
3. Keep everything else:
   - Generation order 1–6 (world facts → key locations → arc origin → pc situation → campaign arc → NPCs → inventory)
   - Schema definition
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

#### `narrate_seed`

**Purpose:** Generate opening narrative, actions, and outcome summary given a fully validated `SeedState`.

**Inputs:**
- `seed_state: SeedState` (the validated dict from `prepare_seed`)
- `config: EngineConfig`
- `pack: Pack` (for scenario context, pool_selection for scene bundle)

**Temperature:** `config.narrate_temperature` (currently 0.9). Reuses the existing narrate temperature knob — no new config key.

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
- The full structured `SeedState` rendered as context (world facts, key locations, pc_situation, arc_origin, NPCs, inventory)
- Opening narrative instructions (3-movement structure, second person, present tense)
- Instructions to weave in pc_situation, arc_origin, world facts, key locations naturally
- Scene bundle ingredients (from pool_selection, if available)
- Actions section (4 choice requirements)
- Outcome summary instructions
- The **scene must be set in or near a key location** constraint

**What does NOT go in the prompt:**
- All schema definitions (world fact structure, NPC field requirements, thread rules, inventory rules, etc.)
- Generation order (already done in `prepare_seed`)

**Retries:** Separate counter, default `max_llm_retries: 1`. Higher temp means retries are more likely but cheap — only three fields to validate.

### Handoff Contract

`prepare_seed` returns a `SeedStateEnvelope` — a lightweight wrapper around `SeedState` without narrative constraints. `narrate_seed` receives `seed_state` and returns a `SeedEnvelope` with the three narrative fields populated. The caller assembles the final envelope:

```python
partial = await prepare_seed(pack, config, overrides=overrides)
# partial: SeedStateEnvelope(seed_state=..., opening_narrative="", actions=[], ...)
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

`SeedEnvelope` model is unchanged. `SeedStateEnvelope` is a new type — a `SeedEnvelope` with `opening_narrative`, `actions`, and `outcome_summary` having no `min_length` constraints.

### Config Changes

Replace the current `generate_seed` block:

```yaml
# BEFORE
generate_seed:
  temperature: 0.65
  top_p: 0.95

# AFTER
prepare_seed:
  temperature: 0.4
  top_p: 0.95
```

`narrate_seed` reuses the existing `narrate` temperature block — no new config key. (The narrate block is the narrator's temperature for ongoing turns; `narrate_seed` uses the same temp because it's the same kind of prose generation.)

**Config code changes:**
- `EngineConfig.generate_seed_temperature` → `EngineConfig.prepare_seed_temperature` (default 0.4)
- `EngineConfig.generate_seed_top_p` → `EngineConfig.prepare_seed_top_p` (default 0.95)
- `build_engine_config()` reads `llm.prepare_seed` instead of `llm.generate_seed`
- `config.yaml` top-level key changes from `generate_seed` to `prepare_seed`
- `temperature_override` in `build_engine_config` applies to `prepare_seed_temperature` but NOT `narrate_seed_temperature` (narrate has its own override path if needed)
- Remove `generate_seed` from the eval config override list since it's no longer a single key

### Engine Changes

`ccya/engine/seed.py`:
- Rename `generate_seed()` → `prepare_seed()` with new signature
- Add `narrate_seed()` function alongside it
- `_build_generate_seed_messages()` → `_build_prepare_seed_messages()` (excludes narrative instructions)
- `_build_narrate_seed_messages()` — new function, builds prompt from SeedState context
- Prompt template: `generate_seed_system.j2` → `prepare_seed_system.j2` + `narrate_seed_system.j2` (new)

`ccya/engine/__init__.py`:
- Update exports

`ccya/server/routes.py`:
- `new_game` route: call `prepare_seed()` then `narrate_seed()` sequentially
- `new_game_reroll` route: same

`ccya/ev/play.py`:
- `_ensure_seed_generated()`: call `prepare_seed()` then `narrate_seed()` sequentially
- Rename config read from `generate_seed` to `prepare_seed`

`ccya/ev/eval.py`:
- Remove `generate_seed` from eval config override sections (or replace with `prepare_seed` + `narrate`)

### File Changes Summary

| File | Change |
|---|---|
| `ccya/engine/seed.py` | Rename `generate_seed` → `prepare_seed`. Add `narrate_seed()`. Split message builders. |
| `ccya/engine/config.py` | `generate_seed_temperature` → `prepare_seed_temperature`. New default 0.4. Narrate_seed reuses narrate_temperature. |
| `config.yaml` | `generate_seed` → `prepare_seed`. Temp changes to 0.4. |
| `ccya/prompts/generate_seed_system.j2` | Rename to `prepare_seed_system.j2`. Remove all narrative prose content. |
| `ccya/prompts/generate_seed_user.j2` | Rename to `prepare_seed_user.j2` if it exists. |
| `ccya/prompts/narrate_seed_system.j2` | **New file.** Prose generation with SeedState context. |
| `ccya/server/routes.py` | New call sequence: prepare → narrate. |
| `ccya/ev/play.py` | New call sequence. Config key rename. |
| `ccya/ev/eval.py` | Config override cleanup. |
| `ccya/engine/__init__.py` | Rename export. |

### What Stays the Same

- `SeedEnvelope` Pydantic model — unchanged
- `SeedState` Pydantic model — unchanged
- `_sanitize_envelope()` — unchanged
- `_validate_seed_envelope()` — unchanged
- Personality assignment logic — unchanged
- Thread limit enforcement — unchanged
- Baseline fact prepend — unchanged
- Currency injection — unchanged
- `_apply_seed_to_save_dir()` — unchanged (receives the same final `SeedEnvelope` as today)
- `_build_seed_prompt` pool/template rendering — unchanged (same context variables)
- NPC generation from pc_situation — unchanged (still part of prepare_seed, same 7b instruction)
- `generate_seed_user.j2` content — only rename, no content change (user prompt has no narrative instructions)

### Why This Works

- **`prepare_seed` at 0.4 temp:** JSON is near-deterministic. No "No JSON found" errors. No schema violations. No missing fields. Retries almost never fire. The 10–15 seconds this takes are predictable.
- **`narrate_seed` at 0.9 temp:** The LLM focuses entirely on prose quality — sensory richness, natural weaving of facts, character-appropriate voice. No cognitive load from maintaining JSON schema. Higher temp makes retries more likely but the output is only 3 fields (string, string[], string) so validation is trivial.
- **Total latency:** Two sequential LLM calls instead of one. Each call is faster than the current single merged call (shorter prompts, simpler output schemas). Net latency is roughly 1.3–1.5× the current single call — acceptable for a one-time operation at game start.

## Decisions

- **Temperature for `prepare_seed`: 0.4.** Start here. If JSON reliability issues surface, lower to 0.2–0.3 on a sliding scale. Not configurable per-environment in the initial implementation — the discovery document recommends a fixed value.
- **Temperature for `narrate_seed`: `narrate_temperature`.** Reuses the existing narrate config key (currently 0.9). Not a separate config entry — the narrate_seed call is the same kind of prose generation as ongoing turns.
- **Actions in `narrate_seed`.** Actions derive from the narrative scene context, not the raw structured state. Generating them alongside prose is a single concern. The one JSON field (actions array) at high temp has negligible failure risk.
- **Full `SeedState` passed to `narrate_seed`.** No subset schema. The LLM receives all structured context and selects what it needs. This matches the existing pattern for narrate prompts that receive full game state.
- **Separate retry counters.** `prepare_seed` retries are cheap and unlikely. `narrate_seed` retries are slightly more likely but validate only 3 fields. No reason to tie them together.
- **Single `SeedEnvelope` built in two phases.** No new model types. The caller assembles the envelope from `prepare_seed` (seed_state) + `narrate_seed` (narrative fields).

## Decisions (Resolved During Scoping Review)

- **`pool_selection` in `narrate_seed`:** Yes, pass the full `pool_selection` dict. The scene bundle is 3 small arrays (items, conditions, sensory) — negligible context cost, simpler than subsetting.
- **Standalone functions:** Confirmed. `prepare_seed()` and `narrate_seed()` are two standalone async functions called sequentially by route handlers and the eval harness. No wrapper.
- **`temperature_override`**: Seed steps are excluded. The override (used by `ev.py play --temperature` for runtime testing) applies only to `ruling`, `extract`, and `narrate`. `prepare_seed` and `narrate_seed` always use their config defaults.

## Non-Goals

- **Changing `SeedEnvelope` or `SeedState` model shapes.** No field renames, no new fields, no deleteions. The split is purely a pipeline change.
- **Changing NPC generation.** `pc_situation` handoff and all NPC rules stay in `prepare_seed`. No change.
- **Changing world state schema.** World facts, tier, valence, permanence are all unchanged.
- **Adding narrative to `prepare_seed`** or structured output to `narrate_seed`. The boundary is strict.
- **Supporting per-step retry counts in config.** Both steps use `max_llm_retries` from the top level. If per-step counts are needed later, add them then.

## Review

### Key Blockers

- **[CRITICAL] `SeedEnvelope` has `opening_narrative: str = Field(min_length=50)` and `actions: list[str] = Field(min_length=4, max_length=4)`. `prepare_seed` cannot return a `SeedEnvelope` with empty strings/lists — Pydantic validation will fail.**
  At `pack.py:90-91`, `opening_narrative` requires min 50 chars and `actions` requires exactly 4 items. If `prepare_seed` returns a `SeedEnvelope` with `opening_narrative=""` and `actions=[]`, Pydantic will raise a validation error before `narrate_seed` even runs.
  **Fix:** `prepare_seed` returns a separate type — `SeedStateEnvelope` — that wraps `SeedState` without the narrative constraints. `SeedStateEnvelope` has `seed_state: SeedState`, `opening_narrative: str = ""`, `actions: list[str] = []`, `outcome_summary: str = ""`, `arc: LongTermObjective | None = None`, `arc_origin: str = ""`. No `min_length` constraints on the narrative fields. `narrate_seed` returns a `SeedEnvelope` (with constraints) and the caller assembles the final envelope.

- **[CRITICAL] `prepare_seed` post-processing calls `_soft_validate_seed(envelope, pack)` which checks `envelope.opening_narrative` — but `prepare_seed` won't have opening_narrative yet.**
  At `seed.py:202`, `_soft_validate_seed` reads `envelope.opening_narrative.lower()` to check for forbidden clichés. If `opening_narrative` is empty at `prepare_seed` time, this check will silently pass (empty string won't match any cliché). This is fine — the check will run again in `narrate_seed` after prose is generated. But the design says `_soft_validate_seed` is "unchanged" — it will need to be called twice (once in each step) or the design should clarify that soft validation only runs after `narrate_seed`.
  **Fix:** Call `_soft_validate_seed` only after `narrate_seed` completes. Skip it in `prepare_seed` — the opening_narrative doesn't exist yet.

- **[CRITICAL] Arc copying and thread limits operate on `envelope.arc` (top-level) — won't exist in `prepare_seed` output.**
  At `seed.py:357-359`, the current flow copies `envelope.arc` (top-level) into `envelope.seed_state.arc`. If `prepare_seed`'s LLM only outputs `seed_state` (without top-level `arc`), `envelope.arc` will be `None` and thread limits won't be enforced.
  **Fix:** `prepare_seed`'s LLM output includes `arc` inside `seed_state.arc` (as part of `SeedState`). The thread limit enforcement code at `seed.py:357` should check `envelope.seed_state.arc` instead of `envelope.arc` for `prepare_seed`. Alternatively, `prepare_seed`'s LLM outputs `arc` at the top level of the JSON (like current flow) — simpler but means `prepare_seed`'s prompt schema needs a top-level `arc` field.

- **[WARN] `SeedState` has `actions` (pack.py:75) and `arc` (pack.py:73) — these exist on both `SeedState` and `SeedEnvelope`.**
  `SeedState` at `pack.py:75` has `actions: list[str] = Field(default_factory=list)`. `SeedEnvelope` at `pack.py:91` has `actions: list[str] = Field(min_length=4, max_length=4)`. Same for `arc` and `arc_origin`. The current flow puts `opening_narrative` and `actions` on `SeedEnvelope` only (not copied to `SeedState`), but `arc` and `arc_origin` are copied from `SeedEnvelope` top-level into `SeedState` at `seed.py:357-361`.
  **Fix:** `prepare_seed` puts `arc` inside `seed_state.arc` (as part of `SeedState`). `narrate_seed` puts `opening_narrative`, `actions`, and `outcome_summary` on the final `SeedEnvelope` (not in `SeedState`). The plan should clarify that `SeedState.actions` is unused — `actions` lives only on `SeedEnvelope`.

### Design Ambiguities

- `[QUESTION]` `pool_selection` flow. The current `generate_seed` returns `tuple[SeedEnvelope, dict[str, Any] | None]` — `pool_selection` alongside the envelope. Should `prepare_seed` also return `pool_selection` (as part of `SeedStateEnvelope`)? The design says `narrate_seed` receives `pool_selection` as a separate input — this is fine, but the plan should clarify whether `pool_selection` flows through the return type or as a separate parameter.

- `[QUESTION]` `prepare_seed`'s prompt schema. The current prompt schema shows a `SeedEnvelope` shape (with `opening_narrative`, `actions`, `outcome_summary` at the top level). The plan author will need to rewrite the schema section of `prepare_seed_system.j2` to show only `SeedState` fields (plus `arc` at the top level if the simpler approach is chosen — see CRITICAL #3).

- `[QUESTION]` `narrate_seed` input type. Should `narrate_seed` accept `SeedState` (Pydantic model) or `dict[str, Any]`? The design says "validated dict" but the type hint in the handoff section shows `envelope.seed_state` which is a `SeedState` model. Using `SeedState` directly avoids serialization/deserialization overhead.

- `[QUESTION]` `narrate_seed` prompt rendering. The design says `narrate_seed` prompt should include "The full structured `SeedState` rendered as context" — but how? The current narrate prompt uses a Jinja2 template that renders game state from a context dict. Should `narrate_seed_system.j2` follow the same pattern? The plan author will need to design the template rendering approach.

- `[QUESTION]` `prepare_seed` should remove "weave in pc_situation / arc_origin / world facts / key locations" instructions from the prompt. But these instructions are in the `prepare_seed_system.j2` prompt — if they're removed, the LLM won't know to generate these fields consistently. The design should clarify that these instructions stay in `prepare_seed` (for generation) and are only removed from `narrate_seed` (for weaving).

### Suggested Improvements

- **[WARN] `prepare_seed` prompt will still be very large.** The design keeps generation order 1–6, schema definition, field requirements, personality archetype table, thread rules, NPC field requirements, PC field rules, key locations rules, PC situation rules, inventory rules, and world state rules. This is roughly 200 lines — comparable to the current prompt. The cognitive load on the LLM is similar. The temperature change (0.4 vs 0.9) is the key improvement, not the prompt simplification. The plan should acknowledge that `prepare_seed`'s prompt is still large and complex.

- **[WARN] `narrate_seed` prompt will receive a full `SeedState` rendered as context.** A `SeedState` with compendium NPCs, inventory, world facts, arc threads, and pc_situation could easily exceed 2000 tokens. At narrate temperature 0.9, the LLM might truncate its own context or produce lower-quality prose due to context bloat. The plan should consider whether `narrate_seed` needs a context filtering step (e.g., only pass pc_situation, arc_origin, key_locations, and a summary of NPCs).

- **[WARN] Two LLM calls means two timeouts.** The current `request_timeout_s: 1200` (20 minutes) is generous. With two calls, the total timeout could be 40 minutes if both hit the limit. The plan should consider whether `request_timeout_s` should apply per-call or per-seed-generation.

- **[WARN] `prepare_seed` and `narrate_seed` share the same `trace_id` generation.** The current `generate_seed` generates a single `trace_id` at the start. With two steps, the plan should decide whether to use one trace_id for both steps (easier debugging) or separate trace_ids (more granular).

### Minor Notes

- The design says `prepare_seed` returns a "partial `SeedState`" but the type is `SeedEnvelope`. The terminology should be consistent — use `SeedEnvelope` throughout.

- The design says `generate_seed_user.j2` content is "only rename, no content change" — but the current `generate_seed_user.j2` might contain narrative instructions that need to be removed for `prepare_seed_user.j2`. The plan should verify the user prompt content.

- The design says `narrate_seed` reuses `narrate_temperature` but the current `narrate_temperature` default in `config.py:125` is 0.9 while `config.yaml` also shows 0.9. These match, so no issue — but the design should note that `narrate_seed` inherits narrate's `top_p` and `frequency_penalty` as well.

- The design says `prepare_seed` temperature is "not configurable per-environment in the initial implementation" — but `prepare_seed_temperature` is a field on `EngineConfig` that gets read from config. The plan should clarify whether this means "hardcoded in the function" or "read from config but not exposed in the UI."

- The design says `SeedEnvelope` is unchanged but the current `SeedEnvelope` has `opening_narrative: str = Field(min_length=50)`. If `prepare_seed` returns a `SeedEnvelope` with an empty string for `opening_narrative`, Pydantic validation will fail. The design should clarify that `prepare_seed` returns a `SeedEnvelope` with `opening_narrative=""` and that the validation is skipped or deferred to after `narrate_seed`.

- The design says `prepare_seed` returns a `SeedEnvelope` but the current `generate_seed` returns `tuple[SeedEnvelope, dict[str, Any] | None]`. The plan should clarify whether `prepare_seed` also returns `pool_selection` or whether `pool_selection` is passed as a separate parameter to `narrate_seed`.
