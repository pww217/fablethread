# Eval Remediation — May 10 Cycle

## Status
`open`

## Part of
Eval remediation — May 2026 cycle

## Dependencies
- Completed: `eval-results-remediation2/` (all 11 phases)
- Completed: `compactor-overhaul.md` (compactor infrastructure)
- Completed: `eval-results-remediation/` (phases A–E, system hardening Phases 01–10)
- None required from open plans

## Conflicts and overlap
None. The existing `eval-remediation/01-extractor-grounding-and-compactor-fix.md` touches `extract_state_system.j2`, `extract_scene_system.j2`, `extraction.py`, and `universal_asserts.py` — but for condition dedup, location change guard, and NPC matching. This plan touches `compact_system.j2`, `narrate_system.j2`, and `extract_state_system.j2` — for compactor sanitization, narrator input validation, and currency mapping. The `extract_state_system.j2` overlap is non-conflicting: the existing plan adds condition dedup directives, this plan strengthens the generic item mapping section. Both are prompt-only changes to different sections of the same file. The `progress-rules-narration.md` plan is about GM beat ownership and does not touch any files in this plan.

## Objective
Fix three critical mechanical failures identified in the May 10 eval runs (e2fxi7rc and trrtunn7): (1) the compactor fires at turns 6 and 12 but the LLM returns empty sanitization JSON, leaving completed quests, resolved pressures, and expired conditions in state; (2) the narrator ignores player input on Turn 7, outputting stale context and breaking immersion; (3) the state extractor invents currency IDs (`iron_coins`) instead of mapping generic terms to existing inventory IDs (`credits`), causing delta rejections and runner errors. These three issues account for all runner errors, all rejected deltas, and are the primary drivers of the low mechanical score (3/5).

## Non-goals
- Fixing auto-checker false positives (flags known locations/items as NPCs) — already addressed in `eval-results-remediation2/` Phase 11
- Fixing premature objective completion in progress extractor — lower impact, prompt-only, deferred
- Fixing scene pressure ID validation (quest ID used as pressure ID) — lower impact, prompt-only, deferred
- Adding new config keys or Pydantic model fields
- Changing the compactor's bullet generation logic (only fixing sanitization JSON production)
- Adding pre-narration engine validation step (prompt-only fix for now)

## Affected files

| File | Change type | Summary |
|---|---|---|
| `ccya/prompts/compact_system.j2` | modify | Strengthen sanitization directive with concrete examples and lower confidence threshold |
| `ccya/engine/compactor.py` | modify | Add debug logging for LLM sanitization output to diagnose empty JSON |
| `ccya/prompts/narrate_system.j2` | modify | Add explicit "process current turn input" directive and turn-number anchoring |
| `ccya/prompts/extract_state_system.j2` | modify | Strengthen generic item mapping section with explicit "credits" example and negative constraint |
| `docs/plans/TODO.md` | modify | Add new eval remediation items for compactor sanitization, narrator input, currency mapping |
| `docs/REPOMAP/engine.md` | modify | Update compactor description with new debug logging |
| `docs/REPOMAP/prompts.md` | modify | Update compact_system, narrate_system, extract_state_system descriptions |

## Firm decisions

1. **Compactor fix is prompt-only.** The engine code (`_apply_sanitization`) is correct — it validates IDs and applies deltas. The LLM is returning `{}` because the prompt's "highly confident" threshold is too conservative. We lower the threshold and add concrete examples of what to flag.

2. **Narrator fix is prompt-only.** Adding an engine-level pre-narration validation step would add latency and complexity. The root cause is the LLM losing track of which turn's input to process. Strengthening the prompt with explicit turn anchoring and a "process current input" directive is sufficient.

3. **Currency mapping fix is prompt-only.** The existing generic item mapping section exists but the LLM ignores it. We strengthen it with an explicit `credits` example and a stronger negative constraint ("NEVER invent currency IDs").

4. **No engine code changes for delta validation.** The `_validate()` function correctly rejects invalid inventory removals. The fix is upstream — prevent the LLM from emitting invalid IDs in the first place.

---

## Implementation — Phase 1: Compactor Sanitization Fix

### Context files to load
1. `ccya/prompts/compact_system.j2`
2. `ccya/engine/compactor.py` (lines 1–130)
3. `ccya/models.py` (CompactorSanitizationResult, lines 363–372)

### Overview
The compactor fires at turns 6 and 12 but the LLM returns empty sanitization JSON (`{}`), leaving completed quests active, resolved pressures in state, and expired conditions unremoved. The prompt's "highly confident" threshold is too conservative — the LLM needs concrete examples of what constitutes a fixable issue and a lower bar for flagging obvious problems. This phase adds debug logging to diagnose the LLM's output and strengthens the prompt.

### Detailed steps

#### Step 1.1 — Add debug logging to compactor sanitization path

