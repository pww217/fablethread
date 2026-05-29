# Plan: Simplify Thread System — Finding #2 (Seed-Thread Mismatch)

## Status
completed

**Date:** 2026-05-17  

---

## Problem Summary

The thread system is over-engineered. The LLM outputs `thread_signals` with 4 signal types (`advanced/blocked/failed/ignored`) plus a separate `drift_analysis` per-thread engagement analysis plus legacy `player_drift_signals`. All of this produces zero useful results in practice — every seed thread gets IGNORED because it doesn't match actual gameplay. The system generates too much LLM output for what amounts to tracking theater.

The user's diagnosis: threads should be simple. Player advances a thread → list its ID. Not listed = ignored. After 5 turns of being ignored, the thread quietly expires and makes room for something new. Max 3 active threads at any time. New candidates promoted every ~3 turns. That's it.

---

## Thread Visibility Model (New)

```
┌─────────────────────────────────────────────────────┐
│                    THREAD STATES                      │
│                                                       │
│  latent_threads                                      │
│  ────────────                                        │
│  • Pack-seeded threads (unlock_if conditions)        │
│  • Tactical candidates from narration                │
│  • Dormant threads demoted after expiry              │
│  → SHOWN to progress extractor ONLY                  │
│  → Allows detect re-engagement → promote back active │
│  → NOT shown in narrator prompt                      │
│                                                       │
│  active_threads (max 3)                              │
│  ──────────────                                      │
│  • Threads the player is currently working on          │
│  → SHOWN to BOTH narrator AND progress extractor     │
│  → Only these threads can be advanced                │
│                                                       │
│  completed_threads                                   │
│  ───────────────────                                 │
│  • Complete (progress >= 3)                          │
│  • Failed                                            │
│  • Expired (demoted from active after 5 silent turns)│
│  → NOT shown in any prompt context                    │
│  → Visible only in UI completed log                   │
└─────────────────────────────────────────────────────┘

Key decisions:
- NARRATOR sees ONLY active threads. Narration should focus on what's pressing 
  and urgent. Keeps context ~30% smaller. Latent/candidate/expired threads are 
  invisible in narration prompts.
- PROGRESS EXTRACTOR sees ACTIVE + LATENT threads. Needs latent awareness so it 
  can detect when player actions naturally re-engage an old thread that deserves 
  promotion back to active. Any latent or active thread not listed = ignored.
- Expired threads demote back to LATENT (not complete). They're removed from 
  active_threads, placed in latent_threads with state=latent. Any future narration 
  that picks up old tags can lift them via compactor or new candidate. This preserves 
  narrative continuity without bloating context.
```

---

## Expiration Behavior: Demote to Latent (Not Complete)

**Question:** After 5 turns expire, should a thread be removed entirely or demoted back to latent for potential resurfacing?

**Answer: Demote to latent.** Here's why:

- If narration later picks up an old thread's tags or summary (e.g., "the port authority audit" mentioned in passing after being dormant), the compactor can lift it. A complete/failed thread is dead — a latent thread has resurrection potential.
- Resurfacing path 1 (compactor): During `thread_cleanup`, if bulletin bullets mention an old latent thread's topic, lift it to active.
- Resurfacing path 2 (candidate_opportunity): If narration strongly echoes an old dormant thread, the progress extractor can emit a new candidate that becomes a fresh latent entry. The old one stays in latent pool available for future promotion.
- No need for a separate `expired_threads` list — just demote to `state=latent`. They're already filtered out of prompt context since only active threads are shown.

**Mechanics:** When an active thread hits 5 silent turns:
1. Remove from `active_threads` (frees a slot)  
2. Add to `latent_threads` with `state=latent`, keeping all original data (summary, tags, urgency)
3. Reset `last_seen_turn = None` — it starts fresh if promoted again

This is simpler than marking complete because: no new UI section needed, compactor already handles latent threads in thread_cleanup, and narrative continuity is preserved.

---

## Current Architecture

