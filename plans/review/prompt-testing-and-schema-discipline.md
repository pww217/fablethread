# Prompt Testing and Schema Discipline — Design Document

## Purpose

This document sets the north star for three related quality concerns that must be resolved before the narration simplification work lands safely: prompt render coverage, schema boundary discipline, and development workflow. It is a design reference, not an implementation plan. Implementing LLMs should derive specific steps from the vision here, the constraints in AGENTS.md, and the narration simplification design doc.

---

## Section 1 — What We Have and Why It Is Not Enough

The repo has meaningful test coverage at the smoke and integration level (`test_engine_smoke.py`, `test_engine_pipeline.py`, `test_turn.py`) and some narrow prompt-level coverage (`test_prompts.py`, `test_extract_progress_template.py`, `test_prompt_audit.py`). The smoke suite proves the engine does not crash and produces plausible output. The existing prompt tests assert a small handful of inclusion and omission properties on one or two templates.

What is missing is a deliberate contract between the engine's Python context-assembly layer and its Jinja templates. Right now, a prompt builder can add or remove a context variable, a template can silently ignore a field, and no test will catch the mismatch until the engine produces wrong narration at runtime. The narration simplification work removes six prompt variables and adds a single `PacingContext` struct — that is exactly the kind of change that the current test surface cannot validate.

Schema boundaries have the same problem. Prompt context is assembled through dict mutation and ad hoc conditional shaping in several places across `turn.py` and `extraction.py`. There is no single moment where the payload crossing into a prompt is validated as a typed object. This means field drift accumulates silently.

The vision here is not exhaustive prompt golden-output testing. It is a thin, stable contract layer that makes the simplification work auditable.

---

## Section 2 — Prompt Render Coverage

### Vision

Every prompt template that touches the narration/extraction pipeline should have direct render tests that assert the presence and omission of the sections that drive story mechanics. These tests are not golden snapshots of full prompt text — they assert structural contracts: specific labeled blocks appear when their context data is populated, and are absent when it is not.

The tests should be organized around the boundary contracts described in `narration-simplification-design.md`: `PacingContext` renders as a single directive block; active threads appear as the canonical thread list; `pending_gm_beat` appears only when populated; and removed fields (`stakes`, `beat_disposition`, `narrative_velocity`, `deescalate`) must not appear anywhere in any prompt after the simplification lands.

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

The data that crosses from Python into a prompt, and the data that comes back from an extraction LLM into Python, should be typed and validated at the boundary — not buried inside dict construction. A future developer reading `turn.py` should be able to find one place where the prompt context is assembled, typed, and handed off to the template renderer. They should not have to trace through multiple conditional dict mutations to understand what variables a template receives.

This does not mean over-engineering typed models for every internal helper. It means the public boundary — the object handed to `template.render()` — is always a validated, typed model. Pydantic models already used throughout the codebase are the right tool.

### The Key Boundary Objects

Two boundaries matter most:

**Prompt-in:** The context dict passed to `template.render()` for Narrator and Progress Extract. This should be the `model_dump()` of a typed model, not an ad hoc dict assembled inline. The model for Progress should match the fields described in `narration-simplification-design.md` — no more, no less.

**Prompt-out:** The Pydantic models already used for extraction results (`ProgressExtractResult`, etc.) are the right shape. The simplification will remove several fields from these models. Once removed, they must be removed completely — no optional shim fields left for backward compatibility.

### What Boundary Discipline Rules Out

- Conditional dict mutations inside prompt builder functions (`if deescalate: context['deescalate'] = ...`)
- Fields that exist in a template but are not in the typed context model
- Fields that exist in the typed model but are never rendered in the template
- Free-form string fields whose semantics are not validated

### Relationship to the Simplification

The narration simplification removes six variables and adds `PacingContext`. Schema boundary discipline ensures that when `PacingContext` is added, it is the only path by which those signals reach the LLM — the old variables cannot silently re-enter through a dict mutation that no test covers.

---

## Section 4 — Test Coverage Strategy

### Vision

Test coverage for the engine should be thought of as three layers with distinct purposes:

**Layer 1 — Schema tests**: Validate that typed boundary models accept valid inputs, reject invalid inputs, and default optional fields correctly. Fast, no I/O, no templates. Purpose: catch schema drift at definition time.

**Layer 2 — Render tests**: Render Jinja templates with synthetic context and assert structural properties of the output. No LLM, no engine. Purpose: catch prompt contract drift at template time.

