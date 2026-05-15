# ARC System Improvements — MVP1

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Wire arc_update into apply_delta | apply_delta ignores StateDelta.arc_update; add surgical merge |
| 02 | Thread promotion engine | Consume thread_signals to increment progress; promote latent→active; cap active at 4 |
| 03 | Latent thread hygiene | Cap latent pool at 4; tag candidate_opportunity threads as tactical; evict tactical-tagged first |
| 04 | Narrator arc_update emission | Narrator emits arc_update JSON after narration; engine strips it before display; expand _arc.j2 |

---

## Objective

The ARC system has correct data structures and a working extraction pipeline, but the arc never evolves: `apply_delta` ignores `StateDelta.arc_update`, thread signals are discarded after extraction, and `candidate_opportunity` floods `latent_threads` with uncapped tactical noise (11 latent threads in the live save, 9 of which are near-duplicate micro-scene hooks). The narrator has no write path for discovered truths. These four phases fix the closed loop with no new LLM calls and minimal new code surface.

## Non-goals
- Do not add a dedicated arc-management LLM call — all promotion/expiry is deterministic engine code.
- Do not auto-advance `arc.phase` in engine code — the narrator emits `arc_update.phase` when the arc genuinely shifts.
- Do not implement secret-reveal detection in the progress extractor — the narrator is the correct entity to decide when a hidden truth has been surfaced.
- Do not implement stale-thread TTL expiry — deferred to post-MVP1.
- Do not change `CampaignArc`, `ArcThread`, or `StateDelta` Pydantic shapes.

---

## Implementation — Phase 01: Wire arc_update into apply_delta

### Files to pull for context
- `ccya/state/delta.py`
- `ccya/models.py`

### Detailed steps

#### Step 1.1 — Add _merge_arc_update() to delta.py

**File:** `ccya/state/delta.py`

**What:** Add a private helper and call it at the end of `apply_delta` when `delta.arc_update` is not None.

**Why:** `StateDelta.arc_update: CampaignArc | None` has existed in the model since the field was added but `apply_delta` never reads it. Every downstream phase depends on this write path existing.

**Code Snippet**
```python
from ccya.models import ArcPhase  # add to existing imports


def _merge_arc_update(arc: dict[str, Any], au: "CampaignArc") -> None:
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

Call site at end of `apply_delta`:
```python
if delta.arc_update is not None:
    _merge_arc_update(state.setdefault("arc", {}), delta.arc_update)
```

**Validation:** Unit test: construct a state with a partial arc + a StateDelta with `arc_update`; call `apply_delta`; assert merged fields updated, fields absent from `arc_update` survive unchanged, `discovered_truths` union not replace.

### Tests to write or update
`tests/test_delta.py` → `test_arc_update_applied`, `test_arc_update_merge_not_replace`, `test_arc_update_discovered_truths_union`, `test_arc_update_none_noop`

### REPOMAP and architecture updates
`docs/REPOMAP/state.md` — document `arc_update` handling in `apply_delta`

### Risks
1. `ArcPhase` not currently imported in `delta.py` — add to imports. Verify no circular import with `models.py`.
2. `_upsert_threads` silently drops threads with no `id` — acceptable; log at DEBUG if needed.

---

## Implementation — Phase 02: Thread Promotion Engine

### Files to pull for context
- `ccya/engine/turn.py`
- `ccya/models.py` (ArcThread, ThreadState, ThreadSignal, ProgressExtractResult)
- `ccya/state/delta.py` (after Phase 01)

### Detailed steps

#### Step 2.1 — Write _apply_thread_signals() in engine/turn.py

**File:** `ccya/engine/turn.py`

**What:** A new deterministic function that:
1. Reads `progress_result.thread_signals`.
2. For each `advanced` signal: find the matching thread in `arc.active_threads` by id; increment `progress` by 1.
3. For each `failed` signal: move the matching thread directly to `completed_threads` with `state=FAILED`.
4. Completion check: any active thread with `progress >= 3` moves to `completed_threads` with `state=COMPLETE`.
5. Promotion: while `len(arc.active_threads) < 4` and `arc.latent_threads` is non-empty, promote the first latent thread (oldest by `last_offered_turn`, then list order) to `active` with `state=ACTIVE`.
6. Returns `CampaignArc | None` — only non-None if any mutation occurred.

Do NOT implement auto-phase-progression here — that belongs to the narrator (Phase 04).

**Code Snippet**
```python
from ccya.models import ArcPhase, ArcThread, CampaignArc, ThreadState

