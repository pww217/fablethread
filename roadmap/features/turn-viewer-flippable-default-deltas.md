---
title: "[EV] Turn viewer flippable + default deltas"
status: done
completed: 2026-06-24
urgency: 4
size: medium
created: 2026-06-14
labels:
  - Feature
  - UI
---

## Detail

Single-column, toggle prompts/flows vs deltas. Default to deltas. Currently the turn viewer shows both columns side-by-side which is wasteful on mobile.

## Motivation

A flippable single-column view would improve mobile usability and reduce visual clutter. Defaulting to deltas would show the most important information first.

## Scope

* **In scope:** Single-column toggle view, default to deltas, mobile optimization
* **Out of scope:** New features, backend changes

## Systems Affected

* — turn viewer templates
* — turn viewer JS
