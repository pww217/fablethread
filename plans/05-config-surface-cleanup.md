# Config Surface Cleanup

## Status
`open`

## Phases

3 phases: remove dead EngineConfig fields that control nothing, remove the `apply_thinking()` no-op and its config flags, fix the `warmup_on_start` default mismatch and `setting_pack` legacy label.

## Issue

The configuration surface has accumulated dead fields, misleading labels, and a silent-behavior-change trap. Four `EngineConfig` fields (`thread_urgency_building_at`, `thread_urgency_immediate_at`, `thread_urgency_immediate_ttl`, `avoidance_decay_per_turn`) are defined, populated from `config.yaml`, and set on the config object — but never read by any application code. Two config booleans (`enable_extract_thinking`, `enable_narrate_thinking`) control a function that is itself a no-op: `apply_thinking()` at `llm_client.py:142-145` ignores its `enable` parameter and returns a shallow copy of messages regardless. `warmup_on_start` has a code default of `True` but a config value of `false` — removing the key from config silently enables warmup. `setting_pack` is labeled "Remove this, legacy" but is actively read at app startup, and its code default (`expanse-belter`) doesn't match the config value (`zombie-survival`).

## Solution

Remove the four dead `EngineConfig` fields from the dataclass, `build_engine_config()`, and `config.yaml`. Remove `apply_thinking()` and its two config flags, replacing each of its 5 call sites with a direct `messages` passthrough. Remove the now-unused `enable_thinking` / `enable_narrate_thinking` parameters from message-builder function signatures and their pipeline-level call sites. Change the `warmup_on_start` code default to `False` to match config intent. Remove the "legacy" comment on `setting_pack` and make the code default match the config value, or vice versa.

## Firm decisions

1. `apply_thinking()` is removed entirely, not fixed. Fixing it would require implementing actual XML `<think>` injection, which is out of scope and has unknown output-quality impact. Two config keys are removed, not deprecated.
2. `warmup_on_start` code default changes to `False` (matching config intent). Users who want warmup must explicitly set it to `true` in config.
3. `setting_pack` label changes from "legacy" to active. The code default is updated to `"zombie-survival"` to match the config value, rather than changing the config to match `"expanse-belter"`.
4. Each phase in this plan touches different files, but the shared concern is "config surface cleanliness." Phases can be executed independently.

## Non-goals

- Not adding migration warnings or deprecation periods. Dead fields are removed silently.
- Not implementing actual thinking injection as a replacement for `apply_thinking()`.
- Not refactoring the `EngineConfig` dataclass beyond removing the dead fields.

## Risks, Ambiguities, and Blockers

- Config files in existing game saves (under `saves/`) reference the dead keys. Since `build_engine_config()` reads from `config.yaml` (repo root) not from per-save configs, this is safe — per-save configs are not read by the engine.
- Five call sites for `apply_thinking()` must all be updated (extraction:288,321,381; ruling:71; narrate:121 — there is no internal call in llm_client.py). Failure to update any one would cause a `NameError`. Separately, the config-field reads at extraction.py:534,580,631 and turn.py:958 must also be updated when the function parameter is removed from the message builders. All are in the same module tree, so a grep sweep is reliable.
- No blocker.

---

## Implementation — Phase 1: Remove dead EngineConfig fields

### Context files to load
- `ccya/engine/config.py` — the `EngineConfig` dataclass (~line 40) and `build_engine_config()` (~line 99)
- `config.yaml` — the `game:` section

### Detailed steps

#### Step 1.1 — Remove field definitions from EngineConfig dataclass

**File:** `ccya/engine/config.py`

**What:** Remove these four field definitions from the `EngineConfig` dataclass (lines 66-77):
- `thread_urgency_building_at: int = 3` (line 67)
- `thread_urgency_immediate_at: int = 5` (line 68)
- `thread_urgency_immediate_ttl: int = 8` (line 73)
- `avoidance_decay_per_turn: int = 1` (line 77)

Renumber lines after removal.

**Why:** These fields are never read by any application code. They consume config surface area and mislead users into thinking they control thread urgency behavior.

**Validation:** `rg "thread_urgency_building_at|thread_urgency_immediate_at|thread_urgency_immediate_ttl|avoidance_decay_per_turn" ccya/ --include='*.py'` returns zero matches after the fix.

#### Step 1.2 — Remove field mappings from build_engine_config()

**File:** `ccya/engine/config.py`

