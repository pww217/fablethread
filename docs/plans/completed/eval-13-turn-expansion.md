# Eval 13-Turn Expansion: Dual Compaction + Gap Coverage

## Status
`open`

## Part of
Eval remediation — May 2026 cycle

## Dependencies
- Completed: `eval-results-remediation2/` (all 11 phases)
- Completed: `compactor-overhaul.md` (compactor infrastructure)
- Completed: `eval-remediation/` (all phases)
- None required from open plans

## Conflicts and overlap
None. No open plans touch eval scenario files, rubric, or eval config.

## Objective
Extend the `full_cycle` eval scenario from 10 to 13 turns so the compactor fires twice (at T6 and T12), and add 3 new turns that test mechanics not yet covered by any existing scenario: combat with condition application, inventory additions, condition removal, critical success/failure outcomes, and post-compaction state verification. Update the rubric and docs to reflect the dual-compaction evaluation.

## Non-goals
- Fixing condition dedup (covered by `01-extractor-grounding-and-compactor-fix.md`)
- Fixing compactor stagnation (separate issue)
- Adding new config keys or Pydantic model fields
- Modifying the core game engine or prompts

## Affected files

| File | Change type | Summary |
|---|---|---|
| `evals/scenarios/full_cycle.py` | modify | Extend from 10 to 13 turns with 3 new turns |
| `evals/config.yaml` | modify | Update `num_turns` from 10 to 13 |
| `evals/rubrics/default.md` | modify | Update Section 4 for dual compaction passes |
| `evals/README.md` | modify | Update scenario docs for 13-turn full_cycle |
| `docs/plans/TODO.md` | modify | Add eval expansion item |
| `docs/REPOMAP/eval.md` | modify | Update scenario table |

---

## Background: Why 13 turns?

The compactor fires at `compact_every` intervals (default: 6). With `compact_every=6`:
- **10 turns:** compactor fires once at T6. T12 is beyond the run.
- **13 turns:** compactor fires at T6 AND T12. This tests:
  1. First compaction pass (fires at T6): compacts T1-3, retains T4-6. Results visible at T7.
  2. Second compaction pass (fires at T12): compacts T7-9, retains T10-12. Results visible at T13.
  3. Post-compaction behavior at T13: narrator operates with compacted history from both passes (6 total bullets covering T1-9, recent window T10-12).

This is critical for evaluating whether the compactor produces consistent output across multiple fires, and whether the narrator handles a heavily compacted chronicle correctly.

---

## Background: Config parity verification

The eval harness builds `EngineConfig` from the game's `config.yaml` via `build_engine_config()` in `ccya/engine/config.py:107-141`. All game config keys are mapped:

| Config area | Keys covered | Parity |
|---|---|---|
| LLM | host, model, prompt_token_budget, request_timeout_s, all temps, thinking flags, retries, log settings | Full |
| Game | window_turns, chronicle_prefix_budget_tokens, recent_events_max, scene_pressure_* (3 keys), compact_every, compact_temperature, recent_turns_min, deescalate flag | Full |
| Rules | temperature, max_retries | Full |
| Logging | log_llm_io, log_llm_io_max_chars, log_prompts | Full |
| Seed gen | generate_seed_temperature, generate_seed_max_retries, max_generate_pack_retries | Full |

**No config gaps.** The eval harness inherits all game settings. The only intentional differences:
- `temperature_override` (null = inherit, or a float to override all temps uniformly)
- Judge model/temperature (separate from engine model)
- Static pack (eval packs have no dynamic seed generation — intentional for determinism)

---

## Background: What's already tested

### full_cycle (10 turns)
| Turn | Phase | Mechanics tested |
|---|---|---|
| 1 | dialogue | No-roll social, scope gating |
| 2 | debt_settlement | Cha roll, inventory_remove (credits), quest progress |
| 3 | quest_accept | Cha roll, quest progress, compendium_npc_update |
| 4 | travel | Location change, no-roll movement |
| 5 | confrontation | Combat engagement, Cha/Str roll, scene_tags=combat |
| 6 | payoff | Cha roll, inventory_remove (credits), quest progress, compaction fires |
| 7 | quest_complete | Quest auto-complete, compendium_npc_update |
| 8 | unconventional_item_use | Wits roll, inventory_remove (brass_key) |
| 9 | absurd_edge_case | Cha roll (absurd), narration handling |
| 10 | npc_development | Cha roll, compendium_npc_update |

### Other scenarios
| Scenario | Turns | Mechanics tested |
|---|---|---|
| pressure_lifecycle | 8 | Scene pressure escalation/expiry |
| gm_beat_lifecycle | 5 | pending_gm_beat lifecycle |
| momentum_high | 3 | High-momentum narration tone |
| momentum_low | 3 | Low-momentum narration tone |

