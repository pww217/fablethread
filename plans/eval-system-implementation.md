# Eval System Implementation

## Purpose

Implement 6 new checkers, config-driven thresholds with pack override cascade, and automated report generation for the CCYA eval system.

## Problem Statement

Four major engine systems have zero checker coverage: ruling engine (intent classification, band determination, reason generation), convergence scoring (RISING→CLIMAX transition driver), location description content, and world state fact content. Checkers use hardcoded thresholds inconsistent with engine tunables. Reports are manually written despite an existing Jinja2 template. Prompt separation (a prerequisite) is pending separate execution.

## Constraints

- New checkers must be deterministic or LLM-based; no external dependencies.
- Checkers read from `events.jsonl` and `state.yaml` only — no engine calls.
- LLM checkers limited to 4 total; `ruling_intent_match` is one of them.
- Prompt separation (`docs/design/prompt-separation-design.md`) is a prerequisite for `pacing_directives`/`gm_beat_lifecycle` re-render refactors — those are NOT in scope.
- `beat_narrative_chain` npc_id/driver prompt context is **already implemented** (source at `llm_checkers.py:135-137, 148-149`). Design doc row 44 status should be updated to DONE.
- Checker count after implementation: 22 current + 6 new = 28 (design doc's "22→22" claim in Failure Modes is stale — fixes already applied before this plan).
- `make check` must pass after every phase.

## Non-goals

- Prompt separation — handled by a separate plan that must execute first or in parallel (it has no code-level conflicts with this plan).
- Sanitizer quality checkers (`sanitizer_dedup_threshold`, `sanitizer_abandon_rate`) — DEFERRED per design.
- Future checkers (`gm_beat_field_coverage`, `party_npc_location_exemption`) — FUTURE per design.
- `pacing_directives`/`gm_beat_lifecycle` re-render refactors — depend on prompt separation.
- Prompt template design — handled separately.
- Web UI changes — handled separately.
- CI/CD integration — future concern.

## Solution

Add a `CheckerConfig` sub-section to `EngineConfig` with default thresholds (cascading from Python defaults → `pack.yaml` → `config.yaml`). Implement 3 ruling checkers (2 deterministic + 1 LLM), 1 convergence checker, and 2 state-application checkers. Wire the existing `report.md.j2` Jinja2 template into `ev.py eval run`. Register all new checkers and verify with `make check`.

## Firm decisions

1. EngineConfig cascade: Python defaults → `pack.yaml` `checkers` key → `config.yaml` `checkers` key.
2. `ruling_intent_match` is LLM-based, runs selectively at end-of-session via `--llm-checkers`.
3. Thresholds: `min_reason_words=3`, `band_skew_ratio=0.8`, `location_min_sentences=2`, `location_min_words=30`, `world_state_fact_min_chars=10`.
4. Report template: existing `evals/ev-tooling/templates/report.md.j2`, rendered via Jinja2, written to `<session_dir>/CONSOLIDATED-REPORT.md`.
5. `--report auto` writes to default location; `--report <path>` writes to explicit path (existing behavior).
6. Historical component key handling: `convergence_components` checker accepts both old (`thread_weight`, `urgency_depth`) and new (`urgent_thread`, `threat_thread`) key names.

## Risks, Ambiguities, and Blockers

1. **Pack.yaml override mechanism is new.** `PackManifest` currently has no engine-config fields. Adding `checkers` to `PackManifest` requires model change. Alternative: skip pack.yaml overrides for now (2-level cascade only). This can be deferred to a follow-up without blocking checkers.
2. **`--report auto` conflicts with existing `--report <path>` behavior.** Current code treats `--report` as a file path. Using `auto` as a sentinel string works but is fragile if someone names a directory `auto`. Safer: a separate `--auto-report` boolean flag.
3. **Template data shape.** The `report.md.j2` template expects `rubric_areas`, `pack`, `personality`, `pass_rate_delta`, etc. The current `cmd_eval_run` output does not collect these. Template rendering requires building the rubric_areas structure.
4. **Prompt separation dependency.** Phases 6 (pacing_directives/gm_beat re-render) are not in scope, but if prompt separation ships first, these phases become simpler. No code conflicts either way.
5. **Component key format ambiguity.** `pacing_context.convergence_components` may store keys as strings or floats. Checker must parse both from event JSONL.
6. **Checker ordering matters.** `run_checkers` iterates a dict — order is insertion order (Python 3.7+). LLM checkers at end ensure deterministic checkers run first.
7. **Deterministic checker config isolation.** New deterministic checkers import `EngineConfig` and create `EngineConfig()` to read thresholds. This produces a fresh default-instance, NOT the pack-aware singleton used by LLM checkers (`_get_config` in `llm_checkers.py`). Pack-level threshold overrides only affect LLM checkers. This is acceptable because: (a) deterministic thresholds are generic (word counts, ratios) and don't need per-pack tuning, (b) a shared config singleton for all checkers is a future improvement. Document this limitation.
8. **AGENTS.md test prohibition.** The project AGENTS.md states "Tests are temporarily removed during refactor. Do not write or reference tests until this phase is complete." The "Tests to write or update" sections in this plan may conflict with this directive. Executor should verify with user whether to write test files or defer them.
9. **`append_event` is write-level.** The eval runner calls `append_event` to write warning events. Checkers remain read-only. The eval runner must have a writable `save_dir` — this is already available in `cmd_eval_run` (it creates `session_dir`). Verify the `save_dir` path is passed through to the warning-generation block.

## Status

`open`

## Phases

7 phases: 1) EngineConfig threshold infrastructure, 2) Ruling checkers, 3) Convergence checker, 4) State application checkers, 5) Report automation, 6) Warning storage, 7) Documentation.

