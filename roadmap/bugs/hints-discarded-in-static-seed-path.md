---
title: "Creation Hints Discarded in Static Seed Path"
status: done
urgency: 2
size: small
created: 2026-06-26
labels:
  - seed
  - routes
  - player-overrides
  - static-removal
---

## Problem

When a player provides creation hints (pc_hints, npc_hints, arc_hints, free_form) at character creation, the hints are **completely discarded** because the static seed path never uses the `overrides` object.

## Root Cause

In `routes.py:517-537`, the new_game route has two paths:

**Static seed path (hints provided):**
```python
if has_hints:
    # Hints provided — use static pack seed as fallback
    pack = _app_mod._active_pack
    if pack.seed is None:
        return HTMLResponse("...Provide no hints to generate a custom game.", status_code=400)
    seed = pack.seed.model_dump(mode="json")
    # overrides is NEVER used here
```

**Dynamic seed path (no hints):**
```python
else:
    # No hints — generate seed via LLM
    envelope, pool_selection = await generate_seed(
        _app_mod._active_pack,
        _app_mod.engine_config,
        template_dir=str(_app_mod.PROMPTS_DIR),
        overrides=overrides,  # overrides used here
    )
```

The `overrides` (containing the player's hints) is constructed on lines 493-499 but is **never passed** in the static seed path. The hints only reach the LLM when `has_hints` is False (i.e., the player submits an empty form with no hints).

This means:
- Player provides hints → static seed used → hints discarded
- Player provides no hints → dynamic seed → hints section is empty (overrides is None)

The completed plan `prompt/seed-hints-and-cleanup.md` strengthened the prompt language to make overrides "authoritative" but the static seed path never calls the LLM, so the prompt changes are irrelevant when hints are provided.

## Impact

- **Scenario-based packs** (all 5 default packs use `scenario.yaml`): When player provides hints, `pack.seed is None` → user sees 400 error: *"This pack has no static seed state. Provide no hints to generate a custom game."* The error message is backwards — it tells the player to NOT provide hints, when the hints should be honored.
- **Static seed packs** (eval harness only): Hints are silently discarded. The static seed is used as-is with no player customization.

## Fix

**Option A (Recommended):** When hints are provided but no static seed exists, fall through to dynamic generation instead of returning 400.

```python
if has_hints:
    pack = _app_mod._active_pack
    if pack.seed is not None:
        # Static seed path — inject hints into seed state for downstream use
        seed = pack.seed.model_dump(mode="json")
        # ... existing static seed logic ...
    else:
        # No static seed — fall through to dynamic generation with overrides
        envelope, pool_selection = await generate_seed(...)
        # ... existing dynamic seed logic ...
else:
    # No hints — generate seed via LLM (existing path)
    envelope, pool_selection = await generate_seed(...)
```

This requires merging the two `generate_seed` call sites. A cleaner refactor would be:

```python
if _app_mod._active_pack.seed is not None and not has_hints:
    # Static seed path — only when NO hints provided
    seed = _app_mod._active_pack.seed.model_dump(mode="json")
    # ... inject pc_stats, generate actions, apply to save dir ...
else:
    # Dynamic seed path — always uses overrides (empty or not)
    envelope, pool_selection = await generate_seed(
        _app_mod._active_pack,
        _app_mod.engine_config,
        template_dir=str(_app_mod.PROMPTS_DIR),
        overrides=overrides,
    )
    # ... apply to save dir ...
```

**Option B:** Always use dynamic seed when hints exist, regardless of static seed availability. Static seed becomes purely a fallback for packs that don't support scenario-based generation.

## Files to Touch

- `ccya/server/routes.py` — `new_game()` function (lines 517-543)
- No prompt changes needed — the prompt language is already correct, the issue is routing

## Validation

1. Start a game with hints on a scenario-based pack (e.g., allied-ww2) — should generate via LLM with hints honored, not return 400
2. Start a game without hints on a scenario-based pack — should still generate via LLM (unchanged behavior)
3. Start a game with hints on a static seed pack — should use static seed (unchanged, but consider injecting hints into seed state for downstream use)
