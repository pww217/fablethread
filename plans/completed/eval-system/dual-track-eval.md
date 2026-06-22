# Dual-Track Eval Implementation

## Purpose

Add a `baseline` eval track that measures aggregate gameplay quality under non-hostile conditions, make it the default eval target, and preserve the existing `adversarial` track for system integrity testing.

## Problem Statement

The eval harness has one scoring philosophy baked into every scenario: per-turn deterministic correctness. Assertions expect specific mechanics to fire on schedule, and rubrics penalize any extraction miss as failure. This produces **misleading scores** when evaluating actual gameplay quality because LLM stochasticity is conflated with system bugs. The full_cycle scenario scores 1-2/5 even when the engine is working correctly, while organic play sessions show fundamentally better quality that the current architecture cannot measure.

## Constraints

- All existing adversarial scenarios remain unchanged (full_cycle, etc.).
- No changes to the 5-call pipeline or engine mechanics.
- No new judge types — reuse the four domain judges + meta judge.
- Universal auto-checkers run identically on both tracks (report rendering differs).
- CLI backward-compatible: `python -m ccya.eval run full_cycle` works identically.
- Track is a scenario property, not a CLI or config flag.

## Non-goals

- No engine changes.
- No new judge types.
- No multi-run trending or cross-track regression.
- No UI changes.
- No new pack system changes.
- No separate rubric files per track — single rubric per judge with per-track sections.

## Solution

Six phases: add `track` to scenario and run result dataclasses, thread it through the judge pipeline (cli.py → run_judges → arch_context), update judge rubrics with baseline scoring guidance, update report formatting, change the default scenario in config and display track in `list`, and create the baseline scenario file. Each phase is independently testable.

## Firm decisions

1. Track field name: `track` with valid values `"adversarial"` and `"baseline"`.
2. Default track: `"adversarial"` (backward compat for existing scenarios).
3. Propagation mechanism: `cli.py` passes `scenario.track` → `run_judges()` → appended to `arch_context` → domain judge system prompt.
4. Rubric approach: single file per judge with `## Baseline Track Scoring` section. No separate rubric files.
5. Baseline scenario design: organic narrative arc (10-13 turns) with `expects` annotations plus minimal structural `asserts`.
6. Auto-checker labeling: `[SYSTEM]` (red) and `[PACING]` (yellow) labels. All failures visible.
7. Assert enforcement: same logic regardless of track. Failing asserts are hard failures.
8. Default scenario: change `default_scenario: full_cycle` to `default_scenario: baseline` in `evals/config.yaml`.
9. Track in `list`: yes, show a track column.
10. Config: no new config fields needed.

## Risks, Ambiguities, and Blockers

- The `build_trace_for_judge()` function passes `arch_context=""` for `narrative_interplay`. This must be fixed to propagate the track line — the judge currently gets no architecture context at all.
- `RunResult` is serialized to JSON via `asdict()`; adding `track` to it means old saved runs won't have the field. `load_run_result()` filters by `__dataclass_fields__`, so missing fields get the new default (`"adversarial"`). Correct by design.
- Baseline scenario quality depends entirely on prompt writing — the file itself is straightforward `Scenario` construction.

## Status

`completed`

## Phases

6 phases: Data model → Track propagation → Rubric updates → Report formatting → Config + CLI list → Documentation.

---

## Implementation — Phase 1: Data model + config

### Context files to load

- `ccya/eval/scenario.py`
- `ccya/eval/runner.py` (RunResult class, line 80)
- `ccya/eval/cli.py` (`_cmd_list`, line 271)
- `evals/config.yaml`

### Detailed steps

#### Step 1.1 — Add `track` field to Scenario dataclass

**File:** `ccya/eval/scenario.py:51-57`

**What:** Add `track: str = "adversarial"` field to the `Scenario` dataclass. Update `load_scenario()` logging at line 76 to log the track value.

**Why:** The scenario declares its own track. Default `"adversarial"` means existing scenarios without the field are treated as adversarial — zero migration.

**Validation:** `python -c "from ccya.eval.scenario import Scenario; s = Scenario(id='test', pack='p', description='d', turns=[]); assert s.track == 'adversarial'; s2 = Scenario(id='t', pack='p', description='d', turns=[], track='baseline'); assert s2.track == 'baseline'"`

#### Step 1.2 — Add `track` field to RunResult dataclass

**File:** `ccya/eval/runner.py:79-95`

**What:** Add `track: str = "adversarial"` to the `RunResult` dataclass.

**Why:** The report reads `RunResult` to display track in the REPORT.md header. `load_run_result()` filters JSON keys against `__dataclass_fields__`, so old saved runs gracefully default to `"adversarial"`.

