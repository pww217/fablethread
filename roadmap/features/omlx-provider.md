---
title: "[Infra] OMLX provider"
status: scoping
urgency: 4
size: large
created: 2026-06-14
labels:
  - Improvement
  - Tooling
---

## Detail

Additional model backend support. Currently limited to a single provider; need support for additional model backends.

## Motivation

Different games may need different model backends for cost, performance, or quality reasons. Supporting multiple providers would improve flexibility.

## Scope

* **In scope:** OMLX provider integration, configuration options
* **Out of scope:** Other provider integrations

## Systems Affected

* — provider abstraction
* — provider configuration
* — provider-specific prompt adjustments
