# NPC Management — Bio/Notes Tightening (5a, 5c)

## Status
`completed`

## Phases

1 phase: tighten scene extractor prompt for bio vs notes separation and note length constraints. Only modifies `ccya/prompts/extract_scene_system.j2`. No model changes, no code changes.

## Issue

The scene extractor conflates bio (persistent identity) with notes (transient situational relevance). Notes are too long — they take most of the scenic structure's output budget and read like narration transcripts rather than quick flavor cues for the player. Bio lacks structural guidance: it should follow a consistent two-sentence pattern (appearance/demeanor + durable personality/facts), but currently gets whatever the LLM generates.

## Solution

Update `extract_scene_system.j2` to add concrete examples showing correct bio vs notes extraction, tighten bio structure into explicit two-sentence format, and constrain notes to one short sentence with relevance guidance ("why is this NPC relevant right now?"). No model changes needed — the schema already separates these fields correctly. Only prompt tightening required.

## Firm decisions

1. **Only modify `extract_scene_system.j2`.** The extraction pipeline code (`extraction.py`, `state/npcs.py`) and models are correct as-is.
2. **Bio = two sentences.** First: appearance + demeanor (how they're presented physically). Second: durable personality traits or tangible facts about who they are as a person — relevant, interesting to the story.
3. **Notes = one short sentence max.** Full sentences okay but strictly limited to one. Must convey situational relevance ("why is this NPC doing what they're doing right now?"). Still flavor text, not plot-critical information.
4. **Concrete examples for both fields.** Show correct vs incorrect extraction side by side so the LLM has a clear pattern to follow.
5. **Skip 5b (stale flag).** Mark as won't do — no stale mechanism needed.
6. **Skip 5d (generic names).** Mark as deferred/won't do — blacklist approach is wrong, and strengthening existing name pool guidance hasn't proven effective enough to justify changes.

## Non-goals

- No model schema changes (`CompendiumNpcUpdate`, `CompendiumEntry`).
- No code changes in extraction.py, state/npcs.py, or any engine module.
- No changes to narrator naming prompt (5d is deferred).
- No changes to seed generation prompts for NPC names/bios.
- No stale flag mechanism for notes (5b is won't do).

## Risks, Ambiguities, and Blockers

**Ambiguity:** "One short sentence" is subjective — the LLM may still produce multi-clause sentences that are technically one sentence but very long. Mitigation: add a concrete example showing what counts as too-long vs acceptable for notes.

**Risk:** Adding examples increases prompt token count slightly (~50-80 tokens). This is negligible compared to the overall narrator/extraction context budget and should improve extraction quality enough to offset it via shorter notes (fewer tokens per turn in output).

---

## Implementation — Phase 1: Tighten scene extractor bio/notes guidance

### Context files to load
- `ccya/prompts/extract_scene_system.j2` — the only file being modified. Read lines 27-58 for current field definitions and NPC rules.

### Detailed steps

#### Step 1.1 — Restructure bio definition with explicit two-sentence format

**File:** `ccya/prompts/extract_scene_system.j2`, line ~34 (bio field definition in schema example) + lines ~47-50 (how to use compendium_npc_update section)

**What:** Update the bio field description from "1-2 sentence identity" to explicitly require a two-sentence structure:
- Sentence 1: appearance and demeanor — how they are physically presented, what they look like, their bearing/posture/expression in this scene. This is visual, immediate, situational but durable (they don't change it next turn).
- Sentence 2: personality traits or tangible facts about who they are as a person — background details, habits, reputation, past events that define them. Must be relevant and interesting to the story, not generic filler like "is a merchant" or "works for someone."

Update both the schema field description (line ~34) AND add concrete examples in the NPC rules section showing correct vs incorrect bio extraction.

**Why:** The current "1-2 sentence identity" is too vague — LLMs produce inconsistent bios, sometimes just describing appearance with no personality, or vice versa. Explicit two-sentence structure ensures both dimensions are covered every time.

**Validation:** Read the file and confirm:
- Schema field description updated to specify two sentences with their respective content requirements
- Examples section added showing 2 correct bio extractions + 1 incorrect extraction (too generic / missing one dimension)

#### Step 1.2 — Constrain notes length and add relevance guidance

**File:** `ccya/prompts/extract_scene_system.j2`, line ~41 (notes field definition in schema example) + lines ~48-49 (how to use compendium_npc_update section)

**What:** Update the notes field description from "current attitude or situation toward the player" to:
"one short sentence about what this NPC is doing right now that matters — their current stance, action, or motivation as it relates to the last round of narration. Still flavor text; not plot-critical information."

Add concrete examples showing correct vs incorrect notes extraction in the same section where bio examples appear (Step 1.1). Examples should show:
- Correct: one short sentence with situational relevance ("leans against the wall, watching your hands for a weapon")
- Too long: multi-clause transcription of narration events
- Generic: vague attitude without scene context ("is suspicious of you")

**Why:** Notes currently take "most of the scenic structure's time" — they're verbose and read like narration transcripts. The constraint to one short sentence forces concision while relevance guidance ensures notes still serve their purpose (giving the player a sense of what's going on around them).

**Validation:** Read the file and confirm:
- Schema field description updated with length constraint + relevance guidance
- Examples section includes 2 correct notes extractions + 1 too-long extraction + 1 generic extraction

### Tests to write or update
None — tests are temporarily removed during refactor.

### REPOMAP updates required
Update `docs/repomap.md` line ~34 (scene extractor prompt reference) if the field descriptions change significantly enough that a summary is warranted. Otherwise, no repomap changes needed since the schema contract (`CompendiumNpcUpdate`) is unchanged and the module behavior is identical — only prompt wording changed.
