# Consolidated Analysis Report — Ev1 + Ev2 Combined Findings

**Ev1 Date:** 2025-05-26 | **Ev2 Date:** 2026-05-27  
**Scope:** Single game save (`saves/default/`) covering turns T1–T11, with ev1 focusing on T1–T10 surface patterns and ev2 examining compaction behavior at T5→T6 boundary  
**Source Reports (Ev1):** compaction-lifecycle-analysis.md, dice.md, gm_beat_lifecycle.md, gm_moves_per_band.md, momentum.md, pacing.md, ruling.md, thread_lifecycle.md  
**Source Reports (Ev2):** ev2/findings.md

---

## What Went Well

- **Dice resolution pipeline**: All 7 rolls verified correct across band assignment (`compute_band()` thresholds), stat modifiers (`stat_value - 2` formula confirmed), difficulty modifiers (hard = -1), and condition modifier lookup when active. No bugs found in core dice math or band classification logic.
- **Momentum tracking**: Band→delta mapping matches `MOMENTUM_DELTA` table exactly across all roll turns. State continuity is unbroken — `momentum_after` of turn N always equals `momentum_before` of turn N+1 with no gaps. Clamping at [-3,+3] exists and uses correct min/max pattern (though never exercised in this dataset). Top-level event momentum fields carry forward correctly for all turns including non-roll ones.
- **Ruling engine**: Intent parsing is accurate across 5 verb types observed (`repair`, `recall`, `deceive`, `pilot`). Check requirements are correct — `recall` checks auto-succeed with no roll, action verbs require rolls. Token usage stable (~1492–1562 in / ~60–86 out), latency consistent at ~2.7–2.9s per call.
- **Pacing directive system**: Pressure→Breathe transition on T4 occurs correctly when post-roll momentum reaches -2 (triggering narrative_velocity ≈ threshold). Beat lock fires on T10/T11 via momentum floor (-3), appending "Resolve a Threat" as secondary directive — dual trigger design works (`consecutive_pressure >= 3` or `momentum <= -3`).
- **Compaction mechanics**: Both T5 and T10 compactions produced valid COMPACTED events with bullet previews, sanitization data, token counts, timing. Chronicle.md updated correctly on both runs.
- **Orphan condition lifecycle tracking**: Orphan conditions (e.g., `acid_splash`) have proper turns_remaining counter decrementing across turns. When count reaches 0, orphan removal logic fires correctly. This pipeline works as designed.

---

## Critical Issues to Fix (Highest → Lowest Priority)

### C1. Key-branch black hole: all scene-scoped thread_add with keys silently dropped
**Severity: CRITICAL | Found: Ev2 (source-code analysis)**  
**Scope:** All LLM-generated scene-scoped thread_add entries in any game  

The `thread_add` if-elif chain at `turn.py:1275–1301` has a structural gap: the `elif _new_thread.key:` branch checks for key collisions but has NO fallthrough to actually add the thread when no collision is found. Threads that pass all gates (gate=allow, cooldown satisfied, no key collision) are silently dropped without being added to state.

**Root cause — code trace (`turn.py:1261–1301`):**

The if-elif chain:
1. `if not gate_ok: pass` (line 1268) — blocked by pacing gate
2. `elif not cooldown_satisfied: pass` (line 1271) — blocked by cooldown
3. **`elif _new_thread.key:`** (line 1275) — checks key collision; if no collision, **falls through doing nothing** (no `else` clause to proceed with addition)
4. `elif _scope == "scene": pass` (line 1297) — only reachable when key is falsy
5. `else:` (line 1301) — only reachable when both key is falsy AND scope is not "scene"

Every scene-scoped `thread_add` emitted by the LLM (T7: `the_bridge_stalker` key=`entity_aggression`, T8: `the_mechanical_beast_siege` key=`entity_attack`, T9: `the_spencermouth_collapse` key=`bridge_structural_failure`, T11: `the_vanishing_runner` key=`rescue_miller`) enters branch 3, passes the collision check, and is silently dropped.

