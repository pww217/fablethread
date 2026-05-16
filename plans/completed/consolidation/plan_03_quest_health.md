# Plan 03: Quest Health Block

**Replaces:** `quest_ages` list + `quest_threshold_directive` string as separate inputs to Step 2c  
**Status:** Planned

---

## Problem

Step 2c receives two separate quest-staleness inputs:

- `quest_ages`: a list of `{id, title, age}` dicts signaling which quests haven't advanced in N turns
- `quest_threshold_directive`: a string telling the extractor how aggressively to generate new quests

Both exist solely to answer one question: *what should the extractor do about quest staleness right now?* They're rendered as two separate sections in `extract_progress_user.j2` with no clear relationship between them, and the LLM has to mentally join them. There's no reason they can't be one structured input.

---

## Solution

Replace both with a single `quest_health` block passed to the extractor.

### Python model

```python
class QuestHealthAggression(str, Enum):
    LOW    = "low"     # quests are moving; don't push new ones
    NORMAL = "normal"  # default; generate if narration warrants it
    HIGH   = "high"    # quests are stalling; actively look for new threads

@dataclass
class QuestHealth:
    stalled: list[dict]             # [{id, title, age}] — same as old quest_ages
    new_quest_aggression: QuestHealthAggression
```

### Computation (replaces separate derivation of `quest_ages` and `quest_threshold_directive`)

```python
def compute_quest_health(
    quests: list[Quest],
    current_turn: int,
    stall_threshold: int = 4,       # turns without advancement = stalled
    high_aggression_threshold: int = 2,  # N stalled quests → HIGH aggression
) -> QuestHealth:
    active = [q for q in quests if q.status == QuestStatus.ACTIVE]
    stalled = [
        {"id": q.id, "title": q.title, "age": current_turn - q.last_advanced_turn}
        for q in active
        if (current_turn - q.last_advanced_turn) >= stall_threshold
    ]

    if len(stalled) >= high_aggression_threshold:
        aggression = QuestHealthAggression.HIGH
    elif stalled:
        aggression = QuestHealthAggression.NORMAL
    else:
        # No stalled quests — check if we have too few active quests
        aggression = QuestHealthAggression.LOW if len(active) >= 2 else QuestHealthAggression.NORMAL

    return QuestHealth(stalled=stalled, new_quest_aggression=aggression)
```

---

## Template changes

### `extract_progress_user.j2` — replace two sections with one

**Remove:**
```jinja2
{# REMOVE #}
{% if quest_ages -%}
## stalled_quests
{% for q in quest_ages %}- `{{ q.id }}` — "{{ q.title }}" — stalled {{ q.age }} turns
{% endfor %}
{% endif -%}

{# REMOVE — wherever quest_threshold_directive is rendered #}
{% if quest_threshold_directive -%}
## new_quest_guidance
{{ quest_threshold_directive }}
{% endif -%}
```

**Add:**
```jinja2
{% if quest_health -%}
## quest_health
New quest aggression: **{{ quest_health.new_quest_aggression | upper }}**
{%- if quest_health.new_quest_aggression == 'high' %} — Quests are stalling. Look actively for new thread opportunities in the narration.{% elif quest_health.new_quest_aggression == 'normal' %} — Generate new quests only when narration clearly warrants it.{% else %} — Quests are advancing; do not manufacture new threads.{% endif %}
{% if quest_health.stalled -%}
Stalled quests (have not advanced in 4+ turns):
{% for q in quest_health.stalled %}- `{{ q.id }}` — "{{ q.title }}" ({{ q.age }} turns)
{% endfor -%}
{% endif -%}
{% endif -%}
```

### `extract_progress_system.j2` — update quest guidance

Replace any reference to `quest_threshold_directive` or `quest_ages` in the system instructions with:

```
`quest_health.new_quest_aggression`: Controls how actively you should generate new quest threads.
- `HIGH`: Multiple quests have stalled. Actively look for new thread opportunities surfaced by narration.
- `NORMAL`: Generate new quests when narration clearly introduces a new objective or commitment.
- `LOW`: Quests are progressing. Do not manufacture new threads to fill space.

For stalled quests listed under `quest_health.stalled`: if the narration this turn touched
any of them (even indirectly), emit a `thread_signals` entry — even a `blocked` or `ignored`
signal resets the staleness clock and prevents artificial pressure.
```

---

## Python payload changes

In `build_extract_progress_payload()`:

```python
# Before
payload["quest_ages"]              = compute_quest_ages(state.quests, state.meta.turn)
payload["quest_threshold_directive"] = derive_quest_threshold_directive(state.quests)

# After
payload["quest_health"] = compute_quest_health(
    quests=state.quests,
    current_turn=state.meta.turn,
)
# quest_ages and quest_threshold_directive removed from payload entirely
```

`compute_quest_ages()` and `derive_quest_threshold_directive()` can be deleted or
folded into `compute_quest_health()` — they have no other callers.

---

## What gets deleted

- `quest_ages` as a payload key
- `quest_threshold_directive` as a payload key
- The two separate Jinja sections that rendered them
- `compute_quest_ages()` function (logic absorbed into `compute_quest_health()`)
- `derive_quest_threshold_directive()` function (logic absorbed into `compute_quest_health()`)

---

## Section cleanup

This plan also touches the `## stalled_quests` and `## new_quest_guidance` sections in
`extract_progress_user.j2`, which were previously unextracted inline blocks. After this
change, quest health is rendered through a single `{% if quest_health %}` block. No
separate section file is warranted — the block is short and context-specific to the
progress extractor. It does not appear in any other template.

---

## Migration

No state migration. `QuestHealth` is computed fresh each turn from `state.quests`.
No saved-game fields change.

---

## Summary of delta

| Before | After |
|--------|-------|
| `quest_ages: list[dict]` in payload | Folded into `quest_health.stalled` |
| `quest_threshold_directive: str` in payload | Folded into `quest_health.new_quest_aggression` |
| Two separate Jinja sections with no explicit relationship | One `## quest_health` block with both fields co-located |
| LLM must infer relationship between staleness data and aggression guidance | Aggression level is pre-computed and stated directly |
