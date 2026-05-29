# Narrate Prompt Cleanup and Reordering

## Status
`completed`

## Phases

1 phase: Fix narrate prompt template structure, remove duplication, add missing BINDING directive for fail bands, and reorder for LLM attention priority.

## Issue

The narrate user prompt (`narrate_user.j2`) has three problems that degrade narration quality: (1) stale campaign arc context is buried between inventory (~line 13 of template) while immediate-turn data — beat type, narration directive, player input — sits at the bottom where LLM attention decays; (2) `goal_context` appears in both system prompt and user template as duplicated guidance for early turns; (3) `_arc.j2` has inconsistent whitespace control that produces merged lines like `starvation.Thematic question:` when certain fields are absent. Additionally, when a roll produces a fail band, no `(BINDING)` marker is injected into the user prompt despite `narrate_system.j2` containing detailed fail-band rules — this causes the eval auto-checker `universal.narrate.binding_present` to fail on ~50% of rolled turns.

## Solution

Clean up `_arc.j2` whitespace for consistent output, remove duplicated `goal_context` from system prompt (keep only in user template), add a `(BINDING)` marker for fail bands in the narrate user prompt, and reorder `narrate_user.j2` so Campaign Arc moves below Recent Turns and directive/beat appear after player input. Expected outcome: cleaner rendered prompts with immediate-turn data at highest-attention position (bottom of prompt) and no duplicated context between system/user templates.

## Firm decisions

1. **goal_context lives only in user template.** Remove lines 64–68 from `narrate_system.j2`. The system prompt already has arc update instructions (lines 70–87). Early-turn behavioral guidance belongs alongside the actual value, not duplicated as a separate system instruction.
2. **Directive and beat go after player input.** LLMs process top-to-bottom; the last thing read should be what to do with the input. Place `pending_beat` and `pacing_context.directive` below `=== END PLAYER INPUT ===`.
3. **Campaign Arc moves down, not out.** Keep arc values in user template (system prompt only has instructions). Move from between inventory/characters (~line 13) to after Recent Turns so stale context doesn't compete with immediate data for attention.
4. **BINDING marker is fail-band-only.** Only inject when `rules_outcome.band == "fail"` and `rolled=true`. Success/partial bands don't need binding constraints — the system prompt already covers general rules.
5. **Whitespace control in `_arc.j2` must be consistent.** Use no strip markers (`{% %}`) throughout for predictable newline behavior, or use `{%-`/`-%}` consistently on every line break.

## Non-goals

- Do not change `narrate_system.j2` prose guidance (style rules, NPC naming, inventory constraints, etc.).
- Do not modify any extract prompt templates (scene/state/storytell).
- Do not change `_location.j2`, `_inventory.j2`, or `_npc_roster.j2`.
- Do not add new template variables to `narrate.py` — all changes use existing context.
- Do not change the arc data model, CampaignArc schema, or thread lifecycle logic.

## Risks, Ambiguities, and Blockers

1. **Repomap stale comment.** Line 117 of `docs/repomap.md` says goal_context is consumed in both system and user prompts. Must update to reflect single-location (user only).
2. **context.py stale comment.** `NarratorSystemBoundary` docstring (line 307) claims template uses only `world_rules` and `narrator_rules`, but lines 64–68 of narrate_system.j2 actively use `current_arc.goal_context`. After removing those lines, the comment becomes correct — update it to reflect that.
3. **No tests for narrate_system render output.** Only alignment check exists. Adding a basic render test is recommended but not required (tests are temporarily removed per AGENTS.md).

## Implementation — Phase 1: Narrate template cleanup and reordering

