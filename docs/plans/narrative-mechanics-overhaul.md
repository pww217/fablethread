# Narrative Mechanics Overhaul

## Status
`open`

## Part of
standalone

## Dependencies
- `docs/plans/progress-rules-narration.md` — Phases 1–2 of that plan are marked done in TODO.md. This plan **supersedes the remaining open items** in that plan: full rules narration (item 9), beat carry/consume disposition, and the `prior_turn_narration` index bug. Those items are folded into Phase 1 and 2 here. Do not execute remaining phases of `progress-rules-narration.md` — use this plan instead.
- `docs/plans/TODO.md` open item: `Fix condition dedup` (eval-remediation Phase 1) — independent; no conflict.

## Conflicts and overlap
- **`progress-rules-narration.md`** (open): overlaps on `rules_user.j2` narration truncation fix (its item 9), `deescalate` float wiring (its Phase 2), `beat_expires_turn` guard (its Phase 2), and `extract_progress_user.j2` gm_beat block (its Ambiguity 2). Per inspection of `ccya/models.py`, the model changes from that plan's Phase 1 are **already merged** (GMBeat new types, ProgressExtractResult.gm_beat, SceneExtractResult without gm_beat). The extraction pipeline wiring (Phase 2) appears **not yet done** — `_extract_progress_messages` does not yet receive `deescalate`/`quest_ages`, and `turn.py` still reads from `scene_result.gm_beat`. This plan completes that wiring and extends it with the new mechanics below. Mark `progress-rules-narration.md` abandoned after this plan ships.

---

## Objective

This plan implements five interconnected narrative improvements identified in design review:

1. **Beat carry/consume disposition** — beats persist across turns until progress explicitly marks them consumed, rather than being cleared after any narration turn regardless of use.
2. **Pressure ownership migration** — `scene_pressure_add` moves from `SceneExtractResult` to `ProgressExtractResult`; scene extractor retains only `_remove` and `_update`. Rules engine reads pressure as context for difficulty; progress generates new pressure from story causality.
3. **Stakes → pressure + condition routing** — `intent.stakes` and `outcome.band` are passed to progress and state extractors so they can enforce the mechanical cost the rules LLM named, rather than inferring it independently from narration prose.
4. **Rules narration context fix** — `rules_user.j2` truncates prior narration to 120 chars. Remove the truncation; emit full `t.narrative`.
5. **Progress `prior_turn_narration` index fix** — `extract_progress_user.j2` reads `recent_turns[-2]` (the turn before last) instead of `recent_turns[-1]` (the most recent). Fix the index.

---

## Non-goals

- Does not implement personality traits or NPC disposition scores (separate future plan).
- Does not implement consequence chains on `ScenePressure` (`cascade_to` field) — deferred.
- Does not change `build_directive()` in `rules.py` or any deterministic dice logic.
- Does not change the narrator's consumption of `pending_gm_beat` in `narrate_user.j2` — only the production and lifecycle change.
- Does not change `StateDelta` field list — all new fields are merge-additive from existing sources.
- Does not change compaction, chronicle, or any persistence path other than `meta.pending_gm_beat` and the extraction result models.
- Does not change eval harness, rubric, or judge.
- Item 22 (NPC relationship scores) is explicitly deferred and not included.

---

## Affected files

