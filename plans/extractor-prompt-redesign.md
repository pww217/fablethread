# Plan: Extractor Prompt Redesign

## Problem

The extractor currently receives a large flat prompt with all game state domains present every
turn, and its output schema puts enumerated delta fields first. Two issues:

1. **Attention competition** — quest, inventory, NPC, location, and facts fields all compete for
   the model's focus regardless of whether any of them could have changed this turn.
2. **Premature commitment** — the model generates delta field values before it has "reasoned
   through" what happened. Because generation is left-to-right, an early `inventory_add` value
   locks in before the model has processed the full narrative implications.

---

## Change 1: Reasoning Field First in Output Schema

### What to do

Add a `turn_notes` string field as the **first key** in `state_delta`. The model writes a brief
internal scratch note before emitting any enumerated delta fields.

### Why it works

LLM token generation is strictly left-to-right. A free-text field placed first functions as
forced chain-of-thought: the model "talks itself through" what changed before committing to
specific item IDs, quest indexes, or condition strings. This is the mechanism — not the field
name.

### Implementation

In `extract_system.j2`, change the top of the output schema block from:

```
"state_delta": {
  "inventory_add": [...],
  ...
}
```

To:

```
"state_delta": {
  "turn_notes": "string — brief scratch reasoning: what changed and why (1-3 sentences, stripped before storing)",
  "inventory_add": [...],
  ...
}
```

In `state.py` (or wherever `state_delta` is applied), strip `turn_notes` before persisting —
it is for generation quality only, never stored.

Optionally surface `turn_notes` in the UI diagnostics/event log for debugging.

---

## Change 2: SKIP DOMAINS Directive

### What to do

Add a `## Skip domains` section to the **extract user prompt** (i.e., in `extract_user.j2`)
that is dynamically populated from the rules/intent output (see `plans/intent-expansion.md`).

### Structure

At the top of the extract user message (before current state), inject:

```
## This turn
Active domains (extract changes for these only): {{ active_domains | join(", ") }}
Skip domains (emit null/empty for these — do not reason about them): {{ skip_domains | join(", ") }}
```

And add a matching directive to `extract_system.j2`:

```
## Domain scoping
You will receive ACTIVE DOMAINS and SKIP DOMAINS each turn.
- For SKIP DOMAINS: emit null or omit entirely. Do not infer changes even if the narrative implies them.
- This is a hard rule. A combat turn does not update quest objectives unless quest_updates is in ACTIVE DOMAINS.
```

### Domain taxonomy

The following domains map to `state_delta` keys:

| Domain name      | Keys covered                                                      |
|------------------|-------------------------------------------------------------------|
| `inventory`      | `inventory_add`, `inventory_remove`, `inventory_update`           |
| `quests`         | `quest_updates`                                                   |
| `npcs`           | `present_npcs`, `compendium_npc_update`                           |
| `location`       | `location_change`, `location_description`                         |
| `conditions`     | `pc_condition_add`, `pc_condition_remove`                         |
| `facts`          | `established_facts_add`, `established_facts_update`, `established_facts_remove` |
| `scene`          | `scene_tags`, `scene_tagline`                                     |

`scene` and `location_description` should almost always be active — they change every turn.
`quests` and `inventory` are the high-false-positive domains and the most valuable to skip.

### Fallback

If the intent expander is unavailable or errors, default to all domains active (current behavior).

---

## Change 3: Active-Domain State Slicing

### What to do

Only include the state sections relevant to active domains in the extract user message.
If `quests` is in SKIP DOMAINS, the full active quest list is not sent at all.

### Implementation

In `engine.py` (or wherever `extract_user.j2` is rendered), wrap each state section in a
conditional check against `active_domains`:

```python
context = {
    ...
    "include_inventory": "inventory" in active_domains,
    "include_quests": "quests" in active_domains,
    "include_facts": "facts" in active_domains,
    # etc.
}
```

In `extract_user.j2`:

```jinja
{% if include_quests %}
### Active quests
...
{% endif %}
```

### Token savings estimate

On a pure combat turn with no quest or fact implications:
- Skipping quests: ~100–300 tokens saved depending on quest list length
- Skipping facts: ~50–150 tokens
- Total per-turn savings on inactive domains: potentially 20–40% of current input token count

---

## Change 4: Explicit "Changes Only" + _failed Pattern

### What to do

Strengthen the existing consolidation rule with two additions:

1. Add to `extract_system.j2` system prompt:
   ```
   Omit any field whose value is identical to what is already shown in Current State.
   Only emit what changed this turn.
   ```
   (The existing schema comment says this but it should be a top-level rule, not buried.)

2. Add a `precondition_failed` optional field to `state_delta`:
   ```json
   "precondition_failed": "string | null — if the player's action could not execute because
   a required precondition was not met (e.g. door was locked, target was already dead),
   describe briefly. Omit if action proceeded normally."
   ```

This surfaces silent failures that currently result in the extractor guessing or hallucinating
a partial state change.

---

## Schema Field Description Quality Pass

The following fields in `extract_system.j2` should have their descriptions tightened:

| Field | Current issue | Suggested tightening |
|-------|--------------|----------------------|
| `quest_updates` | Implicit about turn scope | Add: "Only include quests whose status or objectives changed THIS turn." |
| `inventory_add` | Cap is stated but not the scope rule | Add: "Only items physically acquired in this turn's narrative." |
| `established_facts_add` | Already good | — |
| `pc_condition_add` | Good | — |
| `present_npcs` | Good | — |

---

## Rollout Order

1. **Turn_notes field** (Change 1) — edit `extract_system.j2` schema + strip in `state.py`. No other dependencies.
2. **Explicit changes-only + precondition_failed** (Change 4) — edit `extract_system.j2`. No dependencies.
3. **Schema description pass** — edit `extract_system.j2`. No dependencies.
4. **SKIP DOMAINS + state slicing** (Changes 2 & 3) — requires intent expansion (see `plans/intent-expansion.md`) to supply `active_domains`/`skip_domains`. Implement intent expansion first, then wire output here.
