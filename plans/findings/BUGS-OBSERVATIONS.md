# General Bugs & Observations

> Cross-cutting issues not specific to any single game. Bugs, design gaps, and
> small improvements for the engine / prompts / pipeline.
>
> Severity: **H**=high, **M**=medium, **L**=low  
> Confidence (for new/eval-only findings): **H**=data supports, **M**=pattern suggests needs cross-game validation, **L**=hypothesis only

> **Eval system gaps**: See [EVAL-FIXES.md](../EVAL-FIXES.md) for auto-checker additions needed to detect sanitizer lag (issue #3), thread accumulation (issue #5), and other eval blind spots.

---

## Confirmed Bugs

| # | Severity | Title | Detail |
|---|---|---|---|
| B1 | M | **Ammo decrement uses wrong operation type** | State extractor calls `inventory_update` to remove ammo instead of `inventory_remove`. `InventoryUpdate` model (`models.py:231-234`) has no `amount` field — Pydantic silently drops the key. `delta_builder.py:203-211` never patches amount. **Fixed** in cb623f4 (prompt now directs LLM to use `inventory_remove` with `amount` for decrements, `inventory_add` for additions). |
| B2 | L | **game_over scene tag never set** | UI has a game-over modal that fires when `scene_tags` contains `"game_over"` (routes.py:210). Pipeline never sets this tag. PC reached `unconscious` (99 turns) at T25 instead. Low urgency — was a for-fun feature. |
| B3 | M | **Thread lifecycle loses tracking on exit** [Confidence: L-M] | **Partially fixed** in cb623f4 (sanitizer `removed_threads` removed — all resolutions now go through `resolved_threads`). But `sanitizer_lifecycle` checker at `sanitizer.py:13` still requires `threads_removed` field that doesn't exist in events (events use `threads_resolved`). Verify remaining paths preserve archival. [Confirmed: baseline eval T9/T12 resolved threads reappear active (`store_confrontation`) — judge called this "thread resolution loop".] |
| B4 | M | **MB-5: Pressure counter desyncs when storytell emits no beat** [Confidence: H] | **ENGINE FIXED** — `turn.py:1108-1116` reads from `pending_gm_beat` after floor relief injection (post-floor-relief beat). But `pacing_directives` checker at `pacing.py:30-33` falls back to `state_snapshot` when `post_extraction_consecutive_pressure_turns` is missing, causing stale counter values. Eval-only issue. No-beat emission still clears pending state instead of explicitly setting null. |
| B5 | M | **Scene tags reset between consecutive turns** [Confidence: H] | **FIXED** — `grounded-state-extraction` plan (commits `f93b6740` + `02c6a91a`) removed `scene_tags` entirely from the pipeline. No more tag volatility because there are no tags. Location descriptions are now rewritten fully each turn (not just new details), providing consistent spatial grounding. |
| B6 | M | **Beat generation is non-deterministic — not every turn emits a gm_beat** [Confidence: H] | The storytell stream sometimes produces `gm_beat: null` on success turns (T5, T8 in Byzantium) and sometimes produces a beat. This means beat-driven pacing logic (consecutive pressure counter, beat_locked triggers) can fire or not fire based on extraction variation rather than consistent rules. The beat type alignment fix (`GM-BEAT-TYPE-ALIGNMENT.md`) addresses *what type* beats should be, but not *whether* beats are guaranteed to be generated. A beat should be required every turn — if storytell has nothing meaningful to add, it should emit `null` or `breathing_room` explicitly rather than `None`. [Confirmed: baseline eval Storytell emitted 0 actions (expected 4) at T3/T7/T13 when context was thin.] |
| B7 | H | **Location changes silently dropped from canonical state** — *confirmed in baseline* [Confidence: H] | Scene Extract correctly identified location transitions (`dustfall_main_street` → `assay_office`, etc.) but `_apply_delta` never persisted them to canonical state (T4, T8, T12). This is a new critical finding not present in noir or Byzantium runs. The judge called this "catastrophic" since it breaks all scene-scoped logic (NPC presence, scene tags, thread scope). **Note:** May be primarily a prompting issue rather than engine bug — recent commit tightened the prompt to address location changes explicitly. Verify if engine path (`_apply_delta`) is actually broken or just not receiving valid deltas from extraction. |
| B8 | H | **Momentum sign inversion** — *confirmed in baseline* [Confidence: M] | Baseline eval confirmed momentum deltas being applied with inverted signs: `fail` rolls produced +1 instead of -1 (Turn 4, auto-checker: `band=fail expected delta -1 but got +1`). At Turn 9 (`success` yielded 0 instead of +1). This was NOT flagged by noir findings (MB-4 treated it as a balance/design issue, not an engine bug). The judge traced this to `_apply_momentum_delta` reading stale state snapshots or applying inverted signs during mutation. [Auto-checker: `universal.momentum.band_delta` failed 1/13 at T4 with SYSTEM severity.] [Note: root cause attribution inferred by LLM judge from events.jsonl data — verify against source code before treating as confirmed.] |
| B9 | H | **Floor relief injection failure** — *confirmed in baseline* [Confidence: L-M] | **ENGINE FIXED** — `turn.py:1091-1106` correctly implements momentum guard (only fires floor relief from consecutive_pressure, not momentum floor). But `gm_beat_lifecycle` checker at `gm_beat.py:75-86` still expects `breathing_room` on ALL `beat_locked` turns without the `triggered_by_momentum` guard. Eval-only false positive. Only 2 turns of evidence across both runs — may be scenario-specific or scoring artifact. |
| B10 | M | **Inventory extraction hallucination persists across all runs** — *confirmed* [Confidence: H] | **Partially fixed** — validation at `turn.py:1563-615` blocks damage (missing targets, zero balances). But LLM still emits garbage into events.jsonl as raw emission values — eval assertions on emissions will continue to fail until extraction quality improves. Same root cause as C2 from EVAL-FINDINGS.md: no validation against current state before emission. |
| B11 | M | **Condition schema drift systemic across all runs** — *confirmed* [Confidence: H] | CONDITION_MODS only has 5 entries (`wounded`, `exhausted`, `drugged`, `frightened`, `bleeding`) but LLM generates new conditions via GM moves/narration (e.g., "rattled", "threatened") that become orphaned — mechanically inert because they have no mod definitions. **Confirmed by eval:** auto-checker `universal.conditions.orphan` fails 4/13 turns in baseline run, same pattern across all three runs (Jun 7: 5 fails, Jun 8: 5 fails). No validation rejects unknown conditions during apply_delta. **[SUPERSEDED]** Condition system is being replaced entirely by a ruling agent-driven approach with TTLs and gameplay effects — this bug will become moot once that redesign ships.** |
| B12 | M | **actions_quality assertion fires on system events** — *confirmed* [Confidence: H] | Auto-checker expects exactly 4 distinct actions for EVERY event in the stream, but system events (`kind="condition_expired"` at T3/T7, `kind="sanitizer"` at T5) have no storytell phase and legitimately produce 0 actions. **Confirmed by eval:** exactly 3 failures per run (idx 0/3/7), same turns across all three runs. These are false positives — the assertion should skip non-gameplay turns (events with a `kind` field). |
| B13 | M | **consecutive_pressure_tracking timing mismatch** — *confirmed* [Confidence: H] | Assertion reads storytell.gm_beat.type from THIS event's storytell output but meta.consecutive_pressure_turns captures state_snapshot at event creation time BEFORE extraction completed. For turns with multiple events where only some have storytell outputs (T3idx4, T10idx12/13), stale counter values get paired with wrong storytell types: e.g., T10idx13 has storytell=None but meta.counter=2 and pending_gm_beat={'type':'complication'} — stale data from a prior storytell call bumped consecutive_pressure_turns before being overwritten by this event's storytell output (which is None). **Confirmed by eval:** 6/13 turns fail in baseline run, same symptom across all three runs. |

---

## Feature Ideas & Improvements → Moved

| # | Severity | Title | Cross-ref |
|---|---|---|---|
| F1–F8 | — | **Moved to [FEATURE-IDEAS.md](./FEATURE-IDEAS.md)** | Thread activation, sanitizer naming, impossible-action pathway, arc_resolve state, storyteller actions doc, milestone feedback. See FEATURE-IDEAS.md for full details organized by subsystem. |

---

## Observations (Unaddressed)

### O1. Inventory durability gates — prevent invalid removes

Items that don't exist in inventory shouldn't be removable. More rarely, items that DO exist get removed when they shouldn't be (narrative described consideration, not consumption). Need a validation layer: `inventory_remove` for an ID not in state should warn/skip; items with a "durable" flag shouldn't be removable through consumption.

### O2. Resolved scene threads should purge on location change

When the player leaves a location, scene-scoped threads from that location are stale. The sanitizer should auto-close (resolve with `superseded`) any scene-scoped thread whose associated location is no longer current.

### O3. Thread cap: 2 arc + 1 scene

Current `thread_max_active` config is monolithic. Should split: max 2 arc-scoped active threads + 1 scene-scoped active thread. Any more is overwhelming for both the LLM and the player. Exceeding the cap should demote the least-recently-updated active thread to background.

### O4. Auto-demote arc threads to latent [FIXED — step 01.3a + step 02.1]

Arc threads that haven't been updated in N turns should auto-demote: normal → background after 5 turns without progress, background → latent after 10. Urgency should decay the same way. Currently no decay mechanism exists. **BZ1 (Byzantium) confirms this is still happening in production** — `broken_defense`, `looting_scourge`, `coinage_panic` accumulated progress entries across all 31 turns without any demotion or resolution. The decay mechanisms in `02-thread-lifecycle.md` Steps 2.5–2.6 may not be wired correctly or are insufficient.

**Root cause**: Sanitizer template (`sanitize_thread.j2`) does not explicitly instruct cleanup of stale background threads — it only asks about narrative resolution, urgency, active status, and progress entries. The LLM keeps inactive threads because they're "still relevant to the war." No temporal decay instruction exists in the sanitizer prompt.

**FIXED**: Step 01.3a updated `_apply_thread_updates()` to fire auto-latent demotion every turn (not gated on mutation) so stale active threads reliably get `active=false` set after 3 turns of no updates. Step 02.1 added explicit temporal decay cleanup instruction to sanitizer template (`sanitize_thread.j2`) instructing the LLM to remove inactive latent threads with no progress_updates for multiple sanitizer cycles.

**Eval gap**: No auto-checker validates thread accumulation or decay behavior. See [EVAL-FIXES.md](../EVAL-FIXES.md#issue-5-background-thread-accumulation) for specific checks needed (`check_inactive_thread_age`, `check_accumulating_threads`).

### O5. Thread ordering by most recently updated

Threads in prompts and UI should be ordered by `last_updated_turn` descending, including completed/resolved threads. Currently they render in whatever order they appear in state. Recent activity should rise to the top.

### O6. Latent thread activation ceiling

Compactor/sanitizer should be instructed to keep total active threads at 3-5 max, and only activate a latent thread when another thread has been resolved/archived. Currently it activates based on narrative keyword density. Simple instruction: "Never have more than 5 active threads at once. Before activating a new thread, one must be resolved or demoted."

### O7. Scene extraction should accumulate tags, not replace them [OBSOLETED]

**OBSOLETED** — `grounded-state-extraction` plan (commits `f93b6740` + `02c6a91a`) removed `scene_tags` entirely from the pipeline. No accumulation logic needed because the field no longer exists. B5 is now fixed by removal rather than accumulation.

### O8. Beat generation should be mandatory every turn

The storytell stream's `gm_beat` field is sometimes `None` — this happens more often on success turns where the LLM doesn't generate a beat unprompted. The beat system needs a guaranteed beat every turn: if storytell has nothing meaningful to add, it should default to `breathing_room` (or `null` for the beat field, not None). Currently the absence of a beat is treated differently from an explicit `null` beat, which breaks the consecutive pressure counter and beat_locked logic that depends on consistent beat type reading.

---

## Completed / Superseded

### B11. Condition schema drift [SUPERSEDED]

**Status:** SUPERSEDED — condition system being replaced by ruling agent-driven approach

CONDITION_MODS only has 5 entries (`wounded`, `exhausted`, `drugged`, `frightened`, `bleeding`) but LLM generates new conditions via GM moves/narration (e.g., "rattled", "threatened") that become orphaned — mechanically inert because they have no mod definitions. **Confirmed by eval:** auto-checker `universal.conditions.orphan` fails 4/13 turns in baseline run, same pattern across all three runs (Jun 7: 5 fails, Jun 8: 5 fails). No validation rejects unknown conditions during apply_delta.

**Superseded by:** F-I10 in FEATURE-IDEAS.md — ruling agent will handle conditions, difficulty, and impossibility directly. TTLs and gameplay effects move into the ruling extractor. This bug will become moot once that redesign ships.

**See also:** [PRIORITIES (Previously Fixed)](./PRIORITIES.md#previously-fixed-for-reference)
