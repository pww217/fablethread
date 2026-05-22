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

- `storytell_user.j2` — primary target; most complexity lives here
- `narrate_user.j2` — secondary target for directive and beat rendering
- `ruling_user.j2`, `*_scene_*user.j2`, `*_state_*user.j2` — lower priority but should be included once the framework exists

### North Star Test Properties

- Test failure message should name the missing or unexpected section precisely
- Tests should survive whitespace-only template reformatting
- Tests should fail when a field is removed from context but not from the template
- Tests should fail when a field is added to the template but not to context assembly

---

## Section 3 — Schema Boundary Discipline and Data Block Consolidation

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

### Shared Data Block Consolidation

The engine has 4 LLM calls (rules, narrate, scene extract, state/progress extracts) that each assemble their own context dicts from `state`. Analysis of all call sites and templates reveals significant overlap in what data they need. The consolidation strategy is to define **typed block models** that assemble themselves from the raw state dict, then compose these blocks into per-prompt boundary objects.

#### Data Block Mapping (from full codebase analysis)

| Block | State Source | Used By | Notes |
|---|---|---|---|
| `PlayerBlock` | `state["pc"]` | rules, narrate, scene extract | Most shared block — all 3 of these calls need PC data. Progress extract gets it indirectly via extraction_ctx post-delta values. Currently accessed as full dict or partial (stats/conditions separately). |
| `LocationBlock` | `state["location"]` | rules, narrate, scene extract | Rules needs name/id only; others may use description too. |
| `InventoryBlock` | `state["inventory"][]` | narrate | Currently consumed via `{% include "sections/_inventory.j2" %}` in narrate_user.j2 as a list of items accessed through the full state dict (not wrapped). Progress extract gets post-delta values from extraction_ctx, not this block. |
| `ArcThreadBlock` | `state["arc"]` | narrate, progress extract | Narrate filters to active threads only; progress needs all raw threads. Same underlying data, different projections. |
| `WorldStateBlock` | `state.scene.world_state[]` | narrate (conditional), progress extract (conditional) | Currently rendered via `{% include "sections/_world_state.j2" %}` in both templates — one shared include file already consolidates this rendering logic at the template level. |
| `ChronicleBlock` | `recent_turns`, optionally `chronicle_tail` | rules, narrate, progress extract | Window size varies: rules gets 1 entry (last chronicle), progress gets 2 entries, narrate gets full window plus older compressed history as a separate string field (`chronicle_tail`). ChronicleBlock should handle slicing; chronicle_tail is distinct data. |
| `NPCRosterBlock` | `state.scene.present_npcs`, `compendium.npcs[]`, `scene.recently_left` | narrate (rich), progress extract (minimal) | Two variants: rich form includes motivation/fear/leverage for narrator flavor; minimal form has id/name/title/presence/bio only. Keep as separate blocks but share a common base structure to avoid duplication while preserving specialization. Progress extract gets its roster from extraction_ctx post-delta values, not directly from state. |
| `PacingBlock` | Computed from momentum/deescalate/avoidance | narrate, progress extract | Currently built by `_compute_pacing_context()` in narrate.py and passed separately as a PacingContext model. Should be part of the boundary object for any prompt that needs pacing signals. |

#### Consolidation Pattern

```
Raw state dict → typed block models (assemble from state) → per-prompt boundary objects (compose blocks) → model_dump() → template.render(**ctx.model_dump())
```

Each block is a Pydantic model with a class method or constructor that accepts the raw `state` dict and extracts/computes what it needs. The per-prompt boundary object composes these blocks:

- **RulingBoundary** = PlayerBlock + LocationBlock + ChronicleBlock(sliced 1)
- **NarratorBoundary** = PlayerBlock + LocationBlock + InventoryBlock(as-list from state) + ArcThreadBlock(active-only) + WorldStateBlock + NPCRosterBlock(rich) + PacingBlock + ChronicleBlock(full window)
- **SceneExtractBoundary** = PlayerBlock + LocationBlock + NPCRosterBlock(minimal, compendium-hydrated) + ChronicleBlock(sliced 1)
- **StorytellerBoundary** = PlayerBlock(as-post-delta via extraction_ctx) + InventoryBlock(post-delta via extraction_ctx) + ConditionsBlock(post-delta via extraction_ctx) + ArcThreadBlock(all raw from state.arc.threads) + WorldStateBlock + PacingBlock + ChronicleBlock(sliced 2)

The benefit: if you add a field to `PlayerBlock`, every prompt that needs PC data gets it automatically through type checking of boundary objects rather than hunting through multiple builder functions. If you remove a block from one boundary, the schema test catches orphan fields immediately. New prompts are assembled by composing existing blocks rather than building dicts from scratch.

#### Dead Code Found During Analysis

- `extract_scene_user.j2` references `scene_location_description` which is never passed in context dict (line 17-20 of template). Should be removed or the field should be added to boundary model.
- `_npc_roster_extract.j2` and `_npc_roster.j2` share most variables but differ on motivation/fear/leverage presence — consolidate into a single include with conditional rendering based on block variant, not two separate files.

#### Schema-Template Alignment Check (Section 0 of Test Strategy)

Before any layer tests exist, there should be an AST-based alignment check that runs as part of `make check`. This is the fastest feedback loop possible: it catches template/model drift at edit time without running a single test.

### How It Works

1. Define explicit contracts mapping each user prompt template to its boundary model type:
   ```python
   TEMPLATE_CONTRACTS = {
       "storytell_user.j2": StorytellerBoundary,
       "narrate_user.j2": NarratorBoundary,
       "ruling_user.j2": RulingBoundary,
       # ... etc
   }
   ```