_ACTIVE_THREAD_CAP = 4
_THREAD_COMPLETION_THRESHOLD = 3


def _apply_thread_signals(
    state: dict[str, Any],
    progress_result: "ProgressExtractResult",
) -> "CampaignArc | None":
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
    active_by_id = {t.id: t for t in arc.active_threads}

    # Increment progress on advanced signals
    for tid, sig in signal_map.items():
        if sig == "advanced" and tid in active_by_id:
            t = active_by_id[tid]
            active_by_id[tid] = t.model_copy(update={"progress": t.progress + 1})
            mutated = True

    # Complete or fail threads
    newly_completed: list[ArcThread] = []
    still_active: list[ArcThread] = []
    for tid, t in active_by_id.items():
        sig = signal_map.get(tid, "ignored")
        if sig == "failed":
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

#### Step 2.2 — Call _apply_thread_signals in turn.py and fold result into delta

**File:** `ccya/engine/turn.py`

**What:** After extraction pipeline yields `progress_result`, before calling `apply_delta`:
```python
arc_delta = _apply_thread_signals(state, progress_result)
if arc_delta is not None:
    merged_delta = merged_delta.model_copy(
        update={"arc_update": arc_delta}
    )
```

If `merged_delta.arc_update` is already set (from a prior source), merge rather than overwrite — use `_merge_arc_update` logic from Phase 01 on the two `CampaignArc` objects before assigning.

**Validation:** After a turn where a thread signal of `advanced` is emitted, assert `state["arc"]["active_threads"][matching_id]["progress"]` incremented by 1.

### Tests to write or update
`tests/test_arc.py` (new) → `test_thread_progress_increment_on_advanced_signal`, `test_thread_fails_on_failed_signal`, `test_thread_completes_at_threshold`, `test_latent_thread_promoted_when_slot_available`, `test_active_cap_prevents_excess_promotion`

Use `FakeLLM` patterns from `docs/REPOMAP/testing.md`.

### REPOMAP and architecture updates
`docs/REPOMAP/engine.md` — document `_apply_thread_signals`, inputs, outputs, cap constant

### Risks
1. `CampaignArc.model_validate(arc_raw)` fails on saves missing new fields — wrapped in try/except returning None (noop).
2. `_THREAD_COMPLETION_THRESHOLD = 3` may be wrong for short or long packs. Acceptable for MVP1; make configurable post-MVP1.
3. If `merged_delta.arc_update` is already set when we try to apply thread signals, naive overwrite loses narrator-emitted arc changes. See step 2.2 note on merging.

---

## Implementation — Phase 03: Latent Thread Hygiene

### Files to pull for context
- `ccya/engine/turn.py`
- `ccya/models.py` (ArcThread)

### Detailed steps

#### Step 3.1 — Tag candidate_opportunity threads as tactical

**File:** `ccya/engine/turn.py`

**What:** In `_candidate_to_latent_thread` (new helper), when creating an `ArcThread` from `progress_result.candidate_opportunity`:
- Set `urgency="background"` and `tags=["tactical"]`.
- Generate a stable id from the first 5 words of the opportunity string, snake_cased, stripped of punctuation. Append `_t{turn_no}` if collision detected against existing thread ids.
- Cap `latent_threads` at **4**: if at cap, evict the oldest `tactical`-tagged latent thread first (by `last_offered_turn` ascending, then list order). If no tactical threads to evict and still at cap, do not add.

**Code Snippet**
```python
_LATENT_CAP = 4
_TACTICAL_TAG = "tactical"


def _candidate_to_latent_thread(
    arc: "CampaignArc",
    candidate: str,
    turn_no: int,
) -> "CampaignArc | None":
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

#### Step 3.2 — Call _candidate_to_latent_thread in turn.py

**File:** `ccya/engine/turn.py`

**What:** After `_apply_thread_signals`, if `progress_result.candidate_opportunity` is non-empty:
```python
updated_arc = _candidate_to_latent_thread(
    CampaignArc.model_validate(state["arc"]),
    progress_result.candidate_opportunity,
    turn_no,
)
if updated_arc is not None:
    # fold into merged_delta.arc_update using same merge logic
    ...
