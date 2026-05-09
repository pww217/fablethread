# `world_rules` — Pack-Level Universe Physical Constants

## Status
`open`

## Part of
standalone

## Dependencies
- none

## Objective
Packs have no dedicated way to declare the hard physical laws of their world — the non-negotiable constraints that define what is possible in this universe (e.g., "faster-than-light travel does not exist," "dead cannot be raised," "surveillance cameras cover every public surface"). These belong neither in `world_facts` (which are historical/political/economic facts) nor in `narrator_rules` (which are tone/style/pacing directives). Without a distinct field, authors either bloat `narrator_rules` with mixed concerns or skip world-physics entirely, leading to the LLM inventing contradictory capabilities mid-game. This plan adds `world_rules: list[str]` (max 5 entries) to `ScenarioBrief`, threads it through the narrator and seed-generation prompts, updates the pack generator prompt to produce it, and adds it to the `flooded-world` reference pack as a concrete example.

## Non-goals
- No new `world_rules` field on `Pack`, `PackManifest`, or any state model — it lives only on `ScenarioBrief`.
- No UI surface or display of `world_rules` to the player.
- No mana, willpower, cost, or resource-economy concepts — `world_rules` encodes physical possibility/impossibility, not economy.
- No changes to extraction prompts, rules engine, or dice system.
- No changes to existing packs other than `flooded-world` as the reference example.
- No new config key.

## Affected files

| File | Change type | Summary of change |
|---|---|---|
| `ccya/models.py` | modify | Add `world_rules: list[str]` field to `ScenarioBrief` (max 5 entries, default empty list) |
| `ccya/prompts/narrate_system.j2` | modify | Add `## Universe rules` block, rendered only when `world_rules` is non-empty |
| `ccya/prompts/generate_seed_user.j2` | modify | Pass `world_rules` into seed generation context so the seed LLM respects physical laws |
| `ccya/prompts/generate_pack_system.j2` | modify | Instruct pack-gen LLM to produce `world_rules` (3 entries, physical limits, no economy rules) |
| `packs/default/flooded-world/scenario.yaml` | modify | Add `world_rules` block with 3 entries as reference example |
| `docs/REPOMAP/pack.md` | modify | Document `world_rules` field on `ScenarioBrief` |
| `docs/plans/TODO.md` | modify | Add this plan under a new standalone section |

## Firm decisions

1. **`world_rules` is on `ScenarioBrief`, not `narrator_rules`.** The narrator prompt already has a `## Genre tone` section that renders `narrator_rules`. Universe physics are semantically different — they are hard world constraints, not tone/pacing directions — and belong in a separate labeled block so the LLM treats them as physical laws, not style suggestions.
2. **Max 5 entries.** Keeps token cost minimal; forces authors to choose only the laws that would otherwise be violated by a generic LLM. More than 5 indicates scope creep into `narrator_rules` territory.
3. **Entries are declarative physical facts, not prohibitions.** "Magic cannot travel faster than a spoken word" not "do not describe magic as instantaneous." Positive declarations are more robust instructions than negations.
4. **Default is an empty list.** `world_rules` is optional. Packs that do not need physics declarations (e.g. realistic historical settings) simply omit the field. No backfill of existing packs is required.
5. **Rendered between `## Style` and `## Genre tone` in the narrator prompt.** Physics are more fundamental than style — they logically precede tone directions in the LLM's reading order.
6. **`generate_pack_system.j2` instructs exactly 3 entries.** "Aim for 3" is the guidance — enough to establish world-physics without consuming the full 5-entry budget. Generated packs get 3; hand-authored packs may use up to 5.
7. **No validator that enforces prose style.** Authors write the entries; Pydantic only validates that the list has ≤ 5 strings. The existing `Constraints` model is not modified.

***

## Implementation — Phase 1: Model + Prompts + Reference Pack

### Context files to load

```
ccya/models.py
ccya/prompts/narrate_system.j2
ccya/prompts/generate_seed_user.j2
ccya/prompts/generate_pack_system.j2
packs/default/flooded-world/scenario.yaml
docs/REPOMAP/pack.md
```

