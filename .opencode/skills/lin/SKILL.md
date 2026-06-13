---
name: lin
description: "Create, triage, scope, and prioritize Linear tickets for the CCYA project."
---

Read these repo files before using this skill:
- `docs/linear/new-bugs.md` — create bug tickets, format, area labels, heredoc, duplicates
- `docs/linear/triage-bugs.md` — validate New bugs, append validation, move to Accepted
- `docs/linear/scope-feature.md` — exploratory scoping for feature tickets in Scoping status
- `docs/linear/prioritize.md` — list, sort, group tickets, decide what to work on

## CRITICAL: CLI invocation

**Always use this exact form — no exceptions:**

```bash
linearis <command> [args...]
```

- **Never** use `linear` — the wrapper is unreliable. The actual binary is `linearis`, installed globally at `/opt/homebrew/bin/linearis`.
- **Always** run from the repo root.

## Project constants

| Constant | Value |
|---|---|
| Team | `TICK` |
| Project | `CCYA` |
| Ticket prefix | `TICK-` (auto-increment, e.g., TICK-30) |

All `--team` flags use `TICK`, all `--project` flags use `CCYA`, and ticket IDs are `TICK-#`.

## Intent routing

Match user intent to the appropriate doc:

- `triage`, `validate`, `accepted` → `triage-bugs.md`
- `new bug`, `create bug`, `report bug`, `file a bug` → `new-bugs.md`
- `scope`, `scoping`, `feature`, `backlog` → `scope-feature.md`
- `prioritize`, `prioritise`, `sort`, `group`, `what to work on` → `prioritize.md`
- No matching keyword → load all docs (full reference)

## Key files

| File | Purpose |
|------|------|
| `docs/linear/new-bugs.md` | Create bug tickets, format, area labels, heredoc, duplicates |
| `docs/linear/triage-bugs.md` | Validate New bugs, append validation, move to Accepted |
| `docs/linear/scope-feature.md` | Exploratory scoping for feature tickets in Scoping status |
| `docs/linear/prioritize.md` | List, sort, group tickets, decide what to work on |
| `AGENTS.md` | Global issue tracking conventions |
