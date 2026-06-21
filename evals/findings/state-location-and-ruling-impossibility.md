# Findings: State Extractor Location Changes & Ruling Engine Impossibility Conflation

**Date:** 2026-06-20
**Source:** `evals/runs/2026-06-20--0.28.0-29-g69faea92--69faea9/0432--noir-1930s--custom--30t/events.jsonl` (noir 0432)
  and `evals/runs/2026-06-20--0.28.0-28-ge3998180--e399818/0304--zombie-survival--custom--30t/events.jsonl` (zombie 0304)

---

## Issue 1: State Extractor Fails to Output location_change

### Symptom
In the last 2 turns of both noir 0432 and zombie 0304, the player clearly moved to a new location but `location_change` was not emitted by the state extractor. The game state did not update location.

### Evidence

**Noir 0432 turn 29:**
- Player input: "sneak: William Brandon attempts to find cover in an alleyway"
- Narration: "He lunges toward the narrow gap between the building and the neighboring brick structure, ducking into the darkness of the alleyway..."
- State extractor output: `{"condition_change_reason": "...", "inventory_change_reason": "...", ...}` — **no `location_change`**

**Noir 0432 turn 30:**
- Player input: "I draw my Colt Detective Special and follow him into the shadows of the alley."
- State extractor output: no `location_change` (correct — same location)

**Zombie 0304 turn 30:**
- Narration: "Marcus Walter discovered a diagnostic monitor... while seeking refuge in Service Conduit"
- State extractor output: no `location_change` (should have one)

### Root Cause

The design (`docs/design/consolidate-scene-location-extraction-design.md`) was fully implemented in commit `e443589`. The pipeline is correctly wired:

- `pipeline.py:329-331`: reads `location_change`/`location_description` from `state_result` ✓
- `context.py:54,68-69`: reads from `state_result` ✓
- `StateExtractResult` has `location_change` and `location_description` fields ✓
- `SceneExtractResult` no longer has location fields (pure NPC) ✓

The problem is **LLM output quality**: the state extractor prompt (`extract_state_system.j2:129-131`) instructs the LLM to output `location_change`, but the LLM is not following the instruction. The prompt is ~130 lines focused on inventory/conditions, with location_change instructions as only 2 lines (129-131) at the end. The LLM is not comparing the current location (shown in user prompt) against the narration to detect changes.

### Fix

Strengthen location_change instructions in the state extractor prompt:

1. **Add location context to state extractor user prompt** — `extract_state_user.j2` already has `## location` section, but it may need to be more explicit about comparing current vs. new location
2. **Expand location_change instructions in `extract_state_system.j2`** — add examples showing when location_change should/shouldn't be emitted, similar to how inventory/conditions have examples
3. **Add location to state extractor system prompt examples** — show a concrete example of location_change output

The architecture is correct (state extractor owns location). The fix is prompt engineering, not wiring changes.

---

## Issue 2: Ruling Engine Conflates Narrative Pivot vs Physical Feasibility

### Symptom
The ruling engine classifies "following an NPC that isn't present" as `impossible: true`, when it should be a check (hard/extreme difficulty) or a check.required determination.

### Evidence

**Noir 0432 turn 30:**
- Player input: "I draw my Colt Detective Special and follow him into the shadows of the alley."
- Ruling output: `{"impossible": true, "reason": "No NPC is currently present in the scene to follow.", "check": {"required": false}}`
- This is wrong. The player CAN physically draw and move. The question is whether they succeed in following someone. This should be a check (hard difficulty — following someone in shadows) or at minimum check.required=true with a check.

**Noir 0432 turn 29:**
- Player input: "sneak: William Brandon attempts to find cover in an alleyway..."
- Ruling output: `{"impossible": false, "reason": "Moving into shadows is routine and lacks immediate threat.", "check": {"required": false}}`
- This is correct — no check needed for moving into shadows.

### Root Cause

The ruling prompt (`ccya/prompts/ruling_system.j2:19-33`) lists "Punch X NPC - NPC is not in scene/location" as an **impossibility** example:

```markdown
**Impossible** — set `impossible=true`, `check.required=false`, write reason. Only when the action literally cannot happen — a tangible, objective barrier:
- Requires an item the character doesn't have or is in an unusable state
- Requires a capability contradicted by an active condition
- Acts on something not present in the scene
- "Draw my sword" — sword not in inventory
- "Fire my rifle" — rifle is broken or out of ammo
- "Pay the guard" — no currency in inventory
- "Lift the boulder" — missing an arm
- "Punch X NPC" - NPC is not in scene/location
```

The LLM is treating NPC absence as impossibility. But "following an NPC" is not physically impossible — it's a check with difficulty modifiers. The player can draw and move; the check is whether they succeed.

The ruling prompt conflates two distinct concepts:
1. **Physical impossibility** (no sword in inventory, missing arm, broken rifle) — correct as impossibility
2. **Narrative impossibility** (NPC not present) — should be a check, not impossibility

The NPC roster shown to the ruling LLM (`ruling_user.j2:7`) only includes NPCs with `presence == "present"`. Unnamed NPCs or NPCs that are "nearby"/"known" are invisible. The LLM sees "no NPC present to follow" and classifies it as impossible.

### Fix

Remove "Punch X NPC - NPC is not in scene/location" from the impossibility examples in `ccya/prompts/ruling_system.j2`. NPC absence should be:
- A **difficulty modifier** (harder check — e.g., "hard" because you can't see who you're following)
- A **check.required** determination (is it a narrative pivot?)
- Not an impossibility

The impossibility check should only cover physical/tangible barriers:
- Missing inventory item
- Active condition that physically prevents the action
- Environmental barrier (wall, locked door, etc.)

**Recommended fix:** Edit `ccya/prompts/ruling_system.j2` to replace the NPC example with:
```
- "Punch X NPC" — NPC is physically behind a wall/barrier you cannot pass through
```
This keeps the example but clarifies it must be a physical barrier, not just "not present."

---

## Files Affected

| File | Change Needed |
|------|--------------|
| `ccya/prompts/extract_state_system.j2` | Expand location_change instructions with examples |
| `ccya/prompts/extract_state_user.j2` | Strengthen location context (compare current vs. new) |
| `ccya/prompts/ruling_system.j2:28` | Fix NPC impossibility example |
