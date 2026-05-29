# Phase A: Delete recent_events System

## Status
`completed`

## Phases

1 phase covering structural removal of `recent_events`: model classes, state delta fields, ring buffer logic, compaction aspect, prompt sections, UI rendering, eval asserters, config key. No migration — old state files fail on load intentionally.

## Issue

The `recent_events` system is a mutable event log stored in `state.scene.recent_events`, managed by the storyteller LLM via `StorytellerResult.recent_events_add/update/remove`. It serves as narrative context fed back to the storyteller each turn, but it has multiple problems: (1) it consumes prompt tokens on every storytelling call without proportional value — world_state is a better source of persistent facts; (2) it requires complex ring buffer logic in `apply_delta` with eviction tracking (`recent_events_evicted`) that adds code surface area and UI toast rendering complexity for marginal benefit; (3) the compactor has a dedicated aspect (`recent_events_compact`) to merge similar events, adding another LLM output field the storyteller must produce. The world-state-history-redesign design replaces this with a mutable tiered `world_state` structure that provides better-structured persistent facts without ring buffer management overhead.

## Solution

Delete all `recent_events` infrastructure: model classes (`RecentEvent`, `RecentEventUpdate`, `CompactorRecentEventCompact`), state delta fields on `StateDelta` and `StorytellerResult`, the ring buffer logic in `apply_delta`, compaction aspect, prompt sections in storytell/compact templates, UI rendering of evicted toast and event diffs, eval asserters (`check_recent_events_turn_stamped`, `check_recent_events_ring_size`), config key (`recent_events_max`). Change `apply_delta` return from `(dict, bool)` to just `dict`. Remove the inventory durability gate entirely — it checked `delta.recent_events_add OR delta.actions` as a loot-gain signal and had more false positives than true positives. No replacement needed.

Expected outcome: ~20 files cleaned up with mechanical deletions, no new code surface area added, inventory durability gate removed entirely (false-positive prone and no longer needed), storyteller prompt freed from managing event log state (saves tokens), compactor simplified by one less output field to produce.

## Firm decisions

1. No migration — old state files fail on load intentionally
2. Inventory durability gate removed entirely — the check for `delta.recent_events_add OR delta.actions` as loot-gain signal is deleted with no replacement. It had more false positives than true positives and is not needed.
3. `apply_delta` return type changes from `(dict, bool)` to just `dict` — all unpacking sites updated simultaneously
4. `load_recent_events()` function in `state/chronicle.py` is RENAMED to `load_recent_turns()` — it reads events.jsonl turn logs (not scene.recent_events). All imports and call sites updated to match.

## Non-goals

