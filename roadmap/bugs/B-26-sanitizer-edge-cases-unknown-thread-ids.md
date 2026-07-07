---
title: "Sanitizer edge cases — unknown thread IDs, thread resolutions"
status: canceled
urgency: 4
size: small
created: 2026-06-29
ticket_id: B-26
labels: [sanitizer, edge-case]
---

## Description

Sanitizer logs warnings about unknown thread IDs and thread resolutions referencing non-existent IDs. These are minor, expected failures in checker — not blocking issues.

## Symptoms

- Sanitizer events reference unknown thread IDs
- `thread_resolutions` references unknown id
- Minor failures in checker output
- No functional impact on game state

## Root Cause

Sanitizer validates thread IDs against current state. When threads are resolved or removed between sanitizer runs, references become stale. This is expected behavior — threads have natural lifecycles.

## Fix Needed

### Option A: Tolerate stale references
- Sanitizer should tolerate thread IDs that no longer exist
- Log as info/warning rather than error
- No action needed — expected behavior

### Option B: Clean up stale references
- Sanitizer should remove stale thread references during validation
- `thread_resolutions` should be pruned for non-existent threads
- `thread_updates` should be pruned for non-existent threads

### Option C: Track thread lifecycle
- Add thread lifecycle tracking (created, active, resolved, archived)
- Sanitizer validates against active threads only
- Resolved threads can be archived without removing references

## Recommendation

Option A is sufficient for now. These are minor warnings with no functional impact. If they become frequent or noisy, consider Option B.

## Related

- B-16: Orphaned sanitizer events after cancel/delete (done)
- Sanitizer runs on turns divisible by `sanitize_every` (default 5)
- Every pack showed duplicates at T5, T10, T15, T20, T25 (B-16 fix)

## Files to Review

- `ccya/state/sanitizer.py` — Sanitizer validation logic
- `ccya/state/chronicle.py` — Thread management
- `evals/runs/*/events.jsonl` — Sanitizer event output