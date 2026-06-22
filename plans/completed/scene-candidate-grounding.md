# Scene Candidate Grounding Plan

## Purpose

Fix scene extractor's tendency to invent psychological effects instead of referencing existing compendium fields, and give it access to those fields for all presence levels (not just present).

## Problem Statement

Scene extractor receives compendium fields (motivation/fear/leverage/bond) only for `present` NPCs in the prompt. Even when present, it ignores these fields and invents its own effect text based on reading the narration. This produces effects that don't match the compendium ground truth (e.g., compendium says "fears: Being silenced by syndicates" but scene outputs "fears: panicking during flight").

## Constraints

- Prompt-only fixes for grounding (no engine changes for that).
- Template change for showing fields on all presence levels.
- No engine-level changes for candidate logging — already in `extraction.scene.output.candidate_npcs`.
- AGENTS.md mandates doc updates when prompt templates change.

## Non-goals

- No engine changes to how candidates are stored or logged.
- No changes to `build_npc_roster()` — it already includes all fields for all presence levels.
- No changes to `_filter_unnamed_personality()` — already working.

## Solution

1. Show motivation/fear/leverage/bond for ALL presence levels in `_npc_roster.j2` (currently only present). This gives scene access to psychological drivers for nearby/known NPCs, enabling it to reintroduce them based on existing fields.
2. Tighten `extract_scene_system.j2` — compendium fields are ground truth. Effects must directly reference existing fields, never invent new ones.
3. Verify candidates are already in events.jsonl (they are — under `extraction.scene.output.candidate_npcs`).

## Firm decisions

1. **Show psychological fields for all presence levels** — nearby/known NPCs may have motivations that drive them back into the scene. Scene should see these fields.
2. **Bond already shown for all** — line 9 of `_npc_roster.j2` already renders bond for all presence levels. Only motivation/fear/leverage/personality need to be unconditionally shown.
3. **Prompt grounding rule** — scene must write effects that directly reference compendium fields. "Anthony's fear of being silenced drives him to panic" not "Anthony is panicking."
4. **Candidates already logged** — `extraction.scene.output.candidate_npcs` is already in events.jsonl. No change needed.

## Risks, Ambiguities, and Blockers

- **Token bloat**: Showing fields for all presence levels increases prompt size. Mitigation: only show fields that exist (non-null), same as current behavior for present NPCs.
- **Scene may still invent**: Prompt tightening may not fully prevent invention. If so, a second pass with stricter language may be needed.
- **Bond for present NPCs**: Line 9 shows bond for all, line 10 shows motivation/fear/leverage only for present. After this change, bond will appear twice for present NPCs (line 9 + line 10's personality section). This is acceptable — bond is a separate concept from motivation/fear/leverage.

## Status

`completed`

## Phases

2 phases: (1) template change to show fields for all presence levels, (2) prompt tightening for grounding.

---

## Implementation — Phase 1: Show psychological fields for all presence levels

### Context files to load

- `ccya/prompts/sections/_npc_roster.j2` — template to modify
- `ccya/engine/extraction/scene.py` — pass `show_all_fields=True`

### Detailed steps

#### Step 1.1 — Add `show_all_fields` conditional to `_npc_roster.j2`

**File:** `ccya/prompts/sections/_npc_roster.j2`

**What:** Added `show_all_fields` conditional on line 10. When `True`, renders motivation/fear/leverage/personality for all presence levels. When `False` (default), renders only for present NPCs (existing behavior).

**Why:** Scene extractor needs access to psychological fields for nearby/known NPCs so it can:
- Reintroduce characters based on their existing motivations/fears even when not present
- Reference existing compendium fields rather than inventing new ones

**Validation:** Template renders correctly with `show_all_fields=True` (all fields shown) and `show_all_fields=False` (only present NPCs).

#### Step 1.2 — Pass `show_all_fields=True` in scene extractor

**File:** `ccya/engine/extraction/scene.py`

**What:** Added `"show_all_fields": True` to the template context in `_extract_scene_messages()`.

**Why:** Enables the `show_all_fields` branch in `_npc_roster.j2` for scene extractor prompts only.

---

## Implementation — Phase 2: Tighten prompt for grounding

### Context files to load

- `ccya/prompts/extract_scene_system.j2` — system prompt to modify

### Detailed steps

#### Step 2.1 — Add grounding rule to beat candidate selection section

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Added grounding rule and tightened effect rule in "Beat candidate selection" section:

- Added **Grounding rule:** "Effects must directly reference existing compendium fields. 'Anthony's fear of being silenced drives him to panic' not 'Anthony is panicking.' Never invent new psychological drivers — use what's in the roster."
- Tightened **Effect rule:** "One sentence. Observable behavioral pressure, not internal state. Always implies 'expect this to matter this turn.'"

**Why:** Scene currently reads narration and invents effects. The grounding rule tells it to use existing compendium fields as the source of truth, referencing them explicitly in the effect text.

---

## Documentation updates

- `docs/architecture/step2a-scene.md` — updated "Beat candidate selection" section to note that scene receives psychological fields for all presence levels, and effects must reference compendium fields as ground truth.
