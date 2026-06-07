# General Bugs & Observations

> Cross-cutting issues not specific to any single game. Bugs, design gaps, and
> small improvements for the engine / prompts / pipeline.
>
> Severity: **H**=high, **M**=medium, **L**=low  
> Confidence (for new/eval-only findings): **H**=data supports, **M**=pattern suggests needs cross-game validation, **L**=hypothesis only

---

## Confirmed Bugs

| # | Severity | Title | Detail |
|---|---|---|---|
| B1 | M | **Ammo decrement uses wrong operation type** | State extractor calls `inventory_update` to remove ammo instead of `inventory_remove`. `InventoryUpdate` model (`models.py:231-234`) has no `amount` field — Pydantic silently drops the key. `delta_builder.py:203-211` never patches amount. **Fixed** in cb623f4 (prompt now directs LLM to use `inventory_remove` with `amount` for decrements, `inventory_add` for additions). |
| B2 | L | **game_over scene tag never set** | UI has a game-over modal that fires when `scene_tags` contains `"game_over"` (routes.py:210). Pipeline never sets this tag. PC reached `unconscious` (99 turns) at T25 instead. Low urgency — was a for-fun feature. |
| B3 | M | **Thread lifecycle loses tracking on exit** [Confidence: L-M] | Resolved/failed threads vanish from `threads[]` without appearing in `completed_threads[]` or `resolved_arcs[]`. Multiple resolution paths exist (storytell `thread_resolve`, `arc_resolve`, sanitizer `removed_threads`) but the sanitizer `removed_threads` path destroys records entirely. **Partially fixed** in cb623f4 (sanitizer `removed_threads` removed — all resolutions now go through `resolved_threads`). Verify remaining paths preserve archival. [Confirmed: baseline eval T9/T12 resolved threads reappear active (`store_confrontation`) — judge called this "thread resolution loop".] |
| B4 | M | **MB-5: Pressure counter desyncs when storytell emits no beat** [Confidence: H] | `turn.py:1074-1082` reads from `pending_gm_beat` after floor relief injection (fix IS in place). But when storytell emits no beat (`gm_beat=None`, 3/13 turns at T3/T7/T13), line 1061 pops pending_gm_beat entirely, causing the counter to read None and reset — even if a previous turn's pressure beat was preserved by floor relief. Auto-checker confirms: `consecutive_pressure_tracking` fails 6/13 turns (T1/T3/T5/T7/T9/T13) with [SYSTEM] severity. Root cause: no-beat emission clears pending state instead of preserving it or explicitly setting null. |
| B5 | M | **Scene tags reset between consecutive turns** [Confidence: H] | Scene extraction appears stateless per-turn — tags are cleared and re-established each extraction pass rather than building continuity. In Byzantium (31 turns), tags frequently flipped between `(empty)` and fully-populated states within 1-2 turns even when nothing mechanically changed (e.g., T10: `combat, visceral, tense` → cleared to `(empty)` → re-established; T12: cleared entirely; T13: `tense_refuge, recovery, impending_danger`). This breaks scene identity continuity and makes beat generation less predictable since scene tags feed into directive computation. The scene stream should accumulate/modify tags rather than wholesale replace them. [Confirmed in baseline eval: same volatility pattern observed.] |
| B6 | M | **Beat generation is non-deterministic — not every turn emits a gm_beat** [Confidence: H] | The storytell stream sometimes produces `gm_beat: null` on success turns (T5, T8 in Byzantium) and sometimes produces a beat. This means beat-driven pacing logic (consecutive pressure counter, beat_locked triggers) can fire or not fire based on extraction variation rather than consistent rules. The beat type alignment fix (`GM-BEAT-TYPE-ALIGNMENT.md`) addresses *what type* beats should be, but not *whether* beats are guaranteed to be generated. A beat should be required every turn — if storytell has nothing meaningful to add, it should emit `null` or `breathing_room` explicitly rather than `None`. [Confirmed: baseline eval Storytell emitted 0 actions (expected 4) at T3/T7/T13 when context was thin.] |
| B7 | H | **Location changes silently dropped from canonical state** — *confirmed in baseline* [Confidence: H] | Scene Extract correctly identified location transitions (`dustfall_main_street` → `assay_office`, etc.) but `_apply_delta` never persisted them to canonical state (T4, T8, T12). This is a new critical finding not present in noir or Byzantium runs. The judge called this "catastrophic" since it breaks all scene-scoped logic (NPC presence, scene tags, thread scope). |
| B8 | H | **Momentum sign inversion** — *confirmed in baseline* [Confidence: M] | Baseline eval confirmed momentum deltas being applied with inverted signs: `fail` rolls produced +1 instead of -1 (Turn 4, auto-checker: `band=fail expected delta -1 but got +1`). At Turn 9 (`success` yielded 0 instead of +1). This was NOT flagged by noir findings (MB-4 treated it as a balance/design issue, not an engine bug). The judge traced this to `_apply_momentum_delta` reading stale state snapshots or applying inverted signs during mutation. [Auto-checker: `universal.momentum.band_delta` failed 1/13 at T4 with SYSTEM severity.] [Note: root cause attribution inferred by LLM judge from events.jsonl data — verify against source code before treating as confirmed.] |
| B9 | H | **Floor relief injection failure** — *confirmed in baseline* [Confidence: L-M] | At T12, `beat_locked=True`, storytell emitted a pressure-type beat (`complication`), but pending_gm_beat stayed as `pressure` instead of being overridden by the floor-relief-injected `breathing_room`. This is the **opposite** of what MB-3 diagnosed (floor relief firing 15/16 times during crisis). Either there are two different failure modes: over-firing in some conditions, under-firing in others. [Auto-checker confirms 1 floor_relief failure at T12 with same symptom — beat_locked=True but pending_gm_beat.type='pressure' instead of 'breathing_room'. Only 2 turns of evidence across both runs — may be scenario-specific or scoring artifact.] |
| B10 | M | **Inventory extraction hallucination persists across all runs** — *confirmed* [Confidence: H] | State Extract emits `inventory_remove` deltas for items that do not exist or have zero balance (baseline T7/T8). Same root cause as C2 from EVAL-FINDINGS.md: no validation against current state before emission. F4 fix blocks the damage at runtime but LLM still emits garbage into events.jsonl as raw emission values — eval assertions on emissions will continue to fail until extraction quality improves. |
| B11 | M | **Condition schema drift systemic across all runs** — *confirmed* [Confidence: H] | Conditions added by State Extract (`heat_exhaustion`, `rattled`, etc.) lack corresponding entries in the engine's condition mod lookup table, so they don't affect dice rolls as intended (baseline: 8/13 turns). This is an extraction schema mismatch — the LLM emits valid-looking conditions but the engine doesn't recognize them for mechanical purposes. No validation rejects these "unknown" conditions during apply_delta. |

