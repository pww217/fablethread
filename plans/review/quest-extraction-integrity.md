# Quest Extraction Integrity

## Status
`open`

## Part of
standalone

## Dependencies
- none
- The `quest_id_collision` universal assert already exists in `universal_asserts.py` and will surface failures that this plan fixes — no changes needed to the assert itself

## Objective
Quest extraction has four documented failure modes. First, the progress extractor re-creates completed quests with new entries rather than advancing their status, producing duplicate quest IDs in state. Second, the extractor emits `quest_updates` with `status: "active"` for quests the narrator never actually referenced, creating phantom quest noise. Third, step deduplication is broken — the same step text appears multiple times in `quest.steps` across turns because the extractor emits a new step instead of recognizing it as a continuation or completion of an existing one. Fourth, quest IDs are not stable — the extractor sometimes emits a different slug for the same quest across turns, breaking the ID-keyed lookup. The root cause across all four is under-specification in the progress extractor system prompt: no negative examples, no explicit ID stability rule, no "completed quests are immutable" constraint, and no step deduplication guidance. This plan adds all four constraints.

## Non-goals
- Does not change the quest data model in `models.py`.
- Does not add a new quest deduplication engine pass (that would be a separate engine plan).
- Does not touch the compactor's quest-close sanitization logic.
- Does not change `universal_asserts.py` — the `quest_id_collision` assert already catches the symptom; this plan fixes the cause.
- Does not address quest arc quality (narrative concern, rubric's domain).

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/prompts/extract_progress_system.j2` | modify | Add four quest-specific rules: ID stability, completed-is-immutable, phantom-quest guard, step deduplication |
| `ccya/prompts/sections/_quests.j2` | modify | Mark completed quests with `[COMPLETED — DO NOT UPDATE]` in the rendered block |
| `docs/REPOMAP/prompts.md` | update | Document new quest constraint rules |

## Firm decisions

1. **Completed quests are immutable.** Once a quest has `status: "completed"` or `"failed"`, the extractor must never emit a `quest_updates` entry for that quest ID. This is an absolute prohibition, not a suggestion.
2. **Quest IDs are stable.** The ID for a quest is set on first emission and never changes. The extractor must reuse the exact ID from the `_quests.j2` block. If the quest already exists in state, use its existing ID verbatim.
3. **Phantom quest guard.** The extractor must only emit `quest_updates` for quests that are explicitly referenced in the narration text. "Referenced" means: the quest's location, a named NPC from the quest, or the quest objective is clearly present in this turn's narration. If the narration does not mention a quest's content, do not emit an update for it.
4. **Step deduplication.** Before emitting a new step for an existing quest, the extractor must check if the `_quests.j2` block already contains a step with the same or semantically equivalent text. If it does, do not emit a duplicate. Update the existing step's status instead.
5. The `[COMPLETED — DO NOT UPDATE]` marker in `_quests.j2` must be visible and prominent — on its own line, not inline.

## Implementation — Phase 1: Mark Completed Quests in _quests.j2

### Context files to load
- `ccya/prompts/sections/_quests.j2`

### Overview
Completed and failed quests must be visibly marked in the rendered quests block so the extractor can see at a glance which quest IDs are off-limits.

### Detailed steps

#### Step 1.1 — Add completion marker to _quests.j2

**File:** `ccya/prompts/sections/_quests.j2`

**What:** For each quest in the rendered list, check `quest.status`. If `status in ("completed", "failed")`, append a prominent marker line after the quest entry:

```
{% if quest.status in ("completed", "failed") %}
  ⚠ [COMPLETED — DO NOT emit quest_updates for id: {{ quest.id }}]
{% endif %}
```

**Why:** Same principle as `[DEPLETED]` in the inventory block — make the constraint visually obvious in the data the model reads, not hidden in a system rule it might not attend to.

**Validation:** Render `_quests.j2` with one active and one completed quest. Confirm the completed quest has the `[COMPLETED — DO NOT emit...]` line. Confirm the active quest does not.

***

## Implementation — Phase 2: Add Quest Constraint Rules to extract_progress_system.j2

### Context files to load
- `ccya/prompts/extract_progress_system.j2`
- `ccya/prompts/sections/_quests.j2`

### Overview
Add four explicit rules to the progress extractor system prompt. Each rule addresses one of the four failure modes. Include a negative few-shot for the ID collision case (the most common failure).

### Detailed steps

#### Step 2.1 — Add ID stability rule

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** In the `## Rules` section, add:

```
**QUEST ID STABILITY (MANDATORY):** Quest IDs never change once created. If a quest already exists in the quests block, use its exact id string verbatim — do not paraphrase, re-slug, or create a new id for the same quest. New id values are only valid for quests that do not exist in the quests block at all.
```

**Validation:** Render system prompt. Confirm rule text present.

***

#### Step 2.2 — Add completed-is-immutable rule and few-shot

**File:** `ccya/prompts/extract_progress_system.j2`

**What:**
```
**COMPLETED QUESTS ARE IMMUTABLE (MANDATORY):** Any quest marked [COMPLETED — DO NOT emit quest_updates...] in the quests block must never appear in quest_updates. Do not re-open, re-create, or update a completed quest for any reason.

EXAMPLE (correct):
Quests block contains: "find_the_courier [COMPLETED — DO NOT emit quest_updates for id: find_the_courier]"
Narration references events at the courier's location.
→ Do NOT emit quest_updates for find_the_courier. The quest is closed.

EXAMPLE (incorrect — never do this):
→ { "id": "find_the_courier", "status": "active", "title": "Find the Courier" }
   This re-creates a completed quest. This is always wrong.
```

**Validation:** Render system prompt. Confirm both examples present.

***

#### Step 2.3 — Add phantom quest guard rule

**File:** `ccya/prompts/extract_progress_system.j2`

**What:**
```
**PHANTOM QUEST GUARD:** Only emit quest_updates for a quest if this turn's narration explicitly mentions that quest's objective, its key NPC, or its key location. Do not emit quest_updates just because a quest is in the quests block. Silence is correct when the quest was not advanced this turn.
```

**Validation:** Render system prompt. Confirm rule text present.

***

#### Step 2.4 — Add step deduplication rule

**File:** `ccya/prompts/extract_progress_system.j2`

**What:**
```
**STEP DEDUPLICATION:** Before adding a new step to a quest, check whether a step with the same meaning already exists in the quest's steps list in the quests block. If it does, update that step's status rather than creating a new entry. Two steps are duplicates if they describe the same action or objective, even if worded differently ("Talk to the innkeeper" and "Speak with the innkeeper" are the same step).
```

**Validation:** Render system prompt. Confirm rule text present.

***

### Tests to write or update
- `tests/test_prompts.py`: `test_completed_quest_marker_in_quests_block` — render `_quests.j2` with completed quest fixture → assert `[COMPLETED — DO NOT emit` in output.
- `tests/test_prompts.py`: `test_quest_rules_in_progress_system` — render `extract_progress_system.j2` → assert all four rule headers present.
- `tests/test_universal_asserts.py`: `test_quest_id_collision_assert` — construct event with completed quest + quest_updates re-creating same id → assert assert fires. (May already exist; verify and add if not.)

### REPOMAP updates required
- `docs/REPOMAP/prompts.md`: under `extract_progress_system.j2`, add: "Quest constraint rules: ID stability, completed-is-immutable + few-shot, phantom quest guard, step deduplication."
- `docs/REPOMAP/prompts.md`: under `_quests.j2`, add: "Completed/failed quests marked with [COMPLETED — DO NOT emit...] marker."

### Risks
1. **Phantom quest guard too restrictive** — if a quest's NPC appears in passing in narration (background mention), the extractor may correctly skip updating but a real advancement was missed. Mitigation: the rule says "explicitly mentions" — executor should add a clarifying qualifier: "a brief background mention does not count; the quest must be foregrounded in the turn's action."
2. **Step deduplication semantic matching is hard for an LLM** — the model may miss paraphrases. Mitigation: the rule sets the expectation; it won't be perfect but it will reduce the worst cases. Perfect deduplication would require an embedding-based engine pass (out of scope).

## Ambiguities requiring resolution before execution
1. What is the current field name for quest steps in the quests block render? Is it `steps` (a list of dicts with `text` and `status`), or a different structure? Executor must read `_quests.j2` to confirm field names before writing the deduplication rule.
2. Does `extract_progress_system.j2` currently have a `## Rules` section, or are rules inline with the schema? If no `## Rules` section exists, executor should create one following the schema block (per the Prompting plan's schema/rules separation).

## TODO.md update
Add under **P2 — Quality / Prompting**:
```
- [ ] [Quest Extraction Integrity](plans/quest-extraction-integrity.md)
```
