# Post-Convergence Mechanics Report

## New Mechanics

### 1. Convergence Score

Replaces `crisis_urgency_threshold` (binary: ≥2 urgent threads → CRISIS) with a composite score built from 5 independent signals. Each component contributes +1; threshold 3 triggers CLIMAX entry.

| Component | Signal | Condition |
|---|---|---|
| Thread weight | Any urgent thread active | `thread_urgency_count >= 1` |
| Urgency depth | Multiple concurrent urgent threads | `thread_urgency_count >= 2` |
| Scene age | Scene has been running long enough | `scene_age >= scene_pressure_threshold` (default 3) |
| Beat streak | Recent beats lean pressure | 3+ pressure-bucket beats in last 5 (proportional quorum for <5) |
| Dice weight | Bad roll + urgent thread | `band in (crit_fail, fail)` AND `thread_urgency_count >= 1` |

Key invariant: score cannot reach threshold 3 without at least one urgent thread (thread weight + anything else = +1, max without urgent threads is 2 from scene age + beat streak). CLIMAX always implies an active urgent thread.

Score is computed fresh each turn, never persisted. Persisted only in the event log (`pacing_context.convergence_score`, `pacing_context.convergence_components`).

Five components at +1 each, no weighting in v1. All 5 must be individually useful signals without amplifying noise.

### 2. Curtain Call — Two-Tier Soft Close

Prompt-based mechanism (no mechanical force) that guides the LLM toward thread resolution during CLIMAX:

- **Turn 1** (`climax_turn_count == 1`): Storytell user prompt includes `curtain_call: "active"`. System prompt adds: "CLIMAX phase — you MUST resolve the active thread this scene. Include at least one `thread_resolve` entry in your output."
- **Second-to-last turn** (`climax_turn_count >= climax_turn_limit - 1`): Both narrate and storytell user prompts include `curtain_call: "forced"`. Storytell system prompt escalates to: "This is the final climactic turn. This thread MUST resolve now, for better or worse."
- **Hard cutoff**: Engine transitions to RESOLUTION at `climax_turn_count >= climax_turn_limit` regardless of resolution state. No force-close, no retry loop.

Fallback path for "CLIMAX with no urgent thread" removed as unreachable (score invariant guarantees at least one).

### 3. Beat Classification Changes

| Change | Detail |
|---|---|
| `setback` added to pressure bucket | `BEAT_BUCKETS["pressure"]` = `[pressure, complication, escalation, setback]`. Also added to `PRESSURE_BEAT_TYPES`. Setback now counts toward beat streak component. |
| `twist` removed from Scene Imperative | Replaced by `setback`. `twist` was the primary source of infinite escalation. |
| `breathing_room` in Scene Imperative only | NOT added to `BEAT_PHASE_MAP["CLIMAX"]` base list. Only available as a resolution-adjacent beat when Scene Imperative is already active. |
| Short-scene proportional quorum | When buffer < 5 entries, uses `ceil(n × 0.6)` threshold instead of flat quorum 3. At n=3 → 2, n=4 → 3, n=5 → 3. Prevents 100% pressure requirement at n=3. |

### 4. EV Commands for Convergence

New CLI commands added to `ev.py`:

| Command | Purpose |
|---|---|
| `convergence` | Table of score + 5 components per turn with CLIMAX entry markers |
| `phase-transitions` | Phase change log with trigger signals (convergence_score, climax_turn_count, outcome_hint) |
| `curtain-call` | Per-CLIMAX-turn PASS/FAIL on thread_resolve compliance |
| `warnings` | Warning signal scan (extract retries, retry_errors, rejected items, reconcile_warnings) + gap documentation |
| `prompt-sizes` | Token counts per pipeline stage per turn with linear regression growth trend |
| `rolls` | Renamed from `momentum-check`. Raw/final totals per roll turn with band and momentum display. |

### 5. Narrate Output in Event Schema

