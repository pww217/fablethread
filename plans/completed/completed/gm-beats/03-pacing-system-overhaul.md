# Pacing System Overhaul: scene_age Collapse, Beat Carryover Fix, Consecutive Pressure Counter

## Status
`completed`

## Phases

1 phase: Collapse three age trackers to single `scene_age`, pre-compute effective_scene_age with combat boost before directive function call, rewrite narration directives using new Scene Pressure/Scene Imperative thresholds instead of Combat Fatigue, fix pending_gm_beat carryover by removing both unconditional clears, add consecutive_pressure_turns counter with two-pass end-of-turn update logic, and rework beat_locked relief trigger to dual OR condition (consecutive pressure threshold OR momentum floor).

## Issue
Three redundant age trackers (`location_age`, `combat_age`, `scene_age`) all measure the same concept — scene staleness — but only combat_age drives any directive ("Combat Fatigue"). Location_age feeds dead code (_inject_location_pressure never called) and a dead template section (nearby locations removed in Phase 01). The pacing system cannot detect when players receive repeated pressure directives without thread advancement, making it impossible to distinguish tense-but-progressing sequences from stuck loops. Additionally, `pending_gm_beat` is destroyed by unconditional clears after narration and during storytell else block, defeating any intent for GM beats to carry across turns until expiry or replacement.

## Solution
Collapse `_compute_ages()` to produce only `scene_age` (turns since scene.turn_entered). Pre-compute `"effective_scene_age"` in the ages dict before calling `_compute_narration_directive`: when combat is in scene tags, add +2 to scene_age so effective_scene_age = scene_age + 2. This makes scenes reach pressure thresholds ~2 turns earlier during combat without introducing a second age variable or complex weighted math.

Rewrite `_compute_narration_directive` to read `ages.get("effective_scene_age", 0)` and produce new directives: Scene Pressure (≥3 effective age) joins the priority stack between Tension and Threat Pressure; Scene Imperative (≥5 effective age) sits above Pressure as a higher-priority directive. These two subsume Location Pressure, Location Imperative, and Combat Fatigue — all three legacy definitions removed from narrate_system.j2.

Fix pending_gm_beat carryover by removing BOTH unconditional clears: line 1149 (post-narration clear before storytell runs) and lines 1198-1200 else block (re-clears when storytell emits null/no new beat). Beat lifecycle handled only by write/expiry — written after storytelling if non-null gm_beat, consumed read-gated at turn_no <= beat_expires_turn in _narrate_setup, cleared only on replacement or expiry.

Add `consecutive_pressure_turns` counter to state["meta"] with two-pass end-of-turn update: pacing_ctx directive value is baked into pacing context before storytelling runs (~line 982), thread_advance knowledge only available after extraction completes (~line 1188). At turn end, if pacing_ctx's directive was Pressure or Overwhelm AND storyteller result had empty thread_advance → increment counter. Reset to 0 whenever stored directive from that turn was not Pressure/Overwhelm OR when any thread was advanced during storytelling. beat_locked fires when either consecutive_pressure_turns >= config.consecutive_pressure_threshold (default 3) OR momentum <= config.momentum_floor (-3).

Expected outcome: One age signal replaces three, new directives fire at appropriate scene staleness points with combat acceleration baked in via effective_age pre-computation, GM beats persist across turns as designed until expiry or replacement, engine can detect stuck players receiving repeated pressure without progress.

## Firm decisions
1. Scene age thresholds: intermediate (Scene Pressure) at effective_age ≥ 3; high (Scene Imperative) at effective_age ≥ 5. Combat adds +2 boost to scene_age before threshold check — not a multiplier or weighted value, just additive so combat scenes reach pressure ~2 turns earlier reflecting need to press faster when danger present
2. Many signal inputs → multi-faceted output: scene_age joins the existing priority stack as another input alongside narrative_velocity, urgency counts, threat ages rather than replacing via weighted thresholds — consistent with how directive system already works
3. Effective_scene_age pre-computed in ages dict before calling _compute_narration_directive so function reads `ages.get("effective_scene_age", 0)` — no new parameters needed to existing signature which only accepts narrative_velocity, scope_scene_threads, ages dict, threat_ages list, config thresholds
4. pending_gm_beat carryover fix removes BOTH unconditional clears (~line 1149 and ~lines 1198-1200 else block); beat lifecycle handled by write/expiry only (written after storytelling if non-null gm_beat with beat_expires_turn = turn_no + 2, consumed read-gated at turn_no <= beat_expires_turn in _narrate_setup line 906-910, cleared when new beat written or expires)
5. Consecutive pressure counter uses two-pass end-of-turn update: stored directive value from pacing_ctx baked into context before storytelling runs (~line 982), thread_advance knowledge only available after extraction completes (~line 1188). Both checked together to increment/reset counter at turn end — avoids chicken-and-egg problem where directive must be known before storytelling but thread_advance is only known after
6. beat_locked dual-trigger OR condition: fires when either consecutive_pressure_turns >= config.consecutive_pressure_threshold (default 3) OR momentum <= config.momentum_floor (-3). Both triggers fire beat_locked rather than replacing one with the other — covers both stuck-player detection and rock-bottom safety valve without needing band history windowing
7. scene_age resets only on location_change when scene.turn_entered is updated; intra-scene pivots do NOT reset scene_age

