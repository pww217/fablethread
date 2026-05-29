# Naming Rename: Progress Extractor → Storyteller, Rules → Ruling

## Status
`completed`

## Phases

8 phases: Rename `progress_extractor`/`extract_progress` to `storytell`/`storyteller` and `rules` (pipeline step) to `ruling` across all source code, templates, config, eval infrastructure, server components, scripts, documentation, and plans. No behavioral changes — pure rename with file renames where appropriate.

## Issue

The names "progress extractor" and "rules" misrepresent what these pipeline steps actually do. The progress extractor doesn't extract progress — it makes storytelling decisions (beats, thread advancement, pressure management). The rules step isn't just rule-checking — it classifies intent AND resolves dice rolls to produce a ruling on the player action. These names create cognitive friction and make the codebase harder to navigate because the terminology doesn't match the actual responsibilities of each component or TTRPG conventions.

## Solution

Rename `progress_extractor`/`extract_progress` → `storytell`/`storyteller` across all 50+ references in source, templates, evals, server, scripts, and docs. Rename pipeline-step "rules" → `ruling` (keeping domain-specific `RulesCheck`, `RulesOutcome`, `ccya/rules.py` dice engine as-is since those refer to game mechanics, not the LLM step). The rename covers: class names (`ProgressExtractResult→StorytellerResult`, `ProgressExtractBoundary→StorytellerBoundary`, `RulesBoundary→RulingBoundary`), template filenames (`.j2` renames), function names (`_extract_progress_messages→_storytell_messages`, `_call_rules→_call_ruling`), event dict keys (`"progress"/"extract_progress"→"storytell"`, `"rules"→"ruling"`), stream identifiers, config settings, CSS class mappings, and all documentation references. Expected outcome: terminology accurately reflects component responsibilities with no behavioral changes or backward compatibility overhead.

## Firm decisions

1. `ProgressExtractResult` → `StorytellerResult`. `ProgressExtractBoundary` → `StorytellerBoundary`.
2. `RulesBoundary` → `RulingBoundary`. Pipeline step "rules" → `ruling`. Event key `"rules"` → `"ruling"`. Stream name `"rules"` → `"ruling"`. Prompt storage key `"rules_prompt"` → `"ruling_prompt"`.
3. Domain-specific names stay unchanged: `RulesCheck`, `RulesOutcome` (models.py), `ccya/rules.py` dice engine, `resolve_check()`, `compute_band()` — these refer to game mechanics, not the LLM step.
4. Template renames: `extract_progress_system.j2→storytell_system.j2`, `extract_progress_user.j2→storytell_user.j2`, `rules_system.j2→ruling_system.j2`, `rules_user.j2→ruling_user.j2`.
5. Function renames in extraction.py: `_extract_progress_messages()` → `_storytell_messages()`. In engine/ruling.py (renamed from rules.py): `_call_rules()` → `_call_ruling()`, `_rules_messages()` → `_ruling_messages()`, `_avg_rules_ms()` → `_avg_ruling_ms()`, `_log_rules_outcome()` → `_log_ruling_outcome()`.
6. Config renames: `EngineConfig.rules_temperature→ruling_temperature`, `max_rules_retries→max_ruling_retries`. YAML key `rules:` → `ruling:` in config.yaml.
7. No backward compatibility — rip out all old references immediately, no shims or aliases.

## Non-goals

- Behavioral changes to any pipeline step's logic or output schema.
- Renaming domain-specific game mechanics terms (`RulesCheck`, `RulesOutcome`, `ccya/rules.py` dice engine).
- Updating plans in `/plans/` or `/plans/review/` or `/plans/completed/` that are already being worked on (those will self-correct when their own phases execute, or get caught by Phase 8).
- Renaming `ev.py` debug script's internal variable names beyond what's needed for stream/event key correctness.

## Risks, Ambiguities, and Blockers

1. **Event dict keys are a shared wire format.** The `"rules"` and `"progress"/"extract_progress"` keys appear in event dicts that flow through the entire pipeline (turn.py → extraction → evals → server). All references must be renamed consistently or the event stream breaks at runtime. Phase 4 (pipeline orchestration) is where this becomes live — all prior phases just prepare definitions/templates/functions.
2. **Eval infrastructure assumes specific stream keys.** `judge.py`, `report.py`, `runner.py` use `"rules"` and `"extract_progress"` as stream identifiers to parse event dicts from `events.jsonl`. If any eval run was done with old key names, historical events won't match new keys — but this is acceptable since we're not preserving backward compatibility.
3. **Plan docs in `/plans/` contain references.** These are plans for other work that reference the current naming. Phase 8 updates them, but executors of those plans will encounter conflicts if they run before or after this rename. The safest approach: complete this rename first so downstream plan execution uses correct names.
4. **File renames vs in-place changes.** Git tracks file renames only when `git mv` is used or when diffs are primarily deletions/additions of the same content with name changes. If git doesn't detect renames, history for those files will appear as delete+create rather than rename. This is cosmetic — no functional impact.

## Implementation — Phase 1: Domain models (models.py + context.py)

### Context files to load
- `ccya/models.py` (lines 482–530, ProgressExtractResult class; lines 110–133 for RulesCheck/IntentEnvelope/RulesOutcome which stay unchanged)
- `ccya/prompts/context.py` (all — ProgressExtractBoundary at lines 279–325, RulesBoundary at lines 206–217, template-to-boundary mapping dict at line 325+)

### Detailed steps

#### Step 1.1 — Rename ProgressExtractResult to StorytellerResult in models.py

**File:** `ccya/models.py`

**What:** Rename class `ProgressExtractResult` → `StorytellerResult`. Update all self-referencing string annotations: `_nullify_invalid_gm_beat()` return type `"ProgressExtractResult"` → `"StorytellerResult"`, `_warn_empty_actions()` return type similarly. No field changes — only the class name and its internal forward references.

**Why:** The model's responsibility is storytelling decisions (beats, thread advancement), not progress extraction. `StorytellerResult` accurately describes what it represents in the pipeline.

**Validation:** Run `python -c "from ccya.models import StorytellerResult; print(StorytellerResult().model_fields.keys())"` — verify class exists and fields are unchanged. Also run `grep -n 'ProgressExtractResult' ccya/models.py` to confirm zero remaining references in this file.

#### Step 1.2 — Rename ProgressExtractBoundary to StorytellerBoundary in context.py

**File:** `ccya/prompts/context.py`

