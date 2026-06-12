# Linear — Write

## Issue creation

### Basic creation

```bash
linearis issues create "Ticket title" --team PW --labels "Engine,Bug" --priority 2 --project "CCYA" --description "$(cat /tmp/ticketN.txt)"
```

- `--team PW` — required, team key is `PW`
- `--labels` — area + type, comma-separated: area (`Engine`, `UI`, `EV`, `TV`, `Docs`, `Config`) + type (`Bug`, `Feature`, `Improvement`)
- `--priority` — 1=urgent, 2=high, 3=medium, 4=low
- `--project "CCYA"` — always associate with the CCYA project
- `--status` — set initial status (see status lifecycle in skill)
- Ticket IDs auto-increment as TICK- (e.g., TICK-1, TICK-2)

Area labels categorize by subsystem. Create them in Settings → Labels if they don't exist (see `read.md` for color codes). Always use area + type together (e.g., `--labels "UI,Bug"`).

**Status convention:** Bug tickets start as `New` (unverified, awaiting validation). Feature/Improvement tickets start as `Backlog`. `Accepted` means validated — only move bugs there after confirming the bug still exists in source.

### Heredoc pattern (for inline code)

Use when the description contains backticks, `()`, glob `*`, or `>`:

```bash
cat > /tmp/ticketN.txt << 'ENDOFFILE'
## File

ccya/ev/checkers/momentum.py

## Bugs

1. `requires_fields` includes `ruling.band` (line 18)
2. Floor streak detection uses `state_snapshot` instead of `momentum_after`
3. `break` at line 88 exits early
ENDOFFILE
linearis issues create "Fix momentum_lifecycle checker — 3 bugs" --team PW --labels "EV,Bug" --priority 2 --project "CCYA" --description "$(cat /tmp/ticketN.txt)"
rm /tmp/ticketN.txt
```

### Inline description (plain text only)

Use when the description has no inline code or special characters:

```bash
linearis issues create "NPC left-behind tracking on location change" --team PW --labels "Engine,Feature" --priority 3 --project "CCYA" --description "## Detail\n\nWhen player changes locations, characters who should logically stay behind aren't tracked."
```

### Checking for duplicates

Always search before creating:

```bash
linearis issues search "momentum_lifecycle" --team PW
linearis issues search "mobile carousel" --team PW
```

## Full-cycle workflow

### 1. Discover and validate

When a bug or feature is found:

1. Search for existing tickets: `linearis issues search "<keyword>" --team PW`
2. If no existing ticket, validate against current source code
3. If validated, proceed to create

### 2. Create ticket

Create with appropriate status based on type:

**Bug tickets:**
```bash
# Use heredoc if inline code needed
linearis issues create "Fix momentum_lifecycle checker — 3 bugs" --team PW --labels "EV,Bug" --priority 2 --project "CCYA" --status "New" --description "$(cat /tmp/ticketN.txt)"
```

**Non-bug tickets:**
```bash
linearis issues create "NPC left-behind tracking on location change" --team PW --labels "Engine,Feature" --priority 3 --project "CCYA" --status "Backlog" --description "## Detail\n\n..."
```

Record the ticket ID (e.g., `TICK-6`) for later reference.

### 3. Validate bugs (New → Accepted)

When ready to validate a bug ticket:

1. Read the ticket: `linearis issues read TICK-6`
2. Check the referenced source files to confirm the bug still exists
3. If validated, move to Accepted: `linearis issues update TICK-6 --status "Accepted"`
4. Add a validation comment to the discussion thread:

```bash
linearis issues discuss TICK-6 --body "## Validation\n\nChecked `ccya/ev/checkers/momentum.py` lines 18, 73-88. Bug confirmed: `requires_fields` still includes `ruling.band`, floor streak detection still uses `state_snapshot`, and `break` still exits early."
```

The validation comment should reference specific files and line numbers to document how the bug was verified.

### 4. Plan and execute

1. Pull the ticket: `linearis issues read TICK-6`
2. Write a plan doc in `plans/` (or `plans/review/` for review)
3. Link the plan to the ticket using `--parent-ticket` if creating a sub-issue, or reference the ticket ID in the plan doc
4. Execute the plan
5. When done, update the ticket status and add a resolution comment (see `docs/linear/update.md`)

### 5. Resolve and close

After execution is complete:

1. Add a resolution comment to the ticket (see `docs/linear/update.md`)
2. Update status to `Completed`
3. If the ticket was a bug, verify the fix doesn't break existing checkers

## Key files

| File | Purpose |
|------|---------|
| `ccya/ev/checkers/` | Eval checkers referenced by bug tickets |
| `ccya/engine/` | Engine code referenced by bug tickets |
| `ccya/templates/` | UI templates referenced by bug tickets |
| `plans/` | Plan documents for ticket implementation |
