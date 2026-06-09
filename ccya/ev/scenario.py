from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_log = logging.getLogger(__name__)


@dataclass
class TurnAssert:
    stream: str
    field: str
    expected: str | None = None
    min_amount: int | None = None


@dataclass
class ScenarioTurn:
    input: str
    expects: list[str] = field(default_factory=list)
    asserts: list[TurnAssert] = field(default_factory=list)


@dataclass
class Scenario:
    id: str
    pack: str
    description: str
    turns: list[ScenarioTurn]
    seed_overrides: dict[str, Any] = field(default_factory=dict)


def load_scenario(path: Path) -> Scenario:
    text = path.read_text()
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping, got {type(data).__name__}")

    _require(data, "id", str, path)
    _require(data, "pack", str, path)
    _require(data, "description", str, path)
    _require(data, "turns", list, path)

    turns = []
    for i, turn_data in enumerate(data["turns"]):
        if not isinstance(turn_data, dict):
            raise ValueError(f"{path}: turn {i} must be a mapping")
        _require(turn_data, "input", str, path, f"turn {i}")

        asserts = []
        for j, a in enumerate(turn_data.get("asserts", [])):
            if not isinstance(a, dict):
                raise ValueError(f"{path}: turn {i}, assert {j} must be a mapping")
            _require(a, "stream", str, path, f"turn {i}, assert {j}")
            _require(a, "field", str, path, f"turn {i}, assert {j}")
            asserts.append(TurnAssert(
                stream=a["stream"],
                field=a["field"],
                expected=a.get("expected"),
                min_amount=a.get("min_amount"),
            ))

        expects = turn_data.get("expects", [])
        if isinstance(expects, str):
            expects = [expects]
        elif not isinstance(expects, list):
            expects = []

        turns.append(ScenarioTurn(
            input=turn_data["input"],
            expects=[str(e) for e in expects],
            asserts=asserts,
        ))

    return Scenario(
        id=data["id"],
        pack=data["pack"],
        description=data["description"],
        seed_overrides=data.get("seed_overrides", {}),
        turns=turns,
    )


def discover_scenarios(scenarios_dir: str = "evals/scenarios") -> list[Path]:
    d = Path(scenarios_dir)
    if not d.is_dir():
        return []
    scenarios = sorted(p for p in d.glob("*.yaml") if p.name != "__init__.py")
    _log.info("scenario: discovered %d scenarios in %s", len(scenarios), scenarios_dir)
    return scenarios


def _require(data: dict[str, Any], key: str, expected_type: type, path: Path, context: str = "") -> None:
    if key not in data:
        ctx = f" ({context})" if context else ""
        raise ValueError(f"{path}: missing required field '{key}'{ctx}")
    if not isinstance(data[key], expected_type):
        ctx = f" ({context})" if context else ""
        raise ValueError(f"{path}: field '{key}' must be {expected_type.__name__}, got {type(data[key]).__name__}{ctx}")
