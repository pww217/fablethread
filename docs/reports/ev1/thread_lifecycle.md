# Thread Lifecycle & Arc Management — Turn 1 to 10

## Overview

Evaluates thread lifecycle management in `ccya/engine/turn.py`: creation, advancement, dormancy/demotion, resolution, and urgency aging. Data sourced from events.jsonl extraction.storytell.output (thread_advance, thread_resolve, thread_add), ev.py Active Threads section, and state.yaml arc.threads.

---

## Thread Inventory Per Turn

| Turn | Active Scene Threads | Active Arc Threads | Prompt-Only Dormant Threads (campaign background in prompt context, not state) |
|------|---------------------|--------------------|------------------------------------------|
| 1-9 | siege_escalation [URGENT] | impressed_vessel [NORMAL] | sabotage_investigation, black_market_escape, coalition_enforcement |
| 10 | siege_escalation [URGENT] | impressed_vessel [NORMAL, last_seen T9] | (dropped from prompt after compaction) |

**Total threads in state.yaml:** 2 unique thread IDs (siege_escalation, impressed_vessel). An additional 3 threads (sabotage_investigation, black_market_escape, coalition_enforcement) exist only as prompt-text campaign background in `extraction.storytell.rendered_user` — they are NOT state-managed ArcThread objects. `western_gate_breach_chaos` was emitted as `thread_add` by LLM on T1 but never applied to state (absent from `applied.thread_add` across all turns). No threads resolved or completed on any turn.

---

## Thread Operations Per Turn

| Turn | Band | thread_advance | thread_add | thread_resolve |
|------|------|---------------|------------|----------------|
| 1 | fail | siege_escalation | western_gate_breach_chaos (scene, urgent) | — |
| 2 | no roll | siege_escalation | — | — |
| 3 | no roll | siege_escalation | — | — |
| 4 | fail | — | — | — |
| 5 | partial | siege_escalation | — | — |
| 6 | partial | — | — | — |
| 7 | no roll | siege_escalation | — | — |
| 8 | partial | — | — | — |
| 9 | partial | impressed_vessel | — | — |
| 10 | fail | siege_escalation | — | — |

**Advance frequency:** siege_escalation advanced on 7 of 10 turns (T1,2,3,5,7,9,10). impressed_vessel advanced once on T9. western_gate_breach_chaos was emitted as `thread_add` by LLM on T1 but never stored in state (not in `applied.thread_add`, not in state.yaml).

---

## Urgency Analysis Per Turn

| Thread | Scope | Urgency | Last Seen | Progress | Added Turn? | Managed in State? |
|--------|-------|---------|-----------|----------|-------------|------------------|
| siege_escalation | scene | urgent (constant) | None | 0 | No | Yes — state.yaml |
| impressed_vessel | arc | normal | T9 | 1 | No | Yes — state.yaml |
| western_gate_breach_chaos | scene | urgent (constant) | None | 0 | Not persisted | No — emitted by LLM on T1 but never applied to state |

**Urgency never changed on any thread across all 10 turns.** Urgency values are assigned by LLM on creation/update and never auto-decayed. siege_escalation remains [URGENT] throughout despite being advanced on most turns without resolution or progress increment (progress stays at 0).

---

## Directive Priority Stack Verification

`_compute_narration_directive()` in `turn.py:512-603`:
```python
Priority order (highest to lowest):
  1. Breathe         -- narrative_velocity < -0.3
  2. Scene Imperative -- effective_age >= 5
  3. Overwhelm       -- 3+ urgent threads
  4. Resolve a Threat -- aged-out threat pressure
  5. Pressure        -- 1-2 urgent threads
  6. Tension         -- background urgency threads only
  7. Scene Pressure  -- effective_age >= 3
  8. Threat Pressure -- normal urgency aging toward imperative
```

### Urgent thread count per turn:

| Turn | Urgent Threads (scope=scene) | Expected Directive (no velocity override) | Actual Directive | ✓/✗ |
|------|-----------------------------|------------------------------------------|-----------------|-----|
| 1 | siege_escalation [URGENT] → count=1 | Pressure | Pressure | ✓ |
| 2 | siege_escalation [URGENT] → count=1 | Pressure | Pressure | ✓ |
| 3 | siege_escalation [URGENT] → count=1 | Pressure | Pressure | ✓ |
| 4 | siege_escalation [URGENT] → count=1 | Pressure (but velocity < -0.3) | Breathe | ✓ |
| 5-9 | siege_escalation [URGENT] → count=1 | Pressure (but velocity < -0.3 on all) | Breathe | ✓ |
| 10 | siege_escalation [URGENT] → count=1 | Pressure (but beat_locked overrides) | "Breathe; Resolve a Threat" | ✓ |

**Directive mapping is correct:** 1 urgent scene-scoped thread maps to Pressure on T1-3. Breathe on T4-T9 due to narrative_velocity < -0.3 overriding urgency-based directives. Beat lock on T10 appends "Resolve a Threat".

---

## Urgency Aging Verification

`_compute_threat_ages()` in `turn.py:665-686`:
```python
# Only includes threads with scope=scene AND added_turn > 0
added_turn = t.get("added_turn") or t.get("last_seen_turn")
if not added_turn or added_turn == 0: continue
age = current_turn - added_turn
```

"Resolve a Threat" urgency aging logic in `_compute_narration_directive()` (line 560-564):
```python
old_immediate = [t for t in threat_ages if t.get("urgency") == "urgent" and t.get("age", 0) >= 3]
if old_building or old_background or old_immediate:
    primary = "Resolve a Threat"
```

### Urgency aging per thread:

| Thread | added_turn? | Appears in _compute_threat_ages()? | Age on T10 | Would trigger Resolve a Threat if age >= 3? |
|--------|-------------|-----------------------------------|------------|-------------------------------------------|
| siege_escalation | No (seeded, never assigned) | NO — skipped by added_turn check | N/A | Never fires for this thread |
| western_gate_breach_chaos | Not persisted (thread_add never applied) | NO — not in state.yaml | N/A | Never fires — thread not stored |

**Key finding:** siege_escalation has NO `added_turn` assigned. It was seeded during scene generation (`ccya/engine/seed.py:334-339`) which only sets active=True on dormant threads, never assigning added_turn. Therefore `_compute_threat_ages()` skips it and "Resolve a Threat" urgency aging can never fire for this thread regardless of how many turns pass.

---

## Dormancy/Demotion Verification

`_apply_thread_signals()` in `turn.py:159-320`:
```python
# Arc threads only — scene-scoped excluded (line 274-276)
if t.last_seen_turn is not None and (turn_no - t.last_seen_turn >= _EXPIRE_SILENT_TURNS):
    # Expired -> demote to latent, reset timer
```

Config: `_EXPIRE_SILENT_TURNS = 5` (line 150). Latent cap enforced at line 256-266.

### Dormancy per thread:

| Thread | Scope | last_seen_turn? | Demoted on T10? | Expected Behavior |
|--------|-------|----------------|-----------------|------------------|
| siege_escalation | scene | None (never assigned) | N/A — excluded from _apply_thread_signals() | Scene-scoped threads NOT managed by Python lifecycle; expire via age rules only |
| impressed_vessel | arc | T9 | No (only 1 turn since last_seen, needs >=5) | Correct: not yet expired |
| sabotage_investigation (prompt-only) | arc (prompt) | Never | N/A — not a state-managed thread | Exists only as campaign background text in storyteller prompt; no latent cap applies |

**Scene-scoped threads are excluded from Python lifecycle management.** Line 274-276: `if getattr(t, "scope", "arc") != "arc": updated_threads.append(t)` — scene-scoped threads pass through unchanged. They only age via `_compute_threat_ages()` for directive computation and never get demoted to latent by Python code.

---

## Thread Resolution Verification

No thread_resolve entries on any turn across the entire dataset (T1-T10). Both state-managed threads (siege_escalation, impressed_vessel) remain active with no resolution states assigned. This is consistent with a short scene where no tensions reach completion threshold (`config.thread_completion_threshold`).

Progress values:
- siege_escalation: progress=0 on all turns despite being advanced on T1,2,3,5,7,9,10 (progress never incremented — extraction.storytell.output shows advance but state.yaml shows 0)
- impressed_vessel: progress=1 on T9 after advancement

