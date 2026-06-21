# Location-Change NPC Auto-Demotion Design

## Purpose

Designs the location-change NPC auto-demotion mechanic: when the player changes location, `present` NPCs are auto-demoted to `nearby` unless they are party members (exempt). Fixes the 1-turn gap where the storyteller has no named NPCs to work with after location changes.

Reference: "This document is the design authority for plans implementing location-change NPC auto-demotion with party exemption."

## Problem Statement

**Pipeline roles (scene extractor vs. storyteller):**
- The **scene extractor** (stream 1) reads narration and determines NPC presence (`present`/`nearby`/`known`/`departed`). It manages the NPC compendium.
- The **storyteller** (stream 3) receives the post-demotion state and generates beats. It does not reason about NPC presence management.
- The **delta builder** applies auto-demotion between streams 2 and 3.

**The bug:** When the player changes location, `delta_builder.py:228-234` auto-demotes all `present` NPCs to `nearby` — including companions who logically follow the player. The scene extractor can re-promote them next turn if narration mentions them, but "never repeat prior narration" means location-change turns often don't re-mention all NPCs. This creates a 1-turn gap where:

1. The storyteller receives a roster with no named `present` NPCs
2. Unable to generate NPC-driven beats, the storyteller defaults to ambient "crowd" beats
3. Narrative continuity with established characters breaks

**Confirmed in eval:** On T3→T4 (Millerport Outskirts → Dust-Walker Saloon), Aaron, Jory, and Kaelen went from `present` to `nearby` for one turn. The storyteller emitted "A local guild enforcer enters the saloon" — a new NPC — instead of using established characters.

**Root cause:** Auto-demotion treats all NPCs equally. The system has no way to distinguish companions (who should stay `present`) from scene characters (who should be demoted).

## Constraints

- Must not change the 3-stream extraction pipeline architecture (scene → state → storytell)
- Must not add latency to turn processing
- Must not increase prompt size significantly (context budget is tight)
- Must work with existing `presence` enum: `present`, `nearby`, `known`, `departed`
- Party system is a new feature — no existing data to migrate
- The auto-demotion at `delta_builder.py:228-234` already exists — do not remove it, modify it

## Non-goals

- **NPC re-promotion heuristics.** This design does not add automatic re-promotion logic. If narration shows an NPC following, the scene extractor already handles re-promotion. Party exemption prevents the demotion from happening in the first place — re-promotion becomes unnecessary for party members.
- **Storyteller prompt changes.** The storyteller does not reason about NPC presence. No location-change flag, demoted-NPC list, or present-NPCs section is added to the storyteller prompt. The existing `_npc_roster.j2` sorted-by-presence display is sufficient.
- **Multi-location tracking.** NPCs are not tracked across multiple simultaneous locations.
- **NPC decision-making.** NPCs do not autonomously decide to follow or stay. The scene extractor infers this from narration.
- **Party management UI.** How party members are added/removed from the party is out of scope. Only the scene extractor's party assignment and its effect on auto-demotion are in scope.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Auto-demotion stays | Keep `delta_builder.py:228-234` auto-demotion logic | It is correct — NPCs who don't follow a location change should not stay `present` |
| Party exemption | Per-NPC `party: true` exempts that NPC from auto-demotion | Party members follow by definition; per-NPC handles allies vs. opposition correctly |
| `party` field on NPC compendium entry | New field `compendium[NPC].party: bool` — per-NPC, not global | Scene extractor assigns it per-NPC; avoids global boolean that breaks for oppositional NPCs |
| Scene extractor assigns `party` | Scene extractor sets `party: true` when NPC is likely to follow the PC | Scene extractor reads narration and infers follow-companion relationship (scene extractor's job, not storyteller's) |
| No storyteller prompt changes needed | The existing `_npc_roster.j2` already sorts NPCs by presence — party exemption alone fixes the 1-turn gap | Storyteller does not reason about NPC presence management; scene extractor handles presence, including party assignment |
| `_npc_roster.j2` party indicator | Add `⚔ PARTY` badge to party members in roster (future, cosmetic) | Visual indicator — no functional impact on the fix |

## Open Questions (Resolved)

### Q1: How are party members assigned?

**Resolution:** The scene extractor assigns `party: true` to individual NPC compendium entries during its normal `compendium_npc_update` processing. The criteria is simple: "Is this character likely to follow the PC, or have they been following them?" This is evaluated alongside other NPC updates — not as a separate pass. Once assigned, removal requires a high bar (narration must clearly show the NPC parting ways).

