# Prompt Testing and Schema Discipline

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Lock prompt rendering coverage | Add targeted render tests for narration/progress prompt composition so simplification work can change prompts safely. |
| 02 | Tighten schema boundaries | Enforce simpler, explicit schema contracts around prompt inputs/outputs and remove drift-prone ad hoc prompt context assembly. |
| 03 | Adopt PR-first workflow guardrails | Add lightweight repo workflow and documentation changes so future engine simplification lands through reviewable branches and PR-sized slices. |

## Objective
The engine already has smoke tests and some prompt-level coverage, but it is still missing enough direct render and schema-boundary tests that prompt and orchestration changes can silently alter behavior. This plan adds explicit prompt rendering coverage, strengthens schema discipline at the module boundaries where prompt context is assembled and validated, and introduces a PR-first workflow so future narration simplification can land in smaller, reviewable changes with safer blast radius.

## Non-goals
- Rewriting the narration engine or implementing the larger narration simplification itself.
- Changing game mechanics, pacing rules, thread semantics, or beat semantics in this plan.
- Adding broad golden-output tests for every prompt variant in the codebase.
- Replacing existing smoke tests or end-to-end engine tests.
- Introducing external CI services or heavyweight review automation.

## Implementation — Phase 01: Lock prompt rendering coverage

### Files to pull for context
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/REPOMAP/testing.md`
- `tests/test_prompts.py`
- `tests/test_extract_progress_template.py`
- `tests/test_engine_smoke.py`
- `ccya/prompts/extract_progress_user.j2`
- `ccya/prompts/`
- `ccya/engine/`

### Detailed steps

#### Step 1.1 — Inventory current prompt test surface

**File:** `tests/test_prompts.py`

**What:** Audit the existing prompt tests and split them by responsibility: template rendering assertions, prompt assembly assertions, and smoke-level orchestration assertions. Keep only genuinely prompt-focused assertions in this file, and move any cross-cutting engine behavior assertions to more appropriate tests if needed.

**Why:** The current repo already has prompt tests and smoke tests, but they do not cleanly communicate what is protected at the rendering layer versus the orchestration layer. The simplification work needs a narrow, trustworthy prompt test surface.

**Code Snippet**
```python
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "ccya" / "prompts"

def build_prompt_env() -> Environment:
    return Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))
```

**Validation:** Confirm the resulting test file still only covers prompt-facing responsibilities and that any moved assertions continue to pass in their destination test files.

#### Step 1.2 — Add explicit render tests for narration and progress prompts

**File:** `tests/test_prompts.py`

**What:** Add direct render tests for the prompt templates and/or prompt-builder helpers that assert inclusion, omission, and formatting of the key mechanics now driving narration simplification: active threads, latent or dormant thread sections if still present, stakes, pending GM beat, de-escalation markers, and narration directives. Tests should use minimal synthetic context and assert concrete rendered text blocks, not fuzzy substring bundles.

**Why:** The engine currently has smoke coverage and at least one narrow render test for `extract_progress_user.j2`, but simplification work will alter prompt composition. These render tests create a stable contract for what must still appear in the prompt after refactors.

**Code Snippet**
```python
def test_extract_progress_prompt_renders_pending_beat_block(env: Environment) -> None:
    out = render_extract_progress(
        env,
        pending_beat={
            "type": "revelation",
            "instruction": "Richard Manning recognizes the letter.",
            "expires_turn": 8,
        },
    )
    assert "pending_beat" in out
    assert "Type: revelation" in out
    assert "Expires at turn: T8" in out
```

**Validation:** Run the focused prompt test module and verify failures are specific and readable when prompt copy changes.

#### Step 1.3 — Add render tests for omission paths and de-escalation behavior

**File:** `tests/test_extract_progress_template.py`

**What:** Expand the existing template render test approach to cover omission cases and mutually exclusive prompt sections: no pending beat, empty thread lists, resolved pressures present only in the de-escalation block, and directives that should suppress escalation language.

**Why:** The dangerous regressions are often not missing the happy-path block, but rendering stale or contradictory context when the engine believes it has slimmed the state. Omission-path assertions are the fastest way to catch that drift.

**Code Snippet**
```python
def test_progress_prompt_omits_pending_beat_when_absent(env: Environment) -> None:
    out = _render(env, pending_beat=None)
    assert "pending_beat" not in out
    assert "Expires at turn" not in out
