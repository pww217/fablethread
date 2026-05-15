# Arc System Improvements — Reconciled MVP1

## Status
`open`

## Objective

The ARC system has correct data structures and a working extraction pipeline, but the arc never evolves: `apply_delta` ignores `StateDelta.arc_update`, thread signals are discarded after extraction, and `candidate_opportunity` floods `latent_threads` with uncapped tactical noise. The narrator has no write path for discovered truths. These four phases close the loop with no new LLM calls and minimal new code surface.

## Non-goals
- Do not add a dedicated arc-management LLM call — all promotion/expiry is deterministic engine code.
- Do not auto-advance `arc.phase` in engine code — the narrator emits `arc_update.phase` when the arc genuinely shifts.
- Do not implement secret-reveal detection in the progress extractor — the narrator is the correct entity to decide when a hidden truth has been surfaced.
- Do not implement stale-thread TTL expiry — deferred to post-MVP1.
- Do not change `CampaignArc`, `ArcThread`, or `StateDelta` Pydantic shapes.
- Do not add a `DriftAnalysis` Pydantic model — engagement scoring stays in engine code using existing `player_drift_signals` substring matching.

## Firm decisions
1. Thread lifecycle (signal processing, completion, promotion, latent cap) moves from `tick_arc()` in `arc.py` to dedicated functions in `turn.py`: `_apply_thread_signals()` and `_candidate_to_latent_thread()`. `tick_arc()` is retained for engagement scoring only.
2. Active thread cap is 4 (raised from the current 2-3 in `tick_arc()`).
3. Latent thread cap is 4 with tactical-first eviction. Pack-seeded (non-tactical) threads are never evicted.
4. The narrator sees `hidden_truths` in its context but is explicitly instructed not to reveal them in narration prose. It emits discovered truths via the `<<<ARC_UPDATE_START>>>` JSON block only.
5. Merge order: engine thread signals run first, narrator arc_update is parsed after narration and merged on top. Engine owns thread state; narrator owns phase, visible_goal, discovered_truths.

## Conflicts and overlap
- Supersedes the earlier `arc-system-improvements.md` (open plan) which proposed extraction improvements (thread tags in progress prompt, `DriftAnalysis` model). Those are deferred to a separate plan. This plan focuses on closing the arc evolution loop.
- No file overlap with `quest-story-arc-revamp.md` beyond `arc.py` and `models.py` which are already accounted for.

---

## Implementation — Phase 01: Wire arc_update into apply_delta

### Context files to load
1. `ccya/state/delta.py` — `apply_delta()` function
2. `ccya/models.py` — `CampaignArc`, `ArcPhase`

### Detailed steps

#### Step 1.1 — Add _merge_arc_update() to delta.py

**File:** `ccya/state/delta.py`

**What:** Add a private helper function and import `CampaignArc` from models. Call it at the end of `apply_delta` when `delta.arc_update` is not None.

**Why:** `StateDelta.arc_update: CampaignArc | None` exists on line 274 of `models.py` but `apply_delta` never reads it. Every downstream phase depends on this write path existing.

**Code Snippet**

Add `CampaignArc` to the existing import on line 10:
```python
from ccya.models import CampaignArc, StateDelta
```

Add the helper function before `reconcile_delta`:
```python
def _merge_arc_update(arc: dict[str, Any], au: CampaignArc) -> None:
    """Surgically merge arc_update into the live arc dict. Never wholesale replaces."""

    def _upsert_threads(
        existing: list[dict[str, Any]], updates: list[Any]
    ) -> list[dict[str, Any]]:
        by_id = {t["id"]: t for t in existing if isinstance(t, dict) and t.get("id")}
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
    if au.phase:
        arc["phase"] = au.phase.value if hasattr(au.phase, "value") else str(au.phase)
    if au.pc_drive:
        arc["pc_drive"] = au.pc_drive
    if au.hidden_truths:
        arc["hidden_truths"] = au.hidden_truths
    if au.discovered_truths:
        existing_dt = set(arc.get("discovered_truths") or [])
        arc["discovered_truths"] = list(existing_dt | set(au.discovered_truths))
    if au.active_threads:
        arc["active_threads"] = _upsert_threads(
            arc.get("active_threads") or [], au.active_threads
        )
    if au.latent_threads:
        arc["latent_threads"] = _upsert_threads(
            arc.get("latent_threads") or [], au.latent_threads
        )
    if au.completed_threads:
        existing_comp_ids = {
            t["id"] for t in (arc.get("completed_threads") or []) if isinstance(t, dict)
        }
        for t in au.completed_threads:
            td = t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
            if td.get("id") not in existing_comp_ids:
                arc.setdefault("completed_threads", []).append(td)
    if au.arc_engagement and au.arc_engagement > (arc.get("arc_engagement") or 0):
        arc["arc_engagement"] = au.arc_engagement
```

