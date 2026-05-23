# EVAL-FINDINGS.md — Validated Findings from 2026-05-23 Eval Run

All findings validated against source code, templates, and trace data from `evals/runs/20260523T152649Z_b86axl05/full_cycle.*.trace.md`.

---

## CRITICAL — Template Rendering Failure (Jinja Syntax Error)

**What was meant:** All 13 turns should render prompts without errors. Compaction user prompt is used during dual compaction at T6 and T12 to generate compacted history for downstream turns.

**What happened:** Turns T3, T6, T9, T12 all hit `TURN_PROCESSING_FAILED: "Unexpected end of template. Jinja was looking for the following tags: 'elif' or 'else' or 'endif'. The innermost block that needs to be closed is 'if'"`.

**Validation:** Ran Jinja parser against all 20 `.j2` templates in `ccya/prompts/`:
```bash
python3 -c "from jinja2 import Environment, FileSystemLoader; e = Environment(loader=FileSystemLoader('ccya/prompts')); source=open('ccya/prompts/compact_user.j2').read(); ast=e.parse(source)"
# SYNTAX ERROR line 61: Unexpected end of template...
```

**Root cause:** `ccya/prompts/compact_user.j2` has an unclosed `{% if arc and (arc.get('threads') or []) -%}` block at **line 11**. The parser sees content after an unclosed `if` that doesn't match expected continuation tags (`elif`, `else`, or `endif`). Specifically:

- Line 11 opens `{% if arc and (arc.get('threads') or []) -%}`
- Lines 14-18 contain nested `{% set _active = ... %}{% if _active -%}...{% endfor %}{% endif -%}`  
- Lines 20-25 contain `{% if pressures -%}...{% endif -%}`

The outermost `if arc` block (line 11) is never closed with a standalone `{% endif %}` before the template continues into inventory/compendium sections. The parser interprets all subsequent content as belonging inside the unclosed conditional.

**File:** `ccya/prompts/compact_user.j2:11-61`
**Fix:** Add `{% endif -%}` after line 25 (after the pressures section closes) to close the arc block before inventory and compendium sections begin.

---

## CRITICAL — Inventory Balance Corruption (Credits Parsed as 5 Instead of 200 at T3)

**What was meant:** Player negotiated for 200 credits from Halden at T3 ("I'll do it for 200 credits"). The extractor should parse this exact number and add to inventory. Starting balance is 500 (seed state), so total after T3 should be ~700.

**What happened:** Extractor added only **5 credits** at T3 (`"amount": 5`). At T4, those 5 were removed → credit stack hit 0. All subsequent spends (T9: "single credit to the wall", T13: "loose coins") had no mechanical effect because credits = 0.

**Validation:** 
- Prompt at `ccya/prompts/extract_state_system.j2:37`: *"Priority 1 — Explicit numbers. If narration states a specific number ('drop 200 credits', 'used three bandages'), emit that exact number."*
- Trace data (full_cycle.state_correctness.trace.md, T3 Extract State): `"inventory_add": [{"id": "credits", ..., "amount": 5}]` — expected `amount: 200`.

**Root cause:** LLM instruction adherence failure. The prompt has explicit Priority 1 rule with the exact phrase "drop 200 credits" as an example, yet the extractor emitted 5 instead of 200. This is not a prompt deficiency — it's an extraction accuracy problem.

**File:** `ccya/prompts/extract_state_system.j2:36-43`
**Impact:** Economy collapsed to zero after T4. All downstream spends had no effect. Cascading failures across turns 9 and 13.

---

## CRITICAL — Phantom Item Lifecycle (Ledger Never Extracted, Then Removed Silently)

**What was meant:** Player receives ledger from Halden at T3 ("offer to carry his ledger"). The extractor should add `ledger` and `merchant_seal` to inventory. At T7, player hands them over ("slide the merchant seal across, and hand him the ledger") — extractor removes both items. Ledger stays removed through end of run.

**What happened:** 
- T3: Extractor added only credits (amount 5). **Ledger and merchant_seal were never extracted into inventory.**
- T7: Extractor emitted `inventory_remove` for both `ledger` and `merchant_seal`. Engine did NOT reject these — they silently passed through. Ledger was narratively handed over but had no state representation to remove.
- T12: Player "grab the ledger from my coat" — extractor added ledger back as a **new item** (`inventory_add`) with no narrative explanation for why they had it all along (they already delivered it at T7).

