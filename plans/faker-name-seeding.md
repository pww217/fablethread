# Plan: Faker-backed name seeding for `generate_seed` and mid-game NPCs

## Problem

The `generate_seed` prompt warns the LLM away from Anglo-fantasy defaults
("Elias Thorne", "Marcus Cole", etc.) and toward culturally-plausible names —
but the LLM still has to invent them from nothing. Small local models drift
toward generic Anglo filler when left unsupported. The fix is to hand the
model a short, pre-generated roster of plausible names drawn from locales
appropriate to the pack, **weighted to reflect the genre's actual demographics**,
so it is filling in a character around a name rather than producing a name as
an afterthought.

There is a second problem: NPCs introduced mid-game (after seed generation)
get no name guidance at all — the LLM invents them turn-by-turn with no
cultural anchor. This plan addresses both.

---

## Approach

Use `faker` to generate name pools at two points in the pipeline:

1. **At `generate_seed()` time** — injected into `generate_seed_user.j2` as
   non-binding PC/NPC/place name suggestions.
2. **At `run_turn()` time** — a small rolling pool of NPC name candidates is
   injected into `narrate_system.j2` (or `narrate_user.j2`) whenever there
   are fewer than N compendium NPCs relative to turn count, acting as a
   persistent name-gravity source for mid-game introductions.

Locale lists are **weighted**: each locale is paired with a float weight so
noir-1930s can be 75% Anglo / 25% immigrant mix rather than an even
distribution.

This touches:
- `pyproject.toml` — add `faker` dependency
- `pack.py` / `PackManifest` — `name_locales` becomes a list of `{locale, weight}` pairs
- a new `ccya/names.py` utility module
- `ccya/engine.py` — call `names.py` in both `generate_seed()` and `run_turn()`
- `ccya/prompts/generate_seed_user.j2` — inject the seed-time pool
- `ccya/prompts/narrate_system.j2` — inject the rolling mid-game pool
- every pack's `pack.yaml` — add `name_locales` weighted list

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
name_locales: list[dict[str, Any]] = Field(default_factory=list)
```

Each entry is `{"locale": "en_US", "weight": 0.75}`. Weight is a float;
weights across all entries will be normalised to sum to 1.0 at call time,
so pack authors don't need to be precise — `[0.75, 0.15, 0.10]` and
`[75, 15, 10]` are equivalent.

An empty list means "use `en_US` at weight 1.0" — backwards compatible with
any pack that hasn't declared locales yet.

---

## 3 · `ccya/names.py` — utility module

Create `ccya/names.py`. It owns all Faker interaction; nothing else imports
`faker` directly.

```python
"""
names.py — generate culturally-appropriate name pools for prompt injection.

Owned entirely by this module. Do not import faker elsewhere.
"""
from __future__ import annotations

import random
from faker import Faker

_FALLBACK = [{"locale": "en_US", "weight": 1.0}]


def _build_weighted_fakers(
    locales: list[dict],
    rng: random.Random,
    seed: int | None,
) -> tuple[list[Faker], list[float]]:
    """Return (fakers, normalised_weights). Falls back to en_US if locales empty."""
    if not locales:
        locales = _FALLBACK
    Faker.seed(seed or rng.randint(0, 2**31))
    fakers = [Faker(entry["locale"]) for entry in locales]
    raw_weights = [float(entry.get("weight", 1.0)) for entry in locales]
    total = sum(raw_weights) or 1.0
    weights = [w / total for w in raw_weights]
    return fakers, weights


def _pick(fakers: list[Faker], weights: list[float], rng: random.Random) -> Faker:
    return rng.choices(fakers, weights=weights, k=1)[0]


def generate_name_pool(
    locales: list[dict],
    *,
    pc_count: int = 3,
    npc_count: int = 8,
    location_count: int = 5,
    seed: int | None = None,
) -> dict[str, list[str]]:
    """Return {"pc": [...], "npc": [...], "location": [...]}.

    Names are drawn with probability proportional to each locale's weight,
    so a locale with weight 0.75 produces ~75% of the names.
    """
    rng = random.Random(seed)
    fakers, weights = _build_weighted_fakers(locales, rng, seed)

    return {
        "pc": [_pick(fakers, weights, rng).name() for _ in range(pc_count)],
        "npc": [_pick(fakers, weights, rng).name() for _ in range(npc_count)],
        "location": [_pick(fakers, weights, rng).city() for _ in range(location_count)],
    }


