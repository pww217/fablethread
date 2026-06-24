#!/usr/bin/env python3
"""Generate roadmap/backlog.md, active.md, done.md and archive-index.md from YAML frontmatter."""
from pathlib import Path
import yaml
import sys
import tempfile
import os
import re
import shutil
from datetime import datetime, timedelta

ROADMAP_DIR = Path("roadmap")
BUGS_DIR = ROADMAP_DIR / "bugs"
FEATURES_DIR = ROADMAP_DIR / "features"
BACKLOG_FILE = ROADMAP_DIR / "backlog.md"
ACTIVE_FILE = ROADMAP_DIR / "active.md"
DONE_FILE = ROADMAP_DIR / "done.md"
ARCHIVE_INDEX_FILE = ROADMAP_DIR / "archive-index.md"

ARCHIVE_DIR = ROADMAP_DIR / "archive"
ARCHIVE_DAYS = 10

STATUS_ORDER = ["idea", "scoping", "up-next", "new", "validated", "done", "canceled"]

# Workflow stage grouping
BACKLOG_STATUSES = {"idea", "new"}
ACTIVE_STATUSES = {"scoping", "up-next", "validated"}
DONE_STATUSES = {"done", "canceled"}

BUCKET_ORDER = ["Balancing", "Extraction", "Tech Debt", "Tooling", "UI", "World Building"]

BUCKET_EMOJIS = {
    "Balancing": "🎯",
    "Extraction": "🔍",
    "Tech Debt": "🔧",
    "Tooling": "🛠️",
    "UI": "🎨",
    "World Building": "🌍",
    "Other": "📦",
}

URGENCY_EMOJIS = {
    1: "🚨",
    2: "❗",
    3: "⚠️",
    4: "❕",
}

SIZE_EMOJIS = {
    "small": "🟢",
    "medium": "🟡🟡",
    "large": "🟠🟠🟠",
    "xlarge": "🔴🔴🔴🔴",
}

URGENCY_LABELS = {1: "Urgent", 2: "High", 3: "Medium", 4: "Low"}

SECTION_MAP = {
    "idea": "Idea",
    "scoping": "Scoping",
    "up-next": "Up-Next",
    "new": "New",
    "validated": "Validated",
    "done": "Done",
    "canceled": "Canceled",
}

PREFIX_RE = re.compile(r'^\[.*?\]\s*')
PRIORITY_RE = re.compile(r'^(1|2|3|4)\. ')


def strip_prefix(title: str) -> str:
    s = PREFIX_RE.sub("", title)
    s = PRIORITY_RE.sub("", s)
    return s.strip()


def get_bucket(labels: list) -> str:
    for lbl in labels:
        if lbl in BUCKET_ORDER:
            return lbl
    return "Other"


def urgency_label(n: int) -> str:
    emoji = URGENCY_EMOJIS.get(n, "")
    label = URGENCY_LABELS.get(n, str(n))
    return f"{emoji} {label}" if emoji else label


def size_label(size: str) -> str:
    emoji = SIZE_EMOJIS.get(size, "")
    return emoji if emoji else "?"


def parse_frontmatter(path: Path) -> dict | None:
    text = path.read_text()
    if not text.startswith("---"):
        print(f"  WARN {path.relative_to('.')} has no frontmatter, skipping", file=sys.stderr)
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        print(f"  WARN {path.relative_to('.')} malformed frontmatter, skipping", file=sys.stderr)
        return None
    try:
        return yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        print(f"  WARN {path.relative_to('.')} frontmatter parse error: {e}", file=sys.stderr)
        return None


def load_entries(directory: Path, is_archive: bool = False) -> list[dict]:
    entries = []
    if not directory.exists():
        return entries
    for f in sorted(directory.glob("*.md")):
        if f.name in ("index.md", "archive-index.md", "backlog.md", "active.md", "done.md"):
            continue
        fm = parse_frontmatter(f)
        if fm is None:
            continue
        fm["_path"] = f
        fm.setdefault("status", "unknown")
        if not is_archive:
            fm.setdefault("urgency", 3)
            fm.setdefault("size", "unknown")
        fm.setdefault("created", "unknown")
        fm.setdefault("title", f.stem.replace("-", " ").title())
        fm.setdefault("labels", [])
        entries.append(fm)
    return entries


def auto_archive(dry_run: bool = False) -> list[dict]:
    """Move done/canceled items older than ARCHIVE_DAYS to archive/."""
    now = datetime.now()
    cutoff = now - timedelta(days=ARCHIVE_DAYS)
    moved = []

    for directory in [BUGS_DIR, FEATURES_DIR]:
        if not directory.exists():
            continue
        for f in sorted(directory.glob("*.md")):
            fm = parse_frontmatter(f)
            if fm is None:
                continue
            status = fm.get("status", "")
            if status not in DONE_STATUSES:
                continue
            created_str = fm.get("created", "")
            if not created_str or created_str == "unknown":
                continue
            # PyYAML may parse dates as datetime.date objects
            if isinstance(created_str, datetime):
                created_date = created_str.date() if hasattr(created_str, "date") else created_str
            elif isinstance(created_str, str):
                try:
                    created_date = datetime.strptime(created_str, "%Y-%m-%d").date()
                except ValueError:
                    continue
            else:
                continue
            if created_date < cutoff.date():
                archive_dest = ARCHIVE_DIR / f.name
                if archive_dest.exists():
                    print(f"  SKIP {f.name}: already in archive", file=sys.stderr)
                    continue
                action = "Would move" if dry_run else "Moving"
                print(f"  {action} {f.relative_to('.')} → archive/{f.name} (done {created_str})", file=sys.stderr)
                if not dry_run:
                    ARCHIVE_DIR.mkdir(exist_ok=True)
                    shutil.move(str(f), str(archive_dest))
                moved.append({"path": f, "name": f.name})

    return moved