```mermaid
graph TB
    subgraph "Progress Extraction (LLM)"
        A[thread_signals:<br/>list of {id, signal}] --> B[_apply_thread_signals]
        C[drift_analysis:<br/>per-thread {thread_id, match,<br/>reason, new_interest}] --> D[tick_arc]
        E[player_drift_signals:<br/>deprecated list[str]> --> D
    end

    subgraph "Engine Processing"
        B -->|ADVANCED → progress++<br/>FAILED → complete<br/>progress >= 3 → complete<br/>promote latent if slot open| F[(state arc)]
        B -->|signal=ignored: NO-OP| G[dead code path]
        
        D -->|match=true → engagement+1<br/>no match → engagement-1| H[(arc_engagement -3..+3)]
    end

    subgraph "Prompt Context"
        F -.->|"active_threads"| I[Narrate prompt]
        F -.->|"active_threads"| J[Extract progress prompt]
        H -.->|"arc_engagement"| K[UI sidebar display]
    end

    B -->|thread_signals output schema| L["{id, signal: advanced|blocked|failed|ignored}"]
    D -->|drift_analysis output schema| M["{thread_id, match, reason,<br/>new_interest} — ONE PER ACTIVE THREAD"]
```

**Key inefficiencies:**
- 3 separate LLM outputs about thread engagement (`thread_signals`, `drift_analysis`, `player_drift_signals`) all trying to measure the same thing
- 4 signal types where only "advanced" matters mechanically (blocked/failed are never emitted in practice; ignored is a no-op)
- Drift analysis generates ONE entry per active thread — massive output for zero downstream effect on thread lifecycle
- `arc_engagement` scores engagement but nothing reads it except UI display
- `_map_thread_id_to_id()` coercion logic handles 8+ different LLM output patterns — all vestigial

---

## New Architecture

```mermaid
graph TB
    subgraph "Progress Extraction (LLM)"
        A[advanced_threads:<br/>list of thread IDs<br/>{id1, id2, ...} or []] --> B[_apply_thread_signals]
    end

    subgraph "Engine Processing"
        B -->|thread in list → progress++<br/>progress >= 3 → complete<br/>no advance for 5 turns → demote to latent<br/>promote latent if slot open + 3-turn cooldown| F[(state arc)]
    end

    subgraph "Prompt Context — Narrator (active only)"
        F -.->|"active_threads"| I[Narrate prompt]
    end
    
    subgraph "Prompt Context — Progress Extractor (active + latent)"
        F -.->|"active_threads" + "latent_threads"| J[Extract progress prompt]
    end
    
    B -->|simplified output schema| L["list of thread IDs<br/>e.g. [\"the_missing_ore\", \"fraying_rigging\"]"]
```

**Key simplifications:**
- ONE field in extraction: `advanced_threads` — just a list of thread IDs the player advanced this turn (can reference active or latent threads)
- No signal types, no drift analysis, no engagement scoring — all eliminated
- Any active/latent thread NOT listed = ignored. After 5 consecutive turns without being listed → demoted to latent (frees slot, preserves resurfacing potential)
- `arc_engagement` removed — nothing downstream uses it meaningfully

---

## Phase Structure

Each phase groups changes that share context or tokens. Phases are ordered so each builds on the previous one cleanly.

### Phase 1: Model Layer — Shared State Schema

**Scope:** All files that define or consume the CampaignArc/ArcThread/ProgressExtractResult data structures. Changes here affect both narrator and extractor prompts (shared state). This is the foundational change.

| File | Change |
|------|--------|
| `ccya/models.py` | Delete `ThreadSignalType`, `ThreadSignal`, `DriftAnalysis`. Replace `thread_signals`, `drift_analysis`, `player_drift_signals` in ProgressExtractResult with `advanced_threads: list[str] = Field(default_factory=list)`. Delete `arc_engagement` from CampaignArc. Add `last_seen_turn: int | None = None` to ArcThread. Delete coercion validators `_map_thread_id_to_id()` and `_coerce_drift_analysis()`. |

**Why first:** Everything downstream depends on these types. No other changes are safe until this is done.

### Phase 2: Engine Layer — Shared Thread Lifecycle Logic

**Scope:** All files that process thread state mutations. Changes here affect how threads move between states (active/latent/completed). Affects both narrator context and extraction processing since they share the same arc state.

