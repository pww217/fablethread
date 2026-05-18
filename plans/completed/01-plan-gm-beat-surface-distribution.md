# 01-plan-gm-beat-surface-distribution.md — GM Beat Surface As Distribution

## Status
`open`

## Phases

Phase 01 only: Add surface_as distribution rotation rules and few-shot guidance for all six surface types to `extract_progress_system.j2`, plus beat type diversity instruction requiring non-pressure beats during extended sequences. This is the foundation phase — subsequent phases (02–07) layer crisis-aware selection, band-aligned alignment, narrative peak callbacks, compaction awareness, eval rubric hooks, and validation tests on top of these distribution rules.

## Issue
GM beats use `surface_as = "environmental"` in ~85%+ of cases across both saves examined (medical crisis T3–T8 with respiratory failure→seizures→arrest→near-death→stabilization; boarding combat-heavy segments). Only T2 in the medical save uses `npc_behavior`. The six valid surface types (`ambient`, `event`, `npc_behavior`, `environmental`, `player_discovery`, `item`) have no distribution guidance. LLMs default to "environmental" as the safest option when given freedom, producing beats like "The lantern gutters and dies" repeated across 6+ consecutive turns during crisis arcs. This makes beat manifestations predictable and reduces narrative variety — players experience extended sequences as a wall of atmospheric description with no NPC behavior shifts, discoveries, events, or item relevance to break monotony.

## Solution
Add explicit surface_as rotation rules and few-shot examples for all six types to `extract_progress_system.j2`, instructing the progress extractor LLM to vary surfaces across 3+ turn sequences without repeating consecutive turns. Add beat type diversity guidance requiring non-pressure beats at least every third turn during extended pressure cascades. The prompt template change gives the LLM concrete alternatives with examples, forcing it to rotate through surface types rather than defaulting to environmental. Expected outcome: surface_as distribution shifts from ~85%+ environmental toward roughly even spread across 4–6 types over a 10-turn window, creating more varied beat manifestations during extended sequences.

## Firm decisions
1. **Prompt-only change.** No Python source files are modified. The six surface_as values already exist as a `Literal` type in the GMBeat model — no schema changes needed.
2. **Rotation is soft guidance, not hard constraint.** "Do not repeat same type in consecutive turns" and "at least every third beat must use non-pressure type" set floors/expectations but allow LLM discretion when narrative context demands concentration of a particular surface (e.g., genuine environmental crisis where all beats are legitimately environmental).
3. **Beat type diversity is separate from surface distribution.** Beat types (`pressure`, `escalation`, `callback`, etc.) and surfaces (`ambient`, `event`, `npc_behavior`, etc.) are orthogonal dimensions — this phase addresses both but keeps the guidance sections distinct for clarity.
4. **Examples must be concrete, not abstract.** Each surface type gets a one-line description plus an example instruction string that demonstrates what beats of that surface look like in practice. This is more effective than abstract descriptions alone.

## Non-goals
- No changes to Python source files (`ccya/engine/`, `ccya/models.py`, etc.).
- No changes to GMBeat model schema, validation rules, or the `GMBeat.surface_as` Literal type.
- No changes to engine-level beat lifecycle (carry/consume/replace logic in `turn.py`).
- No changes to pending_gm_beat storage in `state["meta"]`.
- No eval rubric additions — surface distribution quality is not yet scored by judges.
- No Python tests for prompt template behavior — validation is manual via save inspection after execution.

## Risks, Ambiguities, and Blockers

**Risk 1: LLM ignores rotation instruction.** The LLM may still default to environmental despite the guidance if it perceives "environmental" as contextually appropriate for every turn. Mitigation: concrete T1→T2→T3 example sequence in prompt showing type progression; explicit "MUST vary surface_as — do not repeat same type in consecutive turns" language. If LLM still defaults after execution, the next iteration would add a harder constraint line: "Do not repeat surface_as within 2 consecutive turns — this is mandatory."

