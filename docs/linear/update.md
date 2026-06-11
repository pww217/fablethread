# Linear — Update

## Status transitions

### Bug ticket lifecycle

```bash
# New → Accepted (after validation)
linearis issues update PW-6 --status "Accepted"

# Accepted → Up Next
linearis issues update PW-6 --status "Up Next"

# Up Next → In Progress
linearis issues update PW-6 --status "In Progress"

# In Progress → Complete
linearis issues update PW-6 --status "Complete"
```

### Non-bug ticket lifecycle

```bash
# Backlog → Up Next
linearis issues update PW-10 --status "Up Next"

# Up Next → In Progress
linearis issues update PW-10 --status "In Progress"

# In Progress → Complete
linearis issues update PW-10 --status "Complete"
```

### Cancel at any stage

```bash
linearis issues update PW-6 --status "Canceled"
```

## Label changes

### Add labels (without removing existing)

```bash
linearis issues update PW-6 --labels "Bug,plan" --label-mode add
```

### Overwrite labels

```bash
linearis issues update PW-6 --labels "Feature" --label-mode overwrite
```

### Remove all labels

```bash
linearis issues update PW-6 --clear-labels
```

## Resolution comments

After completing work on a ticket, add a resolution comment to the discussion thread:

```bash
linearis issues discuss PW-6 --body "## Resolution\n\nFixed by removing `ruling.band` from `requires_fields`, using `extract_field(ev, momentum_after)` for floor streak detection, and replacing `break` with `continue` at line 88."
```

The resolution comment should:
- Summarize what was changed
- Reference specific files and line numbers
- Note any tradeoffs or decisions made
- Do not need a strict template — just be clear and specific

### Updating status after resolution

```bash
linearis issues update PW-6 --status "Complete"
```

## Discussion thread management

### List threads on a ticket

```bash
linearis issues discussions PW-6
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
linearis issues update PW-6 --priority 3
```

### Change assignee

```bash
linearis issues update PW-6 --assignee "Peter"
```

### Add to project

```bash
linearis issues update PW-6 --project "CCYA"
```

### Set parent ticket (sub-issue)

```bash
linearis issues update PW-7 --parent-ticket PW-6
```

### Add relation

```bash
# This issue blocks another
linearis issues update PW-6 --blocks PW-8

# This issue is blocked by another
linearis issues update PW-8 --blocked-by PW-6

# This issue relates to another
linearis issues update PW-6 --relates-to PW-10
```

## Archiving

Archive a completed ticket to remove it from active views:

```bash
linearis issues archive PW-6
```

## Key files

| File | Purpose |
|------|---------|
| `AGENTS.md` | Global issue tracking conventions |
| `docs/linear/write.md` | Full-cycle workflow |
