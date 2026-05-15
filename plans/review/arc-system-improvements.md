# ARC System Improvements

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Wire arc_update into apply_delta | apply_delta currently ignores StateDelta.arc_update; make it apply surgical arc mutations |
| 02 | Thread promotion engine | Deterministic rules that auto-promote latent threads to active based on thread_signals and progress counters |
| 03 | Secret reveal pipeline | Plumb hidden_truths → discovered_truths reveal path: extraction signal + apply_delta + narrator context |
| 04 | Candidate thread lifecycle | Extract candidate_opportunity into arc as latent threads; cap active thread count; retire stale threads |
| 05 | Narrator arc context upgrade | Expand _arc.j2 and narrate_user.j2 so narrator sees phase-appropriate thread depth and revealed truths |

---

## Objective

The ARC system has correct data structures (`CampaignArc`, `ArcThread`, `ThreadState`, `ThreadSignal`, `hidden_truths`, `discovered_truths`) and the extraction pipeline faithfully emits `thread_signals`, `player_drift_signals`, and `candidate_opportunity` every turn. However, none of that output is ever consumed: `apply_delta` ignores `StateDelta.arc_update`, no code promotes latent→active threads, no code reveals secrets, and `candidate_opportunity` is discarded. The narrator receives a shallow arc context with no visibility into thread state, phase, or revealed truths. The result is an ARC that is written once at pack generation and never evolves.

## Non-goals
- Do not redesign the pack generation arc schema — the existing `CampaignArc` shape is correct.
- Do not change how `thread_signals` are emitted — the extractor is working.
- Do not add a new LLM call for arc management — all transitions must be deterministic code in `state/delta.py` and `engine/turn.py`.
- Do not expose arc internals (hidden_truths, latent thread details) in the player-facing narrator context — only revealed information surfaces.
- Do not change `ArcThread` or `CampaignArc` Pydantic shapes — they are correct and should not be mutated.

---

## Implementation — Phase 01: Wire arc_update into apply_delta

### Files to pull for context
- `ccya/state/delta.py`
- `ccya/models.py` (CampaignArc, ArcThread, StateDelta)

### Detailed steps

#### Step 1.1 — Apply arc_update in apply_delta

**File:** `ccya/state/delta.py`

**What:** At the end of `apply_delta`, after all scene/inventory/NPC mutations, check `delta.arc_update`. If present, merge it surgically into `state["arc"]` — do not wholesale replace the arc. Merge rules:
- `visible_goal`, `thematic_question`, `phase`, `pc_drive` → overwrite if non-empty string
- `hidden_truths` → replace list if non-empty
- `discovered_truths` → union (append new entries not already present)
- `active_threads` → upsert by `id`: update `summary`, `urgency`, `progress`, `state` if present; append new threads not already in arc; do NOT delete threads missing from the update
- `latent_threads` → same upsert logic
- `completed_threads` → union by id
- `arc_engagement` → overwrite if > current value (never regress)

**Why:** `StateDelta.arc_update` has existed in the model since the field was added but `apply_delta` never reads it. This is the missing write path for all downstream phases.

**Code Snippet**
```python
# At end of apply_delta, before return statement:
if delta.arc_update is not None:
    arc = state.setdefault("arc", {})
    au = delta.arc_update

    def _upsert_threads(existing: list[dict[str, Any]], updates: list[Any]) -> list[dict[str, Any]]:
        by_id = {t["id"]: t for t in existing if isinstance(t, dict)}
        for t in updates:
            td = t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
            tid = td.get("id")
            if not tid:
                continue
            if tid in by_id:
                by_id[tid].update({k: v for k, v in td.items() if v is not None})
            else:
                by_id[tid] = td
        return list(by_id.values())

    if au.visible_goal:
        arc["visible_goal"] = au.visible_goal
    if au.thematic_question:
        arc["thematic_question"] = au.thematic_question
    if au.phase and au.phase != ArcPhase.SETUP:
        arc["phase"] = au.phase.value if hasattr(au.phase, "value") else str(au.phase)
    if au.pc_drive:
        arc["pc_drive"] = au.pc_drive
    if au.hidden_truths:
        arc["hidden_truths"] = au.hidden_truths
    if au.discovered_truths:
        existing_dt = set(arc.get("discovered_truths") or [])
        arc["discovered_truths"] = list(existing_dt | set(au.discovered_truths))
    if au.active_threads:
        arc["active_threads"] = _upsert_threads(arc.get("active_threads") or [], au.active_threads)
    if au.latent_threads:
        arc["latent_threads"] = _upsert_threads(arc.get("latent_threads") or [], au.latent_threads)
    if au.completed_threads:
        existing_comp = {t["id"] for t in (arc.get("completed_threads") or []) if isinstance(t, dict)}
        for t in au.completed_threads:
            td = t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
            if td.get("id") not in existing_comp:
                arc.setdefault("completed_threads", []).append(td)
    if au.arc_engagement and au.arc_engagement > (arc.get("arc_engagement") or 0):
        arc["arc_engagement"] = au.arc_engagement
```

