# NPC Death and Purge Mechanism

## Purpose

Design authority for adding explicit death tracking to NPCs and a TTL-based purge from the compendium while preserving narrative reference in history.

## Problem Statement

NPC death is not tracked explicitly. When an NPC dies, the scene extractor sets `presence: "known"` — the same signal used when an NPC leaves, flees, or faints. The engine cannot distinguish a dead NPC from one who merely exited the scene. Dead NPCs accumulate in the compendium forever, polluting LLM prompt context, inflating the NPC roster seen in every pipeline stage, and driving up token costs per turn. No mechanism exists to remove them.

## Constraints

- Must preserve narrative continuity: the narrator must be able to reference dead NPCs (their past actions, death scene, unresolved threads with them) from chronicle context and prior_history.
- The scene extractor LLM controls the death signal — the engine does not infer death from game mechanics.
- Minimal blast radius: this is a data model + purge step, not a pipeline restructuring.
- Token efficiency: dead NPCs should exit prompt context as soon as practical.

## Non-goals

- No NPC revival mechanic. Once dead, always dead.
- No LLM inference of death from momentum/band/conditions. `is_dead` is set explicitly by the scene extractor.
- No tombstone record in the compendium. Purge = complete deletion from `compendium.npcs`.
- No migration of existing saves. NPCs that were previously killed via `presence: "known"` remain as-is until a future turn marks them dead.

## Current State — What Exists

### NPC data model

`CompendiumNpcUpdate` (in `ccya/models.py:245`) is the delta model the scene extractor emits. It has fields for identity (`id`, `name`, `title`, `bio`, `aliases`, `allegiance`), narrative drivers (`motivation`, `fear`, `leverage`), scene state (`presence`, `notes`), and engine bookkeeping (`first_seen_turn`). There is no `is_dead` field.

The state NPC entry (in `state.yaml` under `compendium.npcs`) mirrors these fields as a plain dict, plus `last_seen` dict stamped by `turn.py:1236` after delta application.

### NPC lifecycle

1. **Creation**: Scene extractor emits `compendium_npc_update` with new `id`, `name`, `bio`, `presence: "present"` → `apply_npc_scene_management()` in `ccya/state/npcs.py:97` creates entry with `first_seen_turn`.
2. **Update**: Same function merges fields individually (`name`, `title`, `bio`, `aliases`, `allegiance`, `motivation`, `fear`, `leverage`, `presence`, `notes`).
3. **Departure**: Scene extractor sets `presence: "known"` → notes cleared. NPC stays in compendium.
4. **Death**: Currently identical to departure. `extract_scene_system.j2:82` lists death alongside "left, fled, fainted, or been removed" as a `presence: "known"` signal. No distinction.

### Where NPC data is consumed

- **`build_npc_roster()`** (`ccya/engine/npc_roster.py`): iterates all `compendium.npcs` entries, filters/sorts by presence, truncates to `max_entries` (default 10). Used by every pipeline stage for prompt construction.
- **`_npc_roster.j2`**: renders NPC roster in narrate_user.j2, storytell_user.j2, ruling_user.j2, extract_scene_user.j2. Shows id, name, title, presence tag, bio, notes, motivation, fear, leverage, bond, last_seen.
- **`strip_npcs_notes()`** (`ccya/state/npcs.py:85`): clears `notes` from all NPCs at turn start.
- **`_dedup_compendium_update()`** (`ccya/engine/extraction.py:133`): pre-merge dedup by name/alias match.
- **`last_seen` stamp** (`turn.py:1229-1240`): post-delta stamp on NPCs that received an update this turn.
- **`touch_compendium_order()`**: LRU tracking for present NPCs, used by `build_npc_roster()` in LRU sort mode.

### Problems with Current State

1. **Death is invisible to the engine**. `presence: "known"` conflates death with departure. No way to route dead NPCs differently.
2. **No compendium cleanup**. Every NPC ever created lives in the compendium forever. A long campaign accumulates dozens of NPCs, all of which are iterated every turn by `build_npc_roster()` and included in limited prompt context.
3. **Prompt token waste**. Dead NPCs are irrelevant to current scene but still rendered in the Characters section of every prompt stage. They eat context budget that should go to active characters.
4. **No story callback distinction**. The narrator has no signal about which NPCs are dead (and therefore only referenceable from history) vs. which are alive but elsewhere. The `known` presence tag gives no durability semantics.

## Proposed Solution

### Core Changes

#### 1. Add `is_dead` and `death_turn` to `CompendiumNpcUpdate`

```python
class CompendiumNpcUpdate(BaseModel):
    id: str
    name: str | None = None
    # ... existing fields unchanged ...
    presence: str | None = None  # "present" | "nearby" | "known"
    notes: str | None = None
    first_seen_turn: int | None = None
    is_dead: bool | None = None        # NEW: scene extractor sets true on death
    death_turn: int | None = None       # NEW: engine sets on first is_dead=true
```

Default `None` means "no update" — the scene extractor only emits `is_dead: true` when an NPC dies. The engine sets `death_turn` on first detection (like `first_seen_turn`).

