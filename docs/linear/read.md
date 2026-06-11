# Linear — Read

## List issues

### By team and status

```bash
# All tickets in Backlog for team PW
linearis issues list --team PW --status Backlog

# All bug tickets
linearis issues list --team PW --status "Backlog,New,Accepted,Up Next,In Progress" --label Bug

# All tickets for a project
linearis issues list --project "CCYA"

# All tickets in Scoping status
linearis issues list --team PW --status Scoping
```

### By label

```bash
# All bug tickets
linearis issues list --team PW --label Bug

# All feature tickets
linearis issues list --team PW --label Feature

# All improvement tickets
linearis issues list --team PW --label Improvement
```

### By priority

```bash
# All high-priority tickets
linearis issues list --team PW --priority 2

# All low-priority tickets
linearis issues list --team PW --priority 4
```

### By assignee

```bash
# All tickets assigned to Peter
linearis issues list --team PW --assignee "Peter"
```

## Search issues

Full-text search across ticket titles and descriptions:

```bash
# Search for momentum-related tickets
linearis issues search "momentum" --team PW

# Search for a specific checker
linearis issues search "sanitizer" --team PW

# Search with team and label filters
linearis issues search "dead code" --team PW --label Bug

# Search with status filter
linearis issues search "NPC" --team PW --status "Backlog,Up Next"
```

## Read issue

Get full issue details including description:

```bash
# Read a ticket by identifier
linearis issues read TICK-6

# Read with attachments
linearis issues read TICK-6 --with-attachments

# Read with comments
linearis issues read TICK-6 --with-comments

# Read with discussion threads
linearis issues read TICK-6 --with-comment-threads
```

## List discussion threads on an issue

```bash
# List root discussion threads on a ticket
linearis issues discussions TICK-6
```

## Discover dynamic state

When you need to check what's available in Linear (labels, statuses, projects), use the CLI to discover rather than relying on hardcoded lists:

```bash
# Check available labels
linearis labels list

# Check available teams
linearis teams list

# Check available projects
linearis projects list --limit 10

# Test a status name (returns empty list if valid, error if not)
linearis issues list --team PW --status "SomeStatus" --limit 1
```

## Key files

| File | Purpose |
|------|---------|
| `plans/findings/LINEAR.md` | Deleted |
| `AGENTS.md` | Global issue tracking conventions |