```

**Validation:** Verify the template tests cover both presence and absence paths for every section the simplification touches.

#### Step 1.4 — Add a rendered-prompt smoke fixture for a realistic turn snapshot

**File:** `tests/test_engine_smoke.py`

**What:** Add a single realistic snapshot-style smoke test that renders the prompt context for a known turn state similar to the current investigation example. Assert a handful of critical lines rather than snapshotting the entire prompt, so the test remains stable while still exercising the full assembly path.

**Why:** Narrow render tests protect specific blocks, but one realistic integrated render test is useful to catch mismatches between engine context assembly and template expectations.

**Code Snippet**
```python
def test_progress_prompt_smoke_contains_turn_seven_context(...) -> None:
    rendered = build_progress_prompt_for_test(state_fixture)
    assert "active_threads" in rendered
    assert "rules_stakes" in rendered
    assert "Narration Directive: Breathe" in rendered
    assert "Richard Manning" in rendered
```

**Validation:** The smoke test should fail only when end-to-end prompt assembly changes materially, not on irrelevant whitespace changes.

### Tests to write or update
- `tests/test_prompts.py`
  - `test_extract_progress_prompt_renders_pending_beat_block`
  - `test_extract_progress_prompt_renders_active_threads_section`
  - `test_extract_progress_prompt_renders_rules_stakes_and_band`
  - `test_narration_prompt_renders_breathe_directive`
- `tests/test_extract_progress_template.py`
  - `test_progress_prompt_omits_pending_beat_when_absent`
  - `test_progress_prompt_omits_empty_thread_sections`
  - `test_progress_prompt_renders_deescalation_resolved_pressures`
- `tests/test_engine_smoke.py`
  - `test_progress_prompt_smoke_contains_turn_seven_context`

### REPOMAP and architecture updates
- `docs/REPOMAP/testing.md` — document the distinction between prompt render tests, prompt assembly smoke tests, and full engine smoke tests, including when each should be used.

### Risks
1. Prompt assertions can become brittle if they key off incidental copy rather than structural sections; mitigate by asserting labeled blocks and critical lines only.
2. Integrated smoke tests can duplicate existing end-to-end coverage; mitigate by keeping exactly one realistic rendered-prompt smoke path.
3. Template tests may drift from actual prompt builders if they render templates directly with hand-built context; mitigate by covering both direct-template and assembled-prompt paths.

## Implementation — Phase 02: Tighten schema boundaries

### Files to pull for context
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/REPOMAP/testing.md`
- `ccya/models.py`
- `ccya/engine/turn.py`
- `ccya/engine/extraction.py`
- `ccya/engine/`
- `tests/test_models.py`
- `tests/test_turn_validate.py`
- `tests/test_engine_pipeline.py`
- `tests/test_eval_schema.py`

### Detailed steps

#### Step 2.1 — Identify prompt boundary payloads and make them explicit

**File:** `ccya/models.py`

**What:** Introduce or tighten typed models for the exact payloads passed into prompt rendering and accepted back from extraction. Replace loosely assembled dictionaries where possible with named, versioned Pydantic models or dataclasses already consistent with repo conventions.

**Why:** Prompt complexity is manageable only when the data crossing the boundary is small and explicit. The simplification effort will fail if prompt inputs continue to grow through ad hoc dict expansion.

**Code Snippet**
```python
class ProgressPromptContext(BaseModel):
    turn_no: int
    band: str
    stakes: str
    active_threads: list[StoryThreadSummary]
    resolved_pressures: list[ResolvedPressureSummary] = Field(default_factory=list)
    pending_beat: PendingBeatSummary | None = None
    narration_directive: str | None = None
```

**Validation:** Existing prompt builders should accept the typed model without behavior changes, and schema validation failures should point to the missing field at construction time.

#### Step 2.2 — Move validation to module boundaries, not deep call sites

**File:** `ccya/engine/turn.py`

**What:** Refactor prompt-context assembly so normalization and validation happen once, at the boundary where engine state becomes prompt context. Remove duplicated defensive shaping deeper in prompt builders or extraction helpers.

