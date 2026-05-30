# Incremental History + Compactor Removal

## Status
`open`

## Phases

3 phases: (1) repurpose `outcome_summary` as 3rd-person durable facts (PC name, no 4th wall), append to `prior_history` per turn, cap at 20 newest, slash narrator's recent_turns to 1; (2) remove batch compactor entirely, strip dead config, clean up chronicle/state functions, add `reason` field to `CompactorSanitizationAction` for future use; (3) strip compaction display from TV viewer, strip `[T{n}]` artifacts from player-facing display, rename functions for clarity.

## Issue
The batch compactor creates a systematic gap in narrative context: between compaction cycles, turns exist in the chronicle as full prose but fall outside both the COMPACTED section and the narrator's recent_turns window. With `compact_every=5`, `recent_turns_min=2`, `window_turns=3`, turns 4-5 are invisible at turns 6-9. The compactor is also an expensive LLM call every 5th turn for what amounts to bullet summarization that each turn's storyteller could produce incrementally. Sanitization actions currently lack human-readable reasons.

## Solution
Replace batch compaction with incremental history bullets produced by the storyteller each turn. Repurpose `outcome_summary` from 2nd-person flavor text to 3rd-person durable facts using the PC's name (no 4th wall, no "you"). After each turn, format as `- [T{n}] {outcome_summary}` and append to `meta.prior_history`, capped at the 20 newest bullets (oldest dropped). The narrator receives `prior_history` (last 20 bullets) plus exactly 1 recent turn as full prose. No gaps by construction. Remove the batch compactor entirely — no migration, no backward compatibility. Sanitization is out of scope for this plan (TBD: on-demand or batch). Add `reason: str | None = None` to `CompactorSanitizationAction` for future sanitization work. Rename functions to reflect their simplified behavior.

## Firm decisions
1. **Storyteller produces `outcome_summary` per turn, repurposed as durable history bullet.** No new field — instead of 2nd-person flavor text, `outcome_summary` becomes 3rd-person using the PC's name, factual, no 4th wall, one sentence. Appended to `prior_history` each turn as `- [T{n}] {outcome_summary}`.
2. **Narrator receives 1 recent turn + prior_history (last 20 bullets).** `window_turns` and `recent_turns_min` are removed. Prior_history truncates to 20 newest, dropping oldest. Never truncate bullet content, only drop oldest entries.
3. **Batch compactor is removed entirely.** No backward compatibility. No migration. `maybe_compact()`, `_write_compacted_block()`, `_extract_turns_for_compact()`, `compact_system.j2`, `compact_user.j2` all deleted.
4. **No per-turn deterministic sanitization in this plan.** Sanitization work (NPC dedup, inventory cleanup, etc.) is TBD — on-demand or batch, separate plan. The `CompactorSanitizationResult` model and `reason` field are kept/added for future use.
5. **`CompactorSanitizationAction` gets `reason: str | None = None`.** Added now for future sanitization work. Not wired to any logic in this plan.
6. **`compact_every`, `compact_temperature`, `recent_turns_min` removed from EngineConfig.** `window_turns` is also removed — narrator always gets 1 recent turn. `chronicle_prefix_budget_tokens` is also removed (no COMPACTED section to budget).
7. **`outcome_summary` is repurposed, not split.** Was 2nd-person flavor text; now 3rd-person factual summary using PC name. No separate `history_bullet` field.
8. **UI strips `[T{n}]` prefix from history bullets.** Internal format is `- [T{n}] text`; player display shows pure prose.
9. **No backward compatibility, no migration.** Old saves with COMPACTED sections or `last_compacted_turn` values will simply not use those fields. The narrator reads from `prior_history` (which still works) and 1 recent turn from chronicle.
10. **Functions renamed for clarity.** `_compute_recent_window` → `_recent_turn_count`, `load_chronicle_tail` removed or simplified, `load_recent_chronicle_turns` → `load_last_narration`.

## Non-goals
- **Adding a separate `history_bullet` field.** `outcome_summary` is repurposed instead — one field, 3rd person, PC name, factual.
- **Rewriting storyteller prompts for `actions` or `thread_*` fields.** Only `outcome_summary` guidance changes.
- **Removing the chronicle.md file or stopping narrative writes.** Chronicle still holds full prose for TV viewer and debugging.
- **Per-turn or batch sanitization.** Out of scope. TBD in a future plan.
- **Migrating existing saves.** No backward compatibility.
- **Adding sanitization UI.** No sanitization display changes beyond removing compaction display.

