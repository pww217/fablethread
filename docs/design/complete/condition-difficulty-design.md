# Design: LLM-Driven Condition Effects on Roll Difficulty

## Purpose

Replace the hardcoded `CONDITION_MODS` lookup table with LLM-driven difficulty adjustment in the ruling phase. This document is the design authority for plans implementing this change.

## Problem Statement

Conditions (`pc.conditions`) are mechanically inert for most conditions. The dice resolver has a fixed `CONDITION_MODS` dict (`ccya/rules.py:32-38`) mapping exactly 5 condition IDs to per-skill integer modifiers. Any condition not in this map — which is most of them — contributes 0 to the roll. The LLM selects difficulty blind to conditions, and the `cond_mod` is applied as invisible Python math the player never sees and the LLM never accounts for.

This is brittle at small scale and unscalable: there is no viable path to enumerate every possible condition and its effect on every skill.

## Constraints

- No new LLM call. The ruling phase already runs every turn.
- No backwards compatibility. Old CONDITION_MODS references removed entirely.
- No growth in schema complexity. Reuse existing `difficulty` field.
- Terse output. `reason` field always present, max ~10 words. The LLM explains its difficulty choice every turn.
- Conditions and inventory in scope. The ruling LLM receives both and factors both into difficulty and impossibility decisions.

## Non-goals

- Adding numeric modifier fields to IntentEnvelope or RulesOutcome. All condition and inventory effects are expressed through difficulty selection.
- Changing the extraction pipeline. Conditions continue to be added/removed by turn 2b (state extract).
- Changing the narrator or storyteller prompts. They already see conditions in their context.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Conditions affect difficulty, not numeric mods | LLM adjusts `check.difficulty` in the same field it already uses | No new schema. Qualitative reasoning matches LLM strengths. |
| Remove CONDITION_MODS entirely | Delete dict, `conditions_modifier()`, `cond_mod` field | Clean break. No backwards compat debt. |
| Rename `impossible_reason` → `reason` | Single reason field covers impossibility + difficulty shifts | Forces accountability. LLM explains every deviation. One field, one contract. |
| reason is always required | Every ruling output. Explains the difficulty choice every turn. | Keeps LLM accountable. Simpler contract. Negligible token cost (~10 words). |
| One-pass net effect | LLM weighs all active conditions and picks one difficulty | Simpler prompt. LLM handles conflicting conditions naturally. |
| Two-step guidance in prompt | Prompt tells LLM to "consider conditions, then set difficulty" | Light structure without chain-of-thought token waste. |
| Conditions and inventory in scope | The ruling LLM sees both and factors both into difficulty | Already reads inventory for impossibility checks. Same cognitive step. No extra fields. |

## Open Questions

- None. All decisions are final as recorded above.

## Current State — What Exists

### Dice Flow

```
LLM ruling → picks skill + difficulty → Python resolve_check() →
  1d12 + stat_mod (stat-2) + diff_mod (DIFFICULTY_MOD[difficulty]) + cond_mod (CONDITION_MODS[cond][skill])
  → band
```

### CONDITION_MODS (`ccya/rules.py:32-38`)

```python
CONDITION_MODS = {
    "wounded": {"strength": -1, "dexterity": -1},
    "exhausted": {"strength": -1, "dexterity": -1},
    "drugged": {"wits": -1},
    "frightened": {"charisma": -1},
    "bleeding": {"strength": -1},
}
```

### Ruling prompt (`ccya/prompts/ruling_user.j2`)

Conditions are rendered as a comma-separated label list:
```
**Conditions:** wounded, exhausted
```

The `ruling_system.j2` prompt describes difficulty tiers but says nothing about factoring conditions into difficulty. The impossibility check mentions conditions once: "Requires a capability contradicted by an active condition."

### Downstream consumers of cond_mod

| Location | Usage |
|---|---|
| `ccya/rules.py:resolve_check()` | Sums cond_mod into final_total |
| `ccya/models.py:RulesOutcome.cond_mod` | Stored as field |
| `ccya/engine/turn.py:811` | Phase event field |
| `ccya/engine/turn.py:1371` | events.jsonl ruling_event |
| `ccya/engine/ruling.py:150` | prompts.log display |
| `ccya/eval/universal_asserts.py:768` | `check_orphan_conditions` auto-checker flags conditions without CONDITION_MODS entry |
| `scripts/debug/ev.py:2018+` | Mechanics display section shows cond_mod |