Call site at the end of `apply_delta`, before the `return` on line 521:
```python
    # --- Arc update: merge arc_update into state arc ---
    if delta.arc_update is not None:
        _merge_arc_update(state.setdefault("arc", {}), delta.arc_update)

    return state, recent_events_evicted
```

**Validation:** Unit test: construct a state with a partial arc + a `StateDelta` with `arc_update`; call `apply_delta`; assert merged fields updated, fields absent from `arc_update` survive unchanged, `discovered_truths` union not replace.

### Tests to write or update
`tests/test_delta.py` — add `test_arc_update_applied`, `test_arc_update_merge_not_replace`, `test_arc_update_discovered_truths_union`, `test_arc_update_none_noop`

### REPOMAP updates required
- `docs/REPOMAP/state.md` — document `arc_update` handling in `apply_delta`

### Risks
1. `CampaignArc` not currently imported in `delta.py` — add to imports. No circular import risk: `models.py` has no imports from `state/delta.py`.
2. `_upsert_threads` silently drops threads with no `id` — acceptable; threads always have IDs by construction.

---

## Implementation — Phase 02: Thread Promotion Engine

### Context files to load
1. `ccya/engine/turn.py` — `run_turn()` arc handling at lines 653-663
2. `ccya/models.py` — `ArcThread`, `CampaignArc`, `ThreadState`, `ThreadSignalType`
3. `ccya/engine/arc.py` — `tick_arc()` for reference on current signal processing logic

### Detailed steps

#### Step 2.1 — Add imports and constants to turn.py

**File:** `ccya/engine/turn.py`

**What:** Add `ArcPhase`, `ArcThread`, `ThreadState`, `ThreadSignalType` to the existing `from ccya.models import` block on lines 34-41.

**Why:** These types are needed by the new thread lifecycle functions.

**Code Snippet**

Change the existing import on lines 34-41 from:
```python
from ccya.models import (
    CampaignArc,
    IntentEnvelope,
    RulesCheck,
    RulesOutcome,
    StateDelta,
    TurnResult,
)
```
to:
```python
from ccya.models import (
    ArcPhase,
    ArcThread,
    CampaignArc,
    IntentEnvelope,
    RulesCheck,
    RulesOutcome,
    StateDelta,
    ThreadState,
    ThreadSignalType,
    TurnResult,
)
```

Add constants after the `_log` definition (after line 57):
```python
_ACTIVE_THREAD_CAP = 4
"""Maximum number of threads in the active state."""

_THREAD_COMPLETION_THRESHOLD = 3
"""Progress value at which an active thread is marked complete."""
```

#### Step 2.2 — Write _apply_thread_signals() in turn.py

**File:** `ccya/engine/turn.py`

**What:** A new deterministic function that replaces the signal-processing logic currently in `tick_arc()` (`arc.py` lines 93-227). Responsibilities:
1. Read `progress_result.thread_signals`.
2. For each `advanced` signal: find matching thread in `arc.active_threads` by id; increment `progress` by 1.
3. For each `failed` signal: move matching thread to `completed_threads` with `state=FAILED`.
4. Completion check: any active thread with `progress >= _THREAD_COMPLETION_THRESHOLD` moves to `completed_threads` with `state=COMPLETE`.
5. Promotion: while `len(arc.active_threads) < _ACTIVE_THREAD_CAP` and `arc.latent_threads` is non-empty, promote the first latent thread to `active` with `state=ACTIVE`.

