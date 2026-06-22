# Phase 2 — Seed: enforce_thread_limits + prompt

## Purpose

Update `_enforce_thread_limits()` in `seed.py` to use `dormant` instead of `active`, and update the seed generation prompt to assign thread types and allow dormant threads.

## Problem Statement

`_enforce_thread_limits()` calls `object.__setattr__(t, "active", False)` which will crash after Phase 1 removes the `active` field. The seed prompt has no `type` instructions, so LLM compliance on `type` will be near zero.

## Constraints

- Seed prompt must work with both old arc packs (no `type` field) and new ones.
- Thread count limits still apply: max 2 non-dormant threads at seed time.

## Non-goals

- No changes to turn processing, sanitizer, or any other system — covered in later phases.

## Solution

Replace `active` with `dormant` in `_enforce_thread_limits()`, flip the limiting logic (cap non-dormant threads, not active ones). Update `generate_seed_system.j2` with type assignment instructions and mixed-type enforcement, and add dormant thread examples.

## Firm decisions

1. Max 2 non-dormant threads at game start (was max 2 active threads).
2. Non-dormant threads with `urgency: "urgent"` are allowed (was active+urgent). Dormant threads forced to background.
3. At least one thread with `type == "threat"`, at least one thread with `type != "threat"`.
4. Dormant threads allowed in seed: represent hidden tensions, secrets, foreshadowing.

## Risks, Ambiguities, and Blockers

- **Dormant thread urgency:** Dormant threads at seed time should have `urgency: "background"`. The existing code sets non-active threads to background already. For dormant threads, the same logic applies — excess dormant threads (beyond 3) get the same treatment. This is consistent.
- **Thread count semantics:** The old comment says "max 2 active threads." The new logic caps "non-dormant" threads. Dormant threads are not capped (up to 3 per old code). The variable names change but the behavior is the same.

## Status

`open`

## Implementation — Phase 2: Seed: enforce_thread_limits + prompt

### Context files to load

- `ccya/engine/seed.py:359-396` — `_enforce_thread_limits()`
- `ccya/prompts/generate_seed_system.j2:137-154` — Thread rules section

### Detailed steps

#### Step 2.1 — Update inline thread limit enforcement in seed.py

**File:** `ccya/engine/seed.py:359-396`

**What:** This is inline code inside `generate_seed()` (not a standalone function). Replace all `active` references with `dormant`:
- `getattr(t, "active", True)` → `not getattr(t, "dormant", False)`
- `not getattr(t, "active", False)` → `getattr(t, "dormant", False)`
- `object.__setattr__(t, "active", False)` → `object.__setattr__(t, "dormant", True)`
- Update log line to say "non_dormant" instead of "active"
- Update comment to say "enforce hard limits on non-dormant threads and urgency"

**Why:** `active` field removed in Phase 1. Without this, `__setattr__` will raise `AttributeError`.

**Validation:** `.venv/bin/python -c "import ast; ast.parse(open('ccya/engine/seed.py').read()); print('syntax OK')"` — also run `make check`.

#### Step 2.2 — Add type rules to seed prompt

**File:** `ccya/prompts/generate_seed_system.j2:137-154`

**What:** Add after existing thread quality guidance (after line 154):
- Instruct LLM to assign `type` to each thread: `"threat"`, `"opportunity"`, `"complication"`, or `"revelation"`.
- Enforce: at least one thread with `type == "threat"`, at least one thread with `type != "threat"`.
- Update the thread JSON examples to include `type` and `dormant` fields instead of `active`.
- Update thread count section: `active: true` → `dormant: false`, `active: false` → `dormant: true`.
- Allow dormant threads (hidden secrets, hidden opportunities, foreshadowing) with note that dormant threads represent tensions that have faded but can be reactivated.

**Why:** LLM needs explicit instructions and examples to emit the new fields. Without examples in the JSON schema section, compliance will be low.

**Validation:** Manually inspect the rendered prompt by running a seed generation through ev.py or curl the local server. No automated test for prompt text.

### Tests to write or update

No tests currently. Run `make check` for type/lint.

## Status

completed
