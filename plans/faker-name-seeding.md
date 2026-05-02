# Plan: Faker-backed name seeding for `generate_seed`

## Problem

The `generate_seed` prompt warns the LLM away from Anglo-fantasy defaults
("Elias Thorne", "Marcus Cole", etc.) and toward culturally-plausible names —
but the LLM still has to invent them from nothing. Small local models drift
toward generic Anglo filler when left unsupported. The fix is to hand the
model a short, pre-generated roster of plausible names drawn from locales
appropriate to the pack, so it is filling in a character around a name rather
than producing a name as an afterthought.

---

## Approach

Use `faker` (already absent from `pyproject.toml` — add it) to generate a
small pool of culturally-appropriate raw names at `generate_seed` call time.
Inject them into the `generate_seed_user.j2` prompt as a non-binding
name roster. The LLM picks from the pool or departs from it; the pool
breaks the gravity toward Anglo defaults without being a hard constraint.

This touches:
- `pyproject.toml` — add `faker` dependency
- `pack.py` / `PackManifest` — add `name_locales` field to the manifest
- a new `ccya/names.py` utility module
- `ccya/engine.py` — call `names.py` inside `generate_seed()`
- `ccya/prompts/generate_seed_user.j2` — inject the name pool
- every pack's `pack.yaml` — add `name_locales` list

---

## 1 · Dependency

Add to `pyproject.toml` `[project] dependencies`:

```toml
"faker",
```

`faker` is pure-Python, no system libraries, < 2 MB. Run `uv sync` after.

---

## 2 · `PackManifest` — `name_locales` field

In `ccya/pack.py`, add one field to `PackManifest`:

```python
name_locales: list[str] = Field(default_factory=list)
```

`name_locales` is a list of BCP-47 locale strings Faker understands
(`en_US`, `de_DE`, `fr_FR`, `it_IT`, `pl_PL`, `ru_RU`, `ja_JP`, etc.).
An empty list means "use `en_US` as a fallback" — this preserves backwards
compatibility for any existing pack that hasn't declared locales yet.

Pack authors set this in `pack.yaml`. See §6 for per-pack values.

---

## 3 · `ccya/names.py` — utility module

Create `ccya/names.py`. It owns all Faker interaction; nothing else imports
`faker` directly.

```python
"""
names.py — generate culturally-appropriate name pools for the seed prompt.

Owned entirely by this module. Do not import faker elsewhere.
"""
from __future__ import annotations

import random
from faker import Faker

_FALLBACK_LOCALE = "en_US"


def generate_name_pool(
    locales: list[str],
    *,
    pc_count: int = 3,
    npc_count: int = 8,
    location_count: int = 5,
    seed: int | None = None,
) -> dict[str, list[str]]:
    """Return a dict with three keys: 'pc', 'npc', 'location'.

    - pc: candidate full names for the player character
    - npc: candidate full names for NPCs
    - location: candidate place names (streets, buildings, neighborhoods)

    Names are drawn proportionally from each locale in `locales`.
    If `locales` is empty, falls back to en_US.
    """
    if not locales:
        locales = [_FALLBACK_LOCALE]

    rng = random.Random(seed)
    fakers = [Faker(loc) for loc in locales]
    Faker.seed(seed or rng.randint(0, 2**31))

    def _pick() -> Faker:
        return rng.choice(fakers)

    pc_names = [_pick().name() for _ in range(pc_count)]
    npc_names = [_pick().name() for _ in range(npc_count)]
    location_names = [_pick().city() for _ in range(location_count)]

    return {
        "pc": pc_names,
        "npc": npc_names,
        "location": location_names,
    }
```

### Why these three buckets

- **pc**: 3 candidates. The LLM picks one or riffs on it. Small count keeps
  it fast and avoids prompt bloat.
- **npc**: 8 candidates. The scenario `min_named_npcs` is typically 2–4;
  8 gives variety without constraint.
- **location**: 5 city names. Used as inspiration for street-level and
  neighborhood names in the seed narrative, not as literal city names (the
  world.md sets actual geography).

### No streets or addresses by default

`faker.street_name()` and `faker.address()` often produce format artifacts
(e.g. "123 Main St Apt 4B") that are more confusing than helpful in a prompt
injection. Stick to `city()` for locations unless a specific pack warrants it.
If a pack needs street-name flavor (e.g. a tight urban noir), the pack author
can note that in `style.md` — that's the right place for prose guidance, not
the names pool.

---

## 4 · `engine.py` — call `names.py` in `generate_seed()`

