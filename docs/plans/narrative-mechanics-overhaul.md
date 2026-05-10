# Narrative Mechanics Overhaul

## Status
`open` — **partial implementation detected**. Several items from the prior `progress-rules-narration.md` plan are already merged. This plan is rewritten below to reflect actual code state.

## Part of
standalone

## Dependencies
- `docs/plans/progress-rules-narration.md` — **superseded**. Its Phase 1 (GMBeat new types, ProgressExtractResult.gm_beat, SceneExtractResult without gm_beat) and partial Phase 2 (deescalate float widening, beat_expires_turn storage, beat expiry guard, full narration, progress_result read) are **already merged**. This plan completes the remaining wiring and adds the new mechanics. Mark `progress-rules-narration.md` abandoned after this plan ships.
- `docs/plans/TODO.md` open item: `Fix condition dedup` — independent; no conflict.

## Conflicts and overlap
- **`progress-rules-narration.md`** (open): The plan's Phase 1 model changes are **already merged** (GMBeat new types, ProgressExtractResult.gm_beat, SceneExtractResult without gm_beat). Partial Phase 2 items are also **already done**: `deescalate` is `float` in extraction.py/narrate.py/turn.py, beat expiry guard exists in both `run_turn` and `run_turn_retry`, `beat_expires_turn = turn_no + 2` is written on storage, `rules_user.j2` already emits full `t.narrative` (no truncation), `extract_progress_user.j2` already uses `recent_turns[-1]` (not `[-2]`), and `turn.py` already reads `gm_beat` from `progress_result` (not `scene_result`). The remaining items NOT yet done are: `beat_disposition` model+logic, `stakes`/`band` wiring to extractors, `scene_pressure_add` merge source change, template context blocks, and eval harness updates. This plan covers all remaining work.

---

## Objective

This plan implements five interconnected narrative improvements:

1. **Beat carry/consume disposition** — beats persist across turns until progress explicitly marks them consumed, rather than being cleared after any narration turn regardless of use.
2. **Pressure ownership migration** — `scene_pressure_add` moves from `SceneExtractResult` to `ProgressExtractResult`; scene extractor retains only `_remove` and `_update`. Rules engine reads pressure as context for difficulty; progress generates new pressure from story causality.
3. **Stakes → pressure + condition routing** — `intent.stakes` and `outcome.band` are passed to progress and state extractors so they can enforce the mechanical cost the rules LLM named, rather than inferring it independently from narration prose.
4. ~~**Rules narration context fix** — `rules_user.j2` truncates prior narration to 120 chars.~~ **ALREADY DONE** — `rules_user.j2` already emits full `t.narrative`.
5. ~~**Progress `prior_turn_narration` index fix** — `extract_progress_user.j2` reads `recent_turns[-2]`.~~ **ALREADY DONE** — already uses `recent_turns[-1]`. However, the `{% if recent_turns | length >= 2 %}` guard needs to change to `>= 1`.

---

## Non-goals

- Does not implement personality traits or NPC disposition scores (separate future plan).
- Does not implement consequence chains on `ScenePressure` (`cascade_to` field) — deferred.
- Does not change `build_directive()` in `rules.py` or any deterministic dice logic.
- Does not change the narrator's consumption of `pending_gm_beat` in `narrate_user.j2` — only the production and lifecycle change.
- Does not change `StateDelta` field list — all new fields are merge-additive from existing sources.
- Does not change compaction, chronicle, or any persistence path other than `meta.pending_gm_beat` and the extraction result models.
- Does not change eval harness rubric or judge logic — only the gm_beat_lifecycle scenario and universal asserts need updates for new field presence.
- Item 22 (NPC relationship scores) is explicitly deferred and not included.

---

## Affected files

| File | Change type | Summary of change |
|---|---|---|
| `ccya/models.py` | modify | Add `beat_disposition` to `ProgressExtractResult`; add `scene_pressure_add` to `ProgressExtractResult`; remove `scene_pressure_add` from `SceneExtractResult` |
| `ccya/engine/extraction.py` | modify | Pass `deescalate`, `quest_ages`, `intent.stakes`, `outcome.band` to progress messages; pass `intent.stakes`, `outcome.band` to state messages; move `scene_pressure_add` source from `scene_result` to `progress_result` in merge; add `pending_beat` to progress render context |
| `ccya/engine/turn.py` | modify | Add beat disposition handling logic (carry/consume/replace) in both `run_turn` and `run_turn_retry` — currently only stores beats unconditionally |
| `ccya/prompts/rules_user.j2` | **no change** | Already emits full `t.narrative` — prior plan item already done |
| `ccya/prompts/extract_progress_user.j2` | modify | Change `>= 2` to `>= 1` on prior_turn_narration guard; add stakes/band context block; add gm_beat instruction block with beat_disposition output; add scene_pressure_add instruction block |
| `ccya/prompts/extract_progress_system.j2` | modify | Add `beat_disposition` to output schema; add `scene_pressure_add` to output schema |
| `ccya/prompts/extract_scene_system.j2` | modify | Remove `scene_pressure_add` from output schema and instructions |
| `ccya/prompts/extract_state_user.j2` | modify | Add stakes/band hint block |
| `docs/REPOMAP/models.md` | update | Reflect `ProgressExtractResult` new fields; reflect `SceneExtractResult` removed `scene_pressure_add` |
| `docs/REPOMAP/engine.md` | update | Reflect changed signatures in extraction.py; reflect beat disposition handling in turn.py |
| `docs/plans/TODO.md` | update | Add this plan; mark `progress-rules-narration.md` superseded |
| `evals/scenarios/gm_beat_lifecycle.py` | modify | Update assertions to account for beat_disposition carry behavior |
| `evals/universal_asserts.py` (if exists) | check | Verify no assertions depend on `scene_pressure_add` being in scene stream output |

