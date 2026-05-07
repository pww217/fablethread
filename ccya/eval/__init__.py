"""ccya eval harness.

Tier 2 of the eval system: live-LLM in-process driver, single judge, single scenario.
See ccya/plans/p3-inference/eval-harness.md.
"""

from ccya.eval import engine_mirror as engine_mirror
from ccya.eval.config import EvalConfig, load_eval_config
from ccya.eval.judge import JudgeResult, build_trace, parse_judge_response, run_judge
from ccya.eval.report import generate_report
from ccya.eval.runner import (
    RunResult,
    TurnRecord,
    find_previous_run,
    load_run_result,
    run_scenario,
)
from ccya.eval.scenario import Scenario, Turn, TurnAssert, discover_scenarios, load_scenario

__all__ = [
    "EvalConfig",
    "JudgeResult",
    "RunResult",
    "Scenario",
    "Turn",
    "TurnAssert",
    "TurnRecord",
    "build_trace",
    "discover_scenarios",
    "engine_mirror",
    "find_previous_run",
    "generate_report",
    "load_eval_config",
    "load_run_result",
    "load_scenario",
    "parse_judge_response",
    "run_judge",
    "run_scenario",
]
