# Eval Methodology — Scenario Taxonomy, Checker Suites, and Aggregation Pipeline

## Purpose

Design authority for how CCYA evaluations are structured, what mechanics they test, how deterministic and LLM-based judgments compose, and how results aggregate into a master report. Not a plan — decisions here are final and guide implementation plans.

## Problem Statement

The tooling (`ccya/ev/` with play/check/eval) is built. What does not exist is:

1. **No evaluation scenarios** — `ev.py eval list` returns empty. Scenarios are the executable tests; without them the eval system does nothing.
2. **No checker-to-scenario mapping** — all deterministic + LLM checkers run on every scenario by default, polluting signals (a phase engine scenario should not run `npc_presence`).
3. **No aggregation methodology** — checker results are individual pass/fail with no framework for combining into a per-scenario or cross-scenario verdict.
4. **No LLM sampling strategy** — running all 3 LLM checkers on every turn of every scenario costs 8+ hours of inference time.
5. **No feedback loop** — there is no mechanism to surface "this mechanic fails most often" or suggest improvement targets.
6. **No Makefile targets** — there is no `make eval-full` or `make eval-{name}` workflow. Every eval requires manual command construction.
7. **Event fields exist but are unchecked** — 40+ fields in the event schema have no checker reading them (pacing_context, narrate_summary, rejected, changes.*, most ruling.* sub-fields).
8. **No CLI defaults** — `ev.py play --llm --turns 20 --pack zombie-survival --persona "weary survivor" --no-sanitize` is repetitive. Every run requires the same flag chain.
9. **No persona system** — the `--llm` mode has a generic system prompt that produces boring, repetitive player behavior. No way to define "villain," "hero," "reckless," etc.

## CLI Defaults and Personas

### Problem

The `ev.py play` command requires repetitive flag chains:
```bash
ev.py play --llm --turns 20 --pack zombie-survival --persona "weary survivor" --no-sanitize
```

Every eval run or manual test session requires the same flags. There is no way to define named personas (villain, hero, cautious, reckless) that change the LLM player's system prompt.

### Design: `ev:` section in config.yaml

Merge CLI defaults into the existing `config.yaml` under an `ev:` section. No new config file. No new infrastructure module — the loader lives in `ccya/ev/__init__.py` alongside `_strip_flags()`.

```yaml
# config.yaml additions

ev:
  # Default pack for new sessions (overrides --pack flag if absent)
  default_pack: zombie-survival

  # Default turn count for --llm mode
  default_turns: 20

  # Default persona name (resolved from personas registry below)
  default_persona: weary_survivor

  # Whether to skip sanitization (default false = sanitize enabled)
  # Mirrors --no-sanitize CLI flag semantics
  no_sanitize: false

  # Default model override (for --llm mode; engine model is separate)
  model: mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit-thinking

  # Default temperature for all LLM calls in --llm mode
  temperature: 0.9

  # Named persona registry — each has a description and system prompt
  personas:
    weary_survivor:
      description: "A weary survivor trying to find safety in a desolate wasteland"
      prompt: "You are a weary survivor in a hostile world. You are desperate, cautious, and driven by self-preservation. You take risks when necessary but prefer to find shelter and supplies. You react to danger with fear but push forward when cornered."

    villain:
      description: "A ruthless antagonist who manipulates and exploits"
      prompt: "You are a cunning villain in a text adventure. You manipulate NPCs, exploit weaknesses, and pursue your own agenda. You are calculating, cruel when useful, and always thinking several steps ahead. You do not act heroically."

    hero:
      description: "A brave hero who protects others and seeks justice"
      prompt: "You are a brave hero in a text adventure. You protect the weak, seek justice, and face danger head-on. You are courageous, compassionate, and willing to sacrifice for others. You do not back down from a fight."

    reckless:
      description: "A reckless thrill-seeker who lives on the edge"
      prompt: "You are a reckless thrill-seeker. You take dangerous risks, charge into danger without thinking, and live for the adrenaline. You are impulsive, bold, and often reckless. You do not play it safe."

    cautious:
      description: "A cautious survivor who plans carefully"
      prompt: "You are a cautious survivor. You plan carefully, avoid unnecessary risks, and scout ahead before acting. You are methodical, patient, and strategic. You prefer information over action."
```

### Usage

```bash
# Uses defaults from config.yaml (pack, turns, persona, model, temp)
ev.py play --llm --turns 10

# CLI flags override config
ev.py play --llm --pack space-western --persona villain --turns 5

# Single-turn play uses defaults
ev.py play "I search the room."
```

### Config merge priority

1. **Defaults** (hardcoded in `_strip_flags()` / `_build_play_config()`)
2. **Config file** (`config.yaml` → `ev:` section)
3. **CLI flags** (always win)

### Persona resolution

When `--persona NAME` is provided, the loader looks up `NAME` in `ev.personas` and uses that persona's `prompt` as the system prompt for the LLM player. If `--persona` is absent, uses `ev.default_persona`. If neither exists, falls back to the generic system prompt (current behavior).

### Eval integration

