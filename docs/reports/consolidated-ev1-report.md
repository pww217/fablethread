# Consolidated Analysis Report — Turns 1 to 10

**Date:** 2025-05-26  
**Scope:** Single game save (`saves/default/`) covering turns T1–T10  
**Source Reports:** compaction-lifecycle-analysis.md, dice.md, gm_beat_lifecycle.md, gm_moves_per_band.md, momentum.md, pacing.md, ruling.md, thread_lifecycle.md

---

## What Went Well

- **Dice resolution pipeline**: All 7 rolls verified correct across band assignment (`compute_band()` thresholds), stat modifiers (`stat_value - 2` formula confirmed), difficulty modifiers (hard = -1), and condition modifier lookup when active. No bugs found in the core dice math or band classification logic.
- **Momentum tracking**: Band→delta mapping matches `MOMENTUM_DELTA` table exactly across all roll turns. State continuity is unbroken — `momentum_after` of turn N always equals `momentum_before` of turn N+1 with no gaps. Clamping logic at [-3,+3] boundaries exists and uses correct min/max pattern (though never exercised in this dataset). Top-level event momentum fields carry forward correctly for all turns including non-roll ones, ensuring complete observability regardless of whether a check occurred.
- **Ruling engine**: Intent parsing is accurate across 5 verb types observed (`repair`, `recall`, `deceive`, `pilot`). Check requirements are correct — `recall` checks auto-succeed with no roll, action verbs require rolls. Token usage stable (~1492–1562 in / ~60–86 out), latency consistent at ~2.7–2.9s per call with no degradation over time despite increasing context elsewhere.
- **Pacing directive system**: Pressure→Breathe transition on T4 occurs correctly when post-roll momentum reaches -2 (triggering narrative_velocity ≈ threshold). Beat lock fires on T10 when momentum hits floor (-3), appending "Resolve a Threat" as secondary directive — dual trigger design works (`consecutive_pressure >= 3` or `momentum <= -3`).
- **Thread urgency → directive mapping**: 1 urgent scene-scoped thread maps to Pressure correctly; Breathe overrides via narrative_velocity when momentum drops below threshold. Priority stack logic verified correct for velocity-driven path (no arc threads exist in this dataset).

---

## What Went Poorly

### Band-to-beat misalignment
All 4 PARTIAL roll outcomes received `breathing_room` beats instead of the prompt-guided complication/pressure (`storytell_system.j2:35`). The narration directive from pacing context ("Breathe" when narrative_velocity < -0.3) overrides band-aligned beat guidance, making mechanical meaning of partial outcomes (success at a cost) invisible to the player. 8 of 10 turns have misaligned beats between what rules.py computes and what storyteller emits.

### GM beats emitted every turn, never null
Every single turn emits a non-null gm_beat despite prompt saying "null unless independent narrative reason." `pending_gm_beat` is always present so expiration logic (`turn_no > beat_expires_turn`) is dead code — beats are perpetually replaced before expiring. Persistent environmental pressure that never naturally dissipates regardless of scene state or narration directive.

### Minor: COMPACTED block formatting quirk
Compaction worked correctly on both T5 and T10. T5 compacted T1–T3 into 3 bullets, T10 compacted T4–T8 into 5 bullets. Both events are fully recorded in events.jsonl. The only cosmetic issue is a blank line between the two bullet batches in the COMPACTED block.

### Urgency never auto-decays
All thread urgency values remain constant across all 10 turns. No automatic decay mechanism exists; urgency only changes if LLM updates it, and the prompt gives no instructions to decay urgency over time. Seeded scene-scoped threads stay urgent indefinitely without aging out via directive escalation — only momentum-based overrides work.

---

## Critical Issues to Fix (Highest → Lowest Priority)

### 1. Band-beat misalignment on PARTIAL outcomes
**What:** All 4 partial rolls got breathing_room instead of complication/pressure per prompt guidance (`storytell_system.j2:35`). Pacing directive dominates over band-aligned beat selection, undermining the mechanical meaning of "success at a cost."

**Evidence:** `gm_moves_per_band.md` table shows T5/T6/T8/T9 all PARTIAL → breathing_room. Narration directives for partials say "complication or pressure" but storyteller emits breathing_room consistently.

**Root cause:** Two separate systems influence beat selection — deterministic band alignment in rules.py vs pacing directive from `_compute_narration_directive()` (turn.py:503-594) — with no documented priority order. The LLM follows the "Breathe" directive more closely than band-aligned guidance whenever narrative_velocity < -0.3.

