# Narrative Remediation — Eval Run 20260512T154142Z_uufm2ojg

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Band-directive compliance | Prevent narrator from softening fail bands; enforce near-miss complication semantics instead of partial-success outcomes |
| 02 | NPC voice and cross-NPC contamination | Give each named NPC a distinct register; prevent "NPC voice bleed" where different NPCs speak in identical cadence |
| 03 | Player agency and HIGHEST PRIORITY rule | Detect and log turns where the GM beat overrides or supplants the stated player action; surface in trace |
| 04 | Pacing and de-escalation mechanics | Ensure `breathing_room` beats produce visible tonal shift; confirm de-escalation reward is reflected in narration when triggered |

## Objective
The eval judge scored narrative quality below mechanical integrity, citing: fail bands that narrated partial-success outcomes; named NPCs (Caron, Halden, dock toughs) whose dialogue was indistinguishable in register; turns where the GM beat consumed the player's stated action; and momentum floor runs that did not produce visible tonal relief. This plan targets those narration-quality failures at the prompt and engine level without touching extractor logic.

## Non-goals
- Extractor few-shots or schema changes — covered in prompt-quality plan.
- Engine momentum `_check_floor_relief` logic — covered in system-cohesion plan.
- Eval harness auto-checker changes — covered in eval-harness plan.
- Pack or scenario design changes beyond the narrator templates and a small `narrate_user.j2` context injection.

---

## Implementation — Phase 01: Band-directive compliance