### Overview

Add `world_rules` to `ScenarioBrief` in `models.py`. Thread it into two prompts — `narrate_system.j2` (runtime rendering) and `generate_seed_user.j2` (seed LLM context). Update `generate_pack_system.j2` so the pack-gen LLM knows to produce the field. Write the `flooded-world` entries as the canonical reference. Update REPOMAP.

***

### Detailed steps

#### Step 1.1 — Add `world_rules` to `ScenarioBrief`

**File:** `ccya/models.py`

**What:** Add a new optional field `world_rules` to the `ScenarioBrief` Pydantic model, typed as `list[str]` with a `max_length` validator capped at 5 items and defaulting to an empty list.

**Why:** `ScenarioBrief` is the single Pydantic-validated schema for `scenario.yaml`. Adding the field here ensures all downstream callers (narrator context builder, seed context builder, pack-gen output parser) work off the same validated type. Old-format `scenario.yaml` files that omit `world_rules` continue to validate because the default is `[]`.

**Code Snippet**

Read the current `ScenarioBrief` definition in `models.py` first to find the exact insertion point. The field goes after `narrator_rules` and before `factions`:

```python
from pydantic import field_validator

class ScenarioBrief(BaseModel):
    constraints: Constraints = Field(default_factory=Constraints)
    world_facts: list[str] = Field(default_factory=list, max_length=8)
    narrator_rules: list[str] = Field(default_factory=list, max_length=12)
    world_rules: list[str] = Field(default_factory=list, max_length=5)
    factions: list[Faction] = Field(default_factory=list, max_length=6)
    locations: list[NamedLocation] = Field(default_factory=list, max_length=10)
    name_locales: list[dict] = Field(default_factory=list)
    name_seed: int = 0
    inspiration: Inspiration = Field(default_factory=Inspiration)
```

**Validation:** After the edit, run `python -c "from ccya.models import ScenarioBrief; s = ScenarioBrief(); print(s.world_rules)"` — should print `[]`. Run `python -c "from ccya.models import ScenarioBrief; s = ScenarioBrief(world_rules=['a','b','c','d','e','f'])"` — should raise `ValidationError`.

***

#### Step 1.2 — Add `## Universe rules` block to `narrate_system.j2`

**File:** `ccya/prompts/narrate_system.j2`

**What:** Insert a new Jinja2 conditional block that renders a `## Universe rules` section when `world_rules` is non-empty. Place it immediately before the `{% if narrator_rules %}` block (i.e., after the `## Items and inventory` / `## Player intent is truth` sections but before `## Genre tone`).

**Why:** Physics are more fundamental than style. Placing the block before `## Genre tone` means the LLM reads hard constraints before reading tone/pacing suggestions. A separate labeled heading — `## Universe rules` — prevents the LLM from treating these as style suggestions. AGENTS.md prohibits altering prompts without explicit instruction; this plan is that explicit instruction.

**Code Snippet**

Locate the exact line `{% if narrator_rules %}` in the file and insert the following block immediately before it:

```jinja2
{% if world_rules %}
## Universe rules
These are physical laws of this world. They are not tone suggestions — they are hard constraints on what is physically possible. Never narrate events that contradict them, regardless of player action or dice outcome.
{% for rule in world_rules %}- {{ rule }}
{% endfor %}
{% endif %}
```

**Validation:** Load the template with a mock context where `world_rules=["Magic cannot cross running water."]` and confirm the rendered output contains `## Universe rules` with the bullet. Load it with `world_rules=[]` and confirm no `## Universe rules` section appears.

***

#### Step 1.3 — Pass `world_rules` into `generate_seed_user.j2`

**File:** `ccya/prompts/generate_seed_user.j2`

**What:** Read the existing template. Add a `{% if world_rules %}` block that renders the list in the seed generation context, placed after the `narrator_rules` block and before the `factions` block (mirroring schema order).

