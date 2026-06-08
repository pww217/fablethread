# NPC Lifecycle Management — Departed Tracking, Nearby Decay, and Compendium Archive

## Purpose

Design authority for NPC lifecycle management: tracking permanent departure from the narrative, managing proximity decay, and archiving terminally-departed NPCs so they never appear in prompts but remain in the compendium for debugging and UI reference.

## Problem Statement

Two problems:

1. **No permanent departure signal.** When an NPC dies, sails away, falls into an irreversible coma, or is imprisoned for life, the scene extractor sets `presence: "known"` — the same signal used when an NPC merely exits a scene. The engine cannot distinguish permanent departure from temporary absence. Permanently-departed NPCs accumulate in the compendium forever.

2. **No proximity decay on location change.** When the player changes location, all present NPCs are demoted directly to `known` (in `delta_builder.py:222-228`). This loses the proximity signal — NPCs who were *right there* a moment ago are indistinguishable from NPCs last seen 20 turns ago. The LLM must re-establish proximity from scratch, which often means it forgets logically-following NPCs.

Result: compendium bloat (NPCs that should be removed never are) and roster quality degradation (prominent NPCs get same presence signal as long-forgotten ones).

## Constraints

- Must preserve narrative continuity: the narrator must be able to reference departed NPCs from chronicle context and prior_history.
- The scene extractor LLM controls the departure signal — the engine does not infer departure from game mechanics.
- Minimal blast radius: data model + archive step + one demotion change, not a pipeline restructuring.
- Token efficiency: departed NPCs should exit active prompt context within a few turns.
- Debuggability: all NPCs ever created remain in `state.yaml` for inspection. Archive is a state flag, not deletion.

## Non-goals

- No revival mechanic. Once `departed`, always `departed`. Once `archived`, always `archived`.
- No LLM inference of departure from momentum/band/conditions. Only explicit LLM signal.
- No migration of existing saves. NPCs previously killed via `presence: "known"` remain as-is.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Single terminal state | `presence: "departed"` covers all permanent exits | One signal, one archive path, one TTL — simpler than `is_dead` + `is_gone` |
| `departed_reason` + `departed_summary` | Structured fields alongside `presence: "departed"` | Serves player UI (compendium lookup) and narrator (structured context) |
| `departed_turn` set once by engine | `entry.get("departed_turn", current_turn_no)` | Prevents TTL clock reset on repeated emissions |
| `departed_archive_ttl` configurable | `int = 3` in `EngineConfig` | Per-save tuning; 3 turns is safe for narrative closure |
| Archive = presence flag, not deletion | `entry["presence"] = "archived"` in turn.py post-delta | Debuggability; UI can show archived characters; full record preserved |
| `build_npc_roster()` excludes archived | Pre-filter before main loop | Archived NPCs never bloat prompt context |
| Departed shown in roster during TTL | Sorted last, `[DEPARTED]` tag + reason | Narrator and player see structured departure signal before archive |
| `nearby` activated for location change | Demote `present → nearby` instead of `present → known` | Preserves proximity through location change |
| `nearby_decay_ttl = 2` | Auto-decay `nearby → known` after 2 turns | Prevents `nearby` bloat while giving time for re-entry |
| Scene extractor can re-promote `nearby → present` | Prompt teaches "re-promote, don't recreate" | Prevents duplicate NPC entries on location change |
| No backwards compatibility | Existing NPCs with `presence: "known"` remain as-is | No migration needed |
| Steps run every turn | After `last_seen` stamp: nearby decay → archive | Simple, no new orchestration |

## Current State — What Exists

### NPC data model

`CompendiumNpcUpdate` (in `ccya/models.py:245-258`) is the delta model the scene extractor emits. Fields: `id`, `name`, `title`, `bio`, `aliases`, `allegiance`, `motivation`, `fear`, `leverage`, `presence`, `notes`, `first_seen_turn`. No departed-tracking fields.

State NPC entries (in `state.yaml` under `compendium.npcs`) mirror these as plain dicts plus `last_seen` stamped by `turn.py:1229-1240`.