| File | Change |
|------|--------|
| `ccya/engine/turn.py` | Delete import of `ThreadSignalType`. Reduce `_ACTIVE_THREAD_CAP = 4` → **3**. Rewrite `_apply_thread_signals()` (~70 lines replaced): parse `advanced_threads` as list[str], increment progress for listed IDs, demote silent threads (5+ turns) to latent with state=latent, complete at threshold 3. Add 3-turn promotion cooldown via `arc_last_promotion_turn`. Modify `_candidate_to_latent_thread()` — add check that only creates new candidates if `turn_no - arc_last_promotion_turn >= 3` OR no active slots available. Delete tick_arc call block (lines ~987-993). |
| `ccya/engine/arc.py` | Delete entire `tick_arc()` function (~25 lines). Keep `update_stances()` and `STANCE_KEYWORDS` — these serve a different purpose (PC emotional stances, unrelated to thread system). |

**Why together:** Both files mutate the same arc state. Any split would create inconsistent behavior. The shared context is "how does an active thread's progress get tracked?" — answered in one atomic change.

### Phase 3: Prompt Layer — Shared LLM Output Format

**Scope:** All prompt templates that describe what the LLM should output for threads. Changes here reduce token usage in both narrate and extract calls since they share the same extraction pipeline context. This is where we cut ~50% of thread-related LLM output.

| File | Change |
|------|--------|
| `ccya/prompts/extract_progress_system.j2` | Replace entire `thread_signals` section (lines 30-48) with simplified `advanced_threads` instructions. Delete entire `drift_analysis` section (lines 50-67). Delete `player_drift_signals` line (line 68). Update output schema example (lines 1-25): replace thread_signals/drift_analysis/player_drift_signals with just `advanced_threads`. Note: progress extractor prompt will show both active AND latent threads in context — instructions should mention that advanced_threads can reference any thread from either list. |
| `ccya/prompts/generate_seed_system.j2` | Strengthen Campaign Arc Generation section: add explicit thread quality rules requiring substantial medium-term goals. Threads must describe situations with inherent tension and stakes, not incidental narration details. Must have clear advancement criteria. Can sustain 5-10 turns of play. |

**Why together:** Both prompts serve the extraction pipeline. The system prompt defines output format; the seed generation ensures input quality. They're two halves of "good threads in → simple processing." Changing only one would create mismatch (strong seeds with weak instructions or vice versa).

### Phase 4: Context Building — Shared Presentation Layer

**Scope:** Files that build context dicts for prompts and UI. Changes here affect what data flows into both narrator and extractor calls. No new state schema changes — just filtering out removed fields. **Key change:** progress extractor now receives BOTH active AND latent threads in its context (narrator still only gets active).

| File | Change |
|------|--------|
| `ccya/engine/narrate.py` | Check if arc_engagement was included in arc context dict for narrate prompts. If present, remove it. Keep all other arc context (visible_goal, thematic_question, active_threads, pc_drive, hidden_truths). Only active_threads should be shown — verify latent threads are not already being passed. Narrator prompt gets ONLY `active_threads` from arc. |
| `ccya/engine/turn.py` (context building for progress extractor) | When building context dict for the progress extraction LLM call, include BOTH `arc.active_threads` AND `arc.latent_threads`. The extract_progress_system.j2 template already expects a threads list — update it to render both active and latent sections. Active section labeled "ACTIVE THREADS" (for advancement tracking). Latent section labeled "LATENT THREADS" (for re-engagement detection). |
| `ccya/state/delta.py` | Verify `_merge_arc_update()` doesn't have any special handling for arc_engagement or thread_signals. If present (unlikely since merge is generic CampaignArc), remove. No changes expected if _merge_arc_update handles CampaignArc generically via model_dump. |

**Why together:** Both files serve the "what gets shown" layer. Narrate.py builds context for LLM calls; delta.py persists state mutations. They're connected because what narrate.py reads must match what delta.py writes. Any mismatch would cause stale data in prompts. The new dual-context (active-only for narrator, active+latent for extractor) is a shared concern since both serve the extraction pipeline.

### Phase 5: UI Layer — Shared Display Context

**Scope:** All files that display arc/thread information to the player. Changes here are purely visual — no logic changes. If any phase before this had `arc_engagement` display code, it gets removed here.

| File | Change |
|------|--------|
| `ccya/templates/_state_left.html` | Check if there's any UI rendering of arc_engagement. If so, remove it. The rest of the arc card (goal, active threads with urgency coloring, discovered truths collapsible, completed log) stays unchanged. No changes expected — arc_engagement may not be displayed in current template. |

