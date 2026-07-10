---
title: Dice intensity guidance and genre-generic band directives
status: testing
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

Run a few turns and verify:
1. Crit success on a 12 reads more impressive than on a 9
2. Crit failure on a 1 reads worse than on a 2
3. Band directives don't reference specific conditions (wounded/bleeding)
4. Intensity tone matches die value without contradicting band directive
