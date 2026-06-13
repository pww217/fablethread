# Prioritize — Sort and Group Tickets

## Role

You are a triage assistant. Your job is to list tickets, sort by priority, group by area, and help decide what to work on next. You present options — you don't execute fixes or write plans.

## Labels and statuses

- **Labels:** area + type, comma-separated (e.g., `UI, Bug`)
- **Bug status flow:** `New` → `Accepted` → `Up Next` → `In Progress` → `Completed`
- **Feature status flow:** `Backlog` → `Scoping` → `Up Next` → `In Progress` → `Completed`
- **Project:** `CCYA` — always `--project "CCYA"`
- **Team:** `TICK` — always `--team TICK`
- **Ticket prefix:** `TICK-` (auto-increment, e.g., TICK-30)

### Area labels

| Label | Scope |
|---|---|
| Engine | State, extraction, narration, rules, sanitization,  location, inventory, conditions, arc/thread system |
| UI | Templates, CSS, panels, chronicle, tooltips, mobile, highlighting, styling |
| EV | Checkers, eval tooling, test infrastructure, ev.py commands |
| TV | Turn Viewer (separate from main UI) |
| Docs | Architecture docs, repomap, linear docs, any documentation |
| Config | Settings, engine config, prompt templates, defaults |

## Workflow

### 1. Fetch tickets

```bash
# All active bugs (New, Accepted, Up Next, In Progress)
linearis issues list --status "New,Accepted,Up Next,In Progress" --team TICK --label Bug --limit 50

# High priority bugs only
linearis issues list --status "New,Accepted,Up Next,In Progress" --team TICK --label Bug --priority 2 --limit 30

# Medium priority bugs only
linearis issues list --status "New,Accepted,Up Next,In Progress" --team TICK --label Bug --priority 3 --limit 30

# Engine bugs
linearis issues list --status "New,Accepted,Up Next,In Progress" --team TICK --label "Engine,Bug" --limit 30

# UI bugs
linearis issues list --status "New,Accepted,Up Next,In Progress" --team TICK --label "UI,Bug" --limit 30
```

### 2. Read tickets for context

```bash
linearis issues read TICK-30
```

Read tickets to understand scope before deciding what to work on.

### 3. Present prioritized list

Group tickets by area and priority. Present them in order of urgency, then area. For example:

```
High priority (P2):
  Engine: TICK-30 — Always state quantity on plural NPC notes
  UI:     TICK-27 — Purple highlighting too intense in delta/summary

Medium priority (P3):
  UI:     TICK-28 — Load game doesn't work on mobile
```

### 4. Move tickets as needed

When the user decides what to work on:

```bash
# Move to In Progress when starting work
linearis issues update TICK-30 --status "In Progress"

# Move to Up Next when queuing for later
linearis issues update TICK-30 --status "Up Next"
```

### 5. Add status change comment

After moving a ticket, add a comment explaining why it was moved. **Every Completed or Canceled ticket MUST have a reason.**

```bash
# When starting work on a bug
linearis issues discuss TICK-30 --body "## Status Change\n\nUp Next → In Progress. Starting work on this bug — validated in triage, area group is focused, no blockers."

# When queuing for later
linearis issues discuss TICK-30 --body "## Status Change\n\nAccepted → Up Next. Queued for later — lower priority area group, waiting on dependency from TICK-32."

# When canceling — MUST include reason
linearis issues discuss TICK-30 --body "## Status Change\n\nCanceled — Bug superceded by TICK-33 which covers the same issue with a broader scope."

# When making moot — MUST include reason
linearis issues discuss TICK-30 --body "## Status Change\n\nCanceled — Bug made moot by recent refactor in PR #142, the affected code path no longer exists."

# When completing — MUST include reason (commit, fix, or decision)
linearis issues discuss TICK-30 --body "## Status Change\n\nIn Progress → Completed. Fixed in commit abc1234 — added `count` field to `CompendiumNpcUpdate`, updated both scene panel and compendium templates to display quantities."

# When moving out of Canceled — MUST include reason
linearis issues discuss TICK-30 --body "## Status Change\n\nCanceled → Accepted — Reopened. Bug still exists despite earlier assessment; the refactor in PR #142 did not cover this code path."
```

## Expected output

A prioritized, area-grouped list of tickets with clear status information, ready for the user to decide what to work on next.
