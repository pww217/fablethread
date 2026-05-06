# Plan: Narrative Quality, Pacing, and NPC Continuity

## Context

This plan addresses a cluster of interconnected problems observed in play:

- Combat and tense scenes loop indefinitely — the engine escalates but never de-escalates, even on good rolls
- The narrator invents new NPCs every 1-2 turns because it cannot see the compendium, producing 20+ shallow characters
- The HIT→SHIFT→TURN→HOOK arc fires every single turn, producing breathless, over-dramatic prose
- Historical/genre-appropriate NPC gender casting is broken (female names in WW2 combat roles)
- Scene and quest staleness has no mechanical weight — nothing pushes the story forward to a new location
- NPCs are too durable; the narrator avoids killing or decisively removing them

This plan is a companion to `world-prop-injection.md`. Where that plan covers what gets seeded into the world, this plan covers how the engine uses that material turn-by-turn to produce better stories.

---

## Problem 1: Escalation Without De-escalation

### Root Cause

`scene_pressure` auto-escalates: `background → building` at turn 6, `building → immediate` at turn 10 (`config.py: scene_pressure_building_at`, `scene_pressure_immediate_at`). Nothing in the engine drives de-escalation when the player rolls well. The narrator system prompt also instructs it to always advance and escalate. Both systems push in one direction.

The result: once combat or danger starts, the only exit is the player abandoning the scene. Good rolls produce more danger, not less.

### Fix A: `deescalate` flag (engine, pre-narrate)

After `rules_outcome` resolves and before narration begins, compute a `deescalate` flag in the turn orchestrator:

```python
# engine/turn.py — post-rules, pre-narrate
deescalate = (
    outcome.band in ("success", "crit_success")
    and any(
        p.get("urgency") in ("immediate", "building")
        for p in (state.get("scene") or {}).get("scene_pressure") or []
    )
)
```

Pass `deescalate` into:
1. `_narrate_messages()` context → `narrate_user.j2`
2. `_extract_progress_messages()` context → `extract_progress_user.j2`

### Fix B: Pressure de-escalation in progress extractor

In `extract_progress_system.j2`, add to the `scene_pressure` rules:

> If `deescalate` is true: do NOT emit `scene_pressure_add`. Emit `scene_pressure_update` to downgrade any `immediate` → `building` and any `building` → `background`. If the pressure was fully resolved by the player action, emit `scene_pressure_remove` instead. Pair this with a `breathing_room` GM beat.

### Fix C: Config flags for de-escalation thresholds

Add to `EngineConfig`:

```python
scene_pressure_deescalate_on_success: bool = True
scene_pressure_deescalate_steps: int = 1  # how many urgency levels to step back per success
```

---

## Problem 2: Mandatory Drama Every Turn (HIT/SHIFT/TURN/HOOK)

### Root Cause

The HIT→SHIFT→TURN→HOOK arc in `narrate_system.j2` is a static mandatory structure. The model lands an outcome (HIT), pivots the scene (SHIFT), introduces a twist (TURN), and adds a new pressure (HOOK) — every single turn. This produces "The shift is immediate and violent"-style prose even after a simple success.

### Fix: Jinja-conditional arc segments in `narrate_user.j2`

Move the arc instruction out of `narrate_system.j2` entirely and into `narrate_user.j2` as conditional blocks based on the engine state passed in at call time. The system prompt states the principle; the user prompt gives the specific instruction for this turn.

Pass into `_narrate_messages()`:
- `outcome_band` (from `rules_outcome.band` or `""` if no roll)
- `deescalate` (bool, from Fix A above)
- `scene_pressure` (live list)
- `scene_age` (already present)
- `location_age` (see Problem 5)
- `momentum` (from PC state)

Example Jinja in `narrate_user.j2`:

```jinja2
## Narration Directive

{% if outcome_band in ("success", "crit_success") %}
RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence. Do not soften it.
{% if deescalate %}
BREATHE: A pressure has resolved. Pull back. Let the scene have a moment. No new hook this turn.
{% endif %}
{% elif outcome_band == "partial" %}
COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a new catastrophe.
{% elif outcome_band in ("fail", "crit_fail") %}
CONSEQUENCE: The action failed. One cost. Don't pile on.
{% else %}
NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.
{% endif %}

{% if not deescalate and scene_pressure %}
{% set highest = scene_pressure | sort(attribute="urgency", reverse=True) | first %}
{% if highest.urgency == "immediate" %}
PRESSURE: An active immediate threat — keep it present and felt without manufacturing new crises.
{% elif highest.urgency == "building" %}
TENSION: Danger is building — show it in the environment and character behavior, not in explicit new threats.
{% endif %}
{% endif %}

{% if location_age >= 6 %}
LOCATION IMPERATIVE: The party has been here {{ location_age }} turns. Begin steering toward a natural exit — pursuit, a new goal elsewhere, or the scene resolving into transit. Plant the seed this turn even if the move happens next.
{% elif location_age >= 4 %}
LOCATION HINT: {{ location_age }} turns in this location. If a natural opening to move on presents itself, take it.
{% endif %}
```