Do NOT implement auto-phase-progression here — that belongs to the narrator (Phase 04). Do NOT handle engagement scoring — that stays in `tick_arc()`.

**Code Snippet**
```python
def _apply_thread_signals(
    state: dict[str, Any],
    progress_result: "ProgressExtractResult",
) -> "CampaignArc | None":
    """Process thread signals and update arc thread states.

    Returns a CampaignArc if any mutation occurred, None otherwise.
    """
    arc_raw = state.get("arc")
    if not arc_raw:
        return None
    try:
        arc = CampaignArc.model_validate(arc_raw)
    except Exception:
        return None

    signal_map: dict[str, str] = {
        s.id: s.signal.value for s in (progress_result.thread_signals or [])
    }
    if not signal_map and len(arc.active_threads) >= _ACTIVE_THREAD_CAP:
        return None  # nothing to do

    mutated = False
    active_by_id: dict[str, ArcThread] = {t.id: t for t in arc.active_threads}

    # Increment progress on advanced signals
    for tid, sig in signal_map.items():
        if sig == ThreadSignalType.ADVANCED.value and tid in active_by_id:
            t = active_by_id[tid]
            active_by_id[tid] = t.model_copy(update={"progress": t.progress + 1})
            mutated = True

    # Complete or fail threads
    newly_completed: list[ArcThread] = []
    still_active: list[ArcThread] = []
    for tid, t in active_by_id.items():
        sig = signal_map.get(tid, "")
        if sig == ThreadSignalType.FAILED.value:
            newly_completed.append(t.model_copy(update={"state": ThreadState.FAILED}))
            mutated = True
        elif t.progress >= _THREAD_COMPLETION_THRESHOLD:
            newly_completed.append(t.model_copy(update={"state": ThreadState.COMPLETE}))
            mutated = True
        else:
            still_active.append(t)

    arc = arc.model_copy(update={
        "active_threads": still_active,
        "completed_threads": arc.completed_threads + newly_completed,
    })

    # Promote latent threads up to cap
    completed_ids = {t.id for t in arc.completed_threads}
    available = [
        t for t in arc.latent_threads
        if t.id not in completed_ids
    ]
    slots = _ACTIVE_THREAD_CAP - len(arc.active_threads)
    to_promote = available[:slots]
    if to_promote:
        promoted = [
            t.model_copy(update={"state": ThreadState.ACTIVE}) for t in to_promote
        ]
        remaining_latent = [
            t for t in arc.latent_threads if t.id not in {p.id for p in to_promote}
        ]
        arc = arc.model_copy(update={
            "active_threads": arc.active_threads + promoted,
            "latent_threads": remaining_latent,
        })
        mutated = True

    return arc if mutated else None
```

**Validation:** After a turn where a thread signal of `advanced` is emitted, assert `state["arc"]["active_threads"][matching_id]["progress"]` incremented by 1.

#### Step 2.3 — Replace tick_arc call in run_turn() with _apply_thread_signals

**File:** `ccya/engine/turn.py`

**What:** Replace the arc director call at lines 653-663 with the new function. The call currently reads:

```python
                # Arc director: process thread signals and update arc state
                if state.get("arc") and progress_result:
                    arc = tick_arc(
                        arc=CampaignArc(**state["arc"]),
                        signals=progress_result.thread_signals,
                        drift=progress_result.player_drift_signals,
                        momentum=(state.get("pc") or {}).get("momentum", 0),
                        turn_no=turn_no,
                        candidate=progress_result.candidate_opportunity,
                    )
                    state["arc"] = arc.model_dump(mode="json")
```

Replace with:
```python
                # Arc director: process thread signals and update arc state
                if state.get("arc") and progress_result:
                    arc_delta = _apply_thread_signals(state, progress_result)
                    if arc_delta is not None:
                        merged_delta = merged_delta.model_copy(
                            update={"arc_update": arc_delta}
                        )
                    # Engagement scoring stays in tick_arc() — it reads drift
                    # from player_drift_signals and updates arc_engagement.
                    # This is kept separate from thread lifecycle management.
                    if state.get("arc"):
                        arc = tick_arc(
                            arc=CampaignArc(**state["arc"]),
                            signals=progress_result.thread_signals,
                            drift=progress_result.player_drift_signals,
                            momentum=(state.get("pc") or {}).get("momentum", 0),
                            turn_no=turn_no,
                        )
                        state["arc"] = arc.model_dump(mode="json")
```

