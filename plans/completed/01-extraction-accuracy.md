# Extraction Accuracy

## Status
`completed`

## Phases

2 phases: strengthen the state extraction prompt for numerical/items extraction, then strengthen the scene extraction prompt for NPC deduplication.

## Issue

Three extraction failures from the eval run share the same root cause: the LLM doesn't follow prompt rules that are already correct. At T3, credits were parsed as `"amount": 5` instead of the explicit 200 stated in narration — despite a "Priority 1 — Explicit numbers" rule with the exact example "drop 200 credits". The ledger and merchant_seal were never extracted despite being narratively handed over. NPCs known from the compendium (Halden, scarred_tough) were re-added as new entries via `npc_add` instead of updated via `npc_update`, violating a dedup rule that already exists in the extract prompt.

These are not prompt-structure bugs; the rules exist. The model is failing on instruction adherence.

## Solution

Add structured output schema constraints, mandatory pre-extraction checks, and repetition-based emphasis to the extract prompts. The current rules are stated once as prose instructions. This plan adds: (a) a mandatory "check against the compendium" step before NPC `npc_add`, expressed as a numbered validation step rather than a rule; (b) a "first, verify the number" instruction before extraction for the state extractor; (c) pulling "Priority 1 — Explicit numbers" into a bold numbered checklist at the top of the extraction section.

## Firm decisions

1. Prompts are the only thing changing. No code changes to the engine or extractors.
2. The fix is emphasis + structure, not new rules. The rules are correct; the model needs stronger structural guards.
3. These changes may not fully fix adherence — extraction accuracy is an ongoing tuning concern. This plan makes the prompt as strict as possible without restructuring the stream architecture.

## Non-goals

- Not adding retry logic or LLM-call loops for failed extraction validation.
- Not changing the extractor JSON schema or adding post-extraction validation code.
- Not adding few-shot examples beyond what already exists.

## Risks, Ambiguities, and Blockers

- The primary risk is that adding more prompt structure increases token count. The state extract system prompt is already ~5800 chars. Adding ~200-400 chars is acceptable.
- No way to validate adherence changes without running the model. Recommended approach: run the full-cycle eval scenario after each prompt change and compare extraction accuracy scores. If scores degrade, revert.
- Blocker: no eval run automation in this plan. The executor must run `python3 -m ccya.eval.cli run full_cycle` and check the trace output for extraction fields at T3, T7, T9, T12.

---

## Implementation — Phase 1: Strengthen state extraction prompt for numbers and items

### Context files to load
- `ccya/prompts/extract_state_system.j2` — the full system prompt text
- `plans/EVAL-FINDINGS.md` — findings 1.1 (credits 5→200) and 1.2 (ledger phantom)

### Detailed steps

#### Step 1.1 — Add mandatory "verify the number" checklist at the top of the extraction section

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Before the existing "Priority 1 — Explicit numbers" prose, add a bold numbered checklist:

```
## Numerical extraction — mandatory checklist

Before you output any `inventory_add` or `inventory_remove` with an amount:

1. Find the exact number in the narration. If the narration states a specific number ("200 credits"), that is the number you must use.
2. Do NOT guess, estimate, or round the number. The narration number is authoritative.
3. If no number is stated, infer from context per Priority 2 below.
```

**Why:** The existing Priority 1 rule is expressed as prose in the middle of a paragraph. Moving it to a bold checklist at the top of the extraction section increases the chance the model attends to it.

**Validation:** `python3 -c "from jinja2 import Environment, FileSystemLoader; e = Environment(loader=FileSystemLoader('ccya/prompts')); e.parse(open('ccya/prompts/extract_state_system.j2').read())"` — must not raise syntax error.

#### Step 1.2 — Add "every item mentioned" extraction guard

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Before the existing "Match instruction" section, add:

```
## Item extraction — hard rule

If the narration describes the player receiving, carrying, collecting, or being handed an item — ANY item — you MUST emit an `inventory_add` for it. Do not skip items. Missing an item is worse than extracting an extra one.
```

**Why:** The ledger and merchant_seal were narratively handed over at T3 ("offer to carry his ledger") but never extracted. The current prompt has no guard against omission.

**Validation:** Same as step 1.1 — Jinja parse check.

### Tests to write or update

No automated tests for prompt adherence. Run `python3 -m ccya.eval.cli run full_cycle` after both phases and inspect T3 extraction output for `credits` amount and `ledger`/`merchant_seal` presence.

### REPOMAP updates required

None.

---

## Implementation — Phase 2: Strengthen scene extraction prompt for NPC deduplication

### Context files to load
- `ccya/prompts/extract_scene_system.j2` — the full system prompt text
- `plans/EVAL-FINDINGS.md` — findings 1.3 (Halden ghost), 1.4 (scarred_tough tough_b)
- `plans/FINDINGS.md` — section 1 extraction accuracy context

### Detailed steps

#### Step 2.1 — Add mandatory "before npc_add, check compendium" numbered step

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Before the "Deduplication rule" section, add a bold numbered step:

```
## NPC dedup — mandatory pre-check (apply BEFORE every npc_add)

Before you emit `npc_add` for ANY NPC:

1. Check the `## present_npcs` list. If the NPC is already there, use `npc_update` instead of `npc_add`.
2. Check the `<<<TRACE_IMMUTABLE>>> known_characters` compendium section. If the NPC's name or title matches an existing compendium entry, use that entry's ID and DO NOT emit `npc_add` — use `npc_update` if already present, or do nothing if they haven't entered the scene.
3. If the NPC was removed in a prior turn via `npc_remove` and is now returning, use `npc_add` with the existing compendium ID — but DO NOT re-emit `name`, `title`, or `bio` if those already exist in the compendium.

The engine will hydrate NPC identity from the compendium. You do not need to supply `name`/`title`/`bio` for known NPCs.
```

**Why:** The existing dedup rule at line 81 says "Do not add an NPC whose ID already appears..." but the model doesn't cross-reference before emitting. Making it a numbered pre-check step (not just a rule) forces attention before action.

**Validation:** Jinja parse check.

#### Step 2.2 — Remove the existing NPC dedup rule that this replaces

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** After adding step 2.1's new section, find and remove the existing dedup rule text: `**Do not add an NPC whose ID already appears in the \`## Present NPCs\` list or whose name/title closely matches an existing compendium entry.**` This is text in the existing "Deduplication rule" section.

**Why:** The new step 2.1 subsumes this rule with more structure. Keeping both would create conflicting instructions.

**Validation:** `rg "whose ID already appears" ccya/prompts/extract_scene_system.j2` returns zero matches.

### Tests to write or update

Run `python3 -m ccya.eval.cli run full_cycle` and inspect T9 and T12 scene extraction output. T9 should NOT produce `npc_add` for `scarred_tough`. T12 should NOT produce `npc_add` for `halden` — should use `npc_update` or no-op.

### REPOMAP updates required

None.