**Why last:** UI is purely consumer-facing. Any logic change before this makes UI changes irrelevant or wrong. UI should always reflect the final state of all other layers.

### Phase 6: Test Cleanup — Delete + Rewrite

**Scope:** All test files that reference removed types/functions. This phase has two sub-tasks: (a) delete tests for things that no longer exist, (b) rewrite remaining tests for new simplified format.

#### 6a. DELETE these tests (no longer needed):

| File | What to Delete | Reason |
|------|---------------|--------|
| `tests/test_arc.py` | Entire `TestEngagement` class (~80 lines, all tick_arc tests) | tick_arc() deleted — engagement scoring removed entirely |
| `tests/integration/test_arc.py` | Entire `TestArcEngagement` class (lines 246-279) | arc_engagement/tick_arc gone. Also delete the `assert "arc_engagement" in final["arc"]` assertions scattered throughout all other test classes (~10 occurrences). |
| `tests/test_models.py` | Entire `TestDriftAnalysisCoercion` class (lines 231-252) | DriftAnalysis model deleted. Any drift_analysis validation tests. |
| `tests/test_models.py` | Entire `TestThreadSignalMatchCoercion` class (lines 254-280ish) | ThreadSignal/ThreadSignalType models deleted. All coercion logic for old signal patterns removed. |
| `tests/integration/conftest.py` | `"arc_engagement": 0` from arc fixture helper (line 270) | Field no longer exists on CampaignArc. Any drift_analysis or thread_signals default params in progress_response(). |

#### 6b. REWRITE these tests:

| File | What to Change |
|------|---------------|
| `tests/test_arc.py` | Rewrite all `_apply_thread_signals` test methods (TestThreadAdvancement, TestThreadPromotion, TestThreadCompletionState, TestThreadPromotionUnlockIf) to use new format. Replace `thread_signals=[_signal("t1", "advanced")]` with a ProgressResult that has `advanced_threads=["t1"]`. Delete all `_signal()` helper and ThreadSignal imports. Add tests for 5-turn expiry (demote to latent). Add test for 3-turn promotion cooldown. |
| `tests/integration/test_arc.py` | Replace ALL `"thread_signals": [{"id": "...", "signal": "..."}]` patterns with `"advanced_threads": ["..."]`. Update all progress_response() calls. Fix thread completion threshold tests (still need 3 advances). Keep latent promotion, candidate_opportunity, and narrator arc_update tests — just update format. |
| `tests/test_extraction.py` | Delete `test_progress_result_includes_drift_analysis()` (line 184-193) — drift analysis removed. Any other progress extraction tests that reference old thread signal formats need updating. |
| `tests/test_eval.py` | Update `test_check_asserts_thread_signals_found()` (line 498-503): change from checking `thread_signals` field to checking `advanced_threads`. The TurnAssert check needs the new field name. |
| `tests/test_engine_pipeline.py` | Update `test_progress_prompt_contains_thread_signals()` (lines 512-520): assert `"advanced_threads"` in prompt text instead of `"thread_signals"`. The prompt still has thread-related instructions, just under a different field name. |

**Why last:** Tests must match the code. Any test changes before Phase 3 would fail because the old output format is still expected. After all other phases are done, tests need updating to match new reality.

---

## Detailed Changes by File (Phase 1: Model Layer)

### `ccya/models.py` — Complete model simplification

**Delete these types:**
- `ThreadSignalType` enum (lines 30-34): all 4 values (`ADVANCED`, `BLOCKED`, `FAILED`, `IGNORED`) serve no purpose in simplified system. Any thread not listed as advanced is implicitly ignored. No need for explicit signal types.
- `ThreadSignal` model (lines 82-84): `{id, signal}` — replaced by simple string IDs in list. The structuring overhead (`signal` field with enum validation) adds nothing when all we care about is "was this thread touched?"
- `DriftAnalysis` model (lines 87-95): per-thread engagement analysis. Generates ONE entry per active thread — massive output for zero mechanical effect. Engagement tracking removed entirely.

**Delete these fields from ProgressExtractResult:**
- `thread_signals: list[ThreadSignal]` → replaced by `advanced_threads: list[str] = Field(default_factory=list)` (simple string IDs)
- `drift_analysis: list[DriftAnalysis]` → entire field gone. No engagement tracking.
- `player_drift_signals: list[str]` → deprecated legacy, already superseded by drift_analysis which is now also deleted.

