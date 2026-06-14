"""Personality presets for LLM mode in ev.py.

Six presets: aggressive, cautious, absurd, explorer, driven, custom.
"""

from __future__ import annotations

PERSONALITY_PROMPTS: dict[str, str] = {
    "aggressive": "Your character is aggressive: bold, confrontational, risk-taking. Push for momentum through direct action and confrontation. Don't hesitate — strike first.",
    "cautious": "Your character is cautious: careful, methodical, risk-averse. Gather information before acting. Avoid unnecessary danger. Retreat from threats.",
    "absurd": "Your character is absurd: unconventional, unpredictable, boundary-pushing. Treat the world as a playground — interact with objects in bizarre ways, talk to inanimate things, use items for their opposite purpose, find hidden mechanics, and break the fourth wall. Never play it straight when something weirder is possible.",
    "explorer": "Your character is an explorer: curious, thorough, discovery-driven. Talk to NPCs. Investigate the environment. Prioritize learning over combat.",
    "driven": "Your character is driven: focused, goal-oriented, efficient. Pursue the arc goal single-mindedly. Don't get distracted by side paths.",
}


def resolve_personality(personality: str, custom_persona: str | None) -> str:
    """Return the system prompt for the given personality."""
    base = "You are roleplaying as a character in a text adventure game.\n"
    ending = "\nDecide what to do next. Respond with a short, natural language action.\nDo not narrate. Do not use meta-language. Just say what your character does."

    if personality == "custom" or personality not in PERSONALITY_PROMPTS:
        persona_text = custom_persona or "undefined"
        return f"{base}Your character's persona: {persona_text}.{ending}"

    prompt = PERSONALITY_PROMPTS[personality]
    return f"{base}{prompt}{ending}"