`event.narrate` now includes `"output": narrative` (full prose) alongside `first_token_ms`, `total_ms`, `tokens_in`, `tokens_out`. All existing consumers unchanged.

### 6. Convergence Components in Event Schema

`event.pacing_context.convergence_components` is a `dict[str, int]` with 5 keys: `thread_weight`, `urgency_depth`, `scene_age`, `beat_streak`, `dice_weight`. Written at turn serialization time, never re-computed.

### 7. Warning Signals in Event Schema

- `event.extract.retries` — now records actual retry count (was hardcoded 0). Source: `extraction_event[stream]["retry_errors"]` len.
- `event.reconcile_warnings` — list of warning strings from reconciliation phase.

### 8. Nested Field Support (EV search)

- `extract_field_from_event()` in `events.py` — generic dot-notation traversal of event dict for any dotted path.
- `_match_single_query()` in `state_tools.py` — dotted-field fallback search in any nested event field.

---

## Removed Machinery

| Removed | Reason |
|---|---|
| `derive_enforce_relief()` | Never fired in 49 evaluated turns. Beat diversification naturally prevents pressure-lock. |
| `consecutive_pressure_beats` counter | Replaced by `recent_beats` streak analysis. |
| `consecutive_pressure_threshold` config | Dead config — no consumer after enforce_relief removal. |
| `consecutive_pressure_beats` state counter | Dead state — tracked nothing after removal. |
| `crisis_urgency_threshold` config | Replaced by convergence score + threshold 3. |
| `spiral_decay_turns` config | No consumer — `detect_spiral()` does not reference it. |
| `tension_delta` field | 0 de-escalates across 80 turns. Architectural mismatch — ruling engine lacks scene-level context. |
| `tension_delta` parameters on `_compute_scene_phase` and `_compute_narration_directive` | Dead signal removed from signatures. |
| `tension_delta` checks in RISING→CLIMAX and SETUP→RISING | Replaced by convergence score checks. |
| `crisis_turn_limit` → `climax_turn_limit` | Renamed for semantic clarity. Same default (4). |
| `twist` from Scene Imperative beat list | Primary source of infinite escalation. Replaced by `setback`. |

---

## Renamed

| Old | New | Scope |
|---|---|---|
| `crisis_turn_limit` | `climax_turn_limit` | EngineConfig + state key |
| `crisis_turn_count` | `climax_turn_count` | State key |
| `momentum-check` | `rolls` | EV CLI command |
| `cmd_momentum_check` | `cmd_rolls` | Python function |

---

## Supporting Changes (Synergistic)

Three changes reduce convergence score component firing rates so CLIMAX triggers on genuine narrative pressure, not accumulated condition debt:

| Change | Mechanism | Expected Impact |
|---|---|---|
| Roll frequency reduction | Ruling prompt tightened from 3 permissive criteria to 3 restrictive criteria. Expanded no-roll list. Thread context added to ruling user prompt. | ~69% → 35–45% roll rate. Fewer rolls = fewer fail bands. |
| Band rebalancing | `partial` threshold ≤8 → ≤7 in `rules.py:111`. | Bad total shifts from 50% → 58.3% at -1 mod. Invariant: crit_fail % = crit_success % at all mod levels. |
| Positive condition extraction | State extractor prompt updated with success-guarded positive heuristics. 5-cap per player. Positive ratio target: ~25% (up from ~5%). | Fewer active negatives → fewer hard-difficulty calls → fewer fail bands. |

---

## Invariants

1. CLIMAX always has at least one urgent thread (score invariant: threshold 3 unreachable without thread weight +1).
2. Score computed before storytell runs each turn. Pending beat never included in streak calculation.
3. Phase machine is read-only with respect to threads — never writes thread state.
4. Convergence score never persisted between turns — computed fresh each turn from current state.
5. BREATHER exit unchanged: exits when `thread_urgency_count > 0` OR `breather_turn_count >= breather_max_turns`. Does NOT use convergence score.
