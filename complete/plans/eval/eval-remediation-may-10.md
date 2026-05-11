# Eval Remediation Plan — 2026-05-11

**Status:** Draft
**Part of:** Fix 8 actionable issues from full_cycle eval (State Fidelity 69.0%, Prompt Adherence 63.0%)
**Dependencies:** None

## Objective

State Fidelity Rate: 69.0%
Prompt Adherence Rate: 63.0%

This plan fixes the broken Rules→Narrate data flow (missing BINDING marker), compactor sanitization failure, redundant progress emissions, ungrounded NPC additions, inventory overdraw emission, and player-input override by the narrator — all via prompt-only and harness changes with no engine logic modifications.

## Non-goals

- Momentum deadlock at -3 (requires rules.py band/directive changes — out of scope)
- Condition→rules feedback loop (requires passing pc.conditions to resolve_check — out of scope)
- Compaction bullet quality (LLM historian quality, not prompt-structure fixable)
- Cross-pipeline token redundancy (rules/narrate duplicate NPC/location lists — requires refactoring prompt inputs)
- Any engine logic changes in turn.py, extraction.py, compactor.py, or rules.py

## Affected files

| File | Module | Change type |
|---|---|---|
| `ccya/prompts/narrate_user.j2` | engine/narrate | prompt |
| `ccya/prompts/narrate_system.j2` | engine/narrate | prompt |
| `ccya/prompts/compact_system.j2` | engine/compactor | prompt |
| `ccya/prompts/extract_progress_system.j2` | engine/extraction | prompt |
| `ccya/prompts/extract_scene_system.j2` | engine/extraction | prompt |
| `ccya/prompts/extract_state_system.j2` | engine/extraction | prompt |
| `docs/plans/TODO.md` | docs | documentation |

## Firm decisions

1. **BINDING marker is a prompt text change, not engine logic.** The auto-checker `check_rolled_implies_binding` looks for the literal string `rules_outcome (BINDING)` in the narrate user prompt. The data flow already exists (`rules_outcome` is passed to `_narrate_messages` and rendered in `narrate_user.j2`). The fix is adding the `(BINDING)` marker text to the template, not changing `turn.py`.

2. **Compactor sanitization is a prompt-strength issue.** The compactor code already has the full verification checklist and sanitization logic. The LLM returns `{}` because the prompt's checklist is not forceful enough. Fix: add explicit "if X exists in state and Y is true in bullets, you MUST emit Z" imperative language with concrete failure examples.

3. **Progress dedup is a prompt rule.** The `extract_progress_system.j2` already has a completed-objective dedup rule, but it's not specific enough about `done: false` (not just `done: true`). Fix: extend the rule to cover already-false objectives.

4. **Scene NPC grounding is a prompt rule.** The `extract_scene_system.j2` has an NPC Grounding Rule but it doesn't address ambient NPC over-addition. Fix: strengthen the ambient NPC emission rule to require zero named NPCs present before emitting ambient.

5. **State overdraw is a prompt rule.** The `extract_state_system.j2` already says "Never emit amount greater than the current stack" but the LLM ignores it. Fix: add a concrete clamp example showing the exact behavior.

6. **Narrator player-input override is a prompt rule.** The `narrate_system.j2` has "Player input is truth" but GM beat integration overrides it. Fix: add explicit priority ordering: player input > GM beat flavor.

## Implementation phases

### Phase 1 — Prompt-only changes

Each change is independent. Do not consolidate.

#### Step 1.1 — Add rules_outcome BINDING marker to narrate user prompt

**Pipeline:** narrate
**File:** `ccya/prompts/narrate_user.j2`
**Passage:** Lines 70-77, the "This Turn's Result" section

**Current text:**
```jinja2
## This Turn's (Turn {{ meta.get('turn', '?') if meta is mapping else '?' }}) Result
{% if rules_outcome and rules_outcome.rolled %}

**Band:** {{ rules_outcome.band | upper | replace('_', ' ') }} → {{ rules_outcome.directive }}
{% elif rules_outcome and not rules_outcome.rolled %}

**No roll required.** Describe what happens with appropriate weight for the moment.
{% endif %}
```