Why the scene extractor and not the storyteller:
- The storyteller runs **after** auto-demotion. It receives the post-demotion state and does not reason about NPC presence management.
- The scene extractor reads narration and determines NPC presence (`present`/`nearby`/`known`/`departed`). Party membership is a natural extension of this — an NPC who consistently follows the PC across location changes should be flagged accordingly.

### Q2: Global boolean vs. per-NPC flag?

**Resolution:** Per-NPC `compendium[NPC].party: bool`. A global boolean means "all named NPCs are party members" which is wrong — named NPCs can be oppositional, temporary, or neutral. Per-NPC is more flexible and not significantly more complex (one extra key in `compendium_npc_update`). The scene extractor decides per-NPC based on narration context.

## Current State — What Exists

### Auto-demotion on location change

**File:** `ccya/state/delta_builder.py:222-239`

When `delta.location_change` is present, the delta builder:
1. Updates `state["location"]` with the new location
2. Iterates all compendium NPCs and sets `presence: "nearby"` for any with `presence: "present"`
3. Removes `notes` from demoted NPCs
4. Stamps `scene.turn_entered` and `scene.location_entered_turn`

```python
# delta_builder.py:228-234
if delta.location_change:
    state["location"] = {...}
    comp = state.setdefault("compendium", {}).setdefault("npcs", {})
    for entry in comp.values():
        if isinstance(entry, dict) and entry.get("presence") == "present":
            entry["presence"] = "nearby"
            entry.pop("notes", None)
```

**Problem:** No party exemption. All `present` NPCs are demoted equally.

### Scene extractor re-promotion

**File:** `ccya/prompts/extract_scene_system.j2:44`

The scene extractor prompt says: "If an NPC was demoted to `nearby` by a location change but narration shows they followed, set `presence: 'present'` — do NOT create a new compendium entry."

**Problem:** This only works if narration mentions the NPC. Narration follows "never repeat prior narration" — location change turns often don't re-mention all NPCs. Creates a 1-turn gap.

### Storyteller NPC context

**File:** `ccya/prompts/storytell_user.j2:8`

The storyteller prompt includes `_npc_roster.j2` which shows ALL NPCs sorted by presence level (present → nearby → known → departed). The storyteller's beat selection depends on having named `present` NPCs — when none exist, it defaults to ambient beats.

**Problem:** After location change, no named NPCs are `present`. The storyteller cannot generate NPC-driven beats.

### NPC roster template

**File:** `ccya/prompts/sections/_npc_roster.j2`

Shows NPCs sorted by presence level. Each entry shows: id, name, title, presence, position, motivation, fear, leverage, bond, personality, last_seen_location, last_presence_turn.

**Problem:** No party indicator. No distinction between "present because narration says so" vs "present because location change didn't demote them."

### Data flow

```
Narration + State
       │
       ▼
┌─────────────────┐
│  Stream 1:      │  Scene extractor
│  Scene Extract  │  → compendium_npc_update (presence changes)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stream 2:      │  State extractor
│  State Extract  │  → location_change (if location changed)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Delta Builder  │  → applies location_change auto-demotion
│  (apply_delta)  │    present → nearby for ALL NPCs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stream 3:      │  Storyteller
│  Storytell      │  → sees demoted NPCs, no present named NPCs
└────────┬────────┘
         │
         ▼
     Narration (next turn)
```

**Gap:** Auto-demotion removes all `present` NPCs, including companions who logically follow the player. Party exemption fixes the demographic gap at source — companions stay `present` — so the storyteller receives the correct roster and can generate NPC-driven beats without needing to know why certain NPCs are `present`.

## Proposed Solution

### Core Changes

#### 1. Per-NPC party flag in compendium

**Where:** Individual compendium NPC entries in `state["compendium"]["npcs"][id]`.

**Shape:**
```python
comp = state["compendium"]["npcs"]
comp["aaron_summers"] = {
    "id": "aaron_summers",
    "name": "Aaron Summers",
    "presence": "present",
    "party": True,  # NEW — exempt from location-change auto-demotion
    # ... existing fields: title, bio, motivation, fear, leverage, bond, personality, etc.
}
comp["saloon_bouncer"] = {
    "id": "saloon_bouncer",
    "name": "Bouncer",
    "presence": "present",
    "party": False,  # NEW — will be demoted on location change
    # ... existing fields
}
```

