# Seed/Turn Engine Parity Findings

## Purpose

This document catalogs the gaps, duplications, and divergences between the seed system (out-of-band, turn 0) and the turn engine (in-band, turn 1+). The goal is to identify what needs to be reconciled in a seed system revamp — not to prescribe solutions, but to document findings clearly for decision-making.

---

## Core Observation

Two separate code paths produce architecturally similar but mechanically different game state:

```
Out-of-band (seed):     LLM → SeedEnvelope → seed_state dict → state.yaml
In-band (turn engine):   LLM → StorytellerResult → StateDelta → apply_delta() → state.yaml
```

Both write to the same `state.yaml`. But the models, field names, validation rules, and persistence paths are partly overlapping and partly divergent. Fields seeded in one path may be ignored in the other. Code is duplicated between paths.

---

## 1. Dead / Incompatible Fields

### 1.1 `state["world"]["factions"]` — Completely Inert

**Finding:** `state["world"]["factions"]` is never read by the turn pipeline.

- Default state sets `world: {"factions": [], "locations": []}` at `ccya/state/io.py:106-109`
- Seed never populates `state["world"]["factions"]`
- Turn pipeline reads faction data from the **pack manifest** at `ccya/engine/narrate.py:180`:
  ```python
  world_factions = ctx.packing.get("factions", [])  # from pack, not state
  ```
- No extraction prompt, ruling context, or delta builder ever reads `state["world"]`

**Status:** Dead field. Recommended for removal from default state and any seed schema references.

**Files:**
- `ccya/state/io.py:106-109` — default state initialization
- `ccya/engine/narrate.py:180` — turn pipeline reads from pack, not state

---

### 1.2 `ArcThread.scope` — Seed-Generated, Never Consumed

**Finding:** Seed generates `scope` on threads (set to `"arc"` in static seed examples), but no turn prompt or code path reads this field.

- `ArcThread.scope` is defined at `ccya/models/state.py` (ArcThread model)
- `seed_state.yaml` uses `scope: arc` on threads
- `seed.py` passes threads through from `envelope.arc.threads` without reading `scope`
- No prompt template references `scope` (grep `scope` in all Jinja templates: zero matches)
- `thread_sanitizer.py` does not filter or act on `scope`
- `turn_state.py` auto-dormant logic does not check `scope`
- `_arc.j2` does not render `scope`

**Status:** Dead field. Seed sets it, but nothing consumes it. The field should be removed from `ArcThread` and from any seed generation output, or its purpose must be defined.

---

### 1.3 `ArcThread.tags` — Seed-Generated, Never Consumed

**Finding:** Same as `scope`. Seed generates `tags: [debt, caron, obligation]` on threads. No template or engine code reads `tags`.

- `ArcThread.tags` defined at `ccya/models/state.py:27` (`tags: list[str] = Field(default_factory=list)`)
- Seed examples use tags: `tags: [debt, caron, obligation]`
- `_thread_list.j2` does not render `tags`
- `thread_sanitizer.py` does not filter on `tags`
- No extraction prompt references thread tags

**Status:** Dead field. Same recommendation as `scope`.

---

### 1.4 `ArcThread.last_seen_turn` — Seed-Generated, Engine-Overwritten

**Finding:** Seed initializes `last_seen_turn: null` but the turn pipeline overwrites this via `last_updated_turn` (different field).

- Seed sets `last_seen_turn: null` at `seed_state.yaml:131`
- `ArcThread.last_seen_turn` is in the model at `ccya/models/state.py:36`
- But `last_updated_turn` is the field the engine actually uses and updates (`ccya/models/state.py:36`)
- `seed.py` does not set `last_seen_turn` — it sets `last_updated_turn` when enforcing limits at lines 377-378
- No template or code reads `last_seen_turn`

**Status:** Confusing duplicate. `last_seen_turn` appears to be a stale/legacy field replaced by `last_updated_turn`. Seed should use `last_updated_turn` consistently.

