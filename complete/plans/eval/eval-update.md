# Rubric v2 + Eval Engine Updates

## Status
`open`

## Part of
standalone

## Dependencies
- none (all prior eval-harness phases completed)

## Objective
Replace `evals/rubrics/default.md` with the v2 rubric. Update `judge.py`
front-matter parsing and `report.py` to consume new score fields. Add two new
universal asserts that would have caught the T8/T12 quest ID collision and T6/T12
compactor sanitization misses deterministically.

## Non-goals
- Does not change the game engine pipelines.
- Does not change the 5 system prompts (those are addressed by actionable issues in
  eval output, not this plan).
- Does not add new eval scenarios.
- Does not change the eval runner or scenario system.

## Affected files

| File | Change type | Summary of change |
|---|---|---|
| `evals/rubrics/default.md` | replace | Full rewrite to rubric v2 (11 sections) |
| `ccya/eval/judge.py` | modify | Parse 5 new front-matter fields + 2 rate fields |
| `ccya/eval/report.py` | modify | Render new scores in REPORT.md score table |
| `ccya/eval/universal_asserts.py` | modify | Add 2 new deterministic asserts |
| `docs/REPOMAP/eval.md` | update | Reflect new score fields and new asserts |
| `docs/plans/TODO.md` | update | Add this plan |

## Firm Decisions

1. YAML front matter expands from 2 top-level scores + pipeline_scores to 5 top-level
   scores + 2 rate fields + pipeline_scores. `_normalize_scores()` must handle missing
   new fields gracefully (None, not KeyError).
2. `state_fidelity_rate` and `prompt_adherence_rate` are floats 0.0–1.0. The existing
   `_coerce()` int helper must NOT be applied to these fields.
3. Dropped narrative criteria are removed from the rubric entirely. `report.py` must
   not expect them.
4. Two new universal asserts are deterministic (no LLM involvement):
   - `progress.quest_id_collision`: FAIL if `quest_updates` contains an ID already
     in `completed` quests (re-creation of a closed quest).
   - `compactor.sanitization_nonzero`: FAIL if a compaction turn completes and
     sanitization result shows all empty fields but state contains completed quests.
5. Rubric TOC with anchor links is removed. Numbered sections (SECTION 1–11) are
   sufficient navigation. GitHub anchor links in long markdown are unreliable in
   rendered judge output.

---

## Rubric v2 Structure (SSOT)

The rubric (`evals/rubrics/default.md`) has 11 sections:

```
1. Mechanic Lifecycle Tables (1A-1F)
   - 1A: Momentum Table
   - 1B: GM Beat Table
   - 1C: Scene Pressure Table
   - 1D: Condition Lifecycle Table
   - 1E: Quest Arc Table
   - 1F: Inventory Evolution Table

2. State Fidelity (2A-2D)
   - 2A: State Coherence
   - 2B: State Drift
   - 2C: State Completeness
   - 2D: State Fidelity Rate Calculation

3. Prompt Quality Audit (P1-P9, 3A-3G)
   - 9 criteria per pipeline (system/user separation, mechanical sense, redundancy,
     schema vs guidance, contradictions, terseness, parse-friendly, adherence, few-shot)
   - Per-pipeline audits: Rules, Narrate, Extract Scene, Extract State, Extract Progress
   - Prompt Adherence Rate Calculation
   - Cross-Pipeline Redundancy Summary

4. Mechanic Interplay Assessment (4A-4G)
   - 4A: Beat→Narrative Loop
   - 4B: Momentum→Directive→Tone Chain
   - 4C: Pressure→Stakes→Consequence Chain
   - 4D: Condition→Narrative Callback
   - 4E: Pacing Assessment
   - 4F: NPC Entry/Exit Coherence
   - 4G: Player Intent Fidelity (player action honored, intent classified correctly)

5. Compaction Report (5A-5C)
   - 5A: Chronicle Quality
   - 5B: Sanitization Fidelity
   - 5C: Compaction Score (1-5)

6. Auto-Checker Failures

7. Per-Pipeline Mechanical Critique
   - What Went Well, What Went Poorly, Prompt Adherence Failures
   - Mechanic Ownership Check (field→stream mapping)
   - Extraction Quality Checks (amount accuracy, spending, ambient NPC filtering, quest dedup)
   - Scope Discipline (each pipeline only processes its own domain)
   - Issues Bulleted List, Pipeline Score (1-5)

8. Cross-Pipeline Correlation
   - Rules→Narrate Binding
   - Rules→Extract State Routing
   - Narrate→Scene Extract Consistency
   - Narrate→State Extract Consistency
   - Narrate→Progress Extract Consistency
   - Progress→Narrate Feedback Loop

9. Storytelling Criteria (SECONDARY)
   - quest_arc_quality
   - rewards_and_consequences [trace]
   - world_consistency
   - failure_arc [trace]
   - Dropped (covered by Sections 1 and 4): narrative_compellingness, npc_voice,
     npc_development, world_reactivity, player_agency, pacing_and_pressure,
     deescalation_mechanics, scenario_quality

10. Verdicts
    - V1: Mechanical Integrity → mechanical_score
    - V2: Narrative Quality → narrative_score
    - V3: System Cohesion → system_cohesion_score
    - V4: Prompt Quality → prompt_quality_score
    - V5: Compaction → compaction_score
    - V6: Pipeline I/O Relevance (each pipeline's inputs/outputs focused on its task)
    - V7: Key Findings

11. Actionable Issues
    - Grouped as Critical, Major, Minor
```

