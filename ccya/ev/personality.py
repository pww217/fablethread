"""Personality presets for LLM mode in ev.py.

Eight presets: aggressive, cautious, absurd, explorer, driven,
opportunist, completionist, speedrunner, custom.

Every persona receives the arc goal as context. Persona prompts
describe *how* to pursue the arc; the arc goal tells *what* to pursue.
"""

from __future__ import annotations

PERSONALITY_PROMPTS: dict[str, str] = {
    "aggressive": (
        "Your character is bold and direct. Take initiative on every turn — "
        "confront threats head-on, seize opportunities, push the situation forward. "
        "When in doubt, act decisively. Create momentum through bold moves, "
        "even if they carry risk."
    ),
    "cautious": (
        "Your character is careful but proactive. Gather information through "
        "active scouting, secure your position before advancing, and use terrain "
        "to your advantage. Choose measured actions over reckless ones — but "
        "always move the situation forward. Never stand still."
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
        "Your character is single-minded about the goal. Every turn must produce "
        "concrete progress — question witnesses, follow leads, confront suspects. "
        "Don't wait for opportunities; create them. The arc is your only priority."
    ),
    "opportunist": (
        "Your character is pragmatic and adaptable. Read the situation and choose "
        "the most effective approach — diplomacy, stealth, combat, or items. "
        "Take calculated risks when the payoff justifies it. Let the arc guide "
        "your decisions, not rigid tactics."
    ),
    "completionist": (
        "Your character is thorough and engaged. Interact with everything in the "
        "environment — talk to every NPC, examine every object, explore every area. "
        "The arc matters, but so does the journey. Leave no corner unturned."
    ),
    "speedrunner": (
        "Your character is focused and efficient. Move directly toward the goal "
        "on every turn. Skip unnecessary detours and keep dialogue purposeful. "
        "Take the most direct path available. Every action should advance the situation."
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
