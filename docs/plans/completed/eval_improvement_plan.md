# ccya Eval Improvement Plan

**Status:** Phase 7 complete · May 2026  
**Scope:** Issues 1–6, 8–10 from the eval audit. Issue 7 (additional genre packs) deferred.  
**Post-implementation:** Fixed `build_trace` truncation bug (constants block could be cut in half) — `ccya/eval/judge.py:164`.

---

## Decision Log

| # | Decision | Rationale |
|---|---|---|
| D-1 | Rubric rewrite precedes all other work | The judge drives everything; fixing it first makes phases 2–4 measurable |
| D-2 | Add per-stream context telemetry to `events.jsonl`, not just the runner | Judge needs live data, not post-hoc inference. Touching the runner alone is insufficient. |
| D-3 | `trim_messages` truncation flag lives in `EngineConfig`/`_log_llm_io` path | Runner already imports `EngineConfig`; adding a `trimmed` annotation there avoids touching `build_trace` signature |
| D-4 | Pressure scenario is a new `Scenario` object, not a modification of `full_cycle` | `full_cycle` should stay as the baseline regression suite; pressure/momentum variants are additive |
| D-5 | `note` field constraint stays for narrative criteria; mechanical criteria get `note` + `turns` array | Breaking the single-field contract means updating `JudgeResult` parsing — scoped to mechanical criteria only to minimize blast radius |
| D-6 | Quest `auto_complete` check is a new `TurnAssert` field (`field="quest_status"`) rather than a separate assertion type | Keeps the existing `_check_asserts` switch pattern, adds one case |
| D-7 | `pacing_and_pressure` stays as one criterion in rubric but with two mandatory sub-scores surfaced via `pressure_mechanics_score` and `pacing_score` sub-fields | Avoids adding a 16th criterion to the rubric schema while still separating signals |
| D-8 | Engine constants live in `ccya/eval/engine_mirror.py`, imported by scenarios | Single source of truth: scenarios never hardcode urgency thresholds or momentum bounds. When `EngineConfig` defaults change, `engine_mirror` reflects them and all scenarios pick it up with zero edits. |
| D-9 | `TurnAssert` field-path validation is a Tier 1 `make test` test, not a runtime guard | Catches renames at CI time, not mid-eval. Keeps the runner lean. |
| D-10 | `build_trace()` prepends a live engine-constants block to every judge context | Judge always sees actual current thresholds; rubric prose never needs manual updates when e.g. `scene_pressure_building_at` changes in `EngineConfig`. |

---

## Engine-Eval Integration Strategy

The eval harness already calls `run_turn()` in-process, so any change to the turn pipeline — prompt templates, extraction output, state mutations — is automatically exercised. The gap is the **assertion and observation layer**:

- `TurnAssert` field paths are hardcoded strings. Field renames silently break assertions.
- Urgency thresholds and momentum bounds in scenarios are magic numbers that diverge when `EngineConfig` defaults change.
- The LLM judge sees the rubric prose but not the live engine constants (e.g. what turn `background→building` fires at), so it reasons from potentially stale values.
- There is no Tier 1 test that fails when an assertion path or constant goes stale.

The fix is three small additions that require **zero ongoing maintenance** for structural changes:

1. `ccya/eval/engine_mirror.py` — imports live values from engine modules; scenarios import from here.
2. `tests/test_eval_schema.py` — validates all scenario `TurnAssert` paths against live model fields; runs under `make test`.
3. `build_trace()` prefix — injects a `## Engine Constants` block from `engine_mirror` into every judge trace.

Rubric *prose* (what scores mean, how to weight things) still requires manual update when mechanics are added. Everything else — constants, thresholds, field names — is automated.

---

## Phase 0 — Engine Mirror Module (new, prerequisite)

**Run before Phases 3–7.** No changes to engine code. Read-only imports.

### 0.1 — Create `ccya/eval/engine_mirror.py`

**File:** `ccya/eval/engine_mirror.py`

**What:** A module that imports live values from the engine and exposes them as named constants for use by eval scenarios and `build_trace`. Scenarios import from here instead of hardcoding.

**Why:** Single source of truth. When `EngineConfig` default for `scene_pressure_building_at` changes from 6 to 5, every scenario that uses `PRESSURE_BUILDING_AT` picks it up automatically. No scenario needs editing.