---

## Firm decisions

1. **`beat_disposition` is a string enum field on `ProgressExtractResult`**, not a separate model. Values: `"consume"` | `"carry"` | `"replace"`. Default: `"consume"`. `carry` = beat stays in `meta.pending_gm_beat` unchanged. `consume` = beat is cleared after narration (existing behavior). `replace` = new beat from this turn supersedes the carried one.
2. **Beat TTL guard stays as hard ceiling.** `beat_expires_turn = current_turn + 2` is written on storage. Pre-narration expiry check nullifies beats past their TTL regardless of `beat_disposition`. This prevents indefinite carry accumulation.
3. **Maximum 1 carried beat at a time.** If `beat_disposition == "carry"` but a new beat is also emitted this turn (`gm_beat` is non-null), the new beat supersedes (implicit `replace`). Progress should not emit both a carry signal and a new beat.
4. **`scene_pressure_add` moves entirely to `ProgressExtractResult`.** Scene extractor retains `scene_pressure_remove` and `scene_pressure_update` only. `StateDelta` merge reads `scene_pressure_add` from `progress_result` instead of `scene_result`. No new model is created — field is added to `ProgressExtractResult`.
5. **`intent.stakes` is passed as a plain string to both progress and state extractors.** No new model field on either. It is injected into the Jinja2 `user_ctx` dict under the key `"stakes"`.
6. **`outcome.band` is passed as a plain string alongside `stakes`.** Both are only present when `rules_outcome.rolled == True`.
7. **On `crit_fail` + non-empty `stakes`, progress is instructed to treat the narrative consequence in stakes as a mandatory `scene_pressure_add` at `immediate` urgency** — this is a prompt instruction, not a hard code gate.
8. **On `crit_success` + non-empty `stakes`, progress is instructed to consider emitting an `npc_action` or `offscreen_consequence` beat** (types already in the GMBeat enum) naming the entity that was thwarted — this is advisory, not mandatory.
9. **State extractor uses `stakes` as a condition hint.** When `band` is `setback`, `fail`, or `crit_fail` and `stakes` names a condition (e.g. "wounded", "shaken"), state extractor should treat it as a strong signal to apply that condition even if the narration is ambiguous.
10. **`deescalate` float magnitude mapping:** `crit_success` with active `immediate`/`building` pressure → `1.0`; `success` with same → `0.6`; everything else → `0.0`. **Already implemented in turn.py lines 351-361.**
11. **`rules_user.j2` full narration.** **Already done** — template emits `{{ t.narrative }}` without truncation.
12. **`extract_progress_user.j2` index fix.** Already uses `recent_turns[-1]`. The template guard `{% if recent_turns and recent_turns | length >= 2 %}` on line 51 must change to `{% if recent_turns %}` to not silently skip single-turn contexts.

---

## Already-done inventory (from prior plan)

The following items from `progress-rules-narration.md` are **already merged** and require no changes:

| Item | File | Status |
|---|---|---|
| GMBeat new types (twist, setback, escalation, callback) | `models.py:399-409` | Done |
| `beat_expires_turn` field on GMBeat | `models.py:419` | Done |
| `ProgressExtractResult.gm_beat` field | `models.py:442` | Done |
| `SceneExtractResult` has no `gm_beat` | `models.py:265-303` | Done |
| `deescalate: float = 0.0` in extraction.py | `extraction.py:140,271,403` | Done |
| `deescalate: float = 0.0` in narrate.py | `narrate.py:28` | Done |
| `deescalate: float = 0.0` in turn.py | `turn.py:351` | Done |
| Deescalate magnitude computation (1.0/0.6) | `turn.py:351-361` | Done |
| Beat expiry guard pre-narration | `turn.py:414-419, 927-932` | Done |
| `beat_expires_turn = turn_no + 2` storage | `turn.py:557, 1072` | Done |
| Beat storage reads from `progress_result` | `turn.py:555-558, 1070-1073` | Done |
| `rules_user.j2` full narration | `rules_user.j2:11` | Done |
| `extract_progress_user.j2` uses `recent_turns[-1]` | `extract_progress_user.j2:52` | Done |

---

## Remaining work

### Phase 1: Models

#### Step 1.1 — Add beat_disposition to ProgressExtractResult

**File:** `ccya/models.py`

**What:** Add `beat_disposition` field to `ProgressExtractResult`.

**Why:** Progress needs to signal whether the current `pending_gm_beat` should be consumed, carried forward, or replaced. Without this field the beat is always consumed after narration.