def generate_npc_names(
    locales: list[dict],
    *,
    count: int = 6,
    seed: int | None = None,
) -> list[str]:
    """Return a small flat list of NPC name candidates for mid-game injection.

    Smaller than the seed-time pool; just enough to anchor the narrator for
    one or two new characters without bloating the prompt.
    """
    rng = random.Random(seed)
    fakers, weights = _build_weighted_fakers(locales, rng, seed)
    return [_pick(fakers, weights, rng).name() for _ in range(count)]
```

### Why weighted selection

`rng.choices(population, weights=weights)` maps directly onto the pack
author's intent: noir-1930s with `[{en_US, 0.75}, {it_IT, 0.15}, {de_DE, 0.10}]`
produces names that *feel* like a 1930s LA story — mostly Anglo, with an
Italian or German name surfacing occasionally. Even weighting would make
every third name Italian, which is wrong for the genre.

### Why two functions

`generate_name_pool` is called once at seed time and produces the richer
three-bucket structure (PC / NPC / location). `generate_npc_names` is called
per-turn for the mid-game rolling pool and returns a flat list — simpler to
inject into the narrate prompt without adding a new template variable structure.

---

## 4a · `engine.py` — seed-time pool (in `generate_seed()`)

Locate `_build_generate_seed_messages()`. Before rendering, call:

```python
from ccya.names import generate_name_pool

name_pool = generate_name_pool(pack.manifest.name_locales)
```

Pass `name_pool` into the Jinja2 context alongside existing variables:

```python
ctx = {
    ...existing keys...,
    "name_pool": name_pool,
}
```

No other changes to `generate_seed()`.

---

## 4b · `engine.py` — rolling mid-game pool (in `run_turn()`)

In `run_turn()`, after `state = load_state(save_dir)` and before
`_narrate_messages()` is called, compute a rolling name pool:

```python
from ccya.names import generate_npc_names

# Only inject when the pack has locale data (passed in via pack object,
# or read from state.meta if the pack isn't re-loaded per turn — see note).
_npc_name_pool: list[str] = []
if pack_name_locales:  # list[dict] from the Pack object
    current_turn = (state.get("meta") or {}).get("turn", 0)
    _npc_name_pool = generate_npc_names(
        pack_name_locales,
        count=6,
        # Use turn as seed variation so the pool rotates each turn,
        # giving the LLM fresh names if it needs to introduce multiple
        # characters over the course of the game.
        seed=current_turn,
    )
```

Pass `npc_name_pool=_npc_name_pool` to `_narrate_messages()` and then into
the Jinja template context.

### How the pack locales reach `run_turn()`

`run_turn()` already accepts `pack_style: str` and `pack_examples` as
caller-supplied arguments (set in `server.py` when it loads the Pack). Add a
parallel `pack_name_locales: list[dict] = []` parameter. `server.py` passes
`pack.manifest.name_locales` through at call time — same pattern, no new
state serialisation needed.

The locales live in the Pack manifest, not in `state.yaml`, which means they
can be updated by editing `pack.yaml` without migrating existing saves.

---

## 5a · `generate_seed_user.j2` — inject the seed-time pool

Add after the overrides block and before the "emit JSON" instruction:

```jinja2
{% if name_pool %}
## Name pool (non-binding suggestions)
These names were sampled from the cultural locales appropriate to this setting,
weighted to reflect the genre's demographic reality. Use them, adapt them, or
ignore them — they are a starting point, not a constraint.

