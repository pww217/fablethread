# Prompt Hygiene: Deduplication, Generic Examples, and Rules User Context

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | narrate_system cleanup | Remove dead duplication; genericize named examples |
| 02 | rules_user context | Replace last-turn narrative with outcome_summary; add assistant stub |
| 03 | extract_progress cleanup | Remove behavioral rules restated in user prompt |

## Objective
Several system prompts contain named game characters in illustrative examples (breaking generic reusability and polluting cache-stable content with instance-specific data), duplicate live-state data that already appears in the user prompt, or restate behavioral rules in the user prompt that already exist in the system prompt. This plan cleans those up without touching any prompt logic or behavioral intent.

## Non-goals
- No changes to any behavioral rules, decision logic, or output schemas.
- No changes to extract_scene, extract_state, or compact prompts (examples in those are already generic or justified).
- No creation of shared partials — caching architecture makes this counterproductive.
- No rubric or judge prompt changes.
- No changes to Python code, models, or engine logic.

---

## Implementation — Phase 01: narrate_system cleanup

### Files to pull for context
- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/narrate_user.j2`

### Detailed steps

#### Step 1.1 — Remove `## World consistency` block from narrate_system

**File:** `ccya/prompts/narrate_system.j2`

**What:** Delete the entire `{% if world_factions or world_locations %}...{% endif %}` block including the `## World consistency` header, the instruction sentence, and both faction/location loops.

**Why:** Factions are already rendered in `narrate_user.j2` inside the `<<<TRACE_IMMUTABLE_START>>>` block as `### Known Factions`. Locations are rendered via `_location.j2`. The system prompt rendering these again is pure duplication — the model sees them twice per call.

**Code Snippet**
```jinja2
{# DELETE THIS ENTIRE BLOCK — factions and locations already in narrate_user.j2 #}
{# {% if world_factions or world_locations %} #}
{# ## World consistency ... {% endif %} #}
```
The block to delete starts at `{% if world_factions or world_locations %}` and ends at the matching `{% endif %}`.

**Validation:** Render narrate_user for a session with factions defined. Confirm factions appear once (in user prompt). Confirm narrate_system no longer contains faction names.

---

#### Step 1.2 — Remove `## Active pressures` block from narrate_system

**File:** `ccya/prompts/narrate_system.j2`

**What:** Delete the entire `{% if scene_pressure %}...{% endif %}` block including the `## Active pressures (BINDING)` header and its instructions/loop.

**Why:** `narrate_user.j2` already renders `### Active Threats` with the same pressure list. The system block duplicates this — pressures appear in both system and user every call with active pressure. The directive to mention pressure in the opening is a behavioral rule; it belongs in the user prompt near the actual pressure data, which it already is (via the `**Narration Directive:** Pressure` / `Overwhelm` logic in `narrate_user.j2`). The system block adds no signal the user prompt doesn't already carry.

**Code Snippet**
```jinja2
{# DELETE THIS ENTIRE BLOCK — pressures already rendered in narrate_user.j2 ### Active Threats #}
{# {% if scene_pressure %} #}
{# ## Active pressures (BINDING) ... {% endif %} #}
```

**Validation:** Run a turn with an active immediate pressure. Confirm the pressure text still appears in the user prompt under `### Active Threats`. Confirm narrate_system no longer contains the `## Active pressures` block. Confirm the narration still acknowledges the pressure (behavioral rule is still enforced via the user prompt directive).

---

#### Step 1.3 — Genericize named examples in `## Fail-band outcomes`

**File:** `ccya/prompts/narrate_system.j2`

**What:** Replace the two named examples under `## Fail-band outcomes` with generic stand-ins using `[NPC_NAME]`, `[ITEM]`, and `[VERB]` placeholders. Preserve the Bad/Good structure and the rule text exactly.

**Why:** `Caron` and the ledger are characters from a specific pack. Using them in a role-level system prompt means the instruction leaks game-specific state into what should be cache-stable, generic guidance. Any pack's narrator will misread this as a hint that Caron is a character in their game.