The TURN and HOOK only appear when the engine says the scene is stale or the fiction requires it — not by default every turn.

---

## Problem 3: Compendium Invisible to Narrator

### Root Cause

`_narrate_messages()` never calls `_known_characters_for_extract()`. The narrator has no idea who exists in the world and invents new NPCs every turn. The existing `window_turns` recent narrations do pass through — but the model doesn't reliably recognize its own invented names.

### Fix A: Inject compact known-NPC list into `narrate_user.j2`

In `narrate.py`, call `_known_characters_for_extract(state, compact=True)` and pass the result as `known_npcs` into the narrate context. Render in `narrate_user.j2`:

```jinja2
{% if known_npcs %}
## Known Characters
Before introducing anyone new, check this list. Re-use characters from it when they could plausibly be present.
{% for n in known_npcs %}
- **{{ n.name }}**{% if n.title %} ({{ n.title }}){% endif %}{% if n.last_scene %} — last seen turn {{ n.last_scene.turn }} at {{ n.last_scene.location_name }}: {{ n.last_scene.summary }}{% endif %}
{% endfor %}
{% endif %}
```

Also strengthen the system prompt instruction:
> Before introducing any new NPC, re-read the recent narration provided. If a character was mentioned there, use them. Prefer re-introducing characters from the Known Characters list when the scene and location are consistent with their last known position. Only create a genuinely new character when the scene requires someone no existing character can fill.

### Fix B: Tighten "fewer than 3" scene presence rule

The current rule removes NPCs from the scene delta until only 2-3 remain, even when others are nearby. Replace with:

> Remove an NPC from the active scene only if the narration explicitly describes them leaving, being incapacitated, or dying. If an NPC is in the same location and has any plausible connection to current events, keep them in scene. The scene NPC count is a reflection of the fiction, not a target to minimize.

---

## Problem 4: NPC Gender and Role Casting

### Root Cause

`generate_npc_names()` calls `faker.name()` which returns gendered or ungendered names with no role context. A WW2 combat pack gets `Amanda` as a machine gunner because the locale config has no gender or role signal.

### Fix A: Gender-split name generation in `names.py`

Add `generate_npc_names_split()`:

```python
def generate_npc_names_split(
    locales: list[dict],
    *,
    count_male: int = 6,
    count_female: int = 4,
    seed: int | None = None,
) -> dict[str, list[str]]:
    rng = random.Random(seed)
    fakers, weights = _build_weighted_fakers(locales, rng, seed)

    def pick() -> Faker:
        return rng.choices(fakers, weights=weights, k=1)[0]

    return {
        "male": [
            pick().first_name_male() + " " + pick().last_name()
            for _ in range(count_male)
        ],
        "female": [
            pick().first_name_female() + " " + pick().last_name()
            for _ in range(count_female)
        ],
    }
```

Store both lists in the name pool under `npc_male` and `npc_female`. The existing `npc` key remains for backward compatibility.

### Fix B: Pack locale config `gender` field

Add an optional `gender` field to locale entries in pack YAML:

```yaml
name_locales:
  - locale: en_US
    weight: 1.0
    gender: male   # "male" | "female" | "any" (default)
```

When `gender` is specified, only generate names of that gender from that locale entry.

### Fix C: Narrator prompt — role-aware gender casting

In `narrate_system.j2`:

> When the name pool provides separate `npc_male` and `npc_female` lists, select names appropriate to the role. Historical combat genres (WW2, medieval warfare, etc.): use male names for front-line combat roles. Female names are appropriate for support, medical, intelligence, and civilian roles unless the setting or pack explicitly indicates otherwise. Modern and speculative settings: use any gender freely unless the pack specifies.

---

## Problem 5: Scene Age and Location Age as Mechanical Signals

### Root Cause

`scene_age` is computed and injected into `narrate_user.j2` but only as a hint when `scene_pressure` is absent — meaning it never fires during combat (which always has pressure). Location age is not tracked separately from scene age, though a location can contain multiple scenes.

### Fix A: Always pass `scene_age` and add `location_age`

Compute `location_age` in the turn orchestrator: count of turns with the same `location.id`. Pass both into narrate context regardless of pressure state.

In `narrate_user.j2`, gate location-move hints on `location_age`, not `scene_age`. The conditional arc template in Problem 2 already shows the correct structure.