### Mechanics NOT yet tested by any scenario
1. **Critical success/failure outcomes** — band=crit_success/crit_fail, momentum delta
2. **Inventory additions** — inventory_add (only inventory_remove is tested)
3. **Inventory updates** — inventory_update (not tested at all)
4. **Condition application in combat** — pc_condition_add from combat (starting conditions only)
5. **Condition removal** — pc_condition_remove (not tested)
6. **Multiple NPC interactions in one turn** — npc_add + npc_update simultaneously
7. **Post-compaction narrator behavior** — narrator with heavily compacted chronicle (only T7-T10 after first compaction, but never after a second compaction)
8. **Quest state transitions** — active to completed (only deliver_the_ledger tested)
9. **Location change with description** — location_change + location_description simultaneously
10. **Consumable inventory removal** — inventory_remove for non-credit items used as resources

---

## Implementation — Phase 1: Extend full_cycle to 13 turns

### Context files to load
- `evals/scenarios/full_cycle.py` (current 10-turn scenario)
- `evals/packs/eval-pack/seed_state.yaml` (initial state for context)
- `evals/scenarios/pressure_lifecycle.py` (reference for turn structure)

### Overview
Add 3 new turns (11-13) to `full_cycle.py` that test the 10 untested mechanics listed above. The turns continue the narrative arc from turn 10 (confronting Matthew Estrada).

### Detailed steps

#### Step 1.1 — Add turns 11-13 to full_cycle.py

**File:** `evals/scenarios/full_cycle.py`

**What:** Append 3 new turns after turn 10. Update the docstring and turn count references.

**Turn 11: Combat engagement with condition application and inventory addition**
- Tests: combat roll, critical success/failure, pc_condition_add, inventory_add
- Input: Player discovers Matthew Estrada is a rival agent sent to intercept Halden's ledger. A fight breaks out.
- Expected: rules.required=true, combat roll, condition added (e.g., wounded), item gained (e.g., estrada_wallet)
- Covers untested mechanics: #1 (crit success/fail), #4 (condition in combat), #2 (inventory_add)

**Turn 12: Quest completion + location change + second compaction trigger**
- Tests: quest completion, location_change, compaction fires at T12
- Input: Player rushes to the river dock to intercept the courier boat carrying Halden's rival.
- Expected: quest_updates for deliver_the_ledger (or new quest), location_change to river_dock, compaction fires
- Covers untested mechanics: #6 (multiple NPC interactions), #8 (quest state transitions), #9 (location + description)
- **Critical:** This is the second compaction pass. The rubric must evaluate both compaction outputs.

**Turn 13: Condition removal + post-compaction verification**
- Tests: pc_condition_remove, narrator with compacted history, momentum arc resolution
- Input: Player tends to wounds at the dock infirmary, then sends a message to Caron about the intercepted courier.
- Expected: pc_condition_remove (wounded or similar), no-roll social (message), narrator operates with 2 compaction passes of history
- Covers untested mechanics: #5 (condition removal), #7 (post-compaction narrator), #10 (consumable inventory removal)

**Code Snippet**
```python
# Append after turn 10 (line 175), before the closing ):

        # --- Turn 11: Combat — Matthew's bodyguard attacks ---
        Turn(
            input="Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.",
            phase="combat",
            expects=[
                "rules.required=true skill=strength (combat)",
                "pc_condition_add for player (e.g., wounded from knife)",
                "inventory_add for bodyguard's items (e.g., estrada_wallet)",
                "scene_tags should include combat",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
                TurnAssert(stream="extract.scene", field="scene_tags", expected="combat"),
            ],
        ),
        # --- Turn 12: Rush to river dock — quest completion + location change ---
        Turn(
            input="I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.",
            phase="chase",
            expects=[
                "extract.scene.location_change to river_dock",
                "extract.progress quest_updates for deliver_the_ledger",
                "compaction fires at T12 (second pass)",
                "npc_add for dock workers or rival courier",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="false"),
            ],
        ),
        # --- Turn 13: Tend wounds + send message — condition removal ---
        Turn(
            input="I find a quiet corner at the dock and wrap my wounds with my shirt. Then I write a note to Caron about the intercepted courier and pay the dock boy to deliver it.",
            phase="recovery",
            expects=[
                "pc_condition_remove for wounded (self-treatment)",
                "no rules call (social, no obstacle)",
                "narrator operates with compacted history (2 compaction passes)",
                "inventory_remove for shirt (used as bandage)",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="false"),
            ],
        ),
```

**Docstring update:** Change the first line from `"""full_cycle — 10-turn arc...` to `"""full_cycle — 13-turn arc testing all mechanics across 5+ locations with dual compaction.` Update the "Designed for" line to say "13 turns" and update the "Expected emergent observations" to include compaction at T12 and condition management at T13.