**What:** Remove the corresponding `game.get(...)` calls in `build_engine_config()` (lines 150-152, 163-165):
- `thread_urgency_building_at=int(game.get("thread_urgency_building_at", 3)),`
- `thread_urgency_immediate_at=int(game.get("thread_urgency_immediate_at", 5)),`
- `thread_urgency_immediate_ttl=int(game.get("thread_urgency_immediate_ttl", 8)),`
- `avoidance_decay_per_turn=int(game.get("avoidance_decay_per_turn", 1)),`

**Why:** These are the only places where the dead fields are set. Removing them from the dataclass without removing these assignments would cause TypeError at engine startup.

**Validation:** `python3 -c "from ccya.engine.config import EngineConfig; EngineConfig()"` succeeds without warnings.

#### Step 1.3 — Remove key comments from config.yaml

**File:** `config.yaml`

**What:** Remove these lines from the `game:` section:
- `thread_urgency_building_at: 3   # background → building` (line 25)
- `thread_urgency_immediate_at: 5  # building → immediate` (line 26)
- `thread_urgency_immediate_ttl: 8` (line 28)

**Why:** These keys no longer map to any code path. Leaving them in config is misleading.

**Validation:** `python3 -c "from ccya.models import load_config; cfg = load_config(); from ccya.engine.config import build_engine_config; build_engine_config(cfg)"` succeeds. Confirm that `thread_urgency_building_at` is no longer a key on the built config.

### Tests to write or update

None. No existing tests reference these fields.

### REPOMAP updates required

- `ccya/engine/config.py`: Remove the three-line comment block that preceded the dead fields (lines 66, 68-69, 71-73, 76-77).
- `ccya/eval/engine_mirror.py:19` references `_defaults.thread_urgency_max_age` which is NOT being removed. No change needed.

---

## Implementation — Phase 2: Remove apply_thinking() no-op and config flags

### Context files to load
- `ccya/llm_client.py` — `apply_thinking()` function (line 142) and `_MOCK_MODE` checks (lines 218, 257)
- `ccya/engine/config.py` — `enable_extract_thinking` and `enable_narrate_thinking` fields in `EngineConfig` + `build_engine_config()`
- `config.yaml` — `enable_extract_thinking` and `enable_narrate_thinking` keys
- `ccya/engine/extraction.py` — call sites for `apply_thinking()` (lines 288, 321, 381)
- `ccya/engine/ruling.py` — call site for `apply_thinking()` (line 71)
- `ccya/engine/narrate.py` — call site for `apply_thinking()` (line 122)

### Detailed steps

#### Step 2.1 — Remove the apply_thinking() function

**File:** `ccya/llm_client.py`

**What:** Delete the `apply_thinking()` function definition (lines 142-145). The function body is `return [dict(m) for m in messages]` — it copies the messages list regardless of the `enable` parameter.

**Why:** The function is a no-op that misleads readers into believing thinking injection is functional. It is called from 6 locations with either `config.enable_extract_thinking`, `config.enable_narrate_thinking`, or hardcoded `False` — none of which affect behavior.

**Validation:** `grep -rn "apply_thinking" ccya/` returns zero matches after the function is removed AND all call sites are updated (step 2.2).

#### Step 2.2 — Replace all 5 call sites with direct passthrough

**Files:**
- `ccya/engine/extraction.py` (3 call sites: lines 288, 321, 381)
- `ccya/engine/ruling.py` (1 call site: line 71)
- `ccya/engine/narrate.py` (1 call site: line 122)

**What:** At each call site, replace `apply_thinking(messages, some_config_flag)` with `messages` (the no-op returned a shallow copy of messages; the raw list is not mutated by any downstream code in this call chain, so passing the list directly is safe).

**Why:** Removing the function requires updating all call sites to avoid `NameError`. The no-op's return value is a shallow copy of the input; the caller does NOT modify the returned list, so passing `messages` directly has the same effective behavior.

**Validation:** `python3 -c "import ccya.llm_client; import ccya.engine.extraction; import ccya.engine.ruling; import ccya.engine.narrate"` — all import successfully. Then `make check && make test` passes.

#### Step 2.3 — Remove config fields and mappings

**File:** `ccya/engine/config.py`

**What:** Remove `enable_extract_thinking: bool = False` (line 55) and `enable_narrate_thinking: bool = False` (line 56) from `EngineConfig`. Remove the corresponding lines in `build_engine_config()`:
- `enable_extract_thinking=bool(llm.get("enable_extract_thinking", False)),` (line 140)
- `enable_narrate_thinking=bool(llm.get("enable_narrate_thinking", False)),` (line 141)

**File:** `config.yaml`

