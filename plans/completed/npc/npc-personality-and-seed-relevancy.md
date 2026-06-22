# NPC personality: LLM-assigned from archetype list, with engine fallback

## Purpose

NPC personalities come from the LLM (from a fixed archetype list), not from engine keyword-matching. Seed NPCs always get one. Mid-game named NPCs get one at introduction. Unnamed NPCs get nothing until they earn a name. Also, kill filler NPCs — only generate characters that serve the arc.

## Problem Statement

1. **`assign_personality()` produces arbitrary results** — shallow substring matching against hardcoded keyword tuples. Ties break by insertion order. No semantic understanding. The `personality` field was always meant to be LLM-assigned (model accepts it, seed pipeline accepts it), but the prompts hide it behind "personality assigned by engine post-parse" — so the LLM never emits it and the bad fallback is the only path.

2. **Filler NPCs** — seed prompt demands 4-6 NPCs by presence count, producing compendium entries with no narrative role.

## Constraints

- 12 archetypes are stable. Not changing them.
- `personality` stays a string archetype id in the data model.
- Unnamed NPCs (alias-only, no `name`) never get personality — even from engine.
- Named NPCs (proper name in `name`) must always have one.

## Non-goals

- No migration for existing saves.
- No tests (still disabled).

## Solution

**For personalities:** Make `personality` a required field for all named NPCs in seed and scene extraction prompts. The LLM picks from the 12 archetype table contextually. Engine `assign_personality()` exists only as a safety net for when the LLM omits it or provides an invalid ID. Unnamed NPCs (alias-only) get `bio` and nothing else — when promoted to named later, they get personality + ~2 other fields at that point.

**For NPC relevancy:** Remove all presence-count targets from seed prompt. Only NPCs in the direct path of the arc get generated.

## Firm decisions

1. **LLM assigns personality — engine is fallback only.** The prompt tells the LLM "must have" for named NPCs. Engine `assign_personality()` only fires when the LLM doesn't or provides an invalid ID. Not a complement — a safety net.
2. **Field count tiers:**
   - Unnamed (alias-only): `bio` only.
   - Promoted to named: add `personality` + 2 of {motivation, fear, leverage, bond} at promotion time.
   - Named NPC: `bio` + `personality` + ~3 of {motivation, fear, leverage, bond} total.
   - Important/seed NPCs: 4-5 of {personality, motivation, fear, leverage, bond}.
3. **Alias-only NPCs are valid.** The LLM sets `aliases` only (no `name`) for unnamed characters. When named later, it adds `name` — old aliases stay for history. Engine treats alias-only as valid unnamed NPCs.
4. **Group NPCs always include a count.** If an NPC entry represents a group ("armed guards", "dockworkers"), the `name` or `notes` must state the number. We must always know exactly how many people are in any scene or grouping.
5. **No backward compat.** Remove dead code: `npc_count_override` sections, old presence-count language, the "personality assigned by engine post-parse" comment, and any stale NPC-related code paths that are no longer reachable.
6. Default fallback archetype: `wary_opportunist`. Not relitigated.

## Risks, Ambiguities, and Blockers

- The LLM may omit `personality` for a named NPC despite the instruction. Engine handles this via `assign_personality()` fallback on motivation/fear. Acceptable.
- The LLM may invent archetype IDs. `validate_and_resolve()` catches this — the bug (keeping invalid values) is fixed in Phase 2.
- The named-vs-unnamed heuristic needs careful wording in both seed and extraction prompts to avoid confusion.
- Plural NPC count enforcement is purely prompt-driven — no engine validation. May need a checker later.

## Status
`completed`

## Phases

4 phases, ordered by dependency: prompt changes first so the LLM knows what to produce, then engine fallback/validation, then UI rendering, then prompt tightening + dead code removal + doc updates.

## Implementation — Phase 1: Expose personality to LLM in prompt field rules

### Context files to load

- `ccya/prompts/generate_seed_system.j2`
- `ccya/prompts/generate_seed_user.j2`
- `ccya/prompts/extract_scene_system.j2`
- `ccya/personality.py`

### Detailed steps

#### Step 1.1 — Seed prompt: remove `/* personality assigned by engine post-parse */` comment, add archetype reference to schema

**File:** `ccya/prompts/generate_seed_system.j2` (line 36)

**What:** In the schema comment, replace:
```
bond?: string, motivation?: string, fear?: string, leverage?: string /* personality assigned by engine post-parse */
```
with:
```
bond?: string, motivation?: string, fear?: string, leverage?: string, personality?: archetype_id  /* see Personality archetypes table below — required for named NPCs, omit for unnamed */
```

**Why:** The old comment told the LLM to skip `personality` entirely. The new one tells the LLM it's available and directs to the rules section.

**Validation:** The schema line no longer says "assigned by engine post-parse".

