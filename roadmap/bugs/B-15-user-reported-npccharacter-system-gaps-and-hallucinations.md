---
title: "[User-Reported] NPC/Character System Gaps and Hallucinations"
status: done
urgency: 3
size: medium
created: 2026-06-24
ticket_id: B-15
resolved: 2026-06-24
labels:
  - engine
  - extraction
  - npc
  - scene-management
---
## Problem

Character extraction and management has multiple issues:

1. **All characters need motivation** — Every character (including unnamed NPCs) must have a `motivation` field
2. **Named NPCs need richer profiles** — Named characters should always have: `personality` + `motivation` + 2 of [`fear`, `leverage`, `bond`]
3. **Candidate hints too prescriptive/hallucinating** — Extraction inventing psych states for unnamed NPCs, creating fields that don't exist, hallucinating regular fields
4. **Location drift / NPC persistence** — NPCs not properly managed on location change (scene motion expunging? Setting to nearby?). NPCs drift across locations incorrectly.

## Fix Applied

### Items 1-3: Fixed

- **`extract_scene_system.j2`:** Unnamed NPCs now get `bio` + `motivation` (was `bio` only). Named NPCs now get `bio` + `personality` + `motivation` + 2 of {fear, leverage, bond} (was "at least 2 of" without mandatory motivation). Scene extractor effects changed from beat-like to psychological state format, reducing hallucination of non-existent fields.

- **`generate_seed_system.j2`:** Same field requirements applied to seed generation. Unnamed NPCs get `bio` + `motivation`. Named NPCs get `bio` + `personality` + `motivation` + 2 of {fear, leverage, bond}.

### Item 4: Not addressed

Location drift / NPC persistence on location change is a separate issue in the engine's scene transition logic (`ccya/engine/step/` or `scene.py`). This was not touched in this fix.

## Status

Items 1-3 are resolved. Item 4 (location drift) should be tracked as a separate ticket if it remains a problem.