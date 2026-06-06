# Ideas — Pipeline Improvements from Save Analysis

**Source:** `saves/noir--1930s-2026-06-02/` (turns 1–17)  
**Full findings:** See `plans/findings/NOIR-EV.md`, `CONSOLIDATED-EV-FINDINGS.md`

## Arc & Thread Management

### Problem
Thread progress updates replace previous values entirely (single-string replacement), burying investigative findings in prior_history. Storytell does not receive resolved arcs — only narrate gets them via TTL-filtered list at `narrate.py:56`. All saves confirm zero arc_resolves across 77+ turns combined; visible goals become obsolete but never update or resolve.

### Proposed Fixes

- [ ] **Resolved Arcs for Storytell** — Narrate already receives resolved_arcs with TTL filtering (default 3 turns), showing resolution text AND goal_context via `_arc.j2` lines 14-15. Add it to `_storytell_messages()` params at `extraction.py:248-269`. Helps storytell understand why arcs ended the way they did for better successor generation.
- [ ] **Thread Progress as Append List** — Replace single-string `thread.progress` with `{progress_log: [str, ...], current_summary: str}` where updates append rather than replace. Cap log at N entries per thread or unlimited. Keep `current_summary` as last entry for display in prompts.

### Thread Update Frequency (New)

- [ ] **Band-aligned gating** — In `_apply_thread_updates`, check ruling band before merging LLM-emitted updates. If band is fail/setback/partial/no_roll AND the update isn't a genuinely new thread_add, discard it. Enforces instruction at `storytell_system.j2:138-140` ("do NOT mark threads as affected for failed checks").
- [ ] **Minimum interval enforcement** — Track last-update turn per-thread-id in state. If LLM tries to update a thread within 2 turns of its previous update without adding new progress content, reject it. Prevents the T1→T2 `the_imperial_leak` overwrite pattern seen across all saves.
- [ ] **Pre-emission validation** — Before merging any `thread_update`, compare old vs new progress text similarity (simple string diff). If LLM emits a thread update with identical or near-identical content to previous turn, reject it and log warning.

---

## Condition Lifecycle

### Current Behavior
Python auto-expires conditions at `turn.py:1011-1030`: when `turns_remaining` hits 0, condition is removed from state entirely and an event logged. Permanent conditions (no turns_remaining field) persist indefinitely forever. Zombie save had 5 conditions added across 34 turns with zero present in final state — effectively dead code.

### Proposed Change

- [ ] **Condition age + system guidance instead of hard expiration** — Give LLM visibility into condition age in prompts alongside existing TTL countdown. Add system prompt guidance: "Consider conditions > 4 turns as requiring pruning soon unless narration demands they remain." Shifts lifecycle management partially to the LLM rather than Python silently deleting them.

---

## What Was Considered But Rejected

| Idea | Reason for Rejecting |
|------|---------------------|
| Momentum trend direction | Narrator probably doesn't need it; storytell could use but token cost vs benefit unclear at this stage |
| De-escalation magnitude / narrative velocity raw floats | Already consolidated into directive string ("Pressure"/"Breathe"); adding raw values adds system prompt weight without clear payoff |
| Scene age + combat urgency display | 15-25 tokens is more than others; Python already uses it for directives — if narrator can't self-correct from those, may not help enough to justify cost |
| Inventory/condition delta signals (this-turn changes) | Current handling works fine per assessment |