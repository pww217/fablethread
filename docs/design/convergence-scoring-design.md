# Convergence scoring and Curtain Call — phase machine redesign

## Purpose

This document is the design authority for plans implementing the replacement of `crisis_urgency_threshold` with a composite convergence score, the CRISIS→CLIMAX rename, the Curtain Call soft-close mechanism, and removal of dead pacing machinery. It covers changes to the phase machine, beat classification, prompt guidance, and the EngineConfig surface area.

## Problem Statement

The phase machine drives CLIMAX (formerly CRISIS) entry and scene exit using three signals that are individually insufficient:

1. **Thread urgency count** (binary: ≥2 urgent threads → CRISIS) ignores all other context — a single urgent thread with escalating tension can't converge naturally.
2. **`tension_delta` is a dead signal.** Across 80 EV turns (4 saves), the ruling LLM emitted `escalates` 68.8% of the time, `maintains` 31.2%, and `de-escalates` 0%. The prompt guidance prevents de-escalation in CRISIS (most phases), and BREATHER phases always have urgent threads active, triggering the escalation exception. The field has no useful variance.
3. **Scene age** pushes toward RESOLUTION but the phase machine re-enters CLIMAX immediately because the urgent thread is unresolved, creating infinite loops.

The outcome is a phase machine that oscillates between CLIMAX and RESOLUTION/BREATHER without ever escaping combat, and a Scene Imperative directive that tells the LLM to "wrap it up" but provides no mechanical way to comply.

## Constraints

1. **No new extractors.** The extraction pipeline already produces all the data the design needs (beat type, thread urgency, dice rolls, scene age). The change is in `turn.py` and `_pacing.py` only.
2. **No new model shapes beyond EngineConfig fields.** `StorytellerResult`, `ArcThread`, `GMBeat`, `CampaignArc` are unchanged.
3. **No changes to thread sanitizer.** Thread auto-demotion (`thread_urgency_max_age`) and auto-latent (`thread_stale_threshold`) are kept as-is.
4. **Prompt changes required.** The storytell system prompt beat list and Scene Imperative guidance must be updated. The narrate prompt is unchanged.

## Non-goals

- Hard force-close of threads (deferred, Curtain Call is prompt-based soft close only)
- Arc resolution mechanics
- `narrative_velocity` (confirmed dead in live code)
- UI/frontend changes
- NPC lifecycle changes
- Thread sanitizer changes
- `action_stake` field on `IntentEnvelope` (deferred — would improve convergence signal but requires ruling prompt change + new model field; not committed)

## Decision Table

| Decision | What | Why |
|---|---|---|
| CRISIS → CLIMAX rename | All phase names, config field names, log keys, prompt text referencing "CRISIS" renamed to "CLIMAX" | CLIMAX is semantically clearer — this is the narrative turning point, not a death spiral. |
| `crisis_urgency_threshold` deleted | Removed from EngineConfig. No replacement. | Replaced by composite convergence score. No need for both. |
| `crisis_turn_limit` → `climax_turn_limit` | Renamed in EngineConfig. Same default (4). | Scope change only. |
| Convergence score replaces urgency check | Score computed fresh each turn from 5 components, each worth +1, threshold 3. Never persisted. | Composite signal is more robust than any single proxy. Threshold 3 requires multiple independent systems to agree before CLIMAX fires. |
| `tension_delta` removed from `IntentEnvelope` entirely | Field deleted from model, not merely unused. | 0 de-escalates across 80 turns (68.8% escalates, 31.2% maintains). Architecturally wrong signal — ruling engine operates at action level and lacks scene-level context to classify de-escalation. Keeping it creates a future trap for implementers. |
| `spiral_decay_turns` deleted | Removed from EngineConfig. No replacement. | Has no consumer — `detect_spiral()` does not reference it. `recent_beats_max` is the correct decay tuning knob. Dead config implies control that doesn't exist. |
| `setback` classified as pressure-bucket beat | Added to `BEAT_BUCKETS["pressure"]` and `PRESSURE_BEAT_TYPES` | Setback applies negative pressure to the player — it belongs with escalation, complication, and pressure. Streak counting now includes it. |
| Curtain Call added to storytell prompt | Turn 1 of CLIMAX: thread_resolve added to required outputs. Second-to-last turn: narrate + storytell prompts escalate language. CLIMAX always has at least one urgent thread (see convergence score invariant — score cannot reach threshold 3 without one). | Two-tier soft close gives the LLM guidance without mechanical force. The hard cutoff at climax_turn_limit is unchanged. No-thread fallback path removed as unreachable. |
| `derive_enforce_relief()` deleted | Removed from `_pacing.py`. `consecutive_pressure_threshold` config field removed. `consecutive_pressure_beats` state counter removed. | Fired 0/49 turns across two evals — dead code, not fixable by tuning. The convergence score's beat streak component replaces its function more robustly. |
| `PRESSURE_BEAT_TYPES` tuple in turn.py | Updated to include `setback`. | Consistency with BEAT_BUCKETS. |
| BREATHER exit condition | Exits when `thread_urgency_count > 0` OR `breather_turn_count >= breather_max_turns`. Same old rule, explicit. | BREATHER should not use convergence score — a single urgent thread means the character can't rest. |
| `rules.py` module docstring corrected | `raw_die 1 → crit_fail` changed to `final_total ≤ 1 → crit_fail`, `final_total ≥ 12 → crit_success` | Docstring was factually wrong — conditions and skills affect crit probability, which is correct behavior the docstring was misrepresenting. |
| Short-scene beat streak quorum | Use `ceil(n × 0.6)` threshold when buffer has < 5 entries, where n = current buffer size. At n=3 → 2, n=4 → 3, n=5 → 3 (same as original). | Flat quorum 3 at n=3 requires 100% pressure beats — too restrictive. Proportional threshold maintains consistent sensitivity across buffer sizes. |
| `recent_rolls` renamed to `current_outcome` | Parameter on `compute_convergence_score()` renamed; type is `RulesOutcome | None` | Name clarifies semantics — this is the full outcome of the current turn's roll, not a list of recent rolls. |

