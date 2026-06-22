# Seed Generation Fixes — Skip on Hints, Remove Inventory, Sharpen Instructions

## Purpose

When the player provides hints at character creation, skip LLM seed generation and use the scenario's static seed_state.yaml as fallback. Remove inventory from seed generation instructions. Sharpen seed prompt instructions for better turn 1 integration.

## Problem Statement

When both seed JSON (LLM-generated) and player hints are provided at game creation, they conflict — both inject into the same initial state, causing compendium duplication, missing NPCs, bond issues, and location never changing. The seed JSON should be disabled when hints are provided.

Additionally, seed inventory is rarely used in gameplay and sometimes confuses the inventory extractor. The 2-item skill-tie rule (already removed in a completed plan) was the original source of confusion, but the entire seed inventory concept should be removed since PCs naturally acquire inventory through gameplay.

Finally, turn 1 narration doesn't actively use seed data — it lists things rather than weaving them into narrative choices and arc setup.

## Constraints

- No backward compatibility required — dead code can be removed outright.
- When hints are provided, skip LLM seed generation entirely and use static pack defaults.
- Inventory is removed from seed generation instructions entirely.
- Turn 1 integration is prompt-only — no structural changes to the pipeline.
- No seed quality gate — current retry logic is sufficient.
- Tests temporarily removed per AGENTS.md.

## Non-goals

- No selective merge logic (skip/merge based on which hint fields are populated).
- No programmatic seed generation as fallback (static pack defaults only).
- No structural changes to the turn pipeline for seed data integration.
- No changes to how static packs work (they already exist and are loaded correctly).
- No changes to runtime inventory mechanics (PCs still get inventory through gameplay).
- No changes to the personality assignment system (already completed).
- No changes to NPC compendium at seed time (already handled by completed plans).

## Solution

Three coordinated changes:

1. **Route change:** In `new_game` route, check if any hint field is populated. If yes, skip `generate_seed()` and load the static pack's `seed_state.yaml` instead via `_apply_seed_to_save_dir()`.

2. **Remove inventory from seed instructions:** Remove all inventory generation guidance from `generate_seed_system.j2`. The LLM should not generate inventory at seed time.

3. **Sharpen turn 1 integration:** Update `generate_seed_system.j2` instructions to weave seed data naturally into the opening narration. Arc tension, NPC relationships, and location details should be woven into the narrative, not listed.

## Firm decisions

1. **Skip entirely, not selectively.** If any hint field is populated, skip LLM seed generation. No selective merge logic.
2. **Static pack fallback.** When skipping, use the scenario's `seed_state.yaml` as the game state. Player gets a baseline game.
3. **Remove inventory entirely.** No inventory items generated at seed time. PCs acquire inventory through gameplay.
4. **Prompt-only turn 1 integration.** Sharpen `generate_seed_system.j2` instructions to weave seed data naturally. No structural changes to the pipeline.
5. **No quality gate.** Current retry logic is sufficient. Adding validation adds complexity for marginal gain.

## Risks, Ambiguities, and Blockers

- **Static pack quality varies:** Some static packs may have thin or outdated seed_state.yaml. Players who provide hints but get a static fallback may be disappointed. Mitigation: ensure all default packs have reasonable seed_state.yaml files.
- **Player expectation mismatch:** Players who fill out the character creation form expecting custom content may be confused when they get a static fallback. The UI should communicate this clearly.
- **Inventory removal may affect some packs:** Packs that rely on seed inventory for gameplay may break. Mitigation: verify all packs have `required_inventory_kinds` or other mechanisms to provide starting items.
- **Turn 1 integration is prompt-only:** The LLM may not weave seed data naturally even with good instructions. Monitor extraction logs for compliance.

## Status
`completed`

## Phases

3 phases covering: (1) route change to skip seed on hints, (2) remove inventory from seed instructions, (3) sharpen turn 1 integration instructions.

---

## Implementation — Phase 1: Route change to skip seed on hints

### Context files to load
- `ccya/server/routes.py` — `new_game` route (lines 368-442)
- `ccya/pack.py` — `PlayerOverrides` model (lines 184-206), `is_empty()` method
- `ccya/pack.py` — `load_pack()` function (lines 259-314) for understanding static pack loading
- `ccya/state/io.py` — `init_save_dir()` (lines 147-160) for understanding how seeds are applied

### Detailed steps

#### Step 1.1 — Add hint check to `new_game` route

**File:** `ccya/server/routes.py`, `new_game` route (lines 368-442)

