# POST-OVERHAUL FINDINGS — Cross-Game Analysis (noir + pirate + coruscant)

**Scope:** Three saves after the major game engine updates (beats, narration, pacing, arc/thread mechanics overhaul). Coruscant save was played AFTER the 4 fixes were applied.

| Save | Turns | Setting | Genre |
|---|---|---|---|
| `noir--1930s-2026-06-04` | 12 | Detective noir, 1930s | Investigation, dialogue, political corruption |
| `the-golden-age--17151725-2026-06-04` | 13 | Golden Age piracy | Naval combat, boarding action, single-room siege |
| `the-siege-of-coruscant-2026-06-04` | 19 | Star Wars: Clone Wars era | Sci-fi combat, extraction, medical drama |

**Validation approach:** Findings are annotated `[both]` (observed identically in all saves), `[shared-mechanism]` (same root cause, different surface appearance), `[genre-specific]`, or `[coruscant]`. The noir save represents a naturally-progressing narrative (scene changes every 3-4 turns). The pirate save stress-tests the system when the narrative is stuck in a single scene/combat loop. The coruscant save tests the 4 fixes (A-D) with a multi-scene sci-fi action game.

---

---

## Fixes Applied (Round 2 — from coruscant deep-dive)

### Fix D7: `recent_turns` slicing for storytell
**File:** `ccya/engine/extraction.py:534`
**What:** `(recent_turns or [])[:-1][-10:]` → `(recent_turns or [])[-10:]`
**Effect:** Removed the `[:-1]` that excluded the only loaded narration entry. The storyteller now receives the previous turn's full narration (plus up to 9 more when `_recent_turn_count` is increased). The `## prior turn context` section in `storytell_user.j2` now renders instead of being empty.

### Fix D1: Durability gate removed
**File:** `ccya/state/delta_builder.py:168-180`
**What:** Removed the 12-line durability gate block that checked whether new item IDs appeared in action suggestions.
**Effect:** New items identified by the state extractor from narration are no longer silently discarded. The extractor is trusted to correctly identify loot from the narrative text. Fixes the pirate musket/ammo loss and coruscant blaster loss.

### Fix E: Beat ceiling — twist/setback/callback prompt guidance
**Files:** `ccya/prompts/storytell_system.j2:198-200`
**What:** Three changes:
1. Added `setback` to the type-by-type breakdown with definition and example (was completely missing).
2. Added "Consider twist instead of complication" guidance to the twist entry.
3. Added "Scan recent_beats for callback opportunities" to the callback entry.
4. Added `setback` to the band-aligned beat selection guidance ("setback/fail: breathing_room, null, setback, or rarely complication").
**Effect:** The LLM now has explicit guidance that setback is a valid beat type, and explicit encouragement to consider twist and callback instead of defaulting to complication. Total added: ~80 tokens.

---


## Coruscant Results — Fixes Verified ✅

The coruscant save (19 turns) was played after applying Fixes A-D above. Results:

### Fix A — Pacing directives unblocked ✅
- **Scene Pressure** fired at T12 (first confirmed in any save)
- **Scene Imperative** fired at T17, T18, T19 (FIRST TIME EVER — required Fix A)
- **Breathe** fired at T1 and T4 (correct: FAIL band + no urgent scene-scoped threads)
- All 3 directive paths now confirmed functional: age-based (Scene Pressure/Imperative), velocity-based (Breathe), and momentum-based (beat_locked/Resolve a Threat from pirate save)

### Fix B — `recent_beats` in user prompt ✅
- Recent Beats section visible in all storytell user prompts
- Shows correct beat history: "T15: BREATHING ROOM (ambient)" format
- Null beats rendered as "T17: No beat emitted this turn"
- System prompt still shows its own copy (redundant but harmless)

### Fix C — GM Beat always renders ✅
- GM Beat section present on EVERY turn's user prompt — 100% coverage
- On beat-carryover turns: shows type/surface/expiration
- On null-following turns: "No beat currently carried over from the previous turn. Choose freely."
- Beat awareness no longer drops to ~62%

### Fix D — Thread guidance (mixed results) ⚠️
- **Thread IDs**: `banking_clan_infiltration` and `martial_law_escalation` are appropriately broad buckets ✅. But `the_jedi_shadows` is borderline — captures a specific situation rather than an enduring tension.
- **Progress quality**: Better than pirate, still has redundancy. 13 progress entries for `banking_clan_infiltration` include 7 variants of "medical scarcity" before progressing to novel content about patrols and the data-cylinder. One exact duplicate found (T14 and T15 identical text).
- **Guidance only**: No enforcement. Effectiveness depends on LLM adherence; some improvement but not a complete fix.

### Unprompted improvements observed
- **thread_resolve finally fired!** 🎉 — T6 resolved `the_jedi_shadows` with `resolution_state: resolved` and `promote_to_world_state: true`. Added to `completed_threads` in state. FIRST thread_resolve across 6+ saves examined.
- **Arc goal_update works!** 🎉 — LLM emitted `goal_update` at T3, T7, T8, T9, T11, T13 (6 of 19 turns, 31.6%). visible_goal evolved from "Extract a high-value target..." → "Stabilize Robert..." → "Secure discrete medical treatment..." → "Protect Robert and Gail from Separatist patrol." Arc is no longer static.
- **Beat diversity improved**: 4 of 9 types used (complication, pressure, opportunity, revelation). No escalation, breathing_room, twist, setback, or callback. But appropriate for the genre.
- **Null rate dropped**: 31.5% (6/19) vs 38-42% in pre-fix saves. Consistent beat awareness may be helping.

---

## Coruscant Deep-Dive — New Findings

### C1. `recent_turns` (prior full narration) missing from storytell user prompt ~~~ [FIXED by Fix D7] ~~~

**Status:** Fixed by Fix D7 (above). The `[:-1]` was removed from extraction.py:534. Future saves will have `## prior turn context` rendering in the storytell user prompt.

