---
title: "World step NPC binding in beat effect tags — prompt-eval test"
status: new
urgency: 3
size: medium
created: 2026-07-19
ticket_id: E-17
labels: []
design:
plan:
pr:
  url:
  branch:
---

## Description

Eval of the NPC binding changes to world_system.j2 (commit `93421e51`). Changes:
- Effect tags now require NPC names: `[highlight: Paul Bonilla's fear]` not `[highlight: fear]`
- Blends combine two NPC fields only; threads stay separate
- Tie always requires two NPCs
- Diversity window raised from 4→8 entries, threshold 2+→4+ (50%)

Tested via `prompt-eval call` on space-western T2 and allied-ww2 T2.

## Sources Examined

- `evals/scenarios/world-npcs-test.yaml` — space-western T2 (1 present NPC: Travis Simmons)
- `evals/scenarios/ww2-world-npc-binding.yaml` — allied-ww2 T2 (3 present NPCs: Paul Bonilla, Thomas Miller, Wounded Soldiers)
- `evals/runs/2026-07-17_0.32.1_2e3d0188/2258_allied-ww2_25t/events.jsonl` — stored beats for comparison
- `ccya/prompts/world_system.j2` — updated prompt
- `ccya/prompts/narrate_system.j2` — updated narrate prompt

## Findings

### Improvement: Effect tags are now self-contained

**Before:** `[highlight: leverage]` — narrator must guess which NPC's leverage
**After:** `[highlight: Travis Simmons's leverage]` — narrator knows exactly which field

Examples from prompt-eval call:
- Space-western: `[highlight: Travis Simmons's leverage] [thread: faction_patrols]` ✓
- Allied-ww2: `[blend: Thomas Miller's tie vs German Officer's leverage] [thread: intelligence_leak]` ✓
- Allied-ww2: `[highlight: German Officer's leverage] [tie: Thomas Miller vs German Officer]` ✓

Cross-NPC blending works correctly. Threads stay separate from blends (after blend rule was added).

### Regression: LLM invents field names

The LLM generated `[blend: Paul Bonilla's frustration vs Thomas Miller's tie]` — "frustration" is NOT a valid psychological field. Valid fields: motivation, fear, leverage, tie, bio.

This violates the prompt rule: "MUST use only the NPC fields explicitly listed in the roster (motivation, fear, leverage, tie, bio)."

The LLM may be pulling "frustration" from Paul Bonilla's bio text ("grim frustration") and treating it as a field name.

### Concern: Stored events have old-format recent_beats

The `recent_beats` in stored events.jsonl still have the old format:
- `T1: pressure — [highlight: fear] [thread: intelligence_leak]`

When `prompt-eval dump` re-renders, it shows these old-format beats in the recent_beats section. This creates a mixed-format prompt (new instructions + old data) which may confuse the LLM.

This is a data issue — only affects eval replay, not live turns. New turns will have new-format recent_beats.

### Concern: Longer effect strings = more tokens

Old: `[highlight: leverage]` (18 chars)
New: `[highlight: Travis Simmons's leverage]` (38 chars)

~2x increase in effect string length. For 3 beats per turn, this adds ~60 chars per world step. Over 25 turns, that's ~1500 extra chars in recent_beats tracking. Not a major concern but worth noting.

## Comparison: Old vs New

| Aspect | Old Format | New Format |
|--------|-----------|------------|
| NPC binding | `npcs` field only | NPC name in effect tag |
| Narrator clarity | Must guess field source | Self-contained |
| Cross-NPC blends | `[blend: motivation vs fear]` | `[blend: A's motivation vs B's fear]` |
| Field validation | N/A | LLM sometimes invents fields |
| Token cost | Lower | ~2x effect string length |
| Diversity tracking | NPC in `npcs` field | NPC in effect string |

## Recommendations

1. **DONE (commit `4eddab60`):** Strengthened field validation with explicit valid field list and anti-example. Post-fix tests show all valid fields.
2. **Verify with a live run** — prompt-eval uses stored state which has old-format recent_beats. Run a fresh turn to verify the LLM handles new-format recent_beats correctly.
3. **Monitor token usage** — Track world step token increase after deploying to a full eval run.