**Code Snippet**
```python
"""Read-only mirror of engine constants for use by eval scenarios and build_trace.

Import from here in scenarios — never hardcode thresholds or field names.
All values reflect current engine defaults. Where EngineConfig controls the
value at runtime, the default is used (eval runs use default EngineConfig
unless overridden in EvalConfig).
"""
from __future__ import annotations

from ccya.engine.config import EngineConfig
from ccya.state.momentum import _MOMENTUM_MIN, _MOMENTUM_MAX
from ccya.rules import MOMENTUM_DELTA

_defaults = EngineConfig()

# Scene pressure urgency escalation thresholds (turns since pressure was added)
PRESSURE_BUILDING_AT: int = _defaults.scene_pressure_building_at   # background → building
PRESSURE_IMMEDIATE_AT: int = _defaults.scene_pressure_immediate_at  # building → immediate
PRESSURE_MAX_AGE: int = _defaults.scene_pressure_max_age

URGENCY_LEVELS: tuple[str, ...] = ("background", "building", "immediate")

# Momentum
MOMENTUM_MIN: int = _MOMENTUM_MIN
MOMENTUM_MAX: int = _MOMENTUM_MAX
MOMENTUM_DELTA: dict[str, int] = dict(MOMENTUM_DELTA)

# Extraction stream names — used in TurnAssert.stream validation
EXTRACT_STREAMS: tuple[str, ...] = ("rules", "extract.scene", "extract.state", "extract.progress", "state_yaml")

# Known TurnAssert.field values per stream — used by test_eval_schema.py
# to validate that scenario assertions reference real fields.
# Keep in sync with runner._check_asserts handler names.
KNOWN_ASSERT_FIELDS: dict[str, set[str]] = {
    "rules": {"rolled", "skill", "band"},
    "extract.progress": {"quest_updates", "quest_status"},
    "extract.scene": {"scene_pressure_add"},
    "extract.state": {"condition_add", "condition_remove"},
    "state_yaml": {"pending_gm_beat.present", "pending_gm_beat.absent"},
}


def constants_block() -> str:
    """Return a markdown block of live engine constants for injection into judge traces.

    Called by build_trace() so the LLM judge always reasons from current values,
    not from whatever the rubric prose says.
    """
    return (
        "## Engine Constants (live — do not override with rubric prose)\n\n"
        f"- Scene pressure: background→building at turn age {PRESSURE_BUILDING_AT}, "
        f"building→immediate at turn age {PRESSURE_IMMEDIATE_AT}, "
        f"max age {PRESSURE_MAX_AGE}\n"
        f"- Urgency levels (ordered): {' → '.join(URGENCY_LEVELS)}\n"
        f"- Momentum range: [{MOMENTUM_MIN}, {MOMENTUM_MAX}]\n"
        f"- Momentum delta per band: {MOMENTUM_DELTA}\n\n"
    )
```

**Validation:** `python -c "from ccya.eval.engine_mirror import constants_block; print(constants_block())"` prints the block without errors.

### 0.2 — Export `engine_mirror` from `ccya/eval/__init__.py`

**File:** `ccya/eval/__init__.py`

**What:** Add `engine_mirror` to the module's public surface.

**Why:** Scenarios in `evals/scenarios/` import from `ccya.eval.engine_mirror`; having it in `__init__` makes it discoverable.

**Code Snippet**
```python
from ccya.eval import engine_mirror as engine_mirror  # re-export
```

**Validation:** `from ccya.eval import engine_mirror` works from any context.

---

## Phase 1 — Rubric Rewrite (Issues 1, 6, 10)

**Goal:** Make the judge prioritize mechanics, give mechanical criteria turn-level citation ability, and split pressure/pacing signals.

### 1.1 — Invert criterion priority weighting

In `evals/rubrics/default.md`, swap the "Primary focus" and "Secondary focus" sections:

```markdown
## Primary focus: mechanical correctness

Your most important job is to judge whether the engine's mechanics are
functioning correctly — scene pressure lifecycle, extraction fidelity,
context economy, GM beat consumption, and scope decisions. A run with a
compelling story but broken state tracking is a broken run.

Ask yourself:
- Did scene pressure escalate and expire correctly across turns?
- Did `pending_gm_beat` get consumed within 1 turn and not persist?
- Were per-stream token inputs proportionate to what was actually needed?
- Did extraction outputs match narration outputs turn-by-turn?
- Did `trim_messages` truncation silently discard in-scene state?

## Secondary focus: narrative quality

Narrative criteria (quest arc, genre fit, compellingness) matter, but
they serve as signal that the mechanics are producing good fiction.
A 5/5 story built on broken extraction is a false positive.
```

Also update the `overall_score` weighting instruction at the bottom:

```markdown
`overall_score` weights `mechanical_consistency`, `context_economy`,
`context_fidelity`, `pressure_mechanics`, `pacing_and_pressure`, and
`extraction_consistency` at 2× relative to the narrative criteria.
Briefly justify in `comments` when the overall diverges from criterion scores.
```

### 1.2 — Add `turns` field to mechanical criteria output schema

Update the JSON schema in the rubric:

```json
{
  "criterion": "mechanical_consistency",
  "score": 3,
  "note": "One short sentence.",
  "turns": [3, 7]
}
```

Add this note above the schema:

> For mechanical criteria (`mechanical_consistency`, `extraction_consistency`,
> `context_economy`, `context_fidelity`, `scope_correctness`, `state_drift`,
> `pacing_and_pressure`), populate `turns` with turn numbers where the issue
> was observed. Leave `turns` as `[]` for narrative criteria.

Update `JudgeResult` in `ccya/eval/judge.py` to capture this:

```python
@dataclass
class JudgeResult:
    overall_score: int
    findings: list[dict[str, Any]] = field(default_factory=list)
    comments: str = ""
    raw_response: str = ""
    rubric_path: str = ""
    model: str = ""
    previous_overall: int | None = None

# In parse_judge_response → findings loop:
findings.append(
    {
        "criterion": str(f.get("criterion", "")),
        "score": _coerce_score(f.get("score", 0)),
        "note": str(f.get("note", "")),
        "turns": [int(t) for t in (f.get("turns") or []) if str(t).isdigit()],
    }
)
```

