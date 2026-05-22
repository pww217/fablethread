# Remove dead code: pack_gen.py

## Status
`open`

## Phases

1 phase — remove unused `pack_gen.py` and its re-export from engine package.

## Issue

`ccya/engine/pack_gen.py` is completely inert dead code. It's imported in `engine/__init__.py` and re-exported, but zero callers exist anywhere: not routes, not tests, not evals, not other modules. The active pack generation system is `ccya.engine.generate_pack`.

## Solution

Delete the file and remove its import/re-export from `__init__.py`. Clean up any stale references in docs or repomap.

## Firm decisions

- Delete `pack_gen.py` entirely — no migration needed, zero callers.
- Remove only the pack_gen import line and re-export; leave all other engine exports untouched.

## Non-goals

- Do not modify `generate_pack.py` or its behavior.
- Do not touch scenario.yaml pool parity (separate issue).
- Do not write tests or run lint/typecheck per AGENTS.md rules.

## Risks, Ambiguities, and Blockers

None — grep confirms zero callers outside the re-export line.

---

## Implementation — Phase 1: Remove pack_gen.py and its re-export

### Context files to load
- `ccya/engine/__init__.py` (full file)

### Detailed steps

#### Step 1.1 — Delete pack_gen.py

**File:** `ccya/engine/pack_gen.py`

**What:** Delete the entire file. It is dead code with zero callers.

**Why:** Removes unused module from codebase; no functional impact since nothing imports or calls it.

**Validation:**
```bash
grep -rn "from ccya.engine.pack_gen\|import pack_gen" --include="*.py" | grep -v "__init__.py"
# Should return zero results (only __init__.py reference remains, to be removed next)
```

#### Step 1.2 — Remove import and re-export from engine/__init__.py

**File:** `ccya/engine/__init__.py`

**What:** 
- Delete line: `from ccya.engine.pack_gen import generate_pack` (line 10)
- Delete `"generate_pack",` from the `__all__` list (line 45)

**Why:** Clean up stale re-export of deleted module.

**Validation:**
```bash
grep -n "pack_gen" ccya/engine/__init__.py
# Should return zero results
python3 -c "from ccya.engine import generate_seed, run_turn; print('import ok')"
# Should still work — all live exports intact
```

### Tests to write or update

None per AGENTS.md (tests temporarily removed during refactor).

### REPOMAP updates required

- `docs/repomap.md` — remove pack_gen.py from the Engine section if it's listed there.
