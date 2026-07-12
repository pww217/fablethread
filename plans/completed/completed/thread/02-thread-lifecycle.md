# Ev1 fix — Thread lifecycle: aging, progress tracking, and scene-scoped management

## Status
`completed`

## Phases

Two sub-phases:
- **Step 0** — Key-branch black hole fix (`turn.py:1275-1295`): independent structural fix that can run in parallel with Phases 0–2.
- **Steps 2.1–2.7** — Thread lifecycle fixes (urgency decay, scene-scoped progress, scene expiration): depend on Phase 0 (world-state redesign) for ArcThread model changes and `_apply_thread_resolutions()` modifications.

## Critical Note — Why Step 0 Must Execute Before Steps 2.1–2.7

The `thread_add` if-elif chain at `turn.py:1275` (`elif _new_thread.key:`) has a structural code bug: it checks for key collisions but has NO fallthrough to actually add the thread when no collision is found. Every scene-scoped `thread_add` emitted by the LLM has a non-null `key` field, so every one enters this branch, passes the collision check, and is silently dropped.

Unless Step 0 is executed first, Steps 2.1–2.7 fix code paths that are structurally unreachable for LLM-generated threads.

---

## Phases
Single phase: all changes to `ccya/engine/turn.py`, `ccya/engine/seed.py`, and `ccya/engine/config.py` — the thread lifecycle subsystem.

## Issue
Four interrelated defects in the thread lifecycle system prevent threads from aging, completing, or being cleaned up under sustained play:

