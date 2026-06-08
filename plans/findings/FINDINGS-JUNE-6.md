# Findings — Game Sessions

> Game-specific findings. General bugs and observations are in [BUGS-OBSERVATIONS.md](BUGS-OBSERVATIONS.md). Momentum/beat deep-dive in [MOMENTUM-BEAT-FINDINGS.md](MOMENTUM-BEAT-FINDINGS.md).
>
> Severity: **H**=high, **M**=medium, **L**=low

---

## Game 1 (noir-1930s, 25 turns)

### Needs Investigation

| # | Severity | Title | Detail |
|---|---|---|---|
| G1 | H | **Momentum death spiral — no recovery path** | See [MOMENTUM-BEAT-FINDINGS.md](MOMENTUM-BEAT-FINDINGS.md) (MB-1 through MB-7). Summary: 42% hard difficulty against a +2-max character, no depth-based momentum catch-up, Breathe directive fires at momentum ≤ -2, floor relief injects de-escalatory beats during crisis. |
| G2 | M | **Beat system monotony in extended conflict** | See [MOMENTUM-BEAT-FINDINGS.md](MOMENTUM-BEAT-FINDINGS.md) (MB-1, MB-2, MB-3). Summary: Breathe dominates because urgent scene threads are unreliable; "; Resolve a Threat" append contradicts Breathe; floor relief overrides pressure beats with calm beats. |
| G3 | M | **Goal stagnation — sanitizer too slow to pivot [FIXED — step 02.2]** (Confidence: H) | The arc goal "Secure the missing witness before they are silenced by the union enforcement wing" stayed unchanged for T1–T15. The player fought enforcers (T7), executed a thug (T9), interrogated the survivor (T10), found Devon (T11) — all still under the same goal. The sanitizer runs every 5 turns and its output lags by one turn. Should storytell update the arc goal mid-cycle, or should the sanitizer run more frequently? **Confirmed in baseline eval:** zero `goal_update` events emitted across all 13 turns despite narrative arcs involving debt settlement, ledger pursuit, cellar discoveries, and bodyguard confrontation (Confidence: H — same metric observed independently). **[Live data cross-game validation]** Consistent 3-turn lag between major narrative pivots and goal updates in noir (T12 Devon escape → T15 pivot; T22 Keith killed → T25 pivot). Byzantium showed similar pattern with missed combat-to-escape pivot at T10. Root cause: sanitizer template does not explicitly instruct LLM to pivot goals on major events — it only asks passive evaluation question about whether goal "should be updated." **FIXED:** Step 02.2 added explicit trigger events (witness escapes/killed, ally killed, location shifts dramatically, debt settled/lost, new critical info) that MUST update visible_goal to reflect current reality. See [EVAL-FIXES.md](EVAL-FIXES.md#issue-3-goal-stagnation) for eval gaps and fixes. |
| G4 | L | **Stale goal in narrate prompt at end-of-life** | T25 narrate prompt showed "Goal: Negotiate with Sergeant Keith to secure the manifests" even though Keith was killed at T22. The LLM wrote a death scene anyway, so impact was minimal. Symptom of G3 (goal lags reality). |

### Feature Ideas & Improvements

| # | Severity | Title | Detail |
|---|---|---|---|
| G5 | M | **arc_resolve produced incomplete state at T24** | `council_corruption_war` was resolved (failed) and `police_retaliation_escalation` was added, but `visible_goal` remained "Negotiate with Sergeant Keith" — a dead NPC. `goal_context` summarized the past but didn't project a new objective. The arc_resolve schema expects a forward-looking `visible_goal`; when it doesn't provide one, the UI strand goes dark. |

### What Worked

- **Narrative coherence was strong.** The chronicle forms a legitimate 4-act noir tragedy with consistent voice, character continuity, and escalating stakes. The arc/thread system deserves credit for providing guardrails.
- **T20 sanitizer goal change was correct.** It pivoted "Use manifests to expose council corruption" → "Negotiate with Keith to secure the manifests," matching the alley standoff. Proves the mechanism works when timing aligns.
- **Extraction retry rate was excellent.** Only 1 retry in 25 turns (T12 storytell — arc_resolve field missing from LLM output). 99.2% extraction success rate. No rejections, no skipped streams.
- **T11 crit_success was the only momentum escape.** The player rolled a 10 on charisma (+2, normal) → 12 total → crit_success → momentum +2. It lifted momentum from -3 to -1 and unlocked beat_locked for 3 turns (T11-T13). Proves momentum recovery is possible but requires outlier luck.
- **Scene Imperative fired correctly** at T7, T9, T11-T13, T15 (age≥5, with/without combat boost). The aging mechanism works when a scene persists.

---

---

## Game 2 (the-fall-of-byzantium, 31 turns)

> Custom campaign: Fourth Crusade sacking of Constantinople (1204). PC: Leandros, a Blacksmith. Goal: Navigate burning city to family forge, extract kin to safety.

### Needs Investigation

| # | Severity | Title | Detail |
|---|---|---|---|
| BZ1 | H | **Background threads accumulate forever without decay [FIXED — step 02.1 + step 01.3a]** (`broken_defense`, `looting_scourge`, `coinage_panic` all inactive since turns 5-10, still in active list at turn 31) — root cause: sanitizer template does not explicitly instruct cleanup of stale background threads. The LLM sees these as "still relevant to the war" and keeps them inactive rather than moving to completed_threads. No temporal decay instruction exists in `sanitize_thread.j2`. **FIXED:** Step 02.1 added explicit temporal decay cleanup instruction to sanitizer template (inactive=3+ turns, no progress_updates → move to resolved or remove). Step 01.3a fixed engine auto-latent demotion to fire every turn (not gated on mutation) so stale threads reliably get active=false set before the sanitizer processes them. See [EVAL-FIXES.md](EVAL-FIXES.md#issue-5-background-thread-accumulation) for eval gaps (no accumulation metric, no decay validation). |
| BZ2 | M | **Beat type selection doesn't align with momentum state** | Turns 25–29 (momentum at -3) produced four consecutive BREATHING_ROOM beats despite the player being in a critical survival situation — pinned against a wall with a spear at their throat, broken wrist, family cornered. The mechanical state (momentum=-3) and the beat type generated (breathing_room/ambient) were misaligned. Existing MB-1/MB-3 findings document the structural causes, but this session adds qualitative evidence: the tonal contradiction is felt at the narrative level. At -3, the narrator described "a broken wrist and a stifled gasp" — yet the beat system was signaling ambient calm. |
| BZ3 | M | **Scene tag volatility breaks scene identity continuity** | Scene tags flipped dramatically between consecutive turns throughout the game (e.g., T10: `combat, visceral, tense` → immediately cleared to `(empty)` → re-established; T12: cleared entirely; T13: `tense_refuge, recovery, impending_danger` — all within 2 turns of each other). This happened even when nothing mechanically significant changed. The scene extraction appears stateless per-turn rather than building continuity, causing the "scene identity" to reset between turns rather than evolving naturally. Multiple turns show `(empty)` state mid-game for a scene that was just `combat, violent, tense`. |
| BZ4 | M | **Beat generation is inconsistent — not every turn emits a beat** | Turn 20 (FAIL on intimidate) → PRESSURE beat stored correctly. But Turn 5 (SUCCESS) → no beat emitted despite thread advancement. Turn 8 (success, Kosta Aris dying) → no beat. The `gm_beat` field was sometimes `None` on success and sometimes populated. The beat type selection rules (`GM-BEAT-TYPE-ALIGNMENT.md`) assume beats are generated — but generation is not guaranteed. Beat-driven pacing logic (consecutive pressure counter, beat_locked triggers) can fire or not based on extraction luck rather than consistent rules. **Confirmed in baseline eval:** Storytell emitted 0 actions (expected 4) at T3/T7/T13 when narrative context was thin/empty — same root cause of LLM disengagement when input is sparse. |
| BZ5 | L | **No explicit milestone feedback when primary thread resolves** | `family_extraction` resolved at T30 (thread_resolve in T30 deltas). A new thread `naval_patrol_evasion` appeared immediately. But the player received no narrative acknowledgment that their primary goal had been achieved — the resolution felt like just another state change rather than a milestone. The arc goal switched from "Evacuate family" to "Avoid Latin fleet patrols" without ceremony. |
| BZ6 | L | **Thread scope confusion — scene vs arc boundaries unclear** | A `mercenary_blockade` thread was added as scope=scene in T5, but was never explicitly resolved. It was apparently absorbed into `family_extraction` progress. The boundary between scene-scoped threads (which should expire/latify per `02-thread-lifecycle.md` Step 2.6) and arc-scoped threads is fuzzy in practice — the LLM uses scope inconsistently, and the sanitizers/resolution paths don't clearly differentiate. |

### Feature Ideas & Improvements

| # | Severity | Title | Detail |
|---|---|---|---|
| BZ7 | M | **Storyteller actions list works well but is undocumented** | Storytell consistently produced 4 actionable choices per turn (e.g., T5: "Charge Kosta Aris", "Bribe mercenaries with silver signet", "Slink into shadows", "Shout a challenge"). These gave the player meaningful tactical options that fit scene constraints. No existing plan documents this as a feature, but it worked well across all 31 turns. Should be formally specified and preserved. |

### What Worked

- **Narrative coherence was strong.** The chronicle forms a coherent escape thriller across 31 turns with consistent voice, escalating stakes, and a clear arc from "get to family" → "fight through mercenaries" → "extract family" → "escape to water". The 5-stream pipeline maintained character continuity and world state throughout.
- **Rules outcomes were properly binding.** Narrator never contradicted band results across 31 turns. CRIT_SUCCESS stayed triumphant (T1: shield+shortsword kill, T15: arming family), FAIL stayed a failure (T2: Nikola won't yield, T20: intimidate fails), CRIT_FAIL produced narrative damage (T25: broken wrist). The binding contract between ruling and narration held with zero violations across all 31 turns.
- **Extraction reliability was perfect.** Zero retries, zero rejections, zero errors across all 31 turns and all 5 streams. 100% first-attempt parse rate — better than noir's 99.2%.
- **Thread progress markers were semantically meaningful.** `family_extraction` showed clear ADVANCEMENT/SETBACK progression over 15+ turns: `Family found hiding behind anvil → Kin arm themselves → SETBACK: Family trapped by debris → SETBACK: cornered by guards → ADVANCEMENT: escapes via drainage tunnel → SETBACK: guard discovers family → ADVANCEMENT: family flees to harbor`. The player could track their thread's state at a glance. This is the intended behavior per `simplify-thread-system.md` and it worked.
- **Momentum created a real narrative arc.** Momentum moved from +2 (confident mercenary-killer) → +3 (peak combat effectiveness) → 0 (Demetrios confrontation fails) → -3 (broken, pinned, desperate). At -3, the player was killing guards with bare hands, family members stifling sobs, the PC's vision swimming. This is the death spiral documented in MB-4, but the narrative output made it feel earned rather than mechanical.
- **Consecutive FAIL sequence built genuine tension.** Turns 18-25: bribe fails → intimidate fails → drain tunnel succeeds → trip/injury → mallet miss → CRIT_FAIL (broken wrist) → guard death → family flee. The string of failures was not random — each failure set up the next complication naturally, creating a genuine "pushed into a corner" narrative that made the eventual escape at T30 feel earned.
- **Permanent immutable facts (TRACE_IMMUTABLE) provided persistent lore.** The Golden Horn choked with Venetian galleys, the Fourth Crusade's diversion, the Komnenos dynasty fracturing — these appeared in every turn's thread context and provided world-scale continuity even when the player was focused on immediate survival. They never got lost or trimmed.
---

## Game 3 (baseline eval — `full_cycle` + `baseline`, 26 turns total)

> Two evaluation runs with the same model (`mlx-community/gemma-4-26b-a4b-it-mxfp8`) and judge (`Qwen3.6-35B-A3B-OptiQ`). First run: `full_cycle` scenario (13 turns, adversarial track). Second run: `baseline` scenario (13 turns, organic narrative — Dustfall mystery with PC Aren Voss). Judge scoring for baseline: Mechanical 2/5, Narrative 2/5, System Cohesion 2/5, State Fidelity 38.5%.

### Scoring Breakdown (Baseline Eval) [Confidence: H]

| Metric | Score | Interpretation |
|---|---|---|
| Rules Pipeline | 5/5 | Clean schema adherence; `last_turn_narrative` is wasted ~400 tokens/turn in ruling prompt |
| Narrate Pipeline | 5/5 | High-quality prose, follows constraints well |
| Extract Scene | 4/5 | Good adherence but receives redundant inputs (`previous_turn_narration`) saving ~400 tokens/turn if removed |
| Extract State | 2/5 | Turn 13 failure: hallucinated `whiskey_glass` add+remove for immediately-consumed item; no CONDITION_MODS validation rejects unknown conditions (8/13 turns) |
| Storyteller | 5/5 | Excellent adherence to complex thread and beat rules, but emits 0 actions on 3/13 turns (T3/T7/T13) when context is thin |

**Auto-checker failures by severity:** [SYSTEM] 280 passed / 30 failed. Top SYSTEM failures: `consecutive_pressure_tracking` 6/13, `conditions.orphan` 8/13, `storytell.actions_quality` 3/13, `ruling.rolled` 4/8 (engine routing), `location_change.applied` 2/13, `inventory_add/remove` 2/13.

### Needs Investigation

| # | Severity | Title | Detail |
|---|---|---|---|
| G6 | H | **Location changes silently dropped from canonical state** (T4, T8, T12) — *new* [Confidence: H] | Scene Extract correctly identified location transitions (`dustfall_main_street` → `assay_office`, `isolated_cabin` → `general_store`, `red_canyon` → `dustfall_main_street`) but `_apply_delta` never persisted them to canonical state. This is a new critical finding not present in noir or Byzantium runs — possibly because those games had fewer location transitions, or the bug only manifests under certain delta validation conditions. The judge called this "catastrophic" since it breaks all scene-scoped logic (NPC presence, scene tags, thread scope). |
| G7 | H | **Momentum sign inversion in organic gameplay** — *new* [Confidence: M] | Baseline eval confirmed momentum deltas being applied with inverted signs: `fail` rolls produced +1 instead of -1 (Turn 4), and the opposite at Turn 9 (`success` yielded -1). This was NOT flagged by noir findings (MB-4 treated it as a balance/design issue, not an engine bug). The judge traced this to `_apply_momentum_delta` reading stale state snapshots or applying inverted signs during mutation. Confirms that momentum inversion is deeper than the uniform-delta death spiral — there's actual corruption in how deltas are applied. [Note: root cause attribution (`_apply_momentum_delta`) inferred by LLM judge from events.jsonl data, not verified against source code.] |
| G8 | H | **Floor relief injection failure** (T12) — *contradicts MB-3* [Confidence: M] | At T12, `beat_locked=True`, storytell emitted a pressure-type beat (`complication`), but pending_gm_beat stayed as `pressure` instead of being overridden by the floor-relief-injected `breathing_room`. This is the **opposite** of what MB-3 diagnosed (floor relief firing 15/16 times during crisis). Either there are two different failure modes: over-firing in some conditions, under-firing in others. The judge flagged this as a root cause for pacing directive mismatches (Pressure vs Calm prose). [Only 2 turns of evidence — may be scenario-specific.] |
| G9 | M | **Thread resolution failures — resolved threads reappear active** (T9, T11) [Confidence: L-M] | `store_confrontation` thread was marked resolved but reappeared in the active list. This confirms B3's concern about thread lifecycle losing tracking on exit, and extends it: not only do resolutions fail to archive properly, they may be rolled back or incompletely merged during arc update processing. The judge called this a "thread resolution loop." [Only 2 turns of evidence; inference based on state diffs rather than explicit resolve-then-reactivate sequence in events.jsonl.] |
| G10 | M | **Consecutive pressure counter desync confirmed in baseline** (6/13 turns) [Confidence: H] | Same symptom as MB-5: the pacing meta field `consecutive_pressure_turns` doesn't sync with actual beat types emitted by Storytell. Sometimes a `pressure` beat appears with counter=0, sometimes no beat exists but counter is stuck at 3+. This was supposedly fixed in cb623f4 (B4) — see BUGS-OBSERVATIONS.md for the contradiction. **Timing mismatch:** assertion reads storytell.gm_beat.type from THIS event's storytell output while meta.consecutive_pressure_turns captures pre-extraction state_snapshot — stale counter values get paired with wrong storytell types on multi-event turns (see B13 in BUGS-OBSERVATIONS.md). [Directly observable from events.jsonl data; root cause may be different than originally diagnosed.] |

### What Worked

- **Zero rules parse failures across both runs** (26 turns). The ruling engine consistently produced valid JSON output with no structural errors.
- **Extraction retry rate was excellent.** Only 1 retry in 25 total turns (T12 storytell — arc_resolve field missing from LLM output) in the full_cycle run; baseline had zero retries. Overall ~96% first-attempt parse success.
- **Narrative coherence held across both scenarios.** The noir tragedy (25 turns) and Dustfall mystery (13 turns) both maintained consistent voice, character continuity, and escalating stakes despite systemic state issues beneath the surface.

---
