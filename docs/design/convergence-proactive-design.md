# Convergence Proactive Design

> **Status:** reviewed
> **Source:** `roadmap/bugs/convergence-starvation.md` (validated, root cause confirmed)
> **Evidence:** `docs/discovery/convergence-pacing-evidence.md` (eval data backing the claims below)

> **Review date:** 2026-06-25 (second pass; first pass 2026-06-24)
> **Reviewer:** review-design skill

## Problem Statement

`compute_convergence_score()` in `_pacing.py:86-142` computes a 5-component score that is entirely reactive. Each component depends on state that can remain 0 indefinitely under stealth/avoidance-heavy play styles. The phase machine requires `convergence_score >= 2` for `RISING → CLIMAX`, but when all 5 components are 0, there is no recovery mechanism — convergence deadlocks.

Three components are broken or disabled in practice:
- **`dice_weight`** (+1): requires urgent thread AND a roll AND a fail. Triple-gated — rarely fires even when rolls happen.
- **`beat_streak`** (+1): requires ≥60% pressure beats in last 5. But 34-57% of turns have null beats (storyteller emits no beat), diluting the window. Beat driver is always `"motivation"`, never pressure types.
- **`any_urgent`** (+1): requires the storyteller to escalate a thread to `"urgent"` — which it never does in practice. This is a separate concern (storyteller guidance) but contributes to starvation.

Separately, **CLIMAX → RESOLUTION** is a pure turn-count timeout (default 4 turns). No engine signal can exit early or extend. The curtain_call system provides prompt-level guidance but the engine has no ears — if the storyteller resolves the thread on CLIMAX turn 1, the game stalls for 3 more turns; if the climax is still building at turn 4, the engine force-transitions anyway.

## Current State

### Phase machine

`_compute_scene_phase()` in `_pacing.py:222-294`:

| Transition | Current trigger | Works? |
|------------|----------------|--------|
| SETUP → RISING | urgent thread OR 3-turn TTL | OK — 3-turn timeout works. Urgent-thread early-exit path dead in practice |
| RISING → CLIMAX | `convergence_score >= 2` | BROKEN — convergence can stay 0 forever |
| CLIMAX → RESOLUTION | 4-turn hard cap | WEAK — no signal, just a timer |
| RESOLUTION → BREATHER | Always (1 turn) | FINE |
| BREATHER → RISING | urgent thread OR 3-turn TTL | OK — same as SETUP. 3-turn recovery is reasonable |

SETUP → RISING and BREATHER → RISING always take exactly 3 turns because the urgent-thread path never fires. Acceptable for now — 3 turns of setup or recovery is reasonable.

### Existing convergence components (`_pacing.py:86-142`)

| # | Component | Signal | Fires? |
|---|-----------|--------|--------|
| 1 | `any_urgent` | Non-dormant thread with `urgency="urgent"` | Rarely — storyteller never escalates |
| 2 | `any_threat` | Non-dormant thread with `type="threat"` | Reliably — most threads are threat type |
| 3 | `scene_age` | `scene_age >= scene_pressure_threshold` (3) | Reliably — age always increments |
| 4 | `beat_streak` | ≥60% of last 5 beats are pressure types | Rarely — null beats (type=None) don't count |
| 5 | `dice_weight` | urgent thread AND rolled AND band in fail/crit_fail | Barely ever — triple-gated |

### Dead code

- **`avoidance_keywords`** (`EngineConfig.avoidance_keywords`, `config.py:152`): defined, populated from config, never consumed anywhere. Zero runtime references outside config.

### Relevant functions