---

## Implementation — Phase 1: EngineConfig Checker Threshold Infrastructure

### Context files to load

- `ccya/engine/config.py` (full — EngineConfig model + build_engine_config)
- `ccya/pack.py` (lines 205-260 — PackManifest + load_pack)
- `ccya/ev/eval.py` (lines 33-50 — _build_eval_config)
- `ccya/ev/check.py` (line 68 area — config loading)
- `ccya/ev/play.py` (line 379-402 area — config loading)
- `ccya/ev/checkers/llm_checkers.py` (lines 257-275 — _get_config / set_checker_config)
- `ccya/server/app.py` (lines 61-77 — server config + pack loading)

### Detailed steps

#### Step 1.1 — Add `CheckerConfig` dataclass to `EngineConfig`

**File:** `ccya/engine/config.py`

**What:** Add a `CheckerConfig` dataclass with default thresholds, nested inside `EngineConfig`:

```python
@dataclass
class CheckerConfig:
    min_reason_words: int = 3
    band_skew_ratio: float = 0.8
    location_min_sentences: int = 2
    location_min_words: int = 30
    world_state_fact_min_chars: int = 10
```

Add `checkers: CheckerConfig = field(default_factory=CheckerConfig)` to `EngineConfig`.

**Why:** Single source of truth for checker thresholds. Defaults inline in the dataclass, overridable at config time.

**Validation:** `python3 -c "from ccya.engine.config import EngineConfig; c = EngineConfig(); assert c.checkers.min_reason_words == 3"`

#### Step 1.2 — Update `build_engine_config` to read `checkers` key from config dict

**File:** `ccya/engine/config.py` (inside `build_engine_config`, after line ~298, before return)

**What:** Read `cfg.get("checkers", {})` and override `CheckerConfig` defaults:

```python
checkers_cfg = cfg.get("checkers", {}) or {}
checkers = CheckerConfig(
    min_reason_words=int(checkers_cfg.get("min_reason_words", 3)),
    band_skew_ratio=float(checkers_cfg.get("band_skew_ratio", 0.8)),
    location_min_sentences=int(checkers_cfg.get("location_min_sentences", 2)),
    location_min_words=int(checkers_cfg.get("location_min_words", 30)),
    world_state_fact_min_chars=int(checkers_cfg.get("world_state_fact_min_chars", 10)),
)
```

Pass `checkers=checkers` to the `EngineConfig` constructor.

**Why:** `config.yaml` can now override checker thresholds at the top level.

**Validation:** Add a test config dict with overrides, call `build_engine_config`, verify overrides are reflected.

#### Step 1.3 — Add `checkers` field to `PackManifest`

**File:** `ccya/pack.py` (line 205-213)

**What:** Add optional field `checkers: dict[str, Any] = Field(default_factory=dict)` to `PackManifest`.

**Why:** Packs can specify per-pack checker thresholds via `pack.yaml`. `model_config = {"extra": "ignore"}` already exists, so unknown pack.yaml keys are silently accepted. Adding the field makes it explicit.

**Validation:** `python3 -c "from ccya.pack import PackManifest; p = PackManifest(id='x', name='x'); assert p.checkers == {}"`

#### Step 1.4 — Update `load_pack` to load checkers config

**File:** `ccya/pack.py` (around line 255-310)

**What:** `load_pack` already reads `pack.yaml` into `PackManifest`. No change needed to the load logic — Pydantic will populate `checkers` from the YAML dict automatically (field name matches YAML key). Only if the field presence affects a validation must we add logic.