## Risks, Ambiguities, and Blockers

- **Storyteller prompt quality for `outcome_summary`.** The LLM must produce durable factual summaries in 3rd person using the PC's name, not flavor text. If the prompt guidance is weak, summaries will be too verbose or too sparse. Requires prompt iteration.
- **20-bullet cap may be too aggressive for long games.** After turn 20, the earliest turns are invisible to the narrator. The arc/thread system and world state carry persistent context, so this may be acceptable. Can be tuned later.
- **Removing the compactor touches eval/judge.py and eval/universal_asserts.py.** These files reference `compaction_signals`, `compute_compaction_signals`, `render_compaction_section`, and `_assert_compactor_sanitization_nonzero`. Deleting `compaction_signals.py` without updating `judge.py` and `universal_asserts.py` will cause import errors. These must be gutted or removed alongside the compactor.
- **`context.py` boundary models need updating.** `NarratorBoundary` at line 227 has `prior_history: list[str]` — no changes needed there. But `recent_turns: list[ChronicleEntryBlock]` at line 226 needs review since recent_turns now always has exactly 1 entry. `StorytellerBoundary` at line 283 also has `recent_turns`. The plan doesn't mention `context.py` in its context files for any phase.
- **`panels.py` uses `load_recent_chronicle_turns`.** The plan says to rename this to `load_last_narration` but Step 2.4 only mentions chronicle.py, `__init__.py`, and turn.py. The `panels.py` call site at line 58 must also be updated, or the rename will break the server.
- **Step 2.2 specifies `apply_delta` in `delta.py` but the real implementation is in `delta_builder.py`.** The thin wrapper in `delta.py` at line 30 delegates to `delta_builder.py`. A new `sanitize_state` function would logically go in `delta_builder.py` or a new module, not in the wrapper.
- **`_compute_recent_window` returns a tuple `(desired_recent, last_compacted_turn)` and is called at turn.py line 1089.** The plan says to change it to `_recent_turn_count` returning only `int`. This changes the call site from `desired_recent, last_compacted_turn = _compute_recent_window(state, config)` to `desired_recent = _recent_turn_count(state)`. The `load_recent_chronicle_turns` call at line 1090-1094 currently passes `min_turn_exclusive=last_compacted_turn` — this argument must be removed when the function is renamed since `last_compacted_turn` no longer exists.
- **`CompactorNpcMerge` is only used in `models.py` (definition + field on `CompactorSanitizationResult`).** Not referenced in `compactor.py` at all — the compactor operates on raw dicts from `CompactorSanitizationResult.model_dump()`. This model should be kept since Step 2.1 keeps `CompactorSanitizationResult` and its sub-models.

## Implementation — Phase 1: Incremental history bullet

### Context files to load
- `ccya/models.py` (StorytellerResult at line 382 — no structural change, confirm `outcome_summary` field exists)
- `ccya/prompts/storytell_system.j2` (output schema, outcome_summary guidance at lines 8, 46)
- `ccya/prompts/storytell_user.j2` (storyteller user prompt)
- `ccya/engine/turn.py` (prior_history append, maybe_compact call at ~line 1629, _compute_recent_window at line 779, call sites at lines 1089-1099)
- `ccya/engine/narrate.py` (prior_history and recent_turns rendering at lines 83-84)
- `ccya/prompts/narrate_user.j2` (Prior Turns section at lines 49-61)
- `ccya/prompts/context.py` (NarratorBoundary with prior_history, recent_turns, StorytellerBoundary with recent_turns)
- `ccya/state/chronicle.py` (load_chronicle_tail, load_recent_chronicle_turns)
- `ccya/engine/extraction.py` (storytell result extraction, yield tuple at lines 650-658, outcome_summary at line 653)
- `ccya/server/panels.py` (imports and uses load_recent_chronicle_turns at lines 12, 58)

### Detailed steps

#### Step 1.1 — Repurpose `outcome_summary` as 3rd-person durable fact bullet

