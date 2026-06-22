# Reduce Noisy Arc/Thread Updates

## Purpose

Reduce LLM-emitted thread updates that add no new information, prevent unbounded thread accumulation, and give storytell visibility into resolved arcs and structured progress kinds.

## Problem Statement

The LLM emits thread_updates on most turns — often with progress text that restates the narration or adds no new trajectory information. Each progress entry is appended to an unbounded list and rendered in every future prompt, compounding the noise. There is no cost signal or enforcement mechanism. Additionally, threads accumulate without cleanup: `last_updated_turn` was never persisted (a bug), so the LLM cannot see how stale a thread is. There is no cap on active threads and no auto-demotion for untouched threads.

## Constraints

- Must handle live state migration: old saves have `progress: list[str]`, new saves have `progress: list[ProgressEntry]` with `{text, kind}`.
- Existing prompt templates must remain functional after changes — update rendering as needed.
- Backward compatibility policy: none required (per AGENTS.md), but migration of existing state files via validators is acceptable to avoid silent data loss.

## Non-goals

- Band-aligned gating (ruling band based thread update blocking) — rejected as "too risky."
- Minimum interval enforcement — rejected.
- Prompt truncation of progress entries — rejected as bandaid.
- Full list rewrite for progress — rejected; fuzzy dedup preferred instead.
- Changes to test infrastructure (tests are suspended during refactor per AGENTS.md).

## Solution

Five changes: (1) Add structured `ProgressEntry` model with kind field to replace `list[str]` in thread progress; (2) Add config options for stale threshold and thread cap; (3) Implement content dedup via fuzzy matching in `_apply_thread_updates`, auto-latent on staleness, and thread cap eviction; (4) Pass `resolved_arcs` to storytell context; (5) Tighten prompt instructions with explicit word limits, negative reinforcement, and rarity emphasis. Fix the `last_updated_turn` persistence bug (already done).

## Firm decisions

1. `ProgressEntry` model: `{kind: "advancement"|"setback"|"shift", text: str}`. Default kind on migration is `"advancement"`.
2. Content dedup: reject a progress update if token overlap with the last entry in that thread's progress list is ≥50% (using `difflib.SequenceMatcher`). Log warning, skip the progress append, still apply other thread_update fields.
3. Auto-latent: if a thread's `last_updated_turn` is set and `(current_turn - last_updated_turn) >= thread_stale_threshold` (default 3), set `active: false`. Applied after all LLM-emitted updates for the current turn are processed.
4. Thread cap: max `thread_max_active` (default 5) active threads. If after a `thread_add` the count exceeds the cap, evict the active thread with the oldest `last_updated_turn` (set to `active: false`). If multiple untracked threads exist (no `last_updated_turn`), evict the first one.
5. Resolved arcs: pass `resolved_arcs` (TTL-filtered) into `_storytell_messages` context.
6. Prompt tightening:
   - Thread summaries: 4–7 words, a broad situation bucket (e.g. "City council conspiracy"), not an objective or specific event.
   - Progress entries: one sentence explaining HOW the thread's trajectory changed beyond narration. Must not restate narration.
   - Negative reinforcement: "Do NOT emit progress that restates what happened" over "Progress should be unique."
   - Rarity: "A thread present in the scene is not a reason to update it."

## Risks, Ambiguities, and Blockers

- Fuzzy matching threshold (50%) is a guess — may need tuning after observation.
- Auto-latent at 3 turns may be aggressive for slow-burn threads. Config knob allows adjustment.
- `ProgressEntry` migration: old saves with `progress: list[str]` need the `_coerce_progress` validator to wrap strings into `ProgressEntry(text=s, kind="advancement")`.

## Status
`completed`

## Phases

Six phases: models → config → engine logic → storytell context → prompts → change tracking.

## Implementation — Phase 1: Model changes

### Context files to load
- `ccya/models.py` — ArcThread, ThreadUpdate models
- `ccya/state/delta_builder.py` — _merge_arc_update (line 54–69): dumps threads to dict via model_dump

### Detailed steps

#### Step 1.1 — Add ProgressEntry model

**File:** `ccya/models.py`, after class definitions (before `ArcThread`)

**What:** Add `ProgressEntry` model with:
```python
class ProgressEntry(BaseModel):
    kind: Literal["advancement", "setback", "shift"] = "advancement"
    text: str
```