| File | Change type | Summary of change |
|---|---|---|
| `ccya/models.py` | modify | Add `beat_disposition` to `ProgressExtractResult`; add `scene_pressure_add` to `ProgressExtractResult`; remove `scene_pressure_add` from `SceneExtractResult` |
| `ccya/engine/extraction.py` | modify | Widen `deescalate: bool → float` throughout; pass `deescalate`, `quest_ages`, `intent.stakes`, `outcome.band` to progress messages; pass `intent.stakes`, `outcome.band` to state messages; move `scene_pressure_add` source from scene to progress in merge; complete beat gm_beat source read from progress_result |
| `ccya/engine/turn.py` | modify | Widen `deescalate: bool → float`; compute float magnitude; add beat expiry guard pre-narration; store `beat_expires_turn`; read `gm_beat` from `progress_result` |
| `ccya/engine/narrate.py` | modify | Widen `deescalate: bool → float` in `_narrate_messages` signature |
| `ccya/prompts/rules_user.j2` | modify | Remove 120-char truncation; emit full `t.narrative` |
| `ccya/prompts/extract_progress_user.j2` | modify | Fix `recent_turns[-2]` → `recent_turns[-1]`; add `deescalate`/`quest_ages` context block; add `stakes`/`band` context block; add `gm_beat` instruction block with `beat_disposition` output; add `scene_pressure_add` instruction block |
| `ccya/prompts/extract_progress_system.j2` | modify | Add `scene_pressure_add` to output schema; add `beat_disposition` to output schema |
| `ccya/prompts/extract_scene_system.j2` | modify | Remove `scene_pressure_add` from output schema and instructions |
| `ccya/prompts/extract_state_user.j2` | modify | Add `stakes` and `band` context block |
| `docs/REPOMAP/models.md` | update | Reflect `ProgressExtractResult` new fields; reflect `SceneExtractResult` removed `scene_pressure_add` |
| `docs/REPOMAP/engine.md` | update | Reflect changed signatures in extraction.py and turn.py |
| `docs/plans/TODO.md` | update | Add this plan; mark `progress-rules-narration.md` superseded |

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
10. **`deescalate` float magnitude mapping:** `crit_success` with active `immediate`/`building` pressure → `1.0`; `success` with same → `0.6`; everything else → `0.0`.
11. **`rules_user.j2` full narration.** The truncated `t.narrative[-120:]` is replaced with the full `t.narrative`. The `{% if t.narrative | length > 120 %}… {% endif %}` prefix guard is also removed.
12. **`extract_progress_user.j2` index fix.** `recent_turns[-2]` becomes `recent_turns[-1]`. The template already guards with `{% if recent_turns and recent_turns | length >= 2 %}` — change the bound to `>= 1` to match the new index and not silently skip single-turn contexts.

---

## Implementation — Phase 1: Models

### Context files to load
- `ccya/models.py`

### Overview

Add `beat_disposition` and `scene_pressure_add` to `ProgressExtractResult`. Remove `scene_pressure_add` from `SceneExtractResult`. No other model changes — GMBeat, ProgressExtractResult.gm_beat, and the validator are already in place from the prior plan.

### Detailed steps

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

---

## Implementation — Phase 2: Extraction pipeline wiring

### Context files to load
- `ccya/engine/extraction.py`
- `ccya/engine/turn.py`
- `ccya/engine/narrate.py`
- `ccya/models.py` (Phase 1 complete)

### Overview

Four changes in this phase: (1) complete the `deescalate` bool→float wiring throughout the pipeline, (2) pass `stakes`/`band` to progress and state extractors, (3) fix `scene_pressure_add` merge source, (4) add beat lifecycle management (expiry guard, `beat_disposition` handling, `beat_expires_turn` storage).

---

#### Step 2.1 — Widen deescalate bool→float in extraction.py

**File:** `ccya/engine/extraction.py`

**What:** Change `deescalate: bool = False` to `deescalate: float = 0.0` on `_extract_scene_messages`, `_extract_progress_messages`, and `_run_extraction_pipeline`. All three already have the parameter — only the type annotation changes.

**Why:** Float magnitude is needed so progress and narrate templates can distinguish a strong deescalation (crit_success) from a mild one.