**Validation:** `python -c "from ccya.eval.runner import RunResult; r = RunResult(scenario_id='t', pack='p', model='m', temperature_override=None, started_at='', finished_at='', save_dir='', output_dir='', events_jsonl_path='', state_yaml_path=''); assert r.track == 'adversarial'"`

#### Step 1.3 — Change default scenario in config

**File:** `evals/config.yaml:4`

**What:** Change `default_scenario: full_cycle` to `default_scenario: baseline`.

**Why:** Makes `python -m ccya.eval run` (no scenario arg) run the baseline scenario by default. `full_cycle` remains accessible by name `python -m ccya.eval run full_cycle`.

**Validation:** `grep 'default_scenario' evals/config.yaml | grep baseline`

#### Step 1.4 — Show track in `list` command

**File:** `ccya/eval/cli.py:271-282`

**What:** In `_cmd_list()`, load `scenario.track` and display it in the list output. Change the format from `{sc.id:20s} pack={sc.pack:14s} turns={len(sc.turns)}` to `{sc.id:20s} track={sc.track:10s} pack={sc.pack:14s} turns={len(sc.turns)}`.

**Why:** Helps users discover which scenarios are baseline-friendly without reading each file.

**Validation:** `python -m ccya.eval list` shows track column for every scenario.

#### Step 1.5 — Populate `track` in `RunResult` constructor

**File:** `ccya/eval/runner.py:552-565`

**What:** Add `track=scenario.track` to the `RunResult(...)` constructor call in `run_scenario()`.

**Why:** Without this, `run_result.track` stays `"adversarial"` (the dataclass default) regardless of what the scenario declares. The report reads from `RunResult`, so it must be populated at creation time.

**Validation:** Run `python -m ccya.eval run full_cycle --no-judge` and check `evals/runs/latest/artifacts/full_cycle.run.json` contains `"track": "adversarial"` (the default). Baseline-tagged validation happens in Phase 5 when the scenario file exists.

### Tests to write or update

None (tests temporarily removed during refactor).

---

## Implementation — Phase 2: Track propagation

### Context files to load

- `ccya/eval/cli.py` (`_run_one_scenario`, line 88)
- `ccya/eval/judge.py` (`run_judges`, line 1027; `build_trace_for_judge`, line 166)

### Detailed steps

#### Step 2.1 — Pass `track` from CLI to `run_judges()`

**File:** `ccya/eval/cli.py:139-146`

**What:** Pass `track=scenario.track` to the `run_judges()` call. The scenario is already loaded above at line 95.

```python
# After line 139, before judge_results = await run_judges(...)
# Add track=scenario.track to the run_judges call
```

**Why:** The scenario's track is set at load time; the CLI is the first caller in the chain that has access to both the scenario and `run_judges()`.

**Validation:** `grep -n 'track=scenario.track' ccya/eval/cli.py`

#### Step 2.1b — Pass `track` from `judge-only` command to `run_judges()`

**File:** `ccya/eval/cli.py:232-239`

**What:** Add `track=rr.track` to the `run_judges()` call in `_cmd_judge_only()`. After Phase 1, `rr.track` exists on the loaded `RunResult`.

**Why:** The `judge-only` command re-runs judges against a prior run's events. Without this, it always passes the default `"adversarial"` track, silently scoring baseline runs under adversarial rules.

**Validation:** `grep -n 'track=rr.track' ccya/eval/cli.py`

#### Step 2.2 — Add `track` parameter to `run_judges()` signature

**File:** `ccya/eval/judge.py:1027-1037`

**What:** Add `track: str = "adversarial"` as a keyword parameter to `run_judges()`.

**Why:** The design doc mandates track is a scenario-level property; `run_judges()` must receive it to propagate it into domain judge contexts.

**Validation:** `mypy ccya/eval/judge.py --check-untyped-defs` (no errors for the new param type)

#### Step 2.3 — Inject track into `arch_context`

**File:** `ccya/eval/judge.py:1083-1087`

**What:** After the existing `arch_context` is loaded (line 1085), append the track label:

```python
arch_context = arch_context.rstrip() + f"\n\n**Track:** {track}" if track != "adversarial" else arch_context
```

Only append for non-default track to minimize diff in adversarial runs. The track line goes into `arch_context`, which is appended after the rubric text in `_run_single_judge()` (line 980).

**Why:** arch_context already delivers architecture info to every domain judge's system prompt. Adding the track there means domain judges see `"Track: baseline"` as the last line of their system prompt, telling them which rubric section to apply. No new plumbing needed — `build_trace_for_judge()` already passes `arch_context` for `state_correctness` and `prompt_pipeline`.

**Validation:** Add a debug log line after the injection, run `python -m ccya.eval run baseline` with `--no-judge` (runner only), check logs for the track string.