**Code Snippet**
```python
class ProgressExtractResult(BaseModel):
    quest_updates: list[QuestUpdate] = Field(default_factory=list)
    recent_events_add: list[RecentEvent] = Field(default_factory=list)
    recent_events_update: list[RecentEventUpdate] = Field(default_factory=list)
    recent_events_remove: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""
    gm_beat: GMBeat | None = None
    beat_disposition: Literal["consume", "carry", "replace"] = "consume"
    scene_pressure_add: list[ScenePressure] = Field(default_factory=list)

    @model_validator(mode="after")
    def _nullify_invalid_gm_beat(self) -> "ProgressExtractResult":
        if self.gm_beat is not None:
            if not self.gm_beat.instruction or not self.gm_beat.type:
                self.gm_beat = None
        return self

    @field_validator("actions", mode="before")
    @classmethod
    def _coerce_actions(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[str] = []
        for x in v:
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, dict):
                out.append(x.get("action") or x.get("description") or str(x))
            else:
                out.append(str(x))
        return out
```

**Validation:** `python -c "from ccya.models import ProgressExtractResult; r = ProgressExtractResult(beat_disposition='carry'); print(r.beat_disposition)"` — prints `carry`.

---

#### Step 1.2 — Remove scene_pressure_add from SceneExtractResult

**File:** `ccya/models.py`

**What:** Remove `scene_pressure_add: list[ScenePressure]` from `SceneExtractResult`. Retain `scene_pressure_remove` and `scene_pressure_update`.

**Why:** Scene extractor observes and resolves pressure; progress extractor generates new pressure from narrative causality.

**Code Snippet**
```python
class SceneExtractResult(BaseModel):
    scene_tags: list[str] = Field(default_factory=list)
    scene_tagline: str | None = None
    location_change: LocationRef | None = None
    location_description: str | None = None
    npc_add: list[NpcAdd] = Field(default_factory=list)
    npc_remove: list[NpcRemove] = Field(default_factory=list)
    npc_update: list[NpcUpdate] = Field(default_factory=list)
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(
        default_factory=list, max_length=12
    )
    scene_pressure_remove: list[str] = Field(default_factory=list)
    scene_pressure_update: list[ScenePressure] = Field(default_factory=list)

    @field_validator("npc_remove", mode="before")
    @classmethod
    def _coerce_npc_remove(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[Any] = []
        for x in v:
            if isinstance(x, str):
                out.append({"id": x})
            else:
                out.append(x)
        return out

    @field_validator("location_description", mode="before")
    @classmethod
    def _coerce_location_description(cls, v: Any) -> Any:
        if not v:
            return v
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return v.get("description", str(v))
        return str(v)
```

**Validation:** `python -c "from ccya.models import SceneExtractResult; r = SceneExtractResult(); print(dir(r))"` — `scene_pressure_add` must not appear.

---

### Tests to write or update

**File:** `tests/test_models.py`

- `test_progress_beat_disposition_default` — assert `ProgressExtractResult().beat_disposition == "consume"`.
- `test_progress_beat_disposition_carry` — assert `ProgressExtractResult(beat_disposition="carry").beat_disposition == "carry"`.
- `test_progress_scene_pressure_add` — assert `ProgressExtractResult(scene_pressure_add=[{"id": "p1", "text": "test", "urgency": "immediate"}]).scene_pressure_add` has length 1.
- `test_scene_extract_result_no_pressure_add` — assert `SceneExtractResult` has no `scene_pressure_add` attribute and `SceneExtractResult()` constructs without error.

### REPOMAP updates required

`docs/REPOMAP/models.md`: update `ProgressExtractResult` entry (new fields `beat_disposition`, `scene_pressure_add`); update `SceneExtractResult` entry (removed `scene_pressure_add`).

### Risks

1. Any code that reads `scene_result.scene_pressure_add` directly will raise `AttributeError` after this phase. Verify with `grep -rn "scene_result\.scene_pressure_add" ccya/` — only `extraction.py` should appear, and that read is replaced in Phase 2.
2. `StateDelta` has `scene_pressure_add` as a field. The `apply_delta` in `state/delta.py` reads it from the delta dict, not from `SceneExtractResult` directly, so `state/delta.py` is unaffected.
3. **Eval harness impact:** The eval trace files (`evals/runs/*/full_cycle.trace.md`) contain `scene_pressure_add` in the scene stream output. After this change, the scene stream output will no longer have this key. The eval harness reads `scene_pressure_add` from the scene stream in trace files — verify that `evals/scenarios/gm_beat_lifecycle.py` and any universal asserts don't depend on this key being present in the scene output. The key will still exist in the `applied` dict of `events.jsonl` (from `StateDelta`), just not in the extraction event.

---

## Phase 2: Extraction pipeline wiring

### Context files to load
- `ccya/engine/extraction.py`
- `ccya/engine/turn.py`
- `ccya/models.py` (Phase 1 complete)

### Overview

Three changes in this phase: (1) pass `stakes`/`band` to progress and state extractors, (2) fix `scene_pressure_add` merge source, (3) add beat disposition handling in turn.py.

**Note:** Steps 2.1 (deescalate widening) and 2.4d (deescalate kwarg) are **already done** — `deescalate` is `float = 0.0` throughout the pipeline.

---

#### Step 2.1 — Add stakes and band to progress and state message builders

**File:** `ccya/engine/extraction.py`

**What:** Extract `stakes = (intent.stakes or "") if intent else ""` and `band = (rules_outcome.band if rules_outcome and rules_outcome.rolled else "")` in `_run_extraction_pipeline` and forward both to `_extract_progress_messages` and `_extract_state_messages`.

Add `stakes: str = ""` and `band: str = ""` parameters to both `_extract_progress_messages` and `_extract_state_messages`. In each function, add both to the `user_text` render context dict.

