# Supporting Changes — Phase 3: Positive Condition Extraction

## Purpose

Add success-guarded positive condition heuristics to the state extractor system prompt, targeting ~25% positive condition ratio (up from ~5%) to break the negative-condition→hard-difficulty→fail spiral.

## Firm decisions

- Add positive condition heuristics guarded by decisive success or crit_success.
- Add ally/assistance positive condition heuristics.
- Max 1 positive extracted per turn.
- Total active conditions cap (5) already exists — unchanged.
- No schema changes — uses existing `pc_condition_add` with positive condition IDs.
- Plan 2 Phase 2 (band rebalance) must be complete first (partial threshold change impacts band distribution that conditions respond to).

## Status

`completed`

## Implementation — Phase 3: Positive Condition Extraction

### Context files to load

- `ccya/prompts/extract_state_system.j2` — full file (83 lines)

### Detailed steps

#### Step 3.1 — Add positive condition heuristics

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Replace the "## Stat-to-condition heuristics" section (lines 75-79):

Old:
```
## Stat-to-condition heuristics:
- Combat failure with strength/dexterity → consider `wounded`, `bleeding`
- Failed wits under pressure → consider `frightened` or `drugged`
- Failed strength/dexterity with sustained effort → consider `exhausted`
- Clean success or crit_success → no negative conditions
```

New:
```
## Stat-to-condition heuristics:
- Combat failure with strength/dexterity → consider `wounded`, `bleeding`
- Failed wits under pressure → consider `frightened` or `drugged`
- Failed strength/dexterity with sustained effort → consider `exhausted`
- After a decisive success or critical success → consider a short-lived positive condition (`focused`, `determined`, `elated`, `second_wind`, `protected`). Max 1 per turn.
- When an ally or circumstance actively aids the player → consider a brief positive condition (`guided`, `fortified`, `inspired`). Max 1 per turn.
- Total active conditions must not exceed 5 — remove the least relevant before adding if at cap.
```

**Why:** The old heuristics only mentioned negative conditions. The last line ("Clean success → no negative conditions") actively discouraged positives. New heuristics create space for positives without forcing them. The 5-cap limits stacking.

**Validation:** After deployment, run `ev play --llm --turns 15` and check condition ratio via `ev check --checker conditions` or manual state inspection.

### Tests to write or update

No tests exist. Run `make check` after all Plan 2 phases complete.