## Open Questions — All Resolved

All previously flagged open questions are resolved:

| Question | Resolution |
|---|---|
| Band threshold rebalancing | **Decided** — partial ≤8 → ≤7 (see Decision 8 in Change B) |
| Convergence score weighting | **Confirmed** — all five components at +1 for v1. |
| `action_stake` field | **Deferred to Non-goals** — would improve signal but not committed. |
| Curtain Call beat list | **Decided** — `twist` excluded, `setback` added. `breathing_room` in Scene Imperative override only (see Decision 11 in Curtain Call section). |
| Multiple urgent threads | **Confirmed** — +1 for urgency depth (2+ threads) in convergence score. |
| CLIMAX with no urgent thread | **Impossible** — score cannot reach threshold 3 without one. Fallback removed (Decision 7). |
| `spiral_decay_turns` | **Removed** — dead config (Decision 3). |
| `recent_rolls` parameter | **Clarified** — renamed to `current_outcome` (Decision 6). |
| Past-only beat window | **Confirmed** — pending beat never included (Decision 5). |
| Curtain Call thread_resolve contradiction | **Resolved** — CLIMAX always has a thread (Decision 7), no contradiction. |
| `tension_delta` kept vs removed | **Removed entirely** from `IntentEnvelope` (Decision 2). |
| `rules.py` module docstring | **Corrected** — must change to `final_total ≤ 1 → crit_fail`, `final_total ≥ 12 → crit_success` |
| Short-scene beat streak quorum | **Resolved** — `ceil(n × 0.6)` proportional threshold when buffer < 5 |

## Current State — What Exists

### Phase machine (`turn.py:_compute_scene_phase`)

Five states: SETUP → RISING → CRISIS → RESOLUTION → BREATHER (plus BREATHER → RISING back-edge). Entry into CRISIS from RISING fires when `thread_urgency_count >= crisis_urgency_threshold` (default 2). CRISIS exits to RESOLUTION at `crisis_turn_limit` (default 4). RESOLUTION transitions to BREATHER (no location change) or SETUP (location change). BREATHER exits to RISING when `thread_urgency_count > 0` or `breather_max_turns` exceeded.

### Narration directives (`turn.py:_compute_narration_directive`)

Priority stack: Breathe → Scene Imperative → Scene Pressure → (empty). Scene Imperative fires when `effective_scene_age >= scene_imperative_threshold` (default 4). Scene Pressure fires when `effective_scene_age >= scene_pressure_threshold` (default 3). `outcome_hint` overrides to `"transition"` when Scene Imperative is active.

### Beat classification (`_pacing.py`)

BEAT_BUCKETS: pressure → `[pressure, complication, escalation]`, situation → `[revelation, twist, hazard, callback]`, relief → `[opportunity, breathing_room]`. BEAT_PHASE_MAP maps phase → allowed type lists. Scene Imperative overrides to `BEAT_BUCKETS["situation"] + ["opportunity"]`.

### Beat lifecycle (`turn.py` lines 1030-1067)

