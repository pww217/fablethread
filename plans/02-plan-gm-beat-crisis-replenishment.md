# 02-plan-gm-beat-crisis-replenishment.md — GM Beat Replenishment During Crises

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Add crisis-aware beat type guidance to progress extractor prompt | Provide explicit instructions for callback/twist/revelation beats during narrative pivots in extended sequences. Prompt-only change. |

## Objective
During 6+ turn crisis arcs (medical T3-T8 with respiratory failure→seizures→arrest→near-death→stabilization; boarding combat-heavy segments), GM beat type distribution collapses to pressure/escalation only. Callback beats — which reference earlier narrative developments and create narrative resonance — are virtually absent. Twists and revelations don't fire during major pivot moments (T7 respiratory arrest, T8 near-death stabilization). The current "recent twist/callback should not repeat within 2 turns" rule prevents repetition but doesn't actively encourage callbacks at structurally appropriate moments.

## Non-goals
- No changes to Python source files.
- No changes to beat lifecycle logic in `turn.py` (carry/consume/replace/expires).
- No changes to scene pressure TTL or urgency escalation.
- No changes to narrative_velocity computation.

## Implementation — Phase 01: Add crisis-aware beat type guidance

### Files to pull for context
- `ccya/prompts/extract_progress_system.j2` — ONLY file modified. GM beat section at lines ~97–118.
- Existing saves/default T3-T9 data showing pressure-only beats during extended crises with no callbacks/twists/revelations.

### Detailed steps

#### Step 1.1 — Add crisis-aware beat type guidance to extract_progress_system.j2

**File:** `ccya/prompts/extract_progress_system.j2`

**Add a new section after `- Emit as: {"type": "pressure", "surface_as": "npc_behavior", "instruction": "..."}"` and before `- If no beat is warranted, emit null`:**

> **Crisis-aware beat selection:** During extended sequences (3+ turns with active scene pressures), you MUST vary beat types — do not repeat pressure/escalation every turn. Use this guidance:
> 
> - **Turns 1–2 of a crisis sequence:** Pressure and escalation beats are appropriate. The situation is new; escalate to communicate stakes.
> - **Turn 3+:** At least one in three beats must use callback, complication, revelation, twist, or opportunity type. This breaks monotony and creates narrative resonance.
> - **At major pivot moments** (a character nearly dies and recovers, a failed plan succeeds unexpectedly, an NPC makes a decisive choice), you MUST consider:
>   - `revelation` — new information changes understanding: "You learn Campos filed the audit with the port authority three days ago. This was planned."
>   - `twist` — narrative direction shifts unexpectedly: "The miner's seizures stop as suddenly as they began. His eyes open and he whispers your name in a language you don't know."
>   - `callback` — references an earlier beat or event with new resonance: "The ventilation fan you repaired last week seizes with a grinding shriek — the metal fatigue you warned about has caught up to it."
>   - `opportunity` — a path forward opens in unexpected way: "Through the chaos, you notice Aaron watching your repairs. He's been trained in this work and makes eye contact with clear intent to help."
> 
> **Guidance per non-pressure type:**
> - `complication` — an existing pressure creates cascading effects: "The guard captain's delay means reinforcements arrive armed — not just with batons, but with tear gas canisters you didn't expect."
> - `revelation` — new information changes how earlier events should be understood. Use sparingly (1–2 per arc).
> - `twist` — narrative direction shifts in an unexpected way. Most appropriate at major pivot moments.
> - `callback` — references a beat, NPC action, or environmental detail from 3+ turns ago with new resonance. Most effective when the earlier instance was subtle.
> - `opportunity` — path forward opens unexpectedly. Best used after failure/setback to maintain player agency.

**Add this note at end of `- Recent twist or callback beats should not repeat within 2 turns`:**

> **However, callbacks SHOULD fire during narrative peaks.** A callback beat referencing an earlier event is most effective when it coincides with a major pivot (near-death stabilization, unexpected revelation, decisive NPC action). Do not suppress callbacks just because one fired recently — structural resonance matters more than recency.

**Why:** The current instructions have "recent twist/callback should not repeat within 2 turns" which prevents repetition but actively discourages callbacks at structurally appropriate moments. During extended crises with pressure-only beats every turn, this creates narrative monotony. Players experience T3–T8 as a wall of "more dust/worse equipment failure" with no callback to earlier events (e.g., Campos threatening audit in T1 becoming relevant during stabilization in T8). The guidance above makes callbacks/twists/revelations fire at structurally appropriate moments while keeping pressure beats appropriate for early crisis turns.

### Tests to write or update
Run `make check` after editing. No Python tests affected — template-only change.

To validate: run 5+ turns with active scene pressures and inspect progress extraction outputs. Verify callback/twist/revelation types appear at major pivot moments (not just pressure every turn).

### REPOMAP updates
`docs/REPOMAP/prompts.md` line ~10 — update extract_progress_system.j2 description to note "GM beat crisis-aware type selection with callback/twist/revelation guidance for narrative peaks."

### Risks
1. **LLM overuses callbacks making beats feel forced.** Mitigation: "at least one in three" sets a floor, not a ceiling. LLM can use more callbacks if narratively appropriate. The pivot-moment emphasis keeps callbacks grounded.
2. **Revelation/twist types used too frequently breaking narrative tension.** Mitigation: revelation guidance says "Use sparingly (1–2 per arc)." This is soft guidance; harder constraint could be added later if needed.

## Ambiguities requiring resolution before execution
None. Beat type values are defined in `GMBeat.type` Literal type with 9 valid options. Crisis-aware selection is purely instructional.