**Delete these validators from ProgressExtractResult:**
- `_map_thread_id_to_id()` (entire method): handles 8+ different LLM output patterns for old thread_signal format (`match→signal`, `advanced→signal`, `status→signal`, various id field names). All vestigial — new format is just a list of strings. Pydantic enforces type automatically.
- `_coerce_drift_analysis()` (entire method): drift analysis gone, coercion logic irrelevant.

**Delete from CampaignArc:**
- `arc_engagement: int` (was -3..+3). Nothing downstream reads it except UI display. Engagement tracking removed entirely — if needed in future, data is available in narration text.

**Add to ArcThread:**
- `last_seen_turn: int | None = None`. Engine sets this each turn for threads appearing in advanced_threads. Used by 5-turn expiry check. When a thread is demoted from active → latent after expiry, reset to None.

**Keep on CampaignArc (unchanged):**
- `visible_goal`, `thematic_question`, `hidden_truths`, `discovered_truths` — all serve meaningful purposes in narration context.
- `active_threads: list[ArcThread]` — only these reach prompts. Max 3.
- `latent_threads: list[ArcThread]` — pack-seeded and tactical candidates. Invisible in prompts. Expired threads demote here.
- `completed_threads: list[ArcThread]` — complete/failed/expired. UI display only.
- `pc_drive` — PC motivation, feeds into narration context.

**Keep on ArcThread (unchanged):**
- `id`, `summary`, `tags`, `state`, `urgency`, `progress`, `unlock_if`, `promotes`, `last_offered_turn` — all serve meaningful purposes in thread lifecycle.

---

## Detailed Changes by File (Phase 2: Engine Layer)

### `ccya/engine/turn.py` — Thread lifecycle rewrite

**Delete:**
- Import of `ThreadSignalType` from models (line 45). No longer needed.
- Current `_apply_thread_signals()` function (~70 lines, starts at line 79): complete rewrite. The old logic handles individual signal types (ADVANCED/BLOCKED/FAILED) which no longer exist.

**New constants:**
```python
_ACTIVE_THREAD_CAP = 3  # reduced from 4
```

**Rewrite `_apply_thread_signals(state, progress_result)` — new logic:**

```python
def _apply_thread_signals(
    state: dict[str, Any],
    progress_result: Any,
) -> CampaignArc | None:
    """Process simplified advanced_threads list.
    
    Any active thread NOT in the list is implicitly ignored.
    After 5 consecutive turns without being listed → demote to latent.
    Threads with progress >= _THREAD_COMPLETION_THRESHOLD (3) → complete.
    Promote latent threads if slots available and 3-turn cooldown met.
    """
```

Key logic:
1. Parse `progress_result.advanced_threads` as list of thread ID strings. If empty or None, treat as [].
2. Build set of advanced IDs for this turn.
3. For each active thread:
   - **If in advanced set** → increment progress by 1, reset `last_seen_turn = current_turn_no`. Thread stays active.
   - **If NOT in advanced set AND (`last_seen_turn` is None or `turn_no - last_seen_turn >= 5`)** → demote to latent (remove from active_threads, add to latent_threads with state=latent). This frees a slot for future promotion. Reset `last_seen_turn = None`.
   - **If NOT in advanced set AND `0 < turn_no - last_seen_turn < 5`** → thread stays active but no progress change. Timer continues ticking.
4. Move any thread where `progress >= _THREAD_COMPLETION_THRESHOLD (3)` to completed_threads with state=COMPLETE. Remove from active_threads.
5. **Promotion check:** If there are available slots in active_threads AND (`arc_last_promotion_turn` is None OR `turn_no - arc_last_promotion_turn >= 3`):
   - Find latent threads with empty or satisfied `unlock_if`. Sort by `last_offered_turn` (oldest first).
   - Promote up to available slot count. Update their state to ACTIVE, set `last_seen_turn = turn_no`, update `arc_last_promotion_turn = turn_no`.
6. Return mutated CampaignArc if any changes occurred.

**Modify `_candidate_to_latent_thread(arc, candidate, turn_no)`:**
- Keep existing logic (cap enforcement, tactical tag eviction).
- Add check at start: only create new latent threads from candidates if `turn_no - arc_last_promotion_turn >= 3` OR all active slots are full. This prevents flooding with too many candidates between promotion cycles. If the check fails and there's room in latent pool (below _LATENT_CAP), still add it — just don't count toward future promotions until cooldown expires.