**Code Snippet** (signature lines only — bodies are unchanged except where noted in later steps):
```python
def _extract_scene_messages(
    env: Environment,
    narration: str,
    state: dict[str, Any],
    *,
    active_domains: list[str],
    rules_outcome: "RulesOutcome | None" = None,
    enable_thinking: bool = False,
    deescalate: float = 0.0,          # was: bool = False
    quest_ages: list[dict[str, Any]] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
```

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
    deescalate: float = 0.0,          # was: bool = False
    quest_ages: list[dict[str, Any]] = [],
    recent_turns: list[dict[str, Any]] | None = None,
    turn_no: int = 0,
) -> list[dict[str, str]]:
```

```python
async def _run_extraction_pipeline(
    env: "Environment",
    state: dict[str, Any],
    narration: str,
    *,
    active_domains: list[str],
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    config: "EngineConfig",
    trace_id: str,
    turn_no: int,
    deescalate: float = 0.0,          # was: bool = False
    quest_ages: list[dict[str, Any]] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
) -> tuple[...]:
```

**Validation:** `make check` — mypy accepts float at all call sites.

---

#### Step 2.2 — Add stakes and band to progress and state message builders

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

#### Step 2.3 — Fix scene_pressure_add merge source

**File:** `ccya/engine/extraction.py`

**What:** In `_run_extraction_pipeline`, find the block that merges `SceneExtractResult.scene_pressure_add` into the `StateDelta`. Change it to read from `progress_result.scene_pressure_add` instead.

**Why:** `SceneExtractResult.scene_pressure_add` no longer exists after Phase 1.

Locate the merge block. It will look approximately like:
```python
# Current (approximate):
scene_pressure_add=scene_result.scene_pressure_add,
```

Replace with:
```python
scene_pressure_add=progress_result.scene_pressure_add,
```

Also update `extraction_event["scene"]["output"]` — if it is written from `scene_result.model_dump()`, the `scene_pressure_add` key will now be absent (expected). Confirm no assertions in tests key on `extraction_event["scene"]["output"]["scene_pressure_add"]`.

**Validation:** `grep -n "scene_pressure_add" ccya/engine/extraction.py` — should reference only `progress_result.scene_pressure_add` in the merge block.

---

#### Step 2.4 — Implement beat lifecycle in turn.py

**File:** `ccya/engine/turn.py`

**What:** Four sub-changes:

**2.4a — Widen deescalate to float in run_turn and run_turn_retry**

```python
# Replace the existing bool deescalate block:
deescalate: float = 0.0
if config and config.scene_pressure_deescalate_on_success:
    if (
        outcome.rolled
        and outcome.band in ("success", "crit_success")
        and any(
            p.get("urgency") in ("immediate", "building")
            for p in (state.get("scene") or {}).get("scene_pressure") or []
        )
    ):
        deescalate = 1.0 if outcome.band == "crit_success" else 0.6
```

**2.4b — Pre-narration beat expiry guard**

Insert immediately before the `_narrate_messages` call in both `run_turn` and `run_turn_retry`:

```python
_pending_beat = (state.get("meta") or {}).get("pending_gm_beat")
if _pending_beat:
    _expires = _pending_beat.get("beat_expires_turn")
    if _expires is not None and turn_no > _expires:
        _pending_beat = None
        state.setdefault("meta", {})["pending_gm_beat"] = None
```

`turn_no` must be computed before this block. In `run_turn_retry` it may be computed later — move the `turn_no = state.get("meta", {}).get("turn", 0) + 1` assignment above the narration call if needed.

**2.4c — Read gm_beat from progress_result, handle beat_disposition**

Replace the existing block that stores `pending_gm_beat` (which currently reads from `scene_result.gm_beat`) in both `run_turn` and `run_turn_retry`:

```python
# Beat lifecycle: handle disposition from progress extractor
_new_beat = progress_result.gm_beat if progress_result else None
_disposition = progress_result.beat_disposition if progress_result else "consume"
_current_beat = (state.get("meta") or {}).get("pending_gm_beat")

if _disposition == "carry" and _current_beat and not _new_beat:
    # Keep existing beat — do not overwrite
    pass
elif _new_beat and _new_beat.type:
    # Replace or fresh write
    _beat_dict = _new_beat.model_dump(exclude_none=True)
    _beat_dict["beat_expires_turn"] = turn_no + 2
    state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict
else:
    # consume or no new beat — clear
    state.setdefault("meta", {})["pending_gm_beat"] = None
