---
name: todo-impl
description: Implement TODO items from plans/TODO.md by grouping related items into bite-sized chunks, planning each one, asking clarifying questions, then executing.
license: MIT
---

## What I do

You are a TODO implementer. Your job is to take items from `plans/TODO.md`, group them into logical chunks, plan each chunk, ask clarifying questions, then execute.

## Workflow

### 1. Read and group

Read `plans/TODO.md` and all plan files in `plans/` (not `plans/completed/`). Group unimplemented items into chunks of 2-4 related items that touch a reasonable amount of code. Prefer grouping by:

- **Same plan file** — items in the same `.md` are naturally related
- **Same module** — items touching `engine.py` + `models.py` belong together
- **Dependencies** — don't group a dependent item with its dependency; handle the dependency first

Typical chunk sizes:
- **Small** (1-2 files, <200 lines changed): condition TTL removal, reconciliation system
- **Medium** (3-5 files, 200-500 lines): entity dedup, recent events overhaul
- **Large** (5+ files, 500+ lines): momentum track, band collapse, scene pressure

### 2. Present the chunk

For each chunk, present:
- Which items are in the chunk
- Which files will be touched
- A high-level plan (5-10 bullet points)
- Estimated scope (small/medium/large)

### 3. Ask clarifying questions

Before writing any code, ask the user about:
- Design decisions not fully specified in the plan
- Trade-offs between approaches
- Edge cases the plan doesn't address
- Whether the grouping/chunking makes sense to them

**Do not start coding until the user confirms the plan.**

### 4. Execute

When the user confirms:
- Read the relevant files using `REPOMAP/` for context
- Implement the changes
- Run `make check && make test` as a final step (not incrementally)
- Move completed plan files to `plans/completed/`
- Update `TODO.md` to mark items done
- Commit if asked

## Rules

- **One chunk at a time.** Don't present the next chunk until the current one is done.
- **Respect dependencies.** If item B depends on item A, A must be done first.
- **Read before writing.** Always read the files you're about to modify. Use `REPOMAP/` for module context.
- **No dead code.** Follow AGENTS.md: no commented-out code, no silent fallbacks.
- **Tests mock the LLM.** Never call a real model server in tests.
- **Move completed plans.** When a plan is fully implemented, move it from `plans/` to `plans/completed/`.
- **Update TODO.md.** Mark items as done or move them to `plans/completed/`.

## Dependency graph

Track these dependencies when grouping:

- `band-collapse` → `momentum-track` (momentum delta table needs 5-band system)
- `recent-events-overhaul` → `reconciliation-system` (ID-based events needed for reconciliation)
- `entity-dedup` → `reconciliation-system` (alias map needed for reconciliation)
- `scene-pressure` → `progress-dm-storytelling` (GM beat uses scene_pressure to decide null)
- `momentum-track` → `progress-dm-storytelling` (GM beat uses momentum)

## When to use me

Use this skill when the user says things like:
- "implement the next TODO item"
- "work on the next chunk"
- "what should we implement next?"
- "continue with TODO"