#### Step 2.4 — Fix `narrative_interplay` branch to pass `arch_context`

**File:** `ccya/eval/judge.py:212-219`

**What:** Change the `narrative_interplay` branch from `arch_context=""` to `arch_context=arch_context`.

**Why:** The `narrative_interplay` branch is the only domain judge branch that currently discards `arch_context`. This is a pre-existing bug — the narrative_interplay judge doesn't receive architecture context at all. Fixing it is required for track propagation to reach this judge.

**Validation:** `python -c "from ccya.eval.judge import build_trace_for_judge; help(build_trace_for_judge)"` — no errors. Spot-check: trace for narrative_interplay now includes architecture context when provided.

### Tests to write or update

None (tests temporarily removed).

---

## Implementation — Phase 3: Rubric updates

### Context files to load

- `evals/rubrics/state_correctness.md`
- `evals/rubrics/narrative_interplay.md`
- `docs/design/dual-track-eval-design.md` (Baseline Track Scoring section for reference)

### Detailed steps

#### Step 3.1 — Add Baseline Track Scoring to `state_correctness.md`

**File:** `evals/rubrics/state_correctness.md`

**What:** Insert a `## Baseline Track Scoring` section after the existing scoring philosophy block (line 17-21). The section covers extraction accuracy and mechanic lifecycle scoring under baseline conditions:

```markdown
## Baseline Track Scoring

Use these thresholds when the active track is "baseline":
- **5/5**: Extraction consistently accurate (±1 miss across 13 turns), state tracking correct, all mechanics fire logically. Minor LLM stochasticity (field ordering, phrasing) is expected and ignored.
- **4/5**: Good mechanical fidelity despite 2-3 extraction misses. No critical state corruption. Engine responds correctly to mechanic triggers.
- **3/5**: Functional run with typical LLM noise — scattered extraction misses, minor field drift across 1-2 mechanics. No engine breakage.
- **1-2/5**: Repeated extraction failures, state fields diverging from narrated events, or a mechanic class entirely absent.
```

**Why:** The existing scoring assumes perfect execution. Baseline scoring accepts LLM-level stochastic noise and scores on "does the engine work correctly" rather than "did every field serialize exactly."

**Validation:** Running `python -m ccya.eval run baseline` with judges should produce narrative_score and mechanical_score that reflect the adjusted thresholds (not a 1-2/5 floor). Validate by inspection of REPORT.md scores.

#### Step 3.2 — Add Baseline Track Scoring to `narrative_interplay.md`

**File:** `evals/rubrics/narrative_interplay.md`

**What:** Insert a `## Baseline Track Scoring` section after the existing scoring philosophy block (line 20-25):

```markdown
## Baseline Track Scoring

Use these thresholds when the active track is "baseline":
- **5/5**: Narration consistently honors directives, tone matches momentum, beats create story consequence. Stray prose imperfections (minor anachronisms, slightly repetitive phrasing) are expected and ignored.
- **4/5**: Good narrative-mechanic coupling. Occasional directive drift (1-2 turns) or a beat that lands without narrative effect. Overall experience is coherent.
- **3/5**: Functional storytelling with typical LLM noise — 3+ directive misses, periodic tone-band disconnects, but no systematic breakdown.
- **1-2/5**: Directives routinely ignored, tone disconnected from momentum band, mechanics produce no story consequence.
```

**Why:** Same philosophy shift — narrative interplay scoring under baseline accepts stochastic prose variation and scores on "does the narrative correctly reflect the game state" rather than "is the prose perfect."

**Validation:** Same as 3.1 — inspect REPORT.md after a baseline run.

### Tests to write or update

None.

---

## Implementation — Phase 4: Report formatting

### Context files to load

- `ccya/eval/report.py` (`write_full_report`, line 854; `_render_auto_checker_block`, line 596; `_render_assert_summary_table`, line 615)

### Detailed steps

#### Step 4.1 — Add track line to REPORT.md header

**File:** `ccya/eval/report.py:903-917`

**What:** After the existing header metadata lines (pack, model, temp, timing), add:

```python
parts.append(f"**Track:** {run_result.track}  ")
```

And after the "Compared against" line, insert a scoring philosophy hint:

```python
if run_result.track == "baseline":
    parts.append("**Scoring philosophy:** aggregate quality (baseline)  ")
else:
    parts.append("**Scoring philosophy:** per-turn deterministic correctness (adversarial)  ")
```

**Why:** The report must label the active track so users know which scoring philosophy generated the scores. Prevents cross-track comparison confusion.

**Validation:** Run `python -m ccya.eval run baseline --no-judge`, inspect `evals/runs/latest/REPORT.md` header for `**Track:** baseline` and `**Scoring philosophy:** aggregate quality`.

