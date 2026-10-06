# Plan: <ticket_id> — <title>

## Design Reference

- Design: `docs/design/<slug>-design.md`
- <Any other design references>

## Problem Statement

What is broken or missing. One paragraph.

## Firm decisions (from design)

1. <Decision 1>
2. <Decision 2>
3. <Decision 3>

## Scope

- **Phase 1:** <what>
- **Phase 2:** <what>

## Status

`scoping` / `reviewed` / `implemented` / `completed` / `canceled`

---

## Phase 01: <phase name>

### Depends on

None / Phase 01

### Context files to load

- `fablethread/engine/file.py:line` — what this file does
- `fablethread/prompts/template.j2` — what this template does

### What changes

What files change and what the changes are in prose.

### Where to change

`file:line` — specific location

### Before (current):

```python
# Show the current code if the interface contract is ambiguous
```

### After:

```python
# Show the target code — field definitions and signatures only, no method bodies
```

### Why

Why this change is needed. What problem does it solve?

### Validation

- `make check` passes
- `ev.py <command> --save-dir <dir>` shows expected behavior
- Specific checker passes

---

## Phase 02: <phase name>

### Depends on

Phase 01

### Context files to load

- `fablethread/engine/file.py:line`

### What changes

### Where to change

### Before (current):

### After:

### Why

### Validation

---

## Documentation updates

- `docs/architecture/` — <what to update>
- `docs/repomap.md` — <what to update>
- `AGENTS.md` — <what to update, or "no changes needed">
