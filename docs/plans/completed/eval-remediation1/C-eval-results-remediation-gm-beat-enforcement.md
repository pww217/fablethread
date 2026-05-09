# GM Beat Quality Enforcement

## Status
`open`

## Part of
`eval-results-remediation`

## Dependencies
- Plan A (`eval-results-remediation-pipeline-field-routing.md`) must be complete. After Plan A, `gm_beat` lives in `SceneExtractResult` and is governed by `extract_scene_system.j2`. This plan's model validator and prompt changes target that location.

## Objective
The eval runs found that `gm_beat.instruction` was frequently empty or generic — "something happens," "give the player a rest," etc. — making the beat useless for the narrator. This plan enforces a non-empty, concrete instruction at two levels: a Pydantic validator that silently nullifies a `gm_beat` with a blank or whitespace-only `instruction`, and a strengthened prompt rule that requires the instruction to name a specific NPC, faction, object, or location before choosing `type`.

## Non-goals
- Does NOT change `gm_beat` type logic (when to emit `complication` vs `revelation` etc.) — those rules are in Plan A's scene system prompt and are not modified here beyond the instruction quality rule.
- Does NOT change how `gm_beat` is applied to state or surfaced to the narrator.
- Does NOT change `surface_as` logic.
- Does NOT touch any other model, extractor, or prompt.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/models.py` | modify | Add `@field_validator` on `GMBeat.instruction` that nullifies the beat if instruction is blank/whitespace/generic filler |
| `ccya/prompts/extract_scene_system.j2` | modify | Strengthen the `gm_beat` instruction quality rule; add explicit BAD/GOOD examples; add pre-flight check requiring named entity before choosing `type` |
| `docs/REPOMAP/engine.md` | update | Note `GMBeat` validator behavior |
| `docs/plans/TODO.md` | update | Add this plan |

## Firm decisions

1. **Silent nullification, not hard error.** If `gm_beat.instruction` is empty, whitespace-only, or matches a known filler pattern, the validator sets the entire `gm_beat` to `None` on the parent `SceneExtractResult`. This prevents a bad beat from reaching the narrator without raising a pipeline exception.
2. **The validator lives on `GMBeat` itself**, not on `SceneExtractResult`. It sets `instruction = None` on the `GMBeat` instance; the parent model treats a `GMBeat` with `instruction=None` as invalid. A second class-level validator on `SceneExtractResult` nullifies the `gm_beat` field entirely if `instruction` is absent.
3. **Filler detection is simple string matching**, not LLM-based. Patterns: empty string, whitespace-only, length < 40 characters, or starts with a generic phrase from a fixed set. This is fast and deterministic.
4. **Prompt rule requires a named entity** (NPC name, faction name, object name, or location name) to appear in the instruction before the beat type is chosen. This is a soft rule enforced by language, not code — the validator catches the worst cases mechanically.

## Implementation — Phase 1: Model validator

### Context files to load
- `ccya/models.py` (post Plan A)

### Overview
Add a `@field_validator` to `GMBeat` that cleans up a bad `instruction`. Add a `@model_validator` to `SceneExtractResult` that nullifies `gm_beat` if the instruction didn't survive.

### Detailed steps

#### Step 1.1 — Change `GMBeat.instruction` type, add filler-prefix constant, add validator

**File:** `ccya/models.py`

**Prerequisite — import change:** Add `model_validator` to the Pydantic import on line 9. The existing import is:
```python
from pydantic import BaseModel, Field, field_validator
```
Change to:
```python
from pydantic import BaseModel, Field, field_validator, model_validator
```

**Prerequisite — field type change:** The current `GMBeat.instruction` field (line 386) is `instruction: str = ""`. This must be changed to `instruction: str | None = None` before adding the validator, because the validator returns `None` for bad instructions and the field type must accept `None`. This is the first code change in this step.

**What:** 
1. Insert `_GM_BEAT_FILLER_PREFIXES` directly above the `class GMBeat` definition at line 384.
2. Rewrite `GMBeat` with the type change on `instruction` and the `@field_validator`.
3. Preserve the existing `Literal` constraints on `type` and `surface_as` — do not regress those types.

**Why:** The eval found beats with `instruction: ""` or `instruction: "Something happens."` — these are noise. Silent nullification is cheaper than a retry.

**Code Snippet** (replace lines 384–387 with the following, inserting the constant directly above):
```python
_GM_BEAT_FILLER_PREFIXES: tuple[str, ...] = (
    "something happens",
    "give the player",
    "something bad",
    "an event occurs",
    "things get worse",
    "a complication arises",
    "add tension",
    "raise the stakes",
    "provide a",
    "create a",
    "introduce a",
    "the gm",
)

