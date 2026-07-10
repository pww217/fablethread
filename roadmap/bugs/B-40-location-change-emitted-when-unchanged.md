---
title: "location_change emitted even when location ID is unchanged"
status: done
completed: 2026-07-09
urgency: 2
size: small
created: 2026-07-07
ticket_id: B-40
labels:
  - engine
  - delta-builder
---

# B-40: location_change emitted when location unchanged

## Symptom

The engine emits a `location_change` delta even when the new location ID matches the current location ID. This causes the `location_change` checker to flag the event as a mismatch.

## Evidence

From space-western run, T12:
```
location_change emitted: id=unregistered_docking_ring
Previous location.id: unregistered_docking_ring
Post-turn location.id: unregistered_docking_ring
```

The checker at `inventory.py:50` flags this when `post_loc == prev_loc`.

## Root Cause

The delta_builder or record step emits a `location_change` when the narration suggests a location change, but the state reconciliation doesn't validate that the new location ID differs from the current one before applying it.

## Evidence (ev-review 2026-07-09, all three 15-turn runs)

- noir-1930s: legitimate location changes at T3 (boarding_house), T4 (boarding_house_foyer), T10 (cellar) — each differs from previous
- space-western: legitimate location changes at T6 (secondary_maintenance_corridors), T12 (primary_filtration_ducts_catwalk) — each differs from previous
- golden-piracy: legitimate location changes at T6 (main_deck), T13 (lower_decks) — each differs from previous
- Guard in delta_builder.py:216-224 compares new location ID with current, logs location_change.skipped if match, skips applying
- location_change checker passes 5/5, 15/15, 15/15, 15/15 across all four runs

## Fix

In `delta_builder.py`, a guard was added to compare the new location ID with the current location ID before applying the change. If they match, the location_change is skipped with an info log entry.