### NPC lifecycle

1. **Creation**: Scene extractor emits `compendium_npc_update` with `id`, `name`, `bio`, `presence: "present"` → `apply_npc_scene_management()` creates entry with `first_seen_turn`.
2. **Update**: Same function merges individual fields.
3. **Departure (current)**: Scene extractor sets `presence: "known"` → notes cleared. No distinction between "left the room" and "died permanently."
4. **Location change (current)**: `delta_builder.py:222-228` demotes all `present` NPCs to `known` — no proximity preservation.

### Presence enum

`NpcPresence` in `ccya/models.py:23-26` has `PRESENT`, `NEARBY`, `KNOWN`. `NEARBY` is dead code — no prompt instructs the LLM to emit it, no engine path assigns it. The sort order in `npc_roster.py:52-56` already has a slot for NEARBY (priority 2 between PRESENT=0 and KNOWN=3).

### Where NPC data is consumed

- **`build_npc_roster()`** (`ccya/engine/npc_roster.py`): iterates all `compendium.npcs`, filters/sorts by presence, truncates to `max_entries` (default 10). Used by every pipeline stage.
- **`_npc_roster.j2`**: renders NPC roster. Shows id, name, title, presence tag, bio, notes, motivation, fear, leverage, bond, last_seen.
- **`strip_npcs_notes()`** (`ccya/state/npcs.py:85`): clears `notes` from all NPCs at turn start.
- **`_dedup_compendium_update()`** (`ccya/engine/extraction.py:133`): pre-merge dedup.
- **`last_seen` stamp** (`turn.py:1229-1240`): post-delta stamp on updated NPCs.
- **`touch_compendium_order()`**: LRU tracking for present NPCs.

### Problems

1. **No permanent departure signal.** `presence: "known"` conflates temporary exit with permanent departure. Engine cannot route departed NPCs differently.
2. **No proximity decay.** Location change nukes proximity entirely → LLM loses continuity of logically-following NPCs.
3. **No compendium cleanup.** Every NPC ever created lives forever. Campaigns accumulate dozens of NPCs, all iterated every turn.
4. **Prompt token waste.** Departed NPCs are irrelevant but still rendered in every turn's Characters section.
5. **`NEARBY` is dead code.** Enum member exists but is never assigned — dead state littering the type system.

## Proposed Solution

### Presence continuum

The full NPC lifecycle forms a one-way progression:

```
present → nearby → known → departed → archived
```

| Value | Who sets it | Meaning | Engine action |
|---|---|---|---|
| `present` | LLM (scene extractor) | In the current scene, active | Full roster priority. LRU-tracked. |
| `nearby` | Engine (on location change — demote from `present`), LLM (optional — "just outside") | Was recently present at prior location; could re-enter without introduction | Demote to `known` after `nearby_decay_ttl` turns (default 2). Rendered with `[NEARBY]` tag. |
| `known` | LLM (scene exit) or engine (auto-decay from `nearby`) | Exists elsewhere, could return | Low roster priority. No auto-cleanup. |
| `departed` | LLM (scene extractor — permanent departure) | Permanently gone: dead, sailed away, comatose, imprisoned for life, ascended, etc. | Shown in roster during TTL with `[DEPARTED]` tag + reason. Archived after `departed_archive_ttl` (default 3). |
| `archived` | Engine (auto-transition from `departed` after TTL) | Permanently gone, removed from all prompt context | Completely excluded from `build_npc_roster()`. Never appears in prompts. Remains in `state.yaml` for debugging and compendium UI. |

`known` is the staging ground for NPCs who might return. `departed` is the narrative terminal state with a structured record. `archived` is the engine-internal cleanup state — record kept, prompts unaffected.

The progression is strictly forward. An `archived` NPC is never un-archived. A `departed` NPC is never un-departed. The LLM can re-promote `nearby` → `present` or `known` → `present` if narration calls for it, but `departed` and `archived` are final.

### Core changes

#### 1. Activate `nearby` — change location-change demotion

