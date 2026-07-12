# Arc Thread System Cleanup Plan

## Purpose

Fix type annotation correctness, fully remove dead `thematic_question` field from all source code and prompts, clean up stale JSON schema fields in prompt templates, and update design docs to match actual behavior.

## Problem Statement

Three independent issues degrade system quality: (1) `ArcThread.progress` has a runtime-correct coercion validator but an incorrect type annotation (`str` instead of `list[str]`) that will cause mypy errors; (2) `thematic_question` was removed from the CampaignArc model and runtime prompts but still exists in seed generation, state loading, narrator context, architecture docs, and debug tooling — dead code consuming tokens and confusing developers; (3) the storyteller prompt's JSON schema example contains stale fields (`tags`, `key`) that no longer exist on ArcThread.

## Constraints

- `_merge_arc_update` behavior unchanged — still replaces threads[] unconditionally.
- Pipeline order fixed: narrator → extraction → arc director. No reordering.
- Backwards compatibility not required for model shape changes (design constraint #16).
- Tests are present and must be updated alongside source changes.

## Non-goals

- Behavioral changes to thread lifecycle, arc resolution, or urgency decay — all already implemented correctly per the design doc.
- `_merge_arc_update` refactoring — acknowledged as fragile but acceptable per design constraints.
- Adding new features or prompt guidance — only cleanup of existing issues.

## Solution

Three phases: (1) fix ArcThread.progress type annotation and update affected tests; (2) remove thematic_question from all source code, prompts, state loader, seed generation, narrator context, architecture docs, and debug tooling in one sweep since they share the same concern; (3) clean up stale JSON schema fields (`tags`, `key`) in storytell_system.j2. Each phase independently executable with clear verification steps.

## Firm decisions

1. `ArcThread.progress` type annotation: change from `str = ""` to `list[str] = []`. The wrap validator already coerces strings → lists; this aligns the annotation with runtime behavior.
2. `thematic_question`: fully removed everywhere — model, state loader, seed prompts (system + user), narrator context builder, architecture docs, repomap, ev debug script. No residual references remain.
3. JSON schema in storytell_system.j2: remove `"tags": [], "key": "subject_action"` from the thread_add example. These fields never existed on ArcThread and are stale from a previous model shape.
4. Design doc text corrections for successor arc behavior (lines 34, 193) — clarify that scene-scoped threads survive arc resolution while arc-scoped threads do not carry forward.

## Risks, Ambiguities, and Blockers

- **Test coverage**: Tests reference `thematic_question` in conftest.py:205 and test_schema.py:144/157/163/289/364/573. All must be updated or tests will fail with AttributeError on CampaignArc model validation (field no longer exists).
- **Seed generation**: The seed LLM has been generating `thematic_question` for all existing games. After removal, the first post-deployment seeds won't include it — this is correct but means any external system reading that field from state will see it absent. No migration needed since backwards compat is not required.
- **Architecture docs**: step2c-progress.md has detailed flowcharts referencing thematic_question inheritance during arc resolution. These describe old behavior and must be updated or removed entirely (the "inherited thematic_question" concept no longer exists).

## Status
`open`

## Phases

3 phases: fix type annotation, remove thematic_question everywhere, clean up stale JSON schema fields. Each independently executable with clear verification steps.

---

# Implementation — Phase 01: Fix ArcThread.progress type annotation

### Context files to load
- `ccya/models.py` (lines 29-45)
- `tests/test_schema.py` (search for progress-related tests)
- `tests/conftest.py` (search for progress-related fixtures)

### Detailed steps

#### Step 01.1 — Update ArcThread.progress type annotation

**File:** `ccya/models.py`

**What:** Change line 35 from:
```python
progress: str = ""
```
to:
```python
progress: list[str] = []
```

Also update the `_coerce_progress` validator (lines 40-45): since the type annotation now says `list[str]`, the wrap validator should handle both old string values from pre-change saves AND new list values. The current logic is correct — if v is a str, return `[v]`; otherwise call handler(v). No change needed to validator body.

**Why:** The runtime behavior (produced by the wrap validator) returns `list[str]`, but the type annotation says `str`. This mismatch will cause mypy errors and confuse developers reading the model definition. Aligning them eliminates the ticking type correctness bug identified in the review.

**Validation:** Run:
```bash
python3 -c "from ccya.models import ArcThread; t = ArcThread(id='test', summary='s'); print(type(t.progress), t.progress)"
# Should output: <class 'list'> []
```

Verify with mypy if available: `make typecheck` or equivalent.

### Tests to write or update

- **`tests/test_schema.py`**: Search for any test that creates an ArcThread with a string progress value (e.g., `"progress": "some text"`). These should still pass because the wrap validator coerces strings → lists, but verify they exist and confirm behavior.
- **`tests/conftest.py:205`**: If this fixture sets `progress`, ensure it's compatible with list type or update accordingly.

---

# Implementation — Phase 02: Remove thematic_question everywhere

### Context files to load
All of the following must be loaded together since they share one concern (thematic_question removal):
- `ccya/state/io.py` (lines 74-82)
- `ccya/engine/narrate.py` (line 54, and arc context building lines 48-70)
- `ccya/prompts/generate_seed_system.j2` (lines 26, 39, 42, 61, 102, 107, 195)
- `ccya/prompts/generate_seed_user.j2` (line 84)
- `docs/architecture/step1-narrate.md` (line 45)
- `docs/architecture/step2c-progress.md` (lines 141, 178, 194, 270, 279)
- `docs/architecture/out-of-band.md` (line 50)
- `docs/repomap.md` (lines 181, 246, 252)
- `scripts/debug/ev.py` (lines 874, 969 — debug tool that reads state directly)

### Detailed steps

#### Step 02.1 — Remove thematic_question from state loader default arc dict

**File:** `ccya/state/io.py`

**What:** Delete line 76: `"thematic_question": "",`

The arc default dict (lines 74-82) becomes:
```python
"arc": {
    "visible_goal": "",
    "goal_context": "",
    "threads": [],
    "completed_threads": [],
    "resolution": None,
    "last_thread_created_turn": 0,
},
```

**Why:** The CampaignArc model no longer has this field. New state dicts should not include it. Old saves with the key will still load (Pydantic ignores extra keys), but new initialization won't produce dead data.

**Validation:** `grep -n "thematic_question" ccya/state/io.py` returns nothing.

#### Step 02.2 — Remove thematic_question from narrator arc context builder

**File:** `ccya/engine/narrate.py`

**What:** Delete line 54: `"thematic_question": arc.get("thematic_question", ""),`

The current_arc_ctx dict (lines 52-70) no longer includes this key. Since `_arc.j2` doesn't render it, passing it is dead data that wastes context tokens.

**Why:** The field was removed from the model and runtime prompts but still passed through narrator context. This wastes ~1 token per turn in system+user prompt duplication with zero behavioral value.

**Validation:** `grep -n "thematic_question" ccya/engine/narrate.py` returns nothing.

#### Step 02.3 — Remove thematic_question from seed generation prompts (system)

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Four changes:
1. Line 26: Change "This DIRECTLY GENERATES your thematic_question" → remove this clause entirely or rephrase to not mention thematic_question. The moral_pressure section should still exist but no longer instructs generation of a thematic_question field.
2. Lines 39, 42: Remove `thematic_question` from the campaign arc bullet point and its sub-bullet. Line 39 becomes "Campaign arc (visible_goal, goal_context, threads):" with only visible_goal, goal_context, and threads listed as sub-items.
3. Line 61: Delete or reword the cross-field consistency rule about moral_pressure → thematic_question mapping. Since thematic_question no longer exists, this constraint is meaningless. Keep the moral_pressure section but remove the directive to generate a question from it.
4. Lines 102, 107: Remove `thematic_question` from both TypeScript output schema arc definitions (lines 102 and 107). The arc type becomes `{visible_goal: string, goal_context: string, threads: ArcThread[], completed_threads: ArcThread[]}` in both places.
5. Line 195: Delete the `thematic_question` bullet point from Campaign Arc Generation section.

**Why:** Seed generation prompts are the primary source of thematic_question data flowing into state. Removing it here prevents new seeds from generating dead fields and saves tokens per seed-generation LLM call (~30-40 tokens).

**Validation:** `grep -n "thematic_question" ccya/prompts/generate_seed_system.j2` returns nothing.

#### Step 02.4 — Remove thematic_question from seed generation prompts (user)

**File:** `ccya/prompts/generate_seed_user.j2`

**What:** Line 84: Change the sentence that says "moral pressure creates immediate ethical tension that DIRECTLY GENERATES thematic_question" → rephrase to say moral pressure shapes tone and stakes without mentioning thematic_question. The full line becomes something like: "These four elements shape your generation. The situation archetype defines the opening moment's pressure type; arc category shapes longer-term narrative direction with escalation potential; character dynamic places the PC within power structures and relationships; moral pressure creates immediate ethical tension that informs the campaign arc."

**Why:** Same as Step 02.3 — prevents thematic_question from being generated during seed time via user prompt guidance.

**Validation:** `grep -n "thematic_question" ccya/prompts/generate_seed_user.j2` returns nothing.

#### Step 02.5 — Update architecture docs to remove thematic_question references

**Files:**
- `docs/architecture/step1-narrate.md:45` — Delete the bullet point about thematic_question or reword it if the concept has value elsewhere (unlikely since design says removed).
- `docs/architecture/step2c-progress.md` — Multiple changes:
  - Line 141: Remove `thematic_question: str` from CampaignArc field list.
  - Lines 178, 194, 270, 279: Update flowchart and text to remove "inherited thematic_question" concept from arc resolution description. The successor arc now has only visible_goal + goal_context (no thematic_question inheritance).
- `docs/architecture/out-of-band.md:50` — Remove thematic_question from the CampaignArc field list in the Mermaid diagram.

**Why:** Architecture docs are referenced during development and debugging. Stale references mislead developers about what fields exist on models and how arc resolution works.

**Validation:** `grep -rn "thematic_question" docs/architecture/` returns nothing.

#### Step 02.6 — Update repomap to remove thematic_question references

**File:** `docs/repomap.md`

**What:** Three changes:
1. Line 181: Remove `/ArcResolution with resolution/visible_goal/goal_context/thematic_question/thread_directives/` → keep only the fields that exist on ArcResolution (resolution, visible_goal, goal_context, drop_threads, new_threads). Note: thread_directives was already removed in a previous cleanup — verify this is accurate.
2. Line 246: Remove `thematic_question: str # emotional register — never stated directly in narration` from the CampaignArc field list.
3. Line 252: Update resolved_arcs entry description to remove thematic_question reference.

**Why:** Repomap documents module boundaries, public APIs, and model shapes for developers. Stale references mislead about what fields exist on models.

**Validation:** `grep -n "thematic_question" docs/repomap.md` returns nothing.

#### Step 02.7 — Remove thematic_question from ev debug script

**File:** `scripts/debug/ev.py`

**What:** Two changes:
1. Line 874: Remove `"thematic_question"` from the tuple of arc keys checked for non-empty state. The line becomes: `if any(arc.get(k) for k in ("visible_goal", "threads", "completed_threads", "hidden_truths", "discovered_truths")):`
2. Line 969: Delete or comment out the line that reads thematic_question from arc dict (`question = arc.get("thematic_question") or ""`). If this value is used elsewhere in ev.py for display, remove those references too — check what `question` variable feeds into next.

**Why:** The ev script reads state directly from events.jsonl and displays it. Stale thematic_question references produce dead output when inspecting old saves with the field present. Clean removal keeps debug tooling aligned with current model shape.

**Validation:** Run: `grep -n "thematic_question" scripts/debug/ev.py` returns nothing. Also check that no other variable in ev.py depends on the removed `question` assignment at line 969 — search for uses of `question` near that line to confirm it's safe to remove or update.

### Tests to write or update

- **`tests/conftest.py:205`**: Delete `"thematic_question": ""` from the CampaignArc fixture dict.
- **`tests/test_schema.py:144, 157, 163, 289, 364, 573`**: All references to thematic_question in test assertions and fixtures must be removed or updated. Run `grep -n "thematic_question" tests/` to find all occurrences before editing.
- **`tests/test_render.py:222, 232, 252`**: Arc rendering tests that check for thematic_question output — update assertions since `_arc.j2` no longer renders it.

---

# Implementation — Phase 03: Clean up stale JSON schema fields in storytell_system.j2

### Context files to load
- `ccya/prompts/storytell_system.j2` (line 14)
- `ccya/models.py` (ArcThread model, lines 29-45 — for reference of actual field names)

### Detailed steps

#### Step 03.1 — Remove tags and key from thread_add JSON schema example

**File:** `ccya/prompts/storytell_system.j2`

**What:** Change line 14 from:
```json
"thread_add": {"id": "snake_case_id", "summary": "story tension description", "scope": "arc", "urgency": "normal", "tags": [], "key": "subject_action"},
```
to:
```json
"thread_add": {"id": "snake_case_id", "summary": "story tension description", "scope": "arc", "urgency": "normal"},
```

**Why:** The ArcThread model has no `tags` or `key` fields. These are stale from a previous model shape that was never cleaned up from the prompt template's JSON schema example. The LLM will emit these extra keys and Pydantic will silently ignore them (extra keys pass through), but this wastes tokens in the system prompt (~20 chars × N turns) and may confuse the LLM about what fields are valid on ArcThread.

**Validation:** `grep -n '"tags"' ccya/prompts/storytell_system.j2` returns nothing for thread_add context. The rest of the file should be unchanged.

### Tests to write or update

- No test changes needed — this is a prompt template change with no behavioral impact on model validation (Pydantic already ignores extra keys). Verify with `make check` if available.

---

# Implementation — Design doc text corrections (not a separate phase)

These are minor text-only fixes to the design document that should be applied alongside Phase 02 since they share one concern: correcting factual errors in documentation.

**File:** `docs/design/arc-thread-system-design.md`

#### Step D1 — Correct successor arc behavior description

**What:** Three locations need fixing (all say "empty threads[]" when source carries forward scene-scoped threads):
- Line 34: Change "creates a successor arc with empty `threads[]`. Scene-scoped threads are unaffected." → "creates a successor arc carrying forward surviving scene-scoped threads plus any new_threads from the resolution. Arc-scoped threads do not carry forward — they are auto-resolved with state 'superseded'."
- Line 193: Change "Successor arc starts with empty `threads[]`" → "Successor arc carries forward surviving scene-scoped threads; arc-scoped threads are closed with 'superseded' state and must be re-created if still relevant."

**Why:** The design doc text contradicts the source code at turn.py:287-291. This was identified as a FATAL error in the review — the prompt template itself (line 79) has the correct description, so this is purely a documentation correction with no behavioral impact.

#### Step D2 — Update "What Is Removed" section

**What:** Line 186: The claim that `_merge_arc_update` was removed as the sole visible_goal update mechanism should be clarified to say it's still used for arc_resolve and thread_resolutions paths, but `goal_update` now applies via direct dict assignment outside of `_merge_arc_update`. This is already stated in constraints (line 15) so just ensure consistency.

**Validation:** No behavioral change — documentation accuracy only.
