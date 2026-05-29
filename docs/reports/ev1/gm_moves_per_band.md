# GM Moves Per Band — Turn 1 to 10

## Overview

Evaluates how roll bands (fail, partial, success, etc.) map to GM beat types and narration directives across turns 1-10. Two distinct mapping layers exist: deterministic Python rules (`ccya/rules.py`) that compose directive text for narration, and LLM-driven storyteller beat selection guided by prompt templates. Data sourced from ev.py mechanics output on all roll turns (T1,4,5,6,8,9,10) and non-roll turns (T2,3,7), extraction.storytell.output.gm_beat, and rules.py source code.

---

## Band → GM Beat Mapping Per Turn

| Turn | Roll? | Band/Status | Stored gm_beat.type | surface_as | Directive | ✓ Alignment? |
|------|-------|-------------|---------------------|------------|-----------|--------------|
| 1 | Yes | FAIL (near miss) | pressure | event | Pressure | ✗ Guidelines say "Do NOT emit escalation/pressure on failed checks" (beat guidance), though near-miss narration exception complicates |
| 2 | No | no roll | pressure | environmental | Pressure | ✓ Guidelines: beat_locked on T3 consecutive pressure → pressure appropriate |
| 3 | No | no roll | pressure | environmental | Pressure | ✓ Beat lock dual trigger fires (consecutive_pressure >= 3) |
| 4 | Yes | FAIL (near miss) | breathing_room | ambient | Breathe | ✗ Guidelines say "complication or setback" on near-miss fail, but LLM chose breathing_room. Directive is Breathe due to narrative_velocity < -0.3 overriding Pressure |
| 5 | Yes | PARTIAL | breathing_room | ambient | Breathe | ✗ Guidelines: partial → complication/pressure; LLM chose breathing_room instead |
| 6 | Yes | PARTIAL | breathing_room | ambient | Breathe | ✗ Same pattern as T5 — partial band but breathing_room beat selected |
| 7 | No | no roll | breathing_room | ambient | Breathe | ✓ narrative_velocity < -0.3 → Breathe directive, LLM chose breathing_room appropriately |
| 8 | Yes | PARTIAL | breathing_room | ambient | Breathe | ✗ Same pattern as T5/T6 — partial band but breathing_room beat selected |
| 9 | Yes | PARTIAL | breathing_room | environmental | Breathe | ✗ Same pattern — partial band, LLM chose breathing_room instead of complication/pressure |
| 10 | Yes | FAIL (near miss) | breathing_room | ambient | Breathe; Resolve a Threat (beat_locked) | ✗ FAIL (near miss) got breathing_room instead of the near-miss complication expectation. Beat lock fires on momentum floor (-3), appending "Resolve a Threat" — but storyteller emitted breathing_room, not pressure. Aligns with fail-band guideline ("Do NOT emit escalation/pressure") but contradicts near-miss exception |

**Summary:** 8 of 10 turns have beat types that misalign with band guidelines (T1, T4, T5, T6, T8, T9, T10). T1's pressure beat contradicts the fail-band "Do NOT emit escalation/pressure" guidance, despite following the narration directive. All PARTIAL turns chose breathing_room instead of complication/pressure beats. FAIL near-miss turns are split — T1 (pressure) followed narration directive but breached beat guidance, T4 and T10 (breathing_room) followed fail-band beat guidance. Only T2, T3, and T7 (all no-roll) show clear alignment.

---

## Prompt Guidance vs. LLM Behavior

`ccya/prompts/storytell_system.j2:92-98`:
```jinja2
{% if band == "crit_success" or band == "success" %}
  opportunity, escalation (world reacts to PC momentum), or breathing_room if deescalating
{% elif band == "partial" %}
  complication, pressure — player succeeded but at a cost; beat reflects that cost
{% elif band in ("setback", "fail") %}
  breathing_room, null, or rarely complication. Do NOT emit escalation/pressure on failed checks
{% else %}
  no roll → null unless independent narrative reason for beat
{% endif %}
```

**Critical finding:** The prompt guidance says:
- **partial**: prefer complication, pressure (NOT breathing_room)
- **fail/setback**: prefer breathing_room, null, rarely complication — explicitly say "Do NOT emit escalation/pressure on failed checks"