**Why:** You asked for schema discipline because the current system still feels too complex. One major cause is repeated, distributed shape-fixing. Boundary validation makes the flow auditable and easier to reason about.

**Code Snippet**
```python
def build_progress_prompt_context(state: EngineState, turn: TurnRecord) -> ProgressPromptContext:
    context = ProgressPromptContext.model_validate(
        {
            "turn_no": state.meta.turn,
            "band": turn.rules.band,
            "stakes": turn.rules.stakes,
            "active_threads": summarize_active_threads(state),
            "resolved_pressures": summarize_resolved_pressures(state),
            "pending_beat": summarize_pending_beat(state),
            "narration_directive": compute_narration_directive(state),
        }
    )
    return context
```

**Validation:** Invalid or missing boundary data should fail in targeted unit tests before prompt rendering starts.

#### Step 2.3 — Remove or quarantine drift-prone free-form prompt context assembly

**File:** `ccya/engine/extraction.py`

**What:** Replace scattered dict literals and conditional prompt-only shaping with calls to the new typed summarizers. Where backward compatibility forces transitional code, isolate it in one adapter layer with a clear removal note.

**Why:** Simplification does not stick if every extraction path can still invent one-off prompt fields. A single adapter layer keeps drift visible and temporary.

**Code Snippet**
```python
def render_extract_progress_prompt(context: ProgressPromptContext, env: Environment) -> str:
    template = env.get_template("extract_progress_user.j2")
    return template.render(**context.model_dump())
```

**Validation:** Search the touched modules and confirm prompt rendering paths no longer assemble bespoke context dictionaries inline.

#### Step 2.4 — Add schema-boundary tests for prompt context construction

**File:** `tests/test_models.py`

**What:** Add tests that verify required fields, defaulted optional lists, and rejection of malformed prompt context payloads. Mirror this in turn-level tests that assert the builder returns typed prompt contexts rather than raw dicts.

**Why:** Render tests catch visible prompt regressions, but schema tests catch structural regressions earlier and more precisely.

**Code Snippet**
```python
def test_progress_prompt_context_defaults_optional_lists() -> None:
    ctx = ProgressPromptContext(
        turn_no=7,
        band="FAIL",
        stakes="Lose the clue.",
        active_threads=[],
    )
    assert ctx.resolved_pressures == []
    assert ctx.pending_beat is None
```

**Validation:** The schema tests should fail on malformed boundary payloads without requiring template rendering.

### Tests to write or update
- `tests/test_models.py`
  - `test_progress_prompt_context_defaults_optional_lists`
  - `test_progress_prompt_context_requires_turn_band_and_stakes`
  - `test_progress_prompt_context_rejects_malformed_pending_beat`
- `tests/test_turn_validate.py`
  - `test_build_progress_prompt_context_returns_typed_model`
  - `test_build_progress_prompt_context_rejects_missing_rules_fields`
- `tests/test_engine_pipeline.py`
  - `test_progress_render_uses_model_dump_from_typed_context`
- `tests/test_eval_schema.py`
  - Update schema-eval fixtures if prompt or extraction payload models become explicit engine contracts.

### REPOMAP and architecture updates
- `docs/ARCHITECTURE.md` — add a short section naming prompt context construction as an explicit typed boundary in the turn pipeline.
- Relevant `docs/REPOMAP/*.md` file for engine/prompt modules — record any new boundary models, builders, or adapter layers.

### Risks
1. Tightening schemas may expose existing tolerated nulls or omitted fields; mitigate by adding explicit defaults only where semantically correct.
2. Transitional adapter code can become permanent clutter; mitigate by naming it clearly and documenting removal conditions in the plan and REPOMAP.
3. Typed models can overfit the current prompt design; mitigate by modeling stable concepts, not literal prose layout.

## Implementation — Phase 03: Adopt PR-first workflow guardrails

### Files to pull for context
- `AGENTS.md`
- `README.md`
- `CONTRIBUTING.md`
- `docs/ARCHITECTURE.md`
- `docs/REPOMAP/testing.md`
- `.github/` (if present)
- `Makefile`

### Detailed steps

#### Step 3.1 — Document the branch-and-PR workflow for engine changes

