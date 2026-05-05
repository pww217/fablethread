# Plan: Intent Expansion (Extending the Rules Call)

## Context

The rules/intent call (`rules_system.j2` / `rules_user.j2`) already exists as Call 0 in the
turn loop. It currently outputs an `IntentEnvelope` with:
- `intent` — one-line summary
- `intent_verb` — action category
- `target` — who/what the action is directed at
- `stakes` — what's at risk
- `check` — skill check parameters

This plan extends that output to also produce **scope boundaries** for the extractor and
**ambiguity flags** for both the narrator and extractor. It does NOT create a new call —
it extends the existing one.

---

## Extended Output Schema

Add the following fields to the existing `IntentEnvelope` in `rules_system.j2`:

```json
{
  "intent": "...",
  "intent_verb": "...",
  "target": "...",
  "stakes": "...",
  "check": { ... },

  "active_domains": ["scene", "location", "conditions", "npcs"],
  "skip_domains": ["quests", "inventory", "facts"],

  "ambiguities": [
    {
      "description": "Player assumes the chest is unlocked — unverified against world state",
      "type": "precondition"
    }
  ],

  "genre_note": null
}
```

### Field specs

**`active_domains`** (array of strings, always present)
Domains from the taxonomy in `extractor-prompt-redesign.md` that *could plausibly change*
this turn given the player's intent. Conservative: if unsure, include.
`scene` and `location` should almost always be included.

**`skip_domains`** (array of strings, always present)
Domains with no plausible change path this turn.
Example: a pure combat turn skips `quests`, `inventory`, `facts` unless the narrative might
resolve a kill-target objective or drop loot.

**`ambiguities`** (array, may be empty)
Each entry has:
- `description`: plain English statement of what's uncertain
- `type`: one of `precondition` | `unclear_target` | `impossible` | `genre_break`

`impossible` = physically or narratively impossible given current state.
`genre_break` = action doesn't fit the current genre register (e.g. magic in a hard sci-fi pack).

**`genre_note`** (string or null)
Non-null only when the player's input signals a genre shift or tonal break from the pack's
established register. E.g.: `"Player invoked magic in a grounded noir setting — narrator
should resolve this as metaphor or reject it with in-world explanation."`

---

## Prompt Changes

### `rules_system.j2` additions

After the existing `## Output schema` section, append:

```
## Domain scoping rules
active_domains: list the state domains that could plausibly change this turn.
  - Always include: "scene"
  - Include "location" if movement is implied
  - Include "conditions" if harm, fear, or a buff/debuff is implied
  - Include "npcs" if NPC status, position, or attitude changes
  - Include "inventory" only if physical item acquisition or loss is implied
  - Include "quests" only if an objective could be completed, failed, or a new quest started
  - Include "facts" only if a durable world-truth is revealed or overturned
skip_domains: all domains not in active_domains.

## Ambiguity rules
Emit an ambiguities entry when:
  - The player's action assumes something that may not be true (precondition)
  - The target is ambiguous (multiple possible targets)
  - The action is physically impossible given current state
  - The action's tone breaks genre register

## Genre signal rules
Emit genre_note (non-null) only when the action is meaningfully inconsistent with the pack's
genre. Do not flag genre note for minor tonal variation — only for actual register breaks
(e.g. casting spells in a grounded thriller, making a phone call in a medieval setting).
```

### `rules_user.j2`

No structural change needed. The existing context (PC stats, conditions, present NPCs, recent
turns, location) is sufficient for domain scoping. The model can infer from "player is in
combat" that quests are unlikely to change.

---

## Wiring to Extractor

In `engine.py`, after the rules call returns, extract `active_domains` and `skip_domains`
from the `IntentEnvelope` and pass them into the extractor template context:

```python
intent_envelope = await run_rules_call(user_input, state)

active_domains = intent_envelope.get("active_domains", ALL_DOMAINS)
skip_domains = intent_envelope.get("skip_domains", [])

extract_context = build_extract_context(
    state,
    active_domains=active_domains,
    skip_domains=skip_domains,
    ...
)
```

Define `ALL_DOMAINS` as the full domain list as a fallback constant (graceful degradation if
the rules call doesn't return domain fields, e.g. during the transition period).

---

## Wiring to Narrator

Pass `ambiguities` into the narrate context so the narrator can resolve them against world
state rather than ignoring them:

In `narrate_system.j2` or as an injected section in the narrate user message:

```
{% if ambiguities %}
## Precondition notes (resolve against world state before narrating)
{% for a in ambiguities %}
- {{ a.description }}{% endfor %}
{% endif %}
```

If a precondition is false (e.g. the chest IS locked), the narrator should handle it in prose
rather than letting the extractor silently apply a wrong state change.

---

## Wiring to Extract User Prompt

In `extract_user.j2`, add at the top (before the rules outcome block):

```jinja
## This turn's scope
Active domains: {{ active_domains | join(", ") }}
Skip domains (omit entirely — do not reason about): {{ skip_domains | join(", ") }}

{% if precondition_failed %}
## Precondition note
{{ precondition_failed }}
The extractor should reflect this in state — do not apply the action's intended outcome.
{% endif %}
```

---

## Rollout Order

1. Add `active_domains` / `skip_domains` to `rules_system.j2` output schema
2. Parse new fields in engine after the rules call
3. Pass domains into extract template context + add SKIP DOMAINS block to `extract_user.j2`
4. Add `ambiguities` + `genre_note` to `rules_system.j2`
5. Wire ambiguities into narrate context
6. Wire `precondition_failed` into extract context

Steps 1–3 are independent of 4–6 and should ship first.

---

## Notes on Existing Implementation

The current `rules_system.j2` already does compound action handling, anti-declare-outcome
rules, and stakes classification — this is a solid foundation. The intent/scope extensions
are additive: they expand the output schema without changing the existing decision logic.

The `intent` and `intent_verb` fields already flowing into `extract_user.j2` as
`rules_outcome.intent_verb` give the extractor partial scope signal already. The domain
lists make that signal explicit and machine-readable.
