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
    personality: str = "custom"


@dataclass
class PromptEvalScenario:
    id: str
    description: str
    save: str
    turn: int
    stream: str = "scene"
    model: str | None = None
    temp: float | None = None
    checks: list[PromptCheck] = field(default_factory=list)


@dataclass
class PromptCheck:
    type: str
    extra: dict[str, Any] = field(default_factory=dict)


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


def load_prompt_scenario(path: Path) -> PromptEvalScenario:
    text = path.read_text()
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping, got {type(data).__name__}")

    _require(data, "id", str, path)
    _require(data, "description", str, path)
    _require(data, "save", str, path)
    _require(data, "turn", int, path)

    stream = data.get("stream", "inventory")
    if not isinstance(stream, str):
        raise ValueError(f"{path}: field 'stream' must be str, got {type(data['stream']).__name__}")

    model = data.get("model")
    if model is not None and not isinstance(model, str):
        raise ValueError(f"{path}: field 'model' must be str or null")

    temp = data.get("temp")
    if temp is not None and not isinstance(temp, (int, float)):
        raise ValueError(f"{path}: field 'temp' must be float or null")

    checks_raw = data.get("checks", [])
    if not isinstance(checks_raw, list):
        raise ValueError(f"{path}: field 'checks' must be a list")

    checks = []
    for check_item in checks_raw:
        if isinstance(check_item, str):
            checks.append(PromptCheck(type=check_item))
        elif isinstance(check_item, dict):
            if len(check_item) != 1:
                raise ValueError(f"{path}: each check mapping must have exactly one key")
            checker_type = next(iter(check_item))
            checker_value = check_item[checker_type]
            extra = {}
            if checker_type == "golden_match":
                if not isinstance(checker_value, str):
                    raise ValueError(f"{path}: golden_match value must be a string path")
                extra["golden_path"] = checker_value
            elif checker_type == "extraction_format":
                if isinstance(checker_value, dict):
                    extra["stream"] = checker_value.get("stream", "scene")
                elif isinstance(checker_value, str):
                    extra["stream"] = checker_value
            checks.append(PromptCheck(type=checker_type, extra=extra))
        else:
            raise ValueError(f"{path}: check must be a string or mapping, got {type(check_item).__name__}")

    return PromptEvalScenario(
        id=data["id"],
        description=data["description"],
        save=data["save"],
        turn=data["turn"],
        stream=stream,
        model=model,
        temp=float(temp) if temp is not None else None,
        checks=checks,
    )


def discover_scenarios(scenarios_dir: str = "packs") -> list[Path]:
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
