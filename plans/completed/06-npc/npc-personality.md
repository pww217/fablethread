# NPC Personality System

## Status
`completed`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Data layer | Define `NpcPersonality` dataclass, archetype registry, and seed assignment logic in `ccya/personality.py` |
| 02 | Model + state integration | Add `personality` field to `CompendiumNpcUpdate`, wire into `apply_npc_scene_management`, protect it from overwrite |
| 03 | Seed generation + static seeds | Assign personality on all seed paths (dynamic LLM and static YAML); update schema comment in `generate_seed_system.j2` |
| 04 | Narrator prompt | Look up archetype data at render time via `build_npc_roster`; expose in `_npc_roster.j2` template |

## Objective
NPCs currently have identity fields (`name`, `title`, `bio`, `motivation`, `fear`, `leverage`) but no behavioural style descriptor that shapes *how* they express those traits. A personality system adds a discrete, immutable `personality` field to each compendium NPC entry. Rather than letting the LLM invent freeform personality text (which regresses to blandness) or randomly sampling from a flat trait list (which breaks tonal coherence), the approach defines a small registry of named archetypes in Python. Each archetype is a coherent bundle of traits, a speech style hint, and a set of narrative roles it is valid for. At NPC creation time the engine — not the narrator LLM — picks the archetype that is most coherent with the NPC's existing `motivation` and `fear` fields, using a deterministic scoring function. The narrator then receives the archetype's trait list and speech hint as part of the NPC context block, giving it a concrete signal to act against.

## Non-goals
- No personality for PCs.
- No personality mutation over the course of a run (field is immutable once set).
- No archetype visible to the player in the UI; this is narrator fuel only.
- No LLM call added to the personality assignment path; everything is deterministic Python.
- No changes to the compactor, chronicle, or rules engine.
- No per-world-pack archetype overrides in this plan.

---

## Implementation — Phase 01: Data layer

### Files to pull for context
- `ccya/models.py` — existing Pydantic models (no changes this phase)
- `ccya/state/npcs.py` — understand compendium entry structure
- `docs/repomap.md` — check if a personality module is already mapped

### Detailed steps

#### Step 1.1 — Create `ccya/personality.py`

**File:** `ccya/personality.py`

**What:** New module. Define `NpcPersonality` (a frozen dataclass), the archetype registry `ARCHETYPES`, and `assign_personality` (the scoring function). Also define a validation helper that checks whether an arbitrary string is a valid archetype id, logging a warning if not and returning the fallback default.

**Why:** All personality logic must live at a module boundary with no side-effects. Keeping it in its own file means the narrator, seed builder, and test suite can each import it without importing engine internals. The validation helper covers the edge case where a seed LLM emits an invalid archetype id (e.g., a typo or hallucinated name).

