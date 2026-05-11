"""Chronicle and events I/O."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_TURN_HEADER = re.compile(r"^## Turn (\d+) — (.+)$", re.MULTILINE)
_COMPACTED_HEADER = re.compile(r"^## COMPACTED$", re.MULTILINE)


def append_event(save_dir: Path, event: dict[str, Any]) -> None:
    path = save_dir / "events.jsonl"
    with open(path, "a") as f:
        f.write(json.dumps(event, default=str) + "\n")


def append_chronicle(save_dir: Path, text: str) -> None:
    path = save_dir / "chronicle.md"
    with open(path, "a") as f:
        f.write("\n" + text)


def load_chronicle_tail(
    save_dir: Path, max_tokens: int, skip_last_n_turns: int = 0
) -> str:
    path = save_dir / "chronicle.md"
    if not path.exists():
        return ""
    text = path.read_text()
    if skip_last_n_turns > 0:
        matches = list(_TURN_HEADER.finditer(text))
        if matches:
            cut_at = (
                matches[-skip_last_n_turns].start()
                if skip_last_n_turns <= len(matches)
                else 0
            )
            text = text[:cut_at]
    # Only return the COMPACTED section, not the raw prose for non-compacted turns.
    # The non-compacted turns are provided separately via recent_turns.
    compacted_match = _COMPACTED_HEADER.search(text)
    if compacted_match:
        compacted_text = text[compacted_match.end():]
        # Find where the first non-compacted turn header starts after COMPACTED
        turn_matches = list(_TURN_HEADER.finditer(compacted_text))
        if turn_matches:
            compacted_text = compacted_text[:turn_matches[0].start()]
        words = compacted_text.split()
        if len(words) <= max_tokens:
            return "## COMPACTED\n" + compacted_text
        return "## COMPACTED\n" + " ".join(words[-max_tokens:])
    return ""


def load_recent_events(save_dir: Path, n: int) -> list[dict[str, Any]]:
    path = save_dir / "events.jsonl"
    if not path.exists():
        return []
    lines = path.read_text().strip().split("\n")
    events = []
    for line in lines:
        if line.strip():
            events.append(json.loads(line))
    return events[-n:] if n > 0 else []


def load_recent_chronicle_turns(
    save_dir: Path,
    n: int,
    *,
    min_turn_exclusive: int = 0,
) -> list[dict[str, Any]]:
    """Return up to the last n turns from chronicle.md with turn > min_turn_exclusive."""
    path = save_dir / "chronicle.md"
    if not path.exists() or n <= 0:
        return []
    text = path.read_text()
    matches = list(_TURN_HEADER.finditer(text))
    if not matches:
        return []
    turns: list[dict[str, Any]] = []
    for i, m in enumerate(matches):
        turn_num = int(m.group(1))
        if turn_num <= min_turn_exclusive:
            continue
        turn_input = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        narrative = text[body_start:body_end].strip()
        turns.append({"turn": turn_num, "input": turn_input, "narrative": narrative})
    return turns[-n:] if n > 0 else []


def remove_last_event(save_dir: Path) -> bool:
    """Remove the last line from events.jsonl. Returns True if a line was removed."""
    path = save_dir / "events.jsonl"
    if not path.exists():
        return False
    lines = path.read_text().strip().split("\n")
    lines = [line for line in lines if line.strip()]
    if not lines:
        return False
    lines = lines[:-1]
    path.write_text("\n".join(lines) + "\n" if lines else "")
    return True


def remove_last_chronicle_turn(save_dir: Path) -> bool:
    """Remove the last ## Turn N — ... section from chronicle.md. Returns True if removed."""
    path = save_dir / "chronicle.md"
    if not path.exists():
        return False
    text = path.read_text()
    matches = list(_TURN_HEADER.finditer(text))
    if not matches:
        return False
    prev_end = matches[-2].end() if len(matches) >= 2 else 0
    new_text = text[:prev_end]
    path.write_text(new_text)
    return True
