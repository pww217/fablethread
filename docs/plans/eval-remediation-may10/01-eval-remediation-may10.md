# Eval Remediation — May 10, 2026 (01): Compactor Sanitization, Narrator Input, Currency Mapping

**Eval run:** `evals/runs/20260510T180913Z_2do6ma7m` · `full_cycle` (13 turns)  
**Pack:** `eval-pack` · **Model:** `gemma-4-26b-a4b-it-mxfp8`  
**Mechanical:** 3/5 · **Narrative:** 4/5  
**Related:** `02-extraction-quality.md` (extraction-quality issues from same eval)

---

## Problem Statement

Three issues from the May 10 eval require prompt-level remediation:

1. **Compactor sanitization failure** — Compactor fires at T6/T12 (multiples of `compact_every=6`) but the LLM returns `{}` for all sanitization actions. Quests are not closed, pressures are not removed, conditions are not resolved. The compactor produces history bullets but misses structural state cleanup.

2. **Narrator ignores player input** — Turn 7 narrator outputs stale context (rehashing the toughs confrontation from T5–T6) instead of processing the player's actual input (sitting with Halden, handing over the ledger and merchant seal). The narration spends significant prose on events the player already resolved.

3. **Currency mapping failure (follow-up)** — State extractor still emits `iron_coins` instead of mapping to `credits` despite earlier generic-item-mapping fix. The mapping rule in `extract_state_system.j2` is not being followed by the LLM.

---

## Phase 1: Compactor Sanitization Prompt Fix

**File:** `ccya/prompts/compact_system.j2`  
**Type:** Prompt-only  
**Risk:** Low — changes LLM instruction, not engine logic

### Problem

The compactor prompt (line 41) says: *"Only flag problems you are **highly confident** about — false positives cause data loss."* This instruction is too conservative. The LLM interprets it as "only flag problems you are 100% certain about" and returns `{}` even when there are clear opportunities:

- Quests with all objectives `done: true` but status still `active`
- Pressures whose triggering situation was resolved in narration
- Conditions that narration clearly shows as resolved

The compactor at T6 produced 3 bullets but `{}` for sanitization. At T12 it produced 6 bullets but `{}` for sanitization. The bullet production works; the sanitization section fails.

### Fix

Strengthen the sanitization instructions with three changes:

1. **Lower the confidence threshold** — Replace "highly confident" with "reasonably confident." Add: *"When the bulletin clearly shows a quest ended, a pressure resolved, or a condition cured, flag it even if you're not 100% certain. It's safer to close a quest that's already done than to leave it open."*

2. **Add explicit examples of what to flag** — The prompt lists categories but no concrete examples. Add:

```
### Examples (flag these)

- Quest `deliver_the_ledger` has all objectives `done: true` but status is still `active` → add to `quest_close`
- Pressure `imminent_combat` was resolved by a successful charisma check last turn → add to `pressure_remove`
- Condition `shaken` was resolved after the player found a safe place to rest → add to `condition_remove`
- Inventory `bandages` appears twice with different IDs → add duplicate ID to `inventory_remove`
```

3. **Add a "checklist" instruction** — Tell the LLM to systematically check each category:

```
### Checklist (check each category)

Before outputting, verify each category:
1. **npc_merge:** Are there two NPC entries that are clearly the same person?
2. **inventory_remove:** Are there duplicate inventory items with different IDs?
3. **quest_close:** Are there active quests with all objectives done, or quests that ended narratively?
4. **pressure_remove:** Are there pressures whose triggering situation is resolved?
5. **condition_remove:** Are there conditions that narration shows as cured/resolved?
6. **recent_events_compact:** Can similar events be merged? Is the list too long?

If a category has nothing to flag, omit it from the JSON. But check every category.
```

### Verification

- Re-run eval, check that compactor sanitization at T6/T12 produces non-`{}` JSON
- Verify quests are closed, pressures removed, conditions resolved in post-compaction state
- Verify bullets still produce correctly (no regression)

---

## Phase 2: Narrator Input Processing Fix

**File:** `ccya/prompts/narrate_system.j2`  
**Type:** Prompt-only  
**Risk:** Low — changes narrator instruction, not engine logic

### Problem

Turn 7 player input: *"I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat."*

The narrator's response (from trace) spends ~150 words on the toughs confrontation resolution (T5–T6 events) before reaching the actual Turn 7 action. The narration opens with:

> "The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words..."

This is stale context — the confrontation was already resolved. The player's input is about a completely different scene (sitting with Halden). The narrator should have opened directly with the Halden interaction.

Root cause: The narrator prompt's "Active scope tail" section and the user prompt's `prior_turn_narration` block create a strong narrative momentum that causes the LLM to continue describing the previous scene's resolution before pivoting to the new input. The narrator lacks an explicit instruction to prioritize the player's current input over narrative continuity from the previous turn.

### Fix

Add an explicit "player input priority" rule to the narrator prompt, placed after "Player intent is truth" (line 27):

