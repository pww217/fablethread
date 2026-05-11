# Condition Lifecycle: Duration, Relevance, and NPC Enter/Exit

## Status
`open`

## Part of
standalone

## Dependencies
- none (can run in parallel with all other plans)

## Objective
Conditions are the least-audited mechanic in the current system. Three specific failures appear across runs: (1) conditions last too long — a `rattled` condition applied at T3 persists through T12 with no decay, despite the player having had multiple successful turns since; (2) conditions are irrelevant to actual gameplay — conditions like `dust_in_eyes` appear and are never referenced in narration or checked by any dice roll, making them dead state entries; (3) NPCs enter and leave scenes without corresponding `npc_add`/`npc_remove` events — the extractor fails to track NPC scene presence, so `present_npcs` drifts from the narration's actual cast. This plan adds condition duration enforcement, a relevance check, and NPC scene entry/exit audit to the extraction prompts.

## Non-goals
- Does not change condition Pydantic schema (no new fields beyond `turns_remaining` which should already exist per REPOMAP).
- Does not change how conditions affect dice rolls — that is the rules pipeline's domain.
- Does not change NPC compendium entries or bios — only `present_npcs` tracking.
- Does not add new condition types.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/engine/turn.py` | modify | Add condition age pass: decrement `turns_remaining`, remove expired conditions, log `condition_expired` event |
| `ccya/prompts/extract_state_system.j2` | modify | Add condition duration guidance (short/medium/long taxonomy) and relevance rule |
| `ccya/prompts/extract_scene_system.j2` | modify | Add explicit NPC enter/exit tracking rules and few-shot examples |
| `docs/REPOMAP/engine.md` | update | Document condition age pass |
| `docs/REPOMAP/prompts.md` | update | Document condition duration taxonomy and NPC tracking rules |

## Firm decisions

1. Condition duration is enforced by the engine, not the extractor. The extractor proposes conditions with an initial `turns_remaining`; the engine decrements each turn and removes at 0.
2. Duration taxonomy (for the extractor prompt, to guide initial `turns_remaining` values):
    - `brief` (1–2 turns): physical/sensory conditions from a single event (dust in eyes, winded, startled)
    - `short` (3–4 turns): minor injuries, social discomforts, light debuffs (rattled, shaken, minor wound)
    - `medium` (5–8 turns): significant injuries, fear, ongoing environmental effects (injured arm, frightened, burning building)
    - `long` (9+ turns): major injuries, persistent debuffs, magical/curse effects — must have explicit narrative justification
3. Relevance rule: a condition should only be added if it would plausibly affect at least one future dice roll. `dust_in_eyes` is only valid if the player might attempt a perception or ranged action. If the condition has no plausible mechanical relevance given the current scene, the extractor should not emit it.
4. NPC enter/exit: `npc_add` must be emitted whenever a named NPC is introduced in narration and is not already in `present_npcs`. `npc_remove` must be emitted whenever narration indicates a named NPC has left the scene (departed, fled, died, was rendered unconscious). Ambient/unnamed characters do not require tracking.
5. Condition age decrement runs in `turn.py` after extractor delta application, alongside the pressure aging pass from mechanics-pressure-decay.md.

## Implementation — Phase 1: Condition Age Pass in turn.py

### Context files to load
- `ccya/engine/turn.py`
- `docs/REPOMAP/engine.md` (to confirm `turns_remaining` field exists on Condition model)

### Overview
After extractor deltas are applied, decrement `turns_remaining` on all active conditions. Remove any that reach 0. Log `condition_expired` events.

### Detailed steps

#### Step 1.1 — Add condition age pass to turn.py

**File:** `ccya/engine/turn.py`

**What:** After `apply_deltas()` and after the pressure aging pass (mechanics-pressure-decay.md), add a condition aging step.

**Why:** Without engine-side enforcement, conditions persist indefinitely regardless of their initial `turns_remaining` value.

**Code Snippet:**
```python
# After pressure aging pass:
updated_conditions = []
for cond in state.active_conditions:
    if cond.turns_remaining is None:
        # Permanent condition — do not age
        updated_conditions.append(cond)
        continue
    new_remaining = cond.turns_remaining - 1
    if new_remaining <= 0:
        log_event({
            "kind": "condition_expired",
            "condition_id": cond.id,
            "turn": current_turn,
        })
        # do not append — condition removed
    else:
        updated_conditions.append(cond.model_copy(update={"turns_remaining": new_remaining}))

state = state.model_copy(update={"active_conditions": updated_conditions})
```

**Validation:** Apply a condition with `turns_remaining: 2`. Run 2 turns. Confirm condition is absent from state on turn 3. Confirm `condition_expired` event in `events.jsonl`.

***

## Implementation — Phase 2: Condition Duration and Relevance in extract_state_system.j2

### Context files to load
- `ccya/prompts/extract_state_system.j2`

### Overview
Add the duration taxonomy and relevance rule to the state extractor system prompt so conditions are created with appropriate lifetimes.

### Detailed steps

#### Step 2.1 — Add condition duration taxonomy

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Add a `CONDITION DURATION GUIDE` rule block in the condition section:

```
**CONDITION DURATION GUIDE:** When emitting a `condition_add`, set `turns_remaining` using this taxonomy:
- **brief (1–2 turns):** Single-event physical/sensory conditions — dust in eyes, winded, startled, tripped. These resolve in 1–2 turns naturally.
- **short (3–4 turns):** Minor debuffs — rattled, shaken, minor bruise, light wound. Resolve within the same encounter.
- **medium (5–8 turns):** Significant injuries or ongoing environmental effects — injured arm, frightened, smoke inhalation. Last through an encounter and into the next.
- **long (9+ turns):** Major injuries, persistent effects. Requires explicit narrative justification. Do not use for minor encounters.