**File:** `ccya/models.py`, class `StorytellerResult` (line 382)

**What:** No new field. `outcome_summary` is repurposed from 2nd-person flavor text to 3rd-person factual summary using the PC's name. The field itself stays `outcome_summary: str = ""`. The change is in prompt guidance only (Step 1.2).

**Why:** Avoids adding a separate `history_bullet` field and having the LLM produce two near-identical summaries per turn. One field, one purpose: durable factual summary.

**Validation:** `make check` passes. `StorytellerResult` is unchanged structurally.

#### Step 1.2 — Repurpose `outcome_summary` prompt guidance in storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2`

**What:** Replace the existing `outcome_summary` guidance with new 3rd-person factual guidance. The `outcome_summary` field stays in the JSON schema — only the prompt text changes. Remove any 2nd-person or flavor text guidance for `outcome_summary` and replace with:

```
`outcome_summary`: One sentence in third person using the PC's name (never "you" or "the player"). A durable factual summary of what happened this turn — what the PC did, what changed, and any consequences. Not flavor text or narration. Only include facts that would matter 10 turns from now. Omit if nothing of narrative significance happened.

Examples:
- "Curtis confronted Jacob Mercer about the sealed letter and forced a confession."
- "The crew mutinied against the captain after discovering his betrayal."
- "Curtis searched the captain's cabin but found nothing new."
```

**Why:** The LLM needs explicit constraints: third person, PC name, durable facts only. Without them, summaries drift toward 2nd-person flavor text or trivial details.

**Validation:** Run a turn and verify `outcome_summary` appears in storyteller output JSON as 3rd person, uses PC name, and is factual.

#### Step 1.3 — No extraction pipeline wiring needed

`outcome_summary` already flows through the extraction pipeline and is yielded at `ccya/engine/extraction.py` line 653. No new field was added — `outcome_summary` is repurposed, not replaced. The extraction yield tuple, return types, and downstream destructuring in `turn.py` are unchanged.

#### Step 1.4 — Append outcome_summary to prior_history after each turn, cap at 20

**File:** `ccya/engine/turn.py`

**What:** After the storyteller result is extracted and the turn number is known, format `outcome_summary` as `- [T{turn_no}] {outcome_summary}` and append to `state["meta"]["prior_history"]`.

If `outcome_summary` is empty or whitespace, do NOT append — skip that turn entirely. The `prior_history` list may have no gap in turn numbers.

Cap prior_history at 20 entries: after appending, if `len(prior_history) > 20`, truncate from the front (drop oldest). Never truncate bullet content — only drop entire entries.

Replace the existing `maybe_compact()` call block (lines 1629-1637) with this append logic. The compactor import and call are dead code after this change (removed in Phase 2).

**Why:** Each turn produces one bullet incrementally, replacing the batch compactor's periodic LLM call. Cap at 20 newest ensures the narrator context doesn't bloat indefinitely. Dropping oldest preserves recency.

**Validation:** Run 3 turns and verify `state["meta"]["prior_history"]` grows by one bullet per turn. Run 25 turns and verify it's capped at 20 entries with the oldest dropped.

#### Step 1.5 — Simplify narrator context to 1 recent turn

**File:** `ccya/engine/turn.py`, function `_compute_recent_window` (line 779)

**What:** Replace the function body to always return 1 recent turn. Remove the `config` parameter since it's no longer needed. Rename the function to `_recent_turn_count`:

```python
def _recent_turn_count(state: dict[str, Any]) -> int:
    """Always return 1 — the narrator gets exactly one recent turn as full prose."""
    return 1
```

Also remove the `last_compacted_turn` return value — it's no longer used. Update the call site at turn.py line 1089 that destructures `(desired_recent, last_compacted_turn)` to instead call `_recent_turn_count(state)` and assign just the int. Remove the `load_recent_chronicle_turns` call at lines 1090-1094 that passes `min_turn_exclusive=last_compacted_turn`, since that parameter will be removed in Phase 2. For Phase 1, just pass 0 as `min_turn_exclusive`.

Remove the call to `load_chronicle_tail` in the turn pipeline (lines 1095-1099) since it reads the COMPACTED section from chronicle, which new saves won't have. Set `chronicle_tail` on `TurnContext` to an empty string.