**File:** `ccya/engine/compactor.py`

**What:** Add logging around the `_parse_compact_response` call and the `_apply_sanitization` call to capture what the LLM actually returns. This will help diagnose whether the LLM is returning `{}`, malformed JSON, or something else.

**Why:** Without visibility into the LLM's sanitization output, we cannot verify whether the prompt fix works. The log will show the raw sanitization JSON and whether it was parsed successfully.

**Code Snippet**
```python
# In maybe_compact(), after line 90 (bullets_text, sanitization = _parse_compact_response(response_text)):

    _log.debug(
        "compactor: LLM sanitization raw = %r, parsed = %s",
        response_text[-500:] if len(response_text) > 500 else response_text,
        sanitization,
        extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
    )

    if sanitization is not None:
        _log.info(
            "compactor: applying sanitization: quest_close=%s pressure_remove=%s condition_remove=%s",
            san.quest_close if (san := sanitization) else [],
            san.pressure_remove if san else [],
            san.condition_remove if san else [],
            extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "compactor"},
        )
```

**Validation:** Run `make check` to verify no type errors. The new log lines use `_log.debug` and `_log.info` with the existing `extra` context pattern.

#### Step 1.2 — Strengthen compactor sanitization prompt

**File:** `ccya/prompts/compact_system.j2`

**What:** Replace the PART 2 "State sanitization" section with a stronger directive that lowers the confidence threshold, adds concrete examples of what to flag, and explicitly instructs the LLM to always produce sanitization JSON (never omit it).

**Why:** The current prompt says "Only flag problems you are **highly confident** about — false positives cause data loss." This is too conservative. The LLM interprets this as "don't flag anything unless you're 100% sure." We need to flip the default: flag obvious issues, omit uncertain ones.

**Code Snippet**
```jinja2
## PART 2: State sanitization

You have the full mechanical state. Identify structural problems that should be fixed.

**Default to flagging.** If an issue is obvious from the bulletin and state, flag it. When in doubt, include it — the engine validates all IDs and silently skips unknown ones. False negatives (missing fixes) are worse than false positives (skipped unknown IDs).

### What to flag

**quest_close** — An active quest where ALL objectives have `done: true` but the quest status is still `active`. This is a mechanical bug — close it. Also flag quests whose narrative conclusively ended (e.g., "the debt was paid") but the quest is still listed as active.

**pressure_remove** — A `scene_pressure` entry whose triggering situation has been resolved. Examples: the pursuers were escaped (remove `purposeful_pursuit`), the deadline passed without consequence (remove `ledger_delivery_deadline`), the confrontation ended (remove `toughs_aggression`).

**condition_remove** — A `pc.condition` that the bulletin clearly shows was treated or resolved. Examples: "wrapped wounds to stave off pain" → remove the wound condition; "rested and recovered" → remove fatigue conditions. Do NOT remove conditions that might still plausibly apply.

**npc_merge** — Two compendium NPC entries that are clearly the same person under different IDs (same name, same role, consistent bios). Provide `keep_id` (canonical) and `remove_ids` (duplicates).

**inventory_remove** — An inventory item that appears twice with different IDs but identical name and purpose. Provide the ID of the copy to remove.

### Output format

After the bullet lines and a blank line, output exactly one JSON object. You MUST output this — even if nothing needs fixing, output `{}`.

```json
{
  "quest_close": ["quest_id"],
  "pressure_remove": ["pressure_id"],
  "condition_remove": ["condition_id"]
}
```

Omit any key whose list would be empty. If nothing needs fixing, output `{}`.

### Concrete examples

Example 1 — Quest completed but not closed:
```
Active quests: settle_the_debt (all objectives done: true)
→ Output: {"quest_close": ["settle_the_debt"]}
```

Example 2 — Pressure resolved by escape:
```
Pressures: purposeful_pursuit (immediate), escaped through service hatch
→ Output: {"pressure_remove": ["purposeful_pursuit"]}
```

Example 3 — Condition resolved by self-treatment:
```
Conditions: strained_ribs, narration: "wrapped wounds to stave off pain"
→ Output: {"condition_remove": ["strained_ribs"]}
```

Example 4 — Nothing to fix:
```
All quests have incomplete objectives, no pressures, no resolved conditions
→ Output: {}
```
```

**Validation:** Read the full `compact_system.j2` after the edit to verify the Jinja2 syntax is correct and the section flows logically from PART 1 to PART 2 to PART 3.

#### Step 1.3 — Update compact_user.j2 to surface completed quests

**File:** `ccya/prompts/compact_user.j2`

**What:** Add a "Completed/Failed Quests" section between "Active Quests" and "Present NPCs" to surface quests that are no longer active. This gives the LLM visibility into quests that may need to be closed.

