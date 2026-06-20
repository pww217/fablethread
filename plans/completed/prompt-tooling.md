# Prompt Tooling Improvements

## Purpose

Fix the tooling gaps that allowed the 02b42e4e template regressions to go undetected, and make future template validation reliable.

## Problem Statement

`prompt-eval dump` uses `build_prompt_context()` which builds context independently of the engine's `_*_messages()` functions. When these diverge (as they did for narrate's missing `inventory`/`location`/`conditions` and scene's missing `pc_name`), template bugs pass validation. Additionally, the tool lacks a `--user-only` flag, cross-stream batch dumping, and context-variable contract documentation — all of which would have caught the regressions earlier.

## Constraints

- Do not change the engine's `_*_messages()` functions — only improve the tooling and documentation.
- Keep `prompt_eval.py` CLI interface backward-compatible (new flags only, no removed flags).

## Non-goals

- CI or pre-commit hook setup — infrastructure concern outside prompt tooling.
- Changing how the engine builds context (that's Plan 1).
- Adding LLM-based checkers or golden-file comparisons.

## Solution

Four improvements: `--user-only` flag, `--all` batch mode, section template contract annotations, and cross-reference doc that maps every section template to its callers and required variables.

## Firm decisions

1. `build_prompt_context()` remains as-is for now — fixing it to match engine context exactly is deferred. Instead, add a `--engine-dump` mode that instruments the real engine.
2. Variable contracts live as Jinja2 comments at the top of each section template.

## Risks, Ambiguities, and Blockers

- `--engine-dump`: Requires the engine to be runnable in "dump mode" without making LLM calls. This may require extracting the context-building logic from the `_*_messages()` functions into a separate pure function.

## Status
`completed` — Phases 1, 3, 4 executed. `make check` passes. Phase 2 (engine-dump) deferred — requires extracting context builders from all 5 engine functions, which is a larger refactor.

## Phases

4 phases: CLI flags, engine-dump mode, section contracts, cross-reference doc.

---

## Implementation — Phase 1: CLI improvements

### Context files to load
- `ccya/ev/prompt_eval.py`
- `ccya/ev/__init__.py`

### Detailed steps

#### Step 1.1 — Add `--user-only` flag to `prompt-eval dump`

**File:** `ccya/ev/prompt_eval.py` (`cmd_prompt_eval_dump()`)

**What:** Add `user_only: bool = False` parameter. When `True`, skip printing the system prompt — only render and print the user prompt. Add `--user-only` to the flag parsing in `cmd_prompt_eval()`.

**Why:** During template iteration, the system prompt is large and stable — re-reading it every dump wastes tokens and scrolling. The user explicitly requested this.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream narrate --user-only` should print only the USER section, no SYSTEM section.

#### Step 1.2 — Add `--all` flag for batch dump across all 5 streams

**File:** `ccya/ev/prompt_eval.py` (`cmd_prompt_eval_dump()` or new function)

**What:** When `--all` is set, iterate over all 5 stream names (`ruling`, `narrate`, `scene`, `state`, `storytell`) and dump each in sequence, separated by stream headers.

**Why:** Running 5 separate commands to validate a single turn is tedious and often skipped. A single `--all` flag makes pre-commit validation trivially easy: `prompt-eval dump saves/default --turn 3 --all --user-only`.

**Validation:** `prompt-eval dump saves/default --turn 3 --all --user-only` should print all 5 user prompts sequentially.

#### Step 1.3 — Add stream labels in batch output

**File:** `ccya/ev/prompt_eval.py`

**What:** Each stream in batch output should be clearly delimited:
```
===== Turn 3 — ruling (user) =====
...
===== Turn 3 — narrate (user) =====
...
```

**Why:** Without labels, batch output is an undifferentiated wall of text.

**Validation:** Visual inspection.

---

## Implementation — Phase 2: Engine-dump mode

### Context files to load
- `ccya/ev/prompt_eval.py`
- `ccya/engine/ruling.py` (`_ruling_messages()`)
- `ccya/engine/narrate.py` (`_narrate_messages()`)
- `ccya/engine/extraction/scene.py` (`_extract_scene_messages()`)
- `ccya/engine/extraction/state.py` (`_extract_state_messages()`)
- `ccya/engine/extraction/storytell.py` (`_storytell_messages()`)

### Detailed steps

#### Step 2.1 — Extract context-building logic from engine functions

**File:** One new function per stream, e.g. `ccya/engine/ruling.py` → `build_ruling_context()` (separate from `_ruling_messages()`)

**What:** For each of the 5 engine `_*_messages()` functions, extract the context dict building into a standalone pure function that takes only the input parameters (not the Jinja env or message construction). The function returns just the context dict. Then call it from both the messages function and from `prompt_eval.py`.

Example for ruling:
```python
def build_ruling_context(
    state: dict[str, Any],
    user_input: str,
    *,
    turn_no: int = 0,
    npc_roster: list[dict[str, Any]] | None = None,
    inventory: list[dict[str, Any]] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
    scene_phase: str = "SETUP",
) -> dict[str, Any]:
    pc = state.get("pc") or {}
    location = state.get("location") or {}
    arc = state.get("arc") or {}
    threads = arc.get("threads") or []
    urgent_threads = [
        {"id": t.get("id", ""), "summary": t.get("summary", ""), "progress": t.get("progress", [])}
        for t in threads if t.get("urgency") == "urgent"
    ]
    return {
        "pc": pc,
        "location": location,
        "user_input": user_input,
        "meta": {"turn": turn_no},
        "npc_roster": npc_roster or [],
        "inventory": inventory or [],
        "recent_turns": recent_turns or [],
        "scene_phase": scene_phase,
        "urgent_threads": urgent_threads,
        "state": state,
    }
```

Then `_ruling_messages()` calls `build_ruling_context()` and passes the result to `_render()`.

**Why:** This eliminates the divergence between `build_prompt_context()` in `prompt_eval.py` and the engine's actual context. The prompt-eval tool simply calls the engine's own context builder. Any future changes to engine context automatically propagate to the validation tool.

**Validation:** `prompt-eval dump saves/default --turn 3 --stream ruling --engine-dump` should produce the same user prompt as the non-engine-dump mode (after Phase 1 template fixes are applied).

#### Step 2.2 — Add `--engine-dump` flag to `prompt-eval dump`

**File:** `ccya/ev/prompt_eval.py`

**What:** When `--engine-dump` is set, call the engine's `build_*_context()` function instead of `build_prompt_context()`. This requires importing the engine context builders and passing the full event data.

The `--engine-dump` path needs to reconstruct the input parameters that the engine context builder expects: state snapshot, turn number, NPC roster, inventory, recent turns, etc. Most of these can be extracted from the event data (same way `build_prompt_context()` does it).

**Why:** Validates templates against the actual engine context, not a parallel implementation that may diverge.

**Validation:** Run both `--engine-dump` and standard dump on the same turn/stream — outputs should be identical (after Phase 1 template fixes).

---

## Implementation — Phase 3: Section template variable contracts

### Context files to load
- All files in `ccya/prompts/sections/`

### Detailed steps

#### Step 3.1 — Add contract comments to all section templates

**Files:** `ccya/prompts/sections/_inventory.j2`, `_conditions.j2`, `_location.j2`, `_npc_roster.j2`, `_thread_list.j2`, `_arc.j2`, `_recent_turns.j2`, `_world_state.j2`, `_pc_header.j2`

**What:** Add a comment block at the top of each section template listing:
- Expected context variables (required vs optional)
- Fallback behavior for optional variables
- Whether the template emits its own header

Example for `_inventory.j2`:
```jinja2
{# _inventory.j2
   Required: none (renders "Nothing of note." if empty)
   Optional: inventory (list[dict]) — falls back to state.inventory
   Emits: ## Inventory header
#}
```

**Why:** Creates a single source of truth for what each section template expects. Makes it impossible to change a section template's contract without updating the comment.

**Validation:** Each file should have a comment block listing variables and fallbacks.

---

## Implementation — Phase 4: Cross-reference documentation

### Context files to load
- `ccya/engine/ruling.py`, `narrate.py`, `extraction/scene.py`, `extraction/state.py`, `extraction/storytell.py`
- All section templates
- `docs/repomap.md`
- `docs/architecture/` step docs

### Detailed steps

#### Step 4.1 — Create caller-context matrix

**File:** `docs/architecture/prompt-variable-contracts.md`

**What:** Document a matrix mapping every user template to:
- Which section templates it includes
- What context variables it passes to each include
- What the caller's parent function is (`_ruling_messages()`, etc.)

Example format:
```markdown
| Section template | Callers | Required vars | Optional vars | Emits header |
|---|---|---|---|---|
| `_inventory.j2` | ruling, narrate, extract_state, storytell | — | inventory (→state.inventory) | ## Inventory |
| `_conditions.j2` | ruling, narrate, extract_state, storytell | — | conditions | ## active_conditions |
```

And a reverse map:
```markdown
| Caller | Template | Vars passed | Section includes |
|---|---|---|---|
| `_ruling_messages()` | `ruling_user.j2` | pc, location, meta, npc_roster, inventory, recent_turns, scene_phase, urgent_threads, state | `_pc_header.j2`, `_conditions.j2`, `_inventory.j2`, `_recent_turns.j2` |
```

**Why:** This document would have caught every regression in 02b42e4e — it's immediately obvious that narrate doesn't pass `inventory`/`location`/`conditions` at top level, and that scene doesn't pass `pc_name`.

**Validation:** Matrix matches actual source code. Update whenever a template or context changes.