**Why:** Structured progress allows the LLM to classify each update, reducing noise by making the LLM think about what kind of change is happening. The `kind` field defaults to `"advancement"` for backward compatibility.

**Validation:** `python -c "from ccya.models import ProgressEntry; e = ProgressEntry(text='test'); assert e.kind == 'advancement'; assert e.text == 'test'"`

#### Step 1.2 — Change ArcThread.progress to list[ProgressEntry]

**File:** `ccya/models.py`, lines 37

**What:** Change `progress: list[str] = []` to `progress: list[ProgressEntry] = Field(default_factory=list)`. Replace the `_coerce_progress` validator with one that handles both `list[str]` and `list[dict]` input:
```python
    progress: list[ProgressEntry] = Field(default_factory=list)

    @field_validator("progress", mode="wrap")
    @classmethod
    def _coerce_progress(cls, v: Any, handler: Any) -> Any:
        if isinstance(v, str):
            return [ProgressEntry(text=v, kind="advancement")]
        if not v:
            return []
        if isinstance(v, list):
            converted: list[ProgressEntry] = []
            for item in v:
                if isinstance(item, ProgressEntry):
                    converted.append(item)
                elif isinstance(item, str):
                    converted.append(ProgressEntry(text=item, kind="advancement"))
                elif isinstance(item, dict):
                    converted.append(ProgressEntry(**item))
                else:
                    converted.append(ProgressEntry(text=str(item), kind="advancement"))
            return converted
        return handler(v)
```

**Why:** New structured format; validator handles migration from old `list[str]` state files.

**Validation:** `python -c "from ccya.models import ArcThread; t = ArcThread(id='x', summary='x', scope='arc', progress=['old text']); assert isinstance(t.progress[0], dict); print(t.progress)"`

Wait, validation needs checking. Let me think: when the YAML data `progress: ["old text"]` is loaded, Pydantic's model_validate will call the validator with `v=["old text"]`. The validator converts each str to ProgressEntry. Then Pydantic will further validate that `ProgressEntry` is a list of ProgressEntry objects. But actually, when `mode="wrap"`, the handler handles the Pydantic-side validation. Let me write the validator properly.

Actually, I need to think about this more carefully. In `model_validate` mode, if the schema has `list[ProgressEntry]` and the input is `["old text"]`, Pydantic will first try to validate each item as a ProgressEntry. The string "old text" won't match ProgressEntry, so it will fail. The `mode="wrap"` validator is called BEFORE Pydantic's built-in validation, so I can intercept the list[str] case and convert it.

Let me verify: with `mode="wrap"`, the validator receives the raw value `v` and the `handler` which is the normal Pydantic validation. If I return a value from the validator, that value is used instead of calling handler. If I call `handler(v)`, it does Pydantic's normal validation.

So the validator should:
1. If `v` is a str → wrap in list, call handler
2. If `v` is falsy → return []
3. If `v` is a list → check each item. If any item is a string, convert all to ProgressEntry. Otherwise call handler.
4. Otherwise → call handler

Let me write the validator correctly:

```python
@field_validator("progress", mode="wrap")
@classmethod
def _coerce_progress(cls, v: Any, handler: Any) -> Any:
    if isinstance(v, str):
        return handler([v])
    if not v:
        return []
    if isinstance(v, list):
        if not v:
            return []
        # Check if any item is a bare string (old format)
        if any(isinstance(item, str) for item in v):
            return handler([ProgressEntry(text=item, kind="advancement") for item in v])
        # List of dicts or ProgressEntry objects — pass through
        return handler(v)
    return handler(v)
```

Hmm, but if I pass `[ProgressEntry(...)]` to `handler`, Pydantic will try to validate each ProgressEntry object. Since ProgressEntry IS a BaseModel, Pydantic should handle it fine by calling its model_validate.

Actually for `mode="wrap"`, when I return from the handler, it just returns that value. So `handler([ProgressEntry(...)])` should work.

Let me simplify. Actually, Pydantic's list validation with wrap mode: if I return a list from the validator, Pydantic will still validate each item against the inner type. So if I return `[ProgressEntry(text="foo")]`, Pydantic will validate that as a list of ProgressEntry — which should work since ProgressEntry is already a valid instance.

