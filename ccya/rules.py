"""Pure-Python rules engine. No LLM, no I/O.

Dice system: 2d6 + stat_mod + difficulty_mod + condition_mod.
  stat_mod   = stat_value - 2  (stat range 1–4 → mod -1..+2)
  diff_mod   = DIFFICULTY_MOD[difficulty]
  cond_mod   = sum of CONDITION_MODS[condition][skill] for active conditions

PbtA 7-band resolution:
  raw_sum 2  → crit_fail    (always, ignores modifiers)
  ≤ 6        → fail
  7          → setback      (minor setback or complication)
  8          → mixed        (mostly neutral, slight complication)
  9          → boon         (minor advantage, no full success)
  10–11      → success
  raw_sum 12 → crit_success (always, ignores modifiers)
"""

from __future__ import annotations

import random

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

# GM move suggestions per band — first entry is the binding directive.
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
    "mixed": [
        "Mostly neutral, but a small complication lingers — a minor cost or inconvenience.",
        "The outcome is even, with a slight edge toward complication.",
        "Nothing major changes, but a minor annoyance arises.",
    ],
    "boon": [
        "You gain a small advantage — a useful detail, a moment of respite, or a minor resource.",
        "A minor boon: something works in your favour, though not enough to count as success.",
        "A small benefit accrues, but the main goal remains unfulfilled.",
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

VALID_SKILLS: frozenset[str] = frozenset(
    ["strength", "dexterity", "wits", "lore", "charisma", "resolve"]
)


def roll_2d6(rng: random.Random | None = None) -> tuple[int, int]:
    r = rng or random
    return (r.randint(1, 6), r.randint(1, 6))


def compute_band(final_total: int, dice: tuple[int, int]) -> str:
    """Return the PbtA band. Crits are triggered by raw dice sum, not final total."""
    raw_sum = dice[0] + dice[1]
    if raw_sum == 2:
        return "crit_fail"
    if raw_sum == 12:
        return "crit_success"
    if final_total <= 6:
        return "fail"
    if final_total == 7:
        return "setback"
    if final_total == 8:
        return "mixed"
    if final_total == 9:
        return "boon"
    if final_total <= 11:
        return "success"
    return "crit_success"


def conditions_modifier(skill: str, conditions: list) -> int:
    """Sum all condition penalties that apply to the given skill.

    Accepts either plain strings (legacy) or structured Condition dicts
    ({"id": ..., "label": ..., ...}). The id (or string) is matched against
    CONDITION_MODS case-insensitively.
    """
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


def build_directive(band: str, intent_verb: str, skill: str) -> str:
    """Return a binding one-sentence directive for the narrator based on the roll outcome."""
    moves = GM_MOVES.get(band, GM_MOVES["success"])
    base = moves[0]
    verb = intent_verb or "action"
    if band == "crit_fail":
        return f"The {verb} fails catastrophically. {base}"
    if band == "fail":
        return f"The {verb} fails. {base}"
    if band == "setback":
        return f"The {verb} results in a minor setback. {base}"
    if band == "mixed":
        return f"The {verb} is mostly neutral with a slight complication. {base}"
    if band == "boon":
        return f"The {verb} grants a minor advantage. {base}"
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
) -> "RulesOutcome":
    """Roll 2d6 and return a fully-populated RulesOutcome.

    Raises ValueError for unknown skill or difficulty (programming errors, not player input).
    Pass a seeded ``rng`` for deterministic results in tests.
    """
    from ccya.models import RulesOutcome

    if skill not in VALID_SKILLS:
        raise ValueError(
            f"Unknown skill: {skill!r}. Must be one of {sorted(VALID_SKILLS)}"
        )
    if difficulty not in DIFFICULTY_MOD:
        raise ValueError(
            f"Unknown difficulty: {difficulty!r}. Must be one of {sorted(DIFFICULTY_MOD)}"
        )

    stat_value = int(pc_stats.get(skill, 2))
    stat_mod = stat_value - 2
    diff_mod = DIFFICULTY_MOD[difficulty]
    cond_mod = conditions_modifier(skill, pc_conditions)

    dice = roll_2d6(rng)
    raw_total = dice[0] + dice[1]
    final_total = raw_total + stat_mod + diff_mod + cond_mod

    band = compute_band(final_total, dice)
    directive = build_directive(band, intent_verb, skill)

    return RulesOutcome(
        rolled=True,
        skill=skill,
        stat_value=stat_value,
        difficulty=difficulty,
        stat_mod=stat_mod,
        diff_mod=diff_mod,
        cond_mod=cond_mod,
        dice=list(dice),
        raw_total=raw_total,
        final_total=final_total,
        band=band,
        directive=directive,
        intent_verb=intent_verb,
        intent=intent,
    )