### Context files to load
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/sections/_arc.j2`
- `ccya/prompts/narrate_system.j2`
- `ccya/engine/narrate.py` (for reference only — no changes needed)

### Detailed steps

#### Step 1.1 — Fix `_arc.j2` whitespace consistency

**File:** `ccya/prompts/sections/_arc.j2`

**What:** Replace all `{%-` and `-%}` strip markers with plain `{% %}` throughout the template. This produces consistent newline behavior: each Jinja tag sits on its own line, producing clean paragraph breaks regardless of which fields are populated or absent. Specifically fix lines 8–14 where missing newlines produce merged output like `starvation.Thematic question:` when `pc_drive` is empty/absent (the `{%- set active_threads ... -%}` collapses surrounding whitespace).

Also remove the HTML-comment wrapper from goal_context on line 7: change `<!-- Narrator note: this is... -->**Narrative guidance — goal context:**` to just `**Narrative guidance — goal context:**`. The comment adds no value in user prompt (LLM doesn't distinguish HTML comments from text).

**Why:** Inconsistent whitespace control produces malformed output. Strip markers on some lines but not others cause newlines to be eaten when certain fields are absent, creating merged prose that looks broken and wastes tokens with invisible formatting noise.

**Validation:** Run `python3 scripts/debug/ev.py compact 5 narrate` (or any turn where goal_context is populated). Verify no merged lines between sections: each section header should start on its own line after a blank line from the preceding content.

#### Step 1.2 — Remove duplicated `goal_context` from system prompt

**File:** `ccya/prompts/narrate_system.j2`

**What:** Delete lines 64–68 (the `{% if current_arc.goal_context -%}` block). Update line 61 to remove the parenthetical reference: change `(see user prompt for current values)` to just end at "below." — or rephrase to `Your visible goal, thematic question, active threads, and pc_drive are provided in the context below. Use them as narrative guidance.`

**Why:** After Step 1.1, `_arc.j2` already presents goal_context alongside other arc values with clear labeling. The system prompt's behavioral instruction ("ground the player in personal stakes") is redundant when the same value appears labeled in user template. Single source of truth per AGENTS.md rules.

**Validation:** Run `python3 scripts/debug/ev.py prompt 5 narrate system | grep -c goal_context`. Should return 0 (no references to goal_context remain). Verify line count drops from 142 to ~137 lines.

#### Step 1.3 — Add fail-band BINDING marker in user template

**File:** `ccya/prompts/narrate_user.j2`

**What:** After the existing rules_outcome block (lines 67–74), add a conditional for fail bands:

```jinja
{% if rules_outcome and rules_outcome.rolled and rules_outcome.band == "fail" %}

**rules_outcome (BINDING)** — Fail band constraint applies. The NPC does NOT engage constructively to help the player. Do not turn FAIL into PARTIAL by offering counter-deals, partial payments, or consolation prizes. See system prompt fail-band section for details.
{% endif %}
```

Place this between lines 74 and 75 (after the no-roll block, before pending_beat).

**Why:** The eval auto-checker `universal.narrate.binding_present` checks for `"rules_outcome (BINDING"` in rendered user prompt on rolled turns. It fails ~50% of rolls because this marker was never generated. Fail bands need an explicit binding directive so the Narrator knows to honor dice constraints rather than narrating a favorable outcome anyway.

**Validation:** Run `python3 scripts/debug/ev.py compact 6 narrate` (turn 6 has rolled=true, band=partial — should NOT show BINDING). Then verify against any turn where band=fail and rolled=true that the marker appears between rules_outcome and beat_type sections.

#### Step 1.4 — Reorder `narrate_user.j2`: Campaign Arc down, directive/beat after player input

**File:** `ccya/prompts/narrate_user.j2`

**What:** Restructure template from current order to:

```
PC (lines 1-6) → Location include (line 9) → Inventory include (line 11) → Characters include (line 15, moved up from line 15 stays roughly same position but now between inventory and immutable reference) → Immutable Reference (lines 17-36 stay in place) → Scene Context (lines 38-44) → Prior Turns (lines 52-56) → Recent Turns (lines 58-64) → Campaign Arc ← moved from line 13 to here, after recent turns → This Turn's Result: rules_outcome + beat_type (lines 66-78 stay but directive moves down) === PLAYER INPUT === (line 84-85) → Beat type directive ← moved below player input → Narration Directive ← moved below player input
```

Concretely, in template code terms:

1. Move the `{% include "sections/_arc.j2" %}` line from its current position (after inventory include, before npc_roster include) to after Recent Turns block and before "This Turn's Result". Place it between lines 64 and 65 (between `{% endif -%}` of recent turns and `## This Turn's`).