**What:** Rename class `ProgressExtractBoundary` → `StorytellerBoundary`. Update its docstring from `"""Context for extract_progress_user.j2.` to `"""Context for storytell_user.j2.`. Update all internal comments that reference `extract_progress_user.j2`, `_extract_progress_messages()`, or `progress_extractor` — change to `storytell_user.j2`, `_storytell_messages()`, `storyteller`.

**Why:** The boundary class defines the typed interface between prompt context dicts and the storyteller template. Its name must match both its responsibility (storytelling) and the new template/function names from later phases.

**Validation:** Run `grep -n 'ProgressExtractBoundary' ccya/prompts/context.py` — should return zero matches. Verify class still has all original fields with same types.

#### Step 1.3 — Rename RulesBoundary to RulingBoundary in context.py

**File:** `ccya/prompts/context.py`

**What:** Rename class `RulesBoundary` → `RulingBoundary`. Update its docstring from `"""Context for rules_user.j2.` to `"""Context for ruling_user.j2.`. Update internal comments referencing `rules_user.j2`, `_rules_messages()` — change to `ruling_user.j2`, `_ruling_messages()`.

**Why:** The boundary class defines the typed interface between prompt context dicts and the ruling template. Its name must reflect that this step produces rulings (intent classification + dice resolution), not just rule-checking.

**Validation:** Run `grep -n 'RulesBoundary' ccya/prompts/context.py` — should return zero matches for the old name only. Verify class fields are unchanged.

#### Step 1.4 — Update template-to-boundary mapping dict in context.py

**File:** `ccya/prompts/context.py`

**What:** In the template-to-boundary type mapping dict (around line 325+), update: `"extract_progress_user.j2": ProgressExtractBoundary,` → `"storytell_user.j2": StorytellerBoundary,`. Update: `"rules_user.j2": RulesBoundary,` → `"ruling_user.j2": RulingBoundary,`.

**Why:** The mapping dict connects template filenames to their boundary types. Both keys and values must reflect the new names or type checking will fail at runtime when templates are validated against boundaries.

**Validation:** Run `grep -n 'extract_progress_user\|rules_user' ccya/prompts/context.py` — should return zero matches for old template name strings as dict keys. Verify `"storytell_user.j2"` and `"ruling_user.j2"` appear in the mapping.