### Fix B: `quest_age` — authoritative stall tracking

Currently the progress extractor guesses quest staleness from context. Make it authoritative:

In the turn orchestrator, compute per-quest stall counts:

```python
def _compute_quest_ages(state: dict, turn_no: int) -> list[dict]:
    result = []
    for q in (state.get("quests") or []):
        if q.get("status") != "active":
            continue
        stall_since = q.get("objective_set_turn") or turn_no
        result.append({"id": q["id"], "title": q.get("title", ""), "stalled_turns": turn_no - stall_since})
    return result
```

Pass `quest_ages` into `_extract_progress_messages()`. In `extract_progress_user.j2`:

```jinja2
{% for qa in quest_ages %}
{% if qa.stalled_turns >= 3 %}
⚠ Quest "{{ qa.title }}" has had no objective progress for {{ qa.stalled_turns }} turns. Advance it, branch it, or mark an objective failed.
{% endif %}
{% endfor %}
```

### Fix C: Additional age/staleness counters

| Counter | Tracks | Where computed | Where injected |
|---|---|---|---|
| `scene_age` | Turns in current scene | Turn orchestrator | `narrate_user.j2` (already exists, extend) |
| `location_age` | Turns at current location ID | Turn orchestrator | `narrate_user.j2` |
| `quest_age` | Turns since quest objective last advanced | Turn orchestrator | `extract_progress_user.j2` |
| `pressure_age` | Already in `turn_added` on each pressure entry | Already stored | `narrate_user.j2` — expose per-pressure age |
| `combat_age` | Turns since `combat` tag entered `scene_tags` | Turn orchestrator | `narrate_user.j2` — fires "wrap up combat" directive at 3+ turns |
| `npc_scene_age` | Turns a specific NPC has been continuously in scene | Scene extractor delta | `narrate_user.j2` — suppress NPCs idle > 3 turns unless interacted with |

`combat_age` is the highest-value addition. When `combat` is in `scene_tags` and `combat_age >= 3`, inject into the narrate directive:

> COMBAT FATIGUE: This fight has run {{ combat_age }} turns. Bring it to a decisive close — one side prevails, flees, or is incapacitated. Do not extend it further with new complications.

---

## Problem 6: NPC `last_scene` Field

### Purpose

Give the narrator and the compendium UI a concrete anchor for every NPC: when they were last seen, where, and in what condition. Prevents the model from re-introducing characters as if fresh when they were last seen bleeding out three turns ago.

### Schema addition

Add to `CompendiumNPC`:

```python
class LastScene(BaseModel):
    turn: int
    location_id: str
    location_name: str
    summary: str  # one sentence: "fled the tavern brawl, wounded"

class CompendiumNPC(BaseModel):
    # ... existing fields ...
    last_scene: LastScene | None = None
```

### Stamping — no LLM call needed

Stamp `last_scene` in the turn orchestrator after extraction completes, using already-available data:

```python
# After _run_extraction_pipeline returns
for npc_id in scene_result.npc_add + [u.id for u in scene_result.npc_update]:
    state["compendium"]["npcs"][npc_id]["last_scene"] = {
        "turn": turn_no,
        "location_id": location.get("id", ""),
        "location_name": location.get("name", ""),
        "summary": scene_result.outcome_summary or "",
    }
```

This is deterministic — no prompt needed.

### UI

In the compendium panel, display under each NPC:
> Last seen: Turn 14 · Normandy Beach · *retreating east, arm wound*

### Narrator use

`last_scene` is included in the compact known-NPC list injected into `narrate_user.j2` (see Problem 3, Fix A). The model uses it to re-introduce NPCs with continuity: "Müller — last seen turn 12 fleeing the farmhouse — appears in the doorway."

---

## Problem 7: NPC Mortality — Narrator Reluctance

### Root Cause

The narrator hedges lethality. Enemy NPCs "stumble back," "fall wounded," or "retreat" rather than dying, because the default LLM behavior is to preserve characters. The system prompt's mortality language is permissive rather than directive.

### Fix A: Narrator system prompt — mortality directive

Replace current hedged language in `narrate_system.j2` with:

> **NPC mortality**: NPCs die. In combat and high-stakes genres, enemy NPCs who directly lose a confrontation against a player with a success or crit_success outcome are dead, incapacitated, or decisively removed from the scene. This is not a special condition — it is the default outcome for enemies who lose. Do not default to "stumbling back" or "retreating." If you need to preserve a character (named ally, plot-critical, established relationship), that requires an active narrative reason stated in the fiction — not silence. When in doubt, remove them.

### Fix B: Progress extractor — enforce removal on death

In `extract_progress_system.j2`, add to the `compendium_npc_update` guidance:

> If the narration describes an NPC as killed, mortally wounded, captured, or permanently removed: emit `compendium_npc_update` with `status: dead` (or `captured`/`gone`), update their `bio` to record their fate in one sentence, and emit `npc_remove` from the active scene. The `last_scene` will be stamped by the engine. Do not omit this update — dead NPCs must be recorded.

---

## Problem 8: Pipeline Sequencing (Pre / Post Narration)

### Current order

```
Rules → Narrate → [Scene extract → State extract → Progress extract]
```

### What should move

| What | Current timing | Should be | Rationale |
|---|---|---|---|
| `scope / active_domains` | Pre-narrate (rules prediction) | Post-narrate | Can't confirm relevant domains until narration exists; defer until streaming is improved |
| `deescalate` flag | Not computed | Pre-narrate (post-rules) | Must inform narrator — computed in Python, zero LLM cost |
| `known_npcs` compact list | Not in narrate | Pre-narrate | Narrator needs it to avoid inventing NPCs |
| `location_age` / `combat_age` | Not computed | Pre-narrate | Computed in Python; shape narrator directives |
| `last_scene` stamping | Not implemented | Post-narrate, pre-progress | Engine stamps from `scene_result.outcome_summary`; no LLM needed |
| NPC scene presence tightening | Scene extractor (post-narrate) | Already correct location | Strengthen the prompt, not the timing |

**Scope post-narration is deferred** until streaming improvements land. There is a plan in progress to decouple streaming from the extraction pipeline; once that exists, `active_domains` can be computed from the completed narration text by keyword match (no LLM call) and passed into the extractors.

### Revised order (near-term)

```
Rules
→ [Python] compute deescalate, location_age, combat_age, quest_ages
→ [Python] fetch known_npcs compact list
→ Narrate (receives: deescalate, location_age, combat_age, known_npcs, outcome_band, scene_pressure, momentum)
→ [Python] stamp last_scene on appearing NPCs
→ Scene extract
→ State extract
→ Progress extract (receives: quest_ages, deescalate)
```

---

## TODO Items

Add under `Mechanics` in `TODO.md`:

- [ ] **`deescalate` flag** — compute post-rules in turn orchestrator; pass to narrator and progress extractor. Gate narrator HOOK on this flag. See `narrative-quality-pacing.md`.
- [ ] **Conditional narrate arc** — replace static HIT/SHIFT/TURN/HOOK in system prompt with Jinja-conditional blocks in `narrate_user.j2` gated on `outcome_band`, `deescalate`, `scene_pressure`, `location_age`. See `narrative-quality-pacing.md`.
- [ ] **Known NPC injection into narrator** — call `_known_characters_for_extract(state, compact=True)` in `_narrate_messages()`; pass as `known_npcs`; render in `narrate_user.j2` with `last_scene` summary. See `narrative-quality-pacing.md`.
- [ ] **NPC scene presence rule tightening** — only remove NPCs from active scene if fiction explicitly says so; location proximity = keep in scene. See `narrative-quality-pacing.md`.
- [ ] **Gender-split name generation** — `generate_npc_names_split()` in `names.py`; `npc_male`/`npc_female` pools; optional `gender` field on pack locale entries. See `narrative-quality-pacing.md`.
- [ ] **`location_age` tracking** — turns at current `location.id`; drive location-change directive in narrator at 4+ and 6+ turns. See `narrative-quality-pacing.md`.
- [ ] **`combat_age` tracking** — turns since `combat` entered `scene_tags`; inject "wrap up combat" directive at 3+ turns. See `narrative-quality-pacing.md`.
- [ ] **`quest_age` authoritative tracking** — compute stall turns per active quest in orchestrator; pass to progress extractor; fire advance/branch directive at 3+ stalled turns. See `narrative-quality-pacing.md`.
- [ ] **`npc_scene_age` tracking** — turns each NPC has been continuously in scene; suppress idle NPCs in narrator after 3+ turns without interaction. See `narrative-quality-pacing.md`.
- [ ] **`pressure_age` in narrator** — expose `turn_added` delta per pressure in narrate context. See `narrative-quality-pacing.md`.
- [ ] **`last_scene` field on CompendiumNPC** — `{turn, location_id, location_name, summary}`; stamped by engine post-narrate, no LLM call. See `narrative-quality-pacing.md`.
- [ ] **NPC mortality directive** — strengthen narrator system prompt; add progress extractor rule to emit `compendium_npc_update` with `status: dead` on NPC death. See `narrative-quality-pacing.md`.
- [ ] **Scope post-narration** — defer until streaming improvements land; then compute `active_domains` from narration text by keyword match, pass to extractors. See `narrative-quality-pacing.md`.
