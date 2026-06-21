# Location-Change NPC Party Exemption

## Purpose

One plan to implement per-NPC `party: true` flag that exempts companion NPCs from location-change auto-demotion, preventing the 1-turn gap where the storyteller has no named present NPCs.

## Problem Statement

When the player changes location, `delta_builder.py` auto-demotes all `present` NPCs to `nearby`. There is no distinction between companions (who should stay `present`) and scene characters (who should be demoted). Since the narrator follows "never repeat prior narration," location-change turns often don't re-mention NPCs, so the scene extractor cannot re-promote them next turn. The storyteller receives an empty `present` roster and generates ambient beats instead of NPC-driven ones.

## Constraints

- Must not change the 3-stream extraction pipeline (scene → state → storytell)
- Must work with existing `presence` enum (`present`, `nearby`, `known`, `departed`)
- Auto-demotion at `delta_builder.py:228-234` stays — only add a per-entry exemption check
- No storyteller prompt changes — storyteller does not reason about NPC presence
- Tests are removed during refactor — no test files to write

## Non-goals

- Party badge in `_npc_roster.j2` (cosmetic, deferred)
- Party management UI
- Party roster (`state.pc.party_ids`) — per-NPC flag is the final model
- Any changes to `npc_roster.py`, `context.py`, `pipeline.py`, `storytell_user.j2`, or `narrate_user.j2`

## Solution

Add `party: bool` to `CompendiumNpcUpdate` model and compendium entries. The scene extractor sets `party: true` via `compendium_npc_update` when narration shows an NPC following the PC. The delta builder's auto-demotion loop checks `entry.get("party")` before demoting — if true, the NPC stays `present`. The NPC scene management (`apply_npc_scene_management`) writes the field to state, auto-clears it on `departed`, and rejects it on unnamed NPCs. Seeds pre-set `party: true` on known companions.

## Firm decisions

1. **Per-NPC `party` flag** in compendium, not global `pc.party` boolean
2. **Scene extractor assigns** `party` during normal `compendium_npc_update` processing — criteria: "likely to follow the PC or has been following them"
3. **Seed pre-sets** `party: true` on known companions (Aaron, Jory, Kaelen)
4. **Auto-clear on departed** — engine clears `party` when NPC presence becomes `departed`
5. **Minimal validation** — reject `party: true` on unnamed NPCs only
6. **No storyteller prompt changes** — no location-change flag, no demoted list, no present-NPCs section
7. **No roster changes** — `party` field not needed in `build_npc_roster()` output

## Risks, Ambiguities, and Blockers

- **Scene extractor LLM compliance**: Party assignment relies on the LLM following the new prompt rules. This cannot be validated until the prompt is run against a real save. Mitigation: the auto-clear on departed and high-removal-bar instructions guard against common failure modes.
- **Seed retrofitting**: Existing seeds (packs/outer-rim/) need `party: true` on companion NPCs. This is a data change, not code — but must be done before the save is loaded. If a save was created before this change, companions that should be party members will lack the flag.
- **No test coverage**: Tests are removed during refactor. Manual verification via `ev.py play` is the only validation path.

## Status

`open`

## Phases

2 phases:
- Phase 1: Model + backend (model field, scene management writes, delta builder check, seed data)
- Phase 2: Scene extractor prompt (party assignment rules)

---

## Implementation — Phase 1: Model + backend party logic

### Context files to load

- `ccya/models/extraction.py` — read `CompendiumNpcUpdate` class (lines 18-33)
- `ccya/state/npcs.py` — read `apply_npc_scene_management()` (lines 172-333)
- `ccya/state/delta_builder.py` — read `apply_delta()` location-change section (lines 222-234)
- `ccya/state/io.py` — read `_default_state()` (lines 65-88) to confirm compendium shape
- `ccya/personality.py` — (optional) read `assign_personality()` to understand unnamed guard pattern
- `packs/outer-rim/` — read seed_state.yaml to find companion NPC entries needing `party: true`
- `docs/architecture/state-models.md` — existing state shape documentation
- `docs/architecture/cross-module-contracts.md` — existing contract documentation
- `docs/repomap.md` — existing module index

