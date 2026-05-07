# Plan: Tear Out Static Pack Mode (Dead Code Removal)

## Status & Scope

`pack.py` defines `mode: Literal["static", "dynamic"]` and the entire `static` code path:
`seed_state.yaml`, `opening_scene.md`, hand-authored `SeedState` loading, and
`opening_actions` from the seed file. There are no `static` packs in active use — the
decision to move fully to `dynamic` generation has already been made. This is dead code.

Everything in `generate_seed()` (`ccya/engine/seed.py`) already hard-errors on
`mode != "dynamic"`. The static path in `load_pack()` is therefore unreachable in production.

---

## What Gets Removed

### `pack.py`

- `PackManifest.mode` field: change from `Literal["static", "dynamic"]` to a hard constant
  or remove the field entirely. If kept for forward-compat, default to `"dynamic"` and drop
  the `"static"` literal.
- `Pack.seed: SeedState | None` — remove field.
- `Pack.opening_text: str` — remove field.
- `Pack.opening_actions: list[str]` — remove field.
- `PackFiles.seed`, `PackFiles.opening` — remove both fields.
- `Pack._check_mode_files` model validator — simplify to only validate dynamic requirements;
  remove the `static` branch entirely.
- `load_pack()` — remove the `if manifest.mode == "static":` branch, the `seed_data` parsing,
  `opening_text` loading, and `opening_actions` extraction.
- `SeedState` docstring note about static pack hand-authoring — update to reflect dynamic-only.

### `ccya/engine/seed.py`

- `generate_seed()` guard at top: remove the `if pack.manifest.mode != "dynamic": raise
  ValueError(...)` — it becomes unnecessary. Replace with an `assert` or just trust the
  `Pack` model validator, which will have already enforced dynamic-only.

### `ccya/server/routes.py`

- The new-game handler that branches on `pack.manifest.mode == "static"` to load
  `pack.seed` + `pack.opening_text` directly vs. calling `generate_seed()`. Remove the
  `static` branch. The handler becomes: call `generate_seed()`, always.
- Remove any references to `pack.opening_actions` in the static branch.

### Pack data files

- Delete any `packs/*/seed_state.yaml` files that exist (they are the static seed format).
- Delete any `packs/*/opening_scene.md` files.
- Update `packs/*/pack.yaml` manifests to remove `mode: static` → set `mode: dynamic` if
  still present (there should be none left, but scan).

---

## Step-by-Step

### Step 1 — Grep for all static-mode references

```bash
grep -rn "static" ccya/ packs/ --include="*.py" --include="*.yaml" --include="*.md"
```

Catalogue every hit. Expected:
- `pack.py`: `Literal["static", "dynamic"]`, the validator, the load branch
- `routes.py`: the new-game branch
- `seed.py`: the guard
- Any `pack.yaml` manifest with `mode: static`
- Any `seed_state.yaml` or `opening_scene.md` in packs/

### Step 2 — Remove static fields from `PackManifest` and `Pack`

In `pack.py`:

```python
# Before
mode: Literal["static", "dynamic"]

# After — remove the field or hard-code
# Option A: remove field, imply dynamic everywhere
# Option B: keep for schema documentation, enforce dynamic
mode: Literal["dynamic"] = "dynamic"
```

Remove from `PackFiles`:
```python
# Remove:
seed: str | None = None
opening: str | None = None
```

Remove from `Pack`:
```python
# Remove:
seed: SeedState | None = None
opening_text: str = ""
opening_actions: list[str] = Field(default_factory=list)
```

Simplify `_check_mode_files`:
```python
@model_validator(mode="after")
def _check_mode_files(self) -> "Pack":
    if not self.world_text:
        raise ValueError("pack requires world_text (world.md)")
    if self.scenario is None:
        raise ValueError("pack requires scenario (scenario.yaml)")
    return self
```

### Step 3 — Simplify `load_pack()`

Remove the static branch entirely:

```python
# Remove this block:
if manifest.mode == "static":
    seed_data = _read_yaml(files.seed or "seed_state.yaml")
    opening_actions = seed_data.pop("opening_actions", [])
    if seed_data:
        seed = SeedState(**seed_data)
    opening_text = _read(files.opening or "opening_scene.md")
else:
    world_text = _read(files.world or "world.md")
    ...

# Becomes:
world_text = _read(files.world or "world.md")
scenario_data = _read_yaml(files.scenario or "scenario.yaml")
if scenario_data:
    scenario = ScenarioBrief(**scenario_data)
```

### Step 4 — Simplify `routes.py` new-game handler

Remove the `if pack.manifest.mode == "static":` branch. The handler always calls
`generate_seed()`. Remove any references to `pack.seed`, `pack.opening_text`,
`pack.opening_actions`.

### Step 5 — Clean up `seed.py`

Remove the guard:
```python
# Remove:
if pack.manifest.mode != "dynamic":
    raise ValueError(
        f"generate_seed() requires a dynamic pack, got mode={pack.manifest.mode!r}"
    )
```

The `Pack` model validator now enforces `mode: Literal["dynamic"]` at load time.

### Step 6 — Delete dead pack data files

```bash
find packs/ -name "seed_state.yaml" -delete
find packs/ -name "opening_scene.md" -delete
```

Scan `packs/*/pack.yaml` for `mode: static` entries and either update them to `mode:
dynamic` (with correct `world.md` + `scenario.yaml` added) or delete the pack entirely
if it has no dynamic equivalent.

### Step 7 — Consider `SeedState` retention

`SeedState` is still used as the validated schema for the dynamic seed output (the LLM
generates JSON that is parsed as `SeedState`). **Do not delete `SeedState`**. Only remove
the docstring note about hand-authored static packs and update the `inventory` field comment.

### Step 8 — Tests

- Confirm `load_pack()` raises `ValidationError` (not `ValueError`) if `pack.yaml` has
  `mode: static` (it will, because `Literal["dynamic"]` rejects it at parse time).
- Confirm `load_pack()` raises on missing `world.md` or `scenario.yaml` (existing behaviour,
  now the only path).
- Confirm `generate_seed()` no longer has the guard — call it with a valid dynamic pack,
  assert it returns a `SeedEnvelope`.
- Remove any existing test cases that test static pack loading behaviour.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| A pack.yaml somewhere still has `mode: static` | Low | Step 1 grep catches it |
| `SeedState` accidentally deleted (still needed for dynamic seeds) | Low | Explicitly called out in Step 7 |
| `opening_actions` referenced elsewhere (e.g., UI) | Low | Step 1 grep; `Pack.opening_actions` only fed the static new-game branch |
| `parse_world_facts()` becomes orphaned | Low | It's used in `generate_seed()` as a legacy fallback for packs without `baseline_facts` — keep it until all packs have `baseline_facts` populated |

---

## Files Touched

| File | Change |
|---|---|
| `ccya/pack.py` | Remove static fields, simplify validator, simplify `load_pack()` |
| `ccya/engine/seed.py` | Remove mode guard |
| `ccya/server/routes.py` | Remove static new-game branch |
| `packs/*/seed_state.yaml` | Delete |
| `packs/*/opening_scene.md` | Delete |
| `packs/*/pack.yaml` | Audit; update or delete static entries |
| `tests/test_pack.py` (or equivalent) | Remove static-mode test cases |