#### Step 1.2 — Seed prompt: add Personality archetypes field rules section

**File:** `ccya/prompts/generate_seed_system.j2` (insert after line 91, before "Do NOT add `relation`..." line)

**What:** Add a new section with the archetype table and tiered field rules.

**New section content:**

```
## NPC field requirements

NPCs have 5 personality-related fields: `personality`, `motivation`, `fear`, `leverage`, `bond`.
How many depends on the NPC's role:

- **Unnamed NPCs (descriptive label in `name` + same string in `aliases`; no proper name):**
  `bio` only. Do NOT add any personality fields until the NPC gets a proper name.
- **Named NPCs (proper name in `name`):** Must have `bio`, `personality` (from the table below),
  and at least 2 more of {motivation, fear, leverage, bond} — aim for 3 personality-relevant fields total.
- **Important NPCs (seed characters, arc goal characters, faction leaders):** 4-5 of the 5 fields.
  These are the characters the story revolves around — give them depth.

**Group NPCs:** If an entry represents multiple people ("three armed guards", "dockworkers"),
the `name` or `notes` must always state the exact count. We must know how many people are in any scene.

## Personality archetypes (choose from this fixed list)

| ID | Label | Traits |
|---|---|---|
| `cold_pragmatist` | Cold Pragmatist | calculating, direct, emotionally distant |
| `desperate_idealist` | Desperate Idealist | principled, anxious, self-sacrificing |
| `wary_opportunist` | Wary Opportunist | adaptive, self-interested, quick to read angles |
| `resigned_functionary` | Resigned Functionary | bureaucratic, weary, procedurally polite |
| `volatile_loyalist` | Volatile Loyalist | fiercely loyal, short-fused, protective |
| `charming_manipulator` | Charming Manipulator | persuasive, socially fluid, rarely direct |
| `blunt_survivor` | Blunt Survivor | unsentimental, pragmatic, darkly humorous |
| `true_believer` | True Believer | zealous, certain, morally inflexible |
| `detached_observer` | Detached Observer | analytical, quiet, observant |
| `conflict_avoidant` | Conflict-Avoidant | yielding, nervous, self-effacing |
| `ambitious_climber` | Ambitious Climber | patient, strategic, calculating |
| `broken_defeated` | Broken/Defeated | worn, habit-driven, darkly resigned |

Choose the archetype that best fits the NPC's motivation, fear, and narrative role. Be specific — `wary_opportunist` is the default only when no other archetype clearly fits. Do not invent archetypes outside this list.
```

**Why:** This replaces the old NPC rules section (which listed presence counts) with a clear tiered requirement. Every named NPC must have `personality` — no ambiguity. Unnamed NPCs get nothing extra. Counts are enforced for group NPCs.

**Validation:** Generate a seed — named NPCs have valid archetype IDs, unnamed NPCs have none, group NPCs have counts.

#### Step 1.3 — Seed prompt: remove old NPC count requirements

**File:** `ccya/prompts/generate_seed_system.j2` (lines 74-98 — the old NPC rules block)

**What:** Delete the following content:
- "Generate 4-6 named NPCs total: ~2 present..."
- "Aim for 1-4 present NPCs..."
- "For all present NPCs with narrative roles..."
- The `npc_count_override` line
- The "If `pool_selection.npc_bond`..." line (migrate to new section if relevant)

Replace with the content from Step 1.2 above. Also update the "NPC role alignment" line if it still references old presence categories.

**Note:** The `{% if scenario and scenario.factions %}NPC role alignment{% endif %}` block (lines 94-96) is about faction consistency, not NPC counts — **preserve it as-is**. The new tiered field rules section from Step 1.2 goes in its place after this preserved block.

**Validation:** The seed prompt no longer has presence-count language.

### Tests to write or update

No test changes (tests temporarily disabled during refactor).

#### Step 1.4 — Seed user prompt: remove `npc_count_override` section + update compendium language

**File:** `ccya/prompts/generate_seed_user.j2`

**What:**
- Remove lines 62-65 (the `{% if npc_count_override %}` block)
- Replace lines 57-61 (the "compendium_generation" paragraph) with a brief relevancy constraint: only generate compendium NPCs when they serve a necessary narrative function tied to the arc.

**Validation:** User prompt no longer references NPC count targets.

#### Step 1.5 — Scene extraction prompt: add personality to field rules

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Three changes:

1. **Schema reference (line 12):** Add `bond` (pre-existing gap — in model but not schema) and `personality` to the inline schema:
   ```
   "compendium_npc_update": [{"id", "name", "title", "bio", "aliases", "allegiance", "motivation", "fear", "leverage", "bond", "personality", "presence", "notes", "position"}]
   ```