#### 2. Add `death_purge_ttl` to `EngineConfig`

```python
@dataclass
class EngineConfig:
    # ... existing fields ...
    death_purge_ttl: int = 3  # turns after death before NPC is purged from compendium
```

Configurable per-save via `config.yaml`. Default 3 turns gives narrative breathing room for death scenes and immediate aftermath references.

#### 3. Update `apply_npc_scene_management()` to handle `is_dead`

In `ccya/state/npcs.py:apply_npc_scene_management()`, after the existing field merge block (line ~168):

```python
if comp_upd.is_dead is True:
    entry["is_dead"] = True
    if current_turn_no is not None:
        entry["death_turn"] = entry.get("death_turn", current_turn_no)
```

`death_turn` is set only once (first detection), so repeated `is_dead: true` emissions don't advance the clock.

#### 4. Add purge step in `turn.py` post-delta

After the `last_seen` stamp section (after line 1240), add:

```python
# Purge dead NPCs past TTL
death_ttl = config.death_purge_ttl if config else 3
comp = state.get("compendium", {}).get("npcs", {})
dead_ids = [
    nid for nid, entry in comp.items()
    if isinstance(entry, dict)
    and entry.get("is_dead") is True
    and isinstance(entry.get("death_turn"), int)
    and turn_no - entry["death_turn"] >= death_ttl
]
for nid in dead_ids:
    del comp[nid]
if dead_ids:
    _log.info(
        "purged_dead_npcs ids=%s", sorted(dead_ids),
        extra={"turn": turn_no},
    )
```

This runs every turn and purges NPCs whose `death_turn` is ≥ `death_purge_ttl` turns behind current turn.

#### 5. Update `build_npc_roster()` to exclude dead NPCs by default

In `ccya/engine/npc_roster.py:build_npc_roster()`, add a filter step before presence grouping:

```python
# Skip dead NPCs
entries = [(nid, entry) for nid, entry in comp.items()
           if isinstance(entry, dict) and not entry.get("is_dead")]
```

This prevents dead NPCs from appearing in the standard Characters section of every prompt stage. Dead NPCs are still accessible from chronicle/history context.

For potential future use (e.g., a "dead characters" section in prompts), the function already supports a `presence_filter` parameter; a future `dead_filter` or `include_dead` param could be added when needed.

#### 6. Update prompts

**`extract_scene_system.j2`** — Teach scene extractor about `is_dead`:

In the NPC ENTER/EXIT RULE section, replace the current death-nondescript line:

```diff
- Emit `compendium_npc_update { presence: "known" }` for every named NPC who narration indicates has left, fled, died, fainted, or been removed from the scene.
+ Emit `compendium_npc_update { presence: "known" }` for every named NPC who narration indicates has left, fled, fainted, or been removed from the scene.
+ Emit `compendium_npc_update { presence: "known", is_dead: true }` for every named NPC who narration indicates has died — their story is over, the engine will remove them from the active roster after a few turns.
```

In the JSON schema example (line 13), add `is_dead: true` as an optional field.

In the field rules section, add:
```
`is_dead`: `true` when the NPC dies. Omit for all other state changes.
```

**`narrate_system.j2`** — No change needed. The existing instruction "NPCs die. In any scene with stakes..." already works. The narrator can reference dead NPCs from history context.

**`storytell_system.j2`** — Add brief note:
```
- Dead NPCs are removed from the active roster after a few turns. Reference them from narrative history only — do not create threads or actions involving dead characters.
```

**`_npc_roster.j2`** — No change. Dead NPCs are excluded by `build_npc_roster()` so they never appear here. If a future feature wants a dead NPC section, this template can be extended.

### Alternatives Considered and Rejected