```

**Why:** The live save has 11 latent threads because every turn's `candidate_opportunity` appended unconditionally. A cap of 4 with tactical-first eviction keeps the arc pool meaningful and bounded.

**Validation:** Run 10 turns with mocked `candidate_opportunity`; assert `len(state["arc"]["latent_threads"]) <= 4` after each turn. Assert pack-seeded (non-tactical) latent threads are never evicted.

### Tests to write or update
`tests/test_arc.py` → `test_candidate_becomes_latent_thread`, `test_candidate_dedup_by_id`, `test_latent_cap_evicts_tactical_first`, `test_latent_cap_never_evicts_non_tactical`

### Risks
1. Pack-seeded latent threads that never get a `tactical` tag are protected from eviction even when the pool is full. This is the correct behavior — document it in REPOMAP.
2. Id collision after `_t{turn_no}` suffix is theoretically possible on same-turn duplicate candidates. The second guard `if tid in existing_ids: return None` handles it silently.

---

## Implementation — Phase 04: Narrator arc_update Emission

### Files to pull for context
- `ccya/engine/narrate.py`
- `ccya/prompts/sections/_arc.j2`
- `ccya/prompts/narrate_system.j2`
- `ccya/engine/turn.py` (where narrator output is consumed)

### Detailed steps

#### Step 4.1 — Expand _arc.j2 with pc_drive, thematic_question, discovered_truths

**File:** `ccya/prompts/sections/_arc.j2`

**What:** Replace current template with:
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

**Why:** `pc_drive` and `thematic_question` are already passed to `narrate_system.j2` via `current_arc_ctx` in `narrate.py` [cite:19] but `_arc.j2` reads `state.arc` directly. This makes the user-side context consistent. `discovered_truths` must show here so the narrator treats already-revealed truths as known facts — but `hidden_truths` must never appear here.

**Validation:** Render `narrate_user.j2` with a fixture state containing `discovered_truths` and `hidden_truths`; assert rendered output contains the former and does not contain the latter.

#### Step 4.2 — Add arc_update emission instruction to narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2`

**What:** Read `narrate_system.j2` first to find the correct insertion point (after the main narration rules, before or after the existing `current_arc` block). Add a new section:

```
## ARC UPDATE (optional, after narration)

If this turn's narration has materially advanced, shifted, or revealed something about the campaign arc, append a JSON block AFTER your narration using this exact format:

<<<ARC_UPDATE_START>>>
{"discovered_truths": ["exact text of revealed hidden truth"], "phase": "pursuit", "visible_goal": "updated goal if changed"}
<<<ARC_UPDATE_END>>>

Rules:
- Only emit this block if something genuinely changed. Omit entirely if the arc is unchanged.
- `discovered_truths`: only include if you narrated information this turn that explicitly surfaces a hidden truth. Copy the exact text from the hidden_truths list shown in your arc context (if present). Do not infer or paraphrase.
- `phase`: only include if the arc phase has visibly shifted this turn (e.g. the inciting incident has concluded and pursuit has begun).
- `visible_goal`: only include if the stated goal has materially changed.
- Do NOT include `active_threads`, `latent_threads`, or `hidden_truths` — thread management is handled by the engine.
- The block must be valid JSON. The narration text before the block is what the player sees.
```

**Why:** This gives the narrator a write path for arc-level changes (phase, discovered truths, goal) without delegating thread promotion to it. The output stripping in Step 4.3 ensures the block never reaches the player UI.

**Note on hidden_truths in narrator context:** `narrate_system.j2` already receives `current_arc` which includes `thematic_question` and `pc_drive` but NOT `hidden_truths` (they are not passed in `current_arc_ctx` in `narrate.py`). Do NOT add `hidden_truths` to `current_arc_ctx`. The narrator infers what has been revealed from the narration it just wrote — it does not need to see the raw secret list. If the narrator needs to know what secrets exist to flag a reveal, it already has them contextually from `pc_drive` and the story arc it has been narrating.

#### Step 4.3 — Strip <<<ARC_UPDATE_START>>> blocks from narrator output in turn.py

**File:** `ccya/engine/turn.py` (wherever the narrator LLM response is consumed and returned)

**What:** After receiving the raw narrator response string, before storing or returning it as player-visible text:
```python
import re
import json as _json

_ARC_UPDATE_RE = re.compile(
    r"<<<ARC_UPDATE_START>>>\s*(.*?)\s*<<<ARC_UPDATE_END>>>",
    re.DOTALL,
)


def _extract_narrator_arc_update(raw: str) -> tuple[str, dict | None]:
    """Strip arc_update block from narrator output. Returns (clean_text, arc_dict|None)."""
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

Call site:
```python
narration_text, narrator_arc_dict = _extract_narrator_arc_update(raw_narration)
# narration_text is what gets stored/displayed
# narrator_arc_dict, if non-None, is validated and merged into merged_delta.arc_update
if narrator_arc_dict:
    try:
        narrator_arc_update = CampaignArc.model_validate({**narrator_arc_dict})
        # merge into merged_delta.arc_update
        ...
    except Exception:
        log.warning("narrator emitted invalid arc_update JSON — discarded", ...)