**Evidence chain (all verified from raw events.jsonl):**
1. T1–T5 have non-empty directives (Pressure/Breathe) — proves scene-scoped threads existed pre-compaction
2. T5 compaction removed `bridge_security` via `pressure_remove=[{'id': 'bridge_security', 'confidence': 'high'}]`
3. T6–T11 all have `pacing_context.directive=""`, `summary="neutral"` — empty after compaction
4. LLM emits scene-scoped `thread_add` with keys on T7, T8, T9, T11
5. `state.yaml` has `threads: []` at T11 and no `last_thread_creation_turn` — confirms no `thread_add` ever succeeded
6. `bridge_security` was SEEDED (`seed.py:330–339`), bypassing the broken `thread_add` path

**Impact:** After first compaction removes the seeded scene thread, the LLM's attempts to create replacements are structurally discarded. Directives converge to empty after T5 and stay empty for the entire rest of the game — regardless of narrative events (combat, environmental hazards, NPC losses). All future scene-scoped thread_add emissions are doomed by this code bug.

**Fix:** The `elif _new_thread.key:` branch must fall through to the thread-adding code (the same logic in the `else:` block at line 1301) after the collision check passes. The collision check should only REJECT on collision — on pass, execution should proceed to the add logic.

### C2. Progress=0 for scene-scoped thread_advance only — arc-thread lifecycle works correctly
**Severity: MEDIUM-HIGH | Found: Ev1 | Corrected in Ev2**  
**Scope:** Scene-scoped thread advancement only  

`_apply_thread_signals()` at `turn.py:200` filters to `scope=="arc"` only. Scene-scoped `thread_advance` signals are structurally a no-op for progress tracking. The `supply_sabotage` (arc-scoped) thread DID reach progress=3 and was completed — arc-thread lifecycle works correctly. The ev1 claim of "all thread progress stalls" conflated scene-only data with the full system.

**Impact:** Scene-scoped threads can never advance toward completion through the Python pipeline. This combined with C1 (no new scene threads can be created) and C3 (seeded threads lack added_turn) makes scene-scoped threads effectively inert — they can't be created, advanced, or completed through normal gameplay. Only LLM-driven thread_resolve can remove them.

### C3. Seeded scene-scoped threads never get `added_turn`
**Severity: HIGH | Found: Ev1 | Confirmed in fresh game (Ev2)**  
**Scope:** Scene-scoped thread urgency aging  

`siege_escalation` is seeded during scene generation (`seed.py:334–339`) with urgency=urgent but no `added_turn`. This means `_compute_threat_ages()` skips it (turn.py line 675–677 requires `added_turn > 0`). Urgency aging can never fire for this thread.

**Impact:** Urgent seeded threads stay urgent forever without aging out via directive escalation. Only momentum-based overrides work. This is a structural bug in seed generation, not dataset-specific.

**Fix:** Assign `added_turn` during seed generation (`seed.py:334–339`) or in `_compute_threat_ages()` fallback logic for scene-scoped threads that lack it.

### C4. Urgency never auto-decays on any thread
**Severity: HIGH | Found: Ev1 | Confirmed in fresh game (Ev2)**  
**Scope:** Thread urgency escalation path broken  

No automatic decay exists; urgency only changes via LLM updates which receive no instructions to decay over time (`storytell_system.j2` does not instruct storyteller about urgency aging). `thread_urgency_max_age=8` config value defined at `config.py:79` with comment "auto-remove threads older than this" — but never referenced in production code, only used by eval engine mirror.

**Impact:** Urgent seeded threads stay urgent indefinitely unless the player addresses them and LLM decides to update urgency on a subsequent thread_add/update call. Creates persistent Pressure directives that only resolve through narrative_velocity overrides (momentum-based Breathe) or beat lock triggers rather than natural urgency decay.