### YAML Front Matter

```yaml
---
mechanical_score: <int 1-5>
narrative_score: <int 1-5>
system_cohesion_score: <int 1-5>
prompt_quality_score: <int 1-5>
compaction_score: <int 1-5>
pipeline_scores:
  rules: <int 1-5>
  narrate: <int 1-5>
  extract_scene: <int 1-5>
  extract_state: <int 1-5>
  extract_progress: <int 1-5>
compaction_score: <int 1-5>
state_fidelity_rate: <float 0.0-1.0>
prompt_adherence_rate: <float 0.0-1.0>
---
```

---

## Implementation — Phase 1: Replace Rubric

**Status:** ✅ Complete

### What was done

Replaced `evals/rubrics/default.md` with rubric v2 (11 sections as documented above).

Key changes from old rubric:
- Added Mechanic Lifecycle Tables (Section 1) — 6 compact tables covering every turn
- Added State Fidelity (Section 2) — coherence, drift, completeness, rate calculation
- Added Prompt Quality Audit (Section 3) — 9 criteria per pipeline
- Added Mechanic Interplay Assessment (Section 4) — 7 subsections including Player Intent Fidelity
- Added Cross-Pipeline Correlation (Section 8) — 6 handoff verifications
- Reduced Storytelling Criteria (Section 9) — 4 scored + 8 dropped
- Expanded Verdict (Section 10) — 7 subheaders including Pipeline I/O Relevance
- Completed Actionable Issues (Section 11) — Critical/Major/Minor with format spec
- Added Scope Discipline to Section 7 — each pipeline only processes its own domain

### Validation

Rubric file exists at `evals/rubrics/default.md` with 11 sections.

---

## Implementation — Phase 2: Expand Front-Matter Parsing

**Status:** ⏳ Pending

### Context files to load
- `ccya/eval/judge.py`
- `ccya/eval/report.py`

### Overview

Expand `_normalize_scores()` for new fields. Update `report.py` score table rendering.

### Current state

`_normalize_scores()` in `judge.py:498-514` only handles:
- `mechanical_score` (int)
- `narrative_score` (int)
- `pipeline_scores` (dict)

Missing from rubric front matter:
- `system_cohesion_score` (int 1-5)
- `prompt_quality_score` (int 1-5)
- `compaction_score` (int 1-5)
- `state_fidelity_rate` (float 0.0-1.0)
- `prompt_adherence_rate` (float 0.0-1.0)

`report.py:_render_judge_summary()` at line 341-371 only renders:
- `mechanical_score`
- `narrative_score`
- `pipeline_scores`

Missing: `system_cohesion_score`, `prompt_quality_score`, `compaction_score`, `state_fidelity_rate`, `prompt_adherence_rate`

### Detailed steps

#### Step 2.1 — Expand `_normalize_scores()` in judge.py

**File:** `ccya/eval/judge.py`

**What:** Add handling for `system_cohesion_score`, `prompt_quality_score`,
`compaction_score` (int 1–5) and `state_fidelity_rate`, `prompt_adherence_rate`
(float 0.0–1.0, clamped).

**Why:** Without this, new front-matter fields are silently ignored and missing from
`JudgeResult.scores`.

**Code Snippet:**
```python
def _normalize_scores(fm: dict[str, Any]) -> dict[str, Any]:
    def _coerce_int(v: Any) -> int | None:
        try:
            n = int(round(float(v)))
        except (TypeError, ValueError):
            return None
        return max(1, min(5, n))

    def _coerce_rate(v: Any) -> float | None:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None
        return max(0.0, min(1.0, f))

    out: dict[str, Any] = {}
    for k in ("mechanical_score", "narrative_score", "system_cohesion_score",
              "prompt_quality_score", "compaction_score"):
        if k in fm:
            out[k] = _coerce_int(fm[k])
    for k in ("state_fidelity_rate", "prompt_adherence_rate"):
        if k in fm:
            out[k] = _coerce_rate(fm[k])
    ps = fm.get("pipeline_scores") or {}
    if isinstance(ps, dict):
        out["pipeline_scores"] = {
            k: _coerce_int(v) for k, v in ps.items()
            if k in ("rules", "narrate", "extract_scene", "extract_state",
                     "extract_progress")
        }
    return out
```

