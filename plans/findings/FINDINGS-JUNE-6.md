# Findings — Iteration 1 (noir-1930s, 25 turns)

> Living document. Build onto with each game's findings. Bug fixes will be planned
> once enough cross-game data exists.
>
> Severity: **H**=high, **M**=medium, **L**=low

---

## Confirmed Bugs

| # | Severity | Title | Detail |
|---|---|---|---|
| B1 | M | **Ammo decrement uses wrong operation type** | State extractor calls `inventory_update` to remove ammo instead of `inventory_remove` (or conversely, all inventory mutations should use `update`). Result: ammo count does not persist. Root cause: inconsistent operation selection in state extraction — inventory_remove, inventory_update, and inventory_add are all valid but the extractor chooses the wrong one for decrements. |
| B2 | L | **game_over scene tag never set** | UI has a game-over modal that fires when `scene_tags` contains `"game_over"` (routes.py:210, CSS/HTML/JS present). The pipeline never sets this tag. PC reached `unconscious` (99 turns) at T25 instead. The mechanism exists but nothing triggers it. Was always a for-fun feature, low urgency. |
| B3 | M | **Thread lifecycle tracking loses threads** | `manifest_discrepancy` (failed T23) and `union_shadows` (resolved T10) exit active state but do not appear in `completed_threads` or `resolved_arcs` in the final state.yaml. They vanish from the tracking system entirely — no completion record, no archival. Only `council_corruption_war`, `police_internal_audit`, and `dockyard_strike` survive in `resolved_arcs`. |

---

## Needs Investigation

| # | Severity | Title | Detail |
|---|---|---|---|
| I1 | H | **Momentum death spiral — no recovery path** | See [MOMENTUM-BEAT-FINDINGS.md](MOMENTUM-BEAT-FINDINGS.md) for full root-cause analysis (MB-1 through MB-7). Summary: 42% hard difficulty against a +2-max character, no depth-based momentum catch-up, Breathe directive fires at momentum ≤ -2, floor relief injects de-escalatory beats during crisis. |
| I2 | M | **Beat system monotony in extended conflict** | See [MOMENTUM-BEAT-FINDINGS.md](MOMENTUM-BEAT-FINDINGS.md) (MB-1, MB-2, MB-3). Summary: Breathe dominates because urgent scene threads are unreliable; "; Resolve a Threat" append contradicts Breathe; floor relief overrides pressure beats with calm beats. |
| I3 | M | **Goal stagnation — sanitizer too slow to pivot** | The arc goal "Secure the missing witness before they are silenced by the union enforcement wing" stayed unchanged for T1–T15. The player had fought enforcers (T7), executed a thug (T9), interrogated the survivor (T10), and found Devon (T11) — all still under the same goal about "securing the witness." The sanitizer only runs every 5 turns and its output lags by one turn. Question: should the *storytell* stream be allowed to update the arc goal mid-cycle, or should the sanitizer run more frequently? |
| I4 | L | **Stale goal in narrate prompt at end-of-life** | T25 narrate prompt showed "Goal: Negotiate with Sergeant Keith to secure the manifests" even though Keith was killed at T22. The LLM wrote a death scene anyway, so impact was minimal, but this is a symptom of I3 (goal lags reality). |

---

## Feature Ideas & Improvements

| # | Severity | Title | Detail |
|---|---|---|---|
| F1 | M | **Premature latent thread activation by sanitizer** | `police_internal_audit` and `dockyard_strike` were activated from background→normal at T15 by the sanitizer, but neither had meaningful narrative presence. By game end, 5–6 active threads exceeded what the system could meaningfully track. The sanitizer evaluates the *narrative summary* and promotes threads based on keywords — but mentions in passing shouldn't equal activation. Suggestion: require N distinct narrative mentions across ≥2 turns before promoting a latent thread. |
| F2 | M | **arc_resolve sometimes produces incomplete state** | At T24, `council_corruption_war` was resolved (failed) and `police_retaliation_escalation` was added, but `visible_goal` remained "Negotiate with Sergeant Keith" — a dead, unnegotiable target. `goal_context` summarized the past but didn't project a new objective. The UI shows no resolved/previous threads, burying closure. The arc_resolve schema expects a forward-looking `visible_goal` — when it doesn't provide one, the UI strand goes dark. |
| F3 | M | **Sanitizer misnamed as compactor throughout code/docs** | The sanitizer is a thread/goal refiner that runs every 5 turns — it does *zero* context compaction. No trimming was triggered in 25 turns; the narrate prompt grew from 14k→19k chars monotonically. Every reference to "compactor" or "compaction" in the sanitizer context is misleading and should be removed or renamed to reflect its actual role: arc/thread governance. |
| F4 | L | **No impossible-action pathway in pipeline** | The ruling engine correctly marks `impossible: true` but the pipeline has no special handler for it. The `impossible_reason` text is passed through to the narrate prompt as an instruction and the LLM is trusted to handle it. This worked (T25 wrote a death scene correctly), but a dedicated impossible-action pathway could surface game-over, offer alternative actions, or short-circuit extraction. Currently an improvement area, not a bug. |

---

## What Works (Positive Signals)

- **Narrative coherence was strong.** The chronicle forms a legitimate 4-act noir tragedy with consistent voice, character continuity, and escalating stakes. The arc/thread system deserves credit for providing guardrails.
- **T20 sanitizer goal change was correct.** It pivoted "Use manifests to expose council corruption" → "Negotiate with Keith to secure the manifests," matching the alley standoff. Proves the mechanism works when timing aligns.
- **Extraction retry rate was excellent.** Only 1 retry in 25 turns (T12 storytell — arc_resolve field missing from LLM output). 99.2% extraction success rate. No rejections, no skipped streams.


---

## How to Add New Findings

1. Copy the table row from the relevant section.
2. Assign the next sequential ID: B4, I5, F5, etc.
3. Rate severity: H / M / L.
4. Add detail — what happened, where in the code, why it matters.
5. After 2–3 games of data, run a review pass to:
   - Promote recurring bugs tofix
   - Drop one-off findings that didn't replicate
   - Write prioritized bug-fix plans
