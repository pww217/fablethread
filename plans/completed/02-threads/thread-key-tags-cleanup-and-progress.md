# Remove thread.key, remove thread.tags, add thread.progress

## Purpose

Eliminate dead fields on `ArcThread` (`key`, `tags`) that add complexity without value, and add a `progress` field to give threads actionable mechanical weight vs world_state.

## Problem Statement

`ArcThread.key` duplicates `id` (both identify threads) with a fragile fuzzy dedup heuristic (token-overlap ≥0.70) that can merge unrelated threads or miss actual duplicates. `ArcThread.tags` is purely decorative — rendered in the prompt but drives zero logic (no filtering, routing, state transitions). Meanwhile threads blur into world_state because they lack a concrete progress mechanism — a thread with no measurable state is just a fancy world_state fact.

## Constraints

- Engine dedup must still block duplicate threads by `id` (exact match, already exists).
- No schema version bump needed — `key` and `tags` are optional on `ArcThread`; removing them is backward-compatible for existing saves (they won't be present in new data, old saves still load).
- `progress` field must be `thread_update`-able (storyteller sets it via the same `thread_update` list that carries `urgency`/`active`).

## Non-goals

- No world_state lifecycle changes (deferred to future plan).
- No changes to seed pool `tags` (those are on `PoolEntry`, not `ArcThread`).
- No reprompting or prompt architecture restructuring.
- No eval harness changes beyond removing the `check_arcthread_key_dedup` assertion.

## Solution

1. Remove `key` and `tags` from `ArcThread` model; remove the key-based dedup (exact + fuzzy) and tag-merging logic from `turn.py`.
2. Add `progress: str = ""` to `ArcThread` and its summary/prompt view. The storyteller sets it via `thread_update[].progress`.
3. Update all prompts that reference `key`, `tags`, or the dedup mechanism.
4. Remove the eval assertion that validates key dedup.

## Firm decisions

1. `thread.key` is dead. No replacement. Exact `id` collision is sufficient for dedup.
2. `thread.tags` is dead. No replacement. Categories belong in `summary` text if needed.
3. `thread.progress` is a free-text string, not an enum or structured field. The LLM decides format.
4. `thread_update` adds `progress` as an optional field alongside `urgency`/`active`.

## Risks, Ambiguities, and Blockers

- Existing saves with `key`/`tags` in thread dicts will load fine (Pydantic ignores unknown fields with default config). No migration needed.
- The `check_arcthread_key_dedup` eval assertion is the only user of `_token_overlap_score` — deleting both is safe.
- No changes to `pack.py` seed models (SeedEnvelope.arc uses CampaignArc, which will gain `progress` but the seed generator doesn't set it — zero impact).

## Status

`completed`

## Phases

Single phase: model + engine + prompts + eval, all within the same shared files.

## Implementation — Single Phase

### Context files to load

- `ccya/models.py` — ArcThread, ArcThreadSummary, ThreadUpdate
- `ccya/engine/turn.py` — thread_add dedup logic (~lines 1120–1212)
- `ccya/prompts/context.py` — ArcThreadSummary, ArcThreadBlock
- `ccya/prompts/storytell_system.j2` — output schema for thread_add
- `ccya/prompts/storytell_user.j2` — thread display line
- `ccya/prompts/sections/_thread_list.j2` — thread rendering
- `ccya/prompts/generate_seed_system.j2` — thread field docs
- `ccya/eval/universal_asserts.py` — check_arcthread_key_dedup + _token_overlap_score
- `ccya/state/delta_builder.py` — world_state mutations (check if thread progress is applied here)

### Detailed steps

#### Step 1 — Remove `key` and `tags` from `ArcThread`; add `progress`

**File:** `ccya/models.py` line 28–39

**What:**
- Delete `tags: list[str] = Field(default_factory=list)` (line 34)
- Delete `key: str | None = None` (line 38)
- Add `progress: str = ""` to ArcThread

Result:
```python
class ArcThread(BaseModel):
    id: str
    summary: str
    scope: Literal["scene", "arc"]
    active: bool = True
    urgency: Literal["background", "normal", "urgent"] = "normal"
    progress: str = ""
    resolution_state: str | None = None
    outcome: str | None = None
    resolved_turn: int | None = None
```

**Why:** Remove dead fields; add the only new field that changes thread semantics.

**Validation:** `python3 -c "from ccya.models import ArcThread; t = ArcThread(id='test', summary='x', scope='arc'); assert t.progress == ''; assert not hasattr(t, 'key'); assert not hasattr(t, 'tags')"` — no errors.

---

#### Step 2 — Remove `tags` from `ArcThreadSummary`; add `progress`

**File:** `ccya/prompts/context.py` lines 76–88

**What:**
- Delete `tags: list[str] = Field(default_factory=list)` from ArcThreadSummary
- Add `progress: str = ""`

Result:
```python
class ArcThreadSummary(BaseModel):
    id: str
    summary: str
    scope: Literal["scene", "arc"]
    urgency: Literal["background", "normal", "urgent"]
    progress: str = ""
    active: bool
```

**Why:** ArcThreadSummary mirrors ArcThread's prompt-facing fields; must match.

**Validation:** Same import check.

---

#### Step 3 — Remove `tags` mapping from `ArcThreadBlock.from_state()`

**File:** `ccya/prompts/context.py` lines 97–130

**What:** Remove the `tags=...` line from each branch that constructs `ArcThreadSummary`:
- Line 111: remove `tags=list(t.get("tags", [])),`
- Line 122: remove `tags=list(t.tags),`

**Why:** Field no longer exists on the model.

**Validation:** Same import check.

---

#### Step 4 — Purge key-based dedup and tag merging from turn.py

**File:** `ccya/engine/turn.py` lines 1119–1212

**What:** Replace the entire thread_add block. Remove:
- Exact key collision check (lines 1130–1149)
- Fuzzy auto-merge dedup (lines 1161–1197)
- Tag merging (lines 1182–1186)
- All logging with `key` extra fields

The simplified logic:
1. If `thread_add` is present and gate_ok:
2. Load existing arc, collect existing thread ids
3. If `_new_thread.id` not in existing_ids: append it
4. Error handling as before

**Why:** All dedup now happens on `id` only. The gate-ok check and scope cooldown remain unchanged.

---

#### Step 5 — Update `storytell_system.j2` output schema

**File:** `ccya/prompts/storytell_system.j2` lines 6–15

**What:**
- Line 10: Add `"progress": ""` to the `thread_update` example
- Line 12: Remove `"tags": [], "key": "subject_action"` from the `thread_add` example
- Line 51: Remove `tags (list), key ("subject_action")` from the thread_add specification text

Result line 12:
```json
  "thread_add": {"id": "snake_case_id", "summary": "story tension description", "scope": "arc", "urgency": "normal"},
```

Line 51 becomes: `...urgency ("background", "normal", or "urgent" only — no other values).`

**Why:** Reflect the new model in the LLM's output spec.

---

#### Step 6 — Update `storytell_user.j2` thread display

**File:** `ccya/prompts/storytell_user.j2` line 15

**What:** Remove the tags rendering suffix:
```
{% if t.tags %} tags: {{ t.tags | join(', ') }}{% endif %}
```
And add progress rendering:
```
{% if t.progress %} [progress: {{ t.progress }}]{% endif %}
```

Result line 15:
```
{% for t in all_threads %}{% set scope_tag = "[SCENE]" if t.scope == "scene" else "[ARC]" %}- `{{ t.id }}` {{ scope_tag }} {% if not t.active %}(dormant){% endif %} [{{ t.urgency | upper }}] {{ t.summary | truncate(120) }}{% if t.progress %} [progress: {{ t.progress }}]{% endif %}
{% endfor -%}{% else %}
```

**Why:** Replace a dead display field with an actionable one. Progress shows the LLM measurable thread state.

---

#### Step 7 — Update `generate_seed_system.j2` thread field docs

**File:** `ccya/prompts/generate_seed_system.j2`

**What:**
- Line 43: Change `{id, summary, tags, urgency, scope}` to `{id, summary, urgency, scope}`
- Line 193: Change `{id, summary, tags, urgency, scope}` to `{id, summary, urgency, scope}`

**Why:** Remove references to the dead `tags` field.

---

#### Step 8 — Remove key dedup eval assertion

**File:** `ccya/eval/universal_asserts.py`

**What:**
- Delete `_token_overlap_score` function (lines 637–650)
- Delete `check_arcthread_key_dedup` function (lines 653–695)
- Remove `check_arcthread_key_dedup(event),` from the assertion list (line 1073)

**Why:** No more `key` field means no key-based dedup to validate.

---

#### Step 9 — Add `progress` as optional on `ThreadUpdate` model

**File:** `ccya/models.py` lines 351–356

**What:** Add `progress: str | None = None` to ThreadUpdate.

Result:
```python
class ThreadUpdate(BaseModel):
    id: str
    active: bool | None = None
    urgency: Literal["background", "normal", "urgent"] | None = None
    summary: str | None = None
    progress: str | None = None
```

**Why:** The storyteller must be able to set progress via thread_update, just like urgency/active.

---

#### Step 10 — Remove `_new_thread.key` reference from cooldown check

**File:** `ccya/engine/turn.py` — check for any remaining `.key` access

**What:** After step 4, search the file for any remaining `_new_thread.key` or `.key` references from thread code. Ensure no dangling references.

**Validation:** `grep -rn '\.key' ccya/engine/turn.py` should show zero matches for thread-related key access.

### Tests to write or update

- No test changes needed beyond removing `check_arcthread_key_dedup` from universal_asserts.py (step 8).
- Existing `check_thread_add_applied` continues to validate that threads with matching `id` are not duplicated — that's the dedup mechanism now.
