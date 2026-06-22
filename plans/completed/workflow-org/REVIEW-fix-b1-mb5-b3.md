# Plan Review: fix-b1-mb5-b3.md

## Summary

Three small fixes. B1 and MB-5 are accurate and safe. B3 hypothesis is stale —
the archival mechanism already exists in both the main pipeline and sanitizer.
The actual bug is the `removed_threads` sanitizer path that destroys records
entirely. Plan was updated in place to reflect corrected B3 approach.

**Verdict:** `approved with notes` — B1/B5 ready to execute; B3 needs user
decision on `removed_threads` approach before writing.

---

## Fixes applied to plan

- **B1 scope**: Was "one line" → expanded to 3 prompt lines (line 44, 46, 52).
  Also identified line 52 as a second instance of the same bug (ammo additions
  via `inventory_update` instead of `inventory_add`).
- **MB-5 insertion point**: Verified line 1073 is correct. `storyteller_result`
  is in scope; `apply_delta` doesn't touch `consecutive_pressure_turns`;
  beat history append at 1167-1178 uses the same corrected source.
- **B3 hypothesis**: Was "add archival writes at whichever path removes threads"
  → replaced with specific finding: `removed_threads` in the sanitizer destroys
  records. Provided two options with recommendation.

## Findings requiring user input

- **[blocks-execution] B3**: The plan now correctly identifies `removed_threads`
  as the likely culprit. But execution can't start until user decides between
  option (a) eliminate `removed_threads` entirely vs (b) add archival to it.

## Contract checks

| Check | Verdict |
|-------|---------|
| `extract_state_system.j2` line 44 exists | pass — confirmed |
| `InventoryUpdate` model `models.py:231-234` has no `amount` | pass — confirmed |
| `delta_builder.py:203-211` doesn't patch amount | pass — confirmed |
| `turn.py:1063-1072` floor relief location | pass — confirmed |
| `turn.py:1289-1301` old pressure counter | pass — confirmed |
| `storyteller_result` in scope at line 1073 | pass — defined in enclosing scope |
| `apply_delta` doesn't read/write `consecutive_pressure_turns` | pass — confirmed |
| `_apply_thread_resolutions` writes `completed_threads[]` | pass — confirmed at `turn.py:410-419` |
| `_apply_sanitization` writes `completed_threads[]` | pass — confirmed at `thread_sanitizer.py:433-444` |
| Sanitizer `removed_threads` deletes without archival | pass — confirmed at `thread_sanitizer.py:453-464` |
| Sanitizer prompt offers `removed_threads` | pass — confirmed at `sanitize_thread.j2:73-75` |

## Scope violations

None.

## Format issues

None.