**Why:** Stakes names the mechanical cost the rules LLM identified. Band is the roll outcome. Together they give both extractors a direct signal instead of forcing inference from narration prose.

**Code Snippet** — additions to `_extract_progress_messages`:
```python
def _extract_progress_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    active_domains: list[str],
    state_result: "StateExtractResult",
    rules_outcome: "RulesOutcome | None" = None,
    enable_thinking: bool = False,
    intent: "IntentEnvelope | None" = None,
    deescalate: float = 0.0,
    quest_ages: list[dict[str, Any]] = [],
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
    stakes: str = "",                 # add
    band: str = "",                   # add
) -> list[dict[str, str]]:
    # ...
    user_text = _render(
        env,
        "extract_progress_user.j2",
        {
            # ... existing keys ...
            "deescalate": deescalate,
            "quest_ages": quest_ages,
            "stakes": stakes,          # add
            "band": band,              # add
        },
    )
```

Same pattern for `_extract_state_messages`:
```python
def _extract_state_messages(
    env: "Environment",
    narration: str,
    state: dict[str, Any],
    *,
    active_domains: list[str],
    scene_result: "SceneExtractResult",
    rules_outcome: "RulesOutcome | None" = None,
    enable_thinking: bool = False,
    turn_no: int = 0,
    stakes: str = "",                 # add
    band: str = "",                   # add
) -> list[dict[str, str]]:
    # ...
    user_text = _render(
        env,
        "extract_state_user.j2",
        {
            # ... existing keys ...
            "stakes": stakes,          # add
            "band": band,              # add
        },
    )
```

In `_run_extraction_pipeline`, compute and forward:
```python
_stakes = (intent.stakes or "") if intent else ""
_band = (rules_outcome.band if rules_outcome and rules_outcome.rolled else "")

# pass to state extractor call:
state_msgs = _extract_state_messages(
    env, narration, state,
    active_domains=active_domains,
    scene_result=scene_result,
    rules_outcome=rules_outcome,
    enable_thinking=config.enable_extract_thinking,
    stakes=_stakes,
    band=_band,
    turn_no=turn_no,
)

# pass to progress extractor call:
progress_msgs = _extract_progress_messages(
    env, narration, state,
    active_domains=active_domains,
    state_result=state_result,
    rules_outcome=rules_outcome,
    enable_thinking=config.enable_extract_thinking,
    intent=intent,
    deescalate=deescalate,
    quest_ages=quest_ages or [],
    recent_turns=recent_turns,
    turn_no=turn_no,
    stakes=_stakes,
    band=_band,
)
```

**Validation:** `grep -n "stakes" ccya/engine/extraction.py` — should appear in both message-builder signatures and both call sites.

---

#### Step 2.2 — Fix scene_pressure_add merge source

**File:** `ccya/engine/extraction.py`

**What:** In `_run_extraction_pipeline`, find the block that merges `SceneExtractResult.scene_pressure_add` into the `StateDelta`. Change it to read from `ProgressExtractResult.scene_pressure_add` instead.

**Why:** `SceneExtractResult.scene_pressure_add` no longer exists after Phase 1.

**Current code** (line 654):
```python
scene_pressure_add=scene_result.scene_pressure_add,
```

**Replace with:**
```python
scene_pressure_add=progress_result.scene_pressure_add,
```

Also update `extraction_event["scene"]["output"]` — it is written from `scene_result.model_dump()` at line 458. After Phase 1, the `scene_pressure_add` key will be absent from the scene output (expected). The key will now appear in `extraction_event["progress"]["output"]` instead.

**Validation:** `grep -n "scene_pressure_add" ccya/engine/extraction.py` — should reference only `progress_result.scene_pressure_add` in the merge block.

---

#### Step 2.3 — Wire pending_beat into extract_progress_user.j2 render context

**File:** `ccya/engine/extraction.py`

**What:** The progress user template (Step 3.1 Block C below) references a `pending_beat` variable. This must be passed from `_extract_progress_messages` into the Jinja2 render context.

In `_extract_progress_messages`, add:
```python
pending_beat = (state.get("meta") or {}).get("pending_gm_beat") or None
```

And add `"pending_beat": pending_beat` to the `user_text` render context dict (around line 311).

**Why:** Without this, the `{% if pending_beat %}` block in the template never renders.

**Validation:** In a test with `meta.pending_gm_beat` set, render `_extract_progress_messages` and confirm `pending_beat` data appears in the output.

---

#### Step 2.4 — Implement beat disposition handling in turn.py

**File:** `ccya/engine/turn.py`

**What:** Replace the existing beat storage blocks in both `run_turn` (lines 554-558) and `run_turn_retry` (lines 1070-1073) with disposition-aware logic.

**Current code** (both locations):
```python
# Store gm_beat for next turn's narration (produced by progress extractor)
if progress_result and progress_result.gm_beat and progress_result.gm_beat.type:
    _beat_dict = progress_result.gm_beat.model_dump(exclude_none=True)
    _beat_dict["beat_expires_turn"] = turn_no + 2
    state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict
```