Eval scenarios can optionally use personas for `--llm` mode testing:
```yaml
id: eval-llm-player-persona
pack: zombie-survival
description: "Test that villain persona produces manipulative behavior"
llm_mode: true
persona: villain
turns:
  - input: "I approach the merchant."
  - input: "I try to scam the guard."
```

This is orthogonal to deterministic eval scenarios (fixed inputs, checker validation). Persona-based eval is for testing the LLM player behavior itself, not engine mechanics.

## Constraints

- **Judge model: Qwen3 35B** (`mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit-thinking`) at `localhost:8080/v1`. ~5-10 tok/s on Apple Silicon.
- **Host model: same Qwen3 35B.** Engine and judge are the same model; they never run simultaneously.
- **LLM calls are expensive for iteration.** Each LLM checker call takes 15-60s. At 100% coverage (~124 calls), a full eval takes ~41 minutes — fine for nightly runs but blocks rapid prompt iteration. Sampling (25%) brings it to ~9 minutes.
- **The consolidated data access layer (`ccya/ev/events.py`) is shared** across live-game testing, automated eval, and human CLI. TurnViewer will adopt it later. Do not create a second access path.
- **ev.py is the survivor.** No new top-level CLI tools. The Makefile orchestrates `ev.py eval run` targets.
- **No new infrastructure for orchestration.** `make` + `ev.py eval run` + `scripts/aggregate.py` = done.
- **No backward compatibility with old eval system.** Old `evals/` dir is already deleted.
- **Scenarios are YAML only.** No Python scenario classes.

## Non-goals

- **CI integration.** Triggering evals from CI is future work. This design covers local execution only.
- **Time-series dashboards.** Single-run reports only.
- **Replacing the old meta-judge with a new meta-judge.** See Decision Table.
- **Full coverage of all event fields.** Unchecked fields are documented gaps, not required coverage. New checkers are added per scenario need, not for 100% coverage.
- **Multi-model evaluation.** Always the same Qwen3 35B.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Scenarios declare checker suites | Each YAML has `checker_suite: [phase_transition, action_quality]` | No one-size-fits-all; keeps traces clean and eval fast |
| No meta-judge for score synthesis | `scripts/aggregate.py` (deterministic, ~80 lines) computes pass-rate, avg-score, worst-checker per scenario | The old meta-judge was an LLM untangling contradictions from domain judges. With individual checkers producing precise pass/fail on specific mechanics, deterministic math replaces it. No hallucination, no latency, no cost. |
| LLM checkers default to 100% with slider | `llm_sample_rate: float` in scenario YAML. Default 1.0. 0.25 for fast iteration. Trivial to implement. | 30-40 turns max means 100% is tolerable (~41 min full eval). Slider costs zero code complexity and serves the iteration use case. |
| LLM improvement suggestions are per-scenario-group, one batch call per group | For each scenario group with failures below threshold, one LLM call receives the failing checkers + up to 3 representative failing turns each. | Scenarios are focused by design, so failures naturally scope to a single pipeline stage's mechanics. The LLM never sees data from multiple stages at once. |
| Makefile orchestrates, Python does not | `make eval-full` runs 5 `ev.py eval run` commands + `aggregate.py`. No central Python eval orchestrator. | Make is idempotent, parallelizable (`make -j`), and zero new code to debug. Each `ev.py eval run` is independently testable. |
| Scenario groups are naming conventions + Makefile targets, not code abstractions | `scenarios/ruling-*.yaml` files; `make eval-ruling` globs that pattern. No `ScenarioGroup` class or registry. | The group is a convenience for ordering and report organization. Any scenario is independently runnable via `ev.py eval run`. Group ordering (ruling → extraction → narration → state → cross) is a suggestion, not a hard gate — nothing prevents running narration scenarios in isolation. |
| Aggregation is failure-rate based | Per-checker: pass/total ratio. Per-scenario: min(checker pass rates). Full report: min(scenario scores). | "Weakest link" metric surfaces the most broken mechanic. Average scores hide failures. |
| Improvement suggestions filter to failures | Only checkers with pass_rate < 0.8 (configurable) trigger suggestion calls. | Prevents wasted LLM calls on healthy mechanics. Threshold is high enough to catch real problems, low enough to avoid noise. |
| Unchecked event fields documented but not required | `docs/ev/UNCHECKED_FIELDS.md` lists every event field and whether a checker reads it | Prevents future developers from duplicating or assuming coverage that doesn't exist |
| TurnViewer adopts `ccya/ev/events.py` later | Same access layer, different output format | Already documented in ev-tooling-design.md. Enforced here. |
| CLI defaults merge into config.yaml under `ev:` section | `config.yaml` gains `ev:` section with `default_pack`, `default_turns`, `default_persona`, `no_sanitize`, `model`, `temperature`. No separate `ev-config.yaml`. | Keeps all config in one file. Avoids the "single YAML config" rejection (this is CLI defaults, not scenario definitions). Persona registry is data, not an abstraction layer. |
| Personas are defined in config.yaml under `ev.personas` | Named persona registry with `description` and `prompt` fields. Resolved by name at runtime. | Personas change the LLM player's system prompt, directly affecting behavior. Registry is a simple dict lookup — no classes, no inheritance, no framework. |
| `no_sanitize` defaults to `false` (sanitize enabled) | Config has `no_sanitize: false`. CLI `--no-sanitize` sets it to `true`. Mirrors current CLI semantics. | Sanitization is important for testing. Defaulting to enabled ensures eval runs catch sanitizer issues. |