## Non-goals
- No new config fields beyond consecutive_pressure_threshold (location_pressure_at/location_imperative_at removal deferred to Phase 01 cleanup)
- No changes to ArcThread lifecycle logic or key dedup (Phase 02 handles that separately)
- No primary thread designation ("most important active thread" deferred — value unclear without concrete consumer)
- No band history tracking (momentum covers the same ground well enough; avoids rolling list state management for marginal informational gain over consecutive_pressure_turns + momentum)

## Risks, Ambiguities, and Blockers
- **Ambiguity:** Where exactly to insert effective_scene_age into ages dict? The plan pre-computes it in _narrate_setup after ctx._ages = _compute_ages(state) but before pacing context computation (~line 982). This keeps the change localized to one function rather than modifying _compute_ages return value.
- **Risk:** Storyteller prompt narrate_system.j2 directive rewrites must maintain backward compat with existing pacing_context directives (Breathe, Overwhelm, Pressure, Tension) that are NOT being replaced — only Combat Fatigue is removed and Location Pressure/Imperative definitions deleted. The new Scene Pressure/Scene Imperative must slot into the priority stack correctly so higher-priority directives short-circuit lower ones as designed.
- **Blocker:** Phase 01 cleanup must complete first to have clean turn.py context around line 982 (no conflicting recently_left/JUST_LEFT references in _narrate_messages call). Phase 02 key dedup should also be done before this phase to avoid merge conflicts at the thread_add point.

## Implementation — Phase 3: Pacing System Overhaul

### Context files to load
- `/Users/pwilson/repos/ccya/ccya/engine/turn.py` (~lines 506-647 for _compute_narration_directive and _compute_pacing_context; ~line 890 for _narrate_setup effective_scene_age pre-computation point; ~1320-1360 for pacing_ctx directive storage point; ~1149/1198-1200 for pending_gm_beat unconditional clears to remove; ~lines 1475-1490 for end-of-turn consecutive_pressure_turns update point)
- `/Users/pwilson/repos/ccya/ccya/prompts/narrate_system.j2` (~line 109-113, directives section to rewrite: remove Location Pressure/Imperative and Combat Fatigue; add Scene Pressure/Scene Imperative with new thresholds)

### Detailed steps

#### Step 3.1 — Collapse _compute_ages() to scene_age only in turn.py

**File:** `ccya/engine/turn.py`

**What:** Rewrite `_compute_ages()` function (lines 649-672). Remove location_entered_turn computation and location_age variable entirely. Remove combat_started_turn check and combat_age variable entirely. The function should return only:
```python
return {
    "scene_age": scene_age,
}
```

Delete the following lines from the existing function body (lines 658-666): the loc_entered computation, location_age calculation, tags/combat_entered check for combat_started_turn, and combat_age conditional. Keep only the scene_entered/scene_age computation at lines 655-656.

**Why:** Three independent age counters all measure scene staleness — only scene_age is needed. Location_age feeds dead code (_inject_location_pressure never called) and Combat_Fatigue will be replaced by effective_scene_age combat boost in the directive function. Removing location_age and combat_age eliminates redundant computation and simplifies the ages dict to a single source of truth per concept, consistent with AGENTS.md clean code rules ("one source of truth per concept").

**Validation:** `rg -n "location_age|combat_age" ccya/engine/turn.py` returns zero matches for these strings in _compute_ages function body. The function now only computes and returns scene_age from scene.turn_entered.

#### Step 3.2 — Pre-compute effective_scene_age with combat boost before directive call in _ruling_phase

**File:** `ccya/engine/turn.py`

