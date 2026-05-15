# Arc System Improvements: Thread Signals + Drift Structuring

## Status
`open`

## Objective
Fix the two root causes of arc system starvation: (1) thread signals not firing reliably because the progress extractor lacks enough context to match narration to threads, and (2) drift signals being sparse and freeform, making engagement scoring unreliable. Inject thread tags into the progress prompt so the LLM can actually determine which threads were touched, and restructure drift signals to be a deterministic comparison between player intent and active thread themes.

## Non-goals
- Thread dedup/cleanup (latent threads with near-duplicate summaries)
- Progress tracking consistency (BLOCKED signal vs state value mismatch)
- UI changes to arc display
- Active thread cap changes (deferred to a separate plan)

## Firm decisions
1. Thread tags are injected into the progress extractor user prompt alongside id/summary/urgency. Tags are the matching substrate — the extractor compares narration keywords to tags, not summaries.
2. Drift signals become a structured comparison: `drift_match: bool` (does intent align with any active thread tag?) + `drift_reason: str | null` (one short phrase explaining why). This replaces the freeform `player_drift_signals` list.
3. The active thread cap stays at 2-3 for now. Raising it is a separate change.
4. `ProgressExtractResult` gains a `drift_analysis` field and keeps `player_drift_signals` for backward compatibility during the transition. The arc director reads `drift_analysis` first, falls back to `player_drift_signals`.
5. The `_salience_score` function in `arc.py` is updated to consume the new structured drift format.

## Conflicts and overlap
- `quest-story-arc-revamp.md` is the parent plan that introduced the arc system. This plan refines its extraction and engagement mechanics. No file overlap beyond `arc.py`, `extraction.py`, `extract_progress_system.j2`, `extract_progress_user.j2`, `models.py`.
- `arc-system-mechanics.md` is a reference doc — no conflict.
- `replace-quest-ui-with-arc-ui.md` is frontend-only — no conflict.

## Implementation — Phase 1: Inject thread tags into progress prompt

### Context files to load
1. `ccya/engine/extraction.py` — `_extract_progress_messages()`
2. `ccya/prompts/extract_progress_user.j2` — active_threads block
3. `ccya/prompts/extract_progress_system.j2` — thread_signals field rules

### Detailed steps

#### Step 1.1 — Pass thread tags in extraction context

**File:** `ccya/engine/extraction.py`

**What:** In `_extract_progress_messages()`, change the `active_threads` list to include `tags`:

```python
active_threads = [
    {
        "id": t["id"],
        "summary": t["summary"],
        "urgency": t.get("urgency", "normal"),
        "tags": t.get("tags", []),
    }
    for t in ((state.get("arc") or {}).get("active_threads") or [])
]
```

**Why:** Tags are the matching substrate. The extractor needs to know that `the_extraction_route` has tags `["navigation", "danger"]` to recognize that "FEDRA checkpoint" narration is relevant to it.

**Validation:** The rendered `active_threads` block in the user prompt will now show tags for each thread.

#### Step 1.2 — Update progress user prompt to show tags

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Update the `active_threads` block (lines 25-29) to show tags:

```jinja
{% if active_threads -%}
## active_threads (match narration against these tags to determine signals)
{% for t in active_threads %}- `{{ t.id }}` [{{ t.urgency | upper }}] tags: [{{ t.tags | join(", ") if t.tags else "none" }}] {{ t.summary | truncate(120) }}
{% endfor %}
{% endif -%}
```

**Why:** The extractor needs to see tags explicitly in the prompt. The instruction text "match narration against these tags" guides the LLM to use tags as the matching substrate.

**Validation:** Rendered prompt shows something like:
```
## active_threads (match narration against these tags to determine signals)
- `the_extraction_route` [NORMAL] tags: [navigation, danger] The path through the overgrown ruins of West Brandonfurt is becoming increasingly unstable due to ...
- `marlene_s_secret` [NORMAL] tags: [political, trust] Marlene's instructions for the girl's safety may contradict her actual tactical objectives.
```

#### Step 1.3 — Strengthen thread_signals guidance in system prompt

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Replace the thread_signals field rules (lines 25-33) with more explicit matching guidance:

```
`thread_signals`: For each active thread that was **meaningfully touched** this turn, emit a signal. A thread is "meaningfully touched" when the narration contains keywords, entities, or situations that match the thread's **tags** or **summary**.

Matching process:
1. Read the narration and identify key entities, actions, and situations.
2. Compare them against each thread's tags and summary.
3. If there's a clear connection (e.g., narration mentions "FEDRA" and a thread has tag "danger"), emit a signal.
4. If the connection is tenuous or the thread was only background atmosphere, do NOT emit a signal.

Signal values:
- "advanced": the narrative clearly moved this thread forward — a lead was followed, a relevant person was encountered, meaningful information was gained
- "blocked": an obstacle arose that explicitly impedes this thread
- "failed": the thread was definitively closed with a negative outcome
- "ignored": the player's action had nothing to do with this thread

RULES:
- Emit signals for ALL threads that had any meaningful connection to this turn.
- If a thread was present but not affected, emit "ignored" (not omit it).
- If a thread had zero connection to the narration, omit it entirely.
- Emit at most one signal per thread per turn.
```

**Why:** The current guidance is too vague. The extractor needs a concrete matching process. The key change is: "emit 'ignored' for threads present but not affected" — this ensures the arc director gets a complete picture every turn, not just when something changes.

**Validation:** The system prompt now has explicit matching instructions. The extractor should produce signals more consistently.

### Tests to write or update
- `tests/test_arc.py`: Add test `test_tick_arc_with_signals` that verifies thread progress increments on ADVANCED signals and resets on BLOCKED.
- `tests/test_extraction.py`: Add test verifying that `_extract_progress_messages` includes thread tags in the `active_threads` context.

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: Update `_extract_progress_messages` description to note `tags` field in `active_threads`.
- `docs/REPOMAP/prompts.md`: Update `extract_progress_system.j2` / `extract_progress_user.j2` descriptions to note thread tag injection.

### Risks
1. **Prompt size increase**: Adding tags to each thread adds ~20-30 chars per thread. With 2-3 active threads, this is negligible (~60-90 chars).
2. **Over-emission of "ignored" signals**: If the extractor emits "ignored" for every active thread every turn, the arc director gets noise. Mitigation: the arc director already handles IGNORED signals correctly (tracks ignored streaks for expiry).

## Implementation — Phase 2: Restructure drift signals

### Context files to load
1. `ccya/models.py` — `ProgressExtractResult`
2. `ccya/prompts/extract_progress_system.j2` — player_drift_signals field rules
3. `ccya/prompts/extract_progress_user.j2` — player_drift_signals block
4. `ccya/engine/arc.py` — `tick_arc()` engagement logic

### Detailed steps

#### Step 2.1 — Add DriftAnalysis model to models.py

**File:** `ccya/models.py`

**What:** Add a new model before `ProgressExtractResult`:

```python
class DriftAnalysis(BaseModel):
    """Structured drift analysis: does player intent align with active threads?"""
    match: bool = False           # True if intent aligns with any active thread tag
    reason: str | None = None     # One short phrase explaining why (e.g., "focused on Ellie's well-being")
    new_interest: str | None = None  # If match is False, what new direction is the player taking?

    model_config = {"extra": "ignore"}
```

Add to `ProgressExtractResult`:

```python
drift_analysis: DriftAnalysis = Field(default_factory=DriftAnalysis)
```

Keep `player_drift_signals: list[str] = Field(default_factory=list)` for backward compatibility during transition.

**Why:** Structured output is more deterministic than freeform phrases. The `match` field directly feeds engagement scoring. The `reason` field preserves the freeform insight but in a controlled field.

**Validation:** `ProgressExtractResult` now has `drift_analysis` with `match: bool`, `reason: str | None`, `new_interest: str | None`.

#### Step 2.2 — Update progress system prompt for drift analysis

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Replace the `player_drift_signals` field rules (lines 35-39) with:

```
`drift_analysis`: Analyze whether the player's intent aligns with any active thread's tags or summary.
- `match`: True if the intent clearly connects to an active thread (by tag or summary keyword). False if the player is pursuing something unrelated.
- `reason`: If match is True, a short phrase explaining the connection (e.g., "following Marlene toward the ridge"). If match is False, a short phrase describing the new direction (e.g., "focused on Ellie's well-being"). If neither applies, null.
- `new_interest`: If match is False and the player is pursuing something new, describe it in one short phrase. Otherwise null.

Examples:
  If active threads have tags ["navigation", "danger"] and the narration shows the player following a route through dangerous territory:
    {"match": true, "reason": "following a dangerous route", "new_interest": null}

  If active threads have tags ["political", "trust"] and the narration shows the player checking on a companion's well-being:
    {"match": false, "reason": "focused on Ellie's well-being", "new_interest": "companion care"}

Leave all fields at defaults (match=false, reason=null, new_interest=null) if the player is engaging with active threads normally and there's no notable drift.
```