---

### 1.5 `opening_narrative` / `outcome_summary` in Seed Schema — Display-Only, Not Pipeline-Consumed

**Finding:** Seed outputs `opening_narrative` (~700 words) and `outcome_summary` (1 sentence). These are written to `chronicle.md` and stored in `__seed_meta__`, but never appear in any turn prompt.

- `opening_narrative` is written to `chronicle.md` at `ccya/state/io.py:156-158`
- It is NOT included in `narrate_user.j2`, `storytell_user.j2`, or any extraction prompt
- `outcome_summary` from seed is stored but never referenced in turn pipeline
- The **turn-level** `outcome_summary` (from `StorytellerResult`) IS used — appended to `prior_history` each turn

**Status:** Seed's `opening_narrative` is intentionally one-time display (Turn 0 narrator). This is fine architecturally — it's a pre-game intro. But it means the opening prose has no ongoing gameplay integration: it doesn't inform subsequent narration, world state, or thread context. The two narratives (seed opening + turn 1+ narrate) are disjoint.

**Note:** The `opening_narrative` is also NOT included in the Jinja template rendering for `narrate_user.j2` — the first turn the player actually plays uses the standard narrate prompt, not the seed opening. The seed opening exists only in `chronicle.md` and the initial HTML render.

---

## 2. Field Consumption Gaps

### 2.1 `pc.tagline`, `pc.bio`, `pc.stats` — Inconsistent Visibility

**Finding:** Seed generates full PC profile. Turn pipeline visibility is inconsistent:

| Field | Narrate | Scene Extract | State Extract | Storytell | Ruling |
|---|---|---|---|---|---|
| `pc.name` | Yes | Yes | Yes | Yes | Yes |
| `pc.tagline` | Via `_pc_header.j2` | **NO** | **NO** | **NO** | **NO** |
| `pc.bio` | Via `_pc_header.j2` | **NO** | **NO** | **NO** | **NO** |
| `pc.stats` | Via `_pc_header.j2` | **NO** | **NO** | **NO** | Yes (ruling) |
| `pc.conditions` | Yes | **NO** | Yes | Yes | Yes |
| `pc.allegiance` | Yes (factions) | **NO** | **NO** | **NO** | **NO** |

- `_pc_header.j2` renders: `name`, `tagline`, `bio`, `stats` — included in narrate via `{% include "_pc_header.j2" %}`
- Scene extractor (`extract_scene_user.j2`): only `pc_name` (string)
- State extractor (`extract_state_user.j2`): only `pc_name` (string) + conditions via `_conditions.j2`
- Storyteller (`storytell_user.j2`): only `pc_name` (string) + conditions/inventory via includes
- The PC's character definition (`tagline`, `bio`) is visible to the narrator but **completely invisible to all three extractors**

**Implication:** Extraction can change inventory, conditions, location, and threads — but the extractors have no idea who the PC is beyond a name string. If an extractor needed to reference PC identity (e.g., "does this action contradict the PC's established background?"), it has no data to do so.

---

### 2.2 `goal_context` — Accessible, Not Directed

**Finding:** `arc.goal_context` is seeded and exists in the state, but the pipeline does not explicitly pass it to prompts.

- `narrate_user.j2` passes `current_arc_ctx` (built in `narrate.py:60-82`) which includes `visible_goal` but **NOT** `goal_context`
- However, the **full `state` object** is also passed to the narrate template: `"state": state`
- So `state.arc.goal_context` is technically accessible in `narrate_user.j2` via the `state` variable
- But `_arc.j2` (the arc include) does NOT render `goal_context` — only `visible_goal` and `resolution`
- `thread_sanitizer.j2` does render `goal_context`: `{% if goal_context %}**Context:** {{ goal_context }}{% endif %}`
- `thread_sanitizer.py:143` reads `goal_context = arc.get("goal_context", "")`

