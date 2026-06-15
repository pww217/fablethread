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
- `tension_delta` field removal from `IntentEnvelope` (field kept, just not consumed by phase engine)
- `action_stake` field on `IntentEnvelope` (see Open Questions)

## Decision Table

| Decision | What | Why |
|---|---|---|
| CRISIS → CLIMAX rename | All phase names, config field names, log keys, prompt text referencing "CRISIS" renamed to "CLIMAX" | CLIMAX is semantically clearer — this is the narrative turning point, not a death spiral. |
| `crisis_urgency_threshold` deleted | Removed from EngineConfig. No replacement. | Replaced by composite convergence score. No need for both. |
| `crisis_turn_limit` → `climax_turn_limit` | Renamed in EngineConfig. Same default (4). | Scope change only. |
| Convergence score replaces urgency check | Score computed fresh each turn from 5 components, each worth +1, threshold 3. Never persisted. | Composite signal is more robust than any single proxy. Threshold 3 requires multiple independent systems to agree before CLIMAX fires. |
| `tension_delta` removed from phase logic | `_compute_scene_phase` and `_compute_narration_directive` no longer read tension_delta. | tension_delta was a noisy proxy. The convergence score subsumes it without needing the ruling LLM to classify intensity. |
| `setback` classified as pressure-bucket beat | Added to `BEAT_BUCKETS["pressure"]` and `PRESSURE_BEAT_TYPES` | Setback applies negative pressure to the player — it belongs with escalation, complication, and pressure. Streak counting now includes it. |
| Curtain Call added to storytell prompt | Turn 1 of CLIMAX: thread_resolve added to required outputs. Second-to-last turn: narrate + storytell prompts escalate language. | Two-tier soft close gives the LLM guidance without mechanical force. The hard cutoff at climax_turn_limit is unchanged. |
| `derive_enforce_relief()` deleted | Removed from `_pacing.py`. `consecutive_pressure_threshold` config field removed. `consecutive_pressure_beats` state counter removed. | Fired zero times across two evals (28+21 turns). Dead code. The convergence score + phase map naturally allow relief beats when the phase transitions. |
| `PRESSURE_BEAT_TYPES` tuple in turn.py | Updated to include `setback`. | Consistency with BEAT_BUCKETS. |
| BREATHER exit condition | Exits when `thread_urgency_count > 0` OR `breather_turn_count >= breather_max_turns`. Same old rule, explicit. | BREATHER should not use convergence score — a single urgent thread means the character can't rest. |

## Open Questions

- **Band threshold rebalancing (DECIDED).** See Supporting Changes below. Partial threshold shifted from ≤8 to ≤7, making success ≥8 instead of ≥9. Success goes from 25% → 33.3% at neutral mod. Partial drops from 16.7% → 8.3%. Bad/good split stays 50/50 at neutral. This compensates for conditions bias (see condition analysis in Supporting Changes).
- **Convergence score weighting.** All five components are +1 for v1. Post-eval analysis may justify weighting some higher (e.g., dice weight at +2, or scene age at +1.5). Deferred.
- **`action_stake` field on IntentEnvelope.** A ruling-engine signal classifying whether the player's action directly threatens/defends an active thread. Would improve convergence signal quality. Requires ruling prompt change + new field. Not committed — flagged OPEN.
- **Curtain Call beat list.** The Scene Imperative allowed list during Curtain Call needs to exclude `twist` and include resolution-compatible types (`setback`, `breathing_room`). Exact list to be defined when the Curtain Call prompt section is written.

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
2. **`tension_delta` is consumed by the phase machine but is a weak signal.** The ruling LLM emits "escalates" for any high-stakes action, which overrides the urgency check and forces CRISIS even from a single urgent thread.
3. **Scene Imperative lacks resolution-compatible beats.** The allowed list `[revelation, twist, hazard, callback, opportunity]` contains zero beats that end a scene. The LLM has a "wrap it up" directive but no tool to execute it.
4. **`derive_enforce_relief` never fires.** Dead code across two evals (0/49 turns). The logic is correct but the pressure threshold never triggers because storytell avoids consecutive pressure beats, or the pressure beats aren't clustered densely enough.
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
    recent_rolls: list[dict],
    config: EngineConfig,
) -> int:
    """Compute a composite convergence score (0-5) for CLIMAX entry decisions.
    
    Score components (each worth +1):
    1. Thread weight: any urgent thread active (capped at +1)
    2. Urgency depth: 2+ urgent threads simultaneously (additive)
    3. Scene age: scene_age >= scene_pressure_threshold
    4. Beat streak: 2+ pressure-bucket beats in last 3 recent_beats
    5. Dice weight: band in {crit_fail, fail} AND urgent thread exists
    
    Returns 0-5. Threshold 3 = enter CLIMAX.
    """
