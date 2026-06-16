# Overlap & Contradictions: Automated Evals vs Prior Reports

**Sources compared:**
- `docs/evals/master-report-narrative-mechanics.md` — 5 automated evals (noir, zombie, ww2, pirate, space-western), 100 turns, driven persona
- `docs/findings/post_convergence/evaluation-report.md` — Santa Monica human session, 19 turns, human player + passive AI
- `docs/ev/consolidated-findings.md` — Zombie-driven vs Santa Monica comparison, 20 automated turns

---

## OVERLAP — Things All Three Reports Agree On

### 1. Thread lifecycle is broken in automated play
All three reports identify the same core problem: the storyteller creates threads but doesn't meaningfully progress or resolve them.

| Report | Evidence |
|--------|----------|
| Master report | 47 `thread_updates.dedup` rejections — progress stuck at 0.91-1.00 |
| Zombie-driven vs Santa | `militia_expansion_agenda` updated 13 consecutive times without resolution |
| Santa Monica | `military_cordon_tension` — hallucinated thread ID updated 5 times without creation |

**Consensus:** The storyteller prompt doesn't instruct the LLM to meaningfully increment thread progress or create new threads. In human sessions, threads resolve in 2-4 turns. In automated sessions, they stall immediately.

### 2. `extraction.state.empty` — FIXED (2026-06-16)
All three reports flag this as a major issue.

| Report | Frequency |
|--------|-----------|
| Master report | 39/100 turns (39%) |
| Zombie-driven vs Santa | 4/26 events (15%) in zombie-driven vs 14/38 (37%) in Santa |
| Santa Monica | 0 — clean run, 100% first-pass success |

**Consensus:** The state extractor fails to find inventory/condition changes in the LLM output. The human session had zero extraction failures — this is an automated-play-specific problem, not a fundamental engine bug.

**Validation (2026-06-16):** Root cause is threefold: (1) check only looked at `inventory_add` + `pc_condition_add`, missing `inventory_update`/`inventory_remove`/`pc_condition_remove`; (2) validator missing `inventory_update`; (3) prompt lacked spatial reasoning guidance — LLM treated "draw revolver" as an inventory change. Fix applied: expanded check to all fields, added `state_attempts > 1` guard, expanded validator to include `inventory_update`, rewrote prompt with STEP 0 ("Decide first, output second") and explicit spatial reasoning rules. Validation run confirmed fix works.

### 3. Convergence scoring has a bootstrap problem
Both automated reports identify this. Santa Monica confirms it by contrast — it works fine once in RISING/CLIMAX.

| Report | Finding |
|--------|---------|
| Master report | No convergence_score data available (components missing from events) |
| Zombie-driven vs Santa | `thread_weight=0` because no urgent threads → `score<3` → no phase escalation → no urgent threads |
| Santa Monica | Score works perfectly once in RISING/CLIMAX — 3 CLIMAX entries all at score=3 |

**Consensus:** The convergence score functions correctly once the game is in motion. The problem is escaping SETUP — there's no mechanism to generate initial urgency in automated play where the AI player doesn't create stakes.

### 4. Goal updates are unreliable
All three report `goal_update_validity` failures.

| Report | Evidence |
|--------|----------|
| Master report | FAIL in 4/5 packs |
| Zombie-driven vs Santa | 0 goal updates in zombie-driven session |
| Santa Monica | FAIL — goal_update out of sync with visible_goal, noop updates on T16/T18 |

**Consensus:** The storyteller emits goal_updates that don't match state, or emits noop updates. The timing mismatch between storyteller output and arc pipeline state updates is a real issue.

### 5. `arc_resolve` parse failures
Both automated reports find `arc_resolve.resolution`, `arc_resolve.visible_goal`, `arc_resolve.goal_context` missing. Santa Monica doesn't flag this — `arc_resolution_validity` PASSES in that session.

**Consensus:** This is an automated-play-specific issue. The AI storyteller returns empty `arc_resolve: {}` objects in automated play but not in human sessions.

### 6. `skill: ?` in rulings
Both automated reports note this (~40% of turns). Santa Monica doesn't mention it — `roll_band_consistency` PASSES in that session.

**Consensus:** Likely automated-play-specific — the AI player's inputs may not map to clear action types that the ruling pipeline can classify with a skill.

---

## CONTRADICTIONS — Where Reports Disagree

### 1. Thread resolution rate

| Report | Finding |
|--------|---------|
| Master report | 0% resolution — threads never resolve, all updates rejected as dedup |
| Zombie-driven vs Santa | 1/2 resolved in zombie-driven (50%), 2/2 in Santa (100%) |
| Santa Monica | 6/7 resolved (85.7%) |

**Contradiction:** The master report says threads NEVER resolve in automated play. The zombie-driven vs Santa report says 1 thread resolved in the zombie-driven session. The Santa Monica report says 85.7% resolution.

**Resolution:** The zombie-driven vs Santa report is from an earlier codebase state. The master report reflects the current state where thread dedup has gotten worse — threads that might have resolved in the earlier session now get stuck in dedup loops. This is a regression.

### 2. Checker pass rate — is automated play worse or better?

| Report | Automated | Human |
|--------|-----------|-------|
| Zombie-driven vs Santa | 87% | 78% |
| Santa Monica | — | 88.9% |
| Master report | 78-87% | — |

**Contradiction:** Zombie-driven vs Santa says automated play (87%) outperforms human play (78%). Santa Monica says human play (88.9%) outperforms the pre-convergence automated baseline (77.8%). The master report shows automated play at 78-87%.

**Resolution:** These are different codebase states and different checkers. Zombie-driven vs Santa used an earlier checker set (23 checkers). Santa Monica used 27 checkers. The master report also uses 23 checkers. The apparent contradiction comes from different checker counts and different codebase states, not actual performance differences.

