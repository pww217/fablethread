# Prompt Testing and Schema Discipline — Design Document

## Purpose

This document sets the north star for three related quality concerns that must be resolved **after the narration simplification work lands**: prompt render coverage, schema boundary discipline, and development workflow. It is a design reference, not an implementation plan.

> **Scope change:** The existing test suite (`tests/`) has been deleted. This document now describes how to rebuild it correctly against the simplified architecture, not how to patch the old suite. Do not attempt to restore deleted tests. Build the new suite from scratch using the layer model in Section 4 and the contracts defined in `plans/narration-simplification-design.md`.

Implementing LLMs should derive specific steps from the vision here, the constraints in AGENTS.md, and the narration simplification design doc.

---

## Section 1 — What Was There and Why It Was Removed

The repo had meaningful test coverage at the smoke and integration level (`test_engine_smoke.py`, `test_engine_pipeline.py`, `test_turn.py`) and some narrow prompt-level coverage (`test_prompts.py`, `test_extract_progress_template.py`, `test_prompt_audit.py`). That suite was deleted because it encoded the pre-simplification architecture as invariants. Agents spending time patching those tests during simplification work were doing negative work — cementing behavior under removal.

The replacement suite should be built once the simplified architecture is stable. It should be smaller, better organized, and test contracts rather than implementation details.

---

## Section 2 — Prompt Render Coverage

### Vision

Every prompt template that touches the narration/extraction pipeline should have direct render tests that assert the presence and omission of the sections that drive story mechanics. These tests are not golden snapshots of full prompt text — they assert structural contracts: specific labeled blocks appear when their context data is populated, and are absent when it is not.

Tests should be organized around the boundary contracts in `narration-simplification-design.md`: `PacingContext` renders as a single directive block; active threads appear as the canonical thread list; `pending_gm_beat` appears only when populated; and removed fields (`stakes`, `beat_disposition`, `narrative_velocity`, `deescalate`) must not appear anywhere in any prompt.

### What This Looks Like in Practice

A prompt render test for Progress Extract takes a minimal synthetic context, renders the template directly via Jinja, and makes a handful of targeted string assertions. It does not mock LLM responses or run the full engine. It is fast, isolated, and deterministic.

One additional integrated render test is appropriate: a realistic turn-7-style context rendered through the full prompt builder (not the template directly), asserting that the assembled prompt contains the right blocks in the right relationship. This one test exercises the builder-to-template boundary end-to-end without requiring an LLM.

### Scope

- `extract_progress_user.j2` — primary target; most complexity lives here
- `extract_narrate_user.j2` — secondary target for directive and beat rendering
- `extract_rules_*.j2` — low priority; only if the stakes removal creates a test gap
- Scene and State Extract templates — not in scope; they are not changing

### North Star Test Properties

- Test failure message should name the missing or unexpected section precisely
- Tests should survive whitespace-only template reformatting
- Tests should fail when a field is removed from context but not from the template
- Tests should fail when a field is added to the template but not to context assembly

---

## Section 3 — Schema Boundary Discipline

### Vision

The data that crosses from Python into a prompt, and the data that comes back from an extraction LLM into Python, should be typed and validated at the boundary — not buried inside dict construction. A future developer reading `turn.py` should be able to find one place where the prompt context is assembled, typed, and handed off to the template renderer.

This does not mean over-engineering typed models for every internal helper. It means the public boundary — the object handed to `template.render()` — is always a validated, typed model. Pydantic models already used throughout the codebase are the right tool.

### The Key Boundary Objects

Two boundaries matter most:

**Prompt-in:** The context dict passed to `template.render()` for Narrator and Progress Extract. This should be the `model_dump()` of a typed model, not an ad hoc dict assembled inline. The model for Progress should match the fields described in `narration-simplification-design.md` — no more, no less.

**Prompt-out:** The Pydantic models already used for extraction results (`ProgressExtractResult`, etc.) are the right shape. The simplification removes several fields from these models. Once removed, they must be removed completely — no optional shim fields left for backward compatibility.

