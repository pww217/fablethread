# Eval Framework Parity Findings

Eval framework does not perfectly mirror the core engine pipeline. These gaps explain why eval scores under-report live quality.

## Finding 1: Event/Snapshot Timeline Mismatch

Event written to events.jsonl at `turn.py:1132` happens **before** compaction runs (line 1140-1148). The state snapshot injected into the event would also be pre-compaction if done inside `run_turn()`. But the eval runner reads state from disk after `run_turn()` returns, which is **post-compaction**.

Result: judge sees pre-compaction events but post-compaction state diffs. They're misaligned — a compaction turn's narrate prompt shows a large chronicle tail, but the snapshot already has recent_events pruned and timeline compacted. The judge can't reconcile why narrate had more context than the snapshot suggests was available.

## Finding 2: Silent Phase Discarding / No Partial-Turn Detection

Server SSE streams `("token", chunk)`, `("phase", dict)`, `("complete", TurnResult)` to the client via routes.py:103-156. The eval runner silently consumes all yielded values (runner.py:480-493) with no error handling for partial turns, errors, or unexpected phase types.

Compaction yields two additional phases (`compact_start`, `compact_done`) that the runner discards into `_`. The judge trace can't detect compaction timing or whether it succeeded.

No check exists to verify all expected pipeline phases completed (rules_start/rule_done → narrate_start/narrate_first_token/narrate_done → extract_start/extract_done). A failed LLM call mid-narration would leave a half-written event with no error flag in the runner.

## Finding 3: Missing `state_snapshot` in Engine Events — Eval-Only Injection

The engine writes events to events.jsonl without any state_snapshot field (turn.py:1103-1132). The eval runner injects it as a post-hoc addition at runner.py:538-540 via `_inject_state_snapshot()`.

This means the event and snapshot are from different pipeline points. The engine has no knowledge that a state_snapshot is expected, so there's no guarantee of consistency between what was used to build prompts (pre-delta state) and what gets recorded as "state after turn" (post-delta). In live gameplay this doesn't matter because the UI reads fresh state from disk; in eval it creates ambiguity about whether extraction errors reflect engine bugs or timeline mismatches.

## Finding 4: Per-Judge Field Filtering Creates Blind Spots

`judge.py:_JUDGE_EVENT_FIELDS` gives each judge a different subset of event fields:
- `state_correctness`: gets applied/rejected, extraction outputs, state_snapshot — but **no narrate_prompt** (can't assess narration quality)
- `narrative_interplay`: gets narrate output, scene/state/progress outputs, meta/scene/pc arc snapshot keys only — **no rules prompt**, no full prompts
- `prompt_pipeline`: gets ALL rendered_system/rendered_user/full extraction data — but **no state_snapshot** (can't assess whether prompts reflected actual game state)

Cross-judge comparison is unreliable because each judge sees a different slice of the same turn. The `system_cohesion_score` judgment would need to reconstruct a coherent picture from three judges with complementary blind spots, not overlapping visibility into any single turn.

## Finding 5: Event Dedup via `__metadata__` Splits Timeline; Compaction Detection Is Heuristic-Only

Event dedup relies on `event.get("__metadata__")` (judge.py:486) to separate metadata from turn events. The compaction detection in `_is_compaction_turn()` uses heuristics — checking for `chronicle_append`, `recent_events_compact`, or a `compaction_fired` flag that may not exist in older event formats.

The judge trace has no explicit signal identifying which turns had compaction, what the timeline looked like before/after, or whether compaction succeeded. The `_COMPACTION_WINDOW = 1` includes ±1 turns but doesn't distinguish between a real compaction and a coincidental chronicle append from another source.

## Investigation Approach

Each finding should be investigated separately to determine:
- Is this a code bug (engine does something wrong) or a design gap (eval needs to capture more data)?
- What minimal change achieves parity without regressing live gameplay?
- Does fixing it require engine changes, runner changes, judge trace changes, or all three?

Priority order suggested by impact on eval scores: Finding 3 → Finding 1 → Finding 4 → Finding 5 → Finding 2.