**Why:** This replaces the vague "emit up to 3 short phrases" with a structured comparison. The extractor now has a clear decision tree: does intent match active threads? If yes → match=true with reason. If no → match=false with new_interest.

**Validation:** The extractor output will include a `drift_analysis` object with structured fields.

#### Step 2.3 — Update progress user prompt to show intent for drift comparison

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** The `player_intent` block already exists (lines 84-87). Ensure it's always present when intent is available, not just when `intent.intent` is non-empty. The current template checks `if intent and intent.intent` — this is fine since intent is always populated by the rules engine.

No change needed here — the intent block is already wired.

#### Step 2.4 — Update arc.py to consume structured drift

**File:** `ccya/engine/arc.py`

**What:** In `tick_arc()`, update the engagement logic (lines 246-266) to use `drift_analysis` first, falling back to `player_drift_signals`:

```python
# Arc engagement: check drift alignment with active thread tags
engagement_tags: set[str] = set()
for t in arc.active_threads:
    engagement_tags.update(t.tags)

# Prefer structured drift_analysis; fall back to player_drift_signals
drift_match = False
drift_list: list[str] = []

if hasattr(progress_result, 'drift_analysis') and progress_result.drift_analysis:
    drift_match = progress_result.drift_analysis.match
    if progress_result.drift_analysis.reason:
        drift_list.append(progress_result.drift_analysis.reason)
    if progress_result.drift_analysis.new_interest:
        drift_list.append(progress_result.drift_analysis.new_interest)
elif progress_result.player_drift_signals:
    drift_list = progress_result.player_drift_signals
    # Fallback: substring matching for legacy freeform drift
    for d in drift_list:
        d_lower = d.lower()
        for tag in engagement_tags:
            if tag in d_lower:
                drift_match = True
                break
        if drift_match:
            break

if drift_list:
    if drift_match:
        arc.arc_engagement = min(arc.arc_engagement + 1, 3)
    else:
        arc.arc_engagement = max(arc.arc_engagement - 1, -3)
```

**Why:** The arc director needs to consume the new structured format. The fallback ensures backward compatibility during the transition period.

**Validation:** `tick_arc()` correctly reads `drift_analysis.match` and updates `arc_engagement`. Legacy `player_drift_signals` still work via substring matching.

### Tests to write or update
- `tests/test_arc.py`: Add test `test_tick_arc_drift_analysis_match` that verifies engagement increments when `drift_analysis.match=True`.
- `tests/test_arc.py`: Add test `test_tick_arc_drift_analysis_no_match` that verifies engagement decrements when `drift_analysis.match=False`.
- `tests/test_arc.py`: Add test `test_tick_arc_drift_fallback` that verifies legacy `player_drift_signals` substring matching still works.
- `tests/test_extraction.py`: Add test verifying `drift_analysis` is present in `ProgressExtractResult` output.

### REPOMAP updates required
- `docs/REPOMAP/models.md`: Add `DriftAnalysis` model to extraction results section. Update `ProgressExtractResult` to note `drift_analysis` field.
- `docs/REPOMAP/engine.md`: Update `tick_arc()` description to note `drift_analysis` consumption.

### Risks
1. **Backward compatibility**: Old saves and tests that don't produce `drift_analysis` will fall back to `player_drift_signals`. This is intentional and tested.
2. **LLM output format**: The extractor must produce valid JSON matching `DriftAnalysis`. If it produces malformed JSON, Pydantic validation will fail and the extraction will retry. This is the same retry mechanism that handles all extraction errors.

## Ambiguities requiring resolution before execution
1. **Should `drift_analysis` replace `player_drift_signals` entirely or coexist?** Decision: coexist during transition. Once all tests and production runs produce valid `drift_analysis`, `player_drift_signals` can be removed.
2. **Should the extractor emit "ignored" signals for ALL active threads or only touched ones?** Decision: emit "ignored" for threads present in the narration but not affected. Omit threads with zero connection. This balances completeness with noise reduction.