**Fix:** Either (a) make band alignment in `storytell_system.j2` a stronger signal than pacing directive for beat type selection, or (b) explicitly document that pacing directives override band guidance and adjust prompt accordingly to eliminate the contradiction between what narration says ("complication") and what storyteller emits ("breathing room").

### 2. Seeded scene-scoped threads never get `added_turn`
**What:** `siege_escalation` is seeded during scene generation (`seed.py:334-339`) with urgency=urgent but no `added_turn`. `western_gate_breach_chaos` was emitted as `thread_add` by LLM on T1 but never applied to state (absent from `applied.thread_add` across all turns, not in state.yaml). This means `_compute_threat_ages()` skips siege_escalation and "Resolve a Threat" urgency aging can never fire for it regardless of how many turns pass.

**Evidence:** `thread_lifecycle.md:108-109` — siege_escalation has no added_turn assigned, so it's skipped by the `_compute_threat_ages()` check at turn.py line 675-677 which requires `added_turn > 0`.

**Impact:** Urgent seeded threads stay urgent forever without aging out via directive escalation. Only narrative_velocity (momentum-based) or beat lock can override Pressure directives — urgency decay path is broken for all seeded scene-scoped content.

**Fix:** Assign `added_turn` during seed generation (`seed.py:334-339`) or in `_compute_threat_ages()` fallback logic for scene-scoped threads that lack it.

### 3. Progress=0 for frequently advanced threads — thread completion impossible
**What:** `siege_escalation` is advanced on T1,2,3,5,7,9,10 but state.yaml shows progress=0 throughout. Suggests ID mismatch between extraction output thread IDs and stored ArcThread.id in state, or `_apply_thread_signals()` not finding the thread when processing advances (turn.py line 215-216).

**Evidence:** `thread_lifecycle.md:143` — advance signals exist on 7 turns but progress never increments. No `thread_resolve` entries across all 10 turns; no threads reach `thread_completion_threshold`.

**Impact:** Thread completion is structurally impossible until fixed. If progress never increments, the entire thread resolution/completion pipeline is untested in production data AND threads accumulate indefinitely without ever resolving or being removed from active set. This compounds with issues #2 and #4 below to create a guaranteed thread accumulation problem under sustained play.

**Fix:** Verify that `thread_advance` signal IDs match actual `ArcThread.id` values in state.yaml. If they don't, align them — otherwise threads can never complete regardless of urgency decay or aging logic.

### 4. Compaction works correctly (no issue found — downgraded from original report error)
**What (corrected):** Compaction triggered on schedule and successfully produced work. T5 compacted T1–T3 (3 bullets), T10 compacted T4–T8 (5 bullets). Both events recorded in events.jsonl with full metadata (bullet previews, sanitization, tokens, timing). The `last_compacted_turn` evolved naturally: 0→3→8. The COMPACTED block was created by these two runs. The original report was based on inspecting non-existent `data`/`applied` keys — compaction events use different fields (`compact_start`, `compact_end`, `bullets_count`, `bullets_preview`, etc.).

**Evidence:** Both compaction events in events.jsonl contain `bullets_count=3` (T5) and `bullets_count=5` (T10), `bullets_preview` with actual text, `sanitization` data, `tokens_in`/`tokens_out`, and `ms`. Chronicle.md shows matching bullet sequence (T1–T3 then T4–T8). No observability gap exists.

**Verdict:** No fix needed. The only minor note is a cosmetic blank line between the two bullet batches in the COMPACTED block.

### 5. Beat expiration is dead code
**What:** Every turn emits a replacement beat so the expiry check (`turn_no > beat_expires_turn` at turn.py line 876) never fires in production. If storyteller ever stops emitting beats due to extraction failure or prompt confusion, pending_gm_beat persists for 2 turns then auto-clears on the 3rd turn — but this path is untested and likely broken by the universal emission pattern.

**Evidence:** `gm_beat_lifecycle.md:63` — zero null gm_beat values across all 10 turns. Beat always emitted regardless of narration directive or band type, so pending_gm_beat is always replaced before expiring within T1-T10 window.

**Fix:** Either ensure storyteller can emit `gm_beat: null` when pacing context indicates no beat needed (update prompt to reinforce this), or add a separate mechanism that forces periodic null emissions when scene state doesn't warrant persistent pressure.