In `ccya/state/delta_builder.py:222-228`, change:

```diff
- entry["presence"] = "known"
+ entry["presence"] = "nearby"
+ entry["nearby_since_turn"] = current_turn
```

This preserves proximity. The scene extractor can also optionally set `presence: "nearby"` for NPCs described as "just outside" or "in the next room" — both engine and LLM paths converge on the same state.

#### 2. Add `nearby_decay_ttl` to `EngineConfig`

```python
@dataclass
class EngineConfig:
    # ... existing fields ...
    nearby_decay_ttl: int = 2       # turns before nearby → known auto-decay
    departed_archive_ttl: int = 3  # turns as "departed" before → archived
```

#### 3. Add nearby → known auto-decay step in `turn.py` post-delta

After the `last_seen` stamp section (after line 1240), before the archive step:

```python
# Decay nearby NPCs to known after TTL
nearby_ttl = config.nearby_decay_ttl if config else 2
comp = state.get("compendium", {}).get("npcs", {})
for entry in comp.values():
    if not isinstance(entry, dict):
        continue
    if entry.get("presence") == "nearby":
        nearby_since = entry.get("nearby_since_turn")
        if isinstance(nearby_since, int) and turn_no - nearby_since >= nearby_ttl:
            entry["presence"] = "known"
```

Also handle `nearby_since_turn` in `apply_npc_scene_management()`: if LLM sets `presence: "nearby"`, set `nearby_since_turn` to current turn.

#### 4. Add `departed_reason`, `departed_summary`, `departed_turn` to `CompendiumNpcUpdate`

```python
class CompendiumNpcUpdate(BaseModel):
    id: str
    name: str | None = None
    # ... existing fields unchanged ...
    presence: str | None = None       # "present" | "nearby" | "known" | "departed"
    notes: str | None = None
    first_seen_turn: int | None = None
    departed_reason: str | None = None    # NEW: short label, e.g. "killed in battle", "sailed away"
    departed_summary: str | None = None   # NEW: 1-2 sentence prose for compendium/UI
    departed_turn: int | None = None      # NEW: engine sets on first presence: "departed"
```

All default to `None` = no update. LLM emits `departed_reason` and `departed_summary` alongside `presence: "departed"`. `departed_turn` is engine-set only on first detection.

#### 5. Update `apply_npc_scene_management()` for departed and nearby

In `ccya/state/npcs.py:apply_npc_scene_management()`, after presence merge (line ~166):

```python
if comp_upd.presence == "departed":
    if comp_upd.departed_reason is not None:
        entry["departed_reason"] = comp_upd.departed_reason
    if comp_upd.departed_summary is not None:
        entry["departed_summary"] = comp_upd.departed_summary
    if current_turn_no is not None:
        entry["departed_turn"] = entry.get("departed_turn", current_turn_no)
    entry.pop("notes", None)

if comp_upd.presence == "nearby":
    if current_turn_no is not None:
        entry["nearby_since_turn"] = entry.get("nearby_since_turn", current_turn_no)
```

`departed_turn` is set only once (first detection), so repeated `departed` emissions don't advance the archive clock.

#### 6. Add archive step in `turn.py` post-delta — transition `departed → archived`

After the nearby-decay step:

```python
# Archive departed NPCs past TTL — they still exist in state.yaml
# but are excluded from all prompt context.
archive_ttl = config.departed_archive_ttl if config else 3
comp = state.get("compendium", {}).get("npcs", {})
archived_ids = []
for nid, entry in comp.items():
    if not isinstance(entry, dict):
        continue
    if entry.get("presence") == "departed":
        dep_turn = entry.get("departed_turn")
        if isinstance(dep_turn, int) and turn_no - dep_turn >= archive_ttl:
            entry["presence"] = "archived"
            archived_ids.append(nid)
if archived_ids:
    _log.info(
        "archived_departed_npcs ids=%s", sorted(archived_ids),
        extra={"turn": turn_no},
    )
```

No deletion. NPC remains in `compendium.npcs` with `presence: "archived"`, all fields intact (name, bio, departed_reason, departed_summary, etc.). The compendium UI can still display them in an "Archived" section for player reference.