- Do not add world_state tiered structure (that's Phase B)
- Do not fix key-branch black hole at turn.py:1275 (separate phase)
- Do not update prompt alignment on new structure (Phase E)
- Do not write tests — per AGENTS.md, tests are temporarily removed during refactor

## Risks, Ambiguities, and Blockers

**Risk:** `seed.py` lines 40-41 iterate over `envelope.seed_state.scene.recent_events`. If a seed YAML includes recent_events (common in static packs), this code will crash after deletion. Fix: remove the iteration loop entirely — seeds with old-format scene data simply won't have recent_events anymore, which is acceptable since no migration is needed.

**Risk:** `state/io.py:_convert_seed_recent_events()` converts string-format seed events to dicts. After removal, this function becomes dead code. Remove it and its call from `init_save_dir()`.

**Ambiguity:** `ev.py` search command at line 861 checks for `"recent_events"` as a key that triggers `_render_scene_section(state)`. Removing "recent_events" from the list means scene section only renders if tags/tagline/other keys exist. This is acceptable — removing one of several trigger keys doesn't break rendering, it just removes a redundant check.

**Ambiguity:** `universal_asserts.py` lines 946 and 952 reference both asserters in the main checker list. Must remove both function definitions AND their invocations from the checklist at module bottom (~line ~930-970).

## Implementation — Phase A: Delete recent_events system

### Context files to load
1. `ccya/models.py` (lines 216-451)
2. `ccya/state/delta_builder.py` (entire file, focus on apply_delta at lines 123-362)
3. `ccya/state/delta.py` (entire file)
4. `ccya/engine/turn.py` (lines 58, 128-129, 732, 965-966, 1203-1216, 1536-1543, 1635-1655)
5. `ccya/engine/extraction.py` (lines 249, 267, 548-556, 605-607, 639, 653-655)
6. `ccya/engine/compactor.py` (lines 112-155, 233, 242)
7. `ccya/engine/config.py` (lines 68, 152)
8. `ccya/engine/changes.py` (lines 33-46, 206-220)
9. `ccya/state/io.py` (lines 86, 133-157)
10. `ccya/server/routes.py` (lines 28, 189, 208)
11. `ccya/eval/universal_asserts.py` (lines 23-56, 427-449, ~930-970 checklist)
12. `ccya/prompts/storytell_system.j2`, `storytell_user.j2`, `compact_system.j2`, `compact_user.j2`
13. `ccya/templates/index.html` (lines 1400, 1434), `_turn_viewer.html` (line 100-101), `_state_right.html` (line 2)
14. `scripts/debug/ev.py` (lines 50, 861)
15. `ccya/prompts/context.py` (lines 269, 281)
16. `ccya/pack.py` (line 65)

### Detailed steps

#### Step A.1 — Delete model classes and state delta fields

**File:** `ccya/models.py`

**What:** Remove three Pydantic models: `RecentEvent` (lines 216-219), `RecentEventUpdate` (lines 222-224), `CompactorRecentEventCompact` (lines 316-320). Remove six state delta/result fields: from `StateDelta`, remove `recent_events_add`, `recent_events_update`, `recent_events_remove` (lines 248-250); from `StorytellerResult`, remove the same three fields (lines 386-388); from `CompactorSanitizationResult`, remove `recent_events_compact: list[CompactorRecentEventCompact]` field (line 346).

**Why:** These models and fields are entirely consumed by the recent_events system. No other code references them after this phase — they exist only to carry storyteller output through StateDelta/StorytellerResult into apply_delta, which we're removing.

**Validation:** `rg "RecentEvent|recent_events_add|recent_events_update|recent_events_remove" ccya/models.py` should return zero matches (except any unrelated uses of the word).

#### Step A.2 — Change apply_delta return type and remove ring buffer logic

**File:** `ccya/state/delta_builder.py`

**What:** Three changes:
1. Remove `recent_events_max: int = 20, current_turn_no: int | None = None` parameters from `apply_delta()` signature (line 124). New signature: `def apply_delta(state: dict[str, Any], delta: StateDelta) -> dict[str, Any]:`.
2. Remove the entire recent_events ring buffer section (~lines 291-325): existing events loading/cleaning, remove/update/add processing from delta fields (which no longer exist), sorting by turn, eviction flag computation, and `scene["recent_events"] = ...` assignment.
3. Change return statement at line 362: change `return state, recent_events_evicted` to `return state`.

**Why:** The ring buffer logic is entirely dedicated to managing scene.recent_events as a FIFO capped list. Without the data source (delta fields) and without the destination (scene.recent_events), this code has no purpose. Removing it also eliminates the need for `recent_events_max` parameter propagation across multiple call sites.

**Why:** The inventory durability gate at lines 176-186 checks `delta.recent_events_add or []`. Since that field is deleted, change to check only `delta.actions or []`. This maintains the same safety guarantee — new items must have loot context in either recent events OR actions; after removal, actions-only path preserves protection against accidental item generation.

**Why:** Changing return type from `(dict, bool)` to just `dict` eliminates the evicted flag entirely. No code needs it anymore since there's no ring buffer to evict from and no toast rendering for eviction warnings (that UI is deleted in later steps).

**Validation:** `rg "recent_events_evicted" ccya/state/delta_builder.py` should return zero matches. `python -c "from ccya.state.delta import apply_delta; print(apply_delta.__annotations__)"` should show no tuple return type annotation.

#### Step A.3 — Update state/delta.py wrapper to match new signature

**File:** `ccya/state/delta.py`

**What:** Three changes:
1. Remove `recent_events_max: int = 20, current_turn_no: int | None = None` parameters from `apply_delta()` function signature (line 31). New signature: `def apply_delta(state: dict[str, Any], delta: Any) -> dict[str, Any]:`.
2. Update the internal call at line 36 to not pass those params: change `_impl(state, delta, recent_events_max=recent_events_max, current_turn_no=current_turn_no)` to `_impl(state, delta)`.
3. Change return statement at line 37 from `return result, evicted` to `return result`.

**Why:** Thin wrapper must match the implementation signature change in step A.2. The wrapper delegates to delta_builder.apply_delta which no longer accepts or returns those values.

**Validation:** `rg "recent_events_max|evicted" ccya/state/delta.py` should return zero matches (except comments).

#### Step A.4 — Update turn.py: remove local vars, fix apply_delta call site and unpacking, update TurnResult constructor

**File:** `ccya/engine/turn.py`

**What:** Four changes:
1. Rename the import of `load_recent_events` at line 58 to `load_recent_turns` with matching alias. This function reads events.jsonl turn logs — it's NOT scene.recent_events data and is still called at turn.py:732 (`_prev_outcome = load_recent_turns(ctx.save_dir, 1)`) for ruling outcome context. Rename for clarity — the old name is misleading. Update the call site at line 732 to match.
2. Remove local variable declarations at lines 965-966: `recent_events: list[dict[str, Any]] = []` and `recent_events_evicted: bool = False`.
3. Update apply_delta call site at line 1203: change unpacking from `state, recent_events_evicted = apply_delta(...)` to just `state = apply_delta(...)`. Remove the three arguments `recent_events_max=config.recent_events_max` and `current_turn_no=turn_no` since step A.2 removed them from apply_delta signature.
4. Remove line 1216: `recent_events = list(delta.recent_events_add)` — this field no longer exists on StateDelta after step A.1.
5. Update TurnResult constructor at lines 1530-1545: remove arguments `recent_events=recent_events` (line 1536) and `recent_events_evicted=recent_events_evicted` (line 1543).

**Why:** All these references are to the deleted data structures. The apply_delta call site must match the new signature from step A.2-3. TurnResult no longer carries evicted flag or recent events list since neither exists anymore. `load_recent_events()` is renamed to `load_recent_turns()` since it reads JSONL event logs (not scene.recent_events state field) — the old name was misleading.

**Validation:** `rg "recent_events_evicted|\.recent_events_add" ccya/engine/turn.py` should return zero matches (except comments).

#### Step A.5 — Update turn.py: fix inventory durability gate in _validate()

**File:** `ccya/engine/turn.py`

**What:** In `_validate()` function (~lines 1639-1654), change the loot context check from checking both `delta.recent_events_add or []` AND `delta.actions or []` to only `delta.actions or []`. Remove lines 1640-1644 (the loop over recent_events_add). Update the rejection reason message at line 1654 from "no loot gain context detected in recent_events or actions" to "no loot gain context detected in actions".

**Why:** After step A.1, `delta.recent_events_add` no longer exists on StateDelta. The durability gate must still prevent accidental item generation — the actions-only path provides this guarantee since storyteller is required to emit 4 actions per turn and at least one should reference any new items gained. **Behavioral note:** items added via recent_events (before deletion) will no longer pass durability gate after this step; only items with loot context in actions will be accepted — this is intentional and consistent with the design goal of removing recent_events as a data source.

**Validation:** `rg "recent_events.*durability\|durability.*recent_event" ccya/engine/turn.py` should return zero matches (except comments).

#### Step A.6 — Update extraction.py: remove recent_events from storytell_user.j2 context, fix StateDelta construction, update logging

**File:** `ccya/engine/extraction.py`

**What:** Five changes (NOTE: step A.8 must complete first to delete model fields before these constructor calls are valid):
1. Remove line 249: `recent_events = list(scene.get("recent_events") or [])`.
2. Remove `"recent_events": recent_events,` from the storytell_user.j2 render context at line 267 (within `_run_storytell_stream()`).
3. Update storytelling event building (~lines 548-556): remove the entire block that overwrites turn stamps on `storytell_result.recent_events_add`. Since step A.1 removes this field from StorytellerResult, this stamping code is dead — delete it entirely.
4. Remove three references to `recent_events_add` in logging: line 605 (condition check), line 607 (`events_add=%d` format arg), and line 639 (`events_add=%d` log message). Update the remaining log calls to remove these arguments.
5. Remove from StateDelta construction (~lines 653-655): delete arguments `recent_events_add=storytell_result.recent_events_add`, `recent_events_update=...`, `recent_events_remove=...`. These fields no longer exist on StorytellerResult after step A.1, and won't exist on StateDelta anymore either (step A.8).

**Validation:** `rg "recent_event" ccya/engine/extraction.py` should return zero matches (except comments).

#### Step A.7 — Update compactor.py: remove recent_events_compact handling from maybe_compact(), update compact_user.j2 rendering, fix logging

**File:** `ccya/engine/compactor.py`

**What:** Three changes:
1. Remove the entire recent_events_compact replacement block (~lines 119-135): delete lines that check `sanitization.recent_events_compact`, replace `scene["recent_events"]`, and log compaction counts. The sanitization step itself (`_apply_sanitization(state, sanitization)`) stays — it handles NPC merges and inventory/condition removals which are separate concerns.
2. Remove line 154: `"recent_events_compact_count": len(sanitization.recent_events_compact or []),` from the `san_payload` dict construction. This field is no longer meaningful since compactor won't produce recent_events_compact anymore (step A.1 removes it from CompactorSanitizationResult).
3. Update post-compaction logging at lines 140-141: remove `recent_events=%d` and its corresponding argument from the format string and arguments list.

**Why:** The compactor's recent_events_compact aspect is entirely dedicated to merging similar events in scene.recent_events — a feature that no longer exists after step A.1 removes CompactorRecentEventCompact model class. NPC merges, inventory removals, pressure removals, and condition removals are independent sanitization concerns handled by `_apply_sanitization()` which stays intact.

**Why:** Remove `recent_events=recent_events` from compact_user.j2 render call at line 242 (within `_build_compact_messages`). The template no longer needs this variable since step A.1 removes the model class and compactor won't produce recent_events_compact anymore.

**Validation:** `rg "recent_event" ccya/engine/compactor.py` should return zero matches (except comments).

#### Step A.8 — Remove model fields and config key: StateDelta, StorytellerResult, CompactorSanitizationResult.recent_events_compact, EngineConfig.recent_events_max

**File:** `ccya/models.py`, `ccya/engine/config.py`

**What:** Five changes across two files (NOTE: this step must complete BEFORE step A.6 — model fields must be deleted before constructor calls that reference them are valid):
1. Remove three Pydantic models from `models.py`: `RecentEvent` (lines 216-219), `RecentEventUpdate` (lines 222-224), `CompactorRecentEventCompact` (lines 316-320).
2. From `StateDelta` in `models.py`, remove six fields: `recent_events_add`, `recent_events_update`, `recent_events_remove` (~lines 248-250) and `recent_events=...` (~line ~317-320 — the three typed fields alongside recent_events).
3. From `StorytellerResult` in `models.py`, remove the same three fields: `recent_events_add`, `recent_events_update`, `recent_events_remove` (lines 386-388).
4. From `CompactorSanitizationResult` in `models.py`, remove `recent_events_compact: list[CompactorRecentEventCompact]` field (line 346).
5. Remove from `config.py`: field `recent_events_max: int = 20` from EngineConfig dataclass (line 68), and the loading line at ~line 152: `recent_events_max=int(game.get("recent_events_max", 20)),`.

**Why:** These models and fields are entirely consumed by the recent_events system. No other code references them after this phase — they exist only to carry storyteller output through StateDelta/StorytellerResult into apply_delta, which we're removing.

**Validation:** `rg "recent_event.*max\|recent_events_max" ccya/engine/config.py` should return zero matches (except comments).

#### Step A.9 — Update changes.py: remove recent_events from diff/changes computation

**File:** `ccya/engine/changes.py`

**What:** Four changes within the `compute_changes()` function (~lines 187-230):
1. Remove the three loops at lines 33-46 that iterate over `applied.get("recent_events_add")`, `applied.get("recent_events_remove")`, and `applied.get("recent_events_update")`. These produce emoji diff lines (+/-/~/ prefix) for UI toast display — they're dead code since step A.1 removes these fields from StateDelta model_dump output.
2. Remove the entire recent_events fact computation block (~lines 206-220): pre/post event ID comparison, added/removed/updated fact generation (`{"kind": "added"/"removed"/"updated", ...}`). This feeds into `changes` dict used by UI modal — no longer needed since step A.1 removes these fields from state delta output.
3. Remove the `"recent"` entries from the returned changes list/dict that feed UI toast notifications (the keys produced by loops at lines 33-46). These are dead code after step A.1 and will produce empty/no-op toasts if left in place.
4. Ensure no orphaned references remain — verify `applied.get("recent_events_*")` calls return zero matches via validation grep.

**Why:** changes.py computes human-readable diff lines and structured change facts for the UI toast/modal display based on what apply_delta returns (via model_dump). Since step A.1 removes recent_events_add/update/remove from StateDelta, `applied.get("recent_events_*")` will always return None/empty after this phase — these loops produce no output and are dead code.

**Validation:** `rg "recent_event" ccya/engine/changes.py` should return zero matches (except comments).

#### Step A.10 — Update state/io.py: remove recent_events from default state, delete _convert_seed_recent_events function

**File:** `ccya/state/io.py`

**What:** Three changes:
1. Remove `"recent_events": [],` from `_default_state()` scene section at line 86 (within the "scene" dict).
2. Delete the entire `_convert_seed_recent_events()` function (~lines 133-149) — it converts string-format seed events to dicts, which is dead code since step A.1 removes RecentEvent model and no code reads scene.recent_events anymore.
3. Remove the call ` _convert_seed_recent_events(seed)` from `init_save_dir()` at line 154.

**Why:** Default state shape must match what the engine expects after deletion — having a dead field in default state is acceptable but inconsistent with "one source of truth" principle since no code reads it anymore. The seed conversion function is entirely dedicated to preparing scene.recent_events data which no longer exists.

**Validation:** `rg "recent_event.*\[\]|_convert_seed_recent_event" ccya/state/io.py` should return zero matches (except comments).

#### Step A.11 — Update routes.py: remove recent_events_evicted from JSON response

**File:** `ccya/server/routes.py`

**What:** Three changes:
1. Rename the import of `load_recent_events` at line 28 to `load_recent_turns`. Update the call site at line 208: `last_events = load_recent_turns(_app_mod.SAVE_DIR, 1)`.
2. The function still reads events.jsonl turn logs for the "remove-last-turn" feature — it's not scene.recent_events data. Rename for clarity.
3. Remove `"recent_events_evicted": result.recent_events_evicted,` from JSON response dict at line 189. This field no longer exists on TurnResult after step A.6.

**Why:** The import must be renamed for clarity — `load_recent_events` is misleading since recent_events no longer exists. The function reads JSONL event logs, not scene.recent_events state field, so `load_recent_turns` is accurate. The evicted flag is removed from the response dict since TurnResult no longer carries it after step A.6.

**Validation:** `rg "load_recent_turns" ccya/server/routes.py` should show exactly one match (the renamed call site). `rg "load_recent_events" ccya/server/routes.py` should return zero matches (except comments after the rename).

#### Step A.12 — Remove eval asserters: check_recent_events_turn_stamped, check_recent_events_ring_size

**File:** `ccya/eval/universal_asserts.py`

**What:** Three changes:
1. Delete the entire `check_recent_events_turn_stamped()` function (~lines 23-56).
2. Delete the entire `check_recent_events_ring_size()` function (~lines 427-449).
3. Remove invocations of both asserters from the checker list at module bottom (~lines ~930-970): remove `"assertion": "universal.recent_events_add.turn_stamped"` entry and `"assertion": "universal.recent_events.ring_bounded"` entry (and their function calls).

**Why:** These asserters validate properties of recent_events data that no longer exists: turn stamping on add entries, ring buffer size bounds. They would always pass with empty/missing data after this phase — dead code per AGENTS.md rules.

**Validation:** `rg "recent_event" ccya/eval/universal_asserts.py` should return zero matches (except comments).

#### Step A.13 — Remove recent_events from prompt templates: storytell_system.j2, storytell_user.j2, compact_system.j2, compact_user.j2

**File:** `ccya/prompts/storytell_system.j2`, `storytell_user.j2`, `compact_system.j2`, `compact_user.j2`

**What:** Four changes across four files:
1. **storytell_system.j2**: Remove lines 7-9 (JSON schema example showing empty arrays for recent_events_add/update/remove). Remove the entire instruction paragraph at line 44 about emitting new events with turn stamps and IDs. Remove lines 46, 48, 50 which describe update/remove semantics.
2. **storytell_user.j2**: Remove lines 22-24 (the `{% if recent_events %}` section header and event listing loop). This removes the "Recent events" context block from storyteller prompt — world_state will replace this in Phase B as a better persistent fact source.
3. **compact_system.j2**: Remove line 58 (`**recent_events_compact**` bold instruction), lines 74-80 (JSON example showing recent_events_compact field and schema). Remove the entire section at lines 102, 129-132 describing how to produce compacted events.
4. **compact_user.j2**: Remove lines 57-58 (the `{% if recent_events %}` loop rendering event list for compactor prompt).

**Why:** These templates are consumed by LLM calls. Removing dead fields from JSON schema examples prevents the storyteller/compactor from producing output that no code can consume. The storytelling prompt section showing recent events as context is removed since step A.6 stops passing it to this template — keeping a rendered-but-empty section wastes tokens on a header with no content below it.

**Validation:** `rg "recent_event" ccya/prompts/*.j2` should return zero matches (except comments).

#### Step A.14 — Remove recent_events from UI templates: index.html, _turn_viewer.html, _state_right.html

**File:** `ccya/templates/index.html`, `_turn_viewer.html`, `_state_right.html`

**What:** Three changes across three files:
1. **index.html**: Remove the evicted toast rendering at line 1400 (`if (result.recent_events_evicted) {`). The else branch that renders `_buildTurnChanges()` must be preserved — it handles general state change display and is not specific to recent events. Do NOT remove the entire if/else block, only the `recent_events_evicted` condition check within it.
2. **_turn_viewer.html**: Remove lines 100-101: the `<template x-if="t.sanitization.recent_events_compact_count">` div showing "Recent events compacted to:" count in compaction event rows.
3. **_state_right.html**: Delete the entire file content at line 2 (`{% set _recent = state.scene.recent_events or [] %}`). This template renders recent events on the state sidebar — since step A.1 removes scene.recent_events from default state and no code populates it anymore, this is dead rendering code.

**Why:** UI templates render data that flows through TurnResult JSON responses (index.html) and state YAML panels (_state_right.html). The evicted toast was a UX feature showing when events were pruned — since step A.3 removes the evicted flag entirely, there's no data to display. Compaction count in turn viewer is dead since step A.7 stops producing recent_events_compact_count. Sidebar event rendering is dead since scene.recent_events is removed from state shape (step A.10).

**Validation:** `rg "recent_event" ccya/templates/*.html` should return zero matches (except comments). Note: `_buildTurnChanges()` function in index.html must remain intact — it handles general change display unrelated to recent events specifically.

#### Step A.15 — Update search/debug tooling: ev.py section markers and scene rendering trigger

**File:** `scripts/debug/ev.py`

**What:** Three changes (NOTE: verify no orphaned `_render_recent_events()` function exists after these edits):
1. Remove `"recent_events": r"^## recent_events",` from SECTION_MARKERS dict at line 50. This removes the "recent_events" search command that extracts this section from storytell prompt output in events.jsonl.
2. Update scene rendering trigger at line 861: change `("tags", "tagline", "recently_left", "recent_events")` to `("tags", "tagline", "recently_left")`. Removing one of several keys that determine whether `_render_scene_section(state)` is called — this doesn't break anything since scene section renders if ANY of the listed keys exist.
3. Search for and delete any orphaned `_render_recent_events()` function definition in ev.py (if it exists as a standalone helper). Verify with `rg "_render_recent_event" scripts/debug/ev.py` that zero matches remain after this step.

**Why:** ev.py search commands extract sections from storytell prompt output in events.jsonl for debugging. Without recent_events in state, there's no such section to extract anymore. The scene rendering trigger change removes a redundant key check — removing one condition from an OR-list doesn't affect functionality since other keys (tags/tagline) still exist as triggers.

**Validation:** `rg "recent_event" scripts/debug/ev.py` should return zero matches (except comments).

#### Step A.16 — Update prompt context boundary: StorytellerBoundary model in context.py

**File:** `ccya/prompts/context.py`

**What:** Two changes:
1. Remove `"all_threads/recent_events/world_state/intent/..."` from the docstring comment at line 269 (update to remove "recent_events" from the list of top-level variables).
2. Remove field `recent_events: list[dict[str, Any] | str]` and its comment at line 281 from StorytellerBoundary model.

**Why:** This Pydantic model defines the type boundary for storytell_user.j2 context data. Since step A.6 stops passing recent_events to this template, the field is dead — per AGENTS.md clean code rules, no dead fields in models allowed.

**Validation:** `rg "recent_event" ccya/prompts/context.py` should return zero matches (except comments).

#### Step A.17 — Remove from pack.py: SceneModel.recent_events field

**File:** `ccya/pack.py`

**What:** Remove line 65: `recent_events: list[str] = Field(default_factory=list)` from the SceneModel dataclass/Pydantic model.

**Why:** This is a static scene definition model used by packs (seed state). Since step A.1 removes recent_events from default state shape and no code reads it anymore, this field on pack-defined scenes is dead code.

**Validation:** `rg "recent_event" ccya/pack.py` should return zero matches (except comments).

#### Step A.18 — Remove seed processing: strip_non_ascii loop over scene.recent_events in seed.py

**File:** `ccya/engine/seed.py`

**What:** Delete lines 40-41: the for-loop that iterates over `envelope.seed_state.scene.recent_events` and applies `_strip_non_ascii()` to each event string. This entire loop block is dedicated to cleaning non-ASCII characters in seed-generated recent events — dead code since step A.1 removes this data source entirely.

**Why:** After step A.1, `seed_state.scene.recent_events` no longer exists as a field on the model (it's removed from default state at step A.10). Any static pack seeds that still have scene.recent_events in their YAML will simply ignore it — Pydantic/YAML parsing won't crash since extra fields are ignored by default, and this loop was just doing character cleanup which is no longer needed for a field nobody reads anymore.

**Validation:** `rg "recent_event" ccya/engine/seed.py` should return zero matches (except comments).

#### Step A.19 — Remove from compaction_signals.py: recent_events size tracking in eval metrics

**File:** `ccya/eval/compaction_signals.py`

**What:** Three changes:
1. Remove line 99: `prev_recent_events_size = 0`.
2. Update lines 108-124: remove the block that reads scene.recent_events, computes size before/after compaction, and stores it in event dict as "recent_events_size_before"/"recent_events_size_after".
3. Remove line 159: `parts.append(f"- recent_events: {ev['recent_events_size_before']} → {ev['recent_events_size_after']} entries\n\n")` from the summary formatting section.

**Why:** These lines track compaction impact on recent_events count — a metric that no longer exists after step A.1 removes scene.recent_events entirely. The rest of compaction_signals.py (NPC merges, inventory removals) is independent and stays intact.

**Validation:** `rg "recent_event" ccya/eval/compaction_signals.py` should return zero matches (except comments).

### Tests to write or update
None — per AGENTS.md: tests are temporarily removed during refactor. Do not write or reference tests until this phase is complete.

### REPOMAP updates required
1. `docs/repomap.md`: Remove "recent_events" from TurnResult description at line 54 (change `TurnResult dataclass — returned from run_turn(): turn, trace_id, narrative, state_delta, applied, rejected, actions, scene_tags, recent_events, diff, changes, metrics, errors, ruling, outcome_summary, recent_events_evicted, ts` to remove "recent_events" and "recent_events_evicted").
2. `docs/repomap.md`: Remove "apply_delta() → (dict, bool)" from state section at line 68 — change to "apply_delta(state, delta) → dict".
3. `docs/repomap.md`: Update state shape table at lines 179-230: remove `"recent_events": list[Event]` from scene section (~line 223).
4. `docs/repomap.md`: Remove "recent_events" from extraction field routing description at line 153 (StorytellerResult entry — change to not mention recent_events_add/update/remove, keep thread_advance/thread_resolve/thread_add/actions/outcome_summary/gm_beat).
