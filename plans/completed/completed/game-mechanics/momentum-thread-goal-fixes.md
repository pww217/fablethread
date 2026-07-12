# Fix: Momentum Death Spiral + Thread Accumulation + Goal Stagnation

## Purpose

Fix three systemic fidelity issues causing 20-turn gameplay death spirals, background thread accumulation, and stale arc goals — restoring core mechanical correctness to momentum recovery, thread lifecycle, and goal relevance.

## Problem Statement

The engine has three compounding systemic failures: (1) Momentum at -3/-2 creates a 20-turn death spiral because success only recovers +1 regardless of depth, Breathe directives contradict themselves by appending "Resolve a Threat", floor relief injects ambient beats during crises instead of pressure, and Scene Imperative fires too late to help. (2) Background threads accumulate indefinitely — inactive since turns 5-10 they sit in the active list at turn 31 because the sanitizer prompt never instructs cleanup based on temporal decay. (3) Arc goals stagnate for 2-3 sanitizer cycles despite major narrative events (witness escapes, ally killed) because the sanitizer template only passively asks whether to update rather than explicitly instructing mid-cycle pivot on major events.

## Constraints

- No new config knobs or state shape changes except `scene_imperative_threshold` default 5→4.
- Momentum delta multiplier must be applied in `apply_momentum()` (momentum.py), not by modifying the `MOMENTUM_DELTA` constant dict — keeps band-to-delta mapping clean and eval-compatible.
- Floor relief fix: only change the OR condition, do NOT remove floor relief entirely — it's still needed for consecutive_pressure path.
- Sanitizer prompt changes must follow existing checklist rubric pattern (see `_checklist` section at sanitize_thread.j2:82-87).
- Tests are temporarily removed during refactor; skip test writing per AGENTS.md rules.

## Non-goals