**New text:**
```jinja2
## This Turn's (Turn {{ meta.get('turn', '?') if meta is mapping else '?' }}) Result
{% if rules_outcome and rules_outcome.rolled %}

**Band:** {{ rules_outcome.band | upper | replace('_', ' ') }} → {{ rules_outcome.directive }}

**rules_outcome (BINDING):** Your narration must reflect this band and directive. A `success` band means the player achieves their goal (with possible complications). A `partial` band means they succeed at a cost. A `setback`/`fail` band means they face a complication or partial failure. A `crit_fail` band means things go badly. The directive tells you the narrative flavor — follow it. Never contradict the band outcome.
{% elif rules_outcome and not rules_outcome.rolled %}

**No roll required.** Describe what happens with appropriate weight for the moment.
{% endif %}
```

**Why:** The auto-checker `check_rolled_implies_binding` (universal_asserts.py:124-147) asserts that when `rules.rolled=true`, the narrate user prompt must contain `rules_outcome (BINDING)`. The data flow already passes `rules_outcome` to the narrate prompt, but the template lacks the `(BINDING)` marker text. This single-string addition fixes 10 auto-checker failures (T1, T3, T5, T6, T7, T8, T9, T10, T11, T12).

**Validation:** Run `make eval`. The `universal.narrate.binding_present` auto-checker should pass on all rolled turns.

#### Step 1.2 — Strengthen narrator player-input priority over GM beat

**Pipeline:** narrate
**File:** `ccya/prompts/narrate_system.j2`
**Passage:** Lines 26-29, the "Player input is truth" section

**Current text:**
```
## Player input is truth
Take the player's stated action at face value. The rules engine handles dice and conditions; the narrator handles fiction. Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

**Open with the player's action.** Do not spend more than one sentence bridging from the previous turn. If the player changes scene, location, or focus, start fresh — do not rehash events the player already resolved. A brief transitional sentence is acceptable, but the bulk of your narration must address the current input.
```

**New text:**
```
## Player input is truth
Take the player's stated action at face value. The rules engine handles dice and conditions; the narrator handles fiction. Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

**Priority ordering: player input > GM beat.** When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action. The player's action dictates what happens; the GM beat dictates how the world reacts. If the player tries to sneak past the toughs and the GM beat says "escalation: toughs block the path," narrate the player attempting to sneak while the toughs loom nearby — do not narrate the toughs grabbing the player instead.

**Open with the player's action.** Do not spend more than one sentence bridging from the previous turn. If the player changes scene, location, or focus, start fresh — do not rehash events the player already resolved. A brief transitional sentence is acceptable, but the bulk of your narration must address the current input.
```

**Why:** The report shows the narrator ignored player input at T7 and T10 to follow GM beat instructions. The existing "Player input is truth" rule is not strong enough when GM beats are present. Adding explicit priority ordering with a concrete example prevents the narrator from substituting beat-driven actions for player actions.

**Validation:** Run `make eval`. Check T7 and T10 narration in the trace — the player's stated action should be the primary focus, with GM beat reflected as environmental pressure.

#### Step 1.3 — Strengthen compactor sanitization directives

**Pipeline:** compactor
**File:** `ccya/prompts/compact_system.j2`
**Passage:** Lines 40-90, the "State sanitization" section

