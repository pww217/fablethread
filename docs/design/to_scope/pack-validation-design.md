# Pack Validation Design

> **Status:** implemented
> **Related designs:**
> - [Pack Parity](./to_scope/pack-parity-redesign.md) — **depends on this.** Pack parity requires a single validation gate that both YAML authoring and LLM generation paths must pass.
> - [Dynamic Factions](./to_scope/dynamic-factions-redesign.md) — **depends on this.** Dynamic factions need the same schema contracts as hardcoded factions.
> - [World Creator Seed Pack](./to_scope/world-creator-seed-pack.md) — **depends on this.** User-authored packs need the same validation as auto-generated ones.
> - [Seed Worldbuilding Redesign](./complete/03-seed-worldbuilding-redesign.md) — ScenarioBrief schema already defined; validation layer is the missing enforcement.
> - [Primitives](./complete/01-primitives.md) — pc_situation_schema keys are the only pack-specific field that should vary between packs.
>
> **Note:** This is a foundational design. All subsequent pack-related designs depend on it. Write plans for the other three only after this one is implemented.

## Problem Statement

Packs enter the system through two independent paths:

1. **YAML authoring path** — Pack authors write `pack.yaml` and `scenario.yaml` by hand, place them in `packs/default/<slug>/`, and the engine loads them via `load_pack()`.
2. **LLM generation path** — Players submit a world brief, the LLM generates `scenario.yaml`, and the engine writes both `pack.yaml` and `scenario.yaml` to `packs/generated/<uuid>/`.

Both paths should produce packs that play identically at runtime. But **neither validates against the same schema at load time.** The current state:

- `PackManifest` uses `model_config = {"extra": "ignore"}` — unknown fields in `pack.yaml` are silently dropped. Typos like `descrition` instead of `description` cause silent data loss.
- Several fields already exist in every `pack.yaml` (`description`, `version`, `mode`, `files`) but are **not declared in the `PackManifest` model**. They're silently ignored.
- Scenario pool fields (`situation_archetypes`, `arc_categories`, `npc_bonds`, etc.) are never validated for: duplicate IDs, or broken `incompatible_with` references.
- `list_packs()` silently skips directories that don't have a valid `pack.yaml` — no diagnostic is produced.
- `load_pack()` raises `FileNotFoundError` if `pack.yaml` is missing, but does not validate structural correctness.

The result: a pack can be malformed in ways that don't crash at load time but cause silent failures later — unknown fields indicate authoring errors that should be caught immediately, duplicate IDs cause pool selection bugs, broken references cause seed crashes.

## Design Goals

1. **One golden schema.** Every pack — default, custom, or generated — must conform to the same schema. No exceptions. The only field that legitimately differs between packs is `pc_situation_schema` keys (pack-specific situational axes). Everything else is structural and uniform.
2. **One validation function.** A single `validate_pack(pack: Pack, pack_id: str | None)` function that both paths call. No separate validation for "default" vs "generated" vs "custom" packs.
3. **Fail fast.** Validation runs at `load_pack()` time. Bad packs crash the game start or the new-game flow with clear, actionable error messages that identify the problematic field. No silent degradation.
4. **Schema discipline.** `PackManifest` uses `extra: forbid` so unknown fields trigger immediate errors instead of silent data loss. All fields that exist in pack YAML files must be declared in the model.
5. **Structural validation only.** Validation checks that the pack conforms to the schema — correct fields, correct types, valid references. It does not check content quality (well-written descriptions, interesting factions). That's eval territory.

## Current State: Undeclared Fields in PackManifest

**These fields were added to PackManifest in F-15 (pack-validation-design implemented):**

| Field | Type | Present in all packs? | Current behavior |
|---|---|---|---|
| `description` | str | Yes | **Now declared** in PackManifest |
| `files` | PackFiles | Yes | **Now declared** as `PackFiles` |

**Previously silent, now enforced:**
- `extra: ignore` → `extra: forbid` — unknown fields raise Pydantic validation errors
- `baseline_facts` **removed** from PackManifest (replaced by `ScenarioBrief.world_facts`)

**Removed in pack-parity redesign:**
- `version` — unused by engine, no pack update paths needed
- `mode` — always `"dynamic"`, dead field (F-15 added it but it serves no purpose)

## Proposed Schema Changes

### PackManifest

```python
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
```

Changes from original (baseline_facts removed in F-15):
- `extra: ignore` → `extra: forbid` — unknown fields raise validation errors
- Add `description: str = ""` — declared, not silently dropped
- Add `files: PackFiles` — declared, not silently dropped
- **Remove `baseline_facts`** — replaced by `ScenarioBrief.world_facts` (injected at seed time, not pack time)

**Removed in pack-parity redesign:**
- `version` — unused by engine, no pack update paths needed
- `mode` — always `"dynamic"`, dead field (F-15 added it but it serves no purpose)

### ScenarioBrief

No schema changes needed. ScenarioBrief already declares all fields used in scenario.yaml. The validation layer enforces structural correctness (ID uniqueness, reference validity). All ScenarioBrief fields are mandatory structural elements — every pack must have them all.

## Validation Function

### `validate_pack(pack: Pack, pack_id: str | None = None) -> None`

Called at the end of `load_pack()`, after all files are assembled into a `Pack` object. Raises `ValueError` with a single aggregated message listing every problem found. Each problem identifies the pack, the field path, and what's wrong.

**Checks:**

1. **Manifest structural:**
    - `manifest.id` is non-empty
    - `manifest.name` is non-empty (after stripping)

