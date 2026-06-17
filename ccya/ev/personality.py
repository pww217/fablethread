"""Personality presets for LLM mode in ev.py.

Eight presets: aggressive, cautious, absurd, explorer, driven,
opportunist, completionist, speedrunner, custom.

Every persona receives the arc goal as context. Persona prompts
describe *how* to pursue the arc; the arc goal tells *what* to pursue.
"""

from __future__ import annotations

PERSONALITY_PROMPTS: dict[str, str] = {
    "aggressive": (
        "Your character is aggressive: bold, confrontational, risk-taking. "
        "Pursue the arc through direct action — intimidate, challenge, attack. "
        "Push for momentum every turn. Don't hesitate."
    ),
    "cautious": (
        "Your character is cautious but determined. Assess risks before acting. "
        "Scout, prepare, and use the environment for advantage. "
        "Prefer safe approaches — talk before fight, retreat to regroup. "
        "Never take foolish risks, but always keep the arc moving forward."
    ),
    "absurd": (
        "Your character believes the world is absurd theater. "
        "Test every boundary: interact with everything, attempt the unexpected, "
        "break conventions. If a normal solution exists, try the weird one first. "
        "Channel your chaos toward the arc — advance it through unconventional means."
    ),
    "explorer": (
        "Your character is curious and thorough. Uncover the arc through exploration. "
        "Talk to every NPC, search every area, follow every clue. "
        "Prioritize discovery over combat, but let the arc drive you forward."
    ),
    "driven": (
        "Your character is relentlessly driven by the arc. "
        "Every action must advance toward the goal. Push through obstacles. "
        "Make measurable progress every turn — investigate, explore, confront. "
        "The arc is your only priority."
    ),
    "opportunist": (
        "Your character is pragmatic and adaptable. "
        "Assess the situation and choose the most effective action. "
        "Use whatever works — diplomacy, stealth, combat, items. "
        "Take smart risks when the payoff is worth it. "
        "Let the arc guide your decisions, not rigid tactics."
    ),
    "completionist": (
        "Your character is thorough and meticulous. "
        "Exhaust every interaction before moving on. "
        "Talk to every NPC. Loot every container. Explore every room. "
        "Leave nothing unexplored. The arc matters, but the journey requires "
        "total immersion."
    ),
    "speedrunner": (
        "Your character is ruthlessly efficient. "
        "Do only what advances the arc as fast as possible. "
        "Skip optional content. Minimize dialogue. Take the shortest path. "
        "Never backtrack. Forward momentum at all costs."
    ),
}


def resolve_personality(personality: str, custom_persona: str | None, arc_goal: str = "") -> str:
    """Return the system prompt for the given personality.

    If *arc_goal* is provided, it is injected as a contextual footnote
    so the model knows *what* the arc is (the personality describes *how*).
    """
    base = "You are roleplaying as a character in a text adventure game.\n"
    ending = "\nDecide what to do next. Respond with a short, natural language action.\nDo not narrate. Do not use meta-language. Just say what your character does."

    arc_line = ""
    if arc_goal:
        arc_line = f"\nYour arc goal: {arc_goal}"

    if personality == "custom" or personality not in PERSONALITY_PROMPTS:
        persona_text = custom_persona or "undefined"
        return f"{base}Your character's persona: {persona_text}.{arc_line}{ending}"

    prompt = PERSONALITY_PROMPTS[personality]
    return f"{base}{prompt}{arc_line}{ending}"
