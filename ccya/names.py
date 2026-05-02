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