class GMBeat(BaseModel):
    type: Literal["complication", "revelation", "opportunity", "breathing_room", "pressure"] | None = None
    surface_as: Literal["ambient", "event", "npc_behavior"] = "ambient"
    instruction: str | None = None

    @field_validator("instruction", mode="after")
    @classmethod
    def _validate_instruction_quality(cls, v: str | None) -> str | None:
        if not v:
            return None
        stripped = v.strip()
        if len(stripped) < 40:
            return None
        lower = stripped.lower()
        if any(lower.startswith(prefix) for prefix in _GM_BEAT_FILLER_PREFIXES):
            return None
        return stripped
```

**Note on `mode="after"`:** This mode receives the already-validated (post-coercion) value. With `instruction: str | None`, the validator will receive either a `str` or `None`. The `if not v` check handles both `None` (field not provided) and empty string `""` (Pydantic coerced from LLM output). This is intentional — we want to catch both cases.

**Validation:**
```python
from ccya.models import GMBeat
assert GMBeat(type="complication", instruction="").instruction is None
assert GMBeat(type="complication", instruction="   ").instruction is None
assert GMBeat(type="complication", instruction="Something happens.").instruction is None
assert GMBeat(type="complication", instruction="Give the player a rest.").instruction is None
b = GMBeat(type="complication", instruction="A contact the player trusted has been seen meeting with the dockmaster's crew.")
assert b.instruction is not None
```

---

#### Step 1.2 — Nullify `gm_beat` in `SceneExtractResult` if instruction is gone

**File:** `ccya/models.py`

**Context:** The `SceneExtractResult` you are modifying is the **post-Plan-A version** produced by `A-eval-results-remediation-pipeline-field-routing.md`. Plan A moves `gm_beat` from `ProgressExtractResult` into `SceneExtractResult` and moves `ScenePressure`/`GMBeat` class definitions above `SceneExtractResult`. If Plan A has not been applied, this step will fail because `SceneExtractResult` currently has no `gm_beat` field. Verify that `SceneExtractResult` has a `gm_beat: GMBeat | None = None` field before proceeding.

**What:** Add a `@model_validator(mode="after")` to `SceneExtractResult` that sets `self.gm_beat = None` if `self.gm_beat.instruction is None` or `self.gm_beat.type is None`.

**Why:** A beat with no instruction or no type cannot be applied. Better to surface `None` than a half-formed beat.

**Code Snippet**
```python
# Inside SceneExtractResult, after all field_validators:

    @model_validator(mode="after")
    def _nullify_invalid_gm_beat(self) -> "SceneExtractResult":
        if self.gm_beat is not None:
            if not self.gm_beat.instruction or not self.gm_beat.type:
                self.gm_beat = None
        return self
```

**Validation:**
```python
# Prerequisite check — Plan A must be applied first:
from ccya.models import SceneExtractResult
assert hasattr(SceneExtractResult.model_fields, "gm_beat"), "Plan A not yet applied — gm_beat not in SceneExtractResult"

from ccya.models import SceneExtractResult, GMBeat
r = SceneExtractResult(gm_beat={"type": "complication", "instruction": ""})
assert r.gm_beat is None