2. **Dynamic mode requirements:**
    - If `mode == "dynamic"`, `pack.scenario` must not be `None`

3. **Pool entry structural integrity (all pool fields in ScenarioBrief):**
    - Each pool's entries must have unique IDs
    - Each pool's `incompatible_with` references must point to valid IDs within the same pool
    - Each pool must have at least 1 entry (prevents `_select_from_pool()` ValueError at seed time)
    - Pool fields checked: `situation_archetypes`, `arc_categories`, `character_dynamics`, `moral_pressures`, `npc_bonds`

4. **Faction uniqueness:**
    - If factions exist, their IDs must be unique

5. **PC situation schema:**
    - If `pc_situation_schema` exists, keys must be unique
    - **This is the only pack-specific field that varies.** No minimum count requirement — a pack may legitimately have 0–5 keys.

6. **Scene detail bundles:**
    - If `scene_detail_bundles` exist, their IDs must be unique

### `_validate_pool_entries(entries: list[PoolEntry], pool_name: str) -> list[str]`

Helper for pool validation. Checks:
- Unique IDs
- All `incompatible_with` references resolve to valid IDs in the same pool

Returns the list of IDs for caller use (e.g., faction uniqueness check).

### Static Validation Script

A script (`scripts/validate_packs.py`) that loads every pack in `packs/` and runs `validate_pack()` on each. Used for CI/pre-commit checks and manual verification. Exits 1 if any pack fails validation.

## When Validation Runs

### At load time (mandatory)

`load_pack()` calls `validate_pack()` as its final step. This catches:
- Bad packs at server startup (game fails to start with clear error listing all problematic fields)
- Bad packs at new-game time (clear error instead of cryptic seed crash)
- Bad generated packs if the LLM produces malformed output (generation fails with clear error instead of writing broken files)

### Static validation script (recommended)

`scripts/validate_packs.py` iterates all packs in `packs/default/`, `packs/custom/`, and `packs/generated/`, loads each via `load_pack()`, and validates. Used for:
- Pre-commit hooks (optional)
- CI checks (recommended)
- Manual verification during pack authoring

### list_packs() behavior change

Currently `list_packs()` silently skips directories without valid `pack.yaml`. After validation is added:
- `list_packs()` should log a warning for directories that fail validation (not crash — the pack picker should still render, just mark the pack as invalid)
- This allows the UI to show "this pack has issues" rather than silently hiding it

## Validation Error Messages

Errors should identify the problematic field and what's wrong. Each error identifies the pack, the field path, and the specific problem:

```
Pack 'my-custom-world': scenario.npc_bonds pool entry 'saved_from_infected' references non-existent incompatible_with ID 'nonexistent_id'
Pack 'my-custom-world': scenario.factions has duplicate IDs
Pack 'my-custom-world': scenario.pc_situation_schema has duplicate keys
Pack 'my-custom-world': manifest.name is empty
Pack 'my-custom-world': unknown field 'descrition' in pack.yaml
Pack 'my-custom-world': scenario.situation_archetypes pool must have at least 1 entry (has 0)
```

## Relationship to Other Designs

### Pack Parity

Pack parity's goal is that generated packs and default packs behave identically at runtime. This validation design is the **foundation** for parity: if both paths must pass the same `validate_pack()` gate, parity is enforced by construction. The parity design can then focus on content quality (are the generated pools as rich as hand-authored ones?) rather than structural correctness.

**Note:** `mode` and `version` were removed from PackManifest in the pack-parity redesign (both are unused/dead fields).

### Dynamic Factions

Dynamic factions need to generate factions that conform to the same `Faction` schema as hardcoded factions. Validation already checks faction ID uniqueness and presence in dynamic mode. The dynamic factions design only needs to ensure the LLM generates factions that pass these same checks.

### World Creator Seed Pack

User-authored packs need the same validation as auto-generated ones. This design provides that single validation gate. The world creator seed pack design can focus on the authoring UX (how users write packs) without worrying about validation — it's handled by `validate_pack()`.

## Non-Goals

- **Content quality.** Validation checks structure, not whether pool descriptions are well-written or factions are interesting. That's eval territory.
- **Backward compatibility.** No migration shims for old pack formats. Old packs that don't conform are simply invalid.
- **Per-field semantic validation.** No checking that `baseline_facts` are actually true for the genre, or that `tone_tags` are valid. Those are semantic/content concerns, not structural ones.
- **Validation during generation.** The LLM generation path should write files and let `load_pack()` + `validate_pack()` catch errors. No inline validation during generation — it's redundant and complicates the generation flow.
- **Custom validation hooks.** No plugin system for pack authors to add custom validation. If a pack needs custom validation, the core validation should be extended.
- **Pool emptiness.** validate_pack() now checks that all archetype pools have at least 1 entry. Empty pools cause `_select_from_pool()` ValueError at seed time, so they're caught at pack load time instead.

## Implementation Order

1. **Add undeclared fields to PackManifest.** Add `description`, `files` to the model. Change `extra: ignore` to `extra: forbid`.
2. **Write `validate_pack()` and `_validate_pool_entries()`.** All the structural checks described above.
3. **Call `validate_pack()` at the end of `load_pack()`.** This makes validation mandatory for every pack load.
4. **Write `scripts/validate_packs.py`.** Static validation script that loads all packs and validates them.
5. **Update `list_packs()` to log warnings for invalid packs.** Don't crash the pack picker — log and mark as invalid.
6. **Update the three related design docs.** Cross-reference this design and align their plans with the single-validation-gate approach.