**The "UI-only" claim** (docs: `goal_context` is "UI-only, not rendered in narrator prompts") is **technically accurate** for narrate/storytell — it goes through `state` rather than `current_arc_ctx`, and `_arc.j2` doesn't render it. But `thread_sanitizer` does read it directly. This is implicit architecture — not documented and fragile.

**Status:** Works but by accident. The channel is `state.arc.goal_context` rather than an explicit context variable. If the `state` object shape ever changes or the template is refactored, this breaks silently.

---

### 2.3 `world_state` Tier Metadata — Persisted, Not Distinctly Surfaced

**Finding:** Seed generates `scene.world_state` as `WorldStateFact` entries with `tier: "permanent"` (baseline facts) or `tier: "persistent"` (runtime additions). The `tier` field is persisted but the prompts only render the text.

- `_world_state.j2` renders tier as a prefix: `[permanent]`, `[persistent]`
- But no extraction prompt uses tier to make decisions
- `extract_state` and `extract_scene` don't include world_state at all
- Storytell has world_state as read-only context but doesn't act on tier

**Status:** Not a bug — tier is cosmetic/read-only guidance. But the system has no enforcement that permanent facts are never removed or overwritten.

---

### 2.4 `actions` — Seed Generates 4, Storyteller Generates 4, No Continuity

**Finding:** Seed generates 4 opening action choices. Storyteller generates 4 action choices every turn. There is no connection between them.

- Seed actions: stored in `__seed_meta__["actions"]`, displayed at game start via `_app_mod._dynamic_opening_actions`, then discarded
- Storyteller actions: `StorytellerResult.actions` returned every turn by the storytell extraction
- `state["pc"]["actions"]` is a rolling 10-entry window of storyteller actions (from `apply_delta()`)
- No turn prompt receives seed actions as context
- No turn prompt receives the seed's `outcome_summary`

**Status:** Seed actions and turn actions are entirely separate systems. Opening choices inform player intent but have no gameplay persistence. This may be intentional (seed actions are onboarding; turn actions are ongoing choices), but it's a divergence between out-of-band and in-band.

---

## 3. Code Duplication Patterns

### 3.1 Three Places Do Personality Resolution

**Finding:** NPC personality (archetype) resolution happens in three different places with different logic:

| Location | Trigger | Logic |
|---|---|---|
| `ccya/engine/seed.py:323-342` | Dynamic seed generation | `assign_personality()` for NPCs missing personality; `validate_and_resolve()` + fallback for NPCs with unknown id |
| `ccya/state/io.py:21-36` (`_assign_seed_personalities`) | Static seed loading | `assign_personality()` for NPCs missing valid personality in state |
| `ccya/server/routes.py:518-550` (`_resolve_npc_personalities`) | UI panel rendering | Resolves archetype id → label/traits for sidebar display; reads from `ARCHETYPES` registry; also resolves bond IDs via pack scenario |

**Duplication:** `assign_personality()` is called in two places (seed.py for dynamic, io.py for static). Both use the same keyword-scoring algorithm. `_resolve_npc_personalities()` in routes.py is the only one that also resolves `bond` IDs to human-readable descriptions from the pack scenario.

**Issue:** If the archetype assignment algorithm changes, it must be updated in two places. If a static seed has a personality id that passes validation but the UI resolution in routes.py resolves it differently, they could diverge.

**Proposed:** Consolidate into a single function. `assign_personality()` in `personality.py` should be the one place. `_resolve_npc_personalities()` should be refactored to use the same code path rather than duplicating the lookup.

---

### 3.2 Two Places Build NPC Roster

**Finding:** `build_npc_roster()` is called in multiple places with different parameters:

| Location | `personality_registry` | `slim` |
|---|---|---|
| `ccya/engine/narrate.py:274` | `None` | default (False) |
| `ccya/engine/extraction/scene.py:53` | `ARCHETYPES` | default (False) |
| `ccya/engine/extraction/storytell.py:63` | `ARCHETYPES` | `True` |
| `ccya/engine/ruling.py:216` | `ARCHETYPES` | default (False) |

**Finding:** `narrate.py` passes `personality_registry=None`, while all other callers pass `ARCHETYPES`. When `None`, `build_npc_roster()` falls back to reading personality from the NPC entry directly (which is how seed stores it). When `ARCHETYPES`, it enriches with label/traits from the registry.

**Not a bug** — this is intentional. Narrate gets the raw entry (seed-stored personality id), extractors get enriched archetype data. But it's not obvious why without tracing through the code.

---

### 3.3 Two Places Build Arc Context

**Finding:** Arc context is built twice with different structures:

| Location | Function | Includes |
|---|---|---|
| `ccya/engine/narrate.py:60-82` | `current_arc_ctx` building | `visible_goal`, `resolution`, `resolved_arcs`, `threads` (non-dormant), `completed_threads` (TTL-filtered) — **no `goal_context`** |
| `ccya/engine/extraction/storytell.py:37-40` | `arc` reading from state | **full `arc` object** including `goal_context`, all threads |

- Narrate's `current_arc_ctx` intentionally omits `goal_context`
- Storytell receives the full `arc` dict
- Both read from the same `state["arc"]`

**This is the architectural split** that causes `goal_context` to be "UI-only" for narration but visible to storytell. The two code paths should be documented together to make this intentional separation clear.

---

### 3.4 Seed vs. Default State Shape Divergence

**Finding:** The default state shape (`_default_state()` in `io.py`) and the `SeedState` model have overlapping but non-identical structures.

`SeedState` (`ccya/pack.py:59-72`):
```python
class SeedState(BaseModel):
    meta: dict[str, Any]
    pc: SeedPC
    location: SeedLocation
    inventory: list[InventoryItem]
    scene: SeedScene
    compendium: SeedCompendium
    arc: CampaignArc | None
```

Default state (`io.py:65-110`):
```python
{
    "schema_version": 1,
    "meta": {turn, setting_pack, model, session_name, compendium_touch_order, prior_history},
    "pc": {name, tagline, bio, stats, conditions, allegiance},  # + momentum in default
    "location": {id, name, description},
    "inventory": [],
    "arc": {visible_goal, goal_context, threads, completed_threads, resolution, last_thread_created_turn},
    "resolved_arcs": [],
    "scene": {tags, world_state, turn_entered, location_entered_turn},
    "compendium": {npcs: {}},
    "world": {factions: [], locations: []},  # NOTE: world key not in SeedState
}
```

**Gaps:**
1. Default state has `schema_version`, `world`, `resolved_arcs`, `scene.location_entered_turn`, `scene.turn_entered` — not in `SeedState`
2. Default state has `pc.momentum` — not in `SeedState`
3. `SeedState.scene` uses `SeedScene` model (which has `world_state: list[WorldStateFact | str]`), default state uses plain list
4. `SeedState` is not validated at load time for static seeds — it's `SeedState(**yaml.safe_load(...))` which may succeed with partial data

**Status:** Not a bug but a maintenance hazard. If the schema changes, both `_default_state()` and `SeedState` must be kept in sync manually.

---

## 4. Prompt Template Divergence

### 4.1 World State in Some Prompts, Not Others

| Prompt | Includes `world_state`? | Source |
|---|---|---|
| `narrate_user.j2` | Yes | `state.scene.world_state` via `_world_state.j2` |
| `extract_scene_user.j2` | **NO** | Only NPC roster + narration |
| `extract_state_user.j2` | **NO** | Only conditions, inventory, location, intent |
| `storytell_user.j2` | Yes | `scene.world_state` via `storytell.py:50` |

**Implication:** Scene extraction can introduce NPCs or change NPC presence without any world-state context. If a world fact (e.g., "border closure") is relevant to NPC behavior, the scene extractor doesn't know about it.