**Validation:** The scenario file should have 13 turns. All new turns have input, phase, expects, and asserts. The docstring references 13 turns and dual compaction.

### Tests to write or update
- `tests/test_eval_schema.py`: The existing `test_scenario_assert_fields` and `test_seed_override_paths` tests should pass automatically (schema validation). No new tests needed for schema.
- `tests/test_eval.py`: No new tests needed — the existing test infrastructure validates scenario structure.

### REPOMAP updates required
- `docs/REPOMAP/eval.md`: Update the scenario table to show full_cycle with 13 turns. Add notes about dual compaction testing.

### Risks
1. **Narrative continuity.** The new turns must flow naturally from turn 10 (confronting Matthew Estrada). The chase to the river dock is a logical escalation.
2. **Compaction at T12.** If the compactor has the stagnation bug (produces 0 bullets after first fire), T12 compaction may also fail. This is a valid eval finding — the rubric should flag it.
3. **Condition removal.** The extractor may not remove conditions from self-treatment narration. This is a valid eval finding — the rubric should flag it.

---

## Implementation — Phase 2: Update eval config

### Context files to load
- `evals/config.yaml` (current config)

### Overview
Change `num_turns` from 10 to 13.

### Detailed steps

#### Step 2.1 — Update num_turns

**File:** `evals/config.yaml`

**What:** Change line 13 from `num_turns: 10` to `num_turns: 13`.

**Code Snippet**
```yaml
# Line 13:
num_turns: 13                         # run only first N turns (default/max 13, override with --turns)
```

**Validation:** The config should have `num_turns: 13`. The CLI `--turns` flag can still override this.

---

## Implementation — Phase 3: Update rubric for dual compaction

### Context files to load
- `evals/rubrics/default.md` (current rubric, lines 276-346, Section 4)

### Overview
Update Section 4 (Compaction Capabilities Report) to reflect that eval runs now have TWO compaction passes (T6 and T12) instead of one.

### Detailed steps

#### Step 3.1 — Update compaction expectations

**File:** `evals/rubrics/default.md`

**What:** Replace the "Expectations for typical eval runs" paragraph (lines 303-309) and the "Turn numbering" section (lines 287-301) to reflect dual compaction.

**Code Snippet**
```markdown
Replace lines 287-309 with:

**Turn numbering:** The trace uses 1-indexed turns (`## Turn 1`, `## Turn 2`, etc.). The seed state has `"turn": 0` but the first game turn is "Turn 1". All turn references below are 1-indexed as they appear in the trace.


**How `window_turns` works:** `window_turns` controls how many of the most recent turns are kept uncompressed in `chronicle.md`. Everything older is compacted into summary bullets. With `window_turns=3`:
- After T6: turns 1–3 are compacted into bullets, turns 4–6 are kept as recent narrative. Expect **3 bullets covering T1–T3**.
- After T12: turns 7–11 are compacted into bullets, turns 9–12 are kept as recent narrative. Expect **5 additional bullets covering T7–T11**.
- The engine always retains the 3 most recent turns as full narrative plus all compacted bullets for older turns.


**Expectations for typical eval runs:** With `compact_every=6` and 13 turns, the compactor fires at T6 and T12.

**First compaction (T6):** At T7 (between T6 and T7), you should see **3 bullets covering T1–T3** and turns 4–6 kept as recent narrative. This is correct behavior.

**Second compaction (T12):** At T13 (between T12 and T13), you should see **3 additional bullets covering T7–T9** for a total of **6 bullets** (3 from first pass + 3 from second pass). Turns 10–12 are kept as recent narrative.

Do not penalize the engine for not compacting at turns other than 6 and 12. Do not penalize for having only 3 bullets in a 10-turn run — that is the expected output when compaction fires only once.


**What correct compaction output looks like:** When the compactor fires, evaluate ALL compaction passes:

1. **Narrative bullets:** Each compaction pass should produce concise summary bullets. For T6: T1–T3 as 3 bullets. For T12: T7–T9 as 3 bullets. Each bullet must faithfully represent the key event or player action of that turn. A bullet that misrepresents, inverts, or omits a named entity (NPC name, item name, location name, quest ID) from the turn it covers is a compaction failure.

2. **recent_events deduplication:** After EACH compaction pass, `scene.recent_events` should not contain events whose content is already covered by a compaction bullet. Check the applied sanitization in the Deterministic Signals block after both T6 and T12.

3. **Stale state sanitization:** Each compaction pass should close completed quests, remove resolved conditions, and remove expired pressures from state. Check the `CompactorSanitizationResult` fields after both compaction passes.