```

**2.4d — Widen deescalate in _run_extraction_pipeline call site**

Ensure the call to `_run_extraction_pipeline` in both `run_turn` and `run_turn_retry` passes `deescalate=deescalate` where `deescalate` is now a float. This should already be happening — confirm the kwarg is present and not hardcoded to `False`.

**Validation:**
- `make check` — mypy accepts float deescalate at all call sites.
- In a test: set `meta.pending_gm_beat = {"type": "complication", "instruction": "A named entity does something specific and concrete here", "beat_expires_turn": 0}`. Run a turn with `meta.turn = 2`. Assert `pending_gm_beat` is `None` after narration (expiry guard fired).
- In a test: progress_result with `beat_disposition="carry"` and `gm_beat=None`. Assert existing `pending_gm_beat` is unchanged.

---

#### Step 2.5 — Widen deescalate in narrate.py

**File:** `ccya/engine/narrate.py`

**What:** Change `deescalate: bool = False` to `deescalate: float = 0.0` in `_narrate_messages` signature.

**Why:** `narrate_user.j2` uses `{% if deescalate %}` — `0.0` evaluates as falsy in Jinja2; `0.6`/`1.0` evaluate as truthy. No template change needed.

**Code Snippet** (signature line only):
```python
def _narrate_messages(
    env: Any,
    state: dict[str, Any],
    user_input: str,
    *,
    # ... other params ...
    deescalate: float = 0.0,
    # ... remaining params ...
) -> list[dict[str, str]]:
```

**Validation:** `make check`.

---

### Tests to write or update

**File:** `tests/test_extraction.py`

- `test_progress_messages_receives_stakes_and_band` — call `_extract_progress_messages` with `stakes="wounded + guard raises alarm"`, `band="fail"`. Assert rendered user message contains both strings.
- `test_state_messages_receives_stakes_and_band` — same pattern for `_extract_state_messages`.
- `test_scene_pressure_add_from_progress` — build a `ProgressExtractResult` with `scene_pressure_add=[ScenePressure(...)]` and `SceneExtractResult()` (no add). Run through the merge block. Assert `StateDelta.scene_pressure_add` contains the pressure.
- `test_progress_messages_receives_deescalate_float` — assert `deescalate=0.6` appears in rendered output.

**File:** `tests/test_turn.py`

- `test_beat_expiry_guard` — set `meta.pending_gm_beat` with `beat_expires_turn` in the past. Run turn. Assert beat is cleared before narration.
- `test_beat_carry_disposition` — progress_result with `beat_disposition="carry"`, `gm_beat=None`, existing beat in meta. Assert beat is unchanged after turn.
- `test_beat_replace_disposition` — progress_result with `beat_disposition="replace"` and a new `gm_beat`. Assert new beat overwrites old.
- `test_deescalate_float_crit_success` — active immediate pressure, `crit_success` band. Assert `deescalate == 1.0` passed to extraction pipeline.
- `test_deescalate_float_success` — active immediate pressure, `success` band. Assert `deescalate == 0.6`.
- `test_deescalate_zero_no_pressure` — no pressure. Assert `deescalate == 0.0`.

### REPOMAP updates required

`docs/REPOMAP/engine.md`: update `_extract_progress_messages`, `_extract_state_messages`, `_run_extraction_pipeline` signatures; update `run_turn`/`run_turn_retry` beat lifecycle description.

### Risks

1. **`extraction_event` telemetry.** The `extraction_event["scene"]["output"]` dict (from `scene_result.model_dump()`) no longer contains `scene_pressure_add`. If the turn viewer or eval harness reads this key from the scene stream output, it will silently get an empty list or KeyError. Check `server/tv.py` and `eval/` for references to `scene_pressure_add` in extraction event data.
2. **`run_turn_retry` `turn_no` placement.** In `run_turn_retry`, verify `turn_no` is computed before the pre-narration expiry guard in Step 2.4b. If it is currently computed after the narration call, move the assignment.
3. **Beat disposition default on missing field.** If an older state snapshot has `pending_gm_beat` without `beat_expires_turn`, the expiry guard will see `_expires = None` and skip the check — this is safe (TTL-less beats carry forward until explicitly consumed).

---

## Implementation — Phase 3: Prompt templates

### Context files to load
- `ccya/prompts/rules_user.j2`
- `ccya/prompts/extract_progress_user.j2`
- `ccya/prompts/extract_progress_system.j2`
- `ccya/prompts/extract_scene_system.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/models.py` (Phase 1 complete)

### Overview

Five template changes: fix rules narration truncation, fix progress prior-turn index, add stakes/band/deescalate/gm_beat/pressure blocks to progress, add stakes/band hint to state, remove scene_pressure_add from scene system prompt.

---

#### Step 3.1 — Fix rules_user.j2 narration truncation

**File:** `ccya/prompts/rules_user.j2`

**What:** Replace the truncated last-turn block.

**Current:**
```jinja2
{%- if recent_turns %}
## last_turn (tail of the most recent narrative)
{%- set t = recent_turns[-1] %}
T{{ t.turn }}: {{ t.input }} — {% if t.narrative | length > 120 %}… {% endif %}{{ t.narrative[-120:] }}

{% endif -%}
```

**Replace with:**
```jinja2
{%- if recent_turns %}
## last_turn
{%- set t = recent_turns[-1] %}
T{{ t.turn }}: {{ t.input }}
{{ t.narrative }}