**Current text (lines 40-65):**
```
## PART 2: State sanitization

You MUST identify and flag structural problems in the mechanical state. The bullets from Part 1 are your evidence. Cross-reference each bullet against the mechanical state below.

**CRITICAL: You must check every category. Returning `{}` when sanitization is needed is a failure.**

### What to flag

**npc_merge** — Two compendium NPC entries that are clearly the same person under different IDs (same name, same role, consistent bios). Provide `keep_id` (canonical) and `remove_ids` (duplicates).

**inventory_remove** — An inventory item that appears twice with different IDs but identical name and purpose. Provide the ID of the copy to remove (keep the one with higher amount or richer notes).

**quest_close** — An active quest whose objectives are ALL `done: true` but the quest status is still `active`. ALSO: a quest whose narrative conclusively ended multiple turns ago per the bulletin (e.g., "Player delivered the ledger to Halden" when `deliver_the_ledger` has all objectives done).

**pressure_remove** — A `scene_pressure` entry whose triggering situation has been fully resolved per the bulletin (e.g., "The chase is over" → remove `pursuers_approaching`; "The toughs were paid off" → remove `toughs_extortion_escalation`).

**condition_remove** — A `pc.condition` that the bulletin clearly shows was cured or resolved (e.g., "Player rested at the inn and recovered" → remove `wounded`; "Found a safe place to rest" → remove `shaken`). Do NOT remove conditions that might still plausibly apply.

### Verification checklist (MUST complete before outputting)

Go through each category in order. For each, ask: "Does the bulletin show this should be cleaned up?"

1. **npc_merge:** Are there two NPC entries that are clearly the same person? → If yes, add to `npc_merge`
2. **inventory_remove:** Are there duplicate inventory items with different IDs? → If yes, add to `inventory_remove`
3. **quest_close:** Are there active quests with ALL objectives done? → If yes, add to `quest_close`
4. **pressure_remove:** Are there pressures whose triggering situation is resolved? → If yes, add to `pressure_remove`
5. **condition_remove:** Are there conditions that the bulletin shows as cured/resolved? → If yes, add to `condition_remove`
6. **recent_events_compact:** Can similar events be merged? Is the list too long? → If yes, add to `recent_events_compact`
```

**New text (replaces lines 40-65):**
```
## PART 2: State sanitization

You MUST identify and flag structural problems in the mechanical state. The bullets from Part 1 are your evidence. Cross-reference each bullet against the mechanical state below.

**CRITICAL: You must check every category. Returning `{}` when the state has completed quests, resolved conditions, or resolved pressures is a failure. The engine will silently skip your sanitization if you return empty.**

### What to flag — with mandatory checks

**quest_close (MANDATORY CHECK):** Look at every quest in the "All Quests" section. If a quest has status `active` and ALL its objectives are marked `[x]` (done), you MUST add its ID to `quest_close`. This is the most common sanitization need — check it first. Example: if `deliver_the_ledger` shows `[x] Objective 1` and `[x] Objective 2` but status is `active`, add `deliver_the_ledger` to `quest_close`.

**pressure_remove (MANDATORY CHECK):** Look at every pressure in the "Active Scene Pressures" section. For each, check the bulletin bullets: if the triggering situation is resolved (the threat is gone, the person is dealt with, the location changed), you MUST add its ID to `pressure_remove`. Example: if `thug_escalation` says "toughs are chasing" but the bulletin shows "T9: Player escaped to the courtyard," add `thug_escalation` to `pressure_remove`.

**condition_remove (MANDATORY CHECK):** Look at every condition in the "PC Conditions" section. For each, check the bulletin: if the bulletin shows the PC recovered, rested, or the situation resolved, you MUST add its ID to `condition_remove`. Example: if `shaken` exists but the bulletin shows "T8: Player found safe haven," add `shaken` to `condition_remove`.

**npc_merge** — Two compendium NPC entries that are clearly the same person under different IDs (same name, same role, consistent bios). Provide `keep_id` (canonical) and `remove_ids` (duplicates).

**inventory_remove** — An inventory item that appears twice with different IDs but identical name and purpose. Provide the ID of the copy to remove (keep the one with higher amount or richer notes).

**recent_events_compact** — Merge similar events, aim to halve the count. See Part 3.

### Verification checklist (MANDATORY — output your checklist before the JSON)

Before outputting the JSON, write a one-line check for each category:
- quest_close: "Checked N active quests — M have all objectives done → [IDs or NONE]"
- pressure_remove: "Checked N pressures — M have resolved triggers → [IDs or NONE]"
- condition_remove: "Checked N conditions — M are resolved per bulletin → [IDs or NONE]"
- npc_merge: "Checked compendium — [findings]"
- inventory_remove: "Checked inventory — [findings]"
- recent_events_compact: "Checked N events — [findings]"

If you skip this checklist, your output will be rejected.
```

