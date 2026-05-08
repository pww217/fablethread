# Quest and State Extraction Fixes

## Status

`open`

## Part of

`eval-results-remediation`

## Dependencies

- Plan A (`eval-results-remediation-pipeline-field-routing.md`) must be complete. After Plan A: (1) `compendium_npc_update` lives in `SceneExtractResult` and `extract_scene_system.j2`, so the NPC dedup fix targets the scene extractor; (2) `actions` and `outcome_summary` live in `ProgressExtractResult`, so the contact-objective and inventory domain fixes target the progress extractor.

## Objective

Three extraction bugs found in the eval runs:

1. **Contact/meet quest objectives** were not auto-completing when the target NPC was present in the scene and dialogue was established — the LLM was waiting for a roll outcome that would never come.
2. **Inventory domain** was not activating on explicit physical transfer narration (hand-off, pick up, receive, take) when no other domain signal was present, causing the state extractor to run with inventory disabled.
3. **Duplicate NPC compendium entries** were being created when the same character was referenced by a different descriptor across turns — the extractor saw no compendium match because the existing entry used a different name form.

## Non-goals

- Does NOT change the domain activation trigger architecture — only adds a secondary transfer-verb scan as a supplementary signal.
- Does NOT change the `compendium_npc_update` data model or application logic.
- Does NOT change how quest objectives are stored or rendered.
- Does NOT change inventory model or state application logic.
- Does NOT touch pressure, gm_beat, or scene tags.

## Affected files


| File                                      | Change type | Summary of change                                                                                                          |
| ----------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------- |
| `ccya/prompts/extract_progress_system.j2` | modify      | Add explicit rule for contact/meet objective auto-completion on NPC presence + dialogue                                    |
| `ccya/engine/extraction.py`               | modify      | Add transfer-verb scan in `_determine_active_domains` as supplementary inventory domain trigger                            |
| `ccya/prompts/extract_scene_system.j2`    | modify      | Add dedup pre-check instruction: inject alias lookup before emitting `compendium_npc_update add`                           |
| `ccya/engine/extraction.py`               | modify      | Add deterministic pre-pass in `_apply_compendium_updates` (or equivalent): check all aliases before allowing a new NPC add |
| `docs/REPOMAP/extraction.md`              | update      | Document transfer-verb scan and NPC dedup pre-pass                                                                         |
| `docs/plans/TODO.md`                      | update      | Add this plan                                                                                                              |


## Firm decisions

1. **Contact/meet objective completion is determined by NPC presence + dialogue established**, not by roll outcome. The progress extractor already sees `active_quests` with objectives — add a rule that if the objective text contains "find", "meet", "contact", "locate", "speak with", or "reach" and the narration shows that NPC present and responding to the player, the objective is done regardless of the roll band.
2. **Transfer-verb scan is a deterministic pre-check in Python**, not a prompt instruction. It reads the narration string for explicit transfer verbs (`hand`, `hands`, `handed`, `gives`, `gave`, `receives`, `received`, `picks up`, `picked up`, `takes`, `took`, `drops`, `dropped`) and activates the `inventory` domain if found, even if no other domain signal fired. This runs before the LLM call.
3. **NPC dedup pre-pass** in the engine: before applying `compendium_npc_update` additions from the scene extractor, look up every existing NPC by ID, name, and all aliases. If the new entry's name string-matches any existing NPC's name or alias list (case-insensitive, stripped), redirect the update to the existing NPC's ID rather than creating a new one.
4. **Prompt-level dedup instruction** in `extract_scene_system.j2`: the compendium roster already shown to the scene extractor (added in Plan A) already gives it the full list. Add an explicit instruction to check name and alias against that list before emitting a new `compendium_npc_update` with a new ID. The engine pre-pass is the hard safety net; the prompt instruction reduces LLM dedup errors before they reach the engine.
5. **No new config flags** — all three fixes are always active.

## Implementation — Phase 1: Contact objective completion rule

### Context files to load

- `ccya/prompts/extract_progress_system.j2` (post Plan A)
- `ccya/models.py` — confirm `QuestObjective` model fields