Wait, actually, with `mode="wrap"`, if I call `handler(v)`, the handler does the default validation. If I return a value directly (not calling handler), it skips validation. Since I want validation to happen on the converted values, I should call handler with the converted list.

Let me keep it simple:

```python
@field_validator("progress", mode="wrap")
@classmethod
def _coerce_progress(cls, v: Any, handler: Any) -> Any:
    if isinstance(v, str):
        return [ProgressEntry(text=v)]
    if not v:
        return []
    if isinstance(v, list):
        if v and all(isinstance(item, str) for item in v):
            return [ProgressEntry(text=item) for item in v]
        return v
    return v
```

Wait, if I return `[ProgressEntry(...)]` directly, does Pydantic still validate each item? With `mode="wrap"`, returning without calling handler means the returned value is used as-is. But Pydantic might still do type checking. Let me think...

Actually, the `mode="wrap"` handler IS Pydantic's normal validation. So if I call `handler(v)`, it validates `v` against the field's type. If I return from the validator without calling handler, Pydantic uses the returned value as the final validated value.

But there's a subtlety: even without calling handler, Pydantic might still do type coercion based on the type annotation. Let me just call handler to be safe:

```python
@field_validator("progress", mode="wrap")
@classmethod
def _coerce_progress(cls, v: Any, handler: Any) -> Any:
    if isinstance(v, str):
        return handler([v])
    if not v or (isinstance(v, int) and v == 0):
        return []
    if isinstance(v, list):
        if v and all(isinstance(item, str) for item in v):
            return handler([ProgressEntry(text=item, kind="advancement") for item in v])
        return handler(v)
    return handler(v)
```

This should work:
- Old format `["text"]` → converts to `[ProgressEntry(...)]`, calls handler which validates them
- New format `[{"text": "...", "kind": "advancement"}]` → passes to handler
- ProgressEntry objects → passes to handler
- Strings → wraps in list and recurses
- Falsy → empty list

OK this is getting detailed for the plan. Let me just write it and move on.

#### Step 1.3 — Add progress_kind to ThreadUpdate

**File:** `ccya/models.py`, around line 387–392

**What:** Add to `ThreadUpdate`:
```python
    progress: str | None = None
    progress_kind: Literal["advancement", "setback", "shift"] | None = None
```

**Why:** LLM can classify each progress update's kind. Engine stores it in the ProgressEntry when merging.

**Validation:** `python -c "from ccya.models import ThreadUpdate; u = ThreadUpdate(id='x', progress='found a clue', progress_kind='advancement'); assert u.progress_kind == 'advancement'"`

#### Step 1.4 — Update _apply_thread_updates progress creation

**File:** `ccya/engine/turn.py`, lines 193–196

**What:** Change progress append to create `ProgressEntry`:
```python
        if update.progress is not None:
            current_progress = list(thread.progress)
            kind = update.progress_kind or "advancement"
            current_progress.append({"text": update.progress, "kind": kind})
            updates["progress"] = current_progress
```

**Why:** The LLM emits raw text + optional kind; the engine wraps it into the structured ProgressEntry format.

**Validation:** `python -c "from ccya.models import ProgressEntry, ThreadUpdate; u = ThreadUpdate(id='x', progress='clue found', progress_kind='advancement'); assert u.progress == 'clue found'; assert u.progress_kind == 'advancement'"`

Actually, the validation here is in the runtime behavior. After this change, when a ThreadUpdate with progress is applied, the resulting ArcThread's progress list will contain a ProgressEntry dict, not a bare string.

Let me also update `delta_builder.py` step — actually, `_merge_arc_update` just calls `model_dump()` on the CampaignArc's threads, which will serialize ProgressEntry correctly as `{text: ..., kind: ...}`. No change needed there.

### Tests to write or update

None (tests are suspended during refactor per AGENTS.md).

## Implementation — Phase 2: Config options

### Context files to load
- `ccya/engine/config.py` — EngineConfig class (lines ~145–160), build_engine_config function (lines ~171–260)

### Detailed steps

#### Step 2.1 — Add thread_stale_threshold and thread_max_active to EngineConfig

**File:** `ccya/engine/config.py`, lines ~158–160 (after existing thread/arc TTL fields)