**Why:** Surgical merge prevents one malformed arc_update from nuking the entire arc state.

**Validation:** Unit test: construct a state with a partial arc + a StateDelta with arc_update; call apply_delta; assert fields are merged, not replaced. Existing arc fields not in arc_update must survive unchanged.

### Tests to write or update
- `tests/test_delta.py` → `test_arc_update_applied`, `test_arc_update_merge_not_replace`, `test_arc_update_discovered_truths_union`, `test_arc_update_none_noop`

### REPOMAP and architecture updates
- `docs/REPOMAP/state.md` — document `arc_update` handling in `apply_delta`

### Risks
1. `ArcPhase` enum `.value` access — verify import in `delta.py` (currently only `models.py` imports it). Mitigation: import `ArcPhase` from `ccya.models`.
2. Malformed arc_update from LLM with null thread ids silently corrupts arc. Mitigation: `_upsert_threads` skips any thread with no `id`.

---

## Implementation — Phase 02: Thread Promotion Engine

### Files to pull for context
- `ccya/engine/turn.py`
- `ccya/models.py` (ArcThread, ThreadState, ThreadSignal, ProgressExtractResult)
- `ccya/state/delta.py` (after Phase 01 is applied)

### Detailed steps

#### Step 2.1 — Write _apply_thread_signals() in engine/turn.py

**File:** `ccya/engine/turn.py`

**What:** After extraction completes and before `apply_delta` is called, call a new deterministic function `_apply_thread_signals(state, progress_result, turn_no)` that:
1. Reads `progress_result.thread_signals` (list of `ThreadSignal`).
2. For each `advanced` signal: find the matching thread in `state["arc"]["active_threads"]` by id; increment `thread.progress` by 1.
3. Promotion check: for each latent thread in `state["arc"]["latent_threads"]`, if the current `arc.phase` warrants it AND the thread's `unlock_if` condition string is either empty or matched by the narration context, move it to `active_threads` with `state = ACTIVE`. Cap `active_threads` at 4 — if at cap, do not promote until an active thread completes.
4. Completion check: any active thread with `progress >= 3` AND a `failed`/`advanced` signal in the same turn moves to `completed_threads` with appropriate `state` value.
5. Phase progression: if all active threads are completed/failed and `latent_threads` is non-empty, advance `arc.phase` by one step (SETUP→PURSUIT→REVERSAL→CRISIS→RESOLUTION).
6. Return a `CampaignArc | None` delta — only non-None if any mutation occurred.

**Why:** Promotion must be deterministic engine code, not another LLM judgment call. The extractor already provides the signal; the engine should act on it.