### Detailed steps

#### Step 1.1 — Add `party` field to CompendiumNpcUpdate model

**File:** `ccya/models/extraction.py`

**What:** Add `party: bool | None = None` field to the `CompendiumNpcUpdate` class (after `departed_turn` on line 33, before the closing blank line).

**Why:** Pydantic v2 ignores extra fields by default — without an explicit field, `party` from the LLM output is silently dropped and never reaches state.

**Validation:** Start a Python shell, import `CompendiumNpcUpdate`, create an instance with `party=True`, confirm field is present.

```python
# Contract — new field only, no existing fields change
class CompendiumNpcUpdate(BaseModel):
    # ... existing fields unchanged ...
    departed_turn: int | None = None       # existing
    party: bool | None = None              # NEW
```

#### Step 1.2 — Write `party` in NPC scene management + auto-clear on departed + unnamed guard

**File:** `ccya/state/npcs.py` — `apply_npc_scene_management()`

**What:** Three sub-changes within the processing loop (after existing field writes around line 283, and within the unnamed guard around line 262):

1. **Reject on unnamed NPCs:** In the unnamed NPC guard block (lines 262-275), add `"party": None` to the `model_copy(update=...)` dict so unnamed NPCs never receive `party: true`.

2. **Write party:** After the existing `if comp_upd.personality is not None` block (line 284), add: `if comp_upd.party is not None: entry["party"] = comp_upd.party`

3. **Auto-clear on departed:** After the presence write logic (look for `if comp_upd.presence is not None:` near line 293), add: if `comp_upd.presence == "departed"`, set `entry["party"] = False` (or `entry.pop("party", None)`).

**Why:** Party must persist in state through normal compendium update processing. Auto-clear on departed prevents stale party flags on NPCs that permanently exit. Unnamed NPCs should never be companions.

**Validation:** Read the existing `model_copy(update={...})` pattern for unnamed guard to verify the approach composes correctly.

#### Step 1.3 — Add party exemption check to auto-demotion loop

**File:** `ccya/state/delta_builder.py` — `apply_delta()` location-change block (lines 222-234)

**What:** In the auto-demotion loop (lines 231-234), before setting `entry["presence"] = "nearby"`, check `entry.get("party")`. If `True`, skip demotion (do not mutate the entry at all — keep `presence` as `present` and keep `notes`).

**Contract:**
```python
for entry in comp.values():
    if isinstance(entry, dict) and entry.get("presence") == "present":
        if entry.get("party"):
            continue  # party members stay present
        entry["presence"] = "nearby"
        entry.pop("notes", None)
```

**Why:** Party-exempt NPCs must not be demoted. The check is per-entry (reads `party` from the compendium dict), not global.

**Validation:** Can be verified by inspecting the diff — no runtime test possible without a running server.

#### Step 1.4 — Add `party: true` to Outer Rim seed companion NPCs

**File:** `packs/outer-rim/seed_state.yaml` (or equivalent seed file for the Outer Rim campaign)

**What:** Locate compendium entries for Aaron Summers, Jory Miller, Kaelen Vance (or whatever the companions are). Add `party: true` to each.

```yaml
compendium:
  npcs:
    aaron_summers:
      name: Aaron Summers
      # ... existing fields ...
      party: true       # NEW
    jory_miller:
      name: Jory Miller
      party: true       # NEW
    kaelen_vance:
      name: Kaelen Vance
      party: true       # NEW
```

**Why:** Without seed pre-setting, the first location change can demote companions before the scene extractor has a turn to assign party.

**Validation:** Grep the seed file for the companion NPC IDs and confirm `party: true` is present.

#### Step 1.5 — Update architecture documentation

**Files:**
- `docs/architecture/state-models.md`
- `docs/architecture/cross-module-contracts.md`
- `docs/architecture/OVERVIEW.md`
- `docs/repomap.md`

**What:**