**What:** Add:
```python
    # Auto-latent threshold: threads untouched for N turns go active: false
    thread_stale_threshold: int = 3
    # Max active threads before eviction of oldest
    thread_max_active: int = 5
```

**Why:** Configurable knobs for auto-latent aggressiveness and thread count cap.

**Validation:** `python -c "from ccya.engine.config import EngineConfig; c = EngineConfig(); assert c.thread_stale_threshold == 3; assert c.thread_max_active == 5"`

#### Step 2.2 — Wire config values in build_engine_config

**File:** `ccya/engine/config.py`, around line 258–259

**What:** Add:
```python
        thread_stale_threshold=int(game.get("thread_stale_threshold", 3)),
        thread_max_active=int(game.get("thread_max_active", 5)),
```

**Why:** Maps config.yaml values to EngineConfig fields per the existing pattern.

**Validation:** `python -c "from ccya.engine.config import build_engine_config; cfg = build_engine_config({'game': {}}); assert cfg.thread_stale_threshold == 3; assert cfg.thread_max_active == 5"`

### Tests to write or update

None.

## Implementation — Phase 3: Engine logic

### Context files to load
- `ccya/engine/turn.py` — _apply_thread_updates (lines 141–213), thread_add handler (lines 1217–1243), full run_turn loop (around line 1164–1243)
- `ccya/engine/config.py` — EngineConfig field names (from Phase 2)

### Detailed steps

#### Step 3.1 — Content dedup via fuzzy matching

**File:** `ccya/engine/turn.py`, `_apply_thread_updates`, around line 193 (progress append block)

**What:** Before appending progress, compare the new progress text against the LAST entry in the thread's current progress list. If token overlap ratio ≥ 0.50 (difflib.SequenceMatcher), skip the progress append, log a warning, and continue (still apply other updates like urgency/active/summary).

Add `import difflib` at top of file.

Logic:
```python
        if update.progress is not None:
            current_progress = list(thread.progress)
            if current_progress:
                last_entry = current_progress[-1]
                last_text = last_entry.get("text") if isinstance(last_entry, dict) else str(last_entry)
                ratio = difflib.SequenceMatcher(None, last_text, update.progress).ratio()
                if ratio >= 0.50:
                    _log.warning(
                        "thread_updates.dedup trace_id=%d thread %s — progress %.2f overlap with last entry, rejecting",
                        turn_no, update.id, ratio, extra={"turn": turn_no},
                    )
                else:
                    kind = update.progress_kind or "advancement"
                    current_progress.append({"text": update.progress, "kind": kind})
                    updates["progress"] = current_progress
            else:
                kind = update.progress_kind or "advancement"
                current_progress.append({"text": update.progress, "kind": kind})
                updates["progress"] = current_progress
```

Note: This depends on Phase 1 (ProgressEntry format). If progress is still `list[str]`, the dedup logic uses raw strings; if `list[ProgressEntry]`, it extracts `.text`.

**Why:** The user's primary complaint is trivial updates. Fuzzy matching catches the "same thing rephrased" case that dominates the noise.

**Validation:** Hand-check: if thread has last progress "Following the lead" and LLM emits "Still following the lead", ratio ≈ 0.75, rejected. If LLM emits "Found the hidden cache", ratio ≈ 0.2, accepted.

#### Step 3.2 — Auto-latent on staleness

**File:** `ccya/engine/turn.py`, in `_apply_thread_updates` after the per-update loop (after line 211), before the `return` statement

**What:** After processing all LLM-emitted updates, iterate over `remaining_threads`. For each thread, check:
- If `thread.last_updated_turn` is not None
- If `(turn_no - thread.last_updated_turn) >= config.thread_stale_threshold`
- If the thread is currently `active: True`
Then set `active: False`, log the demotion, and mark `mutated = True`.

Add early return if no config is available (function doesn't currently receive config — need to thread it through).

Wait, `_apply_thread_updates` currently takes `(state, storyteller_result)`. I need to either:
a) Pass `config` as a parameter
b) Or hardcode the threshold

Following the pattern of other functions in turn.py that receive config, option (a) is correct.

But changing the signature of `_apply_thread_updates` requires updating its call site at line 1166:
```python
thread_delta = _apply_thread_updates(state, storyteller_result)
```

Let me add `config` as a parameter.

Actually, let me check if there's a simpler approach. Can I read from state? No — config isn't in state.