**Risk 2: Force-distribution makes beats feel artificial during genuine crises.** Forcing surface variety when all beats are legitimately environmental (e.g., ship sinking sequence) could produce contrived beats. Mitigation: guidance uses "MUST vary" for rotation but allows narrative context to override — the examples show that each surface type CAN apply even in crisis contexts (item relevance with tools, npc_behavior with crew panic, etc.).

**Risk 3: Token budget impact.** Adding ~15 lines of prompt text increases system prompt size by roughly 200–300 tokens. Mitigation: this is within the default `prompt_token_budget` of 32768 and represents <1% increase to total context window for extraction calls. The token cost in prompts.md notes that trim_messages() drops oldest non-system messages first, so system prompt additions are retained over older turn history.

**Ambiguity resolved: Where exactly does the new text go?** The surface distribution rule goes after `- surface_as values:` line (line 99) and before `- Each beat must be narratively specific` (line 100). Beat type diversity goes as a standalone section after the callback/twist recency note on line 70. This keeps related guidance grouped: deescalate rules → callback recency → beat type diversity → surface_as values → surface distribution → per-type examples → grounding rules.

**Ambiguity resolved: What counts as "consecutive turns"?** The rotation rule applies to consecutive GM beats emitted by the progress extractor across successive turn extractions — not to every turn (beats are sparse, null is common). If T3 emits a beat with `surface_as = environmental`, T4's beat should use a different surface. Null beats don't count as "repeating" since null means no beat at all.

**Ambiguity resolved: What if fewer than 6 turns in sequence?** The rotation rule says "across a 3+ turn sequence." For sequences of exactly 3 turns, rotate through 3 different types before cycling back. For shorter sequences (1–2 beats), the guidance is aspirational — it only becomes mandatory at 3+.

**Blockers:** None. No dependencies on other phases or completed work. The template change is self-contained and independently executable.

## Implementation — Phase 01: Add surface_as distribution guidance

### Context files to load
The executor MUST read these files in order before making changes:

1. **`ccya/prompts/extract_progress_system.j2`** (lines 64–113) — the ONLY file modified. Contains current GM beat type/surface instructions that need augmentation with distribution rules and few-shot examples.
2. **`docs/repomap.md`** (line 88, extraction field routing section) — to confirm `gm_beat` is a ProgressExtractResult field and understand how surface_as flows through the pipeline from progress extractor → state delta → pending_gm_beat → narrator.

### Detailed steps

#### Step 01.01 — Add beat type diversity guidance after callback recency note

**File:** `ccya/prompts/extract_progress_system.j2`

**Context (lines 69–70):**
```jinja2
- Recent `twist` or `callback` beats should not repeat within 2 turns, **but callbacks SHOULD fire during narrative peaks** — a callback referencing an earlier event is most effective at major pivot moments (near-death stabilization, unexpected revelation). Do not suppress callbacks just because one fired recently.

```

**What:** Insert a new standalone section after line 70 (the blank line following the callback recency note) that adds beat type diversity guidance for extended sequences. This addresses the problem where T3–T8 in medical save all use `type = "pressure"` with no callbacks, complications, or revelations to break monotony.

**Why:** The current instructions have "recent twist/callback should not repeat within 2 turns" which prevents repetition but actively discourages callbacks at structurally appropriate moments. During extended crises with pressure-only beats every turn, this creates narrative monotony. The guidance below makes callbacks/twists/revelations fire at structurally appropriate moments while keeping pressure beats appropriate for early crisis turns.

**Code Snippet:**
```jinja2
**Beat type diversity:** During extended sequences (3+ consecutive pressure-type beats), at least every third beat must use a non-pressure type. Pressure and escalation are appropriate during active crises, but callbacks, complications, and revelations break monotony even in tense moments. A callback beat references an earlier narrative development: "The merchant you spared last week returns with reinforcements — he remembers your mercy."
```

