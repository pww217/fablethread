# Currency System Fix

## Purpose

Fix the extraction LLM's currency hallucination bug by seeding a currency item in every pack and correcting the extraction prompt's guidance.

## Problem Statement

The state extraction LLM sometimes invents currency items (e.g., `iron_coins`, `cash`) or stores amounts as notes on unrelated items (e.g., `diagnostic_tablet: "Credits transferred: 6,666"`) instead of emitting proper `inventory_add`/`inventory_remove` for the currency. This happens because the extraction prompt tells the LLM to "omit the change entirely" when no currency ID exists in inventory — but the game's economy relies on currency transactions every turn. The LLM then takes a third path: storing amounts as notes on other items, which is neither tracked nor usable.

## Constraints

- No new data model fields. Currency stays as an inventory item.
- No dedicated currency field on the PC.
- Minimal prompt changes — no examples, no new sections.
- All packs must have a seeded currency item.
- Latency-sensitive: no additional LLM calls or prompt bloat.
- Different packs use different currencies (dollars, credits, etc.).

## Non-goals

- Multi-currency exchange rates.
- Bank/wallet/account abstraction.
- Transaction history.
- Currency-specific mechanics (interest, denominations).
- A dedicated `pc.credits` field.

## Solution

Add a `currency_id` field to the pack's scenario manifest. The seed generation code injects the currency item into the initial inventory. The extraction prompt's currency rule is corrected from "omit if no currency ID exists" to "emit with the pack's currency ID." This is three targeted changes across four files.

## Firm decisions

1. `currency_id` lives in `ScenarioBrief` in `ccya/pack.py`.
2. The seed injector in `ccya/engine/seed.py` adds the currency item after LLM generation.
3. The extraction prompt change is one sentence replacement on line 23 of `extract_state_system.j2`.
4. Each pack's `scenario.yaml` declares its currency ID and starting amount.
5. No narration prompt changes — narration already handles currency correctly.
6. No extraction examples — the rule text change is sufficient.

## Risks, Ambiguities, and Blockers

- **Static packs:** Packs with `seed_state.yaml` (eval pack) don't go through `generate_seed()`. The injector in `seed.py` won't run for them. These packs must have the currency item in their `seed_state.yaml` directly.
- **Dynamic packs without scenario:** Packs that use `seed_state.yaml` as a static seed (not through `generate_seed()`) also won't get the injector. They must have the currency in their seed file.
- **Existing saves:** Old saves without a currency item will still trigger the "omit" behavior until the player earns or spends currency. This is acceptable — the fix prevents future hallucinations.

## Status
`completed`

## Phases

Three phases: (1) pack schema + injector, (2) extraction prompt fix, (3) pack updates.

---

## Implementation — Phase 1: Pack schema + seed injector

### Context files to load
- `ccya/pack.py` (lines 132-161: `ScenarioBrief`)
- `ccya/engine/seed.py` (lines 370-387: post-generation processing)
- `ccya/models.py` (lines 220-230: `InventoryItem`, `InventoryRemove`)

### Detailed steps

#### Step 1.1 — Add currency fields to ScenarioBrief

**File:** `ccya/pack.py`

**What:** Add two optional fields to `ScenarioBrief`:
```python
currency_id: str = ""
starting_currency_amount: int = 0
```
Place them after `scene_detail_bundles` (around line 160). Both are optional with defaults so existing packs don't break.

**Why:** The pack manifest declares what currency the world uses. The injector reads these to seed the initial inventory.

**Validation:** `python -c "from ccya.pack import ScenarioBrief; s = ScenarioBrief(); assert s.currency_id == ''; assert s.starting_currency_amount == 0"`

#### Step 1.2 — Inject currency into seed envelope

**File:** `ccya/engine/seed.py`

**What:** After the existing post-generation processing (after line 373, before the soft validation at line 375), add logic to inject the currency item:

1. Check if `scenario.currency_id` is non-empty.
2. If so, check if an item with that ID already exists in `envelope.seed_state.inventory`.
3. If not, append an `InventoryItem(id=scenario.currency_id, name=scenario.currency_id.title(), amount=scenario.starting_currency_amount, notes="")` to the inventory list.

**Why:** The LLM-generated seed doesn't know about the pack's currency. The injector adds it after generation, ensuring every dynamic pack starts with its currency in inventory. This prevents the extraction prompt's "omit" clause from triggering.

**Validation:** Run a new game in a pack with `currency_id` set. Verify the currency item appears in the initial inventory in `state.yaml`.

---

## Implementation — Phase 2: Extraction prompt fix

### Context files to load
- `ccya/prompts/extract_state_system.j2` (line 23)

### Detailed steps

#### Step 2.1 — Fix the currency omission rule

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Replace line 23:
```
Old: "If no currency ID exists, omit the change entirely."
New: "If the narration mentions currency but no matching currency ID exists in inventory, emit `inventory_add` with the pack's currency ID (from the seed inventory's currency item)."
```

**Why:** The current rule tells the LLM to ignore currency changes when no currency exists — which is the root cause of the hallucination. The new rule tells the LLM to use the pack's currency ID as the canonical identifier, preventing it from inventing new currency IDs or storing amounts as notes.

**Validation:** Run a turn where the narration mentions currency. Verify the extraction emits `inventory_add` or `inventory_remove` with the correct currency ID instead of hallucinating or omitting.

---

## Implementation — Phase 3: Pack updates

### Context files to load
- `packs/default/space-western/scenario.yaml`
- `packs/default/noir-1930s/scenario.yaml`
- `packs/default/zombie-survival/scenario.yaml`
- `packs/default/golden-piracy/scenario.yaml`
- `packs/default/sengoku-japan/scenario.yaml`
- `packs/default/allied-ww2/scenario.yaml`

### Detailed steps

#### Step 3.1 — Add currency to each pack's scenario.yaml

**File:** Each pack's `scenario.yaml` (top level, alongside `constraints:`)

**What:** Add `currency_id` and `starting_currency_amount` to each pack:

| Pack | currency_id | starting_currency_amount |
|---|---|---|
| space-western | `credits` | 100 |
| noir-1930s | `dollars` | 50 |
| zombie-survival | `credits` | 0 |
| golden-piracy | `doubloons` | 25 |
| sengoku-japan | `ryō` | 30 |
| allied-ww2 | `dollars` | 75 |

**Why:** Each pack needs its currency declared so the injector can seed it. Starting amounts reflect the pack's economy (frontier spacers start with more than zombie survivors).

**Validation:** Run a new game in each pack. Verify the currency item appears in the initial inventory with the correct amount.

---

## Documentation updates

- `docs/repomap.md`: Update `ScenarioBrief` entry in the pack.py section to include `currency_id` and `starting_currency_amount` fields.
- `docs/architecture/`: Update the seed generation section to mention the currency injection step.

## Tests to write or update

None — tests are temporarily disabled during refactor per AGENTS.md.
