# Plan 4: Code Quality Consolidation (Low-Risk Cleanups)

## Status
`completed`

## Phases

1 phase: four independent low-risk cleanups — dedup `_resolve_pack_dir`, hoist duplicate `_label` defs, extract inputs_snapshot/connectors loop helper, consolidate new_game/reroll seed→init pattern.

## Issue

Four separate code quality issues detected during triage review:

1. **`_resolve_pack_dir` duplicated** in `routes.py:360-375` and `pack.py:253-276`. The routes.py version even has a docstring saying "mirrors pack._resolve_pack_dir for server-side use" — confirming it's intentional duplication, not an import oversight.
2. **`_label` defined twice** inside tv.py at different scopes (lines 80-85 and lines 222-227). 90% identical logic with subtly different fallback behavior: first returns truncated first-value string; second returns empty string.
3. **inputs_snapshot loop duplicates connectors loop** in tv.py — both iterate `_STREAMS` + `sd.inputs` with identical data-fetching/formatting logic (lines 465-501 vs lines 505-531). ~12 lines of raw extraction and formatting duplicated.
4. **new_game / new_game_reroll duplicate seed→init pattern** in routes.py — dynamic pack paths are byte-for-byte identical (`routes.py:265-270` == `291-297`). Static path is similar minus one meta key.

## Solution

Phase 4 consolidates all four cleanups into a single low-risk pass. Each change is independent and can be verified in isolation; they're grouped here because they touch the same two files (routes.py, tv.py) reducing file churn per phase.

## Firm decisions

1. `_resolve_pack_dir`: Import from `pack` module rather than extracting to shared utility. The function already exists as a public helper in pack.py with full docstring and tests; importing is simpler than creating another layer.
2. Duplicate `_label`: Hoist to one module-level `_tv_label()` function in tv.py that uses the more permissive fallback (truncated first-value string) since it's used for display purposes where empty strings are less informative.
3. inputs_snapshot/connectors: Extract a private helper `_extract_stream_output_lines(raw_out, inp_sd)` that returns `seg_lines` — called once by both loops. The connector metadata wrapping and raw snapshot storage remain separate post-processing steps.
4. new_game/reroll seed→init: Extract to `_apply_seed_to_save_dir(seed_dict, opening_narrative=None, actions=None)`. Both static and dynamic pack paths use this helper; the only difference is whether opening/actions are set from envelope vs empty strings.

## Non-goals

- Does not refactor any pipeline logic or change API contracts.
- Does not modify Jinja templates or model definitions.
- Does not add new configuration options.
- Does not touch tests (tests temporarily removed during refactor per AGENTS.md).

## Risks, Ambiguities, and Blockers

**Risk:** Importing `_resolve_pack_dir` from pack into routes.py creates a circular import if pack imports anything from server. Verification: `pack.py` only depends on models.py, config.py, and standard library — no server dependencies. Safe to import.

**Ambiguity:** For the inputs_snapshot/connectors extraction, should the helper also return metadata (upstream_status) or just raw lines? Just raw lines — upstream status is connector-specific context not needed for inputs snapshot.

**Blocker:** None. All four changes are self-contained within routes.py and tv.py with no cross-module impacts.

---

## Implementation: Code Quality Consolidation

### Context files to load
- `ccya/server/routes.py` — `_resolve_pack_dir()` at lines 360-375; seed→init pattern in new_game (lines 245-270) and reroll (lines 286-297)
- `ccya/pack.py` — original `_resolve_pack_dir()` at lines 253-276
- `ccya/server/tv.py` — duplicate `_label` defs at lines 80-85, 222-227; inputs_snapshot/connectors loops at lines 465-531

### Detailed steps

#### Step 4.1 — Import _resolve_pack_dir from pack in routes.py

**File:** `ccya/server/routes.py`

**What:** Remove the local `_resolve_pack_dir()` function (lines 360-375) and add an import at the top of the file:
```python
from ccya.pack import list_packs, load_pack, _resolve_pack_dir
```
Update all call sites in routes.py that use `routes._resolve_pack_dir(...)` to just `_resolve_pack_dir(...)`.

**Why:** The function already exists as a public helper in pack.py with full docstring explaining accepted formats. Duplicating it violates "one source of truth" and means any future fix must be applied twice. Importing is simpler than creating another shared utility layer.

**Validation:** Run `make check` — verify no import errors or type mismatches. The function signature `(pack_id: str, packs_dir: Path) -> Path` matches exactly between both copies.

