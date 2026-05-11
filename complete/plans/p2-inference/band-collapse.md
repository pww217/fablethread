# Plan: Band Collapse + Verb-Differentiated Directives

## Problem

The current 7-band resolution system in `rules.py` has two middle bands — `mixed` and
`boon` — that produce weak, indistinct narrative outcomes:

- `mixed`: "Mostly neutral, slight complication"
- `boon`: "Minor advantage, not quite success"

These bands are nearly impossible to distinguish in practice. PbtA's power comes from the
crispness of its core split: **7- (fail / partial) vs. 10+ (success)**. The more you
subdivide the middle, the more you dilute that tension.

Additionally, `build_directive()` generates the same directive text regardless of *what the
player was trying to do*. A `setback` on a fight and a `setback` on a negotiation currently
produce nearly identical narrator instructions.

---

## Scope

All changes are in **`ccya/rules.py`** only — `GM_MOVES` dict and `build_directive()`.
No changes to `models.py`, templates, or `server.py`.

---

## 1. Collapse to 5 bands

Remove `mixed` and `boon`. Merge into a new `partial` band:

| Old bands | New band | Final total |
|---|---|---|
| `crit_fail` (raw 2) | `crit_fail` | raw=2 |
| `fail` | `fail` | ≤6 |
| `setback` | `setback` | 7 |
| `mixed` + `boon` | `partial` | 8–9 |
| `success` | `success` | 10–11 |
| `crit_success` (raw 12) | `crit_success` | raw=12 |

The `partial` band directive: **"You get what you wanted, but something is taken from you
or goes wrong in the process."** Forces the narrator to commit: the player's goal happens,
but with a real cost.

**Changes in `rules.py`:**
- Remove `mixed` and `boon` from `GM_MOVES`
- Add `partial` to `GM_MOVES`
- Update `compute_band()`: finals 8–9 → `"partial"` instead of `"mixed"`/`"boon"`
- Update `build_directive()`: add `partial` case

---

## 2. Verb-differentiated directives in `build_directive()`

The `intent_verb` field from `IntentEnvelope` is already passed into `build_directive()`
but only prepended as flavor. It should determine the *content* of the directive for
`setback` and `partial` bands.

### Intent verb taxonomy

```python
_VERB_CATEGORY = {
    "fight": "combat", "attack": "combat", "defend": "combat",
    "flee": "movement", "chase": "movement",
    "persuade": "social", "deceive": "social",
    "intimidate": "social", "negotiate": "social",
    "search": "exploration", "investigate": "exploration", "sneak": "exploration",
    "act": "default",
}
```

### Directive table (setback + partial; other bands unchanged)

| Band | combat | social | exploration | movement | default |
|---|---|---|---|---|---|
| `setback` | You land the blow but take a wound or lose ground. | They're listening, but now they want something in return. | You find a lead, but you've made noise — someone knows you're looking. | You move, but something is left behind or someone follows. | You are set back — a resource is spent, time is lost, or a new problem appears. |
| `partial` | You succeed but at a cost — a resource spent, a wound taken, or a complication started. | You get what you asked for, but they now hold leverage over you. | You find it, but you've triggered something: a trap, a witness, a timer. | You reach your destination, but something went wrong on the way. | You get what you wanted, but something is taken from you or goes wrong in the process. |

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

- Existing saves with `mixed`/`boon` in event logs are fine — display only, not
  re-processed.
- The `band` field in `RulesOutcome` stays a `str` (not an enum) for forward compatibility.
- Add tests in `tests/` for `compute_band()` and `build_directive()` covering all new
  bands and verb categories.
- `momentum-track.md` depends on this — use the 5-band delta table after this lands.