## Resolved Questions

### LLM sample rate — default 1.0, slider is trivial

**Decision: Default to 100% (`llm_sample_rate: 1.0`), slider costs zero code complexity.** One float in scenario YAML. A separate `--sample-rate` CLI flag on `ev.py eval run` can override at runtime for iteration. The slider only matters for the iteration use case — nightly evals always run at 100%.

### Improvement suggestions — one batch call per scenario group

**Decision: One LLM call per scenario group that has failures below the threshold.** Since scenarios are focused by design (a narration scenario only runs beat/pacing/tone checkers), a batch call per group naturally gets narrow, focused input. The prompt contains: the scenario group name, the failing checkers with their pass rates, and up to 3 representative failing turns per checker. The LLM never sees data from multiple pipeline stages in a single call.

### Confidence metric — yes, but only as an annotation

**Decision: Include `confidence: str` on the ScenarioReport:** `"high"` (≥30 turns with deterministic results), `"medium"` (≥10 turns or LLM-sampled), `"low"` (<10 turns or heavy sampling). This is trivially computed from turn_count and llm_sample_rate. It's a single-line annotation in the report, not a weighting factor in the score.

### CLI defaults — merge into config.yaml under `ev:` section

**Decision: All CLI defaults live in `config.yaml` under `ev:` section.** No separate `ev-config.yaml`. The `ev:` section contains `default_pack`, `default_turns`, `default_persona`, `no_sanitize`, `model`, `temperature`. Config merge priority: defaults < config file < CLI flags.

### Personas — registry in config.yaml, resolved by name at runtime

**Decision: Personas are defined in `ev.personas` as a dict of `{name: {description, prompt}}`.** No persona classes, no inheritance. The `--persona NAME` flag resolves `NAME` from the registry and uses `prompt` as the LLM player's system prompt. If `--persona` is absent, uses `ev.default_persona`. If neither exists, falls back to the generic system prompt (current behavior).

### `no_sanitize` — defaults to `false` (sanitize enabled)

**Decision: `no_sanitize: false` in config. CLI `--no-sanitize` sets it to `true`.** Mirrors current CLI flag semantics. Sanitization is important for testing; defaulting to enabled ensures eval runs catch sanitizer issues.

## Current State — What Exists

### `ccya/ev/` package

Fully implemented per ev-tooling-design.md:
- Play command (single-turn, interactive, LLM-driven)
- Check command (per-turn, --all, --llm, --checker-model)
- Eval command (YAML scenario runner, checker aggregation, Markdown report)
- Checker library (11 deterministic + 3 LLM, registry, @register_checker)
- Data access layer (events.py)
- Scenario loader (YAML → Scenario dataclass)

### Checker inventory (27 total)

> **Note:** The convergence scoring redesign replaced the old `momentum_lifecycle`, `tension_delta`, `crisis_urgency_threshold`, `derive_enforce_relief`, and `consecutive_pressure_beats` machinery. New checkers validate convergence score computation, CLIMAX turn counting, phase transitions, beat-phase validity, breather enforcement, scene age tracking, roll band consistency, and thread/arc resolution.

| Checker | Type | Pipeline Stage |
|---|---|---|
| `action_quality` | deterministic | Ruling |
| `gm_beat_lifecycle` | deterministic | Narration |
| `pacing_directives` | deterministic | Narration |
| `inventory_integrity` | deterministic | Extraction |
| `conditions_lifecycle` | deterministic | Extraction |
| `location_change` | deterministic | Extraction |
| `npc_presence` | deterministic | Extraction |
| `thread_lifecycle` | deterministic | State (post-turn) |
| `arc_goal_updates` | deterministic | State (post-turn) |
| `sanitizer_lifecycle` | deterministic | State (post-turn) |
| `phase_transition` | deterministic | State (post-turn) |
| `phase_persistence` | deterministic | State (post-turn) |
| `recent_beats` | deterministic | State (post-turn) |
| `climax_turn_counting` | deterministic | State (post-turn) |
| `breather_enforcement` | deterministic | State (post-turn) |
| `scene_age_tracking` | deterministic | State (post-turn) |
| `roll_band_consistency` | deterministic | Ruling |
| `thread_resolution_validity` | deterministic | State (post-turn) |
| `new_thread_validity` | deterministic | State (post-turn) |
| `compendium_lifecycle` | deterministic | Extraction |
| `beat_phase_validity` | deterministic | Narration |
| `arc_resolution_validity` | deterministic | State (post-turn) |
| `goal_update_validity` | deterministic | State (post-turn) |
| `turn_assert` | deterministic | Cross-cutting |
| `directive_tone_match` | LLM | Narration |
| `beat_narrative_chain` | LLM | Narration |
| `state_fidelity` | LLM | Extraction |

### Convergence-specific checkers

The following checkers directly validate the convergence scoring and Curtain Call machinery:

| Checker | What It Validates |
|---|---|
| `climax_turn_counting` | `climax_turn_count` increments by 1 inside CLIMAX, resets to 0 on phase exit, starts at 1 on entry |
| `phase_transition` | Phase transitions respect convergence_score threshold, climax_turn_limit, breather max turns, and outcome_hint alignment |
| `phase_persistence` | Phases persist correctly across turns (no spurious transitions) |
| `recent_beats` | `recent_beats` sliding window structure, capacity, and ordering |
| `breather_enforcement` | BREATHER phase exits on urgency > 0 or breather_max_turns exceeded |
| `scene_age_tracking` | Scene age increments correctly, drives Scene Imperative and convergence score |
| `beat_phase_validity` | Beat types are valid for their phase (e.g., no `breathing_room` in base CLIMAX list) |
| `roll_band_consistency` | Roll band math is correct (matching `compute_band()` rules with partial ≤7 threshold) |
| `thread_resolution_validity` | Thread resolve fields are properly structured when storyteller emits them (Curtain Call compliance) |
| `new_thread_validity` | New threads have required fields (id, summary, urgency) |
| `arc_resolution_validity` | Arc resolution/visible_goal updates are consistent across turns |
| `goal_update_validity` | Goal update records are internally consistent |

### Scenario directory

`packs/` contains 6 game packs + `packs/eval/` with obsolete config files. Zero YAML eval scenarios exist.

### Unchecked event fields

40+ fields exist in turn events that no checker reads:
- `ruling.*` sub-fields beyond band (intent_verb, dice, difficulty, skill, stat_mod, diff_mod, cond_mod, raw_total, final_total, outcome_summary, total_ms, tokens_in, tokens_out)
- `narrate.*` timing fields (first_token_ms, total_ms, tokens_in, tokens_out)
- `extract.*` timing/retry fields
- `pacing_context.*` (directive, gate, outcome_hint, summary — some are partially read)
- `narrate_summary.*`
- `rejected` array
- `changes.*` (momentum, threads, facts, player, inventory)
- `state_snapshot.pc.*` (stats, bio, drive, conditions directly)
- `state_snapshot.arc.*` (goal_context, resolution, visible_goal directly)

### Problems with Current State

1. **No scenarios exist.** The eval tooling has nothing to run against.
2. **All checkers run on all scenarios.** A momentum scenario runs npc_presence, polluting the signal and wasting inference.
3. **No aggregation.** `ev.py eval run` produces a flat list of checker results. No per-scenario pass rate, no ranking, no cross-scenario comparison.
4. **LLM checkers are all-or-nothing.** Either run on every turn (too expensive) or not at all.
5. **No Makefile targets.** No discoverable entry point for "run the evals."
6. **40+ event fields are unchecked.** Problems can exist in ruled mechanics, pacing, and state fidelity without any checker catching them.
7. **Checkers read raw events directly** in some cases instead of using `ccya/ev/events.py`. The `_llm.py` prompt builder renders templates with `event.format()` rather than extracting only the needed fields.

## Proposed Solution

### Core Changes

#### 1. Scenario schema — add `checker_suite` and `llm_sample_rate`

Every eval YAML scenario declares which checkers it needs and whether to sample for LLM judges:

```yaml
id: ruling-convergence-basics
pack: some-pack
description: "convergence score components compute correctly, phase transitions work"
seed_overrides:
  scene.scene_phase: SETUP
checker_suite:
  - action_quality
  - pacing_directives
llm_checkers:
  - directive_tone_match
llm_sample_rate: 0.25
turns:
  - input: "Kick the door down with all your might"
  - input: "Push past the guard"
```

- `checker_suite`: deterministic checkers only. These run on every turn.
- `llm_checkers`: LLM-based checkers. Run only on sampled turns.
- `llm_sample_rate`: 0.0-1.0. 0 = skip all LLM checkers for this scenario.
- If `llm_checkers` is absent or empty, no LLM checkers run regardless of `llm_sample_rate`.

This keeps traces minimal: the LLM checker prompt for `directive_tone_match` gets only `{ruling.band, ruling.intent, narrate, scene_tags}` — no inventory, no threads, no state snapshot.

#### 2. Pipeline-gated scenario order

Scenarios run in pipeline stage order. A failure in an earlier stage gates later stages:

```makefile
STAGES = ruling extraction narration state cross
eval-ruling:
	ev.py eval run scenarios/ruling-*.yaml --report-dir reports/ruling/
eval-extraction: eval-ruling
	ev.py eval run scenarios/extraction-*.yaml --report-dir reports/extraction/
eval-narration: eval-extraction
	ev.py eval run scenarios/narration-*.yaml --report-dir reports/narration/
```

The Makefile enforces ordering via dependencies. If `eval-ruling` fails (exit code non-zero), `eval-extraction` doesn't run. This prevents cascading false signals: if momentum is broken, extraction tests that depend on momentum state produce misleading results.

Each stage is independently runnable: `make eval-narration` skips earlier stages that already passed.

#### 3. Aggregation pipeline — `scripts/aggregate.py`

Deterministic only. No LLM call for scoring.