Update `report.py` to render `turns` in the findings table when present:

```python
# In the findings section of build_report():
turns_str = ""
if finding.get("turns"):
    turns_str = f" *(turns {', '.join(str(t) for t in finding['turns'])})*"
md.append(f"| {criterion} | {score}/5 | {note}{turns_str} |")
```

### 1.3 — Split `pacing_and_pressure` into two sub-scores

Replace the single `pacing_and_pressure` criterion block in the rubric with:

```markdown
### 15. pacing_and_pressure

Score this criterion once. Internally weigh two distinct signals:

**pressure_mechanics (objective — weight 60%):**
- Did scene_pressure entries escalate from `background` → `building` → `immediate`
  across their expected turn span?
- Did pressures expire (disappear from applied state) when `max_turns` was reached?
- Did the narration reflect urgency changes (not just internally tracked)?
- Were new pressures seeded at appropriate story moments?

**narrative_pacing (subjective — weight 40%):**
- Are there breathing-room turns between high-tension beats?
- Does momentum (positive/negative swings) visibly affect narration tone?
- Does the arc feel satisfying across the full run?

Your single `score` is the weighted composite. Call out pressure_mechanics
failures specifically in `note` — they are harder to observe and more critical.
Include offending turn numbers in `turns`.
```

---

## Phase 2 — Context Telemetry in `events.jsonl` (Issues 2, 3, 9)

**Goal:** Make per-stream context size and truncation visible to the judge.

### 2.1 — Add `context_meta` to each stream's extraction event

In `ccya/engine/extraction.py`, after each stream's rendered prompt is assembled but before the LLM call, compute a `context_meta` dict and attach it to the extraction event. The event writer already populates `extraction.scene`, `extraction.state`, `extraction.progress` — extend each with a `context_meta` sub-key.

```python
# In _run_stream() or wherever you build the messages list per stream:

def _context_meta(rendered_system: str, rendered_user: str) -> dict:
    """Compute context size signals for telemetry."""
    return {
        "system_chars": len(rendered_system),
        "user_chars": len(rendered_user),
        "total_chars": len(rendered_system) + len(rendered_user),
        # rough token estimate: chars / 3.5 (good enough for comparisons)
        "est_tokens": int((len(rendered_system) + len(rendered_user)) / 3.5),
        "trimmed": False,   # overwritten below if trim fires
        "trimmed_chars": 0,
    }
```

For the narrate call, add equivalent telemetry to the `narrate_prompt` event key in `ccya/engine/narrate.py` (or wherever narrate constructs its messages).

### 2.2 — Flag `trim_messages` truncation

In `ccya/llm_client.py`, `trim_messages` currently silently truncates. Add a return value indicating whether truncation occurred and by how many characters:

```python
def trim_messages(
    messages: list[dict],
    budget: int,
    *,
    tokenize=None,
) -> tuple[list[dict], bool, int]:
    """
    Returns (trimmed_messages, was_truncated, chars_removed).
    Existing callers that only unpack the first element continue to work
    if we make was_truncated and chars_removed optional unpacking.
    """
    # ... existing logic ...
    # Before returning, compute chars_removed = original_total - new_total
    was_truncated = chars_removed > 0
    return messages, was_truncated, chars_removed
```

Callers in `extraction.py` and `narrate.py` that call `trim_messages` should capture the truncation signal and write it back into `context_meta`:

```python
messages, was_trimmed, trimmed_chars = trim_messages(messages, budget)
ctx_meta["trimmed"] = was_trimmed
ctx_meta["trimmed_chars"] = trimmed_chars
```

### 2.3 — Extend `build_trace` in `judge.py` to include context telemetry and live constants

The judge's `build_trace` function currently shows only output summaries. Make two additions:

**a) Prepend a live engine constants block** (from `engine_mirror.constants_block()`) at the top of every trace so the judge reasons from current values, not stale rubric prose:

```python
# At the top of build_trace():
from ccya.eval.engine_mirror import constants_block

def build_trace(events: list[dict[str, Any]], scenario: Scenario) -> str:
    lines: list[str] = [constants_block()]
    # ... rest of existing build_trace logic ...
```

**b) Add a `[context]` line per turn** showing per-stream token estimates and truncation flags:

```python
def _context_line(event: dict[str, Any]) -> str:
    """Summarize per-stream context sizes and truncation for the judge."""
    parts = []
    narrate = event.get("narrate_prompt") or {}
    nm = narrate.get("context_meta") or {}
    if nm:
        trunc = " TRIMMED" if nm.get("trimmed") else ""
        parts.append(f"narrate={nm.get('est_tokens', '?')}t{trunc}")

    extraction = event.get("extraction") or {}
    for stream in ("scene", "state", "progress"):
        ex = extraction.get(stream) or {}
        cm = ex.get("context_meta") or {}
        if cm:
            trunc = " TRIMMED" if cm.get("trimmed") else ""
            parts.append(f"{stream}={cm.get('est_tokens', '?')}t{trunc}")

    return ", ".join(parts) if parts else "(no context telemetry)"

# In build_trace block assembly:
block = (
    f"TURN {turn} — {inp}\n"
    f"[context] {_context_line(ev)}\n"     # <-- new line
    f"[scope] {scope_line}\n"
    ...
)
```

