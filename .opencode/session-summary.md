# Session Summary — Eval Methodology Design Split

## Goal
- Split the monolithic eval methodology design doc into focused documents: core eval methodology, CLI defaults/personas, and UI streaming improvements

## Constraints & Preferences
- Judge model: Qwen3 35B at localhost:8080/v1 (~5-10 tok/s)
- LLM calls expensive for iteration: 100% coverage ~41 min, 25% ~9 min
- Pyramid structure: deterministic checkers at bottom, LLM checkers sampled, deterministic aggregation
- No meta-judge for score synthesis: deterministic math replaces old LLM meta-judge
- LLM sampling: default 1.0 (100%), slider for iteration
- Improvement suggestions: one batch LLM call per scenario group with failures
- Scenario groups: naming convention + Makefile targets, not code abstractions
- Soft ordering: ruling → extraction → narration → state → cross
- Confidence annotation: high/medium/low based on turn count and sampling

## Progress
### Done
- Eval methodology design doc written: `docs/design/eval-methodology-design.md`
- Resolved open questions: sampling strategy, improvement suggestion approach, confidence metric
- Identified scope creep: CLI defaults, personas, UI streaming sections mixed into eval methodology doc
- Identified implementation gaps: no scenarios exist, no aggregation script, no Makefile targets, field-mapping bugs unfixed
- **Split eval methodology design doc into focused documents:**
  1. Core eval methodology: `docs/design/eval-methodology-design.md` (scenario taxonomy, checker suites, aggregation, Makefile)
  2. CLI defaults and personas: `docs/design/cli-defaults-and-personas-design.md` (CLI defaults, persona registry, `ev:` config section)
  3. UI streaming improvements: `docs/design/eval-ui-streaming-design.md` (live eval streaming, mid-turn pipeline visibility)
- Fixed stale references: `docs/design/ev-tooling-design.md` → `docs/design/complete/ev-tooling-design.md` in eval-methodology-design.md
- Added design docs section to `docs/repomap.md` for discoverability

### In Progress
- (none)

### Blocked
- (none)

## Next Steps
1. Review the three new design docs for accuracy and completeness
2. Fix numbering inconsistencies in remaining docs (if any)
3. Proceed to plan writing for implementation:
   - Plan 1: Eval scenarios + checker_suite/llm_checkers fields in scenario.py
   - Plan 2: Aggregation script (scripts/aggregate.py) + Makefile targets
   - Plan 3: CLI defaults and persona registry (ccya/config.py)
   - Plan 4: UI streaming improvements (ccya/server/streaming.py)
4. Fix field-mapping bugs (EV-3, EV-4, EV-7) before writing scenarios

## Critical Context
- `ccya/ev/` package infrastructure is built: play/check/eval commands, checker library (11 deterministic + 3 LLM), data access layer
- `ccya/ev/scenario.py` needs: `checker_suite`, `llm_checkers`, `llm_sample_rate` fields added to Scenario dataclass
- `ccya/ev/eval.py` `cmd_eval_run()` needs: filter by checker_suite, LLM sampling logic, `--sample-rate` CLI flag
- `scripts/aggregate.py` doesn't exist: needs deterministic aggregation, per-group suggestion calls
- `packs/eval/scenarios/` doesn't exist: zero YAML eval scenarios
- Field-mapping bugs: EV-3 (location_change expects `applied.location_change`), EV-4 (sanitizer_lifecycle expects `threads_updated`), EV-7 (pacing_directives stale counter timing)
- `_llm.py` needs: switch from `mlx_lm` import to `localhost:8080/v1` OpenAI-compatible endpoint
- 40+ event fields unchecked: pacing_context, narrate_summary, rejected, changes.*, most ruling.* sub-fields
- Scenario taxonomy: 5 groups (Ruling, Extraction, Narration, State, Cross-cutting), 12 scenarios total
