"""State delta application: apply_delta, reconcile_delta (thin wrappers).

Implementation lives in delta_builder.py to break circular dependency.
"""

from __future__ import annotations

from typing import Any


def _merge_arc_update(arc: dict[str, Any], au: Any) -> None:
    from ccya.state.delta_builder import _merge_arc_update as _impl
    return _impl(arc, au)


def reconcile_delta(state: dict[str, Any], delta: Any) -> tuple[Any, list[str]]:
    from ccya.state.delta_builder import reconcile_delta as _impl
    return _impl(state, delta)


def apply_delta(
    state: dict[str, Any], delta: Any, *, recent_events_max: int = 20, current_turn_no: int | None = None,
) -> tuple[dict[str, Any], bool]:
    from ccya.state.delta_builder import apply_delta as _impl
    return _impl(state, delta, recent_events_max=recent_events_max, current_turn_no=current_turn_no)