Rename `load_recent_chronicle_turns` to `load_last_narration` in `ccya/state/chronicle.py` and update its call sites in both `turn.py` and `ccya/server/panels.py` (line 12, line 58). Simplify its signature — remove `min_turn_exclusive` parameter since it was only used for compaction boundary tracking.

Update the narrate pipeline: `recent_turns` always contains exactly 1 turn (the most recent). `prior_history` contains the last 20 bullets.

**Why:** With incremental history bullets from `outcome_summary` in `prior_history`, the narrator only needs the most recent turn as full prose. Eliminates the gap problem by construction.

**Validation:** `make check` passes. Run a game past turn 5 and verify the narrator prompt includes `prior_history` bullets and exactly 1 entry in `recent_turns`.

#### Step 1.6 — Update narrate_user.j2 section headers for clarity

**File:** `ccya/prompts/narrate_user.j2`, lines 49-61

**What:** Change `## Prior Turns (Compacted)` to `## Prior Turns`. The content format is unchanged — `- [T{n}] text` bullets. Verify `## Recent Turns` renders correctly with 1 turn.

**Why:** "Compacted" is no longer accurate since bullets are produced incrementally, not by a batch compactor.

**Validation:** Inspect the rendered narrator prompt for a multi-turn game.

### Tests to write or update

No tests during refactor phase per AGENTS.md. Run `make check` at end of phase only.

### REPOMAP updates required

- `outcome_summary` repurposed from 2nd-person flavor text to 3rd-person durable fact summary (prompt guidance change only, no model change)
- `prior_history` populated incrementally per turn using `outcome_summary`, capped at 20 newest
- `_compute_recent_window` → `_recent_turn_count` (always returns 1)
- `load_recent_chronicle_turns` → `load_last_narration` (simplified)
- `chronicle_tail` on `TurnContext` becomes empty string (unused)
- Narrator receives 1 recent turn (down from 2-3)

## Implementation — Phase 2: Remove batch compactor, add reason field, strip dead config

### Context files to load
- `ccya/engine/compactor.py` (entire file — to be deleted)
- `ccya/engine/__init__.py` (maybe_compact re-export)
- `ccya/engine/turn.py` (maybe_compact import, call site already replaced in Phase 1)
- `ccya/models.py` (CompactorSanitizationAction, CompactorSanitizationResult, CompactorNpcMerge)
- `ccya/engine/config.py` (compact_every, compact_temperature, recent_turns_min, window_turns, chronicle_prefix_budget_tokens)
- `ccya/state/chronicle.py` (load_chronicle_tail — to be removed or simplified)
- `ccya/state/__init__.py` (re-exports)
- `ccya/config.yaml` (dead config keys to remove)
- `ccya/eval/compaction_signals.py` (to be deleted)
- `ccya/eval/judge.py` (compaction judge domain — to be gutted: lines 49, 109, 123, 177-235, 728, 1157)
- `ccya/eval/universal_asserts.py` (_assert_compactor_sanitization_nonzero at line 1057 — to be removed)
- `ccya/server/tv.py` (compaction event type handling, lines 376-393)
- `ccya/server/panels.py` (imports load_recent_chronicle_turns at line 12, calls at line 58)

### Detailed steps

#### Step 2.1 — Add `reason` field to CompactorSanitizationAction

**File:** `ccya/models.py`, class `CompactorSanitizationAction` (line 320)

**What:** Add `reason: str | None = None` field:

```python
class CompactorSanitizationAction(BaseModel):
    """A sanitization action with confidence level and reason."""
    id: str
    reason: str | None = None
    confidence: Literal["high", "medium", "low"] = "high"
```

No changes to `_coerce_sanitization_actions` — it already passes dict items through.

**Why:** Future sanitization work (batch or on-demand) needs reasons. Adding the field now ensures model compatibility.

**Validation:** `make check` passes. Existing code that constructs `CompactorSanitizationAction` without `reason` still works.

#### Step 2.2 — Delete batch compactor

**File:** `ccya/engine/compactor.py` — delete the entire file.

**File:** `ccya/prompts/compact_system.j2` — delete.

**File:** `ccya/prompts/compact_user.j2` — delete.

**File:** `ccya/engine/__init__.py` — remove `maybe_compact` from re-exports.

