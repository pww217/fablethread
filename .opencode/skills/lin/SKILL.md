---
name: lin
description: "Create, triage, scope, and prioritize Linear tickets for the CCYA project."
---

Read the relevant doc below before acting. Docs are the source of truth — this file is only a signpost.

- `docs/linear/new-bugs.md` — create, report, or file a bug ticket
- `docs/linear/triage-bugs.md` — validate, triage, or accept a New bug
- `docs/linear/scope-feature.md` — scope a feature, handle an idea, or move through Backlog/Scoping
- `docs/linear/prioritize.md` — list, sort, group, or decide what to work on
- `plans/completed/linear-reorganization.md` — ticket inventory with all 6 buckets, sub-issues, and statuses
- `AGENTS.md` — status lifecycle, label types, and workflow rules

## CLI invocation

```bash
linearis <command> [args...]
```

- Binary: `/opt/homebrew/bin/linearis` (in PATH, never use `linear`)
- Workdir: always repo root
- Team: `TICK` | Project: `CCYA` | Prefix: `TICK-`

## Intent routing

| If user says ... | Read this doc first |
|---|---|
| `triage`, `validate`, `accepted` | `triage-bugs.md` |
| `new bug`, `create bug`, `report bug`, `file a bug` | `new-bugs.md` |
| `scope`, `scoping`, `feature`, `backlog`, `idea` | `scope-feature.md` |
| `prioritize`, `sort`, `group`, `what to work on` | `prioritize.md` |
| No match | Load all four docs |