{% endif -%}
```

**Why:** The rules engine needs full narrative context to distinguish continuation from new action, track ongoing threads, and gauge whether a player's claim asserts an already-established outcome.

**Validation:** Run a turn and inspect `prompts.log` (or the `log_llm_io` output). The rules request should contain the full prior narration, not a 120-char tail.

---

#### Step 3.2 — Fix extract_progress_user.j2 prior-turn index

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Fix the `prior_turn_narration` block.

**Current:**
```jinja2
{% if recent_turns and recent_turns | length >= 2 -%}
## prior_turn_narration (T{{ recent_turns[-2].turn }} — for outcome_summary and actions context)
{{ recent_turns[-2].narrative }}

{% endif -%}
```

**Replace with:**
```jinja2
{% if recent_turns -%}
## prior_turn_narration (T{{ recent_turns[-1].turn }} — for outcome_summary and actions context)
{{ recent_turns[-1].narrative }}

{% endif -%}
```

**Why:** `extraction.py` passes `recent_turns[-2:]` (last 2 turns), so `recent_turns[-1]` is the most recent prior turn. The old index `recent_turns[-2]` was reading the turn before that, giving progress stale context.

**Validation:** After a multi-turn session, verify `prior_turn_narration` in the progress extraction prompt matches the narration from the immediately preceding turn, not two turns ago.

---

#### Step 3.3 — Add context blocks to extract_progress_user.j2

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Add four blocks after the `## END CURRENT TURN NARRATION` line and before any trailing content.

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

Insert all four blocks between `## END CURRENT TURN NARRATION` and the end of file, in order A → B → C → D.

**Validation:** Render the progress extraction prompt with a test state that has stakes, deescalate=0.6, and a pending beat. Confirm all four blocks appear appropriately (deescalate block renders, stakes block renders, pending_beat appears in block C).

---

#### Step 3.4 — Add stakes/band hint to extract_state_user.j2

**File:** `ccya/prompts/extract_state_user.j2`

**What:** Add a `rules_stakes` hint block before the `## CURRENT TURN NARRATION` section.

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

#### Step 3.5 — Update extract_progress_system.j2 output schema

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Add `beat_disposition` and `scene_pressure_add` to the JSON output schema section. Find the section in the system prompt that lists the output fields and add:

```
"beat_disposition": "consume" | "carry" | "replace"  // default: "consume"; "carry" preserves the pending beat without consuming it; "replace" supersedes it with the new gm_beat
"scene_pressure_add": [{ "id": str, "text": str, "urgency": "immediate"|"building"|"background", "turn_added": int }]
```

**Why:** The LLM will not emit fields it has not been told to emit in the schema section.

**Validation:** Inspect the rendered system prompt in a test run. Confirm both fields appear in the schema description.

---

#### Step 3.6 — Remove scene_pressure_add from extract_scene_system.j2

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Find and remove any instruction or schema entry for `scene_pressure_add` in the scene extractor system prompt. Retain `scene_pressure_update` and `scene_pressure_remove` instructions unchanged.

**Why:** Scene extractor no longer emits `scene_pressure_add`. If the schema entry stays, the LLM may still try to emit it, which will be silently ignored by the Pydantic model — but it wastes tokens and can confuse the model about its own scope.

**Validation:** `grep -n "pressure_add" ccya/prompts/extract_scene_system.j2` — should return no results.

---

#### Step 3.7 — Wire pending_beat into extract_progress_user.j2 render context

**File:** `ccya/engine/extraction.py`

**What:** The progress user template (Step 3.3 Block C) references a `pending_beat` variable. This must be passed from `_extract_progress_messages` into the Jinja2 render context.

In `_extract_progress_messages`, add:
```python
pending_beat = (state.get("meta") or {}).get("pending_gm_beat") or None
```

And add `"pending_beat": pending_beat` to the `user_text` render context dict.

**Why:** Without this, the `{% if pending_beat %}` block in the template never renders.

**Validation:** In a test with `meta.pending_gm_beat` set, render `_extract_progress_messages` and confirm `pending_beat` data appears in the output.

---

### Tests to write or update

**File:** `tests/test_prompts.py` (create if not present)