**What:** In `_ruling_phase()` after line 854 (`ctx._ages = _compute_ages(state)`), insert logic to compute and store `"effective_scene_age"` into the ages dict before pacing context computation (~line 982). The insertion point is between lines 854 and any subsequent code that reads from ctx._ages.

Compute effective scene age as: get `scene_age` from `ctx._ages.get("scene_age", 0)`. If `"combat"` in `(state.get("scene") or {}).get("tags") or []`, add +2 to the value; otherwise use raw scene_age. Store this computed value into `ctx._ages["effective_scene_age"]` so it's available when _compute_narration_directive reads from ages dict on line 984-985 (passed as `ages=ctx._ages`).

**Why:** The directive function signature only accepts an ages dict — no new parameters can be added without changing the interface contract. Pre-computing effective_scene_age into the existing ages dict lets _compute_narration_directive read it via `ages.get("effective_scene_age", 0)` with zero signature changes to any callers or downstream functions. The +2 combat boost makes scenes reach pressure thresholds ~2 turns earlier during combat reflecting need to press faster when danger is present, without introducing a second age variable or complex weighted math.

**Validation:** `rg -n "effective_scene_age" ccya/engine/turn.py` returns matches showing the new pre-computed value stored in ctx._ages before pacing context computation at line 982-986. The ages dict passed to _compute_narration_directive now contains both `"scene_age"` and `"effective_scene_age"` keys.

#### Step 3.3 — Rewrite _compute_narration_directive to use effective_scene_age with new thresholds in turn.py (~line 506)

**File:** `ccya/engine/turn.py`

**What:** Modify `_compute_narration_directive()` function (starting line 506). Replace the existing secondary combat fatigue check at lines 585-587 (`if ages.get("combat_age", 0) >= 3: secondary.append("Combat Fatigue")`) with new scene age threshold checks that produce Scene Pressure and Scene Imperative as primary directives rather than Combat_Fatigue as a secondary append.

Insert the following logic AFTER the Breathe check (after line 537 `return "Breathe"`) but before the secondary list init (line 539):
- Check `ages.get("effective_scene_age", 0)` for scene age thresholds: if ≥ 5 → set primary to "Scene Imperative" and return immediately (short-circuits all lower directives); if ≥ 3 but < 5, add "Scene Pressure" as a secondary directive that will be appended after the primary.

Update the docstring at line 514-534 to reflect new priority order:
```
Priority order (highest to lowest):
  1. Breathe       -- explicit de-escalation (velocity < -0.3)
  2. Scene Imperative -- scene has been stale too long (effective_age >= 5)
  3. Overwhelm     -- 3+ urgent threads
  4. Resolve a Threat -- aged-out threat pressure
  5. Pressure      -- 1-2 urgent threads
  6. Tension       -- background urgency threads only
  7. Scene Pressure -- scene approaching staleness (effective_age >= 3)
  8. Threat Pressure -- normal urgency aging toward imperative
```

**Why:** The new directives must slot into the priority stack correctly so higher-priority directives short-circuit lower ones as designed. Scene Imperative at ≥5 effective age is highest-priority (after Breathe) because a scene that has been stale for 5+ turns demands immediate attention — this replaces Location Imperative which was never emitted by any pacing logic anyway. Scene Pressure at ≥3 effective age joins the stack between Tension and Threat Pressure as an intermediate signal reflecting need to wind down or introduce movement reasons. Combat Fatigue is removed entirely because its function (pressing faster during combat) is now handled by the +2 combat boost to effective_scene_age — combat scenes reach scene_pressure threshold 2 turns earlier naturally without needing a separate directive label.

Also update PacingContext docstring at line 138 to include `"Scene Imperative"` and `"Scene Pressure"` in the possible directive values, and remove `"Combat Fatigue"`.

**Validation:** `rg -n "Combat Fatigue" ccya/engine/turn.py` returns zero matches in _compute_narration_directive function body and PacingContext docstring. The new directives use `ages.get("effective_scene_age", 0)` which reads the pre-computed value from Step 3.2.

#### Step 3.4 — Fix pending_gm_beat carryover by removing both unconditional clears in turn.py (~line 1149 and ~lines 1198-1200)

**File:** `ccya/engine/turn.py`

**What:** Two deletions:
- Delete line 1149 entirely: the comment block ("Clear pending_gm_beat after narration consumed it — not restored since Storytell no longer receives beat context") and the assignment `state.setdefault("meta", {})["pending_gm_beat"] = None`
- Delete lines 1198-1200 entirely: the else block (`else:` on line 1198, comment ("consume or no new beat — clear") on line 1199, and assignment `state.setdefault("meta", {})["pending_gm_beat"] = None` on line 1200). The if block above (lines 1192-1197) that writes a new beat when storytell emits non-null gm_beat should remain unchanged.