**Why:** The current prompt only shows active quests. If a quest was completed in a compacted turn but never closed, the LLM can't see it in the "Active Quests" section (because it's filtered to `status == "active"` in `_build_compact_messages`). The LLM needs to see ALL quests with their statuses to identify ones that should be closed.

**Code Snippet**
```jinja2
## MECHANICAL STATE
*(Read-only reference for sanitization. Use exact IDs shown.)*

### Active Quests
{% for q in active_quests -%}
- **[{{ q.get("id", "?") }}] {{ q.get("title", "?") }}**
{% for obj in (q.get("objectives") or []) -%}
  - [{{ "x" if obj.get("done") else " " }}] {{ obj.get("description", "?") }}
{% endfor -%}
{% endfor %}

{% if all_quests and active_quests and (all_quests | length) > (active_quests | length) -%}
### Completed / Failed Quests
{% for q in all_quests -%}
{%- if q.get("status") != "active" -%}
- **[{{ q.get("id", "?") }}] {{ q.get("title", "?") }} — {{ q.get("status", "?") }}**
{%- endif -%}
{% endfor %}
{% endif -%}
```

**Validation:** Read the full `compact_user.j2` after the edit to verify Jinja2 syntax. The new section only renders when there are non-active quests AND there are also active quests (to avoid redundancy when all quests are active).

### Tests to write or update
- No new tests required. The compactor's sanitization path is tested indirectly through the eval harness (Tier 2). The debug logging will be visible in eval run traces.

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: Update compactor description to mention debug logging for sanitization output.
- `docs/REPOMAP/prompts.md`: Update `compact_system.j2` description to mention strengthened sanitization directive with examples.

### Risks
1. **Prompt change makes LLM over-flag.** Mitigation: The engine validates all IDs against allowlists and silently skips unknown ones. False positives are harmless — the LLM can't delete valid state.
2. **Prompt change increases token count.** Mitigation: The added examples add ~200 tokens to the system prompt, which is acceptable for a compaction call that runs every 6 turns.

---

## Implementation — Phase 2: Narrator Input Validation

### Context files to load
1. `ccya/prompts/narrate_system.j2`
2. `ccya/prompts/narrate_user.j2`
3. `ccya/engine/narrate.py` (`_narrate_messages()`)

### Overview
The narrator ignores player input on Turn 7, outputting prose about Turn 6's aftermath instead. This is a context-tracking failure — the LLM loses track of which turn's input to process. This phase strengthens the narrator prompt with explicit turn anchoring and a directive to process the current turn's input before any other context.

### Detailed steps

#### Step 2.1 — Strengthen narrator system prompt for turn anchoring

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add a new section after the opening paragraph that explicitly anchors the narrator to the current turn's input. This section should be placed early in the system prompt so it takes precedence over later context.

**Why:** The current system prompt says "Take the player's stated action at face value and commit to it" but doesn't explicitly tell the LLM to process the CURRENT turn's input. When the context window is large (52K+ tokens), the LLM can get confused about which input is current.

**Code Snippet**
```python
# Insert after the opening paragraph (after line 3), before "## Style":

- **Process the current turn's input.** The user prompt below contains the player's action for THIS turn under `## Player input`. Narrate the consequences of THAT action. Do NOT narrate the aftermath of previous turns, do NOT re-narrate what already happened, and do NOT ignore the player's input to describe something else. The player input is the ONLY action you should narrate.
```

**Validation:** Read the full `narrate_system.j2` after the edit to verify the bullet point fits the existing style and doesn't disrupt the prompt flow.

#### Step 2.2 — Strengthen "Player intent is truth" section

**File:** `ccya/prompts/narrate_system.j2`

**What:** Enhance the existing "Player intent is truth" section with a stronger directive that explicitly forbids ignoring the player's input.

**Why:** The current section says "Take the player's stated action at face value" but doesn't explicitly say "do not ignore it." The eval report shows the narrator outputting Turn 6's aftermath instead of processing Turn 7's input — this is a direct violation of "player intent is truth."

**Code Snippet**
```python
# Replace the existing "## Player intent is truth" section (lines 26-28):