1. **`state-models.md`** (line 49): Add `party: bool | None` to the compendium NPC entry shape in the YAML block.
2. **`state-models.md`** (line 71): Note `party` is NOT a field on `NpcPresence` (that model is just presence values, not the full compendium entry).
3. **`state-models.md`** (line 76): Update `CompendiumNpcUpdate` description to mention `party` field.
4. **`cross-module-contracts.md`** (line 51): Add `party` to the `CompendiumNpcUpdate` contract description.
5. **`repomap.md`**: No changes — module boundaries are unchanged.

**Why:** Stale docs are bugs. The state model and cross-module contracts must reflect the new field.

**Validation:** Read each doc and verify the new field is mentioned where appropriate.

### Tests to write or update

No tests — tests are removed during refactor. Skip this section.

---

## Implementation — Phase 2: Scene extractor prompt party assignment rules

### Context files to load

- `ccya/prompts/extract_scene_system.j2` — read the full file (currently 160 lines)
- `ccya/prompts/extract_scene_user.j2` — read the full file (12 lines, confirms template includes `_npc_roster.j2`)
- `ccya/prompts/sections/_npc_roster.j2` — read the full file (14 lines, confirms no changes needed)
- `docs/architecture/step2a-scene.md` — read the scene extractor architecture doc

Phase 1 must be complete before this phase starts (the model must accept `party` before the LLM can emit it).

### Detailed steps

#### Step 2.1 — Add party assignment section to scene extractor system prompt

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** After the `### Output discipline` section (or before the `## Constraints` section, whichever is more natural — preserve existing section ordering), add a new subsection under the `compendium_npc_update` field rules:

```
### Party assignment

NPCs who consistently accompany the PC — companions, allies, hirelings — should be marked with `party: true`. Ask: "Is this character likely to follow the PC, or have they been following them?"

- Set `party: true` when narration shows the NPC is traveling with, accompanying, or staying near the PC by choice.
- Keep `party: true` until narration clearly shows the NPC parting ways (departure, betrayal, death, different destination). Removal requires a high bar.
- Do NOT set `party: true` for NPCs who are oppositional, temporary scene characters, or neutral parties. Proximity alone is insufficient.
- Only emit `party` in `compendium_npc_update` when the value changes — omit the field when unchanged (consistent with existing "omit unchanged fields" rule).
```

**Why:** The scene extractor needs explicit instructions to assign party membership. Without these, the LLM will never set `party: true` — it doesn't know the field exists or what criteria to use.

**Prompt space budget:** ~15 lines added to `extract_scene_system.j2` (currently 160 lines). No removal needed — the prompt has capacity.

**Contract:** The `party` field must be included in the `compendium_npc_update` JSON schema example at the top of the prompt (around line 9). Update the schema example to show `"party": true` and `"party": false` as valid fields:

```json
{
  "compendium_npc_update": [{
    "id": "...",
    "name": "...",
    "title": "...",
    "bio": "...",
    "aliases": ["..."],
    "motivation": "...",
    "fear": "...",
    "leverage": "...",
    "bond": "...",
    "personality": "...",
    "presence": "present|nearby|known|departed",
    "position": "...",
    "party": true
  }]
}
```

Note the existing example may not include all fields — add `"party"` to whichever example shows the full field set. If there's no full-field example, add a note in the field rules section that `party` is an optional boolean.

**Validation:** Render the template with sample data (use `ev.py prompt-eval dump` if available, or just inspect the rendered output manually) and confirm the party section appears correctly.

#### Step 2.2 — Update scene extractor architecture doc

**File:** `docs/architecture/step2a-scene.md`

**What:** Add a note that the scene extractor now also assigns `party: true` to companion NPCs. Mention the criteria and the pipeline-order rationale (scene extractor runs before delta builder, so party assignment must happen in stream 1).

**Why:** The architecture doc describes what the scene extractor produces. Party assignment is a new output channel.

**Validation:** Read the doc — the party assignment language should be present.

### Tests to write or update

No tests — tests are removed during refactor. Skip this section.
