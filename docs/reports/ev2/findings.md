# Ev2 Analysis Report — Turns 5–11 (Compaction & Thread Lifecycle)

**Date:** 2026-05-27  
**Scope:** Single game save (`saves/default/`) covering turns T1–T11, with focus on compaction behavior and thread lifecycle across the T5→T6 boundary  
**Source Events:** `saves/default/events.jsonl` (11 turns)

---

## What Went Well

- **Compaction mechanics work correctly**: Both T5 (compacted T1–T3 into 3 bullets) and T10 (compacted T4–T8 into 5 bullets) produced valid COMPACTED events with bullet previews, sanitization data, token counts, and timing. Chronicle.md was updated correctly on both runs.
- **Orphan condition lifecycle tracking**: `acid_splash` added at T8 has proper turns_remaining counter decrementing across T9→T10→T11 (3→2→1). Orphan removal logic fires correctly when count reaches 0.
- **Beat type distribution under threshold**: Pressure 45%, breathing_room 27%, escalation 18%, complication 9% — all within normal ranges, no repetition issues detected in this game window.

---

## Critical Findings (Highest → Lowest Priority)

### C1. All scene-scoped thread_add entries silently dropped after T5 — key branch has no add fallthrough
**Severity: CRITICAL**  
**Scope:** All LLM-generated scene-scoped thread_add emissions, affects every game with compaction  

The root cause of empty directives T6–T11 is NOT the compactor alone — it's a code bug in the `thread_add` processing chain at `turn.py:1275` that silently drops ALL scene-scoped thread_add entries that have a `key` field. This means the LLM tries to create new scene threads (T7: `the_bridge_stalker`, T8: `the_mechanical_beast_siege`, T9: `the_spencermouth_collapse`, T11: `the_vanishing_runner`) but the engine discards every one.

**Root cause - the key-branch black hole (turn.py:1275):**
The `thread_add` if-elif chain has three relevant paths:
1. `elif _new_thread.key:` (line 1275) — for threads WITH a key. Checks for exact key collision. If collision found: logs warning, `pass` (skip). If NO collision found: **falls through the entire branch doing nothing**. There is no `else` clause to proceed with adding the thread.
2. `elif _scope == "scene": pass` (line 1297) — for threads WITHOUT a key that are scene-scoped. Runs `pass` (skip). Only reachable when key is falsy.
3. `else:` (line 1301) — for threads WITHOUT a key that are arc-scoped. This is the **only path that actually adds threads to state**. Only reachable when both key is falsy AND scope is NOT "scene."

Every scene-scoped thread_add emitted by the LLM in this game (T7, T8, T9, T11) has a non-null `key` field (e.g., `entity_aggression`, `entity_attack`). They all enter branch 1, pass the collision check (no existing thread has those keys), and then silently fall through without being added.

**How bridge_security existed before T5:**
`bridge_security` was a SEEDED thread (part of `envelope.arc.threads` from `seed.py:330–339`), not added via game-time `thread_add`. It bypassed the broken code path entirely. Seeded threads enter state directly from the seed envelope without going through the `thread_add` if-elif chain.

**The compactor's role:**
T5 compaction DID remove `bridge_security` via `pressure_remove=[{'id': 'bridge_security', 'confidence': 'high'}]`. After removal, no scene-scoped threads remain in state. The LLM tries to replenish via `thread_add` but every attempt hits the key-branch black hole. State stays empty, directives stay empty.

**Evidence chain (all verified from raw events.jsonl):**
1. T5 compaction event: `pressure_remove=[{'id': 'bridge_security', 'confidence': 'high'}]`
2. T1–T5 have non-empty directives (Pressure/Breathe) — proves scene-scoped threads existed pre-compaction
3. T6–T11 all have `pacing_context.directive=""`, `summary="neutral"` — empty after compaction
4. LLM emits scene-scoped `thread_add` on T7, T8, T9, T11 — all with non-null keys
5. `state.yaml` final state has `threads: []` — no scene-scoped threads present
6. `state.yaml` has no `last_thread_creation_turn` — confirms no `thread_add` ever succeeded

**Impact:** After first compaction, narration directives become completely uninformative ("neutral" with no directive). The LLM's attempts to create new narrative threads are silently discarded. The beat system falls back to momentum-based defaults only.