**Code Snippet**
```python
from ccya.models import ArcPhase, ArcThread, ThreadState

_ARC_PHASE_ORDER = [
    ArcPhase.SETUP, ArcPhase.PURSUIT, ArcPhase.REVERSAL,
    ArcPhase.CRISIS, ArcPhase.RESOLUTION,
]
_ACTIVE_THREAD_CAP = 4


def _apply_thread_signals(
    state: dict[str, Any],
    progress_result: ProgressExtractResult,
    turn_no: int,
) -> CampaignArc | None:
    arc_raw = state.get("arc")
    if not arc_raw:
        return None
    try:
        arc = CampaignArc.model_validate(arc_raw)
    except Exception:
        return None

    signal_map: dict[str, str] = {s.id: s.signal.value for s in progress_result.thread_signals}
    mutated = False

    active_by_id = {t.id: t for t in arc.active_threads}
    latent_by_id = {t.id: t for t in arc.latent_threads}
    completed_ids = {t.id for t in arc.completed_threads}

    # --- Increment progress on advanced signals ---
    for tid, sig in signal_map.items():
        if sig == "advanced" and tid in active_by_id:
            t = active_by_id[tid]
            active_by_id[tid] = t.model_copy(update={"progress": t.progress + 1})
            mutated = True

    # --- Complete threads that have hit threshold or received failed signal ---
    newly_completed: list[ArcThread] = []
    still_active: list[ArcThread] = []
    for tid, t in active_by_id.items():
        sig = signal_map.get(tid, "ignored")
        if t.progress >= 3 and sig in ("advanced", "failed"):
            new_state = ThreadState.FAILED if sig == "failed" else ThreadState.COMPLETE
            newly_completed.append(t.model_copy(update={"state": new_state}))
            mutated = True
        elif sig == "failed":
            newly_completed.append(t.model_copy(update={"state": ThreadState.FAILED}))
            mutated = True
        else:
            still_active.append(t)
    arc = arc.model_copy(update={
        "active_threads": still_active,
        "completed_threads": arc.completed_threads + newly_completed,
    })

    # --- Promote latent threads up to cap ---
    if len(arc.active_threads) < _ACTIVE_THREAD_CAP:
        available = [
            t for t in arc.latent_threads
            if t.id not in completed_ids
            and t.id not in {at.id for at in arc.active_threads}
        ]
        slots = _ACTIVE_THREAD_CAP - len(arc.active_threads)
        to_promote = available[:slots]
        if to_promote:
            promoted = [t.model_copy(update={"state": ThreadState.ACTIVE}) for t in to_promote]
            remaining_latent = [t for t in arc.latent_threads if t.id not in {p.id for p in to_promote}]
            arc = arc.model_copy(update={
                "active_threads": arc.active_threads + promoted,
                "latent_threads": remaining_latent,
            })
            mutated = True

    # --- Phase progression ---
    if arc.active_threads == [] and arc.latent_threads:
        current_idx = next(
            (i for i, p in enumerate(_ARC_PHASE_ORDER) if p.value == str(arc.phase)), 0
        )
        if current_idx < len(_ARC_PHASE_ORDER) - 1:
            arc = arc.model_copy(update={"phase": _ARC_PHASE_ORDER[current_idx + 1]})
            mutated = True

    if not mutated:
        return None
    return arc
```

#### Step 2.2 — Call _apply_thread_signals in turn.py and fold result into delta

**File:** `ccya/engine/turn.py`

**What:** After extraction pipeline yields, before calling `apply_delta`:
```python
arc_delta = _apply_thread_signals(state, progress_result, turn_no)
if arc_delta is not None:
    merged_delta = merged_delta.model_copy(update={"arc_update": arc_delta})
```

**Why:** This closes the loop — signals extracted → deterministic mutations → merged into StateDelta → applied to state.

**Validation:** After a turn where a thread signal of `advanced` is emitted for an active thread, assert `state.arc.active_threads[matching_thread].progress` has incremented.

### Tests to write or update
- `tests/test_arc.py` (new file) → `test_thread_progress_increment_on_advanced_signal`, `test_thread_completes_at_threshold`, `test_latent_thread_promoted_when_slot_available`, `test_active_cap_prevents_promotion`, `test_phase_advances_when_all_complete`
- Use `FakeLLM` patterns from `docs/REPOMAP/testing.md` for any turn-level tests.

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — document `_apply_thread_signals` function, inputs, outputs
- `docs/REPOMAP/models.md` — note `ArcPhase` progression order

