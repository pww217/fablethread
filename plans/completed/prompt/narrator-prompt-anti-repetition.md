# Narrator prompt: anti-repetition + NPC favoring

## Status
`completed`

## Phases

2 phases: (1) strengthen anti-repetition directive, (2) add NPC favoring guidance.

## Issue

The narrator re-describes plot events and prior-turn content instead of advancing the story. The current "NO REPETITION RULE" (line 130 of narrate_system.j2) only covers sensory details, metaphors, and imagery. Line 12 says "Don't repeat known facts or restate conditions already mentioned" but it's buried in the Style section and not strong enough to prevent plot rehashing. The LLM needs an explicit, prominent directive to never re-describe events the player already experienced.

Separately, the narrator doesn't favor NPCs with motivation/fear/leverage when weaving characters into scenes. The roster shows all NPCs equally regardless of their narrative depth.

## Solution

Add a strengthened anti-repetition directive in `narrate_system.j2` that explicitly covers plot/event rehashing, not just sensory details. Place it prominently (not buried at line 130). Add soft guidance to favor NPCs with motivation/fear/leverage when weaving characters into scenes. No hard roster filtering.

## Firm decisions

1. The anti-repetition rule must cover plot/event rehashing specifically, not just sensory repetition.
2. The rule must be prominent — near the top of the system prompt, not buried after all other sections.
3. NPC favoring is soft guidance only — "prefer NPCs with motivation/fear/leverage set" — not a hard roster filter.
4. The existing "NO REPETITION RULE" at line 130 will be removed (replaced by the new prominent directive).
5. The existing line 12 guidance ("Don't repeat known facts or restate conditions already mentioned") will be consolidated into the new directive (removed as standalone line).
6. No changes to storyteller prompts or extraction prompts.

## Non-goals

- Restructuring the narrator system prompt beyond what's needed for 4a+4b. A separate plan can address broader restructuring.
- Changing the NPC roster builder or filtering NPCs out of the roster.
- Adding new fields to NPCRosterEntryBlock or other models.
- Changing the storyteller, extraction, or compactor prompts.
- Changing how prior_history or recent_turns are rendered.

## Risks, Ambiguities, and Blockers

- **Prompt length:** Adding a new prominent section increases the narrator system prompt. The current prompt is already ~132 lines. Adding 4-6 lines for the directive is acceptable.
- **LLM compliance:** Anti-repetition rules are hard to enforce perfectly. The directive must be specific and actionable, not just "don't repeat."
- **Overlap with line 40:** "Open with the player's action. Do not spend more than one sentence bridging from the previous turn" already addresses bridge sentences. The new directive overlaps but is more general. Consolidating is fine.

## Implementation — Phase 1: Strengthen anti-repetition directive

### Context files to load

- `ccya/prompts/narrate_system.j2` (full file — 132 lines)

### Detailed steps

#### Step 1.1 — Remove existing anti-repetition rules and consolidate

**File:** `ccya/prompts/narrate_system.j2`

**What:** Remove three existing anti-repetition signals:
1. Line 12: `"Avoid tropes; invent fresh twists, weird details, even humor in dark stories. Don't repeat known facts or restate conditions already mentioned."` — Remove the clause "Don't repeat known facts or restate conditions already mentioned." from this sentence. Keep the rest.
2. Line 40: `". . . Do not spend more than one sentence bridging from the previous turn."` — Remove "Do not spend more than one sentence bridging from the previous turn" from this sentence. Keep the rest.
3. Lines 130-132: The entire `**NO REPETITION RULE:**` block — Remove it entirely.

**Why:** These three rules are being consolidated into one stronger, more prominent directive (Step 1.2). Leaving fragments creates contradictory guidance.

**Validation:** `make check` passes. The three locations listed above no longer contain the removed text.

#### Step 1.2 — Add prominent anti-repetition directive after "## Player input is truth"

**File:** `ccya/prompts/narrate_system.j2`

**What:** Insert a new section immediately after the `## Player input is truth (HIGHEST PRIORITY)` section and before `## Pragmatic interpretation`. The new section:

```
## Never repeat prior narration

The player has already read every prior turn. Do not re-describe events they witnessed, restate conditions already established, or rehash dialogue from earlier scenes. Each turn must advance — never circle back to what the player already knows.

Self-check before writing: does any sentence in your draft restate something the player was already told? If yes, delete it and replace with new information, a new reaction, or a forward beat.
```

**Why:** Placed after Player Input Is Truth (the highest-priority rule) because anti-repetition is the second-most important behavioral constraint. The "self-check" instruction gives the LLM a concrete verification step, which is more effective than just a prohibition. Specific enough to cover plot/event rehashing, not just sensory repetition.

**Validation:** `make check` passes. The new section appears between Player Input Is Truth and Pragmatic Interpretation.

## Implementation — Phase 2: NPC favoring guidance

### Context files to load

- `ccya/prompts/narrate_system.j2` (the `## NPCs in scene` section, around lines 45-63)

### Detailed steps

#### Step 2.1 — Add soft NPC favoring guidance

**File:** `ccya/prompts/narrate_system.j2`, within the `## NPCs in scene` section

**What:** Add two sentences after the `**NPC BEHAVIOR DRIVERS:**` paragraph (which describes motivation/fear/leverage). The addition:

```
Favor NPCs who have at least one of these drivers set. NPCs with empty motivation, fear, and leverage are background — mention them only when setting or continuity requires it, never as scene focal points.
```

**Why:** Soft guidance, not a hard filter. The LLM sees all NPCs in the roster but is nudged to give depth and dialogue to NPCs that have narrative drivers, while treating empty-driver NPCs as scenery.

**Validation:** `make check` passes. The new sentences appear within the `## NPCs in scene` section, after the NPC BEHAVIOR DRIVERS paragraph.

### Tests to write or update

No tests to write or update (tests are temporarily removed during refactor).

### REPOMAP updates required

- `docs/repomap.md` — note that narrate_system.j2 has strengthened anti-repetition and NPC favoring directives (update the prompt templates section if one exists)