### What Boundary Discipline Rules Out

- Conditional dict mutations inside prompt builder functions (`if deescalate: context['deescalate'] = ...`)
- Fields that exist in a template but are not in the typed context model
- Fields that exist in the typed model but are never rendered in the template
- Free-form string fields whose semantics are not validated

---

## Section 4 — Test Coverage Strategy

### Layer Model

Test coverage for the engine should be three layers with distinct purposes:

**Layer 1 — Schema tests**: Validate that typed boundary models accept valid inputs, reject invalid inputs, and default optional fields correctly. Fast, no I/O, no templates. Purpose: catch schema drift at definition time. One file: `tests/test_schema.py`.

**Layer 2 — Render tests**: Render Jinja templates with synthetic context and assert structural properties of the output. No LLM, no engine. Purpose: catch prompt contract drift at template time. One file: `tests/test_render.py`.

**Layer 3 — Smoke tests**: Run the full engine pipeline with `FakeLLM` and assert high-level pipeline properties. Purpose: catch wiring mistakes and regression at the pipeline level. One file: `tests/test_smoke.py`.

Build in this order. Do not write Layer 3 until Layers 1 and 2 exist — the smoke tests are the most expensive to write and maintain and provide the least signal per line.

### What Should Not Happen

- Golden-output tests that snapshot the full text of a rendered prompt
- Tests that use `FakeLLM` to validate prompt rendering — render tests render templates directly
- Test files that mix schema tests, render tests, and smoke tests

### Key Invariants Worth Preserving From the Old Suite

These behavioral contracts were in the deleted tests and are worth encoding in the new suite:

- `_validate_instruction_quality` nullifies a GMBeat under 40 chars or starting with a filler prefix
- Momentum is clamped to `[-3, +3]`
- PC conditions cap at 5, FIFO eviction
- `inventory_remove` rejects IDs not present in state
- Cross-turn dedup on `recent_events`
- NPC scene cap at 8

---

## Section 5 — Development Workflow

### Vision

Engine changes should land through PRs even in a solo project: PRs create a diff reviewable by a planning agent in a future session, force commit discipline that makes `git bisect` useful, and record intent alongside change.

### Branch Naming

- `design/` — design documents
- `plan/` — plan documents
- `feat/` — feature implementation
- `fix/` — bug fixes
- `chore/` — tooling, docs, cleanup

### PR Size

A PR should represent one coherent, reviewable concern. The narration simplification work should be broken into at minimum:

1. Schema changes (`StoryThread`, `PacingContext`, `ProgressExtractResult` model changes)
2. Python logic changes (pacing context builder, thread signal application)
3. Template changes (Progress and Narrate templates)
4. Test additions (Layers 1–3 in order)

### Merge Discipline

`make check` passes before merge. `make test` passes before merge once the new test suite exists. Until then, `make check` alone is the gate.

---

## Section 6 — Sequencing

These concerns are sequenced, not parallel:

1. **Narration simplification lands first** — schema and template changes per `narration-simplification-design.md`
2. **Schema boundary discipline second** — typed prompt context models replace ad hoc dicts
3. **Render coverage third** — once boundary is typed, render tests are stable
4. **Smoke tests last** — rebuild `tests/test_smoke.py` once schema and render layers exist

Do not attempt to write tests against the old architecture or against an in-progress simplification. Wait for the simplified architecture to stabilize, then build the suite once against the clean target.

---

## Context for Implementing LLMs

- The `tests/` directory has been deleted. Do not attempt to restore old test files.
- `narration-simplification-design.md` defines the exact fields being added and removed. All schema and render test work must be consistent with that document.
- AGENTS.md defines the code rules. All implementation derived from this document must comply.
- Do not add new test infrastructure (fixtures, conftest entries, pytest plugins) beyond what is described here.
- Read `docs/repomap.md` before touching `turn.py`, `extraction.py`, or `models.py`.