If compaction did not fire (run was too short), state that and skip the per-capability evaluation for this run.

If compaction fired but produced low-quality bullets (per criteria 1 above), score the `extract_progress` pipeline lower in Section 1.
```

**Validation:** The rubric should reference two compaction passes (T6 and T12), expect 8 total bullets (3 + 5), and instruct the judge to evaluate both passes.

---

## Implementation — Phase 4: Update docs

### Context files to load
- `evals/README.md` (current README)
- `docs/REPOMAP/eval.md` (eval architecture docs)
- `docs/plans/TODO.md` (current TODO)

### Overview
Update README, REPOMAP, and TODO to reflect the 13-turn expansion.

### Detailed steps

#### Step 4.1 — Update evals/README.md

**File:** `evals/README.md`

**What:** Update the scenario description table to show full_cycle with 13 turns and dual compaction.

**Code Snippet**
```markdown
# Update the scenario table row for full_cycle:
| `full_cycle` | 13 | Peaceful start → debt settlement → courier contract → road travel → confrontation → combat → chase → recovery. Tests dual compaction (T6, T12). |
```

#### Step 4.2 — Update docs/REPOMAP/eval.md

**File:** `docs/REPOMAP/eval.md`

**What:** Update the scenario table to show full_cycle with 13 turns.

**Code Snippet**
```markdown
# Update the scenario table:
| `full_cycle` | 13 | Baseline regression: all mechanics across 5+ locations, peaceful start to combat and chase. Tests dual compaction at T6 and T12. |
```

#### Step 4.3 — Update docs/plans/TODO.md

**File:** `docs/plans/TODO.md`

**What:** Add a new item under the "Eval Remediation (May 2026)" section.

**Code Snippet**
```markdown
Add after the existing eval remediation items:

- [x] **Eval 13-turn expansion: dual compaction + gap coverage** — extend full_cycle from 10 to 13 turns, add combat/inventory/condition/removal turns, update rubric for dual compaction — see `[eval-13-turn-expansion.md](eval-13-turn-expansion.md)`
```

---

## Implementation — Phase 5: Update engine_mirror KNOWN_SEED_PATHS

### Context files to load
- `ccya/eval/engine_mirror.py` (current KNOWN_SEED_PATHS)

### Overview
Verify that all seed override dotpaths used in the new turns are in `KNOWN_SEED_PATHS`. The new turns don't use any new seed overrides (they use the default seed state), so no changes needed.

### Verification
Current `KNOWN_SEED_PATHS`:
```python
KNOWN_SEED_PATHS: frozenset[str] = frozenset((
    "meta.momentum",
    "scene.scene_pressure",
    "pc.conditions",
    "pc.credits",
))
```

The new turns (11-13) don't use `seed_overrides` — they inherit the default seed state. No changes needed.

---

## Summary of changes

| File | Change | Lines affected |
|---|---|---|
| `evals/scenarios/full_cycle.py` | Add 3 turns (11-13), update docstring | ~50 lines |
| `evals/config.yaml` | `num_turns: 10` → `13` | 1 line |
| `evals/rubrics/default.md` | Section 4: dual compaction expectations | ~30 lines |
| `evals/README.md` | Scenario table update | 1 line |
| `docs/REPOMAP/eval.md` | Scenario table update | 1 line |
| `docs/plans/TODO.md` | Add completed item | 1 line |

## New turn coverage matrix

| Mechanic | Previously tested | Now tested in |
|---|---|---|
| Critical success/failure | No | T11 (combat) |
| Inventory add | No | T11 (search bodyguard) |
| Inventory update | No | — (still not tested, lower priority) |
| Condition in combat | No | T11 (wounded from knife) |
| Condition removal | No | T13 (self-treatment) |
| Multiple NPC interactions | No | T12 (dock workers + rival) |
| Quest state transitions | Partial (T7) | T12 (deliver_the_ledger completion) |
| Location + description change | Partial (T4, T6) | T12 (river dock) |
| Post-compaction narrator (2 passes) | No | T13 (after T6 + T12 compaction) |
| Inventory remove (consumable) | No | T13 (shirt as bandage) |

## Exit criteria

1. `evals/scenarios/full_cycle.py` has 13 turns with all new turns having input, phase, expects, and asserts
2. `evals/config.yaml` has `num_turns: 13`
3. `evals/rubrics/default.md` Section 4 references dual compaction (T6 + T12) and expects 8 total bullets
4. `evals/README.md` scenario table shows 13 turns for full_cycle
5. `docs/REPOMAP/eval.md` scenario table shows 13 turns for full_cycle
6. `docs/plans/TODO.md` has the completed item
7. `tests/test_eval_schema.py` passes (schema validation for new turns)
8. `make check` passes (lint + typecheck)