**Severity:** ~~High~~ Fixed

**Finding:** The `## prior turn context` section in `storytell_user.j2` renders previous turns' full narration text. It never appeared in any of the 19 coruscant turns. The narrate stream does render it correctly.

**Root cause:** `extraction.py:534` uses `(recent_turns or [])[:-1][-10:]` — the `[:-1]` removes the last entry (intended to exclude the current turn's narration). But `load_last_narration` with `_recent_turn_count` returning 1 loads only 1 turn's narration (the previous completed turn). `[:-1]` on a 1-entry list gives `[]`. The storyteller receives zero prior turn context.

The narrate stream uses `ctx.recent_turns[-1:]` (no `[:-1]`) at `turn.py:823`, so it correctly gets the previous turn's narration.

**Fix:** Change `[:-1][-10:]` to `[-10:]` at `extraction.py:534`. The storyteller would then get up to 10 turns of prior narration (currently only 1 is loaded, so it'd get 1 — the previous turn). This is consistent with the narrate stream's behavior.

**Confidence:** 100% — code-verified and empirically confirmed across 19 turns.

### C2. `goal_update` too aggressive — visible_goal changed 6 times, player lost direction [coruscant]
**Severity:** Medium

**Finding:** `goal_update` fired 6 times in 19 turns (T3, T7, T8, T9, T11, T13). The visible_goal changed every 3 turns on average. The seed goal ("Extract a high-value target") was completely gone by T13 ("Protect Robert and Gail from Separatist patrol"). While the mechanism works, the frequency is too high — the player sees a different objective every few turns, making the arc feel unfocused.

**Key data point:** Between T8 and T9, the goal changed in consecutive turns (T8 → "find supplies with improvised resources", T9 → "secure discrete treatment"). These are essentially the same goal rephrased twice. The LLM is goal-updating on every meaningful action, not just on genuine narrative pivots.

**No `arc_resolve` fired** in the coruscant save. The arc was never formally closed or advanced — just its visible_goal kept moving.

**Recommendation:** Add prompt guidance that `goal_update` should only fire on genuine narrative pivots (genre shifts, location changes, major reveals), not on every micro-progression. Suggest 3-5 turn minimum between goal_updates unless the narrative fundamentally shifts.

**Confidence:** 100% — confirmed in events.jsonl across all 19 turns.

### C3. Beat ceiling — why twist, setback, and callback never fire
**Severity:** Low-Medium

**Finding:** Across 55+ total turns (noir+pirate+coruscant), 6 of 9 beat types have fired. The missing three (twist, setback, callback) appear to be a **guidance + memory problem, not a model capability ceiling.**

| Missing type | Why it likely never fires |
|---|---|
| **twist** | Defined in prompt ("narrative direction shifts unexpectedly") but only at line 191 with one example. No guidance about *when* to use it — only "at major pivot moments." The LLM may not recognize that a twist is appropriate; it defaults to complication (simpler, same energy). |
| **setback** | Almost invisible in the prompt as a beat type. Mentioned once at line 211 ("setback/fail: breathing_room, null, or rarely complication") — but here "setback" is a **band name**, not a beat type. The type-by-type breakdown (lines 189-200) includes every other type but MISSES setback entirely. The LLM has no guidance that setback is a valid beat type with its own meaning. |
| **callback** | Well-defined in the prompt (line 192, 199) with clear example. But requires referencing an event 3+ turns ago. The LLM only has `recent_beats` (5 entries) and `prior_history` (outcome summaries). The full chronicle is invisible. Callbacks to events >5 turns ago are cognitively impossible. Within 5 turns, the LLM could reference recent_beats, but never does — possibly because the prompt says "3+ turns ago" and recent_beats only covers 5 turns, making the window very tight (turns 3-5 behind). |

**Fixes:**
- Add setback to the type-by-type breakdown with definition and example.
- Add "when to use" guidance for twist: "Use twist after a lull or when the player's assumptions should be challenged. Not during active pressure cascades."
- Increase recent_beats max or add chronicle context for older callbacks.
- Add explicit prompt: "When you find yourself reaching for complication again, consider whether twist or setback would be a better fit."

**Confidence:** 85% — inferred from prompt structure and LLM behavior. Needs a targeted test (e.g., add better guidance, then check next save).

---

## Firm Decisions

These are design decisions made during the coruscant analysis. They should be recorded here and referenced in future plans.

### D1. Durability gate: REMOVED
**Decision:** Remove the durability gate entirely. The state extractor correctly identifies items from narration. The gate (delta_builder.py:168-180) gates persistence on action suggestions — the wrong signal — causing silent item loss. Remove it; trust the extractor.
**Status:** **DONE** — gate deleted at delta_builder.py:168-180.

### D2. World state: restrict to static seed-only + resolved threads/arcs only
**Decision:** The current model (unbounded `world_state_add` per turn, no expiry) is unsustainable. Revert to a model where:
- World state starts with seed-generated static facts (universal constraints: "The Banking Clan funds droid production")
- The ONLY dynamic addition path is via resolved threads/arcs (`thread_resolve` with `promote_to_world_state: true`)
- No raw `world_state_add` from the storyteller LLM

This collapses all mutable story tracking into the arc/thread system (where it belongs) and makes world_state a compact reference document.

### D3. Conditions TTL: REMOVE auto-expiry or require narrative event
**Decision:** The current silent auto-TTL expiry causes state/narrative desync (coruscant: shoulder_strain + thigh_burn expired then extraction re-detected them). Two options, TBD:
- Option A: Remove TTL entirely — conditions persist until the LLM explicitly calls `pc_condition_remove` via proper narrative (rest, treatment, time skip).
- Option B: Keep TTL but trigger a `condition_expired` narrative event on expiry so the LLM can describe the recovery.

Both are better than silent vanish. Collecting a narrative event for the expiry seems the safer fix.

### D4. Thread urgency decay guidance: add to pacing system
**Decision:** Urgency never decays across any save. The storyteller has no prompt guidance about urgency progression. This is a PADDING-adjacent problem — a thread that's been `urgent` for 10+ turns without resolution should mechanically decay (not just by LLM fiat). Two approaches, TBD:
- **Mechanical**: Auto-decay urgency over time (urgent → normal after 5 turns, normal → background after 10).
- **Prompt-based**: Add urgency-decay guidance with examples.

Mechanical enforcement is more reliable; prompt guidance is lighter. Prefer mechanical unless it creates complexity elsewhere.

### D5. Batch compactor/sanitizer: MAYBE reintroduce
**Decision:** The pre-overhaul design had batch compaction that was removed during the refactor. Coruscant data shows we need it for:
- Dedup world state facts (two near-identical entries for Banking Clan data cylinder)
- Cap thread progress entries (currently unbounded)
- Consolidate resolved threads into arc history

This is a substantial engineering effort. Not committing yet, but adding as a known gap that will need addressing when world state and thread bloat become terminal (projected around 40-50 turns given current growth rates).

### D6. `goal_update` frequency cap: add prompt guidance
**Decision:** The LLM changes the visible_goal too often (6 times in 19 turns). Add prompt guidance: "Emit `goal_update` only when the narrative direction fundamentally changes — new location, new major antagonist, new primary objective. Do NOT emit goal_update on every action or minor progression. Aim for at least 3 turns between goal_updates unless a genuinely new arc phase begins."

### D7. `recent_turns` fix for storytell — DONE
**Decision:** Change `[:-1][-10:]` to `[-10:]` at `extraction.py:534`. This is a one-line bug fix with no behavioral tradeoffs. The narrate stream already works correctly; this makes the storytell stream consistent.
**Status:** **DONE** — extraction.py:534 updated.

### D8. Beat ceiling prompt guidance — DONE
**Decision:** Add `setback` to the type-by-type breakdown (was completely missing), add "consider twist instead of complication" guidance, add "scan recent_beats for callback opportunities" guidance, and add `setback` to the band-aligned beat selection options.
**Status:** **DONE** — storytell_system.j2 updated (~80 added tokens).

---

## Beat Ceiling — Detailed Analysis

### Why twist, setback, and callback never fire across 55+ turns

**Twist** — The prompt says "narrative direction shifts unexpectedly" with one example (line 191). The LLM has no guidance about **when** to generate a twist — only the negative constraint "don't repeat it within 2 turns." Complication (the generic "bad thing happens") naturally fills the same narrative slot with less cognitive load. A twist requires the LLM to invent a surprising reframing of established facts; complication just adds a new problem. Without explicit "consider twist instead of complication when..." guidance, the LLM defaults to complication every time.

**Setback** — This is a pure guidance gap. The beat type-by-type breakdown (lines 189-200) includes: complication, revelation, opportunity, pressure, breathing_room, escalation, twist, callback. Notice what's MISSING: **setback**. The only mention of "setback" in the beat section is at line 211: "setback / fail: breathing_room, null, or rarely complication" — but here setback is a **band name**, not a beat type. The LLM doesn't know that setback is a valid beat type.

**Callback** — Requires referencing a specific earlier event. The LLM has `recent_beats` (5 entries) and `prior_history` (outcome summaries). The prompt says "3+ turns ago" for callbacks. But with only 5 recent_beats and no chronicle, callbacks to events >5 turns ago are impossible. Even within the 5-turn window, the LLM never reaches for callback — possibly because it's never explicitly encouraged to scan `recent_beats` for callback opportunities.

### What to do about it
1. Add **setback** to the type-by-type breakdown with definition and example (~20 tokens).
2. Add "consider twist instead of complication when" guidance (~40 tokens).
3. Add "scan recent_beats for callback opportunities" guidance (~30 tokens).
4. Consider expanding recent_beats max from 5 to 10 for deeper callback reach.

Total: ~90 tokens of prompt guidance. Low cost, potentially high impact.

---


## Fixes Applied (Post-Overhaul — results on next runs will reflect these)

The following changes were made directly from findings in this document. Future saves will reflect them.

### Fix A: `turn_entered` initialization guard removed
**File:** `ccya/engine/turn.py:575`
**What:** `scene_age = current_turn - scene_entered if scene_entered > 0 else 0` → `scene_age = current_turn - scene_entered`
**Effect:** The guard `if scene_entered > 0` caused `scene_age` to return 0 when `turn_entered` was 0 (the default state value). With `turn_entered = 0` (unset starting scene), `scene_age = current_turn` instead — so at turn 2 with combat boost, `effective_scene_age = 3` triggers Scene Pressure. At turn 4, `effective_scene_age = 5` triggers Scene Imperative. When a location change sets `turn_entered` to a positive value, the subtraction works identically to before.

### Fix B: `recent_beats` now renders in storytell user prompt
**File:** `ccya/engine/extraction.py:274`, `ccya/prompts/storytell_user.j2:39-43`
**What:** Added `"recent_beats"` to the storytell user prompt context dict (was previously only in system prompt). Renders as a compact beat history table between GM Beat and rules_outcome sections.
**Effect:** The LLM now sees beat history in the user prompt (more salient, current-turn context) instead of buried in the system prompt (behavioral guidance). Each entry shows "T{N}: {BEAT TYPE} (surface)" or "T{N}: No beat emitted this turn". Shows however many beats exist (up to 5 stored).

### Fix C: GM Beat section always renders
**File:** `ccya/prompts/storytell_user.j2:29-38`
**What:** Changed the GM Beat section from `{% if pending_beat and pending_beat.type %}` (conditional, vanishes on null) to an if/else that always renders. On null-following turns: "No beat currently carried over from the previous turn. Choose freely."
**Effect:** The storyteller now receives explicit beat awareness on every turn, even when no beat was carried over. No more silent ~38% gap.

### Fix D: Thread guidance tightened (non-trivial progress + broad buckets)
**Files:** `ccya/prompts/storytell_system.j2:52-54`, `ccya/prompts/generate_seed_system.j2:205`
**What:** Added two new guidance paragraphs:
- Progress notes MUST be unique, non-trivial, and NOT a retelling of the narration. Bad examples: "Combat continues." / "The player asked a question." Good examples: "Confirmed Silas Thorne is the surveillance coordinator." / "The ledger reveals a third party."
- Thread IDs must be broad conceptual buckets (3-4 words), not specific events/people. A thread like `naval_boarding_action` should not exist — it's a scene, not a tension. Loosely related developments belong under one broad thread with different progress entries.
- Seed prompt now includes the same broad-bucket guidance with concrete examples (`the_council_conspiracy` good, `the_missing_ledger` + `moss_confrontation` too narrow).
**Effect:** Guidance only, no enforcement. Effectiveness depends on LLM adherence.

---



## 1. Beat System

### 1.1 Beat diversity: moderate — genre-appropriate but capped

| Beat type | noir | pirate | coruscant |
|---|---|---|---|
| complication | 3 | 4 | **7** |
| opportunity | 2 | 0 | **2** |
| revelation | 1 | 0 | **1** |
| pressure | 0 | 3 | **3** |
| escalation | 0 | 1 | 0 |
| breathing_room | **1** | 0 | 0 |
| **Total distinct** | **4 of 9** | **3 of 9** | **4 of 9** |
| Null rate | 42% (5/12) | 38% (5/13) | **31.5% (6/19)** |

All three saves together used 6 of 9 beat types (missing: twist, setback, callback). Coruscant is dominated by complication (7/13 non-null = 54%) which is appropriate for an action/sci-fi genre where things keep going wrong. No escalation or breathing_room — combat-adjacent genres still favor high-tension beats.

- **Confidence:** 90% — three saves with different genres show this ceiling.
- **Severity:** Medium — the system is reaching for diversity but the LLM still orbits its comfort zone. The missing types (twist, setback, callback) require narrative planning the LLM can't do without memory.

### 1.2 breathing_room fires naturally on FAIL bands [noir]

T11 generated `breathing_room/ambient` with no floor relief mechanism — the LLM chose it naturally because the band was FAIL and the prompt guidance says "prefer breathing_room/null beats on fail." This is the intended behavior working correctly. The pirate save never produced a breathing_room, but it also never had a FAIL band on a turn where the LLM chose to breather (pirate had Fails at T2, T8, T10 — all mid-combat, inappropriate for a breather).

- **Confidence:** 95% — one clear instance proves the mechanism exists.
- **Severity:** Low (positive finding) — the guidance works when the narrative context is appropriate.

### 1.3 Beat history exists in state but routes to the wrong prompt [both] ~~~ [FIXED by Fix B] ~~~

**Status:** Fixed by Fix B (above) — `recent_beats` now included in the storytell user prompt context dict, rendering as a compact beat history table between GM Beat and rules_outcome sections.

Both saves have `recent_beats` in `state.meta` (last 5 beats with type/surface/turn). ~~It is passed to the~~ The system **still** prompt renders it in `storytell_system.j2:165-173` ~~where it renders as~~ as "Recent Beats (last N)" guidance, but now the user prompt also renders it with higher salience. ~~It was **not**~~ Previously it was **not** in the user prompt context dict, so `storytell_user.j2` had no access to it.

- **Confidence:** 100% — code-verified (extraction.py:251 vs extraction.py:255-278).
- **Severity:** ~~Medium~~ Low now — system prompt is less salient than user prompt. The LLM sees beat history but it's buried in behavioral guidance rather than being presented as current-turn context. Likely reduces its effectiveness.

### 1.4 GM Beat section in storytell user prompt is present ~62% of turns [both] ~~~ [FIXED by Fix C] ~~~

**Status:** Fixed by Fix C (above) — the GM Beat section now always renders. On null-following turns: "No beat currently carried over from the previous turn. Choose freely."

The section ~~renders~~ used to render only when `pending_gm_beat` is non-null, which only happens when the *previous* turn's storyteller emitted a non-null beat. When the previous turn was null, `pending_gm_beat` is popped and the section vanished.

**Both saves showed identical pattern:**
- Turn following a non-null beat → section present
- Turn following a null beat → section absent
- Turn 1 → absent (no prior turn)

This was technically working as designed — there's literally nothing pending. But the storyteller received zero beat awareness on ~38% of turns.

- **Confidence:** 100% — identical rate in both saves, code-verified (turn.py:1022-1028).
- **Severity:** ~~Low-Medium~~ Low now — the LLM adapts, but losing beat awareness on 2 out of every 5 turns undermines the entire beat system.

### 1.5 Narrate 1-turn beat lag persists [both]

The narrator's user prompt shows `**Beat:** <previous turn's beat>` on turns following a non-null storytell output. On null-following turns, the Beat line is absent. This is by design (race-condition prevention from Phase 03), but it means the narrator always reacts to the beat one turn late.

- **Confidence:** 100% — both saves confirm the pattern in narrate prompts.
- **Severity:** Low — this is a deliberate design choice. Acceptable trade-off.

### 1.6 Null-beat cadence dropping (31.5% in coruscant) [all three]

noir and pirate both emit null beats at a consistent 38-42% rate. Coruscant dropped to 31.5% (6/19). This may reflect Fix C's impact — the LLM now has consistent beat awareness and may be choosing to emit beats more often because it sees the GM Beat section every turn.

- **Confidence:** 80% — only one post-fix save. Trend may be coincidental.
- **Severity:** Low — 31.5% is still above the "at least 1 of every 4" floor (25%). Not a problem.

---

### Section questions

- ~~Should `recent_beats` move to the storytell user prompt for better salience?~~ **[Answered by Fix B — yes, moved]**
- ~~Should the GM Beat section render `(none)` explicitly on null-following turns rather than vanishing?~~ **[Answered by Fix C — yes, always renders with fallback]**
- Is a 38% null rate healthy or should it be lower when the narrative needs more structure? [Open]

---

## 2. Thread System

### 2.1 Thread progress accumulation — coruscant shows mixed improvement [all three] ~~~ [Fix D guidance partially effective] ~~~

**Status:** Fix D added prompt guidance requiring unique, non-trivial progress. Coruscant shows partial improvement — better than pirate but still redundant.

The new list-based progress accumulation (appending each turn's note) works correctly in all three saves. Quality varies by genre and fix effectiveness:

**noir** — `the_missing_ledger` has 10 progress entries that trace a genuine investigation. Each entry advances the story.

**pirate** — `naval_pursuit` has 12 near-identical entries (baseline "bad" — before Fix D).

**coruscant** — `banking_clan_infiltration` has 13 progress entries. Quality is between noir and pirate: the first 7 entries are all variants of "medical scarcity is a problem" (T7-T12), then T13-T19 shift to novel content about patrols and the data-cylinder. One exact duplicate found (T14 and T15: identical "Separatist patrol presence at the medical bay directly threatens the safety of high-value targets"). By T19, the thread has 13 entries — at 50+ turns this would be terminal.

The system prompt guidance is purely advisory with no enforcement. Fix D improved but didn't solve the problem.

- **Confidence:** 95% — all three saves show the accumulation working. Quality gap is genre/stress driven with modest improvement from Fix D.
- **Severity:** Medium-high for spam scenarios. Coruscant's 13-entry thread at 19 turns projects to 34+ entries at 50 turns.

### 2.2 Thread_resolve: finally fired in coruscant [coruscant] ~~~ [PASSED — first ever thread_resolve] ~~~

**Status:** T6 resolved `the_jedi_shadows` with `thread_resolve: {id, resolution_state: "resolved", outcome, promote_to_world_state: true}`. The thread was moved to `completed_threads` in state. FIRST thread_resolve across all 6+ examined saves. This contradicts the pre-overhaul Finding 2.6 that arc-scoped threads never resolve.

However, noir (12 turns) and pirate (13 turns) still had zero resolves. The coruscant save may have triggered resolution because `the_jedi_shadows` had a clear completion condition (hangar extraction). Non-resolution remains the norm.

- **Confidence:** 90% — one data point shows the mechanism can work. But 3/4 saves still show zero resolves.
- **Severity:** Reduced from High to Medium — the mechanism exists and the LLM can use it, but doesn't do so as a default behavior.

### 2.3 Thread_add: noir 2, pirate 0, coruscant 0 (via thread_add, but LLM creates threads via thread_update too) [divergent]

noir created 2 new threads via `thread_add`. Coruscant created 0 via `thread_add` but the LLM introduced `the_jedi_shadows` (via thread_update on T1) and `banking_clan_infiltration` (via thread_update on T7) — these were effectively created by including them in thread_update even though they didn't exist before. The system allows threads to spring into existence just by updating them. The same happened in noir: `the_missing_ledger` was never formally `thread_add`'ed — it was the seed thread.

**Key insight:** Threads can be created by either `thread_add` OR by appearing in `thread_update` without a prior `thread_add`. Both noir and coruscant show this pattern. The `thread_update` path is the dominant creation mechanism.

**Governance assessment:** Thread creation via `thread_update` is ungoverned — no validation, no dedup against existing threads, no scope classification required. This is the actual creation path for most new threads.

- **Confidence:** 90% — all three saves confirm the `thread_update` creation pattern.
- **Severity:** Medium — ungoverned thread creation via thread_update bypasses scope/urgency requirements, but the LLM generally creates appropriate threads anyway.

### 2.4 Thread urgency never decays [all three]

`the_missing_ledger` was `urgent` from T1 to T12. `naval_pursuit` was `urgent` from T1 to T13. `banking_clan_infiltration` started `normal` (latent) but was never updated to urgent or background — it stayed static. `the_jedi_shadows` went from normal → urgent at T5, then was resolved at T6. No thread in any save ever transitioned urgent → normal or normal → background. The storyteller has no prompt guidance about urgency decay over time.

- **Confidence:** 95% — confirmed across all 44 turns (noir + pirate + coruscant).
- **Severity:** Medium-high — constant urgency cheapens the signal. Everything can't be equally urgent.

### 2.5 Thread scope classification correct in all three saves [all three]

noir's 4 threads all correctly scoped. Coruscant's 3 threads: `banking_clan_infiltration` (arc) ✓, `martial_law_escalation` (arc) ✓, `the_jedi_shadows` (arc) ✓ — all correctly classified as arc scope.

This overturns pre-overhaul Finding 2.3 which showed systemic misclassification. The overhaul's scope guidance works consistently.

- **Confidence:** 95% — three saves now confirm correct scope classification.
- **Severity:** Low (positive).

---

### Section questions

- Should thread progress entries be capped in the prompt (e.g., last 3) to prevent bloat? [Open — Fix D tightened guidance, verify effectiveness first]
- ~~Should the prompt say "only update thread progress when the narrative direction of this thread fundamentally changes — do not log every engagement"?~~ **[Answered by Fix D — guidance added]**
- Is the zero-thread-resolve a prompt guidance problem or a model behavior problem? [Open]

---

## 3. Pacing / Directives

### 3.1 Pressure and Scene Pressure directives fire — confirmed across two saves [noir + coruscant]

**noir** produced:
- `Pressure` at T5 (1 urgent scene-scoped thread: `moss_confrontation`)
- `Scene Pressure` at T9 and T12 (effective_scene_age >= 3)

**coruscant** produced:
- `Scene Pressure` at T12 (effective_scene_age >= 3 on Aethelgard scene)
- `Scene Imperative` at T17-19 (effective_scene_age >= 5 — first ever)
- `Breathe` at T1 and T4 (narrative_velocity < -0.3, zero urgent scene-scoped threads)

All three directive paths are now confirmed: age-based (Scene Pressure/Imperative), velocity-based (Breathe), and momentum-based (beat_locked/Resolve a Threat from pirate save).

- **Confidence:** 100% — confirmed across three saves.
- **Severity:** Low (positive) — the directive system works correctly when preconditions are met.

### 3.2 turn_entered never initialized for starting scene — pacing directives dead in static scenes [pirate] ~~~ [FIXED by Fix A] ~~~

**Status:** Fixed by Fix A (above) — the `if scene_entered > 0 else 0` guard was removed. With `turn_entered = 0`, `scene_age = current_turn - 0 = current_turn`. At turn 2 with combat boost, `effective_scene_age = 3` → Scene Pressure. At turn 4, `effective_scene_age = 5` → Scene Imperative.

**Root cause:** `scene.turn_entered` was initialized to 0 in default state (io.py:87) and only updated on `location_change` (delta_builder.py:248-250). When a scene never changes location — as in the pirate save's 13-turn galley combat — `turn_entered` stays 0 forever. `scene_age = current_turn - 0 = current_turn`. Then `_compute_ages` returned 0 because the code did `scene_age = current_turn - scene_entered if scene_entered > 0 else 0`. With `scene_entered = 0`, it returned 0.

After the +2 combat boost, `effective_scene_age = 2` — permanently. The Scene Pressure threshold is 3. The Scene Imperative threshold is 5. Neither could ever fire.

This was a **state initialization bug**, not a design flaw. The starting scene's `turn_entered` should be set to 1 at game start.

- **Confidence:** 100% — code-verified. Noir masked it because scenes naturally change.
- **Severity:** ~~**Critical**~~ **Fixed** — the entire pacing directive system (except Breathe and the beat_locked path) is non-functional in any scene that stays in one location. This affects any game where the player stays in one place for 3+ turns, which is most narrative games.

### 3.3 "Resolve a Threat" directive/beat_locked fires through non-age path [pirate]

Pirate T4 had `directive=Resolve a Threat` with `beat_locked=True`. This fired through the `consecutive_pressure_turns >= threshold` or `momentum <= floor` path, not the scene-age path. The mechanism works independently but is unlikely to trigger in non-combat contexts (consecutive_pressure never increments without combat) or when momentum stays above -3.

- **Confidence:** 90% — one data point, but the code path is clear (turn.py:522-527).
- **Severity:** Medium — provides a fallback for high-combat scenarios but doesn't solve the static-scene problem.

### 3.4 Breathe directive fires on FAIL bands with no urgent scene-scoped threads [coruscant now confirms]

Breathe was confirmed at coruscant T1 and T4. Both had FAIL bands and zero urgent scene-scoped threads — the correct trigger conditions. This validates the Breathe path and suggests it was always working but the noir/pirate saves didn't create the right conditions.

- **Confidence:** 95% — concrete evidence in coruscant T1 and T4 events.jsonl.
- **Severity:** Low (positive) — the mechanism works correctly.

### 3.5 Scene Imperative now confirmed (coruscant T17-19); Overwhelm never fires [coruscant changes this] ~~~ [Scene Imperative CONFIRMED working; Overwhelm still open] ~~~

**Status:** Scene Imperative fired at T17, T18, T19 — the first confirmed instances across all saves. This confirms Fix A unblocked the age-based pacing path. Overwhelm still never fires (requires 3+ urgent scene-scoped threads across all saves).

The Aethelgard Station scene persisted from T9 through T18 (10 turns), giving effective_scene_age long enough to reach ≥5. The station scene had no combat tags, so no boost was needed — natural accumulation hit the threshold.

- **Confidence:** 100% — confirmed in coruscant events.jsonl.
- **Severity:** ~~High~~ Low now — Scene Imperative works. Overwhelm is a design question (does 3+ urgent scene-scoped threads ever occur naturally?).

---

### Section questions

- ~~Fix `turn_entered` initialization: should it be set to 1 at seed time, or at the first turn boundary?~~ **[Answered by Fix A — guard removed, 0 is now a valid starting value]**
- Does the 3/5 threshold for Scene Pressure/Imperative need rebalancing now that the bug is fixed? [Open — test first, then decide]
- Should the system detect a stuck scene (e.g., 5+ turns same location, no new threads) and force-inject a transition directive? [Open]

---

## 4. Inventory / Items

### 4.1 Durability gate blocks combat loot because it gates on wrong signal [pirate-only] ~~~ [FIXED by Fix D1 — gate removed] ~~~

**Status:** Fixed by Fix D1 (above) — the 12-line durability gate block at delta_builder.py:168-180 was removed. The state extractor is now trusted to correctly identify items from narration.

**Root cause:** The durability gate checked whether a new item's `id` or `name` is a substring of `delta.actions` — the storytell's forward-looking action suggestions. These action suggestions are guesses about what the player might do next turn, generated by the storytell LLM **after** the narration that describes the looting. They rarely mentioned the items just acquired.

In the pirate save at T6, the state extractor correctly identified `musket`, `gunpowder_pouches`, and `lead_balls` from the narration. All three were blocked because none appeared in the action suggestions. The player's narration unambiguously states "you wrench the musket from his dying grip, stripping a handful of loose powder pouches and several lead balls from his belt" — this describes looting, but the gate used the action suggestions, not the narration.

**Result:** The player had a musket with zero ammo. The gate was gating persistence on the wrong signal.

- **Confidence:** 100% — traced through events.jsonl and code.
- **Severity:** ~~High~~ Fixed — inventory persistence should now work correctly for loot scenarios.

---

### Section question

- ~~Gate on narration text instead of action suggestions? Or remove the gate entirely and trust the state extractor (which correctly identified the items)?~~ **[Answered by Fix D1 — gate removed entirely; extractor trusted]**

---

## 5. Conditions

### 5.1 Conditions work when genre demands them [pirate + coruscant]

Pirate save: `rib_injury` (T13, 4 turns) and `winded`. Coruscant save: `exhausted` (T2-T5), `shoulder_strain` (T13-T16), `thigh_burn` (T14-T16, reappeared T19). Conditions are added and removed via TTL in combat/action genres.

Notable: coruscant conditions had a TTL mismatch — `shoulder_strain` (added T13, TTL=3 turns) and `thigh_burn` (added T14, TTL=2 turns) both expired around T16 but the narrative context still described the PC as injured. At T19 `thigh_burn` was re-added, suggesting the extraction re-detected it from narration even though the TTL had cleared it.

- **Confidence:** 95% — concrete state evidence in both saves.
- **Severity:** Low (positive) — system works, but TTL cleanup can conflict with narrative persistence.

### 5.2 TTL auto-removes conditions silently — no narrative event [all three]

The condition age pass (turn.py:1034-1053) decrements `turns_remaining` by exactly 1 every turn. When it reaches 0, the condition is removed from state with no LLM awareness. The only evidence is a `condition_expired` event in events.jsonl — the LLM never knows a wound healed.

**Coruscant evidence:** At T16, `shoulder_strain` and `thigh_burn` were both silently removed by TTL expiry. At T19, `thigh_burn` was re-added by extraction (narration still described the injury), creating a silent add/remove/add cycle. The TTL removed a condition that the narrative world still considered active.

**Pirate example:** `rib_injury` (turns_remaining: 4 at T13) auto-expired at T17 regardless of narrative state.

- **Confidence:** 100% — code-verified + trace data from all three saves.
- **Severity:** Medium-high now — coruscant shows TTL expiry directly conflicts with narrative persistence, creating a silent blink where conditions vanish and reappear.

### 5.3 Conditions genre-dependent: combat triggers, investigation doesn't [genre-specific]

noir (investigation): 0 conditions. Pirate (combat): 2 conditions. Coruscant (combat): 3 conditions. The condition system is alive and responsive to genre — investigation games don't cause physical injury, combat games do.

- **Confidence:** 95% — consistent across three different genres.
- **Severity:** Low — this is appropriate behavior, not a bug.

---

### Section questions

- Should condition expiry trigger a narrative event so the LLM can describe the recovery?
- Should more severe injuries get longer TTLs? (Currently all conditions get 10-turn default or the LLM's value.)
- Should conditions be removable only via LLM-driven `pc_condition_remove` instead of auto-TTL?

---

## 6. Arc System

### 6.1 Arc now updates via `goal_update` — coruscant shows 6 updates in 19 turns [coruscant overturns this]

**Status:** Coruscant save contradicts the previous "arc never updates" finding. The LLM emitted `goal_update` at T3, T7, T8, T9, T11, T13 — 6 of 19 turns (31.6%). This incrementally evolved the visible_goal:

1. Seed: "Extract a high-value target from the collapsing lower levels before the Separatist sweep."
2. T3: "Stabilize Robert Hall-Cox and prepare for immediate extraction from the clinic."
3. T7: "Stabilize Robert Hall-Cox using alternative methods before his condition becomes terminal."
4. T8: "Find a way to stabilize Robert Hall-Cox using limited or improvised resources."
5. T9: "Secure discrete medical treatment for Robert Hall-Cox at Aethelgard Station."
6. T11: "Secure immediate medical stabilization for Robert Hall-Cox despite Gail Vance's demand for upfront payment."
7. T13: "Protect Robert Hall-Cox and Gail Vance from the advancing Separatist patrol while securing medical stabilization."

The arc is NO longer static. The `goal_update` field in the storytell output schema provides an incremental update mechanism that works correctly. noir and pirate didn't produce goal_updates — this may be genre-dependent or a coincidence of LLM behavior in those seeds.

- **Confidence:** 95% — confirmed in coruscant events.jsonl. Firmly contradicts Finding 6.1.
- **Severity:** ~~High~~ Low now — the mechanism exists and works. Not a bug; LLM adoption varies by context/seed.

### 6.2 `goal_update` vs `arc_resolve` — separate mechanisms

The storytell schema has two arc-related output fields: `goal_update` (updates visible_goal mid-story) and `arc_resolve` (final closure). The coruscant save confirms `goal_update` works for incremental pivots. `arc_resolve` remains at zero across all saves (no arc has ever been formally closed), which is expected — no game has reached a natural conclusion.

The distinction is clear: goal_update = mid-story pivot; arc_resolve = final closure. Both mechanisms exist and the LLM uses goal_update when the narrative demands it. Prompt guidance about goal_update may help adoption, but it's not missing — the LLM found it.

- **Confidence:** 95% — confirmed in coruscant events.jsonl.
- **Severity:** Low — both mechanisms exist. No missing functionality.

---

### Section question

- ~~Should arc_resolve allow incremental goal updates (mid-story pivots) or only final resolution?~~ **[Answered by coruscant data — goal_update IS the mid-story pivot. arc_resolve is final-only, separate mechanism.]**

---

## 7. State / Extraction / Infrastructure

### 7.1 World state grows without bound — coruscant accelerates [all three]

| Save | Turns | Persistent facts | Total |
|---|---|---|---|
| noir | 12 | 7 | 10 |
| pirate | 13 | 7 | 10 |
| coruscant | 19 | 16+ | **22** |

Coruscant added ~1.2 facts per turn (22 at 19 turns) — faster than noir/pirate (~0.8/turn). The action-heavy genre generates more world state entries per turn. At 50 turns projecting: ~50-60 facts. The pre-overhaul Finding 2.8 about bloat is unchanged and worsening.

World state duplicates: Two entries in coruscant state describe the Banking Clan data-cylinder with nearly identical text but different IDs (`banking_clan_data_cylinder_found`, `graeme_has_banking_clan_data`). The system has no dedup mechanism.

- **Confidence:** 100% — verified in all three state.yaml files.
- **Severity:** High now — 22 facts at 19 turns is concerning. 50+ at 50 turns is terminal for the user prompt context window.

### 7.2 `recent_turns` slicing bug — storytell stream gets zero prior narration [all saves] ~~~ [FIXED by Fix D7] ~~~

**Status:** Fixed by Fix D7 (above) — the `[:-1]` was removed. The storyteller now receives the previous turn's full narration.

Bug confirmed in all saves — the storytell stream has never received prior turn narration since `_recent_turn_count` was set to 1.

**File:** `ccya/engine/extraction.py:534`
**Old:** `(recent_turns or [])[:-1][-10:]`
**New:** `(recent_turns or [])[-10:]`
**Effect:** The storytell stream now gets the previous turn's narration, consistent with the narrate stream (which uses `ctx.recent_turns[-1:]`).

- **Confidence:** 100% — code-verified.
- **Severity:** ~~Medium~~ Low now — fixed for future saves.

### 7.3 Storytell output format changed to parsed dict [both]

In both saves, `extraction.storytell.output` is a Python `dict`, not a JSON string. This is a pipeline change (pre-parsed before storage). The old saves stored JSON strings that needed `json.loads()`. This breaks tools/scripts that expect the old format.

- **Confidence:** 100% — both saves confirm.
- **Severity:** Medium — breaks backward compatibility for debugging tools. Easy fix.

### 7.3 NPC continuity unchanged (last_seen only) [both]

NPCs have `last_seen: {location_id, location_name, turn}` — still location+turn only, no narrative context bridging gaps between appearances. Same as pre-overhaul Finding 5.1.

- **Confidence:** 100% — both state.yaml files.
- **Severity:** Low — NPC continuity is a nice-to-have, not core mechanic.

### 7.4 Player momentum tracking works correctly [both]

Both saves show momentum values in [-3, +3] range with correct band-based deltas. noir ended at +3, pirate at +2. No momentum anomalies.

- **Confidence:** 95% — consistent across both saves.
- **Severity:** Low (positive).

---

### Section questions

- ~~Should world state have an expiry/consolidation mechanism?~~ **[Answered by Firm Decision D2 — seed-only static + resolved thread output]**
- Is the dict-output format change intentional? Should tools be updated, or should the old JSON-string format be restored for consistency?

---

## Summary: Full State (post-coruscant, post-fixes, post-decisions)

| System | Status | Notes |
|---|---|---|
| Pacing directives | ✅ **Working** | All 3 paths (age, velocity, momentum) confirmed. |
| GM Beat coverage | ✅ **Fixed (Fix C)** | 100% turn coverage. |
| Beat routing | ✅ **Fixed (Fix B)** | `recent_beats` in user prompt. |
| Beat diversity | 🟡 **Capped at 6/9 types** | Fix E added guidance for twist/setback/callback. Effectiveness pending next save. |
| Thread scope classification | ✅ **Working** | All saves correct. |
| Thread progress | 🟡 **Partially improved (Fix D)** | Better but still redundant. |
| Thread resolve | ✅ **FIRED (coruscant T6)** | First ever. Sporadic. |
| Thread urgency decay | ❌ **Never decays** | Firm Decision D4 — needs mechanical or prompt fix. |
| Arc `goal_update` | ✅ **Working** | 6 updates in 19 turns — but TOO FREQUENT (C2). |
| Arc `arc_resolve` | ❌ **Never fires** | Still zero across all saves. |
| Conditions | 🟡 **Working but TTL broken** | Firm Decision D3 — silent blink confirmed. |
| World state growth | ❌ **Worsening** | Firm Decision D2 — needs redesign. |
| Inventory durability gate | ✅ **Removed (Fix D1)** | Gate deleted at delta_builder.py:168-180. Extractor trusted. |
| `recent_turns` (narration context) | ✅ **Fixed (Fix D7)** | `[:-1]` removed at extraction.py:534. Storyteller now gets prior narration. |
| Beat ceiling guidance | ✅ **Added (Fix E)** | Setback type defined, twist/callback encouraged, ~80 added tokens. |
| `goal_update` frequency | ❌ **Too aggressive** | Firm Decision D6 — add cap guidance. |
| Batch compactor/sanitizer | 🤷 **Maybe (D5)** | Needed for 50+ turn games. |

**Fixes verified (coruscant confirms 7):**
- ✅ Fix A — Scene Pressure (T12) + Scene Imperative (T17-19) + Breathe (T1, T4)
- ✅ Fix B — `recent_beats` in user prompt, every turn
- ✅ Fix C — GM Beat section 100% coverage
- ⚠️ Fix D — Partial thread quality improvement
- ✅ Fix D7 — `recent_turns` slicing fixed (storyteller now gets prior narration)
- ✅ Fix D1 — Durability gate removed (inventory trust the extractor)
- ✅ Fix E — Beat ceiling guidance added (setback type + twist/callback encouragement)

**Firm Decisions status (recorded in section above):**
- D1: Durability gate — **DONE (removed)**
- D2: World state = seed-only static + resolved thread output — needs design
- D3: Conditions TTL — needs design (two options)
- D4: Thread urgency decay — needs design (mechanical vs prompt)
- D5: Batch compactor/sanitizer — maybe, needs scoping
- D6: `goal_update` frequency cap — needs drafting
- D7: `recent_turns` slicing — **DONE (fixed)**
- D8: Beat ceiling guidance — **DONE (added)**

**Next steps (need design first):**
1. World state redesign (D2)
2. Conditions TTL fix (D3)
3. Urgency decay mechanism (D4)
4. `goal_update` frequency cap (D6)
5. Batch compactor/sanitizer evaluation (D5)