### Problems with Current State

- 5 conditions mapped, infinite possible conditions unmapped. Any condition outside the lookup table is invisible math.
- LLM selects difficulty without seeing condition information in a way it can reason about. Conditions are shown as text but the prompt doesn't tell the LLM to factor them in.
- `cond_mod` is opaque to the player. The combat log shows it, but the feedback loop is weak.
- The condition-aware difficulty auto-checker (`check_orphan_conditions`) flags the wrong thing — it penalizes conditions that *don't* have a lookup entry, but the whole point is that lookups are the wrong approach. This auto-checker is inverted: it should celebrate conditions that the LLM factored into difficulty.

## Proposed Solution

### Core Changes

1. **Remove `CONDITION_MODS`**, `conditions_modifier()`, and `cond_mod` from `ccya/rules.py`. `resolve_check()` computes `final_total = raw_total + stat_mod + diff_mod` — no condition term.

2. **Remove `cond_mod` field from `RulesOutcome`**. All downstream consumers (events, phase events, prompts.log) stop writing it.

3. **Teach the ruling LLM to factor conditions into difficulty.** In `ruling_system.j2`, add a paragraph instructing the LLM to consider active conditions when selecting difficulty. If conditions make the task harder or easier than the base action would suggest, adjust the difficulty up or down accordingly and include a `reason`.

4. **Rename `impossible_reason` → `reason`.** Always present on every ruling output. The LLM explains its difficulty choice (or impossibility) in ≤10 words. Examples: "broken arm → hard climb," "combat stimulant → easy," "normal lockpick — no complications," "impossible — no rope."

5. **Update the `check_orphan_conditions` auto-checker** to remove the `CONDITION_MODS` lookup — the concept of orphan conditions is now about conditions the LLM *could* have factored in but may have missed. Change severity to yellow and check that conditions present in state appear in the ruling LLM's `reason` output.

### Data Flow (new)

```
LLM ruling (sees conditions, uses difficulty + reason) →
  resolve_check() with difficulty that already accounts for conditions →
  1d12 + stat_mod + diff_mod → band
```

### Prompt changes to `ccya/prompts/ruling_system.j2`

- After the "Impossibility check" section, add a "Inventory and conditions" section:
  ```
  ## Inventory and conditions
  
  The player's inventory and active conditions may make a check harder or easier.
  Factor them into your difficulty selection:
  - A condition that hinders the relevant skill → bump difficulty up (e.g., normal → hard)
  - A condition that helps the relevant skill → bump difficulty down (e.g., normal → easy)
  - Equipment that helps the task → bump difficulty down (scope on a rifle, lockpicks on a lock)
  - Missing equipment for the task → bump difficulty up (no rope for a climb, no light in darkness)
  - Multiple factors with opposing effects → net them out
  - Always include `reason` — explain the difficulty choice in ≤10 words, even when nothing unusual is happening ("normal lock — no complications").
  ```

### Schema change to `IntentEnvelope`

| Field | Change |
|---|---|
| `impossible_reason` | Renamed to `reason`. Same type: `str = ""`. |
| `reason` | Always present. Explains the difficulty/impossibility choice. Max ~10 words. |

### Alternatives Considered and Rejected

- **LLM assigns numeric condition modifiers per skill.** Rejected: LLMs are inconsistent at assigning small integers. Difficulty adjustment uses the same qualitative reasoning the LLM already does. No new schema field needed.
- **Add `circumstance_mod` (±1) to IntentEnvelope.** Rejected: redundant with the 5-point difficulty scale. A condition that makes a normal check slightly harder is Hard. A condition that makes a Hard check much harder is Extreme.
- **Keep CONDITION_MODS as fallback.** Rejected (explicit). No backwards compatibility. Clean break.

## Failure Modes and Risks

