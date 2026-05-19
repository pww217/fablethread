"""Load engine-design context from docs/ARCHITECTURE.md for the judge prompt.

Extracts the substring between the literal HTML comment markers
<!-- EVAL_CONTEXT_START --> and <!-- EVAL_CONTEXT_END -->.
"""

from __future__ import annotations

import logging
from pathlib import Path

_log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ARCH_PATH = REPO_ROOT / "docs" / "ARCHITECTURE.md"
_START = "<!-- EVAL_CONTEXT_START -->"
_END = "<!-- EVAL_CONTEXT_END -->"


def load_architecture_context() -> str:
    """Return the engine-design slice of ARCHITECTURE.md, or empty string on failure.

    Wraps the slice in a clear ## ENGINE DESIGN REFERENCE header so the judge
    knows it's prepended context (not part of the rubric body).
    """
    if not _ARCH_PATH.exists():
        _log.warning("architecture context: %s does not exist", _ARCH_PATH)
        return ""
    text = _ARCH_PATH.read_text()
    s = text.find(_START)
    e = text.find(_END)
    if s < 0 or e < 0 or e <= s:
        _log.warning("architecture context: markers not found or malformed in %s", _ARCH_PATH)
        return ""
    body = text[s + len(_START):e].strip()
    return (
        "---\n\n"
        "# ENGINE DESIGN REFERENCE (read this first — it is what the engine is supposed to do)\n\n"
        "The following is extracted verbatim from the project's ARCHITECTURE.md "
        "between the EVAL_CONTEXT markers. It defines the 5-pipeline engine you are "
        "judging. Use it to understand which pipeline owns which mechanic, where "
        "data flows, and what the design intent is. When you find something the "
        "implementation does that contradicts this design, call it out as a "
        "mechanical failure.\n\n"
        f"{body}\n\n---\n\n"
    )