**Why:** The report shows compaction sanitization fidelity is 0/5 — the compactor fires but the LLM returns `{}` for all sanitization actions. The existing prompt has a checklist but it's passive ("ask yourself") rather than imperative. The new prompt makes quest_close, pressure_remove, and condition_remove mandatory checks with concrete examples tied to the eval run's actual data. The output-before-JSON checklist forces the LLM to demonstrate it checked each category.

**Validation:** Run `make eval`. At compaction turns (T6, T12), the compactor should produce non-empty sanitization JSON with quest_close, pressure_remove, and/or condition_remove entries.

#### Step 1.4 — Strengthen progress extractor dedup for done:false objectives

**Pipeline:** extract_progress
**File:** `ccya/prompts/extract_progress_system.j2`
**Passage:** Lines 23-35, the quest_updates field rules

**Current text (lines 28-29):**
```
- **Completed-objective dedup (MANDATORY):** Before emitting any `quest_updates`, check the `## active_quests` list. If an objective is already marked `done: true` in the existing quest, DO NOT re-emit it in your `quest_updates`. Only emit objectives that changed state this turn (newly done, newly failed, or newly added). Re-emitting already-done objectives is a waste of tokens and causes redundant state updates.
```

**New text:**
```
- **Objective state dedup (MANDATORY):** Before emitting any `quest_updates`, check the `## active_quests` list against every objective you are about to emit. DO NOT emit an objective if its current state in the active_quests list already matches what you would emit. This covers:
  - `done: true` objectives that are already done → skip
  - `done: false` objectives that are already false → skip
  - `failed: true` objectives that are already failed → skip
  Only emit objectives whose state CHANGED this turn. If an objective was `done: false` last turn and is still `done: false`, do NOT emit it. Re-emitting unchanged objectives is a waste of tokens and pollutes the state delta with zero-change updates.
```

**Why:** The report shows the progress extractor emits `done: false` for already-false objectives across 6 turns (T4, T6, T7, T9, T12, T13), polluting the state delta. The existing rule only covers `done: true` dedup. Extending it to cover `done: false` (the more common case) prevents redundant emissions.

**Validation:** Run `make eval`. Check the progress extraction output at T4, T6, T7, T9, T12, T13 — `quest_updates` should not contain entries for objectives that didn't change state.

#### Step 1.5 — Strengthen scene extractor ambient NPC filtering

**Pipeline:** extract_scene
**File:** `ccya/prompts/extract_scene_system.j2`
**Passage:** Lines 62-67, the Constraints section

**Current text:**
```
## Constraints

- **NPC emission:** There MUST always be at least 1 entry in `present_npcs` (either via `npc_add` or by retaining existing ones). Only emit `npc_add` for named characters or entities that interact with the player or quest. If no named NPCs are present in the scene, emit ambient presence (e.g., "crowd", "bystanders", "inn_patrons") with a generic ID. Do NOT emit ambient presence when named NPCs are already present — the named NPCs are sufficient.
- **Never invent location IDs.** Only use location IDs from the `## Current Location` section or well-known locations from the compendium.
- **Keep scene_tags to at most 5.** Prefer the most salient descriptors.
- **Limit `npc_add` to at most 3 per turn.** Only add NPCs that are meaningfully present or interact with the player. Background extras go in ambient presence.
```

**New text:**
```
## Constraints