**Replace with** (both `run_turn` and `run_turn_retry`):
```python
# Beat lifecycle: handle disposition from progress extractor
_new_beat = progress_result.gm_beat if progress_result else None
_disposition = progress_result.beat_disposition if progress_result else "consume"
_current_beat = (state.get("meta") or {}).get("pending_gm_beat")

if _disposition == "carry" and _current_beat and not _new_beat:
    # Keep existing beat — do not overwrite
    pass
elif _new_beat and _new_beat.type:
    # Replace or fresh write (includes implicit replace when carry+new_beat)
    _beat_dict = _new_beat.model_dump(exclude_none=True)
    _beat_dict["beat_expires_turn"] = turn_no + 2
    state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict
else:
    # consume or no new beat — clear
    state.setdefault("meta", {})["pending_gm_beat"] = None
```

**Why:** The current code unconditionally overwrites `pending_gm_beat` whenever `progress_result.gm_beat` is set. With beat_disposition, we need three behaviors:
- `carry`: keep existing beat (only when no new beat is emitted)
- `consume`: clear beat (default, when no new beat or explicit consume)
- `replace`: overwrite with new beat (when new beat is emitted)

**Edge case handling:**
- If `beat_disposition == "carry"` but `_new_beat` is also non-null → falls through to `elif` and replaces (implicit replace, per firm decision #3).
- If `beat_disposition == "carry"` but `_current_beat` is None → falls through to `else` and sets None (no beat to carry).
- If `progress_result` is None (extraction failed) → defaults to `"consume"`, clears beat.

**Validation:**
- In a test: set `meta.pending_gm_beat` with a valid beat. Have progress_result with `beat_disposition="carry"`, `gm_beat=None`. Assert `pending_gm_beat` is unchanged after turn.
- In a test: progress_result with `beat_disposition="replace"` and a new `gm_beat`. Assert new beat overwrites old.
- In a test: progress_result with `beat_disposition="consume"` and `gm_beat=None`. Assert `pending_gm_beat` is cleared.

---

### Tests to write or update

**File:** `tests/test_extraction.py`

- `test_progress_messages_receives_stakes_and_band` — call `_extract_progress_messages` with `stakes="wounded + guard raises alarm"`, `band="fail"`. Assert rendered user message contains both strings.
- `test_state_messages_receives_stakes_and_band` — same pattern for `_extract_state_messages`.
- `test_scene_pressure_add_from_progress` — build a `ProgressExtractResult` with `scene_pressure_add=[ScenePressure(...)]` and `SceneExtractResult()` (no add). Run through the merge block. Assert `StateDelta.scene_pressure_add` contains the pressure.
- `test_progress_messages_receives_deescalate_float` — assert `deescalate=0.6` appears in rendered output.
- `test_progress_messages_receives_pending_beat` — call `_extract_progress_messages` with `meta.pending_gm_beat` set. Assert `pending_beat` appears in rendered user message.

**File:** `tests/test_turn.py`

- `test_beat_carry_disposition` — progress_result with `beat_disposition="carry"`, `gm_beat=None`, existing beat in meta. Assert beat is unchanged after turn.
- `test_beat_replace_disposition` — progress_result with `beat_disposition="replace"` and a new `gm_beat`. Assert new beat overwrites old.
- `test_beat_consume_disposition` — progress_result with `beat_disposition="consume"`, `gm_beat=None`. Assert `pending_gm_beat` is cleared.
- `test_beat_carry_with_new_beat_implicit_replace` — progress_result with `beat_disposition="carry"` but also a new `gm_beat`. Assert new beat replaces old (implicit replace).
- `test_beat_disposition_none_progress_result` — extraction fails, progress_result is None. Assert beat is cleared (default consume).

### REPOMAP updates required

`docs/REPOMAP/engine.md`: update `_extract_progress_messages`, `_extract_state_messages`, `_run_extraction_pipeline` signatures; update `run_turn`/`run_turn_retry` beat disposition handling description.

### Risks

1. **`extraction_event` telemetry.** The `extraction_event["scene"]["output"]` dict (from `scene_result.model_dump()`) no longer contains `scene_pressure_add`. If the turn viewer (`server/tv.py`) or eval harness reads this key from the scene stream output, it will silently get a KeyError or absent key. The key moves to `extraction_event["progress"]["output"]["scene_pressure_add"]`. Check `server/tv.py` and `eval/` for references to `scene_pressure_add` in extraction event data.
2. **`run_turn_retry` beat disposition.** The `run_turn_retry` function already reads from `progress_result` (line 1070). The replacement code in Step 2.4 applies to both functions identically.
3. **Beat disposition default on missing field.** If an older state snapshot has `pending_gm_beat` without `beat_expires_turn`, the expiry guard will see `_expires = None` and skip the check — this is safe (TTL-less beats carry forward until explicitly consumed).

---

## Phase 3: Prompt templates

### Context files to load
- `ccya/prompts/extract_progress_user.j2`
- `ccya/prompts/extract_progress_system.j2`
- `ccya/prompts/extract_scene_system.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/models.py` (Phase 1 complete)

### Overview

Four template changes: fix progress prior-turn index guard, add stakes/band/deescalate/gm_beat/pressure blocks to progress, add stakes/band hint to state, remove scene_pressure_add from scene system prompt.

**Note:** Steps 3.1 (rules_user.j2 truncation) and 3.2 (prior-turn index) are **already done** — `rules_user.j2` emits full narration, and `extract_progress_user.j2` uses `recent_turns[-1]`. Only the `>= 2` guard needs to change to `>= 1`.

---

#### Step 3.1 — Fix extract_progress_user.j2 prior-turn index guard

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Change the guard on line 51 from `>= 2` to just check that recent_turns is non-empty.

**Current** (line 51):
```jinja2
{% if recent_turns and recent_turns | length >= 2 -%}
```

**Replace with:**
```jinja2
{% if recent_turns -%}
```

**Why:** `extraction.py` passes `recent_turns[-2:]` (last 2 turns), so `recent_turns[-1]` is the most recent prior turn. The old `>= 2` guard was correct when reading `[-2]` but is overly restrictive now that we read `[-1]`. A single-turn context should still show the prior turn's narration.

---

#### Step 3.2 — Add context blocks to extract_progress_user.j2

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** The template currently has a minimal `## deescalate` block at lines 66-70 that just outputs `{{ deescalate }}`. Replace that block and add three additional blocks before `## CURRENT TURN NARRATION` (line 77). Order: replace deescalate block with Block B, then insert Blocks A, C, D before it.

**Block A — stakes + band:**
```jinja2
{% if stakes and band -%}
## rules_stakes
Band: {{ band | upper }}. At-risk cost named by rules engine: {{ stakes }}
{% if band in ("crit_fail", "fail") -%}
If a narrative consequence is named above (e.g. an NPC acting, alarm raised, escape cut off), emit it as a scene_pressure_add entry at `immediate` urgency.
{% elif band == "crit_success" -%}
If a named entity was thwarted, consider a gm_beat of type `opportunity` or `escalation` naming that entity's reaction.
{% endif -%}

{% endif -%}
```

**Block B — deescalate:**
```jinja2
{% if deescalate > 0 -%}
## deescalate
A pressure resolved this turn (magnitude: {{ "%.1f"|format(deescalate) }}).
{% if deescalate >= 0.8 -%}
Strong deescalation. Prefer `breathing_room` beat type or no beat. Do not add new immediate pressures.
{% else -%}
Partial deescalation. Prefer low-urgency beat or no beat.
{% endif -%}

{% endif -%}
```

**Block C — gm_beat instruction (with beat_disposition):**
```jinja2
## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

{% if pending_beat -%}
## pending_beat (carried from previous turn — not yet surfaced)
Type: {{ pending_beat.type }} | Expires: T{{ pending_beat.beat_expires_turn }}
Instruction: {{ pending_beat.instruction }}
{% endif -%}
```

**Block D — scene_pressure_add instruction:**
```jinja2
## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
```

**Validation:** Render the progress extraction prompt with a test state that has stakes, deescalate=0.6, and a pending beat. Confirm all four blocks appear appropriately.

---

#### Step 3.3 — Add stakes/band hint to extract_state_user.j2

**File:** `ccya/prompts/extract_state_user.j2`

**What:** Add a `rules_stakes_hint` block before the `## CURRENT TURN NARRATION` section (before line 49).

```jinja2
{% if stakes and band in ("setback", "fail", "crit_fail") -%}
## rules_stakes_hint
Rules engine named this cost on failure: {{ stakes }}
If the narration is ambiguous, treat any condition name in the above as a strong signal to apply it.
{% endif -%}
```

**Why:** State extractor independently infers conditions from prose. When the rules LLM already named the condition (e.g. "wounded") in stakes, the state extractor should not have to guess.

**Validation:** Pass `stakes="wounded + ally exposure"`, `band="fail"` in a test render of `extract_state_user.j2`. Confirm the hint block appears.

---

#### Step 3.4 — Update extract_progress_system.j2 output schema

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Add `beat_disposition` and `scene_pressure_add` to the JSON output schema section (lines 6-14) and add field rules.

**Current schema** (lines 6-14):
```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [],
  "outcome_summary": "",
  "gm_beat": null
}
```

**Replace with:**
```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [],
  "outcome_summary": "",
  "gm_beat": null,
  "beat_disposition": "consume",
  "scene_pressure_add": []
}
```

Add field rules after the existing `gm_beat` rules (after line 53):

```
`beat_disposition`: controls what happens to the pending_gm_beat from the previous turn. Values: `"consume"` (default) — beat is cleared after narration; `"carry"` — beat stays in meta.pending_gm_beat unchanged for the next turn; `"replace"` — the new gm_beat above supersedes the carried one. If you emit a new gm_beat, use `"replace"`. If you want to preserve an unsurfaced beat, emit `"carry"` and leave gm_beat null.
```

```
`scene_pressure_add`: new scene pressures generated from story causality this turn. Each: `{"id": "snake_case_id", "text": "Threat description", "urgency": "immediate|building|background", "turn_added": <CURRENT_TURN>}`. Add pressure when a named NPC/faction acts against the player off-screen, a quest deadline triggers, or a failed roll's consequence activates. Do NOT add pressure for resolved threats or vague ambient danger.
```

**Why:** The LLM will not emit fields it has not been told to emit in the schema section.

**Validation:** Inspect the rendered system prompt in a test run. Confirm both fields appear in the schema description.

---

#### Step 3.5 — Remove scene_pressure_add from extract_scene_system.j2

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Remove the `scene_pressure_add` entry from the output schema (line 16) and the field rules section (lines 78-78). Retain `scene_pressure_update` and `scene_pressure_remove` instructions unchanged.

**Current schema** (lines 8-20):
```json
{
  "scene_tags": [],
  "scene_tagline": "",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": null
}
```

**Remove** `"scene_pressure_add": [],` from the schema.

**Remove** the entire `scene_pressure_add` field rules paragraph (line 78):
```
`scene_pressure_add`: Add a `scene_pressure` entry when the narration introduces a time-sensitive threat...
```

**Why:** Scene extractor no longer emits `scene_pressure_add`. If the schema entry stays, the LLM may still try to emit it, which will be silently ignored by the Pydantic model — but it wastes tokens and can confuse the model about its own scope.

**Validation:** `grep -n "pressure_add" ccya/prompts/extract_scene_system.j2` — should return no results.

---

### Tests to write or update

**File:** `tests/test_prompts.py` (create if not present)

- `test_progress_prior_turn_correct_index` — render `extract_progress_user.j2` with `recent_turns=[turn_A, turn_B]`. Assert `turn_B.narrative` appears, not `turn_A.narrative`.
- `test_progress_stakes_block_fail` — render with `stakes="wounded", band="fail"`. Assert stakes block renders with `immediate urgency` instruction.
- `test_progress_stakes_block_crit_success` — render with `stakes="guard thwarted", band="crit_success"`. Assert NPC reaction beat suggestion appears.
- `test_progress_deescalate_block` — render with `deescalate=1.0`. Assert strong deescalation wording appears.
- `test_progress_pending_beat_block` — render with `meta.pending_gm_beat` set. Assert pending beat type and instruction appear in output.
- `test_state_stakes_hint_fail` — render `extract_state_user.j2` with `stakes="wounded", band="fail"`. Assert hint block renders.
- `test_state_stakes_hint_success` — render with `band="success"`. Assert hint block does NOT render.
- `test_progress_system_schema_has_beat_disposition` — render `extract_progress_system.j2`. Assert `beat_disposition` appears in schema section.
- `test_progress_system_schema_has_scene_pressure_add` — render `extract_progress_system.j2`. Assert `scene_pressure_add` appears in schema section.
- `test_scene_system_no_pressure_add` — render `extract_scene_system.j2`. Assert `scene_pressure_add` does NOT appear anywhere.

### REPOMAP updates required

`docs/REPOMAP/prompts.md`: update entries for `extract_progress_user.j2`, `extract_progress_system.j2`, `extract_scene_system.j2`, `extract_state_user.j2`.

### Risks

1. **Token budget.** The new blocks in `extract_progress_user.j2` add approximately 200–400 tokens per turn (stakes block, deescalate block, gm_beat/beat_disposition block, scene_pressure_add block). Measure rendered prompt size after Phase 3 and compare against `config.prompt_token_budget`. If the progress prompt is approaching the budget, consider shortening the `## gm_beat` instruction prose.
2. **`pending_beat` exposure.** The template now shows the pending beat's `instruction` text to the progress LLM. This is intentional — the LLM needs to read it to decide whether to carry or replace. Ensure this does not create a loop where the LLM re-emits the same instruction verbatim as a new beat.
3. **`extract_scene_system.j2` structural dependencies.** The scene system prompt may have a numbered or bulleted field list. Removing `scene_pressure_add` must not leave a dangling reference or break the list numbering.

---

## Phase 4: Eval harness updates

### Context files to load
- `evals/scenarios/gm_beat_lifecycle.py`
- `evals/universal_asserts.py` (if exists)
- `evals/runs/*/full_cycle.trace.md` (for reference)

### Overview

The eval harness needs updates to account for the new `beat_disposition` field and the `scene_pressure_add` migration from scene to progress stream output.

---

#### Step 4.1 — Update gm_beat_lifecycle scenario

**File:** `evals/scenarios/gm_beat_lifecycle.py`

**What:** The current scenario verifies that `pending_gm_beat` is set by extract.progress, surfaced in the next narration, and consumed after narration. With beat_disposition, the carry behavior means the beat may persist beyond 1 turn if the progress extractor emits `beat_disposition: "carry"`.

Update the scenario to:
1. Assert `beat_disposition` is present in the progress extraction output.
2. When testing carry behavior, assert that `pending_gm_beat` persists when `beat_disposition == "carry"`.
3. When testing consume behavior, assert that `pending_gm_beat` is cleared when `beat_disposition == "consume"`.

**Current scenario structure** (from grep):
```python
description="Verifies pending_gm_beat lifecycle.
1. extract.progress generates a pending_gm_beat
2. Narrator surfaces it in narration
3. Beat is consumed after narration
Uses state_yaml assertions to check state_snapshot for pending_gm_beat."
```

**Updated assertions to add:**
- After the progress extraction turn: `TurnAssert(stream="extract.progress", field="beat_disposition.present")`
- When testing carry: `TurnAssert(stream="state_yaml", field="pending_gm_beat.present")` (beat should persist)
- When testing consume: `TurnAssert(stream="state_yaml", field="pending_gm_beat.absent")` (beat should be cleared)

---

#### Step 4.2 — Check universal asserts for scene_pressure_add

**File:** `evals/universal_asserts.py` (if exists)

**What:** Check if any universal assertions read `scene_pressure_add` from the scene stream extraction output. If so, update them to read from the progress stream instead.

**Note:** The `applied` dict in `events.jsonl` still contains `scene_pressure_add` (from `StateDelta`), so assertions that check the applied state are unaffected. Only assertions that read from `extraction.scene.output` need updating.

---

### Risks

1. **Eval trace files are static.** The existing trace files (`evals/runs/*/full_cycle.trace.md`) contain `scene_pressure_add` in the scene stream output. These are historical records and should not be modified. New eval runs will have the updated schema.
2. **gm_beat_lifecycle scenario depends on LLM behavior.** The carry/consume behavior depends on the LLM emitting the correct `beat_disposition` value. If the LLM doesn't emit it (defaults to "consume"), the carry test will fail. Consider adding a mock LLM path for deterministic testing.

---

## Pre-existing issues (out of scope)

These issues exist in the codebase but are NOT addressed by this plan. They should be fixed in a separate plan.

1. **`surface_as` value mismatch in `extract_progress_system.j2`.** The system prompt lists `surface_as` values as `dialogue`, `environmental`, `player_discovery`, `item`, `npc_action` (line 50). The `GMBeat` model has `Literal["ambient", "event", "npc_behavior", "environmental", "player_discovery", "item"]`. The prompt's `dialogue` and `npc_action` do not exist in the model; `ambient`, `event`, and `npc_behavior` are missing from the prompt. This causes the LLM to potentially emit invalid `surface_as` values that get silently dropped by Pydantic.

2. **`turn_added` on `scene_pressure_add`.** The system prompt instructs the LLM to set `"turn_added": <CURRENT_TURN>`, but the `ScenePressure` model defaults to `turn_added: int = 0`. The engine's `apply_delta` in `state/delta.py` line 381 uses `press.turn_added or current_turn`, so a `0` value gets stamped with the current turn. This works but is inconsistent with how `recent_events_add` is handled (engine explicitly stamps turn on the model). Consider adding similar stamping logic for `scene_pressure_add` in `_run_extraction_pipeline`.

3. **`extract_progress_user.j2` deescalate block.** The existing block (lines 66-70) just outputs `{{ deescalate }}` as a raw number. The new Block B provides structured guidance. This plan replaces it, but the old block's presence suggests the deescalate context was always intended to be more informative than a raw number.

---

## Ambiguities requiring resolution before execution

1. **`_run_extraction_pipeline` merge location — RESOLVED.** Confirmed via grep that `scene_pressure_add` is merged in `extraction.py` line 654 from `scene_result.scene_pressure_add` into `StateDelta`. The change is a simple source swap to `progress_result.scene_pressure_add`. No merge logic in `state/delta.py` — it just applies whatever `StateDelta.scene_pressure_add` contains.

2. **`pending_beat` variable name in `extract_progress_user.j2` — RESOLVED.** Step 3.2 Block C uses `pending_beat` as the Jinja2 variable name. `meta.pending_gm_beat` is a dict (per `model_dump()`), so the template accesses `pending_beat.type`, `pending_beat.beat_expires_turn`, `pending_beat.instruction`. These keys exist: `beat_expires_turn` is added by `turn.py` as a plain dict key, and the rest come from `GMBeat.model_dump(exclude_none=True)`. Step 2.3 wires `pending_beat` into the render context.

3. **`extraction_event` schema for progress stream — RESOLVED.** The progress stream event dict is written from `progress_result.model_dump()` at line 568. After Phase 1, this will now include `beat_disposition` and `scene_pressure_add`. The turn viewer (`server/tv.py`) reads from `extraction_event` — verify it handles the new fields gracefully (it should, as it likely just displays whatever keys are present).

4. **`extract_progress_system.j2` schema section format — RESOLVED.** The schema is a JSON block at lines 6-14 with field rules as prose below. New fields are added to both the JSON block and the prose rules section.

5. **`run_turn_retry` `scene_result` read — RESOLVED.** `run_turn_retry` already reads from `progress_result` (line 1070), not `scene_result`. The beat disposition handling in Step 2.4 applies to both functions identically.

6. **`deescalate=False` in `run_turn_retry` — RESOLVED.** `run_turn_retry` passes `deescalate=False` (lines 968, 1065). Since `deescalate` is now `float`, `False` coerces to `0.0` in Python. This is correct — retry should skip deescalation awareness since the rules outcome is already fixed.

7. **Beat expiry guard placement in `run_turn_retry` — RESOLVED.** Both `run_turn` (line 414) and `run_turn_retry` (line 927) have the beat expiry guard before the narration call. `turn_no` is computed before the guard in both functions.

---

## TODO.md update

Under **P2 — Interesting Storytelling**, add:

```
- [ ] **Narrative mechanics overhaul** — beat carry/consume disposition, pressure ownership to progress, stakes routing to extractors — [`docs/plans/narrative-mechanics-overhaul.md`](docs/plans/narrative-mechanics-overhaul.md)
```

Mark `progress-rules-narration.md` as superseded:

```
- ~~**GM beat ownership migration + deescalate float + beat expiry + rules full narration** — superseded by `narrative-mechanics-overhaul.md`~~
```

---

## Execution order summary

Execute phases in order: 1 → 2 → 3 → 4.

**Phase 1** (models): 2 steps. Add `beat_disposition` + `scene_pressure_add` to `ProgressExtractResult`, remove `scene_pressure_add` from `SceneExtractResult`.

**Phase 2** (extraction wiring): 4 steps. Pass stakes/band to extractors, swap merge source, wire pending_beat, implement beat disposition in turn.py.

**Phase 3** (prompts): 5 steps. Fix index guard, add 4 context blocks to progress, add stakes hint to state, update progress system schema, remove scene_pressure_add from scene system.

**Phase 4** (eval): 2 steps. Update gm_beat_lifecycle scenario, check universal asserts.

**Total: 13 steps across 4 phases.**
