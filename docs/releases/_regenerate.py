#!/usr/bin/env python3
"""Regenerate release notes with correct git ranges and dates."""

import subprocess
import re
from pathlib import Path

RELEASES_DIR = Path("docs/releases")

# Patterns for internal/doc-only commits (excluded from main sections)
INTERNAL_PATTERNS = [
    r"^(chore|move|design|plan|review|cleanup|organize|reorganize|mark|merge|Merge|agents|rip|tear|skill|small|followup|follow-up|docs?):",
    r"^Merge\s+(branch|pull|remote)",
    r"^Merge\s+remote",
    r"^(add plan|add design|add docs|add review|add findings|add ticket|add issue)",
    r"^(plan updates?|plan update|plans? update|plans? evals)",
    r"^(eval,\s|eval, planning|eval, design|eval, docs)",
    r"^(review-fixes|review fixes)",
    r"^(plan \d|Phase \d|\d{2}[-.])",
    r"^(TICK-)",
    r"^commit\s+all\s+remaining",
    r"^lotsa\s+docs",
    r"^docs,\s+reviews,\s+evals",
    r"^docs,\s+evals",
    r"^update\s+findings",
    r"^update\s+docs",
    r"^upload\s+design",
    r"^upload\s+plans",
    r"^plans,\s+evals",
    r"^eval,\s+planning",
    r"^new\s+eval$",
    r"^new\s+eval,\s",
    r"^delete\s+old\s+evals",
    r"^completed\s+design\s+docs",
    r"^clean\s+up\s+stale",
    r"^resolve\s+review\s+findings",
    r"^resolve\s+findings",
    r"^organize\s+plans",
    r"^reorganize\s+design",
    r"^reorganize\s+docs",
    r"^reorganize\s+plans",
    r"^mark\s+plan\s+\d",
    r"^mark\s+completed",
    r"^add\s+design\s+docs",
    r"^add\s+new\s+plan",
    r"^add\s+plan\s+",
    r"^add\s+plans?$",
    r"^move\s+to\s+completed",
    r"^move\s+plan",
    r"^move\s+completed",
    r"^move\s+review",
    r"^move\s+active",
]

# UI keywords
UI_KEYWORDS = [
    "ui", "css", "html", "template", "frontend", "sidebar", "mobile",
    "responsive", "layout", "style", "resizable", "streaming", "action.pills",
    "turn.cancel", "auto.resume", "kill.emoji", "roll.math", "thread.tooltip",
    "fluid", "font", "tooltip", "stat.display", "thread.color", "emoji.rebrand",
    "debug.style", "save.picker", "resizable.sidebar", "resizable.gutter",
    "frontend.name", "fix.frontend", "fix.frontend.rule", "fix.templates",
    "fix.suppress", "fix.durability", "fix.tv", "fix.turn", "feat.turn", "feat.tv",
    "fix.turn.500", "feat.turn.seed", "feat.turn.viewer", "fix.turn.viewer",
    "fix.turn.cancel", "fix.turn.persist", "fix.turn.binding", "resizable.drag",
    "sidebar.gutter", "sidebar.collapse", "sidebar.hover", "sidebar.input",
    "mobile.hide", "mobile.center", "mobile.reorder", "mobile.arrow",
    "hold.action", "prevent.scroll", "hide.action.pills", "scroll.reveal",
    "cancel.turn", "server.cancel", "full.revert", "kill.emoji", "arc.emoji",
    "auto.resume.save", "save.auto.resume", "roll.display", "stat.display",
    "gold.dot", "thread.progress", "capitalized.prose", "line.breaks",
    "tag.style", "relative.timestamp", "visible.goal", "save.name", "gear.menu",
    "load.save", "new.game", "always.visible", "save.modal", "save.backend",
    "save.api", "save.discover", "subfolder.save", "ev.toggle",
    "save.picker.discover", "save.picker.toggle",
]

# Eval/tooling keywords
EVAL_KEYWORDS = [
    "eval", "ev.py", "ev/", "ev-checker", "ev-tooling", "ev-debug", "ev.play",
    "ev.checkers", "ev.session", "ev.pacing", "ev.debug", "ev.tooling", "ev.find",
    "ev.find_turn", "checker", "roadmap", "linear", "skill", "rubric", "scenario",
    "pack.gen", "pack.config", "validate_pack", "ev.py",
]


def get_chronological_tags():
    """Get tags in chronological order (oldest first)."""
    result = subprocess.run(
        ["git", "tag", "--sort=creatordate"],
        capture_output=True, text=True, check=True
    )
    return [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]