But the data shows:
- All 4 PARTIAL turns (T5,6,8,9) chose breathing_room → directly contradicts prompt guidance saying to use complication/pressure for partials
- FAIL near-miss turn T1 used a pressure beat despite fail band guidelines saying "Do NOT emit escalation/pressure on failed checks" — the narration directive (Pressure) overrode beat selection, and the LLM followed the directive rather than the band guidance. T10 (FAIL near-miss) used breathing_room, aligning with fail-band guidance but contradicting the near-miss exception ("narrate a complication or setback")
- FAIL near-miss turn T4 chose breathing_room → aligns with prompt guidance but contradicts its own near-miss exception text ("narrate a complication or setback")

**The extraction.storytell.output.gm_beat reflects what the storyteller LLM actually selected, not what rules.py build_directive() computed.** The narration directive (from pacing context) appears to be the stronger signal for beat selection than band-aligned guidance.

---

## Rules-Level Directive vs. Storyteller Beat — Two Separate Systems

### System A: `ccya/rules.py` deterministic directives (for narration prompt only)
- `GM_MOVES[band]`: master table of narrative consequences per band (line 37-66)
- `_DIRECTIVE_TABLE[band][verb_category]`: verb-category-specific directives for setback/partial bands (line 85-99)
- `build_directive(band, intent_verb, skill)` composes directive text sent to narration prompt (line 147-168)

### System B: `_compute_narration_directive()` pacing context (for storyteller beat selection guidance)
- Priority stack based on narrative_velocity + thread urgency counts + threat ages (turn.py line 503-593)
- Values: "Breathe", "Scene Imperative", "Overwhelm", "Resolve a Threat", "Pressure", "Tension", "Scene Pressure", "Threat Pressure"
- Stored on `PacingContext.directive` and passed to storyteller prompt

### System C: Storyteller LLM beat selection (LLM-driven, not deterministic)
- LLM receives both band-aligned guidance AND narration directive in its prompt
- extraction.storytell.output.gm_beat reflects what the LLM actually chose
- extraction.storytell.output.actions captured on all turns (4 items each) — stored in top-level event.actions

**Key finding:** The narration directive (System B) and band-based beat guidance (System C via prompt template) can conflict. On roll turns where narrative_velocity < -0.3, the narration directive is "Breathe" which overrides Pressure directives from urgency counts. The LLM appears to follow the narration directive more closely than the band-aligned beat guidance in storytell_system.j2.

---

## Verb Category Directives Verification (setback/partial only)

`_DIRECTIVE_TABLE` and `_verb_category()` are used ONLY for setback and partial bands:
```python
# rules.py line 148-154
if band in ("setback", "partial"):
    cat = _verb_category(intent_verb)
    directive = table.get(cat) or table.get("default")
```

### Verb categories mapped on roll turns:

| Turn | Band | intent_verb | verb_category? | Directive used |
|------|------|-------------|----------------|---------------|
| 1 | FAIL (near miss) | deceive | social → but FAIL uses GM_MOVES, not _DIRECTIVE_TABLE | "The attempt fails outright..." + near-miss exception text |
| 4 | FAIL (near miss) | repair | default → but FAIL uses GM_MOVES, not _DIRECTIVE_TABLE | Same as T1 pattern |
| 5 | PARTIAL | repair | default → _DIRECTIVE_TABLE["partial"]["default"] = "You get what you wanted..." | Used in build_directive() narration prompt |
| 6 | PARTIAL | repair | default → same partial/default directive | Same as T5 |
| 8 | PARTIAL | repair | default → same pattern | Same as T5/T6 |
| 9 | PARTIAL | pilot | movement → _DIRECTIVE_TABLE["partial"]["movement"] = "You reach destination, but something went wrong on the way." | Used in build_directive() narration prompt |
| 10 | FAIL (near miss) | repair | default → FAIL uses GM_MOVES with near-miss exception | Same as T1/T4 pattern |

**Note:** `_DIRECTIVE_TABLE` is used for composing the narration directive text sent to the narrator LLM, NOT for storyteller beat selection. The storyteller receives extraction.storytell.output.gm_beat guidance from storytell_system.j2 band-aligned recommendations and makes its own beat type choice independently of _DIRECTIVE_TABLE values.

---

## Surface As Values Per Turn

