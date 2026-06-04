# Narration Prompt Overhaul — Phase 3: Seed Opening Narrative + Packs

## Purpose

Revise the seed opening narrative guidance to produce longer, more atmospheric opening narratives (target 530–930 words, +33% from current 400–700) and update the prose_word_range in all 6 default packs.

## Problem Statement

Opening seed narration under-produces at 308 words against a 400-word floor. The 3-movement structure has rigid per-section word targets (close-up ~80, exposition ~100, crisis remaining) that cause the model to over-weight the close-up and shortchange the crisis section. The scene bundle ingredients are presented as a mandatory checklist rather than optional inspiration. The prose_word_range ceiling of 700 caps output below what a proper opening needs.

## Constraints

- Only the opening_narrative section of `generate_seed_system.j2` is changing. JSON schema, generation order, NPC rules, output discipline — all untouched.
- The 3-movement structure (close-up → exposition → crisis) must remain recognizable.
- All 6 default packs (zombie-survival, sengoku-japan, space-western, golden-piracy, noir-1930s, allied-ww2) must get the same `prose_word_range` update.
- Generated packs (in `packs/generated/`) are per-run artifacts — not modified.

## Non-goals

- Not changing the seed system prompt aside from the opening_narrative section.
- Not changing the seed user prompt (`generate_seed_user.j2`).
- Not changing the narrate, extract, ruling, or storyteller prompts.
- Not changing pack inspiration text, situation_archetypes, arc_categories, or pools.

## Solution

Change `prose_word_range: [400, 700]` → `[530, 930]` in all 6 default packs. Rewrite the opening_narrative guidance: replace per-section word targets with a unified ~700 word target, tighten close-up to 1–2 sentences, make exposition a non-checklist weave, add a proportional guard to the crisis movement, and wrap the scene bundle block in an optional preamble.

## Firm decisions

1. `prose_word_range: [530, 930]` in all 6 packs — +33% range to give the model more room.
2. Per-section word targets (~80 / ~100 / remaining) removed. Unified ~700 word target replaces them.
3. Close-up guidance: "1–3 sentences" (previously ~80 words / ~2–5 sentences).
4. Exposition guidance: "weave 1–2 environmental details into the scene" — replaces "describe 2-4 specific environmental details."
5. Crisis proportional guard: "Spend most of your words on the crisis/gameplay moment — the close-up and exposition are setup, not the main event."
6. Scene bundle block wrapped in optional preamble: `Optional ingredients — use what fits, ignore what doesn't:` — existing `{% if pool_selection.scene_bundle %}` already gates the block.

## Risks, Ambiguities, and Blockers

- **Word range increase may not translate to longer output:** The model currently under-produces at 308 words against a 400 floor. Raising the floor to 530 doesn't guarantee the model hits it. The rewritten guidance and proportional guard help, but the targets are advisory.
- **Model variance across runs:** Prose improvements may not be consistent across different runs or seeds. Evaluate across multiple runs before drawing conclusions.
- **Close-up over-weighting may persist:** Without sub-targets, the model may revert to writing 80+ words of close-up. The proportional guard and 1–3 sentence constraint mitigate this but don't guarantee it.

## Status
`open`

## Implementation — Phase 3

### Context files to load

- `ccya/prompts/generate_seed_system.j2` — opening_navigation section (lines 140–162) and prose_word_range reference (line 82)
- `packs/default/zombie-survival/scenario.yaml`
- `packs/default/sengoku-japan/scenario.yaml`
- `packs/default/space-western/scenario.yaml`
- `packs/default/golden-piracy/scenario.yaml`
- `packs/default/noir-1930s/scenario.yaml`
- `packs/default/allied-ww2/scenario.yaml`

### Detailed steps

#### Step 3.1 — Update prose_word_range in all 6 default packs

**File:** Each of the 6 `packs/default/*/scenario.yaml` files.

**What:** Change `prose_word_range: [400, 700]` to `prose_word_range: [530, 930]` on line 9 of each file.

**Why:** Design decision — the old range capped the model at 700 words; actual output averaged 308. New range gives the model 33% more headroom with a higher floor.

**Validation:** `grep prose_word_range packs/default/*/scenario.yaml` shows `[530, 930]` in all 6 files.

#### Step 3.2 — Rewrite opening_narrative section in generate_seed_system.j2

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Replace lines 140–162 (the opening_narrative section) with:

```
## opening_narrative
~700 words. Second person, present tense.

Structure the opening in three movements — these are loose beats, not word-count quotas:

1. **Close-up** (1–3 sentences): Start with one live sensory detail that matters. Orients the player in the character's immediate physical reality. No summary, no biography.

2. **Exposition** (the middle): What is around the PC to see, examine, or potentially interact with — weave 1–2 environmental details into the scene. These aren't a checklist; every detail should imply recent action, conflict, or presence.

   Optional ingredients — use what fits, ignore what doesn't:
   {% if pool_selection and pool_selection.scene_bundle -%}
   {% if pool_selection["scene_bundle"]["items"] %}Objects: {{ pool_selection["scene_bundle"]["items"] | join(", ") }}.{% endif %}
   {% if pool_selection["scene_bundle"]["conditions"] %}Conditions: {{ pool_selection["scene_bundle"]["conditions"] | join(", ") }}.{% endif %}
   {% if pool_selection["scene_bundle"]["sensory"] %}Sensory details: {{ pool_selection["scene_bundle"]["sensory"] | join(", ") }}.{% endif %}
   {% endif -%}

3. **Crisis/gameplay moment** (the bulk): The tension arrives or is revealed. Present NPCs act. The moment the player must respond to. This is where the "mid-scene" feel belongs — earned after the orientation.

   Spend most of your words on the crisis/gameplay moment — the close-up and exposition are setup, not the main event.

Movement guidance:
- The close-up and exposition together should feel like chapter one, building atmosphere and place before revealing danger.
- Bold NPC names on first introduction. Bold inventory item names on first use.
- Let the campaign arc tension surface through what the player observes rather than what the narrator announces.
- NPCs should appear in action, not be introduced.
- The opening should feel like chapter one, not a mid-chapter drop.
```

**Why:** Three changes in one rewrite: (a) per-section word counts → unified target + loose structure, (b) close-up tightened from ~80 words to 1–3 sentences, (c) exposition de-checklisted from "2-4 specific details" to "weave 1–2, not a checklist," (d) scene bundle ingredients made explicitly optional with preamble, (e) proportional guard added to crisis movement.

**Validation:** Template renders without error. `make check` passes.

### Tests to write or update

No tests exist during refactor phase. Validation is by `make check` and manual inspection: generate a seed and verify the opening narrative word count distribution (close-up ≤3 sentences, crisis is the bulk, total in 530–930 range).
