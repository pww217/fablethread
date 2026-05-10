# SYSTEM PROMPTING — ccya prompt-engineering rules

Rules for every `*_system.j2` prompt. Apply these before adding, restructuring, or trimming a prompt.

PRIMARY DIRECTIVE: terse, model-agnostic, accuracy first, latency a close second.

---

## Common skeleton (every prompt)

All five extract/narrate/rules system prompts share this structure:

```
[1–2 sentence imperative opening — what the model does]

## Output schema          ← JSON shape, right after the imperative
## Field rules            ← one paragraph per output field
## [domain-specific rules] ← ID rules, grounding, format constraints
## State-presence rule    ← "absence is not removal"
## Deduplication rule     ← no duplicate entries
## [unique constraints]   ← caps, must-emit rules, grounding
```

**Why this order.** The model anchors on the most-recent schema mention (rule 7). Schema goes first so field rules can reference it. Domain-specific rules come next so they're fresh. Shared rules (state-presence, dedup) go last as a final check before output.

### Shared sections (appear in every prompt)

- **`## Output schema`** — JSON object shape with empty/default values. Placed directly under the opening imperative.
- **`## Field rules`** — One paragraph per output field. Format: `` `field_name`: description + structure + examples. ``
- **`## State-presence rule`** — Identical text in every prompt:
  > Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only emit removals you can justify from the narration.
- **`## Deduplication rule`** — Same structure in every prompt: "Before you submit, verify no duplicates" followed by bullet points per output category.
- **`## Constraints`** — Caps, must-emit rules, and hard limits. Merged here rather than a separate "Hard cap" section.

### What goes in `## [domain-specific rules]`

Each prompt has 1–2 sections unique to its domain. These cover ID formats, grounding requirements, and other rules that don't apply to other extractors. See the per-prompt section below for what each one has.

---

## The twelve rules

### 1. System prompt = byte-stable across turns

Per-turn variability (rules outcome, scope, dynamic guidance, items_gained, quest threshold, faker name pool, last-turn-failed) MUST live in the user prompt. The system prompt should hash to the same bytes whether it's turn 1 or turn 50. Verified with `tests/test_prompt_cache_stability.py`.

### 2. Skip-render — but say "absence ≠ removal"

Don't render empty sections. Every extract system prompt carries the stable state-presence line (see shared sections above). User-prompt sections render only when they have content AND fall inside `scope.active_domains`.

### 3. Engine owns stateful and numerated reasoning

If something can be computed in Python — counts, thresholds, dedup, validation, TTL ticks, dice resolution, ammunition math — do it in code, not in a Jinja `{% if x | length > 3 %}` ladder. Push the model toward fiction; let code own arithmetic.

### 4. Label inputs with output-field nouns

The user-prompt section feeding a `present_npcs` output field is titled `present_npcs` (not "Scene Characters"). The cheap noun-reinforcement reliably improves field-name discipline.

### 5. One delimiter pair per role

- **`=== PLAYER INPUT ===` / `=== END PLAYER INPUT ===`** — player's raw turn input. Used by `rules_user.j2` and `narrate_user.j2`.
- **`## CURRENT TURN NARRATION` / `## END CURRENT TURN NARRATION`** — narrator's prose. Used by all three extractors.

Do not invent a third convention.

### 6. Imperatives over role narration

"Extract scene state from narration. JSON only." beats "You are the scene extractor. Your only job is to extract scene cosmetics, location state, NPC presence…". Each preamble is one short verb-led line.

### 7. Schema near the imperative

Place the output schema directly under the verb. The model anchors on the most-recent schema mention. Don't bury it after 60 lines of guidance.

### 8. One home per directive

If a rule lives in `*_system.j2`, it does NOT also live in `*_user.j2`. No restating. If you're tempted to repeat for emphasis, the original phrasing was probably weak — fix it once.

### 9. Cross-stream surface is minimum-viable

Stream B receives only what stream A produced that B genuinely needs.
- Scene → State: `location_id`, `location_changed`, `present_npcs[id+name]` only.
- Scene+State → Progress: present NPC names + items gained (names) / items lost (ids) only.
No full-state re-sends, ever.

### 10. `_reasoning` only as a true scratchpad

A `_reasoning` JSON field is post-commit narration unless it is the **first** key in the schema. We currently do not use it — the model emitted it last, which made it useless. If reintroduced, position it first and cap it at ≤25 words.

### 11. Faker provides names

`engine.names.generate_name_pool` / `generate_npc_names` already inject genre-and-locale-appropriate candidates. Don't lecture about generic Anglo names. Ship one short directive per prompt:

> Pick from the provided pool; favor names that fit the genre, role, and culture. Mix linguistic origins.

That's it. No "Marcus Cole / Clara Miller / Elias Thorne" anti-list, no triple repetition.

### 12. No commented-out prompt blocks

If it's deferred, track it in `TODO.md` or `plans/`; don't leave it sitting in a `{# ... #}` block in the template. Same goes for legacy alternatives — delete in the PR that supersedes them.

---

## Per-prompt: unique fields and why

### `rules_system.j2` — Intent classification + skill check

**Unique fields:** `intent`, `intent_verb`, `target`, `stakes`, `check`

