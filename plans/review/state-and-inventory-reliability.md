# State and Inventory Integrity

## Status
`open`

## Part of
standalone

## Dependencies
- none

## Objective
Three distinct but related inventory failures corrupt state in every run: (1) the narrator invents item usage when a stack is at zero or an item is absent, producing phantom narration that extraction correctly attempts to apply but the engine rejects; (2) empty-stack weapons/consumables are usable without any failure feedback to the player; (3) inventory amounts drift when extraction emits an incorrect quantity. Together these produce a compounding credits-at-zero death spiral (T6–T13 in the May 11 run) and silent amount mismatches. This plan eliminates all three at the prompt level — the narrator is the first and cheapest place to stop the failure chain.

## Non-goals
- Does not change `_validate()` rejection logic — that layer stays as the safety net, not the primary fix.
- Does not touch the compactor, progress extractor, or scene extractor.
- Does not address condition lifecycle (separate concern).
- Does not introduce new engine state fields.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/prompts/narrate_system.j2` | modify | Add zero-stack / absent-item constraint rule and empty-weapon failure rule |
| `ccya/prompts/narrate_user.j2` | modify | Reinforce inventory cross-reference with explicit zero-stack instruction in the inventory block header |
| `ccya/prompts/extract_state_system.j2` | modify | Add explicit few-shot for zero-stack overdraw: when narrator describes spending nonexistent credits, emit nothing, do not emit a remove delta |
| `ccya/prompts/sections/_inventory.j2` | modify | Emit explicit zero-quantity markers so narrator can see at a glance which items are depleted |
| `docs/REPOMAP/prompts.md` | update | Document new zero-stack rules in narrate_system and extract_state_system entries |

## Firm decisions

1. The narrator is the fix, not the validator. Stopping phantom spends at narration time eliminates the rejected delta entirely rather than logging a failure after the fact.
2. Zero-stack items must be visibly marked in the inventory block so the model doesn't have to infer emptiness — it reads it directly.
3. The extract_state few-shot covers the inverse case: if a narrator somehow still invents a spend (model error), the extractor should not try to honor it when the item is absent.
4. Weapon ammo is treated as a quantity field — a weapon with 0 ammo is identical to any other 0-stack item.
5. No new Pydantic fields or engine changes in this phase.

## Implementation — Phase 1: Narrator Zero-Stack Rules

### Context files to load
- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/sections/_inventory.j2`

### Overview
Add a hard constraint to the narrator system prompt preventing use of zero-stack or absent items. Modify the inventory partial to surface zero quantities explicitly. Add a reinforcing note in the user prompt inventory block header.

### Detailed steps

#### Step 1.1 — Add zero-stack constraint to narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add a new rule block under the existing `inventory hard constraint` rule. The new rule must be adjacent to it and clearly numbered/labeled.

**Why:** The narrator currently has a rule against inventing items not in inventory, but no rule against using items that are present but at zero quantity. This is the root cause of the credits death spiral.

**Text to add (after the existing inventory constraint rule):**

```
**ZERO-STACK RULE (MANDATORY):** Before describing any item use, spending, or consumption, check the quantity in the inventory block. If an item shows quantity 0 or is marked [DEPLETED], the player cannot use it. You MUST narrate the attempt failing — "You reach for your coin purse — empty." / "You raise the pistol and pull the trigger — nothing. The magazine is dry." — do NOT narrate the action succeeding with a substituted item and do NOT invent alternative items. The failure is the narration.
```

**Validation:** Render the system prompt for a turn where credits = 0. Confirm the zero-stack rule text appears in the output.

***

#### Step 1.2 — Mark depleted items in _inventory.j2

**File:** `ccya/prompts/sections/_inventory.j2`

**What:** For each item in the inventory list, if quantity == 0, append `[DEPLETED]` after the item entry. If quantity > 0, render normally.

**Why:** The narrator must be able to see zero-quantity at a glance without inferring it from context. Making it explicit eliminates the ambiguity that causes phantom spending.

**Current pattern (approximate):**
```
- {{ item.name }}: {{ item.quantity }}
```