**Fix:** Implement urgency aging logic in `_apply_thread_signals()` that demotes urgent→normal after N turns, normal→background after M turns. Wire `thread_urgency_max_age` for auto-removal of threads exceeding max age threshold. Add prompt guidance to storyteller about expected urgency decay cadence.

### C5. Band-beat misalignment on PARTIAL outcomes
**Severity: CRITICAL | Found: Ev1 | Validated in fresh game (Ev2)**  
**Scope:** All roll outcomes, affects player experience  

All 4 PARTIAL roll outcomes received `breathing_room` instead of the prompt-guided complication/pressure (`storytell_system.j2:35`). The narration directive from pacing context ("Breathe" when narrative_velocity < -0.3) overrides band-aligned beat guidance, making mechanical meaning of partial outcomes (success at a cost) invisible to the player. 8 of 10 turns have misaligned beats between what rules.py computes and what storyteller emits.

**Root cause:** Two separate systems influence beat selection — deterministic band alignment in rules.py vs pacing directive from `_compute_narration_directive()` (turn.py:503–594) — with no documented priority order. The LLM follows the "Breathe" directive more closely than band-aligned guidance whenever narrative_velocity < -0.3.

**Fix:** Either (a) make band alignment in `storytell_system.j2` a stronger signal than pacing directive for beat type selection, or (b) explicitly document that pacing directives override band guidance and adjust prompt accordingly to eliminate the contradiction between what narration says ("complication") and what storyteller emits ("breathing room").

### C6. Fail near-miss prompt guidance contradicts itself
**Severity: MEDIUM | Found: Ev1 | Still present structurally (Ev2)**  
**Scope:** Inconsistent LLM behavior on mechanically important band variant  

Narration directive for fail near-misses says "narrate a complication or setback" (`GM_MOVES` table) but storyteller beat guidance explicitly says "Do NOT emit escalation/pressure on failed checks" (`storytell_system.j2:37`). T1 got pressure (following narration), T4/T10 got breathing_room (following beat guidance). Inconsistent LLM behavior across fail near-miss turns.

**Fix:** Unify instructions across both systems — either both say to include complications for near-misses, or clarify that near-miss is a special case outside normal fail semantics and update `storytell_system.j2` accordingly. Near miss should be treated as mechanically distinct from outright failure in both narration and storyteller prompts.

### C7. Scene-scoped threads excluded from Python lifecycle management
**Severity: MEDIUM-HIGH | Found: Ev1 | Confirmed in fresh game (Ev2)**  
**Scope:** Long-term thread accumulation under sustained play  

Scene-scoped threads are completely excluded from `_apply_thread_signals()` — they pass through unchanged (`turn.py:274–276`: `if scope != "arc": updated_threads.append(t)`). They never get demoted to latent by Python code, only arc-scoped threads have dormancy/demotion paths (5-turn silence threshold at turn.py line 117).

**Impact:** Scene-scoped urgent threads accumulate without any lifecycle management path other than urgency aging (which is itself broken per C4). Under sustained play with frequent thread_add calls creating new scene-scoped content, there's no mechanism to clean them up or reduce their count.

**Fix:** Either extend `_apply_thread_signals()` lifecycle management to include scene-scoped threads (with appropriate thresholds), or add a separate cleanup path for stale scene-scoped threads that haven't been advanced in N turns. Consider whether "urgent" status should decay differently for scene vs arc scope.

### C8. Beat expiration is dead code
**Severity: MEDIUM | Found: Ev1 | Validated (Ev2)**  
**Scope:** GM beat lifecycle reliability  

Every turn emits a replacement beat so the expiry check (`turn_no > beat_expires_turn` at turn.py line 876) never fires in production. If storyteller ever stops emitting beats due to extraction failure or prompt confusion, pending_gm_beat persists for 2 turns then auto-clears on the 3rd turn — but this path is untested and likely broken by the universal emission pattern.

