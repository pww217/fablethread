# GM Beats Discovery

**Scope:** GM beat generation, passing, consumption; relationship to pacing system, threading, and NPC fields (motivation/fear/leverage).  
**Status:** Findings — not a design or plan.

---

## 1. GM Beat Model

**File:** `ccya/models/extraction.py:181-219`

```python
class GMBeat(BaseModel):
    type: Literal["complication", "revelation", "opportunity", "breathing_room",
                  "pressure", "twist", "setback", "escalation", "callback"] | None = None
    surface_as: Literal["ambient", "event", "npc_behavior", "environmental",
                        "player_discovery", "item"] = "ambient"
    beat_expires_turn: int | None = None
```

**Validation:** `_coerce_gm_beat_type` (line 194-210) nulls any unrecognized `type` string. `surface_as` is **not validated** — accepts any string the LLM emits.

**The `surface_as` field** (`ccya/models/extraction.py:211-218`) is a rendering hint the storyteller emits but the narrator is told *not* to recite metadata directly (`ccya/prompts/narrate_user.j2:88`). The field is currently informational-only — it has no mechanical effect on beat lifecycle, expiration, or behavior.

---

## 2. Beat Lifecycle (Turn Sequence)

### 2.1 Storage: `state.meta.pending_gm_beat`

Beats are stored in `state.meta.pending_gm_beat` (a dict, not a StateDelta field). This is a deliberate exception — the beat bypasses the StateDelta/validation pipeline and is written directly by `turn.py`.

### 2.2 Lifecycle Flow

| Phase | File | What Happens |
|---|---|---|
| **Pre-narration (Step 1)** | `narrate.py:169-174` | Reads `pending_gm_beat`; checks `beat_expires_turn`; nulls if `turn_no > expires` |
| **Narration (Step 1)** | `narrate.py:271` | Passes `_pending_gm_beat` to `_narrate_messages()` as `pending_beat=` |
| **Storytell (Step 2c)** | `storytell.py:87` | Reads current beat from `state.meta.pending_gm_beat`; passes to storytell prompt |
| **Post-extraction** | `turn.py:258-265` | New beat replaces pending; null type pops the key |

### 2.3 Expiry

`turn.py:262` sets `beat_expires_turn = turn_no + 2`. A beat lives for **at most 2 turns** before being auto-nulled by the narrate pre-check.

### 2.4 Beat History

`turn_state.py:470-480` snapshots the beat after floor relief override into `meta.recent_beats`:

```python
meta.setdefault("recent_beats", []).append({
    "turn": turn_no,
    "type": _history_beat.get("type") if _history_beat else None,
    "surface_as": _history_beat.get("surface_as") if _history_beat else None,
})
```

Capped at `config.recent_beats_max` (default 5). Gaps occur on extraction-error turns (intentional — prevents error-path beats from contaminating diversity guidance).

---

## 3. Prompt Injection

### 3.1 Narrator Prompt

**`ccya/prompts/narrate_system.j2:11`**
```
**Priority ordering: player input > GM beat > outcome hint.**
When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action.
```

**`ccya/prompts/narrate_user.j2:86-88`**
```jinja
{% if pending_beat and pending_beat.type -%}
**Beat:** {{ pending_beat.type | replace('_', ' ') | upper }} — surface as `{{ pending_beat.surface_as | default('ambient') }}`.
Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.
{%- endif %}
```

The narrator receives the beat as **ambient creative guidance**. It does not override the player's action. The instruction "do not recite beat metadata directly" means the narrator should internalize the beat and surface it through atmosphere, not announce "a complication occurs."

### 3.2 Storyteller Prompt

**`ccya/prompts/storytell_user.j2:42-52`**
```jinja
{% if pending_beat and pending_beat.type %}
## GM Beat
Type: **{{ pending_beat.type | replace('_', ' ') | upper }}**
Surface: `{{ pending_beat.surface_as | default('ambient') }}`
Expires: Turn {{ pending_beat.beat_expires_turn }}
{% else %}
## GM Beat
No beat currently carried over from the previous turn. Choose freely.
{% endif %}
```

