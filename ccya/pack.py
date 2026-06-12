"""Pack loader: Pydantic models for world-pack manifests, seed states, and scenario briefs.

The models here are the schema-of-record for generate_seed(pack, overrides) -> SeedEnvelope.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator

from ccya.models import CampaignArc, InventoryItem, WorldStateFact


_log = logging.getLogger(__name__)


class SeedPC(BaseModel):
    name: str
    tagline: str = ""
    bio: str = ""
    stats: dict[str, int] = Field(default_factory=dict)
    conditions: list[str] = Field(default_factory=list)
    momentum: int = 0
    drive: str = ""


class SeedLocation(BaseModel):
    id: str
    name: str
    description: str = ""


class CompendiumEntry(BaseModel):
    model_config = {"extra": "allow"}
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    bond: str | None = None
    presence: str | None = None  # "present" | "nearby" | "known" — set by seed or engine
    notes: str | None = None      # scene-specific attitude, cleared on departure
    motivation: str | None = None  # what NPC fundamentally wants (UI-visible in compendium tooltip)
    fear: str | None = None        # what NPC is most afraid of (state-only, not UI-visible)
    leverage: str | None = None   # what NPC can offer/threaten/withhold (state-only, not UI-visible)
    personality: str | None = None  # archetype id; write-once, engine-assigned


class SeedCompendium(BaseModel):
    npcs: dict[str, CompendiumEntry] = Field(default_factory=dict)


class SeedScene(BaseModel):
    tagline: str = ""
    tags: list[str] = Field(default_factory=list)
    world_state: list[WorldStateFact | str] = Field(default_factory=list)


class SeedState(BaseModel):
    """Full validated game state shape — used for static load and dynamic seed writing.

    NOTE: StateDelta.inventory_add has max_length=6 (per-turn add cap).
    Inventory is empty at seed time — PCs acquire items through gameplay.
    """

    meta: dict[str, Any]
    pc: SeedPC
    location: SeedLocation
    inventory: list[InventoryItem] = Field(default_factory=list)
    scene: SeedScene
    compendium: SeedCompendium = Field(default_factory=SeedCompendium)
    arc: CampaignArc | None = None


class SeedEnvelope(BaseModel):
    """Output schema for the generate_seed LLM call.

    The LLM may populate compendium.npcs at seed time with 2-3 additional
    NPCs (name, title, bio). These are known-to-but-not-present in the
    opening scene. Compendium entries may have presence field set to 
    'present' or 'known'. Do NOT set meta.compendium_touch_order — engine manages
    that field at runtime.
    """

    seed_state: SeedState
    opening_narrative: str = Field(min_length=50)
    actions: list[str] = Field(min_length=4, max_length=4)
    arc: CampaignArc | None = None
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


class PoolEntry(BaseModel):
    """Base entry for archetype pools (situation, arc, character, moral, npc_bond)."""

    id: str
    tags: list[str] = Field(default_factory=list)
    incompatible_with: list[str] = Field(default_factory=list)
    description: str = ""


class SceneDetailBundle(BaseModel):
    id: str
    items: list[str] = Field(default_factory=list, max_length=2)
    conditions: list[str] = Field(default_factory=list, max_length=2)
    sensory: list[str] = Field(default_factory=list, max_length=2)


class ScenarioBrief(BaseModel):
    """Complete world definition for a generated pack.

    Sections:
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
    world_name: str = ""
    constraints: Constraints = Field(default_factory=Constraints)
    world_facts: list[str] = Field(default_factory=list, max_length=8)
    narrator_rules: list[str] = Field(default_factory=list, max_length=12)
    world_rules: list[str] = Field(default_factory=list, max_length=5)
    factions: list[Faction] = Field(default_factory=list, max_length=6)
    name_locales: list[dict[str, Any]] = Field(default_factory=list)
    name_seed: int = 0
    inspiration: Inspiration = Field(default_factory=Inspiration)
    situation_archetypes: list[PoolEntry] = Field(default_factory=list, max_length=16)
    arc_categories: list[PoolEntry] = Field(default_factory=list, max_length=20)
    character_dynamics: list[PoolEntry] = Field(default_factory=list, max_length=12)
    moral_pressures: list[PoolEntry] = Field(default_factory=list, max_length=10)
    npc_bonds: list[PoolEntry] = Field(default_factory=list, max_length=8)
    scene_detail_bundles: list[SceneDetailBundle] = Field(default_factory=list, max_length=8)
    currency_id: str = ""
    starting_currency_amount: int = 0


class WorldBrief(BaseModel):
    """Player input for generate_pack(). Five structured sections + one free-form.

    Each section drives a distinct part of world generation:
      concept       — the one-line pitch ("post-flood survival", "1930s supernatural noir")
      tone          — feel and register ("grim survival", "darkly comedic", "tense political")
      geography     — what the physical world looks like and how it shapes daily life
      power         — who holds power, how it was won, what it costs ordinary people
      daily_life    — what people eat, trade, fear, and talk about (grounds the narrator)
      player_hint   — optional: what kind of person the player wants to be (soft guidance)
    """
    concept: str
    tone: str = ""
    geography: str = ""
    power: str = ""
    daily_life: str = ""
    player_hint: str = ""


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


class PackManifest(BaseModel):
    model_config = {"extra": "ignore"}
    id: str
    name: str
    tone_tags: list[str] = Field(default_factory=list)
    baseline_facts: list[str] = Field(default_factory=list, max_length=3)
    name_locales: list[dict[str, Any]] = Field(default_factory=list)
    use_male_only_names: bool = False


class Pack(BaseModel):
    manifest: PackManifest
    seed: SeedState | None = None
    scenario: ScenarioBrief | None = None
    opening_scene: str | None = None
    style: str | None = None

    @model_validator(mode="after")
    def _check_playable(self) -> "Pack":
        if self.seed is None and self.scenario is None:
            raise ValueError("Pack must have seed_state.yaml or scenario.yaml")
        return self


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

    seed: SeedState | None = None
    scenario: ScenarioBrief | None = None

    # Static mode: seed_state.yaml (eval harness only)
    seed_path = pack_dir / "seed_state.yaml"
    if seed_path.exists():
        seed_data = _read_yaml("seed_state.yaml")
        if seed_data:
            seed = SeedState(**seed_data)

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

    return Pack(
        manifest=manifest,
        seed=seed,
        scenario=scenario,
        opening_scene=opening_scene,
        style=style,
    )


def list_packs(packs_dir: Path) -> list[PackManifest]:
    manifests: list[PackManifest] = []
    if not packs_dir.is_dir():
        return manifests
    search_dirs = [
        packs_dir / "generated",
        packs_dir / "default",
        packs_dir / "custom",
        packs_dir / "eval",
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
                    manifests.append(PackManifest(**data))
                except Exception as err:
                    _log.warning("Skipping invalid pack manifest at %s: %s", manifest_path, err)

    return manifests


