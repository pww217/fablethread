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
   ls roadmap/<type>s/ | grep -oP '(F|B|I|E)-\d+' | sort -t- -k2 -n | tail -1
   ```
   If no existing tickets of that type, start at 1.
4. **Create frontmatter** — enforce required fields:
   ```yaml
   ---
   title: "Human-readable title"
   status: <valid-status>
   urgency: 1|2|3|4
   size: small|medium|large|xlarge
   created: YYYY-MM-DD
   ticket_id: <TYPE>-<N>
   labels:
     - <labels>
   ---
   ```
   Optional fields: `design`, `plan`, `pr` (with `url` and `branch`).
5. **Place in correct directory** — use the full path including directory prefix: `roadmap/bugs/<ticket_id>-<slug>.md`, `roadmap/features/<ticket_id>-<slug>.md`, `roadmap/improvements/<ticket_id>-<slug>.md`, or `roadmap/evals/<ticket_id>-<slug>.md`. Never strip the directory prefix when constructing the path.
6. **Run `make roadmap`** — regenerate indices.

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

### Required fields

```yaml
---
title: "Human-readable title"      # Required — used in TOC tables
status: new                        # Required — see status lifecycles
urgency: 3                         # Required — 1=urgent, 2=high, 3=medium, 4=low
size: medium                       # Required — small, medium, large, xlarge
created: 2026-06-27                # Required — ISO date (YYYY-MM-DD)
ticket_id: B-42                    # Required — unique ticket identifier
labels:                            # Optional — array of strings for bucket grouping
  - engine
  - pacing
---
```

### Optional fields

```yaml
---
design: docs/design/pacing-fix.md  # Path to design doc
plan: plans/pacing-fix.md          # Path to plan doc
pr:                                # PR reference
  url: https://github.com/.../pull/123
  branch: ccya-pacing-fix
---
```

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