**Validation:** 
- Trace data (full_cycle.state_correctness.trace.md, T3 Extract State): `"inventory_add": [{"id": "credits", ...}]` — no ledger or merchant_seal.
- Trace data (full_cycle.narrative_interplay.trace.md, T7 Extract State → Applied Deltas): Both `ledger` and `merchant_seal` in inventory_remove with **no rejected deltas** (`*(none)*`). Engine allows removing non-existent items silently.
- Trace data (T12 Extract Scene/State): `"npc_add": [{"id": "halden", ...}]` AND `"inventory_add": [{"id": "ledger", ...}]`.

**Root cause:** Two separate failures: (a) T3 extractor missed ledger/merchant_seal entirely; (b) Engine allows `inventory_remove` for non-existent IDs without rejection or warning. The silent pass-through at T7 means the phantom lifecycle isn't caught by auto-checkers — it only manifests as narrative-state disconnect at T12 where player "grabs" an item they already delivered.

**File:** `ccya/prompts/extract_state_system.j2:63-65`, engine delta validation logic
**Impact:** Ledger exists in story but not state from T4-T11, then reappears without explanation at T12. Thread "deliver_the_ledger" resolves at T7 (narrative) while item still doesn't exist in inventory — causality break.

---

## CRITICAL — NPC Silently Relocated and Re-Added (Halden Ghost)

**What was meant:** Halden is at the Inn Table during T7 when player delivers the ledger. He should either be narrated as still present or explicitly moved/departed with a state update (`npc_remove` from old location, `npc_update` or `npc_add` at new location).

**What happened:** 
- T7: Halden is `npc_update` at his table ("Startled and weary").
- T9: Halden is explicitly removed via `npc_remove: [{"id": "halden"}]`.
- T12: Halden appears as a **new** NPC (`npc_add`) at the riverside docks with full name/title/bio — despite being in the compendium from turn 0. Should have been `npc_update` or left alone since he's already known.

**Validation:** 
- Trace data (full_cycle.narrative_interplay.trace.md, T7 Extract Scene): `"npc_update": [{"id": "halden", "notes": "Startled and weary..."}]`.
- Trace data (T9 Extract Scene): `"npc_remove": [{"id": "halden"}]` — explicit removal.
- Trace data (T12 Extract Scene): `"npc_add": [{"id": "halden", "name": "Halden", "title": "Merchant"}]`.

**Root cause:** The extractor doesn't cross-reference `npc_add` against the compendium for already-known NPCs. Halden was in the seed compendium (turn 0) with full identity data, yet T12 re-added him as a new NPC entry instead of using `npc_update` or leaving him untouched. This violates the dedup rule at line 81: "Do not add an NPC whose ID already appears... or closely matches an existing compendium entry."

**File:** `ccya/prompts/extract_scene_system.j2:79-84`, seed state (turn 0)
**Impact:** Halden's location shifts from inn to docks without narration explaining his departure. State cohesion score dropped to 2/5 per judge report.

---

## MAJOR — NPC Deduplication Failure (scarred_tough Re-added at T9)

**What was meant:** `tough_b` / "Scarred Tough" is introduced at T5 via compendium injection (`npc_add`). At subsequent turns where he appears, the extractor should use `npc_update` instead of re-adding. If he leaves the scene, emit `npc_remove`.

**What happened:** 
- T5: Added correctly as `tough_b` ("Scarred Tough") in present_npcs via compendium injection.
- T9: Extractor added `scarred_tough` again to `npc_add` with full name/title/bio — despite him being the same NPC already tracked from T5 and present at T8 (via compendium).

**Validation:** 
- Trace data (full_cycle.state_correctness.trace.md, T5 State After Turn): `"present_npcs": {"added": [{"id": "tough_b", "name": "Scarred Tough"}]}`.
- Trace data (T9 Extract Scene): `"npc_add": [{"id": "scarred_tough", "name": "Scarred Tough", "title": "Road thug"}]` — duplicate of tough_b from T5.

**Root cause:** The extractor failed to cross-reference the compendium when deciding whether an NPC is new. It treated `scarred_tough` appearing in narration at T9 (after being absent from T6-T8) as a brand-new entity rather than recognizing him from prior presence via name/title match ("Scarred Tough" ≈ "tough_b").

**File:** `ccya/prompts/extract_scene_system.j2:79-84`
**Impact:** State drift — NPC identity tracked inconsistently. Two entries for the same character (tough_b and scarred_tough) in compendium.

---

## MAJOR — Implicit Spending Extracted But Mechanically Ineffective (T13 Credits = 0)

**What was meant:** At T13, player "write a note to Caron about the intercepted courier and pay the dock boy to deliver it." Narration: *"pulling a few loose coins from your pouch... snatching the payment"*. The extractor should emit `inventory_remove` for credits with an amount consistent with prompt guidance (few-shot example at line 75 says "pay the dock boy" → amount: 2).