**Layer 3 — Smoke tests**: Run the full engine pipeline with `FakeLLM` and assert high-level pipeline properties. Slow relative to layers 1 and 2, but exercises integration paths. Purpose: catch wiring mistakes and regression at the pipeline level.

The existing test suite is strong at Layer 3 and weak at Layers 1 and 2. The simplification work needs Layer 1 and 2 coverage added *before* the simplification lands, so changes can be validated at the right layer.

### What Should Not Happen

- Golden-output tests that snapshot the full text of a rendered prompt. These break on any copy change and provide no signal about structural correctness.
- Tests that use `FakeLLM` to validate prompt rendering. Render tests should not require the LLM stub — they should render templates directly.
- Test files that mix schema tests, render tests, and smoke tests. Each layer should be a distinct file or clearly separated class.

### Coverage Debt After Simplification

When the simplification lands, the following existing tests will require review:
- `test_extract_progress_template.py` — passes variables that will be removed; must be updated to match new contract
- `test_prompts.py` — may contain assertions about fields being removed
- `test_pressure.py` — scene pressure model changes; tests must migrate to unified thread model
- `test_engine_smoke.py` — pacing signal assertions may reference removed fields

These should be updated *as part of* the simplification PR, not after.

---

## Section 5 — Development Workflow

### Vision

Engine changes should land through PRs even in a solo project. The reasons are concrete, not ceremonial: PRs create a diff that is reviewable by an LLM planning agent in a future session, they force commit discipline that makes `git bisect` useful, and they create a record of what was intended alongside what was changed.

The branch naming convention already implied by the repo (`plan/`, `feat/`, `fix/`) should be formalized. Design documents land on `design/` branches. Plans land on `plan/` branches. Implementation work lands on `feat/` or `fix/` branches. Each concern gets its own branch and PR — not because of process overhead, but because mixing design, plan, and implementation in one branch makes future LLM context reconstruction unreliable.

### PR Size

A PR should represent one coherent, reviewable concern. For engine work, that means one of: a schema change, a prompt change, a Python logic change, or a test addition. A PR that changes a model, its template, its builder, and its tests is acceptable. A PR that simultaneously changes the pacing model *and* rewrites scene extraction is too large.

The narration simplification work should be broken into at minimum:
1. Schema changes (`StoryThread`, `PacingContext`, `ProgressExtractResult` model changes)
2. Python logic changes (pacing context builder, thread signal application, migration function)
3. Template changes (Progress and Narrate templates)
4. Test updates

These may be separate PRs or separate commits on one PR, but they should be reviewable as distinct units.

### The PR Template

A PR template should prompt for: what changed, why, which prompt or schema contracts were touched, which tests were added or updated, and what the rollback risk is. It should be short enough that it gets filled out, not skipped.

### Merge Discipline

`make check && make test` passes before merge. No exceptions. The design documents, plans, and implementation PRs should all go through this gate even when the changes are documentation-only, to keep the habit clean.

---

## Section 6 — Relationship Between These Concerns

These three concerns are sequenced, not parallel:

1. **Schema boundary discipline first**: Typed prompt context models must exist before render tests can be written against them in a stable way. If the boundary is still a dict, render tests are asserting against an unstable surface.

2. **Render coverage second**: Once the boundary is typed, render tests can be written that will survive the simplification and catch future drift.

3. **Workflow last**: The PR template and branch conventions codify the habits that schema discipline and render coverage require. They are the lowest-stakes change and can land independently.

In practice, the narration simplification and these quality concerns should be interleaved rather than strictly sequential — the simplification is the first real test of whether the discipline holds.

---

## Context for Implementing LLMs

- The narration simplification design doc at `plans/narration-simplification-design.md` defines the exact fields being added and removed. All schema and render test work must be consistent with that document.
- AGENTS.md defines the code rules (type hints, structured logging, input validation at boundaries, make check && make test). All implementation derived from this document must comply.
- Existing render tests in `tests/test_extract_progress_template.py` show the established pattern for Jinja template testing in this repo — use that pattern, do not invent a new one.
- Existing schema tests in `tests/test_models.py` and `tests/test_eval_schema.py` show the established pattern for model validation testing.
- Do not add new test infrastructure (new fixtures, conftest entries, pytest plugins) unless AGENTS.md or `docs/REPOMAP/testing.md` already permits it.
- The REPOMAP files for engine modules should be read before touching `turn.py`, `extraction.py`, or `models.py`.
