---
title: "Seed threads never surface — stay dormant entire run"
status: scoping
urgency: 3
size: medium
created: 2026-07-01
ticket_id: I-19
labels: [threads, seeding, engine]
---

## Description

Seed threads generated during `prepare_seed` can stay dormant for the entire run, never contributing to convergence or gameplay. In golden-piracy:smuggler (15 turns), `navy_patrols` and `guild_bounty` stayed `dormant` for all 15 turns despite being in the arc's initial thread list.

This means the game starts with threads that the LLM never engages with, and the player never encounters the scenarios these threads represent.

## Evidence

Golden-piracy run (15 turns, 54 rolls):
- `navy_patrols`: dormant T1-T15, never updated
- `guild_bounty`: dormant T1-T15, never updated
- `imprisonment_risk`: dormant T1-T11, active T12-T15
- `naval_intervention`: active T8-T15
- `supply_sabotage`: active T1-T15
- `unmarked_cargo_mystery`: active T1-T15

Two seed threads (navy_patrols, guild_bounty) never surfaced. The player never encountered naval patrols or guild bounty scenarios despite them being part of the arc's initial setup.

## Root Cause

The thread sanitizer gives the LLM the current thread list with status, but the LLM only updates threads that are "relevant to the current scene." If seed threads describe scenarios not present in the current scene, the LLM ignores them. There's no mechanism to force the LLM to engage with dormant threads.

## Design Question

Should the engine auto-surface dormant threads, or is this the LLM's responsibility?

### Option A: Engine auto-surface
- After N turns of dormancy, the sanitizer injects a "thread reactivation" signal
- The world step generates a beat that brings the dormant thread into the scene
- Pro: guaranteed thread engagement, no threads lost
- Con: may force narrative in unwanted directions, reduces player agency

### Option B: LLM responsibility with stronger prompting
- Add explicit guidance to sanitizer prompt: "You MUST update at least one dormant thread every 5 turns"
- Add thread diversity constraint to ruling prompt
- Pro: preserves player agency, LLM can naturally weave threads in
- Con: LLM may still ignore threads, no guarantee of engagement

### Option C: Hybrid
- Engine tracks thread age (turns since last update)
- When a thread exceeds max_age (e.g., 8 turns), the sanitizer adds a "stale" flag
- The ruling prompt includes stale threads with higher visual weight
- Pro: gives engine control while preserving LLM narrative freedom
- Con: more complex, requires new config field

## Related
- E-7 thread audit findings
- B-5 (convergence starvation) — threads not building convergence
- Thread lifecycle system (`ccya/engine/thread_sanitizer.py`)

## Files to Review
- `ccya/engine/thread_sanitizer.py` — thread update logic
- `ccya/prompts/sanitize_thread.j2` — thread list presentation
- `ccya/prompts/ruling_system.j2` — ruling prompt thread context
- `ccya/engine/ruling.py` — ruling phase thread handling
