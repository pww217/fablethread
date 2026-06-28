"""Extraction context: this-turn derived state from scene + state streams."""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Any

from ccya.models import SceneExtractResult, StateDelta, StateExtractResult

_log = logging.getLogger(__name__)


@dataclass
class _ExtractionContext:
    """Carries this-turn deltas from scene + state streams into the storytell stream.

    All fields are derived from extract results, NOT from ``state``.  They
    represent what happened *this turn* as determined by the prior two streams.
    """
    comp_this_turn: dict[str, Any] = field(default_factory=dict)
    """Reference to post-delta compendium.npcs dict (not a copy)."""
    location_this_turn: dict[str, Any] = field(default_factory=dict)
    """Location dict after applying location_change from scene result (or state's if no change)."""

    # Scene stream outputs (stream 1) — passed through to storytell
    candidate_npcs: list[dict[str, Any]] = field(default_factory=list)
    """Per-NPC beat candidates: [{"id": "npc_id", "type": "motivation|fear|leverage|bond|personality", "effect": "vague psychological pressure ~5 words"}, ...]"""

    # State stream outputs (stream 2)
    inventory_this_turn: list[dict[str, Any]] = field(default_factory=list)
    """inventory list after applying inventory_add/remove/update from state result."""
    conditions_this_turn: list[dict[str, Any]] = field(default_factory=list)
    """pc.conditions after applying pc_condition_add/remove from state result."""


def _build_extraction_context(
    state: dict[str, Any],
    scene_result: "SceneExtractResult",
    state_result: "StateExtractResult",
) -> _ExtractionContext:
    """Compute this-turn derived context from the two upstream extraction results.

    Calls apply_delta() on a deep copy of state so the storyteller's
    view of NPCs, inventory, and conditions is guaranteed to match what
    apply_delta() will actually write — including any validation rejections.
    Does NOT mutate ``state``.
    """
    from ccya.state.delta_builder import apply_delta

    combined_delta = StateDelta(
        compendium_npc_update=list(scene_result.compendium_npc_update or []),
        location_change=state_result.location_change,
        inventory_add=list(state_result.inventory_add or []),
        inventory_remove=list(state_result.inventory_remove or []),
        inventory_update=list(state_result.inventory_update or []),
        pc_condition_add=list(state_result.pc_condition_add or []),
        pc_condition_remove=list(state_result.pc_condition_remove or []),
    )

    state_copy = copy.deepcopy(state)
    post_state = apply_delta(state_copy, combined_delta)

    post_pc = post_state.get("pc") or {}

    location_this_turn = dict(post_state.get("location") or {})
    if state_result.location_description:
        location_this_turn["description"] = state_result.location_description

    return _ExtractionContext(
        comp_this_turn=post_state.setdefault("compendium", {}).setdefault("npcs", {}),
        location_this_turn=location_this_turn,
        candidate_npcs=_filter_unnamed_personality(scene_result.candidate_npcs or [], post_state),
        inventory_this_turn=list(post_state.get("inventory") or []),
        conditions_this_turn=list(post_pc.get("conditions") or []),
    )


def _is_named(name: str) -> bool:
    """Heuristic: a proper name has 2+ words with first and last capitalized."""
    if not name:
        return False
    words = name.strip().split()
    if len(words) < 2:
        return False
    first_word = words[0]
    last_word = words[-1]
    return bool(first_word and first_word[0].isupper() and last_word and last_word[0].isupper())


def _filter_unnamed_personality(
    candidates: list[dict[str, Any]],
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    """Strip personality type from candidate_npcs entries for unnamed NPCs.

    Unnamed NPCs (name doesn't look like a proper name) should only have bio — they
    cannot have personality, motivation, fear, leverage, or bond. If the
    extractor incorrectly assigns personality to an unnamed NPC, remove it.
    """
    comp_npcs = (state.get("compendium") or {}).get("npcs", {})
    result = []
    for c in candidates:
        npc_id = c.get("id", "")
        npc_entry = comp_npcs.get(npc_id, {})
        # Check if this NPC is unnamed: name doesn't look like a proper name
        name = (npc_entry.get("name") or "").strip()
        is_unnamed = name and not _is_named(name)
        if is_unnamed and c.get("type") == "personality":
            # Skip personality candidates for unnamed NPCs
            _log.debug(
                "candidate_npcs: stripping personality for unnamed NPC %s",
                npc_id,
            )
            continue
        result.append(c)
    return result
