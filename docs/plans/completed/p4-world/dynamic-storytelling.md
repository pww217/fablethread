# Plan: P4 — Dynamic Storytelling

Consolidates `world-prop-injection.md` and `narrative-quality-pacing.md` into 5 independent phases.
Each phase is a single concern, self-contained, and can be developed/tested independently.

**Goal:** Make the story feel alive — NPCs die, factions move, locations shift, tension breathes.
The narrator gets the right context at the right time to produce dynamic, consistent, believable fiction.

---

## Phase 1 — Threat Lifecycle

**Concern:** Scene pressure accumulation, missing de-escalation, stale threats.

### Problem

`scene_pressure` entries only escalate (`background → building → immediate`) and expire via `max_turns`. Nothing de-escalates them. The progress extractor is guarded from adding new pressures when any exist, and has no de-escalation path. Result: 11 IMMEDIATE threats accumulate, narrator sees all of them every turn, story becomes incoherent.

Additionally, `_expire_scene_pressures()` runs post-extraction — the progress extractor sees pressures that should have been cleaned up, making removal decisions with stale data.

### Changes

**1A. Engine-side pressure purge** — New function in `engine/pressure.py`: `_purge_scene_pressures()`

Runs before extraction, removes pressures that are no longer relevant based on hard state changes:

- **Location change:** If `scene_result.location_change` is not null, remove ALL pressures. They were tied to the old location.
- **Combat end:** If `"combat"` was in `scene_tags` last turn but is NOT in current `scene_tags`, remove all pressures that were combat-related. 
- **Age cap:** Pressures older than `scene_pressure_max_age` (new config, default 15 turns) get auto-removed. Even unresolved threats can't persist forever.

```python
# engine/pressure.py — new function
def _purge_scene_pressures(
    state: dict[str, Any],
    delta: StateDelta,
    *,
    location_changed: bool = False,
    combat_ended: bool = False,
    config: EngineConfig | None = None,
) -> None:
    """Remove pressures that are no longer relevant.

    Called post-extraction, before _expire_scene_pressures.
    """
    pressures = list((state.get("scene") or {}).get("scene_pressure") or [])
    current_turn = (state.get("meta") or {}).get("turn", 0)
    max_age = (config.scene_pressure_max_age if config else 15)

    if location_changed:
        # All pressures were location-bound — purge everything
        for p in pressures:
            if isinstance(p, dict):
                delta.scene_pressure_remove.append(p.get("id", ""))
        return

    removed: set[str] = set()
    for p in pressures:
        if not isinstance(p, dict):
            continue
        pid = p.get("id", "")
        if pid in removed:
            continue
        # Age cap
        turn_added = p.get("turn_added")
        if turn_added and turn_added > 0 and (current_turn - turn_added) >= max_age:
            removed.add(pid)
            continue
        # Combat end — remove immediate threats
        if combat_ended and p.get("urgency") == "immediate":
            removed.add(pid)
            continue

    delta.scene_pressure_remove.extend(sorted(removed))
```

