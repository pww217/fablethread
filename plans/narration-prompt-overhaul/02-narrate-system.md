# Narration Prompt Overhaul — Phase 2: Narrate System Prompt Rewrite

## Purpose

Rewrite `narrate_system.j2` to produce shorter, more active turn narration with less modifier repetition and concrete style constraints.

## Problem Statement

Turn narration averages 306 words with pervasive modifier repetition. The Style section's aspirational instructions ("use colorful imagery, metaphors/similes") generate formulaic sensory templates rather than functional prose. Key fluff-cutting rules like "open with the player's action" are visually buried as sub-bullets. The anti-repetition self-check is phrased as a suggestion and routinely ignored.

## Constraints

- Template must remain compatible with the Jinja2 environment used by both streaming narrate and any non-streaming calls.
- No new config fields or model changes.
- The existing template structure (section ordering, dynamic includes after line 98) must be preserved to avoid breaking downstream includes.
- No backwards compatibility — old prompt behavior is discarded.

## Non-goals

- Not changing the narrate user prompt (`narrate_user.j2`).
- Not changing the seed prompt, extract prompt, or storyteller prompt.
- Not adding new Jinja2 includes or changing the rendering pipeline.

## Solution

Replace the length target, promote "open with player action" to a hard rule, replace the Style section with concrete constraints (one-simile max, no sensory templates, prefer direct dialogue), harden the anti-repetition self-check to imperative tone, move Pacing after Style with a directive override rule, collapse NPC naming, harden NPC death, and widen the blockquote scope in the Markdown section.

## Firm decisions

