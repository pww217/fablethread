"""Extraction context: this-turn derived state from scene + state streams."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ccya.models import NPCEntry, SceneExtractResult, StateMerge, StateExtractResult, WorldState

_log = logging.getLogger(__name__)


@dataclass
class _PostDeltaContext:
    """Carries this-turn deltas from scene + state streams into the record stream.

    All fields are derived from extract results, NOT from ``state``.  They
    represent what happened *this turn* as determined by the prior two streams.
    """
    comp_this_turn: dict[str, NPCEntry] = field(default_factory=dict)
    """Reference to post-delta compendium.npcs dict (not a copy)."""
    location_this_turn: dict[str, Any] = field(default_factory=dict)
    """Location dict after applying location_change from scene result (or state's if no change)."""
    # State stream outputs (stream 2)
    inventory_this_turn: list[dict[str, Any]] = field(default_factory=list)
    """inventory list after applying inventory_add/remove/update from state result."""
    conditions_this_turn: list[dict[str, Any]] = field(default_factory=list)
    """pc.conditions after applying pc_condition_add/remove from state result."""


def _build_post_delta_context(
    state: WorldState,
    scene_result: "SceneExtractResult",
    state_result: "StateExtractResult",
) -> _PostDeltaContext:
    """Compute this-turn derived context from the two upstream extraction results.

    Calls apply_delta() on a deep copy of state so the record stream's
    view of NPCs, inventory, and conditions is guaranteed to match what
    apply_delta() will actually write — including any validation rejections.
    Does NOT mutate ``state``.
    """
    from ccya.state.delta_builder import apply_delta

    combined_delta = StateMerge(
        compendium_npc_add=list(scene_result.compendium_npc_add or []),
        compendium_npc_update=list(scene_result.compendium_npc_update or []),
        location_change=state_result.location_change,
        inventory_add=list(state_result.inventory_add or []),
        inventory_remove=list(state_result.inventory_remove or []),
        inventory_update=list(state_result.inventory_update or []),
        pc_condition_add=list(state_result.pc_condition_add or []),
        pc_condition_remove=list(state_result.pc_condition_remove or []),
    )

    state_copy = state.model_copy()
    post_state = apply_delta(state_copy, combined_delta)

    post_pc = post_state.pc

    location_this_turn = post_state.location.model_dump()
    if state_result.location_description:
        location_this_turn["description"] = state_result.location_description

    return _PostDeltaContext(
        comp_this_turn=post_state.compendium.npcs,
        location_this_turn=location_this_turn,
        inventory_this_turn=[item.model_dump() for item in post_state.inventory],
        conditions_this_turn=[c.model_dump() for c in post_pc.conditions],
    )