### Files to pull for context
- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/rules.py` (`build_directive` — where the near-miss note is appended to fail directives)
- `ccya/engine/narrate.py` (`_narrate_messages` — how `rules_outcome` is injected into the prompt)

### Detailed steps

#### Step 1.1 — Strengthen the BINDING block's fail-band prohibition

**File:** `ccya/prompts/narrate_system.j2`

**What:** In the section that defines the narrator's band contract, add explicit counter-examples for fail-band narration under the BINDING block instructions. The examples must show what "not to do" before showing the correct form.

**Why:** The REPOMAP confirms `narrate_system.j2` already has a BINDING block and near-miss directive guidance. The judge found Caron offering a payment schedule and Halden counter-offering on fail bands — these are partial-success outcomes, not complications. The existing guidance needs to be reinforced with a negative example.

**Code Snippet**
```jinja
{# BINDING block — existing section #}
{# ADD under FAIL band: #}

When the band is FAIL:
- The PC does not get what they wanted.
- The NPC does NOT constructively engage to help the PC.
- A complication or setback changes the situation.

Do NOT narrate a FAIL as a partial success:
  BAD: Caron slides a revised payment offer across the table. (This is partial success.)
  GOOD: Caron closes the ledger and turns away. "We're done here." (This is failure with complication.)

The near-miss note (if present) permits a complication that changes the scene — NOT a soft win.
```

**Validation:** Re-run T1 and T3 turns with the updated template; confirm the narration does not include constructive NPC engagement on fail bands.

---

#### Step 1.2 — Clarify near-miss semantics at the `build_directive` output level

**File:** `ccya/rules.py`

**What:** In `build_directive`, when appending the near-miss complication note for `band == "fail"` with `final_total >= 6`, ensure the appended text explicitly says "complication that changes the situation, NOT a partial win" rather than open-ended "latitude."

**Why:** The current note is described as giving the narrator "latitude" — which is being interpreted as license to soften the failure. The note should be a directive toward a specific outcome type.

**Code Snippet**
```python
# Existing: directive += " Near miss — describe a complication that changes the scene."
# Replace with:
directive += (
    " Near miss: describe a setback or complication that changes the situation — "
    "NOT a partial success or a softened refusal. The PC still fails to get what they wanted."
)
```

**Validation:** Unit test `build_directive` with `band="fail"`, `final_total=6`; assert the output contains the "NOT a partial success" language.

---

### Tests to write or update
- `tests/test_rules.py`: add a test for `build_directive` near-miss note content.
- Snapshot test that renders the narrate user prompt for a fail-band turn and asserts the BINDING block contains the near-miss prohibition.

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md`: update narrate_system.j2 entry to note strengthened fail-band counter-examples.
- `docs/REPOMAP/rules.md`: document the updated near-miss note language.

### Risks
1. Strengthening fail-band language could make narration feel punitive across all fail bands, including low-stakes ones. Mitigation: keep the near-miss note conditional on `final_total >= 6` as currently implemented.

---

## Implementation — Phase 02: NPC voice and cross-NPC contamination

### Files to pull for context
- `ccya/prompts/narrate_user.j2` (especially the `known_characters` / `compendium_bios` block rendering)
- `ccya/engine/narrate.py` (`_narrate_messages` — how `compendium_bios` is passed)
- `ccya/prompts/sections/_world_state` (if it contains NPC voice guidance)

### Detailed steps

#### Step 2.1 — Inject NPC voice register into `known_characters` block

**File:** `ccya/prompts/narrate_user.j2`

**What:** In the `known_characters` / `compendium_bios` rendering block, after each NPC's bio, add a one-line "Voice register" field drawn from the NPC's `notes` or a new `voice_register` field if it exists in the compendium entry. If the field is absent, derive it from the bio: formal/terse/verbose/evasive.

**Why:** The judge found Caron, Halden, and the dock toughs spoke in identical cadence. The narrator has no per-NPC voice anchor. The bio alone is insufficient — a short "Voice: terse, formal, never offers more than asked" field changes how the model renders dialogue.

**Code Snippet**
```jinja
{% for npc in known_characters %}
### {{ npc.name }}{% if npc.title %} ({{ npc.title }}){% endif %}
{{ npc.bio }}
{% if npc.notes %}
Voice: {{ npc.notes }}
{% endif %}
{% endfor %}
```

*If `notes` is already used for other purposes, add a `voice_note` field to the compendium NPC model and populate it from the pack's NPC definitions.*

**Validation:** For the eval pack NPCs (Caron, Halden), confirm their `notes` or `voice_note` contains a voice register. Run a narration turn with both NPCs present; review narration for tonal difference.

---

#### Step 2.2 — Add a cross-NPC contamination rule to narrator system prompt

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add a brief directive under the NPC section: "Each named NPC must have a distinct speaking register. Do not let two NPCs sound identical. If two NPCs are present in the same beat, vary sentence length, vocabulary, and formality between them."

**Validation:** Prompt snapshot test confirms the directive is present in the rendered system prompt.

---

### Tests to write or update
- Prompt snapshot test for `_narrate_messages` with a state containing two NPCs with different `notes`; assert the rendered user prompt contains both voice fields.

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md`: narrate_user.j2 entry — document voice register injection.
- If `voice_note` is added to the compendium NPC model, update `docs/REPOMAP/state.md` compendium section and `docs/REPOMAP/models.md`.

### Risks
1. NPC `notes` may currently contain non-voice information (e.g., faction allegiance). If so, adding a separate `voice_note` field is preferable. Read the pack YAML and compendium NPC model before deciding which field to use.
2. The compendium NPC model is in `ccya/models/` — any new field must be added there and will change the model schema. Confirm no existing tests assert on the exact field list.

---

## Implementation — Phase 03: Player agency and HIGHEST PRIORITY rule

### Files to pull for context
- `ccya/prompts/narrate_system.j2` (HIGHEST PRIORITY player input rule)
- `ccya/engine/narrate.py` (`_narrate_messages` — how `pending_gm_beat` is injected)
- `ccya/eval/universal_asserts.py` (`check_pending_gm_beat_consumed`)

### Detailed steps

#### Step 3.1 — Add a log signal when GM beat displacement is detected

**File:** `ccya/engine/turn.py`

**What:** After narration completes, run a lightweight check: if `pending_gm_beat` was present and the narration does not contain any verbatim or near-verbatim phrase from the player's `user_input`, log a `WARNING` with `player_agency_risk=True`.

**Why:** The HIGHEST PRIORITY rule already exists in the prompt, but the engine has no telemetry on whether it was honored. This signal surfaces in logs and events without changing the narration.

**Code Snippet**
```python
if pending_gm_beat and user_input.split()[0].lower() not in narration.lower():
    log.warning(
        "potential player agency displacement",
        extra={
            "turn": turn_no,
            "trace_id": trace_id,
            "pending_gm_beat": pending_gm_beat.get("instruction", "")[:80],
            "player_agency_risk": True,
        },
    )
```

*This is a heuristic signal, not a hard enforcement. Keep it at WARNING, not ERROR.*

**Validation:** Run a turn where the GM beat instruction is the dominant event; check logs for the warning.

---

#### Step 3.2 — Reinforce player-action-first ordering in `narrate_system.j2`

**File:** `ccya/prompts/narrate_system.j2`

**What:** The REPOMAP notes the HIGHEST PRIORITY rule already has "HIGHEST PRIORITY player input rule with concrete conflict example." Verify that the concrete example shows a case where a GM beat was present and the player action was still narrated first. If the example is abstract, replace it with a turn-shaped example.

**Code Snippet**
```jinja
{# HIGHEST PRIORITY — player action first #}
Even when a GM beat instruction is present, narrate the player's action first.

Example:
  Player input: I walk to the window and look out.
  GM beat: The informant enters the tavern.
  CORRECT: You cross to the window and look out over the rain-slicked street.
           Behind you, the door opens and a hooded figure steps inside.
  WRONG: A hooded figure steps through the door, drawing every eye in the room.
         You glance toward the window.
```

**Validation:** Confirm the updated example is present in the rendered system prompt via snapshot test.

---

### Tests to write or update
- `tests/test_engine_smoke.py` or a new `tests/test_player_agency_log.py`: mock a turn with a GM beat and a player input; assert the `player_agency_risk` warning fires only when the player's first verb does not appear in the narration.

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md`: narrate_system.j2 entry — note the reinforced HIGHEST PRIORITY example.

### Risks
1. The first-verb heuristic in Step 3.1 will false-positive on very short player inputs ("Yes.", "I wait."). Add a minimum word-count guard: skip the check if `len(user_input.split()) < 3`.

---

## Implementation — Phase 04: Pacing and de-escalation mechanics

### Files to pull for context
- `ccya/prompts/narrate_user.j2` (Breathe block, de-escalation reward, momentum floor directive)
- `ccya/engine/turn.py` (`_check_floor_relief` — where `breathing_room` beat is injected)
- `ccya/engine/narrate.py` (`_narrate_messages` — `deescalate` and `pending_gm_beat` params)
- `docs/REPOMAP/prompts.md` (narrate_user.j2 entry: "de-escalation reward on Breathe block", "momentum floor two-tier directive")

### Detailed steps

#### Step 4.1 — Confirm `breathing_room` beat renders in the BINDING block

**File:** `ccya/prompts/narrate_user.j2`

**What:** Verify that when `pending_gm_beat.kind == "breathing_room"`, the rendered user prompt explicitly labels it as a tonal instruction ("ease tension, shift to a quieter moment") rather than a plot event. If the Breathe block renders it identically to other GM beats, add a conditional branch.

**Code Snippet**
```jinja
{% if pending_gm_beat %}
{% if pending_gm_beat.kind == "breathing_room" %}
**Breathe:** {{ pending_gm_beat.instruction }} — ease tension, allow a quieter moment before the next pressure.
{% else %}
**GM Beat:** {{ pending_gm_beat.instruction }}
{% endif %}
{% endif %}
```

**Validation:** Snapshot test that renders the narrate user prompt with a `breathing_room` beat; assert "ease tension" language appears and not the generic "GM Beat" label.

---

#### Step 4.2 — Add de-escalation tonal instruction to user prompt when `deescalate > 0`

**File:** `ccya/prompts/narrate_user.j2`

**What:** The REPOMAP notes `deescalate` is a float (0.0–1.0) injected into the narrate prompt. Verify the template renders a visible de-escalation reward sentence when `deescalate > 0.5` (high magnitude). If the template already does this, confirm the instruction is imperative ("soften the tone") not conditional ("you may soften the tone").

**Code Snippet**
```jinja
{% if deescalate and deescalate > 0.5 %}
**De-escalation:** The player has reduced pressure through their actions. Soften the tone — fewer threats, more breathing room, calmer NPC reactions.
{% elif deescalate and deescalate > 0 %}
**De-escalation:** Some pressure has eased. Slightly softer tone where natural.
{% endif %}
```

**Validation:** Snapshot test for `deescalate=0.8`; assert the imperative de-escalation instruction is present.

---

#### Step 4.3 — Verify momentum floor two-tier directive renders correctly

**File:** `ccya/prompts/narrate_user.j2`

**What:** The REPOMAP notes a two-tier momentum floor directive: `-2` softens, `-3` mandatory relief. Confirm the template renders the `-3` tier as a mandatory instruction (not advisory) and that the boundary is exactly `-3` (matching `MOMENTUM_MIN`).

**Code Snippet**
```jinja
{% if momentum <= -3 %}
**MOMENTUM FLOOR — MANDATORY:** The situation must ease. Narrate a moment of relief, luck, or unexpected help. This is not optional.
{% elif momentum <= -2 %}
**Momentum low:** Consider softening the tension. A small reprieve is appropriate.
{% endif %}
```

**Validation:** Snapshot test with `momentum=-3`; assert mandatory language appears. With `momentum=-2`, assert advisory language only.

---

### Tests to write or update
- `tests/test_prompt_audit.py` or new `tests/test_narrate_prompt_pacing.py`: snapshot tests for all three new/verified conditional blocks (`breathing_room` beat, `deescalate` tiers, `momentum` tiers).

### REPOMAP and architecture updates
- `docs/REPOMAP/prompts.md`: narrate_user.j2 entry — document the `breathing_room` beat conditional, `deescalate` tiers, and confirmed momentum tier boundary.

### Risks
1. If `deescalate` is currently rendered as a boolean in the template context rather than a float, the `> 0.5` threshold will not work. Confirm the type in `_narrate_messages` before the template change.
2. Adding a strong mandatory instruction at `momentum=-3` may feel jarring if the player deliberately wants a grim scene. This is a design trade-off: the two-tier system was chosen precisely to provide relief at floor; document that it is intentional.

---

## Ambiguities requiring resolution before execution

1. Does the compendium NPC model have a `notes` or `voice_note` field? Or is `notes` on `NpcRef` (present_npcs) only? Read `ccya/models/` and `docs/REPOMAP/models.md` before Phase 02 Step 2.1.
2. Is `deescalate` passed to `_narrate_messages` as a float (0.0–1.0) or a bool? Confirm in `ccya/engine/narrate.py` and `ccya/engine/turn.py` before Phase 04 Step 4.2.
3. Does `pending_gm_beat` have a `kind` field that can be `"breathing_room"`? Read the `GmBeat` model in `ccya/models/` before Phase 04 Step 4.1. If `kind` does not exist, determine the correct field to distinguish beat types.