### 6. Urgency never auto-decays on any thread
**What:** No automatic decay exists; urgency only changes via LLM updates which receive no instructions to decay over time (`storytell_system.j2` does not instruct storyteller about urgency aging). `thread_urgency_max_age=8` config value defined at `config.py:79` with comment "auto-remove threads older than this" — but never referenced in production code, only used by eval engine mirror (`eval/engine_mirror.py:23`).

**Evidence:** `thread_lifecycle.md:157-160` — urgency values remain constant across all 10 turns. siege_escalation always urgent, impressed_vessel always normal. No automatic decay mechanism exists in `_apply_thread_signals()` or anywhere else.

**Impact:** Urgent seeded threads stay urgent indefinitely unless the player addresses them and LLM decides to update urgency on a subsequent thread_add/update call. Creates persistent Pressure directives that only resolve through narrative_velocity overrides (momentum-based Breathe) or beat lock triggers rather than natural urgency decay.

**Fix:** Implement urgency aging logic in `_apply_thread_signals()` that demotes urgent→normal after N turns, normal→background after M turns, and wire `thread_urgency_max_age` for auto-removal of threads exceeding max age threshold. Add prompt guidance to storyteller about expected urgency decay cadence so LLM updates align with system expectations.

### 7. Scene-scoped threads structurally excluded from Python lifecycle management
**What:** Scene-scoped threads are completely excluded from `_apply_thread_signals()` — they pass through unchanged (`turn.py:274-276`: `if scope != "arc": updated_threads.append(t)`). They never get demoted to latent by Python code, only arc-scoped threads have dormancy/demotion paths (5-turn silence threshold at turn.py line 117).

**Evidence:** `thread_lifecycle.md:131` — scene-scoped threads excluded from `_apply_thread_signals()` explicitly. Only age via `_compute_threat_ages()` for directive computation, never get demoted to latent by Python code.