**`ccya/prompts/storytell_system.j2:78`** — The storyteller is told:
```
`gm_beat`: one beat to shape the next turn, or `null`. Emit as `{"type": "...", "surface_as": "..."}` — must be narratively specific, name NPCs, reference locations, tie to active threads.
```

**`ccya/prompts/storytell_system.j2:86`**:
```
**For this turn, only the types in the `allowed_beat_types` list in the user prompt are valid. `gm_beat.type` MUST be one of those types.**
```

---

## 4. Pacing System Integration

### 4.1 Beat Type Constraints by Phase

**File:** `ccya/engine/_pacing.py:24-30`

```python
BEAT_PHASE_MAP = {
    "SETUP":       ["pressure", "complication", "escalation", "revelation", "twist", "opportunity", "callback", "breathing_room", "hazard"],
    "RISING":      ["pressure", "complication", "escalation", "revelation", "twist"],
    "CLIMAX":      ["pressure", "escalation", "complication"],
    "RESOLUTION":  ["breathing_room", "callback", "revelation"],
    "BREATHER":    ["opportunity", "revelation", "callback", "breathing_room", "hazard"],
}
```

### 4.2 Beat Buckets

**File:** `ccya/engine/_pacing.py:18-22`

```python
BEAT_BUCKETS = {
    "pressure":  ["pressure", "complication", "escalation", "setback"],
    "situation": ["revelation", "twist", "hazard", "callback"],
    "relief":    ["opportunity", "breathing_room"],
}
```

### 4.3 `derive_allowed_beat_types()`

**File:** `ccya/engine/_pacing.py:61-83`

```
1. Scene Imperative directive → situation-changers + opportunity
2. Spiral detected → phase defaults minus pressure bucket
3. Fallback → phase defaults
```

The resulting `allowed_beat_types` list is passed to the storytell prompt (`storytell_user.j2:78`) as a hard constraint: `gm_beat.type` MUST be from that list.

### 4.4 Convergence Score (Beat Streak)

**File:** `ccya/engine/_pacing.py:86-142` — `compute_convergence_score()`

One of 5 components: if ≥60% of recent beats are pressure-bucket types, convergence score increments (+1 toward CLIMAX transition).

### 4.5 Five-Phase State Machine

**File:** `ccya/engine/_pacing.py:222-294` — `_compute_scene_phase()`

Transitions: SETUP → RISING → CLIMAX → RESOLUTION → BREATHER → RISING

| Transition | Condition |
|---|---|
| SETUP → RISING | Urgent thread appears OR turns_in_phase >= 3 |
| RISING → CLIMAX | convergence_score >= threshold (default 3) |
| CLIMAX → RESOLUTION | climax_turn_count >= limit (default 4) |
| RESOLUTION → BREATHER | Always (1-turn) |
| BREATHER → RISING | Urgent thread OR breather_max_turns elapsed |

---

## 5. NPC Fields: Motivation, Leverage, Fear

### 5.1 Model

**File:** `ccya/models/extraction.py:24-26` (CompendiumNpcUpdate)
**File:** `ccya/state/npcs.py:275-280` (application to state)

```python
motivation: str | None   # what NPC fundamentally wants
fear: str | None          # what NPC is most afraid of
leverage: str | None      # what NPC can offer/threaten/withhold
```

### 5.2 Prompt Rendering

**File:** `ccya/prompts/sections/_npc_roster.j2:10`
```jinja
{% if n.presence == "present" %}{%- if n.motivation %} | wants: {{ n.motivation }}{% endif %}{%- if n.fear %} | fears: {{ n.fear }}{% endif %}{%- if n.leverage %} | leverage: {{ n.leverage }}{% endif %}
{% endif %}
```

Only rendered for `presence == "present"` NPCs.

### 5.3 Behavioral Guidance in Narrator System Prompt

**File:** `ccya/prompts/narrate_system.j2:65-71`
- **Motivation** — what they fundamentally want. Drive their actions and dialogue toward it.
- **Fear** — what they dread. Have them avoid it or overreact to it.
- **Leverage** — what they can offer, threaten, or withhold. Use it as a bargaining chip or pressure point.

### 5.4 UI Visibility

`docs/architecture/state-models.md:50` — `motivation` is UI-visible in compendium tooltip; `fear` and `leverage` are state-only, NOT UI-visible.