### 2.4 — Add `context_economy` flag to `EvalConfig`

In `evals/config.yaml`, add a warning threshold:

```yaml
judge:
  model: ...
  rubric_path: evals/rubrics/default.md
  temperature: 0.0
  context_economy_warn_tokens: 8000   # flag any stream exceeding this
```

In `report.py`, add a "Context Warnings" section that fires when any stream's `est_tokens` exceeds the threshold:

```python
# In build_report(), after the findings table:
context_warns = []
for ev in events:
    for stream in ("scene", "state", "progress"):
        cm = (ev.get("extraction") or {}).get(stream, {}).get("context_meta") or {}
        if cm.get("est_tokens", 0) > cfg.judge.context_economy_warn_tokens:
            context_warns.append(
                f"Turn {ev['turn']} {stream}: {cm['est_tokens']}t "
                f"({'TRIMMED' if cm.get('trimmed') else 'ok'})"
            )
    nm = (ev.get("narrate_prompt") or {}).get("context_meta") or {}
    if nm.get("est_tokens", 0) > cfg.judge.context_economy_warn_tokens:
        context_warns.append(f"Turn {ev['turn']} narrate: {nm['est_tokens']}t")

if context_warns:
    md.append("\n## ⚠ Context Economy Warnings\n")
    for w in context_warns:
        md.append(f"- {w}")
```

---

## Phase 3 — Scenario Coverage (Issues 4, 5)

**Goal:** Add scenario variants that actually exercise scene pressure, GM beats, and momentum.

**Note on live constants:** All turn-number expectations in these scenarios derive from `engine_mirror` constants, not hardcoded values. If `EngineConfig.scene_pressure_building_at` changes, the scenario expectations update automatically.

### 3.1 — `pressure_lifecycle` scenario

Create `evals/scenarios/pressure_lifecycle.py`. This scenario must:

1. Seed a `[BACKGROUND]` scene pressure at turn 1 via the pack's `seed.scene.scene_pressure` or via a seeded narration that triggers `extract.progress`.
2. Verify urgency escalates to `[BUILDING]` by turn 3–4.
3. Verify urgency escalates to `[IMMEDIATE]` by turn 6.
4. Verify the pressure expires (absent from applied state) by turn 8 (`max_turns` reached or explicitly resolved).
5. Include a `TurnAssert` on `scene_pressure_add` at turn 1 and a check for pressure absence at turn 8.

```python
# evals/scenarios/pressure_lifecycle.py
from ccya.eval.scenario import Scenario, Turn, TurnAssert
from ccya.eval.engine_mirror import PRESSURE_BUILDING_AT, PRESSURE_IMMEDIATE_AT

scenario = Scenario(
    id="pressure_lifecycle",
    pack="eval-pack",
    description="Tests scene_pressure urgency escalation and expiry across 8 turns.",
    seed_overrides={
        # Inject a starting pressure directly into the seed state before the run.
        # Runner._patch_eval_pack_starting_state needs to be extended to apply
        # seed_overrides (see 3.3 below).
        "scene.scene_pressure": [
            {
                "id": "debt_collector_approaching",
                "text": "A debt collector is making inquiries in Marrow's Crossing.",
                "urgency": "background",
                "max_turns": 7,
            }
        ]
    },
    turns=[
        Turn(
            input="I ask Caron quietly whether anyone has been looking for me lately.",
            phase="pressure_seed_check",
            expects=[
                "scene_pressure should be visible in narrate context",
                "rules.required=false (social inquiry, no obstacle)",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="false"),
            ],
        ),
        Turn(
            input="I spend the afternoon making discreet inquiries at the market.",
            phase="pressure_build_1",
            expects=[f"urgency should advance toward building (threshold: age {PRESSURE_BUILDING_AT})"],
        ),
        Turn(
            input="I try to get a full meal and rest at the inn before dealing with anything.",
            phase="breathing_room",
            expects=["no escalation forced — low-stakes action"],
        ),
        Turn(
            input="I duck into the alley behind the smithy when I hear heavy footsteps on the cobblestones.",
            phase="pressure_building",
            expects=[
                f"urgency should be building or immediate by now (building_at={PRESSURE_BUILDING_AT}, immediate_at={PRESSURE_IMMEDIATE_AT})",
                "scope should include pc_condition if physical",
            ],
            asserts=[
                TurnAssert(
                    stream="extract.scene",
                    field="scene_pressure_add",
                    expected="debt_collector_approaching",
                ),
            ],
        ),
        Turn(
            input="I confront the collector directly — I tell him the debt is settled and show him Caron's ledger mark.",
            phase="pressure_confront",
            expects=[
                "rules.required=true skill=charisma",
                "narration should reflect high urgency (IMMEDIATE)",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
            ],
        ),
        Turn(
            input="I watch the collector leave the square and wait ten minutes before moving.",
            phase="pressure_resolve_check",
            expects=[
                "pressure should be resolved or expired",
                "extract.progress should NOT re-add the same pressure",
            ],
        ),
        Turn(
            input="I head back to the inn and order a drink.",
            phase="post_pressure",
            expects=[
                "scene_pressure list should be empty or contain only new entries",
                "no ACTIVE THREATS in narrate context",
            ],
        ),
        Turn(
            input="I sit by the fire and check my inventory — count credits, check the ledger.",
            phase="cooldown",
            expects=["low-stakes, breathing room — no roll needed"],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="false"),
            ],
        ),
    ],
)
```

