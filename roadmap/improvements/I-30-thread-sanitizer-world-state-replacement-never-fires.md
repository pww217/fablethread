---
title: "Thread sanitizer world_state replacement never fires"
status: idea
urgency: 3
size: large
created: 2026-07-06
ticket_id: I-30
labels:
  - engine
  - thread-sanitizer
  - world-state
  - storyteller
design: docs/design/thread-sanitizer-world-state-redesign.md
---

## Detail

The thread sanitizer's world_state replacement mechanism exists in code and prompt but never actually fires in practice. The LLM never returns the `world_state` key in its sanitizer responses, so seed/baseline canon facts persist unchanged across all sanitizer runs.

### How it's supposed to work

1. Thread resolves via `thread_resolve` → storyteller emits `world_state_candidate` string
2. Candidate stored in `state.world_state_candidates` (turn_state.py:283-291)
3. Thread sanitizer runs every N turns → prompt includes candidates as context
4. LLM should return complete replacement `world_state` array in sanitizer JSON
5. Engine does atomic swap: `state.set_world_state(...)` + clears candidates

### What actually happens

- Sanitizer runs on turns divisible by `sanitize_every` (default 5)
- LLM prompt includes "Current World State" and "World State Candidates" sections
- LLM prompt schema shows `"world_state": [...]` as an output field
- LLM responses never include the `world_state` key
- Code at thread_sanitizer.py:476-482 only swaps if `parsed.get("world_state")` is not None
- Result: seed canon facts (4 facts in cordyceps, 4 in golden-age, 2 in allied) persist unchanged forever

### Evidence

Examined all saves and eval runs:
- `saves/cordyceps-year-twenty-2026-07-04`: sanitizer ran T5, `changes_detail` has no `world_state` key
- `saves/cordyceps-year-twenty-2026-07-05`: 1 thread resolved, `world_state_candidates` empty, seed facts unchanged
- All eval runs: `sanitize_every=0`, sanitizer never runs
- No eval run shows world_state facts changing mid-game

### Root causes (hypothesized)

1. **Storyteller never emits `world_state_candidate`** — thread resolutions don't include candidate strings, so candidates list is always empty and the LLM has no context for world_state evaluation
2. **Sanitizer prompt asks LLM to evaluate candidates but provides no explicit trigger** — candidates shown as context but no instruction that says "you MUST return world_state if candidates exist"
3. **Complete replacement semantics are hard for LLMs** — the prompt asks the LLM to include ALL existing facts plus new ones in the replacement array, which is a large cognitive load and easy to skip if the LLM perceives no change needed

### Impact

- World state facts never change mid-game regardless of narrative events
- TTL expiry on `expires_turn` may not fire if the replacement never happens (TTL expiry runs in turn.py:131-144 as a separate path, but if the replacement never fires, expired facts persist via the seed canon)
- The entire thread-to-world-state promotion pipeline is dead code
- E-7 eval claims "world_state evaluation working" — this was either examining a different run or misinterpreting the seed canon as active evaluation

### Scope

This is a rethink, not a patch. Options to evaluate:
- Make the storyteller directly write world_state via extraction (bypass sanitizer entirely)
- Make the sanitizer directly promote candidates without LLM evaluation
- Fix the prompt/sanitizer flow so the LLM actually returns world_state
- Some hybrid approach

### Related tickets

- [E-7](../../roadmap/evals/E-7-clean-deep-dive-eval.md) — claims world_state evaluation working (finding #10), but our investigation contradicts this
- [E-11](../../roadmap/evals/E-11-fresh-eval-cycle-comprehensive-post-i28.md) — finding #5: TTL expiry not working
- [F-27](../../roadmap/features/F-27-world-world-state-shows-bloat-not-active-constraints.md) — done, about sidebar display
- [I-29](../../roadmap/improvements/I-29-engine-model-naming-audit.md) — naming: `Scene.world_state` should be `world_facts`

### Files

- `ccya/engine/thread_sanitizer.py` — `_apply_sanitization()` world_state swap (line 476-482)
- `ccya/engine/turn_state.py` — candidate collection (line 283-291)
- `ccya/engine/turn.py` — TTL expiry (line 131-144), async sanitize (line 728-733)
- `ccya/prompts/sanitize_thread.j2` — world_state evaluation instructions (lines 101-116)
- `ccya/prompts/record_system.j2` — storyteller thread_resolve schema (line 11)
- `ccya/models/state.py` — `ThreadResolution.world_state_candidate`, `WorldState.world_state_candidates`
- `ccya/models/state.py` — `Scene.world_state`