### 5.5 Seed Generation

**File:** `ccya/engine/seed.py:323-337` — `motivation` and `fear` passed through from NPC entry.

### 5.6 Personality Archetypes

**File:** `ccya/personality.py:17-117` — `motivation_keywords` and `fear_keywords` tuples per archetype. `_score_archetype()` matches NPC motivation+fear text against archetype keywords.

---

## 6. Threading System

### 6.1 Thread Model

**File:** `ccya/models/state.py` — `ArcThread`

```python
class ArcThread(BaseModel):
    id: str                    # 2-4 word broad conceptual bucket (no proper nouns)
    summary: str
    dormant: bool              # engine-set after 4 turns without activity
    type: Literal["threat", "opportunity", "complication", "revelation"] | None
    urgency: Literal["background", "normal", "urgent"] = "normal"
    progress: list[ProgressEntry]
    resolution_state, outcome, resolved_turn, last_updated_turn, added_turn, urgency_set_turn
```

**Note:** `thread_id`/`parent_id`/`root_id` fields are **not present** in the current codebase. The threading system uses a flat `ArcThread` model with `dormant`/`urgency`/`type` fields.

### 6.2 Thread Operations

**File:** `ccya/engine/turn_state.py:17-100` — `_apply_thread_updates()`

- `thread_update` list: `{id, dormant, urgency, type, summary, progress, progress_kind}`
- Progress dedup: 70% textual overlap rejection via `difflib.SequenceMatcher`
- Auto-dormant: 4 turns without activity (urgent threads excluded)
- Urgency decay: stepwise `urgent→normal→background` after `thread_urgency_max_age` turns (default 8)

**File:** `ccya/engine/turn_state.py` — `_apply_thread_resolutions()`
- `thread_resolve` list: `{id, resolution_state, outcome}`
- Moves to `completed_threads`

### 6.3 Thread Reference in Prompts

**File:** `ccya/prompts/storytell_system.j2:27-28`
- Thread IDs must match exactly what appears in the active threads list
- Hallucinating thread IDs causes silent failures (rejected by sanitization)

---

## 7. `surface_as` Field — Current State

### 7.1 Definition

`surface_as` is defined as a Literal with 6 values (`ccya/models/extraction.py:211-218`):
```python
surface_as: Literal["ambient", "event", "npc_behavior", "environmental",
                    "player_discovery", "item"] = "ambient"
```

But there is **no validation** — the Pydantic model accepts any string.

### 7.2 Critical Instruction to Storyteller

**`ccya/prompts/storytell_system.j2:82`**
```
**CRITICAL: `surface_as` is NOT a beat type.** Do NOT use `pressure`, `escalation`, `complication`, or any other beat type as a `surface_as` value.
```

### 7.3 Diversity Guidance

**`ccya/prompts/storytell_system.j2:94`**
```
**Diversity:** Don't repeat the same beat `type` more than twice consecutively. Vary `surface_as` turn to turn.
```

### 7.4 Checker

**`ccya/ev/checkers/pacing.py:128-159`** — Checks consecutive same-type beats don't flip `surface_as` without directive change.

### 7.5 Usage in Templates

`narrate_user.j2:88` passes it as "creative guidance" but tells narrator not to recite metadata. The field is essentially a rendering-style hint that currently has **no mechanical effect** on the beat lifecycle, expiration, or behavior.

---

## 8. Turn Pipeline Summary

```
USER_INPUT
  └─ Step 0: Ruling/Intent → Dice Resolution → Phase Engine
       └─ Step 1: Narrate [streaming]
            ├─ Reads pending_gm_beat (expiry check)
            ├─ Passes to _narrate_messages()
            └─ Renders in narrate_user.j2
       └─ Step 2a: Scene Extract
       └─ Step 2b: State Extract
       └─ Step 2c: Storytell
            ├─ Reads pending_gm_beat (passes to storytell_user.j2)
            ├─ Computes allowed_beat_types from pacing
            └─ LLM emits new gm_beat (or null)
       └─ Validate + Apply Delta
       └─ Post-extraction: new beat written to pending_gm_beat OR key popped
       └─ Persist (state.yaml, chronicle.md, events.jsonl)
```