### Risks
1. `CampaignArc.model_validate(arc_raw)` may fail on older saves missing new fields. Mitigation: wrap in try/except and return None (noop) on failure.
2. `progress >= 3` threshold is arbitrary — may complete threads too quickly or too slowly. Mitigation: make threshold configurable via `EngineConfig.arc_thread_completion_threshold: int = 3` (Phase 01 of config plan, or add here).
3. Phase progression fires when `active_threads == []` but that may happen mid-game if signals are noisy. Mitigation: also require at least one thread was completed (not just that active list is empty).

---

## Implementation — Phase 03: Secret Reveal Pipeline

### Files to pull for context
- `ccya/models.py` (CampaignArc, ProgressExtractResult)
- `ccya/prompts/extract_progress_system.j2`
- `ccya/prompts/extract_progress_user.j2`
- `ccya/state/delta.py` (after Phase 01)

### Detailed steps

#### Step 3.1 — Add secret_reveal field to ProgressExtractResult

**File:** `ccya/models.py`

**What:** Add `secret_reveal: list[str] = Field(default_factory=list)` to `ProgressExtractResult`. Each entry is the exact text of a `hidden_truths` entry the narration has surfaced.

**Why:** The extractor needs a channel to signal that a hidden truth was revealed this turn. Without it there is no way to move a truth from `hidden_truths` to `discovered_truths`.

**Code Snippet**
```python
class ProgressExtractResult(BaseModel):
    # ... existing fields ...
    secret_reveal: list[str] = Field(default_factory=list)
```

#### Step 3.2 — Add secret reveal guidance to extract_progress_system.j2

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Add a new section after the `thread_signals` field rule:

```
`secret_reveal`: If the narration this turn has explicitly surfaced information that matches one of
the hidden_truths shown in context (exact or near-exact match), include that truth's text in this list.
Leave empty if no secret was narrated. Do not infer — only emit if the narration states it outright.
```

Add `"secret_reveal": []` to the output schema block.

**Why:** The LLM needs explicit instruction; without it, it will never emit this field even when relevant.

#### Step 3.3 — Surface hidden_truths in extract_progress_user.j2

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** In the `active_threads` block, after the thread list, add a conditional block:

```jinja2
{% if arc_hidden_truths -%}
## arc_hidden_truths (for reveal detection only — never expose to player)
{% for truth in arc_hidden_truths %}- {{ truth }}
{% endfor %}
{% endif -%}
```

Wire `arc_hidden_truths` from `_extract_progress_messages` in `extraction.py`:
```python
arc_hidden_truths = [
    t for t in ((state.get("arc") or {}).get("hidden_truths") or [])
    if t not in ((state.get("arc") or {}).get("discovered_truths") or [])
]
```
Pass as `"arc_hidden_truths": arc_hidden_truths` in the render context.

**Why:** The extractor can only detect a reveal if it knows what secrets exist. Wrapping in a trace-immutable block or keeping it in a clearly marked "for reasoning only" section prevents the narrator from leaking it.

#### Step 3.4 — Consume secret_reveal in _apply_thread_signals (or new helper)

**File:** `ccya/engine/turn.py`

**What:** In `_apply_thread_signals` (or a new `_apply_secret_reveals`), after processing thread signals:
```python
if progress_result.secret_reveal:
    existing_dt = set(arc.discovered_truths)
    newly_revealed = [s for s in progress_result.secret_reveal if s not in existing_dt]
    if newly_revealed:
        arc = arc.model_copy(update={
            "discovered_truths": arc.discovered_truths + newly_revealed
        })
        mutated = True
```

**Validation:** Set up a state with `hidden_truths: ["The baron is the killer"]`; configure FakeLLM to emit `secret_reveal: ["The baron is the killer"]`; run turn; assert `state.arc.discovered_truths` contains the entry and `state.arc.hidden_truths` still contains it (we never delete hidden truths — discovered is additive).