```python
# scripts/aggregate.py

# Input: directory of Markdown reports from ev.py eval run
# Output: combined Markdown report with:
#   1. Per-scenario: checker pass rates, worst checker, turn count
#   2. Cross-scenario: worst overall checker, most-failing pipeline stage
#   3. Improvement targets: checkers with pass_rate < 0.8
#   4. (optional) Improvement suggestions: if --suggest, one LLM call per target

def parse_report(path: Path) -> ScenarioReport:
    """Parse a Markdown eval report into structured data."""

def aggregate(reports: list[ScenarioReport]) -> FullReport:
    """Compute per-checker pass rates, rank by failure rate."""

def format_report(full: FullReport) -> str:
    """Render as Markdown."""

def suggest_improvements(full: FullReport) -> str | None:
    """Optional: LLM generates fix suggestions for worst checkers."""
```

The `--suggest` flag is always opt-in. By default, aggregation is deterministic math.

#### 4. Improvement suggestions — per-scenario-group LLM call

When `--suggest` is passed, `aggregate.py`:

1. Groups scenario results by group (ruling, extraction, narration, state, cross)
2. For each group, finds checkers with pass_rate < 0.8 (configurable threshold)
3. If a group has no failing checkers, skip it — no suggestion call wasted
4. For each group with failures, builds one prompt containing:
   - Group name and what it tests
   - For each failing checker: description, pass_rate, sample size
   - The 3 worst-failing turns for the worst checker in the group (input text + relevant event fields + correct behavior)
5. Calls the LLM once per failing group with:
   ```
   System: "You are a QA engineer evaluating a game engine. Below are the
   failing mechanics from the {group_name} scenario group. For each failing
   checker, suggest the most likely root cause and a specific fix. Be
   precise: name the prompt section or engine logic that needs changing.
   If the failure is a data quality issue (missing event field), say so."
   ```
6. Appends suggestions as a section per group in the report

Since scenarios are focused by design, a group's failures are scoped to one pipeline stage's mechanics. The narration group's failures are all beat/pacing/tone failures. The LLM call is ~5-15s and produces focused, actionable suggestions. Worst case: 5 group calls if every group has failures.

#### 5. New checker opportunities from unchecked fields

| New Checker | Fields Read | Pipeline Stage | Priority |
|---|---|---|---|
| `ruling_arithmetic` | `ruling.raw_total`, `ruling.stat_mod`, `ruling.diff_mod`, `ruling.cond_mod`, `ruling.final_total` | Ruling | High — validates the mod math |
| `pacing_integrity` | `pacing_context.directive`, `narrate_summary.pacing_directive`, `pacing_context.gate`, `pacing_context.outcome_hint` | Narration | Medium — cross-checks two sources |
| `rejected_field_integrity` | `rejected`, `applied` | Extraction | Medium — rejected fields shouldn't appear in applied |
| `change_consistency` | `changes.inventory`, `applied.inventory_add`/`remove`, `changes.momentum`, `momentum_*` | Extraction | Medium — cross-check changes against applied |
| `extraction_retry` | `extract.retries` | Extraction | Low — should be 0 for healthy extraction |

#### 6. Scenario taxonomy — 5 groups, 12 scenarios

**Group 1: Ruling (3 scenarios)**

Tests: dice resolution, convergence score computation, phase transitions.

| Scenario | Turns | Checkers | What It Exercises |
|---|---|---|---|
| `ruling-convergence-basics` | 8 | action_quality, roll_band_consistency, pacing_directives | Convergence score 5 components compute correctly, threshold 3 fires CLIMAX |
| `ruling-difficulty-curve` | 6 | action_quality, roll_band_consistency | Difficulty modifiers, stat mods, cond mods all apply (partial ≤7 threshold) |
| `ruling-phase-transitions` | 8 | phase_transition, phase_persistence, climax_turn_counting, breather_enforcement | Ruling→CLIMAX from convergence score; CLIMAX→RESOLUTION from climax_turn_limit; BREATHER exit conditions |

No LLM checkers in this group. All mechanical, all deterministic.

**Group 2: Extraction (3 scenarios)**

Tests: inventory, conditions, NPCs, location.

| Scenario | Turns | Checkers | What It Exercises |
|---|---|---|---|
| `extraction-inventory-chain` | 8 | inventory_integrity, change_consistency, location_change | Pick up, use, drop items. No overdraw. Location changes emit. |
| `extraction-conditions-lifecycle` | 6 | conditions_lifecycle | Dedup, cap, TTL, trigger expiry |
| `extraction-npc-presence` | 6 | npc_presence, change_consistency | NPC extraction, tags, scene caps, departed archive |

Optional LLM: `state_fidelity` at 0.25 sample rate.

**Group 3: Narration (3 scenarios)**

Tests: GM beats, pacing directives, narrative tone, phase constraints, Curtain Call.

| Scenario | Turns | Checkers | What It Exercises |
|---|---|---|---|
| `narration-beat-lifecycle` | 8 | gm_beat_lifecycle, beat_phase_validity, pacing_directives | Beat types, surface_as, phase constraints, setback in pressure bucket |
| `narration-pacing-directives` | 8 | pacing_directives, scene_age_tracking, recent_beats | Directive rendering, outcome_hint correctness, Scene Imperative allowed list (setback replaces twist) |
| `narration-curtain-call` | 8 | gm_beat_lifecycle, thread_resolution_validity, beat_phase_validity | Curtain Call: thread_resolve on CLIMAX turn 1, "forced" escalation, phase exit at climax_turn_limit |