**Why they exist.** This prompt is the gatekeeper between player input and the dice engine. `intent` captures what the player is trying to do in-story (feeds the narrator). `intent_verb` normalizes the action into a controlled vocabulary for downstream logic. `target` identifies who/what the action is directed at. `stakes` forces the model to articulate failure consequences upfront, which the narrator uses for pacing. `check` is the mechanical decision: whether to roll, which stat, and at what difficulty.

**Unique sections:** Stats list, difficulty scale, decision rule (default NO), compound actions, anti-declare-outcome rule.

---

### `narrate_system.j2` — Prose generation + scope tagging

**Unique fields:** Prose output (not JSON), `<scope>` tag at the end

**Why they exist.** This is the only non-extractor prompt — it outputs fiction, not a structured JSON object. The `<scope>` tag is a lightweight domain-change signal that tells the engine which extraction streams to run next. Everything else in this prompt is style and behavior guidance.

**Unique sections:** Style (spatial clarity, tropes, dialogue, visceral detail), items/inventory (bolding rules, hard constraint on inventory verification), player intent is truth, pragmatic interpretation, NPCs in scene, mortal stakes + agency, gender-aware naming, NPC naming (given + family name required), quests, markdown rules, world consistency, genre tone, universe rules, active scope tail.

---

### `extract_scene_system.j2` — NPC presence + location + scene classification

**Unique fields:** `scene_tags`, `scene_tagline`, `location_change`, `location_description`, `npc_add/remove/update`, `compendium_npc_update`

**Why they exist.** This is the lightest extractor — it captures the "scene layer" of state without touching inventory, conditions, or quests. `scene_tags` and `scene_tagline` are UI-facing metadata. `location_change` and `location_description` are split because a location ID change is a different event from new spatial detail in the same room. `npc_add/remove/update` track who's in the scene and their attitude. `compendium_npc_update` is the bridge to durable NPC identity — separate from scene updates because compendium changes persist across the entire game.

**Unique sections:** NPC ID rules, NPC grounding rule (names/titles/bios must come from narration or compendium, never invented), ambient NPC must-emit constraint.

---

### `extract_state_system.j2` — Inventory + conditions

**Unique fields:** `inventory_add/remove/update`, `pc_condition_add/remove`

**Why they exist.** This is the most numerically precise extractor. Inventory IDs are immutable once assigned — upgrades use `inventory_update` with the existing ID, not a new add. Quantities require exact math from narration. Conditions are gated by roll context (failed strength → wounded, failed resolve → shaken) to prevent the model from adding conditions on every minor setback. The generic item mapping rule prevents the model from inventing new IDs for vague narration ("a coin" → existing currency ID, not a new `coin` ID).

**Unique sections:** ID format rules (noun / adjective_noun, lowercase, no articles with ✅/❌ examples), match instruction (check existing inventory before adding), quantities guidance, condition guidance tied to roll context, generic item mapping (MANDATORY).

---

### `extract_progress_system.j2` — Quests + events + actions + pressure

**Unique fields:** `quest_updates`, `recent_events_add/update/remove`, `actions`, `outcome_summary`, `gm_beat`, `beat_disposition`, `scene_pressure_add/remove/update`

**Why they exist.** This is the heaviest extractor — it handles the most output fields and the most cross-referencing. Quest deduplication is mandatory and complex (compare subject, target NPC, and object against every active quest). `recent_events` must be narratively significant — default to no new facts. `actions` requires exactly 4 choices with a specific structure (2 quest-related, 1 NPC, 1 exploration). `gm_beat` requires grounding in existing entities (NPCs or pressures from state). `scene_pressure` lifecycle (add/remove/update) is managed here after migration from the scene extractor.

**Unique sections:** Quest deduplication (MANDATORY, with concrete examples of what NOT to do), GM beat grounding rule (must reference existing NPC or pressure ID), rules-outcome guidance (roll band determines objective completion), contact/meet objective rule (overrides general guidance — resolves on narrative presence, not roll outcome), state-presence rule.

---

## When in doubt: the test

Before merging a prompt change, render the system prompt with two distinct turn states and `diff` the output. Identical bytes? Good — system stayed stable. Different bytes? You leaked per-turn state into the system; move it to the user prompt.

---

## Where the wins actually come from

Latency on these calls is dominated by **prefill cost**, which scales linearly with input token count. Reducing system prompt size by 30% reduces prefill time by ~30%. That win lands the same on single-slot caching, multi-slot prefix caching, vLLM, mlx_lm, anything.

Cache stability (rule 1) is **architectural insurance**: it pays off the day mlx_lm gains prefix caching, or the day we swap to a multi-slot runtime. Until then, it's discipline that costs nothing and protects the upgrade path.

If you're tempted to add tokens, ask: does this content change the model's output? If you can't show it does, cut it.

---

## Tense authority

`narrate_system.j2` no longer declares a fixed tense. Tense authority belongs to the pack style block (`## Genre tone` section). Each pack's `style.md` should include a tense instruction. When no pack style is present, the system prompt defaults to past tense.

## Contact/meet objective rule precedence

`extract_progress_system.j2`'s "Contact and meet objective rule" is an explicit override of the general "no dice roll: do NOT complete quest objectives" guidance. Contact and meet objectives resolve on narrative presence, not roll outcome, even when no dice were rolled. The system prompt marks this with "**This rule overrides the general rules-outcome guidance above.**" and the general guidance points back with "**Exception: see Contact and meet objective rule below.**"