**Default:** `False` (no change to existing behavior if not set). The scene extractor explicitly sets `party: true` when narratively justified.

**Why per-NPC instead of global:** Global `pc.party: true` means "all named NPCs are party members" — wrong when named NPCs are oppositional, temporary, or neutral. The Outer Rim campaign happens to treat all named NPCs as a pack, but that's one narrative pattern, not a universal rule. Per-NPC handles every case correctly with minimal extra code (one dict key check).

#### 2. Modify auto-demotion to check per-NPC party flag

**File:** `ccya/state/delta_builder.py:228-234`

**Change:** Before demoting an NPC, check `entry.get("party")`. If `True`, skip demotion for that NPC.

**Contract:** The auto-demotion loop becomes:
```
for each compendium NPC:
    if presence == "present":
        if entry.get("party") is True:
            skip (stay present)
        else:
            demote to nearby
```

**Why this order:** Auto-demotion happens in `apply_delta()` which is called by `_build_extraction_context()` (used by storyteller context assembly) AND by the main turn pipeline. Modifying `apply_delta()` ensures both paths get the party exemption.

**No storyteller prompt changes needed:** The storyteller does not reason about NPC presence management. It receives the post-demotion state via `_build_extraction_context()`. Party-exempt NPCs simply appear as `present` in the roster. The existing `_npc_roster.j2` sorted-by-presence display is sufficient — no location-change flag, no recently-demoted section, no present-NPCs heading needed.

#### 3. Scene extractor assigns party membership

**File:** `ccya/prompts/extract_scene_system.j2`

**Change:** Add a rule to the scene extractor prompt instructing it to set `party: true` when an NPC is established as a companion likely to follow the PC.

**Prompt addition (in the `compendium_npc_update` field rules section):**
```
### Party assignment

NPCs who consistently accompany the PC — companions, allies, hirelings — should be marked with `party: true`. Ask: "Is this character likely to follow the PC, or have they been following them?"

- Set `party: true` when narration shows the NPC is traveling with, accompanying, or staying near the PC by choice.
- Keep `party: true` until narration clearly shows the NPC parting ways (departure, betrayal, death, different destination). Removal requires a high bar.
- Do NOT set `party: true` for NPCs who are oppositional, temporary scene characters, or neutral parties. Proximity alone is insufficient.
- Only emit `party` in `compendium_npc_update` when the value changes — omit the field when unchanged (consistent with existing "omit unchanged fields" rule).
```

**Why the scene extractor and not the storyteller:**
- **Pipeline order:** Scene extractor runs first (stream 1). State extractor detects location changes (stream 2). Delta builder applies auto-demotion. Storyteller runs last (stream 3). Party exemption must be in the compendium **before** auto-demotion runs — which means the scene extractor (stream 1) must set it.
- **Responsibility:** The scene extractor already determines NPC presence (`present`/`nearby`/`known`/`departed`). Party membership is a natural extension: "is this NPC likely to stay with the PC?" is a presence-adjacent judgement. The storyteller's job is generating beats, not managing NPC rosters.

**Prompt space budget:** ~15 lines added to `extract_scene_system.j2` (160 lines currently). No corresponding removal needed — the scene extractor prompt has capacity.

## Resolved Design Decisions

These were surfaced during design review and confirmed by the project owner.

| Decision | Resolution | Rationale |
|---|---|---|
| Seed bootstrap | **Pre-set `party: true` in seed/save data** for known companions | Otherwise the first location change can demote companions before the scene extractor has a turn to assign party, recreating the gap |
| Party removal triggers | **Engine auto-clears `party` on `departed`** | When an NPC permanently exits (dies, sails away, etc.), the `party` flag becomes stale. Auto-clearing prevents edge cases where a departed NPC would have been exempt from demotion if they somehow re-entered via a later turn's bug |
| Engine validation | **Minimal: reject `party: true` on unnamed NPCs only** | Named NPCs are the only candidates for party membership. Everything else is LLM-trust — no auto-clear on `known`, no cross-field consistency checks |
| Future model | **Per-NPC `party` flag is the final model** | A party roster (`state.pc.party_ids: list[str]`) adds complexity without solving anything new. The flag already solves the demotion problem. Group-level operations (party inventory, group travel) are separate features if ever needed |

## Turn Trace — Five Turns

Demonstrates the system end-to-end. NPCs with `party: true` stay `present` across location changes; non-party NPCs demote normally; party assignment evolves through narration.

