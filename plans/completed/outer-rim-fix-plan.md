# Plan: Outer Rim Eval — Prompt + Guard Fixes

**Derived from:** `evals/findings/outer-rim-eval-2026-06-21.md`
**Source:** User review of findings 2026-06-21
**Date:** 2026-06-21

---

## Purpose

Fix 4 eval findings (issues #8, #11, #13) via prompt clarifications and one minimal Python guard. All fixes are prompt-only except §4a (npcs.py guard).

## Problem

The storyteller LLM omits `type` on threads, fires `arc_resolve` far too frequently, and the scene extractor occasionally emits personality fields for unnamed NPCs.

## Constraints

- Keep token bloat minimal — terse language, no verbose examples.
- Prompt-only fixes preferred; Python guards only where prompt alone is insufficient.
- No engine-level complexity for issues solvable with prompt guidance.

## Non-goals

- Group NPC alias-first naming (deferred)
- NPC auto-demote on location change (separate rework)
- `chapter_end` behavioral effect (no effect yet)
- Second-person narration (already fixed in prior session)

## Solution

Four changes across 5 files:
1. Schema examples in `storytell_system.j2` — add `type` to `thread_add`/`thread_update` examples
2. Arc resolution guidance in `storytell_system.j2` — tighten cadence language
3. Personality guard in `npcs.py` — block non-bio fields on unnamed NPCs
4. Scene extractor prompt in `extract_scene_system.j2` — reinforce unnamed NPC constraint
5. Documentation updates to `docs/architecture/` and `docs/repomap.md`

## Firm decisions

- `type` stays optional in Pydantic models (`ArcThread.type`, `ThreadUpdate.type` are `Literal[...] | None = None`). Fix is prompt-only: make it clear in Schema examples and guidance text.
- Arc resolution fix is prompt-only — no Python-level cadence enforcement.
- Personality guard in `npcs.py` is belt-and-suspenders: the existing personality assignment (line 270) already skips unnamed NPCs; this blocks motivation/fear/leverage/bond too.

## Risks

- **maintainability:** Schema examples in `storytell_system.j2` are illustrative, not enforced. If the LLM ignores them again, the fix is ineffective.
- **maintainability:** Arc resolution cadence is a behavioral target, not a hard constraint. Prompt guidance may not change LLM behavior.

## Status

- §1 (second person): DONE — prior session
- §2 (thread type): PENDING
- §3 (arc resolution): PENDING
- §4 (unnamed NPC guard): PENDING
- §5 (docs): PENDING

---

## Phase 01: Thread type required in Schema

**Context files:**
- `ccya/prompts/storytell_system.j2` (lines 7–21: Schema section)
- `ccya/models/state.py:26-31` (ArcThread — `type: Literal[...] | None = None`)
- `ccya/models/state.py:153-157` (ThreadUpdate — `type: Literal[...] | None = None`)

**Steps:**

### 1.1 Add `type` to Schema examples

**File:** `ccya/prompts/storytell_system.j2`
**What:** In the Schema JSON block (lines 11–13), add `"type": "threat"` to `thread_update` and `thread_add` examples.
**Why:** Schema examples are the LLM's primary reference for required fields. Current examples omit `type`, so the LLM treats it as optional.
**Validation:** Schema examples now show `type` on both `thread_add` and `thread_update`.

### 1.2 Add required-type directive

**File:** `ccya/prompts/storytell_system.j2`
**What:** After the Type list (line 37), add one line: "REQUIRED — every `thread_add` and `thread_update` must include exactly one type from the list above."
**Why:** Reinforces that `type` is not optional despite being `| None` in the model.
**Validation:** Line exists in rendered prompt.

---

## Phase 02: Arc resolution cadence

**Context files:**
- `ccya/prompts/storytell_system.j2` (lines 64–74: Arc resolution section)

**Steps:**

### 2.1 Tighten arc resolution preamble

**File:** `ccya/prompts/storytell_system.j2`
**What:** Replace line 66 ("`arc_resolve` ends the current narrative chapter. Emit when: ...") with: "Emit **only** when the narrative chapter genuinely ends — a decisive win, a fundamental shift, or 8+ turns on the same goal. Target cadence: 8–15 turns."
**Why:** Current language ("Emit when:") reads permissive. "Emit **only** when:" reads restrictive.
**Validation:** Line 66 now reads "Emit **only** when..."

### 2.2 Add contrasting example

**File:** `ccya/prompts/storytell_system.j2`
**What:** After line 70 (CRITICAL: Do NOT emit empty `arc_resolve`), add: "WRONG: `arc_resolve` with unchanged `visible_goal` (no-op). RIGHT: `arc_resolve` introduces a new goal or `chapter_end: true` keeps the current one."
**Why:** The LLM fires `arc_resolve` with the same goal (T4, T6, T15, T31). A concrete wrong/right example is the most direct correction.
**Validation:** Example exists after line 70.

---

## Phase 03: Unnamed NPC personality guard

**Context files:**
- `ccya/state/npcs.py:262-288` (field assignment in `apply_npc_scene_management`)
- `ccya/prompts/extract_scene_system.j2:84` (existing unnamed NPC rule)

**Steps:**

### 3.1 Block non-bio fields on unnamed NPCs

**File:** `ccya/state/npcs.py`
**What:** After line 269 (`if comp_upd.bond is not None:`), add a guard before line 270 (personality assignment):
```python
            # Guard: unnamed NPCs (name matches an alias) get bio only.
            _is_unnamed = (
                comp_upd.name
                and comp_upd.aliases
                and comp_upd.name.lower().strip() in {a.lower().strip() for a in comp_upd.aliases}
            )
            if _is_unnamed:
                comp_upd = comp_upd.model_copy(update={
                    "motivation": None,
                    "fear": None,
                    "leverage": None,
                    "bond": None,
                    "personality": None,
                })
```
**Why:** Belt-and-suspenders. The existing personality assignment (line 270) already skips unnamed NPCs, but motivation/fear/leverage/bond are set unconditionally (lines 262-269). This blocks all non-bio fields on unnamed entries.
**Validation:** Unnamed NPC entries in compendium have no motivation/fear/leverage/bond/personality fields.

### 3.2 Reinforce unnamed NPC rule in scene prompt

**File:** `ccya/prompts/extract_scene_system.j2`
**What:** After line 84 ("Unnamed NPCs: bio only. Do NOT add personality..."), add: "The engine rejects personality fields on unnamed NPCs — treat this as a hard constraint."
**Why:** Line 84 already states the rule but the LLM ignores it. Adding "engine rejects" signals this is enforced, not optional.
**Validation:** Line 85 now exists with enforcement language.

---

## Phase 04: Documentation updates

**Context files:**
- `docs/architecture/` — pipeline/data shape docs
- `docs/repomap.md` — module boundaries/APIs

**Steps:**

### 4.1 Update storytell prompt docs

**File:** `docs/architecture/step2c-storytell.md` (or relevant doc)
**What:** Update Schema section to reflect that `type` is now required in prompt guidance (even though model field is `| None`).
**Why:** AGENTS.md mandates doc updates when prompt templates change.
**Validation:** Schema docs match current prompt.

### 4.2 Update scene extractor docs

**File:** `docs/architecture/step2a-scene.md` (or relevant doc)
**What:** Note that unnamed NPCs are now blocked at engine level (npcs.py guard) in addition to prompt guidance.
**Why:** Data shape docs should reflect engine behavior.
**Validation:** Scene extractor docs reflect engine guard.

---

## Verification

After all phases:
1. `make check` — lint + typecheck must pass
2. Render storytell prompt with `ev.py prompt-eval dump` — verify Schema includes `type`
3. No behavioral changes expected from prompt-only fixes; verify by re-running eval scenario