```
## Player input takes priority

The player's stated action is the anchor for this turn. Open your narration with the player's action, not with a bridge from the previous turn. If the player changes scene, location, or focus, start fresh — do not rehash events the player already resolved. A brief transitional sentence is acceptable, but the bulk of your narration must address the current input.

Bad: "The tension of the confrontation at the door breaks... [150 words about toughs] ... Meanwhile, you sit across from Halden..."
Good: "You pull up a chair across from Halden and slide the ledger across the table. He stares at it, fingers grazing the leather..."
```

Also strengthen the "Player intent is truth" section (line 27) to add:

```
Take the player's stated action at face value and commit to it. The rules engine handles dice and conditions; the narrator handles fiction. 
Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.
**Open with the player's action. Do not spend more than one sentence bridging from the previous turn's events.**
```

### Verification

- Re-run eval, check Turn 7 narration opens with the Halden/ledger interaction
- Verify no more than 1–2 sentences of transitional context from previous turn
- Verify the player's actual input (handing ledger + seal) is the primary focus

---

## Phase 3: Currency Mapping Strengthening

**File:** `ccya/prompts/extract_state_system.j2`  
**Type:** Prompt-only  
**Risk:** Low — strengthens existing mapping rule

### Problem

The generic item mapping rule (lines 76–92) exists but the LLM still sometimes emits `iron_coins` instead of mapping to `credits`. The rule provides examples but lacks a strong enough directive. The LLM treats the mapping as "suggested" rather than "mandatory."

The current rule says: *"If the narration references a generic denomination or container term, you MUST map it to the closest matching ID in the ## inventory list. NEVER invent a new inventory ID for a generic term."*

The `MUST` and `NEVER` are present but the LLM is not following them. The rule needs reinforcement with a stronger framing and a concrete consequence statement.

### Fix

Strengthen the generic item mapping section with three changes:

1. **Add a "zero-tolerance" framing** at the top of the section:

```
## Generic item mapping (ZERO TOLERANCE)

If the narration references a generic denomination or container term, you MUST map it to the
closest matching ID in the ## inventory list. NEVER invent a new inventory ID for a generic term.

**This rule has zero tolerance. Inventing a currency ID (e.g., "iron_coins", "silver", "gold_piece")
when an existing currency ID (e.g., "credits") is in inventory is a critical failure.**
```

2. **Add a "what happens if you fail" consequence:**

```
If you invent a currency ID instead of mapping to an existing one, the game state will contain
a phantom item that doesn't exist in the player's actual inventory. This breaks all inventory
tracking for that turn and every subsequent turn. When in doubt, map to the existing currency ID.
```

3. **Add a "verify before emitting" step:**

```
Before emitting any inventory_remove or inventory_add involving currency:
1. Check the ## inventory list for an existing currency ID
2. If one exists, use it — even if the narration uses a different term
3. If none exists, do NOT emit the change
```

### Verification

- Re-run eval, check that state extractor maps all currency references to `credits`
- Verify no `iron_coins` or other invented currency IDs appear in extracted deltas
- Verify existing currency mapping still works (no regression on correct mappings)

---

## Phase Summary

| Phase | File | Change | Risk |
|---|---|---|---|
| 1 | `ccya/prompts/compact_system.j2` | Strengthen sanitization instructions: lower confidence threshold, add examples, add checklist | Low |
| 2 | `ccya/prompts/narrate_system.j2` | Add "player input takes priority" rule; limit transitional bridging to 1 sentence | Low |
| 3 | `ccya/prompts/extract_state_system.j2` | Strengthen currency mapping with zero-tolerance framing and consequence statement | Low |

---

## Coordination with `02-extraction-quality.md`

This plan addresses compactor sanitization (Phase 1) and currency mapping (Phase 3). The `02-extraction-quality.md` plan addresses:
- Compaction phase logging (its Phase 1) — different issue, same compactor
- Inventory amount parsing (its Phase 2) — different state extractor issue
- Quest dedup (its Phase 3), ambient NPC filtering (its Phase 4), auto-checker (its Phase 5), rubric (its Phase 6)

**Recommended execution order:**
1. This plan (01): Phases 1–3 (compactor sanitization, narrator input, currency mapping)
2. `02-extraction-quality.md`: Phases 1–6 (compaction logging, amount parsing, quest dedup, ambient NPC, auto-checker, rubric)

Both plans are prompt-only. No engine code changes required.

---

## Mark as completed (items from existing TODO that this plan addresses):

- [ ] **Compactor sanitization failure** — compactor fires at T6/T12 but LLM returns `{}` for all sanitization actions; quests not closed, pressures not removed — see `[eval-remediation-may10/01-eval-remediation-may10.md](eval-remediation-may10/01-eval-remediation-may10.md) Phase 1`
- [ ] **Narrator ignores player input** — Turn 7 narrator outputs stale context instead of processing input — see `[eval-remediation-may10/01-eval-remediation-may10.md](eval-remediation-may10/01-eval-remediation-may10.md) Phase 2`
- [ ] **Currency mapping failure (follow-up)** — state extractor still emits `iron_coins` instead of mapping to `credits` despite earlier fix; strengthened prompt directive needed — see `[eval-remediation-may10/01-eval-remediation-may10.md](eval-remediation-may10/01-eval-remediation-may10.md) Phase 3`
