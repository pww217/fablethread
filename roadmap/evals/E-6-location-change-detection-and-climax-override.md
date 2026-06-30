---
title: "Location change detection fails on first two changes; CLIMAX forces escape over combat resolution"
status: testing
urgency: 2
size: medium
created: 2026-06-30
ticket_id: E-6
labels:
  - engine
  - pacing
  - extraction
  - narrator
---

## E-6 Eval Session Focus Areas

**This eval session is specifically investigating:**
1. **Pacing problems** — CLIMAX override forcing escape over resolution, endless CLIMAX→escape→CLIMAX loops, scene phase transitions
2. **Convergence issues** — convergence score staying high, preventing scene resolution, convergence detection mechanics
3. **Narration mechanics** — narrator-extractor contract on location detection, transit vs arrival language, narrator agency
4. **Beats** — beats too specific, beats hijacking narrator, beats overriding presence decay, beat specificity causing endless loops
5. **NPC life cycles** — presence tracking not working, guards persisting 20+ turns, presence auto-decay overridden by beats, NPC decay pipeline

**User instructions:** Incremental refinement only. No major overhauls or new features. Fine-tune pacing, convergence, narration mechanics, beats, and NPC life cycles. Gather evidence first. Do full rubric for every set of runs. Track work within this ticket. Make minor changes/fixes and iterate. Everything sequentially.

## Review Context

Eval review of `saves/cordyceps-year-twenty-2026-06-29/`, turns 1-23. User reported: (1) location changes don't register after first one, (2) endless combat struggle with bad rolls, (3) scene imperatives DO fire.

## Sources

- `saves/cordyceps-year-twenty-2026-06-29/chronicle.md`
- `saves/cordyceps-year-twenty-2026-06-29/events.jsonl`
- `saves/cordyceps-year-twenty-2026-06-29/prompts.jsonl`
- `saves/cordyceps-year-twenty-2026-06-29/state.yaml`
- Commands: `ev.py turn`, `ev.py mechanics`, `ev.py trace`, `ev.py check`

## Mechanic Focus

Location change detection, CLIMAX pacing override, narrator-extractor contract.

## Findings

### Finding 1: First two location changes are invisible to extractor

Turns 2 and 3 both describe clear location changes:
- Turn 2: Hub → rooftop ledge (via service chute)
- Turn 3: Rooftop → alleyway → junkyard

But `applied.location_change` shows `(no data)` for both. First registered change is turn 6 (junkyard → cooling station).

**Root cause: narrator-extractor mismatch.** The narrator prompt says *"If location or focus changed, start at the arrival — never narrate the journey there."* But turns 2-3 narration describes **transit** ("scramble through tunnel", "slide down shingles", "break into sprint"), not arrival. The extractor's detection rule requires "arriving at a new place" language. Transit language doesn't trigger detection.

This is a contract violation: the narrator writes what the extractor can't parse.

**Fix applied:** Updated `extract_state_system.j2:123` detection rule to include transit language detection: "scramble through," "run to," "travel to," "head to," "move into," "cross into" — these describe movement between locations and imply a change. Reverted the narrator arrival language constraint (narrator writing transit language is good prose; the extractor should parse it).

### Finding 2: CLIMAX override forces escape over combat resolution

Roll history (23 turns): 7 failures, 5 successes, 1 crit_fail. Combat starts turn 8 (guards breach cooling station) and never resolves.

The scene phase machine cycles normally: CLIMAX→RESOLUTION→BREATHER→RISING→CLIMAX. Scene imperatives fire on turns 6, 12, 18. But the combat threat (`approaching_substation_pursuit`, urgency=urgent) persists across all phase transitions.

**Root cause: `_pacing.py:187-188` unconditionally overrides `outcome_hint` to "transition" when CLIMAX exceeds 4 turns:**

```python
if scene_phase == "CLIMAX" and config and climax_turn_count >= config.climax_turn_limit:
    outcome_hint = "transition"
```

This prevents the narrator from resolving the confrontation. Instead, the narrator writes escape mechanics: "the blast door slams shut" (turn 10), "you miss the shaft" (turn 11). The player escapes but the threat persists. Convergence score stays ≥3. CLIMAX fires again. Endless loop.

**Fix applied:** Removed the CLIMAX override entirely from `_pacing.py`. Trust ruling's `scene_motion` hint — if ruling says "transition" the narrator respects it. Only scene imperative and convergence hard gate can override ruling's hint now.

### Finding 3: Scene imperatives DO fire (validating user's observation)

Confirmed. My initial hypothesis about `turn_entered` resetting `scene_age` to 0 was wrong. `turn_entered` is only set when a location change actually applies. Turns without location changes accumulate `scene_age` normally. Scene imperatives fire correctly on turns 6, 12, 18.

### Finding 4: NPC presence tracking doesn't work — guards persist for 20+ turns

Armed Guards appear turn 2 on the rooftop. They are present in narration through at least turn 23 (21 turns). Even when the player changes locations multiple times (turn 6 cooling station, turn 12 substation, turn 19 crawlspace, turn 23 ventilation shaft), the guards "catch up" every time.