**What:** After building the `overrides` object (line 404-411), check if any hint field is populated. If yes, skip `generate_seed()` and load the static pack's seed_state.yaml instead.

Replace the seed generation block (lines 426-438):

Current:
```python
    try:
        envelope, pool_selection = await generate_seed(
            _app_mod._active_pack,
            _app_mod.engine_config,
            template_dir=str(_app_mod.PROMPTS_DIR),
            overrides=overrides if not overrides.is_empty() else None,
        )
        seed = envelope.seed_state.model_dump(mode="json")
        seed["meta"]["setting_pack"] = _app_mod._pack_id
        _apply_seed_to_save_dir(seed, envelope.opening_narrative, envelope.actions, outcome_summary=envelope.outcome_summary, pack_type="dynamic", pack_source=_app_mod._pack_id, pool_selection=pool_selection)
    except Exception as exc:
        _app_mod.logger.exception("generate_seed failed")
        return HTMLResponse(f"<p class='text-red-400'>Seed generation failed: {exc}</p>")
```

With:
```python
    try:
        if overrides.is_empty():
            # No hints — generate seed via LLM
            envelope, pool_selection = await generate_seed(
                _app_mod._active_pack,
                _app_mod.engine_config,
                template_dir=str(_app_mod.PROMPTS_DIR),
                overrides=None,
            )
            seed = envelope.seed_state.model_dump(mode="json")
            seed["meta"]["setting_pack"] = _app_mod._pack_id
            _apply_seed_to_save_dir(seed, envelope.opening_narrative, envelope.actions, outcome_summary=envelope.outcome_summary, pack_type="dynamic", pack_source=_app_mod._pack_id, pool_selection=pool_selection)
        else:
            # Hints provided — use static pack seed as fallback
            _log.info("new_game hints provided, using static pack seed pack=%s", _app_mod._pack_id)
            pack = _app_mod._active_pack
            if pack.seed is None:
                return HTMLResponse("<p class='text-red-400'>This pack has no static seed state. Provide no hints to generate a custom game.</p>")
            seed = pack.seed.model_dump(mode="json")
            seed["meta"]["setting_pack"] = _app_mod._pack_id
            _apply_seed_to_save_dir(seed, None, None, pack_type="static", pack_source=_app_mod._pack_id)
    except Exception as exc:
        _app_mod.logger.exception("new_game failed")
        return HTMLResponse(f"<p class='text-red-400'>Game creation failed: {exc}</p>")
```

**Why:** When hints are provided, the player has expressed intent for the game. LLM seed generation would conflict with that intent. Using the static pack's seed_state.yaml as fallback gives the player a baseline game that they can then shape through their hints during gameplay.

**Validation:**
1. Start a game with no hints — should use LLM seed generation (existing behavior).
2. Start a game with any hint field populated — should use static pack seed.
3. Start a game with hints on a pack without static seed — should show error message.

#### Step 1.2 — Update `docs/repomap.md` new_game route section

**File:** `docs/repomap.md`

**What:** Add a new section documenting the route change in the new_game route. Search for the route handler section in repomap and add notes about the hint-detection logic and static pack fallback behavior.

**Why:** AGENTS.md mandates documentation updates for route changes. The route behavior change (hint detection → static fallback) is a public API change that affects how players interact with the system.

**Validation:** Grep `docs/repomap.md` for "new_game" — should include the new hint-detection and static fallback behavior.

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

---

## Implementation — Phase 2: Remove inventory from seed instructions

### Context files to load
- `ccya/prompts/generate_seed_system.j2` (full file, 174 lines)
- `ccya/prompts/generate_seed_user.j2` (full file, 97 lines)
- `ccya/pack.py` — `Constraints` model for `required_inventory_kinds` to understand if packs provide inventory through other mechanisms

### Detailed steps

#### Step 2.1 — Remove inventory section from seed system prompt

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Remove the entire "## Inventory rules" section (lines 112-118). Also remove inventory from the schema comment (line 34).

Remove lines 112-118 (the "## Inventory rules" section):
```
## Inventory rules
- 3–6 items appropriate to the opening scene and PC concept.
- Every item has a specific, proper name — not "standard issue rifle" or "random book." Names should hint at why the item matters.
- Firearms always come paired with an ammo item at a realistic starting count. Never put loaded counts in weapon `notes`.
- Items with finite uses must have an explicit `amount`. Melee and single-shot thrown items are exempt.
- No exotic or legendary weapons at start. No items for skills the PC hasn't invested in.
- Inventory item names start with a capital letter.
```

