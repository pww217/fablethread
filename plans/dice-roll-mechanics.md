# Dice Roll Mechanics Fixes

## Status
`open`

## Phases

2 phases covering three dice mechanics concerns: (1) critical success threshold now considers modifiers alongside raw die, (2) roll display in narration includes skill name and full math breakdown, (3) compactor sanitization reasons wired through to UI. These changes touch rules engine output, narrator prompt rendering, compaction model + prompt + parsing + TV template — all centered on making dice outcomes more transparent and actionable for the player.

## Issue
Dice mechanics are under-exposed to both the LLM narrator and the player. Critical successes only trigger on raw_die == 12, ignoring modifiers entirely (an 11+1 roll that hits final_total 12 is just a "success"). Roll results shown in narration don't specify which skill was rolled or show the math breakdown ("8 + 2 = 10"), making it opaque what mechanics drove an outcome. Additionally, compactor sanitization actions have no human-readable reason explaining WHY something was removed/merged, so when sanitization appears in the TV UI it's just a count with no context.

## Solution
Update `compute_band()` to treat high raw dice (10-11) combined with favorable modifiers that push final_total ≥ 9 as potential critical successes — matching player expectations that "12 total" should feel like a crit even if the die wasn't natural 12. Add skill name and full math display (`N + N (SkillName) = N`) to `narrate_user.j2` rules_outcome section so both narrator and player see transparent mechanics. Add a `reason: str | None` field to `CompactorSanitizationAction`, update the compact prompt to require reasons, wire through parsing → state application → event payload → TV template display.

## Firm decisions
1. Critical success triggers when `final_total >= 12` (not just raw_die == 12). This covers natural max dice plus any roll where modifiers push the total to match or exceed a natural 12. All other band thresholds remain unchanged.
2. Roll display format: `N + N (Skill) [+ N condition] = N → BAND` — e.g., `"8 + 2 (Strength) + -1 (Wounded) = 9 → SUCCESS"`. Condition modifiers shown inline when non-zero.
3. Sanitization reasons are optional for the LLM but included in output when available; `reason: str | None` with default None so existing behavior doesn't break if reason is omitted.

## Non-goals
- **recent_events dedup threshold:** The recent_events system was deleted during the world-state-history-redesign (completed plan 04-pipeline/world-state-history-redesign). This feedback item no longer applies — there's nothing to raise a threshold on. Marked as obsolete; no code changes needed.
- **Storyteller prompt roll display:** The storyteller only receives `band` string, not full dice math. No change needed here since the storyteller doesn't narrate mechanics directly.
- **Compactor bullet content quality:** This plan only adds reasons to sanitization actions, not bullet summarization logic.

## Risks, Ambiguities, and Blockers
- The crit threshold rule (raw_die >= 10 AND final_total >= 9) is a design decision that changes outcome distribution slightly — more critical successes will occur when modifiers are favorable. This should be acceptable given the feedback indicates players expect high totals to feel like crits even without natural 12.
- Existing compaction data in saved games won't have reasons; the TV template must handle `reason` being absent gracefully (which it will since we use optional field).
- The narrate_user.j2 change adds more mechanical detail to prompts, which increases token usage per turn slightly (~5-10 tokens for skill name + math display).

## Implementation — Phase 1: Critical success threshold and roll display

### Context files to load
- `ccya/rules.py` (compute_band at line 120)
- `ccya/prompts/narrate_user.j2` (rules_outcome section at lines 70-86)
- `ccya/models.py` (RulesOutcome model at lines 165-182)

### Detailed steps

#### Step 1.1 — Update compute_band to use final_total >= 12 for critical success

**File:** `ccya/rules.py`, function `compute_band(final_total: int, raw_die: int) -> str` (lines 120-131)

**What:** Replace the crit_success condition from checking only `raw_die == 12` to checking `final_total >= 12`. Current logic at lines 121-124:
```python
if raw_die == 1:
    return "crit_fail"
if raw_die == 12:
    return "crit_success"
```

Change line 123 from `if raw_die == 12:` to `if final_total >= 12:`. That's the only change — all other conditions (crit_fail at lines 125-131) remain exactly as they are, including fail/setback/partial/success thresholds which already use final_total correctly.

**Why:** A roll of 11 + 1 (charisma) = 12 should be a critical success because it equals the same total as a natural 12. The current code ignores modifiers entirely for crit determination — only raw_die == 12 triggers crit_success, even though final_total already includes stat_mod + diff_mod + cond_mod at line 200 of rules.py.