**Code Snippet**
```jinja2
## Fail-band outcomes (BINDING)

On a FAIL band:
- The PC does not get what they asked for.
- The NPC does NOT engage constructively to help them.
- The NPC may refuse, stall, shut them down, or walk away.

NEVER on FAIL:
- Do not have the NPC offer a counter-deal, partial payment, or softened demand.
- Do not turn FAIL into PARTIAL by giving the PC a consolation prize.

Bad (do NOT do this on FAIL):
  [NPC_NAME] leans back, smiles thinly, and offers a different payment schedule.
Good (correct FAIL):
  [NPC_NAME] closes the ledger and says, "Then we have nothing to discuss," turning away.
```

**Validation:** Diff confirms only `Caron` → `[NPC_NAME]` change. No behavioral content altered.

---

#### Step 1.4 — Genericize named example in `## Player input is truth`

**File:** `ccya/prompts/narrate_system.j2`

**What:** Replace the `## Conflict example` block's named characters (`Halden`, the merchant seal, the ledger) with generic placeholders.

**Why:** Same reason as 1.3 — the example is correct and valuable, but `Halden`, the merchant seal, and the ledger are pack-specific. Replace with `[NPC_NAME]`, `[ITEM_A]`, `[ITEM_B]`, and `[GM_BEAT_DESCRIPTION]`.

**Code Snippet**
```jinja2
**Conflict example (READ CAREFULLY):**
- Player says: "I sit across from [NPC_NAME] at his table, slide [ITEM_A] across, and hand him [ITEM_B]."
- GM beat says: "pressure: toughs circle and flank the player"
- WRONG: Narrate the toughs attacking and the player fighting them (this replaces the player's action).
- RIGHT: Narrate the player sitting down and sliding [ITEM_A]/[ITEM_B] across the table FIRST. Then describe the toughs circling and flanking as the player attempts this action — the toughs' presence is the environmental pressure, not the main event. The player's action (sitting, sliding [ITEM_A], handing [ITEM_B]) is the primary narration.
```

**Validation:** Diff confirms only named substitutions. Rule text and structure unchanged.

### Tests to write or update
No behavioral change — no new tests required. Existing `tests/test_engine_pipeline.py` narration path covers regression.

### REPOMAP and architecture updates
None — prompt file changes only, no new functions or signatures.

### Risks
1. Removing `## Active pressures` from system: the behavioral rule ("mention pressure in opening") was also stated there. It must still be enforced via `narrate_user.j2`'s `**Narration Directive:** Pressure/Overwhelm` logic. Verify the user prompt path covers this before deploying. Mitigation: run a pressure-active eval turn and inspect narration output.

---

## Implementation — Phase 02: rules_user context

### Files to pull for context
- `ccya/prompts/rules_user.j2`
- `ccya/prompts/rules_system.j2`
- `ccya/engine/narrate.py` — to find where `recent_turns` and `outcome_summary` are passed to prompt context
- `docs/REPOMAP/engine.md` — to confirm where rules prompt context is built

### Detailed steps

#### Step 2.1 — Replace `## Last Turn Narrative` with `outcome_summary`

**File:** `ccya/prompts/rules_user.j2`

**What:** Replace the current `{% if recent_turns %}## Last Turn Narrative...{% endif %}` block with a single `outcome_summary` line sourced from the previous turn's progress extractor result. If no prior outcome exists (turn 1), omit the section entirely.

**Why:** The full narrative text is expensive and mostly irrelevant to intent classification. What the rules engine actually needs from prior context is: *what happened* (the outcome), not the full prose. `outcome_summary` is 1–2 sentences and provides the same disambiguation signal (e.g., "You stabbed the guard" → next turn "I finish him" can now resolve "him" correctly) at a fraction of the token cost.

