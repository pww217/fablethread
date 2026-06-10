"""NPC personality archetype registry and assignment."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class NpcPersonality:
    id: str
    label: str
    traits: tuple[str, ...]  # 2-4 short descriptors surfaced in narrator context
    speech_hint: str          # one-line style note; e.g. "clipped, transactional"
    motivation_keywords: tuple[str, ...] = field(default_factory=tuple)
    fear_keywords: tuple[str, ...] = field(default_factory=tuple)


ARCHETYPES: dict[str, NpcPersonality] = {
    a.id: a for a in [
        NpcPersonality(
            id="cold_pragmatist",
            label="Cold Pragmatist",
            traits=("calculating", "direct", "emotionally distant"),
            speech_hint="terse and transactional; no pleasantries",
            motivation_keywords=("power", "control", "order", "efficiency", "profit"),
            fear_keywords=("chaos", "weakness", "exposure", "loss of control"),
        ),
        NpcPersonality(
            id="desperate_idealist",
            label="Desperate Idealist",
            traits=("principled", "anxious", "self-sacrificing"),
            speech_hint="earnest and sometimes rambling; conviction bleeds through hesitation",
            motivation_keywords=("justice", "protect", "truth", "people", "belief", "cause"),
            fear_keywords=("betrayal", "failure", "complicity", "compromise"),
        ),
        NpcPersonality(
            id="wary_opportunist",
            label="Wary Opportunist",
            traits=("adaptive", "self-interested", "quick to read angles"),
            speech_hint="friendly surface, careful eyes; always gauging what this costs them",
            motivation_keywords=("survival", "gain", "advantage", "escape", "freedom"),
            fear_keywords=("trap", "debt", "loyalty", "obligation", "cornered"),
        ),
        NpcPersonality(
            id="resigned_functionary",
            label="Resigned Functionary",
            traits=("bureaucratic", "weary", "procedurally polite"),
            speech_hint="flat and slightly apologetic; follows rules because fighting them costs too much",
            motivation_keywords=("duty", "routine", "order", "stability", "family"),
            fear_keywords=("punishment", "scrutiny", "responsibility", "change"),
        ),
        NpcPersonality(
            id="volatile_loyalist",
            label="Volatile Loyalist",
            traits=("fiercely loyal", "short-fused", "protective"),
            speech_hint="blunt and emotional; shifts fast between warmth and aggression depending on perceived threat to what they value",
            motivation_keywords=("loyalty", "family", "protect", "honour", "revenge"),
            fear_keywords=("abandonment", "betrayal", "helplessness", "loss"),
        ),
        NpcPersonality(
            id="charming_manipulator",
            label="Charming Manipulator",
            traits=("persuasive", "socially fluid", "rarely direct"),
            speech_hint="warm and engaging; steers conversations without appearing to; says little of substance",
            motivation_keywords=("influence", "control", "reputation", "leverage", "network"),
            fear_keywords=("exposure", "loss of influence", "transparency", "irrelevance"),
        ),
        NpcPersonality(
            id="blunt_survivor",
            label="Blunt Survivor",
            traits=("unsentimental", "pragmatic", "darkly humorous"),
            speech_hint="dry, economical; has seen enough to drop illusions but not quite enough to stop trying",
            motivation_keywords=("survival", "endure", "protect", "independence"),
            fear_keywords=("weakness", "dependence", "betrayal", "hope"),
        ),
        NpcPersonality(
            id="true_believer",
            label="True Believer",
            traits=("zealous", "certain", "morally inflexible"),
            speech_hint="declarative and dense with conviction; treats doubt as an enemy",
            motivation_keywords=("faith", "mission", "purpose", "god", "ideology", "order"),
            fear_keywords=("doubt", "apostasy", "corruption", "failure of purpose"),
        ),
        NpcPersonality(
            id="detached_observer",
            label="Detached Observer",
            traits=("analytical", "quiet", "observant"),
            speech_hint="measured and questioning; prefers to draw others out rather than reveal themselves",
            motivation_keywords=("understand", "knowledge", "truth", "information", "clarity", "insight"),
            fear_keywords=("manipulation", "being used", "blindness", "misinformation", "control"),
        ),
        NpcPersonality(
            id="conflict_avoidant",
            label="Conflict-Avoidant",
            traits=("yielding", "nervous", "self-effacing"),
            speech_hint="hedging and apologetic; trails off or backtracks when pressed; speaks in qualifiers",
            motivation_keywords=("peace", "safety", "quiet", "normalcy", "blend in", "get by"),
            fear_keywords=("confrontation", "attention", "violence", "escalation", "being targeted"),
        ),
        NpcPersonality(
            id="ambitious_climber",
            label="Ambitious Climber",
            traits=("patient", "strategic", "calculating"),
            speech_hint="diplomatic and forward-looking; frames everything as an investment or opportunity",
            motivation_keywords=("advancement", "position", "status", "leverage", "future", "rise"),
            fear_keywords=("stagnation", "being passed over", "irrelevance", "dead end", "humiliation"),
        ),
        NpcPersonality(
            id="broken_defeated",
            label="Broken/Defeated",
            traits=("worn", "habit-driven", "darkly resigned"),
            speech_hint="fragmented and sparse; speaks in dark humor or silence; moves on autopilot",
            motivation_keywords=("routine", "habit", "survive", "endure", "forget", "numb"),
            fear_keywords=("meaning", "responsibility", "hope", "change", "being needed"),
        ),
    ]
}

_DEFAULT_ID = "wary_opportunist"


def _score_archetype(
    archetype: NpcPersonality,
    motivation: str,
    fear: str,
) -> int:
    """Return a keyword match score for an archetype against motivation+fear text."""
    text = (motivation + " " + fear).lower()
    score = 0
    for kw in archetype.motivation_keywords:
        if kw in text:
            score += 2
    for kw in archetype.fear_keywords:
        if kw in text:
            score += 1
    return score


def assign_personality(
    motivation: str | None,
    fear: str | None,
    npc_id: str = "",
) -> NpcPersonality:
    """Return the most contextually coherent personality archetype for an NPC.

    Scores each archetype against the NPC's motivation and fear text using
    keyword matching. Ties are broken by archetype registry insertion order.
    Falls back to ``wary_opportunist`` if both fields are empty or all scores are zero.

    Args:
        motivation: NPC motivation string (may be None).
        fear: NPC fear string (may be None).
        npc_id: Used only for structured logging.

    Returns:
        The best-scoring NpcPersonality instance.
    """
    if not motivation and not fear:
        _log.debug(
            "assign_personality npc=%s no_mf_fields fallback=%s",
            npc_id, _DEFAULT_ID,
        )
        return ARCHETYPES[_DEFAULT_ID]

    scored = [
        (_score_archetype(arch, motivation or "", fear or ""), arch)
        for arch in ARCHETYPES.values()
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_arch = scored[0]
    _log.debug(
        "assign_personality npc=%s best=%s score=%d",
        npc_id, best_arch.id, best_score,
    )
    return best_arch


def validate_and_resolve(personality_id: str | None) -> NpcPersonality | None:
    """Validate a personality archetype id against the registry.

    Returns the resolved NpcPersonality if valid and non-None, otherwise logs
    a warning (for invalid ids) or returns None (for missing). Callers should
    fall back to ARCHETYPES[_DEFAULT_ID] when they receive None for an invalid id.

    Args:
        personality_id: An archetype id string from state or LLM output.

    Returns:
        NpcPersonality if valid, None otherwise.
    """
    if not personality_id:
        return None
    arch = ARCHETYPES.get(personality_id)
    if arch is None:
        _log.warning(
            "personality unknown id=%s for npc; falling back to %s",
            personality_id, _DEFAULT_ID,
        )
        return None
    return arch
