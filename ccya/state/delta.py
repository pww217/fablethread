"""State delta application: apply_delta, reconcile_delta (thin wrappers).

Implementation lives in delta_builder.py to break circular dependency.
"""

from __future__ import annotations

import logging
from typing import Any

_log = logging.getLogger(__name__)


def _merge_arc_update(arc: dict[str, Any], au: Any) -> None:
    from ccya.state.delta_builder import _merge_arc_update as _impl
    _log.debug("_merge_arc_update called")
    return _impl(arc, au)


def reconcile_delta(state: dict[str, Any], delta: Any) -> tuple[Any, list[str]]:
    from ccya.state.delta_builder import reconcile_delta as _impl
    if delta is None:
        _log.warning("reconcile_delta received None delta")
    result, warnings = _impl(state, delta)
    if warnings:
        _log.debug("reconcile_delta warnings=%d: %s", len(warnings), "; ".join(warnings[:3]))
    return result, warnings


def apply_delta(
    state: dict[str, Any], delta: Any,
    *, trace_id: str | None = None,
) -> dict[str, Any]:
    from ccya.state.delta_builder import apply_delta as _impl
    if delta is None:
        _log.warning("apply_delta received None delta")
    result = _impl(state, delta, trace_id=trace_id)
    return result