```python
"""NPC personality archetype registry and assignment."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class NpcPersonality:
    id: str
    label: str
    traits: tuple[str, ...]  # 2-4 short descriptors surfaced in narrator context
    speech_hint: str          # one-line style note; e.g. "clipped, transactional"
    motivation_keywords: tuple[str, ...] = field(default_factory=tuple)
    fear_keywords: tuple[str, ...] = field(default_factory=tuple)


ARCHETYPES: dict[str, NpcPersonality] = {
    a.id: a for a in [
        NpcPersonality(
            id="cold_pragmatist",
            label="Cold Pragmatist",
            traits=("calculating", "direct", "emotionally distant"),
            speech_hint="terse and transactional; no pleasantries",
            motivation_keywords=("power", "control", "order", "efficiency", "profit"),
            fear_keywords=("chaos", "weakness", "exposure", "loss of control"),
        ),
        NpcPersonality(
            id="desperate_idealist",
            label="Desperate Idealist",
            traits=("principled", "anxious", "self-sacrificing"),
            speech_hint="earnest and sometimes rambling; conviction bleeds through hesitation",
            motivation_keywords=("justice", "protect", "truth", "people", "belief", "cause"),
            fear_keywords=("betrayal", "failure", "complicity", "compromise"),
        ),
        NpcPersonality(
            id="wary_opportunist",
            label="Wary Opportunist",
            traits=("adaptive", "self-interested", "quick to read angles"),
            speech_hint="friendly surface, careful eyes; always gauging what this costs them",
            motivation_keywords=("survival", "gain", "advantage", "escape", "freedom"),
            fear_keywords=("trap", "debt", "loyalty", "obligation", "cornered"),
        ),
        NpcPersonality(
            id="resigned_functionary",
            label="Resigned Functionary",
            traits=("bureaucratic", "weary", "procedurally polite"),
            speech_hint="flat and slightly apologetic; follows rules because fighting them costs too much",
            motivation_keywords=("duty", "routine", "order", "stability", "family"),
            fear_keywords=("punishment", "scrutiny", "responsibility", "change"),
        ),
        NpcPersonality(
            id="volatile_loyalist",
            label="Volatile Loyalist",
            traits=("fiercely loyal", "short-fused", "protective"),
            speech_hint="blunt and emotional; shifts fast between warmth and aggression depending on perceived threat to what they value",
            motivation_keywords=("loyalty", "family", "protect", "honour", "revenge"),
            fear_keywords=("abandonment", "betrayal", "helplessness", "loss"),
        ),
        NpcPersonality(
            id="charming_manipulator",
            label="Charming Manipulator",
            traits=("persuasive", "socially fluid", "rarely direct"),
            speech_hint="warm and engaging; steers conversations without appearing to; says little of substance",
            motivation_keywords=("influence", "control", "reputation", "leverage", "network"),
            fear_keywords=("exposure", "loss of influence", "transparency", "irrelevance"),
        ),
        NpcPersonality(
            id="blunt_survivor",
            label="Blunt Survivor",
            traits=("unsentimental", "pragmatic", "darkly humorous"),
            speech_hint="dry, economical; has seen enough to drop illusions but not quite enough to stop trying",
            motivation_keywords=("survival", "endure", "protect", "independence"),
            fear_keywords=("weakness", "dependence", "betrayal", "hope"),
        ),
        NpcPersonality(
            id="true_believer",
            label="True Believer",
            traits=("zealous", "certain", "morally inflexible"),
            speech_hint="declarative and dense with conviction; treats doubt as an enemy",
            motivation_keywords=("faith", "mission", "purpose", "god", "ideology", "order"),
            fear_keywords=("doubt", "apostasy", "corruption", "failure of purpose"),
        ),
        NpcPersonality(
            id="detached_observer",
            label="Detached Observer",
            traits=("analytical", "quiet", "observant"),
            speech_hint="measured and questioning; prefers to draw others out rather than reveal themselves",
            motivation_keywords=("understand", "knowledge", "truth", "information", "clarity", "insight"),
            fear_keywords=("manipulation", "being used", "blindness", "misinformation", "control"),
        ),
        NpcPersonality(
            id="conflict_avoidant",
            label="Conflict-Avoidant",
            traits=("yielding", "nervous", "self-effacing"),
            speech_hint="hedging and apologetic; trails off or backtracks when pressed; speaks in qualifiers",
            motivation_keywords=("peace", "safety", "quiet", "normalcy", "blend in", "get by"),
            fear_keywords=("confrontation", "attention", "violence", "escalation", "being targeted"),
        ),
        NpcPersonality(
            id="ambitious_climber",
            label="Ambitious Climber",
            traits=("patient", "strategic", "calculating"),
            speech_hint="diplomatic and forward-looking; frames everything as an investment or opportunity",
            motivation_keywords=("advancement", "position", "status", "leverage", "future", "rise"),
            fear_keywords=("stagnation", "being passed over", "irrelevance", "dead end", "humiliation"),
        ),
        NpcPersonality(
            id="broken_defeated",
            label="Broken/Defeated",
            traits=("worn", "habit-driven", "darkly resigned"),
            speech_hint="fragmented and sparse; speaks in dark humor or silence; moves on autopilot",
            motivation_keywords=("routine", "habit", "survive", "endure", "forget", "numb"),
            fear_keywords=("meaning", "responsibility", "hope", "change", "being needed"),
        ),
    ]
}

_DEFAULT_ID = "wary_opportunist"


def _score_archetype(
    archetype: NpcPersonality,
    motivation: str,
    fear: str,
) -> int:
    """Return a keyword match score for an archetype against motivation+fear text."""
    text = (motivation + " " + fear).lower()
    score = 0
    for kw in archetype.motivation_keywords:
        if kw in text:
            score += 2
    for kw in archetype.fear_keywords:
        if kw in text:
            score += 1
    return score


def assign_personality(
    motivation: str | None,
    fear: str | None,
    npc_id: str = "",
) -> NpcPersonality:
    """Return the most contextually coherent personality archetype for an NPC.

    Scores each archetype against the NPC's motivation and fear text using
    keyword matching. Ties are broken by archetype registry insertion order.
    Falls back to ``wary_opportunist`` if both fields are empty or all scores are zero.

    Args:
        motivation: NPC motivation string (may be None).
        fear: NPC fear string (may be None).
        npc_id: Used only for structured logging.

    Returns:
        The best-scoring NpcPersonality instance.
    """
    if not motivation and not fear:
        _log.debug(
            "assign_personality npc=%s no_mf_fields fallback=%s",
            npc_id, _DEFAULT_ID,
        )
        return ARCHETYPES[_DEFAULT_ID]

    scored = [
        (_score_archetype(arch, motivation or "", fear or ""), arch)
        for arch in ARCHETYPES.values()
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_arch = scored[0]
    _log.debug(
        "assign_personality npc=%s best=%s score=%d",
        npc_id, best_arch.id, best_score,
    )
    return best_arch


def validate_and_resolve(personality_id: str | None) -> NpcPersonality | None:
    """Validate a personality archetype id against the registry.

    Returns the resolved NpcPersonality if valid and non-None, otherwise logs
    a warning (for invalid ids) or returns None (for missing). Callers should
    fall back to ARCHETYPES[_DEFAULT_ID] when they receive None for an invalid id.

    Args:
        personality_id: An archetype id string from state or LLM output.

    Returns:
        NpcPersonality if valid, None otherwise.
    """
    if not personality_id:
        return None
    arch = ARCHETYPES.get(personality_id)
    if arch is None:
        _log.warning(
            "personality unknown id=%s for npc; falling back to %s",
            personality_id, _DEFAULT_ID,
        )
        return None
    return arch
```