### Tests to write or update
- `tests/test_arc.py` → `test_secret_reveal_moves_to_discovered`, `test_secret_reveal_no_duplicate`, `test_no_reveal_when_not_in_narration`

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md` — document `arc_hidden_truths` context block in `extract_progress_user.j2`; document `secret_reveal` field in `ProgressExtractResult`

### Risks
1. LLM may hallucinate a secret reveal not actually in the narration. Mitigation: fuzzy-match `secret_reveal` entries against `hidden_truths` list before accepting — reject any entry not within edit distance 10 of an actual hidden truth (simple `difflib.get_close_matches` check in engine).
2. Showing `arc_hidden_truths` to the progress extractor creates a risk the narrator template also sees them if templates are ever merged. Mitigation: the block is only in `extract_progress_user.j2`, not `narrate_user.j2` or `_arc.j2`.

---

## Implementation — Phase 04: Candidate Thread Lifecycle

### Files to pull for context
- `ccya/engine/turn.py`
- `ccya/models.py` (ArcThread, ThreadState)
- `ccya/engine/extraction.py` (`_extract_progress_messages`)

### Detailed steps

#### Step 4.1 — Convert candidate_opportunity into a latent ArcThread

**File:** `ccya/engine/turn.py`

**What:** After `_apply_thread_signals`, if `progress_result.candidate_opportunity` is non-null and non-empty:
1. Generate a stable snake_case id from the first 5 words of the opportunity string.
2. Check that no thread with a similar id already exists in `arc.active_threads + arc.latent_threads`.
3. Create an `ArcThread(id=..., summary=candidate_opportunity, state=ThreadState.LATENT, urgency="background")`.
4. Add to `arc.latent_threads` via the arc_update merge path.

Cap total `latent_threads` at 6 — if at cap, drop the oldest by `last_offered_turn` (or id lexicographic fallback).

**Code Snippet**
```python
def _candidate_to_latent_thread(
    arc: CampaignArc,
    candidate: str,
    turn_no: int,
) -> CampaignArc | None:
    if not candidate or not candidate.strip():
        return None
    words = candidate.strip().split()[:5]
    tid = "_".join(w.lower().strip(".,;:!?\"'") for w in words)
    existing_ids = {t.id for t in arc.active_threads + arc.latent_threads + arc.completed_threads}
    if tid in existing_ids:
        return None
    new_thread = ArcThread(
        id=tid,
        summary=candidate.strip(),
        state=ThreadState.LATENT,
        urgency="background",
        last_offered_turn=turn_no,
    )
    latent = list(arc.latent_threads)
    _LATENT_CAP = 6
    if len(latent) >= _LATENT_CAP:
        # Evict oldest
        latent.sort(key=lambda t: t.last_offered_turn or 0)
        latent = latent[1:]
    return arc.model_copy(update={"latent_threads": latent + [new_thread]})
