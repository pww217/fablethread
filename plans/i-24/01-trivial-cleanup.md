# Phase 01: Trivial cleanup — dead code, dead file, inline imports

**Depends on:** None
**Status:** implemented
**Ticket:** I-24

## Purpose

Remove dead code, dead files, and inline imports. Zero behavioral change.

---

## Task 01-01: Delete dead function `_is_named()` from seed.py

**File:** `ccya/engine/seed.py`
**Lines:** 25-34

**What:** Delete the `_is_named()` function (10 lines).

**Why:** Validated as dead code (#2). Zero callers anywhere in the codebase.

**Validation:** `rg -n "_is_named" ccya/` returns no results.

---

## Task 01-02: Delete dead function `_soft_validate_seed()` from seed.py

**File:** `ccya/engine/seed.py`
**Lines:** 205-211

**What:** Delete the `_soft_validate_seed()` function (7 lines).

**Why:** Validated as dead code (#2). Zero callers. No-op function returning empty list.

**Validation:** `rg -n "_soft_validate_seed" ccya/` returns no results.

---

## Task 01-03: Delete dead function `_recent_turn_count()` from _pacing.py

**File:** `ccya/engine/_pacing.py`
**Lines:** 325-327

**What:** Delete the `_recent_turn_count()` function (3 lines).

**Why:** Validated as dead code (#2). Zero callers. Returns hardcoded `1`.

**Validation:** `rg -n "_recent_turn_count" ccya/` returns no results.

---

## Task 01-04: Delete dead file `ccya/mysession_types.txt`

**File:** `ccya/mysession_types.txt`

**What:** Delete the file.

**Why:** Validated as dead file (#13). Contains stray shell error output `zsh:1: command not found: python`.

**Validation:** File no longer exists.

---

## Task 01-05: Delete dormant module `ccya/models/compactor.py`

**File:** `ccya/models/compactor.py`

**What:** Delete the file.

**Why:** Validated as dormant (#14). Zero callers. Docstring: "Dormant compactor models."

**Validation:** `rg -n "compactor\|CompactorSanitizationResult" ccya/` returns no results.

---

## Task 01-06: Move inline `import traceback` to module top in turn.py

**File:** `ccya/engine/turn.py`

**What:** Add `import traceback` to the module-level imports. Remove `import traceback` from lines 256 and 434 (inside `except` blocks).

**Why:** Validated as anti-pattern (#11). Imports should be at module top.

**Validation:** `rg -n "import traceback" ccya/engine/turn.py` returns line 1 (module top only).

---

## Task 01-07: Move inline `import json` to module top in panels.py

**File:** `ccya/server/panels.py`

**What:** Add `import json` to the module-level imports. Remove inline `import json` from lines 32, 104, 152.

**Why:** Validated as broken convention (#12). All imports should be at module top.

**Validation:** `rg -n "import json" ccya/server/panels.py` returns only the module-level import line.

---

## Task 01-08: Move inline `import json` to module top in routes.py

**File:** `ccya/server/routes.py`

**What:** Remove `import json as _json` from line 707. The module-level `import json` at line 6 already exists.

**Why:** Validated as broken convention (#12). Inline import redundant with existing module-level import.

**Validation:** `rg -n "import json" ccya/server/routes.py` returns only line 6 (module level).

---

## Phase verification

Run `make check` — lint + typecheck must pass.