Let me update the function signature and call site.

**File:** `ccya/engine/turn.py`, line 141–144

**What:** Change signature:
```python
def _apply_thread_updates(
    state: dict[str, Any],
    storyteller_result: StorytellerResult,
    config: EngineConfig | None = None,
) -> CampaignArc | None:
```

**Call site** (line 1166):
```python
thread_delta = _apply_thread_updates(state, storyteller_result, config)
```

At the call site, `config` is already available (check the surrounding function — it's the `run_turn` function's `config` parameter).

Wait, let me check what `config` is called in run_turn. Let me look at the function signature:

I'll need to read that. Let me note this in the plan: executor must verify the variable name used for config in run_turn.

Actually, in the plan I can just say "pass the existing `config` variable (EngineConfig instance from run_turn scope)."

**What (auto-latent logic):**
```python
    # Auto-latent: demote stale threads
    if config and mutated:
        stale_threshold = config.thread_stale_threshold
        for i, t in enumerate(remaining_threads):
            if (
                t.last_updated_turn is not None
                and (turn_no - t.last_updated_turn) >= stale_threshold
                and t.active
            ):
                updated = t.model_copy(update={"active": False, "last_updated_turn": turn_no})
                remaining_threads[i] = updated
                _log.info(
                    "thread_updates.auto_latent trace_id=%d thread %s — untouched for %d turns",
                    turn_no, t.id, turn_no - t.last_updated_turn, extra={"turn": turn_no},
                )
```

**Why:** Prevents forgotten threads from accumulating in prompts. The LLM can re-activate them later.

**Validation:** Unit test: create a thread with `last_updated_turn=1` at turn 5, threshold 3, verify `active=False` in returned arc.

#### Step 3.3 — Thread cap eviction

**File:** `ccya/engine/turn.py`, thread_add handler (lines 1217–1243)

**What:** After successfully adding a new thread (line 1238), count active threads. If `len(active_threads) > config.thread_max_active`, find the active thread with the oldest `last_updated_turn` and set it to `active: false`.

```python
                # After thread_add succeeds:
                if _updated_t and config:
                    active_threads = [t for t in arc_with_new_thread.threads if t.active]
                    if len(active_threads) > config.thread_max_active:
                        evict = min(active_threads, key=lambda t: t.last_updated_turn or 0)
                        evicted = evict.model_copy(update={"active": False, "last_updated_turn": turn_no_for_add})
                        new_threads = [evicted if t.id == evict.id else t for t in arc_with_new_thread.threads]
                        capped_arc = arc_with_new_thread.model_copy(update={"threads": new_threads})
                        _merge_arc_update(state.setdefault("arc", {}), capped_arc)
                        _log.info(
                            "thread_cap.evict trace_id=%d evicted=%s active_count=%d max=%d",
                            trace_id, evict.id, len(active_threads), config.thread_max_active,
                            extra={"trace_id": trace_id},
                        )
```

Note: This needs careful placement. The thread_add already calls `_merge_arc_update` at line 1236. The eviction would need to call `_merge_arc_update` again or be integrated before the first merge.

Better approach: Do the eviction check BEFORE setting last_thread_created_turn, and conditionally evict, then merge once.

Simpler: Do the eviction as a second `_merge_arc_update` call. The first merge adds the new thread, the second merges the eviction. This works because `_merge_arc_update` replaces `threads` entirely.

**Why:** Prevents thread count from growing unbounded, which directly drives the pressure to emit noise (more threads → more perceived need to update them all).

**Validation:** Unit test: set max=1, add 2 threads, verify only 1 active after second add.

### Tests to write or update

None (tests suspended).

## Implementation — Phase 4: Storytell context

### Context files to load
- `ccya/engine/extraction.py` — _storytell_messages (lines 226–284)
- `ccya/engine/narrate.py` — _get_resolved_arcs (lines 124–132) for reference/reuse
- `ccya/engine/turn.py` — run_turn around storytell call site (line ~528)

### Detailed steps

#### Step 4.1 — Pass resolved_arcs to _storytell_messages

**File:** `ccya/engine/extraction.py`, `_storytell_messages`, around line 266 (where template context is built)

**What:** Add `resolved_arcs` to the template context dict, using the same TTL-filtered call as narrate does.

