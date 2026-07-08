---
title: "location_change emitted even when location ID is unchanged"
status: testing
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

## Fix

In `delta_builder.py`, a guard was added to compare the new location ID with the current location ID before applying the change. If they match, the location_change is skipped with an info log entry.
