# Plan: Entity Deduplication (Inventory + NPCs)

## Problem

The extractor creates duplicate inventory items and NPCs because it generates new IDs from
whatever surface form appears in the narration. The same object gets multiple entries:

- `"worn dagger"` and `"dagger"` → two inventory rows for one item
- `"Scarred soldier"` and `"Kael"` → two NPC entries for one character

No ID scheme alone fixes this — the LLM generates descriptive identifiers from context, and
the narration uses different surface forms for the same entity at different points.

---

## Design

### 1. Canonical IDs with strict format rules

All inventory items and NPCs get a stable `snake_case` ID assigned at creation.

**ID format rules (injected into extractor system prompts):**

- NPCs: `firstname_lastname` only. No titles, roles, or descriptors.
  - ✅ `kael_marsh`, `torben_klask`
  - ❌ `scarred_soldier`, `doctor_voss`, `the_merchant`
  - If only one name is known: `kael` (single token, no decorators)
  - When a full name is revealed later: emit `npc_update` to set the canonical ID and add old ID as alias
- Inventory: `noun` or `adjective_noun`, lowercase, no articles.
  - ✅ `worn_dagger`, `brass_key`, `short_sword`
  - ❌ `the_dagger`, `a_key`, `soldiers_rifle`
- IDs are immutable once assigned. Name changes go in the `name` field and `aliases`, not the ID.

---

### 2. Extractor match instruction

Before emitting `inventory_add` or `npc_add`, the extractor is explicitly instructed to
check the existing state:

> **In `extract_state_system.j2` and `extract_progress_system.j2`:**
>
> Before adding any inventory item or NPC, check the existing list provided in context.
> If the entity is likely the same object or person referred to differently
> (e.g. `"dagger"` when `"worn_dagger"` already exists, or `"the soldier"` when `"kael"` is
> already in the compendium), use the existing ID and emit an update instead of an add.
> Only emit an add for a genuinely new entity not present in the current state.
>
> For NPCs: if a character is named or re-identified this turn (e.g. you learn the scarred
> soldier's name is Kael), emit `npc_update` on the existing ID — do not create a new entry.
> Add the old descriptor as an alias.

This puts semantic matching where the LLM excels: given both representations side by side,
it reliably recognizes `"dagger"` ≈ `"worn_dagger"`. It is bad at generating consistent IDs
from nothing; it is good at answering "is this the same thing?"

---

### 3. NPC alias registry

Add an `aliases` field to NPC compendium entries:

```yaml
npcs:
  kael:
    name: "Kael Marsh"
    aliases: ["scarred soldier", "the soldier", "kael"]
    ...
```

The engine maintains a flat alias map at runtime, rebuilt on load:

```python
def build_alias_map(npcs: dict) -> dict[str, str]:
    """Returns alias -> canonical_id mapping."""
    result = {}
    for npc_id, npc in npcs.items():
        result[npc_id] = npc_id  # canonical maps to itself
        for alias in (npc.get("aliases") or []):
            result[alias.lower()] = npc_id
    return result
```

Before applying any `npc_add` delta, the engine checks the alias map. If the incoming
name or ID matches a known alias, it routes to `npc_update` on the canonical ID instead.

Same pattern for inventory, lighter weight — items don't get renamed often, but when they
do (e.g. "rifle" upgraded to "scoped rifle"), the alias field handles it:

```yaml
inventory:
  worn_dagger:
    name: "Worn Dagger"
    aliases: ["dagger", "the dagger"]
```

---

### 4. Engine fuzzy match safety net (pure Python)

After alias map lookup, if a new `inventory_add` or `npc_add` still doesn't match any
canonical ID or alias, run a fuzzy match against existing names before writing:

```python
def _fuzzy_match_entity(name: str, existing: dict[str, dict]) -> str | None:
    """
    Returns canonical ID if `name` is a likely duplicate of an existing entity.
    Uses token overlap — no external dependencies.
    """
    name_tokens = set(name.lower().split())
    best_id, best_score = None, 0.0
    for eid, entity in existing.items():
        candidate_tokens = set(entity.get("name", "").lower().split())
        # also check aliases
        for alias in (entity.get("aliases") or []):
            candidate_tokens |= set(alias.lower().split())
        if not candidate_tokens:
            continue
        overlap = len(name_tokens & candidate_tokens)
        score = overlap / max(len(name_tokens), len(candidate_tokens))
        if score > best_score:
            best_score = score
            best_id = eid
    return best_id if best_score >= 0.6 else None
```

Threshold of 0.6 is conservative — requires substantial word overlap before merging.
False positive risk: `"short sword"` vs `"long sword"` scores 0.5 (one shared token out of
two each) → below threshold → correctly treated as distinct.
Log any fuzzy merge as a reconciliation warning so prompt problems are visible.

---

## Files to change

| File | Change |
|---|---|
| `ccya/state.py` | `build_alias_map()`, fuzzy match utility, alias check in `apply_delta()` |
| `ccya/prompts/extract_state_system.j2` | Match instruction + ID format rules |
| `ccya/prompts/extract_progress_system.j2` | Same match instruction |
| `ccya/models.py` | Add `aliases: list[str] = []` to NPC and inventory models |

---

## Relationship to other plans

- **`reconciliation-system.md`** — reconciliation catches add-of-existing-ID as a hard
  block. This plan handles the softer case where the extractor generates a *different*
  ID/name for the same entity. Both are needed.
- **Location-keyed NPC storage** (future, not in P1) — will replace the alias registry for
  NPCs once implemented. The alias field on NPC entries remains useful either way.

---

## Migration

Existing saves with duplicate NPC/inventory entries are not auto-merged — dedup only applies
to new writes. Duplicates in existing state can be manually cleaned or left as-is; they
won't multiply further once this is in place.

Add `aliases: []` as default in `_default_state()` for both inventory items and NPCs.
