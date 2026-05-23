"""Load engine-design context from docs/architecture/ sub-docs for the judge prompt.

Aggregates all architecture subdocuments (excluding harness-specific and UI docs)
into a single string that serves as ENGINE DESIGN REFERENCE context in judge prompts.
This replaces the old single-file ARCHITECTURE.md which was split into focused
subdocuments under docs/architecture/.
"""

from __future__ import annotations

import logging
from pathlib import Path

_log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ARCH_DIR = REPO_ROOT / "docs" / "architecture"

# Docs that are NOT engine design reference (harness itself, UI, etc.)
_EXCLUDED_DOCS = frozenset(("eval-harness.md", "turn-viewer-ui.md"))


def load_architecture_context() -> str:
    """Return aggregated architecture context from all sub-docs.

    Wraps the content in a clear ## ENGINE DESIGN REFERENCE header so the judge
    knows it's prepended context (not part of the rubric body).
    """
    if not _ARCH_DIR.is_dir():
        _log.warning("architecture context: %s does not exist", _ARCH_DIR)
        return ""

    parts: list[str] = []
    doc_files = sorted(_ARCH_DIR.glob("*.md"))

    for doc_path in doc_files:
        if doc_path.name in _EXCLUDED_DOCS:
            continue
        try:
            text = doc_path.read_text()
            # Strip the filename header (first line) to avoid redundancy when combined
            lines = text.splitlines()
            content_start = 1 if lines and lines[0].startswith("# ") else 0
            parts.append(f"## {doc_path.stem}\n\n")
            parts.extend(lines[content_start:])
            parts.append("\n---\n\n")
        except Exception as exc:
            _log.warning("architecture context: failed to read %s: %s", doc_path, exc)

    if not parts:
        return ""

    body = "\n".join(parts).strip()
    return (
        "---\n\n"
        "# ENGINE DESIGN REFERENCE (read this first — it is what the engine is supposed to do)\n\n"
        "The following is extracted from the project's architecture subdocuments under "
        "docs/architecture/. It defines the 5-pipeline engine you are judging. Use it to "
        "understand which pipeline owns which mechanic, where data flows, and what the "
        "design intent is. When you find something the implementation does that contradicts "
        "this design, call it out as a mechanical failure.\n\n"
        f"{body}\n\n---\n\n"
    )
