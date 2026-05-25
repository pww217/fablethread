"""Shared pack-resolution helpers for the eval harness.

Imported by both cli.py and runner.py to avoid circular imports.
"""

from __future__ import annotations

import logging
from pathlib import Path

_log = logging.getLogger(__name__)


def resolve_pack_path(pack_id: str, packs_dirs: list[Path]) -> Path:
    """Find pack_id as a subdirectory of any of the configured packs-dirs.

    Searches each packs-dir in order for a subdirectory named pack_id.
    Raises FileNotFoundError if not found in any directory.
    """
    for pd in packs_dirs:
        candidate = pd / pack_id
        if candidate.is_dir():
            _log.debug("resolve_pack_path pack=%s resolved=%s", pack_id, candidate)
            return candidate
    searched = ", ".join(str(p) for p in packs_dirs)
    raise FileNotFoundError(f"pack {pack_id!r} not found in any of: {searched}")
