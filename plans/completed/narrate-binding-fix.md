# Narrate BINDING block fix

## Status
open

## Issue

The auto-checker (`universal_asserts.py:213`) expects the literal string `"rules_outcome (BINDING"` in the rendered narrate user prompt on **every** turn where `rolled=true`. But the Jinja template (`narrate_user.j2:75`) only emits this block when `rules_outcome.band == "fail"`. This causes false-positive auto-checker failures on successful/partial rolls.

Root cause discovered during planning: FINDINGS.md listed this as "rules_outcome never reaches Narrator" but the wiring (`turn.py:991`, `narrate.py:81`) is correct — both `rules_outcome` and `pacing_context` are already injected. The sole gap is the template condition.

## Solution

Widen the BINDING block guard from `band == "fail"` to cover all rolled turns. Update the block text to be band-agnostic (it's a generic binding instruction, not fail-specific). The template already has per-band directive text at line 69.

## Phases

1 phase.

## Firm decisions

- The BINDING block should appear on **every** rolled turn regardless of band.
- The existing `{{ rules_outcome.directive }}` at line 69 already provides band-specific guidance; the BINDING block is for a meta-instruction about LLM behavior.

## Non-goals

- NOT restructuring the ruling pipeline.
- NOT modifying `turn.py` or `narrate.py` beyond what's needed.
- NOT changing auto-checker assertions.

## Risks

- LLMs may interpret a generic BINDING block differently than a fail-specific one. Mitigation: the text is already in the prompt; we're just making it appear more often. Meta-eval on the next run will catch any behavioral shift.

## Implementation — Phase 1: Template fix

### Context files to load

- `ccya/prompts/narrate_user.j2`
- `ccya/eval/universal_asserts.py` (lines 210-225)

### Detailed steps

#### Step 1.1 — Widen BINDING block condition

**File:** `ccya/prompts/narrate_user.j2:75-78`

**What:** Change the Jinja if-condition from:
```
{% if rules_outcome and rules_outcome.rolled and rules_outcome.band == "fail" -%}
```
to:
```
{% if rules_outcome and rules_outcome.rolled -%}
```

**Why:** The auto-checker contracts for ALL rolled turns, not just fail bands. The band-specific guidance already lives in `{{ rules_outcome.directive }}` on line 69.

**Validation:** `make check`

#### Step 1.2 — Update BINDING block text

**File:** `ccya/prompts/narrate_user.j2:77`

**What:** Replace the fail-specific sentence with a band-agnostic instruction:
```
**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.
```

**Why:** The old text only made sense for fail bands.

**Validation:** `make check`