**Code Snippet**
```jinja2
## Player Character
**{{ pc.name or "Unnamed" }}** — {{ pc.tagline or pc.concept or "" }}

**Stats:** {% for k, v in (pc.stats or {}).items() %}{{ k }}={{ v }}{% if not loop.last %} {% endif %}{% endfor %}

**Conditions:** {% if pc.conditions %}{% for c in pc.conditions %}{{ c.label if c is mapping else c }}{% if not loop.last %}, {% endif %}{% endfor %}{% else %}none{% endif %}

## scene
Location: {{ location.name or location.id or "Unknown" }}
{%- if present_npcs %}
## Present NPCs (in scene right now)
{% for n in present_npcs %}- {{ n.name or n.id }}{% if n.title %} ({{ n.title }}){% endif %}{% if n.notes %} — {{ n.notes }}{% endif %}
{% endfor -%}
{% endif -%}
{%- if last_outcome %}
## Last Turn Outcome
{{ last_outcome }}
{% endif -%}
## Current Turn: {{ meta.turn | default('?') }}
=== PLAYER INPUT ===
{{ user_input }}
=== END PLAYER INPUT ===
```

**Validation:** Confirm `last_outcome` variable is passed to rules prompt context (see Step 2.2). On turn 1, section is absent. On turn 2+, section shows one sentence.

---

#### Step 2.2 — Pass `last_outcome` to rules prompt context

**File:** `ccya/engine/rules.py` (or wherever the rules user prompt context dict is built — confirm in `docs/REPOMAP/engine.md` before editing)

**What:** Add `last_outcome` to the template context passed to `rules_user.j2`. Source it from the previous turn's `TurnResult.outcome_summary` if available, else `None`.

**Why:** The template now references `last_outcome` — it must be in context or Jinja will raise.

**Code Snippet**
```python
# In the function that builds rules user prompt context:
context = {
    "pc": state.pc,
    "location": ...,
    "present_npcs": ...,
    "meta": state.meta,
    "user_input": user_input,
    "last_outcome": getattr(prev_turn_result, "outcome_summary", None),  # None on T1
}
```

**Validation:** `make check` passes (type check). On T1 `prev_turn_result` is `None` — confirm `getattr(None, "outcome_summary", None)` returns `None` and template omits the section.

---

#### Step 2.3 — Add assistant-turn stub to rules call

**File:** `ccya/engine/rules.py` (the function that calls the LLM for intent classification)

**What:** Append a single assistant-role message `{"role": "assistant", "content": "{"}` to the messages list before the LLM call for the rules stream only.

**Why:** The rules call emits pure JSON. An assistant stub primes the model to complete the object directly, eliminating any risk of preamble prose. This is safe for this stream because the output schema is rigid and small — unlike narrate or extract streams where you want the model to reason freely before committing to output.

**Code Snippet**
```python
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt},
    {"role": "assistant", "content": "{"},  # prime JSON completion
]
result = await llm_client.chat(messages, ...)
# Prepend the brace back before parsing:
result_text = "{" + result.strip()
```

**Validation:** Parse result as JSON. Confirm no preamble. Confirm existing JSON parse logic handles the prepended `{` correctly (or adjust parse call to prepend before passing to `json.loads`). Run `make test` — existing rules parse tests must pass.