### 3.2 — `gm_beat_lifecycle` scenario

Create `evals/scenarios/gm_beat_lifecycle.py`. This must:

1. Run enough turns that `extract.progress` generates a `pending_gm_beat`.
2. Assert the beat appears in the next turn's narrate context (visible via `[context]` telemetry).
3. Assert the beat is consumed (absent from state) by turn N+2.

The tricky part is that `pending_gm_beat` is not directly observable from `applied` — it lives in `state.scene`. Add a new `TurnAssert` stream type `"state_yaml"` that reads the state snapshot for the turn:

```python
# In runner._check_asserts, add:
elif a.stream == "state_yaml":
    # Read the state snapshot after this turn
    # Runner needs to snapshot state.yaml per-turn (see 3.3)
    state_snap = event.get("state_snapshot") or {}
    if a.field == "pending_gm_beat.present":
        beat = (state_snap.get("scene") or {}).get("pending_gm_beat")
        passed = beat is not None
        detail = f"pending_gm_beat={'present' if passed else 'absent'}"
    elif a.field == "pending_gm_beat.absent":
        beat = (state_snap.get("scene") or {}).get("pending_gm_beat")
        passed = beat is None
        detail = f"pending_gm_beat={'present' if beat else 'absent'}"
```

```python
# evals/scenarios/gm_beat_lifecycle.py
from ccya.eval.scenario import Scenario, Turn, TurnAssert

scenario = Scenario(
    id="gm_beat_lifecycle",
    pack="eval-pack",
    description="Verifies pending_gm_beat is set by extract.progress, surfaced in next narration, and consumed.",
    turns=[
        # Turns 1-4: Standard arc that should generate a GM beat opportunity
        Turn(
            input="I settle the debt with Caron.",
            phase="setup_1",
            asserts=[TurnAssert(stream="rules", field="rolled", expected="false")],
        ),
        Turn(
            input="I pay Caron the 500 credits and ask him to clear my name in the ledger.",
            phase="setup_2",
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
                TurnAssert(stream="extract.progress", field="quest_updates", expected="settle_the_debt"),
            ],
        ),
        Turn(
            input="I leave the tavern and find Halden at the town well. I offer to courier his ledger.",
            phase="gm_beat_trigger",
            expects=[
                "extract.progress should generate a pending_gm_beat here",
                "state_yaml.pending_gm_beat should be present after this turn",
            ],
            asserts=[
                TurnAssert(stream="state_yaml", field="pending_gm_beat.present", expected="true"),
            ],
        ),
        Turn(
            input="I head east out of town on the merchant road.",
            phase="gm_beat_surface",
            expects=[
                "narrate should reflect the gm_beat instruction",
                "pending_gm_beat should be consumed after this turn",
            ],
            asserts=[
                TurnAssert(stream="state_yaml", field="pending_gm_beat.absent", expected="true"),
            ],
        ),
        Turn(
            input="I keep moving, watching the road ahead.",
            phase="gm_beat_consumed",
            expects=["No pending_gm_beat should persist beyond 1 turn"],
            asserts=[
                TurnAssert(stream="state_yaml", field="pending_gm_beat.absent", expected="true"),
            ],
        ),
    ],
)
```

### 3.3 — Runner changes to support new scenarios

**`seed_overrides` support:**

In `runner.py`, extend `_patch_eval_pack_starting_state` to apply `scenario.seed_overrides` on top of the pack seed:

```python
def _patch_eval_pack_starting_state(
    save_dir: Path, pack_id: str, seed_overrides: dict | None = None
) -> None:
    if pack_id == "eval-pack":
        state = load_state(save_dir)
        state["pc"]["conditions"] = list(_EVAL_PACK_STARTING_CONDITIONS)
        save_state(save_dir, state)
    if seed_overrides:
        state = load_state(save_dir)
        for dotpath, value in seed_overrides.items():
            _apply_dotpath(state, dotpath, value)
        save_state(save_dir, state)

def _apply_dotpath(obj: dict, path: str, value) -> None:
    """Set obj[a][b][c] = value for dotpath 'a.b.c'."""
    parts = path.split(".")
    for part in parts[:-1]:
        obj = obj.setdefault(part, {})
    obj[parts[-1]] = value
```

**Per-turn state snapshots:**

To support `state_yaml` assertions, the runner needs to capture a state snapshot after each turn. In `run_scenario()`, capture state after each `run_turn()` call and accumulate in a list, then merge into events after the loop:

