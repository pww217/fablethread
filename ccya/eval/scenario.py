"""Scenario / Turn dataclasses + Python-file loader.

Scenarios live as importable Python module under evals/scenarios/. Each module
must define a module-level `scenario: Scenario` attribute. Python (not YAML) so
the scenario file gets type-checking, IDE autocomplete, and refactor support.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Turn:
    """One player command in a scenario."""

    input: str
    # Free-text tag for grouping in the REPORT (e.g. "dialogue", "combat_engage").
    # Not enforced; appears in per-turn metrics table.
    phase: str = ""
    # Soft assertions surfaced as report annotations. Not test failures.
    # Examples: "scope_skips_inventory", "rules_call_required", "skill=charisma".
    expects: list[str] = field(default_factory=list)


@dataclass
class Scenario:
    id: str
    pack: str
    description: str
    turns: list[Turn]


def load_scenario(path: str | Path) -> Scenario:
    """Import the scenario module at `path` and return its `scenario` attribute."""
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"scenario not found: {p}")
    spec = importlib.util.spec_from_file_location(f"_eval_scenario_{p.stem}", p)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load scenario module: {p}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sc = getattr(mod, "scenario", None)
    if not isinstance(sc, Scenario):
        raise AttributeError(
            f"{p} must define module-level `scenario: Scenario` (got {type(sc).__name__})"
        )
    return sc


def discover_scenarios(scenarios_dir: str | Path = "evals/scenarios") -> list[Path]:
    """Return all *.py files in scenarios_dir (sorted, ignoring __init__.py)."""
    d = Path(scenarios_dir)
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("*.py") if p.name != "__init__.py")
