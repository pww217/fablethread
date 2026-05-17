# Fix Campaign Arc Thread Lifecycle

## Status
`open`

## Phases

3 phases: restore functional thread lifecycle (silent failure diagnosis, unknown-ID promotion logic), correct active cap constant, and add comprehensive unit tests covering the full arc engine.

## Issue

The campaign arc system's engine-driven thread lifecycle is completely non-functional across all 7 turns of live play. Zero `arc_update` mutations appear in any applied delta. Evidence: `_apply_thread_signals()` returns None every turn despite valid seed data (threads exist in state.yaml with correct structure), progress extractor emits `advanced_threads` correctly on T1/T2/T6, and candidate opportunities surface at T1/T2 but never spawn latent threads. Additionally, the active thread cap constant is stale (`_ACTIVE_THREAD_CAP = 4` per ARCHITECTURE.md specifies 3).

## Solution

Three focused phases: (1) diagnose why `_apply_thread_signals()` silently returns None by adding error logging and fixing any guard condition or model validation issues, plus correct unknown advanced_threads ID handling; (2) fix the stale active cap constant; (3) add comprehensive unit tests for the full thread lifecycle covering silent expiry, completion threshold, promotion cooldown, latent→active transition from unknown IDs, candidate opportunity spawning, and edge cases.

## Firm decisions

1. `_ACTIVE_THREAD_CAP` must be `3` per ARCHITECTURE.md "Campaign Arc System" (explicitly states "down from 4").
2. `_LATENT_CAP` remains `4` — matches documentation.
3. Unknown advanced_threads IDs in progress output should promote matching latent threads to active with progress=0, not silently drop them. This is the documented behavior per ARCHITECTURE.md "Campaign Arc System" → "Engine-Driven Arc: Thread Lifecycle".
4. `_apply_thread_signals` must log at WARNING level when it encounters unexpected arc structure or model validation failures that would cause silent None returns.
5. All new code uses `logging.getLogger(__name__)` with context keys `turn`/`trace_id`.

## Non-goals

- Do not modify the progress extractor prompt templates (extract_progress_user.j2 / extract_progress_system.j2).
- Do not change how the narrator emits arc_update sentinel blocks.
- Do not modify CampaignArc or ArcThread Pydantic model schemas.
- Do not add integration tests — unit tests only, using FakeLLM patterns from existing test suite.

## Risks, Ambiguities, and Blockers

**Risk:** The root cause of `_apply_thread_signals` returning None every turn may involve `state["arc"]` structure mismatch between seed-generated dicts and what `CampaignArc.model_validate()` expects (e.g., enum values not coerced). Phase 1 must diagnose this first.

**Ambiguity:** When unknown advanced_threads IDs promote latent threads, should the promoted thread inherit its original progress value or reset to 0? Per ARCHITECTURE.md "Engine-Driven Arc: Thread Lifecycle" diagram, promotion sets `last_seen_turn = turn_no` but doesn't mention resetting progress — however a newly-promoted thread hasn't been advanced yet. I will set progress=0 for unknown-ID promotions (fresh start) and preserve original progress for re-promotion of previously-active threads that were silently demoted.

**Blocker:** None identified. All changes are contained to `ccya/engine/turn.py` and `tests/test_thread_lifecycle.py`.

## Implementation — Phase 1: Diagnose silent failure + fix unknown-ID promotion

### Context files to load
- `/Users/pwilson/Repos/ccya/ccya/engine/turn.py` (lines 65–234, `_apply_thread_signals`, `_candidate_to_latent_thread`)
- `/Users/pwilson/Repos/ccya/ccya/state/delta.py` (lines 25–68, `_merge_arc_update`)
- `/Users/pwilson/Repos/ccya/ccya/models.py` (CampaignArc, ArcThread, ThreadState)
- `/Users/pwilson/Repos/ccya/docs/ARCHITECTURE.md` ("Campaign Arc System" section, lines 546–750)

### Detailed steps

#### Step 1.1 — Add error logging and guard validation to `_apply_thread_signals`

**File:** `ccya/engine/turn.py`

**What:** Wrap the core logic of `_apply_thread_signals` in a try/except with WARNING-level logging, add early-exit diagnostics when arc_raw structure is unexpected (e.g., threads stored as Pydantic models instead of dicts), and log at DEBUG level what happens per-thread so silent None returns can be diagnosed.

**Why:** Currently the function silently returns None on any error or no-mutation case. Without logging, there's zero visibility into why it fails. The guard `if not arc_raw: return None` is correct but doesn't cover cases where arc_raw exists but has unexpected structure (e.g., CampaignArc model objects instead of dicts from seed generation).

