# Plan 5: Thread Lifecycle Tuning (Config + Throttle)

## Status
`completed`

## Phases

2 phases: (1) make thread progress completion threshold configurable; (2) add per-turn-count throttle on new thread creation via `thread_add`.

## Issue

Two independent tuning gaps in the thread lifecycle system:

**Problem A — Hardcoded completion threshold:** Thread progression completes at exactly `progress >= 3` (`turn.py:220`). This is a hardcoded constant with no config knob. Different game styles may want faster (>= 2) or slower (>= 4) thread resolution, but there's no way to adjust without modifying source code.

**Problem B — No per-turn throttle on thread_add:** The pacing gate (`PacingContext.gate`) blocks thread additions during deescalation turns, but when the gate is "allow", any LLM can emit `thread_add` every single turn. There's no additional rate limit like "only one new thread every X turns" to prevent rapid thread proliferation even during permissive pacing periods. The `_ACTIVE_THREAD_CAP=3` limits concurrent active threads but doesn't throttle creation frequency — the LLM could add 3 threads in one turn, fill the cap, then resolve them and repeat.

## Solution

Phase 1: Add `thread_completion_threshold` config field (default 3) to EngineConfig; replace hardcoded `>= 3` check with configurable value read from config. Phase 2: Track last thread_add turn via `state.meta.last_thread_creation_turn`; only allow new thread additions when `(current_turn - last_thread_creation_turn >= _THREAD_ADD_COOLDOWN_TURNS)`.

## Firm decisions

1. Thread completion threshold defaults to 3 (preserves existing behavior). Config key: `thread_completion_threshold` under `game:` section in config.yaml.
2. Thread creation cooldown defaults to 3 turns (`_THREAD_ADD_COOLDOWN_TURNS = 3`). New threads can only be added once every 3 turns regardless of gate state. This is independent from the pacing gate — both must allow for thread_add to succeed.
3. The cooldown counter is stored in `state.meta.last_thread_creation_turn` (int, defaults to 0 or None). Only incremented on successful thread additions, not on rejected ones.

## Non-goals

- Does not change `_ACTIVE_THREAD_CAP=3` — that remains a separate concurrency limit.
- Does not modify the storyteller prompt template for this cooldown — it's enforced purely in Python.
- Does not add per-NPC or per-location thread creation limits.
- Phase 1 modifies when thread_advance results in completion (threshold check), but does NOT change how thread_advance signals are emitted by the LLM.

## Risks, Ambiguities, and Blockers

**Ambiguity:** Should the cooldown reset on any storyteller call (even without thread_add) or only on successful additions? Only on successful additions — this prevents "gaming" the cooldown by emitting empty thread_add signals. The gate check in Plan 1 already blocks additions during deescalation; adding a separate cooldown provides additional rate limiting even when gate allows.

**Risk:** Existing saves don't have `last_thread_creation_turn` in meta. Default to None/0 which means "never" — first turn after migration will allow thread_add (cooldown satisfied since current_turn - 0 > threshold). Safe fallback.

**Cross-plan dependency:** Phase 2 must be executed AFTER Plan 1 (`01-thread-add-gate-bypass-fix.md`) is complete. Step 5.2.2 adds a cooldown check alongside the gate check from Plan 1 in the same thread_add block (turn.py:1321-1351). If Phase 2 runs first, the executor will need to add both checks simultaneously — which works but duplicates work already done by Plan 1.

**Blocker:** None. Phase 1 touches only config.py and turn.py. Phase 2 adds one state field + gate check in the same location as Plan 1's fix (requires Plan 1 first).

---

## Implementation — Phase 1: Thread completion threshold config knob

### Context files to load
- `ccya/engine/config.py` — EngineConfig dataclass (lines 40-86); build_engine_config() function
- `config.yaml` — game section for new config key
- `ccya/engine/turn.py` — hardcoded `>= 3` at line 220; comment at line 170

### Detailed steps

#### Step 5.1.1 — Add thread_completion_threshold to EngineConfig

**File:** `ccya/engine/config.py`

**What:** Add a new field to the EngineConfig dataclass:
```python
# Thread completion threshold (progress value that completes a thread)
thread_completion_threshold: int = 3
```
Place it near existing thread-related config fields (`thread_urgency_max_age`, `thread_deescalate_on_success`) around line 65-72.

In `build_engine_config()`, add the mapping from raw config dict:
```python
thread_completion_threshold=int(game.get("thread_completion_threshold", 3)),
```
Place it near other thread-related mappings in the return statement (around lines 140-148).

**Why:** Provides a configurable knob for adjusting how quickly threads complete. Default of 3 preserves existing behavior; game designers can lower to 2 for faster pacing or raise for longer story arcs. Single source of truth via EngineConfig rather than scattered constants.

**Validation:** Run `make check`. Verify that default value is 3 (preserves existing behavior). Existing config.yaml entries without this key are unaffected.

#### Step 5.1.2 — Replace hardcoded >= 3 with configurable threshold in turn.py

**File:** `ccya/engine/turn.py`

**What:** In `_apply_thread_signals()` at line 220, replace:
```python
if new_progress >= 3:
```
with:
```python
if new_progress >= config.thread_completion_threshold:
```

The function signature must be updated to accept `config`: add `config` as a third parameter. Update the single call site at turn.py:1300 (`_apply_thread_signals(state, storyteller_result)`) to pass the engine_config from the calling context (the same config object already available in scope for `_compute_pacing_context()` and other calls).

