# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-08T05:15:31.367651+00:00 · **Finished:** 2026-05-08T05:16:37.588665+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260508T051531Z_rj__2hau`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260508T043904Z__egguzof`

## Judge Summary

**Mechanical:** 2/5  
**Narrative:** 3/5  
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 3/5
- narrate: 3/5
- extract_scene: 2/5
- extract_state: 3/5
- extract_progress: 1/5

**Trace:** [`full_cycle.trace.md`](full_cycle.trace.md)
**Judge response:** [`full_cycle.judge.md`](full_cycle.judge.md)

## ✅ No flags

No regressions, retries, failures, or judge score drops detected.


## Auto-Checker

**16 passed, 5 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ❌ | rolled=True |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 1 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed Keys'] |
| 2 | `rules.rolled` | ✅ | rolled=True |
| 2 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] not found |
| 2 | `extract.progress.quest_updates` | ✅ | quest_updates[settle_the_debt] found |
| 2 | `universal.recent_events_add.turn_stamped` | ❌ | 2 entries had turn=0/null instead of 3: ['Aren Voss successfully paid off the debt to Caron, and the ledger has been marked.', 'A red-haired man in boiled leather has approached Aren Voss, eyeing his coin with predatory intent.'] |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Seems', 'Credits', 'Don'] |
| 3 | `rules.rolled` | ✅ | rolled=True |
| 3 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.location_change.applied` | ✅ | (no change) |
| 3 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 3 | `universal.npc_mention.extracted` | ✅ | 5 candidates skipped (likely locations/items, not NPCs) |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | Walk over to Caron's table and sit down across f… | 955 (+0) | 2285 (+3) | 1993 (+6) | — | 2645 (+10) | 0 | 0 | 26.40 |
| 3 | I slide 500 credits across the table to Caron an… | 1026 (-4) | 2593 (-175) | — | — | 2988 (-30) | 0 | 0 | 18.64 |
| 4 | I find Halden by the town well and offer to carr… | 1038 (+0) | 3040 (-65) | — | 2172 (-7) | 2891 (-116) | 0 | 0 | 21.16 |
|  | TOTALS | 3019 | 7918 | 1993 | 2172 | 8524 | 0 | 0 | 66.21 |

**Total turns:** 3 · **Total duration:** 66.21s · **Avg/turn:** 22.07s
**Total tokens in:** 23,626 · **Total tokens out:** 18,291 · **Total LLM time:** 66.1s
**Total retries:** 0 · **Total parse failures:** 0