**Fix:** Either ensure storyteller can emit `gm_beat: null` when pacing context indicates no beat needed (update prompt to reinforce this), or add a separate mechanism that forces periodic null emissions when scene state doesn't warrant persistent pressure.

### C9. Compacted bullet content may reference removed threads
**Severity: MEDIUM | Found: Ev2 only**  
**Scope:** Historical consistency between chronicle.md and current state  

When compactor removes scene-scoped threads during sanitization (C1), the compacted bullets in chronicle.md and events.jsonl still contain narrative references to those threads. This creates inconsistency between historical record (bullets mention bridge security) and current state (no bridge_security thread exists).

**Fix:** When removing threads during compaction sanitization, update bullet previews to remove or generalize references to removed threads. Or prevent removal of active scene-scoped threads entirely (see C1 fix).

### C10. One-turn beat lag
**Severity: LOW-MEDIUM | Found: Ev1 | Validated (Ev2)**  
**Scope:** Cause-and-effect clarity in gameplay  

Beats generated on turn N are read by narrator at start of turn N+1, meaning T1's pressure beat shapes T2 narration not T1. If the beat system is meant to provide immediate feedback for roll outcomes (e.g., "you failed → here's a complication"), this lag means complications appear one turn late.

**Fix:** Either accept as intentional design (beats shape ongoing scene atmosphere rather than immediate consequences) or shift consumption to happen within same turn before narration generation — read pending_gm_beat at end of turn N and write it into that turn's narration context instead of carrying forward to N+1.

### C11. `raw_total` not persisted in events.jsonl
**Severity: LOW | Found: Ev1 | Validated (Ev2)**  
**Scope:** Analysis/debugging friction only  

`raw_total` exists in `RulesOutcome` model (`rules.py:197,213`) but isn't written to events.jsonl ruling dict (`turn.py:1442–1453`). Verification of dice math requires manual computation from separate fields.

**Fix:** Add `raw_total` to the ruling dict serialization at turn.py line 1442–1453 for easier analysis and debugging of dice resolution issues.

### C12. Compactor thread removal semantics are undocumented
**Severity: MEDIUM | Found: Ev2 only**  
**Scope:** Compaction pipeline, compact_user.j2 template  

The compactor conflates two distinct concepts: "pressures to remove" (old resolved threats) and "active scene threads that should persist." The `compact_user.j2` template at line 21 renders all scene-scoped threads under "Active Scene Pressures" — the word "pressure" implies they're temporary conditions, but they represent active narrative elements.

**Fix:** Separate rendering of truly resolved pressures from active scene elements in compact_user.j2 so LLM only evaluates items that should be removed for removal. Add prompt guidance clarifying which threads are disposable vs persistent during bullet review.

### C13. `_scope_scene_threads` empty post-compaction causes silent directive degradation
**Severity: HIGH | Found: Ev2 only**  
**Scope:** Observability gap in compaction aftermath  

When compactor removes all scene-scoped threads, `_compute_narration_directive()` silently falls back to "neutral" with no warning or fallback mechanism. There's no logging or observability that directives have degraded from informative ("Bridge security is deteriorating") to empty string.

**Fix:** Add logging when directive degrades due to empty thread set. Consider whether a default fallback directive (e.g., based on most recent non-empty directive) should be used during periods of empty threads rather than silently falling back to "neutral."

### C15. Narrator step does not render `recent_events` — template omission
**Severity: CRITICAL | Found: Playthrough observation 2026-05-27**  
**Scope:** All narration turns  

The `_narrate_messages()` function (turn.py:920–933) passes full state to the narrator prompt, and `recent_events` IS persisted in state.scene.recent_events (`delta_builder.py:290–326`). However, `narrate_user.j2` never renders them — the template shows world_state (line 17-19), recent_turns narrative prose (line 51-57), and arc threads (line 59) but has no section for scene.recent_events. This means the storyteller step cannot reference "last turn we learned X" or build on established facts from prior turns' fact extraction.

