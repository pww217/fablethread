"""Pack loader: Pydantic models for world-pack manifests, seed states, and scenario briefs.

The models here are the schema-of-record for prepare_seed(pack, overrides) -> SeedStateEnvelope
followed by narrate_seed(seed_state, ...) -> dict, assembled into SeedEnvelope.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from ccya.models import LongTermObjective, InventoryItem, WorldStateFact


_log = logging.getLogger(__name__)


class SeedPC(BaseModel):
    name: str
    tagline: str = ""
    bio: str = ""
    stats: dict[str, int] = Field(default_factory=dict)
    conditions: list[str] = Field(default_factory=list)
    drive: str = ""
    situation: dict[str, str] = Field(default_factory=dict)
    color: str | None = None


class SeedLocation(BaseModel):
    id: str
    name: str
    description: str = ""


class CompendiumEntry(BaseModel):
    model_config = {"extra": "allow"}
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    tie: str | None = None
    presence: str | None = None  # "present" | "nearby" | "known" — set by seed or engine
    notes: str | None = None      # scene-specific attitude, cleared on departure
    motivation: str | None = None  # what NPC fundamentally wants (UI-visible in compendium tooltip)
    fear: str | None = None        # what NPC is most afraid of (state-only, not UI-visible)
    leverage: str | None = None   # what NPC can offer/threaten/withhold (state-only, not UI-visible)
    color: str | None = None      # deterministic sidebar color (set by seed sanitizer)


class SeedCompendium(BaseModel):
    npcs: dict[str, CompendiumEntry] = Field(default_factory=dict)


class SeedScene(BaseModel):
    tags: list[str] = Field(default_factory=list)
    world_state: list[WorldStateFact | str] = Field(default_factory=list)


class SeedState(BaseModel):
    """Full validated game state shape — used for dynamic seed writing.

    NOTE: StateMerge.inventory_add has max_length=6 (per-turn add cap).
    Inventory is empty at seed time — PCs acquire items through gameplay.
    """

    meta: dict[str, Any]
    pc: SeedPC
    location: SeedLocation
    inventory: list[InventoryItem] = Field(default_factory=list)
    scene: SeedScene
    compendium: SeedCompendium = Field(default_factory=SeedCompendium)
    long_term_objective: LongTermObjective | None = None
    arc_origin: str = Field(min_length=1)
    actions: list[str] = Field(default_factory=list)
    world: dict[str, Any] = Field(default_factory=dict)


class SeedStateEnvelope(BaseModel):
    """Wraps SeedState without narrative min_length constraints.

    Output of prepare_seed(). Used as intermediate shape before
    narrate_seed() adds opening_narrative, actions, outcome_summary.
    """

    seed_state: SeedState
    opening_narrative: str = ""
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""
    long_term_objective: LongTermObjective | None = None
    arc_origin: str = Field(min_length=1)
    pool_selection: dict[str, Any] | None = None


class SeedEnvelope(BaseModel):
    """Output schema for the assembled seed (prepare_seed + narrate_seed).

    The LLM may populate compendium.npcs at seed time with 2-3 additional
    NPCs (name, title, bio). These are known-to-but-not-present in the
    opening scene. Compendium entries may have presence field set to 
    'present' or 'known'. Do NOT set meta.compendium_touch_order — engine manages
    that field at runtime.
    """

    seed_state: SeedState
    opening_narrative: str = Field(min_length=1500)
    actions: list[str] = Field(min_length=4, max_length=4)
    long_term_objective: LongTermObjective | None = None
    arc_origin: str = Field(min_length=1)
    outcome_summary: str = ""


class Faction(BaseModel):
    id: str
    name: str
    description: str
    disposition: str = "neutral"


class Constraints(BaseModel):
    inventory_size_range: tuple[int, int] = (4, 8)
    pc_stat_range: tuple[int, int] = (1, 4)
    pc_stat_total_range: tuple[int, int] = (12, 18)
    prose_word_range: tuple[int, int] = (200, 500)
    required_inventory_kinds: list[str] = Field(default_factory=list)
    forbid_cliches: list[str] = Field(default_factory=list)


class Inspiration(BaseModel):
    pc: str = ""
    inventory: str = ""
    npcs: str = ""


class PcSituationSchemaEntry(BaseModel):
    """A single key in the pc_situation_schema."""

    key: str
    description: str = ""
    required: bool = False
    persist: bool = False


class PoolEntry(BaseModel):
    """Base entry for archetype pools (situation, arc, character, npc_bond)."""

    id: str
    tags: list[str] = Field(default_factory=list)
    incompatible_with: list[str] = Field(default_factory=list)
    description: str = ""


class SceneDetailBundle(BaseModel):
    id: str
    conditions: list[str] = Field(default_factory=list, max_length=3)
    sensory: list[str] = Field(default_factory=list, max_length=3)


class ScenarioBrief(BaseModel):
    """Complete world definition for a generated pack.

    Sections:
      description   — one-line pack description (parity with default packs)
      constraints   — hard numeric rules for seed generation
      world_name    — short evocative name for the world (LLM-generated)
      world_facts   — 3–8 durable facts injected into world_state at seed time
      narrator_rules — tone/style rules injected into narrate system prompt (replaces style.md)
      world_rules   — 0–5 hard physical laws of the world (rendered as ## Universe rules)
      factions      — 3–6 named power groups injected into narrate context each turn
      name_locales  — weighted Faker locales for name generation
      name_seed     — int; controls name selection randomness at generate time
      inspiration   — quality anti-pattern guidance for seed generation (no concrete examples)
    """
    description: str = ""
    world_name: str = ""
    constraints: Constraints = Field(default_factory=Constraints)
    world_facts: list[str] = Field(default_factory=list, min_length=3, max_length=8)
    narrator_rules: list[str] = Field(default_factory=list, max_length=12)
    world_rules: list[str] = Field(default_factory=list, max_length=5)
    factions: list[Faction] = Field(default_factory=list, max_length=6)
    name_locales: list[dict[str, Any]] = Field(default_factory=list)
    name_seed: int | None = None
    inspiration: Inspiration = Field(default_factory=Inspiration)
    pc_situation_schema: list[PcSituationSchemaEntry] = Field(default_factory=list)
    situation_archetypes: list[PoolEntry] = Field(default_factory=list, max_length=16)
    arc_categories: list[PoolEntry] = Field(default_factory=list, max_length=20)
    character_dynamics: list[PoolEntry] = Field(default_factory=list, max_length=12)
    npc_bonds: list[PoolEntry] = Field(default_factory=list, max_length=8)
    scene_detail_bundles: list[SceneDetailBundle] = Field(default_factory=list, max_length=8)
    currency_id: str = ""
    starting_currency_amount: int = 0


class WorldBrief(BaseModel):
    """Player input for generate_pack(). Two sections: concept and tone.

    Drives world generation:
      concept   — the one-line pitch ("post-flood survival", "1930s supernatural noir")
      tone      — feel and register ("grim survival", "darkly comedic", "tense political")
    """
    concept: str
    tone: str = ""


class PlayerOverrides(BaseModel):
    """Optional player-supplied direction at New Game time. All fields default empty.
    Authoritative for PC identity (name, stats, concept); strongly preferred for
    arc, NPCs, and location. Only override on direct canon conflict."""

    pc_hints: str = ""
    npc_hints: str = ""
    location_hints: str = ""
    free_form: str = ""
    arc_hints: str = ""

    def is_empty(self) -> bool:
        return not any(
            [
                self.pc_hints,
                self.npc_hints,
                self.location_hints,
                self.free_form,
                self.arc_hints,
            ]
        )


class PackFiles(BaseModel):
    world: str = ""
    scenario: str = ""


class PackManifest(BaseModel):
    model_config = {"extra": "forbid"}
    id: str
    name: str
    description: str = ""
    tone_tags: list[str] = Field(default_factory=list)
    files: PackFiles = Field(default_factory=PackFiles)
    name_locales: list[dict[str, Any]] = Field(default_factory=list)
    use_male_only_names: bool = False
    checkers: dict[str, Any] = Field(default_factory=dict)
    baseline_facts: list[str] = Field(default_factory=list)


class Pack(BaseModel):
    manifest: PackManifest
    scenario: ScenarioBrief | None = None
    opening_scene: str | None = None
    style: str | None = None


def _resolve_pack_dir(pack_id: str, packs_dir: Path) -> Path:
    """Resolve pack_id to a directory.

    Accepts:
      "flooded-world"          -> searches packs/default/, then packs/custom/
      "default/flooded-world"  -> packs/default/flooded-world
      "custom/my-world"        -> packs/custom/my-world
    """
    if "/" in pack_id:
        namespace, slug = pack_id.split("/", 1)
        candidate = packs_dir / namespace / slug
        if not candidate.is_dir():
            raise FileNotFoundError(f"Pack not found: {candidate}")
        return candidate
    # Check for pack directly under packs_dir (no namespace) first — supports
    # eval packs and any other flat pack layout.
    candidate = packs_dir / pack_id
    if candidate.is_dir():
        return candidate
    for namespace in ("default", "custom"):
        candidate = packs_dir / namespace / pack_id
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Pack '{pack_id}' not found in {packs_dir}")


def load_pack(pack_id: str, packs_dir: Path) -> Pack:
    pack_dir = _resolve_pack_dir(pack_id, packs_dir)

    manifest_path = pack_dir / "pack.yaml"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing pack.yaml in {pack_dir}")
    with open(manifest_path) as f:
        manifest_data = yaml.safe_load(f) or {}
    manifest = PackManifest(**manifest_data)

    def _read_yaml(filename: str) -> dict[str, Any]:
        p = pack_dir / filename
        if not p.exists():
            return {}
        with open(p) as f:
            try:
                return yaml.safe_load(f) or {}
            except Exception:
                _log.error("YAML parse failed in %s", p)
                raise

    scenario: ScenarioBrief | None = None

    # Dynamic mode: scenario.yaml (new consolidated schema)
    scenario_path = pack_dir / "scenario.yaml"
    if scenario_path.exists():
        scenario_data = _read_yaml("scenario.yaml")
        if scenario_data:
            scenario = ScenarioBrief(**scenario_data)

    # Load optional text files (opening scene and style guide)
    opening_scene = None
    opening_scene_path = pack_dir / "opening_scene.md"
    if opening_scene_path.exists():
        opening_scene = opening_scene_path.read_text(encoding="utf-8")

    style = None
    style_path = pack_dir / "style.md"
    if style_path.exists():
        style = style_path.read_text(encoding="utf-8")

    pack = Pack(
        manifest=manifest,
        scenario=scenario,
        opening_scene=opening_scene,
        style=style,
    )
    validate_pack(pack, pack_id)
    return pack


def _validate_pool_entries(entries: list[PoolEntry], pool_name: str) -> list[str]:
    """Helper for pool validation. Checks unique IDs and valid incompatible_with references.

    Returns the list of IDs for caller use (e.g., faction uniqueness check).
    """
    seen_ids: dict[str, int] = {}
    for i, entry in enumerate(entries):
        if entry.id in seen_ids:
            raise ValueError(f"pool '{pool_name}' has duplicate ID '{entry.id}' (first at index {seen_ids[entry.id]}, duplicate at {i})")
        seen_ids[entry.id] = i
        for ref in entry.incompatible_with:
            if ref not in seen_ids and ref not in {e.id for e in entries}:
                raise ValueError(f"pool '{pool_name}' entry '{entry.id}' references non-existent incompatible_with ID '{ref}'")
    return list(seen_ids.keys())


def validate_pack(pack: Pack, pack_id: str | None = None) -> None:
    """Validate a pack's structural integrity.

    Called at the end of `load_pack()`. Raises `ValueError` with a single
    aggregated message listing every problem found. Each problem identifies
    the pack, the field path, and what's wrong.
    """
    label = f"Pack '{pack_id}'" if pack_id else "Pack"
    errors: list[str] = []

    # 1. Manifest structural
    if not pack.manifest.id.strip():
        errors.append(f"{label}: manifest.id is empty")
    if not pack.manifest.name.strip():
        errors.append(f"{label}: manifest.name is empty")

    # 2. World facts minimum
    if pack.scenario is not None and len(pack.scenario.world_facts) < 3:
        errors.append(f"{label}: scenario.world_facts must have at least 3 entries (has {len(pack.scenario.world_facts)})")

    # 3. Pool entry structural integrity
    pool_fields: list[tuple[str, list[PoolEntry]]] = [
        ("situation_archetypes", pack.scenario.situation_archetypes if pack.scenario else []),
        ("arc_categories", pack.scenario.arc_categories if pack.scenario else []),
        ("character_dynamics", pack.scenario.character_dynamics if pack.scenario else []),
        ("npc_bonds", pack.scenario.npc_bonds if pack.scenario else []),
    ]
    for pool_name, entries in pool_fields:
        if not entries:
            errors.append(f"{label}: scenario.{pool_name} pool must have at least 1 entry (has 0)")
        else:
            try:
                _validate_pool_entries(entries, pool_name)
            except ValueError as ve:
                errors.append(f"{label}: {ve}")

    # 4. Faction uniqueness
    if pack.scenario and pack.scenario.factions:
        seen_faction_ids: dict[str, int] = {}
        for i, faction in enumerate(pack.scenario.factions):
            if faction.id in seen_faction_ids:
                errors.append(f"{label}: scenario.factions has duplicate ID '{faction.id}' (first at index {seen_faction_ids[faction.id]}, duplicate at {i})")
            else:
                seen_faction_ids[faction.id] = i

    # 5. PC situation schema uniqueness
    if pack.scenario and pack.scenario.pc_situation_schema:
        seen_keys: dict[str, int] = {}
        for i, entry in enumerate(pack.scenario.pc_situation_schema):
            if entry.key in seen_keys:
                errors.append(f"{label}: scenario.pc_situation_schema has duplicate key '{entry.key}' (first at index {seen_keys[entry.key]}, duplicate at {i})")
            else:
                seen_keys[entry.key] = i

    # 6. Scene detail bundles uniqueness
    if pack.scenario and pack.scenario.scene_detail_bundles:
        seen_bundles: dict[str, int] = {}
        for i, bundle in enumerate(pack.scenario.scene_detail_bundles):
            if bundle.id in seen_bundles:
                errors.append(f"{label}: scenario.scene_detail_bundles has duplicate ID '{bundle.id}' (first at index {seen_bundles[bundle.id]}, duplicate at {i})")
            else:
                seen_bundles[bundle.id] = i

    if errors:
        raise ValueError("; ".join(errors))


def list_packs(packs_dir: Path) -> list[PackManifest]:
    manifests: list[PackManifest] = []
    if not packs_dir.is_dir():
        return manifests
    search_dirs = [
        packs_dir / "generated",
        packs_dir / "default",
        packs_dir / "custom",
    ]
    seen: set[str] = set()
    for search in search_dirs:
        if not search.is_dir():
            continue
        for child in sorted(search.iterdir()):
            if not child.is_dir():
                continue
            manifest_path = child / "pack.yaml"
            if manifest_path.exists() and child.name not in seen:
                seen.add(child.name)
                try:
                    with open(manifest_path) as f:
                        data = yaml.safe_load(f) or {}
                    manifest = PackManifest(**data)
                    try:
                        validate_pack(Pack(manifest=manifest), child.name)
                    except ValueError as ve:
                        _log.warning("Pack '%s' failed validation: %s", child.name, ve)
                    manifests.append(manifest)
                except Exception as err:
                    _log.warning("Skipping invalid pack manifest at %s: %s", manifest_path, err)

    return manifests


