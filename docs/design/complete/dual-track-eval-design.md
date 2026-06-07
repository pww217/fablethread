# Dual-Track Evaluation Design

## Purpose

Add a second evaluation track (`baseline`) to CCYA's eval harness that measures aggregate gameplay quality under non-hostile conditions, while preserving the existing `adversarial` track (`full_cycle`) for system integrity testing. The baseline track becomes the default eval target. This document is the design authority for plans implementing this change.

## Problem Statement

The current eval system has a single scoring philosophy baked into every scenario: **per-turn deterministic correctness**. Every assertion expects specific mechanics to fire on schedule, and rubrics penalize any extraction miss or directive drift as a failure. This works fine for testing that the engine doesn't break (system integrity), but it produces misleading scores when evaluating actual gameplay quality of an LLM-based system where stochastic misses are expected.

The full_cycle scenario scored 1-2/5 across all categories because it forced edge cases and demanded perfect mechanic-narrative coupling on every turn. The cordyceps v3 session (same engine, same prompts) played organically with conditions working correctly, thread governance improving, and beat_locked firing — a fundamentally different quality of system that the current eval architecture cannot measure or score meaningfully.

The problem is not in the rubrics or auto-checkers themselves; it's that **the scoring philosophy assumes deterministic behavior** where every assertion should pass and every mechanic should fire on schedule. For an LLM-based interactive narrative engine, this conflates "LLM stochasticity" with "system bug."

## Constraints

- Must preserve all existing adversarial scenarios unchanged (full_cycle, any future ones).
- Must not change the core 5-call pipeline or engine mechanics being tested.
- Must reuse the same judge infrastructure (state_correctness, narrative_interplay, prompt_pipeline, meta) — no new judges.
- Must reuse the same universal auto-checkers — they test system integrity regardless of scenario type.
- The `python -m ccya.eval` CLI interface must remain backward compatible; existing commands work without modification.
- New scenarios must be discoverable via the existing `discover_scenarios()` mechanism.
- Reports from different tracks must not be compared against each other (regression detection only within track).
- Track is a scenario-level property, not a CLI or config flag. You run a specific scenario, and its track determines the scoring philosophy.

## Non-goals

- **No new judge types.** The four domain judges + meta judge handle both tracks; scoring philosophy is a rubric-level concern, not a judge architecture change.
- **No changes to the engine being tested.** This is purely an eval harness change.
- **No multi-run trend tracking across scenarios or tracks.** Regression detection remains "current run vs most recent prior run of same scenario."
- **No UI changes** to the game server, turn viewer, or narration interface.
- **No new pack system or seed generation mechanics.** Eval packs remain static; baseline sessions use existing eval-pack infrastructure.
- **No separate rubric files per track.** Single rubric per judge with YAML front-matter handles both tracks.

## Current State — What Exists

### Scenario Model (`ccya/eval/scenario.py`)

```
Scenario:
  id: str                       # unique name
  pack: str                     # which static pack to use
  description: str
  turns: list[Turn]
  seed_overrides: dict          # dotpath overrides to seed state

Turn:
  input: str                    # player command
  phase: str                    # free-text tag for grouping in reports
  expects: list[str]            # soft annotations (report only)
  asserts: list[TurnAssert]     # structured auto-checker assertions
```

Scenarios are Python modules with a module-level `scenario` attribute. Each turn has optional hard assertions (`asserts`) that the runner checks deterministically against events.jsonl, and soft expectations (`expects`) that appear as report annotations only.

### Runner Flow (`ccya/eval/runner.py`)

1. Load scenario → load pack → init save dir
2. For each turn: call `run_turn()`, capture TurnRecord, run `_check_asserts()` on structured asserts, run all 23 universal asserts
3. Write artifacts (events.jsonl, state.yaml, run.json) to isolated run directory

The runner has no concept of scenario type or scoring philosophy. It runs every scenario identically: execute turns → check assertions → write events.

### Auto-Checker System (`ccya/eval/universal_asserts.py`)

