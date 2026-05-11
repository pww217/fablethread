"""
names.py — generate culturally-appropriate name pools for prompt injection.

Owned entirely by this module. Do not import faker elsewhere.
"""

from __future__ import annotations

import random
import re
from typing import Any

from faker import Faker

_FALLBACK = [{"locale": "en_US", "weight": 1.0}]


def _build_weighted_fakers(
    locales: list[dict[str, Any]],
    rng: random.Random,
    seed: int | None,
) -> tuple[list[Faker], list[float]]:
    if not locales:
        locales = _FALLBACK
    Faker.seed(seed or rng.randint(0, 2**31))
    fakers = [Faker(entry["locale"]) for entry in locales]
    raw_weights = [float(entry.get("weight", 1.0) or 1.0) for entry in locales]  # type: ignore[arg-type]
    total = sum(raw_weights) or 1.0
    weights = [w / total for w in raw_weights]
    return fakers, weights


def _pick(fakers: list[Faker], weights: list[float], rng: random.Random) -> Faker:
    return rng.choices(fakers, weights=weights, k=1)[0]


def _ensure_ascii(name: str) -> str:
    """Strip non-ASCII characters from a name, keeping only Latin letters, digits, spaces, hyphens, and apostrophes."""
    result = re.sub(r"[^\x00-\x7F]", "", name).strip()
    if not result:
        return "Unknown"
    return result


def generate_name_pool(
    locales: list[dict[str, Any]],
    *,
    pc_count: int = 3,
    npc_count: int = 8,
    location_count: int = 5,
    seed: int | None = None,
) -> dict[str, list[str]]:
    rng = random.Random(seed)
    fakers, weights = _build_weighted_fakers(locales, rng, seed)

    return {
        "pc": [_ensure_ascii(_pick(fakers, weights, rng).name()) for _ in range(pc_count)],
        "npc": [_ensure_ascii(_pick(fakers, weights, rng).name()) for _ in range(npc_count)],
        "location": [_ensure_ascii(_pick(fakers, weights, rng).city()) for _ in range(location_count)],
    }


def generate_npc_names(
    locales: list[dict[str, Any]],
    *,
    count: int = 10,
    seed: int | None = None,
) -> list[str]:
    rng = random.Random(seed)
    fakers, weights = _build_weighted_fakers(locales, rng, seed)
    return [_ensure_ascii(_pick(fakers, weights, rng).name()) for _ in range(count)]


def generate_npc_names_split(
    locales: list[dict[str, Any]],
    *,
    male_count: int = 5,
    female_count: int = 5,
    seed: int | None = None,
) -> dict[str, list[str]]:
    """Generate NPC names split by gender for gender-aware casting."""
    rng = random.Random(seed)
    fakers, weights = _build_weighted_fakers(locales, rng, seed)
    male_names = []
    female_names = []
    for _ in range(male_count):
        faker = _pick(fakers, weights, rng)
        male_names.append(_ensure_ascii(faker.first_name_male() if hasattr(faker, 'first_name_male') else faker.name()))
    for _ in range(female_count):
        faker = _pick(fakers, weights, rng)
        female_names.append(_ensure_ascii(faker.first_name_female() if hasattr(faker, 'first_name_female') else faker.name()))
    return {"male": male_names, "female": female_names}



