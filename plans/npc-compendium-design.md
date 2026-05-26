# NPC Compendium & Seed Generation Design

## Purpose

This document codifies changes to seed generation ordering, compendium field management, UI display of NPC data, and scene NPC cap removal. It is the design authority for plans implementing these changes.

## Current State — What Exists

### Seed Generation Order

`generate_seed_system.j2:31-52` instructs the LLM to generate in this order:
1. PC (bio, stats, tagline)
2. World state (3 immutable facts)
3. Recent events (immediate pre-story context)
4. Opening scene / NPCs (instantiates situation_archetype)
5. Inventory (items tied to PC's top skills)
6. Campaign arc (visible_goal, threads, etc.) — LAST

Arc generation is last, meaning NPCs in step 4 have no knowledge of the campaign's visible_goal, active threads, or thematic_question when they are created. NPC bonds and connections are generated without arc context.

### Compendium Entry Fields

`CompendiumEntry` model (`ccya/pack.py:44-52`) has explicit fields: `name`, `title`, `bio`, `bond`, `presence`, `notes`. Extra fields (motivation, fear, leverage) are accepted via `extra="allow"` but seed prompt forbids them on line 11 and line 203.

### Seed Prompt NPC Instructions

`generate_seed_system.j2:11`: "Generate 4–5 named NPCs total: exactly 2 with presence='present' ... Do NOT include motivation, fear, or leverage fields."
- Line 187-191: Scene NPCs count controlled by `npc_count_override`, but line 11 hardcodes "exactly 2" which contradicts the override.
- Lines 193-198: Rigid pattern — one NPC carries personal stakes via bond, other carries external pressure. Formulaic.

### Compendium UI Display

`_state_left.html:153-186`: Compendium panel shows bio + bond + fear + leverage in tooltip for each entry. No spacing between fields. Motivation is not displayed. Scene card (lines 50-74) shows notes inline and bio in tooltip only.

### NPC Cap & Location Clearing

`state/npcs.py:54`: `NPC_SCENE_CAP = 8`. `_enforce_npc_present_cap()` evicts oldest NPCs by `last_seen.turn` when cap exceeded, setting them to "known" and clearing notes.
`clear_present_npcs_on_location_change()`: Sets ALL presence="present" NPCs to "known" on location change.

### Pipeline NPC Surfacing

Both narrate (`narrate_user.j2:13`) and storytell (`storytell_user.j2:1`) include `_npc_roster.j2`, which surfaces all nine fields: `name`, `title`, `bio`, `presence`, `notes`, `motivation`, `fear`, `leverage`, `bond`. Allegiance is surfaced separately via `pc_allegiance` in narrate_user.j2:23.

## Target State — What It Becomes

### Core Changes

**1. Seed generation order: Arc before NPCs.**
PC → World state → Recent events → Campaign arc (visible_goal, threads, thematic_question) → Compendium NPCs (informed by arc) → Inventory. This allows seed LLM to generate NPC bonds and connections that reference the campaign's actual goals and tensions rather than generic patterns.

**2. Seed prompt: Allow motivation/fear/leverage on key NPCs.**
Remove prohibition from lines 11, 203 of `generate_seed_system.j2`. Add motivation, fear, leverage to TypeScript-style seed output schema at line ~105 (compendium entry shape must include these fields or LLM won't emit them — it treats its own schema as contract). LLM may assign these fields to any compendium entries at seed time as metadata (lines 193-198 rigid bond pattern replaced separately). Fear and leverage are stored in state but not surfaced to UI. Motivation is surfaced in compendium tooltip alongside bio, bond, and last_seen.

**3. Compendium tooltip format: Bio → Motivation → Bond → Last Seen with blank-line separators.**
Each field separated by `\n\n` (blank line). Fields only shown if non-empty. Label convention: bio is unlabelled prose; motivation, bond use bold label prefix (`**Motivation:**`, `**Bond:**`) matching existing fear/leverage pattern in current code; last_seen uses plain text label ("Last seen:"). Format example:
```
[Bio as unlabelled prose]

**Motivation:** [value if present]

**Bond:** [value if present]

Last seen: [location_name]
```

**4. Remove NPC cap and location-clear behavior.**
Delete `NPC_SCENE_CAP`, `_enforce_npc_present_cap()`, and the call to it in `apply_npc_scene_management()`. Delete `clear_present_npcs_on_location_change()` and its invocation on location change in `delta_builder.py:245-246`. NPCs exit via LLM-driven presence changes only (presence="known" when narration indicates departure).

**5. Soften seed NPC count constraint.**
Line 11 of `generate_seed_system.j2` becomes flexible guidance rather than hard number. The `npc_count_override` parameter controls scene NPC count: value >0 means exactly that many NPCs in the opening scene; value = 0 (default) means seed uses its own judgment based on situation archetype and world state, typically defaulting to ~2 but allowing flexibility.

**6. Scene NPC ideal: 1-4 present, pressure to exit above that.**
No hard cap (removed in change #4), but seed prompt should guide toward an ideal of 1-4 NPCs per scene. When narration naturally exceeds ~4 present NPCs, the LLM should feel narrative pressure for less relevant ones to depart — ideally with a story reason (they have business elsewhere, they leave after their role is served, etc.). This is soft guidance, not enforcement: engine does NOT track or enforce NPC count at runtime; LLM handles exits through presence transitions.

**7. Seed identification of "key NPCs."**
There is no formal definition of which seed NPC is "key" — it's whichever has a personal connection to the PC or plays a major role in the story (or for the player). Some may all be key; maybe only one is. This judgment call guides the seed LLM on which compendium entries should receive motivation, fear, and leverage fields at seed time. The prompt should instruct: "Assign motivation/fear/leverage to whichever NPCs feel important — those with personal ties to the PC or central roles in the opening situation."

**8. Runtime extraction populates motivation/fear/leverage via `compendium_npc_update`.**
Seed is not the only source of these fields. At runtime, scene extraction (`extract_scene_system.j2`) instructs the extractor to include motivation, fear, and leverage on compendium entries whenever narration reveals new facts about an NPC (lines 37-41). This means NPCs get richer behavioral metadata over time through play — not just at seed but continuously as story events reveal character depths. Seed provides initial motivation/fear/leverage for key NPCs at campaign start; runtime extraction continuously enriches these fields as narration reveals character depths. Both are primary in their respective timeframes (merge, not overwrite).

**9. Fear and leverage are behavioral metadata, not just hidden from UI.**
Fear and leverage serve a specific mechanical purpose: they drive NPC behavior in narration, GM beats, and storytell decisions. They're not merely "don't show to players" — they're internal game mechanics that inform how NPCs act, react, and make decisions during prose generation. The seed prompt's original phrasing ("engine manages those") was misleading because there is no automated scoring or evolution engine; rather, these fields are *consumed* by the LLM pipelines (narrate/storytell/extract) as behavioral drivers while remaining invisible to players through UI. Motivation differs: it IS player-facing in the compendium tooltip because "what this character wants" is useful context for a player reading their dossier.

**10. Compendium tooltip shows bio + motivation + bond + last_seen; NOT notes.**
Notes field (scene-specific attitude, cleared on departure) appears inline only on scene card NPCs (`_state_left.html:63-64`). It does NOT appear in compendium tooltips — those show bio, then motivation (if present), then bond (if present), then last seen location. This separation reflects the semantic difference: notes are ephemeral scene context; compendium entries store durable character information.

### Decision Table

| Decision | What | Why |
|---|---|---|
| Arc before NPCs in seed gen | Move Campaign Arc generation step above Compendium NPCs in `generate_seed_system.j2:31-52` | NPC bonds, connections, and motivations should reference actual campaign goals/threads rather than generic patterns. Arc is the narrative spine; NPCs orbit it. |
| Allow motivation/fear/leverage at seed time | Remove prohibition from lines 11, 203 of `generate_seed_system.j2`; add explicit motivation, fear, leverage fields to CompendiumEntry model (see #2 below); update TypeScript-style seed output schema at line ~105 to include these fields in compendium entry shape (LLM treats its own schema as contract) | These are metadata that enrich state. Fear and leverage drive NPC behavior in narration but need not be UI-visible. Motivation is useful compendium context for players. |
| Fear/leverage hidden from UI | Do NOT render fear or leverage in `_state_left.html` compendium tooltip; motivation IS rendered | Fear and leverage are internal game mechanics (drive NPC decisions, GM beats). Players don't need to see them — they'd break mystery. Motivation is player-facing: "what this character wants." |
| Compendium tooltip format | Bio (unlabelled prose) → Motivation (**Motivation:** prefix) → Bond (**Bond:** prefix) → Last Seen (plain "Last seen:" label); all separated by `\n\n` blank lines; each field only shown if non-empty | Consistency with existing fear/leverage bold-label convention. Bio is unlabelled because it's already descriptive prose. Motivation uses **Motivation:** to match Bond/Fear/Leverage pattern for visual consistency in tooltip scanning. |
| Remove NPC cap (NPC_SCENE_CAP = 8) | Delete constant `NPC_SCENE_CAP`, function `_enforce_npc_present_cap()`, and its call in `apply_npc_scene_management()` via `state/npcs.py:192` | Hard caps create mechanical pressure that conflicts with narrative pacing. If a scene has 6 NPCs, the LLM should decide who stays; engine shouldn't silently evict based on turn number. |
| Remove location-clear behavior | Delete `clear_present_npcs_on_location_change()` and its call in `delta_builder.py:245-246` | Not all location changes mean NPCs leave with you. A shopkeeper doesn't follow you to the street; a guard might. Let LLM handle presence transitions via narration cues, not blanket resets. |
| Soften seed NPC count | Line 11 becomes flexible guidance; `npc_count_override` parameter controls exact number when >0 (value of 0 means seed uses its own judgment); default stays at 2 for simplicity but is overridable | Player's character creation input should determine scene NPC density. npc_count=0 → seed decides, npc_count=N → exactly N NPCs in scene. |
| Scene NPC ideal (1-4) + exit pressure | Add soft narrative guidance to seed prompt only: aim for 1-4 present NPCs; above that, encourage LLM-driven exits with story reasons | Hard caps conflict with narrative pacing (removed in #6). Soft guidance gives the LLM a target without mechanical enforcement. Exits should feel earned, not arbitrary. Engine does NOT track or enforce NPC count at runtime. |
| Seed "key NPC" identification | Add seed prompt guidance: assign motivation/fear/leverage to whichever NPCs have personal ties or major story roles — no formal definition needed | Allows flexible, context-aware assignment rather than rigid rules (e.g., "first 2 get these fields"). Some may all be key; maybe only one. |
| Runtime extraction populates via compendium_npc_update | Document that `extract_scene_system.j2:37-41` instructs extractor to include motivation/fear/leverage when narration reveals new NPC facts | Seed provides initial motivation/fear/leverage for key NPCs at campaign start; runtime extraction continuously enriches these fields as narration reveals character depths. Both are primary in their respective timeframes (merge, not overwrite). |
| Fear/leverage = behavioral metadata (not just hidden) | Explicitly document that fear and leverage drive NPC behavior in narrate/storytell/extraction pipelines; motivation IS player-facing via compendium tooltip | These are consumed by LLMs as narrative drivers, not merely suppressed from UI. Motivation is shown to players because "what this character wants" aids their understanding of the world. |
| Compendium tooltip excludes notes field | Notes appear inline only on scene card NPCs; NOT rendered in compendium tooltips (bio → motivation → bond → last_seen) | Notes are ephemeral scene context (attitude, current situation); compendium stores durable character information. Semantic separation matters for UI clarity. |

### What Is Removed

| Removed | From | Notes |
|---|---|---|
| `NPC_SCENE_CAP = 8` constant | `ccya/state/npcs.py:54` | No replacement — cap removed entirely |
| `_enforce_npc_present_cap()` function | `ccya/state/npcs.py:57-78` | No replacement — engine no longer evicts NPCs |
| Call to `_enforce_npc_present_cap(comp)` | `ccya/state/npcs.py:192` | Removed from `apply_npc_scene_management()` |
| `clear_present_npcs_on_location_change()` function | `ccya/state/npcs.py:121-127` | No replacement — location changes no longer clear NPCs |
| Call to `clear_present_npcs_on_location_change()` | `ccya/state/delta_builder.py:245-246` | Removed from `apply_delta()` on location change branch |
| "Do NOT include motivation, fear, or leverage" prohibition | `ccya/prompts/generate_seed_system.j2:11` | LLM may now assign these to seed NPCs |
| "Do NOT add relation, notes, motivation, fear, or leverage" prohibition | `ccya/prompts/generate_seed_system.j2:203` | Same — seed LLM can populate these fields |
| Rigid NPC bond pattern (personal stakes + external pressure) | `ccya/prompts/generate_seed_system.j2:193-198` | Replaced with flexible arc-informed guidance (#7 above): assign motivation/fear/leverage to whichever NPCs feel important, no formal definition needed. Also add soft scene NPC ideal (1-4 present, pressure to exit above that) per #6 above. |

### What Is Unchanged

- **CompendiumEntry model structure** — existing fields (`name`, `title`, `bio`, `bond`, `presence`, `notes`) remain. Three explicit optional string fields added: `motivation`, `fear`, `leverage` (see New Model Shapes above). `extra="allow"` stays for future-proofing against seed LLM output variance.
- **Scene extraction NPC management** — `compendium_npc_update` channel in `extract_scene_system.j2:27-43` unchanged. Scene pipeline remains sole gatekeeper for compendium mutations at runtime. At seed time, motivation/fear/leverage may be assigned to key NPCs (see #7 above); at runtime, extraction populates these fields when narration reveals new facts about an NPC (see #8 above).
- **NPC roster building** — `build_npc_roster()` in `ccya/engine/npc_roster.py:14-68` unchanged. Still filters by presence, sorts PRESENT→NEARBY→KNOWN. Continues to surface motivation/fear/leverage/bond/allegiance to LLM pipelines for generation guidance (see #9 above).
- **Narrator/storytell NPC context** — `_npc_roster.j2` continues to surface all fields to LLMs for generation guidance. No change to what the LLM sees.
- **Seed state schema** — `CompendiumEntry` in seed output retains Pydantic config; explicit field declarations added (motivation, fear, leverage) prevent strict-mode issues with undocumented extra fields from seed LLM or extraction.
- **Presence values** — "present", "known" remain the only presence states used by engine and UI. No new presence types added.
- **Touch compendium order** — `touch_compendium_order()` in `state/npcs.py:35-43` remains for LRU tracking of accessed NPCs (used by compact pipeline).

### Migration Notes

No state migration needed. Existing saved games with compendium entries lacking motivation/fear/leverage will continue to work — these fields are optional on all models. The seed prompt change only affects new seeds generated after deployment; existing static packs and dynamic seeds already in use retain their current NPC data.

The eval auto-checker `check_npc_scene_cap()` (`ccya/eval/universal_asserts.py:452-472`) will need to be removed or updated since the cap no longer exists. It currently asserts max 8 present NPCs and flags violations as red-severity failures. Without a cap, this checker should either be deleted entirely or changed to warn only when count exceeds some reasonable threshold (e.g., >10) without failing.

### New Model Shapes

`CompendiumEntry` in `ccya/pack.py:44-52` — add three explicit optional string fields (after existing `notes` field, before any extra-fields config):

```python
class CompendiumEntry(BaseModel):
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    bond: str | None = None
    presence: str | None = None       # "present" | "known" — seed or engine sets this
    notes: str | None = None          # scene-specific attitude, cleared on departure
    motivation: str | None = None     # NEW: what NPC fundamentally wants (UI-visible in compendium tooltip)
    fear: str | None = None           # NEW: what NPC is most afraid of (state-only, not UI-visible)
    leverage: str | None = None       # NEW: what NPC can offer/threaten/withhold (state-only, not UI-visible)

    model_config = ConfigDict(extra="allow")  # stays — handles any future extra fields from seed LLM or extraction
```

`extra="allow"` stays because seed LLM output may include unexpected field names; explicit declarations prevent Pydantic v2 strict-mode issues with undocumented fields.

### Prompt Token Impact

**`generate_seed_system.j2`:** ~15 tokens removed (prohibition lines on 11 and 203). ~70 tokens added (flexible arc-informed NPC guidance replacing rigid bond pattern + seed generation order change for step 6 → step 4 positioning + key NPC identification guidance #7 + scene NPC ideal count/exit pressure soft guidance #6). Net: +55 tokens.

**`_state_left.html`:** ~10 tokens added (blank-line separators between tooltip fields, motivation rendering logic, notes field exclusion from compendium tooltips per #10 above). No removals — existing bio/bond/fear/leverage template code replaced with new format.

### Context for Implementing LLMs

Before starting any plan:
- `ccya/pack.py:44-52` — CompendiumEntry model definition; add explicit motivation, fear, leverage fields here (see #9 above for behavioral metadata distinction)
- `ccya/prompts/generate_seed_system.j2:31-52` — seed generation order section (move arc above NPCs); lines 11, 186-203 — NPC instructions to rewrite/soften; add key NPC identification guidance (#7), scene NPC ideal count + exit pressure (#6)
- `ccya/prompts/generate_seed_system.j2:~105` — TypeScript-style seed output schema (compendium entry shape); must add motivation, fear, leverage fields or LLM won't emit them (it treats its own schema as contract)
- `ccya/prompts/extract_scene_system.j2:27-43` — compendium_npc_update schema (runtime extraction populates motivation/fear/leverage when narration reveals new facts, see #8 above); no change needed but implementer should understand this is the primary runtime population mechanism
- `ccya/state/npcs.py:54-78, 121-127, 192` — constants and functions to delete; apply_npc_scene_management call site to remove cap enforcement
- `ccya/state/delta_builder.py:239-246` — location change branch where clear_present_npcs_on_location_change() is called (remove the call)
- `ccya/templates/_state_left.html:153-186` — compendium tooltip section to reformat with blank-line separators, motivation field, exclude notes field (see #10 above); lines 50-74 for scene card notes inline + bio tooltip confirmation
- `ccya/eval/universal_asserts.py:452-472` — check_npc_scene_cap() auto-checker to remove or repurpose
