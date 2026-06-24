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
    ProgressEntry,
    RulesOutcome,
)


class PlayerBlock(BaseModel):
    """Player character snapshot for prompt rendering."""

    name: str
    tagline: str | None = None
    concept: str | None = None
    stats: dict[str, int]  # {strength/dexterity/wits/charisma: int}
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
    """Simplified arc thread data for prompt rendering (subset of full ArcThread)."""

    id: str
    summary: str
    urgency: Literal["background", "normal", "urgent"]
    type: Literal["threat", "opportunity", "complication", "revelation"] | None = None
    progress: list[str] = Field(default_factory=list)
    dormant: bool
    last_updated_turn: int | None = None


def _fmt_progress(progress: Any) -> list[str]:
    if not progress:
        return []
    result: list[str] = []
    for entry in progress:
        if isinstance(entry, str):
            result.append(entry)
        elif isinstance(entry, dict):
            kind = entry.get("kind", "advancement")
            text = entry.get("text", "")
            result.append(f"[{kind.upper()}] {text}")
        elif isinstance(entry, ProgressEntry):
            result.append(f"[{entry.kind.upper()}] {entry.text}")
        else:
            result.append(str(entry))
    return result


class ArcThreadBlock(BaseModel):
    """Arc status + thread overview for prompt rendering."""

    long_term_objective: str
    resolution: str | None = None
    threads: list[ArcThreadSummary]  # simplified thread view for prompts
    completed_threads: list[ArcThreadSummary] = Field(default_factory=list)

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> ArcThreadBlock:
        arc = state.get("long_term_objective", {})
        raw_threads = []
        for t in arc.get("threads", []) + arc.get("completed_threads", []):
            if isinstance(t, ArcThreadSummary):
                raw_threads.append(t)
            elif isinstance(t, dict):
                raw_threads.append(
                    ArcThreadSummary(
                        id=t.get("id", ""),
                        summary=t.get("summary", ""),
                        urgency=t.get("urgency", "normal"),
                        type=t.get("type"),
                        progress=_fmt_progress(t.get("major_updates")),
                        dormant=bool(t.get("dormant", False)),
                        last_updated_turn=t.get("last_updated_turn"),
                    )
                )
            elif isinstance(t, ArcThread):
                raw_threads.append(
                    ArcThreadSummary(
                        id=t.id,
                        summary=t.summary,
                        urgency=t.urgency,
                        type=getattr(t, "type", None),
                        progress=_fmt_progress(t.major_updates),
                        dormant=getattr(t, "dormant", False),
                        last_updated_turn=getattr(t, "last_updated_turn", None),
                    )
                )
        completed_start = len(arc.get("threads", []))
        completed = [t for t in raw_threads[completed_start:] if isinstance(t, ArcThreadSummary)]
        return cls(
            long_term_objective=arc.get("long_term_objective", ""),
            resolution=arc.get("resolution"),
            threads=[t for t in raw_threads if isinstance(t, ArcThreadSummary)],
            completed_threads=completed,
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
    """Last-seen location name for an NPC in the roster."""

    location_name: str


class NPCRosterEntryBlock(BaseModel):
    """Single entry in an NPC roster for prompt rendering.

    Source shapes vary by origin: build_npc_roster() outputs dicts with id/name/title/bio/presence/mfl/notes/last_presence_turn/last_seen_location/departed_reason.
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
    last_presence_turn: int | None = None
    last_seen_location: str | None = None


class RulingBoundary(BaseModel):
    """Context for ruling_user.j2."""

    pc: PlayerBlock
    location: LocationBlock
    user_input: str
    meta: dict[str, int]
    npc_roster: list[NPCRosterEntryBlock]
    recent_turns: list[ChronicleEntryBlock] = Field(default_factory=list)
    inventory: list[dict[str, Any]] = Field(default_factory=list)
    scene_phase: str = "SETUP"
    urgent_threads: list[dict[str, Any]] = Field(default_factory=list)


class NarratorBoundary(BaseModel):
    """Context for narrate_user.j2.

    Source: _narrate_messages() user_ctx (lines 72-104). Note that _location.j2 and _inventory.j2 includes access state.location/state.inventory,
    so these are NOT separate top-level fields — they're accessed via the `state` dict.
    ArcThreadBlock is exposed as `current_objective` to match _arc.j2's variable name (line 1 of _arc.j2).

    NOTE: threat_ages, threat_pressure_at, building_threat_imperative_at are passed in user_ctx but narrate_user.j2 never uses them — dead fields removed from boundary model. momentum, scene, compendium_bios, known_npcs, present_npcs also flagged as dead by alignment check and removed.
    """

    pc: PlayerBlock  # maps to {{ pc.* }} (lines 2-6 of narrate_user.j2)
    current_objective: ArcThreadBlock  # maps to {{ current_objective.* }} in _arc.j2 include (line 13 of narrate_user.j2)
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
    resolved_arcs: list[dict[str, Any]] = Field(default_factory=list)

class SceneExtractBoundary(BaseModel):
    """Context for extract_scene_user.j2.

    Source: _extract_scene_messages() passes pc, conditions directly.
    npc_roster comes from build_npc_roster(comp) — outputs dicts with id/name/title/bio/presence/mfl/position/last_presence_turn/last_seen_location/departed_reason.
    """

    narration: str
    npc_roster: list[NPCRosterEntryBlock]  # from build_npc_roster(comp) — outputs dicts with id/name/title/bio/presence/mfl/position/last_presence_turn/last_seen_location/departed_reason
    pc_name: str = "Unnamed"
    turn_no: int


class StateExtractBoundary(BaseModel):
    """Context for extract_state_user.j2.

    Source: _extract_state_messages() passes pc, conditions, inventory, location, intent, turn_no.
    Template uses narration/conditions/inventory/location/intent/turn_no.
    """

    conditions: list[Condition]
    inventory: list[InventoryItem]
    location: LocationBlock
    intent: IntentEnvelope | None = None
    turn_no: int
    narration: str


class StorytellerBoundary(BaseModel):
    """Context for storytell_user.j2.

    npc_roster/location/inventory/conditions come from extraction_ctx.
    all_threads/world_state/intent/pacing_context/recent_turns/turn_no/band/scene_phase/allowed_beat_types are top-level variables.
    current_objective provides campaign arc metadata (long_term_objective, resolution) via _arc.j2 include.
    all_threads is mapped to threads via {% set threads = all_threads %} before _thread_list.j2 include.
    """

    narration: str
    npc_roster: list[NPCRosterEntryBlock]  # from build_npc_roster(comp) — outputs dicts with id/name/title/bio/presence/mfl/notes/last_presence_turn/last_seen_location/departed_reason
    location: LocationBlock
    conditions: list[Condition]
    inventory: list[InventoryItem]
    current_objective: dict[str, Any]  # campaign arc metadata — passed to _arc.j2 include
    all_threads: list[ArcThreadSummary]  # source is state.arc.threads (raw dicts) — Pydantic coerces since ArcThreadSummary field names match dict keys; schema tests must validate both raw-dict and object inputs
    world_state: list[str | dict[str, Any]]  # template uses `world_state` variable name
    intent: IntentEnvelope | None = None
    pacing_context: PacingBlock | None = None
    recent_turns: list[ChronicleEntryBlock]
    prior_history: list[str]
    turn_no: int
    band: str
    scene_phase: str = "SETUP"
    curtain_call: str = ""
    allowed_beat_types: list[str] = Field(default_factory=list)
    pending_beat: dict[str, Any] | None = None
    recent_beats: list[dict[str, Any]] = Field(default_factory=list)
    resolved_arcs: list[dict[str, Any]] = Field(default_factory=list)


class NarratorSystemBoundary(BaseModel):
    """Context for narrate_system.j2 (only system prompt with dynamic data).

    Source: _narrate_messages() passes narrator_rules, world_rules, current_objective.
    Template uses only `world_rules` and `narrator_rules`. The `current_objective` variable is passed but no longer consumed (lines 64–68 of narrate_system.j2 removed in prompt cleanup). Alignment check passes with no dead fields.
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
