---
name: linear
description: Create and manage Linear tickets for the CCYA project. Team: PW (Peter). Labels: Bug, Feature, Improvement.
---

Read these repo files before using this skill:
- `docs/linear/write.md` — issue creation, heredoc pattern, full-cycle workflow
- `docs/linear/read.md` — list, search, read commands
- `docs/linear/update.md` — status transitions, resolution comments, archiving

## CRITICAL: CLI invocation

**Always use this exact form — no exceptions:**

```bash
linearis <command> [args...]
```

- **Never** use `linear` — the wrapper is unreliable. The actual binary is `linearis`.
- **Always** run from the repo root.

## CRITICAL: Descriptions with inline code

**The CLI passes `--description` through the shell.** Backticks, `()`, glob `*`, and `>` get interpreted by zsh and break creation.

**Workaround for descriptions that need inline code or special characters:**

```bash
cat > /tmp/ticketN.txt << 'ENDOFFILE'
## File

ccya/ev/checkers/momentum.py

## Bugs

1. `requires_fields` includes `ruling.band` (line 18)
2. Floor streak detection uses `state_snapshot` instead of `momentum_after`
3. `break` at line 88 exits early
ENDOFFILE
linearis issues create "Ticket title" --team PW --labels Bug --priority 2 --description "$(cat /tmp/ticketN.txt)"
rm /tmp/ticketN.txt
```

**If the description has no inline code or special characters**, inline `--description` is fine:

```bash
linearis issues create "Ticket title" --team PW --labels Feature --priority 3 --description "## Detail\n\nSome plain text description."
```

## Labels and priorities

| Label | When to use |
|-------|-------------|
| `Bug` | Confirmed defect in current code |
| `Feature` | New functionality, not yet implemented |
| `Improvement` | Code quality, refactoring, minor polish |

| Priority | Meaning |
|----------|---------|
| 1 | Urgent — blocks work or causes data loss |
| 2 | High — real bug or important feature |
| 3 | Medium — useful improvement or minor bug |
| 4 | Low — nice to have, speculative |

## Status lifecycle

| Status | When to use |
|--------|-------------|
| `Backlog` | New tickets, untriaged, non-bug ideas |
| `New` | Bug reported, needs validation (Bug label only) |
| `Accepted` | Bug validated against current source, ready to work on (Bug label only) |
| `Scoping` | Feature/improvement needs more detail before being ready for Up Next |
| `Up Next` | Queued for work |
| `In Progress` | Actively being worked on |
| `Completed` | Done |
| `Canceled` | No longer relevant |

**Bug tickets:** Backlog → New → Accepted → Up Next → In Progress → Completed
**Non-bug tickets:** Backlog → Scoping → Up Next → In Progress → Completed
**All tickets:** Can be canceled at any stage

## Key files

| File | Purpose |
|------|---------|
| `docs/linear/write.md` | Issue creation commands, heredoc pattern, full-cycle workflow |
| `docs/linear/read.md` | List, search, read commands with filtering examples |
| `docs/linear/update.md` | Status transitions, resolution comments, archiving |
| `AGENTS.md` | Global issue tracking conventions |
| `plans/findings/LINEAR.md` | Deleted |
