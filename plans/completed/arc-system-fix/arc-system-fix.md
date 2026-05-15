# Arc System Fix

## Status
`completed`

## Phases

4 phases: fix thread signal extraction, restructure drift analysis, fix state merge duplicates, fix immediate pressure expiry.

## Objective

The arc system is completely non-functional: thread signals fire 0/10 turns, arc engagement stuck at -3, duplicate threads corrupt state, and immediate scene pressures never expire. Root causes: (1) thread tags not passed to progress prompt so LLM cannot match narration to threads, (2) `_merge_arc_update` uses `_upsert_threads` which doesn't remove threads moved between active/completed/latent lists, (3) threat imperative directives only fire for building/background urgency, never immediate.

## Non-goals

- Raise active thread cap (deferred to separate plan)
- Latent thread dedup (deferred)
- Progress tracking consistency (deferred)
- Restructure the three-stream extraction pipeline

## Firm decisions

1. Thread tags are the matching substrate — progress prompt must show tags so LLM compares narration keywords to tags, not summaries.
2. Drift signals become structured `drift_analysis` with `match: bool`, `reason: str`, `new_interest: str` per thread. Keep `player_drift_signals` as legacy fallback during transition.
3. `_merge_arc_update` must do set-replace (not upsert) for active/completed/latent threads. The `_upsert_threads` helper is only needed for compactor NPC merges.
4. Immediate pressures get a "Resolve a Threat" directive after 3 turns, same as building/background at 4/5.
5. `_compute_threat_ages` already returns urgency — the imperative logic in `narrate_user.j2` just needs to include immediate urgency.

## Conflicts and overlap

- `plans/arc-system-improvements.md` (open) — covers phases 1 and 2 (thread tags + drift analysis) with identical intent. This plan supersedes it. Move to `plans/completed/` after execution.
- No file overlap on phases 3 and 4.

---

## Implementation — Phase 1: Inject thread tags into progress prompt

### Context files to load
- `ccya/engine/extraction.py` — `_extract_progress_messages()`
- `ccya/prompts/extract_progress_user.j2` — active_threads block
- `ccya/prompts/extract_progress_system.j2` — thread_signals field rules

### Detailed steps

#### Step 1.1 — Pass thread tags in `_extract_progress_messages()`

**File:** `ccya/engine/extraction.py`

**What:** Add `tags` field to each active thread dict passed to the progress prompt.

**Why:** The LLM has no way to match narration keywords to threads without tags. Tags are the semantic substrate for signal detection.

**Code Snippet**
```python
# In _extract_progress_messages(), line ~443-446:
active_threads = [
    {"id": t["id"], "summary": t["summary"], "urgency": t.get("urgency", "normal"), "tags": t.get("tags", [])}
    for t in ((state.get("arc") or {}).get("active_threads") or [])
]
```

**Validation:** Run a turn and check that `extract.progress.rendered_user` contains thread entries with tags.

### Tests to write or update

**File:** `tests/test_extraction.py`

Add test: `test_progress_messages_includes_thread_tags` — verify `_extract_progress_messages()` context dict contains `tags` key in each active thread entry.

### REPOMAP updates required

- `docs/REPOMAP/engine.md` — update `_extract_progress_messages` description to note tags in active_threads
- `docs/REPOMAP/prompts.md` — note tags in active_threads block

### Risks

- None significant. Pure context addition, no behavior change.

---

## Implementation — Phase 2: Restructure drift signals into DriftAnalysis

### Context files to load
- `ccya/models.py` — `ProgressExtractResult`, `ThreadSignal`, `ThreadSignalType`
- `ccya/prompts/extract_progress_system.j2` — field rules for thread_signals and player_drift_signals
- `ccya/prompts/extract_progress_user.j2` — active_threads block (add tags section)
- `ccya/engine/arc.py` — `tick_arc()`

### Detailed steps

#### Step 2.1 — Add `DriftAnalysis` model to models.py

**File:** `ccya/models.py`