#### 7. Update `build_npc_roster()` to exclude archived and departed-on-TTL

In `ccya/engine/npc_roster.py:build_npc_roster()`, add a pre-filter before the main loop:

```python
# Skip archived NPCs — never appear in prompts
if not isinstance(entry, dict):
    continue
if entry.get("presence") == "archived":
    continue
```

Update the sort order to include departed:

```python
order = {
    NpcPresence.PRESENT.value: 0,
    NpcPresence.NEARBY.value: 2,
    NpcPresence.KNOWN.value: 3,
    NpcPresence.DEPARTED.value: 5,
}
```

Departed NPCs appear at the bottom of the roster (below known), sorted by name, with at most `max_entries` total. The short TTL (3 turns) limits their impact on the roster count.

#### 8. Update `_npc_roster.j2` to render departed NPCs with reason

```diff
- `{{ n.id }}` | {% if n.name %}**{{ n.name }}**{% else %}[Unnamed]{% endif %}{% if n.title %} ({{ n.title }}){% endif %} [{{ n.presence | upper }}]{% if n.bio %} — {{ n.bio }}{% endif %}
+ `{{ n.id }}` | {% if n.name %}**{{ n.name }}**{% else %}[Unnamed]{% endif %}{% if n.title %} ({{ n.title }}){% endif %} [{{ n.presence | upper }}]{% if n.presence == "departed" and n.departed_reason %} — {{ n.departed_reason }}{% endif %}{% if n.bio and n.presence != "departed" %} — {{ n.bio }}{% endif %}
```

Departed NPCs show `[DEPARTED] — killed in battle` instead of the full bio, saving tokens while providing context.

#### 9. Update `strip_npcs_notes()` — skip departed and archived

In `ccya/state/npcs.py:strip_npcs_notes()` (line 85-94), don't clear notes for departed or archived NPCs — they're no longer in the active lifecycle:

```python
def strip_npcs_notes(state: dict[str, Any]) -> None:
    npcs = (state.get("compendium") or {}).get("npcs", {})
    for npc_id, entry in npcs.items():
        if isinstance(entry, dict) and entry.get("presence") not in ("departed", "archived"):
            entry.pop("notes", None)
```

#### 10. Update prompts

**`extract_scene_system.j2`** — Teach scene extractor about `departed` and `nearby` re-promotion:

In the NPC ENTER/EXIT RULE section, replace:

```diff
- Emit `compendium_npc_update { presence: "known" }` for every named NPC who narration indicates has left, fled, died, fainted, or been removed from the scene.
+ Emit `compendium_npc_update { presence: "known" }` for every named NPC who narration indicates has left, fled, fainted, or been removed from the scene.
+ Emit `compendium_npc_update { presence: "departed", departed_reason: "<short label>", departed_summary: "<1-2 sentence prose>" }` for every named NPC who narration indicates is permanently gone — dead, sailed away forever, comatose, imprisoned for life, ascended, or otherwise unreachable. This NPC will be removed from the active roster after a few turns. The `departed_reason` is a short label (e.g. "killed in battle", "sailed to sea"). The `departed_summary` is 1-2 sentences describing what happened, shown in the compendium UI.
+ Emit `compendium_npc_update { presence: "nearby" }` for NPCs described as being just outside, in the next room, watching from the shadows, or otherwise proximate but not in the immediate scene.
```

Add an entry-repromotion rule in the How to use compendium_npc_update section:

```diff
+ **NPC re-enters scene after location change:** If an NPC was demoted to `"nearby"` by an engine location change but the narration indicates they followed the player, set `presence: "present"` — do NOT create a new compendium entry. Re-promote the existing NPC.
```

Update the JSON schema (line 13) presence field to `"present|nearby|known|departed"` and add `departed_reason`, `departed_summary`.

Add field rules:
```
`departed_reason`: Required when `presence` is `"departed"`. Short label describing the departure. Examples: "killed in battle", "sailed away", "imprisoned for life".
`departed_summary`: Required when `presence` is `"departed"`. 1-2 sentences describing what happened, for the compendium and UI display.
```