**File:** `ccya/eval/compaction_signals.py` — delete (it measures compactor behavior that no longer exists).

**File:** `ccya/eval/judge.py` — remove the `compaction` judge domain: remove `_is_compaction_turn()` (line 177), `_select_compaction_events()` (line 195), the `compaction_signals` parameter from dataclasses (lines 219, 243, 258, 270, 281, 452), and the `from ccya.eval.compaction_signals import render_compaction_section` / `compute_compaction_signals` imports (lines 728, 1157). Remove the `"compaction"` entry from the judge domain map (lines 49, 109, 123). Remove the compaction judge section in `_build_judge_prompt` (around line 727-729).

**File:** `ccya/eval/universal_asserts.py` — remove `_assert_compactor_sanitization_nonzero()` function (line 1057) and its call at line 1099 in `run_all_universal_asserts`.

**File:** `ccya/engine/turn.py` — remove `from ccya.engine.compactor import maybe_compact`. The `maybe_compact()` call block was already replaced in Phase 1 with outcome_summary append to prior_history. Also remove any references to `last_compacted_turn` since it's no longer tracked.

**Why:** The batch compactor is replaced entirely by incremental history bullets. No backward compatibility needed.

**Validation:** `make check` passes. `grep -r "maybe_compact\b" ccya/` returns no hits. `grep -r "compact_system\|compact_user" ccya/` returns no hits. `CompactorSanitizationResult` and `CompactorSanitizationAction` and `CompactorNpcMerge` in `models.py` are intentionally kept.

#### Step 2.3 — Remove dead config keys

**File:** `ccya/engine/config.py`

**What:** Remove from `EngineConfig`:
- `compact_every: int = 0`
- `compact_temperature: float = 0.1`
- `recent_turns_min: int = 2`
- `window_turns: int = 3`
- `chronicle_prefix_budget_tokens: int = 1500`

Remove from `build_engine_config` the corresponding lines that read these from the config dict. Remove `_validate_compactor_config`. Remove the validation checks for `compact_every < 0`, `recent_turns_min < 1`, `window_turns < 1`, `recent_turns_min > window_turns`, and `compact_every < recent_turns_min`.

**File:** `ccya/config.yaml` — remove lines for `compact_every`, `compact_temperature`, `recent_turns_min`, `window_turns`, `chronicle_prefix_budget_tokens`.

**Why:** These config keys are dead. No code references them after Phase 1 changes and compactor removal.

**Validation:** `make check` passes. `grep -r "compact_every\|compact_temperature\|recent_turns_min\|window_turns\|chronicle_prefix_budget" ccya/` returns no hits.

#### Step 2.4 — Simplify chronicle.py

**File:** `ccya/state/chronicle.py`

**What:** Remove `load_chronicle_tail` function entirely — it reads the COMPACTED section from chronicle.md, which new saves never write. The narrator no longer needs `chronicle_tail` since `prior_history` provides history context.

Remove `remove_last_chronicle_turn` if it's only used by the compactor (check references first).

Rename `load_recent_chronicle_turns` → `load_last_narration`. Simplify its signature: remove `min_turn_exclusive` parameter since it was only used for compaction boundary tracking. The function now just loads the last N turns from chronicle.md.

**File:** `ccya/state/__init__.py` — update re-exports: remove `load_chronicle_tail`, add `load_last_narration`.

**File:** `ccya/server/panels.py` — update import at line 12 and call at line 58 from `load_recent_chronicle_turns` to `load_last_narration`. Remove `min_turn_exclusive` from any call if present.

**Why:** Dead paths removed, remaining functions renamed for clarity.

**Validation:** `make check` passes. `grep -r "load_chronicle_tail\|load_recent_chronicle_turns\|min_turn_exclusive" ccya/` returns no hits.

#### Step 2.5 — Remove compaction event type from TV viewer

**File:** `ccya/server/tv.py` — remove the `compaction` event type handling (lines 376-393, includes the `continue` at line 393). Remove the `row_kind: "compaction"` branch from the event parsing loop.

**File:** `ccya/templates/_turn_viewer.html` — remove the `row_kind === 'compaction'` template block (lines 71-107). Remove the `onlyCompaction` filter checkbox (line 40). Remove all references to `compact_start`, `compact_end`, `bullets_count`, `bullets_preview`, `has_sanitization`, `sanitization` from the template data.