**Validation:** Run `python -c "from ccya.personality import assign_personality, ARCHETYPES, validate_and_resolve; p = assign_personality('wants to control the city', 'fears exposure'); assert p.id == 'cold_pragmatist'; v = validate_and_resolve('nonexistent'); assert v is None; print('ok')"`

### REPOMAP and architecture updates
- Add `ccya/personality.py` entry to `docs/repomap.md`. Document `assign_personality(motivation, fear, npc_id) -> NpcPersonality`, `validate_and_resolve(personality_id) -> NpcPersonality | None`, and the `ARCHETYPES` registry.

### Risks
1. Keyword scoring is coarse — an NPC whose motivation and fear use unusual phrasing may land on the wrong archetype. Mitigation: the narrator prompt uses personality as *hint*, not hard rule; mismatches degrade gracefully.
2. Archetype count (12) may feel too small for certain packs. Mitigation: registry is a plain dict; adding archetypes in future needs no structural change.

---

## Implementation — Phase 02: Model + state integration

### Files to pull for context
- `ccya/models.py` — `CompendiumNpcUpdate`, `SceneExtractResult`
- `ccya/state/npcs.py` — `apply_npc_scene_management`
- `ccya/personality.py` — from Phase 01

### Detailed steps

#### Step 2.1 — Add `personality` to `CompendiumNpcUpdate`

**File:** `ccya/models.py`

**What:** Add one optional field to `CompendiumNpcUpdate`. Place it after the existing fields (after `first_seen_turn`).

**Why:** The LLM scene extractor must be able to set personality on NPC creation (it will only ever do so when the seed builder sets it — the field is not in the narrator prompt as writable). Keeping it on the model means the JSON wire format is consistent with all other compendium fields.

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
    presence: str | None = None  # "present" | "nearby" | "known" — scene extractor sets this
    notes: str | None = None      # scene-specific attitude, cleared on departure
    first_seen_turn: int | None = None  # set by engine on initial entry creation
    personality: str | None = None  # archetype id; immutable once set
