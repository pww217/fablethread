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
| `evals/rubrics/default.md` | replace | Full rewrite to rubric v2 |
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
5. Rubric TOC with anchor links is removed. Numbered sections (SECTION 1–12) are
   sufficient navigation. GitHub anchor links in long markdown are unreliable in
   rendered judge output.

---

## Implementation — Phase 1: Replace Rubric

### Context files to load
- `evals/rubrics/default.md` (current — read to confirm replacement)
- `ccya/eval/judge.py` (confirm front-matter field names)
- `evals/config.yaml` (confirm rubric_path)

### Overview
File replacement. No code changes.

### Detailed steps

#### Step 1.1 — Replace rubric file

**File:** `evals/rubrics/default.md`

**What:** Replace entire contents with rubric v2.

**Why:** Old rubric over-weighted qualitative narrative criteria, had no mechanic
lifecycle tables, no prompt quality audit, no pacing cap recommendations, no
interplay assessment, and a broken TOC.

**Validation:** Run `make eval-fast`. Confirm `full_cycle.judge.md` YAML front matter
contains all new fields. Confirm Section 1 contains six lifecycle tables.

### Tests to write or update
None for this phase.

### REPOMAP updates required
`docs/REPOMAP/eval.md`: note rubric version bump.

### Risks
1. If judge model doesn't follow the new section structure, the body will be
   unstructured but scores will still parse from YAML front matter. Mitigation:
   run eval-fast and inspect judge.md manually on first run.

---

## Implementation — Phase 2: Expand Front-Matter Parsing

### Context files to load
- `ccya/eval/judge.py`
- `ccya/eval/report.py`

### Overview
Expand `_normalize_scores()` for new fields. Update `report.py` score table rendering.

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

**What:** Extend the score table rendering to include rows for all new fields.
Format rates as percentages (× 100, 1 decimal). Handle None as `—`.

**Code Snippet:**
```python
def _fmt_score(v: int | None) -> str:
    return str(v) if v is not None else "—"

def _fmt_rate(v: float | None) -> str:
    return f"{v*100:.1f}%" if v is not None else "—"

score_rows = [
    ("Mechanical",           _fmt_score(scores.get("mechanical_score"))),
    ("Narrative",            _fmt_score(scores.get("narrative_score"))),
    ("System Cohesion",      _fmt_score(scores.get("system_cohesion_score"))),
    ("Prompt Quality",       _fmt_score(scores.get("prompt_quality_score"))),
    ("Compaction",           _fmt_score(scores.get("compaction_score"))),
    ("State Fidelity Rate",  _fmt_rate(scores.get("state_fidelity_rate"))),
    ("Prompt Adherence Rate",_fmt_rate(scores.get("prompt_adherence_rate"))),
]
```

**Validation:** Run `make eval-fast`. Open `evals/runs/latest/REPORT.md`. Confirm
score table has 7 rows. Confirm `—` appears for any unpopulated field.

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

### Context files to load
- `ccya/eval/universal_asserts.py`
- `ccya/eval/compaction_signals.py`
- One sample `events.jsonl` from `evals/runs/latest/artifacts/` to verify event schema

### Overview
Add two deterministic asserts targeting the most common structural failures.

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

Add under P2 (Eval Harness improvements):