Locate the `generate_seed()` function. Before the prompt is rendered, call:

```python
from ccya.names import generate_name_pool

name_pool = generate_name_pool(pack.manifest.name_locales)
```

Pass `name_pool` into the Jinja2 template context alongside the existing
variables (`schema_json`, `scenario`, `npc_count_override`, etc.):

```python
# existing render call — add name_pool to kwargs
prompt = render_template(
    "generate_seed_user.j2",
    ...,
    name_pool=name_pool,
)
```

No other changes to `engine.py`. Stays inside the function; doesn't touch
state, the turn pipeline, or any other call.

---

## 5 · `generate_seed_user.j2` — inject the pool

Add one new section to the user prompt template. Place it **after** the
existing overrides block and **before** the "emit JSON" instruction so it
lands in the part of the context the model sees last (highest recency weight).

```jinja2
{% if name_pool %}
## Name pool (non-binding suggestions)
These names were drawn from the cultural locales appropriate to this setting.
Use them, adapt them, or ignore them — but they are a starting point that fits
this world's demographic reality. Do not feel obligated to use all of them.

**PC candidates:** {{ name_pool.pc | join(", ") }}
**NPC candidates:** {{ name_pool.npc | join(", ") }}
**Place name inspiration:** {{ name_pool.location | join(", ") }}
{% endif %}
```

The `{% if name_pool %}` guard makes this a no-op if the pool is empty for
any reason (e.g. an unrecognised locale that Faker silently drops).

**Token cost**: ~40–60 tokens for a typical pool. Negligible.

---

## 6 · Pack `pack.yaml` updates

Add `name_locales` to every dynamic pack's `pack.yaml`. Packs without it
remain valid (field defaults to `[]` → fallback `en_US`).

| Pack | `name_locales` |
|---|---|
| `noir-1930s` | `[en_US, it_IT, es_ES, de_DE]` |
| `allied-ww2` | `[en_GB, en_US, de_DE, fr_FR, pl_PL, ru_RU]` |
| `civil-war-1861` | `[en_US]` |
| `cyberpunk-2077-bladerunner` | `[en_US, ja_JP, es_MX, ko_KR, de_DE]` |
| `expanse` | `[en_US, de_DE, es_ES, bn_BD, zh_TW]` |
| `flooded-world` | `[en_GB, pt_BR, id_ID, fr_FR]` |
| `space-western` | `[en_US, es_MX, zh_TW]` |
| `zombie-survival` | `[en_US, es_US]` |

Locale choices are derived from:
- `world.md` geography and demographic notes in each pack
- `scenario.yaml` NPC and PC inspiration prose
- The genre's real-world cultural referents (noir LA → Italian/Irish/Spanish
  immigrant mix; WW2 Allied → British/American/French/Polish/Russian)

Static packs (`civil-war-1861`) benefit less because their seed is
hand-authored, but the field is still valid if a static pack is later
converted to dynamic mode.

---

## 7 · Testing

Add a test in `tests/` (alongside the existing smoke tests) that:

1. Calls `generate_name_pool(["en_US", "de_DE"])` and asserts:
   - All three keys are present
   - `pc` has 3 entries, `npc` has 8, `location` has 5
   - Every entry is a non-empty string

2. Calls `generate_name_pool([])` and asserts fallback to `en_US`
   (i.e. returns a valid pool without raising).

3. Verifies the Jinja2 template renders without error when `name_pool` is
   passed (mock the rest of the context as in existing smoke tests).

No LLM is invoked. `faker` is the only new import under test.

---

## 8 · What this does NOT do

- **No new LLM call.** This is pure Python before the prompt is built.
- **No state changes.** `names.py` doesn't touch `state.py`, events, or
  compendium.
- **No UI changes.** The name pool is prompt-internal.
- **No per-turn injection.** This only runs in `generate_seed()`, not in
  `run_turn()`. NPCs named mid-game are the LLM's problem.
- **No hard constraints.** The LLM can and should deviate. The pool is a
  gravity source, not a fence.

---

## 9 · Files changed summary

| File | Change |
|---|---|
| `pyproject.toml` | add `faker` to dependencies |
| `ccya/names.py` | new module |
| `ccya/pack.py` | add `name_locales: list[str]` to `PackManifest` |
| `ccya/engine.py` | call `generate_name_pool()`, pass to template context |
| `ccya/prompts/generate_seed_user.j2` | add name pool block |
| `packs/*/pack.yaml` (all dynamic packs) | add `name_locales` list |
| `tests/test_names.py` | new test file |