2. Move the beat_type conditional (lines 75-78) and pacing_context directive (lines 79-82) from above player input to below `=== END PLAYER INPUT ===`. Place them after line 86 as:
```jinja
{% if pending_beat and pending_beat.type %}

**Beat:** {{ pending_beat.type | replace('_', ' ') | upper }} — surface as `{{ pending_beat.surface_as | default('ambient') }}`. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
{% endif %}
{% if pacing_context and pacing_context.directive %}

**Directive:** {{ pacing_context.directive }}
{% endif %}
```

3. Keep rules_outcome (lines 67-74) where it is — above player input, alongside the turn result header. The band/directive from dice resolution provides context for interpreting the action.

**Why:** LLMs process top-to-bottom with highest attention at both start and end of prompt. Campaign Arc values are stale (goal rarely changes between turns) so they should be pushed down where they don't compete with immediate data. Beat type and narration directive tell the Narrator *how* to narrate — this instruction must come after reading what the player did, not before. Rules_outcome band stays above input because it provides context for interpreting action weight (success vs fail changes how you describe outcomes).

**Validation:** Run `python3 scripts/debug/ev.py compact 7 narrate` and verify:
- Campaign Arc section appears between Recent Turns and "This Turn's Result" header
- Beat type directive appears after `=== END PLAYER INPUT ===`  
- Narration Directive appears after beat type (or right after player input if no beat)
- Player input is the last substantive content before directives

#### Step 1.5 — Update stale documentation comments

**File:** `docs/repomap.md`, line 117

**What:** Change:
```
- **Narrator consumes**: `goal_context` in both system prompt (`narrate_system.j2` — early-turn guidance block) and user prompt (`_arc.j2` — HTML-comment-wrapped narrator context). The narrator converts these fields into scene texture, dialogue pressure, and prose emphasis — never reciting them directly.
```

To:
```
- **Narrator consumes**: `goal_context` in the narrate user prompt (`_arc.j2`). The system prompt provides general early-turn behavioral guidance; `_arc.j2` presents the actual value alongside other arc context for this turn. The narrator converts these fields into scene texture, dialogue pressure, and prose emphasis — never reciting them directly.
```

**File:** `ccya/prompts/context.py`, line 307 (NarratorSystemBoundary docstring)

**What:** Change:
```
Template uses only `world_rules` and `narrator_rules` — alignment check flags pack_style/current_arc as dead fields removed from boundary model.
```

To:
```
Template uses only `world_rules`, `narrator_rules`, and `pack_style`. The `current_arc` variable was passed but never consumed (lines 64–68 of narrate_system.j2 have been removed). Alignment check passes with no dead fields.
```

**Why:** Documentation must match actual template behavior. Stale comments cause confusion for future edits and incorrect assumptions about data flow.

**Validation:** No code change needed — just verify the updated text accurately describes post-change state.

### Tests to write or update

Per AGENTS.md, tests are temporarily removed during refactor phase. Skip test additions for now. When tests return:
- Add `test_narrate_system_no_goal_context()` in `tests/test_render.py` asserting goal_context doesn't appear in rendered system prompt output
- Add `test_narrate_fail_band_binding()` asserting fail-band rolls produce `(BINDING)` marker in user template

### REPOMAP updates required

- `docs/repomap.md` line 117: update goal_context consumption description (Step 1.5)
