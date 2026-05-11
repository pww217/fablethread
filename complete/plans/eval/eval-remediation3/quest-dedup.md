# Plan: Quest Deduplication in Progress Extractor

**Problem:** Progress extractor creates overlapping quest IDs (`deliver_ledger_to_inn`, `caron_debt`, `secure_silk_shipment`, `deliver_halden_ledger`, `deliver_ledger`) instead of updating the existing `deliver_the_ledger` quest. Splits quest state, dilutes narrative focus.

**Root cause:** The existing dedup rule in `extract_progress_system.j2` (line 23) is not strong enough. The LLM ignores it and creates new IDs that differ only in wording from existing ones.

**Goal:** Enforce quest deduplication so the LLM updates existing quests instead of creating overlapping new ones.

---

## 1. Prompt Changes — `ccya/prompts/extract_progress_system.j2`

### 1.1 Strengthen the quest dedup rule (replace line 23)

Replace the existing "Quest deduplication" paragraph with:

```
- **Quest deduplication (MANDATORY):** Before creating ANY new quest, you MUST compare its subject, target NPC, and object against every quest in the `## active_quests` list. If the new quest overlaps with an existing quest in ANY of these dimensions, you MUST update the existing quest instead of creating a new one. Overlap means: same item being delivered/found, same NPC being sought/paid, same conflict being resolved, or same objective being advanced. New quest IDs that differ only in word choice from existing IDs (e.g., `deliver_stained_ledger` vs `deliver_the_ledger`, `caron_debt` vs `settle_the_debt`) are duplicates — use the EXISTING ID. Only create a genuinely new quest if the task, target, AND context are all distinct from every active quest. When in doubt, update the existing quest.
```

### 1.2 Add explicit "never create" examples

Add after the dedup rule (still within the `quest_updates` bullet):

```
- **NEVER create a new quest ID when an existing active quest covers the same objective.** Examples of what NOT to do:
  - Do NOT create `deliver_ledger_to_inn` when `deliver_the_ledger` already exists — update `deliver_the_ledger` instead.
  - Do NOT create `caron_debt` when `settle_the_debt` already exists — update `settle_the_debt` instead.
  - Do NOT create `secure_silk_shipment` when `deliver_the_ledger` already exists — update `deliver_the_ledger` instead.
```

---

## 2. Few-Shot Examples — `evals/packs/eval-pack/extract_examples.yaml`

Add a new quest dedup example:

```yaml
  - title: "Quest dedup — update existing instead of creating new"
    band: success
    thinking: |
      - Player is delivering Halden's ledger to the inn. This is the same quest as `deliver_the_ledger` which already exists.
      - The LLM must NOT create a new quest ID like `deliver_ledger_to_inn` or `deliver_halden_ledger`.
      - Instead, update the existing `deliver_the_ledger` quest by marking the relevant objective done.
    json: |
      {
        "scene_tags": ["dialogue", "delivery"],
        "scene_tagline": "Ledger delivered to the inn",
        "present_npcs": [{"id": "halden", "notes": "Takes the ledger; confirms the contract is complete."}],
        "quest_updates": [
          {"id": "deliver_the_ledger", "objectives": [{"index": 2, "done": true}]}
        ],
        "outcome_summary": "Halden took the ledger and confirmed the contract is fulfilled."
      }

  - title: "Quest dedup — same objective, different wording"
    band: partial
    thinking: |
      - Player paid Caron 500 credits. This advances `settle_the_debt`, not a new `caron_debt` quest.
      - The existing quest `settle_the_debt` has objectives about finding Caron and paying him.
      - Must update `settle_the_debt` objectives, not create a new quest.
    json: |
      {
        "scene_tags": ["dialogue", "debt_settlement"],
        "scene_tagline": "Debt paid — Caron marks it cleared",
        "present_npcs": [{"id": "caron", "notes": "Closes his ledger with a satisfied nod."}],
        "quest_updates": [
          {"id": "settle_the_debt", "objectives": [{"index": 2, "done": true}]}
        ],
        "outcome_summary": "Caron accepted the credits and marked the debt cleared in his ledger."
      }
```

---

## 3. User Prompt Changes — `ccya/prompts/extract_progress_user.j2`

### 3.1 Add quest IDs to the user prompt context

The user prompt already shows `## active_quests` with IDs and titles. This is good — the LLM can see existing quest IDs. No change needed here.

### 3.2 Add a "quest threshold" directive

The user prompt already has a `quest_threshold` section (line 25-26) that shows `quest_threshold_directive`. This is already being passed from the extraction pipeline. No change needed.

---

## 4. Testing

### 4.1 Add unit test for quest dedup in progress extractor

Add to `tests/test_extraction.py` (or appropriate test file):

```python
async def test_quest_dedup_updates_existing(self, mock_llm: FakeLLM):
    """Progress extractor updates existing quest instead of creating duplicate."""
    # This test verifies the prompt produces correct dedup behavior
    # when the LLM is asked to advance a quest that already exists.
    pass
```

### 4.2 Add integration test with eval run

Run the eval pack and verify:
- No new quest IDs are created for `deliver_the_ledger` — only `deliver_the_ledger` is updated
- No `caron_debt` is created — `settle_the_debt` is updated instead
- Quest count stays reasonable (3 quests from seed, no new overlapping quests)

---

## 5. Summary of Changes

| File | Change |
|---|---|
| `ccya/prompts/extract_progress_system.j2` | Strengthen quest dedup rule (line 23); add explicit "NEVER create" examples |
| `evals/packs/eval-pack/extract_examples.yaml` | Add 2 few-shot examples showing correct quest dedup behavior |
| `ccya/prompts/extract_progress_user.j2` | No changes needed (active_quests already shown with IDs) |