LLM checkers: `directive_tone_match` (0.25), `beat_narrative_chain` (0.25).

**Group 4: State (2 scenarios)**

Tests: thread lifecycle, goal updates, sanitizer runs.

| Scenario | Turns | Checkers | What It Exercises |
|---|---|---|---|
| `state-thread-lifecycle` | 10 | thread_lifecycle, arc_goal_updates | Thread add/update/resolve, visible_goal tracking |
| `state-sanitizer-lifecycle` | 10 | sanitizer_lifecycle, arc_goal_updates | Sanitizer thread ops, goal changes, no orphans |

No LLM checkers. All mechanical.

**Group 5: Cross-cutting (1 scenario)**

Tests: overall game coherence on a longer run with varied inputs.

| Scenario | Turns | Checkers | What It Exercises |
|---|---|---|---|
| `cross-long-run-game` | 20 | All deterministic + all LLM (sampled) | Everything works together. LLM at 0.1 sample. |

This is the closest thing to the old full-eval. It's expensive but comprehensive.

#### 7. Makefile targets

```makefile
# Eval targets

EVAL_REPORT_DIR = reports/eval

eval-ruling:
	ev.py eval run scenarios/ruling-convergence-basics.yaml --report-dir $(EVAL_REPORT_DIR)/ruling
	ev.py eval run scenarios/ruling-difficulty-curve.yaml --report-dir $(EVAL_REPORT_DIR)/ruling
	ev.py eval run scenarios/ruling-phase-transitions.yaml --report-dir $(EVAL_REPORT_DIR)/ruling

eval-extraction:
	ev.py eval run scenarios/extraction-inventory-chain.yaml --report-dir $(EVAL_REPORT_DIR)/extraction
	ev.py eval run scenarios/extraction-conditions-lifecycle.yaml --report-dir $(EVAL_REPORT_DIR)/extraction
	ev.py eval run scenarios/extraction-npc-presence.yaml --report-dir $(EVAL_REPORT_DIR)/extraction

eval-narration:
	ev.py eval run scenarios/narration-beat-lifecycle.yaml --report-dir $(EVAL_REPORT_DIR)/narration
	ev.py eval run scenarios/narration-pacing-directives.yaml --report-dir $(EVAL_REPORT_DIR)/narration
	ev.py eval run scenarios/narration-curtain-call.yaml --report-dir $(EVAL_REPORT_DIR)/narration

eval-state:
	ev.py eval run scenarios/state-thread-lifecycle.yaml --report-dir $(EVAL_REPORT_DIR)/state
	ev.py eval run scenarios/state-thread-resolution.yaml --report-dir $(EVAL_REPORT_DIR)/state
	ev.py eval run scenarios/state-sanitizer-lifecycle.yaml --report-dir $(EVAL_REPORT_DIR)/state

eval-cross:
	ev.py eval run scenarios/cross-long-run-game.yaml --report-dir $(EVAL_REPORT_DIR)/cross

# Full eval with aggregation
eval-full: eval-ruling eval-extraction eval-narration eval-state eval-cross
	python scripts/aggregate.py $(EVAL_REPORT_DIR) --output $(EVAL_REPORT_DIR)/full-report.md

# Full eval with improvement suggestions
eval-full-suggest: eval-full
	python scripts/aggregate.py $(EVAL_REPORT_DIR) --output $(EVAL_REPORT_DIR)/full-report.md --suggest

# Run a single stage by name
eval-stage:
	@if [ -z "$(STAGE)" ]; then echo "Usage: make eval-stage STAGE=ruling"; exit 1; fi
	$(MAKE) eval-$(STAGE)
```

### Alternatives Considered and Rejected

1. **Meta-judge for score synthesis.** 
   Rejected: The old system's meta-judge tried to untangle 12 concerns in one LLM call and produced low-signal scores. Deterministic aggregation (pass-rate, worst-checker) is faster, cheaper, and more honest. An LLM should not be asked to "synthesize" what simple arithmetic already computes.

2. **Python orchestration (a `ccya/ev/orchestrate.py`).**
   Rejected: Make is already installed, supports dependency tracking, parallel execution, and exit-code gating. Writing a Python orchestrator would duplicate Make's job with more code and less expressiveness.

3. **100% LLM checker coverage on all turns.**
   Rejected: 3 LLM checkers × 12 scenarios × avg 8 turns = 288 calls × ~30s = 2.4 hours. Sampling at 0.25 brings this to ~35 minutes of inference, or ~15 minutes with deterministic-only scenarios running first.

4. **Single YAML config for all scenarios.**
    Rejected: Each scenario is independently useful (`ev.py eval run scenarios/ruling-convergence-basics.yaml`). A central config file would split the scenario definition from the scenario file, creating a two-step workflow for what should be a single command.