**What:** Add a new Pydantic model for structured drift analysis per thread.

**Why:** Freeform `player_drift_signals` phrases are unreliable for engagement scoring. Structured match/no-match with reason is deterministic and scorable.

**Code Snippet**
```python
class DriftAnalysis(BaseModel):
    """Structured drift analysis for a single thread."""
    thread_id: str
    match: bool = False
    """Whether the player's action meaningfully engaged this thread."""
    reason: str = ""
    """One-sentence explanation of why this thread was or wasn't matched."""
    new_interest: str = ""
    """If match is False, what new direction the player seems interested in."""


class ProgressExtractResult(BaseModel):
    # ... existing fields ...
    drift_analysis: list[DriftAnalysis] = Field(default_factory=list)
    """Structured drift analysis per active thread. Supersedes player_drift_signals."""
```

**Validation:** `make check` passes mypy for the new model.

#### Step 2.2 — Update progress system prompt for structured drift

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Replace freeform `player_drift_signals` guidance with structured `drift_analysis` instructions. Keep `player_drift_signals` in output schema for backward compat but mark as deprecated.

**Why:** The LLM needs explicit per-thread match/no-match instructions with tags as the matching substrate.

**Code Snippet**
```
# In the output schema, add after thread_signals:
  "drift_analysis": [],
  "player_drift_signals": [],  # DEPRECATED: use drift_analysis

# Replace the player_drift_signals field rules section with:
`drift_analysis`: For EACH active thread, emit a DriftAnalysis entry:
  - `match`: true if the player's action meaningfully engaged this thread (advanced, blocked, or directly affected it)
  - `reason`: one-sentence explanation. E.g. "Player attacked pirates near mainmast, directly advancing boarding_chaos"
  - `new_interest`: if match is false, what new direction the player seems interested in. Empty if match is true.

Match against thread tags, not summaries. If narration contains keywords from a thread's tags, set match=true.
Emit one entry per active thread. Do not emit entries for latent/completed threads.

`player_drift_signals`: DEPRECATED — kept for backward compatibility. Use drift_analysis instead.
```

**Validation:** Check rendered prompt includes drift_analysis instructions.

#### Step 2.3 — Update tick_arc to consume drift_analysis

**File:** `ccya/engine/arc.py`

**What:** Modify `tick_arc()` to accept and process `drift_analysis` with fallback to legacy `player_drift_signals`.

**Why:** During transition, some turns may produce drift_analysis, others may only produce player_drift_signals.

**Code Snippet**
```python
def tick_arc(
    arc: CampaignArc,
    drift: list[str] | None = None,
    drift_analysis: list[Any] | None = None,
) -> CampaignArc:
    """Score arc engagement based on drift overlap with active thread tags.

    Thread lifecycle is handled by _apply_thread_signals / _candidate_to_latent_thread
    in engine/turn.py. This function only updates arc_engagement.
    """
    engagement_tags: set[str] = set()
    for t in arc.active_threads:
        engagement_tags.update(t.tags or [])

    # Prefer structured drift_analysis, fall back to legacy player_drift_signals
    if drift_analysis:
        has_overlap = any(da.match for da in drift_analysis)
    elif drift:
        has_overlap = False
        for d in drift:
            d_lower = d.lower()
            for tag in engagement_tags:
                if tag in d_lower:
                    has_overlap = True
                    break
            if has_overlap:
                break
    else:
        return arc

    if has_overlap:
        arc.arc_engagement = min(arc.arc_engagement + 1, 3)
    else:
        arc.arc_engagement = max(arc.arc_engagement - 1, -3)

    return arc
```

**Validation:** Existing `TestEngagement` tests still pass. New tests for drift_analysis match/no-match.

#### Step 2.4 — Update turn.py to pass drift_analysis to tick_arc

**File:** `ccya/engine/turn.py`

**What:** Pass `progress_result.drift_analysis` to `tick_arc()` alongside legacy `player_drift_signals`.