The function already has `state` and `turn_no`. Add:
```python
    # Resolved arcs: TTL-filtered, same as narrate
    resolved_arcs = _get_resolved_arcs(state, turn_no, ttl=3)
```

Wait, `_get_resolved_arcs` is in `narrate.py`. It's imported and used in turn.py for narrate. The storytell function in extraction.py might not have access to it. I need to either:
a) Import it into extraction.py
b) Pass it as a parameter from turn.py
c) Inline the logic

Option (b) is cleanest — the resolved arcs are computed once in turn.py and passed down.

Actually, looking at how narrate is called in turn.py:

Let me check the call site in turn.py for storytell.

Actually, let me re-read the run_turn flow:
- Line 832: narrate gets resolved_arcs computed
- Line ~528: storytell is called (inside extraction pipeline)

The simplest approach: compute resolved_arcs in run_turn (or reuse the same computation) and pass them to `_storytell_messages`. But `_storytell_messages` is called from `_run_extraction_pipeline`. Let me trace the call chain.

Actually, let me read the relevant parts of turn.py to see how the extraction pipeline is called.

Let me simplify the plan wording and just say "import _get_resolved_arcs into extraction.py" — it's a pure function that only depends on `state` and `turn_no`, no narrate-specific dependencies.

**What:** Add to `extraction.py`:
```python
from ccya.engine.narrate import _get_resolved_arcs
```

Add to the template context: `"resolved_arcs": resolved_arcs` where `resolved_arcs = _get_resolved_arcs(state, turn_no, ttl=3)`.

The TTL value should come from config. But `_storytell_messages` doesn't currently receive config. The extraction pipeline callers in turn.py pass config to `_run_extraction_pipeline`. Let me trace:

Looking at extraction.py, `_run_extraction_pipeline` takes config but `_storytell_messages` doesn't receive it directly. Add `arc_ttl` parameter to `_storytell_messages`.

**Why:** Ensures storytell has visibility into resolved arc context, which it currently lacks (a known gap from IDEAS.md). Helps generate better successor arcs.

**Validation:** `ev.py prompt <turn> storytell user` should show "Previously Resolved Arcs (TTL)" section after this change.

### Tests to write or update

None.

## Implementation — Phase 5: Prompt tightening

### Context files to load
- `ccya/prompts/storytell_system.j2` (98 lines)
- `ccya/prompts/generate_seed_system.j2` (176 lines, thread rules section lines 118–140)
- `ccya/prompts/sections/_thread_list.j2` (7 lines)
- `ccya/prompts/storytell_user.j2` (61 lines)
- `ccya/prompts/narrate_user.j2` (thread display section)

### Detailed steps

#### Step 5.1 — Tighten storytell_system.j2 thread rules

**File:** `ccya/prompts/storytell_system.j2`, lines 22–36

**What:** Replace the Threads section with tightened wording:

**Lines 22–24 (Default rule):**
```
## Threads

**Default: emit nothing.** Most turns produce zero thread operations. Do NOT emit an update because a thread was mentioned in the narration. Only emit when this turn's events changed the thread's trajectory — the tension advanced, pivoted, or resolved. A character acting within a thread is not a change. If the same tension would exist without this turn's events, omit.
```

**Lines 26 (Thread ID rule):**
```
**Thread IDs are 2–4 word broad conceptual buckets.** No proper nouns. If your ID contains a character name, location, or object name, it is too narrow. `enemy_contact_advance` ✓ — `naval_boarding_action` ✗ (it is a scene), `the_missing_ledger` ✗ (one object).
```

**Lines 30 (thread_update rule):**
```
**`thread_update`:** `summary` OR `progress` — not both. `summary` (4–7 words) when the thread's nature or direction changed, describing a broad SITUATION — not an objective or action. `progress` (one sentence) explaining HOW the thread's trajectory evolved beyond what the narration shows, with an optional `progress_kind` classifying the change. Do NOT emit `progress` that restates what happened — if a reader would learn nothing new about the thread's trajectory, omit it. Urgency decays one step per turn unaddressed. If inactive 2+ turns without new progress, set `active: false`.
```

**Lines 28 (thread_resolve):**
```
**`thread_resolve`:** Use when a thread concluded, failed, was absorbed into a broader thread, or urgency fully decayed. `promote_to_world_state: true` only when the outcome is a permanent world fact. Do NOT resolve threads still meaningfully active — prefer `active: false` for threads that might resurface. If a thread went unaddressed for 3+ turns, this probably means resolve or auto-demote rather than update.
```

