# Feature Ideas & Improvements

> Cross-cutting feature ideas, improvements, design questions, and UI polish items not specific to any single game run. Organized by subsystem/concern.
>
> **Net New Features** — things that don't exist yet or need large changes/overhauls  
> **Improvements** — existing systems needing fixes or refinements (bugs)  
> **Design Questions** — tentative ideas, undecided directions, needs more thought

---

## Game Setup

### F-N08. Seed JSON vs hints conflict [Net New] — **Priority #1** — **FIXED**

**Status:** FIXED — `01-seed-fixes.md` plan: when hints are provided, LLM seed generation is skipped entirely and the static pack's `seed_state.yaml` is used instead.

When both seed JSON and player hints are provided at game creation, they can conflict — both inject into the same initial state, causing compendium duplication, missing NPCs, bond issues, and location never changing. The seed JSON should be disabled when hints are provided, or there should be merge/override semantics defined. Currently both may be active simultaneously causing conflicts.

### F-N09. Disable seed JSON when hints given [Net New] — **Priority #1** — **FIXED**

**Status:** FIXED — `01-seed-fixes.md` plan: hints presence triggers static pack seed fallback, skipping LLM seed generation entirely.

Closely related to F-N08. If hints are provided at game creation, seed JSON should be skipped entirely rather than running in parallel. Running both creates competing state injections.

---

## Compendium

### F-N01. Alias consolidation [Net New] — **Priority #2** — **FIXED**

**Status:** FIXED — `02-npc-compendium-hardening.md` plan: alias-first naming instruction in extraction prompt (aliases for descriptive labels, name for proper names, keep historical aliases on promotion). Dedup handled by existing `_dedup_compendium_update()`; no Python dedup logic needed.

Compendium sometimes introduces characters with aliases/descriptions ("Scarred Soldier") without mapping them to their proper name when revealed later. Result: two entries for the same person — one under alias, one under real name. Need a mechanism to detect and consolidate duplicate identities across turns.

### F-N02. Stale character cleanup [Net New] — **Priority #2** — **PARTIALLY FIXED**

**Status:** PARTIALLY FIXED — F-N01 (alias consolidation) is fixed by `02-npc-compendium-hardening.md`. TTL-based removal of unnamed non-key NPCs is still open — see F-N03 for death/removal lifecycle.

Compendium accumulates characters that are no longer relevant (unnamed guards killed/passed through) because there's no removal mechanism. Two sub-problems:
- **Too many chars introduced**: Not a hard-cap problem but related to lack of cleanup — see F-N03 below.
- **No TTL-based removal**: Characters who aren't named key NPCs should be removed after they're no longer relevant.

---

## Pipeline Efficiency

### F-I08. Extractors suppress all-null fields [Improvement — Needs Verification]

Instruct extractors not to emit schema fields that are entirely null (no-op changes). Don't just emit a schema that changes nothing — saves output tokens and reduces noise in events.jsonl. Schema changes may have largely addressed this already; verify against recent runs before treating as active issue.

### F-I10. Ruling agent condition system [Net New]

The existing condition system (B11, CONDITION_MODS) is being replaced by a ruling agent-driven approach. New design: conditions should live in the ruling extractor, which determines difficulty and whether an action is impossible based on current state. TTLs and gameplay effects handled by ruling agent rather than a separate condition subsystem. This supersedes the old CONDITION_MODS approach entirely.

---

## Thread & Arc Management

### DQ03. Threads vs arcs decoupling — cognitive load [Design Question] — **Priority #9**

Threads are overloaded as both a fact sheet (tracking world state/events) and an objective list (player goals). This creates high cognitive load for the player: they see threads with sub-objectives, arc visible_goals, and sometimes overlapping content. Possible division:
- **Arcs/threads should be objectives only** — guidance to storyteller that arcs define what the player is trying to accomplish.
- **Thread updates should be factual journal entries** — not goals but records of events (e.g., "Found wounded ally at [location]", "Discovered enemy patrol route").

May already be sufficiently differentiated via `visible_goal` vs thread progress, but worth testing whether this explicit distinction reduces confusion and cognitive load.

---

## Scene Mechanics

### F-N04. Grounded location descriptions + nearby POIs [Net New] — **PARTIALLY FIXED** — **Priority #8**