**PC candidates:** {{ name_pool.pc | join(", ") }}
**NPC candidates:** {{ name_pool.npc | join(", ") }}
**Place name inspiration:** {{ name_pool.location | join(", ") }}
{% endif %}
```

**Token cost**: ~40–60 tokens. Negligible.

---

## 5b · `narrate_system.j2` — inject the rolling mid-game pool

Add a guarded block near the bottom of the system prompt (after world/scene
context, before the output format instructions):

```jinja2
{% if npc_name_pool %}
## Available NPC name candidates
If this turn introduces a new character who needs a name, these are
culturally appropriate options for this setting. Pick one, adapt it, or
ignore it — but do not default to generic Anglo names if the setting calls
for something else.
{{ npc_name_pool | join(" · ") }}
{% endif %}
```

This block only appears when `npc_name_pool` is non-empty, so turns that
don't introduce anyone get no prompt overhead.

**Why system prompt, not user prompt**: The narrate system prompt is the
stable, KV-cache-friendly half of the narrate call. The pool changes per turn
(seeded by turn number), so it will bust the cache anyway — placing it in the
system prompt just keeps the user prompt cleaner and easier to read in logs.

**Token cost**: ~25–35 tokens per turn. Acceptable.

---

## 6 · Pack `pack.yaml` updates

Replace the plain `name_locales` string list with weighted dicts. The weights
below are genre-justified:

| Pack | `name_locales` |
|---|---|
| `noir-1930s` | `[{en_US, 0.75}, {it_IT, 0.12}, {de_DE, 0.08}, {es_ES, 0.05}]` |
| `allied-ww2` | `[{en_GB, 0.30}, {en_US, 0.25}, {de_DE, 0.20}, {fr_FR, 0.15}, {pl_PL, 0.05}, {ru_RU, 0.05}]` |
| `civil-war-1861` | `[{en_US, 1.0}]` |
| `cyberpunk-2077-bladerunner` | `[{en_US, 0.30}, {ja_JP, 0.30}, {es_MX, 0.20}, {ko_KR, 0.10}, {de_DE, 0.10}]` |
| `expanse` | `[{en_US, 0.40}, {de_DE, 0.15}, {es_ES, 0.15}, {bn_BD, 0.15}, {zh_TW, 0.15}]` |
| `flooded-world` | `[{en_GB, 0.35}, {pt_BR, 0.25}, {id_ID, 0.20}, {fr_FR, 0.20}]` |
| `space-western` | `[{en_US, 0.60}, {es_MX, 0.25}, {zh_TW, 0.15}]` |
| `zombie-survival` | `[{en_US, 0.80}, {es_US, 0.20}]` |

### Weight rationale

- **noir-1930s**: 1930s LA was demographically Anglo-majority, with Italian and
  Irish immigrant communities prominent in organised crime, German immigrants
  present, and smaller Spanish-speaking populations. 75/12/8/5 gives the right
  feel — you'll see a "Jack Malone" next to a "Sal Ferraro" occasionally, not
  every other name.
- **allied-ww2**: Even split across Allied nations; German names appear because
  the scenario likely involves German characters (enemies, informants, civilians).
- **cyberpunk**: Heavy Japanese/American split for the Blade Runner / 2077
  aesthetic; Korean and German names for corp diversity.
- **expanse**: The series explicitly portrays a mixed Belt/Martian/Earth
  demography; the 40/15/15/15/15 split reflects that roughly.

---

## 7 · Testing

Add `tests/test_names.py`:

1. **Weighted distribution test**: Call `generate_name_pool` with
   `[{en_US, 0.9}, {it_IT, 0.1}]`, n=1000. Assert that ~85–95% of names
   come from an en_US Faker instance (spot-check by re-generating with each
   locale alone and checking for overlap). This is a probabilistic test — use
   a fixed seed and assert exact counts.

2. **Structure test**: Assert `pc` has 3, `npc` has 8, `location` has 5 entries;
   all non-empty strings.

3. **Fallback test**: `generate_name_pool([])` returns a valid pool without
   raising.

4. **`generate_npc_names` test**: Returns 6 non-empty strings; honours count
   param.

5. **Jinja render test**: Both `generate_seed_user.j2` and `narrate_system.j2`
   render without error when `name_pool` / `npc_name_pool` are passed
   (mock the rest of the context as in existing smoke tests).

No LLM is invoked. `faker` is the only new import under test.

---

## 8 · What this does NOT do

- **No new LLM call.** Both pools are pure Python before prompts are built.
- **No state changes.** `names.py` doesn't touch `state.py`, events, or
  compendium.
- **No UI changes.** The name pools are prompt-internal.
- **No hard constraints.** The LLM can and should deviate. The pool is a
  gravity source, not a fence.
- **No per-turn pool persistence.** The rolling pool is recomputed fresh each
  turn from the turn number seed. This means the same turn replayed gets the
  same pool (good for determinism) and successive turns get different pools
  (good for variety).

---

## 9 · Files changed summary

| File | Change |
|---|---|
| `pyproject.toml` | add `faker` to dependencies |
| `ccya/names.py` | new module |
| `ccya/pack.py` | `name_locales: list[dict]` on `PackManifest` |
| `ccya/engine.py` | call `generate_name_pool()` in `_build_generate_seed_messages()`; call `generate_npc_names()` in `run_turn()`; add `pack_name_locales` param to `run_turn()` |
| `ccya/prompts/generate_seed_user.j2` | add seed-time name pool block |
| `ccya/prompts/narrate_system.j2` | add rolling mid-game NPC pool block |
| `server.py` | pass `pack.manifest.name_locales` to `run_turn()` |
| `packs/*/pack.yaml` (all dynamic packs) | replace/add weighted `name_locales` list |
| `tests/test_names.py` | new test file |