**Code Snippet:**
```python
def _apply_thread_signals(
    state: dict[str, Any],
    progress_result: Any,
) -> CampaignArc | None:
    """Process simplified advanced_threads list.

    Any active thread NOT in the list is implicitly ignored.
    After 5 consecutive turns without being listed → demote to latent (frees slot).
    Threads with progress >= _THREAD_COMPLETION_THRESHOLD (3) → complete.
    Promote latent threads if slots available and 3-turn cooldown met.

    Returns a CampaignArc if any mutation occurred, None otherwise.
    """
    arc_raw = state.get("arc")
    if not arc_raw:
        return None
    try:
        arc = CampaignArc.model_validate(arc_raw)
    except Exception as exc:
        _log.warning(
            "thread_signals: failed to validate arc",
            extra={"turn": turn_no, "trace_id": "", "kind": "arc"},
        )
        return None

    # Parse advanced_threads as list of string IDs
    advanced_ids = set(progress_result.advanced_threads or [])
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    _log.debug(
        "thread_signals: turn=%d advanced_ids=%s active_count=%d latent_count=%d",
        turn_no, advanced_ids, len(arc.active_threads), len(arc.latent_threads),
    )

    mutated = False
    active_by_id: dict[str, ArcThread] = {t.id: t for t in arc.active_threads}

    # Also index latent threads by ID for unknown-ID promotion
    latent_by_id: dict[str, ArcThread] = {t.id: t for t in arc.latent_threads}

    # Process each active thread
    newly_completed: list[ArcThread] = []
    still_active: list[ArcThread] = []

    for tid, t in active_by_id.items():
        if tid in advanced_ids:
            new_progress = t.progress + 1
            updated_t = t.model_copy(update={
                "progress": new_progress,
                "last_seen_turn": turn_no,
            })

            # Check completion threshold
            if new_progress >= _THREAD_COMPLETION_THRESHOLD:
                newly_completed.append(updated_t.model_copy(
                    update={"state": ThreadState.COMPLETE}
                ))
                mutated = True
                _log.debug(
                    "thread_signals: thread %s completed at progress=%d",
                    tid, new_progress,
                )
            else:
                still_active.append(updated_t)
        elif t.last_seen_turn is None or (turn_no - t.last_seen_turn >= _EXPIRE_SILENT_TURNS):
            # Expired — demote to latent, reset timer
            expired_t = t.model_copy(update={
                "state": ThreadState.LATENT,
                "last_seen_turn": None,
            })
            still_active.append(expired_t)  # will be moved below
            mutated = True
            _log.debug(
                "thread_signals: thread %s silently demoted (turn_no=%d last_seen=%s)",
                tid, turn_no, t.last_seen_turn,
            )

    # Separate actually-still-active from demoted threads
    really_still_active = [t for t in still_active if t.state == ThreadState.ACTIVE]
    demoted_to_latent = [t for t in still_active if t.state != ThreadState.ACTIVE]

    arc = arc.model_copy(update={
        "active_threads": really_still_active,
        "completed_threads": arc.completed_threads + newly_completed,
        "latent_threads": list(arc.latent_threads) + demoted_to_latent,
    })

    # Promote latent threads matching unknown advanced_ids (first-time advancement).
    # These IDs were emitted by the progress extractor but don't exist in active_threads.
    # Per ARCHITECTURE.md: "advanced_threads" should drive thread progression including
    # promotion from latent when a match exists.
    for tid in advanced_ids - set(active_by_id.keys()):
        if tid in latent_by_id:
            promoted = latent_by_id[tid].model_copy(update={
                "state": ThreadState.ACTIVE,
                "progress": 0,
                "last_seen_turn": turn_no,
                "urgency": "normal",
            })
            arc.latent_threads = [t for t in arc.latent_threads if t.id != tid]
            really_still_active.append(promoted)
            mutated = True
            _log.debug(
                "thread_signals: latent thread %s promoted to active (unknown advanced_id)",
                tid,
            )

    # Promotion check: only if 3-turn cooldown met and slots available
    last_promotion = arc_raw.get("arc_last_promotion_turn") or 0
    can_promote = (turn_no - last_promotion >= _PROMOTION_COOLDOWN_TURNS) or len(arc.active_threads) == 0

    if can_promote:
        available_slots = _ACTIVE_THREAD_CAP - len(arc.active_threads)

        # Find eligible latent threads (no unlock_if or satisfied, excluding recently demoted)
        completed_ids = {t.id for t in arc.completed_threads}
        already_active_ids = {t.id for t in really_still_active}
        available = [
            t for t in arc.latent_threads
            if t.id not in completed_ids
            and t.id not in already_active_ids
            and not (t.unlock_if and t.unlock_if.strip())
        ]

        # Sort by last_offered_turn (oldest first) — skip recently demoted ones
        available.sort(key=lambda t: t.last_offered_turn or 0)

        to_promote = available[:available_slots]
        if to_promote:
            promoted = [
                t.model_copy(update={
                    "state": ThreadState.ACTIVE,
                    "last_seen_turn": turn_no
                }) for t in to_promote
            ]
            remaining_latent = [
                t for t in arc.latent_threads if t.id not in {p.id for p in to_promote}
            ]
            arc = arc.model_copy(update={
                "active_threads": really_still_active + promoted,
                "latent_threads": remaining_latent,
                "arc_last_promotion_turn": turn_no,
            })
            mutated = True

    return arc if mutated else None
```