**Validation:** Read the file after edit to confirm the section appears as a standalone bold-paragraph between line 70 (callback recency) and line 72 (`type` values listing). No Python tests affected.

#### Step 01.02 — Add surface_as distribution rule and per-type guidance examples

**File:** `ccya/prompts/extract_progress_system.j2`

**Context (lines 98–100):**
```jinja2
- `surface_as` values: `ambient`, `event`, `npc_behavior`, `environmental`, `player_discovery`, `item`

- Each beat must be narratively specific: name NPCs, reference locations, tie to active threads
```

**What:** Insert surface distribution rotation rules and per-type guidance with concrete examples after line 99 (the `- surface_as values:` bullet) and before the blank line on line 100. This gives the LLM explicit instructions to rotate surfaces across turns plus one-line descriptions + example instruction strings for each of the six types.

**Why:** The current template lists valid surface_types but provides NO distribution guidance or examples. LLMs default to "environmental" as the safest option when given freedom — 85%+ usage in production saves confirms this bias. Few-shot examples with explicit rotation rules force variety through concrete demonstration rather than abstract instruction alone.

**Code Snippet:**
```jinja2
- `surface_as` values: `ambient`, `event`, `npc_behavior`, `environmental`, `player_discovery`, `item`

**Surface distribution rule:** Across a 3+ turn sequence, you MUST vary `surface_as` — do not repeat the same type in consecutive turns. Rotate through T1→T2→T3 using different types each time; cycle back to an unused type before repeating any type.

**Guidance per surface type with examples:**
- `ambient` — atmosphere/mood shift: "A heavy silence falls over the crew as they realize what you've discovered."
- `event` — a concrete happening in-scene: "The door bursts open and Captain Reyes strides in, wet from the storm."
- `npc_behavior` — named NPC changes demeanor or makes a move: "Vargas steps aside with barely concealed bitterness. You notice he's no longer watching you with deference."
- `environmental` — scene setting shifts: "The lantern gutters and dies, leaving only moonlight through the shattered window."
- `player_discovery` — player finds something new: "You pry loose a floorboard and find a folded letter sealed with black wax."
- `item` — inventory/tool relevance: "Your old sea-knife catches on your coat as you move — you hadn't thought of it in years, but its edge is still true."

- Each beat must be narratively specific: name NPCs, reference locations, tie to active threads
```

**Validation:** Read the file after edit. Verify that all six surface types have a description + example instruction string. The blank line before `- Each beat must be narratively specific` should remain intact for readability. No Python tests affected — template-only change. Run `make check` to confirm no linting errors were introduced (ruff only checks Python files, so this is a null operation but good practice).

### Tests to write or update
No Python test changes needed — this phase modifies only the Jinja2 prompt template (`extract_progress_system.j2`). No new tests are written for template content validation.

**Manual validation after execution:** Run 3+ turns with an active save and inspect progress extraction outputs (check `events.jsonl` for turn entries containing progress stream results). Verify that:
1. surface_as values rotate across at least 4 of 6 types over a 5-turn window in extended sequences.
2. No two consecutive beats in the same sequence use the same surface_as type.
3. Beat types include non-pressure types (callback, complication, revelation) during turns 3+ of pressure-heavy sequences.

To inspect progress extraction output for a specific turn: look for entries with `"kind": "progress"` and check the `gm_beat.surface_as` field in the extracted JSON payload within that event's data.

### REPOMAP updates required
Update `docs/repomap.md`: The template file listing section does not currently have a dedicated prompts subsection. Add to the module index table after line 13 (narrate.py entry):

| File | Responsibility |
|---|---|
| `ccya/prompts/extract_progress_system.j2` | Progress extractor system prompt — GM beat type/surface guidance with rotation rules, few-shot examples for all six surface types, crisis-aware selection, band-aligned alignment, narration directive mapping to beats/pressures. |

This gives future executors quick visibility into what the progress extraction template contains without reading 150+ lines of Jinja2 prompt text.
