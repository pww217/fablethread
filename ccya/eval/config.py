"""Eval-harness configuration loading."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_log = logging.getLogger(__name__)


@dataclass
class InferenceConfig:
    temperature_override: float | None = None
    cache: bool = False


@dataclass
class TraceConfig:
    dedup_immutable_sections: bool = True
    state_as_diff: bool = True


@dataclass
class JudgeSpec:
    id: str
    rubric_path: str
    model: str = ""
    temperature: float = 0.3
    timeout_s: float | None = None
    max_tokens: int = 64000


@dataclass
class JudgesConfig:
    enabled: bool = True
    specs: list[JudgeSpec] = field(default_factory=list)
    trace: TraceConfig = field(default_factory=TraceConfig)


@dataclass
class ReportConfig:
    token_warn_pct: float = 10.0
    token_fail_pct: float = 25.0
    flag_at_top: list[str] = field(default_factory=list)


@dataclass
class LoggingConfig:
    level: str = "WARNING"


@dataclass
class _JudgeConfigBackCompat:
    """Synthetic object providing backward-compat attributes for code that accesses eval_cfg.judge.*."""
    _specs: list[JudgeSpec]
    _trace: TraceConfig
    _enabled: bool = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def model(self) -> str:
        return self._specs[0].model if self._specs else ""

    @property
    def rubric_path(self) -> str:
        return self._specs[0].rubric_path if self._specs else "evals/rubrics/default.md"

    @property
    def temperature(self) -> float:
        return self._specs[0].temperature if self._specs else 0.3

    @property
    def timeout_s(self) -> float | None:
        return self._specs[0].timeout_s if self._specs else None

    @property
    def max_tokens(self) -> int:
        return self._specs[0].max_tokens if self._specs else 64000

    @property
    def trace(self) -> TraceConfig:
        return self._trace


@dataclass
class EvalConfig:
    default_pack: str = "eval-pack"
    default_scenario: str = "full_cycle"
    pack_dirs: list[str] = field(default_factory=lambda: ["evals/packs", "packs/default", "packs/custom"])
    default_save_root: str = "~/.cache/ccya-eval"
    runs_dir: str = "evals/runs"
    num_turns: int = 10
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    judges: JudgesConfig = field(default_factory=JudgesConfig)
    report: ReportConfig = field(default_factory=ReportConfig)

    @property
    def judge(self) -> _JudgeConfigBackCompat:
        """Back-compat alias for code that accesses eval_cfg.judge.model, .rubric_path, etc."""
        return _JudgeConfigBackCompat(
            _specs=self.judges.specs,
            _trace=self.judges.trace,
            _enabled=self.judges.enabled,
        )


_DEFAULT_PATH = Path("evals/config.yaml")


def _parse_judge_spec(raw: dict[str, Any], spec_id: str) -> JudgeSpec:
    model_val = raw.get("model")
    return JudgeSpec(
        id=spec_id,
        rubric_path=str(raw.get("rubric_path", "evals/rubrics/default.md")),
        model=model_val if model_val else "",
        temperature=float(raw.get("temperature", 0.3)),
        timeout_s=raw.get("timeout_s"),
        max_tokens=int(raw.get("max_tokens", 64000)),
    )


def load_eval_config(path: str | Path | None = None) -> EvalConfig:
    p = Path(path) if path else _DEFAULT_PATH
    if not p.exists():
        raise FileNotFoundError(f"eval config not found: {p}")
    with open(p) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}
    _log.debug("load_eval_config path=%s num_turns=%d judges=%d", p, raw.get("num_turns"), len(raw.get("judges", {}).get("specs") or []))

    inf_raw = raw.get("inference") or {}
    rpt_raw = raw.get("report") or {}
    log_raw = raw.get("logging") or {}

    # Support both old flat `judge:` and new `judges:` with a `specs:` list.
    judges_raw = raw.get("judges") or {}
    judge_raw = raw.get("judge") or {}  # legacy fallback

    trace_source = judges_raw.get("trace") or judge_raw.get("trace") or {}
    trace_cfg = TraceConfig(
        dedup_immutable_sections=bool(trace_source.get("dedup_immutable_sections", True)),
        state_as_diff=bool(trace_source.get("state_as_diff", True)),
    )

    specs: list[JudgeSpec] = []
    if "specs" in judges_raw:
        for spec_raw in judges_raw["specs"]:
            specs.append(_parse_judge_spec(spec_raw, spec_raw.get("id", "unknown")))
    elif judge_raw:
        # Legacy single-judge config: wrap as single spec with id="default"
        specs.append(_parse_judge_spec(judge_raw, "default"))

    # Handle None from YAML (null → default True)
    _enabled = judges_raw.get("enabled")
    if _enabled is None:
        _enabled = judge_raw.get("enabled", True)
    enabled = bool(_enabled)

    return EvalConfig(
        default_pack=str(raw.get("default_pack", "eval-pack")),
        default_scenario=str(raw.get("default_scenario", "full_cycle")),
        pack_dirs=list(raw.get("pack_dirs") or ["evals/packs", "packs/default", "packs/custom"]),
        default_save_root=str(raw.get("default_save_root", "~/.cache/ccya-eval")),
        runs_dir=str(raw.get("runs_dir", "evals/runs")),
        num_turns=int(raw.get("num_turns", 10)),
        logging=LoggingConfig(level=str(log_raw.get("level", "WARNING"))),
        inference=InferenceConfig(
            temperature_override=inf_raw.get("temperature_override"),
            cache=bool(inf_raw.get("cache", False)),
        ),
        judges=JudgesConfig(
            enabled=enabled,
            specs=specs,
            trace=trace_cfg,
        ),
        report=ReportConfig(
            token_warn_pct=float(rpt_raw.get("token_warn_pct", 10.0)),
            token_fail_pct=float(rpt_raw.get("token_fail_pct", 25.0)),
            flag_at_top=list(rpt_raw.get("flag_at_top") or []),
        ),
    )