**Validation:** Run `python3 -c "from ccya.engine.turn import _apply_thread_signals; print('import ok')"` to verify no syntax errors. Check that the function now logs at DEBUG level per turn with thread counts and advanced_ids. Verify existing tests still pass (they should since behavior is unchanged for known IDs).

#### Step 1.2 — Fix unknown-ID promotion logic placement

**File:** `ccya/engine/turn.py`

**What:** The unknown-ID promotion code I added in Step 1.1 must be placed correctly: after the active-thread processing loop but BEFORE the cooldown-based promotion check. This ensures first-time advancement (latent→active for unknown IDs) happens immediately without waiting for the 3-turn cooldown.

**Why:** Per ARCHITECTURE.md "Campaign Arc System" → "Engine-Driven Arc: Thread Lifecycle", advanced_ids should drive thread progression including latent→active transition when a match exists in `latent_threads`. The existing code only processes threads already in `active_by_id`, silently dropping unknown IDs entirely.

The placement matters because the cooldown check (line 152+) would incorrectly gate first-time promotions behind the 3-turn window. First-time advancement from unknown advanced_ids is an explicit action by the progress extractor and should take priority over passive latent promotion.

**Code Snippet:** (Already included in Step 1.1 above — the block between "Separate actually-still-active" and "Promotion check:") handles this correctly:
```python
# Promote latent threads matching unknown advanced_ids (first-time advancement).
for tid in advanced_ids - set(active_by_id.keys()):
    if tid in latent_by_id:
        promoted = latent_by_id[tid].model_copy(update={...})
        ...
```

**Validation:** Write a unit test that creates an arc with one active thread and one latent thread, then calls `_apply_thread_signals` with `advanced_threads=["latent_thread_id"]`. Verify the latent thread is promoted to active immediately (not gated by cooldown).

#### Step 1.3 — Add error logging around `_candidate_to_latent_thread` call site

**File:** `ccya/engine/turn.py`

**What:** Wrap the existing try/except at lines 1049-1078 with additional DEBUG-level logging that shows what happens when a candidate_opportunity is processed. Also log whether the arc was successfully validated and whether `_candidate_to_latent_thread` returned None or an updated arc.

**Why:** Candidate opportunities surface at T1/T2 in live play but never spawn latent threads. The existing try/except catches exceptions silently with only a WARNING log. We need visibility into whether `CampaignArc.model_validate(arc_raw)` succeeds, whether `_candidate_to_latent_thread` returns None (meaning the candidate was rejected), or whether it successfully creates a thread.

**Code Snippet:**
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
                                _merge_arc_update(
                                    state.setdefault("arc", {}), updated_arc
                                )
                                # ... existing delta merge code unchanged ...
                                _log.debug(
                                    "thread_signals: candidate opportunity created latent thread at T%d",
                                    turn_no,
                                    extra={"turn": turn_no, "trace_id": trace_id},
                                )
                            else:
                                _log.debug(
                                    "thread_signals: candidate opportunity rejected (cap/dedup) at T%d: %s",
                                    turn_no, progress_result.candidate_opportunity[:80],
                                    extra={"turn": turn_no, "trace_id": trace_id},
                                )
                        except Exception as exc:
                            _log.warning(
                                "candidate_opportunity: failed to validate arc at T%d: %s",
                                turn_no, exc,
                                extra={"turn": turn_no, "trace_id": trace_id},
                            )