**Why:** These two unconditional clears destroy any carried GM beat before it reaches the next turn, defeating the designed intent for beats to persist until expiry or replacement. The only legitimate beat lifecycle management should be: written after storytelling if non-null (line 1192-1197), consumed read-gated at turn_no <= beat_expires_turn in _narrate_setup line 906-910, cleared when new beat replaces old or expires. Removing both unconditional clears allows beats to persist across turns as designed — the expiry check in _narrate_setup handles cleanup of expired beats automatically.

**Validation:** `rg -n "pending_gm_beat.*= None" ccya/engine/turn.py` returns zero matches for unconditional assignment outside the expiry-gated read gate at line 910. The only pending_gm_beat clearing now happens in _narrate_setup when turn_no > beat_expires_turn (line 910).

#### Step 3.5 — Add consecutive_pressure_turns counter with two-pass end-of-turn update logic to turn.py (~lines 1420-1434)

**File:** `ccya/engine/turn.py`

**What:** Insert new logic after all extraction/thread processing completes but before the turn increment (line 1436 after Phase 01 already removed recently_left decay block at old lines 1422-1430). The insertion point is after line 1420 (narrator arc_update handling) — the recently_left decay block that previously occupied old lines 1422-1430 was already removed by Phase 01 Step 1.2, so the next content after line 1420 is now whatever followed the decay block (previously at old line 1431+). Insert the new logic between line 1420 and the turn increment, after all processing that reads `n` is done, before state is finalized for save.

This block implements two-pass consecutive pressure counter update. At turn end, read `_pc.directive` (baked into pacing context at ~line 982-986, known before storytelling runs) and `n.thread_advance` from extraction results (available only after `_run_extraction_pipeline()` completes at ~line 1188).

Guard with `if _extract_result is not None and n is not None:` since `n` is only assigned inside `if _extract_result is not None:` at line 1188 — when extraction fails, `n` is undefined.

If `_pc.directive` was "Pressure" or "Overwhelm" AND `n.thread_advance` was empty → increment `state.setdefault("meta", {})["consecutive_pressure_turns"]` to next value. Otherwise (directive was not Pressure/Overwhelm OR any threads were advanced during storytelling) → reset counter to 0.

**Why:** The two-pass approach solves the chicken-and-egg problem: pacing_ctx directive must be known before storytelling runs (~line 982), but thread_advance is only available after extraction completes (~line 1188). By storing both values and checking them together at turn end, we get accurate consecutive pressure detection without requiring new function signatures or reordering the pipeline. The counter persists in state["meta"] so it survives across turns until reset by either non-pressure directive or thread advancement. The guard on `n` prevents `UnboundLocalError` when extraction fails.

**Validation:** `rg -n "consecutive_pressure_turns" ccya/engine/turn.py` returns matches showing the new two-pass update logic at turn end, reading _pc.directive and n.thread_advance to increment/reset counter in state["meta"]. The logic sits between extraction pipeline completion (lines 1390-1420) and turn increment (line 1436), guarded against extraction failure.

#### Step 3.6 — Add consecutive_pressure_threshold to config and dual-trigger beat_locked in _compute_pacing_context

**File:** `ccya/engine/config.py`

**What:** Add new field to EngineConfig dataclass (after line 84, momentum_ceiling):
```python
    # Consecutive pressure threshold for relief trigger
    consecutive_pressure_threshold: int = 3
```

Update build_engine_config function (~line 172 area) to map the config value from game dict with default fallback of 3.

**File:** `ccya/engine/turn.py`

**What:** Modify `_compute_pacing_context()` signature (lines 594-602). Add new parameter after momentum:
```python
    consecutive_pressure_turns: int = 0,
```

Update call site at line 982-986 to pass the value from state["meta"]:
```python
consecutive_pressure_turns=(state.get("meta") or {}).get("consecutive_pressure_turns", 0), config=config,
```

Replace beat_locked condition (lines 621-628) with dual-trigger OR logic:
```python
    # Determine beat_locked: relief fired when either consecutive pressure threshold reached or momentum at minimum
    beat_locked = False
    if consecutive_pressure_turns >= config.consecutive_pressure_threshold or momentum <= config.momentum_floor:
        beat_locked = True
        directive_parts = [directive] if directive else []
        directive_parts.append("Resolve a Threat")
        directive = "; ".join(directive_parts) or ""
```