---

### 4.2 Location Description in Some Prompts, Not Others

| Prompt | Includes `location.description`? |
|---|---|
| `narrate_user.j2` | Yes (via `_location.j2`) |
| `extract_state_user.j2` | Yes |
| `extract_scene_user.j2` | **NO** |
| `storytell_user.j2` | Yes (via `_location.j2`) |

---

### 4.3 NPC Psychological Context (Fear/Motivation/Leverage)

| Prompt | Includes NPC fear/motivation/leverage? |
|---|---|
| `narrate_user.j2` | Yes (`_npc_roster.j2` renders all) |
| `extract_scene_user.j2` | No (only name/title/bio in compendium) |
| `extract_state_user.j2` | N/A |
| `storytell_user.j2` | Yes (`_npc_context.j2`) |

Scene extractor can update NPC entries but doesn't receive the psychological context that would help it do so consistently.

---

## 5. Fields That Flow One Way Only

### 5.1 Seed → State → Chronicle (One-Way, Never Consumed by Prompts)

| Field | Written at seed | Appears in turn prompts? |
|---|---|---|
| `opening_narrative` | Yes | **NO** |
| `outcome_summary` (seed version) | Yes | **NO** |
| `actions` (seed version) | Yes | **NO** |
| `__seed_meta__` | Yes | **NO** |
| `__seed_pools__` | Yes | **NO** |
| `meta._seed_type` | Yes | **NO** |
| `meta._pack_source` | Yes | **NO** |
| `meta._seed_soft_warnings` | Yes | **NO** |

**Observation:** These metadata fields are written and persisted but never consumed by the turn pipeline. They exist for debugging, auditing, and UI display. The seed system is genuinely "out-of-band" — its outputs enter the state file but have no ongoing influence on the turn pipeline.

This is the core architectural divergence: seed and turn engine share a state file but not a data model philosophy.

---

## 6. Specific Incompatibilities

### 6.1 Static Seed Still Uses `active` Field

**Finding:** The eval `seed_state.yaml` uses `active: false` on threads, while the `ArcThread` model uses `dormant`. The model validator coerces `active → dormant` (`models/state.py:40-46`), but the static seed YAML still has the old field.

**Status:** Technical debt. The coercion works but the seed files are stale.

---

### 6.2 Seed Envelope vs. Turn State — Different Arc Structures

**SeedEnvelope arc** (`pack.py:88`): `arc: CampaignArc | None`
**Turn state arc**: Full `CampaignArc` object

The `CampaignArc` model includes `goal_context`, `threads`, `completed_threads`, `resolution`, `last_thread_created_turn`. The seed generates all of these. But the turn engine's `current_arc_ctx` for narrate doesn't include `goal_context`.

---

### 6.3 `pc.momentum` — In Default State, Not In Seed Schema

**Finding:** `pc.momentum` is set in default state (`io.py:87`) but `SeedPC` has no `momentum` field. Seed always generates `pc.momentum: 0` implicitly (Pydantic default).

**Status:** Minor. Seed schema should arguably have `momentum: int = 0` explicitly.

---

## 7. Summary Table: Field Lifecycle