- `test_rules_user_full_narration` — render `rules_user.j2` with a `recent_turns` entry whose `narrative` is > 120 chars. Assert the full narrative appears in output and the truncated suffix does not.
- `test_progress_prior_turn_correct_index` — render `extract_progress_user.j2` with `recent_turns=[turn_A, turn_B]`. Assert `turn_B.narrative` appears, not `turn_A.narrative`.
- `test_progress_stakes_block_fail` — render with `stakes="wounded", band="fail"`. Assert stakes block renders with `immediate urgency` instruction.
- `test_progress_stakes_block_crit_success` — render with `stakes="guard thwarted", band="crit_success"`. Assert NPC reaction beat suggestion appears.
- `test_progress_deescalate_block` — render with `deescalate=1.0`. Assert strong deescalation wording appears.
- `test_progress_pending_beat_block` — render with `meta.pending_gm_beat` set. Assert pending beat type and instruction appear in output.
- `test_state_stakes_hint_fail` — render `extract_state_user.j2` with `stakes="wounded", band="fail"`. Assert hint block renders.
- `test_state_stakes_hint_success` — render with `band="success"`. Assert hint block does NOT render.

### REPOMAP updates required

`docs/REPOMAP/prompts.md`: update entries for `rules_user.j2`, `extract_progress_user.j2`, `extract_progress_system.j2`, `extract_scene_system.j2`, `extract_state_user.j2`.

### Risks

1. **Token budget.** The new blocks in `extract_progress_user.j2` add approximately 200–400 tokens per turn (stakes block, deescalate block, gm_beat/beat_disposition block, scene_pressure_add block). Measure rendered prompt size after Phase 3 and compare against `config.prompt_token_budget`. If the progress prompt is approaching the budget, consider shortening the `## gm_beat` instruction prose.
2. **`pending_beat` exposure.** The template now shows the pending beat's `instruction` text to the progress LLM. This is intentional — the LLM needs to read it to decide whether to carry or replace. Ensure this does not create a loop where the LLM re-emits the same instruction verbatim as a new beat.
3. **`extract_scene_system.j2` structural dependencies.** The scene system prompt may have a numbered or bulleted field list. Removing `scene_pressure_add` must not leave a dangling reference or break the list numbering.

---

## Ambiguities requiring resolution before execution

1. **`_run_extraction_pipeline` return type and StateDelta merge mechanics.** The plan assumes `scene_pressure_add` is merged into `StateDelta` from `scene_result` in `extraction.py`. If `apply_delta` in `state/delta.py` builds the `StateDelta` directly from both stream results independently, the merge location may be in `delta.py` rather than `extraction.py`. The executor must verify with `grep -n "scene_pressure_add" ccya/engine/extraction.py ccya/state/delta.py` before executing Step 2.3 to confirm where the merge happens.

2. **`pending_beat` variable name in `extract_progress_user.j2`.** Step 3.3 uses `pending_beat` as the Jinja2 variable name. If `meta.pending_gm_beat` is a dict (which it is, per `model_dump()`), the template accesses `pending_beat.type`, `pending_beat.beat_expires_turn`, `pending_beat.instruction`. Confirm these keys exist on the stored dict — they should, since `beat_expires_turn` is added by `turn.py` as a plain dict key and the rest come from `GMBeat.model_dump(exclude_none=True)`.

3. **`extraction_event` schema for progress stream.** The progress stream event dict is written from `progress_result.model_dump()`. After Phase 1, this will now include `beat_disposition` and `scene_pressure_add`. If the turn viewer (`server/tv.py`) or eval auto-checker (`eval/universal_asserts.py`) reads specific keys from the progress stream output, verify they handle the new fields gracefully.

4. **`extract_progress_system.j2` schema section format.** The location and format of the output schema within this file is not confirmed from this read. The executor must read `ccya/prompts/extract_progress_system.j2` before executing Step 3.5 and insert the new fields in a format consistent with the existing schema entries.

5. **`run_turn_retry` `scene_result` read.** The existing `run_turn_retry` function reads `scene_result.gm_beat` in the beat storage block. After Phase 1, this field no longer exists. Step 2.4c replaces this with `progress_result.gm_beat`. The executor must verify `run_turn_retry` also returns / has access to `progress_result` — if it does not (e.g. it only returns `scene_result`), the extraction call site must be checked.

---

## TODO.md update

Under **P2 — Interesting Storytelling**, add:

```
- [ ] **Narrative mechanics overhaul** — beat carry/consume disposition, pressure ownership to progress, stakes routing to extractors, rules full narration, prior-turn index fix — [`docs/plans/narrative-mechanics-overhaul.md`](docs/plans/narrative-mechanics-overhaul.md)
```

Mark `progress-rules-narration.md` as superseded:

```
- ~~**GM beat ownership migration + deescalate float + beat expiry + rules full narration** — superseded by `narrative-mechanics-overhaul.md`~~
```