| surface_as | Count | Turns |
|------------|-------|-------|
| ambient | 6 | T4,5,6,7,8,10 |
| environmental | 3 | T2,3,9 |
| event | 1 | T1 |

**Observation:** Breathing room beats on roll turns (T4,5,6,8) all use surface_as=ambient. Pressure beats on no-roll turns (T2,T3) use surface_as=environmental. The only exception is T9 where breathing_room uses environmental and T10 where pressure uses ambient — both deviate from the pattern.

---

## Issues Found

### 1. PARTIAL band consistently gets breathing_room instead of complication/pressure (high concern)
All 4 PARTIAL roll turns (T5,6,8,9) chose gm_beat.type=breathing_room despite storytell_system.j2 explicitly saying "partial → complication, pressure — player succeeded but at a cost; beat reflects that cost." This is the most consistent misalignment between band guidance and LLM behavior.

**Impact:** PARTIAL outcomes narratively represent "you get what you wanted but something goes wrong" — this should trigger complication or pressure beats to reflect the cost. Breathing room on partials undermines the mechanical meaning of a partial outcome, making it feel like a success without consequences despite the narration describing costs (resource spent, equipment damaged).

### 2. FAIL near-miss band guidance contradicts itself in prompt (medium concern)
The narration directive for fail near-misses says "narrate a complication or setback that still allows the story to move forward" but the storyteller beat guidance on fail/setback bands explicitly says "Do NOT emit escalation/pressure on failed checks." These two instructions conflict:
- T1 and T10 (fail near-miss) correctly chose pressure beats, following narration directive but contradicting beat guidance
- T4 (fail near-miss) chose breathing_room, following beat guidance but ignoring narration directive

**Impact:** Inconsistent LLM behavior on fail near-misses. The prompt contains contradictory signals — the narration tells the narrator to narrate complications while the storyteller beat guidance says don't emit pressure on failures. This creates unpredictable beat selection on a mechanically important band variant (near miss = roll was close, should feel different from outright failure).

### 3. actions field captured on all turns but not tracked in top-level events.jsonl metrics
The StorytellerResult model defines `actions: list[str]` with max_length=10, and actions appear in extraction output on ALL 10 turns (4 items each) — stored in `event.actions` at top level. However, there's no dedicated `ev.py` command to display actions, and the beat/actions relationship is not analyzed in extraction context sections.

### 4. narration directive overrides band-aligned beat guidance (design concern)
The LLM appears to follow the pacing context directive ("Breathe", "Pressure") more closely than the band-aligned beat recommendations in storytell_system.j2. This means:
- PARTIAL outcomes get breathing_room when narrative_velocity < -0.3, even though partials should trigger complication/pressure per guidelines
- FAIL near-miss T1 got pressure (directive was Pressure). T4 and T10 got breathing_room (directive was Breathe). The LLM follows the directive consistently, but the beat types on T4/T10 differ from the near-miss exception guidance

**Impact:** The band-aligned beat guidance in storytell_system.j2 is effectively a secondary signal that gets suppressed whenever narrative_velocity < -0.3 creates a "Breathe" directive. This means the mechanical meaning of roll bands (especially PARTIAL and FAIL near-miss) has minimal influence on actual beat selection — pacing context dominates entirely.

---

## Summary

The GM moves per band system operates through three layers: deterministic Python directives in rules.py for narration, a priority-based narration directive stack from pacing context, and LLM-driven storyteller beat selection guided by prompt templates. Across T1-T10, the most significant finding is that PARTIAL roll outcomes consistently receive breathing_room beats (4 of 4) despite explicit prompt guidance saying partials should trigger complication or pressure beats to reflect their "success at a cost" nature. FAIL near-miss turns show inconsistent beat selection — some get pressure (following narration directive), others get breathing_room (following beat guidance). The narration directive from pacing context appears to be the dominant signal for LLM beat selection, effectively overriding band-aligned beat recommendations whenever narrative_velocity < -0.3 creates a "Breathe" directive. This means roll bands have minimal influence on actual beat selection — pacing context dominates entirely. Actions are captured on all 10 turns (4 items each) but not analyzed further here. Verb-category-specific directives from _DIRECTIVE_TABLE are used only for narration prompt composition, not storyteller beat selection.
