#!/usr/bin/env python3
"""Create a new roadmap ticket from a high-level summary.

Prompts for ticket type (bug/feature/improvement/eval) and a single
summary field, then generates a properly formatted ticket file with
frontmatter and a minimal body template.

The triage skill will later flesh out urgency, size, labels, and
cross-references.
"""
import re
from datetime import date
from pathlib import Path

ROADMAP_DIR = Path("roadmap")
TYPE_DIRS = {
    "bug": ROADMAP_DIR / "bugs",
    "feature": ROADMAP_DIR / "features",
    "improvement": ROADMAP_DIR / "improvements",
    "eval": ROADMAP_DIR / "evals",
}
TYPE_PREFIX = {
    "bug": "B",
    "feature": "F",
    "improvement": "I",
    "eval": "E",
}


def next_id(typ: str) -> int:
    """Find the next available ticket ID number for the given type."""
    prefix = TYPE_PREFIX[typ]
    directory = TYPE_DIRS[typ]
    max_n = 0
    if directory.exists():
        for f in directory.glob("*.md"):
            m = re.match(rf"^{prefix}-(\d+)", f.stem)
            if m:
                max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def make_slug(summary: str) -> str:
    """Convert a summary string into a kebab-case slug."""
    slug = summary.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug.strip("-")
    # Truncate to ~60 chars
    if len(slug) > 60:
        slug = slug[:57] + "..."
    return slug


def prompt_type() -> str:
    """Interactive prompt for ticket type."""
    valid = {"bug", "feature", "improvement", "eval"}
    while True:
        typ = input("Ticket type (bug/feature/improvement/eval): ").strip().lower()
        if typ in valid:
            return typ
        print(f"Invalid type. Choose from: {', '.join(sorted(valid))}")


def prompt_summary() -> str:
    """Interactive prompt for the high-level summary."""
    print("\nHigh-level summary (what is this ticket about?):")
    summary = input("> ").strip()
    if not summary:
        print("Summary cannot be empty.")
        return prompt_summary()
    return summary


def create_ticket(typ: str, summary: str) -> Path:
    """Create the ticket file and return its path."""
    ticket_id = next_id(typ)
    slug = make_slug(summary)
    title = summary.title() if summary[0:1].islower() else summary
    created = date.today().isoformat()
    prefix = TYPE_PREFIX[typ]
    full_id = f"{prefix}-{ticket_id}"
    directory = TYPE_DIRS[typ]
    filename = f"{full_id}-{slug}.md"
    filepath = directory / filename

    # Ensure directory exists
    directory.mkdir(parents=True, exist_ok=True)

    content = f"""---
title: "{title}"
status: new
urgency: 3
size: medium
created: {created}
ticket_id: {full_id}
labels:
  - other
---

## Problem

{summary}
"""

    filepath.write_text(content)
    return filepath


def main():
    typ = prompt_type()
    summary = prompt_summary()
    filepath = create_ticket(typ, summary)
    print(f"\nCreated: {filepath}")
    print(f"Ticket ID: {filepath.stem}")
    print("\nNext steps:")
    print("  1. Edit the ticket body to flesh out details")
    print("  2. Run 'make roadmap' to regenerate indices")


if __name__ == "__main__":
    main()
