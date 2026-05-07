# Plan: Tear Out `present_npcs` Legacy Coupling

## Status & Scope

`present_npcs` is alive and load-bearing in several spots — but the *write path* is fully
migrated to `npc_add / npc_remove / npc_update` deltas. The remaining surface area is:

1. **A dangerous fallback** in `apply_delta` that re-populates `present_npcs` from the raw
   compendium when no NPC delta arrives and `present_npcs` is empty.
2. **A location-change hard-reset** that zeroes `present_npcs` (and `recently_left`) directly
   in `apply_delta`.
3. **`SeedState.scene`** (`pack.py`) carries no `present_npcs` field, so seeds are clean —
   but the fallback in `apply_delta` will still fan-in every compendium NPC on the very first
   turn if the LLM omits `npc_add`.
4. **Read surfaces** (`server/routes.py`, `server/tv.py`, `server/panels.py`) that render
   `scene.present_npcs` for the UI — those are correct and stay.

The goal is to remove all *implicit write paths* that aren't explicit delta operations, while
leaving the `scene.present_npcs` list itself intact as a pure read target.

---

## Step-by-Step

### Step 1 — Audit & grep for all write-side touches

Search for every site that writes to `present_npcs` outside of the delta path:

```
grep -rn "present_npcs" ccya/
```

Expected findings:
- `ccya/state/delta.py` — the fallback block and the `location_change` reset (see below)
- `ccya/server/routes.py` — read-only rendering (no action)
- `ccya/server/tv.py`, `ccya/server/panels.py` — read-only rendering (no action)
- Any seed YAML files under `packs/` — check if any hand-author `present_npcs`; delete those
  keys if found (they're ignored on load but cause confusion)

### Step 2 — Remove the compendium-fallback block in `apply_delta`

**Location:** `ccya/state/delta.py`, the `else:` branch of `if delta.npc_add or
delta.npc_remove or delta.npc_update:`.

Current behaviour: if no NPC deltas arrive and `present_npcs` is empty, the engine fans in
every named NPC in the compendium up to `NPC_SCENE_CAP`. This was the bridge from the old
`present_npcs`-as-truth model to the new delta model. It is now a footgun — it silently
re-populates the scene list when the LLM forgets an `npc_add`.

**Change:** replace the entire `else:` block with:

```python
else:
    new_present_ids = old_present_ids
```

The `scene.present_npcs` list persists as-is when the LLM sends no NPC delta. If the scene
is legitimately empty, the LLM must emit an `npc_add` to populate it. No more silent
compendium fan-in.

### Step 3 — Harden the `location_change` reset

**Location:** same file, the `if delta.location_change:` branch.

Current code zeroes `present_npcs` and `recently_left` inline:
```python
state.setdefault("scene", {})["present_npcs"] = []
state.setdefault("scene", {})["recently_left"] = []
state.setdefault("scene", {})["recently_left_turns"] = 0
```

This is correct behaviour — location change should clear the scene. Keep these lines. But
add a guard: if `delta.npc_add` is non-empty, those adds will be applied immediately after
in the NPC delta block, which is already how it works. No code change needed here beyond
confirming the ordering is correct in the flow (it is — location_change fires before the NPC
delta block).

**Optional hardening:** add a log line so it's observable:
```python
_log.debug(
    "location_change \u2192 present_npcs cleared (new location: %s)",
    delta.location_change.id,
)
```

### Step 4 — Add a prompt-layer assertion (system prompt / extract instructions)

The LLM must always emit `npc_add` entries when moving to a scene that has NPCs present.
Add an explicit rule to the extract system prompt (likely `ccya/prompts/extract_system.j2`
or equivalent):

> When `location_change` is set, you MUST emit `npc_add` for every NPC who should be present
> in the new location. `present_npcs` is NOT carried over automatically on a scene change.

Also add a soft-check in `reconcile_delta` (already exists in `ccya/state/delta.py`):
```python
# Warn if location_change with no npc_add — likely LLM omission
if delta.location_change and not delta.npc_add:
    warnings.append(
        "location_change with no npc_add — scene will be empty unless intentional"
    )
```

### Step 5 — Update `SeedState` / seed generation

`SeedState.scene` (`pack.py`) already does not include `present_npcs`. Confirm `generate_seed`
in `ccya/engine/seed.py` also never writes `present_npcs` to the seed envelope — it doesn't
(the seed starts with an empty compendium and no NPC state). No change needed, but add a
comment:

```python
# SeedState intentionally has no present_npcs — first-turn npc_add from the LLM
# (or an initial delta injected by the engine) populates scene.present_npcs.
```

### Step 6 — Tests

- Unit test: `apply_delta` with `npc_add/remove/update` empty and an already-populated
  `present_npcs` → list is preserved unchanged (verifies no silent fan-in).
- Unit test: `apply_delta` with `npc_add/remove/update` empty and an **empty** `present_npcs`
  → list stays empty (the fallback is gone).
- Unit test: `apply_delta` with `location_change` set → `present_npcs` is cleared, then
  any `npc_add` in the same delta populates it correctly.
- Integration smoke: run a new-game + first turn; confirm `present_npcs` is populated only
  if the LLM emits `npc_add`.

### Step 7 — Dead-code cleanup (post-test)

After tests pass:
- Delete the now-empty `else:` block comment if it was only there explaining the fallback.
- Remove any `# Legacy: fallback...` comments that were left as breadcrumbs.
- Run `grep -rn "fallback_present"` — that local variable only existed in the removed block;
  confirm no references remain.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| LLM forgets `npc_add` after location change | Medium | `reconcile_delta` warning + prompt rule (Step 4) |
| Existing saves with empty `present_npcs` in mid-game | Low | They'll stay empty until LLM emits `npc_add`; acceptable |
| Regression in scene NPCs on first turn of new game | Low | Seed has no compendium; first LLM turn must emit `npc_add` (prompt controls this) |

---

## Files Touched

| File | Change |
|---|---|
| `ccya/state/delta.py` | Remove fallback block; add debug log; add reconcile warning |
| `ccya/prompts/extract_system.j2` (or equivalent) | Add `npc_add` rule for location_change |
| `packs/*/seed_state.yaml` (if any contain `present_npcs`) | Delete those keys |
| `tests/test_delta.py` (or equivalent) | Add cases from Step 6 |