Storytell output's `gm_beat` is written to `state["meta"]["pending_gm_beat"]` with `beat_expires_turn = turn_no + 2`. `consecutive_pressure_beats` counter on `meta` tracks pressure-type streak. `derive_enforce_relief` injects `breathing_room` when CRISIS + pressure count ≥ 3.

### Problems with Current State

1. **`crisis_urgency_threshold` is too binary.** Two urgent threads trigger CRISIS even without reinforcing signals (bad dice, beat streak, scene age). This was the primary driver of combat spirals.
2. **`tension_delta` is an actively wrong signal.** Across 80 EV turns (4 saves): 68.8% escalates, 31.2% maintains, 0% de-escalates. The ruling engine operates at action level and cannot distinguish genuine de-escalation from scene-level context it doesn't have. This is an architectural mismatch, not a prompt tuning problem. Removed from `IntentEnvelope` entirely.
3. **Scene Imperative lacks resolution-compatible beats.** The allowed list `[revelation, twist, hazard, callback, opportunity]` contains zero beats that end a scene. The LLM has a "wrap it up" directive but no tool to execute it.
4. **`derive_enforce_relief` never fires.** Fired 0/49 turns across two evals. Dead code, not fixable by tuning. The precondition never accumulates because the storyteller naturally diversifies beat types. The convergence score's beat streak component replaces its function more robustly.
5. **BREATHER exit is ambiguous.** The current code at `turn.py:578` checks `thread_urgency_count > 0` but no BREATHER-specific config key documents this. Reader confusion.
6. **Phase machine and prompt contradict each other.** The prompt says "break the loop" (Scene Imperative), but the phase machine re-enters CLIMAX because the urgent thread still exists. The LLM receives conflicting instructions.

## Proposed Solution

### Core Changes

#### 1. CRISIS → CLIMAX rename

Replace all occurrences:
- `EngineConfig.crisis_urgency_threshold` → delete (no replacement)
- `EngineConfig.crisis_turn_limit` → `EngineConfig.climax_turn_limit`
- `state["scene"]["crisis_turn_count"]` → `state["scene"]["climax_turn_count"]`
- `_compute_scene_phase` internal variable `crisis_turn_count` → `climax_turn_count`
- All references in prompt templates, log messages, checkers, and events

#### 2. Convergence score computation (new function in `_pacing.py`)

```python
def compute_convergence_score(
    scene_phase: str,
    thread_urgency_count: int,
    scene_age: int,
    recent_beats: list[dict],
    current_outcome: RulesOutcome | None,
    config: EngineConfig,
) -> int:
    """Compute a composite convergence score (0-5) for CLIMAX entry decisions.
    
    Invariant: CLIMAX entry always implies at least one urgent thread. The dice
    weight component requires an urgent thread, and without thread weight (>=1)
    or urgency depth (>=2), max achievable score is 2 — below threshold 3.
    
    Score computed before storytell runs each turn. Pending beat for current
    turn is never included in streak calculation (prevents pipeline ordering
    problem where storyteller generates beat under RISING rules then finds
    CLIMAX was entered).
    
    Score components (each worth +1):
    1. Thread weight: any urgent thread active (capped at +1)
    2. Urgency depth: 2+ urgent threads simultaneously (additive)
    3. Scene age: scene_age >= scene_pressure_threshold
    4. Beat streak: 3+ pressure-bucket beats in last 5 recent_beats (quorum)
    5. Dice weight: current_outcome.band is crit_fail or fail AND urgent thread exists
    
    Returns 0-5. Threshold 3 = enter CLIMAX.
    """
```

Components in detail:
- **Thread weight (+1):** `thread_urgency_count >= 1`. Capped at 1 regardless of count.
- **Urgency depth (+1):** `thread_urgency_count >= 2`. Additive with thread weight, so 2+ urgent threads = +2 total from thread signals.
- **Scene age (+1):** `scene_age >= config.scene_pressure_threshold` (default 3).
- **Beat streak (+1):** Of the last 5 entries in `state["meta"]["recent_beats"]` (the full buffer), 3 or more have type in the pressure bucket (including `setback`). Uses quorum — tolerates 2 relief beats interspersed in a pressure run and still fires. The pending beat for the current turn is NOT included. Score reads history only.
- **Dice weight (+1):** `current_outcome.band` is `crit_fail` or `fail` AND `thread_urgency_count >= 1`. If no roll occurred this turn (`current_outcome` is None or `current_outcome.rolled` is False), this component scores 0. This is an amplifier — dice weight alone can't reach threshold without an urgent thread.

Score computed fresh each turn, persisted only in the event log. The phase machine in `_compute_scene_phase` reads the score for RISING→CLIMAX transitions, replacing the old `crisis_urgency_threshold` check and the `tension_delta` checks.

