---
name: bug-triage
description: Validate, reproduce, and prioritize bug candidates
---

Purpose: Confirm bugs are real, assess severity, and set roadmap status. The last step before a bug enters the work queue.

## Sources

- **Roadmap bugs:** `roadmap/bugs/<slug>.md` with `status: new` — created by `ev-review`
- **Ad-hoc:** User-provided bug descriptions, live-play observations, or manual inspection — no prior file exists

## Workflow

1. **Read the bug report** — understand expected vs. actual behavior, reproduction context, root cause estimate
2. **Reproduce** — load the save, inspect the turn, run targeted checkers:
   ```bash
   .venv/bin/python scripts/debug/ev.py turn <N> <save-path>
   .venv/bin/python scripts/debug/ev.py check <N> <checker_name> --save-dir <save-path>
   .venv/bin/python scripts/debug/ev.py mechanics <N> --dice --pacing <save-path>
   ```
3. **Assess** — is it real? Is it a prompt issue, engine bug, checker false positive, or intended behavior?
4. **If real:** assess severity (blocker, major, minor, cosmetic) and urgency
5. **If not real:** set status to `canceled` with a note explaining why

## Status Transitions

| From | To | When |
|---|---|---|
| `new` | `validated` | Bug confirmed real, urgency and size set |
| `new` | `canceled` | False positive, duplicate, or works-as-intended |
| (none) | `validated` | Ad-hoc bug — created + validated in one step |
| any | `canceled` | User decides not to fix |

## Ad-hoc Mode (No Prior Bug File)

Create `roadmap/bugs/<slug>.md` with `status: validated` in one pass:

```yaml
---
title: Descriptive title
status: validated
urgency: 2
size: small
created: YYYY-MM-DD
labels:
  - <component>
---
Reproduction steps and findings.
```

## Output

Update the existing bug file's frontmatter:

```yaml
---
status: validated    # or canceled
urgency: 2           # 1=urgent, 2=high, 3=medium, 4=low
size: small          # small | medium | large | xlarge
completed: YYYY-MM-DD  # only if canceled
---
```

Leave the `design` and `plan` fields empty — those are set when someone picks up the bug.

Done when every input bug is either `validated` (with urgency/size) or `canceled`.
