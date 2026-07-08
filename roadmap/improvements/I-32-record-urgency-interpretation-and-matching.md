---
title: "Record prompt: restore urgency interpretation rules and semantic matching guidance"
status: completed
urgency: 3
size: medium
created: 2026-07-08
ticket_id: I-32
labels:
  - record
  - thread-lifecycle
  - pacing
plan: plans/I-32-record-urgency-interpretation-and-matching.md
---

# I-32: Record Prompt — Urgency Interpretation & Semantic Matching

## Problem

After commit a1d05285, Record's prompt was stripped of all urgency guidance. The system prompt now says "Default: emit nothing" with no criteria for when to escalate urgency. Result: all 3 Phase 2 eval runs stayed in SETUP for 15 turns — no phase transitions occurred because no urgent threads were created.

## Key Decisions

### 1. Don't fully revert a1d05285

Commit a1d05285 was right about one thing: Record shouldn't **force** premature resolutions. These removals were legitimate:
- "3+ turns unaddressed → resolve" — forced premature closure
- Curtain Call rules — engine-enforced, not Record's call
- "Consolidate toward main arc thread" — premature
- "Target 3-4 threads" — pressuring artificial management

### 2. Rewrite as interpretation rules, not corrective rules

Record needs to know when the narrator's portrayal warrants urgency changes. These are **interpretation rules** (translate narrator → urgency), not **corrective rules** (force state changes).

#### Urgency interpretation rules to add to record_system.j2:

```
## Thread urgency interpretation

The Narrator controls thread portrayal. Your job is to translate that portrayal into urgency labels.

**Escalate to urgent when:**
- The narrator describes a threat as immediate/imminent (armed, approaching, time-sensitive)
- A background thread's NPC appears or the thread resurfaces in narration
- Scene phase is CLIMAX — at least one thread MUST be urgent

**Demote to background when:**
- The narrator describes a thread as faded/distant/past
- An NPC associated with the thread departed
- A thread has been dormant for 6+ turns

**Set dormant: true when:**
- The associated NPC departed
- The thread is fading and unlikely to resurface soon
- You're resolving the thread (thread_resolve)

**Set dormant: false when:**
- The associated NPC is present again
- The thread resurfaces in narration
```

#### CLIMAX awareness rules to add to record_system.j2:

```
## CLIMAX phase

If `scene_phase` is CLIMAX:
- At least one thread MUST be urgent. If none are, set the most relevant to urgent.
- Prefer `thread_resolve` for the main pressure thread.
```

### 3. Record CAN promote (not just demote)

Record's `thread_update` schema allows full bidirectional control:
- `urgency: urgent` — promote
- `urgency: normal` — demote
- `dormant: true/false` — toggle
- `thread_resolve` — remove from active list

There's no constraint limiting Record to demotion only. The gap is **interpretation guidance**, not capability.

### 4. Thread summary format — event-mappable (Option A)

Record sees abstract thread summaries and must fuzzy-match them against prose:
```
[THREAT - normal] sabotage_pattern: "A series of deliberate damages to merchant vessels suggests a coordinated effort."
```
vs.
```
"armed men with weapons pursuing you down the cliffside"
```

The summary describes *implications* ("suggests a coordinated effort"), not *events*. Concrete summaries solve this without adding complexity:
```
[THREAT - normal] sabotage_pattern: "Saboteurs damaging merchant vessels at the docks"
```
- "saboteurs" matches "armed men"
- "vessels" matches "pursuing you"
- No schema change, no extra rendering

### 5. `last_updated_turn` — add to user prompt

Record needs to know which threads are stale vs fresh. A thread last updated at T1 is unlikely to have new developments at T8. Add `last_updated_turn` to the thread rendering in `_arc.j2`.

Instructions for Record: "If a thread has `last_updated_turn` ≥ 6 turns ago and is still `normal` urgency, consider escalating to `urgent` — it may have been ignored by the player."

### 6. Beat candidates event capture ordering bug

Unrelated but discovered: `beat_candidates` is empty on every turn in events. Event dict built at `turn.py:619` reads `state.meta.beat_candidates` BEFORE async world step runs (which writes candidates at `turn.py:792`). Fix: capture from `extraction.world.output` or move event write after world step.

## Scope

- [ ] Rewrite urgency interpretation rules in record_system.j2
- [ ] Add CLIMAX awareness rules to record_system.j2
- [ ] Add "how to match" instruction to record_system.j2
- [ ] Optionally: render `last_updated_turn` in record_user.j2
- [ ] Fix beat_candidates event capture ordering in turn.py
- [ ] Re-run eval to verify phase transitions occur

## Why This Matters

Without urgency escalation, the pacing engine's primary trigger (`thread_urgency_count > 0`) never fires. The engine can't transition from SETUP→RISING→CLIMAX. The narrator generates good prose but Record has no guidance to translate that prose into thread urgency changes. The two systems are disconnected.
