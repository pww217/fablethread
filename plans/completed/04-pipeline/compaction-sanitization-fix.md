# Compaction sanitization bug + extract/recheck fixes (2026-05-21)

## Status
`completed`

## Phases

3 phases covering: compactor future-state reading, reusable-item prompt contradiction, and NPC checker false-positive vocabulary.

## Issue

Compaction sanitization reads ALL current game state at compaction time — including conditions added in turns after the compact range ends (`compact_end`). The template provides no temporal metadata (no `added_turn`, no `turns_remaining`), so the LLM cannot distinguish "condition that should auto-expire" from "condition needing bulletin evidence." This causes conditions, NPCs, and other state elements to be incorrectly removed during sanitization based on future-turn context.

Additionally, the Extract State prompt template contains a few-shot example (line 78) that contradicts its own spending/giving rule by treating key-use as consumption rather than retention. The NPC mention checker's `descriptor_stop` set is missing common false-positive words ("Crossed", "Careful", "Narrowing").

## Solution

1. **Compactor fix:** Add temporal metadata (`added_turn`, `turns_remaining`) to conditions in the compact template; pass `compact_end` and filter future-state conditions from state sent to template; add `present_from_turn` for NPCs so LLM can distinguish recently-presented NPCs from ones that should be merged.
2. **Extract State fix:** Replace line 78's few-shot example with correct reusable-item guidance ("sliding key into lock" retains the key).
3. **NPC checker fix:** Add "Crossed", "Careful", "Narrowing" to `descriptor_stop` set in `_extract_candidate_names()`.

## Firm decisions

1. Condition drift (Issue 2) is eval-pack specific — caused by `_patch_eval_pack_starting_state()` seeding conditions with future dates intentionally for testing condition aging logic. Not an engine bug; no fix needed.
2. Location delta emission stays as-is per user direction: document current behavior, do not change code. Only `location_description` updates are emitted when spatial descriptions evolve without player movement. This is intentional design — the engine tracks location correctly in `extraction_context.location_this_turn.id`.
3. World Pack Style token waste (Issue 10) appears already fixed — grep confirms pack_style/narrator_rules does NOT flow into extraction prompts; they only appear in narrate_system.j2. No action needed.

## Non-goals

- Condition drift investigation (Issue 2): Confirmed eval-pack specific; no engine fix needed.
- Location delta emission (Issue 6): Documented as intentional design per user direction; code unchanged.
- World Pack Style token waste (Issue 10): Already fixed — pack_style does not flow into extraction prompts. No action needed.
- Credits disappearance (Issue 4): N/A without currency game; out of scope.
- Brass key reusable item: Addressed via prompt template fix only, not a new engine rule or validation layer.
- NPC removal during transitions (Issue 8): Requires multi-location scenario to reproduce; deferred until reproducible.

## Risks, Ambiguities, and Blockers

- **Ambiguity:** Inventory items have no `added_turn` field. If new inventory appears after compact_end but the LLM sees it during sanitization and removes something based on future context, we'd miss that case. Mitigation: accept this limitation for now — inventory_remove is rare compared to condition_remove false positives; can add temporal tracking later if needed.
- **Ambiguity:** NPC `present_from_turn` would need the engine to track when each NPC was added to present_npcs. Currently compendium NPCs persist indefinitely and new ones are created on-the-fly. Adding this requires a small state shape change (store turn_entered per-present-NPC). If not feasible, skip NPC temporal metadata for phase 1 — conditions alone fix the critical bug.
- **Risk:** Modifying compact_user.j2 template changes what the compactor LLM sees; could affect existing game saves' chronicle quality if behavior shifts. Test with a live game after each phase.

## Implementation — Phase 01: Compaction sanitization future-state filter

### Context files to load
- `ccya/engine/compactor.py` (full file, lines 1–444)
- `ccya/prompts/compact_user.j2` (full file, lines 1–62)
- `ccya/prompts/compact_system.j2` (full file)

### Detailed steps

#### Step 01.1 — Add temporal metadata to conditions in compact template