**Why:** Thread lifecycle (signals, completion, promotion) is now handled by `_apply_thread_signals()` which writes to `merged_delta.arc_update`. Engagement scoring stays in `tick_arc()` as a lightweight call that only reads drift and updates `arc_engagement`. The `candidate` parameter is removed from `tick_arc()` here — candidate handling moves to Phase 03.

**Note on merge order:** `_apply_thread_signals` sets `merged_delta.arc_update` with thread changes. Phase 04's narrator arc_update will be merged on top later in the turn. The `_merge_arc_update` function in Phase 01 ensures engine thread changes are not lost when the narrator's arc_update is merged second.

### Tests to write or update
`tests/test_arc.py` (new file) — add `test_thread_progress_increment_on_advanced_signal`, `test_thread_fails_on_failed_signal`, `test_thread_completes_at_threshold`, `test_latent_thread_promoted_when_slot_available`, `test_active_cap_prevents_excess_promotion`

Use `FakeLLM` patterns from `docs/REPOMAP/testing.md`.

### REPOMAP updates required
- `docs/REPOMAP/engine.md` — document `_apply_thread_signals`, inputs, outputs, cap constant; update `tick_arc()` description to note it now handles engagement scoring only
- `docs/REPOMAP/state.md` — note that `apply_delta` now processes `arc_update` from thread signals

### Risks
1. `CampaignArc.model_validate(arc_raw)` fails on saves missing new fields — wrapped in try/except returning None (noop).
2. `_THREAD_COMPLETION_THRESHOLD = 3` may be wrong for short or long packs. Acceptable for MVP1; make configurable post-MVP1.
3. `tick_arc()` is still called after `_apply_thread_signals` for engagement scoring. If engagement scoring is later moved into `_apply_thread_signals`, the `tick_arc()` call can be removed entirely.

---

## Implementation — Phase 03: Latent Thread Hygiene

### Context files to load
1. `ccya/engine/turn.py` — `_apply_thread_signals()` from Phase 02
2. `ccya/models.py` — `ArcThread`, `ThreadState`
3. `ccya/engine/arc.py` — current candidate_opportunity handling at lines 229-244 (for reference, to be replaced)

### Detailed steps

#### Step 3.1 — Write _candidate_to_latent_thread() in turn.py

**File:** `ccya/engine/turn.py`

**What:** A new helper that creates an `ArcThread` from `progress_result.candidate_opportunity` with:
- `urgency="background"` and `tags=["tactical"]`
- Stable id from first 5 words of opportunity string, snake_cased, stripped of punctuation. Append `_t{turn_no}` if collision detected.
- Cap `latent_threads` at `_LATENT_CAP` (4): if at cap, evict the oldest `tactical`-tagged latent thread first (by `last_offered_turn` ascending, then list order). If no tactical threads to evict and still at cap, do not add.

**Why:** The live save has 11 latent threads because every turn's `candidate_opportunity` appended unconditionally (current `tick_arc()` line 244). A cap of 4 with tactical-first eviction keeps the arc pool meaningful and bounded. Pack-seeded (non-tactical) threads are never evicted.