### Tests to write or update
None during refactor phase (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `docs/repomap.md` — Phase 8 handles all repomap updates together with other docs.

## Implementation — Phase 2: Template renames (.j2 files + string references to template names)

### Context files to load
- `ccya/prompts/extract_progress_system.j2` (rename to `storytell_system.j2`)
- `ccya/prompts/extract_progress_user.j2` (rename to `storytell_user.j2`)
- `ccya/prompts/rules_system.j2` (rename to `ruling_system.j2`)
- `ccya/prompts/rules_user.j2` (rename to `ruling_user.j2`)

### Detailed steps

#### Step 2.1 — Rename progress extractor template files

**Files:** `ccya/prompts/extract_progress_system.j2→storytell_system.j2`, `ccya/prompts/extract_progress_user.j2→storytell_user.j2`

**What:** Physically rename the two `.j2` template files:
- `mv ccya/prompts/extract_progress_system.j2 ccya/prompts/storytell_system.j2`
- `mv ccya/prompts/extract_progress_user.j2 ccya/prompts/storytell_user.j2`

Do NOT modify template content — only rename the filenames. The templates' internal Jinja references (to context variables, partials like `_arc.j2`) remain unchanged since those variable names are not being renamed in this effort.

**Why:** Template filenames must match the new naming convention so that string references to `"storytell_system.j2"` and `"storytell_user.j2"` in Python code resolve correctly after Phase 3 renames the template name strings.

**Validation:** Run `ls ccya/prompts/storytell_*.j2` — both files should exist. Verify old filenames no longer exist: `ls ccya/prompts/extract_progress_*.j2` should return nothing or error.

#### Step 2.2 — Rename rules template files

**Files:** `ccya/prompts/rules_system.j2→ruling_system.j2`, `ccya/prompts/rules_user.j2→ruling_user.j2`

**What:** Physically rename the two `.j2` template files:
- `mv ccya/prompts/rules_system.j2 ccya/prompts/ruling_system.j2`
- `mv ccya/prompts/rules_user.j2 ccya/prompts/ruling_user.j2`

Do NOT modify template content — only rename filenames. Internal Jinja references remain unchanged.

**Why:** Same rationale as Step 2.1 — template filenames must match new naming convention for Python string references to resolve correctly after Phase 3.

**Validation:** Run `ls ccya/prompts/ruling_*.j2` — both files should exist. Verify old filenames no longer exist: `ls ccya/prompts/rules_system.j2 rules_user.j2` should return nothing or error.

### Tests to write or update
None during refactor phase (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `docs/repomap.md` — Phase 8 handles all repomap updates together with other docs.

## Implementation — Phase 3: Engine modules (extraction.py + engine/ruling.py)

### Context files to load
- `ccya/engine/extraction.py` (imports at top, `_extract_progress_messages()` function ~line 325+, call site in extraction pipeline ~line 620+)
- `ccya/engine/rules.py→ruling.py` (rename file; all functions: `_rules_messages`, `_call_rules`, `_avg_rules_ms`, `_log_rules_outcome`)

### Detailed steps

#### Step 3.1 — Rename engine/rules.py to engine/ruling.py and rename internal template references

**File:** `ccya/engine/rules.py→ruling.py` (rename first, then edit)

**What:** 
1. `mv ccya/engine/rules.py ccya/engine/ruling.py`
2. In the renamed file, update all string references to template filenames: `"rules_system.j2"` → `"ruling_system.j2"`, `"rules_user.j2"` → `"ruling_user.j2"`.

**Why:** The module houses LLM calls for the ruling step (intent classification + dice resolution). Its filename and internal template references must match the new naming convention.

**Validation:** Run `grep -n 'rules_system\|rules_user' ccya/engine/ruling.py` — should return zero matches. Verify `"ruling_system.j2"` and `"ruling_user.j2"` appear in the file.

#### Step 3.2 — Rename functions in engine/ruling.py

**File:** `ccya/engine/ruling.py`

**What:** Rename all four public/internal functions:
- `_rules_messages()` → `_ruling_messages()`
- `_call_rules()` → `_call_ruling()`
- `_avg_rules_ms()` → `_avg_ruling_ms()`
- `_log_rules_outcome()` → `_log_ruling_outcome()`

Update internal references between these functions (e.g., if one calls another by name). Update error messages and log strings that contain "rules" as a step identifier: `"No JSON found in rules response"` → `"No JSON found in ruling response"`, `"rules parse failed..."` → `"ruling parse failed..."`, `"rules call failed after all attempts..."` → `"ruling call failed after all attempts..."`.

**Why:** Function names must reflect the new step name so that import statements and call sites throughout turn.py resolve correctly. Log messages use consistent terminology for traceability in event logs.

**Validation:** Run `grep -n 'def _rules_\|_call_rules\|_avg_rules_ms\|_log_rules_outcome' ccya/engine/ruling.py` — should return zero matches for old names only. Verify all four new function definitions exist with correct signatures matching the original signatures exactly (no parameter changes).

#### Step 3.3 — Rename _extract_progress_messages to _storytell_messages in extraction.py

**File:** `ccya/engine/extraction.py`

**What:** 
1. Update import at top: `"extract_progress_system.j2"` → `"storytell_system.j2"`, `"extract_progress_user.j2"` → `"storytell_user.j2"`.
2. Rename function `_extract_progress_messages()` → `_storytell_messages()`. Preserve exact signature and all parameters — only the name changes.
3. Update internal template string references: `"_render(env, "extract_progress_system.j2", ...)"` → `"_render(env, "storytell_system.j2", ...)"`, similarly for user template.

**Why:** The function builds messages for the storyteller LLM call. Its name must match the new step identity so that callers (extraction pipeline in this file + turn.py) resolve correctly after their own renames.

**Validation:** Run `grep -n '_extract_progress_messages' ccya/engine/extraction.py` — should return zero matches. Verify `def _storytell_messages(` exists with identical signature to original. Also run `grep -n 'extract_progress_system\|extract_progress_user' ccya/engine/extraction.py` — should return zero matches for template name strings only (other references like class names or comments are handled in later phases).

#### Step 3.4 — Update call site of _storytell_messages within extraction pipeline

**File:** `ccya/engine/extraction.py`

**What:** In `_run_extraction_pipeline()` or wherever the function is called, rename: `progress_msgs = _extract_progress_messages(` → `storytell_msgs = _storytell_messages(`. Rename any local variable `progress_msgs` to `storytell_msgs`. Update template name string passed to `_render()`: `"extract_progress_system.j2"` → `"storytell_system.j2"`, `"extract_progress_user.j2"` → `"storytell_user.j2"`.

**Why:** The call site must use the new function name and variable names for consistency. Local variable renames ensure code readability matches the renamed domain concept.

**Validation:** Run `grep -n '_extract_progress_messages\|progress_msgs' ccya/engine/extraction.py` — should return zero matches (old names only). Verify `_storytell_messages(` call exists with correct arguments matching original argument list exactly.

#### Step 3.5 — Rename yield stream identifiers and log messages in extraction.py

**File:** `ccya/engine/extraction.py`

**What:** 
- Line ~621: rename `yield ("phase", {"stream": "progress"})` → `yield ("phase", {"stream": "storytell"})`.
- Lines 674, 678: rename log messages `"extract_progress LLM timeout"` → `"storytell LLM timeout"`, `"extract_progress failed: %s"` → `"storytell failed: %s"`.
- Line ~683 (or nearby): rename `yield ("phase", {"stream": "progress"})` at end of try/except block → `yield ("phase", {"stream": "storytell"})`.

**Why:** The yield statements emit phase events with `"stream"` identifiers that downstream consumers (server SSE, TV viewer) use to route data. These must match the renamed event structure or phase indicators break in UI components. Log messages use consistent terminology for traceability in event logs.

**Validation:** Run `grep -n '"progress"' ccya/engine/extraction.py` — should return zero matches for string literal `"progress"` used as stream identifier only (occurrences like `t.progress`, `new_progress` on ArcThread fields are not being renamed). Verify `"storytell"` appears at corresponding yield statement locations.

### Tests to write or update
None during refactor phase (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `docs/repomap.md` — Phase 8 handles all repomap updates together with other docs.

## Implementation — Phase 4: Pipeline orchestration (turn.py)

### Context files to load
- `ccya/engine/turn.py` (imports at top, rules call site ~line 753+, progress extractor call site ~line 620+ in extraction pipeline integration, event dict construction ~line 1320+)

### Detailed steps

#### Step 4.1 — Update imports for renamed engine modules and models

**File:** `ccya/engine/turn.py`

**What:** 
1. Import from `ccya.engine.ruling`: rename `_avg_rules_ms, _call_rules, _log_rules_outcome, _rules_messages` → `_avg_ruling_ms, _call_ruling, _log_ruling_outcome, _ruling_messages`.
2. Import renamed model: `ProgressExtractResult` → `StorytellerResult`.

**Why:** Imports must resolve to the new module and class names or turn.py fails at import time before any pipeline logic runs.

**Validation:** Run `grep -n 'from ccya.engine.rules\|_call_rules, _rules_messages\|ProgressExtractResult' ccya/engine/turn.py` — should return zero matches for old imports only. Verify new imports exist with correct names and same parameter lists as originals (no signature changes).

#### Step 4.2 — Rename ruling call site in turn.py's main pipeline loop

**File:** `ccya/engine/turn.py`

**What:** In the main turn processing function, rename:
- `rules_messages = _rules_messages(` → `ruling_messages = _ruling_messages(` (same arguments)
- `"rules"` step name string passed to event logging or LLM call → `"ruling"`
- Any variable named `rules_event` or `rules_metrics` in ruling-related code blocks → `ruling_event`, `ruling_metrics`

**Why:** The pipeline's main loop invokes the ruling step. All references must use new names for correct function resolution and consistent event logging keys.

**Validation:** Run `grep -n '_call_rules\|_avg_rules_ms\|_log_ruling_outcome' ccya/engine/turn.py` — verify only new `_call_ruling`, `_avg_ruling_ms` appear (old names should be zero). Verify `"ruling"` string appears where `"rules"` was used as step identifier.

#### Step 4.3 — Rename progress extractor call site and event keys in turn.py

**File:** `ccya/engine/turn.py`

**What:** In the extraction pipeline integration within turn.py:
- Update any references to `ProgressExtractResult` → `StorytellerResult` (type annotations, variable declarations)
- Event dict key `"progress"` or `"extract_progress"` → `"storytell"` throughout call sites and event construction
- Variable names like `progress_result`, `progress_event` → `storytell_result`, `storytell_event` where they refer to the storyteller step output

**Why:** The pipeline constructs event dicts with step identifiers as keys. These must match the new naming so that downstream consumers (evals, server, scripts) can find data under consistent keys after their own renames in Phases 5-7.

**Validation:** Run `grep -n 'ProgressExtractResult\|progress_event\|progress_result' ccya/engine/turn.py` — should return zero matches for old names only (comments or unrelated "progress" references like `state.progress` are not being renamed). Verify `"storytell"` appears as event key where appropriate.

#### Step 4.4 — Rename remaining rules-related event dict keys and variables in turn.py

**File:** `ccya/engine/turn.py`

**What:** Find all remaining occurrences of:
- Event dict key `"rules"` → `"ruling"` (e.g., `ev.get("rules")`, `event["rules"]`)
- Prompt storage key `"rules_prompt"` → `"ruling_prompt"` 
- Variable names like `prev_rules_event` or similar patterns → `prev_ruling_event`

**Why:** Event dict keys are the wire format between pipeline stages. All references to `"rules"` as a step identifier must become `"ruling"`. The prompt storage key follows the same pattern since it stores rendered prompts keyed by step name.

**Validation:** Run `grep -n '"rules"' ccya/engine/turn.py` — should return zero matches for string literal `"rules"` used as event/stream keys (occurrences in comments or unrelated contexts like "game rules" are acceptable). Verify all such occurrences now use `"ruling"`. Also run `grep -n 'rules_prompt' ccya/engine/turn.py` → verify only `"ruling_prompt"` remains.

### Tests to write or update
None during refactor phase (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `docs/repomap.md` — Phase 8 handles all repomap updates together with other docs.

## Implementation — Phase 5: Config settings + eval infrastructure

### Context files to load
- `ccya/engine/config.py` (EngineConfig dataclass fields, build_engine_config function)
- `config.yaml` (rules config section at line 12+)
- `ccya/eval/judge.py` (stream keys, event dict references)
- `ccya/eval/report.py` (_STREAM_KEYS tuple, stream processing logic)
- `ccya/eval/runner.py` (_VALID_STREAMS set, stream comparisons, event parsing)
- `ccya/eval/redundancy.py` (event key references, streams tuple)
- `ccya/eval/engine_mirror.py` (stream names list, dict keys)
- `ccya/eval/universal_asserts.py` (assert detail strings, event dict access)

### Detailed steps

#### Step 5.1 — Rename config settings in EngineConfig and build_engine_config

**File:** `ccya/engine/config.py`

**What:** 
1. In `EngineConfig` dataclass: rename `rules_temperature: float = 0.2` → `ruling_temperature: float = 0.2`. Rename `max_rules_retries: int = 1` → `max_ruling_retries: int = 1`.
2. In `build_engine_config()`: rename `cfg.get("rules", {})` → `cfg.get("ruling", {})`. Update assignment `rules_temperature=rules_t,` → `ruling_temperature=ruling_t,`. Rename `max_rules_retries=int(rules.get(...))` → `max_ruling_retries=int(ruling.get(...))`.

**Why:** Config attribute names must match the new step name so that config loading from YAML uses consistent keys. The EngineConfig fields are accessed throughout turn.py and extraction.py — all those accesses use dot notation on the config object, so only the field definitions need changing (not call sites which already use `cfg.rules_temperature` or `config.max_rules_retries`).

**Validation:** Run `grep -n 'rules_temperature\|max_rules_retries' ccya/engine/config.py` — should return zero matches for old names. Verify `ruling_temperature` and `max_ruling_retries` appear with correct defaults matching originals exactly (0.2, 1).

#### Step 5.2 — Rename rules section in config.yaml

**File:** `config.yaml`

**What:** Rename top-level YAML key `rules:` → `ruling:` at line 12+. The subsections (`temperature:`, `max_retries:`) remain unchanged since they're nested under the renamed parent key.

**Why:** Config file keys must match what `build_engine_config()` reads via `cfg.get("ruling", {})`. Mismatched YAML keys cause config loading to use defaults instead of user-specified values.

**Validation:** Run `grep -n '^rules:' config.yaml` — should return zero matches (old key only). Verify `ruling:` appears at approximately the same indentation level as original `rules:` was at line 12.

#### Step 5.3 — Rename stream keys and event references in judge.py

**File:** `ccya/eval/judge.py`

**What:** 
- Line ~534: rename tuple `("Extract Progress System Prompt", "extract_progress")` to `("Storyteller System Prompt", "storytell")`.
- Line ~558: rename mapping tuple `("progress", "extract_progress")` → `("storytell", "storytell")`. The first element is the extraction sub-stream key from event dict (`ev.get("extraction").get("progress")`), the second is the output dictionary key. Both must become `"storytell"`.
- Line ~563: rename check set `all(k in out for k in ("rules", "narrate", "extract_scene", "extract_state", "extract_progress"))` → use new keys with `"storytell"` replacing `"extract_progress"`.
- Lines ~588, 607: rename tuples like `("progress", "Extract Progress User Prompt")` or `("progress", "Extract Progress")` to `("storytell", "Storyteller User Prompt")` or `("storytell", "Storyteller")`. The first element is the extraction sub-stream key, second is display label.
- Line ~658: rename iteration `for stream in ("scene", "state", "progress"):` → `for stream in ("scene", "state", "storytell"):` to iterate over renamed extraction sub-streams from event dict's `"extraction"` key.

**Why:** The judge parses events.jsonl output using stream/event keys as lookup paths. If these don't match the renamed event structure, judges can't find data to evaluate against rubrics. Note: plain `"progress"` is the actual extraction sub-stream key in event dicts (not `"extract_progress"` or `"extract.progress"`).

**Validation:** Run `grep -n '"progress"' ccya/eval/judge.py` — should return zero matches for string literal `"progress"` used as stream or event dict keys only. Verify `"storytell"` appears at corresponding locations with correct syntax matching original tuple patterns exactly (same nesting, same number of elements).

#### Step 5.4 — Rename stream keys in report.py, runner.py, redundancy.py, engine_mirror.py; rename TurnResult.rules field on models.py

**Files:** `ccya/eval/report.py`, `ccya/eval/runner.py`, `ccya/eval/redundancy.py`, `ccya/eval/engine_mirror.py`

**What:** 
- `report.py`: Rename score keys tuple at line ~385: `("rules", "narrate", "extract_scene", "extract_state", "extract_progress")` → use new keys with `"storytell"` replacing `"extract_progress"`. The first element is the pipeline step name, not a template or class name.
- `runner.py`: Rename `_VALID_STREAMS = frozenset(("rules", ...))` at line ~194 to include renamed stream identifiers: rename `"extract.progress"` → `"storytell.extract"` (or keep as plain `"progress"` if this is just an alias — see note below). Update stream comparisons `a.stream == "extract.progress"` at line ~281 and `ev.get("extraction").get("progress")` at lines 284, 350 to use new keys. Specifically rename: `for sub in ("scene", "state", "progress"):` → `for sub in ("scene", "state", "storytell"):` at line ~350; `elif a.stream == "extract.progress":` at line ~281 with corresponding `.get("progress")` to `.get("storytell")`.
- `redundancy.py`: Rename `streams = ("rules", "narrate", "scene", "state", "progress")` → use new keys with `"storytell"` replacing `"progress"`. This tuple defines which streams redundancy analysis covers.
- `engine_mirror.py`: Stream names list at line ~45: rename `"extract.progress"` to match renamed stream identifier (same note as runner.py below). Dict key mapping at line ~55: rename `'"extract.progress": {"thread_advance", ...}'` → use new key name with same field set.

**Note on composite vs plain keys:** The string `"extract.progress"` appears in `runner.py`, `engine_mirror.py` as TurnAssert.stream_id values (used by test scenarios). These are aliases or composite identifiers that reference the extraction sub-stream `"progress"`. Rename to `"storytell.extract"` or keep consistent with whatever naming convention you choose for this alias pattern — but do NOT rename plain event dict key `"progress"` to anything other than `"storytell"`. The plain `"progress"` is what actually appears in `ev.get("extraction").get("progress")` at runtime.

**Also rename TurnResult.dataclass field `rules` → `ruling`:**
- `ccya/models.py` line ~544: rename dataclass field `rules: dict[str, Any] = {}` → `ruling: dict[str, Any] = {}`. This is the model's own field name — not just references to it. Must be renamed before or alongside all downstream access patterns like `result.rules`, `turn_result.rules`, or `data["rules"]` throughout `ccya/server/routes.py` (line ~150).

**Why:** These eval modules iterate over or compare against stream/event keys to parse event data from runs. Keys must match the renamed pipeline output structure or evaluation fails silently (missing data) or crashes (KeyError). The TurnResult.field rename on models.py itself is critical — if `TurnResult.rules` stays as-is, all downstream code accessing `result.ruling` will fail with AttributeError after routes.py tries to pass `result.ruling`.

**Validation:** For `runner.py`: run `grep -n '"extract.progress"\|\.get("progress")' ccya/eval/runner.py` — should return zero matches for old string literals only (occurrences in comments or domain concept references are acceptable). Verify `"storytell"` appears at corresponding locations with correct syntax matching original patterns exactly. For `engine_mirror.py`: run `grep -n '"extract.progress"' ccya/eval/engine_mirror.py` — same expectation.

#### Step 5.5 — Update universal_asserts.py references

**File:** `ccya/eval/universal_asserts.py`

**What:** 
- Line ~107: rename event dict access `extraction.get("progress") or {}` → `extraction.get("storytell") or {}`. This is where the beat lifecycle checker reads progress extraction output from events.
- Lines 504, 514, 522, 529: rename assertion identifiers `"universal.progress.actions_quality"` → `"universal.storytell.actions_quality"`. These are string labels in assert result dicts that identify which universal check produced the result.
- Line ~678: rename `event.get("extraction_prompt") or {}` — verify this is actually accessing extraction sub-stream data (may need to be `ev.get("extraction").get("progress") or {}` or similar; rename `"progress"` → `"storytell"` if so). The variable name `progress_user` suggests it should read from the progress/storyteller extraction output.
- Line ~709: rename assert detail string `"narration_directive computed but not rendered in extract_progress user prompt"` → `"narration_directive computed but not rendered in storytell user prompt"`.

**Why:** Universal asserts validate event data during evaluation runs. If they look for old key names or use stale assertion identifiers, assertions will fail on renamed events (finding no data under old keys) or produce confusing output labels. The plain `"progress"` is the actual extraction sub-stream key in event dicts — rename to `"storytell"`.

**Validation:** Run `grep -n '\.get("progress")\|"universal.progress' ccya/eval/universal_asserts.py` — should return zero matches for string literals used as event dict or assertion identifiers only (occurrences in comments explaining domain concepts are acceptable). Verify `"storytell"` appears at corresponding locations with correct syntax matching original patterns exactly.

### Tests to write or update
None during refactor phase (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `docs/repomap.md` — Phase 8 handles all repomap updates together with other docs.

## Implementation — Phase 6: Server components (tv.py, tv_mirror.py, metrics.py, routes.py, panels.py)

### Context files to load
- `ccya/server/tv.py` (stream-to-CSS mapping at line 21, event dict access throughout ~lines 147+, variable names like `rules_intent`, `rules_ev`)
- `ccya/server/tv_mirror.py` (stream key references in stage definitions at lines 39-94)
- `ccya/server/metrics.py` (event dict access `ev.get("rules") or {}` throughout ~lines 98-148, variable names like `rules_ev`, extraction sub-stream iteration at line 84, raw_streams["progress"] at lines 125-126)
- `ccya/server/routes.py` (event dict key `"rules": result.rules` at line 150; TurnResult.dataclass field rename on `rules: dict[str, Any]` at `ccya/models.py:544`)
- `ccya/server/panels.py` (event dict access `ev.get("rules") or {}`, `rules_map.get(...)` at lines 42, 57)
- `ccya/templates/index.html` (frontend event-stream key references at line 325: `streams.progress`, line 527: `stream === 'progress'`)

### Detailed steps

#### Step 6.1 — Rename stream-to-CSS mapping and event references in tv.py

**File:** `ccya/server/tv.py`

**What:** 
- Stream-to-CSS class mapping at line ~25: rename `"progress": "tv-stage-progress"` → `"storytell": "tv-stage-storytell"`. This is part of the `_STAGE_CSS` dict alongside `"rules": "tv-stage-rules"` which also gets renamed to `"ruling": "tv-stage-ruling"`.
- Event dict access: rename all `ev.get("progress") or {}`, `ev.get("extraction").get("progress") or {}` patterns to use new keys throughout. Specifically `ev.get("progress_prompt", {})` → `ev.get("storytell_prompt", {})` if such a key exists, or `ev.get("extraction").get("progress")` → `ev.get("extraction").get("storytell")`.
- Variable names: rename any variable like `progress_ev = ...`, `pg = ev.get(...)` where it holds progress/storyteller step data to use new naming.

**Why:** The turn viewer displays pipeline events using stream keys as lookups. CSS class mappings must match the new event structure or UI panels won't render correctly for renamed streams. The `_STAGE_CSS` dict maps stream identifiers to CSS classes — both key and value must reflect the rename.

**Validation:** Run `grep -n '"progress"' ccya/server/tv.py` — should return zero matches for string literal `"progress"` used as event/stream or CSS class keys only (occurrences in comments or domain concept references are acceptable). Verify `"storytell"` appears at corresponding locations with correct syntax matching original dict structure exactly.

#### Step 6.2 — Rename stage definitions in tv_mirror.py

**File:** `ccya/server/tv_mirror.py`

**What:** In all stage definition dictionaries:
- `key="rules"` → `key="ruling"`, `label="rules"` → `label="Ruling"` or keep label as-is if it's user-facing display text (decide based on whether this shows to end users).
- `stage_css="rules"` or similar CSS class references → `stage_css="ruling"` or `"tv-stage-ruling"`.
- `metrics_path="rules"` or `prompt_path="rules_prompt"` → `metrics_path="ruling"`, `prompt_path="ruling_prompt"`.
- Dependency arrays: `inputs=["rules"]` or `inputs=["rules", "narrate"]` etc. → `inputs=["ruling"]` or `inputs=["ruling", "narrate"]`.

**Why:** The TV mirror UI defines stages with stream keys as identifiers and dependency relationships between stages. If these don't match renamed event structure, the UI can't load or display data for renamed streams.

**Validation:** Run `grep -n 'key="rules"\|label="rules"\|inputs=\["rules"' ccya/server/tv_mirror.py` — should return zero matches for old string literals only. Verify `"ruling"` appears at corresponding locations with correct syntax matching original dict structure exactly (same keys, same nesting).

#### Step 6.3 — Rename event references in metrics.py

**File:** `ccya/server/metrics.py`

**What:** 
- Line ~84: rename iteration `for s in ("scene", "state", "progress"):` → `for s in ("scene", "state", "storytell"):` to iterate over renamed extraction sub-streams from event dict's `"extraction"` key.
- Lines 125-126: rename `raw_streams["progress"]["ms"]` and `raw_streams["progress"]["tokens_in"/"tokens_out"]` → use new keys with `raw_streams["storytell"][...]`. These access metrics for the progress/storyteller extraction sub-stream from event data.
- Event dict access at line ~98: rename `ev.get("rules") or {}` to `ev.get("ruling") or {}`, variable name `rules_ev = ...` → `ruling_ev = ...`.

**Why:** Metrics collection parses event dicts using stream/event keys. Mismatched keys cause metrics to show zero or missing data for the renamed streams, breaking observability. The plain `"progress"` is the actual extraction sub-stream key in events.jsonl — rename to `"storytell"`.

**Validation:** Run `grep -n '"progress"\|ev.get("rules")\|"rules_ev' ccya/server/metrics.py` — should return zero matches for string literals used as event/stream or dict keys only (occurrences in comments or domain concept references are acceptable). Verify `"storytell"` and `"ruling"` appear at corresponding locations with correct Python syntax matching original patterns exactly.

#### Step 6.4 — Rename event key in routes.py

**File:** `ccya/server/routes.py`

**What:** Event dict key: rename `"rules": result.rules,` → `"ruling": result.ruling,`. Verify that `result.ruling` exists or adjust to match the actual attribute name on whatever `result` object this references. If `result` is a dataclass/model with a `rules` field being renamed to `ruling`, update accordingly.

**Why:** API routes return event data keyed by step names. The response structure must use consistent keys matching what clients expect after rename.

**Validation:** Run `grep -n '"rules":' ccya/server/routes.py` — should return zero matches for old key only. Verify `"ruling"` appears at corresponding location with correct attribute access on the result object (match original attribute name exactly, just renamed).

#### Step 6.5 — Rename event references in panels.py

**File:** `ccya/server/panels.py`

**What:** 
- Event dict access: rename `ev.get("rules") or {}`, `ev.get("rules_prompt", {})` to use new keys throughout.
- Variable names like `rules = ...` or `rules_map.get(...)` where they hold ruling step data → rename to `ruling`, `ruling_map`.

**Why:** UI panels display pipeline event data keyed by stream/event identifiers. Mismatched keys cause panels to show empty or missing content for renamed streams.

**Validation:** Run `grep -n 'ev.get("rules")\|ev.get("rules_prompt"\|"rules = \|rules_map' ccya/server/panels.py` — should return zero matches for old string literals and variable names only. Verify `"ruling"` appears at corresponding locations with correct syntax matching original dict access patterns exactly.

#### Step 6.6 — Rename frontend event-stream key references in index.html

**File:** `ccya/templates/index.html`

**What:** 
- Line ~325: rename `streams.progress` → `streams.storytell`. This accesses the progress/storyteller extraction sub-stream data from SSE events to display metrics (ms, tokens_in, tokens_out).
- Line ~527: rename `stream === 'progress'` → `stream === 'storytell'`. This is a phase indicator comparison that sets UI label text ("Writing the next page…") when progress/storyteller extraction is in flight.

**Why:** The turn viewer frontend uses SSE event-stream keys to display per-step metrics and phase indicators. If these don't match renamed event structure, the UI will fail to display storyteller extraction metrics or show incorrect phase labels after rename takes effect. This is a production file that must be updated alongside backend references or the UI breaks at runtime.

**Validation:** Run `grep -n 'streams.progress\|stream === .progress' ccya/templates/index.html` — should return zero matches for old string literals only (occurrences in comments are acceptable). Verify `streams.storytell` and `stream === 'storytell'` appear at corresponding locations with correct JavaScript syntax matching original patterns exactly.

### Tests to write or update
None during refactor phase (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `docs/repomap.md` — Phase 8 handles all repomap updates together with other docs.

## Implementation — Phase 7: Scripts and debug tools (ev.py + scripts/debug/README.md)

### Context files to load
- `scripts/debug/ev.py` (stream tuple at line 28, stream comparisons `if stream == "rules"` at lines 63+, event dict access throughout ~lines 138+ through end of file, dependency arrays with `"rules"` as first element)
- `scripts/debug/README.md` (.extraction.progress reference at line 88+)

### Detailed steps

#### Step 7.1 — Rename stream keys and event references in ev.py

**File:** `scripts/debug/ev.py`

**What:** 
- Stream tuple: rename `STREAMS = ("rules", "narrate", ...)` → `("ruling", "narrate", ...)`.
- Stream comparisons: `if stream == "rules":` or `stream == "extract_progress"` → use new names. Specifically all `ev.get("rules") or {}`, `ev.get("progress") or {}`, `ev.get("extract_progress") or {}` patterns to `ev.get("ruling") or {}`, `ev.get("storytell") or {}`.
- Event dict keys: `ev.get("rules_prompt", {})` → `ev.get("ruling_prompt", {})`. `ev.get("progress_prompt", {})` or similar → use new names.
- Variable names like `rules_ev = ...`, `raw = rules_prompt.get(...)` where they hold ruling/storyteller step data → rename to `ruling_ev`, `storytell_event`, etc.
- Dependency arrays: `inputs=["rules"]` or `["narrate", "rules"]` or `["scene", "state", "extract_progress"]` patterns throughout pipeline dependency map (~lines 528+) — rename `"rules"` → `"ruling"`, `"progress"/"extract_progress"` → `"storytell"`.
- Stream comparison in path lookup: `ev.get("rules_prompt" if inp_key == "rules"...` or similar ternary expressions with stream key comparisons → use new names.

**Why:** The debug script parses events.jsonl to inspect pipeline output during development. If it looks for old event keys, it can't display data from renamed runs, making debugging impossible after the rename takes effect.

**Validation:** Run `grep -n '"rules"\|"extract_progress"' scripts/debug/ev.py` — should return zero matches for string literals used as stream or event dict keys only (occurrences in comments explaining domain concepts are acceptable). Verify `"ruling"` and `"storytell"` appear at corresponding locations with correct Python syntax matching original patterns exactly.

#### Step 7.2 — Update scripts/debug/README.md references

**File:** `scripts/debug/README.md`

**What:** 
- Rename `.extraction.progress` → `.extraction.storytell` or similar reference to progress extractor output file at line 88+.
- Any other references to "progress extractor" or "rules engine" in documentation text within this README — rename to "storyteller" and "ruling".

**Why:** Documentation for debug tools should reflect current naming so developers know what files/keys to look for when debugging. Stale names create confusion during development.

**Validation:** Run `grep -n 'progress.extractor\|extraction.progress' scripts/debug/README.md` — verify only new "storyteller" or renamed references appear at corresponding locations.

### Tests to write or update
None during refactor phase (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `docs/repomap.md` — Phase 8 handles all repomap updates together with other docs.

## Implementation — Phase 8: Documentation and architecture references

### Context files to load
All documentation, design documents, architecture docs, rubrics, evals, plans, completed plans, AGENTS.md, and repomap that contain references to `progress_extractor`, `extract_progress`, `ProgressExtractResult`, `ProgressExtractBoundary`, or pipeline-step "rules" (not domain rules).

### Detailed steps

#### Step 8.1 — Rename architecture doc step0-rules.md → step0-ruling.md

**File:** `docs/architecture/step0-rules.md→step0-ruling.md` (rename first, then edit)

**What:** 
1. `mv docs/architecture/step0-rules.md docs/architecture/step0-ruling.md`.
2. Update title: `# Step 0 — Rules / Intent Classification` → `# Step 0 — Ruling / Intent Classification`.
3. Mermaid diagram references: rename `rules_system.j2 + rules_user.j2` → `ruling_system.j2 + ruling_user.j2` in subgraph labels. Rename `stageRules` class definitions or CSS references if they use "rules" as identifier (e.g., `classDef stageRuling`).
4. Python module reference: `Python — rules.resolve_check()` stays unchanged since this refers to `ccya/rules.py` dice engine which is NOT being renamed per Firm Decision 3.

**Why:** Architecture docs describe the pipeline structure for developers reading design decisions. The doc filename and internal references must match current naming or readers navigate to non-existent files or encounter confusing terminology mismatches.

**Validation:** Run `ls docs/architecture/step0-ruling.md` — file should exist. Verify `docs/architecture/step0-rules.md` no longer exists. Check mermaid diagram renders correctly (no broken class references).

#### Step 8.2 — Update OVERVIEW.md table entries and pipeline overview

**File:** `docs/architecture/OVERVIEW.md`

**What:** 
- Table row for step 0: rename `Step 0 — Rules / Intent` → `Step 0 — Ruling / Intent`. Rename link `[step0-rules](./step0-rules.md)` → `[step0-ruling](./step0-ruling.md)`.
- Subsystem table: rename `Step 0 — Rules` → `Step 0 — Ruling`. Same link update.
- Table row for step 2c (progress extract): rename `Step 2c — Progress Extract` → `Step 2c — Storytell`. Rename doc link `[step2c-progress](./step2c-progress.md)` to keep as-is or rename if the progress doc itself gets renamed (check first).
- Pipeline overview flowchart: update any mermaid labels referencing "Rules" or "Progress Extract" step names.
- `ProgressExtractResult` references in text or tables → `StorytellerResult`.

**Why:** OVERVIEW.md is the primary navigation document for understanding pipeline architecture. All step names, model references, and doc links must reflect current naming so developers can navigate to correct subdocs without confusion.

**Validation:** Run `grep -n 'ProgressExtractResult\|step0-rules' docs/architecture/OVERVIEW.md` — should return zero matches for old names only (occurrences in historical context or completed plan references are acceptable). Verify `StorytellerResult`, `step0-ruling` appear at corresponding locations.

#### Step 8.3 — Update repomap.md references

**File:** `docs/repomap.md`

**What:** 
- Engine module table: rename `ccya/engine/rules.py` → `ccya/engine/ruling.py`. Rename function references `_rules_messages(), _call_rules()` → `_ruling_messages(), _call_ruling()`.
- Extraction field routing section: rename `ProgressExtractResult` entries to `StorytellerResult`. Update step name labels from "Progress Extract" or "progress extractor" to "storytell" or "storyteller". Rename `"rules"` stream key references in pipeline flow descriptions.
- Pipeline call sequence (5-call pipeline): update any mentions of rules/progress_extractor step names or function signatures that reference old names.

**Why:** The repomap is the developer's first stop for understanding module boundaries, public APIs, and cross-module contracts. Stale names cause developers to look in wrong files or expect non-existent functions when navigating code during implementation work.

**Validation:** Run `grep -n 'ProgressExtractResult\|_call_rules\|ccya/engine/rules.py' docs/repomap.md` — should return zero matches for old names only (occurrences in historical context or completed plan references are acceptable). Verify `StorytellerResult`, `_call_ruling`, `ccya/engine/ruling.py` appear at corresponding locations with correct descriptions matching actual current code.

#### Step 8.4 — Update AGENTS.md references

**File:** `AGENTS.md`

**What:** Navigation path reference: rename `step0-rules.md, step1-narrate.md` → `step0-ruling.md, step1-narrate.md`. Any other mentions of "progress extractor" or pipeline-step "rules" in AGENTS.md instructions text — rename to "storyteller"/"ruling".

**Why:** AGENTS.md provides runtime guidance for AI agents working on the codebase. Navigation paths must point to actual existing files with current names, or agent navigation fails at step 1 of any task.

**Validation:** Run `grep -n 'step0-rules' AGENTS.md` — should return zero matches (old name only). Verify `step0-ruling` appears at corresponding location in the navigation path text.

#### Step 8.5 — Update design docs references

**Files:** `docs/design/narration-simplification-design.md`, `docs/design/prompt-testing-and-schema-discipline.md`, `docs/design/observability-design.md`

**What:** 
- `narration-simplification-design.md`: Rename all template name references: `extract_progress_system.j2→storytell_system.j2`, `extract_progress_user.j2→storytell_user.j2`. Rename `ProgressExtractResult.beat_disposition` → `StorytellerResult.beat_disposition`. Rename `_extract_progress_messages()` → `_storytell_messages()`.
- `prompt-testing-and-schema-discipline.md`: Rename template references: `extract_progress_user.j2→storytell_user.j2`, `rules_user.j2→ruling_user.j2`. Rename class names in code blocks: `ProgressExtractBoundary→StorytellerBoundary`, `RulesBoundary→RulingBoundary`.
- `observability-design.md`: Function name reference `_call_rules` → `_call_ruling`.

**Why:** Design docs capture architectural decisions and implementation plans. Stale references create confusion when developers read design docs to understand why certain patterns or names were chosen, especially if they encounter non-existent file/function names while following links or code references.

**Validation:** For each file, run `grep -n 'ProgressExtractResult\|_call_rules\|extract_progress_\|rules_user.j2' <file>` — should return zero matches for old template/class/function name strings only (occurrences in historical context or completed plan references are acceptable). Verify new names appear at corresponding locations.

#### Step 8.6 — Update BUGS.md, step2c-progress.md, pacing-context.md

**Files:** `docs/BUGS.md`, `docs/architecture/step2c-progress.md`, `docs/architecture/pacing-context.md`

**What:** 
- `BUGS.md`: Rename template reference `extract_progress_user.j2→storytell_user.j2`.
- `step2c-progress.md`: Rename mermaid diagram references: `extract_progress_system.j2 + extract_progress_user.j2→storytell_system.j2 + storytell_user.j2`. Rename `ProgressExtractResult` → `StorytellerResult`. Update step name labels from "progress extractor" to "storyteller".
- `pacing-context.md`: Rename function reference `_extract_progress_messages()→_storytell_messages()`. Template references: `extract_progress_system.j2→storytell_system.j2`, `user.j2` and `system.j2` template names in architecture diagram nodes.

**Why:** Architecture subdocs describe specific pipeline step internals or cross-cutting concerns (pacing context). References to renamed functions, templates, or models must match current naming for these docs to remain useful as implementation references.

**Validation:** Run `grep -n 'ProgressExtractResult\|_extract_progress_messages\|extract_progress_' docs/architecture/step2c-progress.md docs/architecture/pacing-context.md` — should return zero matches for old names only (occurrences in historical context or completed plan references are acceptable). Verify new names appear at corresponding locations.

#### Step 8.7 — Update rubrics and evals references

**Files:** `evals/rubrics/default.md`, `evals/rubrics/prompt_pipeline.md`, `evals/rubrics/meta.md`

**What:** 
- `default.md`: Rename scoring key `"extract_progress:"` → `"storytell:"`. Any step name or stream identifier references in rubric instructions (e.g., "progress extraction" or "progress_extractor"). Also rename any event dict access patterns like `ev.get("progress")` or `ev["progress"]` to use new keys with `ev.get("storytell")` or `ev["storytell"]`.
- `prompt_pipeline.md`: Rename scoring keys: `extract_progress:` → `storytell:`. References to "progress extractor" in evaluation criteria text → "storyteller". Any template name references like `extract_progress_system.j2` or `extract_progress_user.j2` → rename to `storytell_system.j2` / `storytell_user.j2`.
- `meta.md`: Reference to "Progress actions pipeline" and "progress extractor" — rename terminology to match new names where it refers to the pipeline step (not domain concepts).

**Why:** Rubrics are used by LLM judges to evaluate engine output. If rubric instructions reference old stream keys or step names, judges will look for data under wrong keys in event dicts, producing false-negative evaluation scores or missing evaluations entirely.

**Validation:** Run `grep -n '"extract_progress"\|progress.extractor' evals/rubrics/default.md evals/rubrics/prompt_pipeline.md` — should return zero matches for string literals used as scoring keys or step identifiers only (occurrences in historical context or domain concept references are acceptable). Verify `"storytell"` appears at corresponding locations.

#### Step 8.8 — Update plans and completed plan references

**Files:** All markdown files under `plans/`, `plans/review/`, `plans/completed/` that contain references to `ProgressExtractResult`, `extract_progress`, `progress_extractor`, or pipeline-step "rules" (not domain rules).

**What:** For each file found:
- Rename `ProgressExtractResult→StorytellerResult`. `ProgressExtractBoundary→StorytellerBoundary`.
- Rename template name strings: `extract_progress_system.j2→storytell_system.j2`, `extract_progress_user.j2→storytell_user.j2`.
- Rename function references: `_extract_progress_messages()→_storytell_messages()`.
- Rename event/stream keys in plan text or code blocks where they reference pipeline step identifiers (not domain concepts): `"progress"/"extract_progress"` → `"storytell"`, `"rules"` → `"ruling"`.
- References to "progress extractor" or "progress extraction" as a pipeline step name → "storyteller" or "storytell".

**Why:** Plan documents are historical records of design decisions and implementation steps. Stale references create confusion when reading plans during future development or debugging, especially if they reference non-existent files/functions or use terminology that no longer matches the codebase.

**Validation:** Run `grep -rn 'ProgressExtractResult\|extract_progress' /plans/` to find all remaining occurrences before starting this step. After completion, run again — should return zero matches for old names only (occurrences in historical context or domain concept references are acceptable). Verify new names appear at corresponding locations throughout all plan files.

### Tests to write or update
None during refactor phase (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `docs/repomap.md` — updated as part of Step 8.3 above.