```python
# In run_scenario(), inside the turn loop, after run_turn() completes:
state_snap = {}
try:
    state_snap = load_state(save_dir)
except Exception:
    pass
state_snapshots.append(state_snap)  # list indexed by turn position

# After the loop, merge snapshots into events before running _check_asserts:
for i, snap in enumerate(state_snapshots):
    if i < len(events):
        events[i]["state_snapshot"] = snap
```

**`Scenario.seed_overrides` field:**

Add to `ccya/eval/scenario.py`:

```python
@dataclass
class Scenario:
    id: str
    pack: str
    description: str = ""
    turns: list[Turn] = field(default_factory=list)
    seed_overrides: dict = field(default_factory=dict)  # <-- new
```

---

## Phase 4 — Quest Status Assertion and Rubric Coverage (Issue 8)

**Goal:** Assert `quest.status == "completed"` when all objectives are done, not just that `quest_updates` fired.

### 4.1 — Add `quest_status` assert field and `stream_id` to `TurnAssert`

In `ccya/eval/scenario.py`, add `stream_id` to `TurnAssert`:

```python
@dataclass
class TurnAssert:
    stream: str
    field: str
    expected: str = ""
    min_amount: int | None = None
    stream_id: str = ""   # <-- new: used for quest_status and similar keyed lookups
```

In `runner._check_asserts`, add a `quest_status` field handler under `extract.progress`:

```python
elif a.field == "quest_status":
    updates = applied.get("quest_updates") or []
    found = None
    for u in updates:
        if isinstance(u, dict) and u.get("id") == a.stream_id:
            found = u
            break
    if found:
        status = found.get("status", "")
        passed = status == a.expected
        detail = f"quest[{a.stream_id}].status={status!r} (expected {a.expected!r})"
    else:
        passed = False
        detail = f"quest[{a.stream_id}] not found in quest_updates"
```

### 4.2 — Add quest_status assert to `full_cycle` turn 7

```python
# In full_cycle.py, Turn 7 asserts:
asserts=[
    TurnAssert(stream="extract.progress", field="quest_updates", expected="deliver_the_ledger"),
    TurnAssert(
        stream="extract.progress",
        field="quest_status",
        stream_id="deliver_the_ledger",
        expected="completed",
    ),
],
```

### 4.3 — Add rubric guidance for quest status

In `evals/rubrics/default.md`, update criterion `extraction_consistency`:

```markdown
### 5. extraction_consistency
...
- extract.progress marks quest `status: completed` when all objectives are `done: true`
  (auto_complete) — failure here means the quest silently hangs open.
```

---

## Phase 5 — Momentum Scenario Variants (Issue 4 partial)

**Goal:** Test high-momentum and low-momentum paths using the `seed_overrides` infrastructure from Phase 3.3.

**Note on live constants:** `MOMENTUM_MAX` and `MOMENTUM_MIN` are imported from `engine_mirror`, so `seed_overrides` values and `expects` strings are always accurate.

### 5.1 — `momentum_high` scenario

```python
# evals/scenarios/momentum_high.py
from ccya.eval.scenario import Scenario, Turn, TurnAssert
from ccya.eval.engine_mirror import MOMENTUM_MAX

scenario = Scenario(
    id="momentum_high",
    pack="eval-pack",
    description=f"Starts with momentum={MOMENTUM_MAX}. Verifies narration tone reflects opportunity, not struggle.",
    seed_overrides={"meta.momentum": MOMENTUM_MAX},
    turns=[
        Turn(
            input="I walk up to Caron confidently and tell him the debt is settled before he can speak.",
            phase="high_momentum_social",
            expects=[
                f"Narrate should reflect HIGH MOMENTUM advisory from narrate_user.j2 (momentum={MOMENTUM_MAX})",
                "Raised stakes or elevated consequence expected in narration",
            ],
            asserts=[TurnAssert(stream="rules", field="rolled", expected="true")],
        ),
        Turn(
            input="I pocket the ledger receipt and head for the door without looking back.",
            phase="momentum_maintained",
            expects=["momentum should remain elevated unless roll fails"],
        ),
        Turn(
            input="I try to fast-talk the innkeeper into giving me a free room for the night.",
            phase="momentum_spend",
            expects=[
                "rules.required=true skill=charisma",
                "difficulty should reflect favorable conditions given high momentum",
            ],
            asserts=[TurnAssert(stream="rules", field="rolled", expected="true")],
        ),
    ],
)
```

### 5.2 — `momentum_low` scenario

```python
# evals/scenarios/momentum_low.py
from ccya.eval.scenario import Scenario, Turn, TurnAssert
from ccya.eval.engine_mirror import MOMENTUM_MIN

scenario = Scenario(
    id="momentum_low",
    pack="eval-pack",
    description=f"Starts with momentum={MOMENTUM_MIN}. Verifies engine offers small breaks per narrate_user.j2 advisory.",
    seed_overrides={"meta.momentum": MOMENTUM_MIN},
    turns=[
        Turn(
            input="I try to reason with Caron. Tell him I can get the money by nightfall.",
            phase="low_momentum_plea",
            expects=[
                f"Narrate should reflect LOW MOMENTUM advisory (momentum={MOMENTUM_MIN})",
                "Small break or partial success expected — not piling on",
            ],
            asserts=[TurnAssert(stream="rules", field="rolled", expected="true")],
        ),
        Turn(
            input="I accept whatever Caron says and leave the tavern quietly.",
            phase="low_momentum_exit",
            expects=["narration should not compound misery without reason"],
        ),
        Turn(
            input="I find a quiet corner and assess my options.",
            phase="low_momentum_recover",
            expects=[
                "rules.required=false (reflection, no obstacle)",
                "momentum should not drop further on no-roll turn",
            ],
            asserts=[TurnAssert(stream="rules", field="rolled", expected="false")],
        ),
    ],
)
```

