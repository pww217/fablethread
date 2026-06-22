# Phase 6 — Context + template rendering

## Purpose

Update `ArcThreadSummary` and `ArcThreadBlock.from_state()` to use `dormant` and `type`, and update `_thread_list.j2` to render `[Dormant]` tag instead of `(latent)`.

## Problem Statement

`ArcThreadSummary` still uses `active: bool`. No `type` or `dormant` fields. `ArcThreadBlock.from_state()` constructs `ArcThreadSummary` without `type` or `dormant`. The thread list template shows `(latent)` for inactive threads but should show `[Dormant]` for dormant threads.

## Constraints

- `ArcThreadSummary` is a prompt-facing model — its field names must match what prompt templates reference.
- `from_state()` must handle both dict data and `ArcThread` objects.

## Non-goals

- No changes to UI templates (`_state_left.html`, `tv.py`) — no semantic type display in UI.
- No changes to turn processing, sanitizer, seed, or convergence — covered in other phases.

## Solution

Replace `active: bool` with `dormant: bool` on `ArcThreadSummary`, add `type` field, update `from_state()` to populate both from dict/ArcThread sources, and update `_thread_list.j2` to render `[Dormant]` for dormant threads.

## Firm decisions

1. `dormant: bool` is required (no default) — `from_state()` must always provide it.
2. `type` is optional (`None = None`) — storyteller may not assign types to all threads.
3. Thread list templates: `[Dormant]` tag only when `dormand == True`, no `(latent)` for non-dormant.
4. No semantic type tags in templates (type is narrative metadata, not displayed).

## Risks, Ambiguities, and Blockers

- **Stale filter in `_thread_list.j2`:** The current template line 3 filters out threads untouched for > 2 turns (`(turn_no - t.last_updated_turn) > 2`). Dormant threads (auto-dormanted at 4 turns) would be hidden for 2 turns before getting `[Dormant]`. The stale filter should be either removed or extended to match the auto-dormant threshold (4 turns) so dormant threads remain visible.
- **Completed threads in `from_state()`:** Completed threads go through the same `ArcThreadSummary` construction. Completed threads won't have `dormant` set meaningfully — they should default to `dormant: False` (a completed thread is not dormant, it's resolved). The `from_state()` paths handle this by providing the field explicitly.

## Status

`completed`

## Implementation — Phase 6: Context + template rendering

### Context files to load

- `ccya/prompts/context.py:77-150` — `ArcThreadSummary` + `ArcThreadBlock.from_state()`
- `ccya/prompts/sections/_thread_list.j2` — Thread list rendering (7 lines)

### Detailed steps

#### Step 6.1 — Update `ArcThreadSummary` model

**File:** `ccya/prompts/context.py:77-85`

**What:** Replace `active: bool` with `dormant: bool`, and add `type: Literal["threat", "opportunity", "complication", "revelation"] | None = None`.

```python
class ArcThreadSummary(BaseModel):
    """Simplified arc thread data for prompt rendering (subset of full ArcThread)."""

    id: str
    summary: str
    urgency: Literal["background", "normal", "urgent"]
    type: Literal["threat", "opportunity", "complication", "revelation"] | None = None
    progress: list[str] = Field(default_factory=list)
    dormant: bool
    last_updated_turn: int | None = None
```

**Why:** `dormant` and `type` must be available in prompt context. `active` removed.

**Validation:** `.venv/bin/python -c "from ccya.prompts.context import ArcThreadSummary; s = ArcThreadSummary(id='t1', summary='test', urgency='normal', dormant=False); print('OK')"`

#### Step 6.2 — Update `from_state()` dict path

**File:** `ccya/prompts/context.py:122-131`

**What:** In the dict branch (lines 122-131), add `type` and replace `active` with `dormant`:

```python
raw_threads.append(
    ArcThreadSummary(
        id=t.get("id", ""),
        summary=t.get("summary", ""),
        urgency=t.get("urgency", "normal"),
        type=t.get("type"),
        progress=_fmt_progress(t.get("progress")),
        dormant=bool(t.get("dormant", False)),
        last_updated_turn=t.get("last_updated_turn"),
    )
)
```

Remove the `active=bool(t.get("active", True))` line.

**Why:** Dict source (from state JSON) needs to provide `type` and `dormant`. Old dicts may lack both; `type` defaults to `None`, `dormant` defaults to `False`.

**Validation:** `.venv/bin/python -c "from ccya.prompts.context import ArcThreadBlock; b = ArcThreadBlock.from_state({'arc': {'threads': [{'id':'t1','summary':'test','urgency':'normal'}]}}); print(b.threads[0].dormant, b.threads[0].type); assert b.threads[0].dormant == False; assert b.threads[0].type is None"`

#### Step 6.3 — Update `from_state()` ArcThread path

**File:** `ccya/prompts/context.py:132-141`

**What:** In the ArcThread branch (lines 132-141), add `type` and replace `active` with `dormant`:

```python
raw_threads.append(
    ArcThreadSummary(
        id=t.id,
        summary=t.summary,
        urgency=t.urgency,
        type=getattr(t, "type", None),
        progress=_fmt_progress(t.progress),
        dormant=getattr(t, "dormant", False),
        last_updated_turn=getattr(t, "last_updated_turn", None),
    )
)
```

Remove the `active=bool(t.active)` line.

**Why:** ArcThread source has the new `type` and `dormant` fields after Phase 1.

**Validation:** `.venv/bin/python -c "from ccya.models import ArcThread; from ccya.prompts.context import ArcThreadBlock; t = ArcThread(id='t1', summary='test', urgency='normal', dormant=False, type='threat'); b = ArcThreadBlock.from_state({'arc': {'threads': [t]}}); assert b.threads[0].dormant == False; assert b.threads[0].type == 'threat'"`

#### Step 6.4 — Update `_thread_list.j2` template

**File:** `ccya/prompts/sections/_thread_list.j2`

**What:** Replace the `(latent)` check with `[Dormant]` tag:
- Remove `{% if not t.active %} (latent){% endif %}`
- Add `{% if t.dormant %} [Dormant]{% endif %}` before the urgency tag
- Update or remove the stale filter (`(turn_no - t.last_updated_turn) > 2`) — extend to match auto-dormant threshold (> 4), or remove it entirely so dormant threads remain visible.

Result:
```
{% if threads %}
### Active Threads ({{ threads | length }} active — target: 3-4, ~5 total)
{% for t in threads %}{% if not t.dormant %}- `{{ t.id }}` [{{ t.urgency | upper }}] {{ t.summary }}
{%- if t.last_updated_turn is not none %} ({{ turn_no - t.last_updated_turn }} turns ago){% endif %}
{%- for entry in t.progress %}   - {{ entry }}{% endfor %}
{% endif %}{% endfor %}{% else %}No active threads.
{% endif %}
```

Show dormant threads separately:
```
{% if threads | selectattr('dormant') | list %}
### Dormant Threads (faded but recoverable)
{% for t in threads %}{% if t.dormant %}- `{{ t.id }}` [DORMANT] {{ t.summary }} ({{ turn_no - t.last_updated_turn }} turns ago)
{% endif %}{% endfor %}{% endif %}
```

**Why:** Dormant threads should be visible to the narrator (with `[DORMANT]` tag) so they know the thread exists but is faded from relevance. Separating dormant threads into their own section reduces clutter in the active threads section.

**Validation:** Manual inspection of rendered template.

### Tests to write or update

No tests currently. Run `make check` for type/lint.

## Status

completed