```

**Why:** This is the exact pattern needed to prevent the old `active_scope` failure mode where structured output after narration leaked into the player-visible UI. The sentinel strings `<<<ARC_UPDATE_START>>>` / `<<<ARC_UPDATE_END>>>` are already used elsewhere in the codebase (`TRACE_IMMUTABLE`) as a precedent.

**Validation:** 
1. Unit test `_extract_narrator_arc_update` with: (a) clean narration, no block → returns unchanged; (b) narration + valid block → returns clean text + parsed dict; (c) narration + malformed JSON block → returns clean text + None.
2. Integration test: verify that `state["arc"]["discovered_truths"]` is populated after a turn where FakeLLM emits a narrator response containing an `<<<ARC_UPDATE_START>>>` block.
3. Assert that the block text does NOT appear in the stored narration event.

### Tests to write or update
`tests/test_arc.py` → `test_extract_narrator_arc_update_clean`, `test_extract_narrator_arc_update_valid_block`, `test_extract_narrator_arc_update_malformed_json`, `test_narrator_arc_update_merged_into_state`

### REPOMAP and architecture updates
- `docs/REPOMAP/engine.md` — document `_extract_narrator_arc_update`, sentinel strings, merge order
- `docs/REPOMAP/prompts.md` — document `<<<ARC_UPDATE_START>>>` block format in `narrate_system.j2`

### Risks
1. Narrator emits the block mid-narration rather than at the end. Mitigation: `_ARC_UPDATE_RE.sub("", raw).rstrip()` removes it regardless of position; add a prompt instruction to emit it at the very end.
2. Narrator includes `hidden_truths` in the emitted JSON. Mitigation: `CampaignArc.model_validate` accepts it, but `_merge_arc_update` only overwrites `hidden_truths` when non-empty — and since `hidden_truths` is not in the narrator's context, it won't have the real list to emit. Risk is low.
3. Sentinel strings appear in player narration in a non-arc context (e.g. player input quotes them). Mitigation: regex is DOTALL and greedy-minimally; real risk is near-zero. If it becomes an issue, use a UUID-based sentinel post-MVP1.
4. Merge order: engine thread signals (Phase 02) run before narrator arc_update is parsed. Both may mutate `arc_update` in `merged_delta`. Resolve by: Phase 02 sets `merged_delta.arc_update` from thread signals; Phase 04 narrator output is parsed AFTER narration, then merged on top using `_merge_arc_update` as a second pass.

---

## Ambiguities requiring resolution before execution

1. **Phase 02, Step 2.2 merge order:** When both `_apply_thread_signals` and the narrator emit `arc_update` in the same turn, which wins on field conflicts? Proposed: narrator wins on `phase`, `visible_goal`, `discovered_truths` (additive union); engine wins on `active_threads`, `latent_threads`, `completed_threads` (engine is authoritative on thread state). Confirm this before implementing the merge in Step 2.2.

2. **Phase 04, Step 4.2 — hidden_truths in narrator context:** The narrator currently does NOT see `hidden_truths` (they're not in `current_arc_ctx` in `narrate.py`). For the narrator to emit `discovered_truths`, it needs to know what the secrets are to copy them verbatim. Options: A) Pass `hidden_truths` to `narrate_system.j2` via `current_arc_ctx` inside a clearly-labelled "for internal reasoning only" block — acceptable given the narrator is not the player-facing output directly. B) Accept that the narrator will paraphrase rather than copy exactly, and do fuzzy matching in `_merge_arc_update`. C) Don't pass hidden_truths; let the narrator emit free-text discovered truths and accept they won't match the hidden_truths list verbatim. Recommendation: Option A, with an explicit instruction that hidden_truths must never appear in the narration prose itself.

3. **Phase 03 cap value:** Is 4 the right latent cap? The live save has 2 pack-seeded latent threads (`fedra_encroachment`, `the_revelation_of_ellie_s_biological_sig`) that matter, plus 9 tactical ones. A cap of 4 allows 2 meaningful pack threads + 2 tactical slots. If the pack generates more than 2 latent threads at seed time, raise to 6. Verify against the pack schema before committing to 4.
