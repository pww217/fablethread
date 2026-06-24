---
title: "Compendium alias priority and naming strategy"
status: done
urgency: 3
size: medium
created: 2026-06-11
labels:
  - Feature
  - Extraction
---

## Status

Needs scoping. Feature.

## Detail

Current naming/priority: UI shows `name or node_id`. When no name exists but aliases exist, shows "Previously known as: X" only in tooltip. Fallback to machine-readable node ID is not UI-friendly.

## Scope

* Scene extractor: use alias field for unnamed characters instead of placeholder names. If character later gets a proper name, append to same entry (dedup).
* UI display priority: proper name → first alias → error (NOT node ID)
* IDEAS.md alias resolution is related but this is broader — covers display priority and naming strategy
