# Plan: Split Seed Generation into prepare_seed + narrate_seed

**Derived from:** [Seed Two-Step Design](../docs/design/seed-two-step-design.md)
**Ticket:** [F-23](../../roadmap/features/F-23-split-seed-generation-into-prepareseed-narrateseed.md)
**Date:** 2026-06-29

---

## Purpose

Split the single `generate_seed()` LLM call into two sequential calls: `prepare_seed()` (low temp, structured JSON) and `narrate_seed()` (high temp, creative prose). This resolves the temperature tension where low temp gives reliable JSON but formulaic narration, and high temp gives vivid prose but ~50% JSON parse failures.

## Problem

Seed generation makes a single LLM call producing both structured game state (world facts, locations, PC situation, arc, NPCs, inventory) and creative prose (opening_narrative, actions, outcome_summary). These outputs have opposite temperature requirements:

- **Structured JSON:** needs 0.2–0.5 for reliable schema conformance
- **Creative prose:** needs 0.7–0.9 for vivid, non-generic narration

At 0.9, ~50% of first attempts fail with "No JSON found". At 0.65, reliability improves to ~80% but narration becomes formulaic. One call cannot optimize both.

## Scope

- New `SeedStateEnvelope` model in `ccya/pack.py`
- Config migration (`generate_seed` → `prepare_seed`)
- Prompt template changes (rename, clean, create new)
- Split `ccya/engine/seed.py` into `prepare_seed()` + `narrate_seed()`
- Route handler updates (`new_game`, `new_game_reroll`)
- Eval harness updates (`play.py`, `eval.py`)
- Engine exports (`__init__.py`)
- Documentation updates

## Out of Scope

- Changing `SeedEnvelope` or `SeedState` model shapes
- Changing NPC generation
- Changing world state schema
- Pack parity (generated/custom packs)
- Location tracking system
- Per-step retry counts in config

## Firm Decisions

- **Two sequential LLM calls.** `prepare_seed()` at 0.55 temp → `SeedStateEnvelope` → `narrate_seed()` at 0.9 temp → final `SeedEnvelope`.
- **`SeedStateEnvelope` as new type.** Wraps `SeedState` without narrative `min_length` constraints. No `min_length` on `opening_narrative`, `actions`, `outcome_summary`.
- **Hard fail safety.** Each step gets 1 retry. If either fails after retries, game does not start. Clear log message on hard fail.
- **Clean break.** No backward compatibility. `generate_seed` fully replaced by `prepare_seed`. `generate_seed_system.j2` renamed and cleaned. New `narrate_seed_system.j2` created.
- **`temperature_override` excludes seed steps.** The override (used by `ev.py play --temperature`) applies only to `ruling`, `extract`, and `narrate`. `prepare_seed` and `narrate_seed` always use their config defaults.
- **Arc/arc_origin in prompt schema only inside `seed_state`.** Funnel general → specific maintained. Post-processing reads from `seed_state.arc` directly (no copy from envelope.arc).
- **Context passed to `narrate_seed`:** pc (name, tagline, bio, stats, conditions, situation), location, arc_origin, world.locations (key locations), inventory (only if relevant), pool_selection. NOT passed: world_state, compendium.npcs, arc threads/objective, meta.
- **`pool_selection` passed via `SeedStateEnvelope.pool_selection`.** Scene bundle is 3 small arrays — negligible context cost, simpler than subsetting. Pool pre-selection stays in `prepare_seed`.
- **Standalone functions.** `prepare_seed()` and `narrate_seed()` are two standalone async functions called sequentially. No wrapper.
- **`narrate_seed_system.j2` prompt template.** Follows the same Jinja2 template pattern as existing `narrate_system.j2`. Receives a context dict with filtered SeedState fields. Open Question resolved: prompt uses Jinja2 template with context dict containing pc, location, arc_origin, world.locations, inventory, pool_selection.

## Risks

- **Latency increase.** Two sequential LLM calls instead of one. Each call is faster (shorter prompts, simpler output), but net latency is ~1.3–1.5× the current single call. Acceptable for a one-time operation at game start.
- **Prompt template design.** `narrate_seed_system.j2` needs careful design to produce high-quality prose from structured context without the guidance of generation rules.
- **Hard fail at game start.** If either step fails, the game does not start. This is intentional (better to fail than boot into stateless void), but means users see an error instead of a broken game.

---

## Phase 01: Model and config changes

**Files:**
- `ccya/pack.py` — add `SeedStateEnvelope` model
- `ccya/engine/config.py` — rename config fields, exclude seed from override
- `config.yaml` — rename key, update temperature