```

**Validation:** Confirm the model change is backward compatible (optional field with `None` default).

#### Step 2.2 — Protect and persist `personality` in `apply_npc_scene_management`

**File:** `ccya/state/npcs.py`

**What:** In the `apply_npc_scene_management` loop, after the `leverage` assignment block (lines 160-161), add a personality write block that is **only applied when the entry has no existing personality value**. Store only the archetype id — denormalized fields are resolved at render time by `build_npc_roster()`.

**Why:** Personality is immutable once assigned. The narrator LLM must never be able to overwrite it by emitting a `compendium_npc_update` with a different `personality` value mid-game. Only storing the archetype id avoids duplication — template rendering resolves label/traits/speech_hint from ARCHETYPES at render time via build_npc_roster (Phase 04).

```python
# Inside the for-loop in apply_npc_scene_management, after:
#   if comp_upd.leverage is not None:
#       entry["leverage"] = comp_upd.leverage

if comp_upd.personality is not None and not entry.get("personality"):
    entry["personality"] = comp_upd.personality
    _log.debug(
        "apply_npc_scene_management npc=%s personality=%s",
        resolved_id, comp_upd.personality,
    )
```

**Validation:** Assert that a second update with a different personality value does not overwrite the first.

### REPOMAP and architecture updates
- Update `CompendiumNpcUpdate` signature in repomap to note `personality: str | None` field.
- Note that `personality` is write-once: set on creation, ignored on subsequent updates.
- Note that denormalized personality fields (label/traits/speech_hint) are resolved at render time by build_npc_roster from ARCHETYPES — they do not persist in state.

### Risks
1. Old saved game states have no `personality` key. Mitigation: all reads of `personality` from the compendium dict use `.get("personality")` which returns `None`; build_npc_roster skips archetype lookup when personality is None, so old saves render without a personality block and new saves get it automatically. No migration needed.

---

## Implementation — Phase 03: Seed generation + static seeds

**Depends on:** Phase 01, Phase 02

### Files to pull for context
- `ccya/personality.py` — `assign_personality`, `validate_and_resolve`, `ARCHETYPES`
- `ccya/pack.py` — `CompendiumEntry`, `SeedState`, `SeedEnvelope` (Pydantic models)
- `ccya/engine/seed.py` — dynamic seed generation (`generate_seed()`)
- `ccya/state/io.py` — static seed loading and save initialization (`init_save_dir()`)
- `ccya/prompts/generate_seed_system.j2` — schema comment update

### Detailed steps

#### Step 3.1 — Assign personality in dynamic seed builder (engine/seed.py)

**File:** `ccya/engine/seed.py`

**What:** After the seed LLM response is parsed and validated (`envelope = SeedEnvelope(**j)` at line ~296), iterate over all NPC entries in `envelope.seed_state.compendium.npcs` (which are Pydantic CompendiumEntry objects) and call `assign_personality` for any that lack a `personality` attribute. Write only the archetype id back onto each entry. Validate against ARCHETYPES; if an invalid id is present, log warning and fall back to default — do not overwrite with a new assignment (preserve whatever the LLM produced).

**Why:** Phase 01 established the scoring function and validation helper. This phase calls both at the moment NPC state is created from dynamic seeds, so every NPC born from a seed has a personality before the first narrator turn. Only storing the archetype id avoids duplication — denormalized fields are resolved by build_npc_roster (Phase 04).

```python
# In generate_seed(), after line ~298 (_validate_seed_envelope(envelope)),
# and before any other post-processing:

from ccya.personality import assign_personality, validate_and_resolve, ARCHETYPES, _DEFAULT_ID