**Code Snippet**
```python
_LATENT_CAP = 4
"""Maximum number of threads in the latent state."""

_TACTICAL_TAG = "tactical"
"""Tag applied to engine-generated latent threads from candidate_opportunity."""


def _candidate_to_latent_thread(
    arc: CampaignArc,
    candidate: str,
    turn_no: int,
) -> CampaignArc | None:
    """Convert a candidate_opportunity string into a latent thread with cap enforcement."""
    if not candidate or not candidate.strip():
        return None

    words = candidate.strip().split()[:5]
    base_id = "_".join(
        w.lower().strip(".,;:!?\"'") for w in words
    )
    existing_ids = {
        t.id for t in arc.active_threads + arc.latent_threads + arc.completed_threads
    }
    tid = base_id if base_id not in existing_ids else f"{base_id}_t{turn_no}"
    if tid in existing_ids:
        return None  # genuine collision after suffix

    new_thread = ArcThread(
        id=tid,
        summary=candidate.strip(),
        state=ThreadState.LATENT,
        urgency="background",
        tags=[_TACTICAL_TAG],
        last_offered_turn=turn_no,
    )

    latent = list(arc.latent_threads)
    if len(latent) >= _LATENT_CAP:
        # Evict oldest tactical thread; if none, do not add
        tactical = [
            (i, t) for i, t in enumerate(latent)
            if _TACTICAL_TAG in (t.tags or [])
        ]
        if not tactical:
            return None
        tactical.sort(key=lambda x: (x[1].last_offered_turn or 0))
        evict_idx = tactical[0][0]
        latent.pop(evict_idx)

    return arc.model_copy(update={"latent_threads": latent + [new_thread]})
```

#### Step 3.2 — Call _candidate_to_latent_thread in run_turn()

**File:** `ccya/engine/turn.py`

**What:** After the `_apply_thread_signals` call (Step 2.3), if `progress_result.candidate_opportunity` is non-empty:

```python
                    # Handle candidate_opportunity as latent thread
                    if progress_result.candidate_opportunity:
                        arc_raw = state.get("arc")
                        if arc_raw:
                            try:
                                arc = CampaignArc.model_validate(arc_raw)
                                updated_arc = _candidate_to_latent_thread(
                                    arc,
                                    progress_result.candidate_opportunity,
                                    turn_no,
                                )
                                if updated_arc is not None:
                                    # Merge into merged_delta.arc_update
                                    # _merge_arc_update handles field-level merging
                                    # so engine thread changes from _apply_thread_signals
                                    # are preserved when this is merged.
                                    merged_delta = merged_delta.model_copy(
                                        update={"arc_update": updated_arc}
                                    )
                            except Exception:
                                _log.warning(
                                    "candidate_opportunity: failed to validate arc",
                                    extra={"turn": turn_no, "trace_id": trace_id},
                                )
```

**Validation:** Run 10 turns with mocked `candidate_opportunity`; assert `len(state["arc"]["latent_threads"]) <= 4` after each turn. Assert pack-seeded (non-tactical) latent threads are never evicted.

### Tests to write or update
`tests/test_arc.py` — add `test_candidate_becomes_latent_thread`, `test_candidate_dedup_by_id`, `test_latent_cap_evicts_tactical_first`, `test_latent_cap_never_evicts_non_tactical`

### REPOMAP updates required
- `docs/REPOMAP/engine.md` — document `_candidate_to_latent_thread`, latent cap, tactical tag

### Risks
1. Pack-seeded latent threads that never get a `tactical` tag are protected from eviction even when the pool is full. This is the correct behavior — document it in REPOMAP.
2. Id collision after `_t{turn_no}` suffix is theoretically possible on same-turn duplicate candidates. The guard `if tid in existing_ids: return None` handles it silently.

---

## Implementation — Phase 04: Narrator arc_update Emission

### Context files to load
1. `ccya/engine/narrate.py` — `_narrate_messages()`, `current_arc_ctx` construction at lines 72-89
2. `ccya/prompts/sections/_arc.j2` — current arc template for narrator user prompt
3. `ccya/prompts/narrate_system.j2` — current narrator system prompt
4. `ccya/engine/turn.py` — narration consumption at line 671 (`_strip_fallback`)

### Detailed steps

#### Step 4.1 — Pass hidden_truths to narrator context

**File:** `ccya/engine/narrate.py`

**What:** Add `hidden_truths` to `current_arc_ctx` (lines 74-87) so the narrator can recognize when a hidden truth has been revealed. Add an explicit instruction in the system prompt that hidden_truths must never appear in narration prose.

**Why:** The narrator needs to know what secrets exist to flag a reveal in the `<<<ARC_UPDATE_START>>>` JSON block. Without seeing `hidden_truths`, it cannot know which truths to surface.

**Code Snippet**