**Note:** Progress increment logic in `_apply_thread_signals()` line 215-216 increments `t.progress + 1` when thread is advanced. But siege_escalation shows progress=0 despite being advanced on most turns — this suggests either (a) extraction.storytell.output.thread_advance contains IDs that don't match the actual ArcThread.id in state, or (b) there's a mismatch between advance signal and state update.

---

## Issues Found

### 1. Seeded scene-scoped threads never get added_turn assigned (high concern)
`siege_escalation` is seeded during scene generation with urgency=urgent but no `added_turn`. This means:
- `_compute_threat_ages()` skips it entirely (line 675-677 requires added_turn > 0 or last_seen_turn, and siege_escalation has neither)
- "Resolve a Threat" urgency aging can never fire for this thread regardless of age
- The urgent count on every turn comes from ALL scene-scoped threads with urgency=urgent, but these seeded threads have no age tracking

**Impact:** Urgency-based directives (Pressure/Overwhelm based on urgent count) work correctly because they don't require added_turn. But the aging path to "Resolve a Threat" is broken for all seeded scene-scoped threads. This means if a player never addresses an urgent seeded thread, it stays [URGENT] forever and never ages out via directive escalation — only narrative_velocity (momentum-based) can override Pressure directives.

### 2. Urgency never auto-decays on any thread (medium concern)
All urgency values remain constant across all 10 turns: siege_escalation is always urgent, impressed_vessel always normal. No automatic decay mechanism exists — urgency only changes if LLM updates it via thread_add/update extraction output. The extraction prompt (`ccya/prompts/storytell_system.j2`) does not instruct the LLM to decay urgency over time or demote threads based on age.

**Impact:** Urgent seeded threads stay urgent indefinitely unless the player addresses them and the LLM decides to update their urgency on a subsequent thread_add/update call. This creates persistent Pressure directives that never naturally de-escalate through aging alone.

### 3. progress=0 for siege_escalation despite frequent advances (low concern)
siege_escalation is advanced on T1,2,3,5,7,9,10 but state.yaml shows progress=0. This could indicate:
- The extraction.storytell.output.thread_advance IDs don't match the actual ArcThread.id in state (ID mismatch between extraction and stored thread)
- Or _apply_thread_signals() is not finding siege_escalation when processing advances

**Impact:** If progress never increments, threads can never reach `thread_completion_threshold` and complete. This needs investigation to confirm whether it's a data display issue or an actual bug in the advance-to-progress mapping.

### 4. thread_urgency_max_age config exists but is not enforced (low concern)
Config value `thread_urgency_max_age = 8` defined at `ccya/engine/config.py:79` with comment "auto-remove threads older than this" — but no production code references this value for auto-removal. Only used by eval engine mirror (`ccya/eval/engine_mirror.py:23`).

**Impact:** No automatic thread removal based on age exists in production. Threads accumulate indefinitely unless manually resolved or demoted via the 5-turn dormancy path (which only applies to arc-scoped threads, not scene-scoped).

---

## Summary

The thread lifecycle system functions correctly for its core paths: arc-scoped threads advance progress and get last_seen_turn updated on each thread_advance signal, dormant threads are tracked in ev.py Active Threads output, and urgent thread counts map correctly to Pressure directives (1-2 urgent = Pressure, 3+ = Overwhelm). Scene-scoped threads are excluded from Python lifecycle management as designed — they age via `_compute_threat_ages()` for directive computation only.

The main issues are: seeded scene-scoped threads never get `added_turn` assigned during seed generation, breaking the urgency aging path to "Resolve a Threat" directives; urgency values never auto-decay and rely entirely on LLM updates which receive no instructions to decay urgency over time; progress tracking for siege_escalation shows 0 despite frequent advances suggesting an ID mismatch between extraction output and stored threads; and `thread_urgency_max_age` config exists but is never enforced in production code. These issues mean urgent seeded threads persist indefinitely without aging out, creating persistent Pressure directives that only resolve through narrative_velocity overrides (momentum-based Breathe) or beat lock triggers rather than natural urgency decay.