2. **Detailed schema (lines 26-42):** Add `bond` and `personality` as optional fields. Insert after `leverage` (line 36):
   ```json
   "bond": "durable personal history — to the PC, or between two NPCs (name both parties)",
   "personality": "archetype_id — see archetype reference below; required for named NPCs, omit for unnamed",
   ```

3. **NPC field requirements (lines 70-74):** Replace with tiered rules:
   - **Named NPCs (proper name in `name`):** Must have `bio` + `personality` + at least 2 of {motivation, fear, leverage, bond} = 4 fields minimum. On first entry, aim for all fields.
   - **Unnamed NPCs (descriptive label only; name goes in `aliases`, not `name`):** `bio` only. Do NOT add personality, motivation, fear, leverage, bond, or any other personality-related fields.
   - **Promotion to named:** When narration reveals a proper name for an NPC previously known by description, set `name` to the proper name AND add `personality` + 2 of {motivation, fear, leverage, bond}. Keep the old descriptor in `aliases`.
   - **Group NPCs:** If the entry represents multiple people, the `name` or `notes` must always state the exact count. We must always know how many people are in any scene or grouping.

4. **Add archetype reference line:**
   ```
   Valid personality archetype IDs: cold_pragmatist, desperate_idealist, wary_opportunist, resigned_functionary, volatile_loyalist, charming_manipulator, blunt_survivor, true_believer, detached_observer, conflict_avoidant, ambitious_climber, broken_defeated. Do not invent archetypes outside this list.
   ```

**Why:** The scene extractor needs to produce `personality` for named NPCs it introduces or promotes. The tiered rules mirror the seed prompt rules exactly.

**Validation:** Run a turn where a named NPC enters the scene — it should have a valid personality archetype. An alias-only NPC gets no personality.

---

## Implementation — Phase 2: Fix engine fallback and validation

### Context files to load

- `ccya/engine/seed.py` (lines 300-316)
- `ccya/state/io.py` (lines 19-34)
- `ccya/state/npcs.py` (lines 97-190)
- `ccya/personality.py`

### Detailed steps

#### Step 2.1 — Seed: fall back to `assign_personality()` when LLM provides invalid archetype id

**File:** `ccya/engine/seed.py` (lines 310-316)

**What:** When `validate_and_resolve()` returns `None`, call `assign_personality()` with the NPC's motivation/fear instead of keeping the invalid value.

**Why:** Currently the code logs a warning but keeps the bad string. This means the NPC silently has no personality in the UI.

**Validation:** Every NPC with a truthy `personality` after `generate_seed()` must be in `ARCHETYPES.keys()`.

#### Step 2.2 — State loader: validate archetype before skipping

**File:** `ccya/state/io.py` (line 27)

**What:** Change `if entry.get("personality"): continue` to `if entry.get("personality") and entry["personality"] in ARCHETYPES: continue`. Import `ARCHETYPES` from `ccya.personality`.

**Why:** Bad values survive permanently under the current guard.

**Validation:** Run `_assign_seed_personalities()` on a state dict with `personality: "bogus"` — it overwrites with a valid archetype.

#### Step 2.3 — Mid-game named NPC fallback

**File:** `ccya/state/npcs.py` (after line 167)

**What:** After the existing `comp_upd.personality` block, add a fallback that assigns personality only for NPCs with a proper name. An NPC has a proper name if `name` is populated and `name.lower()` is not in `[a.lower() for a in aliases]` — this matches the prompt convention where unnamed NPCs put their descriptor in both fields.

**The code:**

```python
# Engine fallback: assign personality for named NPCs that still lack one.
# Unnamed NPCs (alias-only, no proper name) are intentionally skipped.
if not entry.get("personality") and entry.get("name"):
    entry_aliases = [a.lower() for a in (entry.get("aliases") or [])]
    if entry["name"].lower().strip() not in entry_aliases:
        from ccya.personality import assign_personality
        arch = assign_personality(
            motivation=entry.get("motivation"),
            fear=entry.get("fear"),
            npc_id=resolved_id,
        )
        entry["personality"] = arch.id
```

**Why:** Named NPCs always need a personality. If the LLM doesn't provide one, the engine assigns it via keyword-scoring fallback. Unnamed NPCs (alias-only or descriptor-only) are correctly skipped.

**Validation:** A named NPC update without `personality` gets one engine-side. An alias-only NPC update with no `name` stays personality-free.

#### Step 2.4 — Remove dead `npc_count_override` code in seed generation (if exists)

**File:** `ccya/engine/seed.py`

**What:** Search for any references to `npc_count_override` (likely passed as a CLI parameter or config value). If the prompt no longer supports it, remove the code paths that pass it.

**Validation:** No references to `npc_count_override` remain in the engine.

### Tests to write or update

No test changes (tests temporarily disabled during refactor).

---

## Implementation — Phase 3: Fix UI rendering

### Context files to load

- `ccya/server/routes.py` (lines 187-208, 462-463, 491-494, 497-509, 512-516)

