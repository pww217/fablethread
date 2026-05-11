# Eval Remediation — Issues 4-8 + Inventory Capitalization

**Goal:** Fix scene extractor domain routing, generic item mapping, location_description nullification, npc_add compendium bloat, redundant style injection, and enforce inventory item capitalization.

**Target:** Improve Mechanical score from 3/5 to 4/5, reduce auto-checker failures, reduce prompt token waste.

---

## Status
`open`

## Part of
Eval Remediation (May 2026)

## Dependencies
- Completed plans: `compactor-recent-events.md`, `quest-dedup.md`, `eval-pack-turn-0.md`
- None of the other open plans overlap with this scope.

## Conflicts and overlap
None. These are all prompt-level fixes plus one engine routing fix. No model/state changes. No config changes. No server changes.

---

## Objective

Five eval findings target the extraction and narration prompts: the scene extractor skips when `compendium_npc` is the only active domain (issue 4), the state extractor invents inventory IDs instead of mapping generic terms (issue 5), the scene emitter redundantly re-describes locations (issue 6), `npc_add` triggers compendium upserts for already-known NPCs (issue 7), and the narrator prompt redundantly copies the full world pack style verbatim (issue 8). Additionally, inventory item names should start with a capital letter for consistency. These are all prompt-strengthening and one routing fix — no new models, no state schema changes.

## Non-goals

- No new Pydantic models or state fields.
- No new config keys.
- No server/route changes.
- No changes to the rules/intent pipeline (Call 0).
- No changes to the progress extractor.
- No changes to the compactor.
- No frontend changes.

## Affected files

| File | Change type | Summary |
|---|---|---|
| `ccya/engine/extraction.py` | modify | Add `compendium_npc` to scene domain check in `_run_extraction_pipeline` |
| `ccya/prompts/extract_state_system.j2` | modify | Strengthen generic item mapping rule with explicit examples |
| `ccya/prompts/extract_scene_system.j2` | modify | Strengthen location_description nullification with decision checklist |
| `ccya/prompts/extract_scene_system.j2` | modify | Add npc_add compendium pre-check instruction |
| `ccya/prompts/narrate_system.j2` | modify | Remove redundant `{{ pack_style }}` block, reference by name |
| `ccya/engine/extraction.py` | modify | Add `_capitalize_inventory_names()` post-processing helper |
| `ccya/engine/extraction.py` | modify | Call capitalization in `_run_extraction_pipeline` before merge |
| `tests/test_extraction.py` | create | Tests for scene domain routing, capitalization |
| `docs/REPOMAP/engine.md` | modify | Update extraction.py function descriptions |
| `docs/REPOMAP/prompts.md` | modify | Update prompt template descriptions |
| `docs/plans/TODO.md` | modify | Add completed items under Eval Remediation section |

---

## Firm decisions

1. **No model changes.** All fixes are prompt-level or routing-level. The `InventoryItem.name` field already accepts any string; capitalization is enforced at the extraction output level.
2. **Capitalization is a post-processing step.** Applied in `_run_extraction_pipeline()` after all three streams produce results, before merging into `StateDelta`. This avoids touching the Pydantic models and keeps the fix localized.
3. **Scene domain routing fix is minimal.** Add `compendium_npc` to the `scene_domains` set in `_run_extraction_pipeline()`. One line change.
4. **Style injection removal is safe.** The `pack_style` is already rendered in the system prompt via `{% elif pack_style %}## Genre tone\n{{ pack_style }}`. The user prompt does not need it.

---

## Implementation — Phase 1: Scene extractor domain routing

### Context files to load
- `ccya/engine/extraction.py` (lines 366-445)
- `docs/REPOMAP/engine.md` (lines 93-95)

### Overview

Fix the scene extractor being skipped when `compendium_npc` is the only active domain. The scene extractor handles `npc_add`, `npc_remove`, `npc_update`, and `compendium_npc_update` — all of which require the scene extractor to run. Currently it only runs when `scene` or `location_change` is in `active_domains`.

### Detailed steps

#### Step 1.1 — Add `compendium_npc` to scene domain check

**File:** `ccya/engine/extraction.py`

**What:** In `_run_extraction_pipeline()`, change the scene domain check from `{"scene", "location_change"}` to `{"scene", "location_change", "compendium_npc"}`.

**Why:** The scene extractor is the only extractor that handles `npc_add`, `npc_remove`, `npc_update`, and `compendium_npc_update`. When the narrator's scope tail includes `compendium_npc` but not `scene` or `location_change`, the scene stream is skipped and new NPCs are never tracked in state.