#### Step 4.2 — Add `[SYSTEM]` / `[PACING]` labels to auto-checker table

**File:** `ccya/eval/report.py:596-612` (`_render_auto_checker_block`) and `ccya/eval/report.py:641-654` (`_render_assert_summary_table`)

**What:** In `_render_auto_checker_block`, change the emoji status indicators to labeled text:

```
Current: "✅" / "❌"
New:     "[PASS]" / "[FAIL]"
```

In `_render_assert_summary_table`, change severity emojis to labeled text:

```
Current: "🔴" / "🟡"  
New:     "[SYSTEM]" / "[PACING]"
```

Also add a legend line below the table header:

```markdown
> **Legend:** `[SYSTEM]` = system integrity failure (red severity) · `[PACING]` = pacing/perfection concern (yellow severity)
```

**Why:** Emoji rendering is platform-dependent and visually ambiguous. Text labels are unambiguous, screen-reader-friendly, and consistent with the design's goal of clearly distinguishing engine breakage from perfection concerns.

**Validation:** Inspect auto-checker table in REPORT.md after any eval run. Labels should show `[SYSTEM]` for red-severity failures and `[PACING]` for yellow.

### Tests to write or update

None.

---

## Implementation — Phase 5: Baseline scenario file

### Context files to load

- `evals/scenarios/full_cycle.py` (reference for existing format, pack, and style)
- `ccya/eval/scenario.py` (Scenario, Turn, TurnAssert dataclasses)
- `docs/design/dual-track-eval-design.md` (baseline scenario design decision: hybrid with structural asserts)

### Detailed steps

#### Step 5.1 — Create `evals/scenarios/baseline.py`

**File:** `evals/scenarios/baseline.py` (new file)

**What:** A 10-13 turn organic narrative arc using the same `eval-pack` pack as `full_cycle.py`. The scenario:
- Sets `track="baseline"`
- Uses natural, player-like inputs forming a coherent story arc (no edge-case forcing)
- Has `expects` annotations for report context
- Carries a minimal set of structural `asserts` for critical system-integrity checks (e.g., `rolled` expectations on obvious rule calls, a location change assertion)

The narrative arc should be distinct from full_cycle's arc — not a rehash. A suggested structure:
- Turns 1-3: Establish setting, meet NPC, gentle dialogue (few/no rolls)
- Turns 4-6: Rising action, skill checks, discovery
- Turns 7-10: Escalation, resource use, condition management
- Turns 11-13: Resolution, aftermath

Asserts should be minimal (5-8 total across all turns) and focus on:
- `rolled=true/false` for obviously-rolled/obviously-free turns
- One `location_change` scene assertion
- One `inventory_remove` or `inventory_add` if the narrative naturally involves item transfer

**Why:** The baseline scenario is what `python -m ccya.eval run` defaults to. It must feel like a real play session to get meaningful aggregate gameplay scores, while still catching engine breakage via its few structural asserts.

**Validation:** `python -m ccya.eval list` shows `baseline` with `track=baseline`. `python -m ccya.eval run baseline --no-judge` completes 13 turns without unhandled errors and produces `evals/runs/latest/artifacts/baseline.run.json` with `"track": "baseline"`.

### Tests to write or update

None.

---

## Implementation — Phase 6: Documentation

### Context files to load

- `docs/architecture/eval-harness.md`
- `docs/repomap.md`

### Detailed steps

#### Step 6.1 — Update eval-harness.md

**File:** `docs/architecture/eval-harness.md`

**What:** Document the two-track model:
- The `track` field on `Scenario`
- Flow: `scenario.track` → `cli.py` → `run_judges()` → `arch_context` → domain judge system prompt
- Which judges receive track context (`state_correctness`, `narrative_interplay`) and which don't (`prompt_pipeline`, `meta`)
- How rubrics handle per-track scoring (`## Baseline Track Scoring` sections)
- Report labeling
- That `track` is NOT a CLI flag — it's a scenario property

**Why:** Architecture doc must reflect the new track flow for future contributors.

**Validation:** `grep -q 'dual-track\|baseline' docs/architecture/eval-harness.md`

#### Step 6.2 — Update repomap.md

**File:** `docs/repomap.md`

**What:** Update the eval harness module section to reflect:
- New field: `Scenario.track` (with valid values)
- New scenario file: `evals/scenarios/baseline.py`
- Updated signatures: `run_judges()` now takes `track: str`
- Updated model: `RunResult.track`

**Why:** Repomap is the navigation document for implementing LLMs.

**Validation:** `grep -q 'baseline\|track' docs/repomap.md`

### Tests to write or update

None.