**PARTIALLY FIXED** — `grounded-state-extraction` plan (commits `f93b6740` + `02c6a91a`) rewrote `location_description` to be a complete rewrite each turn (not just new details), with explicit guidance for tangible details (materials, lighting, sounds, smells) and spatial relationships. Location descriptions are now grounded and spatial. **NOT FIXED:** Nearby/POI system deferred to separate feature per the plan constraints.

### F-N06. Interactive inventory items in scenes [Net New] — **PARTIALLY FIXED** — **Priority #5**

**PARTIALLY FIXED** — `grounded-state-extraction` plan (commits `f93b6740` + `02c6a91a`) tightened inventory notes to end with spatial position (e.g., `"quest item, in locked safe"`, `"worn, in right holster"`). Inventory is now tracked with spatial context. **NOT FIXED:** First-class item interaction mechanics (pick up, use, examine as scene actions) deferred — inventory remains a passive list tracked behind the scenes.

---

## Narrative Setup

### F-I01. Bond naming fix [Improvement] — **Priority #3**

Close bonds (family, spouse) are referred to generically as "kin" or "family" instead of by proper name/role ("wife", "daughter"). This happens mid-game too — e.g., player travels across town and doesn't run into family until T3+, but when they do appear the narrator still uses generic terms. The bond system needs explicit instruction to use named relationships, not abstract kinship labels.

### F-I02. Turn 1 seed integration [Net New] — **Priority #6** — **FIXED**

**Status:** FIXED — `01-seed-fixes.md` plan phase 3: updated `generate_seed_system.j2` opening narrative instructions to weave world state facts, NPC relationships, and compendium NPCs naturally into the narration rather than listing them.

The initial seed JSON sets up world state (locations, factions, relationships) but turn 1 narration doesn't actively USE it — it lists things rather than weaving them into narrative choices and arc setup. The opening should be driven by seed data where relevant to existing threads/arcs.

### F-I09. Bonds generate arc objectives at start [Net New] — **Priority #3**

Close bonds (family, spouse) should not just improve narration labels but actually seed concrete arc objectives at game start. Example: "find my lost brother" instead of generic "secure family safety." The bond data needs to be used by the storyteller/sanitizer to create specific, named-person arcs that give the player clear narrative direction from turn 1. This is about world-building depth in bonds — using them as a source for actionable story hooks rather than just improving how characters are referred to.

---

## NPC Mechanics

### F-N03. NPC death/removal lifecycle [Net New] — **Priority #4**

NPCs who are dead, incapacitated, or no longer relevant need structured removal:
- **Marking**: Narrator/ruling agent marks character as `dead`, `incapacitated`, or `gone_from_scene`.
- **UI retention**: Character stays visible in UI for 2–3 turns after being removed from scene. Append a "last note" to the compendium entry explaining what happened (e.g., "Died fighting at [location]"). This gives player context and clarity.
- **Backend TTL**: On the backend, character persists for ~10 turns so engine can still understand callbacks/references to recently deceased characters. By turn 10, callback probability is slim.
- **Key NPC exception**: Named/key NPCs marked with a `key_npc` flag are exempt from automatic removal — they stay until explicitly removed by narrative events.

### F-N07. Left-behind tracking on location change [Net New] — **PARTIALLY FIXED** — **Priority #7**

**PARTIALLY FIXED** — `grounded-state-extraction` plan (commits `f93b6740` + `02c6a91a`) added `position` field to `CompendiumNpcUpdate` for explicit NPC spatial positioning in scenes. NPCs now track where they are in the scene. **NOT FIXED:** Explicit "left behind" state tracking (last known location when PC changes scenes) deferred — NPC departure/known status handles some of this via F-N03 (NPC death/removal lifecycle), but dedicated left-behind tracking is not implemented.

---

## Storytelling Pipeline

### Bug 15. Autoplay momentum spiral [Net New — Verified] — **Priority #7**

Autoplay loop has no guard against consecutive impossible actions. Each turn drains momentum by 1, and once at floor, there's no escape mechanism. Verified across two saves (outer-rim, cordyceps-06-09). On cordyceps-06-09, cascade ran for 12 consecutive turns (20-31), dropping momentum from 3 to -3 and then stuck at floor for 7+ turns with beat_locked=True, consecutive pressure=8, and no escape mechanism.

**Fix:** Add detection in `play.py` autoplay mode: if 2+ consecutive impossible-action turns are generated, inject a proactive input suggestion or pause for intervention. Consider a "momentum floor escape hatch" for beat_locked: after 3+ turns at floor with beat_locked, force a breathing_room regardless of triggered_by_momentum.