### Overview

Add an explicit sub-rule under `quest_updates` in the progress system prompt for the contact/meet objective pattern.

### Detailed steps

#### Step 1.1 — Add contact-objective rule to `extract_progress_system.j2`

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** After the existing `quest_updates` rules-outcome guidance block (the `crit_fail / fail / setback / partial: do NOT mark...` section), add the following explicit rule.

**Why:** Contact-type objectives have no roll to succeed on — they resolve on NPC presence and dialogue. The LLM was treating them the same as combat or skill objectives and waiting for a success band.

**Code Snippet** (insert after the rules-outcome guidance block):

Contact and meet objective rule

If a quest objective's description contains any of: "find", "meet", "contact", "locate", "speak with", "reach", "talk to", "seek out" — the objective completes when ALL of:

```
The named NPC or target is present in the current narration (they appear, respond, or speak).

The player has established or attempted communication (spoken to them, signaled them, made contact).

The narration does not explicitly show the contact failed or was refused.
```

This applies regardless of rules_outcome.band. Contact objectives are resolved by narrative presence, not roll outcome.

**Validation:** Construct a test where `active_quests` has an objective `"Find and speak with Torben Klask"` and the narration shows Torben responding to the player. Run through `_extract_progress_messages` with a FakeLLM — assert `quest_updates[0].objectives[0].done == True`.

---

## Implementation — Phase 2: Transfer-verb domain scan

### Context files to load

- `ccya/engine/extraction.py` (post Plan A)

### Overview

Add a transfer-verb scan function. Call it in `_determine_active_domains` (or equivalent) as a supplementary check that activates `inventory` domain even when the primary domain detection didn't fire.

### Detailed steps

#### Step 2.1 — Add `_narration_has_transfer` helper

**File:** `ccya/engine/extraction.py`

**What:** New private function that takes a narration string and returns `True` if explicit inventory-transfer language is present.

**Why:** Domain activation was missing physical hand-off narration that didn't use the exact vocabulary the domain detector expected.

**Code Snippet**

```python
_TRANSFER_VERBS: frozenset[str] = frozenset({
    "hand", "hands", "handed", "handing",
    "gives", "give", "gave", "given",
    "receives", "receive", "received", "receiving",
    "picks up", "picked up", "picking up",
    "takes", "take", "took", "taken",
    "drops", "drop", "dropped", "dropping",
    "passes", "pass", "passed", "passing",
    "tosses", "toss", "tossed",
    "pockets", "pocket", "pocketed",
    "retrieves", "retrieve", "retrieved",
    "grabs", "grab", "grabbed",
    "presses into", "slips into", "slides across",
})

def _narration_has_transfer(narration: str) -> bool:
    """Return True if the narration contains explicit physical transfer language."""
    lower = narration.lower()
    return any(verb in lower for verb in _TRANSFER_VERBS)
```

**Validation:**

```python
assert _narration_has_transfer("She hands you a sealed envelope.")
assert _narration_has_transfer("You pick up the coin from the table.")
assert not _narration_has_transfer("The guard watches you from across the room.")
```

---

#### Step 2.2 — Call `_narration_has_transfer` in domain activation

**File:** `ccya/engine/extraction.py`

**What:** In `_determine_active_domains` (read the exact function name first), after the primary domain detection block, add:

```python
if "inventory" not in active_domains and _narration_has_transfer(narration):
    active_domains = list(active_domains) + ["inventory"]
    _log.debug(
        "extraction.domains: transfer-verb scan activated inventory domain",
        extra={"turn": turn_no, "trace_id": trace_id},
    )
```

**Why:** The transfer scan is a supplementary signal only — it does not override existing domain logic, it only adds `inventory` if it was otherwise absent.

**Validation:** Unit test: `_determine_active_domains` called with a narration containing "handed you" and no other inventory signal — assert `"inventory"` in returned domains.

---

## Implementation — Phase 3: NPC compendium dedup

### Context files to load

