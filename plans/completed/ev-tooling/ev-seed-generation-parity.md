# ev.py seed generation parity

## Purpose

Align ev.py's new-session seed generation with the server's `POST /new-game` logic so that `--pack` on a scenario-based pack always calls `generate_seed()`.

## Problem Statement

The server's decision tree (routes.py:428-448):
1. Pack has a scenario → call `generate_seed()` (LLM generates opening + initial state)
2. No scenario → use static seed (or error if none)

ev.py's decision tree (play.py, duplicated in 3 callers):
1. Pack has a static seed → use it, skip `generate_seed()`
2. No static seed → check for scenario → call `generate_seed()` or empty default

The priority is inverted. Today this causes no behavioral difference — no pack has both `seed_state.yaml` and `scenario.yaml` (eval has only a seed; the 6 default packs have only a scenario). But the logic is wrong on principle and would silently pick the wrong path if a future pack had both.

Additionally, the seed-generation flow is copy-pasted identically in 3 places (single-turn, interactive, llm sessions), each doing a partial re-load of the pack.

## Constraints

- `generate_seed()` raises `ValueError` if called on a static-only pack (`pack.seed is not None and pack.scenario is None`). The guard must remain.
- `--save-dir` (continuing an existing game) must NOT trigger seed generation.
- No functional change to existing packs — eval uses static seed, zombie-survival uses `generate_seed()` — same as before.

## Non-goals

- No `reroll` equivalent (explicitly excluded by user).
- No `--hints`/`--overrides` support in ev.py's seed gen (out of scope).
- No changes to how packs are structured or loaded.
- No changes to server-side seed generation.

## Solution

Replace the 3 duplicated blocks with a single `_ensure_seed_generated()` helper. Change the condition from "no static seed" to "pack has scenario" — matching the server's logic. The helper returns the loaded state dict (or loads it if no generation was needed).

## Firm decisions

1. The condition for calling `generate_seed()` is `pack.scenario is not None` — same as the server's no-hints path.
2. The guard in `generate_seed()` (rejects static-only packs) is correct and stays.
3. `_create_play_session()` still creates the directory + symlink but no longer pre-writes `init_save_dir()` for scenario packs (that write is immediately overwritten by `generate_seed()`).

## Risks, Ambiguities, and Blockers

None. All current packs produce the same behavior; the change is purely a correctness fix for the decision logic.

## Status

`completed`

## Phases

Single phase.

## Implementation — Phase 1: Seed generation parity

### Context files to load

- `ccya/ev/play.py` — the target
- `ccya/engine/seed.py` — `generate_seed()` signature and guard
- `ccya/server/routes.py:64-101` — `_apply_seed_to_save_dir()` for reference (mirror the meta injection pattern)
- `ccya/state/io.py` — `init_save_dir()`, `load_state()`, `_default_state()`
- `ccya/pack.py` — `Pack` model (seed, scenario fields)

### Detailed steps

#### Step 1.1 — Extract `_ensure_seed_generated()` helper

**File:** `ccya/ev/play.py` (after line 288, before `_create_play_session`)

**What:** Add a new function that encapsulates the seed-generation decision logic currently duplicated. Signature:

```python
def _ensure_seed_generated(
    save_dir: Path,
    pack_id: str | None,
    config: EngineConfig,
    seed_dict: dict[str, Any] | None,
    opening_scene: str | None,
) -> dict[str, Any]:
```

Returns the loaded state dict after generation (or after loading the pre-existing state if no generation was needed).

**Logic:**
1. If `pack_id` is None → return `load_state(save_dir)` (no generation, no scenario)
2. Load the pack fresh via `load_pack(pack_id, Path("packs"))`
3. If `pack.scenario is not None`:
   - Call `generate_seed(pack, config, template_dir=...)`
   - Unpack `SeedEnvelope` into `seed_dict` dict
   - Inject meta: `setting_pack`, `_seed_type`, `_pack_source`, `__seed_meta__` (opening_narrative, actions, outcome_summary), `__seed_pools__`
   - Call `init_save_dir(save_dir, seed_dict)` to overwrite the directory
   - Return `load_state(save_dir)`