```

Components in detail:
- **Thread weight (+1):** `thread_urgency_count >= 1`. Capped at 1 regardless of count.
- **Urgency depth (+1):** `thread_urgency_count >= 2`. Additive with thread weight, so 2+ urgent threads = +2 total from thread signals.
- **Scene age (+1):** `scene_age >= config.scene_pressure_threshold` (default 3).
- **Beat streak (+1):** Of the last 3 entries in `state["meta"]["recent_beats"]`, 2+ have type in the pressure bucket (including `setback`). The pending beat for the current turn is also included in the check window.
- **Dice weight (+1):** Most recent roll's band is `crit_fail` or `fail` AND `thread_urgency_count >= 1`. This is an amplifier — dice weight alone can't reach threshold without an urgent thread.

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

**Curtain Call beat list (for Scene Imperative during Curtain Call):** The Scene Imperative allowed list during CLIMAX phase replaces `twist` with `setback`. The final list: `[revelation, hazard, callback, opportunity, setback, breathing_room]`. `twist` is excluded because it was the primary source of infinite escalation.

#### 6. Removed machinery

| Component | File | Replacement |
|---|---|---|
| `derive_enforce_relief()` | `_pacing.py:92-94` | Deleted with no replacement |
| `consecutive_pressure_threshold` config field | `config.py:144` | Deleted with no replacement |
| `consecutive_pressure_beats` counter on `state["meta"]` | `turn.py:1042-1050` | Deleted; recent_beats streak replaces |
| `crisis_urgency_threshold` config field | `config.py:157` | Deleted with no replacement |
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
```

Renamed fields:
```python
# crisis_turn_limit: int = 4  →  climax_turn_limit: int = 4
```

### Alternatives Considered and Rejected

- **Hard force-close of threads (deferred).** The engine could inject a synthetic `thread_resolve` when the LLM fails to resolve. Rejected for v1 because the LLM has been compliant in both evals — it follows the allowed list and required outputs. If Curtain Call guidance is insufficient, add hard close in a follow-up.
- **New beat type (e.g., `scene_resolution`).** A dedicated beat type would require a `GMBeat.type` schema change and extraction wiring. The simpler approach is to use the existing `thread_resolve` structured output field. The LLM already knows how to emit it; it just doesn't because no prompt guidance tells it to.
- **`turn_entered` stamping as scene exit.** The old approach (synthetic location change) bypassed the phase machine entirely and didn't fix the urgency re-entry problem. Abandoned.

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

### Change B: Band rebalancing (rules.py)

**Problem:** Condition distribution across 81 turns shows 18:1 negative-to-positive ratio (19 distinct types: 18 negative, 1 positive). Average ~0.9 active conditions per turn. Net accumulation in every run (+4, +10, +6). Conditions bias difficulty upward (55% of rolls at hard), shifting the effective distribution left:

| Mod | Bad (crit+fail+setback) | Middle (partial) | Good (success+crit) |
|---|---|---|---|
| 0 (neutral) | 50% | 16.7% | 33.3% |
| -1 (typical) | 58.3% | 8.3% | 33.3% |

**Solution (`rules.py:111`):** One-line change:

```python
# Old
if final_total <= 8:    return "partial"
# New
if final_total <= 7:    return "partial"
```

