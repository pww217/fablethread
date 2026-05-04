# Plan: Band Collapse + Verb-Differentiated Directives

## Problem

The current 7-band resolution system in `rules.py` has two middle bands — `mixed` and `boon` — that produce weak, indistinct narrative outcomes:

- `mixed`: "Mostly neutral, slight complication"
- `boon`: "Minor advantage, not quite success"

These bands are nearly impossible to distinguish in practice. PbtA's power comes from the crispness of its core split: **7- (fail / partial) vs. 10+ (success)**. The more you subdivide the middle, the more you dilute that tension — the LLM produces wishy-washy hedging prose instead of committing to a clear outcome.

Additionally, `build_directive()` generates the same directive text regardless of *what the player was trying to do*. A `setback` on a fight and a `setback` on a negotiation currently produce nearly identical instructions to the narrator, which leads to generic narration.

## Proposed Changes

### 1. Collapse to 5 bands

Remove `mixed` and `boon`. Merge them into a new `partial` band defined as "success at a cost":

| Old bands | New band | Final total |
|---|---|---|
| `crit_fail` (raw 2) | `crit_fail` | raw=2 |
| `fail` | `fail` | ≤6 |
| `setback` | `setback` | 7 |
| `mixed` + `boon` | `partial` | 8–9 |
| `success` | `success` | 10–11 |
| `crit_success` (raw 12) | `crit_success` | raw=12 |

The `partial` band directive: **"You get what you wanted, but something is taken from you or goes wrong in the process."** This forces the narrator to commit: the player's goal happens, but with a real cost.

#### Changes required

**`ccya/rules.py`**
- Remove `mixed` and `boon` from `GM_MOVES`
- Add `partial` to `GM_MOVES`
- Update `compute_band()`: finals 8–9 → `"partial"` instead of `"mixed"`/`"boon"`
- Update `build_directive()`: add `partial` case

**`ccya/models.py`**
- Update any `Literal` band enums or validators to include `partial` and remove `mixed`/`boon`

**Templates** (`ccya/prompts/`)
- Any template that renders band names or GM move suggestions needs updating
- Search for `mixed`, `boon` in all `.j2` files

**`ccya/server.py`**
- Any band-to-UI color/label mapping in the frontend

---

### 2. Verb-differentiated directives in `build_directive()`

The `intent_verb` field from `IntentEnvelope` is already passed into `build_directive()` but is only prepended as flavor. It should determine the *content* of the directive.

#### Intent verb taxonomy

Group known verbs into categories:

```python
_VERB_CATEGORY = {
    # Combat / physical force
    "fight": "combat",
    "attack": "combat",
    "defend": "combat",
    "flee": "movement",
    "chase": "movement",
    # Social
    "persuade": "social",
    "deceive": "social",
    "intimidate": "social",
    "negotiate": "social",
    # Exploration / investigation
    "search": "exploration",
    "investigate": "exploration",
    "sneak": "exploration",
    # Default
    "act": "default",
}
```

#### Directive tables per band per category

For each `(band, category)` pair, define a specific directive. Examples:

| Band | combat | social | exploration |
|---|---|---|---|
| `setback` | You land the blow but take a wound or lose ground. | They're listening, but now they want something in return. | You find a lead, but you've made noise — someone knows you're looking. |
| `partial` | You succeed but at a cost — a resource spent, a wound taken, or a complication set in motion. | You get what you asked for, but they now hold leverage over you. | You find it, but you've triggered something: a trap, a witness, a timer. |
| `fail` | The attack fails and you are now in a worse position. | They refuse and your relationship with them worsens. | You find nothing, or what you find is wrong — and time has passed. |

#### Implementation

```python
_DIRECTIVE_TABLE: dict[str, dict[str, str]] = {
    "setback": {
        "combat":      "You land the blow but take a wound or lose ground.",
        "social":      "They're listening, but now they want something in return.",
        "exploration": "You find a lead, but you've made noise — someone knows you're looking.",
        "movement":    "You move, but something is left behind or someone follows.",
        "default":     "You are set back — a resource is spent, time is lost, or a new problem appears.",
    },
    "partial": {
        "combat":      "You succeed but at a cost — a resource spent, a wound taken, or a complication started.",
        "social":      "You get what you asked for, but they now hold leverage over you.",
        "exploration": "You find it, but you've triggered something: a trap, a witness, a timer.",
        "movement":    "You reach your destination, but something went wrong on the way.",
        "default":     "You get what you wanted, but something is taken from you or goes wrong in the process.",
    },
    # ... fail, success, crit_fail, crit_success
}

def _verb_category(intent_verb: str) -> str:
    return _VERB_CATEGORY.get(intent_verb.lower() if intent_verb else "", "default")

def build_directive(band: str, intent_verb: str, skill: str) -> str:
    cat = _verb_category(intent_verb)
    table = _DIRECTIVE_TABLE.get(band, {})
    return table.get(cat) or table.get("default") or GM_MOVES.get(band, [""])[0]
```

---

## Migration Notes

- Existing saves with `mixed`/`boon` in their event logs are fine — those fields are only read for display, not re-processed.
- The `band` field in `RulesOutcome` should remain a `str` (not an enum) for forward compatibility.
- Add tests in `tests/` for `compute_band()` and `build_directive()` covering all new bands and verb categories.