**What:** Add `SeedStateEnvelope` model. Rename config fields. Update config.yaml.

**Why:** New model wraps `SeedState` without narrative constraints. Config migration from `generate_seed` to `prepare_seed`.

**Interface contract — `SeedStateEnvelope`:**
```python
class SeedStateEnvelope(BaseModel):
    seed_state: SeedState
    opening_narrative: str = ""
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""
    arc: LongTermObjective | None = None
    arc_origin: str = ""
    pool_selection: dict[str, Any] | None = None
```

**Config changes:**
- `EngineConfig.generate_seed_temperature` → `EngineConfig.prepare_seed_temperature` (default 0.55)
- `EngineConfig.generate_seed_top_p` → `EngineConfig.prepare_seed_top_p` (default 0.95)
- `build_engine_config()` reads `llm.prepare_seed` instead of `llm.generate_seed`
- `temperature_override` does NOT apply to `prepare_seed_temperature`

**Validation:**
- `SeedStateEnvelope` model exists in `ccya/pack.py` with no `min_length` constraints on narrative fields
- `EngineConfig` has `prepare_seed_temperature` (default 0.55) and `prepare_seed_top_p` (default 0.95)
- `build_engine_config()` reads `llm.prepare_seed` config key
- `temperature_override` does not override `prepare_seed_temperature`
- `config.yaml` has `llm.prepare_seed` instead of `llm.generate_seed`

---

## Phase 02: Prompt template changes

**Files:**
- `ccya/prompts/generate_seed_system.j2` → `ccya/prompts/prepare_seed_system.j2` (rename + clean)
- `ccya/prompts/generate_seed_user.j2` → `ccya/prompts/prepare_seed_user.j2` (rename + update)
- `ccya/prompts/narrate_seed_system.j2` (new file)

**What:** Rename prompt templates. Clean `prepare_seed_system.j2` (remove narrative sections). Create `narrate_seed_system.j2`.

**Why:** `prepare_seed` prompt should only contain generation rules (what to produce). `narrate_seed` prompt should only contain prose instructions (how to write).

**prepare_seed_system.j2 changes:**
1. Rename from `generate_seed_system.j2`
2. Remove narrative prose instructions (lines 197–236):
   - Opening narrative instructions (3-movement structure, sensory detail, second person)
   - Actions section (4 choices, posture requirements)
   - Outcome summary section
   - All "weave in pc_situation / arc_origin / world facts / key locations" prose instructions
3. Keep generation rules (what the LLM should produce):
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
5. Schema shows `arc` and `arc_origin` only inside `seed_state` (not at top level)

**prepare_seed_user.j2 changes:**
1. Rename from `generate_seed_user.j2`
2. Update JSON output discipline section for narrower output (SeedState only, not SeedEnvelope)

**narrate_seed_system.j2 — new prompt template:**

Context dict passed to template:
```python
{
    "pc": {
        "name": str,
        "tagline": str,
        "bio": str,
        "stats": dict[str, int],
        "conditions": list[str],
        "situation": dict[str, str],
    },
    "location": {
        "id": str,
        "name": str,
        "description": str,
    },
    "arc_origin": str,
    "world_locations": list[dict[str, Any]],  # key locations from seed_state.world.locations
    "inventory_items": list[dict[str, Any]],  # only if relevant to opening moment
    "pool_selection": dict[str, Any] | None,  # scene bundle ingredients
}
```

Prompt structure (Jinja2 template):
```
Opening narrative instructions (3-movement structure, second person, present tense)
- Close-up: 1-3 sentences, one live sensory detail
- Exposition: what is around the PC, weave in environmental details
- Crisis moment: tension arrives, NPCs act, moment player must respond

Weaving instructions:
- Weave in pc.situation naturally (establish PC's baseline)
- Weave in arc_origin naturally (world-level event as background pressure)
- Scene must be set in or near one of the key locations
- If a present NPC has personal tie to PC, show through action/dialogue
- If compendium NPC known to PC but not present, reference naturally

Actions (exactly 4, 7-10 words each, active voice):
- At least 2 advance arc goal or active thread
- One involves named NPC present in scene
- One is environmental
- One is freeform rooted in PC background/motivation
- Span different postures
- No generic verbs
- At least 2 reveal character priorities/relationships

Outcome summary (one sentence, 10-20 words, third person, factual)

Pool selection context (if pool_selection is not None):
- Scene bundle ingredients (items, conditions, sensory)
```