**Evidence:** Traced `_run_extraction_pipeline` → `_storytell_messages()` at extraction.py:231–280 — `recent_events` IS passed to storyteller step and rendered in `storytell_user.j2:22-25`. But the narrator step (which runs first) never renders them from state.

**Impact:** Narration lacks continuity with previously established world knowledge. Each turn's narration is generated blind to factual state changes (new alliances discovered, threats confirmed, opportunities found) that should inform tone and direction. This contributes directly to "story not related enough to Arc" — the narrator can't reference what matters because it doesn't see recent_events in its prompt.

**Fix:** Add a `## Recent Events` section to narrate_user.j2 rendering state.scene.recent_events, or pass them as an explicit template variable alongside state/arc context. Alternatively (deferred decision): remove recent_events entirely if the feature isn't worth fixing — see deferred decisions section below.

### C16. Storytell step blind to `world_state` due to conditional rendering bug
**Severity: HIGH | Found: Playthrough observation 2026-05-27**  
**Scope:** All extraction/storyteller steps with active threads  

The storyteller prompt template (`storytell_user.j2:26`) renders world state only when there are NO threads: `{% if not all_threads and world_state %}`. In normal gameplay where threads exist (which is always), this section never appears in the prompt. The data IS passed to `_storytell_messages()` at extraction.py:250/268 — it's a template rendering bug, not a data flow gap.

**Evidence:** `storytell_user.j2:15–31` — threads section renders unconditionally when present; world_state section only as `{% else %}` fallback (line 26) with condition `not all_threads and world_state`. This means world state is invisible whenever any thread exists in state.

**Impact:** Storyteller step cannot reference established world facts (politics, geography, history) that should inform tone, NPC behavior, and narrative choices. This contributes directly to "failure/neutral outcomes don't open doors" — without world context, the storyteller has no basis for introducing new opportunities after a failed check or neutral outcome.

**Fix:** Remove the `not all_threads` condition from line 26 of storytell_user.j2 so world_state is always rendered alongside threads. Or move world_state to a separate section that renders regardless of thread state (e.g., as "## World Context" before threads).

---

## Ambiguities Identified

### A1. What signal should dominate beat selection?
Band-aligned guidance in `storytell_system.j2` vs pacing directive from `_compute_narration_directive()` — the data shows pacing wins, but this contradicts design intent for PARTIAL outcomes where band alignment matters most ("success at a cost" becoming "breathing room"). Three separate systems (rules.py directives, pacing context, storyteller LLM) with no documented priority hierarchy.

### A2. Why does consecutive_pressure not trigger beat lock on T4?
Three consecutive Pressure directives (T1–T3) all carry `thread_advance=['siege_escalation']`, which triggers the cpt reset branch at turn.py line 1418–1419 (resets to 0 when thread_advance is non-empty). The counter never reaches >= 3 because every Pressure turn also has thread_advance progress. Beat lock only fires via momentum floor path.

### A3. Turn 7 "anomaly" — false alarm from wrong query field
Ruling.md initially flagged `ruling.momentum_before` returning None/missing on non-roll turns as a momentum anomaly, but top-level event fields show correct continuity (-2→-2). The "anomaly" was caused by querying `ruling.momentum_before` instead of top-level `event['momentum_before']`. Analysts should always use top-level momentum fields.

### A4. Is progress=0 for siege_escalation a display bug or logic bug?
Could be that ev.py Active Threads section doesn't reflect actual state.yaml values, or it could indicate `_apply_thread_signals()` isn't finding the thread by ID when processing advances. Needs direct source inspection to resolve whether `thread_advance` signal IDs match ArcThread.id in state.

### A5. Surface_as inconsistency on T9/T10
Breathing_room beats mostly use `ambient`, pressure uses `environmental`, but some turns show cross-pattern usage (e.g., breathing_room=environmental). Surface_as varies independently of beat type for unclear reasons — could indicate LLM inconsistency or separate decision path.