Change `current_arc_ctx` construction at lines 74-87 from:
```python
        current_arc_ctx = {
            "visible_goal": arc.get("visible_goal", ""),
            "thematic_question": arc.get("thematic_question", ""),
            "phase": arc.get("phase", "setup"),
            "active_threads": [
                {
                    "summary": t.get("summary", ""),
                    "urgency": t.get("urgency", "normal"),
                    "tags": t.get("tags", []),
                }
                for t in (arc.get("active_threads") or [])
            ],
            "pc_drive": arc.get("pc_drive", ""),
        }
```
to:
```python
        current_arc_ctx = {
            "visible_goal": arc.get("visible_goal", ""),
            "thematic_question": arc.get("thematic_question", ""),
            "phase": arc.get("phase", "setup"),
            "active_threads": [
                {
                    "summary": t.get("summary", ""),
                    "urgency": t.get("urgency", "normal"),
                    "tags": t.get("tags", []),
                }
                for t in (arc.get("active_threads") or [])
            ],
            "pc_drive": arc.get("pc_drive", ""),
            "hidden_truths": arc.get("hidden_truths") or [],
        }
```

**Validation:** Render `narrate_user.j2` with a fixture state containing `hidden_truths`; assert the rendered system prompt includes the hidden truths block.

#### Step 4.2 — Expand _arc.j2 with pc_drive, thematic_question, discovered_truths

**File:** `ccya/prompts/sections/_arc.j2`

**What:** Replace the current 13-line template with an expanded version that shows `thematic_question`, `pc_drive`, `discovered_truths`, and per-thread progress.

**Why:** `pc_drive` and `thematic_question` are already passed to `narrate_system.j2` via `current_arc_ctx` but `_arc.j2` reads `state.arc` directly. This makes the user-side context consistent. `discovered_truths` must show here so the narrator treats already-revealed truths as known facts — but `hidden_truths` must never appear in narration prose.

**Code Snippet**
```jinja2
{% if state.arc and state.arc.get('visible_goal') -%}
### Campaign Arc
**Goal:** {{ state.arc.get('visible_goal', '') }}
**Phase:** {{ state.arc.get('phase', 'setup') }}
**Thematic question:** {{ state.arc.get('thematic_question', '') }}
{% if state.arc.get('pc_drive') -%}
**PC drive:** {{ state.arc.get('pc_drive', '') }}
{% endif -%}
{% if state.arc.get('active_threads') -%}
**Active threads:**
{% for t in state.arc.get('active_threads') -%}
- [{{ t.get('urgency', 'normal') | upper }}] {{ t.get('summary', '') }}{% if t.get('progress', 0) > 0 %} (progress: {{ t.get('progress') }}/3){% endif %}
{% endfor -%}
{% endif -%}
{% if state.arc.get('discovered_truths') -%}
**Revealed truths:**
{% for truth in state.arc.get('discovered_truths') -%}
- {{ truth }}
{% endfor -%}
{% endif -%}
{%- else -%}
No active campaign arc.
{% endif -%}
```

**Validation:** Render `narrate_user.j2` with a fixture state containing `discovered_truths` and `hidden_truths`; assert rendered output contains the former and does not contain the latter in the `_arc.j2` section.

#### Step 4.3 — Add arc_update emission instruction to narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add a new section after the Campaign Arc section (after line 87, before "## Markdown") instructing the narrator to emit a JSON block after narration when arc-level changes occur.

**Why:** This gives the narrator a write path for arc-level changes (phase, discovered truths, goal) without delegating thread promotion to it. The output stripping in Step 4.4 ensures the block never reaches the player UI.

**Code Snippet**