---

## Feature Ideas & Improvements

| # | Severity | Title | Detail |
|---|---|---|---|
| F1 | M | **Premature latent thread activation by sanitizer** | Sanitizer promotes threads from background→normal based on keyword mentions in narrative summary. Passing mentions activate threads. Suggestion: require N distinct mentions across ≥2 turns before promotion. Or: cap total active threads at a lower number (see thread cap observation below). |
| F2 | M | **Sanitizer misnamed as compactor throughout code/docs** | The sanitizer is a thread/goal refiner that runs every 5 turns — it does *zero* context compaction. Every reference to "compactor" or "compaction" in the sanitizer context is misleading. No trimming was triggered in the noir game; the narrate prompt grew monotonically from 14k→19k chars. |
| F3 | L | **No impossible-action pathway in pipeline** | Ruling engine correctly marks `impossible: true` but pipeline has no special handler. The `impossible_reason` is passed through to the narrate prompt and the LLM is trusted to handle it. Worked in noir (T25 death scene was correct), but a dedicated pathway could surface game-over, offer alternatives, or short-circuit extraction. |
| F4 | M | **arc_resolve incomplete state on pivot** | When an arc resolves and a successor is created, `visible_goal` sometimes stays on the old (dead) objective. The schema expects a forward-looking goal but the LLM doesn't always provide one, leaving the UI strand dark. [Confirmed: baseline eval had zero `goal_update` events across 13 turns despite narrative context shifting dramatically.] |
| F7 | M | **Storyteller actions list is valuable but undocumented** | The storytell stream consistently generates 4 actionable choices per turn (confirmed across 31 turns of Byzantium). This works well — it gives players meaningful tactical options that fit scene constraints. No existing plan or spec documents this as a designed feature. It should be formally specified in the storytell prompt and preserved. |
| F8 | L | **No milestone feedback when primary thread resolves** | When `family_extraction` resolved in Byzantium T30, the player received no narrative acknowledgment of achieving their primary goal — just a state transition to a new thread. Thread resolution should produce a narrative beat (brief summary of what was accomplished) rather than a silent state change. |

