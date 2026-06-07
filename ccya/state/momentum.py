"""Momentum application from rules bands."""

from __future__ import annotations

import logging
from typing import Any

from ccya.rules import MOMENTUM_DELTA

_log = logging.getLogger(__name__)

MOMENTUM_MIN: int = -3
MOMENTUM_MAX: int = 3


def apply_momentum(state: dict[str, Any], band: str) -> None:
    """Update pc.momentum deterministically from a rules band.

    Clamped to [-3, +3]. Mutates state in place.
    """
    pc = state.setdefault("pc", {})
    current = int(pc.get("momentum", 0))
    delta = MOMENTUM_DELTA.get(band, 0)
    if band not in MOMENTUM_DELTA:
        _log.warning("apply_momentum unrecognized band=%s delta=0", band)

    # MB-4: depth-based catch-up acceleration at -3 or below
    recovery_delta = delta
    if current < -2 and band in ("success", "crit_success"):
        deeper_delta = 2 if band == "success" else 3
        _log.debug("apply_momentum MB-4 deep_recovery momentum=%d band=%s delta=%d→%d",
                   current, band, delta, deeper_delta)
        recovery_delta = deeper_delta

    new_val = max(MOMENTUM_MIN, min(MOMENTUM_MAX, current + recovery_delta))
    pc["momentum"] = new_val
    _log.debug("apply_momentum band=%s current=%d delta=%d new=%d", band, current, delta, new_val)