**New pattern:**
```
{% if item.quantity == 0 %}- {{ item.name }}: 0 [DEPLETED]
{% else %}- {{ item.name }}: {{ item.quantity }}
{% endif %}
```

For items without a quantity field (non-countable), render unchanged.

**Validation:** Create a test fixture with a zero-quantity credits entry. Render `_inventory.j2`. Confirm `[DEPLETED]` appears next to the zero-stack item.

***

#### Step 1.3 — Reinforce in narrate_user.j2 inventory header

**File:** `ccya/prompts/narrate_user.j2`

**What:** Change the inventory section header comment from:
```
## inventory (cross-reference before describing item use)
```
to:
```
## inventory (MANDATORY: cross-reference before any item use — items marked [DEPLETED] cannot be used)
```

**Why:** Belt-and-suspenders. The user prompt header is the last thing the model sees before it would write item usage. A stronger label reduces the chance it skips the check.

**Validation:** Render narrate_user for a normal turn. Confirm header text updated.

***

## Implementation — Phase 2: Extractor Few-Shot for Phantom Spends

### Context files to load
- `ccya/prompts/extract_state_system.j2`

### Overview
Add a few-shot negative example to the state extractor covering the case where narration describes spending a zero-stack item. The extractor should emit no delta, not a remove delta that will be rejected.

### Detailed steps

#### Step 2.1 — Add zero-stack overdraw few-shot to extract_state_system.j2

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Add a new few-shot example adjacent to the existing spending/giving few-shot examples. The example covers: narration says player spent credits, but inventory shows credits = 0.

**Why:** Even with the narrator fix, edge cases will occur — model errors, first-turn race conditions. The extractor must not emit a remove delta for an item that isn't there, because that delta will always be rejected and pollutes the event log.

**Text to add (in the few-shot section, after the existing spending examples):**

```
EXAMPLE — Zero-stack item (emit nothing):
Narration: "You press a handful of coins into his palm."
Inventory: credits: 0 [DEPLETED]
→ Do NOT emit inventory_remove for credits. The narrator made an error. If the item has no quantity, emit nothing for that item.
```

**Validation:** Confirm the example renders in the system prompt for extract_state. In the next eval run, check whether credits remove deltas are emitted on turns where credits = 0.

***

### Tests to write or update
- `tests/test_prompts.py` or equivalent: render `_inventory.j2` with a fixture item at quantity 0 → assert `[DEPLETED]` in output.
- `tests/test_prompts.py`: render `narrate_system.j2` → assert `ZERO-STACK RULE` appears.
- No engine-level test needed for Phase 2 (few-shot text change only).

### REPOMAP updates required
- `docs/REPOMAP/prompts.md`: under `narrate_system.j2` entry, add: "zero-stack / absent-item use constraint rule; empty-weapon failure rule."
- `docs/REPOMAP/prompts.md`: under `extract_state_system.j2` entry, add: "zero-stack overdraw few-shot (emit nothing when narrator describes spend of absent/depleted item)."

### Risks
1. **`[DEPLETED]` marker confuses extractor** — mitigation: the extractor system prompt already scopes to narration as source of truth, not the inventory block directly. The marker is narrator-facing only.
2. **Narrator still invents spend on first turn before inventory is loaded** — mitigation: seed generation should initialize all quantities to > 0 for items the player is meant to start with. That's a seed plan concern, not this one.
3. **Items with no quantity field (non-countable, unique items)** — mitigation: the `_inventory.j2` change only fires on quantity == 0, not on absent quantity field.

## Ambiguities requiring resolution before execution
1. Does `_inventory.j2` currently use `item.quantity` or a different field name? The REPOMAP shows `Condition` has an `id` field but inventory field names aren't fully listed. Options: A) field is `quantity` — proceed as written. B) field is `amount` or `count` — adjust template accordingly. Executor must read `_inventory.j2` and `models.md` to confirm the field name before modifying.

## TODO.md update
Add under **P2 — Stability / Fidelity**:
```
- [ ] [State/Inventory Integrity — zero-stack narrator constraint + extractor few-shot](plans/state-inventory-integrity.md)
```

