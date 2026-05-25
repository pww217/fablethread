# Inventory Decision Record

## Problem

The inventory system has persistent accuracy issues. Three failure modes recur:

| Failure | Description |
|---|---|
| **False additions** | Items NPCs possess or that exist in the scene are added to PC inventory |
| **False removals** | Items are removed when "used" but not consumed (keys, tools) or when a transaction fails |
| **Currency splitting** | Narrative synonyms ("coins", "gold") become new inventory IDs instead of mapping to the existing currency ID (e.g. "credits") |

## Root cause

The state extractor LLM is asked to convert narrative prose into precise mechanical deltas. This is the wrong abstraction — LLMs are poor at bookkeeping from ambiguous language. Current mitigations (160-line prompt with few-shot examples, durability gate, fuzzy matching, currency mapping rules) have diminishing returns.

## Decisions

### 1. Citation grounding for all inventory ops (P0)

Every `inventory_add` and `inventory_remove` must cite the specific narration sentence that justifies it. Python validates that the cited sentence exists verbatim in the narration text. No citation → no change.

This turns a prompt rule into a hard Python gate and eliminates hallucinated changes.

### 2. Remove speculative removal rule (P0)

The current prompt instructs: "even if the transaction failed, emit inventory_remove." This actively causes false positives. Replaced with: **only emit inventory_remove when the narration unambiguously confirms the item left the PC's possession.** If the transaction failed or is ambiguous, keep the item.

### 3. Scene-grounding for additions (P1)

Add a `notable_items: list[str]` field to `SceneExtractResult`. The durability gate in `delta_builder.py` already blocks brand-new items without loot gain context. Extend it: a new item can only be added if its ID or name appears in the scene's `notable_items`. This is a hard contractual constraint between streams — the scene extractor declares what exists in the scene, the state extractor can only operate on that set.

### 4. Possession statements (P2 — future)

The state extractor's output changes from mechanical deltas to narrative possession statements:

```
received_from, gave_to, consumed, used_but_retained
```

Python maps these to deltas. Separates narrative interpretation (LLM strength) from mechanical application (Python strength).

## Non-decisions

- No inventory-as-purely-mechanical redesign (too invasive)
- No authorial-intent-embedding from narrator (streaming complexity)
- No scene-boundary clearing of ephemeral items (separate feature)
