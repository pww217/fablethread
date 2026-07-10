#!/usr/bin/env python3
"""Create a new roadmap ticket from a high-level summary.

Usage:
  new-ticket.py <type> <summary> [--slug SLUG] [--status STATUS]

Prompts for ticket type and summary interactively, or accepts them as
positional arguments. Optionally accepts --slug and --status to override
defaults.

Generates a ticket file from the matching template in
roadmap/templates/<type>.md with frontmatter filled in.
"""
import argparse
import re
from datetime import date
from pathlib import Path

ROADMAP_DIR = Path("roadmap")
TEMPLATE_DIR = ROADMAP_DIR / "templates"
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
DEFAULT_STATUS = {
    "bug": "new",
    "feature": "idea",
    "improvement": "idea",
    "eval": "new",
}


def next_id(typ: str) -> int:
    """Find the next available ticket ID number for the given type.

    Always uses the highest existing number + 1, never fills gaps.
    """
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


def load_template(typ: str) -> str:
    """Load the template for the given ticket type."""
    template_path = TEMPLATE_DIR / f"{typ}.md"
    return template_path.read_text()


def extract_default_status(template: str) -> str:
    """Extract the default status value from a template file."""
    in_frontmatter = False
    for line in template.splitlines():
        if line == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter and line.startswith("status:"):
            return line.split(":", 1)[1].strip()
    return "new"


def apply_frontmatter(template: str, title: str, status: str, created: str, ticket_id: str) -> str:
    """Replace placeholder frontmatter values with actual values."""
    lines = template.splitlines()
    result = []
    in_frontmatter = False
    for line in lines:
        if line == "---":
            result.append(line)
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            if line.startswith("title:"):
                result.append(f'title: "{title}"')
            elif line.startswith("status:"):
                result.append(f"status: {status}")
            elif line.startswith("created:"):
                result.append(f"created: {created}")
            elif line.startswith("ticket_id:"):
                result.append(f"ticket_id: {ticket_id}")
            else:
                result.append(line)
        else:
            result.append(line)
    return "\n".join(result)


def create_ticket(typ: str, summary: str, slug: str | None = None, status: str | None = None) -> Path:
    """Create the ticket file and return its path."""
    ticket_id = next_id(typ)
    slug = slug or make_slug(summary)
    title = summary.title() if summary[0:1].islower() else summary
    created = date.today().isoformat()
    prefix = TYPE_PREFIX[typ]
    full_id = f"{prefix}-{ticket_id}"
    directory = TYPE_DIRS[typ]
    filename = f"{full_id}-{slug}.md"
    filepath = directory / filename

    directory.mkdir(parents=True, exist_ok=True)

    template = load_template(typ)

    # Determine status: explicit arg > template default > hardcoded fallback
    if status is None:
        status = extract_default_status(template)

    content = apply_frontmatter(template, title, status, created, full_id)

    filepath.write_text(content)
    return filepath


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


def main():
    parser = argparse.ArgumentParser(description="Create a new roadmap ticket")
    parser.add_argument("type", nargs="?", help="Ticket type (bug/feature/improvement/eval)")
    parser.add_argument("summary", nargs="?", help="High-level summary")
    parser.add_argument("--slug", help="Custom slug (auto-generated from summary if omitted)")
    parser.add_argument("--status", help="Ticket status (defaults to template default)")
    args = parser.parse_args()

    # Interactive mode if no args provided
    if not args.type or not args.summary:
        typ = prompt_type()
        summary = prompt_summary()
        slug = None
        status = None
    else:
        typ = args.type
        summary = args.summary
        slug = args.slug
        status = args.status

    filepath = create_ticket(typ, summary, slug=slug, status=status)
    print(f"\nCreated: {filepath}")
    print(f"Ticket ID: {filepath.stem}")
    print("\nNext steps:")
    print("  1. Edit the ticket body to flesh out details")
    print("  2. Run 'make roadmap' to regenerate indices")


if __name__ == "__main__":
    main()