4b. **Separate `ev-config.yaml` for CLI defaults.**
    Rejected: Merging into `config.yaml` under `ev:` section keeps all config in one file. The `ev:` section is for CLI defaults (pack, turns, persona, sanitize, model, temp), not scenario definitions. This is orthogonal to the scenario rejection in #4. Persona registry is a simple dict lookup — data, not an abstraction layer.

5. **One big checker that reads every available field.**
   Rejected: This recreates the monolithic rubric problem. Narrow checkers with clean inputs produce actionable results. A "momentum arithmetic failed on turn 3: stat_mod -1 not applied" is useful. "Your game is 68% correct" is not.

## Failure Modes and Risks

1. **Scenario-pipeline gating creates cascade failures.** If `eval-ruling` hits an infrastructure issue (LLM down, file permission), no later stages run. Mitigation: each stage is independently runnable. The Makefile dependency is a suggestion, not a hard gate.

2. **LLM checkers with sampling miss real failures.** A bug that manifests on exactly the unsampled turns produces a false negative. Mitigation: scenarios designed to exercise specific mechanics repeatedly (8+ turns) make sampling error less likely. Cross-cutting long-run at 0.1 is explicitly documented as low-confidence.

3. **Aggregation is lossy.** Reducing 32 checker results to a single pass_rate loses distribution shape. A 0.75 pass rate could mean "75% of turns perfect, rest fully broken" or "every turn 75% correct." Mitigation: the full report preserves per-turn results in appendices. The aggregated view is a summary, not a replacement.

4. **Scenarios drift from engine changes.** A new engine feature (e.g., a new `applied` field) has no corresponding checker until one is written. Mitigation: the unchecked-fields doc is updated as part of every engine change per AGENTS.md rules. When a field becomes populated, a checker should exist or a gap is documented.