## Player intent is truth
Take the player's stated action at face value and commit to it. The rules engine handles dice and conditions; the narrator handles fiction. 
**You MUST narrate the player's current input — never ignore it, never substitute a different action, and never narrate previous turns instead.** If the action involves an inventory item or present NPC, always use that item or NPC.
```

**Validation:** Read the full `narrate_system.j2` after the edit to verify the replacement is clean and the section flows logically.

### Tests to write or update
- No new tests required. The narrator's behavior is tested through the eval harness (Tier 2). The fix will be verified by re-running the eval and checking that Turn 7 no longer shows a narrator input ignore.

### REPOMAP updates required
- `docs/REPOMAP/prompts.md`: Update `narrate_system.j2` description to mention turn anchoring directive.

### Risks
1. **Prompt change increases token count.** Mitigation: The added text is ~100 tokens, negligible compared to the 52K token context.
2. **Prompt change is too aggressive and causes other issues.** Mitigation: The directive reinforces existing behavior ("player intent is truth") rather than changing it. If issues arise, the directive can be toned down.

---

## Implementation — Phase 3: Currency Mapping Fix

### Context files to load
1. `ccya/prompts/extract_state_system.j2`
2. `ccya/prompts/extract_state_user.j2`

### Overview
The state extractor emits `iron_coins` instead of mapping generic currency terms to the existing `credits` inventory ID, causing delta rejections and runner errors on turns 7 and 13. The existing "Generic item mapping (MANDATORY)" section exists but the LLM ignores it. This phase strengthens the mapping directive with an explicit `credits` example and a stronger negative constraint.

### Detailed steps

#### Step 3.1 — Strengthen generic item mapping section

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Replace the existing "Generic item mapping (MANDATORY)" section with a stronger, more explicit version that includes the `credits` example and a stronger negative constraint.

**Why:** The current section lists mapping examples but doesn't explicitly mention `credits`. The LLM doesn't know that `credits` is the canonical currency ID in this game. By explicitly naming `credits` and adding a stronger negative constraint, we prevent the LLM from inventing new currency IDs.

**Code Snippet**
```python
# Replace the existing "## Generic item mapping (MANDATORY)" section (lines 76–92):

## Generic item mapping (MANDATORY)

If the narration references a generic denomination or container term, you MUST map it to the
closest matching ID in the ## inventory list. NEVER invent a new inventory ID for a generic term.

**Currency mapping is the most common error.** If the inventory contains a currency item (e.g., `credits`), ALL generic currency references in the narration MUST map to that ID. Examples:
  "coin", "silver", "iron coin", "gold piece", "copper", "a coin", "a few coins", "roll of cash", "stack of credits", "pouch of money", "money" → map to `credits` (or whatever currency ID exists in inventory)

**If the inventory has NO currency item**, do NOT emit an inventory_remove or inventory_add for currency references. Omission is safer than inventing a new ID.

If no inventory item clearly matches the generic term (non-currency items), do NOT emit an inventory_remove or
inventory_add for that reference. The narrator's language is imprecise — the state should not
change. Omission is always safer than inventing a new ID.

**If you create an inventory ID that does not match any existing item and is not a genuinely
new item described in the narration, you have failed this rule.**
```

**Validation:** Read the full `extract_state_system.j2` after the edit to verify the section flows logically and the examples are clear.

### Tests to write or update
- No new tests required. The currency mapping fix will be verified by re-running the eval and checking that turns 7 and 13 no longer show rejected deltas for `iron_coins`.

### REPOMAP updates required
- `docs/REPOMAP/prompts.md`: Update `extract_state_system.j2` description to mention strengthened currency mapping with explicit `credits` example.

### Risks
1. **Prompt change is too specific to `credits`.** Mitigation: The prompt says "or whatever currency ID exists in inventory" — it's an example, not a hardcode. Other packs with different currency IDs will still work.
2. **Prompt change increases token count.** Mitigation: The added text is ~80 tokens, negligible.

---

## Ambiguities requiring resolution before execution
1. **Should we also add an engine-level pre-narration validation step?** The plan deliberately chooses prompt-only for now. If the prompt fix doesn't resolve the Turn 7 issue after eval re-run, an engine-level validation step (checking if input references absent NPCs/locations) can be added in a follow-up. **Decision: prompt-only for now.**
2. **Should the compactor's "Completed/Failed Quests" section in `compact_user.j2` show objectives for non-active quests?** Currently it only shows the quest ID, title, and status. Adding objectives would increase token count significantly. **Decision: status only — the LLM can infer from the bulletin whether the quest is truly done.**

## TODO.md update

Add the following under a new section in `docs/plans/TODO.md`, after the "Eval Remediation (May 2026)" heading and before the existing items:

```markdown
- [ ] **Compactor sanitization failure** — compactor fires at T6/T12 but LLM returns `{}` for all sanitization actions; quests not closed, pressures not removed — see `[eval-remediation-may10/01-eval-remediation-may10.md](eval-remediation-may10/01-eval-remediation-may10.md) Phase 1`
- [ ] **Narrator ignores player input** — Turn 7 narrator outputs stale context instead of processing input — see `[eval-remediation-may10/01-eval-remediation-may10.md](eval-remediation-may10/01-eval-remediation-may10.md) Phase 2`
- [ ] **Currency mapping failure** — state extractor emits `iron_coins` instead of mapping to `credits`, causing rejected deltas — see `[eval-remediation-may10/01-eval-remediation-may10.md](eval-remediation-may10/01-eval-remediation-may10.md) Phase 3`
```