| Field | Seeded? | Consumed by prompts? | apply_delta preserves? | Notes |
|---|---|---|---|---|
| `meta.turn` | No (managed) | No | N/A | Managed by turn.py |
| `meta._seed_type` | Yes | No | No | Debug metadata only |
| `meta._pack_source` | Yes | No | No | Debug metadata only |
| `meta.session_name` | Yes | No | No | Display only |
| `meta.prior_history` | No (accumulated) | Narrate + storytell | N/A | Built up each turn |
| `world.factions` | **Never** | **NO** | N/A | Dead field — remove |
| `pc.name` | Yes | Yes (all) | No | Preserved |
| `pc.tagline` | Yes | Narrate only | No | Not in extractors |
| `pc.bio` | Yes | Narrate only | No | Not in extractors |
| `pc.stats` | Yes | Narrate + ruling | No | Not in extractors |
| `pc.conditions` | Yes | Narrate + extractors | Yes | Fully integrated |
| `pc.allegiance` | Yes | Narrate only | No | Faction display only |
| `location.*` | Yes | All three | Yes | Fully integrated |
| `inventory.*` | Yes | All three | Yes | Fully integrated |
| `arc.visible_goal` | Yes | Narrate + storytell | Yes | Fully integrated |
| `arc.goal_context` | Yes | **Thread sanitizer only** | Yes | Not in narrate/storytell prompts explicitly |
| `arc.threads` | Yes | Narrate + storytell | Yes | `scope`/`tags`/`last_seen_turn` dead |
| `scene.world_state` | Yes | Narrate + storytell | No (promoted via thread) | Tier metadata cosmetic |
| `scene.tags` | Yes | Ruling only | No | Not in extraction |
| `scene.scene_phase` | No (setdefault) | All | No (computed) | Defaults to SETUP |
| `compendium.npcs.*` | Yes | Narrate + storytell | Yes | `notes` not rendered |
| `opening_narrative` | Yes | **NO** | N/A | Chronicle only |
| `outcome_summary` (seed) | Yes | **NO** | N/A | Stored, unused |
| `actions` (seed) | Yes | **NO** | N/A | Turn 0 display only |
| `__seed_pools__` | Yes | **NO** | No | Debug/audit only |

---

## 8. Recommended Principles for Seed Revamp

These are principles the team should consider, not hard requirements:

### 8.1 Single Source of Truth for Shared Models

`CampaignArc`, `ArcThread`, `InventoryItem`, `Condition`, `WorldStateFact` exist in `ccya/models/state.py` and are used by both seed and turn engine. `SeedState` in `ccya/pack.py` is a parallel schema with similar but divergent shapes. 

**Principle:** The seed schema (`SeedState`, `SeedPC`, `SeedScene`, `SeedCompendium`) should derive from or validate against the same underlying models used by the turn engine. Currently `SeedPC` has no `momentum`; the default state has `momentum`. If a field is in the turn state model, it should be in the seed schema (even if seeded defaults are used).

### 8.2 Out-of-Band Should Feed In-Band

The seed produces `opening_narrative`, `outcome_summary`, and `actions` that are displayed once and discarded. The seed's narrative tone, arc framing, and opening situation have no ongoing influence on the turn pipeline.

**Principle:** If the seed opening establishes tone, situation pressure, or narrative framing that should persist into turn 1+, consider whether that data should influence the turn prompt context (e.g., as a `seed_narrative_tone` field that narrate could reference).

### 8.3 Deduplicate Personality Resolution

Three separate places do personality resolution. Consolidate into one function in `personality.py` that handles both assignment (keyword scoring) and resolution (id → label/traits). Routes panel helper should call the same function.

### 8.4 Remove Dead Fields

- `world.factions` — remove from default state and any seed schema references
- `ArcThread.scope` — remove or define its purpose
- `ArcThread.tags` — remove or define its purpose
- `ArcThread.last_seen_turn` — consolidate with `last_updated_turn`

### 8.5 Document the `goal_context` Channel

The `goal_context` path (`state.arc.goal_context` → `state` variable in template → `thread_sanitizer.py` direct read) is fragile. Either:
- Make it explicit in `current_arc_ctx` (add to `narrate.py:60-82`)
- Or document clearly that it's intentionally UI-only and must not be used in prompts

### 8.6 Static Seeds Should Use Current Schema

Update `packs/eval/seed_state.yaml` to use `dormant` instead of `active`. Remove stale fields that are no longer consumed.

---

## 9. Linked Document

Primary seed system findings: `docs/findings/seed-system.md`