4. Else (no scenario):
   - If `seed_dict` is not None (static seed exists) → seed was already written by `_create_play_session()`, return `load_state(save_dir)`
   - Else → `_default_state()` was written by `_create_play_session()`, return `load_state(save_dir)`

**Why:** Centralizes the decision logic, removes 3 copies of the same ~30-line block, makes the condition match the server.

**Validation:** `.venv/bin/python -c "from ccya.ev.play import _ensure_seed_generated; print('imported')"`

#### Step 1.2 — Simplify `_create_play_session()` for scenario packs

**File:** `ccya/ev/play.py`, function `_create_play_session()` (line 260)

**What:** Skip `init_save_dir()` when the pack has a scenario — `_ensure_seed_generated()` will call it with the generated seed. Only write state for packs without a scenario.

Change the body to:

```python
def _create_play_session(pack: str | None = None, packs_dir: Path | None = None) -> Path:
    now = datetime.now()
    rand_suffix = uuid.uuid4().hex[:6]
    session_name = now.strftime("%Y%m%d_%H%M%S_") + rand_suffix
    session_dir = EV_SAVES_DIR / session_name
    session_dir.mkdir(parents=True, exist_ok=True)

    has_scenario = False
    if pack:
        packs_dir = packs_dir or Path("packs")
        p = load_pack(pack, packs_dir)
        has_scenario = p.scenario is not None
        if not has_scenario:
            # Static-only packs: write seed state now (scenario packs get written by _ensure_seed_generated)
            if p.seed:
                state_dict = p.seed.model_dump()
            else:
                state_dict = _default_state()
            if p.opening_scene and not state_dict.get("__seed_meta__", {}).get("opening_narrative"):
                state_dict.setdefault("__seed_meta__", {})["opening_narrative"] = p.opening_scene
            init_save_dir(session_dir, state_dict)
    else:
        init_save_dir(session_dir, _default_state())

    # Create events.jsonl for scenario packs (directory must exist for generate_seed)
    if has_scenario:
        (session_dir / "state.yaml").touch()
        (session_dir / "events.jsonl").touch()
        (session_dir / "chronicle.md").touch()

    latest_link = EV_SAVES_DIR / "latest"
    if latest_link.is_symlink() or latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(session_dir)

    return session_dir
```

Wait — actually `generate_seed()` doesn't write to the save directory. `generate_seed()` returns a `SeedEnvelope`. The callers then unpack it and call `init_save_dir()` themselves. So I need `init_save_dir()` to already have been called — or I need to call it from within `_ensure_seed_generated()`.

Looking more carefully: the current callers do this pattern:
1. `_create_play_session()` → `init_save_dir(session_dir, seed_dict)` (writes state)
2. Then `generate_seed()` → unpack → `init_save_dir(session_dir, seed_dict)` again (overwrites)

So the pre-write IS wasted. We should let `_ensure_seed_generated()` handle `init_save_dir()` for scenario packs. Better approach:

**`_create_play_session`** just creates the directory and symlink. Call `init_save_dir` only for non-scenario packs. For scenario packs, `_ensure_seed_generated()` will call it.

Let me re-think. Actually, we need the directory structure (events.jsonl, chronicle.md) to exist before generate_seed. `init_save_dir()` creates those. So we should:

1. `_create_play_session()` creates dir + symlink + calls `init_save_dir()` with whatever we have (static seed or default state)
2. `_ensure_seed_generated()` for scenario packs calls `generate_seed()` then `init_save_dir()` again to overwrite

This is what the code already does (pre-write then overwrite). We can either:
a) Keep the double-write (trivial waste, simpler code)
b) Have `_create_play_session` skip `init_save_dir()` for scenario packs and let `_ensure_seed_generated()` handle it

Option (b) is cleaner but slightly more complex. Let me go with (b) since the plan already proposes it.