for npc_id, npc_entry in envelope.seed_state.compendium.npcs.items():
    if not hasattr(npc_entry, "personality") or not getattr(npc_entry, "personality"):
        # No personality set — assign one from motivation/fear
        arch = assign_personality(
            motivation=getattr(npc_entry, "motivation", None),
            fear=getattr(npc_entry, "fear", None),
            npc_id=npc_id,
        )
        object.__setattr__(npc_entry, "personality", arch.id)
    else:
        # LLM already set a personality — validate it
        resolved = validate_and_resolve(getattr(npc_entry, "personality"))
        if resolved is None:
            _log.warning(
                "seed npc=%s has unknown personality '%s'; keeping as-is (LLM may have produced freeform text)",
                npc_id, getattr(npc_entry, "personality"),
            )

_log.info("seed.assign_personality complete pack=%s", pack.manifest.id)
```

**Note on Pydantic objects:** `CompendiumEntry` has `extra: "allow"` (`pack.py:38`). We use `object.__setattr__()` to set the personality attribute directly since it's not a declared field. It will be included when `.model_dump(mode="json")` is called later in `ccya/server/routes.py` (lines 435/455).

**Validation:** Run the seed builder and assert that every NPC in the returned envelope has a non-empty `personality` attribute set to a valid archetype id.

#### Step 3.2 — Assign personality for static seeds (state/io.py)

**File:** `ccya/state/io.py`

**What:** Add a helper function `_assign_seed_personalities(state: dict[str, Any]) -> None` that iterates over all NPCs in the state's compendium and assigns personalities where missing. Call this from both `init_save_dir()` (after loading seed data) and any other path that initializes game state from seeds.

**Why:** Static seeds loaded via YAML (`__main__.py --new-game`) or eval harness go directly into `init_save_dir()` without passing through the dynamic seed builder's post-parse hook. This ensures all NPCs — whether born from LLM-generated seeds or hand-authored static packs — get personalities at game start time.

```python
# Add to ccya/state/io.py (near top, after imports):

from typing import Any


def _assign_seed_personalities(state: dict[str, Any]) -> None:
    """Assign personality archetype ids to any NPCs missing one in the seed state."""
    from ccya.personality import assign_personality
    
    npcs = (state.get("compendium") or {}).get("npcs", {})
    for npc_id, entry in npcs.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("personality"):
            continue  # already set; skip
        arch = assign_personality(
            motivation=entry.get("motivation"),
            fear=entry.get("fear"),
            npc_id=npc_id,
        )
        entry["personality"] = arch.id


# Modify init_save_dir() to call this after seed data is loaded:

def init_save_dir(save_dir: Path, seed: dict[str, Any]) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Assign personalities to any NPCs missing one (static seeds only; dynamic seeds already have them)
    _assign_seed_personalities(seed)
    
    save_state(save_dir, seed)
    (save_dir / "chronicle.md").write_text("")
    (save_dir / "events.jsonl").write_text("")
    # Remove stale snapshot from a previous game
    (save_dir / "state_snapshot.yaml").unlink(missing_ok=True)
