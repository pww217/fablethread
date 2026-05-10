# GM Beat Ownership Migration: Scene → Progress

## Status
`completed`

## Part of
standalone

## Dependencies
- none

## Objective (completed)

`gm_beat` ownership was moved from the scene extractor (`SceneExtractResult`) to the
progress extractor (`ProgressExtractResult`), which has `outcome_summary`, quest updates,
and recent-event history — stronger signals for deciding *whether* a beat is needed and
*what kind* serves the story. The migration also:

- Extended `GMBeat.type` with `twist`, `setback`, `escalation`, `callback`
- Extended `GMBeat.surface_as` with `environmental`, `player_discovery`, `item`
- Added `beat_expires_turn` field to `GMBeat`
- Widened `deescalate` from `bool` to `float` (0.0-1.0) across the pipeline
- Added beat expiry guard in `run_turn` / `run_turn_retry`

## Remaining work (template fixes)

All template fixes have been implemented:

1. ~~**`rules_user.j2` truncation** (line 11): Still emits `t.narrative[-120:]` instead of~~
    ~~full `t.narrative`. The rules engine needs full narration to gauge intent, track~~
    ~~ongoing threads, and distinguish continuation from new action. The call site in~~
    ~~`turn.py` already passes `recent_turns[-1:]` — only the template needs updating.~~ ✅
2. ~~**`extract_progress_user.j2` wrong index** (line 52-53): Reads `recent_turns[-2].narrative`~~
    ~~which is the turn *before* the previous one. The pipeline passes `recent_turns[-2:]`~~
    ~~but the template should read `recent_turns[-1].narrative` to get the most recent prior~~
    ~~turn.~~ ✅
3. ~~**`extract_progress_user.j2` missing `gm_beat` instruction block**: The template does~~
    ~~not have a `gm_beat` instruction block. It should use `deescalate` and `quest_ages`~~
    ~~context to decide beat type/urgency. The `user_ctx` dict in `_extract_progress_messages`~~
    ~~already passes both keys (lines 307-308 in `extraction.py`).~~ ✅

## Non-goals

- Does not change how `pending_gm_beat` is consumed by the narrator (`narrate_user.j2`
  or `narrate_system.j2`) — only the producer changes.
- Does not change the directive-shaping logic in `rules.py` (`build_directive`).
- Does not touch compaction, chronicle, or any persistence path other than
  `meta.pending_gm_beat`.
- Does not change `StateDelta` — `gm_beat` was always absent from it and remains so.

## Completed changes

### Phase 1: Models

| File | Change | Status |
|---|---|---|
| `ccya/models.py` | Extended `GMBeat.type` with 4 new values | Done |
| `ccya/models.py` | Extended `GMBeat.surface_as` with 3 new values | Done |
| `ccya/models.py` | Added `beat_expires_turn: int | None` field | Done |
| `ccya/models.py` | Moved `gm_beat` from `SceneExtractResult` to `ProgressExtractResult` | Done |
| `ccya/models.py` | Moved `_nullify_invalid_gm_beat` validator to `ProgressExtractResult` | Done |
| `docs/REPOMAP/models.md` | Updated to reflect new types, surface_as, and field moves | Done |
| `tests/test_models.py` | Added tests for new types, surface_as, expiry, nullification | Done |

### Phase 2: Extraction pipeline

| File | Change | Status |
|---|---|---|
| `ccya/engine/extraction.py` | Widened `deescalate: bool` to `deescalate: float` in all functions | Done |
| `ccya/engine/extraction.py` | Added `deescalate` and `quest_ages` to `_extract_progress_messages` | Done |
| `ccya/engine/extraction.py` | Forwards `deescalate` and `quest_ages` at call site in `_run_extraction_pipeline` | Done |
| `ccya/engine/turn.py` | Reads `gm_beat` from `progress_result` instead of `scene_result` | Done |
| `ccya/engine/turn.py` | Adds `beat_expires_turn = turn_no + 2` when storing `pending_gm_beat` | Done |
| `ccya/engine/turn.py` | Added beat expiry guard in `run_turn` and `run_turn_retry` | Done |
| `ccya/engine/turn.py` | Widened `deescalate` computation to float magnitude (1.0/0.6/0.0) | Done |
| `ccya/engine/narrate.py` | Widened `deescalate: bool` to `deescalate: float` | Done |
| `tests/test_extraction.py` | Added tests for deescalate/quest_ages forwarding, beat source | Done |
| `tests/test_turn.py` | Added `test_beat_expiry` and `test_deescalate_float_magnitude` | Done |

## Remaining work: detailed steps

### Step 3.1 — Fix rules_user.j2 narration truncation

**File:** `ccya/prompts/rules_user.j2` (line 11)

**Current:**
```jinja2
T{{ t.turn }}: {{ t.input }} — {% if t.narrative | length > 120 %}… {% endif %}{{ t.narrative[-120:] }}
```

**Change to:**
```jinja2
T{{ t.turn }}: {{ t.input }} — {{ t.narrative }}
```

Remove the truncation and conditional ellipsis. The rules engine needs the full
narration to understand context and track ongoing threads.

### Step 3.2 — Fix extract_progress_user.j2 wrong recent_turns index

**File:** `ccya/prompts/extract_progress_user.j2` (lines 52-53)

**Current:** Reads `recent_turns[-2].narrative` (the turn before the previous one)

**Change to:** Read `recent_turns[-1].narrative` (the most recent prior turn)

The pipeline passes `recent_turns[-2:]` (two turns). Index `-2` is the older of the
two; `-1` is the most recent prior turn, which is the correct context for the player.

### Step 3.3 — Add gm_beat instruction block to extract_progress_user.j2

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Add a `gm_beat` instruction block after the existing decision-context sections.
The block should use `deescalate` and `quest_ages` context to decide beat type/urgency.

- `deescalate` is already passed in `user_ctx` (extraction.py lines 307-308)
- `quest_ages` is already passed in `user_ctx` (extraction.py lines 307-308)
- `deescalate > 0.5` → prefer `breathing_room` or no beat
- `deescalate == 0.0` with active pressure → `pressure` or `escalation`
- Quest staleness in `quest_ages` → `setback` or `complication`

## Risks (remaining)

1. **`rules_user.j2` full narration increases tokens.** Emitting full narration instead
   of 120 chars will increase LLM input tokens per turn. This is acceptable — the rules
   engine needs the context for accurate intent classification. Monitor token usage after
   the change.

2. **`extract_progress_user.j2` index fix is a behavioral change.** Switching from
   `recent_turns[-2]` to `recent_turns[-1]` changes which turn's narration is shown.
   This is the correct behavior (most recent prior turn), but if any existing game state
   depends on the stale index, it may shift slightly.

## TODO.md update

Line 60 in `docs/plans/TODO.md` already has:
```
- [ ] **GM beat ownership migration + deescalate float + beat expiry + rules full narration**
  — progress owns gm_beat, deescalate widened to float, beat expiry guard,
  rules step receives full narration — [progress-rules-narration.md](progress-rules-narration.md) (Phases 1-2 done)
```

Update to reflect remaining template fixes:
```
- [ ] **GM beat ownership migration: template fixes** — rules_user.j2 full narration,
  extract_progress_user.j2 recent_turns index, gm_beat instruction block —
  [progress-rules-narration.md](progress-rules-narration.md) (Phases 1-2 done, 3 pending)
```