---

## Observations (Unaddressed)

### O1. Inventory durability gates — prevent invalid removes

Items that don't exist in inventory shouldn't be removable. More rarely, items that DO exist get removed when they shouldn't be (narrative described consideration, not consumption). Need a validation layer: `inventory_remove` for an ID not in state should warn/skip; items with a "durable" flag shouldn't be removable through consumption.

### O2. Resolved scene threads should purge on location change

When the player leaves a location, scene-scoped threads from that location are stale. The sanitizer should auto-close (resolve with `superseded`) any scene-scoped thread whose associated location is no longer current.

### O3. Thread cap: 2 arc + 1 scene

Current `thread_max_active` config is monolithic. Should split: max 2 arc-scoped active threads + 1 scene-scoped active thread. Any more is overwhelming for both the LLM and the player. Exceeding the cap should demote the least-recently-updated active thread to background.

### O4. Auto-demote arc threads to latent

Arc threads that haven't been updated in N turns should auto-demote: normal → background after 5 turns without progress, background → latent after 10. Urgency should decay the same way. Currently no decay mechanism exists. **BZ1 (Byzantium) confirms this is still happening in production** — `broken_defense`, `looting_scourge`, `coinage_panic` accumulated progress entries across all 31 turns without any demotion or resolution. The decay mechanisms in `02-thread-lifecycle.md` Steps 2.5–2.6 may not be wired correctly or are insufficient.

### O5. Thread ordering by most recently updated

Threads in prompts and UI should be ordered by `last_updated_turn` descending, including completed/resolved threads. Currently they render in whatever order they appear in state. Recent activity should rise to the top.

### O6. Latent thread activation ceiling

Compactor/sanitizer should be instructed to keep total active threads at 3-5 max, and only activate a latent thread when another thread has been resolved/archived. Currently it activates based on narrative keyword density. Simple instruction: "Never have more than 5 active threads at once. Before activating a new thread, one must be resolved or demoted."

### O7. Scene extraction should accumulate tags, not replace them

The scene stream extracts tags fresh each turn and submits them as a complete set — if tags aren't mentioned in the current turn's narration, they disappear. This causes dramatic tag flips between consecutive turns even when the scene hasn't meaningfully changed. The scene stream should receive the prior turn's tags and add/remove only what's explicitly changed, rather than submitting a wholesale replacement set. This is the root cause of B5 (scene tag volatility).

### O8. Beat generation should be mandatory every turn

The storytell stream's `gm_beat` field is sometimes `None` — this happens more often on success turns where the LLM doesn't generate a beat unprompted. The beat system needs a guaranteed beat every turn: if storytell has nothing meaningful to add, it should default to `breathing_room` (or `null` for the beat field, not None). Currently the absence of a beat is treated differently from an explicit `null` beat, which breaks the consecutive pressure counter and beat_locked logic that depends on consistent beat type reading.