---

## Meta-Failures

### M1. Three systems with no clear hierarchy
Band alignment (`rules.py`), pacing directive (`turn.py:503–594`), and storyteller beat selection (LLM-driven) all influence outcomes but have an undocumented priority order. The LLM follows pacing directives over band guidance, which undermines the mechanical meaning of roll results — especially PARTIAL ("success at a cost" becoming "breathing room"). This is not an edge case; it's structural: whenever narrative_velocity < -0.3 creates "Breathe", all band-aligned beat recommendations become effectively ignored.

### M2. Config values that exist but aren't wired
`thread_urgency_max_age=8` exists with a comment about auto-removal but is never enforced in production code — only used by eval engine mirror (`eval/engine_mirror.py:23`). Creates false confidence that thread aging has an upper bound when it doesn't. `recent_turns_min=2` may be too low to retain sufficient narrative context between COMPACTED blocks and Turn headers, making compaction hard to verify but no one flagged this as a config wiring issue.

### M3. Prompt contradictions baked into system — playthrough confirms systemic pacing problem
Fail near-miss guidance says "narrate a complication" (narration) but "Do NOT emit pressure on failed checks" (storyteller). PARTIAL band says "complication, pressure" in one place and gets overridden by "Breathe" directive from pacing context. These aren't edge cases — they're structural conflicts between what different LLM roles are told to do.

**Playthrough confirmation (2026-05-27):** Two player-throughs confirmed these contradictions produce a systemic pacing problem: narration and choices don't open doors on failure/neutral outcomes, story isn't related enough to Arc. This is the practical manifestation of M1+M3 combined — three systems pulling toward stasis rather than momentum.

### M4. Thread lifecycle is structurally inert post-compaction
The key-branch black hole (C1) means the LLM's scene-scoped thread_add emissions are always discarded. Thread lifecycle for scene-scoped content is effectively inert: seeded threads get removed by compaction, new threads can't be created (C1), existing threads can't be advanced (C2), urgency never decays (C4), and lifecycle management excludes them (C7). The only functional path is LLM-driven `thread_resolve` — which itself is filtered to arc-scoped threads only. Scene-scoped threads can't enter, advance, age, or leave the system through normal code paths.

### M5. Compactor is a secondary contributor
The compactor removing bridge_security was initially blamed as primary cause of empty directives. The real root cause is the key-branch black hole. Even if the compactor never removed threads, the system would still be unable to create new scene-scoped threads through LLM `thread_add`. The compactor merely triggered the symptom a few turns earlier than it would have occurred naturally.

### M6. ev.py lacks dedicated commands for key analysis paths
No dice display command (must query events.jsonl directly), no beat consumption tracking field in extraction output, and no dedicated `ev.py` command to display storyteller actions (though actions ARE captured). Analysis of these fields requires manual event querying rather than built-in tooling.

---

## Summary Table: Issue Severity Matrix

