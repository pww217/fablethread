---
name: release
description: Create a version tag and release notes for everything since the last release
---

Purpose: Tag the current HEAD with the next incremental version and produce release notes covering all commits since the last tag.

## Version Bumping

Tags follow `0.X.Y` format (major.minor.patch). Determine the bump:

- **Patch (0.X.Z→Z+1):** Bug fixes only, no new features or breaking changes
- **Minor (0.X.Y→X+1.0):** New features, new mechanics, notable improvements
- **Major (0.X.Y→X+1.0.0):** Breaking changes, major refactors that change how the game works

When in doubt, bump minor. This is pre-1.0 — everything is somewhat breaking.

## Release Notes Format

Write release notes to `docs/releases/0.X.Y.md` (create the directory if needed).

**Structure:**

```markdown
# Release 0.X.Y

Released: YYYY-MM-DD

## Summary

2-3 sentence overview of what this release is about.

## Highlights

- Major change 1
- Major change 2
- Major change 3

## Mechanical Changes

- Engine/system change with brief description
- Another engine/system change

## UI / Frontend

- UI change
- Another UI change

## Eval / Tooling

- Tooling change

## Bug Fixes

- Fix description

## Documentation

- Doc changes (brief, only notable ones)

## Full Changelog

Full list of commits since last release (git log format).
```

**Guidelines:**
- Group commits by category (mechanical, UI, eval, fixes, docs)
- Identify the 3-5 most impactful changes for Highlights
- Mechanical changes = anything that changes game behavior, engine logic, or data models
- UI/Frontend = anything touching the web interface
- Eval/Tooling = ev.py, checkers, skills, workflows
- Bug Fixes = fixes that aren't major mechanical changes
- Documentation = only notable doc additions/reorganizations
- Full Changelog at the bottom is the raw git log
- Use emojis sparingly (max 2-3 total, only for section headers or highlights)
- Keep descriptions concise — one line per item

## Execution

1. **Find the last tag:** `git tag --sort=-v:refname | head -1`
2. **Determine next version** per the bump rules above
3. **Tag it:** `git tag -a 0.X.Y -m "Release 0.X.Y"` (then push)
4. **Get the log:** `git log --oneline <last_tag>..HEAD`
5. **Categorize commits** into the sections above
6. **Write the release notes** to `docs/releases/0.X.Y.md`
7. **Commit the release notes** (they are part of the release)
8. **Create a GitHub release:** `gh release create 0.X.Y --title "Release 0.X.Y" --notes-file docs/releases/0.X.Y.md` (then push the release)