Insert after line 87 (after `{% endif %}` for the Campaign Arc section, before `## Markdown`):
```

## ARC UPDATE (optional, after narration)

If this turn's narration has materially advanced, shifted, or revealed something about the campaign arc, append a JSON block AFTER your narration using this exact format:

<<<ARC_UPDATE_START>>>
{"discovered_truths": ["exact text of revealed hidden truth"], "phase": "pursuit", "visible_goal": "updated goal if changed"}
<<<ARC_UPDATE_END>>>

Rules:
- Only emit this block if something genuinely changed. Omit entirely if the arc is unchanged.
- `discovered_truths`: only include if you narrated information this turn that explicitly surfaces a hidden truth. Copy the exact text from the hidden_truths list shown in your arc context above. Do not infer or paraphrase.
- `phase`: only include if the arc phase has visibly shifted this turn (e.g. the inciting incident has concluded and pursuit has begun).
- `visible_goal`: only include if the stated goal has materially changed.
- Do NOT include `active_threads`, `latent_threads`, `completed_threads`, or `hidden_truths` — thread management and hidden secrets are handled by the engine.
- The block must be valid JSON. The narration text before the block is what the player sees.
- Emit the block at the very end of your response, after all narration prose.

### IMPORTANT: Hidden truths are for internal reasoning only
The hidden_truths list above contains story secrets. You must NEVER reveal them in your narration prose. If a hidden truth has been surfaced through player actions, indicate it through atmosphere, NPC behavior, or environmental detail — but never state the secret directly. Surface the truth to the player only through the ARC UPDATE JSON block when the narration has genuinely revealed it.
```

**Validation:** The system prompt now contains the arc_update emission instructions. The hidden_truths non-reveal instruction is explicit.

#### Step 4.4 — Strip <<<ARC_UPDATE_START>>> blocks from narrator output in turn.py

**File:** `ccya/engine/turn.py`

**What:** After receiving the raw narrator response string, before storing or returning it as player-visible text, extract and parse any `<<<ARC_UPDATE_START>>>` block.

**Why:** This is the exact pattern needed to prevent the old `active_scope` failure mode where structured output after narration leaked into the player-visible UI. The sentinel strings `<<<ARC_UPDATE_START>>>` / `<<<ARC_UPDATE_END>>>` follow the same precedent as `<<<TRACE_IMMUTABLE_START>>>` / `<<<TRACE_IMMUTABLE_END>>>` used in `extract_progress_user.j2`.

**Code Snippet**

Add imports at the top of the file (after `import logging`):
```python
import json as _json
```

Add the helper function after `_strip_fallback` (after line 821):
```python
_ARC_UPDATE_RE = re.compile(
    r"<<<ARC_UPDATE_START>>>\s*(.*?)\s*<<<ARC_UPDATE_END>>>",
    re.DOTALL,
)


def _extract_narrator_arc_update(raw: str) -> tuple[str, dict[str, Any] | None]:
    """Strip arc_update block from narrator output.

    Returns (clean_text, arc_dict|None). If no block found, returns (raw, None).
    If block found but JSON is malformed, returns (clean_text, None).
    """
    match = _ARC_UPDATE_RE.search(raw)
    if not match:
        return raw, None
    clean = _ARC_UPDATE_RE.sub("", raw).rstrip()
    try:
        arc_dict = _json.loads(match.group(1))
    except Exception:
        arc_dict = None  # malformed JSON — discard silently, log at WARNING
    return clean, arc_dict
```

Call site: after line 671 where `_strip_fallback` is called, add:
```python
        narrative = _strip_fallback(narrative, trace_id=trace_id, turn=turn_no)

        # Extract narrator arc_update block if present
        narrative, narrator_arc_dict = _extract_narrator_arc_update(narrative)
        if narrator_arc_dict:
            try:
                narrator_arc_update = CampaignArc.model_validate(narrator_arc_dict)
                # Merge into merged_delta.arc_update on top of engine changes
                # _merge_arc_update handles field-level merging:
                # - engine owns thread state (active/latent/completed)
                # - narrator owns phase, visible_goal, discovered_truths
                # Since narrator merge happens second, it wins on narrative fields.
                if delta is not None:
                    _merge_arc_update(
                        state.setdefault("arc", {}), narrator_arc_update
                    )
                    # Also update merged_delta so save_state persists it
                    merged_delta = merged_delta.model_copy(
                        update={"arc_update": narrator_arc_update}
                    )
            except Exception:
                _log.warning(
                    "narrator emitted invalid arc_update JSON — discarded",
                    extra={"turn": turn_no, "trace_id": trace_id},
                )
```

**Why:** The narration text is cleaned (block removed) before being stored in chronicle.md and returned to the player. The parsed `narrator_arc_dict` is merged into state via `_merge_arc_update` (Phase 01), which preserves engine thread changes while allowing narrator narrative changes to take effect.

