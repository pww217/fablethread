# Linear — Update

## Status transitions

### Bug ticket lifecycle

```bash
# New → Accepted (after validation)
linearis issues update TICK-6 --status "Accepted"

# Accepted → Up Next
linearis issues update TICK-6 --status "Up Next"

# Up Next → In Progress
linearis issues update TICK-6 --status "In Progress"

# In Progress → Completed
linearis issues update TICK-6 --status "Completed"
```

### Non-bug ticket lifecycle

```bash
# Backlog → Up Next
linearis issues update TICK-10 --status "Up Next"

# Up Next → In Progress
linearis issues update TICK-10 --status "In Progress"

# In Progress → Completed
linearis issues update TICK-10 --status "Completed"
```

### Cancel at any stage

```bash
linearis issues update TICK-6 --status "Canceled"
```

## Label changes

### Add labels (without removing existing)

```bash
# Add area label to existing ticket
linearis issues update TICK-6 --labels "Engine,plan" --label-mode add

# Add area + type labels
linearis issues update TICK-6 --labels "UI,Feature" --label-mode add
```

### Overwrite labels

```bash
# Replace all labels with area + type
linearis issues update TICK-6 --labels "Engine,Bug" --label-mode overwrite
```

### Remove all labels

```bash
linearis issues update TICK-6 --clear-labels
```

## Resolution comments

After completing work on a ticket, add a resolution comment to the discussion thread:

```bash
linearis issues discuss TICK-6 --body "## Resolution\n\nFixed by removing `ruling.band` from `requires_fields`, using `extract_field(ev, momentum_after)` for floor streak detection, and replacing `break` with `continue` at line 88."
```

The resolution comment should:
- Summarize what was changed
- Reference specific files and line numbers
- Note any tradeoffs or decisions made
- Do not need a strict template — just be clear and specific

### Updating status after resolution

```bash
linearis issues update TICK-6 --status "Completed"
```

## Discussion thread management

### List threads on a ticket

```bash
linearis issues discussions TICK-6
```

### Reply to a thread

```bash
# Reply to a root discussion thread (thread ID from discussions output)
linearis issues reply <thread-id> --body "Follow-up: also checked gm_beat.py and confirmed the same issue exists there."
```

### Resolve a discussion thread

```bash
linearis issues resolve <thread-id>
```

## Issue metadata updates

### Change priority

```bash
linearis issues update TICK-6 --priority 3
```

### Change assignee

```bash
linearis issues update TICK-6 --assignee "Peter"
```

### Add to project

```bash
linearis issues update TICK-6 --project "CCYA"
```

### Set parent ticket (sub-issue)

```bash
linearis issues update TICK-7 --parent-ticket TICK-6
```

### Add relation

```bash
# This issue blocks another
linearis issues update TICK-6 --blocks TICK-8

# This issue is blocked by another
linearis issues update TICK-8 --blocked-by TICK-6

# This issue relates to another
linearis issues update TICK-6 --relates-to TICK-10
```

## Archiving

Archive a completed ticket to remove it from active views:

```bash
linearis issues archive TICK-6
```

## Key files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Global issue tracking conventions |
| `docs/linear/write.md` | Full-cycle workflow |