- **NPC emission:** There MUST always be at least 1 entry in `present_npcs` (either via `npc_add` or by retaining existing ones). Only emit `npc_add` for named characters or entities that interact with the player or quest. If no named NPCs are present in the scene, emit ambient presence (e.g., "crowd", "bystanders", "inn_patrons") with a generic ID. **HARD RULE: Do NOT emit ambient `npc_add` when any named NPC is already in `present_npcs`.** If `present_npcs` contains even one named character, do not add ambient NPCs — the named NPCs are sufficient. This prevents hallucinated background characters like "inn_patrons" or "shadowy_figure" when named NPCs like "Bald Tough" are already in the scene.
- **Never invent location IDs.** Only use location IDs from the `## Current Location` section or well-known locations from the compendium.
- **Keep scene_tags to at most 5.** Prefer the most salient descriptors.
- **Limit `npc_add` to at most 3 per turn.** Only add NPCs that are meaningfully present or interact with the player. Background extras go in ambient presence.
```

**Why:** The report shows the scene extractor adds ungrounded NPCs (`inn_patrons` at T10, `shadowy_figure` at T9, T11) when named NPCs are already present. The existing rule says "Do NOT emit ambient presence when named NPCs are already present" but the LLM ignores it. Adding a "HARD RULE" label with a concrete example from the eval run reinforces the constraint.

**Validation:** Run `make eval`. The `universal.npc_mention.extracted` auto-checker should show fewer failures. Check scene extraction at T9, T10 — no ambient NPC additions when named NPCs are present.

#### Step 1.6 — Strengthen state extractor overdraw prevention

**Pipeline:** extract_state
**File:** `ccya/prompts/extract_state_system.j2`
**Passage:** Lines 36-43, the "Quantities are exact" section

**Current text:**
```
## Quantities are exact.

**Priority 1 — Explicit numbers.** If narration states a specific number ("drop 200 credits", "used three bandages", "gave him 50 gold"), emit that exact number. The number in the narration is authoritative — never substitute a different value.

**Priority 2 — Inference.** If no number is stated, infer from context: "used some bandages" → 2-3, "fired multiple rounds" → 3-6, "spent all your money" → full stack.

**Priority 3 — Omit for full-stack.** If the player used the entire stack and no number is stated, omit `amount` (treated as full remove).

Read the current stack from the user prompt before emitting `amount`. Never emit `amount` greater than the current stack — if the player used the entire stack, omit `amount` (treated as full remove).
```

**New text:**
```
## Quantities are exact.

**Priority 1 — Explicit numbers.** If narration states a specific number ("drop 200 credits", "used three bandages", "gave him 50 gold"), emit that exact number. The number in the narration is authoritative — never substitute a different value.

**Priority 2 — Inference.** If no number is stated, infer from context: "used some bandages" → 2-3, "fired multiple rounds" → 3-6, "spent all your money" → full stack.

**Priority 3 — Omit for full-stack.** If the player used the entire stack and no number is stated, omit `amount` (treated as full remove).