```

**Validation:** Load a static seed pack with `--new-game` and verify all NPCs in the resulting state.yaml have a personality field. Check eval harness runs similarly produce seeded personalities for static seeds.

#### Step 3.3 — Update `generate_seed_system.j2` schema comment

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** In the TypeScript-style output schema comment (line 36), add a note that `personality` is assigned by the engine post-parse and should not be set by the LLM. Do **not** instruct the LLM to populate it — keep it as documentation only for future prompt authors who reference this template.

Update line 36 from:
```ts
compendium: {npcs: {snake_case: {name: string, title: string, bio: string, allegiance?: string, bond?: string, motivation?: string, fear?: string, leverage?: string}}},
```
to:
```ts
compendium: {npcs: {snake_case: {name: string, title: string, bio: string, allegiance?: string, bond?: string, motivation?: string, fear?: string, leverage?: string /* personality assigned by engine post-parse */}}},
```

**Validation:** Grep for `personality` in the template to confirm no instruction asks the LLM to populate the field.

### REPOMAP and architecture updates
- Document the personality assignment step in both dynamic seeds (engine/seed.py, post-parse) and static seeds (state/io.py, init_save_dir).
- Note that `_assign_seed_personalities` runs on all seed paths — it is idempotent (skips NPCs with existing personality).

### Risks
1. If the seed LLM emits a `personality` field despite the schema comment, validation logs a warning but preserves whatever the LLM produced rather than overwriting — acceptable behaviour since we don't want to silently discard LLM output even if it's unusual.
2. Static seeds loaded via YAML go through `_assign_seed_personalities` in init_save_dir which imports `ccya.personality`. This is a new import dependency on state/io.py but personality has no side-effects so there are no circular import concerns (personality only uses stdlib + logging).

---

## Implementation — Phase 04: Narrator prompt

**Depends on:** Phase 01, Phase 02, Phase 03

### Files to pull for context
- `ccya/engine/npc_roster.py` — build_npc_roster() (merges compendium into npc_roster list)
- `ccya/prompts/sections/_npc_roster.j2` — NPC rendering template
- `ccya/personality.py` — ARCHETYPES registry

### Detailed steps

#### Step 4.0 — Update `build_npc_roster()` to resolve personality at render time

**File:** `ccya/engine/npc_roster.py`

**What:** Add an optional `personality_registry: dict[str, Any] | None = None` parameter (defaulting to None for backward compat). When provided and a compendium entry has a `personality` key that resolves in the registry, add three resolved fields (`personality_label`, `personality_traits`, `personality_speech_hint`) to each NPC dict in the output roster.

**Why:** This is how personality data reaches the template without denormalization or duplication. The archetype id persists in state; label/traits/speech_hint are looked up from ARCHETYPES at render time and added only to the npc_roster list passed to Jinja templates. Old saves with no `personality` key simply skip the lookup — no error, no personality block rendered.

```python
# Update build_npc_roster() signature:

def build_npc_roster(
    comp: dict[str, Any],
    *,
    presence_filter: str | None = None,
    max_entries: int = 10,
    sort_by_lru: bool = False,
    lru_order: list[str] | None = None,
    personality_registry: dict[str, Any] | None = None,  # NEW
) -> list[dict[str, Any]]:

# In the seen[nid] = {...} block (line 40), add after last_seen:
            "last_seen": entry.get("last_seen") or None,
        }

        if personality_registry and isinstance(entry, dict):
            arch_id = entry.get("personality")
            if arch_id and arch_id in personality_registry:
                arch = personality_registry[arch_id]
                seen[nid]["personality_label"] = getattr(arch, "label", arch_id)
                seen[nid]["personality_traits"] = ", ".join(getattr(arch, "traits", ())) if hasattr(arch, "traits") else ""
                seen[nid]["personality_speech_hint"] = getattr(arch, "speech_hint", "")

# In engine/narrate.py _narrate_messages(), pass ARCHETYPES when building npc_roster:
    # At lines 41-43 where npc_roster is built if None:
    from ccya.personality import ARCHETYPES

    if npc_roster is None:
        comp = (state.get("compendium") or {}).get("npcs") or {}
        npc_roster = build_npc_roster(comp, personality_registry=ARCHETYPES)