| File | Line(s) | Function |
|------|---------|----------|
| `_pacing.py` | 86-142 | `compute_convergence_score()` |
| `_pacing.py` | 222-294 | `_compute_scene_phase()` — phase machine |
| `narrate.py` | 204-211 | Invocation of `compute_convergence_score()` |
| `narrate.py` | 238-266 | Convergence component booleans (mirrors core function) |
| `turn_state.py` | 478-486 | `recent_beats` append + cap (after extraction; convergence reads prior turns' beats) |
| `turn.py` | 139-144 | `recent_rolls` append for spiral detection |
| `config.py` | 146 | `avoidance_keywords` (dead); also deserialization at line 280 |
| `turn_context.py` | 41-48 | `PacingContext` dataclass |

## Target State

Two reforms:

### Reform 1: RISING → CLIMAX — proactive convergence (7 components)

Replace the 5 reactive components with 7 components (6 boolean + 1 integer floor).

#### 1. `any_urgent` — UNCHANGED
+1 if any non-dormant thread has `urgency="urgent"`.
Field: `"urgent_thread": 0|1`

#### 2. `any_threat` — UNCHANGED
+1 if any non-dormant thread has `type="threat"`.
Field: `"threat_thread": 0|1`

#### 3. `scene_age` — UNCHANGED
+1 if `scene_age >= scene_pressure_threshold` (default 3).
Field: `"scene_age": 0|1`

#### 4. `beat_streak` — REPAIRED
+1 if ≥60% of last 5 beats are pressure types. **When a beat entry has `type=None`, carry over the type from the chronologically previous non-null entry in the window.** Reflects the 2-turn TTL: a null beat means the prior beat is still narratively active.

```
pressure_types = set(BEAT_BUCKETS["pressure"])
last_non_null_type = None
pressure_count = 0
for b in window:
    bt = b.get("type")
    if bt is not None:
        last_non_null_type = bt
    if last_non_null_type in pressure_types:
        pressure_count += 1
threshold = ceil(n * 0.6) if n < 5 else 3
score += 1 if pressure_count >= threshold
```

If all beats in the window are null (no prior non-null beat exists), `last_non_null_type` stays `None` and `pressure_count` = 0, so beat_streak = 0. This is correct: no pressure beats means no pressure streak. The `stall_floor` component handles deadlock prevention in this case.

Field: `"beat_streak": 0|1`

#### 5. `roll_starvation` — NEW
+1 if no roll has occurred in `config.roll_starvation_threshold`+ turns. Computed from `recent_rolls` (most-recent-first, capped at 5).

```
turns_since_last_roll = current_turn - recent_rolls[0]["turn"] if recent_rolls else None
score += 1 if turns_since_last_roll is not None and turns_since_last_roll >= config.roll_starvation_threshold
```

If no roll has ever occurred in the game (`recent_rolls` empty), this stays 0 — not punishing turn-1 avoidance or very slow games.

Field: `"roll_starvation": 0|1`
Config: `roll_starvation_threshold`, default `3`.

#### 6. `threat_density` — NEW
+1 if the number of active (non-dormant) threat-type threads ≥ `config.threat_density_threshold`. High threat saturation means pressure even without individual urgency.

```
active_threat_count = count of t where t.get("type") == "threat" and not t.get("dormant", False)
score += 1 if active_threat_count >= config.threat_density_threshold
```

Field: `"threat_density": 0|1`
Config: `threat_density_threshold`, default `3`.

#### 7. `stall_floor` — NEW
Proactive floor that increments when convergence stays below threshold. **Global across all arcs and scenes** — not reset on arc boundaries or phase transitions. This is intentional: persistent convergence starvation indicates a systemic pacing problem that should accumulate pressure regardless of narrative context.

State tracking: `meta.consecutive_low_convergence` (int, default 0), incremented in `narrate.py:_narrate_setup()` immediately after `compute_convergence_score()` returns, reset to 0 when `>= convergence_threshold`.

```
if consecutive_low_convergence >= 3:
    floor = 1 + ((consecutive_low_convergence - 3) // 3)
    score += min(floor, stall_floor_max)
```

Field: `"stall_floor": int` (not 0|1 — can be >1)
Config: `stall_floor_max`, default `3`. Cap at 3.

### Reform 2: CLIMAX → RESOLUTION — signal-gated exit

Replace the hard 4-turn cap with a signal-gated system. The base limit stays 4, but engine signals can exit early or extend.

#### Early exit

Transition CLIMAX → RESOLUTION when:
```
a thread was resolved this turn AND convergence_score < 2
```

The thread resolution is the natural narrative endpoint. Convergence < 2 ensures the resolved thread was genuinely the main pressure source — if another thread is still urgent, convergence stays high and the climax continues.

**Implementation note:** The early-exit check should NOT read the in-flight `storyteller_result.thread_resolve` (which is not yet available at `_compute_scene_phase`'s call site — it's produced later by the extraction pipeline). Instead source the signal from state: `thread_resolved_prev_turn = any(ct for ct in (state.get("arc", {}) or {}).get("completed_threads", []) if ct.get("resolved_turn") == turn_no - 1)`. This matches how every other phase transition sources its inputs (end-of-prior-turn state). One-turn delay is consistent with the existing RISING→CLIMAX pattern (turn-1 resolve → CLIMAX turn-2's phase is RESOLUTION).

#### Extension

If at turn 4 (`climax_turn_limit`) the climax is still building, extend the cap:
```
if climax_turn_count >= config.climax_turn_limit AND convergence >= 3 AND has_urgent_active_thread:
    extend by up to config.extension_max additional turns
```

`has_urgent_active_thread` is computed inline in `_compute_scene_phase()` by iterating over `state['arc']['threads']` — same pattern as the existing SETUP transition thread count (lines 249-253 of `_pacing.py`). One pass over threads for both checks.

The extension is recalculated each turn. As soon as conditions clear (or the extended cap is reached), transition.

**Convergence=2 gap:** Convergence=2 falls through both early exit (`< 2` required) and extension (`>= 3` required). At convergence=2, the game stays in CLIMAX until turn 4 or 6. This is intentional — convergence=2 is borderline and the design treats it as "stay in CLIMAX."

#### Absolute maximum

`config.climax_turn_limit + config.extension_max` = 4 + 2 = **6 total CLIMAX turns maximum**. After turn 6, the engine forces RESOLUTION regardless. This is the hard safety net.

```
elif phase == "CLIMAX":
    climax_turn_count += 1
    # Early exit — evaluated EVERY CLIMAX turn (not just at the limit).
    # Signal sourced from state (end-of-prior-turn), not in-flight storyteller_result.
    thread_resolved_prev_turn = any(
        ct for ct in (state.get("arc", {}) or {}).get("completed_threads", [])
        if ct.get("resolved_turn") == turn_no - 1
    )
    if thread_resolved_prev_turn and convergence_score < 2:
        phase = "RESOLUTION"
        climax_turn_count = 0
    # Hard cap + extension — only evaluated at/after the limit
    elif climax_turn_count >= config.climax_turn_limit:
        if convergence >= 3 and has_urgent_active_thread:
            if climax_turn_count >= config.climax_turn_limit + config.extension_max:
                phase = "RESOLUTION"          # hard safety net
                climax_turn_count = 0
            # else stay in CLIMAX (extension active)
        else:
            phase = "RESOLUTION"
            climax_turn_count = 0
    # else: stay in CLIMAX (below limit, no early-exit signal)
```

`has_urgent_active_thread = any(t for t in state["arc"]["threads"] if t.get("urgency") == "urgent" and not t.get("dormant", False))`. Do NOT copy the existing `_pacing.py:249-253` `thread_urgency_count` pattern verbatim — that pattern does not filter dormant threads, which is a pre-existing latent bug (out of scope for this design).

### Removing `dice_weight`

Removed. Triple-gated, rarely fired even with active play, conflated player failure with narrative pressure.

### Removing `avoidance_keywords`

Removed. Dead code — defined in `EngineConfig` but never consumed anywhere. No runtime references, no YAML consumers. Delete config field, deserialization, and any related import.

### State model changes

| Field | Scope | Type | Owner |
|-------|-------|------|-------|
| `meta.consecutive_low_convergence` | Add | `int`, default 0 | `turn_state.py` — updated every turn after convergence computed; reset on cancel/retry |

### `EngineConfig` changes

| Key | Action | Default | Notes |
|-----|--------|---------|-------|
| `avoidance_keywords` | Remove | — | Dead code |
| `roll_starvation_threshold` | Add | `3` | Turns without a roll before +1 |
| `threat_density_threshold` | Add | `3` | Active threat threads before +1 |
| `stall_floor_max` | Add | `3` | Cap on stall floor extra score |
| `extension_max` | Add | `2` | Max additional CLIMAX turns beyond `climax_turn_limit` |

### `PacingContext`

No new fields. `convergence_components: dict[str, int]` accommodates arbitrary keys. Export new keys (`roll_starvation`, `threat_density`, `stall_floor`), remove `dice_weight`.

### Templates

### Templates

**Narrator prompt — `curtain_call` strengthened.** The narrator is authoritative on when a thread comes to an end (it decides what the story is; the storyteller merely records it). The existing `curtain_call` signal (`active` at CLIMAX turn 1, `forced` at the limit) is the right channel — it already tells the narrator to bring the climax home. The reform strengthens this nudge so the narrator reliably resolves the climax thread in the prose: when `curtain_call` is `active` or `forced`, the narrator prompt makes explicit that the main pressure thread should reach its conclusion this turn. This is a prompt template change (the original "no prompt template changes" claim is dropped).

**Storyteller prompt — light secondary nudge.** The storyteller is a recorder of what the narrator wrote, so it cannot be the primary lever. A light, optional nudge guides the storyteller to lower its threshold for emitting `thread_resolve` in CLIMAX/RESOLUTION phases — if the narrator resolved the thread in the prose, the storyteller should record that resolution as a `thread_resolve` event rather than reframing it as a `thread_update`. Without this, the narrator may resolve while the storyteller fails to record it, leaving `completed_threads` empty and starving the early-exit signal.

**Hard cap (turn 6) does not force thread closure.** When the engine advances CLIMAX→RESOLUTION at the hard cap without a recorded `thread_resolve`, the thread is not closed by the engine — the narrator narrates the aftermath (RESOLUTION/BREATHER) however it sees fit. The un-resolved thread may carry into the next arc; the engine does not retroactively close it.

Convergence score and phase transitions themselves remain engine-side. `PacingContext` propagates `convergence_score` to logs via `summary`; `convergence_components` available for debug rendering.

## Scenario Math

All RISING scenarios use the 7-component score with threshold=2. Components that fire marked `✓`. Stall floor shown only when >0.

### A: Aggressive fighter (rolls every turn, threat threads exist, some beats)

| Turn | U | T | A | B | R | D | F | Σ | Phase |
|------|---|---|---|---|---|---|---|---|-------|
| T1 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | **1** | RISING |
| T2 | 0 | ✓ | 0 | ✓ | 0 | 0 | 0 | **2** | → CLIMAX |
| T3 | 0 | ✓ | ✓ | ✓ | 0 | 0 | 0 | **3** | CLIMAX |

→ CLIMAX at T2. One threat thread + normal beats is enough by turn 2.

### B: Stealth rogue (no threat threads, no beats at all, no rolls — pure starvation)

Isolates `stall_floor`. `roll_starvation` stays 0 by rule (never any roll). `beat_streak` stays 0 (no prior non-null beat to carry over). Only `scene_age` and `stall_floor` can fire.

| Turn | U | T | A | B | R | D | F | clc | Σ | Phase |
|------|---|---|---|---|---|---|---|-----|---|-------|
| T1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | **0** | RISING |
| T2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | **0** | RISING |
| T3 | 0 | 0 | ✓ | 0 | 0 | 0 | 0 | 3 | **1** | RISING |
| T4 | 0 | 0 | ✓ | 0 | 0 | 0 | 1 | 4 | **2** | → CLIMAX |

→ CLIMAX at T4 via stall_floor. **This is the only scenario where stall_floor is the deciding component. Permanently stuck under the old system (would run ∞ at Σ=0).**

### C: Social/political player (rolls charisma, 1-2 non-threat threads, no threats)

| Turn | U | T | A | B | R | D | F | Σ | Phase |
|------|---|---|---|---|---|---|---|---|-------|
| T1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **0** | RISING |
| T2 | 0 | 0 | 0 | ✓ | 0 | 0 | 0 | **1** | RISING |
| T3 | 0 | 0 | ✓ | ✓ | 0 | 0 | 0 | **2** | → CLIMAX |
| T4 | 0 | 0 | ✓ | ✓ | 0 | 0 | 0 | **2** | CLIMAX |

→ CLIMAX at T3 via scene_age + beat_streak. **Stall_floor does NOT fire here** — reaching threshold at T3 resets `consecutive_low_convergence` to 0, so T4's stall_floor input is 0. T4 stays at Σ=2 (scene_age + beat_streak) in CLIMAX. This was mis-stated in the first pass (which claimed "stall_floor catches at turn 4" — never true for this scenario).

### D: High-threat-density arc (5 active threads, 3 are threat type)

| Turn | U | T | A | B | R | D | F | Σ | Phase |
|------|---|---|---|---|---|---|---|---|-------|
| T1 | 0 | ✓ | 0 | 0 | 0 | ✓ | 0 | **2** | → CLIMAX |

→ CLIMAX at T1. any_threat + threat_density fire immediately on turn 1.

### E: Mixed activity (some rolls, 3 active threads, 2 threats, variable beats)

| Turn | U | T | A | B | R | D | F | Σ | Phase |
|------|---|---|---|---|---|---|---|---|-------|
| T1 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | **1** | RISING |
| T2 | 0 | ✓ | 0 | 0 | 0 | 0 | 0 | **1** | RISING |
| T3 | 0 | ✓ | ✓ | ✓ | 0 | 0 | 0 | **3** | → CLIMAX |

→ CLIMAX at T3. Scene_age + any_threat + beat_streak.

### RISING→CLIMAX summary

| Persona | Old (avg) | New (avg) | Worst case |
|---------|-----------|-----------|------------|
| Aggressive fighter | 2-3 | T2 | T3 |
| Stealth rogue (no beats/rolls/threads) | ∞ (stuck) | T4 (via stall_floor) | T4 |
| Stealth rogue (some beats, occasional roll) | ∞ (stuck) | T3 | T4 |
| Social/political | 3-5 | T3 | T3 |
| High-threat-density | T1 | T1 | T1 |
| Mixed activity | 2-3 | T3 | T3 |

**No more convergence deadlock. Worst case: 4 turns.**

**Note on `stall_floor`'s actual contribution:** stall_floor only adds to the score in the narrow case where *no other component besides `scene_age`* fires for 3+ consecutive RISING turns — i.e., truly beat-less, roll-less, threat-less, urgency-less stealth. In every other scenario, one of `any_threat`, `beat_streak`, or `roll_starvation` reaches threshold before `consecutive_low_convergence` accumulates enough to contribute. The component is essential for the pure-starvation case (B) but does not contribute to the easier scenarios (C, D, E) — those reach CLIMAX through the other repaired/new components.

## CLIMAX→RESOLUTION scenarios

### F: Thread resolves on CLIMAX turn 1 (early exit)

| CLIMAX turn | Thread resolved? | Convergence | Action |
|-------------|-----------------|-------------|--------|
| T1 | ✓ (resolved) | 0 (pressure dropped) | → RESOLUTION (early exit) |
| T1 | ✓ (resolved) | 2+ (another thread still urgent) | Stay in CLIMAX |

→ Early exit when the resolved thread actually relieves pressure. If convergence stays high, the climax continues for the remaining unresolved thread.

### G: Climax still intense at turn 4 (extension)

| CLIMAX turn | Convergence | Urgent threads | Action |
|-------------|-------------|----------------|--------|
| T4 | 3 | ✓ (1+ urgent) | Extend to T5 |
| T5 | 3 | ✓ (1+ urgent) | Extend to T6 |
| T6 | any | any | Force RESOLUTION (hard cap) |

→ Up to 2 extra turns when the climax is genuinely still building. Hard stop at 6.

### H: Normal climax run

| CLIMAX turn | Convergence | Action |
|-------------|-------------|--------|
| T1 | 3 | Curtain_call=active |
| T2 | 3 | — |
| T3 | 2 | Curtain_call=forced |
| T4 | 1 | → RESOLUTION (no early exit needed, timeout reached) |

→ Normal 4-turn climax, no early exit needed, no extension triggered. Unchanged behavior.

## What is unchanged

- `PacingContext` struct fields (convergence_components dict auto-adapts)
- `BEAT_BUCKETS` and `BEAT_PHASE_MAP`
- `derive_allowed_beat_types()`
- `detect_spiral()`
- `_compute_pacing_context()`
- `_compute_narration_directive()`
- Storytell and Narrate prompt templates
- `convergence_threshold` default (2) and config key
- `climax_turn_limit` default (4) and config key
- Turn viewer / debug panel rendering
- SETUP → RISING transition logic (3-turn TTL unchanged)
- RESOLUTION → BREATHER (always, 1 turn)
- BREATHER → RISING transition logic (3-turn TTL unchanged)

## Review (second pass, 2026-06-25)

Second-pass review against `docs/discovery/convergence-pacing-evidence.md` and current source. Supersedes the 2026-06-24 first-pass review. The first-pass review's note claiming scenario C math was "correct" was itself wrong (it incorrectly assumed convergence stayed 0 through T3); see the corrected analysis under Key Blockers §3.

### Key Blockers

1. **[OK — corrected from FATAL] Signal source for early-exit.** *First-pass concern was wrong.* `_compute_scene_phase()` runs at `narrate.py:214` inside `_narrate_setup()` before the extraction pipeline produces the in-flight `storyteller_result`, but it doesn't need to read the in-flight result: every existing phase decision (`convergence_score`, `recent_beats`, thread dicts) is sourced from `state`, populated at end of the prior turn. Early-exit should follow the same pattern — source "a thread was resolved" from `state["arc"]["completed_threads"]` filtered by `resolved_turn == turn_no - 1` (or equivalent), not from `storyteller_result.thread_resolve`. Plan author: substitute `thread_resolved_prev_turn = any(ct for ct in state["arc"]["completed_threads"] if ct.get("resolved_turn") == turn_no - 1)` for `len(storyteller_result.thread_resolve or []) > 0`. One-turn delay (resolve on CLIMAX T1 → RESOLUTION phase narrated on CLIMAX T2) is consistent with how RISING→CLIMAX behaves today. No pipeline restructuring needed. The original `len(storyteller_result.thread_resolve or []) > 0` pseudocode in lines 176-193 must be replaced accordingly.

2. **[OK — resolved] Early-exit timing.** First-pass pseudocode placed the early-exit check inside `if climax_turn_count >= config.climax_turn_limit` so it could only fire at/after turn 4 — contradicting the Problem Statement's "thread resolves on CLIMAX turn 1, game stalls 3 more turns" motivation. User decision: evaluate early-exit on **every** CLIMAX turn (1-6), with the 4-turn cap acting only as part of the hard fallback. Pseudocode updated above to evaluate the thread-resolve check before the limit gate.

3. **[CRITICAL] Scenario tables B and C have incorrect arithmetic; the design's evidence for `stall_floor` is internally inconsistent.** Working through the increment ordering (floor uses the *previous* turn's `consecutive_low_convergence`; counter increments *after* `compute_convergence_score` and resets when `>= threshold`):
   - **Scenario B ("Stealth rogue, no rolls, null beats"):** table shows `roll_starvation` (R) firing at T3, but the design's own rule (lines 108-112) says R stays 0 when no roll has ever occurred. It also shows `beat_streak` (B) firing at T2, but with "null beats" and no prior non-null beat to carry over, B is 0 per lines 100. Corrected trajectory: T1 Σ=0 (clc=1), T2 Σ=0 (clc=2), T3 Σ=1 (scene_age only, clc=3), T4 Σ=2 via **stall_floor=1** → CLIMAX at **T4, not T3**.
   - **Scenario C ("social/political, no threats"):** table shows `stall_floor`=1 at T4, but at T3 convergence reached 2 (scene_age + beat_streak) and transitioned RISING→CLIMAX, which resets `consecutive_low_convergence` to 0 (per the design's reset rule). At T4, `compute_convergence_score` uses clc=0 → stall_floor=0. So T4 Σ = 2 (scene_age + beat_streak), NOT 3. The first-pass review "confirmed the math is correct" by wrongly assuming convergence was 0 at T2/T3 — it was not. The claim "Stall floor catches at turn 4" for scenario C is **false**; stall_floor cannot fire there because other components reach threshold first and reset the counter.
   - **Implication:** `stall_floor` only actually contributes in the narrow case where *no other component fires for 3+ consecutive turns* (pure stealth: no rolls ever, no threat threads, all-null beats, only scene_age eventually firing alone — insufficient to reach threshold). The design should add that isolating scenario and stop claiming stall_floor "catches" in C. The corrected B is the real stall_floor case (T4 climax), not T3.

4. **[OK — resolved] Reform 2 thread-resolve reliability.** First-pass flagged that early-exit depends on `thread_resolve` the LLM rarely emits (Cycle 1-3 rates ~10-17%), so early-exit would rarely fire. User decision reframes the root cause: the narrator is authoritative on when a thread ends (it decides the story); the storyteller is a recorder. The fix is therefore narrator-side: strengthen the existing `curtain_call` nudge so the narrator actually resolves the climax thread in the prose; `thread_resolve` then flows naturally as the extractor's record of the narrator's decision. A light secondary storyteller nudge (lower the threshold for emitting `thread_resolve` in CLIMAX/RESOLUTION) catches the case where the narrator resolves in prose but the storyteller fails to record it. The hard cap at turn 6 advances phase without forcing the thread closed — the narrator narrates the aftermath; an unresolved thread can carry into the next arc. The "no prompt template changes" claim is dropped; the Templates section above now documents both nudges.

### Design Ambiguities

- **`has_urgent_active_thread` dormant filtering.** The design says to compute this "same pattern as the existing SETUP transition thread count (lines 249-253 of `_pacing.py`)." That existing pattern (`thread_urgency_count`) does **not** filter dormant threads — it counts every urgent thread including dormant ones. "Active" implies non-dormant. Plan author must add a `not dormant` filter; do not copy the existing pattern verbatim. (There is also a pre-existing latent bug this reveals: the current `_compute_scene_phase` SETUP/BREATHER urgent-thread triggers use `thread_urgency_count` including dormant urgent threads, which can trigger early RISING exit on a dormant-only urgent set. Out of scope for this design but worth noting.)
- **`compute_convergence_score` signature change not stated.** `roll_starvation` needs `current_turn`/`turn_no` to compute `turns_since_last_roll`, which is not in the current signature (`scene_phase, active_threads, scene_age, recent_beats, current_outcome, config`). Plan author must add a `turn_no` (or `current_turn`) parameter. `threat_density` uses `active_threads` (already passed) — OK.
- **`_compute_scene_phase` signature change not stated.** Reform 2's early-exit needs `turn_no` (to filter `completed_threads` by `resolved_turn == turn_no - 1`) and the `state` dict (already passed). No signature redesign needed beyond adding `turn_no`.
- **`stall_floor` "global" property is partly moot.** The counter resets when `convergence >= threshold`, which is exactly the RISING→CLIMAX condition, so it *does* reset on that phase transition despite the prose saying "not reset on phase transitions." The global property only meaningfully applies across BREATHER→RISING cycles (a stall in the next RISING continues accumulating). Design should state this precisely: "global across BREATHER→RISING; resets on reaching threshold (which coincides with RISING→CLIMAX)."
- **`convergence=2` during CLIMAX.** Falls through early exit (`< 2`) and extension (`>= 3`); hits the `else` branch → RESOLUTION at turn 4. So convergence=2 resolves at the limit, not "stays until 4 or 6" as the design's note implies — "6" only applies at convergence≥3+urgent. Plan author should document: convergence=2 → RESOLUTION at turn 4 (the else branch), convergence≥3+urgent → possible extension to 6.

### Suggested Improvements

- **Add a "pure starvation" scenario that actually exercises `stall_floor`.** Construct: stealth persona, no rolls ever, no threat/urgent threads, all-null beats. Show T1 Σ=0, T2 Σ=0, T3 Σ=1 (scene_age), T4 Σ=2 via stall_floor → CLIMAX. This is the only scenario where stall_floor is the deciding component; the current tables don't isolate it.
- **Fix the existing `dice_weight` mirror bug while rewriting.** `narrate.py:260-264` mirror uses `thread_urgency_count >= 1` (no dormant filter) whereas the real `compute_convergence_score` uses `any_urgent` (filters dormant). The mirror is being rewritten for 7 components anyway; make the new mirror compute each component from the same primitives as the core function (or, better, have the core function return both score and components to eliminate the mirror entirely).
- **Eliminate the narrate.py mirror by returning components from `compute_convergence_score`.** The design notes the mirror "MUST match" the core function (narrate.py:238 comment). Two sources of truth is a recurring bug source (this pre-existing dormant-filter divergence is the proof). Recommended: `compute_convergence_score` returns `(score, components_dict)`; narrate.py just uses the returned dict. Removes ~30 lines of duplicated logic and the entire class of mirror-drift bugs.
- **Add a `convergence_dead_spot` checker.** Per the evidence doc, `ccya/ev/checkers/convergence.py` only validates internal consistency (sum matches, transition at threshold) — that's why all recent evals pass 1.0 while the system has documented score=0 dead spots. Without a checker that fails on >2 consecutive RISING turns with score < 1, the same silent deadlock will recur after this reform. Not strictly a design-doc concern but the design should call it out as a required follow-up.

### Minor Notes

- **`PacingContext` docstring** (`turn_context.py:47`) says "5-component score" — update to "7-component" or just "convergence score."
- **`compute_convergence_score` docstring** (`_pacing.py:94`) says "5-component" and line 96 says threshold default 3 — source default is 2 (`config.py:162`). Update both during implementation.
- **Line refs corrected in this pass:** `config.py` avoidance_keywords is line 146 (plus deserialization at 280), `turn_state.py` recent_beats is at 478-486 (not 420-433). Both fixed in the table above.
- **`threat_density` fires at T1** with 3+ active threats (Scenario D) — confirmed acceptable; high-threat arcs reaching CLIMAX turn 1 is intentional.
- **`avoidance_keywords` removal is safe** — `rg` confirms only `config.py` references it (field at 146, deserialization at 280). No tests, templates, or YAML consumers.
