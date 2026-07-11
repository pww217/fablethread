---
title: Dice intensity guidance and genre-generic band directives
status: done
completed: 2026-07-11
urgency: 3
size: small
created: 2025-07-09
ticket_id: I-39
labels: [dice, narration]
design:
plan:
pr:
  url:
  branch:
---

## Description

The dice system was only affecting roll difficulty. This improvement adds prose intensity guidance so the specific die value (1-12) shapes how the narrator describes outcomes, and makes band directives genre-generic.

## Changes Made

### Prose intensity guidance (`narrate_user.j2`)

Added guidance telling the narrator to shape prose tone based on the specific die value passed via `dice[0]`:

| Die | Intensity |
|-----|-----------|
| 12 | Exceptional — character does something remarkable, beyond what was asked |
| 11 | Effortless — total control, clean execution |
| 10-9 | Competent — character knows what they're doing |
| 7-6 | Hard-won — character has to work for it |
| 5-4 | Precarious — character is outmatched |
| 3-2 | Hopeless — character has no control |
| 1 | Catastrophic — situation has collapsed entirely |

This sits on top of the band directive — same band but different prose flavor depending on the die.

### Genre-generic band directives (`rules.py`)

- **crit_fail**: Changed "You are left in a worse position" → "much worse position" (stronger)
- **crit_success**: Changed "gain a small additional benefit" → "gain an unexpected bonus beyond what was asked" (differentiates from plain success)
- **crit_fail**: Removed "Gain a condition: wounded, bleeding, or exhausted" (assumed combat) → "You are left in a much worse position than before you acted" (genre-generic)
- **partial**: Removed "a wound taken" → "a complication started" (genre-generic)
- **_DIRECTIVE_TABLE default**: Removed specific condition examples ("a wound, a resource, leverage given") → "must be named concretely" (genre-generic)

## Verification

- Narrator receives `dice[0]` — no code changes needed for this field
- Band directives are used by `build_directive()` in `rules.py` — verified genre-generic
- Intensity guidance is in `narrate_user.j2` — verified no overlap with band directives (band = what happens, intensity = how it's written)

## Testing

Verified 2026-07-11 against noir-1930s and zombie-survival 20-turn evals:

### What works ✅

- **Dice intensity prose** — confirmed via turn-level inspection:
  - Turn 6 (zombie, d12=12, crit_success): "surgical precision", "math is flawless", "airtight indictment" — exceptional tone ✓
  - Turn 2 (zombie, d12=2, fail): "screen stalls", "refuses your access attempts" — hopeless tone ✓
  - Turn 19 (zombie, d12=3, fail): "coordination fails you completely", "violent tremors", "jerks aimlessly" — catastrophic tone ✓
- **Band directives genre-generic** — GM_MOVES for crit_fail/fail/setback/success/crit_success are genre-generic ✓
- **Intensity guidance** present in `narrate_user.j2:81`, no overlap with band directives ✓

### Minor cleanup needed (deferring)

- `_DIRECTIVE_TABLE` combat category (setback line 101, partial line 108) still has "**wound**" references:
  - Setback/combat: `"You land the blow but take a wound or lose ground."`
  - Partial/combat: `"You succeed but at a cost — a resource spent, a wound taken, or a complication started."`
- These are narrow edge cases (only on combat partials/setbacks) and not blocking. Can be addressed in a follow-up.

### Rolls and bands

`roll_band_consistency` checker passes across all tested turns. `directive_tone_match` (LLM) passes on the noir-1930s eval. Narration tone correlates with die value severity in direct inspection.