Update line 34 (schema comment) — remove the `inventory` line:
Replace:
```ts
    inventory: Array<{id: snake_case, name: string, notes?: string, amount: int}>,
```
With:
```ts
    // inventory: removed — PCs acquire items through gameplay
```

**Why:** Seed inventory is rarely used in gameplay and sometimes confuses the inventory extractor. PCs naturally acquire inventory through gameplay. Removing it simplifies seed generation and reduces extraction noise.

**Validation:** Grep `generate_seed_system.j2` for "inventory" — should only find the commented-out schema line and any references to `required_inventory_kinds` in the hard constraints section (which should remain, as packs may still define required inventory kinds for other purposes).

#### Step 2.2 — Update generation order in seed system prompt

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Update the "Generation order" section (lines 55-72) to remove inventory from the generation sequence.

Replace lines 55-72:

Current:
```
## Generation order — wide to narrow

Build in this order, using everything already established before generating what comes next:

1. **PC** — bio, stats, tagline. Must be consistent with `character_dynamic`.
2. **World state** — 3 immutable hard constraints that directly affect gameplay choices now (border closures, martial law, banned technologies, faction blockades). No historical backstory older than one generation unless it's an active constraint today. No flavor lore. Fewer high-quality facts beats many generic ones.
3. **Campaign arc** — informed by PC, world state, situation archetype, and character dynamic:
   - `visible_goal`: multi-stage objective. What happens after the first step succeeds? After it fails?
   - `goal_context`: 2–3 sentences on why this goal matters to this character specifically — inner cost, emotional stakes. Don't restate visible_goal or leak hidden truths.
   - `threads`: see Thread rules below.
4. **Opening scene + NPCs** — instantiates the situation archetype concretely.
5. **Inventory** — appropriate to scene and PC concept.
```

With:
```
## Generation order — wide to narrow

Build in this order, using everything already established before generating what comes next:

1. **PC** — bio, stats, tagline. Must be consistent with `character_dynamic`.
2. **World state** — 3 immutable hard constraints that directly affect gameplay choices now (border closures, martial law, banned technologies, faction blockades). No historical backstory older than one generation unless it's an active constraint today. No flavor lore. Fewer high-quality facts beats many generic ones.
3. **Campaign arc** — informed by PC, world state, situation archetype, and character dynamic:
   - `visible_goal`: multi-stage objective. What happens after the first step succeeds? After it fails?
   - `goal_context`: 2–3 sentences on why this goal matters to this character specifically — inner cost, emotional stakes. Don't restate visible_goal or leak hidden truths.
   - `threads`: see Thread rules below.
4. **Opening scene + NPCs** — instantiates the situation archetype concretely.
```

**Why:** Inventory is no longer generated at seed time. The generation order should reflect what's actually being generated.

**Validation:** Read the updated template — should have 4 generation steps, not 5.

#### Step 2.3 — Update `docs/repomap.md` seed system prompt section

**File:** `docs/repomap.md`

**What:** Update the seed system prompt section (line 189) to reflect:
- Inventory section removed from generation order
- Inventory rules section removed
- Schema comment updated to note inventory removal
- Opening narrative instructions now include weaving guidance for world state facts, NPC relationships, and compendium NPCs

**Why:** AGENTS.md mandates documentation updates for prompt changes. The seed system prompt is a documented public API in the repomap.

**Validation:** Grep `docs/repomap.md` for "generate_seed_system" — should reflect inventory removal and weaving instructions.

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

---

## Implementation — Phase 3: Sharpen turn 1 integration instructions

### Context files to load
- `ccya/prompts/generate_seed_system.j2` (full file, 174 lines)
- `ccya/prompts/generate_seed_user.j2` (full file, 97 lines)

### Detailed steps

#### Step 3.1 — Sharpen opening narrative instructions for seed data integration

**File:** `ccya/prompts/generate_seed_system.j2`, "## Opening narrative" section (lines 140-156)

**What:** Update the opening narrative instructions to weave seed data naturally into the narration. Arc tension, NPC relationships, and location details should be woven into the narrative, not listed.

Replace lines 140-156:

Current:
```
## Opening narrative

~700 words. Second person, present tense. Three movements:

1. **Close-up** (1–3 sentences): One live sensory detail that orients the player in the character's immediate physical reality. No summary, no biography.
2. **Exposition** (middle): What is around the PC — weave in 1–2 environmental details that imply recent action, conflict, or presence. Every detail should do work.
   {% if pool_selection and pool_selection.scene_bundle -%}
   Optional ingredients (use what fits):
   {% if pool_selection["scene_bundle"]["items"] %}Objects: {{ pool_selection["scene_bundle"]["items"] | join(", ") }}.{% endif %}
   {% if pool_selection["scene_bundle"]["conditions"] %}Conditions: {{ pool_selection["scene_bundle"]["conditions"] | join(", ") }}.{% endif %}
   {% if pool_selection["scene_bundle"]["sensory"] %}Sensory: {{ pool_selection["scene_bundle"]["sensory"] | join(", ") }}.{% endif %}
   {%- endif %}
3. **Crisis moment** (the bulk): The tension arrives. Present NPCs act. The moment the player must respond to. Spend most of your words here.

- Bold NPC names on first introduction. Bold inventory item names on first use.
- NPCs appear in action, not in introduction.
- Let arc tension surface through what the player observes, not what the narrator announces.
```

With:
```
## Opening narrative

~700 words. Second person, present tense. Three movements:

1. **Close-up** (1–3 sentences): One live sensory detail that orients the player in the character's immediate physical reality. No summary, no biography.
2. **Exposition** (middle): What is around the PC — weave in 1–2 environmental details that imply recent action, conflict, or presence. Every detail should do work.
   {% if pool_selection and pool_selection.scene_bundle -%}
   Optional ingredients (use what fits):
   {% if pool_selection["scene_bundle"]["items"] %}Objects: {{ pool_selection["scene_bundle"]["items"] | join(", ") }}.{% endif %}
   {% if pool_selection["scene_bundle"]["conditions"] %}Conditions: {{ pool_selection["scene_bundle"]["conditions"] | join(", ") }}.{% endif %}
   {% if pool_selection["scene_bundle"]["sensory"] %}Sensory: {{ pool_selection["scene_bundle"]["sensory"] | join(", ") }}.{% endif %}
   {%- endif %}
3. **Crisis moment** (the bulk): The tension arrives. Present NPCs act. The moment the player must respond to. Spend most of your words here.

- Bold NPC names on first introduction.
- NPCs appear in action, not in introduction.
- Let arc tension surface through what the player observes, not what the narrator announces.
- Weave in world state facts naturally — don't list them. If a border closure is a world fact, show its effect (a checkpoint, a denied passage) rather than stating it.
- If a present NPC has a personal tie to the PC (shared history, debt, emotional bond), show it through action or dialogue — not exposition.
- If there's a compendium NPC known to the PC but not present, reference them naturally in narration (a phone call, a rumor, a memory).
```

**Why:** The current instructions tell the LLM to weave details but don't specify which seed data should be woven. The new instructions explicitly tell the LLM to weave world state facts, NPC relationships, and compendium NPCs into the narration naturally.

**Validation:** Read the updated template — should contain explicit instructions for weaving world state, NPC relationships, and compendium NPCs into narration.

#### Step 3.2 — Remove "Bold inventory item names" instruction

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Remove "Bold inventory item names on first use" from the opening narrative bullet points (line 154).

Replace:
```
- Bold NPC names on first introduction. Bold inventory item names on first use.
```
With:
```
- Bold NPC names on first introduction.
```

**Why:** Inventory is no longer generated at seed time, so there are no inventory item names to bold.

**Validation:** Grep `generate_seed_system.j2` for "inventory" in the opening narrative section — should be gone.

#### Step 3.3 — Update `docs/repomap.md` seed system prompt section (consolidate)

**File:** `docs/repomap.md`

**What:** The Phase 2 documentation update (Step 2.3) covers this phase's changes. No separate update needed — both phases modify the same file (`generate_seed_system.j2`). Step 2.3 should capture all changes to this prompt in a single update.

**Why:** Avoid duplicate documentation updates. Both Phase 2 and Phase 3 modify `generate_seed_system.j2`.

**Validation:** Confirm `docs/repomap.md` seed section captures all changes from both phases.

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

---

## Verification

After all phases:

1. Run `make check` (lint + typecheck) — must pass.
2. Start a game with no hints — should use LLM seed generation (existing behavior).
3. Start a game with any hint field populated — should use static pack seed.
4. Verify `generate_seed_system.j2` has no inventory generation instructions.
5. Verify `generate_seed_system.j2` has explicit instructions for weaving seed data into narration.
6. Verify compendium NPCs are referenced naturally in opening narration (check events.jsonl for a generated game).