| # | Issue | Severity | Found In | Fix Complexity |
|---|-------|----------|----------|----------------|
| C1 | Key-branch black hole: all thread_add with keys silently dropped | **CRITICAL** | Ev2 (source-code) | Medium — add fallthrough after collision check |
| C5 | Band-beat misalignment on PARTIAL outcomes | **CRITICAL** | Ev1 | Medium — prompt + directive alignment |
| C3 | Seeded threads missing `added_turn` | **HIGH** | Ev1 | Low — assign added_turn in seed.py or _compute_threat_ages() |
| C4 | Urgency never auto-decays | **HIGH** | Ev1 | Medium-High — implement aging logic + config wiring |
| C7 | Scene threads excluded from Python lifecycle | **MEDIUM-HIGH** | Ev1 | Medium — extend or create separate cleanup path |
| C2 | Progress=0 for scene-scoped advances only (arc works) | **MEDIUM-HIGH** | Ev1 | Medium — remove scope filter in _apply_thread_signals() |
| C6 | Fail near-miss prompt contradiction | **MEDIUM** | Ev1 | Low — unify narration/storyteller instructions |
| C8 | Beat expiration dead code | **MEDIUM** | Ev1 | Low — enable null emissions in storyteller prompt |
| C9 | Compacted bullets reference removed threads | **MEDIUM** | Ev2 | Medium — update bullet previews during sanitization |
| C12 | Compactor thread removal semantics undocumented | **MEDIUM** | Ev2 | Low-Medium — separate rendering of resolved vs active elements |
| C13 | Silent directive degradation post-compaction | **LOW-MEDIUM** | Ev2 | Low — add logging + fallback mechanism |
| C10 | One-turn beat lag | **LOW-MEDIUM** | Ev1 | Medium — architectural decision about consumption timing |
| C11 | raw_total not persisted in events.jsonl | **LOW** | Ev1 | Trivial — add field to serialization |
| C14 | Compactor removed seeded scene thread (secondary contributor) | **MEDIUM** | Ev2 | Low — prompt guidance to preserve active scene elements |
| C15 | Narrator step blind to recent_events (template rendering omission) | **CRITICAL** | Playthrough 2026-05-27 | Medium — add section to narrate_user.j2 or remove feature entirely |
| C16 | Storytell step blind to world_state (conditional rendering bug at storytell_user.j2:26) | **HIGH** | Playthrough 2026-05-27 | Low — remove `not all_threads` condition from line 26 of storytell_user.j2 |

---

## Cross-Run Consistency Check: Ev1 vs Ev2 Findings

| Finding | Ev1 Status | Ev2 Validation |
|---------|-----------|----------------|
| C3: Seeded threads missing added_turn | Found in ev1 | Confirmed in fresh game |
| C4: Progress=0 for advanced threads | Found in ev1 | Confirmed in fresh game |
| C5: Urgency never auto-decays | Found in ev1 | Confirmed in fresh game |
| C7: Scene threads excluded from lifecycle | Found in ev1 | Confirmed in fresh game |
| C6: Fail near-miss contradiction | Found in ev1 | Still present structurally |
| C8: Beat expiration dead code | Found in ev1 | Validated (zero null beats) |
| C5: Band-beat misalignment on PARTIAL | Found in ev1 | Validated against fresh game |
| **C1: Key-branch black hole** | NOT found in ev1 | NEW — root cause of empty directives |
| C2: Progress=0 for scene-scoped only | Found in ev1 (imprecise) | CORRECTED — arc advances work, scene don't |
| C8: Beat type distribution | Not analyzed | Normal range (45/27/18/9) |
| C9: Orphan conditions lifecycle | Not analyzed | Working correctly |
| C14: Compactor removal of scene threads | NOT found in ev1 | NEW — secondary contributor |

ev1 analyzed T1–T10 surface patterns without examining compaction internals or thread_add code paths. ev2 discovered the **key-branch black hole** at `turn.py:1275` — an egregious code bug where `elif _new_thread.key:` has a collision check but no fallthrough to add the thread. This is the definitive root cause of empty directives T6–T11. The compactor removal of `bridge_security` at T5 is a secondary contributor — even if the compactor never ran, the system still couldn't create new scene-scoped threads via the normal LLM `thread_add` path.

ev2 corrected two ev1 claims:
- C2 progress=0: Only scene-scoped threads stall. Arc-scoped threads advance correctly (`supply_sabotage` reached progress=3 and completed).
- "bridge_security becoming MORE urgent": Removed as unverifiable.

ev2 confirmed all other ev1 findings in a fresh game run, validating they are structural bugs not dataset artifacts.

**Playthrough observations (2026-05-27):** Two player-throughs confirmed the systemic pacing problem: three systems simultaneously pull toward stasis (C5+C6+M3). Playthrough also identified two new template rendering issues — narrator blind to recent_events and storyteller blind to world_state due to conditional rendering at `storytell_user.j2:26`. These contribute directly to "story not related enough to Arc" and "failure/neutral outcomes don't open doors."