**File:** `ccya/prompts/compact_user.j2`, lines 48–53

**What:** Update the PC Conditions section of the template to include `added_turn` and `turns_remaining` for each condition:
```jinja2
### PC Conditions
{% for c in conditions -%}
- [{{ c.get("id", "?") }}] {{ c.get("label", "?") }} (added T{{ c.get("added_turn", "?") }}, TTL: {{ c.get("turns_remaining", "permanent") }}): {{ c.get("description", "") }}
{% else -%}
(none)
{% endfor %}
```

**Why:** The compactor LLM currently has no way to know when a condition was added or how many turns it has left. Without this metadata, it removes conditions based on bulletin evidence alone — including ones that are still active (haven't expired yet). Adding `added_turn` lets the LLM see if a condition is newer than the compact range; adding `turns_remaining` lets it distinguish "still-active" from "should-expire-soon."

**Validation:** Template renders correctly with conditions that have both fields and ones without TTL:
```bash
python -c "from jinja2 import Environment, FileSystemLoader; e = Environment(loader=FileSystemLoader('ccya/prompts')); t = e.get_template('compact_user.j2'); print(t.render(conditions=[{'id':'test','label':'Test','description':'desc','added_turn':1,'turns_remaining':3}, {'id':'perm','label':'Permanent','description':'cursed','added_turn':0}], turns=[], arc=None, pressures=[], inventory=[], compendium_npcs=[], recent_events=[]))" | grep -A2 "PC Conditions"
```

#### Step 01.2 — Filter conditions sent to template by compact_end

**File:** `ccya/engine/compactor.py`, function `_build_compact_messages()` at line 217, and the call site where conditions are extracted (line 214)

**What:** In `_build_compact_messages()`:
- After extracting conditions from state on line 214 (`conditions = list((state.get("pc") or {}).get("conditions") or [])`), filter to only include conditions with `added_turn <= compact_end`.
- Pass `compact_end` as a parameter into `_build_compact_messages()` (update function signature at line 201).

**Why:** Conditions added after the compaction range end represent future-turn state. Even though they're in current game state, including them in sanitization context lets the LLM see and potentially remove conditions that didn't exist when it's making decisions about past turns. Filtering by `added_turn <= compact_end` ensures only conditions that were actually present during the compacted turn range are visible to the compactor.

**Validation:** After applying this fix, a condition added at T3 should NOT appear in sanitization context for a compaction at T2 with `compact_end=1`. Run:
```bash
python -c "
conditions = [{'id':'startled','added_turn':2}, {'id:'wounded','added_turn':4}]
compact_end = 1
filtered = [c for c in conditions if c.get('added_turn',0) <= compact_end]
assert filtered == [{'id':'startled','added_turn':2}], f'Expected startled only, got {filtered}'
print('PASS: future conditions excluded')
"
```

#### Step 01.3 — Add NPC temporal metadata (present_from_turn) to template

**File:** `ccya/prompts/compact_user.j2`, lines 40–46 and compactor.py line 213

**What:** 
- In `_build_compact_messages()`: when building the compendium_npcs list, include a new field `present_from_turn` for each NPC that tracks when they were first added to present_npcs. This requires reading from state's `scene.present_npcs` and matching IDs against compendium entries.
- In template: add `(seen since T{turn})` annotation next to each NPC name in the Compendium NPCs section.

**Why:** When the LLM is told to merge duplicate NPCs, it needs context about which ones are recently-presented (likely still active) vs long-established characters that might represent consolidation opportunities. Without temporal context, merging a newly-introduced NPC with an established one could lose fresh character information.

**Validation:** Template renders with `present_from_turn` for each compendium NPC:
```bash
python -c "from jinja2 import Environment, FileSystemLoader; e = Environment(loader=FileSystemLoader('ccya/prompts')); t = e.get_template('compact_user.j2'); print(t.render(compendium_npcs=[('trevor', {'name':'Trevor Williams','present_from_turn':1})], conditions=[], turns=[], arc=None, pressures=[], inventory=[], recent_events=[]))" | grep -A1 "Compendium NPCs"
```

### Tests to write or update

- No tests currently exist (tests removed during refactor per AGENTS.md). Document test intent: when tests return, add a unit test for `_build_compact_messages()` that verifies conditions with `added_turn > compact_end` are excluded from the rendered user prompt. Also verify NPC temporal metadata is included in template output.

### REPOMAP updates required

- No REPOMAP changes needed — state shape and public APIs unchanged; only internal compactor behavior modified.

## Implementation — Phase 02: Extract State reusable-item fix

### Context files to load
- `ccya/prompts/extract_state_system.j2` (full file, lines 1–148)

### Detailed steps

#### Step 02.1 — Fix few-shot example for reusable key use

**File:** `ccya/prompts/extract_state_system.j2`, line 78

**What:** Replace the existing line:
```
- Narration: `"You slide the brass key into the lock. It turns with a click and the door swings open."` → `{"inventory_remove": [{"id": "brass_key"}]}` (full remove, no amount)
```
With:
```
- Narration: `"You slide the brass key into the lock. It turns with a click and the door swings open."` → `{}` (key is retained; using ≠ consuming — do NOT emit inventory_remove for reusable items used without destruction or loss)
```

**Why:** The existing example contradicts the spending/giving rule at line 69 which says "spending, giving away, or parting with" triggers removal. Sliding a key into a lock is neither spending nor parting — it's using while retaining ownership. This contradiction causes the LLM to incorrectly remove reusable items on use (eval report Issue 5: brass_key removed at T8 when used to unlock door).

**Validation:** Template renders correctly with new example text visible in output context. No code structure changes needed.

### Tests to write or update

- When tests return, add an extraction unit test that verifies the reusable-item few-shot guidance produces correct behavior (no inventory_remove for key-use narration). Reference FakeLLM patterns: feed a turn where player uses brass_key to unlock door and assert `inventory_remove` is empty in extracted state delta.

### REPOMAP updates required

- No REPOMAP changes needed — template-only change, no new models or APIs.

## Implementation — Phase 03: NPC checker false-positive vocabulary fix

### Context files to load
- `ccya/eval/universal_asserts.py` (lines 275–283 for descriptor_stop set)

### Detailed steps

#### Step 03.1 — Add missing words to descriptor_stop set

**File:** `ccya/eval/universal_asserts.py`, lines 275–283, in `_extract_candidate_names()` function

**What:** Extend the `descriptor_stop` set at line 275-283 with: "Crossed", "Careful", "Narrowing". These are capitalized words that appear as adjectives or location-name fragments (e.g., "Crossed Keys Inn") in narration but get falsely flagged as NPC names because they pass all existing filters.

**Why:** The eval report's Issue 7 documents false positives on these exact words:
- "Crossed" — from location name fragment ("Crossed Keys Inn")  
- "Careful" — adjective describing action or environment
- "Narrowing" — verb participle describing passage/hallway

These pass the regex `\b[A-Z][a-z]{2,}\b` (length >= 3), are not sentence starters, and were absent from `descriptor_stop`. Adding them prevents false NPC mention flags.

**Validation:** Run the checker against narration containing these words:
```bash
python -c "
from ccya.eval.universal_asserts import _extract_candidate_names
narr = 'Crossed Keys Inn loomed ahead. Careful now, he told himself. The narrowing passage swallowed light.'
result = _extract_candidate_names(narr, 'player', [], ['Crossed Keys Inn'])
print(f'candidates: {result}')
assert result == set(), f'Expected empty but got {result}'
print('PASS: false positives filtered')
"
```

### Tests to write or update

- When tests return, add unit test for `_extract_candidate_names()` verifying that "Crossed", "Careful", and "Narrowing" are excluded from candidates when they appear in narration. Also verify partial location-name matching still works (e.g., "Crossed" should not match if full name is already filtered).

### REPOMAP updates required

- No REPOMAP changes needed — only modifying existing `descriptor_stop` set, no new functions or models.
