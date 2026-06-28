---
title: "[Tech Debt] Dead imports / parity gaps sweep"
status: canceled
urgency: 4
size: medium
created: 2026-06-14
ticket_id: F-6
labels:
  - Improvement
  - Tech Debt
---

## Detail

Remove dead imports and fix parity gaps between modules. Some imports may be unused and some modules may have inconsistent patterns.

## Motivation

Dead imports waste time and create confusion. Parity gaps make the codebase harder to maintain.

## Scope

* **In scope:** Remove dead imports, fix parity gaps, standardize patterns
* **Out of scope:** Major refactors, new features

## Systems Affected

* — Python source files