---

## Appendix: Source Report Cross-Reference

| Issue | Primary Source(s) | Supporting Evidence |
|-------|------------------|---------------------|
| C1 Key-branch black hole | Ev2 ev2/findings.md | turn.py:1275 elif _new_thread.key: no fallthrough after collision check; state.yaml has threads:[] + no last_thread_creation_turn |
| C2 Scene-scoped progress=0 (arc works) | Ev1 thread_lifecycle.md + Ev2 correction | supply_sabotage (arc) completed with progress=3; siege_escalation (scene) stuck at 0 |
| C3 Missing added_turn | Ev1 thread_lifecycle.md:149–156 | siege_escalation affected; western_gate_breach_chaos thread_add never applied to state |
| C4 Urgency no decay | Ev1 thread_lifecycle.md:157–160, :169–172 | All urgency constant across 10 turns in both runs |
| C5 Band-beat misalignment | Ev1 gm_moves_per_band.md, gm_beat_lifecycle.md | 8/10 turns misaligned; all PARTIAL→breathing_room |
| C6 Fail near-miss contradiction | Ev1 gm_moves_per_band.md:122–128 | T1 pressure vs T4/T10 breathing_room split |
| C7 Scene threads excluded from lifecycle | Ev1 thread_lifecycle.md:131 | turn.py line 274–276 excludes scope != "arc" |
| C8 Beat expiration dead code | Ev1 gm_beat_lifecycle.md:83–109 | Zero null beats; expiry check never fires |
| C9 Compacted bullets reference removed threads | ev2/findings.md | Bridge security mentioned in T5 compacted bullets but thread removed during sanitization |
| C10 One-turn beat lag | Ev1 gm_beat_lifecycle.md:88–97, :141–151 | Beats generated N consumed by narration on N+1 |
| C11 raw_total not persisted | Ev1 dice.md:84–86 | RulesOutcome model has field but serialization omits it |
| C12 Compactor semantics undocumented | ev2/findings.md | compact_user.j2:21 renders all scene threads as "pressures" |
| C13 Silent directive degradation | ev2/findings.md | No logging when _scope_scene_threads becomes empty post-compaction |
| C14 Compactor removed seeded scene thread | ev2/findings.md | T5 compaction pressure_remove=[{id: bridge_security, confidence: high}] |
| C15 Narrator blind to recent_events (template rendering) | Playthrough 2026-05-27 | state.scene.recent_events persisted but narrate_user.j2 never renders them; storytell_user.j2 does render them at line 22-25 |
| C16 Storytell blind to world_state (conditional rendering) | Playthrough 2026-05-27 | storytell_user.j2:26 `{% if not all_threads and world_state %}` blocks rendering when threads exist; data IS passed via extraction.py:250/268 |

---

## Deferred Decisions

### Remove `recent_events` entirely
**Status:** Deferred — playthrough confirmed narrator step doesn't render recent_events (C15), making them effectively dead weight. Storytell step does receive them but repetition threshold is too aggressive (`storytell_system.j2:44` "never restate facts that overlap"). Two options on the table: (a) add a Recent Events section to narrate_user.j2 rendering state.scene.recent_events, or (b) remove recent_events entirely as a concept since it adds complexity without value when not properly wired. Decision deferred pending design review of whether narrative continuity via state YAML is worth fixing vs removing the feature.

### Compactor window shrinking
**Status:** Deferred — `_compute_recent_window()` at turn.py:701 uses `min(config.window_turns, turns_since_compaction)` which resets after each compaction, causing progressively fewer preserved turns (turn 8 misses T4, turn 9 misses T4/T5, etc.). This is a structural bug but low priority until C1 (key-branch black hole) is fixed since the window issue only matters when threads can actually be created.