5. **Improvement suggestions from a single LLM call are low-confidence.** The model sees 3 failing turns and produces a root cause analysis. It might hallucinate. Mitigation: suggestions are clearly marked as "AI-generated, verify before acting." They are advisory only.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| Old "all checkers on all scenarios" default | `ccya/ev/eval.py` `cmd_eval_run()` | Replaced by `checker_suite` field in scenario YAML |
| Fallback-to-all-checkers logic | `ccya/ev/eval.py` line 101 | When `checker_suite` is absent, skip (don't default to all) |
| Old `evals/` directory reference | `scripts/debug/README.md` | Already deleted, but any remaining reference is removed |

## What Is Unchanged

- Existing checker implementations (momentum.py, inventory.py, etc.) — their logic and field access patterns remain
- `ccya/ev/checkers/__init__.py` — registry, CheckerResult, run_checker all unchanged
- `ccya/ev/events.py` — shared data access layer unchanged
- `ccya/ev/play.py` — play command unchanged
- `ccya/ev/check.py` — check command unchanged (still useful for ad-hoc per-turn debugging)
- `ccya/ev/eval.py` `cmd_eval_list()` — unchanged
- `ccya/ev/scenario.py` — Scenario/ScenarioTurn/TurnAssert dataclasses unchanged
- Pipeline stage order (ruling → extraction → narration → state) — already enforced by the engine pipeline

## New Model Shapes

```python
# Scenario — two new optional fields
@dataclass
class Scenario:
    id: str
    pack: str
    description: str
    turns: list[ScenarioTurn]
    seed_overrides: dict[str, Any] = field(default_factory=dict)
    checker_suite: list[str] | None = None       # NEW: deterministic checkers for this scenario
    llm_checkers: list[str] | None = None         # NEW: LLM checkers for this scenario
    llm_sample_rate: float = 0.0                  # NEW: 0 = no LLM sampling

# ScenarioReport — structured output from parsing an eval report
@dataclass
class ScenarioReport:
    scenario_id: str
    turn_count: int
    turns_with_errors: int
    checker_results: dict[str, CheckerStats]
    improvement_targets: list[str]  # checker_ids with pass_rate < threshold

@dataclass
class CheckerStats:
    checker_id: str
    checker_type: str
    total_runs: int
    passed: int
    failed: int
    inconclusive: int
    pass_rate: float       # passed / total_runs
    avg_score: float       # average score across all runs
    worst_turn: int | None # turn with lowest score
    findings_count: int    # total findings across all runs

# FullReport — output of aggregation
@dataclass
class FullReport:
    generated_at: str
    scenarios: list[ScenarioReport]
    cross_scenario: CrossScenarioStats
    improvement_suggestions: str | None  # None unless --suggest

@dataclass
class CrossScenarioStats:
    total_turns: int
    total_failures: int
    worst_checker: str            # checker with lowest avg pass_rate
    worst_pipeline_stage: str     # pipeline group with most failures
    improvement_targets: list[str]  # unique checker_ids below threshold
```

## Context for Implementing LLMs

- `ccya/ev/scenario.py` — `Scenario` dataclass. Add fields and update `load_scenario()` to parse `checker_suite`, `llm_checkers`, `llm_sample_rate`.
- `ccya/ev/eval.py` `cmd_eval_run()` — Update to use `checker_suite` and `llm_checkers` from scenario. Add sampling logic for LLM checkers (select random subset of turns).
- `ccya/engine/config.py` — Model config defaults. The `--checker-model` flag in ev.py dispatch should use the OpenAI-compatible endpoint (localhost:8080/v1), not `mlx_lm` directly.
- `ccya/ev/checkers/_llm.py` — Currently uses `mlx_lm import load`. Must switch to `localhost:8080/v1` OpenAI-compatible API via `llm_client.py`. This is the fix for EV-9.
- `ccya/ev/events.py` — `extract_field()` is the correct way for checkers to read event data. Some checkers bypass it. Enforce in the LLM checker prompt builders.
- `packs/` — Directory for YAML scenario files. Create `packs/eval/scenarios/` subdirectory.
- The Makefile has targets: `eval-ruling`, `eval-extraction`, `eval-narration`, `eval-state`, `eval-cross`, `eval-full`, `eval-full-suggest`.
- `eval-full` runs all 5 groups in order and then `aggregate.py`.
- `eval-full-suggest` adds `--suggest` to the aggregation call.
- Each group target is independently runnable: `make eval-narration`.
- Group ordering is a soft gate — nothing in code prevents running narration before ruling; the ordering is a Makefile convention that reflects the engine pipeline's data flow. Any scenario can be run standalone via `ev.py eval run scenarios/ruling-convergence-basics.yaml`.
- `--sample-rate` CLI flag on `ev.py eval run` overrides `llm_sample_rate` at runtime, enabling fast iteration without editing YAML.
- `--report-dir` flag on `ev.py eval run` writes the scenario's Markdown report to a subdirectory, which `aggregate.py` then reads. No centralized state needed — each eval target writes independent files.
- `ccya/ev/__init__.py` — Add `load_ev_config()` function that reads `config.yaml` and extracts the `ev:` section. Called by `_build_play_config()` in `play.py` to merge defaults before CLI flags.
- `config.yaml` — Gains `ev:` section with `default_pack`, `default_turns`, `default_persona`, `no_sanitize`, `model`, `temperature`, and `personas` registry.
- Persona resolution: `--persona NAME` looks up `NAME` in `ev.personas` dict. Uses `prompt` field as LLM player system prompt. Falls back to `ev.default_persona` if `--persona` absent. Falls back to generic prompt if neither exists.
- Eval scenarios can optionally use `llm_mode: true` and `persona: NAME` for testing LLM player behavior (separate from deterministic eval scenarios).

### Nice to Have: Live UI Streaming for Evals

Eval saves land in `saves/ev/{timestamp}-{hash}/events.jsonl`. The UI's existing infrastructure already supports viewing them:

- **Save listing:** `GET /api/saves` scans `saves/` and excludes only `default`. Eval saves would appear automatically if the exclusion list includes `ev/`.
- **TurnViewer:** Reads `events.jsonl` generically. No eval-specific code needed. Switching to an eval save displays it like any other game.
- **Live streaming:** `/turn_viewer/stream` polls `events.jsonl` mtime every 1s via SSE. `/turn_viewer/data` returns full turn JSON. The client merges updates into the UI.

**How it works:** Start an eval run (`ev.py eval run ...`). The file gets written incrementally — new lines appended as each turn completes. Start the TurnViewer, select the eval save, and watch it populate in real-time. No new streaming infrastructure needed. The mtime polling picks up new lines as they're written.

**Changes required:**
1. Add `ev/` to the save directory exclusion list in `/api/saves` (routes.py:113-178) so eval saves appear in the save picker
2. Add a save picker dropdown to the TurnViewer page so the user can switch between normal saves and eval saves
3. When an eval save is selected, point the streaming endpoint to `saves/ev/{name}/events.jsonl` instead of the default save

No new SSE endpoint. No new streaming infrastructure. Reuses the existing TurnViewer streaming mechanism entirely. The "live streaming during an eval run" works because the file is appended to incrementally — the polling picks up new lines as they're written.

**What you see:** Completed turns populate one-by-one as each turn finishes. Each turn appears fully rendered with ruling, narrative, extraction, and state all done.

**What you don't see:** Mid-turn pipeline phases (ruling → narrate → extract → state). The SSE streaming (`/turn?input=`) that shows `phase` events in real-time is for the human-in-the-loop gameplay path. Eval runs the pipeline programmatically — it doesn't hit the SSE endpoint. The events.jsonl gets written after each turn completes, not during.

### Even Nicer to Have: Mid-Turn Pipeline Visibility

Showing ruling phases, narrate streaming, moodlet updates, and in-flight state diffs during an eval run would require:

1. **New streaming endpoint** — either a separate SSE endpoint that exposes in-flight turn state, or a debug endpoint that the UI polls for the current turn's pipeline progress
2. **Pipeline phase logging** — the eval runner would need to log phase transitions to a file or in-memory state that the UI can read
3. **UI changes** — the TurnViewer would need a "live mode" that shows partial turn data (ruling band, beat surface, streaming narrative) before the turn is complete

This is a separate feature from the "nice to have" above. It requires new infrastructure: a new endpoint, new logging hooks in the eval runner, and new UI components for partial turn display. Not required for the eval system to be useful. If it's worth building, it should be scoped as its own design.