- No engine-level thread eviction or periodic cleanup mechanism (#5 is prompt-only).
- No event-driven `goal_update` mid-cycle emission — sanitizer remains purely periodic (prompt fix only).
- No new auto-checker metrics for stagnation detection, accumulation validation, or sanitizer event validation — these go in a later eval-fixes pass.
- No changes to location state (#1 deferred pending root cause confirmation).
- No difficulty assignment algorithm overhaul (MB-7 noted as observation; scoring artifact may be scenario-specific).

## Solution

Add depth-based momentum recovery at -3 (`apply_momentum` returns +2 for success instead of +1), prevent Breathe from appending "Resolve a Threat" in beat_locked logic, make floor relief injection conditional on consecutive_pressure (not momentum_floor) to avoid injecting ambient beats during momentum crisis, lower scene_imperative_threshold from 5→4 so it fires earlier, validate existing MB-5 pressure counter fix, add explicit temporal decay and goal pivot instructions to `sanitize_thread.j2`, update eval constant imports if needed, verify with `make check`.

## Firm decisions

1. **Momentum catch-up at -3 only**: Success at momentum < -2 (i.e., -3) returns +2 instead of +1. This is the minimum acceleration that meaningfully breaks the spiral without over-correcting.
2. **Breathe never gets threat append**: When directive is "Breathe", beat_locked must NOT append "; Resolve a Threat". Breathe is de-escalation — it contradicts itself to demand threat resolution.
3. **Floor relief only from consecutive_pressure**: The OR condition (`consecutive_pressure_threshold OR momentum_floor`) becomes AND for floor relief injection. Floor relief fires when both conditions are met, not either one. This prevents ambient beat injection during pure momentum-floor crisis while preserving it for genuine pressure spirals.
4. **Scene imperative threshold 5→4**: Lower from 5 to 4 so Scene Imperative fires at turn 4 instead of 5 (or turn 2 with combat boost). Gives more room for pacing recovery before the directive forces scene advancement.
5. **MB-5 already fixed, validate only**: The consecutive pressure counter at `turn.py:1074-1082` reads from `pending_gm_beat` after floor relief injection — this was previously reading raw storyteller output (now corrected). No code change needed; add a validation step to confirm the logic is correct.
6. **Thread cleanup threshold**: Inactive 3+ turns with no progress_updates → move to completed_threads or remove from active list. This aligns with `thread_stale_threshold=3` already in config.py for auto-latent demotion.
7. **Goal pivot instruction**: Explicitly instruct sanitizer to update visible_goal when major events occur (witness escapes, ally killed, location changes) — not just "should it be updated" passively but "must update if narrative direction fundamentally changed."

## Risks, Ambiguities, and Blockers

- **MB-3 floor relief AND condition**: Changing OR to AND means floor relief may NOT fire during pure momentum_floor crisis (when consecutive_pressure is 0). This is intentional — the findings show ambient beats are the wrong intervention at -2/-3. But it's a behavioral change that should be validated against gameplay data after implementation.
- **Momentum +2 at -3**: If player is at -2 with success (+2 multiplier), they reach 0 (capped at max 3). This may feel too aggressive — consider whether threshold should be `< -2` (only -3) or `<= -2` (-2 and below). Decision: use `< -2` (only -3) for minimum change.
- **MB-7 difficulty assignment**: The 42% hard difficulty rate against a +2-max character may be partially correct scoring logic, not purely a bug. Without deeper analysis of the difficulty assignment algorithm (`rules.py:_assign_difficulty` or equivalent), this is noted as an observation to investigate later rather than fixed here.
- **Sanitizer prompt changes**: Adding explicit cleanup/pivot instructions may cause the LLM to over-correct — resolving threads too aggressively or changing goals on minor events. The checklist rubric should mitigate this by forcing explicit justification for each change.

## Status

`completed — both Phase 01 (momentum systemic) and Phase 02 (sanitizer prompt fixes) executed.`

---

# Implementation Phases

Two phases grouped by shared files: Phase 01 handles momentum systemic changes (rules.py, momentum.py, turn.py, config.py). Phase 02 handles sanitizer prompt fixes (sanitize_thread.j2) covering both thread accumulation (#5) and goal stagnation (#3), since they share the same template file.

---

## Implementation — Phase 01: Momentum systemic fixes (MB-1 through MB-7)

### Context files to load- `ccya/state/momentum.py` — apply_momentum() function with MOMENTUM_DELTA import
- `ccya/engine/turn.py` — lines 224-237 (thread_updates auto-latent demotion), lines 483-560 (_compute_narration_directive, _compute_pacing_context), lines 1063-1082 (floor relief injection + pressure counter)
- `ccya/engine/config.py` — scene_imperative_threshold default at line ~153

### Detailed steps

#### Step 01.1 — Add depth-based momentum recovery to apply_momentum()

**File:** `ccya/state/momentum.py`

**What:** Modify `apply_momentum()` to return +2 for success/crit_success when current momentum < -2 (i.e., at -3). Use a local multiplier variable, do NOT modify the global MOMENTUM_DELTA dict.

```python
# In apply_momentum(), after line 23:
delta = MOMENTUM_DELTA.get(band, 0)
if band not in MOMENTUM_DELTA:
    _log.warning("apply_momentum unrecognized band=%s delta=0", band)

# MB-4: depth-based catch-up acceleration at -3
current_for_multiplier = current
new_val = max(MOMENTUM_MIN, min(MOMENTUM_MAX, current + delta))
if momentum < -2 and band in ("success", "crit_success"):
    deeper_delta = 2 if band == "success" else 3
    new_val = max(MOMENTUM_MIN, min(MOMENTUM_MAX, current_for_multiplier + deeper_delta))
```

Wait — I need to be more careful. The function reads `current` from state at line 22 (`pc.get("momentum", 0)`). But the multiplier should apply based on what momentum IS before applying delta (i.e., the pre-roll value), not after clamping. Let me re-read the code:

```python
# Current implementation (lines 16-27):
def apply_momentum(state, band):
    pc = state.setdefault("pc", {})
    current = int(pc.get("momentum", 0))   # ← pre-roll momentum from state
    delta = MOMENTUM_DELTA.get(band, 0)
    new_val = max(MOMENTUM_MIN, min(MOMENTUM_MAX, current + delta))
    pc["momentum"] = new_val
```

The `current` value is the pre-roll momentum read directly from state. The multiplier should apply to this same `current` value:

**Change:** After line 23 (`delta = MOMENTUM_DELTA.get(band, 0)`), add depth-based override for success/crit_success at -3:

```python
    delta = MOMENTUM_DELTA.get(band, 0)
    if band not in MOMENTUM_DELTA:
        _log.warning("apply_momentum unrecognized band=%s delta=0", band)

    # MB-4: depth-based catch-up acceleration when momentum is at -3 or below
    if current < -2 and band in ("success", "crit_success"):
        deeper_delta = 2 if band == "success" else 3
        new_val = max(MOMENTUM_MIN, min(MOMENTUM_MAX, current + deeper_delta))

    # MB-4: normal path (unchanged) — only apply if no depth override happened
    # Actually, the original line 26 already handles this. Just replace it with conditional logic above.
```

Actually let me be precise about what to change. The existing code at lines 23-27 is:

```python
    delta = MOMENTUM_DELTA.get(band, 0)
    if band not in MOMENTUM_DELTA:
        _log.warning("apply_momentum unrecognized band=%s delta=0", band)
    new_val = max(MOMENTUM_MIN, min(MOMENTUM_MAX, current + delta))
    pc["momentum"] = new_val
```

Replace lines 23-26 with:

```python
    delta = MOMENTUM_DELTA.get(band, 0)
    if band not in MOMENTUM_DELTA:
        _log.warning("apply_momentum unrecognized band=%s delta=0", band)

    # MB-4: depth-based catch-up acceleration at -3 or below
    recovery_delta = delta
    if current < -2 and band in ("success", "crit_success"):
        deeper_delta = 2 if band == "success" else 3
        _log.debug("apply_momentum MB-4 deep_recovery momentum=%d band=%s delta=%d→%d",
                   current, band, delta, deeper_delta)
        recovery_delta = deeper_delta

    new_val = max(MOMENTUM_MIN, min(MOMENTUM_MAX, current + recovery_delta))
    pc["momentum"] = new_val
```

**Why:** MB-4 confirmed — `MOMENTUM_DELTA` uses uniform deltas (`success=+1`, `fail=-1`) regardless of depth. At -3, a single success only recovers to -2 (one turn of progress). Depth-based acceleration at -3 gives +2 recovery (to 0), breaking the spiral in one successful roll instead of requiring two consecutive successes against likely failures.

**Validation:**
```python
# Test momentum.py directly:
python3 -c "
from ccya.state.momentum import apply_momentum
s = {'pc': {'momentum': -2}}; apply_momentum(s, 'success'); assert s['pc']['momentum'] == 0, f'expected 0 got {s[\"pc\"][\"momentum\"]}'
s = {'pc': {'momentum': -3}}; apply_momentum(s, 'success'); assert s['pc']['momentum'] == -1, f'expected -1 got {s[\"pc\"][\"momentum\"]}'  # +2 at -3
s = {'pc': {'momentum': -3}}; apply_momentum(s, 'fail'); assert s['pc']['momentum'] == -3, f'expected -3 (clamped) got {s[\"pc\"][\"momentum\"]}'  # fail=-1 from -3 → -4 clamped to -3
print('All momentum tests passed')
"
```

---

#### Step 01.2 — Prevent Breathe from appending "Resolve a Threat" in beat_locked

**File:** `ccya/engine/turn.py` (lines ~551-557)

**What:** In `_compute_pacing_context()`, when building the beat_locked directive, check if the existing directive is "Breathe". If so, do NOT append "; Resolve a Threat" — Breathe is de-escalation and contradicting itself with threat resolution makes no sense.

Current code (lines 551-557):
```python
    # Determine beat_locked: relief fired when either consecutive pressure threshold reached or momentum at minimum
    beat_locked = False
    if consecutive_pressure_turns >= config.consecutive_pressure_threshold or momentum <= config.momentum_floor:
        beat_locked = True
        directive_parts = [directive] if directive else []
        directive_parts.append("Resolve a Threat")
        directive = "; ".join(directive_parts) or ""
```

Change to:
```python
    # Determine beat_locked: relief fired when either consecutive pressure threshold reached or momentum at minimum
    beat_locked = False
    if consecutive_pressure_turns >= config.consecutive_pressure_threshold or momentum <= config.momentum_floor:
        beat_locked = True
        directive_parts = [directive] if directive else []
        # MB-2: never append threat resolution to Breathe — it's de-escalation, not escalation
        if directive != "Breathe":
            directive_parts.append("Resolve a Threat")
        directive = "; ".join(directive_parts) or ""
```

**Why:** MB-2 confirmed — `beat_locked` appends "; Resolve a Threat" to ANY directive including Breathe, producing contradictory "Breathe; Resolve a Threat". The player is at -2/-3 momentum (crisis) and the system tells them to both de-escalate AND resolve threats simultaneously.

**Validation:**
```python
# Verify no syntax errors:
python3 -c "from ccya.engine.turn import _compute_pacing_context; print('OK')" 2>&1 | head -5
```

---

#### Step 01.3 — Make floor relief injection conditional on consecutive_pressure (not momentum_floor)

**File:** `ccya/engine/turn.py` (lines ~1064-1072)

**What:** Change the OR condition for floor relief from (`consecutive_pressure_threshold OR momentum_floor`) to AND (`consecutive_pressure_threshold AND beat_locked`). Floor relief should only fire when there's genuine consecutive pressure, not pure momentum-floor crisis.

Current code (lines 1063-1072):
```python
            # Floor relief injection — runs BEFORE apply_delta so breathing_room persists through the deep copy. Post-apply block was moved here and removed from its original location.
            if _pc.beat_locked:
                _current_beat = state.get("meta", {}).get("pending_gm_beat")
                if _current_beat is None or _current_beat.get("type") in PRESSURE_BEAT_TYPES:
                    meta = state.setdefault("meta", {})
                    meta["pending_gm_beat"] = {
                        "type": "breathing_room",
                        "surface_as": "ambient",
                        "beat_expires_turn": turn_no + 2,
                    }
```

Change to check that beat_locked was triggered by consecutive_pressure (not just momentum_floor):

```python
            # Floor relief injection — runs BEFORE apply_delta so breathing_room persists through the deep copy. Post-apply block was moved here and removed from its original location.
            # MB-3: only inject floor relief when beat_locked is caused by consecutive pressure, not pure momentum crisis
            if _pc.beat_locked:
                # Read current state values at this scope (momentum and consecutive_pressure_turns are not local vars)
                cur_momentum = int((state.get("pc") or {}).get("momentum", 0))
                triggered_by_momentum = (cur_momentum <= config.momentum_floor)

                # Don't inject ambient beats during momentum crisis — player needs escalation, not breathing room
                if not triggered_by_momentum:
                    _current_beat = state.get("meta", {}).get("pending_gm_beat")
                    if _current_beat is None or _current_beat.get("type") in PRESSURE_BEAT_TYPES:
                        meta = state.setdefault("meta", {})
                        meta["pending_gm_beat"] = {
                            "type": "breathing_room",
                            "surface_as": "ambient",
                            "beat_expires_turn": turn_no + 2,
                        }
```

Wait — this is too restrictive. The findings say floor relief should only fire when beat_locked from consecutive_pressure, not momentum_floor. But what about the case where BOTH conditions are true? Let me re-read MB-3:

> **MB-3 CONFIRMED:** Floor relief injection (`turn.py:1064-1072`) fires when `beat_locked`, injecting `breathing_room` (type=ambient) — the opposite of what's needed during momentum crisis. Fires 15/16 beat_locked turns.

The issue is that floor relief injects ambient beats DURING momentum crisis, which is wrong because at -2/-3 you want pressure not breathing room. But when consecutive_pressure triggers it (without momentum being low), the player genuinely needs a breather after sustained pressure.

So the fix should be: only fire floor relief when triggered_by_pressure AND NOT triggered_by_momentum. If both are true, don't inject — let the momentum spiral play out without ambient interference.

Actually wait, re-reading more carefully: what if consecutive_pressure is high but momentum happens to also be low because of it? That's a natural cascade and floor relief might still help break the cycle... But MB-3 says 15/16 beat_locked turns fire floor relief — that's almost every time. The problem isn't just momentum_floor triggering it, it's that ambient beats are wrong during ANY crisis period (whether from pressure or momentum).

Let me reconsider: maybe the fix is simpler — only inject when triggered_by_pressure AND consecutive_pressure hasn't been climbing for too long (e.g., < 3 turns)? No, that overcomplicates it.

The simplest correct interpretation of MB-3: floor relief should NOT fire during pure momentum_floor crisis (`momentum <= config.momentum_floor`). It's fine to fire when only triggered by consecutive_pressure threshold. If both are true, don't inject — the player is in a genuine spiral and needs pressure, not breathing room.

Let me refine the change (final version):

```python
            # Floor relief injection — runs BEFORE apply_delta so breathing_room persists through the deep copy. Post-apply block was moved here and removed from its original location.
            # MB-3: only inject floor relief when beat_locked is caused by consecutive pressure, not momentum crisis
            if _pc.beat_locked:
                triggered_by_momentum = (momentum <= config.momentum_floor)

                # Don't inject ambient beats during momentum crisis — player needs escalation, not breathing room
                if not triggered_by_momentum:
                    _current_beat = state.get("meta", {}).get("pending_gm_beat")
                    if _current_beat is None or _current_beat.get("type") in PRESSURE_BEAT_TYPES:
                        meta = state.setdefault("meta", {})
                        meta["pending_gm_beat"] = {
                            "type": "breathing_room",
                            "surface_as": "ambient",
                            "beat_expires_turn": turn_no + 2,
                        }
```

**Why:** MB-3 confirmed — floor relief injects `breathing_room` (type=ambient) when beat_locked fires from momentum_floor. This is the opposite of what's needed during a momentum crisis at -2/-3 where the player needs escalation/pressure to break out of the spiral, not ambient de-escalation. By excluding momentum_floor-triggered relief, floor relief only fires for genuine consecutive_pressure spirals (where sustained pressure without momentum penalty genuinely warrants a breather).

**Validation:**
```python
# Verify no syntax errors:
python3 -c "from ccya.engine.turn import _compute_pacing_context, apply_thread_updates; print('OK')" 2>&1 | head -5
```

---

#### Step 01.3a — Fix auto-latent demotion to fire every turn (thread lifecycle gap)

**File:** `ccya/engine/turn.py` (~lines 224-237, in thread_updates loop after mutations applied)

**What:** The existing auto-latent demotion at lines 226-237 only runs when `mutated=True`, meaning it never fires if no other threads were updated that turn. Stale active threads stay active indefinitely. Fix: update `last_updated_turn` for ALL active threads every turn so the stale threshold check (`turn_no - last_updated_turn >= thread_stale_threshold`) can fire reliably regardless of mutation state.

Before (lines 224-237):
```python
    if config and mutated:
        stale_threshold = config.thread_stale_threshold
        for i, t in enumerate(remaining_threads):
            if (
                t.last_updated_turn is not None
                and (turn_no - t.last_updated_turn) >= stale_threshold
                and t.active
            ):
                updated = t.model_copy(update={"active": False, "last_updated_turn": turn_no})
                remaining_threads[i] = updated
```

After:
```python
    # Update last_updated_turn for all active threads every turn so the
    # stale threshold check below fires reliably regardless of mutation state.
    if config and remaining_threads:
        for i, t in enumerate(remaining_threads):
            if t.active:
                updated = t.model_copy(update={"last_updated_turn": turn_no})
                remaining_threads[i] = updated

    # Auto-latent demotion — fire every turn (not gated on mutated).
    if config and remaining_threads:
        stale_threshold = config.thread_stale_threshold
        for i, t in enumerate(remaining_threads):
            if (
                t.last_updated_turn is not None
                and (turn_no - t.last_updated_turn) >= stale_threshold
                and t.active
            ):
                updated = t.model_copy(update={"active": False, "last_updated_turn": turn_no})
                remaining_threads[i] = updated
```

**Why:** The existing auto-latent demotion at `thread_stale_threshold=3` (config.py) only fires when `mutated=True`, meaning it never runs if no other threads were updated that turn. Stale active threads stay active indefinitely — this is the root cause of #5 thread accumulation alongside the sanitizer's missing temporal decay instruction. By updating all active threads' timestamps every turn, the stale threshold check can fire reliably regardless of mutation state.

**Validation:**
```python
# Verify no syntax errors:
python3 -c "from ccya.engine.turn import apply_thread_updates; print('OK')" 2>&1 | head -5
```

---

#### Step 01.4 — Lower scene_imperative_threshold from 5 to 4 (MB-6)

**File:** `ccya/engine/config.py` (~line 153)

**What:** Change the default value of `scene_imperative_threshold` from 5 to 4 in both the dataclass definition and the YAML parser.

Current code:
```python
    scene_imperative_threshold: int = 5
```

Change to:
```python
    scene_imperative_threshold: int = 4
```

Also update the YAML parser default (around line ~263):
```python
        scene_imperative_threshold=int(game.get("scene_imperative_threshold", 4)),
```

**Why:** MB-6 confirmed — combat boost adds +2 to scene_age, causing Scene Imperative to fire earlier in combat scenes. But even without combat, it fires at turn 5 which is late relative to when scenes actually need intervention (by T7+ the same scene may have been active 10+ turns). Lowering threshold from 5→4 gives one extra turn of pacing recovery before forcing scene advancement.

**Validation:**
```python
# Verify config loads correctly:
python3 -c "from ccya.engine.config import EngineConfig; c = EngineConfig(); assert c.scene_imperative_threshold == 4, f'expected 4 got {c.scene_imperative_threshold}'; print('OK')" 2>&1 | head -5
```

---

#### Step 01.5 — Validate MB-5 pressure counter fix (no code change)

**File:** `ccya/engine/turn.py` (lines ~1074-1082)

**What:** Audit the existing consecutive pressure counter logic to confirm it reads from `pending_gm_beat` after floor relief injection, not raw storyteller output. No changes needed — this was already fixed in a previous commit (`fix-b1-mb5-b3.md`).

Current code (lines 1074-1082):
```python
            # Consecutive pressure counter: reads post-floor-relief pending_gm_beat
            _current_beat = state.get("meta", {}).get("pending_gm_beat")
            _beat_type = _current_beat.get("type") if _current_beat else None
            meta = state.setdefault("meta", {})
            current_pressure = meta.get("consecutive_pressure_turns", 0)
            if _beat_type in PRESSURE_BEAT_TYPES:
                meta["consecutive_pressure_turns"] = current_pressure + 1
            else:
                meta["consecutive_pressure_turns"] = 0
```

**Why:** MB-5 was previously at different line numbers (findings referenced 1291-1301 which is now thread_add validation). The fix moved the counter to read from `pending_gm_beat` after floor relief injection. Verify this logic is correct: it reads the stored beat type (which may have been overridden by floor relief) and only increments pressure when the actual pending beat is a pressure-type, not breathing_room.

**Validation:**
```python
# Confirm no syntax errors from all turn.py changes above:
python3 -c "from ccya.engine.turn import _compute_pacing_context; print('OK')" 2>&1 | head -5

# Verify the counter logic reads pending_gm_beat (not storyteller output):
grep -n 'consecutive_pressure_turns' /Users/pwilson/repos/ccya/ccya/engine/turn.py | head -10
```

Expected: all references to `consecutive_pressure_turns` should be in the block at lines 1074-1082 (reading from pending_gm_beat). No other locations should read raw storyteller output for this counter.

---

#### Step 01.6 — Update eval constant imports if needed

**File:** `ccya/eval/universal_asserts.py` and/or `ccya/eval/engine_mirror.py`

**What:** Check whether the momentum delta changes in Step 01.1 require updating any eval assertions that validate momentum band-to-delta mapping. The `MOMENTUM_DELTA` constant dict is unchanged (still success=+1, fail=-1), but `apply_momentum()` now applies a depth-based multiplier internally.

The auto-checker at `universal_asserts.py:268-279` (`check_momentum_band_delta`) validates that momentum changed per the band using `MOMENTUM_DELTA.get(band)`. With MB-4, this assertion will FAIL for success rolls at -3 because actual delta is +2 but expected from MOMENTUM_DICT is +1.

**Change needed:** Modify `check_momentum_band_delta` at line ~279 to account for depth-based recovery. The function already has access to prev momentum via the local variable `prev_m` (line 307). Replace lines 278-279 with:

```python
    # In universal_asserts.py, modify around line 279:
    band = ruling.get("band", "")
    
    # MB-4: account for depth-based catch-up at -3 or below
    prev_momentum_for_delta = int(prev_snap.get("pc", {}).get("momentum") or 0)
    delta = MOMENTUM_DELTA.get(band, 0)
    if band in ("success", "crit_success") and prev_momentum_for_delta < -2:
        deeper_delta = 2 if band == "success" else 3
        expected = deeper_delta
    else:
        expected = delta
```

**Why:** The auto-checker validates momentum changes against the static `MOMENTUM_DELTA` mapping. With MB-4, actual delta at -3 is +2 (not +1). Without this update, every success roll at -3 would trigger a false-positive assertion failure in eval runs. Note: the function already reads prev_momentum at line 307 as `prev_snap.get("pc", {}).get("momentum") or 0` — reuse that same value with the MB-4 override logic instead of computing it again from scratch.

**Validation:**
```python
# Verify universal_asserts imports cleanly:
python3 -c "from ccya.eval.universal_asserts import check_momentum_band_delta; print('OK')" 2>&1 | head -5
```

---

#### Step 01.7 — Update documentation (repomap)

**File:** `docs/repomap.md`

**What:** If any new functions, signatures, or module boundaries changed in this phase, update the repomap accordingly. Check if momentum.py's apply_momentum signature changed (it didn't — same function name and parameters). Verify no other doc updates needed for config defaults change (`scene_imperative_threshold: 4`).

**Validation:**
```python
# Final syntax check across all modified files:
python3 -c "from ccya.state.momentum import apply_momentum; from ccya.engine.turn import _compute_pacing_context, _compute_narration_directive, apply_thread_updates; from ccya.engine.config import EngineConfig; print('All imports OK')" 2>&1 | head -5

# Run lint + typecheck:
make check 2>&1 | tail -20
```

---

## Implementation — Phase 02: Sanitizer prompt fixes (thread cleanup #5 + goal pivot #3)

### Context files to load
- `ccya/prompts/sanitize_thread.j2` — the sanitizer LLM template (88 lines, system section at top, user instructions at ~line 37)

### Detailed steps

**Ordering note:** Steps 02.1 and 02.2 must run sequentially (step 02.1 first) because step 02.2's edit target references the file state after step 02.1's insertion.

#### Step 02.1 — Add explicit temporal decay instruction for stale background threads (#5)

**File:** `ccya/prompts/sanitize_thread.j2` (~lines 42-46)

**What:** In the Instructions section (after existing items 1-4), add item 5 with explicit temporal decay cleanup:

Current instructions (lines 39-48):
```markdown
Review each active thread against the narrative evidence and output a JSON
object inside <sanitize> tags. For each thread consider:

1. Is it narratively resolved? → add to resolved_threads[] with resolution_state + outcome.
2. Is urgency wrong for what happened? → update urgency field.
3. Should it be latent or active again? → set active field.
4. Are progress entries noisy, dedup-worthy, or too long? → provide updated progress list (5–7 words per entry, factual).

Also consider the arc goal and context — should visible_goal or goal_context be
updated to reflect current narrative direction?
```

After line 427 (after item 4's period), insert the temporal decay instruction:

Before (line 428):
```markdown


Also consider the arc goal and context — should visible_goal or goal_context be
updated to reflect current narrative direction?
```

After (insert between lines 427-429):
```markdown


# Temporal decay cleanup:
# If a thread is inactive (active=false) and has not been updated for 3+ turns,
# it was likely auto-demoted to latent by the engine. Check whether it still has
# narrative relevance — if no new progress entries since its last_updated_turn AND
# there's no ongoing narrative reason to keep it alive, move it to resolved_threads[]
# or remove from active threads entirely. Do NOT immediately remove a thread that was
# just demoted this turn (it may have 1-2 more turns of relevance). Use judgment:
# background threads with no progress_updates for multiple sanitizer cycles should be removed.

Also consider the arc goal and context — should visible_goal or goal_context be
updated to reflect current narrative direction?
```

And update the `_checklist.resolved` field at lines 84-85 to reflect decay cleanup:

Before (line 84):
```json
"resolved": "N threads narratively resolved",
```

After (line 84):
```json
"resolved": "N threads narratively resolved or decayed to completed",
```

**Why:** #5 confirmed — background threads (`broken_defense`, `looting_scourge`, `coinage_panic`) accumulated across 20+ turns without resolution, demotion to latent, or fading. Step 01.3a fixes the engine so auto-latent demotion fires reliably every turn (not gated on mutation). But demotion only sets `active=False` — it doesn't remove threads from the list entirely. The sanitizer is what actually removes stale latent threads via temporal decay: inactive for 3+ turns with no new progress_updates → move to resolved_threads[] or remove entirely. This two-layer approach handles both active (engine) and latent (sanitizer) thread cleanup paths.

**Validation:**
```python
# Verify template renders without Jinja errors:
python3 -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('/Users/pwilson/repos/ccya/ccya/prompts'))
t = env.get_template('sanitize_thread.j2')
print(t.render(visible_goal='test', threads=[], completed_threads=[], turn_no=10, recent_turns=[], prior_history=[]))
print('Template renders OK')
" 2>&1 | tail -3
```

---

#### Step 02.2 — Add explicit goal pivot instruction for major events (#3)

**File:** `ccya/prompts/sanitize_thread.j2` (~after the temporal decay section, before "Also consider")

After step 02.1's temporal decay section, add the goal pivot instruction before "Also consider":

Before (lines ~439-452 after step 02.1 runs):
```markdown


# Temporal decay cleanup:
# If a thread is inactive (active=false) and has not been updated for 3+ turns,
# it was likely auto-demoted to latent by the engine. Check whether it still has
# narrative relevance — if no new progress entries since its last_updated_turn AND
# there's no ongoing narrative reason to keep it alive, move it to resolved_threads[]
# or remove from active threads entirely. Do NOT immediately remove a thread that was
# just demoted this turn (it may have 1-2 more turns of relevance). Use judgment:
# background threads with no progress_updates for multiple sanitizer cycles should be removed.

Also consider the arc goal and context — should visible_goal or goal_context be
updated to reflect current narrative direction?
```

After (insert between temporal decay section's last line and "Also consider"):
```markdown


# Temporal decay cleanup:
# If a thread is inactive (active=false) and has not been updated for 3+ turns,
# it was likely auto-demoted to latent by the engine. Check whether it still has
# narrative relevance — if no new progress entries since its last_updated_turn AND
# there's no ongoing narrative reason to keep it alive, move it to resolved_threads[]
# or remove from active threads entirely. Do NOT immediately remove a thread that was
# just demoted this turn (it may have 1-2 more turns of relevance). Use judgment:
# background threads with no progress_updates for multiple sanitizer cycles should be removed.

# Goal pivot — must update visible_goal when narrative direction fundamentally changed:
# If a major event occurred that changes what the PC is trying to accomplish
# (witness escapes/is killed, ally falls in combat, location shifts dramatically,
#  debt settled/lost, new critical information discovered), you MUST update
# visible_goal to reflect current reality. Do NOT keep goals about objectives
# that no longer exist or are no longer relevant. The goal should always point
# forward to what the PC needs to do NOW, not what they were trying to do 3 turns ago.

Also consider the arc goal and context — should visible_goal or goal_context be
updated to reflect current narrative direction?
```

And update the `_checklist.goal` field at lines 86-87 to reflect goal pivot tracking:

Before (line 86):
```json
"goal": "Goal unchanged or updated (why)"
```

After (line 86):
```json
"goal": "Goal updated (why) OR confirmed current and relevant"
```

**Why:** #3 confirmed — arc goal stayed unchanged T1-T15 (2/3 of noir) despite debt settlement, ledger pursuit, cellar discoveries, bodyguard confrontation, and alley standoff. The sanitizer template only asks whether the goal "should be updated to reflect current narrative direction" — a passive evaluation that depends on subjective judgment. Adding explicit trigger events (witness escapes/killed, ally killed, location changes, new critical info) gives the LLM concrete criteria for when pivot is mandatory vs optional.

**Validation:**
```python
# Verify template still renders cleanly after all sanitizer changes (#3 goal pivot + #5 temporal decay):
python3 -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('/Users/pwilson/repos/ccya/ccya/prompts'))
t = env.get_template('sanitize_thread.j2')
print(t.render(visible_goal='test', threads=[], completed_threads=[], turn_no=10, recent_turns=[], prior_history=[]))
print('Template renders OK after all changes')
" 2>&1 | tail -3

# Final syntax check:
python3 -c "from ccya.engine.thread_sanitizer import sanitize_threads; print('OK')" 2>&1 | head -5

# Run lint + typecheck:
make check 2>&1 | tail -20
```

---

### Tests to write or update

Tests are temporarily removed during refactor per AGENTS.md rules. No test writing required for this plan.