Verify: `pack.yaml` can contain `checkers: {min_reason_words: 5}` and it flows through.

**Why:** The `extra = "ignore"` on `PackManifest` means the key is silently dropped unless the field exists. Adding the field makes it loadable.

**Validation:** Load a pack with `checkers` in its YAML, assert `pack.manifest.checkers.min_reason_words == 5`.

#### Step 1.5 — Update `_build_eval_config` to merge pack-level overrides

**File:** `ccya/ev/eval.py` (lines 33-42)

**What:** Add optional `pack_dir: Path | None = None` parameter. When provided, load the pack, merge `pack.manifest.checkers` into the config dict before calling `build_engine_config`.

```python
def _build_eval_config(
    model: str | None = None,
    temp: float | None = None,
    pack_dir: Path | None = None,
) -> EngineConfig:
    raw_cfg = load_config()
    if pack_dir:
        from ccya.pack import load_pack
        pack = load_pack(pack_dir)
        if pack.manifest.checkers:
            raw_cfg.setdefault("checkers", {}).update(pack.manifest.checkers)
    ...
```

**Why:** Pack-level checker overrides are merged into the config dict before `build_engine_config` processes it. Cascade: defaults → pack.yaml → config.yaml.

**Validation:** Call with a test pack_dir, verify `EngineConfig.checkers` reflects pack overrides.

#### Step 1.6 — Update `cmd_check` and call sites to accept and pass pack dir

**File:** `ccya/ev/check.py` (around line 60-75), `ccya/ev/__init__.py` (line 293-330), `ccya/ev/play.py` (line 599)

**What:** Add `pack_dir: Path | None = None` parameter to `cmd_check`. When provided, merge pack-level checker config into the raw config dict before calling `build_engine_config` and `set_checker_config`.

Update the `--pack` flag in CLI: add `"pack"` flag parsing in the `__init__.py` check dispatch (line 293-330), pass it to `cmd_check`. Also update the `play.py` call site (line 599) to pass `pack_dir` if available.

Update the `ev.py check --help` output to show `--pack` flag.

**Why:** Checkers run via `ev.py check` need the same config cascade as `ev.py eval run`. Two call sites besides the main CLI must be updated.

**Validation:** `python3 .venv/bin/ev.py check --pack packs/my-pack --list` lists checkers with pack-aware config.

### Tests to write or update

- `tests/ev/test_checker_config.py`: minimal test for `CheckerConfig` defaults + `build_engine_config` with checkers dict overrides. Follow existing `test_schema.py` pattern.
- `tests/ev/test_pack_manifest.py` or extend `test_schema.py`: test `checkers` field loads from `pack.yaml` dict.

---

## Implementation — Phase 2: Ruling Checkers

### Context files to load

- `ccya/ev/checkers/roll_band_consistency.py` (full — reference deterministic checker pattern)
- `ccya/ev/checkers/__init__.py` (line 124 — import line)
- `ccya/ev/checkers/_llm.py` (full — LLM checker utilities)
- `ccya/ev/checkers/llm_checkers.py` (lines 46-81, 119-162 — reference LLM checker pattern)
- `ccya/engine/ruling.py` (around lines where `reason`, `band`, `intent`, `impossible` fields are set)

### Detailed steps

#### Step 2.1 — Create `ruling_reason_quality` checker

**File:** `ccya/ev/checkers/ruling.py` (new file)

**What:** Register deterministic checker `ruling_reason_quality` that:
- Requires fields: `["ruling"]` 
- Iterates turn events where `ruling.rolled` is truthy
- Checks `ruling.reason` is non-empty
- Checks length >= `EngineConfig().checkers.min_reason_words` words (or contains a reason keyword: "because", "since", "due to", "as")
- Reports per-turn findings for failures
- Returns `CheckerResult` with passed=False if any failure, else passed=True

Signature:

```python
from ccya.engine.config import EngineConfig
from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

@register_checker(
    "ruling_reason_quality", "deterministic",
    requires_fields=["ruling"],
    description="Verify ruling.reason is non-empty and substantive",
)
def ruling_reason_quality(events: list[dict[str, Any]]) -> CheckerResult:
```

**Why:** First pipeline step has zero coverage. This checks the GM-facing reason is not a generic placeholder.