**`extract_scene_system.j2` — Universal NPC Channel section** — Update the schema example:

```diff
- "presence": "present|known",
+ "presence": "present|nearby|known|departed",
```

**`narrate_system.j2`** — No change needed. Narrator already handles death and departure; departed NPCs are referenceable from history context.

**`storytell_system.j2`** — Add brief note:
```
- Departed NPCs (marked with `[DEPARTED]`) are permanently gone and will be archived after a few turns. Reference them from narrative history only — do not create threads or actions involving departed characters.
```

**`generate_seed_system.j2`** — Update presence schema to include `"departed"` and `"nearby"` alongside `"present"` and `"known"`.

**`_npc_roster.j2`** — Update per section 8 above.

### Integration: order of operations in `turn.py` post-delta

The post-delta section (after `last_seen` stamp at line 1240) runs in this order:

1. `last_seen` stamp (existing, line 1229-1240)
2. Arc/thread processing (existing, line 1242+)
3. **Nearby decay** (new) — demote `nearby` → `known` past TTL
4. **Departed archive** (new) — transition `departed` → `archived` past TTL

This order matters: nearby decay runs before archive, so an NPC who is both `nearby` and `departed` in the same turn is handled correctly.

### Alternatives Considered and Rejected

1. **Separate `is_dead` flag**: Rejected. Too narrow — departure covers death and other permanent exits uniformly.
2. **Tombstone record in compendium**: Rejected. Archive state is the tombstone — cleaner than a separate record because the full NPC data (bio, reason, summary) is preserved.
3. **Purge immediately on departure**: Rejected. TTL gives narrative breathing room for death scenes and immediate aftermath.
4. **Infer departure from `presence: "known"` + conditions**: Rejected. Engine has no reliable signal. Explicit LLM signal is more reliable.
5. **Separate `dead_characters` section in prompts**: Rejected for now. Departed NPCs during TTL are in the main roster with `[DEPARTED]` tag. After archive, they're in compendium history only.
6. **Full deletion on archive**: Rejected. Keeping `archived` records in state.yaml preserves debuggability and allows a compendium UI "Archived NPCs" section without inflating prompt context.

## Failure Modes and Risks

1. **LLM forgets to set `presence: "departed"`**. Mitigation: prompt teaches the field explicitly. Soft failure — NPC stays as `known` (current behavior), no data loss.
2. **NPC marked departed but narration contradicts**. Mitigation: rare but harmless. Scene extractor can omit departure on subsequent turns. The engine does not enforce permanence through the LLM interface.
3. **Departed TTL too short**. Mitigation: configurable. Default 3 is conservative for token savings.
4. **`departed_turn` advancement race**. Mitigation: `entry.get("departed_turn", current_turn_no)` ensures first emission sets the clock.
5. **NPC with active threads gets archived**. Mitigation: storyteller should resolve threads naturally. Threads referencing archived NPCs become dangling references — acceptable narrative friction.
6. **Empty roster after archive**. Mitigation: `build_npc_roster()` returns empty list, `_npc_roster.j2` uses `{% if npc_roster %}`, no crash.
7. **Location-change proximity spam**. Mitigation: `nearby_decay_ttl = 2`. NPCs left behind at a location decay to `known` within 2 turns.

## What Is Removed

Nothing. `NEARBY` stays in the enum — it's now actively used, not dead.

## What Is Unchanged

- `ccya/engine/narrate.py` — unchanged.
- `ccya/engine/extraction.py` — unchanged. Dedup logic does not interact with departed/archived fields.
- `ccya/state/delta.py` — unchanged. StateDelta carries new fields automatically.
- `ccya/state/inventory.py` — unchanged.
- `ccya/state/momentum.py` — unchanged.
- `ccya/state/chronicle.py` — unchanged.
- `ccya/engine/seed.py`, `ccya/engine/pack_gen.py` — unchanged.
- `ccya/models.py` — only `CompendiumNpcUpdate` gains fields; all other models unchanged.
- `ccya/prompts/extract_scene_user.j2`, `narrate_user.j2`, `storytell_user.j2`, `ruling_user.j2` — unchanged (they include `_npc_roster.j2`).
- `ccya/prompts/ruling_system.j2`, `narrate_system.j2` — unchanged.
- `ccya/state/delta_builder.py` — only the one line (`known` → `nearby`) changes.