23 deterministic checks with two severity levels:
- **red** (must fix): system integrity — parse failures, state corruption, missing mechanics
- **yellow** (advisory): pacing/perfection concerns — beat variety, momentum floor runs, directive rendering

All 23 run on every event regardless of scenario. Failures are surfaced in the report; passes are discarded. The `--gate` flag exits 1 on any red failure.

### Judge System (`ccya/eval/judge.py`)

Four domain judges + meta judge, each receiving a filtered trace:
- **state_correctness**: mechanic lifecycle tables, state fidelity rate, extraction accuracy score (1-5)
- **narrative_interplay**: narrative score (1-5), system cohesion score (1-5)
- **prompt_pipeline**: prompt quality score (1-5), adherence rate, per-pipeline scores
- **meta**: synthesizes domain results into 7 final scores

Each judge uses a rubric markdown file that defines scoring philosophy. The default rubrics say: "3/5 is functional with minor issues; 5/5 requires genuinely excellent execution — no extraction misses." This assumes deterministic behavior.

### Report Generation (`ccya/eval/report.py`)

Produces REPORT.md with metadata, judge summary, flags (regressions, retries, failures), auto-checker table, pacing metrics, state comparison vs prior run, turn metrics. Regression detection compares against the most recent prior run of the same scenario ID.

### Problems with Current State

**1. No track/scenario type concept.** Every scenario is treated identically by the runner and judges. There's no way to signal "this scenario tests system integrity" vs "this scenario measures gameplay quality."

**2. Scoring philosophy baked into rubrics, not configurable per-track.** The default rubric scoring thresholds (3/5 = functional with minor issues; 5/5 = perfect execution) are appropriate for adversarial testing but wrong for baseline sessions where LLM stochasticity means some misses are expected on every run.

**3. Auto-checker severity not differentiated in reporting.** Red and yellow failures both appear in the report's auto-checker table without clear visual distinction about which category they belong to. The `--gate` flag only blocks on red, but reports don't help users understand that a scenario with 24 failed assertions might be fine if most are yellow/perfection concerns.

**4. Regression detection doesn't account for track differences.** Comparing an adversarial run score against a baseline session score is meaningless — they measure different things. The current system compares "most recent prior run of same scenario," which works but could be more explicit about what's being compared.

**5. Turn assertions are all-or-nothing.** A turn with 3 hard asserts that fails on assertion #2 counts the same as a turn where no mechanics fired at all. There's no distinction between "the system partially worked" and "the system broke."

## Proposed Solution

### Core Changes

#### Change 1: Add `track` field to Scenario model

```
Scenario:
  id: str                       # unique name (unchanged)
  pack: str                     # which static pack to use (unchanged)
  description: str              # unchanged
  turns: list[Turn]             # unchanged
  seed_overrides: dict          # dotpath overrides to seed state (unchanged)
  track: str                    # NEW: "adversarial" or "baseline"
```

Default value is `"adversarial"` for backward compatibility. Existing scenarios without a `track` field are treated as adversarial. New baseline scenarios explicitly set `track="baseline"`.

#### Change 2: Inject `track` into each domain judge's system prompt via `arch_context`

The design doc's original approach ("meta judge passes track to domain judges") is impossible because domain judges run *before* the meta judge and never see its output. Instead:

1. `_run_one_scenario()` in `cli.py` loads the scenario and has access to `scenario.track`.
2. It passes `track` to `run_judges()` in `judge.py`.
3. `run_judges()` injects the track as a line in `arch_context` (architecture context block that gets appended to each domain judge's system prompt after the rubric text).
4. Each domain judge's system prompt reads: `rubric_text + "\n\n" + arch_context`, where `arch_context` now includes `"Track: baseline"` or `"Track: adversarial"`.
5. Domain judges use this to modulate their scoring expectations. The rubric front-matter provides scoring guidance per track, and the system prompt's track line tells the judge which set of expectations to apply.

The meta judge does **not** need track context — it receives already-scored domain results and synthesizes them. Prompt_pipeline judge does **not** need track context either (prompt quality is system-level, not gameplay-dependent). Only `state_correctness` and `narrative_interplay` judges need track-aware scoring.

#### Change 3: Rubric front-matter for per-track scoring guidance

Each judge rubric (`state_correctness.md`, `narrative_interplay.md`) gains a YAML front-matter section with scoring expectations for both tracks:

```yaml
---
track: "adversarial"
adversarial_scoring: true
# 3/5: functional with minor issues, any extraction miss or directive drift drops score
# 4/5: most mechanics fire correctly, rare misses
# 5/5: genuinely excellent execution — no misses
---
```

The **baseline** scoring expectations are expressed in the same file as a separate section:

```markdown
## Baseline Track Scoring

Use these thresholds when the active track is "baseline":
- **3/5**: Functional run with typical LLM noise — occasional extraction misses, minor directive drift
- **4/5**: Good experience overall despite stochastic imperfections
- **5/5**: Consistently excellent across turns, mechanics meaningfully shape narrative
```

The system prompt line `"Track: baseline"` (injected via arch_context) tells the judge which section to use. If no track line is present, the judge defaults to adversarial scoring.

#### Change 4: Auto-checker severity labeling

Universal auto-checkers continue running on all tracks (they test system integrity). Report distinguishes red vs yellow failures visually:
- **Red failures** = system breakage, labeled `[SYSTEM]`, always flagged regardless of track
- **Yellow failures** = pacing/perfection concerns, labeled `[PACING]`, visible but visually de-emphasized

The `--gate` flag behavior is unchanged (blocks on any red failure). This is a rendering change only — no assertion logic changes.

#### Change 5: Report labeling

REPORT.md header includes the active track:

```markdown
# Eval Report — <scenario_id>

**Track:** adversarial | baseline
**Scoring philosophy:** deterministic correctness | aggregate quality
...
```

Regression detection remains "current run vs most recent prior run of same scenario ID." The report explicitly labels what's being compared.

#### Change 6: Default scenario in config

`evals/config.yaml` changes `default_scenario: full_cycle` to `default_scenario: baseline`. This makes `python -m ccya.eval run` (no args) run the baseline scenario by default. Existing adversarial scenarios remain accessible by name: `python -m ccya.eval run full_cycle`.

### Alternatives Considered and Rejected

**A) Separate judge rubrics per track instead of front-matter metadata.**
- What: Create entirely new judge types (e.g., `state_correctness_adversarial`, `state_correctness_baseline`) with separate rubric files.
- Why rejected: Adds 4x the judge infrastructure, doubles config complexity, and creates maintenance burden for marginal benefit. The same judges can evaluate both tracks; only scoring philosophy differs, which is a prompt-level concern in the rubrics.

**B) Scenario-specific auto-checker filters instead of track-based filtering.**
- What: Add `universal_asserts_disabled` or `severity_filter` to TurnAssert/Scenario that lets scenario authors disable specific checks per-scenario.
- Why rejected: Too granular, encourages inconsistency across scenarios, and shifts the burden to scenario authors. Track-level filtering is simpler and covers all baseline sessions uniformly without requiring each author to configure filters manually.

**C) New "quality score" metric separate from mechanical scores.**
- What: Add a new 8th score (e.g., `experience_score`) that measures player experience quality separately from system integrity.
- Why rejected: The existing narrative_score and system_cohesion_score already measure what players care about. Adding a redundant score creates confusion about which metric to trust. The difference is in *how* those scores are computed, not in adding new dimensions.