- `ccya/engine/extraction.py` (post Plan A)
- `ccya/prompts/extract_scene_system.j2` (post Plan A, post Plan B)

### Overview

Two-layer dedup: a prompt instruction and an engine pre-pass. The prompt instruction tells the LLM to check name and aliases before emitting a new compendium add. The engine pre-pass catches any that slip through.

### Detailed steps

#### Step 3.1 — Strengthen compendium dedup instruction in `extract_scene_system.j2`

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Expand the existing "NPC match instruction" section (already present from Plan A's scene system rewrite) to explicitly require alias checking.

**Why:** The LLM was creating `compendium_npc_update` entries for "the scarred soldier" even though "Kael Marsh" was already in the compendium — because it matched by appearance descriptor rather than checking aliases.

**Code Snippet** (replace existing "NPC match instruction" section):

# Quest and State Extraction Fixes

## Status

`open`

## Part of

`eval-results-remediation`

## Dependencies

- Plan A (`eval-results-remediation-pipeline-field-routing.md`) must be complete. After Plan A: (1) `compendium_npc_update` lives in `SceneExtractResult` and `extract_scene_system.j2`, so the NPC dedup fix targets the scene extractor; (2) `actions` and `outcome_summary` live in `ProgressExtractResult`, so the contact-objective and inventory domain fixes target the progress extractor.

## Objective

Three extraction bugs found in the eval runs:

1. **Contact/meet quest objectives** were not auto-completing when the target NPC was present in the scene and dialogue was established — the LLM was waiting for a roll outcome that would never come.
2. **Inventory domain** was not activating on explicit physical transfer narration (hand-off, pick up, receive, take) when no other domain signal was present, causing the state extractor to run with inventory disabled.
3. **Duplicate NPC compendium entries** were being created when the same character was referenced by a different descriptor across turns — the extractor saw no compendium match because the existing entry used a different name form.

## Non-goals

- Does NOT change the domain activation trigger architecture — only adds a secondary transfer-verb scan as a supplementary signal.
- Does NOT change the `compendium_npc_update` data model or application logic.
- Does NOT change how quest objectives are stored or rendered.
- Does NOT change inventory model or state application logic.
- Does NOT touch pressure, gm_beat, or scene tags.

## Affected files


| File                                      | Change type | Summary of change                                                                                                          |
| ----------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------- |
| `ccya/prompts/extract_progress_system.j2` | modify      | Add explicit rule for contact/meet objective auto-completion on NPC presence + dialogue                                    |
| `ccya/engine/extraction.py`               | modify      | Add transfer-verb scan in `_determine_active_domains` as supplementary inventory domain trigger                            |
| `ccya/prompts/extract_scene_system.j2`    | modify      | Add dedup pre-check instruction: inject alias lookup before emitting `compendium_npc_update add`                           |
| `ccya/engine/extraction.py`               | modify      | Add deterministic pre-pass in `_apply_compendium_updates` (or equivalent): check all aliases before allowing a new NPC add |
| `docs/REPOMAP/extraction.md`              | update      | Document transfer-verb scan and NPC dedup pre-pass                                                                         |
| `docs/plans/TODO.md`                      | update      | Add this plan                                                                                                              |


## Firm decisions

1. **Contact/meet objective completion is determined by NPC presence + dialogue established**, not by roll outcome. The progress extractor already sees `active_quests` with objectives — add a rule that if the objective text contains "find", "meet", "contact", "locate", "speak with", or "reach" and the narration shows that NPC present and responding to the player, the objective is done regardless of the roll band.
2. **Transfer-verb scan is a deterministic pre-check in Python**, not a prompt instruction. It reads the narration string for explicit transfer verbs (`hand`, `hands`, `handed`, `gives`, `gave`, `receives`, `received`, `picks up`, `picked up`, `takes`, `took`, `drops`, `dropped`) and activates the `inventory` domain if found, even if no other domain signal fired. This runs before the LLM call.
3. **NPC dedup pre-pass** in the engine: before applying `compendium_npc_update` additions from the scene extractor, look up every existing NPC by ID, name, and all aliases. If the new entry's name string-matches any existing NPC's name or alias list (case-insensitive, stripped), redirect the update to the existing NPC's ID rather than creating a new one.
4. **Prompt-level dedup instruction** in `extract_scene_system.j2`: the compendium roster already shown to the scene extractor (added in Plan A) already gives it the full list. Add an explicit instruction to check name and alias against that list before emitting a new `compendium_npc_update` with a new ID. The engine pre-pass is the hard safety net; the prompt instruction reduces LLM dedup errors before they reach the engine.
5. **No new config flags** — all three fixes are always active.

## Implementation — Phase 1: Contact objective completion rule

### Context files to load

- `ccya/prompts/extract_progress_system.j2` (post Plan A)
- `ccya/models.py` — confirm `QuestObjective` model fields

### Overview

Add an explicit sub-rule under `quest_updates` in the progress system prompt for the contact/meet objective pattern.

### Detailed steps

#### Step 1.1 — Add contact-objective rule to `extract_progress_system.j2`

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** After the existing `quest_updates` rules-outcome guidance block (the `crit_fail / fail / setback / partial: do NOT mark...` section), add the following explicit rule.

**Why:** Contact-type objectives have no roll to succeed on — they resolve on NPC presence and dialogue. The LLM was treating them the same as combat or skill objectives and waiting for a success band.

**Code Snippet** (insert after the rules-outcome guidance block):

Contact and meet objective rule

If a quest objective's description contains any of: "find", "meet", "contact", "locate", "speak with", "reach", "talk to", "seek out" — the objective completes when ALL of:

```
The named NPC or target is present in the current narration (they appear, respond, or speak).

The player has established or attempted communication (spoken to them, signaled them, made contact).

The narration does not explicitly show the contact failed or was refused.
```

This applies regardless of rules_outcome.band. Contact objectives are resolved by narrative presence, not roll outcome.

text

**Validation:** Construct a test where `active_quests` has an objective `"Find and speak with Torben Klask"` and the narration shows Torben responding to the player. Run through `_extract_progress_messages` with a FakeLLM — assert `quest_updates[0].objectives[0].done == True`.

---

## Implementation — Phase 2: Transfer-verb domain scan

### Context files to load

- `ccya/engine/extraction.py` (post Plan A)

### Overview

Add a transfer-verb scan function. Call it in `_determine_active_domains` (or equivalent) as a supplementary check that activates `inventory` domain even when the primary domain detection didn't fire.

### Detailed steps

#### Step 2.1 — Add `_narration_has_transfer` helper

**File:** `ccya/engine/extraction.py`

**What:** New private function that takes a narration string and returns `True` if explicit inventory-transfer language is present.

**Why:** Domain activation was missing physical hand-off narration that didn't use the exact vocabulary the domain detector expected.

**Code Snippet**

```python
_TRANSFER_VERBS: frozenset[str] = frozenset({
    "hand", "hands", "handed", "handing",
    "gives", "give", "gave", "given",
    "receives", "receive", "received", "receiving",
    "picks up", "picked up", "picking up",
    "takes", "take", "took", "taken",
    "drops", "drop", "dropped", "dropping",
    "passes", "pass", "passed", "passing",
    "tosses", "toss", "tossed",
    "pockets", "pocket", "pocketed",
    "retrieves", "retrieve", "retrieved",
    "grabs", "grab", "grabbed",
    "presses into", "slips into", "slides across",
})

def _narration_has_transfer(narration: str) -> bool:
    """Return True if the narration contains explicit physical transfer language."""
    lower = narration.lower()
    return any(verb in lower for verb in _TRANSFER_VERBS)
```

**Validation:**

```python
assert _narration_has_transfer("She hands you a sealed envelope.")
assert _narration_has_transfer("You pick up the coin from the table.")
assert not _narration_has_transfer("The guard watches you from across the room.")
```

---

#### Step 2.2 — Call `_narration_has_transfer` in domain activation

**File:** `ccya/engine/extraction.py`

**What:** In `_determine_active_domains` (read the exact function name first), after the primary domain detection block, add:

```python
if "inventory" not in active_domains and _narration_has_transfer(narration):
    active_domains = list(active_domains) + ["inventory"]
    _log.debug(
        "extraction.domains: transfer-verb scan activated inventory domain",
        extra={"turn": turn_no, "trace_id": trace_id},
    )
```

**Why:** The transfer scan is a supplementary signal only — it does not override existing domain logic, it only adds `inventory` if it was otherwise absent.

**Validation:** Unit test: `_determine_active_domains` called with a narration containing "handed you" and no other inventory signal — assert `"inventory"` in returned domains.

---

## Implementation — Phase 3: NPC compendium dedup

### Context files to load

- `ccya/engine/extraction.py` (post Plan A)
- `ccya/prompts/extract_scene_system.j2` (post Plan A, post Plan B)

### Overview

Two-layer dedup: a prompt instruction and an engine pre-pass. The prompt instruction tells the LLM to check name and aliases before emitting a new compendium add. The engine pre-pass catches any that slip through.

### Detailed steps

#### Step 3.1 — Strengthen compendium dedup instruction in `extract_scene_system.j2`

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Expand the existing "NPC match instruction" section (already present from Plan A's scene system rewrite) to explicitly require alias checking.

**Why:** The LLM was creating `compendium_npc_update` entries for "the scarred soldier" even though "Kael Marsh" was already in the compendium — because it matched by appearance descriptor rather than checking aliases.

**Code Snippet** (replace existing "NPC match instruction" section):

NPC match instruction

Before emitting compendium_npc_update with a new id, run this checklist:

```
Is the character's name (or any name they've been called) present in the known_characters list above? If yes — use the existing ID. Do NOT create a new entry.

Does the character's description match an existing NPC's bio or role (same faction, same job, same physical descriptor)? If yes — use the existing ID with an alias update.

Are they referred to by a descriptor used in a previous turn (e.g., "the scarred soldier", "the dockmaster's man")? If a compendium NPC has that descriptor in their bio or aliases — use the existing ID.
```

Only emit a new id if you have confirmed the character is not any existing compendium NPC by name, descriptor, or role.

When using an existing ID after a descriptor match: add the old descriptor as an alias in the update. This prevents future mismatches.

**Validation:** Template renders without error.

---

#### Step 3.2 — Add engine-level dedup pre-pass in `_apply_compendium_updates`

**File:** `ccya/engine/extraction.py`

**What:** Read the existing function that applies `compendium_npc_update` from `StateDelta` to the `state["known_characters"]` list. Before applying an add, run a match check: for each proposed new entry, compare its `name` field (lowercased, stripped) against every existing NPC's `name`, `aliases` list, and ID. If a match is found, redirect the update to the existing NPC's ID and merge fields rather than creating a duplicate.

**Why:** Hard safety net — catches dedup failures that survive the prompt instruction.

**Code Snippet**

```python
def _dedup_compendium_add(
    proposed: "CompendiumNpcUpdate",
    existing_npcs: list[dict[str, Any]],
) -> "CompendiumNpcUpdate":
    """
    If proposed.name matches any existing NPC's name or aliases (case-insensitive),
    redirect proposed.id to the existing NPC's id and return the modified update.
    Otherwise return proposed unchanged.
    """
    if not proposed.name:
        return proposed
    candidate = proposed.name.strip().lower()
    for npc in existing_npcs:
        npc_names = [
            (npc.get("name") or "").lower(),
            (npc.get("id") or "").lower().replace("_", " "),
        ] + [(a or "").lower() for a in (npc.get("aliases") or [])]
        if candidate in npc_names:
            _log.info(
                "extraction.dedup: redirecting compendium add '%s' → existing id '%s'",
                proposed.id,
                npc["id"],
                extra={},
            )
            return proposed.model_copy(update={"id": npc["id"]})
    return proposed

# In the apply block, before inserting a new NPC:
for update in delta.compendium_npc_update:
    update = _dedup_compendium_add(update, state.get("known_characters") or [])
    # ... existing upsert logic ...
```

Note: read the actual apply function in `extraction.py` or `state/delta.py` to confirm the insertion point and adapt the snippet to the real variable names.

**Validation:**

```python
from ccya.engine.extraction import _dedup_compendium_add
from ccya.models import CompendiumNpcUpdate

existing = [{"id": "kael_marsh", "name": "Kael Marsh", "aliases": ["the scarred soldier"]}]
proposed = CompendiumNpcUpdate(id="scarred_soldier_new", name="Kael Marsh")
result = _dedup_compendium_add(proposed, existing)
assert result.id == "kael_marsh"

# No match — should pass through unchanged
proposed2 = CompendiumNpcUpdate(id="new_person", name="Lira Venn")
result2 = _dedup_compendium_add(proposed2, existing)
assert result2.id == "new_person"
```

---

### Tests to write or update

**File:** `tests/test_extraction.py` (extend)

```python
def test_transfer_verb_activates_inventory_domain():
    from ccya.engine.extraction import _narration_has_transfer, _determine_active_domains
    assert _narration_has_transfer("She hands you a sealed envelope.")
    assert _narration_has_transfer("You pick up the coin from the floor.")
    assert not _narration_has_transfer("The guard nods at you from across the room.")

def test_domain_scan_adds_inventory_when_transfer_present():
    # Call _determine_active_domains with narration containing transfer verb
    # and no other inventory trigger — assert "inventory" in result.
    ...

def test_dedup_redirects_alias_match():
    from ccya.engine.extraction import _dedup_compendium_add
    from ccya.models import CompendiumNpcUpdate
    existing = [{"id": "torben_klask", "name": "Torben Klask", "aliases": ["the big man"]}]
    proposed = CompendiumNpcUpdate(id="the_big_man", name="Torben Klask")
    result = _dedup_compendium_add(proposed, existing)
    assert result.id == "torben_klask"

def test_dedup_allows_genuinely_new_npc():
    from ccya.engine.extraction import _dedup_compendium_add
    from ccya.models import CompendiumNpcUpdate
    existing = [{"id": "torben_klask", "name": "Torben Klask", "aliases": []}]
    proposed = CompendiumNpcUpdate(id="sera_lant", name="Sera Lant")
    result = _dedup_compendium_add(proposed, existing)
    assert result.id == "sera_lant"
```

**File:** `tests/test_progress_prompt.py` (create — FakeLLM pattern)

```python
def test_contact_objective_completes_on_npc_presence():
    # active_quests has objective "Find and speak with Torben Klask"
    # narration: "Torben looks up from his ledger and nods. 'What do you want?'"
    # FakeLLM returns quest_updates with objectives.done = True
    # Assert that the prompt rule permits this even with no_dice_roll outcome
    ...
```

### REPOMAP updates required

`docs/REPOMAP/extraction.md` — document `_narration_has_transfer`, `_dedup_compendium_add`, and the contact-objective rule addition to the progress prompt.

### Risks

1. `**_determine_active_domains` function location** — must read the actual file to find where domain activation happens before implementing the transfer-verb scan insertion point. If domain activation is spread across multiple places, the scan must be added to the canonical aggregation point only.
2. **Transfer-verb false positives** — "takes a seat", "drops the subject", "passes a moment" are idiomatic uses that don't signal inventory transfer. The verb list should be reviewed against actual narration samples. Worst case: inventory domain runs an extra time — this is low-risk since the state extractor is conservative and only extracts explicit items.
3. `**_apply_compendium_updates` location** — this function may be in `state/delta.py` rather than `extraction.py`. Read both before writing the pre-pass insertion.
4. **Alias list may not exist** on older NPC records — the pre-pass must handle `npc.get("aliases") or []` defensively, which the snippet above already does.

## Ambiguities requiring resolution before execution

None.

## TODO.md update

Under `## P1 — Active`:

Quest and state extraction fixes — docs/plans/eval-results-remediation/eval-results-remediation-quest-state-extraction.md