**See also:** [Bug 15](./EVAL-FINDINGS-2026-06-09.md#bug-15-autoplay-momentum-spiral-on-continue-the-story-medium) | [MB-3](./MOMENTUM-BEAT-FINDINGS.md#finding-mb-3-floor-relief-beats-deepen-de-escalation-during-momentum-crisis)

---

### F-N05. Proactive NPC agency [Net New — Tentative] — **Priority #12**

Current turn flow is player-centric: "I do a thing → world/NPCs respond." This makes NPCs reactive and the world feel static around only the protagonist. Want to add opportunities for NPCs to drive scenes independently:
- **Storytell→Ruling→Narrate pass-through**: Storyteller identifies an NPC with reason to act this turn, passes that intent to ruling extractor (which determines likely action type), then narrator improvises from there. Turn starts with "This NPC does X" instead of "Player does Y → world responds."
- **Scope**: Could apply to named NPCs, party members, or even environmental forces. Not every turn needs this — just enough that the world feels alive beyond player actions.

### F-I05. GM beats replacement [Design Question]

Current GM beat system provides pacing direction but reads as "player-centric complications" rather than genuine world/NPC agency. Skeptical it's useful in current form. May need to adapt or replace with a more dynamic system where storyteller can direct NPC actions and environmental events independently of player input (ties into F-N05).

---

## UI Improvements

### F-I06. Turn number display [Improvement] — **Priority #10**

Add turn number `()` after thread updates in the UI. Also fix this in narration UI. Currently missing context about where you are in the game flow.

### F-I07. Debug/developer panel toggle [Net New] — **Priority #10**

Two-part improvement:
- **Developer mode**: When enabled, show debug information directly in UI — turn numbers, state snapshots, extraction outputs (things currently only visible via Turn Viewer or `ev` pipeline). Useful for development and troubleshooting.
- **Player mode** (default): Clean, polished view with minimal verbosity. Show what's immediately relevant to the current scene without exposing engine internals.

### F-I13. Entity highlighting in narration [Improvement] — **FIXED**

**Status:** FIXED — replaced LLM-driven `**bold**` for NPC names and inventory items with client-side `_highlightEntities()` JS function. After markdown rendering, the function walks text nodes and wraps known entity names in colored `<span>` tags. CSS classes: `.entity-npc` (#e06c75), `.entity-item` (#61afef), `.entity-pc` (#98c379), `.entity-location` (#d19a66). Plan at `plans/completed/11-ui/entity-highlighting.md`.

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

## Low Priority / Nice-to-Have

### F-I11. Cached universal system prompt [Maybe] — **Priority #13**

Investigate whether any stage-agnostic base system prompt could be cached. Unlikely to be feasible given how much system prompts content varies by pipeline stage, but worth a look if it saves tokens without degrading quality.

### F-I12. PC point total: 11 not 10 [Improvement] — **Priority #14** — **FIXED**

**Status:** FIXED — UI budget display, validation, and archetype presets updated from 10 to 11. Backend already allowed 8--12 range, no change needed.

---

## Previously Cross-Referenced Features (Moved Here)

> Items F1–F8 moved from BUGS-OBSERVATIONS.md "Feature Ideas & Improvements" section. These are low-priority meta-items (thread activation cap maps to O3/O6 in BUGS-OBSERVATIONS, sanitizer naming convention cleanup, impossible-action pathway design question, arc_resolve state management maps to F-I01 narrative continuity, storyteller actions documentation need, thread resolution milestone feedback) — retained as cross-references but not actionable feature items.

---

## Summary by Category

| Category | Net New Features | Improvements/Bugs | Design Questions |
|----------|-----------------|-------------------|------------------|
| Game Setup | F-N08, F-N09 | — | — |
| Compendium | F-N01, F-N02 | — | — |
| Scene Mechanics | F-N04, F-N06 (partial) | — | — |
| Thread & Arc Management | — | — | DQ03 (cognitive load) |
| Narrative Setup | F-I02, F-I09 | F-I01, F-I03, F-I04 | DQ01 (tentative) |
| NPC Mechanics | F-N03, F-N07 (partial) | — | — |
| Storytelling Pipeline | F-N05, Bug 15 | — | DQ02 |
| UI Improvements | F-I07 | F-I06, F-I13 | — |
| Pipeline Efficiency | — | F-I08, F-I10 | — |
| Low Priority | — | F-I11, F-I12 | — |