#### Step 4.2 — Hoist duplicate _label defs to module-level helper in tv.py

**File:** `ccya/server/tv.py`

**What:** Create one module-level `_tv_label(x: dict[str, Any]) -> str` function that implements the more permissive fallback logic (truncated first-value string). Replace both nested definitions with calls to this single function.

The unified implementation uses keys `("id", "name", "text", "label")`, returns `val[:60]` for matching key, and falls back to `str(list(x.values())[0])[:60] if x else ""`. This matches the first definition's behavior which is more informative than empty string.

**Why:** Two nested defs with subtly different fallbacks create maintenance confusion — callers can't predict whether a missing label returns truncated text or empty string. One function eliminates this ambiguity and makes any behavioral difference explicit rather than accidental.

**Validation:** Run `make check`. No interface changes — `_label` is private to tv.py. The unified implementation uses the first definition's fallback which produces more informative output in edge cases.

#### Step 4.3 — Extract inputs_snapshot/connectors loop helper in tv.py

**File:** `ccya/server/tv.py`

**What:** Create a private function `_extract_stream_output_lines(raw_out: Any, inp_sd) -> list[dict[str, Any]]` that encapsulates the raw output extraction and formatting logic shared between connectors (lines 478-491) and inputs_snapshot (lines 517-529).

The helper takes `raw_out` and an input stream descriptor (`inp_sd`) and returns formatted `seg_lines`. Both loops call this once instead of duplicating the if/elif chain for text output, JSON string parsing, dict rendering, and fallback.

After extraction:
- Connectors loop wraps results in richer dicts with "from", "label", "anchor", "upstream_status" fields (unchanged post-extraction)
- Inputs_snapshot stores raw `seg_lines` keyed by inp_key (unchanged post-extraction)

**Why:** ~12 lines of data-fetching and formatting logic duplicated between two loops. Extracting into a helper eliminates duplication while keeping connector metadata wrapping and raw snapshot storage as separate concerns.

**Validation:** Run `make check`. No behavioral changes — same output produced via extracted function. The if/elif chain for text/JSON/dict/fallback is preserved inside the helper exactly once.

#### Step 4.4 — Consolidate new_game/reroll seed→init pattern in routes.py

**File:** `ccya/server/routes.py`

**What:** Extract a private helper `_apply_seed_to_save_dir(seed_dict: dict, opening_narrative: str | None = None, actions: list[str] | None = None) -> None` that encapsulates the common seed→init flow. The helper does:
```python
def _apply_seed_to_save_dir(
    seed_dict: dict[str, Any],
    opening_narrative: str | None = None,
    actions: list[str] | None = None,
) -> None:
    """Apply generated/loaded seed to save directory and set dynamic pack variables."""
    seed_dict.setdefault("meta", {})["model"] = _app_mod.config["llm"]["model"]
    init_save_dir(_app_mod.SAVE_DIR, seed_dict)
    if opening_narrative is not None:
        _app_mod._dynamic_opening = opening_narrative
    if actions is not None:
        _app_mod._dynamic_opening_actions = actions
```

Replace the duplicated blocks in `new_game` (lines 265-270) and `reroll` (lines 291-297) with calls to this helper. The static pack path already uses empty strings for opening/actions — it can pass explicit `""` / `[]` or use defaults.

**Why:** Dynamic pack paths in new_game and reroll are byte-for-byte identical (`routes.py:265-270` == `291-297`). Extracting eliminates duplication and makes the seed→init flow a single source of truth that can be modified once if the pattern changes.

**Validation:** Run `make check`. No behavioral changes — same operations performed via extracted function. Static pack path behavior unchanged (opening/actions set to empty strings). Dynamic paths use envelope values as before.

### Tests to write or update

No automated tests needed per AGENTS.md (tests temporarily removed during refactor). Manual verification:
- Import `_resolve_pack_dir` from routes context — verify it resolves packs correctly
- Run turn viewer rendering with sample event data — confirm _label and stream output extraction produce same visual output as before
- Create new game via static pack path and dynamic pack path — verify seed applied identically

### REPOMAP updates required

None. All changes are internal refactors within existing modules:
- `ccya/server/routes.py`: `_resolve_pack_dir` removed, replaced by import; helper functions added privately
- `ccya/server/tv.py`: duplicate defs consolidated into module-level helpers
No public API or model shape changes.