**Validation:**
- `prepare_seed_system.j2` exists, narrative sections removed, schema shows SeedState only
- `prepare_seed_user.j2` exists, JSON output discipline updated
- `narrate_seed_system.j2` exists with opening narrative, actions, outcome summary instructions
- `narrate_seed_system.j2` receives filtered context (pc, location, arc_origin, world_locations, inventory_items, pool_selection)

---

## Phase 03: Split seed.py into prepare_seed + narrate_seed

**Files:**
- `ccya/engine/seed.py` — rename, split, update validation

**What:** Rename `generate_seed()` → `prepare_seed()`. Add `narrate_seed()`. Split message builders. Update validation.

**Why:** Two-step pipeline requires separate functions for structured JSON generation and prose generation.

**prepare_seed() changes:**
1. Rename from `generate_seed()`
2. New signature: `async def prepare_seed(pack, config, *, overrides=None, seed=None, template_dir=None) -> tuple[SeedStateEnvelope, dict[str, Any] | None]`
3. Returns `SeedStateEnvelope` (not `SeedEnvelope`)
4. Rename `_build_generate_seed_messages()` → `_build_prepare_seed_messages()`
5. Update prompt template references: `prepare_seed_system.j2`, `prepare_seed_user.j2`
6. Update temperature: `config.prepare_seed_temperature` instead of `config.generate_seed_temperature`
7. Update top_p: `config.prepare_seed_top_p` instead of `config.generate_seed_top_p`
8. Update log messages: `prepare_seed` instead of `generate_seed`
9. Update JSON parsing: expects `SeedState` shape (not `SeedEnvelope`), unwrap if nested under "seed_state" key
10. Validate against `SeedState` Pydantic model (not `SeedEnvelope`)
11. Remove arc copy logic (lines 381-385): arc and arc_origin are already inside `seed_state`
12. Update thread limit enforcement to read from `seed_state.arc` directly (not `envelope.arc`)
13. Update `_soft_validate_seed()` — remove cliché check (opening_narrative doesn't exist at prepare_seed time). The soft validation should be moved to post-`narrate_seed` or removed entirely.
14. Hard fail if prepare_seed fails after retries (each gets 1 retry). Clear log message.

**narrate_seed() — new function:**
```python
async def narrate_seed(
    seed_state: SeedState,
    config: EngineConfig,
    *,
    pack: Pack | None = None,
    pool_selection: dict[str, Any] | None = None,
    template_dir: str | None = None,
) -> dict[str, Any]:
    """Generate opening_narrative, actions, outcome_summary from validated SeedState.
    
    Returns dict with exactly:
    - opening_narrative: str (min_length=50)
    - actions: list[str] (min_length=4, max_length=4)
    - outcome_summary: str
    """
```

**_build_narrate_seed_messages() — new function:**
```python
def _build_narrate_seed_messages(
    env: Environment,
    seed_state: SeedState,
    pool_selection: dict[str, Any] | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any] | None]:
    """Build prompt for narrate_seed from filtered SeedState context.
    
    Context passed to template:
    - pc.name, pc.tagline, pc.bio, pc.stats, pc.conditions, pc.situation
    - location.id, location.name, location.description
    - arc_origin
    - world.locations (key locations)
    - inventory.items (only if relevant)
    - pool_selection (scene bundle ingredients)
    
    NOT passed: world_state, compendium.npcs, arc threads/objective, meta
    """
```

**_soft_validate_seed() changes:**
- Remove cliché check (opening_narrative doesn't exist at prepare_seed time)
- This function should be removed entirely or moved to post-`narrate_seed` validation

**Validation:**
- `prepare_seed()` returns `SeedStateEnvelope` with `seed_state: SeedState`
- `narrate_seed()` returns dict with `opening_narrative`, `actions`, `outcome_summary`
- `_build_prepare_seed_messages()` uses `prepare_seed_system.j2` and `prepare_seed_user.j2`
- `_build_narrate_seed_messages()` uses `narrate_seed_system.j2` with filtered context
- Arc copy logic removed (arc/arc_origin already inside seed_state)
- Thread limit enforcement reads from `seed_state.arc` directly
- `_soft_validate_seed()` no longer checks opening_narrative clichés
- Hard fail on prepare_seed or narrate_seed failure (each gets 1 retry)

---

## Phase 04: Update callers

**Files:**
- `ccya/engine/__init__.py` — add `narrate_seed` export
- `ccya/server/routes.py` — new_game, new_game_reroll
- `ccya/ev/play.py` — _ensure_seed_generated, config key rename
- `ccya/ev/eval.py` — config override cleanup

**What:** Update all callers to use new two-step pipeline.

**Why:** Route handlers and eval harness need to call `prepare_seed()` then `narrate_seed()` sequentially.

**engine/__init__.py changes:**
- Add `narrate_seed` to imports and `__all__`
- Rename `generate_seed` import to `prepare_seed`

**routes.py changes:**
- `new_game` route: call `prepare_seed()` then `narrate_seed()` sequentially
  - `partial = await prepare_seed(...)` → `SeedStateEnvelope`
  - `narrate_fields = await narrate_seed(partial.seed_state, ..., pool_selection=partial.pool_selection)` → dict
  - Assemble final `SeedEnvelope`:
    ```python
    final_envelope = SeedEnvelope(
        seed_state=partial.seed_state,
        opening_narrative=narrate_fields["opening_narrative"],
        actions=narrate_fields["actions"],
        outcome_summary=narrate_fields["outcome_summary"],
        arc=partial.seed_state.arc,
        arc_origin=partial.seed_state.arc_origin,
    )
    ```
  - Pass `final_envelope` to `_apply_seed_to_save_dir()` (unchanged)
- `new_game_reroll` route: same pattern (no overrides)

**play.py changes:**
- `_ensure_seed_generated()`: call `prepare_seed()` then `narrate_seed()` sequentially
  - Same assembly pattern as routes.py
- Rename config read from `generate_seed` to `prepare_seed` in `_build_play_config()`
- Update `_build_play_config()` temperature override: replace `generate_seed` with `prepare_seed` in the override list

**eval.py changes:**
- `_build_eval_config()`: replace `generate_seed` with `prepare_seed` in temperature override list

**Validation:**
- `engine/__init__.py` exports `prepare_seed` and `narrate_seed`
- `routes.py` new_game calls prepare_seed → narrate_seed → assembles SeedEnvelope
- `routes.py` new_game_reroll calls prepare_seed → narrate_seed → assembles SeedEnvelope
- `play.py` _ensure_seed_generated calls prepare_seed → narrate_seed → assembles SeedEnvelope
- `play.py` _build_play_config uses `prepare_seed` in temperature override
- `eval.py` _build_eval_config uses `prepare_seed` in temperature override

---

## Phase 05: Documentation updates

**Files:**
- `docs/architecture/OVERVIEW.md` — update pipeline overview (two-step seed generation)
- `docs/repomap.md` — update module boundaries, signatures, public APIs
- `AGENTS.md` — update build commands, signposts if needed

**What:** Update all documentation to reflect changes.

**Why:** AGENTS.md mandates doc updates when models, prompts, or engine behavior change.

**OVERVIEW.md changes:**
- Update seed generation section: single call → two-step pipeline
- Document `prepare_seed()` → `SeedStateEnvelope` → `narrate_seed()` → `SeedEnvelope` flow
- Document temperature separation (0.55 for prepare_seed, 0.9 for narrate_seed)

**repomap.md changes:**
- Update `ccya/engine/seed.py` entry: `generate_seed()` → `prepare_seed()` + `narrate_seed()`
- Add `SeedStateEnvelope` to `ccya/pack.py` entry
- Update config entry: `generate_seed_temperature` → `prepare_seed_temperature`

**Validation:**
- `docs/architecture/OVERVIEW.md` documents two-step seed generation pipeline
- `docs/repomap.md` reflects new function signatures and model additions
- `AGENTS.md` updated if build commands or signposts changed

---

## Verification

After all phases:
1. `make check` — lint + typecheck must pass
 2. Start a new game via server — verify two-step seed generation (prepare_seed at 0.4, narrate_seed at 0.9)
3. Reroll seed — verify same two-step pipeline
4. Run `ev.py play --pack <pack>` — verify seed generation works in eval harness
5. Run `ev.py eval <scenario.yaml>` — verify config override uses `prepare_seed` not `generate_seed`
 6. Verify `temperature_override` does NOT affect `prepare_seed_temperature` (use `ev.py play --temp N` and confirm prepare_seed still uses 0.4)
7. Verify hard fail: if prepare_seed or narrate_seed fails after 1 retry, game does not start
8. Verify prompt templates: `prepare_seed_system.j2` has no narrative sections, `narrate_seed_system.j2` has opening narrative/actions/outcome_summary instructions
9. Verify `SeedStateEnvelope` has no `min_length` constraints on narrative fields
 10. Verify arc/arc_origin read from `seed_state.arc` directly (no copy from envelope.arc)

---

## Status

completed — all 5 phases implemented on 2026-06-29. Branch: `seed-two-step`.