### Setup

| NPC | Initial `party` | Role |
|---|---|---|
| Aaron Summers | `true` | Long-time companion |
| Jory Miller | `true` | Long-time companion |
| Kaelen Vance | `false` | Neutral ally, not yet flagged as follower |
| Saloon Bouncer | `false` | Scene character |
| Guild Enforcer | *(not yet met)* | — |

Locations: A = Millerport Outskirts, B = Dust-Walker Saloon, C = Wharf District.

---

### Turn 1 — Millerport Outskirts (steady state)

**Narration:** Aaron, Jory, Kaelen and the PC are camped. A saloon bouncer stands nearby.

**Scene extractor** (stream 1) reads narration, emits:
- Aaron: `presence: "present"`, `party: true` (unchanged, omitted)
- Jory: `presence: "present"`, `party: true` (unchanged, omitted)
- Kaelen: `presence: "present"` (no party field — still `false`)
- Bouncer: `presence: "present"`

**No location change** — delta builder skips auto-demotion.

**Storyteller** (stream 3) receives roster with 4 `present` NPCs. Generates NPC-driven beat normally.

| NPC | Presence after T1 |
|---|---|
| Aaron | present |
| Jory | present |
| Kaelen | present |
| Bouncer | present |

---

### Turn 2 — Travel to Dust-Walker Saloon (location change)

**Narration:** "You pack up camp and head into town. The saloon doors creak as you enter."

**State extractor** (stream 2) detects `location_change: {id: "dust_walker_saloon"}`.

**Delta builder** runs auto-demotion loop:
- Aaron: `presence == "present"` and `entry.get("party") == True` → **skip** (stays `present`)
- Jory: same → **skip**
- Kaelen: `presence == "present"` and `entry.get("party")` is `None`/`False` → **demote to `nearby`**
- Bouncer: same → **demote to `nearby`**

**Storyteller** (stream 3) receives roster with:
- 2 `present` NPCs (Aaron, Jory) → generates NPC-driven beat using established characters
- 2 `nearby` NPCs (Kaelen, Bouncer) — available for "catches up" beats

**Key difference from current bug:** Storyteller never sees an empty roster. Party exemption bridges the gap.

| NPC | Before delta | After delta |
|---|---|---|
| Aaron | present | **present** (exempt) |
| Jory | present | **present** (exempt) |
| Kaelen | present | nearby |
| Bouncer | present | nearby |

---

### Turn 3 — Inside the Saloon (narration re-introduces Kaelen)

**Narration:** "Kaelen pushes through the saloon doors a moment later, brushing dust off his coat as he joins you at the bar."

**Scene extractor** (stream 1) reads narration. Kaelen is following the PC. Emits:
- Kaelen: `presence: "present"`, `party: true` (new assignment — "following the PC")

**No location change.** Auto-demotion does not run.

**Storyteller** sees 3 `present` NPCs (Aaron, Jory, Kaelen). Normal NPC-driven beat.

| NPC | Presence | party |
|---|---|---|
| Aaron | present | true |
| Jory | present | true |
| Kaelen | present | **true** (newly assigned) |
| Bouncer | nearby (1 turn) | false |

**Prompt side effect:** The scene extractor needed to determine Kaelen was "likely to follow." The narration showed him catching up — a clear signal. The high bar for removal means once `party: true`, it stays unless narration explicitly shows him parting ways.

---

### Turn 4 — Saloon altercation (Bouncer engages)

**Narration:** "The bouncer stomps over, jabbing a thick finger at Aaron. 'You're banned, Summers. Out.' Aaron doesn't flinch."

**Scene extractor** reads narration. Bouncer is oppositional (not party). Aaron is present. No changes to party assignments — Bouncer was already `party: false`, Aaron already `party: true`.

**No location change.** Auto-demotion does not run.

**Nearby decay:** Bouncer has been `nearby` for 2 turns — decays to `known` after this turn.

**Storyteller** sees 3 `present` NPCs, 1 `known` (Bouncer). Generates beat around the conflict.

| NPC | Presence | party |
|---|---|---|
| Aaron | present | true |
| Jory | present | true |
| Kaelen | present | true |
| Bouncer | nearby → **known** (decayed) | false |

---

### Turn 5 — Move to Wharf District (second location change, Kaelen still following)

**Narration:** "You leave the saloon behind and head for the wharf. Aaron mutters about the bounty on his head."