**Why:** Compaction events no longer exist. No replacement is needed (sanitization is out of scope for this plan).

**Validation:** TV viewer renders without errors on a running game. No compaction cards appear.

### Tests to write or update

No tests during refactor phase per AGENTS.md. Run `make check` at end of phase.

### REPOMAP updates required

- `ccya/engine/compactor.py` — deleted
- `ccya/engine/compactor.py::maybe_compact` — deleted
- `ccya/prompts/compact_system.j2` — deleted
- `ccya/prompts/compact_user.j2` — deleted
- `ccya/eval/compaction_signals.py` — deleted
- `ccya/eval/judge.py` — compaction judge domain removed (`_is_compaction_turn`, `_select_compaction_events`, `compaction_signals` parameter, compaction imports)
- `ccya/eval/universal_asserts.py` — `_assert_compactor_sanitization_nonzero` removed
- `ccya/models.py` — `CompactorSanitizationAction` gains `reason: str | None`
- `ccya/engine/config.py` — `compact_every`, `compact_temperature`, `recent_turns_min`, `window_turns`, `chronicle_prefix_budget_tokens` removed
- `ccya/state/chronicle.py` — `load_chronicle_tail` deleted, `load_recent_chronicle_turns` → `load_last_narration` (simplified signature)
- `ccya/server/tv.py` — compaction event type handling removed
- `ccya/server/panels.py` — `load_recent_chronicle_turns` → `load_last_narration`
- `ccya/templates/_turn_viewer.html` — compaction card and filter removed

## Implementation — Phase 3: Strip artifacts, rename functions, final cleanup

### Context files to load
- `ccya/server/tv.py` (remaining event rendering after compaction removal)
- `ccya/templates/_turn_viewer.html` (remaining turn display after compaction removal)
- `ccya/templates/index.html` (outcome_summary display)
- `ccya/engine/turn.py` (outcome_summary append to prior_history, TurnContext, remaining references)
- `ccya/engine/narrate.py` (prior_history rendering, recent_turns usage)
- `ccya/prompts/narrate_user.j2` (section headers)
- `ccya/prompts/context.py` (NarratorBoundary, StorytellerBoundary — update recent_turns docs if needed)
- `scripts/debug/ev.py` (compact command and compaction display logic — to be removed)
- `docs/repomap.md` (module boundaries and public APIs — to be updated)

### Detailed steps

#### Step 3.1 — Strip `[T{n}]` prefix from history bullets in player-facing display

**File:** `ccya/templates/_turn_viewer.html`

**What:** Where `prior_history` content is displayed to the player, strip the `- [T{n}] ` prefix and show only the prose text. Add a small Jinja filter or template helper that renders each bullet as: `Turn {n}: {prose_without_prefix}` or just `{prose_without_prefix}`.

The `- [T{n}]` format stays in `prior_history` for narrator context but is stripped when rendering in any player-facing UI.

**Why:** Player-facing UI shows pure prose, not internal artifacts.

**Validation:** Inspect the TV viewer and confirm history bullets display as readable sentences without `- [T{n}]` prefixes.

#### Step 3.2 — Rename remaining functions for clarity

**File:** `ccya/engine/turn.py`

**What:** Rename any remaining compactor-adjacent functions:
- `_compute_recent_window` was renamed to `_recent_turn_count` in Phase 1. Confirm this is done.
- Any remaining `compact*` or `compaction*` references in variable names, log messages, or comments should be updated to reflect the new incremental history approach.

**File:** `ccya/state/chronicle.py`

**What:** Confirm `load_last_narration` (renamed from `load_recent_chronicle_turns` in Phase 2) has a clean signature and no dead parameters.

**Why:** Names should reflect what code does, not what it used to do.

**Validation:** `grep -r "compact\|recent_window\|chronicle_tail" ccya/` returns no hits (except in comments or strings that reference the old behavior for context).

#### Step 3.3 — Remove `last_compacted_turn` from state shape

**File:** `ccya/state/io.py` (default state shape), `ccya/engine/turn.py` (any remaining references)