**Validation:**
1. Unit test `_extract_narrator_arc_update` with: (a) clean narration, no block → returns unchanged; (b) narration + valid block → returns clean text + parsed dict; (c) narration + malformed JSON block → returns clean text + None.
2. Integration test: verify that `state["arc"]["discovered_truths"]` is populated after a turn where FakeLLM emits a narrator response containing an `<<<ARC_UPDATE_START>>>` block.
3. Assert that the block text does NOT appear in the stored narration event.

### Tests to write or update
`tests/test_arc.py` — add `test_extract_narrator_arc_update_clean`, `test_extract_narrator_arc_update_valid_block`, `test_extract_narrator_arc_update_malformed_json`, `test_narrator_arc_update_merged_into_state`

### REPOMAP updates required
- `docs/REPOMAP/engine.md` — document `_extract_narrator_arc_update`, sentinel strings, merge order
- `docs/REPOMAP/prompts.md` — document `<<<ARC_UPDATE_START>>>` block format in `narrate_system.j2`; note `hidden_truths` in `current_arc_ctx`

### Risks
1. Narrator emits the block mid-narration rather than at the end. Mitigation: `_ARC_UPDATE_RE.sub("", raw).rstrip()` removes it regardless of position; prompt instruction says to emit at the very end.
2. Narrator includes `hidden_truths` in the emitted JSON. Mitigation: `CampaignArc.model_validate` accepts it, but `_merge_arc_update` only overwrites `hidden_truths` when non-empty — and the prompt explicitly forbids it. Risk is low.
3. Sentinel strings appear in player narration in a non-arc context (e.g. player input quotes them). Mitigation: regex is DOTALL with minimal matching; real risk is near-zero. If it becomes an issue, use a UUID-based sentinel post-MVP1.
4. Merge order: engine thread signals (Phase 02) run before narrator arc_update is parsed. Both may mutate `arc_update` in `merged_delta`. Resolved by: Phase 02 sets `merged_delta.arc_update` from thread signals; Phase 04 narrator output is parsed AFTER narration, then merged on top using `_merge_arc_update` as a second pass. Engine thread changes are preserved because `_merge_arc_update` only overwrites fields present in the incoming object.

---

## Ambiguities requiring resolution before execution

1. **Merge order — engine vs narrator authority:** Engine thread signals run first and set `merged_delta.arc_update` with thread state changes. Narrator arc_update is parsed after narration and merged on top. The `_merge_arc_update` function handles field-level merging: engine thread changes (active/latent/completed threads) are preserved because the narrator's JSON block explicitly omits thread fields. Narrator wins on `phase`, `visible_goal`, `discovered_truths`. This is the correct split — engine is authoritative on thread state, narrator on narrative state.

2. **Hidden truths in narrator context:** Resolved — `hidden_truths` are passed to `narrate_system.j2` via `current_arc_ctx` with an explicit instruction that they must never appear in narration prose. The narrator recognizes revealed truths by comparing narration content against the hidden_truths list, then emits them via the `<<<ARC_UPDATE_START>>>` JSON block only.

3. **Latent cap value of 4:** The live save has 2 pack-seeded latent threads that matter plus 9 tactical ones. A cap of 4 allows 2 meaningful pack threads + 2 tactical slots. If a pack generates more than 2 latent threads at seed time, raise to 6. For MVP1, 4 is the default; make configurable post-MVP1 if needed.

4. **tick_arc() retention:** `tick_arc()` is retained for engagement scoring only (reads `player_drift_signals`, updates `arc_engagement`). The thread lifecycle logic has been extracted to `_apply_thread_signals()` and `_candidate_to_latent_thread()`. If engagement scoring is later restructured (e.g., with a `DriftAnalysis` model), `tick_arc()` can be removed entirely.

---

## Execution order

Phase 01 → Phase 02 → Phase 03 → Phase 04

Each phase is independently testable. Phase 01 must complete before 02-03 (they write to `arc_update`). Phase 04 can be developed in parallel but must be the last to execute (it depends on the merge infrastructure from 01).