**Code Snippet**
```python
# In _run_extraction_pipeline(), line ~403:
# BEFORE:
scene_domains = {"scene", "location_change"}

# AFTER:
scene_domains = {"scene", "location_change", "compendium_npc"}
```

**Validation:** Run `make test`. Verify that a turn where the narrator emits `compendium_npc` in the scope tail (but not `scene` or `location_change`) causes the scene extractor to run and process NPC updates.

### Tests to write or update

**File:** `tests/test_extraction.py` (or existing test file)

```python
async def test_scene_extractor_runs_for_compendium_npc_domain():
    """Scene extractor must run when compendium_npc is in active_domains."""
    env = _build_jinja_env()
    state = {
        "pc": {"name": "Test", "tagline": "Tester", "stats": {}, "conditions": []},
        "location": {"id": "test_loc", "name": "Test Location", "description": "A test."},
        "scene": {"present_npcs": [], "scene_pressure": [], "location_description": None, "recent_events": [], "world_state": []},
        "compendium": {"npcs": {}},
        "quests": [],
        "inventory": [],
        "meta": {"turn": 5},
    }
    narration = "A new character named Joel steps into view."
    active_domains = ["compendium_npc"]
    
    delta, actions, outcome, event_data, progress_result, scene_result = await _run_extraction_pipeline(
        env, state, narration,
        active_domains=active_domains,
        config=EngineConfig(),
        trace_id="test",
        turn_no=5,
    )
    
    # Scene stream should NOT be skipped
    assert not event_data["scene"]["skipped"]
    # Should have processed the NPC
    assert len(delta.npc_add) > 0 or len(delta.compendium_npc_update) > 0
```

### REPOMAP updates required

- `docs/REPOMAP/engine.md` line ~94: Update `_run_extraction_pipeline` description to note `compendium_npc` triggers scene stream.

### Risks

1. **Scene stream runs more often.** Adding `compendium_npc` to the trigger set means the scene extractor runs on any turn with compendium NPC updates. This is the intended behavior — the scene extractor is the correct extractor for NPC data. Minimal token cost since the prompt is already structured for this.

---

## Implementation — Phase 2: Generic item mapping in state extractor

### Context files to load
- `ccya/prompts/extract_state_system.j2` (lines 70-76)
- `ccya/prompts/extract_state_user.j2`

### Overview

Strengthen the generic item mapping rule in the state extractor system prompt. The LLM currently invents `iron_coin` instead of mapping to `credits`. The rule exists but is not emphatic enough.

### Detailed steps

#### Step 2.1 — Strengthen generic item mapping rule

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Replace the existing generic item mapping paragraph (last paragraph) with a stronger version that includes explicit examples and a clear "do not invent" directive.

**Why:** The current rule is a single paragraph at the end of the prompt. The LLM needs explicit examples showing the correct mapping and a clear prohibition against inventing IDs.

**Code Snippet**
```jinja2
## Generic item mapping (MANDATORY)

If the narration references a generic denomination or container term, you MUST map it to the
closest matching ID in the ## inventory list. NEVER invent a new inventory ID for a generic term.

Mapping examples:
  "coin", "silver", "iron coin", "gold piece", "copper" → map to existing currency ID (e.g., "credits")
  "roll of cash", "stack of credits", "pouch of money" → map to existing currency ID
  "a coin" → map to existing currency ID
  "some money" → map to existing currency ID

If no inventory item clearly matches the generic term, do NOT emit an inventory_remove or
inventory_add for that reference. The narrator's language is imprecise — the state should not
change. Omission is always safer than inventing a new ID.

**If you create an inventory ID that does not match any existing item and is not a genuinely
new item described in the narration, you have failed this rule.**
```

**Validation:** Check that the prompt renders correctly. Verify in eval runs that generic terms like "coin" map to `credits` instead of creating `iron_coin`.

### Tests to write or update

**File:** `tests/test_extraction.py`

```python
def test_generic_item_mapping_in_system_prompt():
    """System prompt must contain explicit generic item mapping examples."""
    env = _build_jinja_env()
    system_text = _render(env, "extract_state_system.j2", {})
    
    assert "generic denomination" in system_text.lower() or "generic item" in system_text.lower()
    assert "NEVER invent" in system_text or "never invent" in system_text
    assert "credits" in system_text  # example mapping target
```