**Delete tick_arc call block (around lines 987-993):**
```python
# Delete these lines entirely:
if state.get("arc"):
    arc = tick_arc(
        arc=CampaignArc(**state["arc"]),
        drift=progress_result.player_drift_signals,
        drift_analysis=progress_result.drift_analysis,
    )
    state["arc"] = arc.model_dump(mode="json")
```

### `ccya/engine/arc.py` — Delete engagement scoring only

**Delete:** Entire `tick_arc()` function (lines 32-67). Engagement tracking removed. The function's sole purpose was updating `arc_engagement` based on drift overlap with thread tags. Nothing downstream reads arc_engagement for any meaningful behavior.

**Keep:** `update_stances()` and `STANCE_KEYWORDS`. These serve a different purpose — tracking PC emotional stances (compassionate/ruthless/defiant/cautious) from player input. Completely unrelated to thread system. Called separately in turn.py line 997. Can stay in arc.py since it's arc-related.

---

## Detailed Changes by File (Phase 3: Prompt Layer)

### `ccya/prompts/extract_progress_system.j2` — Simplify output instructions

**Replace the entire thread_signals section (lines 30-48):**

Old instruction set explaining 4 signal types with examples and CRITICAL warnings about field schema mixing.

New instruction:
```
advanced_threads: A list of snake_case thread IDs that were meaningfully advanced this turn. 
If no threads (active or latent) were touched, emit an empty array [].
Each ID must match exactly the id from either the active_threads or latent_threads lists in context.

CONTEXT NOTE for LLM: You will see two sections — ACTIVE THREADS and LATENT THREADS.
- Active threads are currently pressing storylines. Advancing them keeps momentum.
- Latent threads are dormant but still relevant. Re-engaging one signals it should be promoted back to active.
- Include a thread ID if this turn's events DIRECTLY advanced that specific thread, whether from either section.

Example output: ["the_missing_ore", "fraying_rigging_and_broken"]

CRITICAL RULES for including a thread ID:
- Include ONLY if this turn's events DIRECTLY advanced that specific thread. 
  The player took meaningful action toward it. A check was rolled on it, or its 
  narrative arc clearly progressed.
- Do NOT include threads merely mentioned in narration. Mentioning ≠ advancing.
- Do NOT include threads present as background. Presence ≠ advancement.  
- If uncertain whether a thread was advanced — do not include it. Under-inclusion 
  is better than false positives. The 5-turn expiry timer will handle dormant threads.
```

**Delete the entire drift_analysis section (lines 50-67):** This entire block explaining per-thread match/reason/new_interest output. Gone. No engagement tracking.

**Delete `player_drift_signals` line (line 68):** Deprecated legacy field. Gone.

**Update output schema example (top of file, lines 1-25):** Replace these three fields in the JSON schema:
```json
"thread_signals": [...],
"drift_analysis": [...],  
"player_drift_signals": []
```
With just:
```json
"advanced_threads": ["thread_id_1", "thread_id_2"]
```

**Keep unchanged:** `candidate_opportunity` section. Candidates still serve a purpose — introducing new latent threads from narration events. The 3-turn cooldown in engine prevents flooding.

### `ccya/prompts/generate_seed_system.j2` — Strengthen thread quality

Add explicit requirements under "Campaign Arc Generation" (around lines 116-133):

```
Thread quality rules:
- Threads must be substantial medium-term goals capable of sustaining 5-10 turns. 
  They represent ongoing narrative arcs, not single events or observations.
- Each thread should describe a situation with inherent tension and stakes — something 
  that naturally escalates over time. Not a static fact.
- Do NOT generate threads from incidental narration details (a character's cough, 
  dust in the air, passing weather). These are atmospheric, not narrative.
- DO generate threads from plot-relevant developments: threats emerging, alliances 
  forming, discoveries made, consequences of player actions.
- Threads must have clear advancement criteria — what would make progress on this thread? 
  If you can't describe what "advancing" looks like for a thread, it's not ready to be one.
```

**Keep unchanged:** Thread summary examples (good/bad). They already illustrate the right pattern. Just reinforce with explicit rules.