**What:** Remove `last_compacted_turn` from the default state shape in `io.py`. Remove any code in `turn.py` that reads or writes `state["meta"]["last_compacted_turn"]`. The field is no longer needed since there's no compactor.

**Why:** Dead state field. No backward compatibility needed.

**Validation:** `make check` passes. `grep -r "last_compacted_turn" ccya/` returns no hits.

#### Step 3.4 — Remove `chronicle_tail` from `TurnContext`

**File:** `ccya/engine/turn.py`

**What:** Remove the `chronicle_tail` field from `TurnContext` dataclass (line 78). Remove all places where it's set or passed. The narrator no longer needs it — `prior_history` provides history context.

Remove the call to `load_chronicle_tail` in the turn pipeline (was removed in Phase 1 Step 1.5, confirm it's gone).

Update `narrate.py` — remove the `chronicle_tail` parameter from `_narrate_messages` and the template context dict where it was passed.

**Why:** Dead field. No code sets it, no template uses it.

**Validation:** `make check` passes. `grep -r "chronicle_tail" ccya/` returns no hits.

#### Step 3.5 — Remove `ev.py` compaction command and update repomap

**File:** `scripts/debug/ev.py`

**What:** Remove the `compact` command and all compaction-related display logic (compaction event parsing, sanitization display, compact_start/compact_end fields). The `cmd_compact` function and its subcommand dispatch can be removed entirely.

**File:** `docs/repomap.md`

**What:** Update the repomap to reflect all changes:
- `ccya/engine/compactor.py` — deleted, remove from module index
- `ccya/engine/turn.py` — update to reflect `_recent_turn_count` (was `_compute_recent_window`), no `maybe_compact`, no `last_compacted_turn`, `outcome_summary` append to `prior_history`
- Remove `maybe_compact` from public APIs section
- Remove compaction-related config fields from EngineConfig description
- Note `outcome_summary` is now 3rd-person durable summary in cross-module contracts

**Why:** Repomap must stay accurate to source. Ev.py command must not reference deleted code.

**Validation:** `grep -r "compact\b" scripts/debug/ev.py ccya/ --include="*.py" | grep -v "CompactorSanitiz" | grep -v "# compact"` returns no hits except in comments.

### Tests to write or update

No tests during refactor phase per AGENTS.md. Run `make check` at end of phase only.

### REPOMAP updates required

- `ccya/engine/turn.py` — `TurnContext.chronicle_tail` field removed, `last_compacted_turn` state key removed
- `ccya/engine/narrate.py` — `chronicle_tail` parameter removed from `_narrate_messages`
- `ccya/state/io.py` — `last_compacted_turn` removed from default state shape
- `scripts/debug/ev.py` — `compact` command and compaction display logic removed
- `docs/repomap.md` — updated to reflect all Phase 1-3 changes (compactor removed, config keys removed, function renames, `outcome_summary` repurposed as 3rd-person durable summary, pipeline changes)

## Final validation

After all phases: `make check` passes. Run a game for 20+ turns and verify:
1. `state["meta"]["prior_history"]` grows by one bullet per turn, capped at 20, oldest dropped
2. Narrator prompt shows prior_history bullets and exactly 1 recent turn
3. No compaction events in events.jsonl
4. No `compact_every`, `recent_turns_min`, `window_turns`, `chronicle_prefix_budget_tokens`, `last_compacted_turn` in config or state
5. TV viewer renders without compaction cards
6. `outcome_summary` is present in storyteller JSON output, third-person, uses PC name
7. `grep -r "maybe_compact\|load_chronicle_tail\|compact_every\|recent_turns_min\|last_compacted_turn\|chronicle_tail" ccya/` returns no hits
8. `grep -r "compaction_signals" ccya/` returns no hits (eval file deleted)
9. `scripts/debug/ev.py compact TURN STREAM` no longer works (command removed)
10. `docs/repomap.md` reflects all changes (no compactor module, no deleted functions)

Additional cleanup (not in source but may need updating):
- `ccya/tests/conftest.py` line 186: `"prior_history": []` and `"recent_events": []` default state — remove `recent_events` if it's dead. `prior_history` stays.
- `ccya/tests/test_integration.py` line 79: `"recent_events_add"` — remove if dead.
- `ccya/tests/test_render.py`: references to `recent_events` — remove if dead. References to `prior_history` stay.