**Key:** GM beats flow `storytell → pending_gm_beat → narrate`. The storyteller generates a beat, which is consumed by the narrator on the *next* turn. This means beats are always "shaping the scene atmosphere" for the turn *after* they were generated — not immediately.

---

## 9. Relevant Recent Commits

| Commit | Description |
|---|---|
| `b69308f2` | refactor: split turn.py into turn_context.py and turn_state.py |
| `6a0e166e` | engine/extraction: Split 803-line file into subpackage with 7 files |
| `00cf16fd` | Plan 05: Thread lifecycle tuning (config + throttle) + dormant/urgent invariant |
| `50eb04e8` | 05-phase-engine: Convergence score with type/dormant + SETUP TTL |
| `74841356` | 01-model-changes: Add type field, replace active with dormant on ArcThread |

Key structural change: `active` field replaced with `dormant` on ArcThread. Threading is now flat (no parent/child hierarchy).

---

## 10. Key File Index

| File | Lines | Purpose |
|---|---|---|
| `ccya/models/extraction.py` | 181-219 | GMBeat model + validator |
| `ccya/engine/turn.py` | 256-265 | Beat lifecycle: write/pop pending_gm_beat |
| `ccya/engine/narrate.py` | 163-174 | Pre-narration expiry check |
| `ccya/engine/narrate.py` | 271 | Pass beat to _narrate_messages() |
| `ccya/engine/turn_state.py` | 470-480 | Beat history snapshot |
| `ccya/engine/_pacing.py` | 18-30 | BEAT_BUCKETS, BEAT_PHASE_MAP |
| `ccya/engine/_pacing.py` | 61-83 | derive_allowed_beat_types() |
| `ccya/engine/_pacing.py` | 86-142 | compute_convergence_score() (beat streak) |
| `ccya/engine/_pacing.py` | 222-294 | _compute_scene_phase() (5-phase machine) |
| `ccya/engine/extraction/storytell.py` | 87 | Pass pending_beat to storytell prompt |
| `ccya/prompts/narrate_system.j2` | 11, 65-71 | Beat priority ordering; NPC motivation/fear/leverage guidance |
| `ccya/prompts/narrate_user.j2` | 86-88 | Beat rendering in narrator prompt |
| `ccya/prompts/storytell_system.j2` | 27-28, 76-94 | Thread ID contract; beat schema, types, diversity |
| `ccya/prompts/storytell_user.j2` | 42-58, 78 | Beat context + allowed_beat_types |
| `ccya/prompts/sections/_npc_roster.j2` | 10 | NPC motivation/fear/leverage rendering |
| `ccya/ev/checkers/pacing.py` | 128-159 | surface_as consistency checker |
| `ccya/ev/checkers/gm_beat.py` | — | Beat lifecycle checker (not yet reviewed) |
| `ccya/personality.py` | 17-117 | NPC motivation/fear archetype keywords |
| `docs/architecture/state-models.md` | — | State schema documentation |
| `docs/architecture/OVERVIEW.md` | — | Pipeline overview |

---

## 11. Open Questions / Observations

1. **Beat generation is reactive, not proactive.** The storyteller sees the *previous* turn's beat (or none) and generates the *next* beat. This means every turn's beat was actually generated by the storyteller on the prior turn's pass. The beat shaping turn N+1 was created by a storyteller reacting to turn N's state.

2. **`surface_as` has no mechanical effect.** It is rendered in prompts but has no impact on lifecycle, expiration, or behavior. It could be removed without any functional change.

3. **NPC motivation/fear/leverage are narrator-only guidance**, not used by the storyteller in beat generation. The storyteller receives `pending_beat`, `allowed_beat_types`, `recent_beats`, and `active_threads` — but not NPC psychological fields.

4. **Beat expiry is 2 turns.** `beat_expires_turn = turn_no + 2` means a beat lives for 2 turns maximum before being auto-nulled.

5. **Beat history is post-floor-relief**, meaning the beat snapshot reflects the state after floor relief override is applied — not the raw beat that was passed to narration.

6. **Threading is flat** — no parent/child hierarchy despite the user's description of "threads" suggesting otherwise. The `ArcThread` model is a flat list with dormancy and urgency.