1. **Seeded threads missing `added_turn` (High, ev1 #2):** `seed.py:334-339` sets `active=True` on seeded threads but never assigns `added_turn`. `_compute_threat_ages()` at `turn.py:675-677` skips threads without `added_turn > 0`, so urgency aging cannot produce "Resolve a Threat" directives for any seeded scene-scoped thread.

2. **Progress never increments despite advances (Critical, ev1 #3):** `_apply_thread_signals()` at `turn.py:200` filters to arc-scoped threads only (`scope == "arc"`). Scene-scoped threads like `siege_escalation` (scope=scene) bypass the entire advance/progress/completion pipeline. Their progress stays at 0 regardless of how many `thread_advance` signals fire.

3. **Urgency never decays (High, ev1 #6):** No production code reads `thread_urgency_max_age=8` from config or demotes thread urgency over time. Urgency only changes via LLM updates, and the prompt gives no instructions for urgency decay cadence.

4. **Scene-scoped threads excluded from Python lifecycle (Medium, ev1 #7):** `turn.py:274-276` explicitly passes scene-scoped threads through unchanged. They have no demotion path, no latent transition, and no completion path. Combined with issues #1 and #3, scene threads accumulate without any cleanup mechanism — should follow a two-stage lifecycle: active → latent after inactivity → removed if never surfaced.

**Compound impact (ev1 M6):** All four issues together guarantee thread accumulation under sustained play — urgent seeded threads never age out, frequently advanced threads can't complete (progress stuck), scene threads aren't managed at all, urgency doesn't decay. Threads accumulate until the `_LATENT_THREAD_CAP` or `_ACTIVE_THREAD_CAP` are hit, at which point new thread additions fail silently.

## Solution
Four changes to the thread lifecycle subsystem:

1. **Assign `added_turn` in seed generation:** In `seed.py:334-339`, set `added_turn` to the current turn (from `meta.turn`) on every seeded thread. As a defense-in-depth measure, also add a fallback in `_compute_threat_ages()`: if a thread lacks `added_turn` and `last_seen_turn`, derive `added_turn` from `meta.turn` at the time of the check.

2. **Extend progress tracking to scene-scoped threads:** In `_apply_thread_signals()` at `turn.py:200`, remove the scope filter so scene-scoped threads also receive progress increments and `last_seen_turn` updates. Add a config guard `track_scene_thread_progress: bool` (default True) to allow disabling if the behavioral change is undesirable — documented in config.py.

3. **Wire urgency decay into `_apply_thread_signals()`:** After processing advances and expirations, add a pass that reads `thread_urgency_max_age` from config and demotes urgency for threads that have been at the same urgency level for ≥ threshold turns. Track `urgency_set_turn` on each ArcThread (new field, optional int). Demote urgent→normal→background stepwise. Log demotion events.

4. **Add scene-scoped thread latency path:** In the expiration pass of `_apply_thread_signals()`, add a two-stage lifecycle for scene-scoped threads. When a scene-scoped thread hasn't been advanced in `scene_thread_expire_silent_turns` (default 5) turns, move it to latent state (`active=False`). If a latent scene thread remains unsurfaced for another `scene_thread_expire_silent_turns` turns, remove it entirely from `arc.threads`. This gives scene threads a two-stage lifecycle: active → latent after 5 inactive → removed after 5 more unsurfaced.

## Firm decisions
1. Scene-scoped threads gain progress tracking and a two-stage cleanup lifecycle: active → latent (`active=False`) after `scene_thread_expire_silent_turns` (default 5) turns without progress → removed entirely after 5 more turns without being surfaced. Seed should create 1-2 active threads and 3-5 latent threads at game start for discovery. Latent threads are visible in both Narrator and Storyteller prompts, which actively push players towards exploring them without directly exposing the content.
2. The `urgency_set_turn` field is added to `ArcThread` model. When a thread's urgency is explicitly set (via seed, thread_add, or thread_update), record the current turn. The decay pass checks urgency age against the `thread_urgency_max_age` config.
3. Urgency decay is a Python-side demotion only — it does not send signals to the LLM. The LLM can still set urgency to any value on thread_add/update; the Python decay is a floor that prevents threads from being stuck at "urgent" indefinitely.
4. Progress increments for scene-scoped threads use the same threshold (`thread_completion_threshold`) as arc threads. A scene thread reaching completion threshold is moved to `completed_threads` with `resolution_state = "completed"`.

## Non-goals
- Does not add new prompt instructions about urgency decay (the LLM can still set urgency arbitrarily on thread creation/update — the Python floor handles it).
- Does not change the thread completion threshold or add scene-specific completion rules.
- Does not add a new `ev.py` command (addressed in `03-beat-timing-observability.md`).
- Does not retroactively fix existing state data — only new threads benefit from `added_turn` assignment; old threads without it use the `_compute_threat_ages()` fallback.

## Risks, Ambiguities, and Blockers
- Extending progress tracking to scene-scoped threads changes the semantics of the `thread_completion_threshold` for scene content. Previously scene threads could never complete via Python — they lived until location change or manual LLM resolution. Adding progress-based completion means a scene thread could complete before a location change, which may be unexpected. The `track_scene_thread_progress` config flag provides a rollback path.
- The `urgency_set_turn` field needs to be set in all the right places: seed (seed.py), thread_add (turn.py ~1340-1365), and thread_update (if the LLM updates urgency on an existing thread). Missing any of these will cause the decay pass to use a default value (0 or None), producing incorrect urgency ages.
- The 5-turn silent expiry for scene threads may be too aggressive if events.jsonl compaction drops thread references. Verify that the expiry check reads from state.yaml (the source of truth), not from compacted chronicle history.
- The ev1 dataset only spans 10 turns — urgency decay at 8 turns (the default `thread_urgency_max_age`) would not fire within this window. Testing requires a longer eval scenario or a lowered threshold during testing.

## Implementation

### Context files to load
- `ccya/engine/turn.py` (lines 159-358, 665-686)
- `ccya/engine/seed.py` (lines 334-339)
- `ccya/engine/config.py` (lines 73-92)
- `ccya/models.py` (ArcThread model, for `urgency_set_turn` field)
- `ccya/eval/engine_mirror.py` (`THREAD_ARC_DEMOTE_AGE` ref)

### Detailed steps

#### Step 0 — Fix key-branch black hole: add creation fallthrough after collision check

**File:** `ccya/engine/turn.py`

**What:** Restructure the `thread_add` if-elif chain at lines 1275-1301 so that threads with non-null keys that pass the collision check proceed to the normal thread creation path instead of being silently dropped.

**Current structure (bug):**
```python
elif _new_thread.key:                # line 1275 — enters if thread has key
    # collision check...
    if exact_collision_id is not None:
        pass  # skip creation
    # BUG: no else — falls through entire chain
elif _scope == "scene":              # line 1297 — unreachable for keyed threads
    pass
else:                                # line 1301 — normal creation
    ...
```

**Fix:** Move the key collision check into the final `else:` (creation) branch. The scene-scope pass stays as a separate `elif` for the edge case of non-keyed scene threads. The result:

```python
elif _scope == "scene":              # moved up — catches non-keyed scene threads
    # Scene-scoped threads are handled by age rules in Python, not here
    pass

else:                                # creation path for arc+keyed threads
    # Key collision gate: if matching key exists, skip creation.
    if _new_thread.key:
        exact_collision_id = None
        _state_arc = state.get("arc")
        if _state_arc and delta is not None:
            try:
                _check_arc = CampaignArc.model_validate(_state_arc)
                for _t in (_check_arc.threads or []) + (_check_arc.completed_threads or []):
                    if getattr(_t, 'key') and str(getattr(_t, 'key', '')).lower() == str(_new_thread.key).lower():
                        exact_collision_id = _t.id
                        break
            except Exception:
                pass

        if exact_collision_id is not None:
            _log.warning(
                "thread_add.key_collision",
                extra={"turn": turn_no_for_cooldown, "key": str(_new_thread.key), "existing_id": exact_collision_id, "new_id": _new_thread.id or "?"},
            )
            pass  # skip thread creation — key collision detected
        # else: no collision — proceed to normal creation below

    # ── Existing thread creation logic (previously at line 1301) ──
    arc_raw = state.get("arc")
    ...
```

**Specific changes to lines 1275-1301:**
1. Remove the `elif _new_thread.key:` line (1275) and its block (1275-1295) as a separate branch.
2. Move `elif _scope == "scene": pass` (1297-1299) to replace the key-check position.
3. The `else:` block (1301) now starts with the key collision check before proceeding to the existing creation logic.
4. Variables `_state_arc` and `exact_collision_id` that were local to the removed block are now local to the new inner `if _new_thread.key:` block. The `exact_collision_id` reference inside the existing creation logic at line 1311 (`if _new_thread.key and not exact_collision_id:`) is now scoped correctly — it will be `None` (falsy) when the thread has no key, and will be set appropriately when the thread has a key and was processed by the collision check.

**Why:** This is the root cause of ev2 findings C1 and C14. Every LLM-emitted `thread_add` has a non-null `key` field, so all scene-scoped threads enter the key branch, pass the collision check, and are silently dropped. The fix ensures that threads with non-null keys that don't collide with existing keys proceed to normal creation.

**Validation:** After the fix, emit a `thread_add` with a non-null key and scope=scene. Verify the thread appears in `state.arc.threads` on the next turn. Verify existing behavior is preserved: (a) threads with colliding keys are still rejected with a warning log, (b) gate and cooldown checks still block creation independently, (c) non-keyed scene threads are still passed through unchanged.

**File:** `ccya/models.py`

**What:** Add optional integer field `urgency_set_turn: int | None = None` to the `ArcThread` model class. This field records the turn number when urgency was last set, enabling the decay pass to measure how long a thread has been at its current urgency level.

**Why:** Without tracking when urgency was set, the decay pass cannot determine whether a thread has been "urgent" for 2 turns or 20 turns.

**Validation:** `make typecheck` passes.

#### Step 2.2 — Assign `added_turn` and `urgency_set_turn` during seed generation

**File:** `ccya/engine/seed.py`

**What:** In the seeded thread loop at lines 337-339, after setting `active=True`, also set:
- `added_turn` to the current turn from `meta.turn` (or 1 if meta not yet available)
- `urgency_set_turn` to the same value

The current turn is available from `envelope.seed_state.meta.turn` or from the turn counter at the time of seed generation.

**Why:** Seeded scene-scoped threads never get `added_turn`, which causes `_compute_threat_ages()` to skip them entirely. This is the root cause of ev1 finding #2.

**Validation:** `make check` passes. After seed generation, inspect state.yaml and verify seeded threads have `added_turn` set.

#### Step 2.3 — Add fallback in `_compute_threat_ages()` for missing `added_turn`

**File:** `ccya/engine/turn.py`

**What:** In `_compute_threat_ages()` at line 675, add a fallback: if a thread has neither `added_turn` nor `last_seen_turn`, derive `added_turn` from the current turn number (or default to 1). Change the skip condition to only skip if both fields are missing AND the thread appears to be newly created (no turn context). Specifically:

```python
added_turn = t.get("added_turn") or t.get("last_seen_turn")
if not added_turn or added_turn == 0:
    # Fallback: use current turn for threads that were seeded without added_turn.
    # This allows urgency aging to work for pre-existing data without migration.
    added_turn = state.get("meta", {}).get("turn", 1)
```

**Why:** Defense-in-depth. Even after seed generation is fixed, existing saved games with threads that lack `added_turn` will still have broken urgency aging. The fallback ensures they age correctly from the first turn they're evaluated.

**Validation:** `make check` passes. Simulate a thread without `added_turn` and verify it appears in the threat ages output.

#### Step 2.4 — Extend progress tracking to scene-scoped threads

**File:** `ccya/engine/turn.py`

**What:** In `_apply_thread_signals()`, change the scope filter at line 200 from `scope == "arc"` to include both arc and scene scopes. After the advance loop (line 251), add a separate pass to reactivate latent threads that received an advance signal:

```python
# Change line 200:
all_arc_threads = [t for t in arc.threads if getattr(t, "scope", "arc") in ("arc", "scene")]

# After the advance loop (line 251), before the really_still_active filter (line 253):
for tid, t in list(latent_by_id.items()):
    if tid in advanced_ids:
        # Reactivate: move from latent_by_id to still_active with active=True
        t = t.model_copy(update={"active": True, "last_seen_turn": turn_no, "progress": t.progress + 1})
        still_active.append(t)
        mutated = True
        _log.info("turn.thread_signals.reactivated trace_id=%d thread %s", turn_no, tid)
```

Add a new config field `track_scene_thread_progress: bool = True` to `EngineConfig` in `config.py`. Wrap the scene-thread inclusion in a check: if `track_scene_thread_progress` is True (default), include scene-scoped threads; if False, restore old behavior of filtering to arc only (providing a rollback path).

Also update the function docstring (line 168) to remove "Scene-scoped threads are not processed here."

**Why:** Scene-scoped threads never get progress increments because the filter at line 200 excludes them. This is the root cause of ev1 finding #3 — siege_escalation has scope=scene, so it's excluded, progress stays at 0, and completion is structurally impossible. Additionally, any latent thread (active=False) that receives a thread_advance should be reactivated: set `active=True` alongside the progress increment and last_seen_turn update.

**Validation:** `make check` passes. Add a temporary debug check: after `_apply_thread_signals()` runs on a thread_advance for a scene-scoped thread, verify `progress` incremented and `last_seen_turn` updated. Also verify that a latent thread receiving an advance has `active=True` after the pass completes.

#### Step 2.5 — Wire urgency decay into `_apply_thread_signals()`

**File:** `ccya/engine/turn.py`

**What:** After the advance/expiration loop (after line 251), add a new pass that evaluates urgency decay for all threads (arc and scene):

```python
# Urgency decay: demote threads that have been at their urgency level for
# >= thread_urgency_max_age turns. Urgency decays stepwise: urgent → normal → background.
_urgency_decay_threshold = getattr(config, "thread_urgency_max_age", 8)
for tid, t in list(active_by_id.items()) + list(latent_by_id.items()):
    _urgency_set = getattr(t, "urgency_set_turn", None)
    if _urgency_set is None:
        continue
    _urgency_age = turn_no - _urgency_set
    if _urgency_age >= _urgency_decay_threshold:
        _current_urgency = getattr(t, "urgency", "background")
        if _current_urgency == "urgent":
            t = t.model_copy(update={"urgency": "normal", "urgency_set_turn": turn_no})
            mutated = True
            _log.info(...)
        elif _current_urgency == "normal":
            t = t.model_copy(update={"urgency": "background", "urgency_set_turn": turn_no})
            mutated = True
            _log.info(...)
        # Write new model back to its active/latent by_id dict
        if tid in active_by_id:
            active_by_id[tid] = t
        elif tid in latent_by_id:
            latent_by_id[tid] = t
```

This requires tracking `urgency_set_turn` on each thread. Set it during:
- Seed generation (Step 2.2)
- `thread_add` in the extraction pipeline (turn.py ~1340-1365, plus the key-branch fallthrough path at ~1275-1295)
- Any `thread_resolve` or thread update that changes urgency

**Note:** For the key-branch path (turn.py:1275–1295 — threads with non-null key that pass collision check), the `urgency_set_turn` field must be set when the new thread is created via the fallthrough fix. This is currently dead code (the key branch has no fallthrough at all), so `urgency_set_turn` cannot be set there until the key-branch black hole is fixed first.

**Why:** Urgency never decays because no production code reads the `thread_urgency_max_age` config. The ev1 dataset shows siege_escalation remaining "urgent" across all 10 turns. Adding urgency decay ensures threads naturally wind down over time, reducing persistent Pressure directives.

**Validation:** `make check` passes. Write a unit check: create thread with `urgency="urgent"`, `urgency_set_turn=1`, run `_apply_thread_signals()` at turn=10 with `thread_urgency_max_age=8`, verify urgency demoted to "normal".

#### Step 2.6 — Add scene-scoped thread two-stage latency and expiration

**File:** `ccya/engine/turn.py`

**What:** In the `_apply_thread_signals()` expiration pass (around line 269-276), add a two-stage lifecycle for scene-scoped threads. Stage 1: active → latent after `scene_thread_expire_silent_turns` without advance. Stage 2: latent → removed after another `scene_thread_expire_silent_turns` without being surfaced:

```python
# Scene-scoped thread two-stage lifecycle
_latency_threshold = getattr(config, "scene_thread_expire_silent_turns", 5)
scene_threads = [t for t in arc.threads if getattr(t, "scope", "arc") == "scene"]
for t in scene_threads:
    _last_seen = getattr(t, "last_seen_turn", None)
    if _last_seen is None:
        continue
    _turns_since_seen = turn_no - _last_seen
    
    if getattr(t, "active", True):
        # Active → latent: no advance for threshold turns
        if _turns_since_seen >= _latency_threshold:
            t = t.model_copy(update={"active": False, "urgency": "background"})
            mutated = True
            _log.info("turn.thread_signals.scene_latent trace_id=%d scene_thread %s last_seen_turn=%d",
                       trace_id, t.id, _last_seen)
    else:
        # Latent → remove: unsurfaced for 2x threshold turns
        if _turns_since_seen >= _latency_threshold * 2:
            arc.threads = [x for x in arc.threads if getattr(x, "id", None) != t.id]
            mutated = True
            _log.info("turn.thread_signals.scene_removed trace_id=%d scene_thread %s unsurfaced_since_turn=%d",
                       trace_id, t.id, _last_seen)
```

**Why:** Scene-scoped threads previously had no expiration path beyond location-change. The two-stage lifecycle gives them a soft landing: after 5 turns without progress, they go latent (visible to prompts for discovery). If unsurfaced for another 5 turns, they're removed. This matches the user-defined lifecycle: active → latent after 5 inactive → removed after 5 more unsurfaced. Note: for both arc and scene threads, `_latency_threshold` is used for the first stage; the second stage uses `2 * threshold` as a simple proxy for "surfaced in the meantime."

**Validation:** `make check` passes. Verify that a scene-scoped thread not advanced for 5+ turns is removed from `arc.threads`.

#### Step 2.7 — Add thread lifecycle config fields to EngineConfig

**File:** `ccya/engine/config.py`

**What:** Add three new config fields:

```python
track_scene_thread_progress: bool = True
thread_urgency_max_age: int = 8
scene_thread_expire_silent_turns: int = 5
```

Add YAML loading support at the config loading section (around line 161):

```python
track_scene_thread_progress=bool(game.get("track_scene_thread_progress", True)),
thread_urgency_max_age=int(game.get("thread_urgency_max_age", 8)),
scene_thread_expire_silent_turns=int(game.get("scene_thread_expire_silent_turns", 5)),
```

**Why:** `track_scene_thread_progress` provides a rollback path for extending progress tracking to scene-scoped threads. `thread_urgency_max_age` controls how many turns a thread stays at a given urgency before Python-side demotion (was previously only a constant reference with a silent fallback of 8). `scene_thread_expire_silent_turns` controls both latency triggers (active→latent threshold and the multiplier for latent→removed), making the two-stage lifecycle tunable without code changes.

**Validation:** `make check` passes. Verify config loads with both `true` and `false` values from YAML.

### Tests to write or update

`tests/test_integration.py` — No changes needed. The existing scenario auto-discovery will test the new behavior when the `eval_coverage_gap` scenario (from `eval-coverage-gaps.md` Phase 3) exercises thread progress.

A unit test for urgency decay: create `ArcThread` with known `urgency_set_turn`, run `_apply_thread_signals()` with a mock config at a later turn, verify urgency demotion.

### REPOMAP updates required

`docs/repomap.md` — Update the ArcThread model description (line 216) to note `urgency_set_turn` field. Update `_apply_thread_signals()` description (line 104-109) to note scene-scoped thread progress tracking and urgency decay. Update `_compute_threat_ages()` description to note the added_turn fallback.
