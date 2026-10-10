---
title: API Key Configuration
status: up-next
urgency: 3
size: medium
created: 2026-10-10
ticket_id: F-36
labels: []
design: ../../docs/design/api-key-config-design.md
plan:
pr:
  url:
  branch:
---

## Description

Make `api_key` configurable via `config.yaml` instead of hardcoding `"local"` in the LLM client. This enables hosted LLM providers (OpenAI, Anthropic, Together, etc.) that require API key authentication.

## Problem

Two README caveats block users from using hosted providers. Root cause: `api_key="local"` is hardcoded in `llm_client.py:512`.

## Scope

- Add `api_key` field to `EngineConfig`
- Add `llm.api_key` to `config.yaml.example`
- Pass api_key through `_get_client()` cache key and constructor
- Update README caveats

## Out of Scope

- Secret encryption, vault integration, per-endpoint keys