**Why:** The structured data needs to flow from extraction to arc scoring.

**Code Snippet**
```python
# In run_turn(), around line 802-806:
                    if state.get("arc"):
                        arc = tick_arc(
                            arc=CampaignArc(**state["arc"]),
                            drift=progress_result.player_drift_signals,
                            drift_analysis=progress_result.drift_analysis,
                        )
                        state["arc"] = arc.model_dump(mode="json")
```

Same change in `run_turn_retry()`.

**Validation:** Run a turn, check that drift_analysis flows through to engagement scoring.

### Tests to write or update

**File:** `tests/test_arc.py`

Add to `TestEngagement`:
- `test_drift_analysis_match_increments_engagement` — drift_analysis with match=true increments engagement
- `test_drift_analysis_no_match_decrements_engagement` — drift_analysis with match=false decrements engagement
- `test_drift_analysis_fallback_to_legacy_drift` — empty drift_analysis with legacy drift still works
- `test_drift_analysis_takes_precedence_over_legacy` — both present, drift_analysis used

**File:** `tests/test_extraction.py`

Add test: `test_progress_result_includes_drift_analysis` — verify ProgressExtractResult model accepts drift_analysis field.

### REPOMAP updates required

- `docs/REPOMAP/models.md` — add DriftAnalysis model, note drift_analysis field on ProgressExtractResult
- `docs/REPOMAP/engine.md` — note tick_arc accepts drift_analysis parameter
- `docs/REPOMAP/prompts.md` — note drift_analysis field rules

### Risks

- Backward compat: existing saved state has no drift_analysis field. Pydantic default_factory handles this.
- LLM may not produce valid drift_analysis initially. Fallback to player_drift_signals ensures engagement still scores.

---

## Implementation — Phase 3: Fix state merge duplicates

### Context files to load
- `ccya/state/delta.py` — `_merge_arc_update()`, `_upsert_threads()`
- `ccya/engine/turn.py` — `_apply_thread_signals()`
- `tests/test_arc.py` — existing thread lifecycle tests

### Detailed steps

#### Step 3.1 — Replace upsert with set-replace for thread lists in `_merge_arc_update`

**File:** `ccya/state/delta.py`

**What:** Change `_merge_arc_update` to do set-replace (not upsert) for active_threads, latent_threads, and completed_threads. When an arc_update provides a thread list, it replaces the entire list for that category — not merging by ID.

**Why:** `_apply_thread_signals` returns a complete arc where threads have been moved between lists (active→completed, active→latent). The `_upsert_threads` helper only updates by ID, so threads that were removed from active_threads in the update remain in state's active_threads, creating duplicates.

**Code Snippet**
```python
# In _merge_arc_update(), replace lines 57-64:
    if au.active_threads is not None:
        arc["active_threads"] = [
            t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
            for t in au.active_threads
        ]
    if au.latent_threads is not None:
        arc["latent_threads"] = [
            t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
            for t in au.latent_threads
        ]
    if au.completed_threads is not None:
        arc["completed_threads"] = [
            t.model_dump(exclude_none=True) if hasattr(t, "model_dump") else dict(t)
            for t in au.completed_threads
        ]
```

**Why:** `_apply_thread_signals` returns a complete arc with the correct final state for each thread list. Set-replace preserves this. The `_upsert_threads` helper is only needed for compactor NPC merges (line 100+), not for arc thread lists.

**Validation:** Run 10 turns, verify no thread appears in both active_threads and completed_threads, or active_threads and latent_threads.

### Tests to write or update

**File:** `tests/test_arc.py`

Add to `TestThreadAdvancement`:
- `test_completed_thread_not_in_active_after_completion` — after 3 ADVANCED signals, thread is only in completed_threads, not active_threads
- `test_promoted_thread_not_in_latent_after_promotion` — after latent promoted to active, thread is only in active_threads, not latent_threads

