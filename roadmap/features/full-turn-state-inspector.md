---
title: "[EV] Full turn state inspector"
status: scoping
urgency: 4
size: large
created: 2026-06-14
labels:
  - Feature
  - Tooling
---

## Detail

Click a turn for complete state JSON, syntax-highlighted. Currently no way to inspect the full state of a turn in a developer-friendly format.

## Motivation

Developers need a way to inspect the full state of a turn for debugging. A syntax-highlighted JSON viewer would make this much easier.

## Scope

* **In scope:** Click-to-inspect turn state, syntax-highlighted JSON viewer
* **Out of scope:** Backend changes, new features

## Systems Affected

* — inspector templates
* — inspector JS
* — inspector routes
