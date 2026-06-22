# Plan 04: Tiered NPC List

## Status
completed

**Replaces:** `known_npcs` + `present_npcs` + `recently_left` as three separate NPC inputs to Step 1

---

## Problem

The narrator in Step 1 currently receives three separate NPC-related inputs:

1. **`known_npcs`** — LRU-10 compendium slice: last-seen location, bio, motivation, fear, leverage. These are characters the world knows about but who may not be present.
2. **`present_npcs`** — Characters currently in the scene: attitude notes, motivation, fear, leverage. These overlap heavily with `known_npcs` for characters who happen to be present.
3. **`recently_left`** — Characters who left the scene this turn. Rendered in a separate section with a "do not write dialogue for these" caveat.

In `narrate_user.j2`, these produce three adjacent sections:
- `## Known Characters` (from `known_npcs`)
- `## NPCs Present in Scene` (from `present_npcs`)
- `## Recently Left` (from `recently_left`)

For any NPC who is *present*, the narrator gets their data twice — once in Known Characters with bio and last_seen, and again in NPCs Present with attitude notes. For any NPC who *just left*, there's a third partial entry. The narrator has to reconcile all three to know who is actually standing in the room.

The sections also have inconsistent header names (`Known Characters` vs `NPCs Present in Scene` vs `Recently Left`) and inconsistent field rendering — `known_npcs` shows `last_seen.location_name`, `present_npcs` shows `notes`, and `recently_left` shows only name and title. No single section gives the full picture.

---

## Solution

Merge all three into a single `npc_roster` list, where presence is a **property** of each entry, not a separate list. The narrator sees one section: `## Characters`. Every NPC in that section has a consistent field set and a `presence` field that tells the narrator exactly where they stand.

### NPC roster entry model

```python
class NpcPresence(str, Enum):
    PRESENT      = "present"       # in the scene right now
    JUST_LEFT    = "just_left"     # departed this turn
    NEARBY       = "nearby"        # known to be in the area (same location cluster)
    KNOWN        = "known"         # seen before, current location unknown

@dataclass
class RosterEntry:
    id:           str
    name:         str
    title:        str | None
    bio:          str | None
    presence:     NpcPresence
    motivation:   str | None       # always shown when present
    fear:         str | None       # always shown when present
    leverage:     str | None       # always shown when present
    notes:        str | None       # scene-specific attitude/state notes
    last_seen:    str | None       # location name — shown for KNOWN only
```

### Assembly

```python
def build_npc_roster(
    present_npcs:   list[NpcRef],
    known_npcs:     list[NpcRef],     # LRU-10 compendium slice
    recently_left:  list[NpcRef],
) -> list[RosterEntry]:
    """
    Merge into one ordered list. Priority order: PRESENT > JUST_LEFT > NEARBY > KNOWN.
    Dedup by id — the highest-priority presence wins.
    """
    seen: dict[str, RosterEntry] = {}

    for n in present_npcs:
        seen[n.id] = RosterEntry(
            id=n.id, name=n.name, title=n.title,
            bio=n.bio,
            presence=NpcPresence.PRESENT,
            motivation=n.motivation, fear=n.fear, leverage=n.leverage,
            notes=n.notes,
            last_seen=None,
        )

    for n in recently_left:
        if n.id not in seen:
            seen[n.id] = RosterEntry(
                id=n.id, name=n.name, title=n.title,
                bio=n.bio,
                presence=NpcPresence.JUST_LEFT,
                motivation=None, fear=None, leverage=None,
                notes=None,
                last_seen=None,
            )

    for n in known_npcs:
        if n.id not in seen:
            seen[n.id] = RosterEntry(
                id=n.id, name=n.name, title=n.title,
                bio=n.bio,
                presence=NpcPresence.KNOWN,
                motivation=n.motivation, fear=n.fear, leverage=n.leverage,
                notes=None,
                last_seen=n.last_seen.location_name if n.last_seen else None,
            )

    # Order: PRESENT first, JUST_LEFT second, rest alphabetical by name
    order = {NpcPresence.PRESENT: 0, NpcPresence.JUST_LEFT: 1,
             NpcPresence.NEARBY: 2, NpcPresence.KNOWN: 3}
    return sorted(seen.values(), key=lambda e: (order[e.presence], e.name))
```

---

## Template changes

### `narrate_user.j2` — replace three NPC sections with one

**Remove all three existing sections:**
```jinja2
{# REMOVE #}
{% if recently_left -%}
## Recently Left (do NOT write dialogue or action for these — may briefly acknowledge their departure)
{% for n in recently_left %}- {{ n.name or n }}{% if n is mapping and n.get('title') %} ({{ n.title }}){% endif %}
{% endfor -%}
{% endif -%}

{# REMOVE #}
{% if known_npcs -%}
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
{% for n in known_npcs %}...
{% endfor -%}
{% endif -%}

{# REMOVE #}
{% if present_npcs -%}
### NPCs Present in Scene
{% for n in present_npcs %}...
{% endfor -%}
{% endif -%}
```

**Extract to `sections/_npc_roster.j2`:**