def get_tag_date(tag):
    """Get creator date for a tag."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ai", tag],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip().split()[0]


def get_commits(from_tag, to_tag):
    """Get commit messages between two tags."""
    if from_tag is None:
        cmd = ["git", "log", "--format=%h %s", to_tag, "--max-count=500"]
    else:
        cmd = ["git", "log", "--format=%h %s", f"{from_tag}..{to_tag}", "--max-count=500"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return [c for c in result.stdout.strip().split("\n") if c.strip()] if result.stdout.strip() else []


def is_internal_commit(message):
    """Check if a commit is internal/doc-only."""
    # Strip hash prefix if present (format: "hash message")
    parts = message.split(" ", 1)
    msg_text = parts[1] if len(parts) == 2 else message
    msg_lower = msg_text.lower()
    for pattern in INTERNAL_PATTERNS:
        if re.search(pattern, msg_lower, re.IGNORECASE):
            return True
    return False


def categorize_commit(message):
    """Categorize a commit into a section based on prefix and keywords."""
    # Strip hash prefix if present (format: "hash message")
    parts = message.split(" ", 1)
    msg_text = parts[1] if len(parts) == 2 else message
    msg_lower = msg_text.lower()
    
    if is_internal_commit(message):
        return None
    
    # Extract prefix
    prefix_match = re.match(r'^(\w+):', msg_lower)
    prefix = prefix_match.group(1) if prefix_match else None
    
    # Prefix-based routing
    if prefix == "fix":
        return "Bug Fixes"
    if prefix == "feat":
        return "What's New"
    if prefix == "refactor":
        return "Engine Changes"
    if prefix == "chore":
        return None
    
    # Keyword-based routing for unprefixed commits
    for kw in EVAL_KEYWORDS:
        if kw in msg_lower:
            return "Eval & Tooling"
    for kw in UI_KEYWORDS:
        if kw in msg_lower:
            return "UI Changes"
    
    # What's New keywords
    if re.search(r"\b(add|implement|introduce|create|new\s+system|new\s+feature|new\s+mechanic|redesign|overhaul|rewrite|build|develop|launch|deliver|ship)\b", msg_lower):
        return "What's New"
    
    return "Engine Changes"


def deduplicate_commits(commits):
    """Remove duplicate commits (same message)."""
    seen = set()
    unique = []
    for commit in commits:
        parts = commit.split(" ", 1)
        if len(parts) == 2:
            msg = parts[1]
            if msg not in seen:
                seen.add(msg)
                unique.append(commit)
        else:
            unique.append(commit)
    return unique


def write_release_notes(version, date, commits):
    """Write release notes for a version."""
    sections = {
        "What's New": [],
        "Engine Changes": [],
        "UI Changes": [],
        "Eval & Tooling": [],
        "Bug Fixes": [],
    }
    
    internal_commits = []
    
    for commit in commits:
        category = categorize_commit(commit)
        if category is None:
            internal_commits.append(commit)
        else:
            sections[category].append(commit)
    
    # Build summary from top "What's New" items
    whats_new_msgs = [c.split(" ", 1)[1] if " " in c else c for c in sections["What's New"][:3]]
    
    if whats_new_msgs:
        summary_parts = []
        for wn in whats_new_msgs:
            clean = wn.split(": ", 1)[-1] if ": " in wn else wn
            clean = re.sub(r"^(Phase \d+:|\d{2}[-.]|fix:|feat:|chore:|refactor:)\s*", "", clean)
            summary_parts.append(clean)
        summary = "This release includes: " + ", ".join(summary_parts) + "."
    else:
        summary = f"Release with {len(commits)} commit(s)."
    
    # Build the release notes
    lines = []
    lines.append(f"# Release {version}")
    lines.append("")
    lines.append(f"Released: {date}")
    lines.append("")
    lines.append("## 📋 Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")
    
    for section_name, emoji in [
        ("What's New", "✨"),
        ("Engine Changes", "🔧"),
        ("UI Changes", "🎨"),
        ("Eval & Tooling", "🛠️"),
        ("Bug Fixes", "🐛"),
    ]:
        items = sections[section_name]
        if items:
            lines.append(f"## {emoji} {section_name}")
            lines.append("")
            for item in items:
                msg = item.split(" ", 1)[1] if " " in item else item
                msg = re.sub(r"^(Phase \d+:|\d{2}[-.]|fix:|feat:|chore:|refactor:|review:|design:|plan:|docs?:)\s*", "", msg)
                lines.append(f"- {msg}")
            lines.append("")
    
    # Full changelog
    lines.append("## 📜 Full Changelog")
    lines.append("")
    lines.append("```")
    for commit in commits:
        if commit.strip():
            lines.append(commit)
    lines.append("```")
    lines.append("")
    
    filepath = RELEASES_DIR / f"{version}.md"
    filepath.write_text("\n".join(lines))
    whats_new = sections["What's New"]
    engine_changes = sections["Engine Changes"]
    ui_changes = sections["UI Changes"]
    eval_tooling = sections["Eval & Tooling"]
    bug_fixes = sections["Bug Fixes"]
    print(f"  {version}: {len(commits)} commits → {filepath} ({len(whats_new)} new, {len(engine_changes)} engine, {len(ui_changes)} ui, {len(eval_tooling)} eval, {len(bug_fixes)} bugs, {len(internal_commits)} internal)")


def main():
    print("Building chronological tag list...")
    chrono_tags = get_chronological_tags()
    print(f"  Found {len(chrono_tags)} tags")
    
    print("Generating release notes...")
    for i, tag in enumerate(chrono_tags):
        prev = chrono_tags[i - 1] if i > 0 else None
        date = get_tag_date(tag)
        commits = get_commits(prev, tag)
        commits = deduplicate_commits(commits)
        write_release_notes(tag, date, commits)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
