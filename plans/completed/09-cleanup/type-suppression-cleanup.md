# Type suppression cleanup — remove unnecessary `# type: ignore` / `# noqa`

## Status
`completed`

## Phases

2 phases: remove obsolete `# noqa` in rules.py, then fix remaining fixable suppressions and document unavoidable ones.

## Issue

9 `# type: ignore` / `# noqa` suppression comments across 6 source files, most without inline rationale per AGENTS.md rule ("No `# noqa` / `# type: ignore` unless absolutely unavoidable — document why inline"). One suppression masks a forward-reference pattern that's already handled by `from __future__ import annotations`. Others silently swallow real type mismatches that could be properly fixed.

## Solution

Phase 1: Remove the unnecessary `# noqa: F821` in `rules.py` — `from __future__ import annotations` already makes string annotations safe. Phase 2: Fix each fixable type-suppression bug (narrow types in `names.py`, fix return-type handling in `cli.py` and `tv_mirror.py`) and add inline rationale comments for the 3 genuinely unavoidable suppressions.

## Firm decisions

- `# type: ignore[misc]` on the 7-tuple yields in `turn.py` and `extraction.py` are unavoidable — the type checker cannot express heterogeneous generator yields. Add inline rationale.
- `from __future__ import annotations` is the preferred fix for forward references, not `TYPE_CHECKING` guards.
- All remaining suppressions have concrete fixes available (type narrowing, cast, return-type refinement).

## Non-goals

- No behavioral changes beyond type annotations and suppression comments.
- No refactoring the generator tuple types in extraction/turn (that's a separate effort).
- No adding `TYPE_CHECKING` blocks unless absolutely necessary.

## Risks, Ambiguities, and Blockers

- `_get_nested` in `tv_mirror.py` returns `dict | str | list | None` but mypy disagrees because the chain of `dict.get()` returns `Any`. The return type annotation may need adjustment rather than a cast.
- `args.func(args)` return type in `cli.py` is genuinely `Any` — the fix is to type-narrow or accept `Any` in the return annotation.

## Implementation — Phase 1: Remove obsolete `# noqa` in rules.py

### Context files to load

- `ccya/rules.py`

### Detailed steps

#### Step 1.1 — Remove `# noqa: F821`

**File:** `ccya/rules.py:178`

**What:** Remove the `# noqa: F821` trailing comment from the `resolve_check` return annotation. The file already has `from __future__ import annotations` at line 13, so `"RulesOutcome"` is never evaluated at runtime and F821 should not fire.

**Why:** Dead suppression comment violates AGENTS.md clean code rules.

**Validation:** `ruff check ccya/rules.py` passes without F821.

### REPOMAP updates required

None.

## Implementation — Phase 2: Fix remaining fixable suppressions

### Context files to load

- `ccya/engine/names.py` (lines 33-56)
- `ccya/eval/cli.py` (lines 334-335)
- `ccya/server/tv_mirror.py` (lines 103-113)
- `ccya/engine/turn.py` (line 1187)
- `ccya/engine/extraction.py` (line 795)
- `ccya/server/app.py` (line 125)

### Detailed steps

#### Step 2.1 — Fix names.py type suppressions

**File:** `ccya/engine/names.py:33-34,56`

**What:** Three suppressions:
- Lines 33-34: `Faker(entry["locale"])` — `entry` is `dict[str, Any]` so `entry["locale"]` is `Any`. Fix: cast to `str` via `str(entry["locale"])` or use `cast(str, entry["locale"])`.
- Line 56: `Kakasi()` — untyped third-party constructor. Fix: add inline comment documenting why the ignore is unavoidable.

**Why:** Lines 33-34 are fixable type-narrowing bugs, not structurally unavoidable.

**Validation:** `mypy ccya/engine/names.py` passes.

#### Step 2.2 — Fix cli.py return-type suppressions

**File:** `ccya/eval/cli.py:334-335`

**What:** Two `# type: ignore[no-any-return]` sites. `asyncio.run(args.func(args))` and `args.func(args)` return `Any`. Fix: change the function return annotation to accept `Any` rather than suppressing.

**Why:** The return type from argparse dispatch is genuinely dynamic. The annotation should match reality.

**Validation:** `mypy ccya/eval/cli.py` passes.

#### Step 2.3 — Fix tv_mirror.py return-type suppression

**File:** `ccya/server/tv_mirror.py:113`

**What:** `_get_nested` return type is `dict[str, Any] | str | list[Any] | None` but mypy sees `Any` from the `dict.get()` chain. Fix: adjust the return annotation or add a `cast()` call at the return site.

**Why:** The return type contract is correct; the suppression masks a type-narrowing limitation.

**Validation:** `mypy ccya/server/tv_mirror.py` passes.

#### Step 2.4 — Document unavoidable suppressions

**File:** `ccya/engine/turn.py:1187`, `ccya/engine/extraction.py:795`, `ccya/server/app.py:125`

**What:** Add inline comments explaining why each suppression is unavoidable:
- `turn.py:1187` — 7-tuple unpack from async generator, mypy cannot express heterogeneous yields
- `extraction.py:795` — 7-tuple yield from async generator, same reason
- `app.py:125` — Late import is required for FastAPI route registration; circular import if done earlier

**Why:** AGENTS.md requires inline rationale for all unavoidable suppressions.

**Validation:** `make check` passes.

### REPOMAP updates required

None.