---

## Detailed Changes by File (Phase 4: Context Building)

### `ccya/engine/narrate.py` — Filter out removed fields from arc context, active-only for narrator

Check what arc context is built for narrate prompts. If `arc_engagement` was included in the context dict passed to templates, remove it. The rest of the arc context (`visible_goal`, `thematic_question`, `active_threads`, `pc_drive`, `hidden_truths`) stays. **Only active_threads should be shown** — verify latent threads are not already being passed (they shouldn't be). Narrator prompt gets ONLY `active_threads` from arc.

### Context building for progress extractor in `ccya/engine/turn.py` — include both active AND latent threads

When the context dict is built for the progress extraction LLM call, include BOTH `arc.active_threads` and `arc.latent_threads`. The extract_progress_system.j2 template will need to render two sections:
- "ACTIVE THREADS" section — all currently active threads (for advancement tracking)
- "LATENT THREADS" section — all dormant but still-relevant threads (for re-engagement detection)

This is the key change in Phase 4. The engine's context-building code needs to pass both lists so the LLM can see and potentially advance latent threads. Template changes are handled in Phase 3.

### `ccya/state/delta.py` — Verify no special handling for removed fields

The `_merge_arc_update()` function handles CampaignArc mutations generically via model_dump. No changes expected since it doesn't have field-specific logic for arc_engagement or thread_signals. Just verify during implementation. If any special handling exists (unlikely), remove it.

---

## Detailed Changes by File (Phase 5: UI Layer)

### `ccya/templates/_state_left.html` — Remove arc_engagement display if present

Check lines 99-153 for any rendering of `arc_engagement`. If found, remove. The rest of the arc card stays unchanged:
- Goal displayed in `.arc-goal` div with markdown rendering ✓ (keep)
- Active threads list colored by urgency ✓ (keep — only active_threads shown anyway)  
- Discovered truths collapsible section ✓ (keep)
- Completed threads log ✓ (keep — expired threads demoted to latent, not complete. Only truly complete/failed appear here.)

**Expected:** No changes needed. arc_engagement may not be displayed in current template since it had no meaningful consumer.

---

## Test Cleanup Summary (Phase 6)

### Files with tests to DELETE entirely:
- `tests/test_arc.py`: `TestEngagement` class (~80 lines, all tick_arc/engagement tests) — engagement scoring removed
- `tests/integration/conftest.py`: `"arc_engagement": 0` from arc fixture (line 270), any drift_analysis/thread_signals default params in progress_response()

### Files with scattered assertions to REMOVE:
- `tests/integration/test_arc.py`: All `"arc_engagement": 0` entries in test fixtures (~10 occurrences across all classes). Delete the `assert "arc_engagement" in final["arc"]` assertion (lines 278-279).

### Files with tests to REWRITE:
- `tests/test_arc.py`: All `_apply_thread_signals` methods — replace ThreadSignal format with advanced_threads list. Add expiry and cooldown tests. Delete all ThreadSignal/ThreadSignalType imports.
- `tests/integration/test_arc.py`: Replace ALL `"thread_signals": [{"id": "...", "signal": "..."}]` patterns with `"advanced_threads": ["..."]`. Keep test structure (completion threshold, latent promotion, candidate_opportunity) — just update data format.
- `tests/test_models.py`: Any ProgressExtractResult validation tests for old thread signal/drift analysis formats. Add validation test for new `advanced_threads: list[str]` field.
- `tests/test_extraction.py`: Delete drift_analysis test (line 184). Update any other progress extraction references.
- `tests/test_eval.py`: Change TurnAssert check from `thread_signals` to `advanced_threads`.
- `tests/test_engine_pipeline.py`: Assert `"advanced_threads"` in prompt text instead of `"thread_signals"`.

### Files with NO changes needed:
- `tests/integration/test_compactor.py`: No arc_engagement or thread_signal references found. Compactor's thread_cleanup instruction stays the same (check for stale threads — engine handles expiry).

---

## What Gets Simpler for the LLM

The progress extractor's thread-related job goes from:
- **Before:** "For each active thread (potentially 4), determine if it was advanced/blocked/failed/ignored. Then separately, for EACH of those same threads, produce a drift_analysis entry with match/reason/new_interest. That's potentially 8 structured outputs about the same threads."
- **After:** "List which threads were advanced this turn. Empty list = none. Simple array of strings."

This eliminates roughly 50% of thread-related LLM output per turn (the entire drift_analysis section). The extraction prompt for progress stream shrinks significantly — no more explaining 4 signal types, no more drift analysis schema, no more CRITICAL warnings about mixing field schemas.

---

## Edge Cases & Decisions

1. **Thread expiry timing:** 5 consecutive turns without being in `advanced_threads` list. Narration mention alone doesn't prevent expiry — only appearing in the extraction output resets the timer. Intentional: if player isn't actively working on a thread, it should expire.

2. **New threads with no prior history:** A newly promoted latent thread has `last_seen_turn = None`. Engine treats this as "seen this turn" for first turn after promotion. Timer starts ticking from next silent turn.

3. **Candidate_opportunity interaction:** Candidates still enter the latent pool whenever narration introduces something interesting. The 3-turn cooldown only applies to PROMOTION (latent → active). Candidates accumulate in latent; they just wait for their slot. This is fine — with _LATENT_CAP = 4 and tactical eviction, old candidates get pruned naturally.

4. **Thread completion threshold:** Kept at 3 advances. A thread needs 3 meaningful player actions targeting it before completing. Not too fast (2), not too slow (5). Matches user's "meaningful progress" requirement.

5. **Expired threads in UI:** Expired threads demote to latent, NOT complete. They won't appear in the completed log — they're just removed from active_threads and sit quietly in latent pool. If later promoted again, they start fresh. No special notification needed per user request ("expire quietly").

6. **Backward compatibility on old saves:** Old save files will have `thread_signals`, `drift_analysis`, `player_drift_signals` fields. Since ProgressExtractResult has `model_config = {"extra": "ignore"}` (line 371), these extra keys are silently ignored during validation. State files with arc_engagement will just have an extra field ignored on load since state loading doesn't re-validate against CampaignArc schema.

---

## Implementation Order Summary

```
Phase 1: Model Layer          → ccya/models.py (foundational types)
     ↓
Phase 2: Engine Layer         → turn.py + arc.py (thread lifecycle logic)  
     ↓
Phase 3: Prompt Layer         → extract_progress_system.j2 + generate_seed_system.j2 (LLM output format)
     ↓
Phase 4: Context Building     → narrate.py + delta.py (filter removed fields from context)
     ↓
Phase 5: UI Layer             → _state_left.html (remove arc_engagement display if present)
     ↓  
Phase 6: Test Cleanup         → all test files (delete obsolete, rewrite for new format)
```

Each phase depends on the previous one. Phase 1 changes must land before any downstream code compiles. Phases 2-3 can be reviewed together since they're closely coupled (engine processes what prompts produce). Phase 4 is a light validation pass. Phase 5 is cosmetic. Phase 6 makes all tests match new reality.

---

## Risks & Mitigations

1. **Risk:** LLM might not produce clean simple output with just a list of IDs.  
   **Mitigation:** Extraction retry logic already handles parse failures. Pydantic enforces `list[str]` type automatically. If the LLM produces old-format output, it will fail validation and trigger a retry.

2. **Risk:** 5-turn expiry might feel too aggressive for some narrative arcs.  
   **Mitigation:** This is configurable if needed later. For now, 5 turns = about 1-2 minutes of real play. If threads are substantial (per strengthened seed requirements in Phase 3), they should naturally attract player attention.

3. **Risk:** Removing all engagement tracking means losing a potential future feature.  
   **Mitigation:** Engagement scoring was never used for anything meaningful. The only consumer was UI display. Can always add it back if needed — the data is still available in narration text, just not pre-computed.

4. **Risk:** Expired threads demoted to latent could be promoted again prematurely.  
   **Mitigation:** 3-turn cooldown prevents rapid cycling. A dormant thread would need 3 silent turns before being eligible for promotion. If it was already ignored for 5+ turns, another 3 turns of silence is reasonable — the player had time to notice and act.

5. **Risk:** Resurfacing dormant threads via compactor adds complexity.  
   **Mitigation:** Compactor's thread_cleanup instruction already handles latent threads. No new logic needed — just lift a dormant latent thread if bulletin bullets mention its topic. This is Phase 3+ future work; for now, expired threads simply sit in latent pool and get evicted by tactical cap pressure.