```jinja2
{# sections/_npc_roster.j2 #}
{# npc_roster: list[RosterEntry], ordered PRESENT → JUST_LEFT → KNOWN #}
{% if npc_roster -%}
## Characters
Before introducing a new named NPC, check this list first.

{% for n in npc_roster -%}
- **{{ n.name }}**{% if n.title %} ({{ n.title }}){% endif %} [{{ n.presence | upper }}]{% if n.bio %} — {{ n.bio }}{% endif %}
{%- if n.notes %} | {{ n.notes }}{% endif %}
{%- if n.motivation %} | wants: {{ n.motivation }}{% endif %}
{%- if n.fear %} | fears: {{ n.fear }}{% endif %}
{%- if n.leverage %} | leverage: {{ n.leverage }}{% endif %}
{%- if n.last_seen %} | last seen: {{ n.last_seen }}{% endif %}
{%- if n.presence == 'just_left' %} — Do not write dialogue or new action for this character this turn.{% endif %}

{% endfor -%}
{% endif %}
```

In `narrate_user.j2`, replace all three removed sections with:
```jinja2
{% include "sections/_npc_roster.j2" %}
```

**Position:** Immediately before `## Scene Context` (where `## Known Characters` currently lives), after `## inventory`.

---

## System prompt changes (`narrate_system.j2`)

The NPC behavior section already handles motivation/fear/leverage correctly and doesn't need changes. One sentence update to the re-use instruction:

**Current:**
> Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.

**Updated (in system prompt NPC section):**
> The `## Characters` list in the user prompt shows everyone relevant to this scene, tagged with their presence status. `PRESENT` means they are in the room. `JUST_LEFT` means they departed this turn — do not write new dialogue for them, but you may briefly acknowledge their exit. `KNOWN` means they are not in the scene but could plausibly arrive — re-use them before creating new characters.

---

## Extractor changes (`extract_progress_user.j2`)

Step 2c currently receives `present_npcs` and `known_npcs` as separate lists and renders them in two separate sections. Apply the same merge:

**Remove:**
```jinja2
{# REMOVE #}
{% if present_npcs -%}
## present_npcs (in scene right now)
...
{% endif -%}

{# REMOVE #}
{% if known_npcs -%}
## known_characters (not in scene — system-called, for reasoning only)
...
{% endif -%}
```

**Replace with a minimal roster.** The extractor does not need the full roster — it needs
the `id` for referencing pressures and beats, and the name for readability. `recently_left`
is not relevant to the extractor (it manages structural state, not prose). Use a simpler
shared section, `sections/_npc_roster_extract.j2`:

```jinja2
{# sections/_npc_roster_extract.j2 — minimal form for extractors #}
{% if npc_roster -%}
## characters
{% for n in npc_roster -%}
- `{{ n.id }}` | **{{ n.name }}**{% if n.title %} ({{ n.title }}){% endif %} [{{ n.presence | upper }}]{% if n.bio %} — {{ n.bio }}{% endif %}{% if n.last_seen %} — last seen: {{ n.last_seen }}{% endif %}
{% endfor %}
{% endif %}
```

In `extract_progress_user.j2`, replace the two removed sections with:
```jinja2
{% include "sections/_npc_roster_extract.j2" %}
```

Note: Step 2c's `gm_beat` grounding rule ("instruction must reference a specific named entity
already present in state") currently points to `Present NPCs list`. Update it to
reference `## characters` roster where `presence == PRESENT`.

---

## Python payload changes

In `build_narrate_payload()` and `build_extract_progress_payload()`:

```python
# Before
payload["known_npcs"]    = build_known_npcs(state, compendium_lru=10)
payload["present_npcs"]  = state.scene.present_npcs
payload["recently_left"] = get_recently_left(state)   # narrate only

# After — same for both callers
payload["npc_roster"] = build_npc_roster(
    present_npcs=state.scene.present_npcs,
    known_npcs=build_known_npcs(state, compendium_lru=10),
    recently_left=get_recently_left(state),   # empty list for extract_progress
)
# known_npcs, present_npcs, recently_left removed from payload
```

`get_recently_left()` is not called for the extractor payloads — pass `[]` for
`recently_left` in extractor contexts. Characters marked `JUST_LEFT` are irrelevant
to the extractor and would add noise.

---

## What gets deleted

- `known_npcs`, `present_npcs`, `recently_left` as payload keys in both narrator and extractor payloads
- The three-section NPC block in `narrate_user.j2` (Known Characters / NPCs Present / Recently Left)
- The two-section NPC block in `extract_progress_user.j2` (present_npcs / known_characters)

## What gets added

- `NpcPresence` enum
- `RosterEntry` dataclass  
- `build_npc_roster()` function
- `sections/_npc_roster.j2` (narrator — full fields)
- `sections/_npc_roster_extract.j2` (extractor — id + presence + name + bio + last_seen only)

---

## Section philosophy note

This plan creates two section files that differ in verbosity by design. The narrator
needs full character detail to write good prose. The extractor needs IDs and presence
status to correctly reference entities in its JSON output. Sharing one section file
between them would mean either over-informing the extractor or under-informing the
narrator. Two files, one data source.

---

## Migration

No state migration. `NpcRef` objects in `state.yaml` are unchanged — `build_npc_roster()`
reads them at runtime and produces `RosterEntry` objects that never touch state. Old
saves load identically; the roster is assembled fresh each turn.

---

## Summary of delta

| Before | After |
|--------|-------|
| 3 payload keys: `known_npcs`, `present_npcs`, `recently_left` | 1 payload key: `npc_roster` |
| 3 template sections with inconsistent field sets | 1 `## Characters` section with consistent fields and explicit `[PRESENCE]` tags |
| Present NPCs appear twice (Known + Present sections) | Each NPC appears exactly once |
| `recently_left` caveat buried in its own header | `just_left` caveat inline on the character entry |
| Extractor renders two separate NPC lists | Extractor renders one minimal roster |
| 6 total template sections across both templates | 2 section files (one full, one minimal) |