**Validation:** Run `make check` after changes. Verify manually that:
- raw_die=12, final_total=12 → crit_success (unchanged)
- raw_die=11, stat_mod=+1, final_total=12 → **crit_success** (your example)
- raw_die=8, all mods=+4, final_total=12 → **crit_success** (modifiers pushed to 12)
- raw_die=6, all mods=+5, final_total=11 → success (below threshold)
- All fail/setback/partial/success thresholds unchanged from existing behavior

#### Step 1.2 — Add skill name and math display to narrate_user.j2 rules_outcome section

**File:** `ccya/prompts/narrate_user.j2`, lines 75-86 (the rules_outcome rendering block)

**What:** In the `{% elif rules_outcome and rules_outcome.rolled %}` branch, add a dice math display line between the band/directive line and the BINDING note. The new output should render:
```
**Roll:** {{ raw_die }} + {{ stat_mod_display }} ({{ skill_label }}) → {{ final_total }}
```

Where `stat_mod_display` shows individual components when non-zero (e.g., "+2" for positive, "-1" for negative). When condition modifiers exist and are non-zero, append them: e.g., "+ 2 (Strength) + -1 (Wounded)". The skill label should use the value from `rules_outcome.skill`.

The existing band/directive line stays; this adds a new roll math line above it. Structure:
```jinja2
{% elif rules_outcome and rules_outcome.rolled %}

**Roll:** {{ rules_outcome.dice[0] }} + {{ rules_outcome.stat_mod | default(0) }} ({{ rules_outcome.skill | title }}){% if rules_outcome.cond_mod != 0 %} + {{ rules_outcome.cond_mod }} (conditions){% endif %} → {{ rules_outcome.final_total }}

**Band:** {{ rules_outcome.band | upper | replace('_', ' ') }} → {{ rules_outcome.directive }}
```

Keep it concise — the narrator prompt already has all RulesOutcome fields available since `rules_outcome` is passed directly as a Python object.

**Why:** The feedback specifically requests "X + Y = Z should specify what skill Y is" (e.g., "8 + 2 (Strength) = 10"). This makes mechanics transparent to both the narrator LLM and any future player-facing display, reducing ambiguity about why an outcome occurred.

**Validation:** Run `make check`. Verify Jinja template renders correctly with all field combinations:
- Roll with no condition mods → `"6 + 2 (Strength) → 8"`
- Roll with negative condition mod → `"7 + 1 (Dexterity) + -1 (Wounded) → 7"`  
- All skills render title-cased properly

### Tests to write or update

No tests during refactor phase per AGENTS.md. Run `make check` at end of last phase only.

### REPOMAP updates required

None expected — no new files, interfaces, or module boundaries changed. The changes are internal logic (rules.py) and template rendering (narrate_user.j2). If a repomap exists for rules engine output sections, update the "dice resolution" bullet to note that compute_band now considers final_total in addition to raw_die for crit_success determination.

## Implementation — Phase 2: Compactor sanitization reasons

### Context files to load
- `ccya/models.py` (CompactorSanitizationAction at line 320, CompactorSanitizationResult at line 338)
- `ccya/engine/compactor.py` (_parse_compact_response at line 236, _apply_sanitization at line 282, compaction event record at lines 124-151)
- `ccya/prompts/compact_system.j2` (sanitization output format section at lines 58-92)
- `ccya/server/tv.py` (compaction event parsing at line 376, sanitization display)
- `ccya/templates/_turn_viewer.html` (sanitization rendering at lines 88-100)

### Detailed steps

#### Step 2.1 — Add reason field to CompactorSanitizationAction model

**File:** `ccya/models.py`, class `CompactorSanitizationAction` (lines 320-324)

**What:** Add a new optional field:
```python
class CompactorSanitizationAction(BaseModel):
    """A sanitization action with confidence level."""
    id: str
    reason: str | None = None
    confidence: Literal["high", "medium", "low"] = "high"
```

The `_coerce_sanitization_actions` validator (line 326) should pass through `reason` if present in input, defaulting to None. No changes needed there since it already handles dict passthrough for non-string items.

**Why:** Sanitization actions need human-readable explanations so the TV UI can show WHY something was removed/merged instead of just a count with no context.

**Validation:** `make check` — mypy should confirm the field is optional and compatible with existing coercion logic.

#### Step 2.2 — Update compact_system.j2 to require reasons in sanitization output

**File:** `ccya/prompts/compact_system.j2`, lines 58-92 (output format section)

**What:** In the JSON output example (lines 64-77), add a `reason` field to each action item. Update the checklist guidance and examples to mention reasons. Specifically:
1. Change the `_checklist` description to note that per-action reasons should be included in the JSON arrays
2. Add an instruction block after "Confidence guidelines" (around line 93) saying:

```markdown
### Reason field (MANDATORY for each action item)

Every item you include in sanitization lists MUST have a `reason` string explaining WHY this action is needed. Reference specific evidence from the bulletin or state that supports your decision. Examples:

- `"reason": "T12 bullet confirms player delivered ledger to contact — all objectives met"`
- `"reason": "Same name 'Marcus' and same role (dockworker) in both entries; bios consistent across turns 8-14"`
```

3. Update the JSON example to show items with reasons:
```json
{
  "_checklist": { ... },
  "pressure_remove": [
    {"id": "pursuers_approaching", "reason": "T12 bullet says 'Player escaped to river bend, pursuers lost'", "confidence": "high"}
  ],
  "npc_merge": [
    {"keep_id": "marcus_dockworker", "remove_ids": ["marus"], "reason": "Same name spelling variant; both described as dockworkers at the wharf with matching bio details from turns 8-14", "confidence": "high"}
  ]
}
```

**Why:** The LLM needs explicit instruction to include reasons. Without it, even if the field exists in the model, the LLM won't populate it (as seen currently — no reasons are being generated).

**Validation:** Read back a compaction event from an existing save and verify the prompt changes would produce reason fields. No runtime test needed; this is prompt-only guidance.

#### Step 2.3 — Wire reason through parsing, application, and event payload

**File:** `ccya/engine/compactor.py` (multiple locations)

**What:** Three small changes:
1. `_parse_compact_response()` at line 275 already validates sanitization through `CompactorSanitizationResult.model_validate(payload)` — since we added an optional field with default None, this will automatically accept and pass through any `reason` fields from the LLM output. No code change needed here; validation is automatic via Pydantic model update from Step 2.1.

2. `_apply_sanitization()` at line 282 — add logging that includes reasons for each action:
   - In npc_merge loop (around line 304): log the reason alongside merge info
   - In inventory_remove, pressure_remove, condition_remove loops: log reasons where available
   
   Example change to existing `_log.info` calls: append `reason=merge.reason` or similar structured field.

3. Compaction event record at lines 126-131 — the sanitization payload construction already uses `.model_dump()` on each action, so reason fields will automatically flow into the JSONL event output. No code change needed here either; Pydantic serialization handles it.

**Why:** The model field addition (Step 2.1) and prompt update (Step 2.2) are sufficient for data to flow through — but we should log reasons so they're visible in server logs during debugging, matching the structured logging standards from AGENTS.md.

**Validation:** `make check` passes. Manual verification: run a compaction cycle with debug logging enabled and confirm reason fields appear in both event JSONL records and server logs where applicable.

#### Step 2.4 — Display sanitization reasons in TV template

**File:** `ccya/templates/_turn_viewer.html`, lines 88-100 (sanitization display section)

**What:** Update the sanitization rows to show reasons alongside each action type:
- For npc_merge rows: after showing count, render individual merge entries with their reason strings
- For inventory_remove/condition_remove/pressure_remove rows: instead of just a count, list items with their reasons

Specific changes to lines 91-98: replace the simple count display with itemized lists that include reasons. Example for npc_merge (line 92):
```html
<template x-if="t.sanitization.npc_merge && t.sanitization.npc_merge.length">
    <div class="tv-compaction-san-row">
        NPCs merged: 
        <template x-for="(m, i) in t.sanitization.npc_merge" :key="'nm-'+i">
            <span>
                {{ m.keep_id }} ← [{{ m.remove_ids | join(', ') }}]
                <span x-show="m.reason" class="tv-san-reason" x-text="'— ' + m.reason"></span><br>
            </span>
        </template>
    </div>
</template>
```

Similar treatment for inventory_remove, condition_remove, pressure_remove — show each item with its reason. Items without reasons should still display (just without the reason text) to maintain backward compatibility with older compaction events that don't have reasons.

**Why:** The feedback states "sanitization does not show up in UI anywhere" and "should add a reason for WHY it chose to sanitize something." Currently only counts are shown; itemized display with reasons makes sanitization transparent to the user reviewing turn history.

**Validation:** Open TV viewer on a save that has compaction events (with or without reasons) and verify rendering is correct in both cases. No automated test needed for template changes during refactor phase.

### Tests to write or update

No tests during refactor phase per AGENTS.md. Run `make check` at end of this phase only.

### REPOMAP updates required

If a repomap exists documenting the compaction pipeline, add/update:
- CompactorSanitizationAction model now has optional `reason` field (str | None)
- Sanitization reasons flow through: compact prompt → LLM output → _parse_compact_response → _apply_sanitization → event JSONL → TV template display