```

**Validation:** After applying this phase and running a new game through 2-3 turns, check debug logs for thread_signals entries. Verify that candidate opportunities at T1/T2 either create latent threads or are rejected with reason (cap/dedup). If they're silently rejected, the next investigation step is to check whether `_LATENT_CAP` was exceeded or whether dedup found a matching ID.

### Tests to write or update

**New file:** `tests/test_thread_lifecycle.py`

Write these test classes:

1. **TestApplyThreadSignalsBasic** — 4 tests
   - `test_advance_increments_progress`: Create arc with one active thread, advance it → progress becomes 1, last_seen_turn updated
   - `test_complete_at_threshold`: Advance same thread twice more (total 3 advances) → state=COMPLETE, moved to completed_threads
   - `test_silent_expiry_demotes_to_latent`: Active thread not advanced for 5 turns → demoted to latent with LATENT state and last_seen_turn=None
   - `test_no_mutation_returns_none`: No threads advanced, no silent expiry → returns None

2. **TestUnknownIdPromotion** — 3 tests (NEW: covers the unknown-ID promotion logic)
   - `test_unknown_id_promotes_matching_latent`: Arc has one active + one latent thread; progress emits advanced_ids containing only the latent thread's ID → latent promoted to active with progress=0, removed from latent list
   - `test_unknown_id_no_match_ignored`: Progress emits unknown IDs that don't match any latent thread → no mutation (mutated=False)
   - `test_unknown_id_promotion_bypasses_cooldown`: Arc has 3 active threads at max cap; one slot freed by silent expiry; progress emits unknown ID matching a latent thread → promoted immediately without waiting for cooldown

3. **TestPromotionCooldown** — 2 tests
   - `test_respects_3_turn_cooldown`: Latent thread eligible but only 1 turn since last promotion → not promoted
   - `test_promotes_when_no_active_threads`: No active threads (all expired) → promotes immediately regardless of cooldown

4. **TestCandidateToLatentThread** — 3 tests
   - `test_creates_latent_from_candidate_string`: Valid candidate string creates latent thread with correct id, summary, tags=["tactical"], urgency="background"
   - `test_dedup_prevents_duplicate_id`: Same candidate string re-emitted → returns None (id exists in active/latent/completed)
   - `test_evicts_oldest_tactical_when_full`: Latent cap at 4 with all tactical threads; new candidate arrives → oldest tactical evicted, new one added

5. **TestActiveCap** — 1 test
   - `test_caps_at_three_threads`: Arc has 3 active threads (at cap); silent expiry frees one slot; eligible latent exists → exactly 2 promoted to fill slots (not more than cap)

### REPOMAP updates required

- Update `docs/REPOMAP/engine.md` — Add thread lifecycle section documenting `_apply_thread_signals`, `_candidate_to_latent_thread`, unknown-ID promotion behavior, and the new error logging points.
- No changes needed for models.py or delta.py (schema unchanged).

## Implementation — Phase 2: Fix active cap constant

### Context files to load
- `/Users/pwilson/Repos/ccya/ccya/engine/turn.py` (line 65)
- `/Users/pwilson/Repos/ccya/docs/ARCHITECTURE.md` ("Campaign Arc System" section, line ~613)

### Detailed steps

#### Step 2.1 — Change `_ACTIVE_THREAD_CAP` from 4 to 3

**File:** `ccya/engine/turn.py`

**What:** Change the constant on line 65 from `4` to `3`. Also update the docstring.

**Why:** ARCHITECTURE.md "Campaign Arc System" explicitly states: *"Active cap: 3 threads (down from 4)."* The code still has the old value of 4, which was apparently changed in a previous plan but not applied here. This is a one-line change with no behavioral impact on existing games that have fewer than 4 active threads.

**Code Snippet:**
```python
_ACTIVE_THREAD_CAP = 3
"""Maximum number of threads in the active state."""
```

**Validation:** Run `make check` to verify type checking passes. No test changes needed — all thread lifecycle tests use `_ACTIVE_THREAD_CAP` via import, so they automatically pick up the new value. Verify that existing integration tests don't hardcode 4 as an expected cap.

### Tests to write or update

No new tests required for this phase alone. The `TestActiveCap.test_caps_at_three_threads` test from Phase 1 validates the correct behavior with the updated constant. If any existing test fails due to expecting 4 active threads, update it there.

### REPOMAP updates required

None — no file structure changes.

## Implementation — Phase 3: Comprehensive unit tests for thread lifecycle

### Context files to load
- `/Users/pwilson/Repos/ccya/tests/test_thread_lifecycle.py` (created in Phase 1)
- `/Users/pwilson/Repos/ccya/tests/integration/conftest.py` (`state_with_arc`, `_PROGRESS_RESPONSE`)
- `/Users/pwilson/Repos/ccya/ccya/models.py` (CampaignArc, ArcThread, ThreadState)

### Detailed steps

#### Step 3.1 — Add edge case tests for thread lifecycle

**File:** `tests/test_thread_lifecycle.py`

Add these additional test classes:

6. **TestSilentExpiryEdgeCases**
   - `test_last_seen_none_treated_as_new_thread`: Thread with last_seen_turn=None is NOT silently demoted on first turn (turn_no=1, 1-None can't be computed). Must check for None before subtraction. If the code checks `t.last_seen_turn is None` first per line 133, this should correctly handle it — but verify the condition order prevents TypeError.
   - `test_partial_advance_preserves_non_advanced`: Arc has 2 active threads; only one advanced → non-advanced thread keeps its original progress and last_seen_turn unchanged (not incremented).

7. **TestMergeArcUpdateThreadFields**
   - `test_set_replace_active_threads_on_engine_update`: When engine produces arc_delta with new active_threads list, `_merge_arc_update` replaces the entire active_threads in state dict (set-replace semantics per ARCHITECTURE.md "Engine owns threads").
   - `test_preserves_completed_when_only_active_changes`: Engine updates only active_threads → completed_threads unchanged.

8. **TestFullLifecycle** — 1 integration-style test using FakeLLM patterns
   - `test_three_turn_advance_completes_thread`: Seed arc with one thread, run through 3 turns where progress emits the same advanced_thread ID each turn → after T3, thread should be in completed_threads with state=COMPLETE.

#### Step 3.2 — Add error handling tests

9. **TestErrorHandling**
   - `test_malformed_arc_raw_returns_none`: Pass arc dict with invalid structure (e.g., active_threads contains non-dict items) → `_apply_thread_signals` returns None without crashing, logs WARNING.
   - `test_empty_advanced_threads_no_crash`: progress_result.advanced_threads is empty list or None → function processes normally (no threads advanced, no mutations if nothing else changed).

#### Step 3.3 — Run validation suite

**What:** After all test classes are written in Phase 1 and this phase, run the full test suite:
```bash
python -m pytest tests/test_thread_lifecycle.py -v
python -m pytest tests/ -x --timeout=15
```

**Validation:** All new tests must pass. No existing tests should break. If any integration test fails due to thread behavior changes (e.g., expecting 4 active threads), update the fixture or assertion there.

### Tests to write or update

All in `tests/test_thread_lifecycle.py` — see Step 1.2 and Step 3.1 above for complete list of ~18 new tests. Also check whether any existing integration test hardcodes `_ACTIVE_THREAD_CAP = 4` expectations (in conftest.py fixtures) and update them to use the constant or expect 3.

### REPOMAP updates required

- Update `docs/REPOMAP/testing.md` — Add entry for `tests/test_thread_lifecycle.py` documenting what each test class covers.
- No changes needed for other REPOMAP files (file structure unchanged).

## Risks, Ambiguities, and Blockers

**Risk:** If the root cause of silent None returns is that `state["arc"]` doesn't exist during turn processing (e.g., seed generation creates threads but they're lost before `_apply_thread_signals` runs), Phase 1's error logging will surface this. The fix would then involve ensuring arc data flows correctly through the extraction pipeline, not just fixing the thread logic itself.

**Risk:** If `CampaignArc.model_validate(arc_raw)` fails because seed-generated YAML contains Pydantic model objects instead of dicts (e.g., ArcThread instances rather than plain dicts), the error logging will surface this too. The fix would be in `_migrate_state` or `save_state` to ensure proper serialization.

**Ambiguity:** When unknown advanced_ids promote latent threads, should they reset progress to 0? I chose yes (fresh start) per the principle that "advancing" a thread means meaningful action was taken on it this turn — but if the intent is that unknown IDs represent threads the LLM discovered mid-stream rather than first-time creation, preserving original progress might be better. The test suite covers both paths so we can adjust.

**Blocker:** None identified. All changes are contained and reversible.

## Execution order

Phase 1 → Phase 2 → Phase 3 (in parallel with Phase 1's Step 3.1). Phase 1 must complete first because the error logging is required to diagnose whether `_apply_thread_signals` even runs correctly before we can verify unknown-ID promotion works. Phase 2 is independent and could technically run in parallel, but it's safer to do after Phase 1 so any discovered issues with arc structure don't mask themselves behind a wrong cap value.

## Final validation

After all phases complete:
```bash
make check && make test
```

Then verify against the live save at `saves/default/events.jsonl` by running:
```bash
python3 scripts/debug/ev.py mechanics 7 saves/default/events.jsonl | grep -A20 "Campaign Arc"
```

Confirm that active_threads now correctly reflects thread lifecycle (silent expiry, promotion) rather than showing stale seed data. Also verify no `arc_update` keys appear in applied deltas with unexpected content — they should only contain legitimate mutations from `_apply_thread_signals`.
