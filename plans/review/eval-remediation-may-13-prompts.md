# Eval Remediation Plan — 2026-05-13 — Prompt Fixes

**Status:** Draft
**Part of:** Full cycle eval remediation — engine, prompts, harness
**Dependencies:** `eval-remediation-may-13-engine.md` (Phase 1 fixes quest objective filtering; this plan adds prompt-level guards)

## Conflicts and overlap

This plan handles **prompt changes** only. A companion plan `eval-remediation-may-13-engine.md` handles engine code fixes (quest objective filtering bug, auto-checker NPC false positives). The two plans can run in parallel since they touch disjoint file sets.

---

## Objective

**State Fidelity Rate:** 85.0%
**Prompt Adherence Rate:** 92.0%

Strengthen two prompts to reduce LLM non-compliance: (1) narrate_system.j2 — add explicit negative constraint against altering numerical values from player input, and (2) extract_progress_system.j2 — add few-shot examples for quest dedup and empty objectives prevention.

## Non-goals

- Engine code fixes (handled in companion plan `eval-remediation-may-13-engine.md`)
- Auto-checker harness changes (handled in companion plan)
- Compaction prompt changes (report rated compaction 4/5, no issues found)
- Rules/narrate binding (report rated rules 5/5, no issues)
- Scene/state extractor prompts (report rated both 5/5, no issues)

---

## Affected files

| File | Module | Change type |
|---|---|---|
| `ccya/prompts/narrate_system.j2` | engine (prompts) | prompt |
| `ccya/prompts/extract_progress_system.j2` | engine (prompts) | prompt |
| `docs/REPOMAP/prompts.md` | docs | docs |

---

## Firm decisions

1. **Narrate prompt: add explicit negative constraint on numerical values.** The current "Player input is truth" rule (line 26-40 of narrate_system.j2) is strong but the LLM still altered "500 credits" to "fifty coins" at T2. The fix is to add a concrete negative constraint with an example, similar to the existing conflict example.

2. **Progress prompt: add few-shot examples for quest dedup and empty objectives.** The current prompt has rules against re-emitting completed quests (lines 42-46) and quest dedup (lines 29-51), but the LLM still violated them at T2, T6, T7. The fix is to add more explicit few-shot examples showing the correct behavior.

3. **No changes to progress prompt for empty objectives at creation.** The engine fix in the companion plan (Phase 1) removes the `if o.description` filter, which is the root cause. The prompt already says "Use `description` only when adding a new objective" (line 25), which is ambiguous. The companion plan clarifies this by preserving all objectives the LLM emits.

---

## Implementation phases

### Phase 1 — Strengthen "Player input is truth" in narrate prompt

**Pipeline:** Narrate
**File:** `ccya/prompts/narrate_system.j2`
**Passage:** Lines 26-40 (Player input is truth section)

**Current text:**
```
## Player input is truth (HIGHEST PRIORITY)

Take the player's stated action at face value. The rules engine handles dice and conditions; the narrator handles fiction. Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

**Priority ordering: player input > GM beat > stakes/directive.** When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action. The player's action dictates what happens; the GM beat dictates how the world reacts.

**Conflict example (READ CAREFULLY):**
- Player says: "I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger."
- GM beat says: "pressure: toughs circle and flank the player"
- WRONG: Narrate the toughs attacking and the player fighting them (this replaces the player's action).
- RIGHT: Narrate the player sitting down and sliding the seal/ledger across the table FIRST. Then describe the toughs circling and flanking as the player attempts this action — the toughs' presence is the environmental pressure, not the main event. The player's action (sitting, sliding seal, handing ledger) is the primary narration.

**Fallback for conflicts:** If player input and GM beat conflict, narrate the player's action FIRST (2-3 sentences describing the action completing or failing), then integrate the beat as an environmental reaction or NPC behavior that occurs during or immediately after. The player's stated action is the primary event; the GM beat is the world's response. Never narrate the GM beat event as if it replaced the player's action.

**Open with the player's action.** Do not spend more than one sentence bridging from the previous turn. If the player changes scene, location, or focus, start fresh — do not rehash events the player already resolved. A brief transitional sentence is acceptable, but the bulk of your narration must address the current input.
```