#### 3. Phase machine transition changes

**RISING → CLIMAX** (replaces `turn.py:553-562`):
```python
elif phase == "RISING":
    if convergence_score >= config.convergence_threshold:
        phase = "CLIMAX"
        climax_turn_count = 1
```

**All other phase transitions unchanged** (SETUP→RISING, CLIMAX→RESOLUTION, RESOLUTION→BREATHER/SETUP, BREATHER→RISING).

**`tension_delta` removed** from the parameter list of `_compute_scene_phase` and `_compute_narration_directive`.

#### 4. Beat classification changes

`BEAT_BUCKETS["pressure"]` updated in `_pacing.py`:
```python
"pressure": ["pressure", "complication", "escalation", "setback"],
```

`PRESSURE_BEAT_TYPES` in `turn.py` updated to match.

#### 5. Curtain Call (prompt guidance only)

Two-tier escalation applied via the storytell system prompt:

**Turn 1 of CLIMAX:** The storytell user prompt includes a field `curtain_call: "active"` when `climax_turn_count == 1`. The system prompt adds: "CLIMAX phase — you MUST resolve the active thread this scene. Include at least one `thread_resolve` entry in your output."

**Turn >= climax_turn_limit - 1 (second-to-last turn before hard cutoff):** Both narrate and storytell user prompts include `curtain_call: "forced"`. The storytell system prompt escalates to: "This is the final climactic turn. This thread MUST resolve now, for better or worse. The engine will force a transition if you don't."

If the storytell LLM still does not resolve: the engine transitions to RESOLUTION at `climax_turn_count >= climax_turn_limit` regardless. `outcome_hint = "transition"` carries the signal. No hard force-close, no retry loop.

**`breathing_room` scope:** Added to the Scene Imperative override list only — NOT to `BEAT_PHASE_MAP["CLIMAX"]`. The base CLIMAX beat list (`["pressure", "complication", "escalation"]`) is unchanged. Adding `breathing_room` to the base list would let the storyteller defuse CLIMAX on turns 1-2 before Scene Imperative activates. `breathing_room` is only appropriate as a resolution-adjacent beat when Scene Imperative is already active (scene running too long).

**Curtain Call beat list (for Scene Imperative during Curtain Call):** The Scene Imperative allowed list during CLIMAX phase replaces `twist` with `setback`. The final list: `[revelation, hazard, callback, opportunity, setback]` (base CLIMAX list) plus `breathing_room` (Scene Imperative override only). `twist` is excluded because it was the primary source of infinite escalation.

#### 6. Removed machinery

| Component | File | Replacement |
|---|---|---|
| `derive_enforce_relief()` | `_pacing.py:92-94` | Deleted with no replacement |
| `enforce_relief` parameter on `derive_allowed_beat_types()` | `_pacing.py:63` | Deleted |
| `consecutive_pressure_threshold` config field | `config.py:144` | Deleted with no replacement |
| `consecutive_pressure_beats` counter on `state["meta"]` | `turn.py:1042-1050` | Deleted; recent_beats streak replaces |
| `crisis_urgency_threshold` config field | `config.py:157` | Deleted with no replacement |
| `spiral_decay_turns` config field | `config.py` | Deleted with no replacement. `recent_beats_max` is the correct decay tuning knob. |
| `tension_delta` field on `IntentEnvelope` | `models.py` | Deleted from model entirely, not merely unused. |
| `tension_delta` parameter on `_compute_scene_phase` | `turn.py:505` | Removed from signature |
| `tension_delta` parameter on `_compute_narration_directive` | `turn.py:407` | Removed from signature |
| `tension_delta` check in RISING→CLIMAX transition | `turn.py:557-558` | Removed |
| `tension_delta` check in SETUP→RISING transition | `turn.py:550-551` | Removed |

#### 7. EngineConfig changes

New fields:
```python
convergence_threshold: int = 3
climax_turn_limit: int = 4  # renamed from crisis_turn_limit
```

Removed fields:
```python
# crisis_urgency_threshold: int = 2       # deleted
# consecutive_pressure_threshold: int = 3  # deleted
# spiral_decay_turns: int = N              # deleted — no consumer
```

Renamed fields:
```python
# crisis_turn_limit: int = 4  →  climax_turn_limit: int = 4
```

### Alternatives Considered and Rejected