### Tests to write or update
- `tests/test_engine_pipeline.py` or equivalent: add a test asserting that when a prior `outcome_summary` is available, the rules user prompt contains `## Last Turn Outcome`. Assert it is absent on turn 1.
- Add a test asserting the assistant stub is present in the messages list for the rules LLM call (mock the LLM client, inspect call args).

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md`: note that `rules_user.j2` now accepts `last_outcome` (optional string) in its context, sourced from previous `TurnResult.outcome_summary`.
- `docs/REPOMAP/prompts.md` if it exists: update rules_user context variables.

### Risks
1. Assistant stub + `{` prepend: some LLM APIs reject assistant turns that don't end with a complete token boundary. Test with the actual model being used. Mitigation: if rejected, remove the stub — it's a nice-to-have, not load-bearing.
2. `outcome_summary` field: confirm this field exists on `TurnResult` and is populated by `extract_progress`. If it's sometimes empty string vs `None`, guard the template with `{% if last_outcome %}` (already done in the snippet above).
3. Turn 1 edge case: `prev_turn_result` is `None` on the first turn. The `getattr(None, ...)` call is safe but verify the actual variable name used in the rules context builder.

---

## Implementation — Phase 03: extract_progress user cleanup

### Files to pull for context
- `ccya/prompts/extract_progress_user.j2`
- `ccya/prompts/extract_progress_system.j2`

### Detailed steps

#### Step 3.1 — Remove behavioral rule restatement from `## gm_beat` section in user prompt

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Remove the instruction sentence that appears under `## gm_beat (optional...)` in the user prompt:

```
If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).
```

Replace the header with a minimal label that just signals the section exists for context:

**Code Snippet**
```jinja2
## gm_beat
{% if pending_beat -%}
## pending_beat (carried from previous turn — not yet surfaced)
Type: {{ pending_beat.type }} | Expires at turn: T{{ pending_beat.beat_expires_turn }}
Instruction: {{ pending_beat.instruction }}
{% endif -%}
```

**Why:** The full disposition decision tree (`consume` / `carry` / `replace`) and the beat behavior rules are already stated in `extract_progress_system.j2` under `beat_disposition`. Restating them in the user prompt adds tokens and creates a potential conflict surface if the two ever drift.

**Validation:** Diff confirms only the instruction text is removed. The `pending_beat` data block is preserved. Run an eval turn where a beat should be carried — confirm `beat_disposition: "carry"` is still emitted correctly by the model.

---

#### Step 3.2 — Remove behavioral rule restatement from `## scene_pressure_add` section in user prompt

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Replace the `## scene_pressure_add` instruction block with a minimal label:

Current (to remove):
```
## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
```

Replacement — just remove the block entirely. The `## Current Pressures` list below it already signals to the model that pressures exist, and the full rules are in system.

**Code Snippet**
```jinja2
{# scene_pressure_add instruction block removed — rules are in extract_progress_system.j2 #}
{% if quest_ages -%}
## quest_ages
...
```

**Why:** This is a restatement of system-level rules in the user prompt. It adds ~60 tokens per call with no signal the system prompt doesn't already provide. Unlike the `pending_beat` section, there's no per-turn data here — it's pure instruction.

**Validation:** Run an eval turn where a new pressure should be generated from a failed roll. Confirm `scene_pressure_add` is still emitted correctly. If not, the rule restatement was doing load-bearing work — restore it and note in Ambiguities.

### Tests to write or update
No new tests required. Existing eval scenario `pressure_lifecycle.py` covers scene pressure add/remove behavior and will catch regressions.

### REPOMAP and architecture updates
None — prompt text changes only.

### Risks
1. `## scene_pressure_add` removal: the instruction block may have been reinforcing system rules that the model was under-weighting at the user-turn boundary. If pressure generation degrades in eval, restore the block. This is the highest-risk change in Phase 03.
2. `## gm_beat` instruction removal: same risk. Beat disposition logic is nuanced (`carry` vs `replace` vs `consume`). If eval shows beat disposition errors increase, restore the abbreviated instruction. Mitigation: run `make eval` with `full_cycle` scenario after this phase before merging.

---

## Ambiguities requiring resolution before execution

1. **Step 2.2 — rules context builder location.** Where exactly is the dict passed to `rules_user.j2` constructed? It may be in `engine/rules.py`, `engine/turn.py`, or `engine/narrate.py`. Read `docs/REPOMAP/engine.md` to confirm before editing. Options: A) It's in `engine/rules.py` directly. B) It's assembled in `engine/turn.py` and passed down. The executor must not guess.

2. **Step 2.3 — assistant stub API compatibility.** Does the current `llm_client.chat()` call for the rules stream use a model/provider that accepts assistant-prefill? Options: A) Yes — implement stub as described. B) No or unknown — skip Step 2.3 and note as a follow-up. Do not implement if untested.

3. **Step 1.2 — Active pressures removal coverage.** After removing `## Active pressures (BINDING)` from `narrate_system.j2`, the instruction "weave the current pressure into your opening" is only present in the user prompt via the `**Narration Directive:** Pressure/Overwhelm` label. Confirm this is sufficient enforcement. Options: A) The directive label alone is enough — model has seen the full pressure text and the directive. B) The explicit "In the FIRST 2–3 sentences" instruction needs to be preserved somewhere — move it into `narrate_user.j2` near the `### Active Threats` section. Resolve by running one eval turn with an active immediate pressure before committing.
