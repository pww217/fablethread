# Ev1 fix — Prompt alignment for beat type selection, null emission, and fail near-miss guidance

## Status
`open`

## Phases
Single phase: all changes to `storytell_system.j2` and `narrate_system.j2`.

## Issue
Three prompt-level contradictions in the storyteller and narrator system prompts produce incorrect and inconsistent LLM behavior:

1. **Band-beat misalignment (Critical, ev1 #1):** The band-aligned beat selection section (`storytell_system.j2:92-98`) says `partial → complication, pressure` but the pacing context directive (Breathe when narrative_velocity < -0.3) overrides this. The LLM follows the directive rather than the band guidance, producing breathing_room beats on all 4 PARTIAL outcomes. No documented priority between these two signals.

2. **Fail near-miss contradiction (Medium, ev1 #8):** The narration directive says "narrate a complication or setback" for fail near-misses, while the storyteller beat guidance explicitly says "Do NOT emit escalation/pressure on failed checks." These contradictory instructions produce split behavior: T1 chose pressure (following narration), T4/T10 chose breathing_room (following beat guidance).

3. **Universal beat emission (Medium, ev1 #5):** The storyteller emits a non-null `gm_beat` on every turn despite guidance saying "null unless independent narrative reason for beat." This makes the `turn_no > beat_expires_turn` expiry check dead code — beats are perpetually replaced before expiring, and the auto-clear path for extraction failures is untested.

All three issues are structural: the prompt contains conflicting signals that the LLM resolves inconsistently, and no documented priority hierarchy exists for beat selection.

## Solution
Three edits to `storytell_system.j2`, one to `narrate_system.j2`:

1. **Document directive/band priority**: Add a priority rule at the top of the "Band-aligned beat selection" section: "Pacing context directive takes precedence over band alignment for beat type selection. When directive is Breathe, always prefer breathing_room or null regardless of roll band. When directive is Pressure/Overwhelm, always prefer complication/pressure regardless of roll band." This eliminates the contradiction by establishing Breathe as the override signal for beat type, making partial+low-momentum "Breathe → breathing_room" the correct behavior.

2. **Fix fail near-miss beat guidance**: Update the fail/setback beat guidance to include a near-miss exception: "On fail near-misses (roll was close — within 2 of the threshold), a complication beat is acceptable as the near-miss creates narrative friction without compounding punishment. Use discretion: breathing_room is still valid if the scene needs de-escalation." This removes the contradiction while keeping discretion for scene-appropriate choices.

3. **Add null emission requirement**: Add a sentence to the "no roll" guidance and the "deescalating" guidance: "Emit `gm_beat: null` at least once every 4 turns, even during Pressure phases, to give the beat expiry path a chance to fire and to allow for turns without narrative pressure."

4. **Narrator fallback for null beats**: Add a line to `narrate_system.j2` (or the `_arc.j2` template that renders beat context) covering the null-beat case: "If no GM beat is present, the scene continues without added pressure or relief — narrate purely from pacing context and player input."

## Firm decisions
1. The pacing directive always wins over band alignment for beat type. This is the actual observed behavior and documenting it as correct eliminates the prompt contradiction. Partial outcomes at low momentum *should* produce breathing_room beats.
2. The null emission cadence is "at least once every 4 turns" — not a strict counter, but a guideline to break the universal emission pattern. The exact cadence is a soft rule; the LLM keeps discretion based on scene state.
3. Narrator prompt gets the null-beat guidance but no structural changes to how prompts are built — when `pending_gm_beat` is None, the existing template already handles it gracefully (the narrator just doesn't receive a beat block).

## Non-goals
- Does not change the Python pacing logic or beat lifecycle code in `turn.py`. All changes are prompt-level only.
- Does not add a new pipeline phase or beat type. The existing beat types and lifecycle remain unchanged.
- Does not enforce strict rules for null emission cadence — the LLM retains discretion. The eval harness (Phase 1 universal asserts from `plans/eval-coverage-gaps.md`) will flag if universal beats continue.
- Does not change the one-turn beat lag (addressed in `03-beat-timing-observability.md`).

## Risks, Ambiguities, and Blockers
- Making Breathe the explicit override for beat type may cause PARTIAL outcomes at *high* momentum to keep getting breathing_room beats. The prompt must clarify that override only applies when directive is Breathe — if directive is Pressure (high urgency, high momentum), partials should still get complication/pressure. The fix must not blanket-silence band guidance.
- The near-miss definition ("within 2 of the threshold") must be documented in the prompt. Threshold means the fail cutoff (final_total ≤ 6 → fail). A near-miss is final_total = 5 or 6 (within 2 of the fail→setback boundary at 7). This is already how `build_directive()` distinguishes near-misses from outright failures — the prompt just needs to match that definition.
- Adding null emission guidance makes the prompt longer (~30 tokens). This is negligible for the token budget.
- The storyteller should be able to emit null even when `beat_locked` is True. Beat lock appends "Resolve a Threat" as a secondary directive but shouldn't force a non-null beat — the evaluator scenario added in `eval-coverage-gaps.md` Phase 3 will test this.

## Implementation

### Context files to load
- `ccya/prompts/storytell_system.j2`
- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/_arc.j2` (narrator context block that renders beat)
- `ccya/rules.py` (for `build_directive()` near-miss logic reference)

### Detailed steps

#### Step 1 — Document directive/band priority in storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2`

**What:** At the top of the "Band-aligned beat selection" section (line 92), add a priority preamble:

```
Pacing context directive takes precedence over band alignment for beat type.
- Directive "Breathe" → always prefer `breathing_room` or `null`, regardless of roll band.
- Directive "Pressure"/"Overwhelm" → always prefer `complication`/`pressure`, regardless of roll band.
- Directive "Tension" or empty → follow band alignment below.
```

Then update the existing guidance under it to remove the implied contradiction. The Breathe case already says "prefer breathing_room beat" at line 60 — make that explicit and link it to the priority rule.

**Why:** Eliminates the band-beat contradiction by establishing Breathe as the override. PARTIAL outcomes at low momentum producing breathing_room becomes *correct* behavior rather than a bug.

**Validation:** Re-read the updated prompt. Verify the band guidance and directive guidance no longer contradict each other.

#### Step 2 — Add near-miss exception to fail/setback guidance

**File:** `ccya/prompts/storytell_system.j2`

**What:** Update the `setback / fail` line (currently line 96):

Before:
```
- **setback / fail**: `breathing_room`, `null`, or rarely `complication`. Do NOT emit escalation or pressure beats on failed checks — the failure itself is the consequence. Escalation compounds punishment and breaks pacing.
```

After:
```
- **setback / fail**: `breathing_room`, `null`, or rarely `complication`. Do NOT emit escalation or pressure beats on failed checks — the failure itself is the consequence. Escalation compounds punishment and breaks pacing.
  Exception — **fail near-misses** (final_total is within 2 of the setback threshold at 7): `complication` is acceptable here because the near-miss creates narrative friction without compounding punishment. Use discretion — breathing_room or null are still valid if the scene needs de-escalation.
```

**Why:** The narration directive says "narrate a complication or setback" for fail near-misses, but the storyteller beat guidance says "Do NOT emit escalation/pressure on failed checks." Both are correct in isolation but contradictory when combined. The near-miss exception resolves this by acknowledging that near-misses are mechanically distinct from outright failures.

**Validation:** Re-read the updated prompt. Verify the exception text doesn't conflict with the general fail guidance above it.

#### Step 3 — Add null emission cadence guidance

**File:** `ccya/prompts/storytell_system.j2`

**What:** Add a sentence after the "Beat type diversity" section (line 73 area), or at the end of the band-aligned beat selection section:

```
To prevent beats from being perpetually active without release, emit `gm_beat: null` on at least 1 of every 4 turns, regardless of pacing directive. This gives the beat expiry mechanism a chance to fire and creates natural quiet moments even during Pressure phases.
```

Also update the "no roll" guidance (currently at the else clause, likely around line 98):
```
- **no roll**: `null` unless independent narrative reason for beat. Follow the 1-in-4 null cadence.
```

**Why:** The ev1 dataset showed zero null beats across 10 turns, making the expiry mechanism dead code. A soft cadence guideline creates opportunities for the expiry path to be exercised without forcing null on any specific turn.

**Validation:** Re-read the updated prompt. Verify cadence guidance appears in both the general section and the no-roll section.

#### Step 4 — Add null-beat fallback to narrator prompt

**File:** `ccya/prompts/narrate_system.j2` (or `ccya/prompts/_arc.j2` — confirm which template renders beat context)

**What:** Find where `pending_gm_beat` context is rendered for the narrator. Add a brief instruction: "If no GM beat is present, the scene continues without added pressure or relief — narrate purely from the pacing directive and player input."

If the narrator template already handles null beats gracefully (the existing `_arc.j2` may skip the beat block when null), this step is already done and only needs verification.

**Why:** When the storyteller starts emitting null beats, the narrator must handle that gracefully. The current code already passes `pending_beat=None` to the narrator when no beat exists, so the only risk is the prompt expecting a beat that isn't there.

**Validation:** Render the narrate template with `pending_beat=None` and verify no Jinja errors. Check that `_arc.j2` references `pending_gm_beat` with a null-safe pattern.

### Tests to write or update

None. Prompt changes are validated by review and subsequent eval runs (the universal asserts from `eval-coverage-gaps.md` Phase 1 will detect if beats remain universal).

### REPOMAP updates required

`docs/repomap.md` — Update the storytell_system.j2 description (line 111-114) to note the established directive/band priority, near-miss exception, and null cadence guidance.