r2 = SceneExtractResult(gm_beat={"type": "complication", "instruction": "The harbormaster's ally has marked the player's ship for seizure at dawn."})
assert r2.gm_beat is not None
assert r2.gm_beat.instruction is not None
```

---

## Implementation — Phase 2: Prompt reinforcement

### Context files to load
- `ccya/prompts/extract_scene_system.j2` (post Plan A)

### Overview
The GM Beat section in the scene system prompt already has BAD/GOOD examples from Plan A. Strengthen them. Add a mandatory pre-flight check: before choosing `type`, the model must confirm the instruction names a specific NPC, faction, object, or location.

### Detailed steps

#### Step 2.1 — Strengthen the `gm_beat` instruction rule

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Replace the existing BAD/GOOD instruction examples section with the expanded version below. The key additions: (1) explicit pre-flight check, (2) additional BAD examples covering generic category language, (3) minimum length signal.

**Why:** The LLM was generating instructions like "Introduce a complication" or "Add tension to the scene" — these name no entity and give the narrator nothing to work with.

**Code Snippet** (replace the `Beat instruction rules:` section):

Beat instruction rules:

    Before writing instruction, confirm you can name at least one specific entity from the current scene: an NPC by name, a faction, an object, or a named location. If you cannot, emit null for the entire beat.

    instruction: 1–2 sentences. Concrete and story-specific — name the entity. Minimum ~25 words. Must not be empty, must not be a generic category description.

    BAD (too short): "Something happens." "Guards arrive." "Tension rises."

    BAD (generic category): "Introduce a complication involving the guards." "Give the player an opportunity." "Add pressure to the scene."

    BAD (no entity): "A rival faction acts against the player's interests." ← no names, no scene anchor

    GOOD: "Marten Voss, the dockmaster's enforcer the player spoke with earlier, has quietly signaled two armed men near the exit — they are waiting for the player to leave."

    GOOD: "The satchel the fleeing guard dropped contains a partial map with a location marked in red ink — the same symbol the player saw on the warehouse door."

    GOOD: "Councilor Drae has just entered the far end of the hall. She has not seen the player yet, but one of the staff has noticed both of them."


**Validation:** Template renders without error. Run a scenario through the full pipeline with a FakeLLM returning `instruction: "Add tension."` — assert `scene_result.gm_beat` is `None` (caught by validator).

---

### Tests to write or update

**File:** `tests/test_models.py` (extend)
```python
def test_gm_beat_validator_rejects_empty():
    from ccya.models import GMBeat
    assert GMBeat(type="complication", instruction="").instruction is None

def test_gm_beat_validator_rejects_short():
    from ccya.models import GMBeat
    assert GMBeat(type="complication", instruction="Guards arrive.").instruction is None

def test_gm_beat_validator_rejects_filler():
    from ccya.models import GMBeat
    fillers = [
        "Something happens to the player.",
        "Give the player a chance to rest.",
        "Add tension to the scene.",
        "Introduce a complication.",
        "Create a problem.",
    ]
    for f in fillers:
        assert GMBeat(type="complication", instruction=f).instruction is None, f"Expected None for: {f}"

def test_gm_beat_validator_accepts_specific():
    from ccya.models import GMBeat
    b = GMBeat(
        type="revelation",
        instruction="The woman the player spoke with at the inn, Sera Lant, is visible through the crowd — she is meeting with the harbor prefect who publicly denied knowing her."
    )
    assert b.instruction is not None

def test_scene_extract_result_nullifies_bad_beat():
    from ccya.models import SceneExtractResult
    r = SceneExtractResult(gm_beat={"type": "complication", "instruction": "Something bad happens."})
    assert r.gm_beat is None

def test_scene_extract_result_preserves_good_beat():
    from ccya.models import SceneExtractResult
    r = SceneExtractResult(gm_beat={
        "type": "complication",
        "surface_as": "npc_behavior",
        "instruction": "Torben Klask, who agreed to help the player, has just received a message that visibly disturbed him — he is avoiding eye contact."
    })
    assert r.gm_beat is not None
    assert r.gm_beat.type == "complication"
```

### REPOMAP updates required
`docs/REPOMAP/engine.md` — document that `GMBeat.instruction` has a quality validator; note `SceneExtractResult._nullify_invalid_gm_beat` model validator.

### Risks
1. **Filler prefix list is incomplete** — new generic patterns will emerge. The length floor (< 40 chars) is a reliable secondary catch. Accept that some low-quality beats survive the validator and rely on the prompt rule to reduce frequency. The `startswith` check is intentionally limited — it only catches instructions that open with these phrases. Mid-sentence filler is handled by the 40-char length floor. This is by design.
2. **`model_validator(mode="after")` order** — Pydantic runs field validators before model validators. Confirm that `_validate_instruction_quality` runs before `_nullify_invalid_gm_beat`. If order is wrong, the model validator may see a non-None instruction that should have been cleared. Test explicitly.
3. **False positives on short but valid beats** — a valid short instruction like `"She lied to you."` (16 chars) is clipped by the 40-char floor. This is intentional — the eval evidence shows the narrator generates better beats from `null` than from vague noise. If legitimate short beats are being lost, the prefix list should be extended rather than the floor lowered.

## Ambiguities requiring resolution before execution
None.

## TODO.md update
Under `## P1 — Active`:

GM beat quality enforcement — docs/plans/eval-results-remediation/C-eval-results-remediation-gm-beat-enforcement.md