Also update the docstring comment at line 170 from "Threads with progress >= 3 -> complete" to "Threads reach completion_threshold -> complete".

**Why:** Centralizes thread lifecycle tuning in EngineConfig rather than scattering hardcoded constants across turn.py. The threshold is now adjustable per-save via config.yaml without code changes.

**Validation:** Run `make check`. Verify function signature change propagates correctly if `_apply_thread_signals()` gains a `config` parameter. All callers must be updated to pass the config object.

### Tests to write or update

- **Test: thread completes at configurable threshold (default 3)**
  - Setup: Thread with progress=2, advance it once via storyteller_result.thread_advance
  - Run `_apply_thread_signals()` with default config
  - Assert: thread moved to completed_threads (progress reached 3)

- **Test: thread does not complete at threshold > current progress**
  - Setup: Same as above but with `thread_completion_threshold=4` in config
  - Run `_apply_thread_signals()`
  - Assert: thread remains active with progress=3, NOT completed

### REPOMAP updates required

- `ccya/engine/config.py`: New field `thread_completion_threshold: int = 3` on EngineConfig dataclass — update repomap entry at line ~65 if present.
- `ccya/engine/turn.py`: `_apply_thread_signals()` may gain `config` parameter — update signature in repomap thread lifecycle section (lines 98-108) if needed.

---

## Implementation — Phase 2: Per-turn thread creation cooldown

### Context files to load
- `ccya/engine/turn.py` — thread_add processing block at lines 1321-1351; PacingContext gate check from Plan 1
- `config.yaml` — game section for new config key
- `ccya/engine/config.py` — EngineConfig dataclass

### Detailed steps

#### Step 5.2.1 — Add thread_add_cooldown to EngineConfig and turn.py constant

**File:** `ccya/engine/config.py` + `ccya/engine/turn.py`

**What:** In config.py, add:
```python
# Thread creation cooldown (minimum turns between new thread additions)
thread_creation_cooldown: int = 3
```
In turn.py, define a module-level constant that reads from config at runtime OR use the hardcoded default with config override. Given this is only used in one location, read directly from config parameter rather than creating another global constant.

**Why:** Provides rate limiting on thread creation independent of pacing gate. Even when `gate == "allow"`, new threads can only be added once every N turns (default 3). Prevents rapid thread cycling that degrades narrative focus.

**Validation:** Run `make check`. Default value of 3 matches the original plan's intent ("only every X turns"). Existing configs unaffected.

#### Step 5.2.2 — Add cooldown gate to thread_add processing in turn.py

**File:** `ccya/engine/turn.py`

**What:** In the thread_add processing block (lines 1321-1351), add a cooldown check alongside the existing gate check from Plan 1 (`01-thread-add-gate-bypass-fix.md`). The full guard should read: only process thread_add if BOTH conditions are met:
1. `_pc is None or _pc.gate == "allow"` (from Plan 1)
2. `state.get("meta", {}).get("last_thread_creation_turn") is None or (turn_no - last_thread_creation_turn >= config.thread_creation_cooldown)`

If cooldown not satisfied, log at debug level and skip thread creation for this turn. On successful addition, update:
```python
state.setdefault("meta", {})["last_thread_creation_turn"] = turn_no_for_add
```

**Required execution order:** This step must be executed AFTER Plan 1 is complete. The gate check referenced here (`_pc.gate == "allow"`) does not exist in source until Plan 1's Step 1.1 is applied. If this step runs first, the executor will need to add both the gate check AND cooldown simultaneously — which works but duplicates work already done by Plan 1.

**Why:** Two-layer defense against thread proliferation: (a) pacing gate blocks additions during deescalation turns; (b) cooldown prevents rapid-fire additions even when gate allows. Both must pass for a new thread to be created. This matches the original design intent of "max 3 threads, only every X turns."

**Validation:** Run `make check`. No behavioral changes on first turn after game start (last_thread_creation_turn is None → cooldown satisfied). Subsequent additions respect both gate and cooldown. Existing saves without meta.last_thread_creation_turn default to None which satisfies the first addition.

### Tests to write or update

- **Test: thread_add blocked by cooldown within threshold turns**
  - Setup: State with `meta.last_thread_creation_turn = turn_no`, storyteller_result with valid thread_add, gate == "allow"
  - Run thread processing for same turn (or turn < last + cooldown)
  - Assert: thread NOT added; debug log emitted

- **Test: thread_add allowed when cooldown satisfied**
  - Setup: State with `meta.last_thread_creation_turn = turn_no - 3`, storyteller_result with valid thread_add, gate == "allow"
  - Run thread processing for current turn
  - Assert: thread added; meta.last_thread_creation_turn updated to current turn

- **Test: first thread creation after migration (no last_thread_creation_turn)**
  - Setup: State without `meta.last_thread_creation_turn` key
  - Run thread processing with valid thread_add and gate == "allow"
  - Assert: thread added; meta.last_thread_creation_turn set to current turn

### REPOMAP updates required

- `ccya/engine/config.py`: New field `thread_creation_cooldown: int = 3` on EngineConfig dataclass.
- State shape documentation (repomap.md lines 158-209): Add `meta.last_thread_creation_turn: int | None` to meta section explaining it tracks cooldown for thread_add rate limiting.