**Validation:** Python shell — feed the new front-matter block to
`parse_judge_response()`. Confirm all 7 new fields in returned scores dict with
correct types.

#### Step 2.2 — Update score table in report.py

**File:** `ccya/eval/report.py`

**What:** Extend `_render_judge_summary()` to include rows for all new fields.
Format rates as percentages (× 100, 1 decimal). Handle None as `—`.

**Code Snippet:**
```python
def _fmt_score(v: int | None) -> str:
    return str(v) if v is not None else "—"

def _fmt_rate(v: float | None) -> str:
    return f"{v*100:.1f}%" if v is not None else "—"

scores = judge.scores or {}
parts.append(f"**Mechanical:** {_fmt_score(scores.get('mechanical_score'))}/5  ")
parts.append(f"**Narrative:** {_fmt_score(scores.get('narrative_score'))}/5  ")
parts.append(f"**System Cohesion:** {_fmt_score(scores.get('system_cohesion_score'))}/5  ")
parts.append(f"**Prompt Quality:** {_fmt_score(scores.get('prompt_quality_score'))}/5  ")
parts.append(f"**Compaction:** {_fmt_score(scores.get('compaction_score'))}/5  ")
parts.append(f"**State Fidelity:** {_fmt_rate(scores.get('state_fidelity_rate'))}  ")
parts.append(f"**Prompt Adherence:** {_fmt_rate(scores.get('prompt_adherence_rate'))}")
```

**Validation:** Run `make eval-fast`. Open `evals/runs/latest/REPORT.md`. Confirm
score table has 7 score rows + 2 rate rows. Confirm `—` appears for any unpopulated field.

### Tests to write or update
- `tests/eval/test_judge.py`: `test_normalize_scores_new_fields` — feed all 7 new
  fields, confirm types are correct (int for scores, float for rates).

### REPOMAP updates required
`docs/REPOMAP/eval.md`: update `JudgeResult.scores` field list.

### Risks
1. `report.py` may look for old narrative criteria fields (e.g., `npc_voice_score`).
   Search for any such references and remove them. Leaving them will produce `—` rows
   for fields that no longer exist.

---

## Implementation — Phase 3: New Universal Asserts

**Status:** ⏳ Pending

### Context files to load
- `ccya/eval/universal_asserts.py`
- `ccya/eval/compaction_signals.py`
- One sample `events.jsonl` from `evals/runs/latest/artifacts/` to verify event schema

### Overview

Add two deterministic asserts targeting the most common structural failures.

Current universal asserts (10): `recent_events_add.turn_stamped`, `pending_gm_beat.consumed`,
`location_change.applied`, `narrate.binding_present`, `npc_mention.extracted`,
`recent_events.ring_bounded`, `scene.npc_cap`, `pc.condition_no_dupes`,
`progress.actions_quality`, `momentum.band_delta`.

### Detailed steps

#### Step 3.1 — `progress.quest_id_collision`

**File:** `ccya/eval/universal_asserts.py`

**What:** Assert that fires when `quest_updates` contains an ID already present in
`completed` quests (re-creation of a closed quest). Also fires if a new ID appears
that exactly matches an ID in `active_quests` but the entry has no prior history
(full re-creation, not a status update).

**Why:** The T8/T12 `deliver_halden_ledger` duplicate would have been a deterministic
failure, not a judge observation.

**Code Snippet:**
```python
def _assert_quest_id_collision(
    ev: dict[str, Any], prev_ev: dict[str, Any] | None
) -> list[dict[str, Any]]:
    results = []
    ext = (ev.get("extraction") or {}).get("progress") or {}
    if ext.get("skipped"):
        return results
    output = ext.get("output") or {}
    quest_updates = output.get("quest_updates") or []
    snap = ev.get("state_snapshot") or {}
    quests = snap.get("quests") or {}
    # Support both {active: [...], completed: [...]} and flat list with status
    active = quests.get("active") or []
    completed = quests.get("completed") or []
    active_ids = {q["id"] for q in active if "id" in q}
    completed_ids = {q["id"] for q in completed if "id" in q}
    for qu in quest_updates:
        qid = qu.get("id")
        if not qid:
            continue
        if qid in completed_ids:
            results.append({
                "assertion": "progress.quest_id_collision",
                "passed": False,
                "detail": (
                    f"quest_updates re-creates already-completed quest id={qid!r}"
                ),
            })
    return results
```