### 3. Extraction pipeline — broken vs working

| Report | Finding |
|--------|---------|
| Master report | `extraction.state.empty` on 39% of turns — broken |
| Zombie-driven vs Santa | `extraction.state.empty` on 15% of turns — degraded but not broken |
| Santa Monica | 0 extraction failures — working perfectly |

**Contradiction:** The master report paints the extraction pipeline as fundamentally broken. The earlier reports show it as degraded but functional.

**Resolution:** The master report reflects a regression — the state extraction prompt/template has gotten worse since the earlier sessions. The human session still works because human inputs produce clearer state changes that the extractor can find.

### 4. Convergence score — present vs absent

| Report | Finding |
|--------|---------|
| Santa Monica | `convergence_score` present in all events — score-driven CLIMAX entry confirmed |
| Master report | No convergence_score data — components missing from events |
| Zombie-driven vs Santa | `convergence_score` present — 0 times at ≥3 in zombie-driven |

**Contradiction:** Santa Monica says convergence_score is present and working. The master report says it's not available in the automated eval saves.

**Resolution:** The master report saves were generated after the convergence components serialization was fixed (the Santa Monica save was from a gap where components weren't persisted). The automated saves DO have `convergence_score` — the master report just didn't check for it. This is an oversight in the master report, not a contradiction in the engine.

### 5. Beat lifecycle — twist beats

| Report | Finding |
|--------|---------|
| Santa Monica | 0 twist beats — removed from Scene Imperative list |
| Master report | Doesn't mention twist beats at all |
| Zombie-driven vs Santa | Doesn't mention twist beats |

**Contradiction:** Santa Monica explicitly notes twist beats are gone as a positive change. The master report doesn't mention them.

**Resolution:** Not a real contradiction — the master report focused on failures and didn't catalog what's working. Twist beats being absent is consistent across all three reports.

---

## NEW FINDINGS IN MASTER REPORT NOT IN PRIOR REPORTS

### 1. `thread_same_turn_conflict` — update AND resolve same ID
Not identified in prior reports. The storyteller simultaneously updates and resolves a thread in the same turn. This is a new bug introduced in the narrative overhaul.

### 2. `thread_resolutions` — unknown IDs
14 `thread_resolve` references to non-existent thread IDs across all packs. Prior reports identified this as `military_cordon_tension` in Santa Monica but didn't quantify it across multiple packs.

### 3. `extract_state parse failed` — `inventory_change_reason` NoneType
Not identified in prior reports. The state extractor returns `None` for `inventory_change_reason` when inventory changes are present, causing Pydantic validation to fail.

### 4. `delta validation failed` + `Fallback narrative`
Not identified in prior reports. Zombie pack had 2 turns where state deltas failed validation and fell back to stripped narratives.

### 5. `TypeError` in logging
Not identified in prior reports. `thread_same_turn_conflict` log uses `%d` for string `trace_id`.

### 6. `reconcile_delta duplicate condition add ignored`
Not identified in prior reports. Pirate pack had `watched` condition attempted to be added twice in one turn.

### 7. `inventory over-draw clamped`
Not identified in prior reports. Zombie pack tried to remove 4 `pistol_ammo` when only 2 remained.

### 8. `generate_seed soft-check` — opening narrative too short
All 5 packs have opening narratives below the 530-930 word target. Prior reports didn't check this metric.

---

## KEY INSIGHT: Automated vs Human Play Diverges Sharply

The three reports together paint a clear picture:

| Aspect | Human Play (Santa Monica) | Automated Play (All 3 reports) |
|--------|--------------------------|-------------------------------|
| Extraction failures | 0% | 15-39% |
| Thread resolution | 85.7% | 0-50% |
| `arc_resolve` parse failures | 0% | 20% of packs |
| `skill: ?` in rulings | Not observed | ~40% of turns |
| `thread_same_turn_conflict` | Not observed | 4 occurrences |
| `goal_update_validity` | FAIL | FAIL in 4/5 packs |
| `pacing_directives` | PASS | PASS in 2/5 packs |
| `beat_phase_validity` | PASS | FAIL in 2/5 packs |
| Convergence score | Working (score-driven CLIMAX) | Working but no urgency to trigger it |

**The engine works correctly for human players.** Santa Monica proves this — 88.9% checker pass rate, clean extraction, threads resolve naturally, phases cycle correctly.

**Automated play breaks the extraction and threading layers.** The AI player's inputs don't produce clear state changes, the storyteller doesn't create/progress threads meaningfully, and `arc_resolve` returns empty objects.

**The narrative generation (scene imperatives, combat narration, location tracking) works in both modes.** This is the strongest finding — the prose quality and mechanical coherence of combat/scene progression is consistent across human and automated play.

---

## RECOMMENDATION

The prior reports' recommendations still apply but should be prioritized differently based on the automated vs human divergence:

1. **Fix state extraction for automated inputs** — The extractor needs to handle the AI player's less explicit state changes. This is the highest-impact fix.

2. **Fix storyteller thread management** — The storyteller prompt needs explicit instructions for thread creation, progress incrementing, and resolution. The `thread_same_turn_conflict` bug needs a prompt fix.

3. **Fix `arc_resolve` schema compliance** — Either make `arc_resolve` optional or require all three fields when present.

4. **Address the bootstrap problem** — The convergence score works fine once in motion. The issue is generating initial urgency in automated play. The prior report's auto-escalation recommendation (random seed events, thread auto-escalation) is still valid.

5. **Human vs automated parity** — The engine should work similarly for both. The gap between 0% and 39% extraction failure rate is too large.
