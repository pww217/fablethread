# ArcThread.key Deduplication + Narrator ARC_UPDATE Exposure

## Status
`completed`

## Phases

1 phase: Add optional `key` field to ArcThread for canonical concept labeling, implement Python-side auto-merge dedup gate at thread_add point using token-overlap scoring (70% threshold), and expose `thematic_question` as an allowed ARC_UPDATE key in the narrator prompt schema example.

## Issue
Two independent gaps prevent GM signal system from working effectively:

1. **Thread duplication:** The storyteller can emit multiple threads with semantically identical tensions but different IDs because deduplication only checks exact ID collision (string match). There's no instruction to check for conceptual overlap before emitting `thread_add`, and no Python-side validation using fuzzy matching on canonical labels. This causes duplicate entries in the campaign arc that confuse pacing logic and waste prompt tokens re-processing the same tension multiple times.

2. **Silent capability gap:** The engine already accepts `thematic_question` updates from the narrator (it's in `_ALLOWED_NARRATOR_ARC_KEYS` at turn.py line 1352), but the ARC_UPDATE JSON schema example in narrate_system.j2 only shows `discovered_truths` and `visible_goal`. The LLM doesn't know it can emit `thematic_question`, so this engine capability is unused.

## Solution
Add optional `key: str | None = None` field to ArcThread model for canonical 2-4 token snake_case concept labels (e.g., `"lira_betrayal"`, `"hull_breach"`). At the thread_add point in turn.py (between lines 1313 and 1314, before scope gate), implement auto-merge dedup: if new thread has a non-null key, compare against existing threads' keys using token-overlap scoring (set intersection of tokens divided by max length) with 70% threshold. If similarity ≥ 70%, update the existing thread's summary and tags rather than creating a duplicate — log INFO at merge point noting which threads were merged. If exact key collision but below fuzzy match: reject `thread_add` with WARNING log (`thread_add.key_collision`).

Update narrate_system.j2 ARC_UPDATE JSON example to include `"thematic_question": "..."` as an allowed field. The engine already accepts it — only the prompt schema needs updating. No code changes required for this part.

Expected outcome: Duplicate threads caught at creation time and auto-merged rather than silently dropped or accepted; narrator informed of `thematic_question` capability so campaign arc can track emotional register shifts.

## Firm decisions
1. Auto-merge uses token-overlap scoring from inventory.py `_fuzzy_match_inventory` pattern (set intersection / max length), not SequenceMatcher or substring containment — 70% threshold rather than inventory's 60%, justified because thread keys are short canonical labels where false positives more damaging than longer inventory names
2. Dedup placement must be before scope gate (`elif _scope == "scene": pass` on lines 1314-1316) so scene-scoped threads also get key-based deduplication rather than bypassing new logic via `pass`
3. Reject only if fuzzy match below threshold after exact key collision detected — auto-merge on high similarity to preserve new tension rather than silently dropping it
4. Storyteller instructed to generate keys using structured conventions (`subject_action` or `location_event` format, lowercase snake_case) to prevent drift across turns; existing hint at line 126 ("Do not emit `key: null`") kept as useful guidance for handling optional field
5. `_ALLOWED_NARRATOR_ARC_KEYS` set unchanged — already includes `thematic_question`; only prompt schema example updated

## Non-goals
- No new config fields (consecutive_pressure_threshold deferred to Phase 03 pacing overhaul)
- No changes to ArcThread lifecycle logic (advance/expire/promote/complete unchanged except for key field presence)
- No primary thread designation mechanism ("most important active thread" deferred — value unclear without concrete consumer)
- No migration of existing threads to have keys — new field is optional, only affects newly created threads

## Risks, Ambiguities, and Blockers
- **Ambiguity:** What constitutes "conceptual overlap" for auto-merge? The plan uses token-overlap scoring as a proxy. If two keys share tokens but represent different concepts (e.g., `"lira_betrayal"` vs `"lira_return"` — 33% overlap, below threshold), the fuzzy match correctly rejects them. Edge case: very short keys like `"betrayal"` and `"the betrayal"` have 100% overlap on token set `{"betrayal"}` but may represent different narrative beats. This is acceptable risk because auto-merge updates summary/tags rather than replacing — new tension gets preserved in the merged thread's content even if label differs slightly.
- **Risk:** Storyteller LLM may not consistently generate meaningful keys or check for overlap before emitting `thread_add`. The structured convention instruction (`subject_action` / `location_event`) and explicit overlap-checking instruction mitigate this, but imperfect key generation is better than no dedup — auto-merge handles near-duplicates gracefully.
- **Blocker:** None. Phase 01 cleanup must complete first to have clean turn.py context around lines 1300-1320 (no conflicting recently_left/JUST_LEFT references in the thread_add block).

## Implementation — Phase 1: ArcThread.key Dedup + ARC_UPDATE Exposure

### Context files to load
- `ccya/models.py` (ArcThread model definition)
- `ccya/engine/turn.py` (lines 1300-1320, thread_add point before scope gate; line 1352 for _ALLOWED_NARRATOR_ARC_KEYS context)
- `ccya/state/inventory.py` (_fuzzy_match_inventory function — reference only for token-overlap scoring pattern to replicate)
- `ccya/prompts/narrate_system.j2` (~line 69, ARC_UPDATE JSON schema example to update)
- `ccya/prompts/storytell_system.j2` (~lines 15 and 38-39, thread_add rules section to add overlap-checking instruction and optional key field to schema example)

### Detailed steps

#### Step 1.1 — Add optional `key` field to ArcThread model in models.py

**File:** `ccya/models.py`

**What:** Add the following line after `promotes: list[str] = Field(default_factory=list)` on line 57 (at the end of ArcThread class definition, before the blank line separating it from CampaignArc):
```python
    key: str | None = None  # optional canonical concept label; 2-4 token snake_case for dedup at thread_add time with auto-merge on collision
```

**Why:** ArcThread needs an optional field to hold a canonical concept label emitted by the storyteller. This enables Python-side dedup validation at the thread_add point in turn.py (between lines 1313 and 1314). The field is optional (`str | None = None`) so existing threads without keys continue to work — only newly created threads with non-null `key` will trigger dedup logic.

**Validation:** `rg -n "key: str \| None" ccya/models.py` returns exactly one match on the ArcThread class definition (after line 57). `python -c "from ccya.models import ArcThread; t = ArcThread(id='test', summary='Test'); assert t.key is None"` passes without error (backward compat for threads created without key).

#### Step 1.2 — Implement auto-merge dedup gate at thread_add point in turn.py (between lines 1313 and 1314)

**File:** `ccya/engine/turn.py`

**What:** Insert new key-based dedup logic between the cooldown check block (line 1313 ending with `pass`) and the scope gate (`elif _scope == "scene": pass` on line 1314). Specifically, add an `elif` clause after line 1313 that runs for all threads regardless of scope. The dedup logic implements two paths:

1. **Exact key collision:** If `_new_thread.key` exists and matches any existing thread's `key` exactly (case-insensitive), reject the new thread with a WARNING log using structured context `"thread_add.key_collision"` including turn number, colliding key value, both thread IDs, and extra={"turn": ...}. Use `pass` to skip creation — same pattern as pacing gate block on line 1308.

2. **Fuzzy match auto-merge:** If no exact collision but `_new_thread.key` is non-null, compute token-overlap similarity against all EXISTING (non-completed) thread keys using the scoring formula from inventory.py: set intersection of tokens divided by max length (not min). Track best matching key and score across existing threads only — completed threads are excluded from fuzzy matching since they represent resolved tensions that should not be re-merged. If any score ≥ 0.70, auto-merge instead of creating new thread: update the matched thread's `summary` to use `_new_thread.summary` if non-empty, union its `tags` with new tags via set operation, refresh `last_seen_turn`. Use `_merge_arc_update` to persist changes (same pattern as existing calls at turn.py lines 1281/1361). Log INFO at merge point using structured context `"thread_add.auto_merge"` including turn number, matched key value, similarity score rounded to 2 decimals, existing thread ID, new thread ID, and extra={"turn": ...}. Count merged threads toward `last_thread_creation_turn` to prevent rapid re-creation. If best score < 0.70 or no matches found, fall through to the scope gate check below (scene-scoped threads will be skipped by the scope gate below; arc-scoped threads proceed to creation logic).

**Critical placement:** This dedup block must sit **before the scope gate check** (`elif _scope == "scene": pass` on lines 1314-1316) so ALL threads get key-based deduplication regardless of scope. The exact collision path uses `pass` to skip creation; the fuzzy match auto-merge path handles everything inline and does NOT fall through to existing thread creation block (it already merged). If no merge occurs, execution falls through to the next `elif` which is the scope gate (lines 1314-1316) — preserving original control flow for threads that don't need dedup action.

**Fallback behavior:** Threads without a key (`_new_thread.key is None`) or with empty string bypass dedup entirely and fall through to existing scope gate / creation logic unchanged. This ensures backward compat for any threads created before keys were introduced.

**Validation:** `rg -n "thread_add.auto_merge|thread_add.key_collision" ccya/engine/turn.py` returns matches after edit confirming log statements present. The dedup block sits between lines 1313 and 1314 in the existing thread creation if-elif chain, before any scope gate check. Threads without key field pass through to existing logic unchanged via fall-through.

#### Step 1.3 — Update storytell_system.j2: add conceptual overlap instruction + optional key field to schema example

**File:** `ccya/prompts/storytell_system.j2`

**What:** Two changes to the thread_add section (~lines 15 and 38-39):
- Line 15 (JSON schema example `"thread_add": null`): Replace with a minimal ArcThread structure showing all required fields plus optional `key`. The new example should show: id, summary, scope ("arc"), urgency ("normal"), tags ([]), and key ("subject_action") as an illustrative value.
- After line 38 (the existing thread_add rules paragraph), add a new instruction paragraph at the START of the section before the existing description: "CRITICAL: Before emitting `thread_add`, check all active and latent thread summaries for conceptual overlap. If an existing thread covers the same story tension (even with a different ID), do NOT emit `thread_add` — instead advance that existing thread via `thread_advance`. Only create new threads when the tension is genuinely distinct."
- Append to the end of line 38's thread_add instruction paragraph (which ends with "tags (list)."), adding `"key"` as an optional snake_case canonical label like `"subject_action"` or `"location_event"`, lowercase with underscores — helps engine deduplicate semantically identical threads. Keep the hint at line 126 ("Do not emit `key: null`") as useful guidance for handling optional field.

**Why:** The storyteller needs explicit instruction to check for conceptual overlap before emitting new threads — without this, it will create duplicates even with Python-side dedup (better to prevent than catch). The key field in the schema example teaches the LLM how to generate structured canonical labels that enable auto-merge on near-duplicates.

**Validation:** `rg -n "conceptual overlap" ccya/prompts/storytell_system.j2` returns one match for the new instruction paragraph. `"key"` appears in the JSON example and key guidance text but not as a required field (optional). The existing hint at line 126 ("Do not emit `key: null`") remains unchanged.

#### Step 1.4 — Update narrate_system.j2 ARC_UPDATE schema to include thematic_question

**File:** `ccya/prompts/narrate_system.j2`

**What:** Change line 69 to add `"thematic_question"` field to the ARC_UPDATE JSON example. The existing value is `{"discovered_truths": ["exact text of revealed hidden truth"], "visible_goal": "updated goal if changed"}` — append `, "thematic_question": "new or shifted emotional register question for the campaign"` to show this as an allowed field alongside the two existing ones.

**Why:** The engine already accepts `thematic_question` in `_ALLOWED_NARRATOR_ARC_KEYS` at turn.py lines 1352-1355. Only the prompt schema example needs updating to inform the LLM that this field is available. This closes the gap between engine capability and narrator knowledge — currently the narrator never emits `thematic_question` because it's not shown as an option in the JSON example.

**Validation:** `rg -n "<<<ARC_UPDATE_START>>>" ccya/prompts/narrate_system.j2` returns line 68 with updated JSON on line 69 containing `"thematic_question"` field alongside existing fields. No other changes to narrate_system.j2 needed — engine parsing logic unchanged, allowed keys set already includes `thematic_question`.

### Tests to write or update
Per AGENTS.md ("Tests are temporarily removed during refactor"), tests are skipped for this phase. The following test references will need updating when tests re-enable:
- `tests/test_schema.py` — ArcThread model validation tests may fail if they construct threads without the new optional field (unlikely since key has default value); verify any thread construction patterns include or omit key as appropriate

### REPOMAP updates required
- `ccya/models.py`: ArcThread gains optional `key: str | None = None` field after line 57 (`promotes`). REPOMAP should note the new optional field if it documents ArcThread shape. The field is Python-managed for dedup purposes — not set by LLM directly but emitted via storyteller thread_add when key is provided.
- `ccya/engine/turn.py`: New auto-merge dedup logic inserted between lines 1313 and 1314 (between cooldown check block and scope gate, as new elif clause). Contains exact-key collision rejection path for all threads regardless of scope, and fuzzy-match auto-merge path that only matches against EXISTING non-completed threads (completed threads excluded from matching to avoid re-merging resolved tensions). Uses token-overlap scoring with 70% threshold. REPOMAP should note the new thread_add validation step if it documents the pipeline flow around lines 1300-1320. Log statements use `thread_add.auto_merge` and `thread_add.key_collision` as structured context keys for observability.
- `ccya/prompts/storytell_system.j2`: JSON schema example updated to show optional key field in thread_add structure (~line 15). New conceptual overlap checking instruction added before existing thread_add rules (~after line 38). Key guidance text appended to end of line 38 thread_add instruction paragraph, adding `"key"` as optional snake_case canonical label. REPOMAP should note the new storyteller instruction if it documents prompt templates or LLM-facing instructions.
- `ccya/prompts/narrate_system.j2`: ARC_UPDATE JSON example updated to include `"thematic_question"` field alongside existing fields (~line 69). No engine changes — `_ALLOWED_NARRATOR_ARC_KEYS` already includes this key. REPOMAP should note the schema expansion if it documents narrator prompt templates or ARC_UPDATE parsing behavior.