- **Hard force-close of threads (deferred).** The engine could inject a synthetic `thread_resolve` when the LLM fails to resolve. Rejected for v1 because the LLM has been compliant in both evals — it follows the allowed list and required outputs. If Curtain Call guidance is insufficient, add hard close in a follow-up.
- **New beat type (e.g., `scene_resolution`).** A dedicated beat type would require a `GMBeat.type` schema change and extraction wiring. The simpler approach is to use the existing `thread_resolve` structured output field. The LLM already knows how to emit it; it just doesn't because no prompt guidance tells it to.
- **`turn_entered` stamping as scene exit.** The old approach (synthetic location change) bypassed the phase machine entirely and didn't fix the urgency re-entry problem. Abandoned.

## Arc and Thread Integration

### Read-only boundary

The phase machine is **read-only with respect to threads**. It reads:

- `thread_urgency_count` (how many threads are at urgency ≥ `thread_urgency_max_age`) → used in convergence score (threshold depth) and BREATHER exit condition
- Thread urgency depth (2+ urgent threads → +2 instead of +1) → used in convergence score

It never writes to threads. Thread creation, advancement, setback, resolution, and urgency decay are all handled by the storytell and extraction pipeline (`_apply_thread_updates`, `_apply_thread_resolutions`, `sanitize_threads`).

### Curtain Call is prompt-based, not phase-machine-based

The Curtain Call soft-close mechanism uses `thread_resolve` as a structured output field from the **storyteller LLM**, driven by prompt guidance. The phase machine does not inject, force, or synthesize thread resolutions — it only transitions to RESOLUTION at `climax_turn_limit` regardless of resolution state. The storyteller is responsible for resolving threads; the phase machine is responsible for ending the scene.

### Future integration point (explicit non-goal)

The natural future connection is **phase transitions emitting arc-level signals**: CLIMAX entry could trigger a thread escalation hint, BREATHER entry could inject a relief opportunity. This is currently:

- **Not designed** — no model shapes, no mechanism specified
- **Not committed** — deferred until Curtain Call proves insufficient
- **Named here to prevent accidental wiring** — an implementer should not hook the convergence score into `_apply_thread_updates` or bypass the read-only boundary

## Supporting Changes

Three changes work alongside the convergence design to reduce spiral pressure and improve narrative pacing. All were informed by analysis of 81 EV turns across 3 persona/scenario pairs and 17 combat-duration eval turns.

### Change A: Dice roll frequency reduction (ruling prompt)

**Problem:** Rolls occur on ~69% of turns (56/81). 55% of rolls are at `hard` difficulty (mod=-1), and 64% of roll reasons explicitly cite a negative condition. The combination of high roll frequency + condition-driven difficulty penalty creates a failure feedback loop: roll → fail → gain condition → harder next roll → fail again.

**Solution (ruling_system.j2):** Tighten the roll criteria from three permissive conditions to three restrictive conditions:

| Before | After |
|---|---|
| (a) Clear intent + meaningful action | (a) Occurs at a major narrative pivot — scene transition, decisive confrontation, gamble that alters the story. Actions in scenes with urgent threads are more likely to qualify. |
| (b) Meaningful failure consequence | (b) Failure has a real, irreversible consequence |
| (c) Genuine uncertainty | (c) Genuine uncertainty |

Plus an expanded no-roll list: idle observation, unimpeded movement, item inspection, casual conversation, passing time, routine commerce, information gathering, actions already attempted in this scene without new stakes, taking cover, reloading, healing, using a prepared item as intended.

**Thread context for ruling LLM (ruling_user.j2):** The ruling LLM needs to know whether the player's action relates to an active thread to apply criterion (a). Adding ~50-100 tokens:

```
## Urgent Threads
- {{ thread.id }} — {{ thread.summary }}
    T12: advancement — "Bald Tough confronts courier in the street"
    T13: setback — "negotiation fails, Bald Tough rejects bribe"
    T14: advancement — "Bald Tough incapacitated by knee strike"
```

Only urgent threads are shown (typically 1-2). Last 3 progress entries in chronological order with turn number. This gives enough signal for the LLM to assess thread relevance without adding full thread metadata.

**Expected impact:** ~69% → ~35-45% roll rate. Fewer rolls = fewer FAIL bands feeding the convergence score's dice weight component. Directly reduces spiral risk.

**Status:** Implemented in `plans/completed/12-convergence/01-roll-frequency.md`.

### Change B: Band rebalancing (rules.py)

**Problem:** Condition distribution across 81 turns shows 18:1 negative-to-positive ratio (19 distinct types: 18 negative, 1 positive). Average ~0.9 active conditions per turn. Net accumulation in every run (+4, +10, +6). Conditions bias difficulty upward (55% of rolls at hard), shifting the effective distribution left.

**Solution (`rules.py:111`):** One-line change:

```python
# Old
if final_total <= 8:    return "partial"
# New
if final_total <= 7:    return "partial"
```

**Canonical probability table:**

| Band | final_total | Neutral mod | -1 mod | +1 mod |
|---|---|---|---|---|
| crit_fail | ≤1 | 8.3% | 8.3% | 8.3% |
| fail | 2–5 | 33.3% | 41.7% | 25% |
| setback | 6 | 8.3% | 8.3% | 8.3% |
| partial | 7 | 8.3% | 8.3% | 8.3% |
| success | 8–11 | 33.3% | 25% | 41.7% |
| crit_success | ≥12 | 8.3% | 8.3% | 8.3% |
| **Bad total** | | **50%** | **58.3%** | **41.7%** |
| **Good total** | | **50%** | **41.7%** | **58.3%** |

**Symmetry invariant:** At all mod levels, crit_fail % = crit_success %, setback % = partial %. Only fail and success shift with mod.

**Criticals are modifier-sensitive:** `compute_band()` uses `final_total` for crit thresholds (≤1 and ≥12), not raw die. The `rules.py` module docstring incorrectly states "raw_die 1 → crit_fail (always, ignores modifiers)." The code is correct; the docstring is wrong and must be updated to: `final_total <= 1 → crit_fail`, `final_total >= 12 → crit_success`. Conditions and skills should affect crit probability — a player in a -2 condition stack can crit-fail on raw die 3; a player with +2 advantage can crit-succeed on raw die 10.

**Partial directive language strengthened:** The `build_directive()` output for `partial` band is updated to make the cost non-optional and concretely named. The existing text "you succeed but at a cost" is treated as optional flavor. New text: "The [verb] partially succeeds — but the cost is mandatory and must be named concretely: a wound taken, a resource spent, leverage given to an opponent, or a new complication now in play. Do not narrate a clean success. The cost is not optional flavor."

**Status:** Implemented in `plans/completed/12-convergence/02-band-rebalance.md`.

### Change C: Positive condition extraction guidance (extract_state_system.j2)

**Problem:** 18 of 19 condition types extracted across all runs are negative. The state extractor's heuristics only mention negative conditions:

```
## Stat-to-condition heuristics:
- Combat failure with strength/dexterity → consider wounded, bleeding, pinned
- Failed charisma under social pressure → consider shaken
- Clean success or crit_success → no negative conditions
```

The last line actively discourages positive conditions — it only says "no negative" without suggesting positives for success.

**Solution (`extract_state_system.j2`):** Add success-guarded positive condition heuristics:

```
## Stat-to-condition heuristics:
- Combat failure with strength/dexterity → consider wounded, bleeding, pinned
- Failed charisma under social pressure → consider shaken
- After a decisive success or critical success → consider a short-lived positive condition (focused, determined, elated, second_wind, protected). Max 1 per turn.
- When an ally or circumstance actively aids the player → consider a brief positive condition (guided, fortified, inspired). Max 1 per turn.
- Total active conditions must not exceed 5 — remove the least relevant before adding if at cap.
```

Expected impact: ~5% positive ratio → ~25% (1:3 neg:pos). The 5-cap limits negative stacking while creating space for positives. Fewer active negatives means fewer hard-difficulty calls, breaking the fail→condition→harder→fail spiral.

**Status:** Implemented in `plans/completed/12-convergence/03-conditions-extraction.md`.

### Synergy with convergence design

All three changes reduce the inputs to the convergence score's components:

- **Fewer rolls** → dice weight component fires less often
- **Balanced bands** → fail/crit_fail less frequent at typical condition load
- **More positive conditions** → fewer hard-difficulty calls → fewer fail bands

The convergence score still enters CLIMAX when appropriate (3 of 5 components agree), but the baseline rate of bad dice outcomes is lower, so the score triggers on genuine narrative pressure rather than accumulated condition debt.

## Failure Modes and Risks

### Pipeline risks
1. **LLM ignores Curtain Call guidance.** Mitigation: the hard cutoff at `climax_turn_limit` still fires. The worst case is 2-3 extra CLIMAX turns, which is the same as today.
2. **Convergence threshold too high or low.** Threshold 3 means 3 of 5 components must agree. In practice, an active urgent thread (+1) with scene age (+1) and a bad beat streak (+1) reaches threshold without dice input. If CLIMAX fires too early, lower the threshold. If too late, raise it. Config-driven.
3. **Scene age component is redundant with Scene Imperative.** The score includes scene age as a signal, but Scene Imperative also fires at the same threshold. They're both present but the phase machine and directives are separate concerns — score drives transitions, directives guide LLM behavior. Slight overlap is acceptable.
4. **BREATHER exit condition (urgency > 0) is unchanged.** If an urgent thread persists but the player genuinely needs rest, BREATHER still exits early. This is by design — BREATHER without safety is false calm. The real fix is urgency decay (`thread_urgency_max_age`), unchanged.