**CONDITION RELEVANCE RULE:** Only add a condition if it would plausibly affect at least one future dice roll in the current scene context. Do not add flavor conditions with no mechanical relevance. If unsure, omit.
```

**Validation:** In the next eval run, check conditions added by `extract_state`. Confirm `turns_remaining` values align with the taxonomy. Confirm no flavor-only conditions with 0 mechanical relevance.

***

## Implementation — Phase 3: NPC Enter/Exit in extract_scene_system.j2

### Context files to load
- `ccya/prompts/extract_scene_system.j2`

### Overview
Add explicit NPC enter/exit tracking rules and two few-shot examples to `extract_scene_system.j2`.

### Detailed steps

#### Step 3.1 — Add NPC enter/exit rules and few-shots

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Add the following rule block in the NPC section:

```
**NPC ENTER/EXIT RULE (MANDATORY):**
- Emit `npc_add` for every named NPC who appears in the narration for the first time this turn and is NOT already in `present_npcs`.
- Emit `npc_remove` for every named NPC who narration indicates has left, fled, died, fainted, or been removed from the scene.
- Do NOT emit `npc_add` for NPCs already in `present_npcs` — that causes duplicates.
- Do NOT emit `npc_remove` for NPCs who are simply not mentioned — only remove if narration actively indicates departure.
- Unnamed ambient characters ("a group of guards," "bystanders") do not require `npc_add`/`npc_remove` tracking.

EXAMPLE — NPC enters (correct):
Narration: "A red-haired man in boiled leather steps through the door and locks eyes with you."
`present_npcs` before: [caron]
→ Emit: `npc_add: { id: "red_haired_man", name: "Red-Haired Man", ... }`

EXAMPLE — NPC exits (correct):
Narration: "Caron spits on the floor and shoves through the crowd, disappearing into the street."
→ Emit: `npc_remove: { id: "caron" }`

EXAMPLE — NPC not mentioned, no remove (correct):
Narration does not mention Halden this turn.
→ Do NOT emit `npc_remove: { id: "halden" }` — absence ≠ departure.
```

**Why:** The current prompt has add/remove examples but no rule about when NOT to remove. The "absence ≠ departure" failure is the most common — the extractor removes NPCs simply because they aren't mentioned, causing `present_npcs` to shrink every turn.

**Validation:** Run a turn where Halden is in `present_npcs` but is not mentioned in narration. Confirm no `npc_remove` for Halden. Run a turn where narration explicitly says Caron leaves. Confirm `npc_remove` for Caron is emitted.

***

### Tests to write or update
- `tests/test_turn.py`: condition expiry test — condition with `turns_remaining: 1` expires after one turn, `condition_expired` event emitted.
- `tests/test_turn.py`: condition persistence test — condition with `turns_remaining: 3` decrements correctly over 3 turns.
- `tests/test_prompts.py`: render `extract_state_system.j2` — confirm CONDITION DURATION GUIDE and CONDITION RELEVANCE RULE present.
- `tests/test_prompts.py`: render `extract_scene_system.j2` — confirm NPC ENTER/EXIT RULE with all three examples present.

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: document condition age pass in `turn.py` — decrements `turns_remaining`, removes at 0, logs `condition_expired`.
- `docs/REPOMAP/prompts.md`: under `extract_state_system.j2` — add CONDITION DURATION GUIDE and RELEVANCE RULE.
- `docs/REPOMAP/prompts.md`: under `extract_scene_system.j2` — add NPC ENTER/EXIT RULE with examples.

### Risks
1. **`turns_remaining` field may be named differently** — executor must confirm the exact field name on the `Condition` model before implementing the age pass.
2. **`active_conditions` field on GameState** — executor must confirm whether conditions are stored as `state.active_conditions` or nested under `state.scene` or another sub-model.
3. **Permanent conditions** — the `turns_remaining is None` guard handles permanent conditions but the model must know it can emit `None` for permanent effects. The duration guide should note: "Omit `turns_remaining` (null) only for permanent effects like amputations or magical curses."

## Ambiguities requiring resolution before execution
1. Is `turns_remaining` already on the `Condition` Pydantic model? If it is not, the executor must add it as `turns_remaining: int | None = None` before implementing the engine-side decrement.
2. Are conditions stored on `state.active_conditions` or `state.scene.conditions` or another path? Executor must confirm the path before writing the age pass.

## TODO.md update
Add under **P2 — Stability / Fidelity**:
```
- [ ] [Condition Lifecycle: Duration, Relevance, and NPC Enter/Exit](plans/condition-lifecycle.md)
```