1. **Infer death from `presence: "known"` + conditions**: Rejected. The engine has no reliable signal for death from conditions alone (NPCs don't have conditions in the same way PCs do). Explicit LLM signal is more reliable and simpler.

2. **Tombstone record in compendium**: Rejected. The user explicitly said purged from compendium. A tombstone adds complexity for no benefit — chronicle and prior_history already serve as the record.

3. **Purge immediately on death**: Rejected. The narrator needs to narrate the death scene and immediate aftermath. A 3-turn TTL allows death scenes, reactions, and thread closure before the NPC disappears from prompt context.

4. **Separate `dead_characters` section in prompts**: Rejected for now. Dead NPCs already exist in prior_history and chronicle context. A separate prompt section would add token cost without clear benefit. Can be added later as a configurable option.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Death signal is explicit | `is_dead: true` in `CompendiumNpcUpdate`, set by scene extractor LLM | Reliable, no inference errors, LLM controls narrative semantics |
| Death TTL is configurable | `death_purge_ttl: int = 3` in `EngineConfig` | Allows per-save tuning; 3 turns is a safe default for narrative closure |
| Purge = deletion from `compendium.npcs` | `del comp[nid]` in turn.py post-delta | Minimal surface area; no tombstone record needed |
| `build_npc_roster()` excludes dead by default | Filter before presence grouping | Dead NPCs don't belong in active Characters section |
| No backwards compatibility | Existing dead NPCs with `presence: "known"` remain as-is | No migration needed; scene extractor will mark them dead on next relevant turn (or they stay as known NPCs) |
| `death_turn` set once by engine | `entry.get("death_turn", current_turn_no)` | Prevents TTL clock reset on repeated `is_dead: true` emissions |
| Purge step runs every turn | After `last_seen` stamp in turn.py post-delta | Simple, no new orchestration; dead NPCs beyond TTL removed within 1 turn |
| No prompt section for dead NPCs | Dead NPCs excluded from roster, referenceable from history only | Token efficiency; history context already covers callback references |

## Failure Modes and Risks

1. **LLM forgets to set `is_dead: true`**. Mitigation: the scene extractor prompt teaches the field explicitly. The narrator's "NPCs die" instruction still works even without the flag — the engine just won't track or purge it. This is a soft failure: NPC remains as `presence: "known"` (current behavior), no data loss.
2. **NPC marked dead but survived in narration**. Mitigation: rare, but harmless. If the LLM contradicts itself, the scene extractor can later set `is_dead: false` or omit it. The engine does not enforce death as irreversible through the LLM interface.
3. **Death TTL too short**. Mitigation: configurable default of 3 turns. If players linger on death scenes, config can be raised. Default is conservative for token savings.
4. **`death_turn` advancement race**. Mitigation: `entry.get("death_turn", current_turn_no)` ensures the first emission sets the clock; subsequent emissions are no-ops.
5. **Purge removes NPC with active threads**. Mitigation: the thread sanitizer or storyteller should resolve threads involving dead NPCs naturally. If threads referencing dead NPCs remain, they become dangling references — the narrator cannot act on them. This is acceptable narrative friction. A future improvement could auto-resolve threads referencing dead NPCs.
6. **Empty compendium after purge**. Mitigation: handled — `build_npc_roster()` returns an empty list, which suppresses the Characters section in templates (`{% if npc_roster %}`). No crash.

## Open Questions

- `[OPEN: Should `build_npc_roster()` gain an `include_dead` parameter for potential future dead-NPC prompt sections, or add only when needed?]`

## What Is Removed

Nothing. No fields or functions are removed.

## What Is Unchanged

- `ccya/engine/narrate.py` — unchanged. Narrator receives dead NPCs in history context.
- `ccya/engine/extraction.py` — unchanged. Dedup logic does not interact with death flag.
- `ccya/state/delta.py` — unchanged. StateDelta carries `compendium_npc_update` with new field automatically.
- `ccya/state/inventory.py` — unchanged.
- `ccya/state/momentum.py` — unchanged.
- `ccya/state/chronicle.py` — unchanged.
- `ccya/engine/seed.py`, `ccya/engine/pack_gen.py` — unchanged.
- `ccya/models.py` — only `CompendiumNpcUpdate` gains fields; all other models unchanged.
- `ccya/prompts/extract_scene_user.j2`, `narrate_user.j2`, `storytell_user.j2`, `ruling_user.j2` — unchanged (they include `_npc_roster.j2` which doesn't need changes).
- `ccya/prompts/sections/_npc_roster.j2` — unchanged (dead NPCs filtered out by `build_npc_roster()`).
- `ccya/prompts/generate_seed_system.j2` — unchanged (seed doesn't create dead NPCs).
- `ccya/prompts/ruling_system.j2`, `narrate_system.j2` — unchanged.

## New Model Shapes

```python
# In ccya/models.py, class CompendiumNpcUpdate:

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
    presence: str | None = None  # "present" | "nearby" | "known"
    notes: str | None = None
    first_seen_turn: int | None = None
    is_dead: bool | None = None        # NEW: scene extractor sets true
    death_turn: int | None = None       # NEW: engine sets on first is_dead=true
```

```python
# In ccya/engine/config.py, class EngineConfig:

@dataclass
class EngineConfig:
    # ... existing fields ...
    death_purge_ttl: int = 3  # NEW: turns before dead NPC purged from compendium
```

## Context for Implementing LLMs

| File | What it contains | Why it matters |
|---|---|---|
| `ccya/models.py:245-258` | `CompendiumNpcUpdate` model | Add `is_dead` and `death_turn` fields |
| `ccya/engine/config.py:85-179` | `EngineConfig` dataclass | Add `death_purge_ttl` field |
| `ccya/state/npcs.py:97-171` | `apply_npc_scene_management()` | Add `is_dead`/`death_turn` merge logic |
| `ccya/engine/turn.py:1229-1240` | Post-delta NPC stamp section | Add purge step after `last_seen` stamp |
| `ccya/engine/npc_roster.py` | `build_npc_roster()` | Add dead NPC filter |
| `ccya/prompts/extract_scene_system.j2` | Scene extractor system prompt | Teach LLM about `is_dead: true` |
| `ccya/prompts/storytell_system.j2` | Storyteller system prompt | Add dead NPC guidance |
| `ccya/prompts/sections/_npc_roster.j2` | NPC roster template | Confirm no change needed |