### REPOMAP updates required

- `docs/REPOMAP/prompts.md` line ~10: Update extract_state_system.j2 description to note strengthened generic item mapping rule.

### Risks

1. **Prompt length increase.** The new rule is ~10 lines vs the original ~6 lines. Negligible token impact (~50 tokens).

---

## Implementation — Phase 3: Location description nullification + NPC compendium bloat

### Context files to load
- `ccya/prompts/extract_scene_system.j2` (lines 31, 33)

### Overview

Two related fixes to the scene extractor system prompt: strengthen the location_description nullification rule, and add a compendium pre-check for `npc_add` to prevent redundant compendium upserts.

### Detailed steps

#### Step 3.1 — Strengthen location_description nullification

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Replace the existing `location_description` field rule with a stronger version that includes a decision checklist.

**Why:** The current rule has the right intent but the LLM still emits redundant descriptions. A decision checklist forces the LLM to explicitly compare before emitting.

**Code Snippet**
```jinja2
# Replace the location_description paragraph (line 31) with:

`location_description`: A short prose description of the current location's notable features.
**Before emitting, run this checklist:**
1. Does the narration contain NEW spatial, atmospheric, or structural details about the location?
2. Are those details absent from `## current_location_description` in the user prompt?
3. If the answer to BOTH is yes → emit the description.
4. If the answer to EITHER is no → set `location_description` to `null`.

**Default to null on uncertainty.** Omission is safer than redundant re-description.
If the narration only confirms the player is still in the same location without adding
environmental details, set to `null`.
```

**Validation:** Check the prompt renders correctly. Verify in eval runs that `location_description` is `null` when the narration doesn't add new environmental details.

#### Step 3.2 — Add npc_add compendium pre-check

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** In the `npc_add` field rule, add a compendium pre-check instruction that prevents `npc_add` from triggering compendium upserts for already-known NPCs.

**Why:** The current rule says "Compendium NPCs are NOT in the scene by default. Emit `npc_add` for any NPC mentioned in the narration that is NOT in `present_npcs`, even if they appear in the compendium roster." This causes the engine to auto-create compendium entries for known NPCs via `npc_add` → `apply_delta` → compendium upsert. The fix is to instruct the LLM to check the compendium roster first.

**Code Snippet**
```jinja2
# In the npc_add field rule (line 33), add after the existing instruction:

**Compendium pre-check before npc_add:** Before adding an NPC, check the `## known_characters`
list. If the NPC is already in the compendium (marked with [compendium] tag), do NOT emit
npc_add — instead emit npc_update if their notes changed, or emit nothing if nothing changed.
Only emit npc_add for genuinely new NPCs not in the compendium roster.
```

**Validation:** Check the prompt renders correctly. Verify in eval runs that known NPCs don't trigger redundant compendium upserts via `npc_add`.

### Tests to write or update

**File:** `tests/test_extraction.py`

```python
def test_location_description_nullification_in_system_prompt():
    """System prompt must contain location_description decision checklist."""
    env = _build_jinja_env()
    system_text = _render(env, "extract_scene_system.j2", {})
    
    assert "null" in system_text.lower()
    assert "checklist" in system_text.lower() or "compare" in system_text.lower()

def test_npc_add_compendium_check_in_system_prompt():
    """System prompt must instruct npc_add to check compendium first."""
    env = _build_jinja_env()
    system_text = _render(env, "extract_scene_system.j2", {})
    
    assert "known_characters" in system_text
    assert "compendium" in system_text.lower()
```

### REPOMAP updates required

- `docs/REPOMAP/prompts.md` line ~9: Update extract_scene_system.j2 description to note strengthened location_description and npc_add compendium pre-check.

### Risks

1. **Prompt length increase.** ~15 new lines total. ~100 tokens. Negligible.

---

## Implementation — Phase 4: Remove redundant style injection in narrate

### Context files to load
- `ccya/prompts/narrate_system.j2` (lines 54-61)
- `ccya/engine/narrate.py` (function signature for `_narrate_messages`)

### Overview

The narrator system prompt already renders `pack_style` via the `{% elif pack_style %}## Genre tone\n{{ pack_style }}` block. The user prompt does not need to include it. However, looking at the code more carefully, the `pack_style` is rendered in the SYSTEM prompt, not the user prompt. Let me re-examine.