- **LLM ignores conditions.** Mitigation: the `reason` field requirement when difficulty ≠ normal forces explicit reasoning. The eval auto-checker flags turns where conditions existed but weren't mentioned in reason.
- **LLM over-adjusts.** A trivial condition (+1) might inappropriately bump difficulty by 2 steps. Mitigation: prompt guidance to adjust proportionally. Eval auto-checker can flag large shifts for review.
- **Loss of dice transparency.** Currently `cond_mod` appears in event logs. Without it, players see only diff_mod in the roll display. Mitigation: the `reason` field is rendered in the turn UI wherever difficulty is displayed, giving the player visible feedback about why the roll was harder/easier.
- **Eval gap.** Old auto-checkers that relied on CONDITION_MODS need updating. Mitigation: covered below in "What Is Removed" and "What Is Unchanged."

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `CONDITION_MODS` dict | `ccya/rules.py` | Deleted with no replacement |
| `conditions_modifier()` function | `ccya/rules.py` | Deleted with no replacement |
| `cond_mod` field | `ccya/models.py:RulesOutcome` | Deleted with no replacement |
| `cond_mod` in final_total sum | `ccya/rules.py:202` | `final_total = raw_total + stat_mod + diff_mod` (no cond term) |
| `cond_mod` in phase events | `ccya/engine/turn.py:811` | Remove the line |
| `cond_mod` in events.jsonl ruling_event | `ccya/engine/turn.py:1371` | Remove the line |
| `cond_mod` in prompts.log | `ccya/engine/ruling.py:150` | Remove the line |
| `impossible_reason` field | `ccya/models.py:IntentEnvelope` | Renamed to `reason` |
| `check_orphan_conditions` auto-checker | `ccya/eval/universal_asserts.py:767` | Replaced with new assert (see below) |
| `cond_mod` in mechanics display | `scripts/debug/ev.py` | Remove cond from display calculations |

## What Is Unchanged

- `ccya/prompts/ruling_user.j2` — conditions and inventory are already rendered. No structural change needed.
- `ccya/prompts/extract_state_user.j2`, `extract_state_system.j2` — condition extraction unchanged.
- `ccya/prompts/storytell_user.j2`, `narrate_user.j2` — condition rendering in other prompts unchanged.
- `ccya/state/delta_builder.py` — condition dedup, add, remove, and cap logic unchanged.
- `ccya/engine/turn.py` condition TTL aging and expiration logic unchanged.
- `DIFFICULTY_MOD` in `ccya/rules.py` — unchanged. The difficulty bands remain the same.
- `resolve_check()` signature — unchanged except removing `cond_mod` from the computation.
- `ccya/models.py:RulesOutcome` — all fields except `cond_mod` and `impossible_reason` unchanged.
- `ccya/eval/universal_asserts.py` — all auto-checkers except `check_orphan_conditions` unchanged.

## New Model Shapes

### IntentEnvelope (updated)

```python
class IntentEnvelope(BaseModel):
    intent: str = Field(default="", max_length=200)
    intent_verb: str = Field(default="act", max_length=24)
    target: str = ""
    check: RulesCheck = Field(default_factory=RulesCheck)
    impossible: bool = False
    reason: str = ""              # renamed from impossible_reason
    scene_motion: Literal["hold", "advance", "transition"] = "hold"
```

### RulesOutcome (updated)

```python
class RulesOutcome(BaseModel):
    rolled: bool = False
    skill: str = ""
    stat_value: int = 0
    difficulty: str = "normal"
    stat_mod: int = 0
    diff_mod: int = 0
    # cond_mod: int = 0          # REMOVED
    dice: list[int] = Field(default_factory=list)
    raw_total: int = 0
    final_total: int = 0
    band: Band = "success"
    directive: str = ""
    intent_verb: str = ""
    intent: str = ""
    impossible: bool = False
    reason: str = ""              # renamed from impossible_reason
```

## Context for Implementing LLMs

| File | Why |
|---|---|
| `ccya/prompts/ruling_system.j2` | Add the "Conditions and difficulty" section. Update impossibility section for the renamed field. |
| `ccya/models.py` (lines 167-194) | Rename `impossible_reason` → `reason` in IntentEnvelope and RulesOutcome. Remove `cond_mod` from RulesOutcome. |
| `ccya/rules.py` (lines 32-38, 133-144, 197, 202, 215) | Delete CONDITION_MODS, conditions_modifier(), cond_mod from resolve_check() and RulesOutcome construction. |
| `ccya/engine/turn.py` (lines 811, 1371) | Remove cond_mod from phase events and events.jsonl ruling_event. |
| `ccya/engine/ruling.py` (line 150) | Update prompts.log to write `reason` instead of `cond_mod`. |
| `ccya/eval/universal_asserts.py` (lines 767-796) | Replace `check_orphan_conditions` — old assert checks CONDITION_MODS membership, which is now deleted. New assert: check that conditions in state_snapshot appear in the ruling LLM's `reason` output for the turn. |
| `scripts/debug/ev.py` (lines 2018-2078) | Remove cond_mod from mechanics display section. |
