"""Chronicle and events I/O."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

_TURN_HEADER = re.compile(r"^## Turn (\d+) — (.+)$", re.MULTILINE)


def append_event(save_dir: Path, event: dict[str, Any]) -> None:
    path = save_dir / "events.jsonl"
    _log.debug("append_event path=%s keys=%s", path, list(event.keys()))
    save_dir.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(event, default=str) + "\n")


def append_chronicle(save_dir: Path, text: str) -> None:
    path = save_dir / "chronicle.md"
    _log.debug("append_chronicle path=%s chars=%d", path, len(text))
    save_dir.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write("\n" + text)



def load_recent_turns(save_dir: Path, n: int) -> list[dict[str, Any]]:
    path = save_dir / "events.jsonl"
    if not path.exists():
        return []
    lines = path.read_text().strip().split("\n")
    events = []
    for line in lines:
        if line.strip():
            events.append(json.loads(line))
    return events[-n:] if n > 0 else []


def load_last_narration(
    save_dir: Path,
    n: int,
) -> list[dict[str, Any]]:
    """Return up to the last n turns from chronicle.md."""
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
        _log.debug("remove_last_event path=%s not found", path)
        return False
    lines = path.read_text().strip().split("\n")
    lines = [line for line in lines if line.strip()]
    if not lines:
        return False
    lines = lines[:-1]
    path.write_text("\n".join(lines) + "\n" if lines else "")
    _log.debug("remove_last_event path=%s removed=True", path)
    return True


def remove_last_chronicle_turn(save_dir: Path) -> bool:
    """Remove the last ## Turn N — ... section from chronicle.md. Returns True if removed."""
    path = save_dir / "chronicle.md"
    if not path.exists():
        _log.debug("remove_last_chronicle_turn path=%s not found", path)
        return False
    text = path.read_text()
    matches = list(_TURN_HEADER.finditer(text))
    if not matches:
        return False
    prev_end = matches[-2].end() if len(matches) >= 2 else 0
    new_text = text[:prev_end]
    path.write_text(new_text)
    _log.debug("remove_last_chronicle_turn path=%s removed=True", path)
    return True