**Lines 32–34 (thread_add + scope):**
```
**Before emitting `thread_add`:** scan all active AND latent threads for conceptual overlap. If the same tension is already tracked, use `thread_update` instead. Only create a new thread for genuinely distinct tension. Maximum 5 active threads at any time — if you are at the cap, resolve an existing thread first.

**Scope:** `scene` threads auto-delete on location change. `arc` threads persist until arc resolution or explicit resolve. Choose deliberately. Broad buckets only — if your thread would resolve after one scene, it belongs in `scene` scope or in the narration, not in the arc.
```

**Why:** Concretizes "not a retelling" into "if a reader would learn nothing new, omit." Adds word limits. Uses negative reinforcement ("Do NOT emit progress that restates"). Adds cap awareness.

**Validation:** Read file, verify changes look correct.

#### Step 5.2 — Tighten generate_seed_system.j2 thread rules

**File:** `ccya/prompts/generate_seed_system.j2`, lines 118–140

**What:** Replace thread rules section:

```
## Thread rules

**Thread IDs are 2–4 word broad conceptual buckets.** No proper nouns. `council_conspiracy` ✓ — `the_missing_ledger` ✗ (one object), `moss_confrontation` ✗ (one NPC).

**Summaries: one sentence (8–15 words), describing a SITUATION, not an objective.** "A rival crew is closing in on the same salvage" ✓ — "Find the salvage before the rival crew" ✗.

**Thread count (hard limits at game start):**
- Exactly 1–2 threads `active: true` — prefer 1 if unsure. Never more than 2.
- All other threads `active: false`.
- Up to 3 latent threads (`active: false`).
- Total: 4–5 threads (minimum 3, maximum 6).
- All new threads use `scope: "arc"`. Do not generate `scope: "scene"` threads at game start.
- Active threads: urgency `"normal"` or `"urgent"` (prefer `"normal"`).
- Inactive threads: urgency `"background"` or `"normal"`. Never `"urgent"`.

**Thread quality:** Each thread must be a medium-term tension capable of sustaining 5–10 turns — a situation with inherent escalation, not a single event, person, or goal. If your thread would resolve after one interaction, it belongs in the opening scene, not the arc. Thread summaries are seeds for the narrator, not scripted plot — describe a situation; do not specify events. Do not generate threads from incidental narration details.

Good summary: "A rival crew is closing in on the same salvage coordinates."
Bad summary: "Go to Saint Mercy Hospital and find the ledger."
```

**Why:** Aligns seed generation with the same tight-summary philosophy. Explicitly forbids summaries that read as objectives.

**Validation:** Read file, verify changes.

#### Step 5.3 — Update _thread_list.j2 to render progress kind

**File:** `ccya/prompts/sections/_thread_list.j2`, line 5

**What:** Change the progress render loop to show kind badge:
```
{%- for entry in t.progress %}   - [{{ entry.kind | upper }}] {{ entry.text }}{% endfor %}
```

But `ArcThreadSummary` has `progress: list[str]`, and the entries are stored as dicts in state but flattened to strings by `from_state`. I need to either:
a) Render the dict directly (if progress is list[dict])
b) Change ArcThreadSummary.progress type

For the plan, I'll specify:
1. Update `ArcThreadSummary.progress` from `list[str]` to `list[dict[str, Any]]` or keep it as `list[str]` and render formatted kind+text
2. Update `from_state` in `ArcThreadBlock` to format progress entries as `"[KIND] text"` when building summaries

Actually, simplest approach: keep `ArcThreadSummary.progress: list[str]` and format the kind+text string in `from_state`. So when building from state, convert `ProgressEntry(text="found clue", kind="advancement")` to the string `"[ADVANCEMENT] found clue"`.

This way, `_thread_list.j2` doesn't change at all — it already renders `{{ entry }}` for each progress item.

**What (alternative, simpler):** Don't change `_thread_list.j2`. Instead, in `ArcThreadBlock.from_state` and anywhere else that builds `ArcThreadSummary` progress from state dicts, format the progress entry as `"[{kind.upper()}] {text}"`.

