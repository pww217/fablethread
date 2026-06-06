# NPC Personality System

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Data layer | Define `NpcPersonality` dataclass, archetype registry, and seed assignment logic in `ccya/personality.py` |
| 02 | Model + state integration | Add `personality` field to `CompendiumNpcUpdate`, wire into `apply_npc_scene_management`, protect it from overwrite |
| 03 | Seed generation | Assign personality in `build_seed` before the LLM call; inject into `generate_seed_system.j2` |
| 04 | Narrator prompt | Expose personality in `narrate_user.j2` NPC context block |

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
- `docs/REPOMAP/` — check if a personality module is already mapped

### Detailed steps

#### Step 1.1 — Create `ccya/personality.py`

**File:** `ccya/personality.py`

**What:** New module. Define `NpcPersonality` (a frozen dataclass), the archetype registry `ARCHETYPES`, and `assign_personality` (the scoring function).

**Why:** All personality logic must live at a module boundary with no side-effects. Keeping it in its own file means the narrator, seed builder, and test suite can each import it without importing engine internals.

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
    # Keywords that score positively when found in motivation or fear text.
    # Used by assign_personality to rank archetypes without an LLM call.
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
    ]
}


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
    Falls back to ``wary_opportunist`` if both fields are empty.

    Args:
        motivation: NPC motivation string (may be None).
        fear: NPC fear string (may be None).
        npc_id: Used only for structured logging.

    Returns:
        The best-scoring NpcPersonality instance.
    """
    if not motivation and not fear:
        _log.debug(
            "assign_personality npc=%s no_mf_fields fallback=wary_opportunist", npc_id
        )
        return ARCHETYPES["wary_opportunist"]

    scored = [
        (_score_archetype(arch, motivation or "", fear or ""), arch)
        for arch in ARCHETYPES.values()
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_arch = scored[0]
    _log.debug(
        "assign_personality npc=%s best=%s score=%d",
        npc_id,
        best_arch.id,
        best_score,
    )
    return best_arch
```

**Validation:** Run `python -c "from ccya.personality import assign_personality, ARCHETYPES; p = assign_personality('wants to control the city', 'fears exposure', 'test_npc'); assert p.id == 'cold_pragmatist', p.id; print('ok')"`

### Tests to write or update

**File:** `tests/test_personality.py` (new)

```python
import pytest
from ccya.personality import assign_personality, ARCHETYPES, NpcPersonality


def test_all_archetypes_present():
    assert len(ARCHETYPES) == 8


def test_assign_cold_pragmatist():
    p = assign_personality("wants to control the trade routes", "fears losing power", "villain")
    assert p.id == "cold_pragmatist"


def test_assign_desperate_idealist():
    p = assign_personality("wants justice for the people", "fears betraying their cause", "hero")
    assert p.id == "desperate_idealist"


def test_fallback_on_empty_fields():
    p = assign_personality(None, None, "unknown")
    assert p.id == "wary_opportunist"


def test_personality_is_frozen():
    arch = ARCHETYPES["cold_pragmatist"]
    with pytest.raises((AttributeError, TypeError)):
        arch.id = "new_id"  # type: ignore[misc]


def test_all_archetypes_have_required_fields():
    for arch in ARCHETYPES.values():
        assert arch.id
        assert arch.label
        assert len(arch.traits) >= 2
        assert arch.speech_hint
```

### REPOMAP and architecture updates
- Add `ccya/personality.py` entry to `docs/REPOMAP/` in whichever file covers NPC state (likely `npcs.md`). Document `assign_personality(motivation, fear, npc_id) -> NpcPersonality` and the `ARCHETYPES` registry.

### Risks
1. Keyword scoring is coarse — an NPC whose motivation and fear use unusual phrasing may land on the wrong archetype. Mitigation: the narrator prompt uses personality as *hint*, not hard rule; mismatches degrade gracefully.
2. Archetype count (8) may feel too small for certain packs. Mitigation: registry is a plain dict; adding archetypes in future needs no structural change.

---

## Implementation — Phase 02: Model + state integration

### Files to pull for context
- `ccya/models.py` — `CompendiumNpcUpdate`, `SceneExtractResult`
- `ccya/state/npcs.py` — `apply_npc_scene_management`
- `ccya/personality.py` — from Phase 01

### Detailed steps

#### Step 2.1 — Add `personality` to `CompendiumNpcUpdate`

**File:** `ccya/models.py`

**What:** Add one optional field to `CompendiumNpcUpdate`.

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
    presence: str | None = None
    notes: str | None = None
    first_seen_turn: int | None = None
    personality: str | None = None  # archetype id; immutable once set
```

**Validation:** `python -m pytest tests/test_models.py -x -q` (or equivalent); confirm no existing tests break.

#### Step 2.2 — Protect and persist `personality` in `apply_npc_scene_management`

**File:** `ccya/state/npcs.py`

**What:** In the `apply_npc_scene_management` loop, after the `leverage` assignment block, add a personality write block that is **only applied when the entry has no existing personality value**.

**Why:** Personality is immutable once assigned. The narrator LLM must never be able to overwrite it by emitting a `compendium_npc_update` with a different `personality` value mid-game.

```python
# Inside the for-loop in apply_npc_scene_management, after:
#   if comp_upd.leverage is not None:
#       entry["leverage"] = comp_upd.leverage

if comp_upd.personality is not None and not entry.get("personality"):
    entry["personality"] = comp_upd.personality
    _log.debug(
        "apply_npc_scene_management npc=%s personality=%s",
        resolved_id,
        comp_upd.personality,
    )
```

**Validation:** Write a unit test (see below) that asserts a second update with a different personality value does not overwrite the first.

### Tests to write or update

**File:** `tests/test_npcs.py` (extend existing or create)

```python
from ccya.models import CompendiumNpcUpdate, SceneExtractResult
from ccya.state.npcs import apply_npc_scene_management


def _make_state() -> dict:
    return {"compendium": {"npcs": {}}, "location": {"id": "town", "name": "Town"}}


def test_personality_written_on_first_update():
    state = _make_state()
    result = SceneExtractResult(
        compendium_npc_update=[
            CompendiumNpcUpdate(
                id="guard",
                name="Guard",
                title="Town Guard",
                personality="cold_pragmatist",
                presence="present",
            )
        ]
    )
    apply_npc_scene_management(state, result, current_turn_no=1)
    assert state["compendium"]["npcs"]["guard"]["personality"] == "cold_pragmatist"


def test_personality_immutable_once_set():
    state = _make_state()
    first = SceneExtractResult(
        compendium_npc_update=[
            CompendiumNpcUpdate(
                id="guard",
                name="Guard",
                title="Town Guard",
                personality="cold_pragmatist",
                presence="present",
            )
        ]
    )
    second = SceneExtractResult(
        compendium_npc_update=[
            CompendiumNpcUpdate(
                id="guard",
                personality="charming_manipulator",
            )
        ]
    )
    apply_npc_scene_management(state, first, current_turn_no=1)
    apply_npc_scene_management(state, second, current_turn_no=2)
    assert state["compendium"]["npcs"]["guard"]["personality"] == "cold_pragmatist"
```

### REPOMAP and architecture updates
- Update `CompendiumNpcUpdate` signature in REPOMAP to note `personality: str | None` field.
- Note in REPOMAP that `personality` is write-once: set on creation, ignored on subsequent updates.

### Risks
1. Old saved game states have no `personality` key. Mitigation: all reads of `personality` from the compendium dict must use `.get("personality")` — it will return `None` and the narrator will simply omit the block. No migration needed.

---

## Implementation — Phase 03: Seed generation

**Depends on:** Phase 01, Phase 02

### Files to pull for context
- `ccya/personality.py` — `assign_personality`, `ARCHETYPES`
- `ccya/models.py` — `CompendiumNpcUpdate`
- The seed builder entry point (wherever `SeedEnvelope` / `build_seed` is constructed — likely `ccya/engine.py` or `ccya/seed.py`; executor must locate this before starting)
- `ccya/state/npcs.py` — `apply_npc_scene_management`
- `ccya/prompts/generate_seed_system.j2` — for schema update only

### Detailed steps

#### Step 3.1 — Assign personality to all seed NPCs after seed LLM call

**File:** The seed builder module (locate by searching for `SeedEnvelope` construction and `compendium.npcs` write).

**What:** After the seed LLM response is parsed and `seed_state.compendium.npcs` is populated but before the state is finalised, iterate over all NPC entries and call `assign_personality` for any that lack a `personality` key. Write the archetype id back into the entry dict.

**Why:** Phase 01 established the scoring function. Phase 02 established the write path. This phase calls both at the moment NPC state is created, so every NPC born from a seed has a personality before the first narrator turn.

```python
from ccya.personality import assign_personality

# After seed LLM parse, before state is returned:
for npc_id, npc_entry in seed_state["compendium"]["npcs"].items():
    if not isinstance(npc_entry, dict):
        continue
    if npc_entry.get("personality"):
        continue  # already set; skip
    arch = assign_personality(
        motivation=npc_entry.get("motivation"),
        fear=npc_entry.get("fear"),
        npc_id=npc_id,
    )
    npc_entry["personality"] = arch.id
    _log.info(
        "seed.assign_personality npc=%s personality=%s",
        npc_id,
        arch.id,
    )
```

**Validation:** Run the seed builder in test mode (or use an integration test fixture) and assert that every NPC in the returned seed state dict has a non-empty `personality` key.

#### Step 3.2 — Update `generate_seed_system.j2` schema comment

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** In the TypeScript-style output schema comment, add `personality?: string` as a read-only documentation note on the compendium NPC entry. Do **not** instruct the LLM to populate it — the engine sets it post-parse.

**Why:** The schema comment is what the seed LLM references when deciding which fields to emit. Adding it as a comment-only note prevents the LLM from trying to set it to a freeform value while still making the field's existence visible to future prompt authors.

```
// In the compendium.npcs entry TypeScript comment:
compendium: {
  npcs: {
    snake_case: {
      name: string,
      title: string,
      bio: string,
      allegiance?: string,
      bond?: string,
      motivation?: string,
      fear?: string,
      leverage?: string,
      // personality is assigned by the engine post-parse; do not set it
    }
  }
}
```

**Validation:** Grep for `personality` in the template to confirm no instruction asks the LLM to populate the field.

### Tests to write or update

**File:** `tests/test_seed.py` or `tests/test_engine.py` (extend existing)

Add a test that:
1. Constructs a minimal fake `seed_state` dict with 2–3 NPCs containing `motivation` and `fear` values.
2. Runs the personality assignment loop from Step 3.1 directly (extract the loop into a helper `assign_seed_personalities(seed_state: dict) -> None` if the executor finds it cleaner to test).
3. Asserts every NPC has `personality` set to a valid archetype id.

```python
from ccya.personality import ARCHETYPES, assign_personality


def _run_personality_assignment(seed_state: dict) -> None:
    """Extracted helper — mirrors the loop added to the seed builder."""
    for npc_id, npc_entry in seed_state["compendium"]["npcs"].items():
        if not isinstance(npc_entry, dict) or npc_entry.get("personality"):
            continue
        arch = assign_personality(
            motivation=npc_entry.get("motivation"),
            fear=npc_entry.get("fear"),
            npc_id=npc_id,
        )
        npc_entry["personality"] = arch.id


def test_all_seed_npcs_get_personality():
    seed_state = {
        "compendium": {
            "npcs": {
                "captain": {"name": "Captain", "motivation": "seeks order", "fear": "chaos"},
                "merchant": {"name": "Merchant", "motivation": "profit above all", "fear": "debt"},
                "beggar": {"name": "Beggar"},  # no MF fields
            }
        }
    }
    _run_personality_assignment(seed_state)
    npcs = seed_state["compendium"]["npcs"]
    for npc_id, entry in npcs.items():
        assert entry.get("personality") in ARCHETYPES, f"{npc_id} missing valid personality"
```

### REPOMAP and architecture updates
- Document the personality assignment step in the seed builder section of REPOMAP.
- Note that `assign_seed_personalities` (or the inline loop) runs post-LLM-parse, pre-state-write.

### Risks
1. Executor must locate the exact file/function where `seed_state.compendium.npcs` is finalised — the plan cannot name it without risking an incorrect guess. Executor must read the seed builder source before inserting code.
2. If the seed LLM emits a `personality` field despite the schema comment, the `if npc_entry.get("personality"): continue` guard preserves it rather than overwriting — acceptable behaviour.

---

## Implementation — Phase 04: Narrator prompt

**Depends on:** Phase 01, Phase 02, Phase 03

### Files to pull for context
- `ccya/prompts/narrate_user.j2` — the NPC context block
- `ccya/personality.py` — `ARCHETYPES` (to verify field names match template tokens)
- `ccya/state/npcs.py` — confirm how `notes` and other per-NPC fields are rendered into the prompt

### Detailed steps

#### Step 4.1 — Expose personality in the NPC context block

**File:** `ccya/prompts/narrate_user.j2`

**What:** In the existing NPC rendering loop (where `motivation`, `fear`, `leverage`, `notes` are output), add a conditional block that emits the personality label, traits, and speech hint when `npc.personality` resolves to a known archetype.

**Why:** The personality data is only useful if the narrator sees it. The speech hint is the highest-signal element — it directly shapes dialogue. Traits give the narrator vocabulary for NPC actions and reactions.

Locate the NPC loop in the template (it iterates over `compendium.npcs` for present NPCs). The executor must read the current template to find the exact anchor point and indentation. The addition should be inserted after the existing `leverage` line and before `notes`.

The template does not have access to the Python `ARCHETYPES` registry at render time, so the personality data must be pre-resolved into the context dict passed to the template, or the archetype fields must be stored on the compendium entry itself.

**Decision for executor:** The simplest approach is to store `personality_label`, `personality_traits`, and `personality_speech_hint` directly on the compendium entry dict when personality is assigned in Phase 03 (alongside the `personality` id). This avoids adding a Jinja global or template filter. The Phase 03 loop should be updated accordingly:

```python
# Updated Phase 03 assignment loop — store denormalized fields for template use
from ccya.personality import assign_personality, ARCHETYPES

for npc_id, npc_entry in seed_state["compendium"]["npcs"].items():
    if not isinstance(npc_entry, dict):
        continue
    if npc_entry.get("personality"):
        # If personality id is already set but denormalized fields are missing, backfill.
        arch = ARCHETYPES.get(npc_entry["personality"])
        if arch and not npc_entry.get("personality_traits"):
            npc_entry["personality_label"] = arch.label
            npc_entry["personality_traits"] = ", ".join(arch.traits)
            npc_entry["personality_speech_hint"] = arch.speech_hint
        continue
    arch = assign_personality(
        motivation=npc_entry.get("motivation"),
        fear=npc_entry.get("fear"),
        npc_id=npc_id,
    )
    npc_entry["personality"] = arch.id
    npc_entry["personality_label"] = arch.label
    npc_entry["personality_traits"] = ", ".join(arch.traits)
    npc_entry["personality_speech_hint"] = arch.speech_hint
    _log.info(
        "seed.assign_personality npc=%s personality=%s",
        npc_id,
        arch.id,
    )
```

The same denormalization should be applied in `apply_npc_scene_management` in Phase 02's write block (replace `entry["personality"] = comp_upd.personality` with the full three-field write, looking up the archetype from `ARCHETYPES`).

**Template addition** (find exact anchor, insert after `leverage` line):

```jinja
{% if npc.personality_traits %}
- Personality: {{ npc.personality_label }} — {{ npc.personality_traits }}. Speech: {{ npc.personality_speech_hint }}.
{% endif %}
```

**Validation:**
1. Run the narrator prompt rendering in test mode with a seed that has NPCs, and confirm the personality block appears for present NPCs.
2. Confirm that NPCs with no `personality_traits` key (old saves) render without error.

### Tests to write or update

**File:** `tests/test_prompt_render.py` or equivalent template render test (locate existing template tests first).

Add a test that:
1. Constructs a minimal state dict with one present NPC that has `personality_label`, `personality_traits`, and `personality_speech_hint` populated.
2. Renders `narrate_user.j2` against it.
3. Asserts the personality line appears in the rendered output.
4. Constructs a second state with an NPC missing those fields (simulating an old save).
5. Asserts rendering does not raise.

### REPOMAP and architecture updates
- Update `docs/REPOMAP/` narrator prompt section to note the new personality block and its three fields.
- Update the NPC entry schema note to include `personality`, `personality_label`, `personality_traits`, `personality_speech_hint` as engine-managed fields.

### Risks
1. The narrator template structure is not known to this plan author without reading it. Executor **must** read `narrate_user.j2` before making changes.
2. If the NPC loop only runs for `presence == "present"` NPCs, personality will not render for `nearby` NPCs. Executor should confirm and match existing behaviour (do not expand scope beyond present).
3. Denormalized fields stored on the compendium entry dict will be serialised to saved game state — this is intentional but adds ~3 short strings per NPC to storage size, which is acceptable.

---

## Ambiguities requiring resolution before execution

1. **Seed builder location.** This plan cannot name the exact file where `seed_state.compendium.npcs` is finalised after the seed LLM call. Options: A) It is in `ccya/engine.py`. B) It is in a dedicated `ccya/seed.py`. C) It is elsewhere. Executor must locate it before starting Phase 03.

2. **Narrator template NPC loop structure.** The exact Jinja block that renders present NPC fields in `narrate_user.j2` is unknown to this plan. Executor must read the file and find the loop anchor before making Phase 04 changes. If the NPC section renders fields differently than assumed (e.g. using a macro, not inline conditionals), the executor must adapt the template addition accordingly without changing the surrounding structure.
