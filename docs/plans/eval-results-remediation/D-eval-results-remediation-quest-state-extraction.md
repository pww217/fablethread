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
| `ccya/engine/extraction.py`               | modify      | Add `_narration_has_transfer` helper and call it in `_run_extraction_pipeline` before the `run_state` guard to activate inventory domain |
| `ccya/prompts/extract_scene_system.j2`    | modify      | Add dedup pre-check instruction: inject alias lookup before emitting `compendium_npc_update add`                           |
| `ccya/engine/extraction.py`               | modify      | Add `_dedup_compendium_add` helper and call it in `_run_extraction_pipeline` between the progress call and `StateDelta(...)` merge |
| `docs/REPOMAP/extraction.md`              | update      | Document transfer-verb scan and NPC dedup pre-pass                                                                         |
| `docs/plans/TODO.md`                      | update      | Add this plan                                                                                                              |


## Firm decisions

1. **Contact/meet objective completion is determined by NPC presence + dialogue established**, not by roll outcome. The progress extractor already sees `active_quests` with objectives — add a rule that if the objective text contains "find", "meet", "contact", "locate", "speak with", or "reach" and the narration shows that NPC present and responding to the player, the objective is done regardless of the roll band.
2. **Transfer-verb scan is a deterministic pre-check in Python**, not a prompt instruction. It reads the narration string for explicit transfer verbs (`hand`, `hands`, `handed`, `gives`, `gave`, `receives`, `received`, `picks up`, `picked up`, `takes`, `took`, `drops`, `dropped`) and activates the `inventory` domain if found, even if no other domain signal fired. This runs inside `_run_extraction_pipeline` before the `run_state` guard.
3. **NPC dedup pre-pass** in the engine: inside `_run_extraction_pipeline` after the progress call but before the `StateDelta(...)` merge, look up every existing NPC by ID, name, and all aliases. If the new entry's name string-matches any existing NPC's name or alias list (case-insensitive, stripped), redirect the update to the existing NPC's ID rather than creating a new one.
4. **Prompt-level dedup instruction** in `extract_scene_system.j2`: the compendium roster already shown to the scene extractor (added in Plan A) already gives it the full list. Add an explicit instruction to check name and alias against that list before emitting a new `compendium_npc_update` with a new ID. The engine pre-pass is the hard safety net; the prompt instruction reduces LLM dedup errors before they reach the engine.
5. **No new config flags** — all three fixes are always active.

## Cross-plan seam: return signature coordination

`_run_extraction_pipeline` currently returns a 6-tuple at line 500-507 of `extraction.py`:
```python
return (merged, scene_result.actions, scene_result.outcome_summary, state_result.failed, extraction_event, progress_result)
```

Both callers in `turn.py` (lines 538 and 1055) unpack exactly 6 values:
```python
delta, actions, outcome_summary, failed, extraction_event, progress_result = await _run_extraction_pipeline(...)
```

**Plan A** may cut or move `failed` from `StateExtractResult`. If Plan A removes `failed` from the return tuple, both call sites in `turn.py` will break with an unpacking error. **Plan D must not change the return tuple arity.** If Plan A changes the return signature, Plan D's Phase 2 step 2.2 logging block that references `state_result.failed` will need to be updated to match the new signature, and both `turn.py` call sites must be updated in lockstep. This plan assumes the 6-tuple signature remains stable.

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

Add a transfer-verb scan function. Call it inside `_run_extraction_pipeline` before the `run_state` guard (line 393) as a supplementary check that activates `inventory` domain even when the primary domain detection didn't fire.

**Key detail:** Domain activation is controlled by the caller (`turn.py` lines 503-505) which parses domains from the narration and passes `active_domains` into `_run_extraction_pipeline`. There is no `_determine_active_domains` function — the transfer-verb scan must be inserted inside `_run_extraction_pipeline` itself, modifying the `active_domains` list before the `run_state = bool({"inventory", "pc_condition"} & active)` guard at line 393.

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

#### Step 2.2 — Call `_narration_has_transfer` in `_run_extraction_pipeline` before the `run_state` guard

**File:** `ccya/engine/extraction.py`

**What:** Inside `_run_extraction_pipeline`, after the `active = set(active_domains)` line (line 333) and before the `run_state = bool({"inventory", "pc_condition"} & active)` line (line 393), add the transfer-verb scan. The narration string is available as a parameter to `_run_extraction_pipeline` (line 318).

```python
# After: active = set(active_domains)
# Before: run_state = bool({"inventory", "pc_condition"} & active)

# Transfer-verb scan: supplementary inventory domain trigger
if "inventory" not in active and _narration_has_transfer(narration):
    active_domains = list(active_domains) + ["inventory"]
    active = set(active_domains)  # refresh the set
    _log.debug(
        "extraction.domains: transfer-verb scan activated inventory domain",
        extra={"turn": turn_no, "trace_id": trace_id},
    )
```

**Why:** The transfer scan is a supplementary signal only — it does not override existing domain logic, it only adds `inventory` if it was otherwise absent. It must run before the `run_state` guard so that the state stream is conditionally executed when transfer verbs are detected.

**Validation:** Unit test: `_run_extraction_pipeline` called with a narration containing "handed you" and no other inventory signal — assert that the state stream runs (i.e., `extraction_event["state"]["skipped"]` is `False`).

