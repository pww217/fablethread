"""Typed block and boundary models for prompt context assembly.

Blocks are read-only data containers that accept a raw state dict and produce
typed snapshots via .model_dump(). Boundaries compose blocks as fields — each
boundary corresponds to one user/system prompt template.

This keeps prompt context types separate from LLM output types (models.py).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


from ccya.models import (
    ArcThread,
    Condition,
    InventoryItem,
    IntentEnvelope,
    NpcPresence,
    RulesOutcome,
)


class PlayerBlock(BaseModel):
    """Player character snapshot for prompt rendering."""

    name: str
    tagline: str | None = None
    concept: str | None = None
    stats: dict[str, int]  # {strength/dexterity/wits/lore/charisma/resolve: int}
    conditions: list[Condition]

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> PlayerBlock:
        pc = state.get("pc", {})
        return cls(
            name=pc.get("name", "Unnamed"),
            tagline=pc.get("tagline"),
            concept=None,  # Not stored in state — computed at render time if needed.
            stats=dict(pc.get("stats", {})),
            conditions=[Condition(**c) for c in pc.get("conditions", [])],
        )


class LocationBlock(BaseModel):
    """Location snapshot for prompt rendering."""

    id: str
    name: str
    description: str | None = None

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> LocationBlock:
        loc = state.get("location", {})
        return cls(
            id=loc.get("id", ""),
            name=loc.get("name", "Unknown"),
            description=loc.get("description"),
        )


class InventoryBlock(BaseModel):
    """Inventory snapshot for prompt rendering."""

    items: list[InventoryItem]  # reuses existing InventoryItem model from models.py

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> InventoryBlock:
        raw = state.get("inventory", [])
        return cls(items=[InventoryItem(**i) if isinstance(i, dict) else i for i in raw])


class ArcThreadSummary(BaseModel):
    """Simplified arc thread data for prompt rendering (subset of full ArcThread).

    Used by _thread_list.j2 and storytell_user.j2. Both templates access: id, scope, urgency, summary, tags, active.
    """

    id: str
    summary: str
    scope: Literal["scene", "arc"]
    urgency: Literal["background", "normal", "urgent"]
    tags: list[str] = Field(default_factory=list)
    active: bool


class ArcThreadBlock(BaseModel):
    """Campaign arc snapshot for prompt rendering."""

    visible_goal: str
    thematic_question: str
    threads: list[ArcThreadSummary]  # simplified thread view for prompts

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> ArcThreadBlock:
        arc = state.get("arc", {})
        raw_threads = []
        for t in arc.get("threads", []) + arc.get("completed_threads", []):
            if isinstance(t, ArcThreadSummary):
                raw_threads.append(t)
            elif isinstance(t, dict):
                raw_threads.append(
                    ArcThreadSummary(
                        id=t.get("id", ""),
                        summary=t.get("summary", ""),
                        scope=t.get("scope", "arc"),
                        urgency=t.get("urgency", "normal"),
                        tags=list(t.get("tags", [])),
                        active=bool(t.get("active", True)),
                    )
                )
            elif isinstance(t, ArcThread):
                raw_threads.append(
                    ArcThreadSummary(
                        id=t.id,
                        summary=t.summary,
                        scope=t.scope,
                        urgency=t.urgency,
                        tags=list(t.tags),
                        active=bool(t.active),
                    )
                )
        return cls(
            visible_goal=arc.get("visible_goal", ""),
            thematic_question=arc.get("thematic_question", ""),
            threads=raw_threads,
        )


class WorldStateBlock(BaseModel):
    """World state snapshot for prompt rendering."""

    entries: list[str]  # raw world state strings from scene.world_state[]

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> WorldStateBlock:
        ws = state.get("scene", {}).get("world_state", [])
        return cls(entries=[str(e) if isinstance(e, str) else str(e.values()) for e in ws])


class ChronicleEntryBlock(BaseModel):
    """A single chronicle/turn entry for prompt rendering.

    Source: load_last_narration() returns dicts with turn/input/narrative keys (line 43 of state/chronicle.py).
    Templates only use .turn and .narrative — the "input" field is dead in boundary models but preserved from source data shape.
    """

    turn: int
    narrative: str


class PacingBlock(BaseModel):
    """Pacing context snapshot for prompt rendering."""

    directive: str | None = None  # used by storytell_user.j2 line 56 and narrate_user.j2 line 80


class LastSeenBlock(BaseModel):
    """Last-seen metadata for an NPC in the roster."""

    turn: int
    location_id: str
    location_name: str


class NPCRosterEntryBlock(BaseModel):
    """Single entry in an NPC roster for prompt rendering.

    Source shapes vary by origin: build_npc_roster() outputs dicts with last_seen as a dict (turn/location_id/location_name) from compendium data, or None for present NPCs. Template extract_scene_user.j2 line 7 accesses n.last_seen.location_name — not a string.
    """

    id: str
    name: str
    title: str | None = None
    bio: str | None = None
    presence: NpcPresence  # reuses existing enum from models.py
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    notes: str | None = None
    last_seen: LastSeenBlock | None = None


class RulingBoundary(BaseModel):
    """Context for ruling_user.j2.

    NOTE: recent_turns is passed by _ruling_messages but ruling_user.j2 never renders it — dead field removed from boundary model.
    """

    pc: PlayerBlock
    location: LocationBlock
    user_input: str
    meta: dict[str, int]
    npc_roster: list[NPCRosterEntryBlock]
    last_outcome: str | None = None


class NarratorBoundary(BaseModel):
    """Context for narrate_user.j2.

    Source: _narrate_messages() user_ctx (lines 72-104). Note that _location.j2 and _inventory.j2 includes access state.location/state.inventory,
    so these are NOT separate top-level fields — they're accessed via the `state` dict.
    ArcThreadBlock is exposed as `current_arc` to match _arc.j2's variable name (line 1 of _arc.j2).

    NOTE: threat_ages, threat_pressure_at, building_threat_imperative_at are passed in user_ctx but narrate_user.j2 never uses them — dead fields removed from boundary model. chronicle_tail was also dead and was removed from user_ctx in the incremental history refactor.
    momentum, scene, compendium_bios, known_npcs, present_npcs also flagged as dead by alignment check and removed.
    """

    pc: PlayerBlock  # maps to {{ pc.* }} (lines 2-6 of narrate_user.j2)
    current_arc: ArcThreadBlock  # maps to {{ current_arc.* }} in _arc.j2 include (line 13 of narrate_user.j2)
    state: dict[str, Any]  # covers state.location, state.inventory, state.scene.world_state accessed by includes
    npc_roster: list[NPCRosterEntryBlock]  # from build_npc_roster() call on line 98 of _narrate_messages
    pacing_context: PacingBlock | None = None
    recent_turns: list[ChronicleEntryBlock]
    prior_history: list[str] = Field(default_factory=list)
    rules_outcome: RulesOutcome | None = None
    user_input: str
    pending_beat: dict[str, Any] | None = None
    meta: dict[str, int]
    ages: dict[str, int]
    pc_allegiance: str | None = None
    world_factions: list[dict[str, str]]
    npc_name_pool: dict[str, list[str]]

class SceneExtractBoundary(BaseModel):
    """Context for extract_scene_user.j2.

    Source: _extract_scene_messages() passes pc, location, conditions directly (lines 274-282).
    npc_roster comes from build_npc_roster(comp) — outputs dicts with id/name/title/bio/presence/mfl/notes/last_seen.
    """

    narration: str
    location: LocationBlock
    npc_roster: list[NPCRosterEntryBlock]  # from build_npc_roster(comp) — outputs dicts with id/name/title/bio/presence/mfl/notes/last_seen
    recent_turns: list[ChronicleEntryBlock]
    turn_no: int


class StateExtractBoundary(BaseModel):
    """Context for extract_state_user.j2.

    Source: _extract_state_messages() passes pc, conditions, inventory, intent, turn_no (lines 308-315).
    Template only uses narration/conditions/inventory/intent/turn_no — pc is passed but never rendered.
    """

    conditions: list[Condition]
    inventory: list[InventoryItem]
    intent: IntentEnvelope | None = None
    turn_no: int
    narration: str


class StorytellerBoundary(BaseModel):
    """Context for storytell_user.j2.

    npc_roster/location/inventory/conditions come from extraction_ctx.
    all_threads/world_state/intent/pacing_context/recent_turns/turn_no/band are top-level variables.
    current_arc provides campaign arc metadata (visible_goal, thematic_question) via _arc.j2 include.
    """

    narration: str
    npc_roster: list[NPCRosterEntryBlock]  # from build_npc_roster(comp) — outputs dicts with id/name/title/bio/presence/mfl/notes/last_seen
    location: LocationBlock
    conditions: list[Condition]
    inventory: list[InventoryItem]
    current_arc: dict[str, Any]  # campaign arc metadata — passed to _arc.j2 include
    all_threads: list[ArcThreadSummary]  # source is state.arc.threads (raw dicts) — Pydantic coerces since ArcThreadSummary field names match dict keys; schema tests must validate both raw-dict and object inputs
    world_state: list[str | dict[str, Any]]  # template uses `world_state` variable name
    intent: IntentEnvelope | None = None
    pacing_context: PacingBlock | None = None
    recent_turns: list[ChronicleEntryBlock]
    prior_history: list[str]
    turn_no: int
    band: str


class NarratorSystemBoundary(BaseModel):
    """Context for narrate_system.j2 (only system prompt with dynamic data).

    Source: _narrate_messages() passes narrator_rules, world_rules, current_arc.
    Template uses only `world_rules` and `narrator_rules`. The `current_arc` variable is passed but no longer consumed (lines 64–68 of narrate_system.j2 removed in prompt cleanup). Alignment check passes with no dead fields.
    """

    narrator_rules: list[str]
    world_rules: list[str]


# ---------------------------------------------------------------------------
# TEMPLATE_CONTRACTS mapping — alignment check wiring.
# ---------------------------------------------------------------------------

TEMPLATE_CONTRACTS: dict[str, type[BaseModel]] = {
    "storytell_user.j2": StorytellerBoundary,
    "narrate_user.j2": NarratorBoundary,
    "ruling_user.j2": RulingBoundary,
    "extract_scene_user.j2": SceneExtractBoundary,
    "extract_state_user.j2": StateExtractBoundary,
    "narrate_system.j2": NarratorSystemBoundary,
}
