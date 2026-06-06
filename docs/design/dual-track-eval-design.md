# Dual-Track Evaluation Design

## Purpose

Add a second evaluation track (`standard_session`) to CCYA's eval harness that measures aggregate gameplay quality rather than per-turn deterministic correctness, while preserving the existing `adversarial` track (full_cycle) for system integrity testing. This document is the design authority for plans implementing this change.

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

## Non-goals

- **No new judge types.** The four domain judges + meta judge handle both tracks; scoring philosophy is a rubric-level concern, not a judge architecture change.
- **No changes to the engine being tested.** This is purely an eval harness change.
- **No multi-run trend tracking across scenarios or tracks.** Regression detection remains "current run vs most recent prior run of same scenario."
- **No UI changes** to the game server, turn viewer, or narration interface.
- **No new pack system or seed generation mechanics.** Eval packs remain static; standard sessions use existing eval-pack infrastructure.

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

**2. Scoring philosophy baked into rubrics, not configurable per-track.** The default rubric scoring thresholds (3/5 = functional with minor issues; 5/5 = perfect execution) are appropriate for adversarial testing but wrong for standard sessions where LLM stochasticity means some misses are expected on every run.

**3. Auto-checker severity not differentiated in reporting.** Red and yellow failures both appear in the report's auto-checker table without clear visual distinction about which category they belong to. The `--gate` flag only blocks on red, but reports don't help users understand that a scenario with 24 failed assertions might be fine if most are yellow/perfection concerns.

**4. Regression detection doesn't account for track differences.** Comparing an adversarial run score against a standard session score is meaningless — they measure different things. The current system compares "most recent prior run of same scenario," which works but could be more explicit about what's being compared.

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
  track: str                    # NEW: "adversarial" or "standard_session"
```

Default value is `"adversarial"` for backward compatibility. Existing scenarios without a `track` field are treated as adversarial. New standard session scenarios explicitly set `track="standard_session"`.

#### Change 2: Add scoring philosophy to rubrics via front-matter metadata

Each judge rubric gains an optional YAML front-matter field that defines its track's scoring expectations:

```yaml
---
# track: "adversarial" | "standard_session" (default: "adversarial")
# adversarial_scoring: true if this rubric expects per-turn perfection
---
```

The meta judge reads the active scenario's `track` and passes it to domain judges via `_build_meta_judge_input()`. Domain judges that don't specify a track in their rubric default to adversarial scoring.

A new standard session-specific rubric (`evals/rubrics/standard_session.md`) overrides the default with:
- 3/5 = functional run with typical LLM noise (occasional extraction misses, minor directive drift)
- 4/5 = good experience overall despite stochastic imperfections
- 5/5 = consistently excellent across turns, mechanics meaningfully shape narrative

The scoring philosophy shift is in the rubric text that guides the judge's analysis, not in new code. The meta judge passes `track` to domain judges via a new field in the trace context.

#### Change 3: Auto-checker filtering by track

Universal auto-checkers continue running on all tracks (they test system integrity). But the report generation distinguishes red vs yellow failures visually and semantically:
- **Red failures** = system breakage, always flagged regardless of track
- **Yellow failures** = perfection concerns, de-emphasized in standard_session reports

The `--gate` flag behavior is unchanged (blocks on any red failure). This is a reporting change only.

#### Change 4: Report labeling

REPORT.md header includes the active track:

```markdown
# Eval Report — <scenario_id>

**Track:** adversarial | standard_session
**Scoring philosophy:** deterministic correctness | aggregate quality
...
```

Regression detection remains "current run vs most recent prior run of same scenario ID." The report explicitly labels what's being compared.

### Alternatives Considered and Rejected

**A) Separate judge rubrics per track instead of front-matter metadata.**
- What: Create entirely new judge types (e.g., `state_correctness_adversarial`, `state_correctness_standard`) with separate rubric files.
- Why rejected: Adds 4x the judge infrastructure, doubles config complexity, and creates maintenance burden for marginal benefit. The same judges can evaluate both tracks; only scoring philosophy differs, which is a prompt-level concern in the rubrics.

**B) Scenario-specific auto-checker filters instead of track-based filtering.**
- What: Add `universal_asserts_disabled` or `severity_filter` to TurnAssert/Scenario that lets scenario authors disable specific checks per-scenario.
- Why rejected: Too granular, encourages inconsistency across scenarios, and shifts the burden to scenario authors. Track-level filtering is simpler and covers all standard sessions uniformly without requiring each author to configure filters manually.

**C) New "quality score" metric separate from mechanical scores.**
- What: Add a new 8th score (e.g., `experience_score`) that measures player experience quality separately from system integrity.
- Why rejected: The existing narrative_score and system_cohesion_score already measure what players care about. Adding a redundant score creates confusion about which metric to trust. The difference is in *how* those scores are computed, not in adding new dimensions.

**D) Make the runner skip assertions on standard sessions entirely.**
- What: Standard session scenarios would run turns but check no assertions at all.
- Why rejected: Universal auto-checkers test system integrity (no parse failures, valid state deltas, mechanics don't crash). These are always valuable to verify regardless of scenario type. Skipping them entirely loses the ability to detect engine breakage during standard sessions.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Track field on Scenario | Add `track: str` with default `"adversarial"` to Scenario dataclass, valid values `"adversarial"`, `"standard_session"` | Backward compatible; existing scenarios unchanged; new scenarios opt in explicitly. Default preserves current behavior for all existing code paths. |
| Scoring philosophy via rubric front-matter | Add `# track: "..."` and scoring guidance to YAML front matter of judge rubrics; meta judge passes active scenario's track to domain judges via trace context | Keeps scoring philosophy where it belongs — in the text that guides LLM judgment. No new judge types, no config changes, no schema changes beyond what the judge already reads from its system prompt. |
| New standard_session rubric file | Create `evals/rubrics/standard_session.md` with adjusted scoring thresholds (3/5 = functional with typical LLM noise) for narrative_interplay and state_correctness judges on this track | The default rubrics assume deterministic correctness; a separate file provides the right expectations without modifying existing files. Prompt_pipeline meta judge uses same rubric regardless of track (prompt quality is system-level, not gameplay-dependent). |
| Auto-checker severity in reports | Report renders red failures prominently with "SYSTEM" label, yellow failures de-emphasized with "PACING/QUALITY" label and collapsible section header | Users can immediately distinguish engine breakage from perfection concerns. No functional change to assertion logic; purely a reporting improvement that helps interpret results across tracks. |
| Track labeling in REPORT.md | Header includes `**Track:** adversarial \| standard_session` and regression comparison explicitly notes track context | Prevents cross-track score comparison confusion. Makes it clear what the report is measuring before users read scores. |