So for the `from_state` conversion:
```python
progress=self._format_progress(t.get("progress", [])),
```

And a helper:
```python
@staticmethod
def _format_progress(progress: Any) -> list[str]:
    if not progress:
        return []
    result = []
    for entry in progress:
        if isinstance(entry, str):
            result.append(entry)
        elif isinstance(entry, dict):
            kind = entry.get("kind", "advancement").upper()
            text = entry.get("text", "")
            result.append(f"[{kind}] {text}")
        else:
            result.append(str(entry))
    return result
```

This is the cleanest approach: no template changes, no ArcThreadSummary model changes, just format at the rendering boundary.

**Why:** LLM sees the kind badge and can distinguish "this was an advancement" from "this was a setback" at a glance.

**Validation:** Verify `ev.py state` or prompt rendering shows `[ADVANCEMENT]` prefixed progress entries.

### Tests to write or update

None.

## Implementation — Phase 6: Change tracking

### Context files to load
- `ccya/engine/changes.py` — thread diff logic (lines 230–313), format_change_lines (lines ~373–397)

### Detailed steps

#### Step 6.1 — Detect progress_kind changes in thread diff

**File:** `ccya/engine/changes.py`, lines 287–301 (thread update detection)

**What:** Add progress list diff detection alongside existing urgency/active/summary checks. If the number of progress entries changed, or the kind of the last entry changed, mark as updated with detail "progress updated" (or similar).

```python
            elif po and pr:
                changes = []
                if po.get("urgency") != pr.get("urgency"):
                    changes.append(f"urgency: {pr.get('urgency', '?')}→{po.get('urgency', '?')}")
                if po.get("active") != pr.get("active"):
                    changes.append("reactivated" if po.get("active") else "dormant")
                if po.get("summary") and po.get("summary") != pr.get("summary"):
                    changes.append("summary updated")
                # Progress diff: check entry count or last entry kind/text
                pre_progress = pr.get("progress") or []
                post_progress = po.get("progress") or []
                if len(post_progress) > len(pre_progress):
                    changes.append("progress added")
                elif len(post_progress) < len(pre_progress):
                    changes.append("progress consolidated")
                elif post_progress and pre_progress and post_progress[-1] != pre_progress[-1]:
                    changes.append("progress updated")
```

This adds detection of progress changes to the display diff, which was previously a known gap.

**Why:** The UI (change lines) should reflect progress changes, not just urgency/active/summary. Previously this was a known gap.

**Validation:** Hand-check: add a progress entry → diff shows "progress added". No save file needed.

### Tests to write or update

None.

## Implementation — Phase 7: Post-implementation verification

### Context files to load
- None needed

### Detailed steps

#### Step 7.1 — Run lint and type-check

**Command:** `make check` from repo root.

**What:** Must pass. Fix any failures introduced by the changes.

**Why:** Project hygiene per AGENTS.md.

#### Step 7.2 — Read all changed files

**What:** Read each file edited by this plan. Verify each change matches what was specified. No missing steps, no extra unrequested changes.

**Why:** Final verification.

### Tests to write or update

None.

## Implementation — Phase 8: Documentation

### Context files to load
- `docs/architecture/OVERVIEW.md` — check if pipeline docs mention thread update flow
- `docs/repomap.md` — check for thread/arc/update entries

### Detailed steps

#### Step 8.1 — Update docs/repomap.md

**File:** `docs/repomap.md`

**What:** Add entries for any new public models (ProgressEntry), and note the new config fields (thread_stale_threshold, thread_max_active) in the EngineConfig section.

**Why:** Per execute skill instructions: "Documentation updated: docs/architecture/ docs reflecting any architectural changes, and docs/repomap.md reflecting new files, functions, signatures, module boundaries, cross-module contracts, or public APIs. Not optional — missing doc updates mean the execution is not done."

#### Step 8.2 — Update docs/architecture if needed

**What:** If any pipeline mechanics changed (e.g., auto-latent, thread cap), add a brief note. Skip if the architecture doc doesn't detail thread update mechanics.

#### Step 8.3 — Move plan to completed

**What:** Move this plan doc to `plans/completed/04-pipeline/thread-noise-reduction.md`

**Why:** Standard plan lifecycle.

#### Step 8.4 — Commit

**What:** `git add -A && git commit` with detailed message covering all phases.