Partial goes from 16.7% → 8.3% (only die=7 with neutral mod). Success goes from 25% → 33.3% (die 8-11). All other bands unchanged:

| Band | Old (0 mod) | New (0 mod) | New (-1 mod) |
|---|---|---|---|
| crit_fail | 8.3% | 8.3% | 16.7% |
| fail | 33.3% | 33.3% | 33.3% |
| setback | 8.3% | 8.3% | 8.3% |
| partial | 16.7% | 8.3% | 0% |
| success | 25% | 33.3% | 25% |
| crit_success | 8.3% | 8.3% | 16.7% |
| **Bad** | **50%** | **50%** | **58.3%** |
| **Good** | **50%** | **50%** | **41.7%** |

At neutral mod, bad/good stays 50/50. At typical condition load (-1), success drops to 25% but the overall good rate stays at 41.7% — much closer to 50/50 than before. Partial outcomes halve in frequency, making outcomes more decisive.

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

### Synergy with convergence design

All three changes reduce the inputs to the convergence score's components:

- **Fewer rolls** → dice weight component fires less often
- **Balanced bands** → fail/crit_fail less frequent at typical condition load
- **More positive conditions** → fewer hard-difficulty calls → fewer fail bands

The convergence score still enters CLIMAX when appropriate (3 of 5 components agree), but the baseline rate of bad dice outcomes is lower, so the score triggers on genuine narrative pressure rather than accumulated condition debt.

1. **LLM ignores Curtain Call guidance.** Mitigation: the hard cutoff at `climax_turn_limit` still fires. The worst case is 2-3 extra CLIMAX turns, which is the same as today.
2. **Convergence threshold too high or low.** Threshold 3 means 3 of 5 components must agree. In practice, an active urgent thread (+1) with scene age (+1) and a bad beat streak (+1) reaches threshold without dice input. If CLIMAX fires too early, lower the threshold. If too late, raise it. Config-driven.
3. **Scene age component is redundant with Scene Imperative.** The score includes scene age as a signal, but Scene Imperative also fires at the same threshold. They're both present but the phase machine and directives are separate concerns — score drives transitions, directives guide LLM behavior. Slight overlap is acceptable.
4. **BREATHER exit condition (urgency > 0) is unchanged.** If an urgent thread persists but the player genuinely needs rest, BREATHER still exits early. This is by design — BREATHER without safety is false calm. The real fix is urgency decay (`thread_urgency_max_age`), unchanged.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `derive_enforce_relief()` | `_pacing.py:92-94` | Deleted with no replacement |
| `enforce_relief` parameter on `derive_allowed_beat_types()` | `_pacing.py:63` | Deleted |
| `consecutive_pressure_threshold` | `config.py:144` | Deleted with no replacement |
| `consecutive_pressure_beats` state counter | `turn.py:1042-1050` | Replaced by recent_beats streak |
| `crisis_urgency_threshold` | `config.py:157` | Deleted with no replacement |
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
- All model shapes (unchanged)
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
    recent_beats: list[dict],
    recent_rolls: list[dict],
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
- **`ccya/prompts/storytell_system.j2`** — Scene Imperative beat list (line 71): replace `twist` with `setback` and `breathing_room`. Add Curtain Call guidance for CLIMAX phase.
- **`ccya/rules.py`** — `compute_band()` (line 102-113): threshold rebalancing is OPEN, not committing in this plan.
- **Checkers** — `ccya/ev/checkers/gm_beat.py` (enforce_relief check), `ccya/ev/checkers/pacing.py` (consecutive_pressure_beats tracking), `ccya/ev/checkers/crisis_turn_counting.py` (rename to climax_turn_counting), `ccya/ev/checkers/beat_phase_validity.py` (enforce_relief reference on line 30).
- **`ccya/ev/deltas.py`** — `_cmd_deltas_compact()` (line 132-191): references to CRISIS/climax naming, pressure beat tracking.
- **`ccya/server/tv.py`** — `gm_beat_enforce_relief` field (line 619): remove.