**Fix:** The `elif _new_thread.key:` branch (line 1275–1295) needs an `else` clause after the collision check that falls through to the actual thread-adding code (the same logic in the `else:` block at line 1301). After the key collision check passes (no collision), execution should proceed to add the thread to state rather than silently falling through.

### C2. Compactor removed the only scene-scoped thread — secondary contributor
**Severity: MEDIUM** (downgraded from CRITICAL — compactor is a contributor, not root cause)  
**Scope:** Compaction pipeline  

Even after fixing the key-branch bug, the compactor will still remove the remaining scene-scoped thread during sanitization. The compactor's `_build_compact_messages` builds `pressures` from ALL scene-scoped threads and renders them under "Active Scene Pressures" in `compact_user.j2`. The LLM then recommends removal. After fixing the key-branch, fixing the compactor is a secondary concern — new threads can be added again, but they'll be removed on the next compaction unless the compactor is taught to distinguish resolved from active scene elements.

### C3. Seeded threads missing `added_turn` confirmed (ev1 issue #2)
**Severity: High**  
**Scope:** All seeded scene-scoped threads  

Validated against fresh game: seeded threads never get `added_turn` assigned during seed generation. `_compute_threat_ages()` skips them because it requires `added_turn > 0`.

### C4. Progress=0 for scene-scoped thread advances (ev1 issue #3)
**Severity: Medium-High** (downgraded from Critical)  
**Scope:** Scene-scoped thread advancement only  

Validated against fresh game: `siege_escalation` (scope=scene, from ev1 data) was advanced on multiple turns but progress=0. This is because `_apply_thread_signals()` at line 200 filters to `scope=="arc"` only. Scene-scoped thread_advance is structurally a no-op for progress tracking. Arc-scoped threads DO advance correctly (`supply_sabotage` reached progress=3 and completed). The issue is specific to scene-scoped threads only — arc-thread lifecycle works.

### C5. Urgency never auto-decays confirmed (ev1 issue #6)
**Severity: High**  
**Scope:** All threads  

Validated against fresh game: urgency values remain constant across all turns. No automatic decay mechanism exists in `_apply_thread_signals()`. `thread_urgency_max_age=8` config is never enforced in production code.

### C6. Scene-scoped threads excluded from Python lifecycle (ev1 issue #7)
**Severity: Medium-High**  
**Scope:** All scene-scoped threads  

Validated against fresh game: `_apply_thread_signals()` at line 200 filters to `scope=="arc"` only. Scene threads have no dormancy/demotion, no progress tracking, no completion path.

### C7. Fail near-miss contradiction (ev1 issue #8)
**Severity: Medium**  

Contradiction between narration ("narrate a complication") and storyteller ("Do NOT emit pressure on failed checks") still exists structurally.

### C8. Beat type distribution normal
**Severity: Low (informational)**  

Pressure 45%, breathing_room 27%, escalation 18%, complication 9%. Under >60% threshold for repetition detection. No issues.

### C9. Orphan conditions lifecycle works correctly
**Severity: Low (informational)**  

`acid_splash` at T8 has proper turns_remaining decrement (3→2→1). Removal fires correctly at 0.

### C10. Compactor `pressure_remove` semantics protect arc-scoped threads correctly
**Severity: Low (informational)**  

The compactor's `_apply_sanitization` at `compactor.py:363` has an explicit guard: `t.get("scope") != "scene"` — arc-scoped threads are always preserved during pressure_remove. The code-level protection is correct; the problem is the prompt labeling biases the LLM toward removal.

### C17. Narrator step blind to recent_events (template rendering omission)
**Severity: CRITICAL**  
**Scope:** All narration turns  

The `_narrate_messages()` function at turn.py:920–933 passes full state to the narrator prompt, and `recent_events` IS persisted in state.scene.recent_events (`delta_builder.py:290–326`). However, `narrate_user.j2` never renders them — confirmed by reading all 85 lines of the template.

**Evidence:** Traced `_run_extraction_pipeline` → `_storytell_messages()` at extraction.py:231–280 — `recent_events` IS passed to storyteller step and rendered in `storytell_user.j2:22-25`. But narrate_user.j2 has no section for scene.recent_events despite state containing them.