**D) Make the runner skip assertions on baseline sessions entirely.**
- What: Baseline scenarios would run turns but check no assertions at all.
- Why rejected: Universal auto-checkers test system integrity (no parse failures, valid state deltas, mechanics don't crash). These are always valuable to verify regardless of scenario type. Skipping them entirely loses the ability to detect engine breakage during baseline sessions. Additionally, baseline scenarios may carry structural asserts for critical system-integrity checks.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Track field on Scenario | Add `track: str` with default `"adversarial"` to Scenario dataclass, valid values `"adversarial"`, `"baseline"` | Backward compatible; existing scenarios unchanged; new scenarios opt in explicitly. Default preserves current behavior for all existing code paths. |
| Scoring philosophy via rubric front-matter | Add `## Baseline Track Scoring` section to each domain judge's rubric file; inject `"Track: baseline"` into domain judge system prompt via arch_context | Keeps scoring philosophy where it belongs — in the text that guides LLM judgment. No new judge types, no config changes, no schema changes beyond what the judge already reads from its system prompt. |
| Track propagation mechanism | `cli.py` passes `scenario.track` → `run_judges()` → appended to arch_context → each domain judge reads it in system prompt | Domain judges run before meta judge, so meta cannot propagate track to them. arch_context already appends architecture info to every domain judge's system prompt; track is just one more line. |
| Default scenario change | Set `default_scenario: baseline` in `evals/config.yaml` | `python -m ccya.eval run` (no args) runs the baseline scenario by default. Full_cycle still accessible by name. Track default stays `"adversarial"` for backward compat with existing scenarios. |
| Baseline scenario design | Organic narrative arc (10-13 turns) with `expects` annotations plus a few structural `asserts` for critical system-integrity checks | Hybrid approach: rubric-based scoring for gameplay quality, plus assert-level safety net against engine breakage. Authors keep asserts minimal. |
| Auto-checker severity in reports | Report renders red failures with `[SYSTEM]` label, yellow failures with `[PACING]` label. All failures visible in table regardless of track. | Users distinguish engine breakage from perfection concerns at a glance. No information hidden from reports. |
| Assert enforcement on baseline | Same assertion logic regardless of track. Failing asserts on baseline are hard failures (gate-worthy). | Baseline scenarios carry few asserts by design, but those they do carry test real system integrity. |
| Track naming | Track field value = `"baseline"`, scenario file = `evals/scenarios/baseline.py` | Matches user's mental model. Simpler term than "standard_session" for the track concept. |
| Track in `list` output | `python -m ccya.eval list` shows track column | Helps users discover which scenarios are baseline-friendly without reading each file. |
| Report track labeling | REPORT.md header includes `**Track:** adversarial \| baseline` | Prevents cross-track score comparison confusion. Makes clear what the report is measuring. |

## Failure Modes and Risks

**1. Rubric drift between tracks.** If the baseline rubric section doesn't clearly differentiate scoring expectations from adversarial, judges will still penalize LLM stochasticity as failures. Mitigation: write explicit examples of acceptable vs unacceptable behavior in each score band for the baseline rubric section.

**2. Scenario authors forget to set track.** New scenarios without `track="baseline"` default to adversarial, which is safe but means they get adversarial scoring by accident. This is unlikely because creating a baseline scenario requires deliberate effort (writing organic-feeling inputs rather than hard assertions). Additionally, the list command shows track, making omissions visible.

**3. arch_context not propagated.** If `run_judges()` doesn't receive or forward the track string, domain judges won't know which scoring philosophy to apply and will default to adversarial. Mitigation: `run_judges()` signature gains a `track: str` parameter; CLI caller always passes `scenario.track`.

**4. Regression detection confusion across tracks.** If a user runs full_cycle (adversarial) then a new baseline scenario, regression comparison against the prior run could be misleading if they share a scenario ID or if users don't read the track label. Mitigation: each scenario has a unique ID; regression only compares same-scenario-ID runs. Report header labels track explicitly.

**5. Universal auto-checker false positives on baseline sessions.** Some universal checks (e.g., `check_momentum_band_delta`) may flag valid LLM stochastic behavior as failures because they expect deterministic outcomes. These are yellow-severity pacing concerns, not system breakage, but users unfamiliar with the distinction might misinterpret them. Mitigation: clear `[SYSTEM]` vs `[PACING]` labeling in reports and documentation of what each check measures.

**6. Existing config.yaml customizations.** Users with `default_scenario` overridden in their local config won't automatically get the baseline scenario. This is correct behavior — local overrides express user intent and should not be overwritten.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| None (no removals) | N/A | This design adds capabilities without removing existing functionality. All current scenarios, judges, auto-checkers, and CLI flags remain unchanged. |

## What Is Unchanged

- **The 5-call engine pipeline** — Rules → Narrate → Scene Extract → State Extract → Storytell is untouched
- **StateDelta schema** — No new fields on any extraction result or state model
- **Universal auto-checker logic** — All 23 checks run identically; only report rendering differs
- **Judge filtering (`_JUDGE_EVENT_FIELDS`)** — Each judge still receives the same filtered event fields
- **Trace construction (`build_trace()`)** — Same deterministic signals, same per-turn blocks
- **CLI subcommands** — `python -m ccya.eval run`, `judge-only`, `pack`, `list` all work identically; no new flags required
- **Regression detection logic** — Still compares current run vs most recent prior run of same scenario ID
- **Pack system** — Eval packs remain static with seed_state.yaml; no changes to pack loading or resolution
- **Auto-checker severity model** — Red/yellow distinction already exists in assertion results; only report presentation improves
- **Meta judge rubric selection** — Meta judge uses same rubric regardless of track (synthesis scores don't need track awareness)
- **Prompt_pipeline rubric selection** — Prompt quality is system-level, not gameplay-dependent; same rubric regardless of track

## New Model Shapes

```python
@dataclass
class Scenario:
    id: str
    pack: str
    description: str
    turns: list[Turn]
    seed_overrides: dict[str, Any] = field(default_factory=dict)
    track: str = "adversarial"  # NEW: valid values are "adversarial", "baseline"
```

No new model shapes needed for judges, reports, or config. The track flows as a runtime parameter through `run_judges()` → `arch_context` → domain judge system prompt.

New scenario file `evals/scenarios/baseline.py` follows the same `Scenario` dataclass shape with `track="baseline"`.

## Context for Implementing LLMs

- **ccya/eval/scenario.py** — Add `track: str = "adversarial"` to Scenario dataclass; update `load_scenario()` logging
- **ccya/eval/judge.py** — Add `track: str` parameter to `run_judges()` function signature; inject into `arch_context` before passing to `build_trace_for_judge()` for domain judges. No change to `_run_single_judge()` signature (track lives in arch_context, which it already reads). No change to `_build_meta_judge_input()`.
- **ccya/eval/report.py** — Read `track` from `RunResult` (or `JudgeResult`) to display in REPORT.md header; render red/yellow failures with `[SYSTEM]` / `[PACING]` labels in auto-checker table
- **ccya/eval/runner.py** — Add `track` to `RunResult` dataclass so report can display it. The runner already stores `scenario.id` in RunResult; add `scenario.track` as well.
- **ccya/eval/cli.py** — Pass `scenario.track` to `run_judges()` call in `_run_one_scenario()`. No CLI flag changes.
- **ccya/eval/config.py** — No changes needed (track is a scenario property, not a config field). Default scenario pointer changes via `evals/config.yaml` value, not code default.
- **evals/config.yaml** — Change `default_scenario: full_cycle` to `default_scenario: baseline`
- **evals/scenarios/baseline.py** — New file: 10-13 turn organic narrative arc with `expects` annotations and minimal structural `asserts`, `track="baseline"`
- **evals/rubrics/state_correctness.md** — Add `## Baseline Track Scoring` section with adjusted scoring thresholds
- **evals/rubrics/narrative_interplay.md** — Add `## Baseline Track Scoring` section with adjusted scoring thresholds
- **evals/rubrics/prompt_pipeline.md** — No changes needed (prompt quality is system-level)
- **evals/rubrics/meta.md** — No changes needed (synthesis scores don't need track awareness)
- **docs/architecture/eval-harness.md** — Update architecture doc to document the two-track model and where track flows through the pipeline