### Post-implementation watch items
5. **Roll rate may overcorrect downward.** The ruling criteria tightening targets 35–50% roll rate. If the LLM interprets the new criteria too strictly and drops to 15–20%, turns become pure narration with no mechanical stakes. Post-implementation EV check required. If roll rate drops below 25%, criteria are too restrictive.
6. **Single-urgent-thread scenarios escalate slower.** By design: without urgency depth (+1 for 2+ threads), single-threat scenarios max at thread weight +1, requiring scene age and beat streak to carry the remaining 2 points to threshold. This means CLIMAX fires no earlier than turn 3 in single-threat scenarios — intentional, prevents premature CLIMAX on scene entry.
7. **Beat streak quorum may underfire in short scenes.** A 5-entry window requires 5 beats to have occurred. In a scene reaching CLIMAX on turn 3–4, the buffer may only have 2–3 entries. **Resolved:** proportional threshold `ceil(n × 0.6)` when buffer < 5 (see Decision Table). At n=3 → 2, n=4 → 3, n=5 → 3. Post-eval verify that short-scene CLIMAX timing is consistent with longer scenes.
8. **Positive condition ratio may not reach 25% target.** The extraction prompt change targets ~25% positive conditions. LLMs have strong priors toward negative extraction. Post-eval check needed. If positive ratio stays below 10%, prompt guidance may need to be more directive — possibly adding "You MUST extract at least one positive condition per scene if a crit_success or decisive success occurred."
9. **Partial directive enforcement may be insufficient.** Strengthening the `build_directive()` text may not be enough — the narrator has significant context from prior turns that may override the directive. If EV shows partial still being narrated as success after this change, the fix is to add partial to the `outcome_hint` system so the narrator receives an explicit signal.
10. **EV checker debt.** Multiple EV checkers reference removed fields (`consecutive_pressure_beats`, `crisis_urgency_threshold`, `enforce_relief`, `tension_delta`). These will not break at runtime but will produce incorrect or vacuous results. EV tool update is out of scope for this plan but must be tracked as immediate follow-up work. **[OPEN: EV checker debt — needs a tracking stub (e.g. `plans/ev-checker-update.md`) before this plan closes.]**

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `derive_enforce_relief()` | `_pacing.py:92-94` | Deleted with no replacement |
| `enforce_relief` parameter on `derive_allowed_beat_types()` | `_pacing.py:63` | Deleted |
| `consecutive_pressure_threshold` | `config.py:144` | Deleted with no replacement |
| `consecutive_pressure_beats` state counter | `turn.py:1042-1050` | Replaced by recent_beats streak |
| `crisis_urgency_threshold` | `config.py:157` | Deleted with no replacement |
| `spiral_decay_turns` | `config.py` | Deleted with no replacement. `recent_beats_max` is the correct decay tuning knob. |
| `tension_delta` field on `IntentEnvelope` | `models.py` | Deleted from model entirely, not merely unused. 0 de-escalates across 80 turns. |
| `tension_delta` parameter on `_compute_scene_phase` | `turn.py:505` | Removed from signature |
| `tension_delta` parameter on `_compute_narration_directive` | `turn.py:407` | Removed from signature |
| `crisis_turn_limit` | `config.py:158` | Renamed to `climax_turn_limit` |
| `tension_delta` check in RISING→CLIMAX entry | `turn.py:557-558` | Replaced by convergence score |
| `tension_delta` check in SETUP→RISING | `turn.py:550-551` | Removed (urgency + threshold handles it) |
| `twist` from Scene Imperative beat list | `_pacing.py:75`, storytell_system.j2:71 | Replaced by `setback` + `breathing_room` |

## What Is Unchanged