**Why:** beat_locked must fire when either signal path triggers. Passing consecutive_pressure_turns as new parameter to _compute_pacing_context keeps pacing context computation self-contained rather than scattering logic across multiple functions. The config field provides the threshold value for stuck-player detection. Existing "Resolve a Threat" append behavior unchanged — fires whenever beat_locked is True regardless of which trigger fired it.

**Validation:** `rg -n "consecutive_pressure_threshold" ccya/engine/config.py` returns new field definition and build_engine_config mapping. `_compute_pacing_context` signature includes consecutive_pressure_turns parameter; call site at line 982-986 passes value from state["meta"]. beat_locked condition uses dual OR logic checking both thresholds.

#### Step 3.7 — Rewrite narrate_system.j2 directives section: remove Location Pressure/Imperative and Combat Fatigue, add Scene Pressure/Scene Imperative (~line 101)

**File:** `ccya/prompts/narrate_system.j2`

**What:** Two changes to the directives section (lines 101-113 after Phase 01 has already removed Location Imperative and Location Pressure bullet points from lines 110-111):
- Delete line 109 entirely: `- **Combat Fatigue** — Fight has run long. Bring to decisive close...` (Location Imperative and Pressure at old lines 110-111 were already removed by Phase 01; Threat Pressure shifted from old line 112 up to the new line 110)
- Add new directives AFTER the existing Tension definition (line 108) but BEFORE Threat Pressure (now at line 110 after Phase 01 cleared lines 110-111):

```
- **Scene Pressure** — The scene has been active for several turns. Begin winding down or introduce a reason to shift focus: a development elsewhere, a closing window, or a change in local situation that makes staying less compelling. Hint at movement without forcing it yet.
- **Scene Imperative** — The player has been in this scene too long (5+ turns). The story MUST advance — introduce a new development that forces resolution or movement: a character arrives with news from elsewhere, a time-sensitive opportunity or threat emerges, the environment changes to make staying untenable. Do not linger. Move the story forward decisively.
```

**Why:** These two new directives replace Location Pressure/Imperative (which were never emitted by any pacing logic) and Combat Fatigue (replaced by effective_scene_age combat boost). The new definitions use scene-level language rather than location-specific, reflecting that scene_age is now the single staleness signal. Scene Imperative at 5+ turns matches the high threshold from design doc; Scene Pressure at 3+ turns matches intermediate threshold.

**Validation:** `rg -n "Scene Pressure|Scene Imperative" ccya/prompts/narrate_system.j2` returns two new bullet point definitions in directives section. `rg -n "Combat Fatigue|Location Pressure|Location Imperative" ccya/prompts/narrate_system.j2` returns zero matches — all three legacy directive definitions removed.

### Tests to write or update
Per AGENTS.md ("Tests are temporarily removed during refactor"), tests are skipped for this phase. The following test references will need updating when tests re-enable:
- `tests/conftest.py` scene fixture includes `"location_entered_turn": 1` which becomes stale after _compute_ages collapse to only scene_age — inert data that won't cause failures but should be noted

### REPOMAP updates required
- `ccya/engine/turn.py`: `_compute_ages()` function signature unchanged (still accepts state dict, returns dict[str, int]) but return value shrinks from 3 keys ("scene_age", "location_age", "combat_age") to only `"scene_age"`. REPOMAP should note the removed age counters if it documents _compute_ages output shape. `_narrate_setup` adds effective_scene_age pre-computation into ctx._ages dict before pacing context computation (~line 982). `_compute_narration_directive` docstring updated to reflect new priority order with Scene Pressure/Scene Imperative replacing Combat Fatigue; function reads `ages.get("effective_scene_age", 0)` instead of combat_age. `_compute_pacing_context` signature gains new `consecutive_pressure_turns: int` parameter for dual-trigger beat_locked condition. Call site at line 982-986 updated to pass this value from state["meta"]. pending_gm_beat unconditional clears removed (line 1149 and lines 1198-1200 else block); only expiry-gated clear remains in _narrate_setup. New consecutive_pressure_turns two-pass update logic added at turn end (~line 1473). REPOMAP should note the new pipeline point if it documents run_turn flow around line 1320-1500.
- `ccya/prompts/narrate_system.j2`: Directives section rewritten — removed Combat Fatigue, Location Pressure, Location Imperative definitions; added Scene Pressure and Scene Imperative with scene-level language reflecting new single-age signal. REPOMAP should note the directive rewrites if it documents narrator prompt templates or pacing directives.