**New text:**
```
## Player input is truth (HIGHEST PRIORITY)

Take the player's stated action at face value. The rules engine handles dice and conditions; the narrator handles fiction. Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

**Priority ordering: player input > GM beat > stakes/directive.** When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action. The player's action dictates what happens; the GM beat dictates how the world reacts.

**Numerical values are sacred.** NEVER alter explicit numerical values from player input. If the player says "500 credits", you narrate "five hundred credits" or "the 500 credits" — never "fifty coins" or "a handful of coins". This applies to all quantities: credits, items, distance, time, damage. The rules engine handles costs and consequences; the narrator preserves the player's numbers exactly.

**Numerical value example (READ CAREFULLY):**
- Player says: "I slide 500 credits across the table to Caron."
- WRONG: "You slide the fifty coins across the table." (changed 500 to 50)
- WRONG: "You hand over a thick stack of credits." (vague, lost the number)
- RIGHT: "You slide the 500 credits across the table to Caron." (preserved exact number)
- RIGHT: "You slide five hundred credits across the table to Caron." (spelled out but preserved value)

**Conflict example (READ CAREFULLY):**
- Player says: "I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger."
- GM beat says: "pressure: toughs circle and flank the player"
- WRONG: Narrate the toughs attacking and the player fighting them (this replaces the player's action).
- RIGHT: Narrate the player sitting down and sliding the seal/ledger across the table FIRST. Then describe the toughs circling and flanking as the player attempts this action — the toughs' presence is the environmental pressure, not the main event. The player's action (sitting, sliding seal, handing ledger) is the primary narration.

**Fallback for conflicts:** If player input and GM beat conflict, narrate the player's action FIRST (2-3 sentences describing the action completing or failing), then integrate the beat as an environmental reaction or NPC behavior that occurs during or immediately after. The player's stated action is the primary event; the GM beat is the world's response. Never narrate the GM beat event as if it replaced the player's action.

**Open with the player's action.** Do not spend more than one sentence bridging from the previous turn. If the player changes scene, location, or focus, start fresh — do not rehash events the player already resolved. A brief transitional sentence is acceptable, but the bulk of your narration must address the current input.
```

**Why:** The report (Section 3B, Section 4G) identifies T2 narration drift where "500 credits" became "fifty coins". The existing "Player input is truth" rule is at HIGHEST PRIORITY but the LLM still violated it. Adding a dedicated "Numerical values are sacred" subsection with a concrete example (mirroring the existing conflict example format) gives the LLM a specific negative constraint to follow. The example directly mirrors the T2 failure case.

**Validation:** Re-run eval. T2 narration should preserve "500" (either as digits or spelled out). Narrate pipeline score should improve from 4/5 to 5/5. State fidelity rate should improve (T2 narration drift is one of two drift turns).

---

### Phase 2 — Strengthen quest dedup few-shot in progress prompt

**Pipeline:** Progress Extract
**File:** `ccya/prompts/extract_progress_system.j2`
**Passage:** Lines 42-46 (NEVER emit a completed quest again section)

**Current text:**
```
  - **NEVER emit a completed quest again:**
    State says: `settle_the_debt.status = "completed"`
    Narration: "You shake hands; the debt is settled."
    Wrong extract: `{"id": "settle_the_debt", "status": "active", "objectives": [...]}` — This is WRONG. Do not re-activate completed quests.
    Correct extract: (omit entirely — the quest is already completed, no update needed)
```

**New text:**
```
  - **NEVER emit a completed quest again:**
    State says: `settle_the_debt.status = "completed"`
    Narration: "You shake hands; the debt is settled."
    Wrong extract: `{"id": "settle_the_debt", "status": "active", "objectives": [...]}` — This is WRONG. Do not re-activate completed quests.
    Correct extract: (omit entirely — the quest is already completed, no update needed)

  - **Completed quest re-emission examples (READ CAREFULLY):**
    State: `settle_the_debt.status = "completed"`, `clear_the_road_toughs.status = "completed"`
    Narration: "The debt is paid and the road is clear."
    Wrong extract: `{"id": "settle_the_debt", "objectives": [{"index": 2, "done": true}]}` — WRONG. Quest is already completed.
    Wrong extract: `{"id": "clear_the_road_toughs", "objectives": [{"index": 2, "done": true}]}` — WRONG. Quest is already completed.
    Correct extract: (omit both quests — they are already completed, no update needed)

    State: `deliver_the_ledger.status = "completed"`
    Narration: "You delivered the ledger to Halden at the inn."
    Wrong extract: `{"id": "deliver_the_ledger", "objectives": [{"index": 2, "done": true}, {"index": 3, "done": true}]}` — WRONG. Quest is already completed.
    Correct extract: (omit — quest is already completed)
```

**Why:** The report (Section 3E, Section 6) identifies quest dedup failures at T2, T6, T7 where the progress extractor re-emitted completed quests. The current prompt has a rule against this (lines 42-46) but only one example. Adding more concrete examples with multiple completed quests in the same state makes the rule harder to miss. The examples directly mirror the T2 (settle_the_debt), T6 (clear_the_road_toughs), and T7 (deliver_the_ledger) failure cases.