**Impact:** Scene-scoped urgent threads accumulate without any lifecycle management path other than urgency aging (which is itself broken per issue #6). Under sustained play with frequent thread_add calls creating new scene-scoped content, there's no mechanism to clean them up or reduce their count — only arc-scoped threads have dormancy/demotion logic.

**Fix:** Either extend `_apply_thread_signals()` lifecycle management to include scene-scoped threads (with appropriate thresholds), or add a separate cleanup path for stale scene-scoped threads that haven't been advanced in N turns. Consider whether "urgent" status should decay differently for scene vs arc scope.

### 8. Fail near-miss prompt guidance contradicts itself
**What:** Narration directive for fail near-misses says "narrate a complication or setback" (`GM_MOVES` table) but storyteller beat guidance explicitly says "Do NOT emit escalation/pressure on failed checks" (`storytell_system.j2:37`). T1 got a pressure beat (following narration directive), T4 and T10 got breathing_room (T4 following beat guidance, T10 aligning with directive=Breathe + beat_lock). Inconsistent LLM behavior across the 3 fail near-miss turns.

**Evidence:** `gm_moves_per_band.md:122-128` — fail near-miss turns show split behavior. T1 used pressure (contradicting "Do NOT emit escalation/pressure on failed checks" but following narration directive). T4 chose breathing_room (aligning with beat guidance for fail/setback). T10 also chose breathing_room (aligning with fail-band beat guidance despite beat_lock appending "Resolve a Threat"). The prompt contains contradictory signals producing inconsistent outcomes.

**Fix:** Unify instructions across both systems — either both say to include complications for near-misses, or clarify that near-miss is a special case outside normal fail semantics and update `storytell_system.j2` accordingly. Near miss should be treated as mechanically distinct from outright failure in both narration and storyteller prompts.

### 9. Beat consumed on next turn creates one-turn lag
**What:** Beats generated on turn N are read by narrator at start of turn N+1, meaning T1's pressure beat shapes T2 narration not T1, and T4's breathing_room replaces T3's pressure but doesn't appear in narration until T5. If the beat system is meant to provide immediate feedback for roll outcomes (e.g., "you failed → here's a complication"), this lag means complications appear one turn late.

**Evidence:** `gm_beat_lifecycle.md:97` — beats generated on turn N shape narration on turn N+1, not current turn. Narrator receives pending_gm_beat from state at start of each turn and integrates it into narration (narrate_system.j2 line 30).

**Impact:** Disconnect between mechanical outcome timing and narrative beat delivery. If intended as "ongoing atmosphere shaping" this is fine; if intended as immediate feedback for roll outcomes, the one-turn lag creates confusion about cause-and-effect in gameplay.

**Fix:** Either accept as intentional design (beats shape ongoing scene atmosphere rather than immediate consequences) or shift consumption to happen within same turn before narration generation — read pending_gm_beat at end of turn N and write it into that turn's narration context instead of carrying forward to N+1.

### 10. `raw_total` not persisted in events.jsonl
**What:** `raw_total` exists in `RulesOutcome` model (`rules.py:197,213`) but isn't written to events.jsonl ruling dict (`turn.py:1442-1453`). Verification of dice math requires manual computation from separate fields (`final_total` and modifiers are both present so no data loss — just harder analysis).

**Evidence:** `dice.md:84-86` — field exists in model but omitted during serialization. No direct way to verify raw dice sum + modifiers = final_total without reconstructing from persisted pieces.

**Fix:** Add `raw_total` to the ruling dict serialization at turn.py line 1442-1453 for easier analysis and debugging of dice resolution issues.

---

## Ambiguities Identified

### A1. What signal should dominate beat selection?
Band-aligned guidance in `storytell_system.j2` vs pacing directive from `_compute_narration_directive()` — the data shows pacing wins, but this contradicts design intent for PARTIAL outcomes where band alignment matters most ("success at a cost" becoming "breathing room"). The report (`gm_moves_per_band.md:52-73`) identifies three separate systems (rules.py directives, pacing context, storyteller LLM) with no documented priority hierarchy.

### A2. Why does consecutive_pressure not trigger beat lock on T4?
Three consecutive Pressure directives (T1-T3) all carry `thread_advance=['siege_escalation']`, which triggers the cpt reset branch at turn.py line 1418-1419 (resets to 0 when thread_advance is non-empty). The counter never reaches >= 3 because every Pressure turn also has thread_advance progress. Beat lock only fires on T10 via momentum floor path. The analysis in pacing.md correctly identified the counter wasn't reaching threshold but missed the thread_advance reset because it was not inspecting extraction data.

### A3. Turn 7 "anomaly" — false alarm from wrong query field
Ruling.md initially flagged `ruling.momentum_before` returning None/missing on non-roll turns as a momentum anomaly (showing -2→+0 jump), but the report corrects this at line 164: top-level event fields show correct continuity (-2→-2). The "anomaly" was caused by querying `ruling.momentum_before` instead of top-level `event['momentum_before']`. Analysts should always use top-level momentum fields to avoid misleading defaults on non-roll turns.

### A4. Is progress=0 for siege_escalation a display bug or logic bug?
Could be that ev.py Active Threads section doesn't reflect actual state.yaml values, or it could indicate `_apply_thread_signals()` isn't finding the thread by ID when processing advances (`thread_lifecycle.md:163-167`). Needs direct source inspection to resolve whether `thread_advance` signal IDs match ArcThread.id in state.

### A5. COMPACTED block origin (resolved)
The COMPACTED block was created by this run's two compaction events. T5 compaction wrote T1–T3 bullets to chronicle.md; T10 compaction appended T4–T8 bullets. Both events are fully recorded in events.jsonl with matching data. No mystery about its origin.

### A6. Surface_as inconsistency on T9/T10
Breathing_room beats mostly use `ambient`, pressure uses `environmental`, but T9 has breathing_room=environmental and T10 has breathing_room=ambient (T10 was NOT a pressure beat — corrected from source report error). Surface_as varies independently of beat type for unclear reasons — could indicate LLM inconsistency or separate decision path.

---

## Meta-Failures

### M1. Three systems with no clear hierarchy
Band alignment (`rules.py`), pacing directive (`turn.py:503-594`), and storyteller beat selection (LLM-driven) all influence outcomes but have an undocumented priority order. The LLM follows pacing directives over band guidance, which undermines the mechanical meaning of roll results — especially PARTIAL ("success at a cost" becoming "breathing room"). This is not an edge case; it's structural: whenever narrative_velocity < -0.3 creates "Breathe", all band-aligned beat recommendations become effectively ignored (`gm_moves_per_band.md:135-139`).

### M2. (Removed — compaction is working correctly. See corrected issue #4 above.)
No observability gap was found. Compaction events are fully recorded in events.jsonl with bullet previews, sanitization, tokens, and timing. Both T5 and T10 compactions performed real work. The original analysis was based on inspecting non-existent `data`/`applied` fields on compaction event records.

### M3. Config values that exist but aren't wired
`thread_urgency_max_age=8` exists with a comment about auto-removal but is never enforced in production code — only used by eval engine mirror (`eval/engine_mirror.py:23`). Creates false confidence that thread aging has an upper bound when it doesn't. `recent_turns_min=2` may be too low to retain sufficient narrative context between COMPACTED blocks and Turn headers, making compaction hard to verify but no one flagged this as a config wiring issue (`compaction-lifecycle-analysis.md:179`).

### M4. ev.py lacks dedicated commands for key analysis paths
No dice display command (must query events.jsonl directly), no beat consumption tracking field in extraction output, and no dedicated `ev.py` command to display storyteller `actions` (though actions ARE captured in extraction output on all 10 turns and stored in top-level `event.actions`). Analysis of these fields requires manual event querying rather than built-in tooling.

### M5. Prompt contradictions baked into system
Fail near-miss guidance says "narrate a complication" (narration) but "Do NOT emit pressure on failed checks" (storyteller). PARTIAL band says "complication, pressure" in one place and gets overridden by "Breathe" directive from pacing context. These aren't edge cases — they're structural conflicts between what different LLM roles are told to do (`gm_moves_per_band.md:123-128`).

### M6. Thread accumulation guaranteed under sustained play
Combined effect of issues #2, #3, #6, and #7 above creates a scenario where threads accumulate indefinitely: urgent seeded threads never age out (no added_turn), frequently advanced threads can't complete (progress=0), scene-scoped threads aren't managed by Python lifecycle at all, urgency decay doesn't exist in production code. Under sustained play with frequent thread_add calls creating new content, there's no cleanup path for stale or completed threads (`thread_lifecycle.md:172-180`).

---

## Summary Table: Issue Severity Matrix

| # | Issue | Severity | Scope | Fix Complexity |
|---|-------|----------|-------|----------------|
| 1 | Band-beat misalignment on PARTIAL | **Critical** | All roll outcomes, affects player experience | Medium — prompt + directive alignment |
| 2 | Seeded threads missing `added_turn` | **High** | Scene-scoped thread urgency aging | Low — assign added_turn in seed.py or _compute_threat_ages() |
| 3 | Progress=0 for advanced threads | **Critical** | Thread completion pipeline broken entirely | Medium-High — ID mismatch investigation needed |
| 4 | Compaction works correctly (no issue) | **None** | (corrected — compaction functioned as designed) | N/A |
| 5 | Beat expiration dead code | **Medium** | GM beat lifecycle reliability | Low — enable null emissions in storyteller prompt |
| 6 | Urgency never auto-decays | **High** | Thread urgency escalation path broken | Medium-High — implement aging logic + config wiring |
| 7 | Scene threads excluded from Python lifecycle | **Medium** | Long-term thread accumulation under sustained play | Medium — extend or create separate cleanup path |
| 8 | Fail near-miss prompt contradiction | **Medium** | Inconsistent LLM behavior on mechanically important band variant | Low — unify narration/storyteller instructions |
| 9 | One-turn beat lag | **Low-Medium** | Cause-and-effect clarity in gameplay | Medium — architectural decision about consumption timing |
| 10 | raw_total not persisted | **Low** | Analysis/debugging friction only | Trivial — add field to serialization |

---

## Appendix: Source Report Cross-Reference

| Issue | Primary Source(s) | Supporting Evidence |
|-------|------------------|---------------------|
| #1 Band-beat misalignment | gm_moves_per_band.md, gm_beat_lifecycle.md | 7/10 turns misaligned; all PARTIAL→breathing_room |
| #2 Missing added_turn | thread_lifecycle.md:149-156 | siege_escalation affected; western_gate_breach_chaos thread_add never applied to state |
| #3 Progress=0 for advanced threads | thread_lifecycle.md:135-143, :162-167 | 7 advances on T1-T10 but progress stays at 0 |
| #4 Compaction works correctly (no issue) | compaction-lifecycle-analysis.md | Both compactions produced bullets, recorded in events.jsonl |
| #5 Beat expiration dead code | gm_beat_lifecycle.md:83-109 | Zero null beats; expiry check never fires |
| #6 Urgency no decay | thread_lifecycle.md:157-160, :169-172 | All urgency constant across 10 turns |
| #7 Scene threads excluded from lifecycle | thread_lifecycle.md:131 | turn.py line 274-276 excludes scope != "arc" |
| #8 Fail near-miss contradiction | gm_moves_per_band.md:122-128 | T1 pressure vs T4/T10 breathing_room split |
| #9 One-turn beat lag | gm_beat_lifecycle.md:88-97, :141-151 | Beats generated N consumed by narration on N+1 |
| #10 raw_total not persisted | dice.md:84-86 | RulesOutcome model has field but serialization omits it |
