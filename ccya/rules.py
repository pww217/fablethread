"""Pure-Python rules engine. No LLM, no I/O.

Dice system: 1d12 + stat_mod + difficulty_mod + condition_mod.
  stat_mod   = stat_value - 2  (stat range 1–4 → mod -1..+2)
  diff_mod   = DIFFICULTY_MOD[difficulty]
  cond_mod   = sum of CONDITION_MODS[condition][skill] for active conditions

PbtA 7-band resolution (1d12):
  raw_die 1  → crit_fail  (always, ignores modifiers)
  raw_die 12 → crit_success (always, ignores modifiers)
  final_total ≤ 5 → fail
  final_total = 6 → setback
  final_total ≤ 8 → partial
  final_total ≥ 9 → success
"""

from __future__ import annotations

import random
from typing import Any

from ccya.models import RulesOutcome

DIFFICULTY_MOD: dict[str, int] = {
    "trivial": +2,
    "easy": +1,
    "normal": 0,
    "hard": -1,
    "extreme": -2,
}

CONDITION_MODS: dict[str, dict[str, int]] = {
    "wounded": {"strength": -1, "dexterity": -1},
    "exhausted": {"strength": -1, "dexterity": -1, "resolve": -1},
    "drugged": {"wits": -1, "resolve": -1},
    "frightened": {"resolve": -1, "charisma": -1},
    "shaken": {"resolve": -1},
    "bleeding": {"strength": -1},
}

GM_MOVES: dict[str, list[str]] = {
    "crit_fail": [
        "Something precious is lost, damaged, or turned against you.",
        "An enemy or hazard makes an immediate hard move.",
        "Gain a condition: wounded, shaken, or exhausted.",
    ],
    "fail": [
        "The attempt fails outright — what you tried to do does not happen.",
        "A complication arises and something gets measurably worse.",
        "You are put in a difficult spot with few good options.",
    ],
    "setback": [
        "You are set back — a resource is spent, time is lost, or a new problem appears.",
        "The situation worsens slightly; you are worse off than before you acted.",
        "A complication interrupts your plan and pushes you back.",
    ],
    "partial": [
        "You get what you wanted, but something is taken from you or goes wrong in the process.",
        "You succeed but at a cost — a resource spent, a wound taken, or a complication started.",
        "The outcome is positive but carries a real price.",
    ],
    "success": [
        "Clean success — you do what you intended.",
        "Note any minor consequence if the fiction demands it.",
    ],
    "crit_success": [
        "Best possible outcome — something unexpected goes in your favour.",
        "You succeed outstandingly; gain a small additional benefit.",
    ],
}

_VERB_CATEGORY: dict[str, str] = {
    "fight": "combat", "attack": "combat", "defend": "combat",
    "flee": "movement", "chase": "movement",
    "persuade": "social", "deceive": "social",
    "intimidate": "social", "negotiate": "social",
    "search": "exploration", "investigate": "exploration", "sneak": "exploration",
}

MOMENTUM_DELTA: dict[str, int] = {
    "crit_success": 2,
    "success": 1,
    "partial": 0,
    "setback": -1,
    "fail": -1,
    "crit_fail": -2,
}

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


def _verb_category(intent_verb: str | None) -> str:
    return _VERB_CATEGORY.get(intent_verb.lower() if intent_verb else "", "default")

VALID_SKILLS: frozenset[str] = frozenset(
    ["strength", "dexterity", "wits", "lore", "charisma", "resolve"]
)


def roll_1d12(rng: random.Random | None = None) -> int:
    r = rng or random
    return r.randint(1, 12)


def compute_band(final_total: int, raw_die: int) -> str:
    if final_total <= 1:
        return "crit_fail"
    if final_total >= 12:
        return "crit_success"
    if final_total <= 5:
        return "fail"
    if final_total == 6:
        return "setback"
    if final_total <= 8:
        return "partial"
    return "success"


def conditions_modifier(skill: str, conditions: list[Any]) -> int:
    total = 0
    for cond in conditions:
        if isinstance(cond, dict):
            key = str(cond.get("id") or cond.get("label") or "").lower()
        else:
            key = str(cond or "").lower()
        if not key:
            continue
        mods = CONDITION_MODS.get(key, {})
        total += mods.get(skill, 0)
    return total


def build_directive(band: str, intent_verb: str, skill: str, *, near_miss: bool = False) -> str:
    if band in ("setback", "partial"):
        cat = _verb_category(intent_verb)
        table = _DIRECTIVE_TABLE.get(band, {})
        verb = intent_verb or "action"
        directive = table.get(cat) or table.get("default")
        if directive:
            return f"The {verb} results in a {band}. {directive}"
    moves = GM_MOVES.get(band, GM_MOVES["success"])
    base = moves[0]
    verb = intent_verb or "action"
    if band == "crit_fail":
        return f"The {verb} fails catastrophically. {base}"
    if band == "fail":
        if near_miss:
            return f"The {verb} fails. {base} The roll was close — narrate a complication or setback that still allows the story to move forward, rather than a full dead-end punishment."
        return f"The {verb} fails. {base}"
    if band == "success":
        return f"The {verb} succeeds cleanly. {base}"
    if band == "crit_success":
        return f"The {verb} succeeds outstandingly. {base}"
    return base


def resolve_check(
    *,
    skill: str,
    difficulty: str,
    pc_stats: dict[str, int],
    pc_conditions: list[str],
    intent_verb: str = "",
    intent: str = "",
    rng: random.Random | None = None,
    difficulty_mods: dict[str, int] | None = None,
    near_miss_softening: bool = True,
) -> RulesOutcome:

    if skill not in VALID_SKILLS:
        raise ValueError(
            f"Unknown skill: {skill!r}. Must be one of {sorted(VALID_SKILLS)}"
        )
    mods = difficulty_mods or DIFFICULTY_MOD
    if difficulty not in mods:
        raise ValueError(
            f"Unknown difficulty: {difficulty!r}. Must be one of {sorted(mods)}"
        )

    stat_value = int(pc_stats.get(skill, 2))
    stat_mod = stat_value - 2
    diff_mod = mods[difficulty]
    cond_mod = conditions_modifier(skill, pc_conditions)

    raw_die = roll_1d12(rng)
    dice = [raw_die]
    raw_total = raw_die
    final_total = raw_total + stat_mod + diff_mod + cond_mod

    band = compute_band(final_total, raw_die)
    near_miss = near_miss_softening and band == "fail" and final_total >= 5
    directive = build_directive(band, intent_verb, skill, near_miss=near_miss)

    return RulesOutcome(
        rolled=True,
        skill=skill,
        stat_value=stat_value,
        difficulty=difficulty,
        stat_mod=stat_mod,
        diff_mod=diff_mod,
        cond_mod=cond_mod,
        dice=dice,
        raw_total=raw_total,
        final_total=final_total,
        band=band,
        directive=directive,
        intent_verb=intent_verb,
        intent=intent,
    )