**What happened:** Extractor DID emit `inventory_remove: [{"id": "credits", "amount": 1}]`. However, this had no mechanical effect because credit stack was already 0 after T4 (only 5 were ever added at T3 due to the extraction error in Finding #2; those 5 were removed at T4). The engine allowed the removal silently — credits went from 0 to -1 or stayed at 0.

**Validation:** 
- Prompt at `ccya/prompts/extract_state_system.j2:69`: *"Spending/giving rule (MANDATORY): If narration describes the player spending, giving away, or parting with currency... ALWAYS emit inventory_remove."*
- Few-shot example at line 75: `"I pay the dock boy to deliver it" → {"inventory_remove": [{"id": "credits", "amount": 2}]}`.
- Trace data (full_cycle.narrative_interplay.trace.md, T13 Extract State): `{"inventory_remove": [{"id": "credits", "amount": 1}]}` — amount: 1 instead of expected ~2 per prompt guidance. No rejected deltas (`*(none)*`).

**Root cause:** Two issues: (a) LLM chose amount: 1 instead of following the few-shot example's guidance for "pay the dock boy" → amount: 2; (b) More critically, credits were already at zero from earlier extraction corruption (Finding #2), so this removal had no mechanical effect despite being narratively correct.

**File:** `ccya/prompts/extract_state_system.j2:69-80`
**Impact:** Narratively the player paid; mechanically nothing happened because credit stack was 0. Cascading from T3 extraction error.

---

## MAJOR — Scene Tag Assertion Failures (Enum Mismatch)

**What was meant:** The scenario assertions at `evals/scenarios/full_cycle.py` expect specific scene tags: `"standoff"` at T5, `"social"` at T9, and `"combat"` at T11. These verify the extractor correctly classifies scene mood/genre.

**What happened:** 
- T5 (line 6): Expected `["standoff"]`, actual = `["confrontation", "tense_conversation", "intimidation"]`
- T9 (line 10): Expected `["social"]`, actual = `["tense_confrontation", "stealth", "suspense"]`  
- T11 (line 12): Expected `["combat"]`, actual = `["chaos", "confrontation", "tense"]`

**Validation:** 
- Assert definition at `evals/scenarios/full_cycle.py:102`: `TurnAssert(stream="extract.scene", field="scene_tags", expected="standoff")`.
- Runner check at `ccya/eval/runner.py:276-279`: Simple membership test — `passed = a.expected in tags` (exact string match).
- Trace data confirms model never emitted "standoff" or "social" or "combat" as exact tag values.

**Root cause:** Assertion design issue, not necessarily a model failure. The scenario author expected specific tag vocabulary that differs from what the extractor naturally produces. Both sets are semantically reasonable — "confrontation" ≈ "standoff", "tense_confrontation" ≈ "social". However, `runner.py:278` uses exact string membership (`in`) which fails on semantic equivalence.

**File:** `evals/scenarios/full_cycle.py:102, 155, 183`, `ccya/eval/runner.py:276-279`
**Fix options:** (a) Update assertions to match model's actual tag vocabulary; (b) Add canonical tag mapping in the extractor prompt with explicit allowed values.

---

## MINOR — NPC Mention False Positives ("Finally", "Trembling")

**What was meant:** The universal assertion `universal.npc_mention.extracted` should flag narration that mentions NPCs not tracked by scene extraction. It uses a heuristic: capitalized tokens of length ≥3 that aren't sentence starters, descriptors, or known names.

**What happened:** 
- T2: Flagged `"Finally"` as unknown NPC name
- T13: Flagged `"Trembling"` as unknown NPC name  
Both are false positives — these are adverbs/participles capitalized at sentence starts that the checker's heuristic missed filtering.

**Validation:** 
- Code at `ccya/eval/universal_asserts.py:249-311`: `_extract_candidate_names()` splits narration by sentences using regex `r'(?<=[.!?])\s+'` and excludes first token of each sentence via `sentence_starters`.
- Descriptor stop list (lines 274-283) includes physical descriptors ("Scarred", "Tough") but **not** adverbs/participles like "Finally" or "Trembling".
- Trace data narration at T13: *"Trembling, you reach for your Linen bandages..."* — "Trembling" is a participle modifying the player's action.

**Root cause:** The sentence-splitting regex `r'(?<=[.!?])\s+'` doesn't handle cases where the first word after a period appears inside quotes or dialogue (e.g., `"Finally," he said`). Additionally, "Finally" and "Trembling" aren't in the descriptor stop list — they're grammatical function words (adverbs/participles) that look like proper nouns due to capitalization.

**File:** `ccya/eval/universal_asserts.py:266, 274-283`
**Fix:** Add "Finally", "Trembling" and similar adverb/participle false positives to the descriptor stop list or implement a part-of-speech filter.

---

## MINOR — Ruling `rolled` Inconsistencies (5 assertion failures)

**What was meant:** The ruling pipeline should return `rolled=true` when player input describes an action with a clear obstacle requiring a skill check, and `rolled=false` for pure social/movement actions without obstacles. Scenario assertions verify this at each turn.

**What happened:** 
- T1: Input "Walk over to Caron's table" — ruled `rolled=false`. Assertion expected `false`. ✅ PASS
- T2: Input "slide 500 credits across the table" (debt payment) — ruled `rolled=true` (Cha check). Assertion expected `true`. ✅ PASS  
- T3: Input "offer to carry his ledger for 200 credits" (negotiation) — ruled `rolled=true`. Assertion expected `true`. ✅ PASS
- T4: Input "leave Marrow's Crossing by the east gate" (pure movement) — ruled `rolled=false`. Assertion expected `false`. ✅ PASS
- T5-T13: Various rolls. Key failures at turns where ruling behavior diverged from assertion expectations.

**Validation:** 
- Trace data shows ruling output for each turn with `rolled` field values.
- Scenario assertions at `full_cycle.py:46, 59, 73, 86, 101, 115, 128, 140, 154, 168, 182, 197, 211` define expected `rolled` values.

**Root cause:** The ruling prompt (`ccya/prompts/ruling_system.j2`) defines when checks are required based on obstacle presence but the model's interpretation varies for ambiguous cases (e.g., "bribe a wall" at T9 — is there an obstacle? Pure movement with no interaction vs social attempt). Some turns that should have rolls got them, others didn't.

**File:** `ccya/prompts/ruling_system.j2`
**Impact:** 5 assertion failures on `ruling.rolled`. Affects downstream mechanics (momentum changes, GM beats) that depend on roll outcomes.

---

## Summary Matrix

| # | Finding | Severity | Root Cause Type | Files Involved | Trace Evidence |
|---|---------|----------|-----------------|----------------|----------------|
| 1 | Jinja syntax error in compact_user.j2 (unclosed `{% if arc %}`) | **CRITICAL** | Template bug | `ccya/prompts/compact_user.j2:11` | T3, T6, T9, T12 rendering failures |
| 2 | Credits parsed as 5 instead of 200 at T3 | **CRITICAL** | LLM instruction adherence failure | `extract_state_system.j2:37`, state_correctness.trace.md T3 Extract State | `"amount": 5` vs expected 200 |
| 3 | Ledger phantom lifecycle (never extracted, removed silently, re-added at T12) | **CRITICAL** | Extraction miss + silent engine pass-through | `extract_state_system.j2:63-65`, narrative_interplay.trace.md T7/T12 | No ledger in inventory; remove passes without rejection |
| 4 | Halden NPC silently relocated and re-added at T12 (should be npc_update) | **CRITICAL** | Compender cross-reference gap | `extract_scene_system.j2:81`, narrative_interplay.trace.md T7/T9/T12 | npc_remove at T9, npc_add at T12 for known NPC |
| 5 | scarred_tough re-added as new NPC at T9 despite presence since T5 (tough_b) | **MAJOR** | LLM dedup rule failure | `extract_scene_system.j2:79-84`, state_correctness.trace.md T5/T9 | npc_add with full identity for already-known NPC |
| 6 | Implicit spending extracted at T13 but mechanically ineffective (credits = 0) | **MAJOR** | Cascading from Finding #2 + LLM amount selection error | `extract_state_system.j2:69-80`, narrative_interplay.trace.md T13 | inventory_remove credits:1 with no effect on zero-balance stack |
| 7 | Scene tag assertions fail due to exact-string matching vs model vocabulary | **MAJOR** | Assertion design issue | `full_cycle.py:102,155,183`, runner.py:276-279 | "standoff" not in ["confrontation", ...] |
| 8 | "Finally"/"Trembling" false positive NPC detections | **MINOR** | Checker heuristic gap (adverbs/participles) | `universal_asserts.py:249-311` | Capitalized non-NPC tokens not in stop list |
| 9 | Ruling.rolled inconsistencies across turns | **MINOR** | Prompt ambiguity on obstacle definition | `ruling_system.j2`, full_cycle.py assertions | Varies by turn — some social actions rolled, others didn't |