**Why:** The seed LLM generates the opening situation, PC, NPCs, inventory, and quests. If `world_rules` says "synthetic life cannot be created" but the seed LLM doesn't see that, it may generate an android NPC or a biotech quest that immediately violates the world's physics. The seed must know the physical laws at generation time.

**Code Snippet**

Read the file first. Find the block that renders `narrator_rules` (it will be a `{% for rule in narrator_rules %}` loop). Insert the following immediately after that block's `{% endif %}`:

```jinja2
{% if world_rules %}
## Universe rules
Physical laws of this world. Seed state must not contradict these.
{% for rule in world_rules %}- {{ rule }}
{% endfor %}
{% endif %}
```

**Validation:** Render the template with `world_rules=["The dead cannot be raised."]` and confirm the rule appears. Render with `world_rules=[]` and confirm the section is absent.

***

#### Step 1.4 — Update `generate_pack_system.j2` to produce `world_rules`

**File:** `ccya/prompts/generate_pack_system.j2`

**What:** Read the existing template. Find the section that describes `narrator_rules` output requirements. Add a new instruction block describing `world_rules`: produce exactly 3 declarative physical laws of the world; each entry must be a single sentence stating what is physically true or impossible in this universe; no cost/economy/resource rules; no tone or pacing directions; no prohibitions framed as negations if a positive declaration is possible.

**Why:** Without explicit instruction the pack-gen LLM will not produce `world_rules` in its output. The pack-gen output is parsed into `ScenarioBrief` by Pydantic, so once the field is in the model the LLM only needs to be told to emit it. Adding this to the system prompt (not user prompt) keeps the structural schema definition in one place.

**Code Snippet**

Read the file first to find the exact location of the `narrator_rules` output spec. Then insert after it:

```
## world_rules (required, exactly 3 entries)
Produce exactly 3 entries. Each entry is a single declarative sentence that states a hard physical law of this specific world — what is possible or impossible here that would not be true in a generic setting. 

Rules for writing entries:
- State physical facts, not tone directions ("Communication beyond line of sight requires relay towers" not "describe communication as difficult").
- Cover tech, biology, or metaphysics — whatever the world's defining physical constraints are. If the world has magic, state what magic physically can and cannot do without referencing cost or willpower.
- Do not state economic rules, resource costs, or willpower mechanics.
- Prefer positive declarations ("The only faster-than-light method is the Jump network, which requires a registered beacon at both endpoints") over negations ("FTL travel is not possible without beacons").
- Each entry must be a world-specific fact — not something true of all possible worlds ("people need air to breathe" is not a useful entry).
```

**Validation:** The pack-gen LLM is only tested at eval time. Validation here is: confirm the system prompt text renders without Jinja2 errors. The executor should also run `make check` to confirm no syntax issues in the template.

***

#### Step 1.5 — Add `world_rules` to `flooded-world/scenario.yaml`

**File:** `packs/default/flooded-world/scenario.yaml`

**What:** Add a `world_rules` block with 3 entries after `narrator_rules` and before `factions`. These should be the hard physical laws of the flooded world that have nothing to do with tone, economics, or political facts.

**Why:** `flooded-world` is the best-maintained, most structurally complete pack in the default set. Adding `world_rules` here serves as the canonical author reference for every future pack author and for the pack-gen LLM when it reads examples. The entries must be genuinely physical — not economic (salt pricing is already in `world_facts`) and not stylistic (water-based descriptions are already in `narrator_rules`).

**Code Snippet**

```yaml
world_rules:
  - "Desalination at industrial scale is physically impossible with available technology — salt cannot be removed from seawater in bulk, only harvested where it has already precipitated."
  - "The flood is a permanent hydrological fact: sea level rose two hundred feet over forty years and is not receding — no technology or political action in this world can reverse it."
  - "Radio and optical communication are line-of-sight only above water; submerged infrastructure carries no electrical signals — there is no wireless communication below the flood line."
```

**Validation:** Run `python -c "from ccya.pack import load_pack; p = load_pack('default/flooded-world', 'packs'); print(p.scenario.world_rules)"` — should print the three strings. Confirm no Pydantic validation error is raised.