**State extractor** detects `location_change: {id: "wharf_district"}`.

**Delta builder** runs auto-demotion loop:
- Aaron: `party == True` → **skip** (stays `present`)
- Jory: `party == True` → **skip** (stays `present`)
- Kaelen: `party == True` → **skip** (stays `present`)
- Bouncer: `presence == "known"` → not in loop (loop only checks `present` NPCs; `known` is below threshold)

**Storyteller** sees 3 `present` NPCs. Generates NPC-driven beat about the bounty hunt. No gap.

| NPC | After delta |
|---|---|
| Aaron | present |
| Jory | present |
| Kaelen | present |
| Bouncer | known (unaffected) |

### Summary

| Turn | Location change? | Present NPCs | Beat quality |
|---|---|---|---|
| 1 | No | Aaron, Jory, Kaelen, Bouncer | NPC-driven (normal) |
| 2 | **Yes** (A→B) | **Aaron, Jory** (exempt), Kaelen+Bouncer demoted | **NPC-driven** — no gap |
| 3 | No | Aaron, Jory, **Kaelen** (re-promoted + party assigned) | NPC-driven |
| 4 | No | Aaron, Jory, Kaelen (Bouncer decays) | NPC-driven |
| 5 | **Yes** (B→C) | **Aaron, Jory, Kaelen** (all exempt) | **NPC-driven** — no gap |

**Key result:** Every turn has at least 2 `present` named NPCs. The 1-turn gap never materializes because party exemption covers the location-change turns where the narrator "never repeats prior narration."

### Alternatives Considered and Rejected

#### Alternative: Pre-demotion roster in storyteller prompt

**What:** Pass the pre-demotion NPC roster to the storyteller so it can see who was present before location change.

**Why rejected:** The storyteller does not reason about NPC presence management — that's the scene extractor's role. Party exemption already fixes the gap by keeping party-member NPCs `present`. The storyteller sees the correct post-demotion state and generates beats from it. No snapshot needed.

#### Alternative: Scene extractor knows about location change

**What:** Pass location change information to the scene extractor so it can pre-populate re-promotion.

**Why rejected:** Scene extractor runs BEFORE state extractor in the pipeline. It cannot know about location changes that haven't been detected yet. The pipeline order is: scene → state → storytell. Location change is detected by state extractor, not scene extractor.

#### Alternative: Don't auto-demotion, let scene extractor handle it

**What:** Remove auto-demotion entirely. Let scene extractor demote NPCs based on narration.

**Why rejected:** This is what the eval found — narration doesn't mention NPCs on location change turns ("never repeat prior narration"), so they stay `present` indefinitely. The guild enforcer stayed `present` for 12 turns across location changes because narration kept mentioning them. Auto-demotion is the correct default — it prevents NPC ghosting.

#### Alternative: Global `pc.party` Boolean

**What:** Single `state.pc.party: true/false` flag meaning "all named NPCs are party members."

**Why rejected:** Named NPCs can be oppositional, temporary, or neutral. A global boolean incorrectly treats every named NPC as a companion. Per-NPC `party` flag handles every case correctly — companions stay present, oppositional NPCs get demoted, scene characters cycle normally.

## Failure Modes and Risks

### Risk: Scene extractor assigns `party: true` inconsistently

**What:** The LLM is asked to make a judgement ("is this character likely to follow the PC?") that varies across invocations for the same NPC. One turn it sets `party: true`, the next it omits the field, the next it sets `party: false`.

**Mitigation:** The instructions emphasize a high bar for removal — once `party: true` is set, narration must clearly show the NPC parting ways before the scene extractor should change it. This biases toward keeping the flag stable. Additionally, the scene extractor typically only emits a `compendium_npc_update` for an NPC when narration mentions them — if an NPC is `party: true` and not mentioned this turn, the flag persists from the prior compendium state (no update emitted = no change).

### Risk: Oppositional NPC accidentally flagged as party

**What:** The scene extractor incorrectly sets `party: true` on a named antagonist who is present in the scene but not a companion.

**Mitigation:** The prompt explicitly says "Do NOT set `party: true` for NPCs who are oppositional." The scene extractor already differentiates NPC stances via `position`, `motivation`, and `fear` fields — party assignment leverages the same narrative understanding.

### Risk: Party flag set on NPCs that then never get demoted

**What:** Once `party: true` is set, an NPC is permanently exempt from location-change auto-demotion. If the flag is set too aggressively, NPCs ghost across locations without narrative justification.