---

## Phase 6 — Config and CI Wiring

### 6.1 — Register new scenarios in `evals/config.yaml`

```yaml
scenarios:
  - full_cycle
  - pressure_lifecycle
  - gm_beat_lifecycle
  - momentum_high
  - momentum_low
```

### 6.2 — `context_economy_warn_tokens` threshold

Add to the `judge:` block in `evals/config.yaml`:

```yaml
judge:
  model: ...
  rubric_path: evals/rubrics/default.md
  temperature: 0.0
  context_economy_warn_tokens: 8000
```

Add to `EvalConfig`'s judge section in `ccya/eval/config.py`:

```python
@dataclass
class JudgeConfig:
    model: str = ""
    rubric_path: str = "evals/rubrics/default.md"
    temperature: float = 0.0
    context_economy_warn_tokens: int = 8000   # <-- new
```

### 6.3 — Guard `context_meta` absence in report

`report.py` additions from Phase 2.4 must guard against missing keys — existing runs won't have `context_meta`:

```python
cm = (ev.get("extraction") or {}).get(stream, {}).get("context_meta") or {}
# .get() returns {} for old runs; all subsequent .get() calls are safe
```

---

## Phase 7 — Tier 1 Schema Validation Test (new, `make test`)

**Goal:** Catch stale `TurnAssert` field paths and broken `engine_mirror` imports at `make test` time, before any LLM is involved.

This is the "automatic reflection" layer. It doesn't test LLM output — it tests that the eval harness itself is structurally valid against the live codebase.

### 7.1 — Create `tests/test_eval_schema.py`

**File:** `tests/test_eval_schema.py`

**What:** A Tier 1 test that loads all scenarios via `discover_scenarios()`, then for each `TurnAssert` validates that `(stream, field)` is a known combination according to `engine_mirror.KNOWN_ASSERT_FIELDS`. Also validates that `engine_mirror` constants are importable and self-consistent.

**Why:** If a field is renamed in `runner._check_asserts` (e.g. `quest_updates` → `quest_progress`), this test fails immediately under `make test` with a clear error naming the scenario, turn, and field. Without this, the assertion silently passes or fails wrong during a full eval run — which is slow, costs LLM calls, and produces misleading scores.

**Code Snippet**
```python
"""Tier 1 schema validation for eval scenarios and engine_mirror.

Runs under `make test`. No LLM calls. No I/O beyond imports.
"""
import pytest
from ccya.eval.scenario import discover_scenarios
from ccya.eval.engine_mirror import (
    KNOWN_ASSERT_FIELDS,
    EXTRACT_STREAMS,
    PRESSURE_BUILDING_AT,
    PRESSURE_IMMEDIATE_AT,
    MOMENTUM_MIN,
    MOMENTUM_MAX,
    constants_block,
)


def test_engine_mirror_imports() -> None:
    """engine_mirror constants are importable and self-consistent."""
    assert PRESSURE_BUILDING_AT < PRESSURE_IMMEDIATE_AT, (
        f"PRESSURE_BUILDING_AT ({PRESSURE_BUILDING_AT}) must be < "
        f"PRESSURE_IMMEDIATE_AT ({PRESSURE_IMMEDIATE_AT})"
    )
    assert MOMENTUM_MIN < 0 < MOMENTUM_MAX
    block = constants_block()
    assert "Engine Constants" in block
    assert str(PRESSURE_BUILDING_AT) in block


def test_engine_mirror_known_fields_cover_streams() -> None:
    """Every stream in EXTRACT_STREAMS has an entry in KNOWN_ASSERT_FIELDS."""
    for stream in EXTRACT_STREAMS:
        assert stream in KNOWN_ASSERT_FIELDS, (
            f"Stream {stream!r} in EXTRACT_STREAMS has no entry in KNOWN_ASSERT_FIELDS. "
            f"Add it or remove it from EXTRACT_STREAMS."
        )


@pytest.mark.parametrize("scenario", discover_scenarios())
def test_scenario_assert_fields_are_known(scenario) -> None:
    """Every TurnAssert in every scenario uses a known (stream, field) combination.

    Fails immediately with the scenario id, turn index, and field name when a
    field is renamed in runner._check_asserts without updating KNOWN_ASSERT_FIELDS.
    """
    for turn_idx, turn in enumerate(scenario.turns):
        for assert_ in (turn.asserts or []):
            known_fields = KNOWN_ASSERT_FIELDS.get(assert_.stream)
            assert known_fields is not None, (
                f"Scenario {scenario.id!r} turn {turn_idx} uses unknown stream "
                f"{assert_.stream!r}. Add it to KNOWN_ASSERT_FIELDS in engine_mirror.py "
                f"and add a handler in runner._check_asserts."
            )
            assert assert_.field in known_fields, (
                f"Scenario {scenario.id!r} turn {turn_idx}: stream {assert_.stream!r} "
                f"has no field {assert_.field!r}. "
                f"Known fields: {sorted(known_fields)}. "
                f"Update engine_mirror.KNOWN_ASSERT_FIELDS and runner._check_asserts together."
            )


def test_scenario_seed_overrides_use_known_paths() -> None:
    """seed_overrides dotpaths are in a known set — catches typos before a full eval run."""
    KNOWN_SEED_PATHS: set[str] = {
        "meta.momentum",
        "scene.scene_pressure",
        "pc.conditions",
        "pc.credits",
    }
    for scenario in discover_scenarios():
        for path in (scenario.seed_overrides or {}):
            assert path in KNOWN_SEED_PATHS, (
                f"Scenario {scenario.id!r} uses unknown seed_override path {path!r}. "
                f"Add it to KNOWN_SEED_PATHS in test_eval_schema.py if it's intentional."
            )
```