---

## Implementation — Phase 3: NPC compendium dedup

### Context files to load

- `ccya/engine/extraction.py` (post Plan A)
- `ccya/prompts/extract_scene_system.j2` (post Plan A, post Plan B)

### Overview

Two-layer dedup: a prompt instruction and an engine pre-pass. The prompt instruction tells the LLM to check name and aliases before emitting a new compendium add. The engine pre-pass catches any that slip through.

**Key detail:** `compendium_npc_update` from `progress_result` is merged directly into `StateDelta` at line 494 in `extraction.py`. The actual apply logic is in `state/delta.py:554-588` inside `apply_delta`. The dedup pre-pass must go in `_run_extraction_pipeline` between the progress call (line 456) and the `merged = StateDelta(...)` construction (line 477), operating on `progress_result.compendium_npc_update` before it enters the `StateDelta` constructor.

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

#### Step 3.2 — Add engine-level dedup pre-pass in `_run_extraction_pipeline`

**File:** `ccya/engine/extraction.py`

**What:** Add a `_dedup_compendium_add` helper function, then call it inside `_run_extraction_pipeline` between the progress call (line 456) and the `merged = StateDelta(...)` construction (line 477). The dedup operates on `progress_result.compendium_npc_update` before it enters the `StateDelta` merge.

**Why:** Hard safety net — catches dedup failures that survive the prompt instruction. The dedup must run at extraction time (before the delta is constructed), not at apply time in `state/delta.py`, because we need to redirect the ID before it enters the `StateDelta` model.

**Code Snippet** — helper function (add near `_narration_has_transfer`):

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
```

**Code Snippet** — insertion point in `_run_extraction_pipeline` (between lines 474 and 477):

```python
# --- Dedup compendium updates before merging into StateDelta ---
existing_npcs = list(state.get("known_characters") or [])
deduped_compendium: list["CompendiumNpcUpdate"] = []
for cu in (progress_result.compendium_npc_update or []):
    deduped_compendium.append(_dedup_compendium_add(cu, existing_npcs))
# Replace progress_result.compendium_npc_update with deduped version
# (mutate in place to avoid replacing the entire result object)
progress_result.compendium_npc_update = deduped_compendium

# --- Merge into single StateDelta ---
merged = StateDelta(
```

Note: `known_characters` in state is the list of NPC dicts with `id`, `name`, `aliases` fields. The dedup function compares against this list before the delta is constructed.

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
    from ccya.engine.extraction import _narration_has_transfer
    assert _narration_has_transfer("She hands you a sealed envelope.")
    assert _narration_has_transfer("You pick up the coin from the floor.")
    assert not _narration_has_transfer("The guard nods at you from across the room.")

def test_domain_scan_adds_inventory_when_transfer_present():
    # Call _run_extraction_pipeline with narration containing transfer verb
    # and no other inventory trigger — assert state stream is NOT skipped.
    # The state stream skip is determined by: run_state = bool({"inventory", "pc_condition"} & active)
    # After transfer-verb scan, "inventory" should be in active_domains, so run_state should be True.
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

`docs/REPOMAP/extraction.md` — document `_narration_has_transfer`, `_dedup_compendium_add`, the transfer-verb scan insertion point in `_run_extraction_pipeline`, the dedup pre-pass insertion point in `_run_extraction_pipeline`, and the contact-objective rule addition to the progress prompt.

### Risks

1. **Transfer-verb false positives** — "takes a seat", "drops the subject", "passes a moment" are idiomatic uses that don't signal inventory transfer. The verb list should be reviewed against actual narration samples. Worst case: inventory domain runs an extra time — this is low-risk since the state extractor is conservative and only extracts explicit items.
2. **Dedup operates on `known_characters` from state** — the dedup pre-pass uses `state.get("known_characters")` which is the full NPC list. This is the correct source because it includes all known NPCs, not just compendium entries. The `known_characters` list has `id`, `name`, and `aliases` fields (aliases may be absent on older records — the snippet handles this with `npc.get("aliases") or []`).
3. **Cross-plan seam with Plan A** — if Plan A removes `failed` from the `_run_extraction_pipeline` return tuple, both `turn.py` call sites (lines 538 and 1055) will break with an unpacking error. Plan D does not change the return tuple, but if Plan A changes it, Plan D's Phase 2 step 2.2 that references `state_result.failed` will need updating. This is tracked in the cross-plan seam section above.
4. **scene_pressure is still passed via user template** — Plan D's non-goals say it doesn't touch pressure, which is fine. `scene_pressure` is read from `state["scene"]["scene_pressure"]` and injected into `extract_progress_user.j2` (line 214 of `extraction.py`). After Plan A moves pressure fields to the scene extractor, whoever updates Plan D needs to know scene_pressure is still passed via the user template from state, not from `scene_result`. Plan D's Phase 3 step 3.1 says "post Plan A, post Plan B" as a dependency for `extract_scene_system.j2`, which is correct.

## Ambiguities requiring resolution before execution

None.

## TODO.md update

Under `## P1 — Active`:

Quest and state extraction fixes — docs/plans/eval-results-remediation/eval-results-remediation-quest-state-extraction.md