Actually, for option (b), `_create_play_session` needs to still create the files minimally. `init_save_dir` creates `state.yaml`, `events.jsonl`, and `chronicle.md`. If we skip it, `_ensure_seed_generated` needs to call `init_save_dir` which does all of those. That's fine.

But there's a subtlety: `_ensure_seed_generated` is called AFTER `_create_play_session` returns the session_dir. So the flow would be:

```python
session_dir = _create_play_session(pack=pack_id)  # just mkdir + symlink
# _create_play_session does NOT call init_save_dir for scenario packs
state = _ensure_seed_generated(session_dir, pack_id, config, seed_dict, opening_scene)
# _ensure_seed_generated calls init_save_dir for scenario packs
```

This works. Let me finalize the plan with this approach.

**Why:** Removes the wasted double-write for scenario packs.

**Validation:** `.venv/bin/python scripts/debug/ev.py play "test" --pack zombie-survival` produces correct turn 0.

#### Step 1.3 — Replace the 3 duplicated blocks with the helper

**File:** `ccya/ev/play.py`, 3 locations:
- `_interactive_session()` lines 326-356
- `_llm_session()` lines 407-437
- `cmd_play()` single-turn path lines 652-685

**What:** In each of the 3 callers, replace the ~30-line block of seed-generation logic with a single call to `_ensure_seed_generated()`.

Before:
```python
# Generate seed for dynamic packs (scenario.yaml but no static seed)
if pack and not seed_dict:
    p = load_pack(pack, packs_dir)
    if p.scenario is not None:
        loop = _get_play_loop()
        envelope, pool_selection = loop.run_until_complete(
            generate_seed(p, config, template_dir=...),
        )
        # ... 20 lines of unpacking and init_save_dir ...
```

After:
```python
state = _ensure_seed_generated(session_dir, pack, config, seed_dict, opening_scene)
```

For `_interactive_session` and `_llm_session`, also adjust the `seed_dict` variable name — it's no longer needed since `state` is returned directly.

**Why:** Eliminates 3× copy-paste, makes the decision logic live in one place.

**Validation:** `.venv/bin/python scripts/debug/ev.py summary` no regressions. Run all 3 modes:
1. `.venv/bin/python scripts/debug/ev.py play "look around" --pack zombie-survival`
2. `.venv/bin/python scripts/debug/ev.py play --interactive --pack zombie-survival` (type "quit")
3. `.venv/bin/python scripts/debug/ev.py play --llm --turns 2 --pack zombie-survival`

#### Step 1.4 — Remove unused `_load_pack_params()` at callers that still use it

**File:** `ccya/ev/play.py`

**What:** The callers still call `_load_pack_params()` to extract `name_locales`, `narrator_rules`, `world_rules`, `factions`, `opening_scene`, `style`. These are needed for `play_turn()` pack context and the LLM player persona context. The function also extracts `seed_dict` which is now only consumed by `_ensure_seed_generated()`.

Remove the unused `seed_dict` return from the tuple unpacking at each caller (or keep it if `_ensure_seed_generated()` uses it). Since `_load_pack_params()` loads the pack and extracts `seed_dict`, and we now re-load the pack inside `_ensure_seed_generated()` — this is a redundant load. 

But `_load_pack_params()` also extracts pack metadata (name_locales, narrator_rules, etc.) that are still needed. We can either:
a) Keep `_load_pack_params()` as-is (it loads the pack once for metadata, `_ensure_seed_generated()` loads it again for seed gen — minor redundancy)
b) Refactor so `_ensure_seed_generated()` returns the scenario metadata too — over-complicated

Do (a) — the simplest change. The double-load is negligible (YAML file read).

**Why:** Minimal diff, avoids scope creep.

**Validation:** Same commands as step 1.3.

### Tests to write or update

No tests exist for ev.py — they were removed during refactor. Manual verification via the 3 commands in step 1.3 is sufficient.

### Documentation updates

- **`docs/repomap.md`** — No change needed (ev.py seed gen is internal, not a public API).
- **`docs/architecture/`** — No change needed (pipeline flow unchanged).
- **`AGENTS.md`** — No change needed.
