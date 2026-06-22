# Seed Hint Wiring + 2-Item Removal

## Purpose

Make character creation hints authoritative in seed generation, remove the 2-item inventory requirement, and clean up dead fields in the `PlayerOverrides` / routes pipeline.

## Problem Statement

Character creation hints reach the seed LLM prompt as "soft — honor when compatible with canon" guidance, which the LLM routinely ignores. Additionally, the `quest_hints` field is dead code (read from form, silently dropped by Pydantic), `arc_hints` is sent by the JS form but never read by routes.py, and `drive_hint` has no form source at all. The 2-item inventory tie-to-top-skills requirement in the seed prompt creates items that confuse inventory behavior.

## Constraints

- No backward compatibility required — dead fields can be removed outright.
- This is a one-time setup concern; seed state is not re-referenced after turn 0.
- Prompt changes should prioritize player intent over random generation.

## Non-goals

- Adding seed-to-prompt pipeline changes for later turns (seed is setup-only, all downstream state derives from it).
- Addressing #9b (unearned inventory) separately — removing the 2-item requirement should fix this naturally.
- Changing `required_inventory_kinds` in `Constraints` or scenario YAML files — that's a separate pack-level concept.
- Adding a `drive_hint` form field to the char creation UI — `drive_hint` will be wired on the Python side (accept from form data, default empty) so it's connectable later without a UI change.

## Solution

Strengthen the `player_overrides` prompt language from soft/optional to authoritative; remove the 2-item inventory rule from the seed prompt; wire `arc_hints` and `drive_hint` through routes.py; remove dead `quest_hints` from routes.py and its stale reference in docs; update the `PlayerOverrides` docstring to reflect the new authority level.

## Firm decisions

1. Player overrides are **authoritative** for PC identity (name, stats, concept, drive) and **strongly preferred** for arc/NPC/location direction. The prompt will say this explicitly.
2. The 2-item inventory rule is removed entirely from `generate_seed_system.j2`. No code-level enforcement exists — prompt-only.
3. `quest_hints` is removed from routes.py and all references. It has no model field and no template usage.
4. `arc_hints` is already sent by the char creation JS but not read by routes.py — wire it through.
5. `drive_hint` is added to routes.py form reading (defaulting to empty string). No UI field added yet.
6. `location_hints` stays in `PlayerOverrides` and routes.py even though the JS form doesn't send it currently — it's not dead code, it's a pre-wired field that could be used by other clients or future UI. No change needed.

## Risks, Ambiguities, and Blockers

- Strengthening override language may cause the LLM to follow bad/hallucinated player hints (e.g., "make me a god"). The existing canon clause in the system prompt ("World facts are non-negotiable canon") should counterbalance, and the prompt language should stay scoped to *character identity and direction*, not world-breaking.
- Removing the 2-item rule may lead to more generic starter inventories. The remaining inventory rules (appropriate to opening scene, firearms always paired with ammo, no items for untrained skills, realistic quantities) plus `required_inventory_kinds` from packs should provide sufficient structure.

## Status

`completed`

## Phases

2 phases: one for prompt/template changes, one for Python plumbing changes.

---

## Implementation — Phase 1: Prompt changes

### Context files to load

- `ccya/prompts/generate_seed_system.j2`
- `ccya/prompts/generate_seed_user.j2`

### Detailed steps

#### Step 1.1 — Remove 2-item inventory rule from seed system prompt

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Remove lines 133-134 (the "**At least 2 items must be directly tied to the PC's strongest skills**" rule and its example) from the `## inventory — Starter Inventory Rules` section. Also update line 52, which currently reads:

```
5. **Inventory**: Items tied to PC's top skills (existing rule unchanged)
```

Change to:

```
5. **Inventory**: Items appropriate to the opening scene and PC concept
```

**Why:** The 2-item rule forces the LLM to create skill-tied items that often mismatch the character concept or opening scene, confusing inventory. Removing it lets the LLM generate items appropriate to the PC concept instead.

**Validation:** Grep `generate_seed_system.j2` for "2 items" and "top 2 by value" — both should be gone. Grep for "top skills" — no matches. Line 52 reference updated.

#### Step 1.2 — Strengthen player_overrides language in seed system prompt

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Change line 5 from:

```
- Player overrides (if any) are soft requests — honor when compatible with canon; silently ignore conflicts.
```

To:

```
- Player overrides are authoritative for PC identity (name, stats, concept, drive) and strongly preferred for arc direction, NPCs, and location. Honor them unless they directly contradict world facts or canon. If a player specifies a character concept, build around it — don't generate a contrasting concept.
```

**Why:** The current "soft" language lets the LLM disregard player hints. The new language makes PC identity authoritative and other hints strongly preferred with a clear override condition (direct contradiction with world facts).

**Validation:** Read the updated line — should contain "authoritative" and "strongly preferred", should not contain "soft" or "silently ignore".