def emit_table(lines: list[str], entries: list[dict], show_size: bool) -> None:
    if show_size:
        lines.append("| Title | Urgency | Size | Created |")
        lines.append("|---|---|---|---|")
        for e in entries:
            title = strip_prefix(e.get("title", "Untitled"))
            urg = urgency_label(e.get("urgency", 3))
            size = size_label(e.get("size", "unknown"))
            created = e.get("created", "?")
            lines.append(f"| {title} | {urg} | {size} | {created} |")
    else:
        lines.append("| Title | Created |")
        lines.append("|---|---|")
        for e in entries:
            title = strip_prefix(e.get("title", "Untitled"))
            created = e.get("created", "?")
            lines.append(f"| {title} | {created} |")
    lines.append("")


def write_sections(filepath: Path, entries: list[dict], show_size: bool, status_filter: set | None = None) -> int:
    lines = []
    lines.append("Auto-generated by scripts/generate-roadmap.py. Do not edit manually.")
    lines.append("")

    if not entries:
        lines.append("No items in this stage.")
        lines.append("")
        _write_file(filepath, "\n".join(lines))
        return 0

    if status_filter:
        entries = [e for e in entries if e["status"] in status_filter]
        if not entries:
            lines.append("No items in this stage.")
            lines.append("")
            _write_file(filepath, "\n".join(lines))
            return 0

    # Group by status first, then by bucket within each status
    status_order = ["idea", "scoping", "up-next", "new", "validated", "done", "canceled"]
    status_entries: dict[str, list[dict]] = {}
    for e in entries:
        status_entries.setdefault(e["status"], []).append(e)

    for status in status_order:
        if status not in status_entries:
            continue
        group = status_entries[status]
        section = SECTION_MAP.get(status, status.replace("-", " ").title())
        lines.append(f"## {section}")
        lines.append("")

        bucket_groups: dict[str, list[dict]] = {}
        for e in group:
            bucket = get_bucket(e["labels"])
            bucket_groups.setdefault(bucket, []).append(e)

        for bucket in BUCKET_ORDER:
            g = bucket_groups.pop(bucket, None)
            if g:
                emoji = BUCKET_EMOJIS.get(bucket, "")
                lines.append(f"**{emoji} {bucket}**")
                lines.append("")
                emit_table(lines, g, show_size)

        if bucket_groups:
            for bucket, g in sorted(bucket_groups.items()):
                emoji = BUCKET_EMOJIS.get(bucket, "")
                lines.append(f"**{emoji} {bucket}**")
                lines.append("")
                emit_table(lines, g, show_size)

        lines.append("")

    _write_file(filepath, "\n".join(lines))
    return len(entries)


def _write_file(filepath: Path, content: str) -> None:
    fd, tmp_path = tempfile.mkstemp(dir=ROADMAP_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp_path, filepath)
    except Exception:
        os.unlink(tmp_path)
        raise


def main():
    dry_run = "--dry-run" in sys.argv

    # Auto-archive old done/canceled items
    moved = auto_archive(dry_run=dry_run)
    if moved:
        if dry_run:
            print(f"  [DRY RUN] {len(moved)} item(s) would be archived.", file=sys.stderr)
        else:
            print(f"  Archived {len(moved)} item(s).", file=sys.stderr)

    # Load active entries (bugs + features)
    active_entries = load_entries(BUGS_DIR) + load_entries(FEATURES_DIR)

    # Split into workflow stages
    backlog_entries = [e for e in active_entries if e["status"] in BACKLOG_STATUSES]
    active_stage_entries = [e for e in active_entries if e["status"] in ACTIVE_STATUSES]
    done_entries = [e for e in active_entries if e["status"] in DONE_STATUSES]

    # Sort each group
    for group in [backlog_entries, active_stage_entries, done_entries]:
        group.sort(key=lambda e: (
            BUCKET_ORDER.index(get_bucket(e["labels"])) if get_bucket(e["labels"]) in BUCKET_ORDER else len(BUCKET_ORDER),
            e["urgency"],
            e["created"],
        ))

    # Generate files
    n_backlog = write_sections(BACKLOG_FILE, backlog_entries, show_size=True, status_filter=BACKLOG_STATUSES)
    n_active = write_sections(ACTIVE_FILE, active_stage_entries, show_size=True, status_filter=ACTIVE_STATUSES)
    n_done = write_sections(DONE_FILE, done_entries, show_size=True, status_filter=DONE_STATUSES)

    # Archive index (items physically in archive/)
    archived = load_entries(ARCHIVE_DIR, is_archive=True)
    archived.sort(key=lambda e: (
        BUCKET_ORDER.index(get_bucket(e["labels"])) if get_bucket(e["labels"]) in BUCKET_ORDER else len(BUCKET_ORDER),
        e["created"],
    ))
    n_archive = write_sections(ARCHIVE_INDEX_FILE, archived, show_size=False, status_filter=None)

    print(f"Wrote {BACKLOG_FILE} ({n_backlog} items)", file=sys.stderr)
    print(f"Wrote {ACTIVE_FILE} ({n_active} items)", file=sys.stderr)
    print(f"Wrote {DONE_FILE} ({n_done} items)", file=sys.stderr)
    print(f"Wrote {ARCHIVE_INDEX_FILE} ({n_archive} items)", file=sys.stderr)


if __name__ == "__main__":
    main()
