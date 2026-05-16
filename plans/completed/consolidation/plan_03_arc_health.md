# Plan 03: Arc Health Block

**Replaces:** `active_threads` raw list as opaque context input to Step 2c  
**Status:** Planned

---

## Problem

Step 2c receives `active_threads` as a raw list of `{id, summary, urgency, tags}` dicts. The extractor has no visibility into *how stale* each thread is — whether it's been ignored for 5 turns or just advanced last turn. The LLM has to guess whether to push new threads or focus on existing ones.

There's no pre-computed signal about arc health: are threads progressing, stalling, or dormant? The extractor must infer this from narration alone, which is noisy and token-wasteful.

---

## Solution

Replace the raw `active_threads` list with a single `arc_health` block that pre-computes thread staleness and aggression level.

### Python model

```python
class ArcHealthAggression(str, Enum):
    LOW    = "low"     # threads are advancing; don't push new ones
    NORMAL = "normal"  # default; generate if narration warrants it
    HIGH   = "high"    # threads are stalling; actively look for new threads
```

```python
@dataclass
class ArcHealth:
    stalled: list[dict]             # [{id, summary, age}] — threads not signaled in N turns
    new_thread_aggression: ArcHealthAggression
```

### Computation

```python
def compute_arc_health(
    arc: CampaignArc,
    current_turn: int,
    stall_threshold: int = 4,       # turns without signal = stalled
    high_aggression_threshold: int = 2,  # N stalled threads → HIGH aggression
) -> ArcHealth:
    active = [t for t in arc.active_threads if t.state == ThreadState.ACTIVE]
    stalled = [
        {"id": t.id, "summary": t.summary, "age": current_turn}
        for t in active
    ]
    # age = current_turn means the thread has existed for N turns with no signal

    if len(stalled) >= high_aggression_threshold:
        aggression = ArcHealthAggression.HIGH
    elif stalled:
        aggression = ArcHealthAggression.NORMAL
    else:
        aggression = ArcHealthAggression.LOW if len(active) >= 2 else ArcHealthAggression.NORMAL

    return ArcHealth(stalled=stalled, new_thread_aggression=aggression)
```

---

## Template changes

### `extract_progress_user.j2` — replace `active_threads` block with `arc_health`

**Remove:**
```jinja2
{# REMOVE #}
{% if active_threads -%}
## active_threads
{% for t in active_threads %}- `{{ t.id }}` [{{ t.urgency | upper }}] {{ t.summary | truncate(120) }}{% if t.tags %} tags: {{ t.tags | join(', ') }}{% endif %}
{% endfor %}
{% else -%}
## active_threads
None currently active. Generate actions that could introduce new story directions or explore the environment.
{% endif -%}
```

**Add:**
```jinja2
{% if arc_health -%}
## arc_health
New thread aggression: **{{ arc_health.new_thread_aggression | upper }}**
{%- if arc_health.new_thread_aggression == 'high' %} — Threads are stalling. Actively look for new thread opportunities in the narration.{% elif arc_health.new_thread_aggression == 'normal' %} — Generate new threads when narration clearly introduces a new objective or commitment.{% else %} — Threads are advancing; do not manufacture new threads.{% endif %}
{% if arc_health.stalled -%}
Stalled threads (have not received a signal in 4+ turns):
{% for t in arc_health.stalled %}- `{{ t.id }}` — "{{ t.summary }}" ({{ t.age }} turns)
{% endfor -%}
{% endif -%}
{% endif -%}
```

### `extract_progress_system.j2` — update thread guidance

Replace any reference to `active_threads` in the system instructions with:

```
`arc_health.new_thread_aggression`: Controls how actively you should generate new thread opportunities.
- `HIGH`: Multiple threads have stalled. Actively look for new thread opportunities surfaced by narration.
- `NORMAL`: Generate new threads when narration clearly introduces a new objective or commitment.
- `LOW`: Threads are progressing. Do not manufacture new threads to fill space.

For stalled threads listed under `arc_health.stalled`: if the narration this turn touched
any of them (even indirectly), emit a `thread_signals` entry — even a `blocked` or `ignored`
signal resets the staleness clock and prevents artificial pressure.
```

---

## Python payload changes

In `_extract_progress_messages()`:

```python
# Before
active_threads = [
    {"id": t["id"], "summary": t["summary"], "urgency": t.get("urgency", "normal"), "tags": t.get("tags", [])}
    for t in ((state.get("arc") or {}).get("active_threads") or [])
]
# ... passed as "active_threads": active_threads in user_text render kwargs

# After
arc_health = compute_arc_health(
    arc=CampaignArc(**(state.get("arc") or {})),
    current_turn=turn_no,
)
# ... passed as "arc_health": arc_health in user_text render kwargs
# active_threads removed from render kwargs
```

---

## What gets deleted

- `active_threads` as a render kwarg / template variable
- The `## active_threads` Jinja section in `extract_progress_user.j2`
- The raw thread list computation in `_extract_progress_messages()`

---

## Migration

No state migration. `ArcHealth` is computed fresh each turn from `state.arc`.
No saved-game fields change.

---

## Summary of delta

| Before | After |
|--------|-------|
| `active_threads: list[dict]` raw list in user prompt | Folded into `arc_health.stalled` + `arc_health.new_thread_aggression` |
| LLM must infer thread staleness from raw list | Aggression level is pre-computed and stated directly |
| No distinction between active and stalled threads | Stalled threads explicitly listed with age |