## Failure Modes and Risks

**1. Rubric drift between tracks.** If the standard_session rubric doesn't clearly differentiate scoring expectations from adversarial, judges will still penalize LLM stochasticity as failures. Mitigation: write explicit examples of acceptable vs unacceptable behavior in each score band for the standard session rubrics.

**2. Scenario authors forget to set track.** New scenarios without `track="standard_session"` default to adversarial, which is safe but means they get adversarial scoring by accident. This is unlikely because creating a standard session scenario requires deliberate effort (writing organic-feeling inputs rather than hard assertions).

**3. Meta judge doesn't pass track context properly.** If `_build_meta_judge_input()` doesn't include the active scenario's `track` value, domain judges won't know which scoring philosophy to apply and will default to adversarial. This would silently produce wrong scores for standard sessions.

**4. Regression detection confusion across tracks.** If a user runs full_cycle (adversarial) then a new standard_session scenario, regression comparison against the prior run could be misleading if they share a scenario ID or if users don't read the track label. Mitigation: each scenario has a unique ID; regression only compares same-scenario-ID runs.

**5. Universal auto-checker false positives on standard sessions.** Some universal checks (e.g., `check_momentum_band_delta`) may flag valid LLM stochastic behavior as failures because they expect deterministic outcomes. These are yellow-severity pacing concerns, not system breakage, but users unfamiliar with the distinction might misinterpret them. Mitigation: clear labeling in reports and documentation of what each check measures.

## Open Questions

- `[OPEN: Should standard_session rubrics be separate files or inline modifications to existing rubrics?]` — Separate files avoid modifying proven adversarial rubrics but create duplication of shared scoring guidance. Inline modification with track-aware conditional text keeps a single source of truth but makes the rubric harder to read.
- `[OPEN: What happens if a scenario has both hard assertions and soft expectations on standard_session? Should hard asserts be allowed or discouraged?]` — Hard asserts test system integrity (always valid), but they may conflict with organic gameplay where mechanics don't fire on schedule. Need a policy decision.
- `[OPEN: Should the meta judge produce different score dimensions for each track, or just weight existing ones differently?]` — Keeping 7 identical scores across tracks is simpler but might not capture that standard sessions care more about narrative_score and less about extraction_accuracy_score.

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
- **CLI interface** — `python -m ccya.eval run`, `judge-only`, `pack`, `list` all work identically; no new flags required
- **Regression detection logic** — Still compares current run vs most recent prior run of same scenario ID
- **Pack system** — Eval packs remain static with seed_state.yaml; no changes to pack loading or resolution
- **Auto-checker severity model** — Red/yellow distinction already exists in assertion results; only report presentation improves

## New Model Shapes

```python
@dataclass
class Scenario:
    id: str
    pack: str
    description: str
    turns: list[Turn]
    seed_overrides: dict[str, Any] = field(default_factory=dict)
    track: str = "adversarial"  # NEW: valid values are "adversarial", "standard_session"
```

No new model shapes needed for judges or reports. The meta judge passes `track` as a string in the trace context that domain judges read from their system prompt (rubric front-matter).

## Context for Implementing LLMs

- **ccya/eval/scenario.py** — Add `track: str = "adversarial"` to Scenario dataclass; update load_scenario() logging
- **ccya/eval/judge.py** — Pass active scenario's track via `_build_meta_judge_input()` into domain judge system context; meta judge reads and propagates track
- **ccya/eval/report.py** — Add `track` field to REPORT.md header metadata section; render red/yellow failures with distinct labels in auto-checker table
- **ccya/eval/universal_asserts.py** — No changes needed (already returns severity per assertion); only report rendering uses this
- **ccya/eval/cli.py** — No changes needed (track is a scenario property, not a CLI flag)
- **ccya/eval/config.py** — No changes needed (no config-level track settings; each scenario declares its own)
- **docs/architecture/eval-harness.md** — Update architecture doc to document the two-track model and where track flows through the pipeline
