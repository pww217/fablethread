"""
names.py — generate culturally-appropriate name pools for prompt injection.

Owned entirely by this module. Do not import faker elsewhere.
"""

from __future__ import annotations

import logging
import random
from typing import Any

from faker import Faker
from pykakasi import Kakasi

_log = logging.getLogger(__name__)

_FALLBACK = [{"locale": "en_US", "weight": 1.0}]


def _build_weighted_fakers(
    locales: list[dict[str, Any]],
    rng: random.Random,
    seed: int | None,
) -> tuple[list[Faker], list[float]]:
    if not locales:
        locales = _FALLBACK
    # ja_JP locale: use exclusively (romaji conversion handles the rest)
    ja_locales = [e for e in locales if e.get("locale") == "ja_JP"]
    if ja_locales:
        locales = ja_locales
    Faker.seed(seed or rng.randint(0, 2**31))
    fakers = [Faker(str(entry["locale"])) for entry in locales]
    raw_weights = [float(str(entry.get("weight", 1.0) or 1.0)) for entry in locales]
    total = sum(raw_weights) or 1.0
    weights = [w / total for w in raw_weights]
    return fakers, weights


def _pick(fakers: list[Faker], weights: list[float], rng: random.Random) -> Faker:
    return rng.choices(fakers, weights=weights, k=1)[0]


def _ensure_ascii(name: str) -> str:
    """Keep the name as-is; Unicode names are valid."""
    return name.strip()


_kakasi = None


def _to_romaji(name: str) -> str:
    """Convert Japanese (kanji/kana) to romaji using passport-style romanization."""
    global _kakasi
    if _kakasi is None:
        _kakasi = Kakasi()  # type: ignore[no-untyped-call]  # pykakasi has no type stubs
    result = _kakasi.convert(name)
    parts = []
    for part in result:
        passport = part.get("passport", "")
        if passport and passport != " ":
            parts.append(passport)
    return " ".join(parts) if parts else name


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
    use_romaji = any(entry.get("locale") == "ja_JP" for entry in locales)

    def _gen_names(count: int) -> list[str]:
        names = []
        for _ in range(count):
            faker = _pick(fakers, weights, rng)
            first = faker.first_name() if hasattr(faker, "first_name") else faker.name()
            last = faker.last_name() if hasattr(faker, "last_name") else ""
            full = f"{first} {last}" if last else first
            if use_romaji:
                names.append(_to_romaji(full))
            else:
                names.append(_ensure_ascii(full))
        return names

    def _gen_locations(count: int) -> list[str]:
        suffixes = ["shire", "burg", "ton", "stead", "ford", "worth", "bury", "port", "mouth"]
        locations = []
        for i in range(count):
            faker = _pick(fakers, weights, rng)
            last = faker.last_name()
            suffix = suffixes[i % len(suffixes)]
            name = f"{last}{suffix}"
            if use_romaji:
                locations.append(_to_romaji(name))
            else:
                locations.append(_ensure_ascii(name))
        return locations

    result = {
        "pc": _gen_names(pc_count),
        "npc": _gen_names(npc_count),
        "location": _gen_locations(location_count),
        "inventory": _gen_locations(3),
    }
    for cat, names in result.items():
        expected = {"pc": pc_count, "npc": npc_count, "location": location_count, "inventory": 3}.get(cat, 0)
        if len(names) < expected:
            _log.warning("name pool '%s' generated %d/%d names", cat, len(names), expected)
        else:
            _log.debug("name pool '%s' generated %d names", cat, len(names))
    return result


def generate_npc_names(
    locales: list[dict[str, Any]],
    *,
    count: int = 10,
    seed: int | None = None,
    gender: str | None = None,
) -> list[str]:
    rng = random.Random(seed)
    fakers, weights = _build_weighted_fakers(locales, rng, seed)
    use_romaji = any(entry.get("locale") == "ja_JP" for entry in locales)
    names = []
    for _ in range(count):
        faker = _pick(fakers, weights, rng)
        if gender == "male" and hasattr(faker, "first_name_male"):
            first = faker.first_name_male()
        elif gender == "female" and hasattr(faker, "first_name_female"):
            first = faker.first_name_female()
        else:
            first = faker.first_name() if hasattr(faker, "first_name") else faker.name()
        last = faker.last_name() if hasattr(faker, "last_name") else ""
        full = f"{first} {last}" if last else first
        if use_romaji:
            names.append(_to_romaji(full))
        else:
            names.append(_ensure_ascii(full))
    return names


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
        first = faker.first_name_male() if hasattr(faker, "first_name_male") else faker.first_name() if hasattr(faker, "first_name") else faker.name()
        last = faker.last_name() if hasattr(faker, "last_name") else ""
        male_names.append(_ensure_ascii(f"{first} {last}" if last else first))
    for _ in range(female_count):
        faker = _pick(fakers, weights, rng)
        first = faker.first_name_female() if hasattr(faker, "first_name_female") else faker.first_name() if hasattr(faker, "first_name") else faker.name()
        last = faker.last_name() if hasattr(faker, "last_name") else ""
        female_names.append(_ensure_ascii(f"{first} {last}" if last else first))
    return {"male": male_names, "female": female_names}



