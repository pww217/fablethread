# Ev1 fix — Beat timing architecture decision and observability improvements

## Status
`completed`

## Phases
Single phase: architectural decision about beat consumption timing (turn.py), plus two trivial serialization/CLI fixes (turn.py, ev.py).

## Issue
Two issues from the ev1 audit affect beat observability and game feel:

1. **One-turn beat lag (Low-Medium, ev1 #9):** Beats generated on turn N are consumed by the narrator on turn N+1. The `pending_gm_beat` from turn N's storyteller extraction is stored in state, then read by `_narrate_setup()` at the start of turn N+1. This means T1's pressure beat shapes T2's narration, not T1's — a one-turn delay between mechanical outcome and narrative consequence.

2. **`raw_total` not persisted (Low, ev1 #10):** The `RulesOutcome` model computes and stores `raw_total` (sum of dice + modifiers before threshold adjustment), but the serialization to events.jsonl ruling dict at `turn.py:1442-1453` omits it. Verification of dice math requires reconstructing from separate fields.

## Solution
1. **Beat timing:** Move beat consumption to same-turn by reading `pending_gm_beat` (from *previous* turn's storyteller) and passing it into the narration context — this is already what happens. The "lag" is inherent to the architecture: beats set the atmosphere for the *next* turn. Document this as intentional: "Beats generated on turn N set the scene atmosphere for turn N+1 narration, creating forward-facing narrative continuity rather than immediate mechanical feedback." The right fix for immediate feedback is to improve the narrator's integration of roll outcomes (narration tells the story of the roll's consequences), not to change beat timing.

2. **`raw_total` serialization:** Add `"raw_total": outcome.raw_total` to the ruling dict in `turn.py` events.jsonl writer.

3. **ev.py dice command:** Add a `--dice` display mode to `scripts/debug/ev.py` that reads `ruling.raw_total`, `ruling.final_total`, `ruling.dice`, `ruling.skill`, `ruling.difficulty` from events.jsonl and prints a formatted dice table.

## Firm decisions
1. The one-turn beat lag is accepted as intentional design. Beats are atmosphere-shapers across turns, not immediate feedback for roll outcomes. The narrator already provides immediate feedback through roll-band-driven prose. Changing beat timing would require restructuring the pipeline and risks creating circular dependencies between narration and extraction phases.
2. The `raw_total` fix is purely observability — no behavioral change. All dice math is already verifiable from persisted fields; `raw_total` is a convenience field.
3. The ev.py dice command reads from events.jsonl only, not from state.yaml or the rules model. It parses the serialized ruling dict fields.

## Non-goals
- Does not restructure the pipeline to eliminate the one-turn lag. The architectural decision is documented, not executed.
- Does not add beat integration quality tracking to events.jsonl (the judge rubric from `eval-coverage-gaps.md` Phase 2 covers this).
- Does not backfill `raw_total` into existing events.jsonl files — the field is absent from prior data, and the ev.py command gracefully handles missing fields.

## Risks, Ambiguities, and Blockers
- The architectural decision to accept the one-turn lag should be reviewed by the design team. If immediate feedback for roll outcomes is a priority, this decision needs reconsideration and a more invasive pipeline change.

## Implementation

### Context files to load
- `ccya/engine/turn.py` (lines 873-881 for beat consumption timing, 1442-1453 for ruling dict serialization)
- `ccya/models.py` (RulesOutcome model for raw_total field)
- `scripts/debug/ev.py` (for dice display command)

### Detailed steps

#### Step 3.1 — Document beat timing decision

**File:** `ccya/engine/turn.py`

**What:** Add a docstring/comment to the `_narrate_setup()` function (or to the `pending_gm_beat` read at line 873) that documents the intentional one-turn lag:

```python
# pending_gm_beat from the previous turn's storyteller is read here to set
# the atmosphere/scene context for this turn's narration. Beats are consumed
# on the turn AFTER generation — this is intentional: beats shape ongoing scene
# atmosphere rather than providing immediate mechanical feedback.
# Immediate feedback for roll outcomes is handled by the roll-band narration
# directive (rules.py build_directive()), not by the beat system.
```

**Why:** The ev1 report identified this as ambiguous (A3 in the original report). Explicit documentation prevents future confusion about whether the lag is a bug or a feature.

**Validation:** No code change — comment only. `make check` passes.

#### Step 3.2 — Add `raw_total` to events.jsonl ruling dict

**File:** `ccya/engine/turn.py`

**What:** In the ruling dict construction section (around line 1442-1453, inside the `if outcome` block), add:

```python
"raw_total": outcome.raw_total,
```

This outputs `raw_total` in the events.jsonl ruling dict alongside the existing `final_total`, `dice`, `band`, `skill`, `difficulty`, `stat_mod`, `diff_mod`, `cond_mod` fields.

**Why:** `raw_total` exists in the `RulesOutcome` model (line 197, 213) but was omitted from serialization. Every other field in the model is serialized except `raw_total` — this appears to be an oversight. Adding it makes dice math directly verifiable from events.jsonl without manual reconstruction.

**Validation:** `make check` passes. Run a turn with a dice roll, inspect events.jsonl, verify `raw_total` appears in the ruling dict.

#### Step 3.3 — Add dice display command to ev.py

**File:** `scripts/debug/ev.py`

**What:** Add a `dice` subcommand that reads all events with `ruling.rolled=true` and prints:

```
Turn | Skill     | Difficulty | Dice    | Raw → Final | Band       | Modifiers
1    | charisma  | normal     | [1, 3]  | 4 → 6       | fail       | stat:+2 diff:+0 cond:+0
4    | strength  | normal     | [3, 3]  | 6 → 6       | fail       | stat:+0 diff:+0 cond:+0
...
```

Fields read from `event["ruling"]`: `skill`, `difficulty`, `dice`, `raw_total`, `final_total`, `band`, `stat_mod`, `diff_mod`, `cond_mod`. If `raw_total` is absent (pre-fix data), fall back to computing `sum(dice) + stat_mod + diff_mod + cond_mod` manually for display purposes.

Include a summary row at the bottom: total rolls, band distribution, stats used.

**Why:** The ev1 analysis (`dice.md:93-94`) noted that inspecting dice math requires querying events.jsonl directly with a custom script. A dedicated `ev.py dice` command makes this a single command.

**Validation:** Run `python scripts/debug/ev.py dice` against the ev1 events.jsonl. Verify all 7 rolls are displayed with correct fields.

### Tests to write or update

`scripts/debug/ev.py` — No test file exists. The command is validated by manual run against known events.jsonl data.

`ccya/engine/turn.py` — The `raw_total` serialization is tested by existing integration tests that inspect events.jsonl output. No new test needed.

### REPOMAP updates required

`docs/repomap.md` — Update `turn.py` events.jsonl writer section (around line 126-127) to note `raw_total` is now serialized. Add `ev.py dice` to the ev.py description (line 37).