**File:** `tests/test_delta.py` (if exists) or add to `tests/test_arc.py`:
- `test_merge_arc_update_replaces_active_threads` — verify set-replace behavior

### REPOMAP updates required

- `docs/REPOMAP/state.md` — update `_merge_arc_update` description to note set-replace for thread lists

### Risks

- `_upsert_threads` is also used for compactor NPC merges. Verify those still work (they use a different code path, not arc_update).
- If any other caller of `_merge_arc_update` expects upsert behavior, it will break. Check all callers: lines 792, 826, 853, 1527, 1560, 1587 in turn.py — all pass full CampaignArc from `_apply_thread_signals` or `_candidate_to_latent_thread`, which return complete state. Set-replace is correct for all callers.

---

## Implementation — Phase 4: Fix immediate pressure expiry

### Context files to load
- `ccya/prompts/narrate_user.j2` — threat imperative directive blocks (lines 138-151)
- `ccya/engine/config.py` — `threat_imperative_at`, `building_threat_imperative_at`

### Detailed steps

#### Step 4.1 — Fire "Resolve a Threat" for immediate pressures past threshold

**File:** `ccya/prompts/narrate_user.j2`

**What:** Add immediate urgency pressures to the "Resolve a Threat" directive. Immediate pressures that have been active 3+ turns should also trigger resolution.

**Why:** Current code only fires "Resolve a Threat" for building (4+ turns) and background (5+ turns) urgency. Immediate pressures with `max_turns: null` accumulate forever.

**Code Snippet**
```jinja2
{% if threat_ages %}
{% set old_building = threat_ages | selectattr("urgency", "equalto", "building") | selectattr("age", "ge", building_threat_imperative_at) | list %}
{% set old_background = threat_ages | selectattr("urgency", "equalto", "background") | selectattr("age", "ge", threat_imperative_at) | list %}
{% set old_immediate = threat_ages | selectattr("urgency", "equalto", "immediate") | selectattr("age", "ge", 3) | list %}
{% set background_pressure = threat_ages | selectattr("urgency", "equalto", "background") | selectattr("age", "ge", threat_pressure_at) | selectattr("age", "lt", threat_imperative_at) | list %}
{% if old_building or old_background or old_immediate %}

**Narration Directive:** Resolve a Threat
Resolve the oldest threat listed above. It has been active too long. Weave its resolution naturally into the narration — the threat is dealt with, neutralized, or escapes. Do NOT introduce a new threat in this narration.
{% elif background_pressure %}

**Narration Directive:** Threat Pressure
A background threat has been lingering. Acknowledge it in the scene — show its presence affecting the environment or NPCs. No need to resolve it yet, but don't ignore it.
{% endif %}
{% endif %}
```

**Validation:** Run a turn with an immediate pressure older than 3 turns. Check that narration includes "Resolve a Threat" directive. Verify the extractor removes the resolved pressure.

### Tests to write or update

No new tests needed — this is a prompt template change. Verify manually with a save that has old immediate pressures.

### REPOMAP updates required

- `docs/REPOMAP/prompts.md` — note immediate pressures now trigger "Resolve a Threat" at 3 turns

### Risks

- Immediate pressures are meant to be urgent and short-lived. A 3-turn threshold means pressures added at T4 will trigger resolution at T7. This is reasonable — if an immediate threat persists 3 turns without being addressed, it should resolve.

---

## Ambiguities requiring resolution before execution

1. **DriftAnalysis model field naming:** Should `new_interest` be per-thread or a separate top-level field? Current design: per-thread (empty if match=true). This avoids duplicate "new interest" phrases.
2. **Immediate pressure threshold:** 3 turns chosen arbitrarily. Could be 4 to match building urgency. 3 is more aggressive — immediate threats should resolve faster.
3. **Backward compat for drift_analysis:** Should we add a migration in `_apply_sanitization` or similar to convert existing state's `player_drift_signals` to `drift_analysis`? No — Pydantic default_factory handles missing field, and tick_arc falls back to legacy drift.