***

#### Step 1.6 — Update `docs/REPOMAP/pack.md`

**File:** `docs/REPOMAP/pack.md`

**What:** In the `ScenarioBrief` model entry, add `world_rules` after `narrator_rules`:

```
- `ScenarioBrief` — ... `world_rules` (max 5 strings, optional, default []; hard physical laws of the world rendered in narrator as `## Universe rules` block; distinct from narrator_rules which are tone/style directives) ...
```

Also update the `scenario.yaml fields` description line to include `world_rules` in the field list.

**Why:** AGENTS.md is explicit: new fields on documented models must update REPOMAP in the same change.

**Validation:** Read the file and confirm the entry is present and accurate.

***

### Tests to write or update

**File:** `tests/test_models.py` (create or extend)

```python
def test_scenario_brief_world_rules_defaults_empty():
    from ccya.models import ScenarioBrief
    s = ScenarioBrief()
    assert s.world_rules == []

def test_scenario_brief_world_rules_max_five():
    from ccya.models import ScenarioBrief
    import pytest
    with pytest.raises(Exception):
        ScenarioBrief(world_rules=["a", "b", "c", "d", "e", "f"])

def test_scenario_brief_world_rules_accepts_three():
    from ccya.models import ScenarioBrief
    s = ScenarioBrief(world_rules=["a", "b", "c"])
    assert len(s.world_rules) == 3
```

No `FakeLLM` patterns needed — this plan does not touch LLM call sites, only model schema and Jinja2 templates.

***

### REPOMAP updates required

- `docs/REPOMAP/pack.md` — `ScenarioBrief` entry: add `world_rules` field description. `scenario.yaml fields` line: add `world_rules` to the field list.

***

### Risks

1. **`max_length` validator syntax.** Pydantic v1 vs v2 handle `max_length` on `list` fields differently. If the repo is on Pydantic v2, use `Field(default_factory=list, max_length=5)` directly on the annotation; if v1, use `@validator`. The executor must check the Pydantic version in `pyproject.toml` before writing the validator.
2. **`narrate_system.j2` context does not currently pass `world_rules`.** The context is built in `engine/narrate.py`. The executor must confirm whether `world_rules` reaches the Jinja2 context at render time. Read `engine/narrate.py` to find `_build_narrate_messages()` or equivalent and confirm `scenario.world_rules` is passed. If it is not, add it to the context dict — this is a one-liner. This is the most likely execution-time gap.
3. **`generate_seed_user.j2` may not receive `world_rules` in its context either.** Same issue as risk 2 — check `engine/seed.py` `_build_generate_seed_messages()`. Add `world_rules` to the context dict if missing.

***

## Ambiguities requiring resolution before execution

1. **Pydantic version.** The executor must check `pyproject.toml` for `pydantic` version before writing the `max_length` validator. Options: A) Pydantic v2 — use `Field(max_length=5)` or a `@field_validator`. B) Pydantic v1 — use `@validator("world_rules")` with a `len()` check.

2. **Narrator context builder location.** The executor must read `engine/narrate.py` to confirm the exact dict key name used for `narrator_rules` when building the Jinja2 context. The new `world_rules` key must use the same naming convention. Options: A) `world_rules` is already passed (unlikely, field is new). B) It is not passed — add it alongside `narrator_rules` in the context dict.

3. **Seed context builder location.** Same as above for `engine/seed.py`. Options: A) `world_rules` already in context. B) Must be added.

If any of these three are unresolved, the executor must check the source before writing code — not guess.

***

## TODO.md update

Add under a new `## Standalone` section at the bottom of `TODO.md`, after the `## Debug / Tooling` section:

```markdown
## Standalone

- [ ] **`world_rules` — pack-level universe physical constants** — `ScenarioBrief.world_rules` (max 5), narrator `## Universe rules` block, seed context pass-through, pack-gen LLM instruction, `flooded-world` reference entries — see [`world-rules.md`](world-rules.md)
```