**Impact:** Contributes directly to "story not related enough to Arc" (playthrough 2026-05-27). Narration lacks continuity with previously established world knowledge — each turn's narration is generated without awareness of what facts were established in prior turns' recent_events lists.

### C18. Storytell step blind to `world_state` due to conditional rendering at storytell_user.j2:26
**Severity: HIGH**  
**Scope:** All extraction/storyteller steps  

The storyteller prompt template (`storytell_user.j2:26`) renders world state only when there are NO threads: `{% if not all_threads and world_state %}`. In normal gameplay where threads exist (which is always), this section never appears in the prompt. The data IS passed to `_storytell_messages()` at extraction.py:250/268 — it's a template rendering bug, not a data flow gap.

**Evidence:** `storytell_user.j2:15–31` — threads section renders unconditionally; world_state section only as `{% else %}` fallback (line 26) with condition `not all_threads and world_state`.

**Impact:** Contributes directly to "failure/neutral outcomes don't open doors" (playthrough 2026-05-27). Without world context, storyteller has no basis for introducing new opportunities after a failed check or neutral outcome.

---

## Root Cause Summary — Narrative Directive Degradation

The empty directives T6–T11 have **two interacting root causes**:

1. **Primary: Key-branch black hole (turn.py:1275)** — All LLM `thread_add` emissions with a `key` field are silently dropped because the `elif _new_thread.key:` branch has no fallthrough to add the thread after passing collision check. This prevents ANY scene-scoped thread from being created via the normal LLM extraction pipeline.

2. **Secondary: Compactor removes seeded threads** — The only scene-scoped thread (`bridge_security`, seeded at game start) was removed by T5 compaction. Even if the key-branch were fixed, the compactor would still remove threads on each compaction cycle unless taught to distinguish resolved from active scene elements.

**The combined effect:** Seeded threads get removed at first compaction, and the LLM's replacements are structurally discarded. Directives converge to empty after T5 and stay empty for the rest of the game — regardless of narrative events (combat, environmental hazards, NPC losses).

---

## Cross-Run Consistency: Ev1 vs Ev2

| Finding | Ev1 Status | Ev2 Validation |
|---------|-----------|----------------|
| C3: Seeded threads missing added_turn | Found in ev1 | Confirmed in fresh game |
| C4: Progress=0 for scene-scoped advances | Found in ev1 | Confirmed — arc advances work, scene advances don't |
| C5: Urgency never auto-decays | Found in ev1 | Confirmed |
| C6: Scene threads excluded from lifecycle | Found in ev1 | Confirmed |
| C7: Fail near-miss contradiction | Found in ev1 | Still present |
| **C1: Key-branch black hole** | NOT found in ev1 | NEW — root cause of empty directives |
| C2: Compactor removes threads | NOT found in ev1 | NEW — secondary contributor |

---

## Summary: Ev2 Unique Contributions

ev1 found surface-level patterns (beat types, momentum tracking) and identified structural thread lifecycle issues. ev2's unique contributions:

1. **Discovered the key-branch black hole** at `turn.py:1275` — the definitive root cause of post-compaction empty directives. All scene-scoped `thread_add` with keys are silently dropped.
2. **Found the compactor secondary contribution** — bridge_security was removed at T5, and even if the key-branch were fixed, compaction would remove replenished threads.
3. **Corrected earlier claims:** progress=0 is scene-thread-only (arc threads advance fine), "bridge_security becoming MORE urgent" was unverifiable and removed.

## Playthrough Observations (2026-05-27)

Two player-throughs confirmed a systemic pacing problem: three systems simultaneously pull toward stasis (C1+C5+C6+M3). Two new template rendering issues identified:
- **Narrator blind to recent_events** — state has them but narrate_user.j2 never renders them, contributing to "story not related enough to Arc"
- **Storytell blind to world_state** — storytell_user.j2:26 `{% if not all_threads and world_state %}` blocks rendering when threads exist (normal gameplay), contributing to "failure/neutral outcomes don't open doors"

Deferred decisions: remove recent_events entirely vs fix template; compactor window shrinking bug (`_compute_recent_window()` resets after each compaction).