1. Word target: "~180 words, hard ceiling 250. If your draft exceeds 250 words, reduce it — every sentence must advance the beat; delete the rest."
2. "Open with the player's action" becomes a BINDING top-level section (Hard Rule #2).
3. Style: replace 9 aspirational bullets with 8 concrete constraints. "The air smells of" is banned. One simile max.
4. Anti-repetition self-check rewritten to "BEFORE OUTPUTTING: scan every sentence..." imperative.
5. Pacing moved after Style with override rule: "Outcome directive and pending GM beat are authoritative scene signals."
6. NPC naming collapsed from 6 lines to 2. Single-word names not permitted.
7. NPC death hardened: "NPCs die. No 'stumbles back' or 'retreats' in high-stakes beats."
8. "Build the 4 player choices" removed from latent thread section.
9. Markdown blockquote widened: "> blockquote for signage, broadcasts, and any text the player reads verbatim (books, terminals, letters)."

## Risks, Ambiguities, and Blockers

- **Word ceiling may be ignored:** The 250-word hard ceiling is advisory, not enforced by the engine. If over-production persists, a follow-up could add a `max_tokens` limit or stronger enforcement language.
- **Direct dialogue mandate could cause all-talk turns:** Mitigation: instruction says "when a character speaks" — action-first narration takes priority.
- **Smell ban too absolute:** Mitigation: instruction says "if a smell matters, say it in 3 words" — it bans gratuitous smell, not all smell.

## Status
`open`

## Implementation — Phase 2

### Context files to load

- `ccya/prompts/narrate_system.j2` — the full file (108 lines, read once)

### Detailed steps

All steps target `ccya/prompts/narrate_system.j2` unless otherwise noted.

#### Step 2.1 — Replace length target on line 1

**File:** `ccya/prompts/narrate_system.j2`

**What:** Change line 1 from "2-4 short paragraphs" to:
```
Narrate the next beat of a text adventure. Second person. 2-3 paragraphs, ~180 words. Hard ceiling: 250 words. If your draft exceeds 250 words, reduce it — every sentence must advance the beat; delete the rest.
```

Preserve the existing tense guidance clause: `If the genre tone section below specifies a tense, use it; otherwise use past tense.`

**Why:** Design decision — replace unenforceable vague target with concrete ceiling + enforcement instruction.

**Validation:** Visual inspection. Template renders without error.

#### Step 2.2 — Promote "Open with player action" to Hard Rule #2

**File:** `ccya/prompts/narrate_system.j2`

**What:** Remove the "Open with the player's action" sentence from its current position (end of the Player Input section, line 17). Insert a new top-level section between the Player Input section and the Inventory section:

```
## Open with the player's action (BINDING)

First sentence addresses what the player does this turn. No establishing shots, no "you scan the room," no throat-clearing. If location or focus changed, start at the arrival — never narrate the journey there.
```

**Why:** The single most effective fluff-cutting rule was buried as a sub-bullet. Promoting it to a standalone BINDING section gives it maximum visual weight.

**Validation:** Visual inspection. Template renders without error.

#### Step 2.3 — Replace Style section (lines 67–77)

**File:** `ccya/prompts/narrate_system.j2`

**What:** Replace the entire Style section with:

```
## Style
- Keep it tight — each turn is a scene beat, not a chapter. Every sentence must advance.
- Subvert the obvious. If the reader can predict the next sentence, rewrite it.
- Prefer direct dialogue over summarized speech. When a character speaks, write the quote.
  When the player reads a book, sign, or terminal, show the text verbatim in `> blockquote`.
- One simile per turn maximum. If it doesn't earn its place, cut it.
- Describe new characters briefly on first appearance.
- No sensory templates. "The air smells of" is banned. If a smell matters to the action, say it in 3 words. If it doesn't, cut it.
- Concrete phrases observed repeating 20+ times across recorded sessions — treat them as a signal the model is falling back on trained patterns: "The air smells of", "rhythmic", "sudden", "like a". If you catch yourself writing these, cut or replace.
- Spatial clarity when positioning matters (combat, stealth, formations). Say where things are relative to each other.
```

**Why:** Removes the aspirational "colorful imagery/metaphors/similes" instruction that directly caused the repetition problem. Replaces with concrete constraints: one simile max, banned phrases, no sensory templates, direct dialogue requirement. The "20+ times" observation is a behavioral signal — gives the model a specific pattern to avoid.

**Validation:** Visual inspection. Template renders without error.

#### Step 2.4 — Rewrite anti-repetition self-check to imperative

**File:** `ccya/prompts/narrate_system.j2`

**What:** Replace lines 28–29 of the "Never repeat prior narration" section:

```
Self-check before writing: does any sentence in your draft restate something the player was already told? If yes, delete it and replace with new information, a new reaction, or a forward beat.
```

with:

```
BEFORE OUTPUTTING: scan every sentence. If it restates information from a prior turn — an NPC's attitude, a room's atmosphere, a known condition — delete it. Replace with what is NEW this turn. If two sentences say the same thing, keep the tighter one.
```

**Why:** The current phrasing is a suggestion ("does any sentence...") that the model routinely ignores. The imperative "BEFORE OUTPUTTING: scan every sentence" is harder to bypass.

**Validation:** Visual inspection. Template renders without error.

#### Step 2.5 — Move Pacing section after Style, add directive override rule

**File:** `ccya/prompts/narrate_system.j2`

**What:** Move the Pacing section from its current position (lines 82–84) to immediately after the Style section. Replace its content with:

```
## Pacing
Each beat must advance the plot meaningfully. No holding patterns, no extended descriptions of static scenes.

Override rule: The Outcome directive and pending GM beat are authoritative scene signals. Do not override them because the prose feels like it should go a different direction.
```

Remove the existing Outcome instruction sentence (lines 84) that enumerates "hold/advance/transition" — the user prompt still renders the Outcome instruction; the system prompt only needs the override rule.

**Why:** Pacing is the core of the fluff problem but was visually under-weighted at line 82. Moving it after Style and adding the override rule prevents the narrator from vetoing scene signals.

**Validation:** Visual inspection. Template renders without error.

#### Step 2.6 — Collapse NPC naming section

**File:** `ccya/prompts/narrate_system.j2`

**What:** Replace the NPC NAMING paragraph (lines 63–65) with:

```
**NPC NAMING:** Every NPC must be referred to by a given name and family name (e.g. "Mira Sovak", "Dren Calloway"). Titles are optional. Descriptive labels like "scarred veteran" are aliases, not names — use the NPC's real name.
```

Remove lines 65 (which repeats the rule about using proper names in narration) — it's now redundant with the collapsed version.

**Why:** The same instruction was spread across 6 lines. Collapsed to 2 lines with the same meaning.

**Validation:** Visual inspection. Template renders without error.

#### Step 2.7 — Harden NPC death instruction

**File:** `ccya/prompts/narrate_system.j2`

**What:** Replace lines 60–61:

```
NPCs die. In combat and high-stakes situations, NPCs who lose a confrontation are dead, incapacitated, or removed from the scene. This is the default outcome — not a special condition. Do not default to "stumbling back" or "retreating." When in doubt, remove them. The progress extractor will record their fate.
```

with:

```
NPCs die. In any scene with stakes, losing a confrontation means death, incapacitation, or removal from the scene. If you find yourself writing "stumbles back" or "retreats" in a high-stakes beat, replace it with a decisive outcome. The narrator and storyteller adjust — preserving plot by keeping characters alive is forbidden.
```

**Why:** The model defaults to non-lethal outcomes ("stumbles back," "retreats") even in high-stakes scenes. The new language forbids the preservation-by-default behavior and explicitly tells the model the pipeline adjusts.

**Validation:** Visual inspection. Template renders without error.

#### Step 2.8 — Remove stale "4 player choices" from latent thread section

**File:** `ccya/prompts/narrate_system.j2`

**What:** In the Campaign arc context section (lines 87–90), replace the sentence `Build the 4 player choices to naturally lead toward discovery.` with nothing (delete it). The surrounding paragraph should read:

```
Your visible goal and thematic question are provided in the context below. Use them as narrative guidance — never state the thematic question directly or reveal hidden truths in prose. If an arc resolution is present, use it to inform how this new arc relates narratively to what was resolved before.

You have visibility into all threads — active, latent, and completed — plus their resolutions. Use this knowledge actively. Latent threads represent narrative threads the party has not yet discovered. Your job is to push the player gently towards them through narration, environmental detail, and NPC behaviour — without explicitly exposing the thread content. Show, don't tell. An NPC glancing nervously at a locked door, a flicker of torchlight from an unexplored tunnel, a curious sound carried on the wind. Introduce narrative elements that hint at the latent thread's existence and invite investigation. If a latent thread has gone unsurfaced for many turns, increase the pressure — make the hints less subtle.
```

**Why:** The narrator no longer writes player choices. The reference to "4 player choices" is stale and misleading.

**Validation:** Visual inspection. Template renders without error.

#### Step 2.9 — Widen blockquote scope in Markdown section

**File:** `ccya/prompts/narrate_system.j2`

**What:** Change line 96:

```
`> blockquote` only for signage or quoted broadcast text.
```

to:

```
`> blockquote` for signage, broadcasts, and any text the player reads verbatim (books, terminals, letters).
```

**Why:** The Style section now says "show the text verbatim in `> blockquote`" for books/terminals/letters. Without this widening, the Markdown rule contradicts the Style instruction.

**Validation:** Visual inspection. Template renders without error.

### Tests to write or update

No tests exist during refactor phase. Validation is by `make check` after all steps and visual inspection of rendered template output (run a turn and inspect `/v1/chat/completions` messages via `log_llm_io` or prompt log).