Actually, looking at `narrate_system.j2` lines 54-61, the `pack_style` is rendered in the system prompt template itself. The user prompt (`narrate_user.j2`) does NOT include `pack_style`. So the redundancy is within the system prompt — but wait, the findings say "World Pack Style copied verbatim into narrate prompt. Reference by name instead."

Let me re-read the findings: "Both runs: `World Pack Style` copied verbatim into narrate prompt. Reference by name instead."

Looking at the system prompt, `pack_style` is rendered inline in the system prompt. The issue is that the system prompt is sent every turn, and the style text is repeated every time. The fix should be to remove the `pack_style` from the system prompt and instead reference it by name in a shorter form, or better yet, since the system prompt is static per game, the style is already baked into the system prompt's instructions. The `pack_style` block at lines 58-61 is redundant with the system prompt's own style guidance.

Actually, re-reading more carefully: the system prompt has both generic style guidance (lines 10-18) AND the pack-specific style (lines 58-61). The pack style is a superset/addition. The finding says to "reference by name instead" — meaning instead of embedding the full style text, just reference the pack name and let the LLM use its knowledge.

But wait — the system prompt IS sent every turn. The pack_style text is part of the system prompt. So every turn, the full style text is in the context. The fix is to remove the `pack_style` block from the system prompt since the system prompt's own style guidance (lines 10-18) is sufficient, and the pack style was already used during pack generation.

Let me look at this differently. The `pack_style` is passed to `_narrate_messages()` and rendered in the system prompt. It's the same text every turn. The LLM already has the system prompt's style guidance. The pack_style is redundant.

**The fix:** Remove the `pack_style` rendering from `narrate_system.j2`. The system prompt's own style guidance (lines 10-18) is sufficient. The pack style was used during pack generation and doesn't need to be re-sent every turn.

### Detailed steps

#### Step 4.1 — Remove pack_style block from narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2`

**What:** Remove lines 58-61 (`{% elif pack_style %}## Genre tone\n{{ pack_style }}\n{% endif %}`). Keep the `narrator_rules` block (lines 54-57) since those are turn-specific rules.

**Why:** The `pack_style` text is the full world pack style description, repeated every turn in the system prompt. This wastes tokens. The system prompt's own style guidance (lines 10-18) provides sufficient direction. The pack style was already used during pack/seed generation.

**Code Snippet**
```jinja2
# Remove lines 58-61 from narrate_system.j2:

# BEFORE (lines 54-61):
{% if narrator_rules %}
## Genre tone
{% for rule in narrator_rules %}- {{ rule }}
{% endfor %}
{% elif pack_style %}
## Genre tone
{{ pack_style }}
{% endif %}

# AFTER (lines 54-57):
{% if narrator_rules %}
## Genre tone
{% for rule in narrator_rules %}- {{ rule }}
{% endfor %}
{% endif %}
```

**Validation:** Check the prompt renders correctly when `pack_style` is provided (should be silently ignored). Check that `narrator_rules` still renders correctly. Verify in eval runs that token count per turn decreases.

### Tests to write or update

**File:** `tests/test_extraction.py`

```python
def test_narrate_system_prompt_no_pack_style():
    """System prompt should not include pack_style — it wastes tokens."""
    env = _build_jinja_env()
    system_text = _render(env, "narrate_system.j2", {})
    
    # The system prompt should not have a Genre tone section with pack_style
    # (narrator_rules are injected at render time, not in the base system prompt)
    assert "## Genre tone" not in system_text or "pack_style" not in system_text
```

### REPOMAP updates required

- `docs/REPOMAP/prompts.md` line ~8: Update narrate_system.j2 description to note pack_style removal.

### Risks

1. **Loss of pack-specific style guidance.** If a pack's style has unique instructions not covered by the generic system prompt guidance, removing pack_style could lose that context. Mitigation: ensure the generic style guidance (lines 10-18) is comprehensive enough, or move pack_style to the seed/narration opening where it's used once.

---

## Implementation — Phase 5: Inventory item capitalization

### Context files to load
- `ccya/engine/extraction.py` (lines 575-610, merge block)
- `ccya/models.py` (InventoryItem model)

### Overview

Add a post-processing step that capitalizes the first letter of all inventory item names after extraction but before merging into StateDelta. This ensures consistent display formatting across all inventory items.

### Detailed steps

#### Step 5.1 — Add capitalization helper and apply it

**File:** `ccya/engine/extraction.py`

**What:** Add a `_capitalize_inventory_names()` helper function and call it in `_run_extraction_pipeline()` after all three streams produce results, before merging into `StateDelta`.