```

**Why:** `candidate_opportunity` is currently discarded every turn. Converting it to a latent thread gives the arc a self-populating hook pool.

#### Step 4.2 — Stale thread expiry

**File:** `ccya/engine/turn.py`

**What:** In `_apply_thread_signals`, before returning, expire latent threads that have been latent for more than 10 turns without promotion (configurable via `EngineConfig.arc_latent_thread_ttl: int = 10`). Move them to `completed_threads` with `state=ThreadState.EXPIRED`.

**Validation:** Construct an arc with a latent thread at `last_offered_turn=0`; run `_apply_thread_signals` at `turn_no=11`; assert thread is in `completed_threads` with state `expired`.

### Tests to write or update
- `tests/test_arc.py` → `test_candidate_becomes_latent_thread`, `test_candidate_dedup_by_id`, `test_latent_cap_evicts_oldest`, `test_stale_latent_thread_expires`

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — document candidate→latent conversion and stale expiry

### Risks
1. Id generation from candidate text may collide on short candidates. Mitigation: append `_t{turn_no}` suffix if collision detected.
2. 6-latent cap may feel too restrictive for long campaigns. Mitigation: make it `EngineConfig.arc_latent_thread_cap: int = 6`.

---

## Implementation — Phase 05: Narrator Arc Context Upgrade

### Files to pull for context
- `ccya/prompts/sections/_arc.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/engine/narrate.py`

### Detailed steps

#### Step 5.1 — Expand _arc.j2 with phase, thread state, and discovered truths

**File:** `ccya/prompts/sections/_arc.j2`

**What:** Replace the current shallow template with:

```jinja2
{% if state.arc and state.arc.get('visible_goal') -%}
### Campaign Arc
**Goal:** {{ state.arc.get('visible_goal', '') }}
**Phase:** {{ state.arc.get('phase', 'setup') | upper }}
**Thematic question:** {{ state.arc.get('thematic_question', '') }}
{% if state.arc.get('pc_drive') -%}
**PC drive:** {{ state.arc.get('pc_drive', '') }}
{% endif -%}
{% if state.arc.get('active_threads') -%}
**Active threads:**
{% for t in state.arc.get('active_threads') -%}
- [{{ t.get('urgency', 'normal') | upper }}] {{ t.get('summary', '') }}{% if t.get('progress', 0) > 0 %} (progress: {{ t.get('progress') }}){% endif %}
{% endfor -%}
{% endif -%}
{% if state.arc.get('discovered_truths') -%}
**Known truths (revealed):**
{% for truth in state.arc.get('discovered_truths') -%}
- {{ truth }}
{% endfor -%}
{% endif -%}
{%- else -%}
No active campaign arc.
{% endif -%}
```

**Why:** The narrator currently sees only `visible_goal`, `phase`, and `active_thread summaries`. It has no visibility into `pc_drive` (which shapes inner narration), `thematic_question` (which shapes emotional register), thread progress (which should affect urgency tone), or discovered truths (which the narration should reflect as known facts).

#### Step 5.2 — Ensure narrate_user.j2 passes full arc state to _arc.j2

**File:** `ccya/engine/narrate.py` and `ccya/prompts/narrate_user.j2`

**What:** Verify the `state` dict passed to the narrator template includes the full `arc` sub-dict (not just `current_arc`). The existing `current_arc` context dict in `narrate_user.j2` is a flattened extraction — check whether `pc_drive` and `discovered_truths` are already passed through; add them if missing.

Read `narrate_user.j2` and `narrate.py` before implementing to confirm current wiring. If `current_arc` is constructed from `state.arc` in `narrate.py`, add `pc_drive` and `discovered_truths` to that construction. If the template uses `_arc.j2` include with `state.arc` directly, Step 5.1 is sufficient.

**Validation:** After a turn where `discovered_truths` is non-empty, check that the rendered narrator system prompt contains the discovered truth text.

### Tests to write or update
- No new tests required for template changes; validate via `_log_prompts` output inspection or a unit test that renders the template with a fixture state and asserts the discovered truth appears.

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md` — update `_arc.j2` description to reflect new fields

### Risks
1. Adding `pc_drive` and `thematic_question` to narrator context increases prompt size. Estimate: ~50–100 tokens. Acceptable given their value. Monitor `context_meta.est_tokens` in turn viewer.
2. `discovered_truths` may contain player-sensitive spoilers that were intended to surface gradually. Mitigation: the template only shows `discovered_truths` (already revealed), never `hidden_truths`.

---

## Ambiguities requiring resolution before execution

1. In Phase 02 Step 2.1, the completion threshold is hardcoded at `progress >= 3`. Should this be pack-configurable (per-thread) or a global `EngineConfig` value? Options: A) Global `EngineConfig.arc_thread_completion_threshold: int = 3` B) Per-thread field `ArcThread.completion_threshold: int = 3` with pack-level override. Per-thread is more flexible but adds schema complexity.

2. In Phase 03 Step 3.2, the `arc_hidden_truths` block is shown to the progress extractor for reveal detection. Should we also show it to the state extractor (for inventory/condition-driven reveals) or only the progress extractor? Options: A) Progress extractor only (simpler, less exposure) B) Both progress and state (would allow item-use to trigger a reveal). Current assumption: progress extractor only.

3. In Phase 05 Step 5.2, the current `narrate_user.j2` uses a `current_arc` context dict constructed in `narrate.py` — not the raw `state.arc` dict. Before implementing, confirm whether `_arc.j2` receives `state` (the full state dict) or `current_arc` (the flattened dict). If the latter, Phase 05 must also update `narrate.py`'s arc dict construction. This must be verified by reading `narrate_user.j2` and `narrate.py` before any code is written.
