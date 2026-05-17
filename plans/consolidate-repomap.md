# Consolidate REPOMAP into lean signpost

## Status
`open`

## Phases

1 phase: Replace 14 REPOMAP files with a single ~200-line `repomap.md` that keeps module boundaries, public APIs, cross-module contracts, and the state shape reference. Drop internal function signatures, model field listings, and implementation detail duplication. Update AGENTS.md navigation table accordingly.

## Issue

The 14-file REPOMAP is too heavy to maintain. It duplicates source code (every internal function signature with full parameter lists, every Pydantic model field-by-field) rather than serving as a signpost. Maintenance cost grows linearly with code changes — after any minor refactor, all the right files must be updated. For an AI agent, this volume also wastes tokens loading content that's already in the source.

## Solution

Consolidate into one `repomap.md` (~200 lines) at signpost level: module index (file → responsibility), public API surface (function names + 1-liner purpose only), cross-module data flows/contracts, and the state shape reference. Drop internal function signatures, model field listings, eval/judge internals, server panel/viewer internals, seed generation internals that duplicate engine.md content, generic helper functions, test-only mock functions, and prompt template descriptions (those belong in prompts/). Update AGENTS.md to reflect the new single-file structure.

## Firm decisions
1. Single file: `docs/REPOMAP/repomap.md` replaces all 14 existing files.
2. Keep signpost-level content only — module boundaries, public APIs, cross-module contracts, state shape.
3. Drop internal function signatures with full parameter lists (those are in the code).
4. Drop model field-by-field listings except for models with non-obvious behavior (GMBeat validation, CompactorSanitizationResult coercion).
5. Add new content: error propagation path, scene pressure lifecycle, arc thread state machine, token budget cascade.

## Non-goals
- Do not add per-module internal function documentation.
- Do not document prompt template contents (that belongs in prompts/ or a separate doc).
- Do not change any source code — this is docs-only.
- Do not reorganize the actual codebase structure.

## Risks, Ambiguities, and Blockers
- The consolidated file must be short enough to load quickly but comprehensive enough that AGENTS.md cross-references still work. ~200 lines target.
- Some content from `eval.md` (judge internals) may be too niche for a signpost — if the eval module is rarely touched, keep it minimal or drop entirely.
- The state shape YAML in `state.md` (~65 lines) is the most frequently referenced section. It must stay intact.

## Implementation — Phase 1: Consolidate REPOMAP

### Context files to load
All 14 existing REPOMAP files, AGENTS.md (to update navigation table), and optionally `ccya/models.py`, `ccya/engine/__init__.py` for quick verification of public symbols.

### Detailed steps

#### Step 1.1 — Write consolidated repomap.md

**File:** `docs/REPOMAP/repomap.md`

**What:** Create a single ~200-line file with these sections:
1. **Module index table** (file → responsibility, one line each) — from directory.md + engine.md package structure
2. **Public APIs by module** (function names + 1-liner purpose only) — distilled from all files
3. **Cross-module contracts** (new content): error propagation path, scene pressure lifecycle, arc thread state machine, token budget cascade
4. **State shape reference** (complete YAML from state.md:37-115) — critical reference, keep intact
5. **Type aliases** (SkillName, Band, etc.) — from models.md + rules.md

Keep only model field listings for GMBeat and CompactorSanitizationResult (non-obvious validation behavior). Drop all other per-model field docs.

Drop entirely: eval/judge internals (`eval.md` internal functions), server panel/viewer internals (`server.md` `_tv_parse_json_blob`, etc.), seed generation internals that duplicate engine.md, generic helpers (`_build_jinja_env`, `_render`, etc.).

**Why:** Signpost-level content answers "where do I look?" without duplicating what's in the code. Cross-module contracts fill gaps no single file documents alone. The state shape must stay because it's the canonical reference for GameState structure.

**Validation:** File should be ~180-220 lines. Every section answerable with a quick scan. No internal function signatures with full parameter lists. State shape YAML complete and accurate.

#### Step 1.2 — Update AGENTS.md navigation table

**File:** `AGENTS.md` (in workspace root)

**What:** Change the cross-cutting tasks table from referencing multiple REPOMAP files to pointing at the single consolidated file:
```markdown
- Modify turn pipeline → `docs/REPOMAP/repomap.md` (engine section + state contracts)
- Add new config option → `docs/REPOMAP/repomap.md` (config section)
... etc.
```

Also update the "Working on... Read..." table at the end to reference `repomap.md` with section names instead of individual files, e.g.:
```markdown
| Working on... | Section in repomap.md |
|---|---|
| Turn pipeline, extractors, retry | Module index + Engine public APIs + State contracts |
| State persistence, apply_delta | Module index + Public APIs (state/) + State shape reference |
```

**Why:** AGENTS.md is the entry point. It must reflect the new single-file structure so agents know where to look.

#### Step 1.3 — Delete old REPOMAP files

**Files:** All 14 existing `docs/REPOMAP/*.md` except `repomap.md` (which we just created).

**What:** Remove:
- `config.md`, `directory.md`, `engine.md`, `eval.md`, `frontend.md`, `llm_client.md`, `models.md`, `pack.md`, `prompts.md`, `rules.md`, `seed.md`, `server.md`, `state.md`, `testing.md`

**Why:** Eliminate duplication. The consolidated file is the single source of truth now.

### Tests to write or update
None — this is documentation-only. Verify accuracy by spot-checking 3-4 sections against actual source code (e.g., verify public API surface in `ccya/engine/__init__.py` matches what we document).

### REPOMAP updates required
This IS the REPOMAP update. After completion, AGENTS.md points to the new structure. No further REPOMAP maintenance needed beyond this consolidation.