**Mitigation:** This is the intended behavior. If an NPC is flagged as party, they are expected to follow. The high-removal-bar mitigates false positives — the scene extractor must clearly see a departure before removing the flag. Over-assignment is less harmful than under-assignment (the original problem was demoting NPCs who should stay).

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| Location change flag for storyteller | Design (never existed in code) | Storyteller does not reason about NPC presence — scene extractor handles it |
| Demoted NPC list / recently demoted section | Design (never existed in code) | No consumer; storyteller sees correct post-demotion state without this |
| `demoted_this_turn` flag | Design (never existed in code) | Would create transient mutable state in compendium — removed before implementation |
| Present NPCs section in storyteller prompt | Design (never existed in code) | The existing `_npc_roster.j2` already sorts by presence — sufficient |
| Global `pc.party` boolean | Design (never existed in code) | Replaced by per-NPC `party` flag on compendium entries |

## What Is Unchanged

- Scene extractor pipeline (stream 1) — `extract_scene_system.j2` gains ~15 lines for party assignment rules; `extract_scene_user.j2` unchanged
- Scene extractor re-promotion rules — narration-based re-promotion stays as-is
- State extractor pipeline (stream 2) — no changes to `extract_state_system.j2` or `extract_state_user.j2`
- `presence` enum values — `present`, `nearby`, `known`, `departed` stay unchanged
- Nearby decay TTL — `nearby` NPCs still decay to `known` after 2 turns if not re-promoted
- Departed archive TTL — `departed` NPCs still archive after 3 turns
- NPC roster sorting — present → nearby → known → departed order stays unchanged
- Storyteller beat selection logic — no changes to how beats are selected
- Storyteller thread/arc logic — no changes to thread or arc handling
- Delta builder inventory/condition logic — only location-change NPC demotion is modified
- `_npc_roster.j2` — no changes; party badge is cosmetic and deferrable

## New Model Shapes

### Compendium NPC entry (extension)

```python
# Existing fields unchanged. New field:
{
    "id": str,
    "name": str,
    "presence": "present|nearby|known|departed",
    # ... existing fields ...
    "party": bool,  # NEW — exempt from location-change auto-demotion if true; assigned by scene extractor, high bar to remove
}
```

**Default:** `False` (omitted or false — no change to existing behavior). Set to `True` by scene extractor via `compendium_npc_update` when NPC is established as a companion.

### State PC dict (no changes)

```python
state["pc"] = {
    "name": str,
    "tagline": str,
    "bio": str,
    "stats": dict,
    "conditions": list,
    "allegiance": str | None,
    # No party field here — it lives on individual NPC entries
}
```

## Context for Implementing LLMs

| File | What it contains | Why it matters |
|---|---|---|
| `ccya/state/delta_builder.py:222-239` | Location change auto-demotion loop | Primary change — add per-NPC `party` check before demoting |
| `ccya/prompts/extract_scene_system.j2` | Scene extractor system prompt | Add party assignment rules (~15 lines in compendium_npc_update section) |
| `ccya/state/npcs.py:172-333` | `apply_npc_scene_management()` | Must add explicit write logic: `if comp_upd.party is not None: entry["party"] = comp_upd.party` (around line 310, with other field writes) |
| `ccya/models/extraction.py:18-33` | `CompendiumNpcUpdate` model | Must add `party: bool | None = None` field — Pydantic ignores extra fields by default, so `party` from LLM output would be silently dropped without this |
| `ccya/engine/npc_roster.py:14-93` | `build_npc_roster()` | Verify `party` field is included in roster entries (it copies all dict keys via `npc.get("party")`) |
| `ccya/prompts/sections/_npc_roster.j2` | NPC roster template | No changes needed — party badge is cosmetic and deferrable |
| `ccya/prompts/storytell_user.j2` | Storyteller user prompt | No changes — storyteller does not reason about NPC presence; the existing roster display is sufficient |
| `ccya/engine/extraction/pipeline.py` | Pipeline context assembly | No changes — `_build_extraction_context()` calls `apply_delta()` which handles the party check; no new context to pass |
| `ccya/engine/extraction/context.py:38-77` | `_build_extraction_context()` | No changes — already calls `apply_delta()` on a state copy; party exemption works automatically |
| `ccya/models/extraction.py` | `SceneExtractResult` model | Verify `party` is accepted in compendium_npc_update dicts (Pydantic `Extra.forbid` check) |