### Detailed steps

#### Step 3.1 — Add `_resolve_npc_personalities()` to `index` route

**File:** `ccya/server/routes.py` (line 190)

**What:** Call `_resolve_npc_personalities(state)` after `state = _load_current_state()`.

#### Step 3.2 — Add `_resolve_npc_personalities()` to `new_game` route

**File:** `ccya/server/routes.py` (line 462)

**What:** Add `_resolve_npc_personalities(ctx["state"])` after `ctx = _debug_context()`.

#### Step 3.3 — Add `_resolve_npc_personalities()` to `panel_state` route

**File:** `ccya/server/routes.py` (line 492-494)

**What:** Load state and call `_resolve_npc_personalities()` before rendering.

### Tests to write or update

No test changes (tests temporarily disabled during refactor).

---

## Implementation — Phase 4: Tighten seed NPC relevancy + dead code removal + doc updates

### Context files to load

- `ccya/prompts/generate_seed_system.j2`
- `ccya/prompts/generate_seed_user.j2`
- `ccya/engine/seed.py` (line 167)
- `ccya/pack.py` (line 193, 204)
- `ccya/server/routes.py` (lines 403-407, 415)
- `ccya/templates/_char_creation.html` (lines 7, 95-100)
- `ccya/templates/index.html` (line 926, 1520, 1522)
- `docs/architecture/out-of-band.md` (line 73)
- `docs/architecture/step2a-scene.md` (line 44)
- `docs/repomap.md` (lines 20, 64, 197, 252)

### Detailed steps

#### Step 4.1 — Verify seed prompt NPC relevancy changes are complete

(Already covered in Phase 1 steps 1.2-1.3 — validation pass to confirm the seed system prompt no longer has presence-count requirements and the new tiered field rules are in place.)

**Validation:** Read `generate_seed_system.j2` — no "4-6 NPCs", "~2 present", "1-2 nearby", "2-3 known", or `npc_count_override` language remains.

#### Step 4.2 — Remove `npc_count_override` from all code paths

**File:** `ccya/engine/seed.py` (line 167-169)

**What:** Remove `npc_count_override` from the template context dict. The key and its conditional logic are no longer used since the prompt no longer references it.

**Why:** This is dead code. The LLM now determines NPC count from narrative necessity.

**Validation:** `git grep npc_count_override` returns only matches in removed prompt sections.

**File:** `ccya/pack.py` (lines 193, 204)

**What:** Remove the `npc_count: int = 0` field from `PlayerOverrides` model and the associated comment on line 204.

**Validation:** `PlayerOverrides` no longer has `npc_count`.

**File:** `ccya/server/routes.py` (lines 403-407, 415)

**What:** Remove the `npc_count_raw` parsing and `npc_count` assignment from the `new_game` handler. Remove `npc_count=npc_count` from the `PlayerOverrides(...)` construction call.

**Validation:** The `new_game` handler no longer reads or passes `npc_count`.

**File:** `ccya/templates/_char_creation.html` (lines 7, 95-100)

**What:** Remove the hidden `npc_count` input and the +/- stepper UI for NPC count.

**Validation:** Character creation form no longer has NPC count controls.

**File:** `ccya/templates/index.html` (lines 926, 1520, 1522)

**What:** Remove `npc_count: 2` from the `charCreation()` Alpine.js component default, and remove the JS that reads the `npc_count` input value.

**Validation:** No references to `npc_count` in UI templates remain.

#### Step 4.3 — Update documentation

**File:** `docs/architecture/out-of-band.md` (line 73)

**What:** Change "validates any LLM-provided personality ids via `validate_and_resolve()` (logs WARNING for unknown ids, preserves as-is)" to "validates any LLM-provided personality ids via `validate_and_resolve()`; unknown ids fall back to `assign_personality()`".

**File:** `docs/architecture/step2a-scene.md` (line 44)

**What:** Update the NPC field requirements bullet to include `personality` as a mandatory field for named NPCs, with the tiered counts (named = 4 fields, unnamed = bio only).

**File:** `docs/repomap.md` (line 20)

**What:** Update the `seed.py` description: "post-parse hook validates LLM-assigned personality archetype ids; falls back to `ccya.personality.assign_personality()` for NPCs missing or having an invalid personality".

**File:** `docs/repomap.md` (line 64)

**What:** Update the `personality.py` description to note `assign_personality()` is fallback, not primary: "assign_personality(motivation, fear, npc_id) → NpcPersonality (engine fallback; LLM is primary); validates via validate_and_resolve()".

**File:** `docs/repomap.md` (lines 197, 252)

**What:** Review the historical notes about seed schema and extraction field requirements for accuracy after the prompt changes. Update if stale.

### Tests to write or update

No test changes (tests temporarily disabled during refactor).