**File:** `CONTRIBUTING.md`

**What:** Add a concise repo workflow section recommending short-lived branches and PRs for engine, prompt, and schema changes, even for solo development. Include expected PR scope, test expectations, and how to separate design docs, plans, and implementation PRs.

**Why:** You said that even though it is just you, you should start using PRs. This only helps if the repo itself encodes that expectation so future work does not slide back into direct-commit habits.

**Code Snippet**
```python
WORKFLOW = {
    "change_types": ["design doc", "plan", "implementation"],
    "branch_prefixes": ["design/", "plan/", "feat/", "fix/"],
    "required_checks": ["targeted tests during development", "make check", "make test before merge"],
}
```

**Validation:** The documentation should give a future executor enough detail to choose the right branch and PR shape without guessing.

#### Step 3.2 — Add a pull request template tailored to engine changes

**File:** `.github/pull_request_template.md`

**What:** Add a PR template with sections for mechanic or prompt contract changes, schemas touched, prompts touched, tests added or updated, REPOMAP or architecture docs updated, and rollback risk.

**Why:** A good PR template forces explicit reasoning about schema drift, prompt drift, and documentation drift before merge.

**Code Snippet**
```python
PR_TEMPLATE_SECTIONS = [
    "What changed",
    "Why this change",
    "Prompt or schema contracts touched",
    "Tests added or updated",
    "Docs updated",
    "Risks and rollback",
]
```

**Validation:** The PR template should map directly onto the repo's existing architecture and testing rules rather than generic OSS boilerplate.

#### Step 3.3 — Document prompt/schema review checklist

**File:** `docs/REPOMAP/testing.md`

**What:** Add a short checklist for any PR that changes prompt inputs, prompt templates, extraction outputs, or state schemas: render tests updated, schema tests updated, smoke coverage considered, docs updated if contracts moved.

**Why:** This turns the schema-discipline idea into a repeatable review habit rather than a one-off preference.

**Code Snippet**
```python
REVIEW_CHECKLIST = [
    "Prompt render assertions updated for changed sections",
    "Boundary schemas validated at construction time",
    "Smoke coverage still exercises the changed path",
    "Architecture or REPOMAP docs updated for contract changes",
]
```

**Validation:** The checklist should clearly cover the exact failure modes that made the current system feel hard to reason about.

#### Step 3.4 — Final validation and merge discipline

**File:** `Makefile`

**What:** Ensure the documented final validation command for the last phase remains `make check && make test`, and update any docs that refer to weaker or inconsistent validation flows.

**Why:** AGENTS.md requires `make check && make test` as the final validation step. The PR-first workflow should reinforce that instead of introducing ad hoc validation rules.

**Code Snippet**
```python
FINAL_VALIDATION = "make check && make test"
```

**Validation:** The final docs and workflow references should consistently point to `make check && make test` as the pre-merge validation step.

### Tests to write or update
- No new automated tests required for documentation-only workflow changes.
- If the repo already has documentation link or template checks, update them accordingly.

### REPOMAP and architecture updates
- `docs/REPOMAP/testing.md` — add the PR review checklist and where prompt/schema tests belong.
- `docs/ARCHITECTURE.md` — only if it currently documents workflow expectations or PR sizing; otherwise leave unchanged.

### Risks
1. Workflow docs can become performative if too long; mitigate by keeping them short and tied to existing commands and repo concepts.
2. A PR template that is too generic will be ignored; mitigate by making every section specific to prompt, schema, and engine changes.
3. Documentation-only workflow changes can drift from actual practice; mitigate by using the template immediately for the next implementation PR.

## Ambiguities requiring resolution before execution
1. Which prompt builders are the canonical render entry points today? Options: A) direct Jinja template rendering remains first-class and tests target templates plus a few builders, B) tests should target only higher-level builder helpers and stop testing templates directly.
2. How far should schema discipline go in this pass? Options: A) typed prompt-context models only, B) typed prompt-context models plus typed extraction adapter models for inbound and outbound payloads.
3. Should the PR-first workflow be documented in existing repo docs only, or should the implementation also add GitHub-native repo templates under `.github/`? Options: A) docs only, B) docs plus `.github/pull_request_template.md`.