**Validation:** `make test` passes. Rename `rolled` → `roll_fired` in `KNOWN_ASSERT_FIELDS` without updating a scenario → test fails naming the scenario and field.

### 7.2 — Maintenance contract for `KNOWN_ASSERT_FIELDS`

When a new assert handler is added to `runner._check_asserts`:
1. Add the `(stream, field)` to `engine_mirror.KNOWN_ASSERT_FIELDS`.
2. `make test` will enforce it from that point forward.

When a field is renamed:
1. Update `runner._check_asserts`.
2. Update `engine_mirror.KNOWN_ASSERT_FIELDS`.
3. `make test` catches any scenario that still uses the old name.

This is the only manual step required when extending the assertion system.

---

## Implementation Order

```
Phase 0 (engine_mirror — no engine changes, pure imports)
  → Phase 1 (rubric text only — no code)
  → Phase 2 (engine telemetry — most invasive, touches llm_client + extraction + narrate)
  → Phase 3 (new scenarios using engine_mirror + runner seed_overrides + state snapshots)
  → Phase 4 (TurnAssert.stream_id + quest_status handler + full_cycle update)
  → Phase 5 (momentum scenarios — depend on seed_overrides from Phase 3)
  → Phase 6 (config + report guards)
  → Phase 7 (Tier 1 schema test — run last so all scenarios/handlers exist)
```

---

## Files Touched

| File | Change |
|---|---|
| `ccya/eval/engine_mirror.py` | Phase 0.1 (new file — live constants + KNOWN_ASSERT_FIELDS + constants_block()) |
| `ccya/eval/__init__.py` | Phase 0.2 (re-export engine_mirror) |
| `evals/rubrics/default.md` | Phases 1.1, 1.2, 1.3, 4.3 |
| `ccya/eval/judge.py` | Phase 1.2 (`turns` field in findings), Phase 2.3 (constants_block prefix + `[context]` line in `build_trace`) |
| `ccya/eval/report.py` | Phases 1.2, 2.4 (render `turns`, context warnings section) |
| `ccya/eval/scenario.py` | Phase 3.3 (`seed_overrides` on `Scenario`), Phase 4.1 (`stream_id` on `TurnAssert`) |
| `ccya/eval/runner.py` | Phases 3.3 (seed_overrides, state snapshots, `state_yaml` assert handler), 4.1 (`quest_status` handler) |
| `ccya/eval/config.py` | Phase 6.2 (`context_economy_warn_tokens` on `JudgeConfig`) |
| `ccya/llm_client.py` | Phase 2.2 (`trim_messages` returns `(messages, was_trimmed, trimmed_chars)`) |
| `ccya/engine/extraction.py` | Phases 2.1, 2.2 (attach `context_meta`, capture truncation flag) |
| `ccya/engine/narrate.py` | Phases 2.1, 2.2 (attach `context_meta` to narrate event) |
| `evals/scenarios/pressure_lifecycle.py` | Phase 3.1 (new — imports PRESSURE_BUILDING_AT/IMMEDIATE_AT from engine_mirror) |
| `evals/scenarios/gm_beat_lifecycle.py` | Phase 3.2 (new file) |
| `evals/scenarios/momentum_high.py` | Phase 5.1 (new — imports MOMENTUM_MAX from engine_mirror) |
| `evals/scenarios/momentum_low.py` | Phase 5.2 (new — imports MOMENTUM_MIN from engine_mirror) |
| `evals/scenarios/full_cycle.py` | Phase 4.2 (`quest_status` assert on turn 7) |
| `evals/config.yaml` | Phases 6.1, 6.2 (scenario list, `context_economy_warn_tokens`) |
| `tests/test_eval_schema.py` | Phase 7.1 (new Tier 1 test — validates scenario assert paths against live engine) |
| `docs/REPOMAP/eval.md` | Add `engine_mirror` row to package structure table; add `test_eval_schema.py` to test files |
