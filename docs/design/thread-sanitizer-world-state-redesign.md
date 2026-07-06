# Thread Sanitizer World State Redesign

> **Status:** scoping
> **Related tickets:**
> - [I-30](../../roadmap/improvements/I-30-thread-sanitizer-world-state-replacement-never-fires.md) — thread sanitizer world_state replacement never fires (scoping)
>
> **Related designs:**
> - [Seed Two-Step Design](./seed-two-step-design.md) — seed world_state injection at game start

## Problem Statement

The thread sanitizer's world_state replacement mechanism exists in code and prompt but never fires in practice. World state facts (seed/baseline canon) persist unchanged across all sanitizer runs and all examined game sessions. The entire thread-to-world-state promotion pipeline is dead code.

### How it's supposed to work

1. Storyteller resolves a thread via `thread_resolve` with a `world_state_candidate` string
2. Engine stores the candidate in `state.world_state_candidates`
3. Thread sanitizer runs every N turns, passes candidates as context to LLM
4. LLM should return a complete replacement `world_state` array
5. Engine does atomic swap via `state.set_world_state(...)`

### How it actually works

- Storyteller rarely emits `world_state_candidate` on thread resolution
- Candidates list is always empty in examined saves
- LLM prompt includes candidates as context but no explicit trigger to return `world_state`
- LLM responses never include the `world_state` key
- Atomic swap never fires — seed canon facts persist forever

### Root causes

1. **Storyteller never emits candidates** — `record_system.j2` documents `thread_resolve` but doesn't explain `world_state_candidate` or when to use it (noted as LEFT AS-IS in I-29 prompt audit)
2. **Sanitizer prompt has no explicit trigger** — candidates shown as context but no instruction that says "if candidates exist, you MUST return world_state"
3. **Complete replacement semantics are hard** — LLM must include ALL existing facts plus new ones; easy to skip if no change perceived
4. **No feedback loop** — if the LLM skips world_state, the engine silently does nothing. No log, no warning, no fallback.

### Impact

- World state facts never change mid-game regardless of narrative events
- TTL expiry via `expire_world_state_facts()` runs as a separate path in turn.py but seed canon facts with `permanent: True` never expire
- The thread-to-world-state promotion pipeline is dead code
- E-7 eval claims "world_state evaluation working" — contradicted by our investigation

## Design Goals

1. **World state facts should change mid-game** when narrative events warrant it
2. **Mechanism should be reliable** — deterministic or at least explicit, not LLM-dependent on a field the LLM consistently skips
3. **Minimal prompt complexity** — don't add more fields the LLM will ignore
4. **Clear ownership** — who writes world state facts? Storyteller? Sanitizer? Both? When?

## Options Under Consideration

### Option A: Storyteller directly writes world_state via extraction

- Add `world_state_add` and `world_state_remove` as first-class extraction fields
- Storyteller emits these directly in `thread_resolve` or as separate fields
- Engine applies them immediately via `apply_delta` or direct mutators
- No sanitizer involvement — world state changes are turn-level, not batched
- Pros: direct, no waiting for sanitizer cadence, storyteller has full context
- Cons: adds more fields to storyteller prompt, storyteller may not reliably use them

### Option B: Sanitizer directly promotes candidates (no LLM evaluation)

- When a thread resolves with `world_state_candidate`, auto-promote it into `world_state`
- No LLM evaluation step — if the storyteller said it's worth proposing as a candidate, it's worth adding
- Keep TTL expiry as the only removal mechanism
- Pros: deterministic, no prompt complexity, candidates serve as explicit storyteller intent
- Cons: less curation — no LLM filtering of redundant or stale facts

### Option C: Fix the sanitizer prompt/sanitizer flow

- Add explicit instruction: "if candidates exist, you MUST return world_state"
- Simplify the replacement task — don't ask for ALL facts, ask for "facts that changed"
- Add logging/warning if candidates exist but LLM returns no world_state
- Pros: keeps existing architecture, gives LLM curation ability
- Cons: requires prompt engineering that may or may not work, LLM may still skip it

### Option D: Hybrid — storyteller proposes, sanitizer curates

- Storyteller emits `world_state_candidate` on thread resolution (make this explicit in prompt)
- Sanitizer auto-promotes candidates into world_state (no LLM evaluation of world_state)
- Sanitizer still handles thread progress/urgency/dormancy as it does now
- Pros: combines explicit storyteller intent with deterministic promotion
- Cons: loses LLM curation of world state facts

## Decision Criteria

- **Reliability:** does the mechanism actually fire in practice?
- **Prompt complexity:** does it add fields the LLM will ignore?
- **Architectural clarity:** is ownership clear (who writes, who curates, who removes)?
- **Minimal change:** don't redesign the entire thread system if only world_state needs fixing

## Open Questions

1. Should world state facts be scoped (global vs local) or should that be removed?
2. Should TTL expiry via `expires_turn` be the only removal mechanism, or should explicit removal be supported?
3. Does `Scene.world_state` need to be renamed to `WorldState.world_facts` as proposed in I-29?
4. Should candidates be promoted immediately on thread resolution, or only at sanitizer cadence?
5. What's the relationship between seed-injected world_state and mid-game world_state changes?

## Files

- `ccya/engine/thread_sanitizer.py` — `_apply_sanitization()` world_state swap
- `ccya/engine/turn_state.py` — candidate collection
- `ccya/engine/turn.py` — TTL expiry, async sanitize
- `ccya/prompts/sanitize_thread.j2` — world_state evaluation instructions
- `ccya/prompts/record_system.j2` — storyteller thread_resolve schema
- `ccya/models/state.py` — `ThreadResolution.world_state_candidate`, `WorldState.world_state_candidates`, `Scene.world_state`
- `ccya/state/delta_builder.py` — inventory/NPC delta application (for comparison on how extraction fields are applied)