The presence system (`present` → `nearby` → `known` → `departed`) is designed to auto-decay NPCs when the player leaves their area. `extract_scene_system.j2:79` says `"nearby" auto-decays to "known" after 2 turns if not re-promoted`. But the guards never get demoted past `nearby`/`present`.

**Root cause: world pipeline beats inject guard pressure every turn.** The world pipeline generates beat candidates every turn. Even after the player escapes to different locations, the beat candidates keep including guard-related effects ("searchlight beam snaps toward the terminal's blue glow", "heavy footsteps approach from both ends"). The narrator reads these beats and writes the guards into the new scene. The extractor sees the guards in narration and re-promotes them to `present`. The presence system's auto-decay never gets a chance to work because the beats keep re-inserting the NPCs.

This is a beats-over-presence conflict: beats are the stronger signal and override the presence decay system.

**Fix applied:** Excluded `nearby` NPCs from beat generation (`world.py:47`), ruling prompt (`narrate.py:251`), and scene narration (`narrate_system.j2:34`). Only `present` NPCs are used for beat generation, preventing the feedback loop: beats → narration → extractor re-promotion → beats for present.

### Finding 5: Beats are too specific — they hijack the narrator

World pipeline beats are written as full paragraphs with specific actions, specific NPCs, specific outcomes. Example from turn 4:

```
{'type': 'escalation', 'effect': "The searchlight beam that was sweeping the rooftops suddenly snaps toward the terminal's blue glow, as an Armed Guard halts their patrol to investigate the light leak.", 'npcs': ['armed_guards']}
```

This is not a hint — it's a script. The narrator reads this and has no room to interpret it differently. It clamps the narrator's mouth shut. The narrator's job is to write fiction based on player input + scene context. Beats should be vague directional hints, not specific plot points.

**Root cause: beats are too specific.** They should be 5-7 words, vague, interpretable, and allowed to move in multiple directions. Examples of what beats should be:
- "searchlight sweeps closer" (could go toward player, toward an object, toward a guard)
- "boots echo in the dark" (could be guards, could be something else, could be player's own echo)
- "static crackles on the recorder" (could be the voice, could be interference, could be a new signal)

Instead, beats are specific plot instructions: "The searchlight beam that was sweeping the rooftops suddenly snaps toward the terminal's blue glow, as an Armed Guard halts their patrol to investigate the light leak." This forces the narrator to write exactly that scene. It removes all narrative agency from the narrator and turns beats into a parallel plot driver that competes with (and usually wins against) player input.

This explains the endless combat loop too: the beats keep injecting guard pressure regardless of what the player does, regardless of location changes, regardless of scene phase. The beats are the real driver of the loop, not just the CLIMAX override.

**Fix applied:** Updated `world_system.j2:21` to require 5-7 word vague hints with explicit good/bad examples. Beats are now 5-6 words (previously 26-38 words).

### Finding 6: convergence_recompute checker fails on real saves

The `convergence_recompute` checker failed on both `the-outer-rim--after-unification-2026-06-30` and `cordyceps-year-twenty-2026-06-29` saves. It reported `scene_age: stored=1, recomputed=0` on turns 4-6.

**Root cause: checker's fallback for `scene_entered` didn't match `_compute_ages()`.** `_compute_ages()` reads `scene.get("turn_entered", 0)` and defaults to 0 when not set. The checker's fallback computed `scene_entered = current_turn - turns_in_phase + 1`, which gave wrong values. Additionally, when a location change occurred, `turn_entered` was set by `delta_builder` AFTER ruling, so the checker read the post-delta_builder value instead of the pre-delta_builder value that `_compute_ages()` saw.

**Fix applied:** Updated `ccya/ev/checkers/pacing_convergence.py:216-242`: fallback for `scene_entered` uses 0 (matching `_compute_ages`), handles `turn_entered` just-set by delta_builder, reads `recent_beats`/`recent_rolls` from previous turn's state to match what engine used. Both saves now pass `convergence_recompute`.

### Finding 7: Beats are now appropriately short but still repeating

After updating `world_system.j2` to require 5-7 word vague hints, beats are now 5-6 words (previously 26-38 words). However, the same beats repeat across turns 2-5.

**Root cause: dedup only tracks selected beats, not all generated beats.** The ruling phase only appends selected beats to `recent_beats` (`ruling.py:220`). If no beat was selected, the generated beats are discarded (`ruling.py:232`). The next turn's world step generates new beats based on `recent_beats` (which doesn't include the unselected beats), so the LLM generates the same beats again.

**This is a design issue, not a prompt issue.** The world step should track all generated beats (not just selected ones) to avoid repetition. Alternatively, the dedup should compare against all generated beats from previous turns, not just selected beats.

**Fix applied:** Moved `recent_beats` tracking from ruling phase (`ruling.py:219-227`) to world step (`world.py:191-205`). All generated beats (not just selected) are now tracked in `recent_beats` for diversity tracking.

### Finding 8: sanitizer_lifecycle checker false positive on threads_resolved

Checker only checked `state.arc.threads` for `threads_resolved`, but threads resolved on the same turn are already in `completed_threads`.

**Fix applied:** Updated `ccya/ev/checkers/sanitizer.py:46-53` to also check `completed_threads` in valid thread lookup.
