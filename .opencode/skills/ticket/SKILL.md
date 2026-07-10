---
name: ticket
description: Create, update, validate, and audit roadmap tickets with enforced standards
---

Create, update, validate, and audit roadmap tickets. Enforces frontmatter schema, status transitions, slug conventions, and type inference.

## Context loading

Read `roadmap/README.md` for schema, lifecycles, and conventions before acting.

## Responsibilities

### Create tickets

1. **Infer type** — bug, feature, improvement, or eval. If ambiguous, ask using `question` tool (recommended option first).
2. **Generate slug** — kebab-case, descriptive, no special chars. Max ~60 chars.
3. **Assign ticket ID** — `F-N`, `B-N`, `I-N`, or `E-N`. Find the next available number for the type:
   ```bash
   ls roadmap/<type>s/ | grep -oE '(F|B|I|E)-[0-9]+' | sort -t- -k2 -n | tail -1
   ```
   If no existing tickets of that type, start at 1. Always use highest number + 1 (never fill gaps).
4. **Create ticket** — run `scripts/new-ticket.py <type> "<summary>" [--slug SLUG] [--status STATUS]`. The script handles ID generation, slug generation (if omitted), template loading, frontmatter filling, and file placement. Status defaults to template default (`new` for bug/eval, `idea` for feature/improvement).
5. **Run `make roadmap`** — regenerate indices.

### Update tickets

1. **Validate status transition** — check against lifecycle rules:
   - Bugs: `new` → `validated` → `up-next` → `testing` → `done`/`canceled`
   - Features: `idea` → `scoping` → `up-next` → `done`/`canceled`
   - Improvements: `idea` → `scoping` → `up-next` → `done`/`canceled`
   - Evals: `new` → `triaged` → `up-next` → `done`/`canceled`
   - `canceled` allowed from any status
2. **Reject invalid transitions** — error with clear message showing valid transitions.
3. **Update cross-link fields** — when a design/plan/PR is created, update the corresponding field on the roadmap file.
4. **Run `make roadmap`** — regenerate indices.

### Audit tickets

1. **Check frontmatter compliance** — required fields present, valid values.
2. **Check status transitions** — no invalid transitions in history.
3. **Check cross-references** — `design`, `plan`, `pr` point to existing files/URLs.
4. **Check ticket ID uniqueness** — no duplicates within type.
5. **Report issues** — list all violations found.

## Slug conventions

- Kebab-case: `pacing-fix`, `beat-driver-always-motivation`
- Descriptive: what the ticket is about
- No special characters, no spaces
- Max ~60 characters
- If too long, truncate to most significant part

## Type inference

| Indicator | Type |
|-----------|------|
| "broken", "fail", "crash", "error", "disconnect" | bug |
| "new", "add", "create", "implement", "capability" | feature |
| "better", "improve", "refine", "optimize", "fix" (on existing thing) | improvement |
| "eval", "checker", "rubric", "scenario" | eval |

If ambiguous, ask using `question` tool.

## Frontmatter schema

Full schema with field descriptions: `roadmap/templates/<type>.md` (bug, feature, improvement, or eval).

Required fields: `title`, `status`, `urgency`, `size`, `created`, `ticket_id`.
Optional fields: `design`, `plan`, `pr` (with `url` and `branch`), `labels`.

## Status transition validation

Enforce lifecycle rules strictly. Reject invalid transitions with a clear error:

```
Invalid status transition: <current> → <proposed> for ticket <ticket_id>.
Valid transitions: <list of valid next statuses>.
```

Allow `canceled` from any status without validation.

## Integration with other skills

All skills that touch roadmap items should call the ticket skill:

- `create-design`: Call ticket skill to create/update roadmap file, then write design doc
- `plan`: Call ticket skill to update `plan` field, set status to `up-next`
- `execute`: Call ticket skill to update `pr` field, set design status to `implemented`, set ticket status to `done` on completion
- `review-plan`: Call ticket skill to verify plan references correct ticket
- `review-code`: Call ticket skill to verify PR references correct ticket
- `ev-run`: Call ticket skill to create ONE `E-` ticket per eval session, include eval group path, phase report links, and all findings
- `ev-review`: Call ticket skill to update testing items, create ONE `E-` ticket per session if new issues warrant tracking, report lives within the eval ticket

## Done when

Ticket created/updated/audited with valid frontmatter, correct type, valid status, unique ticket ID, and proper directory placement. Indices regenerated via `make roadmap`.

## Never do

Skip status transition validation, invent ticket IDs, place files in wrong directory, skip `make roadmap`, assume type without asking when ambiguous, modify tickets outside the requested scope.