2. The check parses each `.j2` file using Jinja's AST (`Environment.parse()`), extracts all variable references (all `{{ }}`, `{% %}` data accesses that aren't builtins/control flow keywords).

3. For each contract, compare extracted variables against the boundary model fields:
   - **Orphan in template**: Variable used in `.j2` but not present on boundary model → test fails
   - **Dead field**: Field on boundary model never rendered in `.j2` → test warns (not all fields need rendering; some may be for LLM context only)

4. This runs as part of `make check` — no CI or pre-commit needed, just the existing lint/typecheck step extended with a new command.

### How Variables Map to Models

Jinja variable access like `pc.name` maps to the boundary model field `name`. Loops over lists (e.g., `{% for item in inventory %}`) map to iterating over a list field. Filters and builtins (`|join`, `|length`) are ignored — only data accesses count as contract references.

Section includes count as part of their parent template's contract: variables used inside an include file must exist on the boundary model passed by the parent template (Jinja passes context through includes automatically).

### Scope

- All user prompt templates (`*_user.j2`)
- System prompts that inject dynamic data — currently only `narrate_system.j2` consumes pack_style, narrator_rules, world_rules, current_arc. Other system prompts render with `{}` and are excluded (hardcoded rules prose)
- Section includes count as part of their parent template's contract

### Dead Field Policy

A field on a boundary model that is never rendered in any `.j2` file should be treated as dead code — either remove it or explicitly mark it as reserved for future use. Silent unused fields undermine schema discipline and make the alignment check less useful over time.

---

## Section 4 — Test Coverage Strategy

### Layer Model

Test coverage for the engine should be four layers with distinct purposes:

**Section 0 — Schema-template alignment**: AST-based check that every variable used in a `.j2` user prompt exists on its boundary model. Fast, no I/O, no rendering. Purpose: catch drift at template edit time. Runs as part of `make check`. One file: `tests/test_alignment.py`.

**Layer 1 — Schema tests**: Validate that typed boundary models accept valid inputs, reject invalid inputs, and default optional fields correctly. Also validate extraction result Pydantic models (`ProgressExtractResult`, etc.) for the prompt-out boundary. Fast, no I/O, no templates. Purpose: catch schema drift at definition time. One file: `tests/test_schema.py`.

**Layer 2 — Render tests**: Render Jinja templates with synthetic context and assert structural properties of the output. No LLM, no engine. Purpose: catch prompt contract drift at template time. One file: `tests/test_render.py`.

**Layer 3 — Integration/smoke tests**: Run the full engine pipeline with `FakeLLM` or real scenarios and assert high-level pipeline properties. Purpose: catch wiring mistakes and regression at the pipeline level. One file: `tests/test_smoke.py`.

Build in this order (Section 0 → Layer 1 → Layer 2 → Layer 3). Section 0 can be built incrementally as boundary models land; render tests should not be written until Layers 1-2 exist — smoke tests are the most expensive to write and maintain and provide the least signal per line.

### Eval Framework Integration

The existing eval framework (`ccya/eval/scenario.py` + `evals/scenarios/`) defines qualitative scenarios with turn definitions and assertions against events.jsonl output. This should be kept as a separate importable module, not moved into `tests/`. Scenario objects are imported two ways:
- The existing eval runner consumes them for rubric-based evaluation (qualitative)
- Pytest layer 3 integration tests consume the same scenario definitions to run through the engine pipeline

One source of truth, two consumers. No duplication.

### What Should Not Happen

- Golden-output tests that snapshot the full text of a rendered prompt
- Tests that use `FakeLLM` to validate prompt rendering — render tests render templates directly
- Test files that mix schema tests, render tests, and smoke tests
- New test infrastructure (fixtures, conftest entries, pytest plugins) beyond what is described here

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
4. Test additions (Section 0 + Layers 1–3 in order)

### Merge Discipline

`make check` passes before merge. `make test` passes before merge once the new test suite exists. Until then, `make check` alone is the gate.

---

## Section 6 — Sequencing

These concerns are sequenced, not parallel:

1. **Narration simplification lands first** — schema and template changes per `narration-simplification-design.md`
2. **Shared data block consolidation second** — typed boundary models replace ad hoc dicts in prompt builders; define the TEMPLATE_CONTRACTS mapping as each boundary model is created
3. **Schema-template alignment third** (Section 0) — AST-based check runs as part of `make check`; catches drift at edit time before any layer tests exist
4. **Layer 1 schema tests fourth** — validate boundary and extraction result models
5. **Render coverage fifth** (Layer 2) — once boundaries are typed, render tests are stable
6. **Smoke/integration last** (Layers 3+eval integration) — rebuild `tests/test_smoke.py` plus scenario-based pytest imports

Do not attempt to write tests against the old architecture or against an in-progress simplification. Wait for the simplified architecture to stabilize, then build the suite once against the clean target.

---

## Context for Implementing LLMs

- The `tests/` directory has been deleted. Do not attempt to restore old test files.
- `narration-simplification-design.md` defines the exact fields being added and removed. All schema and render test work must be consistent with that document.
- AGENTS.md defines the code rules. All implementation derived from this document must comply.
- Do not add new test infrastructure (fixtures, conftest entries, pytest plugins) beyond what is described here.
- Read `docs/repomap.md` before touching `turn.py`, `extraction.py`, or `models.py`.