## Model Shapes

### `CompendiumNpcUpdate` (ccya/models.py)

```python
class CompendiumNpcUpdate(BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    aliases: list[str] = Field(default_factory=list)
    allegiance: str | None = None
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    presence: str | None = None       # "present" | "nearby" | "known" | "departed"
    notes: str | None = None
    first_seen_turn: int | None = None
    departed_reason: str | None = None    # NEW
    departed_summary: str | None = None   # NEW
    departed_turn: int | None = None      # NEW — engine sets on first departed
```

### `EngineConfig` (ccya/engine/config.py)

```python
@dataclass
class EngineConfig:
    # ... existing fields ...
    nearby_decay_ttl: int = 2         # NEW
    departed_archive_ttl: int = 3    # NEW
```

### `NpcPresence` (ccya/models.py)

```python
class NpcPresence(str, Enum):
    PRESENT = "present"
    NEARBY = "nearby"
    KNOWN = "known"
    DEPARTED = "departed"            # NEW
```

(`ARCHIVED` is not in the enum — it's an engine-internal state, not an LLM-settable value.)

### State NPC entry shape (compendium.npcs[id]) — full lifecycle

```python
# Active phases (present/nearby/known):
{
    "name": str,
    "title": str | None,
    "bio": str | None,
    "aliases": list[str] | None,
    "allegiance": str | None,
    "motivation": str | None,
    "fear": str | None,
    "leverage": str | None,
    "presence": "present" | "nearby" | "known",
    "notes": str | None,
    "first_seen_turn": int,
    "last_seen": dict | None,
    "nearby_since_turn": int | None,
}

# Departed phase (TTL countdown — still in roster):
{
    # ... all active fields ...
    "presence": "departed",
    "departed_reason": str | None,
    "departed_summary": str | None,
    "departed_turn": int,
}

# Archived phase (post-TTL — excluded from prompts, kept in state.yaml):
{
    # ... all departed fields ...
    "presence": "archived",
}
```

## Files touched

| File | Change |
|---|---|
| `ccya/models.py:23-26` | Add `DEPARTED` to `NpcPresence` enum |
| `ccya/models.py:245-258` | Add `departed_reason`, `departed_summary`, `departed_turn` to `CompendiumNpcUpdate` |
| `ccya/engine/config.py` | Add `nearby_decay_ttl: int = 2`, `departed_archive_ttl: int = 3` |
| `ccya/state/delta_builder.py:222-228` | Change `present → known` to `present → nearby` on location change; stamp `nearby_since_turn` |
| `ccya/state/npcs.py:apply_npc_scene_management()` | Merge `departed_reason`, `departed_summary`, `departed_turn`; handle `nearby_since_turn` on LLM-set `nearby` |
| `ccya/state/npcs.py:strip_npcs_notes()` | Skip departed and archived NPCs |
| `ccya/engine/turn.py:1240+` | Add nearby-decay step + departed-archive step after `last_seen` stamp |
| `ccya/engine/npc_roster.py` | Pre-filter to skip `archived`; add `DEPARTED` sort order entry |
| `ccya/prompts/extract_scene_system.j2` | Teach LLM about `presence: "departed"`, `departed_reason`, `departed_summary`, `presence: "nearby"`, and re-promotion of engine-demoted NPCs |
| `ccya/prompts/sections/_npc_roster.j2` | Render `[DEPARTED]` with reason instead of bio |
| `ccya/prompts/storytell_system.j2` | Add departed NPC guidance |
| `ccya/prompts/generate_seed_system.j2` | Add `"departed"` and `"nearby"` to presence schema |
