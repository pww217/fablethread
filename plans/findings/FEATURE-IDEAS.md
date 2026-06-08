# Feature Ideas & Improvements

> Cross-cutting feature ideas, improvements, design questions, and UI polish items not specific to any single game run. Organized by subsystem/concern.
>
> **Net New Features** — things that don't exist yet or need large changes/overhauls  
> **Improvements** — existing systems needing fixes or refinements (bugs)  
> **Design Questions** — tentative ideas, undecided directions, needs more thought

---

## Compendium

### F-N01. Alias consolidation [Net New]

Compendium sometimes introduces characters with aliases/descriptions ("Scarred Soldier") without mapping them to their proper name when revealed later. Result: two entries for the same person — one under alias, one under real name. Need a mechanism to detect and consolidate duplicate identities across turns.

### F-N02. Stale character cleanup [Net New]

Compendium accumulates characters that are no longer relevant (unnamed guards killed/passed through) because there's no removal mechanism. Two sub-problems:
- **Too many chars introduced**: Not a hard-cap problem but related to lack of cleanup — see F-N03 below.
- **No TTL-based removal**: Characters who aren't named key NPCs should be removed after they're no longer relevant.

---

## Pipeline Efficiency

### F-I08. Extractors suppress all-null fields [Improvement — Needs Verification]

Instruct extractors not to emit schema fields that are entirely null (no-op changes). Don't just emit a schema that changes nothing — saves output tokens and reduces noise in events.jsonl. Schema changes may have largely addressed this already; verify against recent runs before treating as active issue.

---

## Scene Mechanics

### F-N06. Interactive inventory items in scenes [Net New]

Inventory items should be interactive within scene mechanics, not just mentioned in narration. The state extractor needs to handle item interactions (pick up, use, examine) as first-class actions that affect the scene — similar to how NPCs can act independently but for objects rather than characters. This would make inventory feel more integrated into gameplay rather than being a passive list tracked behind the scenes.

---

## Narrative Setup

### F-I01. Bond naming fix [Improvement]

Close bonds (family, spouse) are referred to generically as "kin" or "family" instead of by proper name/role ("wife", "daughter"). This happens mid-game too — e.g., player travels across town and doesn't run into family until T3+, but when they do appear the narrator still uses generic terms. The bond system needs explicit instruction to use named relationships, not abstract kinship labels.

### F-I02. Turn 1 seed integration [Net New]

The initial seed JSON sets up world state (locations, factions, relationships) but turn 1 narration doesn't actively USE it — it lists things rather than weaving them into narrative choices and arc setup. The opening should be driven by seed data where relevant to existing threads/arcs.

### F-I03. Hints disable seed JSON [Improvement]

When player provides hints through character creation flow, the seed JSON should be entirely disabled (toggled off). Both mechanisms introduce randomness/variability; using both together confuses the narrator about what world state is real vs overridden. Simple config toggle: if `hints` field has any populated values → disable all seed-based world generation.

### F-I04. Narrator relevance for scene items [Improvement]

The opening narration (which receives seed data with scene items) mentions everything regardless of whether it's relevant to the current scene or arc. The narrator should only mention interactable/nearby items when they're actually relevant to what's happening, not as a laundry list from seed state.

---

## NPC Mechanics

### F-N03. NPC death/removal lifecycle [Net New]

NPCs who are dead, incapacitated, or no longer relevant need structured removal:
- **Marking**: Narrator/ruling agent marks character as `dead`, `incapacitated`, or `gone_from_scene`.
- **UI retention**: Character stays visible in UI for 2–3 turns after being removed from scene. Append a "last note" to the compendium entry explaining what happened (e.g., "Died fighting at [location]"). This gives player context and clarity.
- **Backend TTL**: On the backend, character persists for ~10 turns so engine can still understand callbacks/references to recently deceased characters. By turn 10, callback probability is slim.
- **Key NPC exception**: Named/key NPCs marked with a `key_npc` flag are exempt from automatic removal — they stay until explicitly removed by narrative events.