**What:** Remove `enable_extract_thinking: false` (line 8) and `enable_narrate_thinking: false` (line 9) from the `llm:` section.

**Why:** These flags only controlled `apply_thinking()`, which is being removed. They have no other consumers.

**Validation:** `rg "enable_extract_thinking|enable_narrate_thinking" ccya/ --include='*.py'` returns zero matches.

#### Step 2.4 — Remove dead `enable_thinking` param from message-builder signatures and pipeline call sites

**File:** `ccya/engine/narrate.py`

**What:** Remove the `enable_narrate_thinking: bool = False` parameter from `_narrate_messages()` function signature (line 26). The internal `apply_thinking` call was replaced in step 2.2.

**File:** `ccya/engine/extraction.py`

**What:** Remove the `enable_thinking: bool = False` parameter from three function signatures:
- `_extract_scene_messages()` (line 244)
- `_extract_state_messages()` (line 297)
- `_storytell_messages()` (line 332)

The internal `apply_thinking` calls in each were replaced in step 2.2.

**File:** `ccya/engine/turn.py`

**What:** Remove `enable_narrate_thinking=config.enable_narrate_thinking` from the `_narrate_messages()` call at line 958.

**File:** `ccya/engine/extraction.py`

**What:** Replace the three pipeline-level calls that pass `enable_thinking=config.enable_extract_thinking`:
- line 534: `_extract_scene_messages(env, narration, state, recent_turns=..., turn_no=turn_no)` — drop the `enable_thinking=...` kwarg
- line 580: `_extract_state_messages(env, narration, state, intent=intent, turn_no=turn_no)` — drop the `enable_thinking=...` kwarg
- line 631: `_storytell_messages(env, narration, state, state_result=..., extraction_ctx=..., intent=..., pacing_context=..., recent_turns=..., turn_no=turn_no, band=...)` — drop the `enable_thinking=...` kwarg

**Why:** After removing `apply_thinking()` and its config flags from EngineConfig, the parameters that passed `config.enable_extract_thinking` / `config.enable_narrate_thinking` are no longer needed. Leaving them would create dead parameters that ruff `ARG` rules may flag, and removing the EngineConfig fields without removing these reads would cause AttributeError.

**Validation:** `python3 -c "import ccya.engine.turn; import ccya.engine.extraction; import ccya.engine.narrate; import ccya.engine.ruling"` — all import successfully. `make check` passes.

### REPOMAP updates required

- `ccya/llm_client.py`: Remove the `apply_thinking()` function and update any imports that reference it.
- `ccya/engine/config.py`: Remove the thinking-related fields and mappings.

---

## Implementation — Phase 3: Fix warmup_on_start and setting_pack

### Context files to load
- `ccya/server/app.py` — lines 37 (`setting_pack`), 56 (`warmup_on_start`)
- `config.yaml` — `game:` section, lines 18 (`setting_pack`) and 22 (`warmup_on_start`)

### Detailed steps

#### Step 3.1 — Fix warmup_on_start code default to False

**File:** `ccya/server/app.py`

**What:** Change `config.get("game", {}).get("warmup_on_start", True)` (line 56) to `config.get("game", {}).get("warmup_on_start", False)`.

**Why:** The config file explicitly sets `warmup_on_start: false`. The code default of `True` means removing the key from config silently enables warmup — a behavior change trap. The config value is the source of truth for runtime behavior; the code default should match.

**Validation:** No validation needed beyond `make check`. The change is a single boolean from `True` to `False`.

#### Step 3.2 — Fix setting_pack legacy label and default

**File:** `config.yaml`

**What:** Change the comment on line 18 from `setting_pack: zombie-survival # Remove this, legacy` to `setting_pack: zombie-survival` (remove the comment).

**File:** `ccya/server/app.py`

**What:** Change `config.get("game", {}).get("setting_pack", "expanse-belter")` (line 37) to `config.get("game", {}).get("setting_pack", "zombie-survival")`.

**Why:** The "Remove this, legacy" comment is misleading — the key IS actively read at app startup. Removing it would silently change the active pack from `zombie-survival` to the code default `expanse-belter`. The code default should match the config value so that removing the key is safe if ever truly desired.

**Validation:** `python3 -c "from ccya.server.app import _pack_id; print(_pack_id)"` — must print `"zombie-survival"`.

### Tests to write or update

None. Warmup and pack loading are startup-sequencing concerns, not logic functions.

### REPOMAP updates required

- `ccya/server/app.py`: Update docstring or comments if they reference the old defaults.
