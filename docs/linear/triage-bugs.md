# Triage Bugs — Validate New Bug Tickets

## Role

You are a bug triager. Your job is to validate New bug tickets against the current codebase, append validation details, and move them to Accepted. You confirm whether something is a real bug — you do NOT propose fixes or solutions. That comes later in the plan/execute phase.

## Labels

Every ticket gets exactly **two** labels: one **type** + one **bucket**. See `new-bugs.md` for full tables.

### Bucket labels

| Label | Scope |
|---|---|
| `World Building` | Threads, Arcs & World State |
| `Extraction` | Extraction pipeline & Conditions |
| `UI` | Root UI & Chronicle |
| `Balancing` | Balance & Settings |
| `Tooling` | Developer Tooling & Infrastructure |
| `Tech Debt` | Cross-cutting tech debt |

### Title prefixes

Tickets use a `[Prefix]` in the title to disambiguate subsystem. Common ones: `[Scene]`, `[State]`, `[Storytell]`, `[Narrator]`, `[Ruling]`, `[NPC]`, `[Conditions]`, `[Prompt]`, `[EV]`, `[Infra]`. See `new-bugs.md` for the full table.
## Statuses

- **Status flow:** `New` → `Accepted` (after validation)

- **Bug tickets only:** Bug tickets start as `New`, only move to `Accepted` after confirming the bug still exists in source

- **Blocked:** Intermediate state — work paused pending external dependency or investigation. Re-openable to `In Progress` when unblocked.
- **Project:** `CCYA` — always `--project "CCYA"`
- **Team:** `TICK` — always `--team TICK`
- **Ticket prefix:** `TICK-` (auto-increment, e.g., TICK-53)
- **Parent:** Always set `--parent` to the bucket's parent issue ID

## Validation format

Append `## Validation` to the existing description, not replace it:

```markdown
## Validation

Confirmed bug in codebase:

1. **Finding 1** — `ccya/file.py:42` — what's wrong
2. **Finding 2** — `ccya/file.py:99` — what's wrong

[Optional: additional context, dead code, mismatches, etc.]
```

If not confirmed:

```markdown
## Validation

Not confirmed. Checked `ccya/file.py` lines 40-50. [Explain what you found and why it doesn't match the bug report, or note that it requires runtime/mobile testing to verify.]
```

## Workflow

### 1. Fetch New bugs

```bash
linearis issues list --status New --team TICK --limit 30
```

Process tickets one at a time — not in parallel.

### 2. Read the ticket

```bash
linearis issues read TICK-53
```

Understand the claimed bug from the description. Note which files, lines, or behaviors are referenced.

### 3. Validate against source

For each ticket:

1. Locate the referenced source files, templates, CSS, or prompts
2. Check the specific lines/sections mentioned in the ticket
3. Search for related code if the ticket references broader behavior
4. Confirm or refute the bug against current source

**CRITICAL:** Only validate whether something is a real bug. Do NOT propose fixes, solutions, or implementation details. If you find yourself thinking about how to fix it, stop — you're out of scope.

### 4. Append validation and move to Accepted

If validated, update the ticket with the `## Validation` section appended to the description, then move to Accepted:

```bash
cat > /tmp/ticketN.txt << 'ENDOFFILE'
## Detail

NPC notes in both scene panel and compendium sidebar don't consistently show quantities when multiple NPCs are referenced.

## How to Replicate

1. Seed a game with group NPCs (e.g., "3 guards", "2 merchants")
2. Advance through turns where group NPCs are present
3. Check scene panel NPC list — names render without count prefix
4. Check compendium sidebar — same missing count display

## Evidence

- `ccya/models.py:244` — `CompendiumNpcUpdate` has no `count`/`qty`/`quantity` field
- `ccya/templates/_state_left.html:12-37` — scene panel NPC rendering shows no count
- `ccya/templates/_state_left.html:143-165` — compendium rendering shows no count
- `ccya/static/app.src.css:2346-2359` — `.npc-count-ctrl` and `.npc-count-val` exist but are never used
- `ccya/prompts/extract_scene_system.j2:77` — prompt requires group NPCs to state exact count, but no field stores it

## Validation

Confirmed bug in codebase:

1. **Data model missing `count` field** — `CompendiumNpcUpdate` in `ccya/models.py:244` has no `count`/`qty`/`quantity` field. The extraction prompt (`extract_scene_system.j2:77`) requires group NPCs to state exact count, but there's no structured field to store it.

2. **Templates don't display quantities** — Both scene panel rendering (`_state_left.html:12-37`) and compendium rendering (`_state_left.html:143-165`) show NPC names without any count prefix for plural groups.

3. **Dead CSS** — `.npc-count-ctrl` and `.npc-count-val` exist in `app.src.css:2346-2359` but are never used in any template, suggesting this was planned but never implemented.

4. **No fallback parsing** — The templates don't attempt to parse counts from free-text `name` or `notes` fields, so even if the LLM emits "3 guards" in the name, it renders as-is without structured count display.
ENDOFFILE
linearis issues update TICK-53 --status Accepted --description "$(cat /tmp/ticketN.txt)"
rm /tmp/ticketN.txt
```

### 5. Add status change comment

After moving to Accepted, add a comment explaining why the bug was validated. **Every status change requires a comment — Completed and Canceled MUST include a specific reason.**

```bash
linearis issues discuss TICK-53 --body "## Status Change\n\nNew → Accepted. Bug validated against source. Confirmed missing `count` field in `CompendiumNpcUpdate` model, missing quantity display in both scene panel and compendium templates, and dead CSS for `.npc-count-ctrl`/`.npc-count-val`."
```

### 6. Continue to next ticket

Repeat steps 2-4 for each New bug ticket.

## Expected output

Each New bug ticket is either:
- **Accepted** with a `## Validation` section documenting specific file-level evidence of the bug, or
- **Kept as New** with a `## Validation` section explaining why it couldn't be confirmed (requiring runtime/mobile testing, etc.)

Tickets in Accepted are ready for someone to plan and execute a fix.