**Validation:** Re-run eval. `progress.quest_id_collision` auto-checker should pass on all turns. Progress pipeline score should improve from 3/5 to 4/5+.

---

### Phase 3 — Add empty objectives prevention to progress prompt

**Pipeline:** Progress Extract
**File:** `ccya/prompts/extract_progress_system.j2`
**Passage:** Lines 24-25 (New quest schema guidance)

**Current text:**
```
- New quest: `{"id": "snake_case_new_id", "title": "Quest Title", "status": "active", "objectives": [{"description": "first objective"}]}`. Use `description` only when adding a new objective.
```

**New text:**
```
- New quest: `{"id": "snake_case_new_id", "title": "Quest Title", "status": "active", "objectives": [{"description": "first objective"}]}`. Use `description` only when adding a new objective. **NEVER emit a quest with an empty objectives array.** Every new quest must have at least one objective with a `description`. If you cannot determine an objective from the narration, do not create the quest — wait for more information.
```

**Why:** The report (Section 1E, Section 6) identifies T8 where `deliver_halden_ledger` was created with `objectives: []`. The current prompt says "Use `description` only when adding a new objective" which is ambiguous — the LLM interpreted this as "you can emit objectives with only `index` and `done`". Adding an explicit "NEVER emit a quest with an empty objectives array" rule prevents this. Note: the engine fix in the companion plan (Phase 1) also removes the `if o.description` filter, so objectives without descriptions will be preserved. But the prompt rule prevents the LLM from creating quests with no objectives at all.

**Validation:** Re-run eval. T8 `deliver_halden_ledger` should either have populated objectives (if the LLM can infer them from context) or not be created at all (if no objectives can be determined). The engine fix ensures that if objectives ARE emitted (even without descriptions), they are preserved.

---

## Tests

- `make test` — all existing tests should pass. Prompt changes don't affect test logic (tests use FakeLLM).
- Re-run eval: `make eval` — verify:
  - T2 narration preserves "500" (either digits or spelled out)
  - `progress.quest_id_collision` passes on all turns
  - T8 `deliver_halden_ledger` has populated objectives or is not created
  - Prompt adherence rate improves from 92% to ~97%
  - Progress pipeline score improves from 3/5 to 4/5+
  - Narrate pipeline score improves from 4/5 to 5/5

## Risks

1. **Adding more examples to the progress prompt increases token count.** The new text adds ~120 tokens to the system prompt. This is negligible compared to the ~4.5k token user prompt per progress call. Total progress tok_in at T13 is 4406 — a 120-token increase is ~2.7%.

2. **The "Numerical values are sacred" rule in narrate prompt may feel restrictive.** The rule is narrow: it only applies to explicit numerical values from player input. It does not prevent the narrator from using "a handful" for vague quantities. The T2 failure was specifically about changing 500 to 50, which this rule directly addresses.

3. **Quest creation with empty objectives may still occur if the LLM is uncertain.** The prompt rule says "do not create the quest" if no objectives can be determined. This is the correct behavior — an empty quest is worse than no quest. The engine fix (companion plan) ensures that if objectives ARE emitted, they are preserved.

## Ambiguities and posed design questions

1. **Should the narrate prompt also address the inventory hard constraint rule?** The current inventory rule (line 24 of narrate_system.j2) says "verify the item appears in the `## inventory` list". This is separate from the numerical value rule. The T2 failure was about numerical values, not inventory. No change needed.

2. **Should the progress prompt add a rule about quest title?** The T8 `deliver_halden_ledger` had `title: ""` (empty). The prompt says `"title": "Quest Title"` but the LLM emitted empty. This is a minor issue — the engine's `_strip_non_ascii` handles empty titles gracefully. Not worth adding a rule for.

3. **Should the quest dedup rule be moved earlier in the prompt?** The current placement (lines 42-46) is after the objective state dedup section. Moving it earlier might improve compliance. However, the current order follows the logical flow: (1) how to update, (2) how to create, (3) dedup rules, (4) examples. Changing the order is a cosmetic change with uncertain benefit.

## Execution order summary

| Phase | File | Steps | Description |
|---|---|---|---|
| 1 | `ccya/prompts/narrate_system.j2` | 1 | Add "Numerical values are sacred" subsection with example |
| 2 | `ccya/prompts/extract_progress_system.j2` | 1 | Add completed quest re-emission few-shot examples |
| 3 | `ccya/prompts/extract_progress_system.j2` | 1 | Add "NEVER emit empty objectives" rule for new quests |

**Total steps:** 3 prompt changes
**Estimated impact:** Prompt adherence 92% → ~97%, progress pipeline 3/5 → 4/5+, narrate pipeline 4/5 → 5/5