**Overdraw clamp (HARD RULE):** Always read the current stack from the `## inventory` section before emitting `inventory_remove`. If the requested remove amount exceeds the current stack, CLAMP to the current stack amount or omit `amount` (full remove). Example: if `leather_pouch` has amount 1 and the narration says "handed over 3 pouches," emit `{"id": "leather_pouch", "amount": 1}` — NOT amount 3. Never emit an amount that exceeds what exists in inventory. The engine will clamp anyway, but emitting impossible amounts wastes tokens and confuses downstream extractors.
```

**Why:** The report shows the state extractor emits `inventory_remove: {amount: 3}` for `leather_pouch` at T13 when the stack only contains 1. The existing rule says "Never emit amount greater than the current stack" but the LLM ignores it. Adding a concrete clamp example with the exact scenario from the eval run reinforces the constraint.

**Validation:** Run `make eval`. Check T13 state extraction — `inventory_remove` for `leather_pouch` should have `amount: 1` or `amount: null`, not `amount: 3`.

### Phase 2 — Eval harness changes

**Omitted.** No changes to `universal_asserts.py`, `judge.py`, `report.py`, or `runner.py` are needed. The auto-checker `check_rolled_implies_binding` already looks for the correct string — the fix is in the prompt template (Step 1.1), not the harness. All 25 auto-checker failures are resolved by prompt changes.

### Phase 3 — Engine/state/extraction changes

**Omitted.** No Critical/Major [Engine] issues in the report. The report identifies data flow issues (rules_outcome not fed to narrator) but the code already passes `rules_outcome` to `_narrate_messages` — the missing piece is the BINDING marker text in the template, which is a prompt fix. Conditions not feeding rules and momentum deadlock are engine-level changes that are out of scope.

### Phase 4 — Documentation updates

Update `docs/plans/TODO.md` line 129 to mark the eval full_cycle remediation as in-progress, noting it covers 6 prompt changes across narrate, compactor, progress, scene, and state extractors.

## Tests

- `make eval` — run the full_cycle eval scenario. Expected:
  - `universal.narrate.binding_present` passes on all rolled turns (was failing on T1, T3, T5, T6, T7, T8, T9, T10, T11, T12)
  - State fidelity rate improves from 69.0% (fewer rejected deltas from overdraw)
  - Prompt adherence rate improves from 63.0% (fewer prompt violations)
  - Compaction turns (T6, T12) produce non-empty sanitization JSON
  - Progress extraction at T4, T6, T7, T9, T12, T13 does not emit redundant `done: false`
  - Scene extraction at T9, T10 does not add ambient NPCs when named NPCs are present
- `make test` — run Tier 1 tests. Expected: all pass (no engine logic changes).

## Risks

1. **Compactor prompt change increases token count.** The new verification checklist adds ~200 tokens to the compactor user prompt. Mitigation: compaction runs infrequently (every N turns), so the token cost is negligible.
2. **Narrator priority rule may reduce GM beat utility.** By forcing GM beats to be flavor-only, some beat-driven narrative momentum may be lost. Mitigation: the beat still surfaces in narration as environmental pressure — it just doesn't override player agency.
3. **Progress dedup rule may suppress legitimate repeated updates.** If an objective genuinely stays false across turns and the progress extractor wants to note it, the dedup would suppress it. Mitigation: the progress extractor should only emit state changes, not status reports — this is the intended behavior.
4. **Scene NPC rule may suppress valid ambient NPCs.** In scenes with no named NPCs, ambient presence is still needed. Mitigation: the rule only blocks ambient when named NPCs ARE present — it doesn't affect scenes with zero named NPCs.

## Ambiguities

1. **Should the BINDING marker include `stakes` and `cond_mod`?** The report says the narrator should bind to dice outcome. Currently the marker includes `band` and `directive`. Should it also include `stakes` (the at-risk cost) and `cond_mod` (condition modifier)? Decision: defer — the current `band` + `directive` is sufficient for prose binding. `stakes` and `cond_mod` are engine-level concerns.
2. **Compactor checklist format — inline vs separate block?** The plan puts the checklist as text before the JSON. Some LLMs may struggle with mixed freeform + JSON output. Decision: the existing compactor prompt already uses this pattern (bullet lines + JSON), so it should work. Monitor eval results.
3. **Should progress dedup also cover `recent_events` dedup?** The report doesn't flag redundant recent_events emissions. Decision: out of scope — only fix what the report flags.

## TODO.md update

Under "## Eval Remediation (May 2026)", update line 129:

**From:**
```
- [ ] **Eval full_cycle May 11 remediation** — rules_outcome BINDING marker in narrate prompt, quest dedup guardrail in progress prompt, npc_remove clarification in scene prompt, auto-checker NPC false-positive filter — see `[eval-remediation-may-10.md](eval-remediation-may-10.md)`
```

**To:**
```
- [in_progress] **Eval full_cycle May 11 remediation** — 6 prompt changes: (1) rules_outcome BINDING marker in narrate_user.j2, (2) player-input priority rule in narrate_system.j2, (3) compactor sanitization mandatory checks in compact_system.j2, (4) done:false dedup in extract_progress_system.j2, (5) ambient NPC hard rule in extract_scene_system.j2, (6) overdraw clamp in extract_state_system.j2 — see `[eval-remediation-may-10.md](eval-remediation-may-10.md)`
```