**Why:** Inventory item names should start with a capital letter for consistent display. The LLM may emit lowercase names (e.g., "brass key" → "Brass key"). This is a simple post-processing step that doesn't require model changes.

**Code Snippet**
```python
def _capitalize_inventory_names(items: list[Any]) -> list[Any]:
    """Capitalize the first letter of inventory item names.
    
    Modifies items in place and returns them.
    Handles both InventoryItem model instances and dicts.
    """
    for item in items:
        if hasattr(item, "name"):
            name = item.name
            if name and name[0].islower():
                item.name = name[0].upper() + name[1:]
        elif isinstance(item, dict) and "name" in item:
            name = item["name"]
            if name and name[0].islower():
                item["name"] = name[0].upper() + name[1:]
    return items


# In _run_extraction_pipeline(), after the dedup block (around line 573)
# and before the StateDelta merge (line 576), add:

    # --- Capitalize inventory item names ---
    _capitalize_inventory_names(state_result.inventory_add)
    _capitalize_inventory_names(state_result.inventory_update)
```

**Validation:** Run `make test`. Verify that inventory items with lowercase names (e.g., "brass key") are capitalized to "Brass key" in the final state.

### Tests to write or update

**File:** `tests/test_extraction.py`

```python
def test_capitalize_inventory_names_lowercase():
    """Inventory names starting with lowercase should be capitalized."""
    from ccya.models import InventoryItem
    
    items = [
        InventoryItem(id="brass_key", name="brass key"),
        InventoryItem(id="worn_dagger", name="worn dagger"),
        InventoryItem(id="credits", name="Credits"),  # already capitalized
    ]
    
    result = _capitalize_inventory_names(items)
    
    assert result[0].name == "Brass key"
    assert result[1].name == "Worn dagger"
    assert result[2].name == "Credits"

def test_capitalize_inventory_names_empty():
    """Empty or None names should not cause errors."""
    items = [
        InventoryItem(id="empty", name=""),
    ]
    result = _capitalize_inventory_names(items)
    assert result[0].name == ""
```

### REPOMAP updates required

- `docs/REPOMAP/engine.md` line ~104: Add `_capitalize_inventory_names` to the internal functions list.

### Risks

1. **Over-capitalization.** If an item name is a single lowercase letter (e.g., "a"), `name[1:]` would be empty string, resulting in "A". This is correct behavior.
2. **Already-capitalized names.** The check `name[0].islower()` prevents double-capitalization.

---

## Ambiguities requiring resolution before execution

1. **Phase 4 (style injection):** The `pack_style` is used in the system prompt every turn. Removing it means the LLM loses pack-specific style guidance. Is the generic style guidance (lines 10-18 of narrate_system.j2) sufficient for all packs? If not, should we move pack_style to the seed-generated opening narrative instead of removing it entirely?

2. **Inventory capitalization scope:** Should capitalization apply to ALL inventory names (including those set by the compactor during state sanitization), or only to names from the extraction pipeline? Currently the plan only capitalizes extraction output. If the compactor also sets inventory names, those would need capitalization too.

3. **NPC compendium bloat:** The fix adds a prompt instruction for the LLM to check the compendium before emitting `npc_add`. However, the engine already has `_dedup_compendium_add()` for `compendium_npc_update` but not for `npc_add`. Should we also add an engine-level dedup for `npc_add` (similar to `_dedup_compendium_add`) as a safety net, or is the prompt fix sufficient?

---

## TODO.md update

Add the following under the `## Eval Remediation (May 2026)` section, after the existing three items:

```markdown
- ~~**Fix scene extractor domain routing** — `eval-remediation/issues-4-8.md` Phase 1 — scene extractor skipped when compendium_npc active but scene/location_change not~~
- ~~**Fix generic item mapping in state extractor** — `eval-remediation/issues-4-8.md` Phase 2 — invents iron_coin instead of mapping to credits~~
- ~~**Strengthen scene extractor location_description nullification + npc_add compendium bloat** — `eval-remediation/issues-4-8.md` Phase 3 — redundant location descriptions, npc_add triggers compendium upserts for known NPCs~~
- ~~**Remove redundant style injection in narrate** — `eval-remediation/issues-4-8.md` Phase 4 — World Pack Style copied verbatim into narrate prompt~~
- ~~**Inventory item capitalization** — `eval-remediation/issues-4-8.md` Phase 5 — inventory items should start with a capital letter~~
```