#### Step 1.3 — Strengthen player_overrides section header in seed user prompt

**File:** `ccya/prompts/generate_seed_user.j2`

**What:** Change line 34 from:

```
## player_overrides (soft — honor when compatible with canon)
```

To:

```
## player_overrides (authoritative for PC identity; strongly preferred otherwise — only override on canon conflict)
```

**Why:** The user prompt section header reinforces the system prompt authority change. The header is what the LLM sees most directly in context.

**Validation:** Read updated line — should contain "authoritative" and "strongly preferred", should not contain "soft".

### Tests to write or update

None — tests are temporarily removed during refactor per AGENTS.md.

---

## Implementation — Phase 2: Python plumbing changes

### Context files to load

- `ccya/server/routes.py` (lines 254-290)
- `ccya/pack.py` (lines 207-231, `PlayerOverrides` class)
- `ccya/engine/seed.py` (lines 134-168, `_build_generate_seed_messages`)

### Detailed steps

#### Step 2.1 — Remove `quest_hints` from routes.py

**File:** `ccya/server/routes.py`

**What:** Remove line 260 (`quest_hints = str(form.get("quest_hints", "")).strip()`) and remove `quest_hints=quest_hints` from the `PlayerOverrides(...)` call on line 273.

**Why:** `quest_hints` is dead code — `PlayerOverrides` has no `quest_hints` field, so Pydantic silently drops it. No template sends it. No code reads it.

**Validation:** Grep `routes.py` for `quest_hints` — zero matches.

#### Step 2.2 — Wire `arc_hints` through routes.py

**File:** `ccya/server/routes.py`

**What:** Add `arc_hints = str(form.get("arc_hints", "")).strip()` after the `npc_hints` line (~line 258). Add `drive_hint = str(form.get("drive_hint", "")).strip()` after `arc_hints`. Add both `arc_hints=arc_hints` and `drive_hint=drive_hint` to the `PlayerOverrides(...)` call.

The `PlayerOverrides` call becomes:

```python
overrides = PlayerOverrides(
    pc_hints=pc_hints,
    npc_hints=npc_hints,
    location_hints=location_hints,
    arc_hints=arc_hints,
    drive_hint=drive_hint,
    free_form=free_form,
    npc_count=npc_count,
)
```

**Why:** The char creation JS already sends `arc_hints` in the POST body (index.html line 1086), but routes.py doesn't read it. `drive_hint` has no JS form field yet, but wiring it on the Python side makes it connectable without a code change later.

**Validation:** `arc_hints` and `drive_hint` appear in routes.py form reading and in the `PlayerOverrides` constructor. The `quest_hints` line and kwarg are gone.

#### Step 2.3 — Update `PlayerOverrides` docstring

**File:** `ccya/pack.py`

**What:** Update the `PlayerOverrides` class docstring (lines 208-210) from:

```
"""Optional player-supplied tweaks at New Game time. All fields default empty.
Engine injects into generate_seed prompt as soft guidance — Pydantic constraints
and world.md canon win on conflict."""
```

To:

```
"""Optional player-supplied direction at New Game time. All fields default empty.
Authoritative for PC identity (name, stats, concept, drive); strongly preferred for
arc, NPCs, and location. Only override on direct canon conflict."""
```

**Why:** The docstring should match the new authority level established in the prompts. The old "soft guidance" language is now inaccurate.

**Validation:** Read updated docstring — should contain "Authoritative" and "strongly preferred", should not contain "soft".

#### Step 2.4 — Update `quest_hints` references in architecture docs

**File:** `docs/architecture/out-of-band.md`

**What:** Update the three Mermaid diagram node labels that reference `quest_hints`:
- Line 11: replace `quest_hints` with `arc_hints` in the FORM node label
- Line 20: replace `quest_hints` with `arc_hints, drive_hint` in the DS node label
- Line 49: replace `quest_hints` with `arc_hints, drive_hint` in the G3 node label

All three are within `<br>`-separated field lists in Mermaid flowchart text blocks.

**Why:** These architecture diagrams describe the current data flow. After removing `quest_hints` from routes.py and `PlayerOverrides`, the docs would be stale — they'd reference a field that no longer exists. Updating them keeps the documentation consistent with the implementation.

**Validation:** Grep `docs/architecture/out-of-band.md` for `quest_hints` — zero matches.

### Tests to write or update

None — tests are temporarily removed during refactor per AGENTS.md.

---

## Verification

After both phases:

1. Run `make check` (lint + typecheck) — must pass.
2. Start a game via the UI — confirm `arc_hints` from the form reaches `generate_seed_user.j2` rendering (check via server logs or by inspecting the prompt in events.jsonl).
3. Confirm no `quest_hints` references remain in `routes.py`, `pack.py`, or prompt templates.
4. Confirm the 2-item rule text no longer appears in `generate_seed_system.j2`.
5. Confirm `player_overrides` language in both prompts says "authoritative" not "soft".