**Note to executor:** If `state_snapshot.quests` uses a flat list with a `status`
field instead of nested active/completed keys, adapt the lookup accordingly. Read
the actual schema from the events.jsonl sample before implementing.

**Validation:**
- Unit test: construct fake event where quest_updates has a completed quest ID → assert fires.
- Unit test: quest_updates has a new ID not in completed → assert does NOT fire.
- Run `make test`.

#### Step 3.2 — `compactor.sanitization_nonzero`

**File:** `ccya/eval/universal_asserts.py`

**What:** Assert that fires when a compaction turn completes AND the sanitization
result is entirely empty AND state contains at least one completed quest (meaning
the compactor had work to do but did none).

**Why:** The T6/T12 sanitization miss (3× FAIL in compaction report) would have been
a deterministic failure instead of requiring judge opinion.

**Code Snippet:**
```python
def _assert_compactor_sanitization_nonzero(
    ev: dict[str, Any], prev_ev: dict[str, Any] | None
) -> list[dict[str, Any]]:
    results = []
    compaction = ev.get("compaction") or {}
    if not compaction.get("fired"):
        return results
    sanit = compaction.get("sanitization") or {}
    quest_close = sanit.get("quest_close") or []
    cond_remove = sanit.get("condition_remove") or []
    pres_remove = sanit.get("pressure_remove") or []
    if quest_close or cond_remove or pres_remove:
        return results  # something was sanitized — pass
    snap = ev.get("state_snapshot") or {}
    quests = snap.get("quests") or {}
    completed = quests.get("completed") or []
    if completed:
        results.append({
            "assertion": "compactor.sanitization_nonzero",
            "passed": False,
            "detail": (
                f"compaction fired but sanitized nothing; "
                f"{len(completed)} completed quest(s) remain un-closed in state"
            ),
        })
    return results
```

**Note to executor:** Verify whether `compaction.fired` is a key stored directly in
the event dict or whether it needs to be derived from `ev["turn"] % compact_every == 0`
using engine constants. Check `compaction_signals.py` for how the signal is computed.

**Validation:**
- Unit test: compaction fired + empty sanitization + completed quests → fires.
- Unit test: compaction fired + non-empty sanitization → does NOT fire.
- Run `make test`.

#### Step 3.3 — Register new asserts

**File:** `ccya/eval/universal_asserts.py`

**What:** Add calls to both new functions inside `run_all_universal_asserts()`,
following the existing pattern.

**Validation:** Run `make eval-fast`. Confirm Auto-Checker Failures table in
REPORT.md shows new assertion names if triggered.

### Tests to write or update
- `tests/eval/test_universal_asserts.py`:
  - `test_quest_id_collision_fires`
  - `test_quest_id_collision_clean`
  - `test_compactor_sanitization_nonzero_fires`
  - `test_compactor_sanitization_nonzero_clean`

### REPOMAP updates required
`docs/REPOMAP/eval.md`: add two new asserts to the universal asserts table.

### Risks
1. `compaction.fired` may not exist as a direct event key — derive from turn number
   and `compact_every` constant if needed. Add defensive `.get()` throughout.
2. Quest schema in state_snapshot may be a flat list with `status` field. Executor
   must read actual schema from events.jsonl before finalizing assert logic.
3. Phase 3 asserts on older event logs will silently pass if `compaction` key is
   absent — that is correct behavior (older runs had no compaction tracking).

## Ambiguities requiring resolution before execution

1. Is `compaction.fired` a key in each event JSONL entry, or derived post-hoc by
   `compaction_signals.py`?
   Options: A) Direct event key B) Must derive from `turn % compact_every`

2. What is the exact schema of `state_snapshot.quests`?
   Options: A) `{active: [...], completed: [...]}` B) Flat list with `status` field

## TODO.md update

Add under P3 (Inference Speed and Evaluation):

- [ ] **Expand front-matter parsing** — `_normalize_scores()` must handle `system_cohesion_score`, `prompt_quality_score`, `compaction_score` (int 1-5) and `state_fidelity_rate`, `prompt_adherence_rate` (float 0.0-1.0); `report.py` must render all new fields — see `[eval-update.md](eval-update.md) Phase 2`
- [ ] **Add quest_id_collision assert** — deterministic check for re-creation of completed quests — see `[eval-update.md](eval-update.md) Phase 3`
- [ ] **Add compactor_sanitization_nonzero assert** — deterministic check for empty sanitization on compaction turns with completed quests — see `[eval-update.md](eval-update.md) Phase 3`