### F-N04. Party designation [Net New]

NPCs who should follow the player (family allies, squad mates) need explicit party membership tracking:
- **Assignment**: Both seed-configured at start AND dynamically assigned by narrator when characters join up mid-game ("both" approach).
- **Scene retention**: Narrator prompt explicitly keeps party members together in scene descriptions — they shouldn't be left behind or separated without a strong narrative reason.
- **Enhanced treatment**: Party members get the same bond/narrative depth as key NPCs (motivations, fears, named relationships) even if introduced mid-game. They're not "random faceless guards."

---

## Storytelling Pipeline

### F-N05. Proactive NPC agency [Net New — Tentative]

Current turn flow is player-centric: "I do a thing → world/NPCs respond." This makes NPCs reactive and the world feel static around only the protagonist. Want to add opportunities for NPCs to drive scenes independently:
- **Storytell→Ruling→Narrate pass-through**: Storyteller identifies an NPC with reason to act this turn, passes that intent to ruling extractor (which determines likely action type), then narrator improvises from there. Turn starts with "This NPC does X" instead of "Player does Y → world responds."
- **Scope**: Could apply to named NPCs, party members, or even environmental forces. Not every turn needs this — just enough that the world feels alive beyond player actions.

### F-I05. GM beats replacement [Design Question]

Current GM beat system provides pacing direction but reads as "player-centric complications" rather than genuine world/NPC agency. Skeptical it's useful in current form. May need to adapt or replace with a more dynamic system where storyteller can direct NPC actions and environmental events independently of player input (ties into F-N05).

---

## UI Improvements

### F-I06. Turn number display [Improvement]

Add turn number `()` after thread updates in the UI. Also fix this in narration UI. Currently missing context about where you are in the game flow.

### F-I07. Debug/developer panel toggle [Net New]

Two-part improvement:
- **Developer mode**: When enabled, show debug information directly in UI — turn numbers, state snapshots, extraction outputs (things currently only visible via Turn Viewer or `ev` pipeline). Useful for development and troubleshooting.
- **Player mode** (default): Clean, polished view with minimal verbosity. Show what's immediately relevant to the current scene without exposing engine internals.

---

## Design Questions

### DQ01. Full narration passing between stages [Tentative]

Should narrate→storytell pipeline pass last turn's full prose narration as context? Previous iterations had this (current turn + previous-before-that) but it was abandoned for compacted bullet points. Unclear if re-implementing would help or just add noise. Tentative — needs testing before committing.

### DQ02. GM beats vs proactive NPC actions [Undecided]

See F-I05 and F-N05 above. Two related ideas:
- **GM beats on threads**: Structured foreshadowing via active thread state (unclear if useful)
- **Proactive NPC agency via storytell→ruling pass-through**: NPCs drive scenes independently
  
Should these be unified (scene direction comes from active threads) or separate systems? Or should GM beats be replaced entirely by the proactive agency system? Needs more design work.

---

## Previously Cross-Referenced Features (Moved Here)

> Items F1–F8 moved from BUGS-OBSERVATIONS.md "Feature Ideas & Improvements" section. These are low-priority meta-items (thread activation cap maps to O3/O6 in BUGS-OBSERVATIONS, sanitizer naming convention cleanup, impossible-action pathway design question, arc_resolve state management maps to F-I01 narrative continuity, storyteller actions documentation need, thread resolution milestone feedback) — retained as cross-references but not actionable feature items.

---

## Summary by Category

| Category | Net New Features | Improvements/Bugs | Design Questions |
|----------|-----------------|-------------------|------------------|
| Compendium | F-N01, F-N02 | — | — |
| Scene Mechanics | F-N06 | — | — |
| Narrative Setup | F-I02 | F-I01, F-I03, F-I04 | DQ01 (tentative) |
| NPC Mechanics | F-N03, F-N04 | — | — |
| Storytelling Pipeline | F-N05 | — | DQ02 |
| UI Improvements | F-I07 | F-I06 | — |
| Pipeline Efficiency | — | F-I08 (needs verification) | — |