Called from `turn.py` after extraction, before `_expire_scene_pressures()`. Needs `location_changed` (from `scene_result.location_change`) and `combat_ended` (compare current `scene_tags` with last turn's tags from events.jsonl).

**1B. De-escalation flag** — Computed in Python, pre-narrate

In `turn.py`, after rules outcome resolves:

```python
deescalate = (
    outcome.rolled
    and outcome.band in ("success", "crit_success")
    and any(
        p.get("urgency") in ("immediate", "building")
        for p in (state.get("scene") or {}).get("scene_pressure") or []
    )
)
```

Pass `deescalate` into `_narrate_messages()` and `_extract_progress_messages()`.

**1C. De-escalation in progress extractor** — Prompt change in `extract_progress_system.j2`

Add to `scene_pressure` field rules:

> If `deescalate` is true (injected in user prompt): do NOT emit `scene_pressure_add`. Instead emit `scene_pressure_update` to downgrade urgency: `immediate → building`, `building → background`. If the narration shows a pressure was fully resolved, emit `scene_pressure_remove`. Pair with a `breathing_room` GM beat.

**1D. GM beat guard relaxation** — Prompt change in `extract_progress_system.j2`

Current guard: "Emit `null` if current scene has active `scene_pressure` entries (don't pile on)."

Replace with: "Emit `null` if there are 3+ active pressures OR if `deescalate` is true (use `breathing_room` instead)."

**1E. Config additions** — `engine/config.py`

```python
scene_pressure_max_age: int = 15  # hard cap, auto-remove
scene_pressure_deescalate_on_success: bool = True  # gate for deescalate flag
```

**Files touched:** `engine/pressure.py`, `engine/turn.py`, `engine/config.py`, `engine/narrate.py`, `engine/extraction.py`, `prompts/extract_progress_system.j2`, `prompts/extract_progress_user.j2`, `prompts/narrate_user.j2`

---

## Phase 2 — Conditional Narration Arc

**Concern:** Static HIT/SHIFT/TURN/HOOK fires every turn, producing breathless prose.

### Problem

`narrate_system.j2` mandates the full arc every turn. The model always produces HIT→SHIFT→TURN→HOOK regardless of context. After a success, the narrator still introduces a twist and hook. After a failure, it still pivots dramatically. No breathing room.

### Changes

**2A. Strip arc from system prompt** — `narrate_system.j2`

Remove the "Beat structure" section entirely. Replace with a single principle:

> Each beat advances the fiction. Match the weight of your narration to the outcome and the scene's current state. The user prompt provides a Narration Directive for this specific turn — follow it.

**2B. Conditional arc in user prompt** — `narrate_user.j2`

Add a `## Narration Directive` section, rendered with Jinja conditionals based on engine-computed context:

```jinja2
## Narration Directive

{% if rules_outcome and rules_outcome.rolled %}
{% if rules_outcome.band in ("crit_success", "success") %}
RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.
{% if deescalate %}
BREATHE: A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn. Show the aftermath, not the next crisis.
{% endif %}
{% elif rules_outcome.band == "partial" %}
COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.
{% elif rules_outcome.band in ("fail", "crit_fail") %}
CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.
{% endif %}
{% else %}
NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.
{% endif %}

{% if scene_pressure and not deescalate %}
{% set immediate_count = scene_pressure | selectattr("urgency", "equalto", "immediate") | list | length %}
{% if immediate_count >= 3 %}
OVERWHELM: Multiple immediate threats. Focus on the most pressing one. Don't try to address everything at once — the player can't either.
{% elif immediate_count > 0 %}
PRESSURE: Active immediate threat(s). Keep them present and felt.
{% else %}
{% set building_count = scene_pressure | selectattr("urgency", "equalto", "building") | list | length %}
{% if building_count > 0 %}
TENSION: Danger is building — show it in the environment and character behavior, not in explicit new threats.
{% endif %}
{% endif %}
{% endif %}

{% if combat_age is defined and combat_age >= 3 %}
COMBAT FATIGUE: This fight has run {{ combat_age }} turns. Bring it to a decisive close — one side prevails, flees, or is incapacitated. Do not extend it.
{% endif %}

{% if location_age is defined %}
{% if location_age >= 6 %}
LOCATION IMPERATIVE: The party has been here {{ location_age }} turns. Begin steering toward a natural exit — pursuit, a new goal elsewhere, or the scene resolving into transit.
{% elif location_age >= 4 %}
LOCATION HINT: {{ location_age }} turns in this location. If a natural opening to move on presents itself, take it.
{% endif %}
{% endif %}
```

**2C. Remove "escalate or resolve" language from system prompt**

Current `narrate_system.j2` line 23: "If a situation has persisted 2+ turns, escalate or resolve it immediately — never linger."

Replace with: "Pacing is critical. Each beat must advance the plot meaningfully. No holding patterns. The Narration Directive in the user prompt tells you how to pace this specific turn."

**2D. Pass new context variables into `_narrate_messages()`**

Add to the function signature and context dict:
- `deescalate` (bool)
- `combat_age` (int, from Phase 3)
- `location_age` (int, from Phase 3)

**Files touched:** `prompts/narrate_system.j2`, `prompts/narrate_user.j2`, `engine/narrate.py`

---

## Phase 3 — Engine Computations

**Concern:** Missing age/staleness counters. Narrator has no mechanical signals about how long things have been going on.

### Problem

`scene_age` exists but only fires when no pressure is present. `location_age` doesn't exist. `combat_age` doesn't exist. `quest_age` is guessed by the extractor. The narrator has no way to know if a fight has been going on for 5 turns or if the player has been stuck in one room for 8 turns.

### Changes

**3A. Compute age counters in turn orchestrator** — `engine/turn.py`

New helper function, called after rules, before narrate:

```python
def _compute_ages(state: dict[str, Any]) -> dict[str, int]:
    """Compute age/staleness counters for narration directives."""
    meta = state.get("meta") or {}
    scene = state.get("scene") or {}
    location = state.get("location") or {}
    current_turn = meta.get("turn", 0)

    # Scene age: turns since scene started
    scene_entered = scene.get("turn_entered", 0)
    scene_age = current_turn - scene_entered if scene_entered > 0 else 0

    # Location age: turns at current location
    loc_entered = scene.get("location_entered_turn", 0)
    location_age = current_turn - loc_entered if loc_entered > 0 else 0

    # Combat age: turns since "combat" entered scene_tags
    tags = scene.get("tags") or []
    combat_entered = scene.get("combat_started_turn", 0)
    combat_age = current_turn - combat_entered if ("combat" in tags and combat_entered > 0) else 0

    return {
        "scene_age": scene_age,
        "location_age": location_age,
        "combat_age": combat_age,
    }
```

**3B. Track `location_entered_turn` and `combat_started_turn`** — `state/delta.py`

In `apply_delta()`, when `location_change` is applied:
```python
if delta.location_change:
    scene["location_entered_turn"] = current_turn
```

In `apply_delta()`, when `scene_tags` changes:
```python
new_tags = set(delta.scene_tags) if delta.scene_tags else set()
old_tags = set(state.get("scene", {}).get("tags") or [])
if "combat" in new_tags and "combat" not in old_tags:
    scene["combat_started_turn"] = current_turn
elif "combat" not in new_tags and "combat" in old_tags:
    scene.pop("combat_started_turn", None)  # combat ended
```

**3C. Quest age tracking** — computed in `turn.py`, passed to progress extractor

```python
def _compute_quest_ages(state: dict[str, Any], current_turn: int) -> list[dict[str, Any]]:
    result = []
    for q in (state.get("quests") or []):
        if q.get("status") != "active":
            continue
        last_advanced = q.get("last_advanced_turn", 0)
        stalled = current_turn - last_advanced if last_advanced > 0 else 0
        result.append({
            "id": q["id"],
            "title": q.get("title", ""),
            "stalled_turns": stalled,
        })
    return result
```

Pass into `_extract_progress_messages()` as `quest_ages`. In `extract_progress_user.j2`:

```jinja2
{% for qa in quest_ages %}
{% if qa.stalled_turns >= 3 %}
⚠ Quest "{{ qa.title }}" stalled for {{ qa.stalled_turns }} turns. Advance it, branch it, or mark an objective failed.
{% endif %}
{% endfor %}
```

**3D. Stamp `last_advanced_turn` on quests** — `state/delta.py`

When `quest_updates` marks an objective as done or changes quest status, set `quest["last_advanced_turn"] = current_turn`.

**3E. Pass ages into narrate context** — `engine/narrate.py`

`_narrate_messages()` receives `ages` dict, passes it through to `narrate_user.j2` as `scene_age`, `location_age`, `combat_age`.

**3F. Update `turn.py` pipeline**

Revised order:
```
Rules
→ [Python] compute deescalate, ages (location_age, combat_age, scene_age, quest_ages)
→ [Python] fetch known_npcs compact list (Phase 4 dependency, wire now)
→ Narrate (receives: deescalate, ages, known_npcs, outcome_band, scene_pressure, momentum)
→ Extraction pipeline
→ [Python] stamp last_scene on NPCs (Phase 4 dependency)
→ [Python] _purge_scene_pressures (Phase 1)
→ [Python] _expire_scene_pressures
→ Validate → Apply → Persist
```

**Files touched:** `engine/turn.py`, `engine/narrate.py`, `engine/extraction.py`, `state/delta.py`, `prompts/extract_progress_user.j2`

---

## Phase 4 — NPC System

**Concern:** Narrator invents NPCs every turn. No continuity. NPCs never die. No allegiance tracking.

### Problem

`_narrate_messages()` never calls `_known_characters_for_extract()`. The narrator has no compendium visibility. It sees `npc_name_pool` (10 random names) and `recently_left`, but not who's actually present or who exists in the world. Result: 20+ shallow characters, no continuity.

NPCs are too durable — the narrator hedges lethality. "Stumbles back" instead of dies.

No allegiance/faction tracking for NPCs or PC.

### Changes

**4A. Inject known NPCs into narrator** — `engine/narrate.py`

Call `_known_characters_for_extract(state, compact=True)` in `_narrate_messages()`, pass as `known_npcs` to `narrate_user.j2`:

```jinja2
{% if known_npcs %}
## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
{% for n in known_npcs %}
- **{{ n.name }}**{% if n.title %} ({{ n.title }}){% endif %}{% if n.last_scene %} — last seen turn {{ n.last_scene.turn }}: {{ n.last_scene.summary }}{% endif %}
{% endfor %}
{% endif %}
```

**4B. Strengthen narrator system prompt — NPC reuse rule**

In `narrate_system.j2`, replace current "NPCs in scene" section with:

> NPCs should feel like persistent people, not props. Re-use characters from the Known Characters list when the scene and location are consistent with their last known position. Only create a genuinely new character when the scene requires someone no existing character can fill. When introducing a new named NPC, pick from the name pool. Give a brief physical description.

**4C. `last_scene` field on compendium NPCs** — `models.py` + `state/delta.py`

Add to compendium NPC schema:
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

Stamp deterministically in `turn.py` after extraction, before persist:
```python
for npc_id in touched_npc_ids:  # from scene_result.npc_add + npc_update + compendium_npc_update
    comp["npcs"][npc_id]["last_scene"] = {
        "turn": turn_no,
        "location_id": location.get("id", ""),
        "location_name": location.get("name", ""),
        "summary": outcome_summary or "",
    }
```

No LLM call needed. `outcome_summary` from scene extractor already captures what happened.

**4C.5. Compendium UI — `last_scene` sub-text** — `templates/_state_left.html`

In the compendium sidebar, render `last_scene` as small sub-text below the NPC name, one sentence, styled like scene NPC `notes`:

```html
{% set ls = entry.last_scene if entry is mapping %}
<div class="compendium-item has-tooltip">
    <span class="compendium-line">{{ nm or nid }}{% if ttl %}<span class="compendium-title"> — {{ ttl }}</span>{% endif %}</span>
    {% if ls %}
    <span class="compendium-last-seen">Last seen: Turn {{ ls.turn }} · {{ ls.location_name }} — {{ ls.summary }}</span>
    {% endif %}
    <div class="tooltip-body" data-md>{{ bio or '—' }}</div>
</div>
```

Add CSS:
```css
.compendium-last-seen {
    display: block;
    font-size: 0.75em;
    color: var(--muted);
    margin-top: 2px;
    font-style: italic;
}
```

**4D. NPC mortality directive** — `narrate_system.j2`

Replace current mortality language with:

> NPCs die. In combat and high-stakes situations, NPCs who lose a confrontation are dead, incapacitated, or removed from the scene. This is the default outcome — not a special condition. Do not default to "stumbling back" or "retreating." When in doubt, remove them. The progress extractor will record their fate.

**4E. Progress extractor — enforce removal on death** — `extract_progress_system.j2`

Add to `compendium_npc_update` guidance:

> If the narration describes an NPC as killed, mortally wounded, captured, or permanently removed: emit `compendium_npc_update` with `bio` recording their fate in one sentence. The engine will stamp `last_scene`. Do not omit this update — dead NPCs must be recorded.

**4F. NPC allegiance field** — `models.py` + `state/delta.py`

Add `allegiance` field to compendium NPC entries and PC state:

```python
# CompendiumNpcUpdate gains:
allegiance: str | None = None  # faction ID, or "neutral" / "hostile" / "friendly"

# PC state gains:
"allegiance": "faction_id"  # or null
```

The progress extractor can set NPC allegiance from narration. The scene extractor can update PC allegiance when the player joins/leaves a faction.

**4G. Gender-aware name casting** — `engine/names.py` + `narrate_system.j2`

Add `generate_npc_names_split()` returning `{"male": [...], "female": [...]}`. Store both in name pool. Narrator system prompt:

> When the name pool provides separate male and female lists, select names appropriate to the role and setting. Historical combat genres: use male names for front-line combat roles. Modern and speculative settings: use any gender freely.

**4H. Present NPCs in narrator context**

Pass `state.scene.present_npcs` into narrate context. Render in `narrate_user.j2`:

```jinja2
{% if present_npcs %}
## NPCs Present in Scene
{% for n in present_npcs %}
- {{ n.name }}{% if n.title %} ({{ n.title }}){% endif %}{% if n.notes %} — {{ n.notes }}{% endif %}
{% endfor %}
{% endif %}
```

**Files touched:** `engine/narrate.py`, `engine/turn.py`, `models.py`, `state/delta.py`, `prompts/narrate_system.j2`, `prompts/narrate_user.j2`, `prompts/extract_progress_system.j2`, `engine/names.py`

---

## Phase 5 — Dynamic World

**Concern:** World feels static. No factions, no location variety, no outside forces.

### Problem

The world is whatever the narrator invents each turn. No persistent factions, no location roster, no outside motivations. The story has no backdrop beyond the current scene.

### Changes

**5A. Faction pool** — `engine/names.py` + state storage

At seed time (and dynamically during play), generate 3-4 faction names. Store in `state["world"]["factions"]`:

```python
def generate_faction_pool(seed: int | None = None, count: int = 4) -> list[dict[str, str]]:
    rng = random.Random(seed)
    adjectives = ["Iron", "Gilded", "Shadow", "Quiet", "Pale", "Broken", "Ash", "Crimson", "Silent", "Rusted"]
    nouns = ["Hand", "Circle", "Order", "Coin", "Brand", "Chain", "Compact", "Lodge", "Crown", "Veil"]
    alignments = ["hostile", "neutral", "friendly"]

    factions = []
    used = set()
    for _ in range(count):
        while True:
            name = f"The {rng.choice(adjectives)} {rng.choice(nouns)}"
            if name not in used:
                used.add(name)
                break
        factions.append({
            "id": slugify(name),
            "name": name,
            "alignment": rng.choice(alignments),
        })
    return factions
```

Called during seed generation and stored in `state["world"]["factions"]`. Also callable during play to inject new factions.

**5B. Location pool** — `engine/names.py` + state storage

Generate 4-5 location names at seed time. Store in `state["world"]["locations"]`:

```python
def generate_location_pool(seed: int | None = None, count: int = 5) -> list[dict[str, str]]:
    rng = random.Random(seed)
    # Compositional: modifier + suffix
    modifiers = ["Copper", "Tanner's", "Miller's", "Salt", "Old", "Low", "High", "Ember", "Dust", "River", "Harbor", "Ash", "Iron", "Wax", "Black", "Pale"]
    suffixes = ["gate", "ward", "quarter", "row", "yard", "cross", "lane", "end", "side", "docks", "market", "square"]

    locations = []
    used = set()
    for _ in range(count):
        while True:
            name = f"{rng.choice(modifiers)}{rng.choice(suffixes)}"
            if name not in used:
                used.add(name)
                break
            if len(used) > 100:  # safety valve
                name = f"District {len(locations) + 1}"
                break
        locations.append({
            "id": slugify(name),
            "name": name,
        })
    return locations
```

**5C. Dynamic faction injection** — `engine/turn.py` + `narrate_user.j2`

When the narrator needs a faction (political context, new location, GM beat), the engine injects available factions:

```jinja2
{% if world_factions %}
## Known Factions
{% for f in world_factions %}
- **{{ f.name }}** ({{ f.alignment }}){% if f.alignment == "friendly" and pc_allegiance == f.id %} — your faction{% endif %}
{% endfor %}
{% endif %}
```

Conditionally shown: inject when `scene_tags` contains `dialogue` or `market`, or when `location_age >= 3` (new location context).

**5D. Dynamic location injection** — `narrate_user.j2`

When `location_age >= 3` or GM beat suggests movement, inject available locations:

```jinja2
{% if world_locations and (location_age is defined and location_age >= 3) %}
## Nearby Locations (use when steering the player toward a new area)
{% for loc in world_locations %}
- {{ loc.name }}
{% endfor %}
{% endif %}
```

**5E. Faction injection via GM beats** — `extract_progress_system.j2`

Extend GM beat types to include faction activity:

> When emitting a `complication` or `pressure` beat, you may reference factions from the Known Factions list. Example: "The Iron Compact has been seen recruiting in the docks."

**5F. PC allegiance in narrator context**

Pass `pc.allegiance` into narrate context. Used to mark which faction the player belongs to in the factions list.

**5G. Seed-time initialization** — `engine/seed.py`

During seed generation, call `generate_faction_pool()` and `generate_location_pool()` with the game seed. Store in `state["world"]`. Set initial `pc.allegiance = null`.

**5H. Narrator system prompt — world consistency**

Add to `narrate_system.j2`:

> When the user prompt provides named factions or locations, use them rather than inventing new ones. Do not use all of them — pick what fits the scene. Unused entries remain available for future turns. Factions have alignments (hostile/neutral/friendly) — reflect this in how they interact with the player.

**Files touched:** `engine/names.py`, `engine/seed.py`, `engine/turn.py`, `engine/narrate.py`, `state/io.py`, `prompts/narrate_system.j2`, `prompts/narrate_user.j2`, `prompts/extract_progress_system.j2`

---

## Phase Dependencies

```
Phase 1 (Threat Lifecycle)  — independent
Phase 2 (Conditional Arc)   — depends on Phase 3 (needs deescalate, ages)
Phase 3 (Engine Computations) — independent
Phase 4 (NPC System)        — depends on Phase 3 (needs ages for pipeline sequencing)
Phase 5 (Dynamic World)     — independent
```

Recommended implementation order: 1 → 3 → 2 → 4 → 5

Phases 1 and 3 can be developed in parallel. Phase 2 requires Phase 3's computed values. Phase 4 requires Phase 3's pipeline sequencing. Phase 5 is independent.

---

## What's Deferred

The following items from the original plans are explicitly deferred:

- **Rumor pool** — template-filled rumors. Defer until faction system proves valuable.
- **Object epithet pool** — named items. Defer; current inventory system suffices.
- **Typed place pool generation** (settlements, taverns, wilderness) — simplified to location pool in Phase 5.
- **Locale-aware word lists by genre** — defer to pack configuration overhaul.
- **Location-keyed NPC storage** — replaced with simpler `last_scene` field (Phase 4C).
- **Character traits/relationships/avatars** — defer. `last_scene` + allegiance provides sufficient continuity.
- **Scope post-narration** — defer until streaming improvements land.
- **`npc_scene_age` tracking** — defer. `last_scene` + scene cap handles staleness.
- **`pressure_age` in narrator** — covered by age cap purge in Phase 1.