# In eval harness and any other callers of build_npc_roster that pass a custom roster, they can omit the parameter for backward compat.
```

**Validation:** Run narrator prompt rendering with a seed that has NPCs and confirm the personality block appears in rendered output for present NPCs. Confirm old saves (no personality key) render without error or crash.

#### Step 4.1 — Add personality rendering to `_npc_roster.j2` template

**File:** `ccya/prompts/sections/_npc_roster.j2`

**What:** In the existing NPC rendering loop, add a conditional block that emits the personality label, traits, and speech hint when resolved fields are present in the npc dict. Insert after the `bond` line (line ~12) and before the blank line separator.

```jinja
{# sections/_npc_roster.j2 #}
{# npc_roster: list[dict], ordered PRESENT → NEARBY → KNOWN #}
{% if npc_roster -%}
## Characters

{% for n in npc_roster -%}
- `{{ n.id }}` | {% if n.name %}**{{ n.name }}**{% else %}[Unnamed]{% endif %}{% if n.title %} ({{ n.title }}){% endif %} [{{ n.presence | upper }}]{% if n.bio %} — {{ n.bio }}{% endif %}
{%- if n.notes %} | {{ n.notes }}{% endif %}
{%- if n.motivation %} | wants: {{ n.motivation }}{% endif %}
{%- if n.fear %} | fears: {{ n.fear }}{% endif %}
{%- if n.leverage %} | leverage: {{ n.leverage }}{% endif %}
{%- if n.bond %} | bond: {{ n.bond }}{% endif %}
{# Personality block — resolved from archetype id at render time #}
{%- if n.personality_traits -%}
| personality: **{{ n.personality_label }}** ({{ n.personality_traits }}). Speech: {{ n.personality_speech_hint }}.
{%- endif %}
{%- set _ls = n.last_seen %}{% if _ls is mapping and _ls.location_name %} | last seen: {{ _ls.location_name }}{% elif _ls and not (_ls is mapping) %} | last seen: {{ _ls }}{% endif %}

{% endfor -%}
{% endif %}
```

**Why:** The personality data is only useful if the narrator sees it. The speech hint is the highest-signal element — it directly shapes dialogue. Traits give the narrator vocabulary for NPC actions and reactions. Since build_npc_roster now resolves archetype fields at render time (Step 4.0), these three keys (`personality_label`, `personality_traits`, `personality_speech_hint`) will be present on npc dicts that have a valid personality id, and absent on old saves or NPCs without personalities — making the `{% if n.personality_traits %}` guard sufficient for backward compat.

**Validation:**
1. Run the narrator prompt rendering in test mode with a seed that has NPCs, and confirm the personality block appears for present NPCs.
2. Confirm that NPCs with no `personality` key (old saves) render without error or crash — they simply won't have any of the three resolved fields so the `{% if %}` guard prevents rendering.

### REPOMAP and architecture updates
- Update `docs/repomap.md` narrator prompt section to note: build_npc_roster now accepts optional `personality_registry` parameter; when provided, resolves archetype data into npc dict keys (`personality_label`, `personality_traits`, `personality_speech_hint`) for template rendering.
- Note that `_npc_roster.j2` renders a personality block using those resolved fields.

### Risks
1. If the NPC loop only runs for `presence == "present"` NPCs, personality will not render for `nearby` or `known` NPCs. This matches existing behaviour (the template already only shows present/nearby/known based on presence_filter). Do not expand scope beyond what build_npc_roster already does.
2. No duplication: archetype data is resolved fresh from ARCHETYPES at each roster-build call, so if archetypes are ever updated in code, new games immediately get the updated values while old saves simply won't have a personality key and render without it (graceful degradation).

---

## Ambiguities requiring resolution before execution

1. **Seed builder location.** Resolved: `ccya/engine/seed.py`, function `generate_seed()`. The post-parse hook goes after line ~298 (`_validate_seed_envelope(envelope)`) and before the arc/world_state processing that starts at line 316.

2. **Narrator template NPC loop structure.** Resolved: `_npc_roster.j2` iterates over `npc_roster` list (not directly over compendium). The anchor point for personality insertion is after the `bond` conditional on line ~12 and before the last_seen block. build_npc_roster() in engine/npc_roster.py builds this list from compendium entries — it must be updated to pass archetype data into each npc dict (Step 4.0).

3. **Static seeds path.** Resolved: `_assign_seed_personalities()` called inside `init_save_dir()` in state/io.py covers both CLI --new-game and eval harness paths for static YAML seeds. Dynamic seeds get personality assignment in engine/seed.py after parsing. Both paths are idempotent (skip NPCs that already have a personality).

---

## Summary of changes from initial review
- **Denormalization removed.** Only `personality` (archetype id) persists in state. Label, traits, and speech_hint are resolved at render time by build_npc_roster() looking up ARCHETYPES — no duplication, no staleness risk on old saves.
- **Static seeds covered.** `_assign_seed_personalities()` added to state/io.py init_save_dir() so static YAML seeds get personalities too (not just dynamic LLM-generated ones).
- **Validation + warning logging.** `validate_and_resolve()` in personality.py checks archetype ids against the registry and logs a WARNING for unknown ids. Seed builder preserves whatever invalid id the LLM produced rather than silently overwriting it.
