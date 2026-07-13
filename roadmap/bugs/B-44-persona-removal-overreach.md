---
title: "EV persona presets removed in I-24 but only NPC personality removal was intended"
status: new
urgency: 3
size: medium
created: 2026-07-13
ticket_id: B-44
labels: []
design:
plan:
pr:
  url:
  branch:
---

## Description

### What happened

Commit `108ef2bb` ("I-24: Remove NPC personality field from state model and ev scripts") was intended to remove **NPC personality fields** (archetype labels like "Cold Pragmatist") from the turn engine, narration prompts, and state model. This was tracked in **I-23 Phase 4** where the ticket explicitly stated:

> "NPC personality field on NPCEntry (plus personality_label, personality_traits) is a label that duplicates what motivation/fear/leverage/ties already express."

However, the commit also removed **EV player persona presets** — the `ev/personality.py` module (78 lines) with player archetype presets ("Driven", etc.) and the `--personality` CLI flag support. The old eval runs still reference `personality: driven` in their `run-meta.yaml` files and the persona presets were still functional.

### Why it happened

The two systems used the same label — "personality" — which caused confusion during the I-23/I-24 cleanup sweep. The commit title "Remove NPC personality field" masked the broader removal of all personality/persona infrastructure, including the player-facing EV system.

I-23 Phase 4 referenced plan `plans/I-24-remove-npc-personality-field-plan.md` which did not exist separately; the personality removal was treated as part of a single sweep without clearly distinguishing between NPC personality (engine-side) and player persona presets (EV-side).

### What should happen

**Phase 4 evals can continue as-is** (following the generic LLM player prompt). But for the next eval round, player persona presets must be restored so players have distinct behavioral archetypes again.

**Solution:**

1. Restore `ccya/ev/personality.py` (or rename to `ccya/ev/persona.py`) with the player persona presets that existed before I-24. The identified them, they should be called **personas** (not personalities) to avoid the naming confusion.

2. Support `--persona <name>` CLI flag on `ev.py play` for LLM player sessions.

3. Persona injection into `_llm_session()` prompt — the system prompt should include persona guidance (e.g., "You are a driven operative in a noir setting...").

4. Store `persona: driven` in `run-meta.yaml` for future evals.

5. The NPC personality removal from I-24 stays — that was correct. Just separate the naming:
   - **NPC personality** → removed (correct decision)
   - **Player persona** → restored with renamed concept

### Naming convention going forward

- **Personality** = property of NPCs in state model (motivation/fear/leverage derived, NOT archetype labels) — already removed, don't restore
- **Persona** = LLM player behavioral preset in EV evals — needs to be restored

### Pre-I-24 reference state

The deleted `ev/personality.py` contained player persona presets. The git diff of `108ef2bb` shows it was 78 lines with presets. Can be reconstructed from `git show 108ef2bb^:ccya/ev/personality.py`.

### Findings from Noir 25-turn spot check (2026-07-13)

Run: `ev.py play --llm --turns 25 --pack noir-1930s --eval`

**950/975 checker PASS (97.4%).** Only failing checker: `extraction_retry_rates` — scores FAIL on every single turn (T1-T25). The checker logic appears broken — see **B-45** for the fix.

**Fix for B-44/B-45 combined findings:**

The checker is a session-level metric that was displayed per-turn. Fixed by adding `requires_all_events` metadata flag to checker system. Session-level checkers are now hidden in per-turn mode (`ev.py check 1 --all`) and shown in full-session mode (`ev.py check --all`).

**T21 extraction retry (real issue, addressed by B-45):** `record` extraction retry on T21 — `arc_resolve.resolution` received `None` (Pydantic error: `"Input should be a valid string"`). This is the only actual parsing failure in the run. The LLM returned a null resolution field when asked to resolve the arc during Thomas Reed interrogation. Handled by retry mechanism without data loss.

**Inventory canonical resolution warnings:** `resolve_inventory_canonical_id no match` fired on T13/T15 for items `tarnished_silver_lighter` and `maintenance_logs`. The LLM extracted inventory items whose canonical IDs didn't match any pack-defined item. The engine still applied them (amount=1) but could not canonicalize the name. This is a pack coverage gap, not a code bug.

**72 runs with `(phase_transfer_wait_delay_ms=None` warnings in T3/T6/T7/T10 — harmless debug metadata showing field is always `None` and gets logged as-is. Not a bug but indicates a `field_missing` or optional field surfacing as `None`.