Config pattern: Creates `EngineConfig()` directly for defaults. Pack-level overrides do not affect this checker (see Risk #7). Future: move to shared singleton.

**Validation:** Write a minimal `/tmp/` script that constructs mock events with empty/short/valid reasons and asserts the checker passes/fails correctly.

#### Step 2.2 — Create `ruling_band_distribution` checker

**File:** `ccya/ev/checkers/ruling.py` (same file as step 2.1)

**What:** Register deterministic checker `ruling_band_distribution` that:
- Requires fields: `["ruling"]`
- Collects `ruling.band` across all turn events (only where `ruling.rolled` is truthy)
- Computes per-band frequency
- Flags if any single band exceeds `EngineConfig().checkers.band_skew_ratio` (default 80%) of all rolls
- If `band_skew_ratio >= 1.0`, skip the check (effectively disabled)
- Returns single result for the session

```python
@register_checker(
    "ruling_band_distribution", "deterministic",
    requires_fields=["ruling"],
    description="Detect skewed dice band distribution over a session",
)
def ruling_band_distribution(events: list[dict[str, Any]]) -> CheckerResult:
```

**Why:** Extremely skewed band distribution suggests a bug in dice rolling, ruling logic, or LLM roll interpretation.

Config pattern: Creates `EngineConfig()` for threshold defaults. Pack overrides not applied (see Risk #7).

**Validation:** Test with mock events: 9 SUCCESS + 1 FAIL (80% SUCCESS = exactly at threshold, should pass); 10 SUCCESS (100% SUCCESS = exceed threshold, should fail).

#### Step 2.3 — Create `ruling_intent_match` LLM checker

**File:** `ccya/ev/checkers/ruling.py` (same file)

**What:** Register LLM checker `ruling_intent_match` that:
- Requires fields: `["ruling.intent", "ruling.impossible", "ruling.reason"]`
- For each turn event, builds a user prompt showing: `intent`, `impossible`, `reason`, and player input text
- Calls LLM to determine if the `impossible` flag matches the player's intent semantics
- Returns per-turn or aggregated result

Prompt template:

```python
register_prompt_template(
    "ruling_intent_match",
    """You are evaluating whether a ruling's 'impossible' classification
matches the player's stated intent. The GM classified the action as
'impossible: true' or 'impossible: false'. Determine if this classification
is correct based on the player's input.

Return JSON:
{"passed": bool, "score": 0.0-1.0, "reasoning": str, "findings": [{"turn": int, "issue": str}]}""",
    """Turn {turn}:
Intent: {intent}
Impossible: {impossible}
Reason: {reason}
Player input: {player_input}""",
)
```

**Why:** The `impossible` flag gates whether a roll is attempted. Incorrect classification breaks the ruling. This requires LLM-level semantic understanding.

**Validation:** Run against a few turns from a real session via `--llm-checkers`. Verify output format matches `CheckerResult`.

#### Step 2.4 — Register ruling module in checker imports

**File:** `ccya/ev/checkers/__init__.py` (line 124)

**What:** Append `ruling` to the import line:

```python
from . import gm_beat, inventory, conditions, threads, arc_goals, npc_presence, pacing, sanitizer, llm_checkers, phase_transition, climax_turn_counting, breather_enforcement, roll_band_consistency, thread_resolution_validity, new_thread_validity, compendium_lifecycle, beat_phase_validity, arc_resolution_validity, goal_update_validity, ruling  # noqa: E402, F401
```

**Why:** Module-level imports trigger `@register_checker` decorators.

**Validation:** `python3 -c "from ccya.ev.checkers import list_checkers; ids = [m['id'] for m in list_checkers()]; assert 'ruling_reason_quality' in ids"`

### Tests to write or update

- `tests/ev/test_ruling_checkers.py`: minimal tests for `ruling_reason_quality` (empty/short/valid reasons) and `ruling_band_distribution` (skewed/normal). `ruling_intent_match` is LLM-based — test output parsing with mock LLM response.

---

## Implementation — Phase 3: Convergence Components Checker

### Context files to load

- `ccya/engine/_pacing.py` — `compute_convergence_score()` function, 5-component formula
- `ccya/engine/narrate.py` — convergence component display (fixed keys: `urgent_thread`, `threat_thread`)
- `ccya/ev/checkers/pacing.py` — reference deterministic checker (field access patterns)
- `ccya/ev/state_tools.py` — `cmd_convergence` (estimate calculation for reference)

### Detailed steps

#### Step 3.1 — Create `convergence_components` checker

**File:** `ccya/ev/checkers/convergence.py` (new file)

**What:** Register deterministic checker `convergence_components` that:
- Requires fields: `["pacing_context.convergence_components", "pacing_context.convergence_score"]`
- For each turn event where `convergence_components` is present:
  - Extracts the 5 component values. Accepts both old key names (`thread_weight`, `urgency_depth`) and new key names (`urgent_thread`, `threat_thread`). If old keys are found, remaps them to new key names internally.
  - Computes expected score as `sum(urgent_thread, threat_thread, scene_age, beat_streak, dice_weight)`
  - Flags if `abs(expected - convergence_score) > 0.01` (floating point tolerance)
  - Flags if `urgent_thread` or `threat_thread` are negative
- Checks phase transitions: if `scene_phase` changed from RISING to CLIMAX, verify `convergence_score >= convergence_threshold` (default 3)
- Returns per-turn findings

```python
@register_checker(
    "convergence_components", "deterministic",
    requires_fields=["pacing_context.convergence_components", "pacing_context.convergence_score"],
    description="Verify 5-component convergence score matches stored value, drive phase transitions",
)
def convergence_components(events: list[dict[str, Any]]) -> CheckerResult:
```

**Why:** Convergence is the core mechanic driving RISING→CLIMAX transitions. No checker coverage exists. Bug was found: stored component names differed from score formula.

**Validation:** Write a mock event with known component values, compute expected score, assert checker logic matches. Test both old and new key names.

#### Step 3.2 — Register convergence module in checker imports

**File:** `ccya/ev/checkers/__init__.py` (line 124)

**What:** Append `convergence` to the import line.

**Validation:** `python3 -c "from ccya.ev.checkers import list_checkers; ids = [m['id'] for m in list_checkers()]; assert 'convergence_components' in ids"`

### Tests to write or update

- `tests/ev/test_convergence.py`: minimal test for score recomputation, old/new key name handling, RISING→CLIMAX threshold check.

---

## Implementation — Phase 4: State Application Checkers

### Context files to load

- `ccya/ev/events.py` — `extract_field()`, `_SKIP_FIELDS`
- `ccya/models/state.py` — `Location`, `Scene` models (world_state field types)

### Detailed steps

#### Step 4.1 — Create `location_description_consistency` checker

**File:** `ccya/ev/checkers/state.py` (new file)

**What:** Register deterministic checker `location_description_consistency` that:
- Requires fields: `["state_snapshot.location.description"]`
- For each turn event, checks `state_snapshot.location.description`:
  - Non-empty
  - Length >= `EngineConfig().checkers.location_min_words` words
  - OR has at least `EngineConfig().checkers.location_min_sentences` sentences (split by `.`)
- Reports per-turn findings

```python
@register_checker(
    "location_description_consistency", "deterministic",
    requires_fields=["state_snapshot.location.description"],
    description="Verify extracted location description is non-empty and substantive",
)
def location_description_consistency(events: list[dict[str, Any]]) -> CheckerResult:
```

**Why:** Location description is stripped from event blobs via `_SKIP_FIELDS`. Only accessible via `state_snapshot.location.description`. No checker exists for location content.

Config pattern: Creates `EngineConfig()` for threshold defaults. Pack overrides not applied (see Risk #7).

**Validation:** Mock events with empty/short/valid descriptions. Assert pass/fail.

#### Step 4.2 — Create `world_state_facts` checker

**File:** `ccya/ev/checkers/state.py` (same file)

**What:** Register deterministic checker `world_state_facts` that:
- Requires fields: `["state_snapshot.scene.world_state"]`
- For each turn event, checks `state_snapshot.scene.world_state` (a list):
  - Each entry is non-empty
  - Each entry is either a string with length >= `world_state_fact_min_chars` OR a dict with a non-empty `text` field
  - Reports findings per-turn listing empty/minimal facts

```python
@register_checker(
    "world_state_facts", "deterministic",
    requires_fields=["state_snapshot.scene.world_state"],
    description="Verify world_state facts are non-empty strings or dicts with text",
)
def world_state_facts(events: list[dict[str, Any]]) -> CheckerResult:
```

**Why:** World state facts use a dual format (string legacy, dict with `text`+`tier` for structured facts). Content quality is unchecked.

Config pattern: Creates `EngineConfig()` for threshold defaults. Pack overrides not applied (see Risk #7).

**Validation:** Mock events with empty strings, valid strings, valid dicts, empty dicts, mixed lists.

#### Step 4.3 — Register state module in checker imports

**File:** `ccya/ev/checkers/__init__.py` (line 124)

**What:** Append `state` to the import line.

**Validation:** `python3 -c "from ccya.ev.checkers import list_checkers; ids = [m['id'] for m in list_checkers()]; assert 'location_description_consistency' in ids and 'world_state_facts' in ids"`

### Tests to write or update

- `tests/ev/test_state_checkers.py`: minimal tests for `location_description_consistency` (empty/short/valid) and `world_state_facts` (string/dict/mixed formats).

---

## Implementation — Phase 5: Report Automation

### Context files to load

- `ccya/ev/eval.py` (full — `cmd_eval_run`)
- `ccya/ev/__init__.py` (line 330-370 — CLI dispatch for `eval run`)
- `ccya/ev/scenario.py` (full — `Scenario` dataclass)
- `evals/ev-tooling/templates/report.md.j2` (full — template)
- `ccya/ev/checkers/__init__.py` — `list_checkers()` for categories
- `evals/runs/` — existing run-meta.yaml files for prev_run comparison

### Detailed steps

#### Step 5.0 — Add `personality` to Scenario dataclass

**File:** `ccya/ev/scenario.py`

**What:** Add `personality: str = "custom"` to the `Scenario` dataclass (line 29). Add `_require(data, "personality", str, path)` to `load_scenario()`. YAML scenario files must include a `personality` key (defaulting to `"custom"` if absent for backward compat).

**Why:** The report template expects `{{ personality }}`. `play_turn` already accepts a `personality` parameter. Eval scenarios need to specify which personality they're testing so the report is meaningful.

**Validation:** `python3 -c "from ccya.ev.scenario import Scenario; s = Scenario(id='x', pack='y', description='z', turns=[], personality='noir'); assert s.personality == 'noir'"`

#### Step 5.1 — Add `--auto-report` and `--llm-checkers` boolean flags to `ev.py eval run`

**File:** `ccya/ev/__init__.py` (line 42 — `_BOOL_FLAGS`, line 341 area — CLI dispatch)

**What:** Add `"auto-report"` and `"llm-checkers"` to the `_BOOL_FLAGS` set. Accept both flags. When `--auto-report` is set, pass `auto_report=True` to `cmd_eval_run`. When `--llm-checkers` is set, pass `llm_checkers=True` to `cmd_eval_run`. Keep existing `--report <path>` behavior unchanged.

Update usage line (line 341) to show `[--auto-report] [--llm-checkers]`.

Update `cmd_eval_run` call (line 358) to pass `auto_report=("auto-report" in flags), llm_checkers=("llm-checkers" in flags)`.

**Why:** `--auto-report` avoids ambiguity with `--report` file paths. `--llm-checkers` is needed because LLM checkers are expensive (~30s each) and run selectively at end-of-session. The RUBRIC_AREAS mapping includes LLM checkers, so they must be executable from eval run.

**Validation:** `python3 .venv/bin/ev.py eval run --help` shows both flags.

#### Step 5.2 — Add `auto_report` and `llm_checkers` params to `cmd_eval_run`

**File:** `ccya/ev/eval.py` (line 139 — `cmd_eval_run` signature)

**What:** Add `auto_report: bool = False, llm_checkers: bool = False` to the function signature.

**Why:** The function needs to accept these new parameters from the CLI dispatch.

#### Step 5.3 — Add duration tracking around turn loop

**File:** `ccya/ev/eval.py` (inside `cmd_eval_run`, around line 154)

**What:** Import `time` at the top of the file. Wrap the turn loop with timing:

```python
t0 = time.perf_counter()
for i, turn_data in enumerate(scenario.turns):
    ...
duration_ms = round((time.perf_counter() - t0) * 1000.0)
```

Store `duration_ms` as a local variable passed to the report rendering step.

**Why:** The report template expects `{{ duration_ms }}`. Without it, the template renders `None`.

#### Step 5.4 — Run LLM checkers when `--llm-checkers` is set

**File:** `ccya/ev/eval.py` (inside `cmd_eval_run`, after deterministic checker run)

**What:** After `run_checkers(runner_checkers, events, save_dir=session_dir)`, if `llm_checkers=True`:

```python
llm_checker_ids = [m["id"] for m in list_checkers(checker_type="llm")]
llm_results = run_checkers(llm_checker_ids, events, save_dir=session_dir)
checker_results.update(llm_results)
```

This merges LLM checker results into the same `checker_results` dict so they appear in rubric_areas.

**Why:** The RUBRIC_AREAS mapping includes LLM checkers (`ruling_intent_match`, `directive_tone_match`, `beat_narrative_chain`, `state_fidelity`). They won't appear in results unless explicitly run. LLM checkers are expensive so they're opt-in via `--llm-checkers`.

**Validation:** Run `ev.py eval run <scenario> --llm-checkers`, verify LLM checker results appear in output.

#### Step 5.5 — Build rubric_areas structure from checker results

**File:** `ccya/ev/eval.py` (inside `cmd_eval_run`, after checker run)

**What:** After running checkers, group checker results into rubric areas. Define area mapping:

```python
RUBRIC_AREAS: dict[str, list[str]] = {
    "Ruling": ["ruling_reason_quality", "ruling_band_distribution", "ruling_intent_match"],
    "Narration": ["directive_tone_match", "beat_narrative_chain", "state_fidelity"],
    "Pacing": ["pacing_directives", "phase_transition", "climax_turn_counting",
               "breather_enforcement", "convergence_components"],
    "State": ["location_change", "inventory_integrity", "conditions_lifecycle",
              "location_description_consistency", "world_state_facts"],
    "Threads": ["thread_lifecycle", "thread_resolution_validity", "new_thread_validity",
                "sanitizer_lifecycle"],
    "Arcs": ["arc_goal_updates", "arc_resolution_validity", "goal_update_validity"],
    "NPCs": ["npc_presence", "compendium_lifecycle"],
    "GM Beats": ["gm_beat_lifecycle", "beat_phase_validity"],
    "Rolls": ["roll_band_consistency"],
}
```

Build a list of dicts: `{number, name, passed, total, checkers: [{name, status, detail}], red_flags}`.

For each area, iterate the checker IDs, look up results from `checker_results`, set `status` to "PASS"/"FAIL"/"SKIP" based on `CheckerResult.passed`, collect `detail` from `CheckerResult.detail`, and collect `red_flags` from findings where `score < 0.5`.

`pass_rate`: compute as `passed_checkers / total_checkers * 100` (excluding None-skipped checkers), rounded to 1 decimal.

**Why:** Template expects rubric_areas. Grouping by rubric area gives meaningful report structure.

**Validation:** Print test rubric_areas structure matches template expectations.

#### Step 5.6 — Implement prev_run comparison

**File:** `ccya/ev/eval.py` (inside `cmd_eval_run`, before report rendering)

**What:** After running checkers, look for the most recent previous run to compare against:

```python
def _find_latest_run(scenario_pack: str) -> dict[str, str] | None:
    runs_dir = Path("evals/runs")
    if not runs_dir.exists():
        return None
    # Collect all run-meta.yaml paths
    meta_files: list[Path] = []
    for group in runs_dir.iterdir():
        if not group.is_dir():
            continue
        for run in group.iterdir():
            meta_path = run / "run-meta.yaml"
            if meta_path.exists():
                meta_files.append(meta_path)
    # Sort by created_at descending
    meta_files.sort(
        key=lambda p: yaml.safe_load(p.read_text()).get("created_at", ""),
        reverse=True,
    )
    for meta_path in meta_files:
        meta = yaml.safe_load(meta_path.read_text())
        if meta.get("pack") == scenario_pack and meta.get("pass_rate") is not None:
            return {
                "path": str(meta_path.parent),
                "date": meta.get("created_at", ""),
                "pass_rate": meta.get("pass_rate", 0),
            }
    return None
```

If a previous run is found, compute `pass_rate_delta = current_pass_rate - prev_pass_rate`.

**Why:** The report template has a "Comparison vs Previous Run" section. Without prev_run logic, it always renders "No previous run to compare."

**Validation:** Run eval twice on the same pack, verify second run shows comparison.

#### Step 5.7 — Render report via Jinja2 template

**File:** `ccya/ev/eval.py` (in `cmd_eval_run`, near line 207)

**What:** When `auto_report=True` or `report_path` is set:
- Load the Jinja2 environment from `evals/ev-tooling/templates/`
- Build template vars:
  - `pack` = `scenario.pack`
  - `personality` = `scenario.personality`
  - `created_at` = `datetime.now(timezone.utc).isoformat()`
  - `git_sha` = `subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()[:7]` (fallback to `"unknown"` if not in git repo)
  - `git_branch` = `subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()` (fallback to `"unknown"`)
  - `actual_turns` = `len(scenario.turns)`
  - `max_turns` = `len(scenario.turns)`
  - `duration_ms` = computed duration from step 5.3
  - `pass_rate` = computed pass rate from step 5.5
  - `rubric_areas` = built from step 5.5
  - `prev_run` = dict with `path`, `date`, `pass_rate` from step 5.6, or `None`
  - `pass_rate_delta` = integer delta from step 5.6, or `0`
- Render `report.md.j2` with the vars
- Write to `session_dir / "CONSOLIDATED-REPORT.md"` (auto mode) or `report_path` (explicit)

**Why:** Existing template is unused. Auto-generation eliminates manual report writing.

**Validation:** Run `ev.py eval run <scenario> --auto-report`, verify `<session_dir>/CONSOLIDATED-REPORT.md` exists with rendered content.

### Tests to write or update

- `tests/ev/test_report.py`: test rubric_areas builder with mock checker results; test template rendering with min/max data; test prev_run finder with mock run directory.

---

## Implementation — Phase 6: Warning Storage for New Checkers

### Context files to load

- `ccya/state/chronicle.py` — `append_event(save_dir, event)`
- `ccya/ev/warnings.py` — existing warning display

### Detailed steps

#### Step 6.1 — Store ruling warnings as `kind="warning"` events

**File:** `ccya/ev/eval.py` (inside `cmd_eval_run`)

**What:** After running checkers, inspect `ruling_reason_quality` and `ruling_band_distribution` results. For each finding, construct a warning event:

```python
{
    "kind": "warning",
    "turn": finding.get("turn", 0),
    "checker": "ruling_reason_quality",
    "warning": finding.get("detail", ""),
}
```

Call `append_event(save_dir, warning_event)` for each finding. Also include these warnings in the report output.

**Why:** Storing as events preserves timeline context (turn number, timestamp). The `ev.py warnings` command already reads warning events from `events.jsonl`. Checkers are kept read-only — the eval runner post-processes results into events.

**Validation:** Run eval with skewed ruling data, verify warning events exist in `events.jsonl` with `kind="warning"`.

#### Step 6.2 — Store convergence warnings

**File:** `ccya/ev/eval.py` (same mechanism)

**What:** Same pattern as Step 6.1. When `convergence_components` finds anomalies, construct warning events and call `append_event`.

```python
{
    "kind": "warning",
    "turn": finding.get("turn", 0),
    "checker": "convergence_components",
    "warning": finding.get("detail", ""),
}
```

**Why:** Convergence anomalies (score mismatch, negative components) need timeline context. Events preserve this. Report text is supplemental.

**Validation:** Run eval with mocked convergence anomaly, verify warning event in `events.jsonl`.

### Tests to write or update

- No separate tests needed. Warning events are exercised by eval run on real or mocked data.

---

## Implementation — Phase 7: Documentation

### Context files to load

- `docs/repomap.md` — module listing
- `docs/architecture/OVERVIEW.md` — pipeline overview
- `docs/ev/CHECKERS.md` — existing checker docs
- `docs/ev/RUBRIC.md` — rubric
- `AGENTS.md` — build commands, signposts
- `docs/design/eval-system-design.md` — update stale statements

### Detailed steps

#### Step 7.1 — Update `docs/design/eval-system-design.md`

**File:** `docs/design/eval-system-design.md`

**What:**
- Row 44: change `beat_narrative_chain` npc_id/driver status from PENDING to DONE
- Failure Modes section: change "net 0 change (22→22)" to "net +6 change (22→28)"
- Add `CheckerConfig` to the data shapes table (new section or row)
- Add row to decision table for EngineConfig checkers section: `Add EngineConfig.checkers with cascade | DONE`
- Update checker list (rows 66-88) to include 6 new checkers

**Why:** Design doc must reflect current state.

**Validation:** `make check` still passes (markdown files not checked).

#### Step 7.2 — Update `docs/ev/CHECKERS.md`

**File:** `docs/ev/CHECKERS.md`

**What:** Add entries for 6 new checkers: ID, type, fields read, purpose, examples.

**Why:** Checker documentation is the reference for what each checker verifies.

**Validation:** N/A (markdown).

#### Step 7.3 — Update `docs/ev/RUBRIC.md`

**File:** `docs/ev/RUBRIC.md`

**What:** Add new checkers to their respective rubric areas. Add "Convergence" rubric area if absent.

**Why:** Rubric should list all checkers by area.

**Validation:** N/A (markdown).

#### Step 7.4 — Update `docs/repomap.md`

**File:** `docs/repomap.md`

**What:** Add `ccya/ev/checkers/ruling.py`, `ccya/ev/checkers/convergence.py`, `ccya/ev/checkers/state.py` to the checker module listing. Update any field references to include new checker fields. Add `CheckerConfig` to EngineConfig section.

**Why:** Repomap is the module index. Stale repomap = slower navigation.

**Validation:** `make check` passes.

#### Step 7.5 — Update `AGENTS.md`

**File:** `AGENTS.md`

**What:** No structural changes needed. Verify the "Execution rules" and "Known tooling notes" are still accurate. If `CheckerConfig` or new phases are relevant, add brief signpost.

**Why:** AGENTS.md must not be stale.

**Validation:** `make check` passes.

### Tests to write or update

- No tests needed (documentation only).
