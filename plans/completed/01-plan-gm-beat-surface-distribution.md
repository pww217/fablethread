# 01-plan-gm-beat-surface-distribution.md — GM Beat Surface As Distribution

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Add surface_as distribution guidance to progress extractor prompt | Provide few-shot examples showing healthy distribution across all six surface types; add explicit instruction to rotate surfaces during extended sequences. Prompt-only change. |

## Objective
GM beats use `surface_as = "environmental"` in ~85%+ of cases across both saves examined (medical crisis T3-T8, boarding combat). Only T2 in the medical save uses `npc_behavior`. The six valid surface types (`ambient`, `event`, `npc_behavior`, `environmental`, `player_discovery`, `item`) have no distribution guidance. This makes beat manifestations predictable and reduces narrative variety during extended sequences like 6-turn crisis arcs.

## Non-goals
- No changes to Python source files.
- No changes to GMBeat model schema or validation.
- No changes to engine-level beat lifecycle (carry/consume/replace).
- No changes to pending_gm_beat storage in `state["meta"]`.

## Implementation — Phase 01: Add surface_as distribution guidance

### Files to pull for context
- `ccya/prompts/extract_progress_system.j2` — the ONLY file modified. Contains current GM beat type/surface instructions at lines ~97–118.
- Existing beats from saves/default (T1-T9) as negative examples: T3-T8 all use environmental.

### Detailed steps

#### Step 1.1 — Add surface_as distribution guidance to extract_progress_system.j2

**File:** `ccya/prompts/extract_progress_system.j2`

**Current text (GM beat section, lines ~97–106):**
```
gm_beat: a single GM beat to shape the next turn, or null if none is needed.
- deescalate > 0.5 → prefer breathing_room or null (no beat)
- deescalate == 0.0 with active pressure → pressure or escalation
- narration_directive takes precedence over deescalate when both are present
- Recent twist or callback beats should not repeat within 2 turns
- type values: complication, revelation, opportunity, breathing_room, pressure, twist, setback, escalation, callback
- surface_as values: ambient, event, npc_behavior, environmental, player_discovery, item
- Each beat must be narratively specific: name NPCs, reference locations, tie to active threads
- Emit as: {"type": "pressure", "surface_as": "npc_behavior", "instruction": "..."}
```

**Add after `- surface_as values:` line:**

> **Surface distribution rule:** Across a 3+ turn sequence, you MUST vary `surface_as` — do not repeat the same type in consecutive turns. Rotate through:
> - T1 beat → use one type (e.g., environmental)
> - T2 beat → switch to a different type (e.g., npc_behavior or player_discovery)
> - T3+ beat → cycle back to an unused type, then repeat only after all six have appeared at least once.
> 
> **Guidance per surface type with examples:**
> - `ambient` — atmosphere/mood shift: "A heavy silence falls over the crew as they realize what you've discovered."
> - `event` — a concrete happening in-scene: "The door bursts open and Captain Reyes strides in, wet from the storm."
> - `npc_behavior` — named NPC changes demeanor or makes a move: "Vargas steps aside with barely concealed bitterness. You notice he's no longer watching you with deference."
> - `environmental` — scene setting shifts: "The lantern gutters and dies, leaving only moonlight through the shattered window."
> - `player_discovery` — player finds something new: "You pry loose a floorboard and find a folded letter sealed with black wax."
> - `item` — inventory/tool relevance: "Your old sea-knife catches on your coat as you move — you hadn't thought of it in years, but its edge is still true."

**Add after `- Recent twist or callback beats should not repeat within 2 turns`:**

> **Beat type diversity:** During extended sequences (3+ consecutive pressure-type beats), at least every third beat must use a non-pressure type. Pressure and escalation are appropriate during active crises, but callbacks, complications, and revelations break monotony even in tense moments. A callback beat references an earlier narrative development: "The merchant you spared last week returns with reinforcements — he remembers your mercy."

**Why:** The current instructions list valid surface types but provide no distribution guidance. LLMs default to the safest option (environmental) when given freedom. Few-shot examples with explicit rotation rules force variety. This is a proven technique in prompt engineering for structured JSON output.

### Tests to write or update
Run `make check` after editing to confirm no linting errors were introduced. No Python tests affected — this is a template-only change.

To validate the fix works: run 3+ turns with an active save and inspect progress extraction outputs. Verify that surface_as values rotate across at least 4 of 6 types over a 5-turn window.

### REPOMAP updates
`docs/REPOMAP/prompts.md` line ~10 — update extract_progress_system.j2 description to note "GM beat surface distribution guidance with few-shot examples and rotation rules."

### Risks
1. **LLM ignores rotation instruction.** Mitigation: include concrete T1→T2→T3 example sequence in the prompt showing type progression. If LLM still defaults, consider adding a harder constraint: "Do not repeat surface_as within 2 consecutive turns — this is mandatory."
2. **Force-distribution makes beats feel artificial during genuine crises.** Mitigation: guidance says "at least every third beat must use non-pressure type" — allows concentration of pressure types during active combat/crisis while preventing monotony.

## Ambiguities requiring resolution before execution
None. The six surface_as values are defined in `GMBeat.surface_as` Literal type. Distribution guidance is purely instructional in the prompt.