- `EngineConfig.scene_pressure_threshold` (default 3)
- `EngineConfig.scene_imperative_threshold` (default 4)
- `EngineConfig.breather_max_turns` (default 3)
- `EngineConfig.thread_urgency_max_age` (default 8, auto-demotion)
- `EngineConfig.thread_stale_threshold` (default 3, auto-latent)
- `EngineConfig.recent_beats_max` (default 5)
- `PacingContext` struct (directive, outcome_hint, summary, spiral_detected fields)
- `Breathe` directive logic (unchanged: de-escalation + 0 urgent threads)
- `Scene Pressure` directive (unchanged: age-based)
- `Scene Imperative` directive (unchanged except allowed beat list)
- `outcome_hint = "transition"` override (unchanged: fires when effective_scene_age >= scene_imperative_threshold)
- `pending_gm_beat` lifecycle (unchanged: storytell → meta, expires at turn+2)
- `_apply_thread_resolutions()`, `_apply_thread_updates()`, `_apply_arc_resolve()` (unchanged)
- `sanitize_threads()` (unchanged)
- Ruling engine (`resolve_check`, `build_directive`) — band threshold rebalanced (partial ≤8 → ≤7), see Supporting Changes
- Ruling system prompt — roll criteria tightened, thread context added to user prompt (see Supporting Changes)
- Extraction pipeline — state extractor prompt updated with positive condition heuristics (see Supporting Changes)
- `IntentEnvelope` — `tension_delta` field removed from model (see What Is Removed). All other fields unchanged.
- `compute_convergence_score` is NEW, not a replacement of an existing function

## New Model Shapes

```python
# engine/config.py — EngineConfig changes
convergence_threshold: int = 3
climax_turn_limit: int = 4  # renamed from crisis_turn_limit

# Removed:
# crisis_urgency_threshold: int = 2
# consecutive_pressure_threshold: int = 3
```

```python
# engine/_pacing.py — new function
def compute_convergence_score(
    scene_phase: str,
    thread_urgency_count: int,
    scene_age: int,
    recent_beats: list[dict],          # full buffer (max 5), history only; pending beat not included
    current_outcome: RulesOutcome | None,  # current turn's roll; None or rolled=False = no roll
    config: EngineConfig,
) -> int:
    ...
```

```python
# models.py — BEAT_BUCKETS update
BEAT_BUCKETS["pressure"] = ["pressure", "complication", "escalation", "setback"]
```

## Context for Implementing LLMs

- **`ccya/engine/turn.py`** — `_compute_scene_phase()` (line 503-582): the phase machine. RISING→CLIMAX transition replaced with convergence score. `_compute_narration_directive()` (line 405-441): remove tension_delta parameter. Post-extraction block (line 1030-1067): remove `consecutive_pressure_beats` tracking, remove `derive_enforce_relief` call.
- **`ccya/engine/_pacing.py`** — `BEAT_BUCKETS` (line 15-19): add `setback` to pressure bucket. `derive_allowed_beat_types()` (line 58-89): remove `enforce_relief` parameter, update Scene Imperative allowed list. New function: `compute_convergence_score()`. Delete `derive_enforce_relief()`.
- **`ccya/engine/config.py`** — `EngineConfig` (line 97-184): add `convergence_threshold`, rename `crisis_turn_limit` to `climax_turn_limit`, remove `crisis_urgency_threshold`, remove `consecutive_pressure_threshold`.
- **`ccya/engine/extraction.py`** — imports (line 19): remove `derive_enforce_relief`. Storytell message builder (line 319-327): remove `enforce_relief` parameter from `derive_allowed_beat_types()` call.
- **`ccya/prompts/storytell_system.j2`** — Scene Imperative beat list (line 71): replace `twist` with `setback`. Add `breathing_room` to Scene Imperative override list only (NOT to `BEAT_PHASE_MAP["CLIMAX"]` base list). Add Curtain Call guidance for CLIMAX phase. Distinction between base CLIMAX list and override list must be explicit in prompt text.
- **`ccya/rules.py`** — `compute_band()` (line 102-113): partial threshold ≤8 → ≤7. Module docstring corrected to `final_total <= 1 → crit_fail`, `final_total >= 12 → crit_success`. `build_directive()` partial band text updated to make cost mandatory and concretely named. **Status: Implemented.**
- **`ccya/models.py`** — `IntentEnvelope` (line 168-177): remove `tension_delta` field.
- **Checkers** — `ccya/ev/checkers/gm_beat.py` (enforce_relief check), `ccya/ev/checkers/pacing.py` (consecutive_pressure_beats tracking), `ccya/ev/checkers/crisis_turn_counting.py` (rename to climax_turn_counting), `ccya/ev/checkers/beat_phase_validity.py` (enforce_relief reference on line 30).
- **`ccya/ev/deltas.py`** — `_cmd_deltas_compact()` (line 132-191): references to CRISIS/climax naming, pressure beat tracking.
- **`ccya/server/tv.py`** — `gm_beat_enforce_relief` field (line 619): remove.
- **`ccya/ev/checkers/pacing.py`** — confirmed: no `spiral_decay_turns` reference exists. No change needed.
- **`docs/design/review-pacing-plan.md`** — `spiral_decay_turns` flagged as open question. Mark resolved: "Remove it."
