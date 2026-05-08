"""Eval-harness configuration loading."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class InferenceConfig:
    temperature_override: float | None = None
    cache: bool = False


@dataclass
class TraceConfig:
    dedup_immutable_sections: bool = True
    state_as_diff: bool = True


@dataclass
class JudgeConfig:
    enabled: bool = True
    model: str | None = None
    rubric_path: str = "evals/rubrics/default.md"
    temperature: float = 0.3
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
class EvalConfig:
    default_pack: str = "eval-pack"
    default_save_root: str = "~/.cache/ccya-eval"
    runs_dir: str = "evals/runs"
    num_turns: int = 10
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    judge: JudgeConfig = field(default_factory=JudgeConfig)
    report: ReportConfig = field(default_factory=ReportConfig)


_DEFAULT_PATH = Path("evals/config.yaml")


def load_eval_config(path: str | Path | None = None) -> EvalConfig:
    p = Path(path) if path else _DEFAULT_PATH
    if not p.exists():
        raise FileNotFoundError(f"eval config not found: {p}")
    with open(p) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    inf_raw = raw.get("inference") or {}
    jdg_raw = raw.get("judge") or {}
    rpt_raw = raw.get("report") or {}
    log_raw = raw.get("logging") or {}

    trace_raw = jdg_raw.get("trace") or {}
    trace_cfg = TraceConfig(
        dedup_immutable_sections=bool(trace_raw.get("dedup_immutable_sections", True)),
        state_as_diff=bool(trace_raw.get("state_as_diff", True)),
    )

    return EvalConfig(
        default_pack=str(raw.get("default_pack", "eval-pack")),
        default_save_root=str(raw.get("default_save_root", "~/.cache/ccya-eval")),
        runs_dir=str(raw.get("runs_dir", "evals/runs")),
        num_turns=int(raw.get("num_turns", 10)),
        logging=LoggingConfig(
            level=str(log_raw.get("level", "WARNING")),
        ),
        inference=InferenceConfig(
            temperature_override=inf_raw.get("temperature_override"),
            cache=bool(inf_raw.get("cache", False)),
        ),
        judge=JudgeConfig(
            enabled=bool(jdg_raw.get("enabled", True)),
            model=jdg_raw.get("model"),
            rubric_path=str(jdg_raw.get("rubric_path", "evals/rubrics/default.md")),
            temperature=float(jdg_raw.get("temperature", 0.3)),
            trace=trace_cfg,
        ),
        report=ReportConfig(
            token_warn_pct=float(rpt_raw.get("token_warn_pct", 10.0)),
            token_fail_pct=float(rpt_raw.get("token_fail_pct", 25.0)),
            flag_at_top=list(rpt_raw.get("flag_at_top") or []),
        ),
    )
