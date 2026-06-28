---
title: "[State] ID vs name normalization"
status: scoping
urgency: 4
size: medium
created: 2026-06-14
ticket_id: F-10
labels:
  - Feature
  - Extraction
---

## Detail

Human-readable names vs camelCase IDs for state keys. Currently mixed usage creates confusion and inconsistency.

## Motivation

Consistent naming conventions improve readability and reduce errors. Human-readable names are more user-friendly; IDs are more machine-friendly.

## Scope

* **In scope:** Establish naming convention, update extraction to use consistent naming
* **Out of scope:** UI changes, prompt changes

## Systems Affected

* — state model
* — state extraction
* — state management
