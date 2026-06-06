# Consolidated EV Findings — Cross-Game Analysis

**Sources:**
- `NOIR-EV.md` — noir save (17 turns, 1930s detective)
- `cordyceps-v1` — original cordyceps save (34 turns, zombie survival, gemma-4-26b-a4b-it-mxfp8)
- `cordyceps-v2` — fresh cordyceps save (26 turns, zombie survival, model unknown)
- `cordyceps-v3` — June 6 save (8 turns, zombie survival, Qwen3 ~25B-4bit)
- Code-level tracing from `turn.py`, `delta_builder.py`, `delta.py`

**Validation approach:** Every finding below was observed in MULTIPLE saves unless marked `[noir-only]`, `[zombie-v1-only]`, `[zombie-v2-only]`, or `[v3-new]`. Shared findings are real system issues, not save-specific noise.

Analysis covers **noir** (17), **cordyceps-v1** (34), **cordyceps-v2** (26), and **cordyceps-v3** (10) — 87 combined turns.

---

## Category 0: Beat Distribution is Radically Seed-Dependent [new]

### Finding 0.1: Beat profile flips entirely between runs with the same system
| Beat type | noir (17) | v1 (34) | v2 (26) | v3 (10) |
|-----------|:---:|:---:|:---:|:---:|
| complication | 0 | 11 | 1 | 2 |
| opportunity | 1 | 10 | 1 | 1 |
| pressure | 9 | 5 | 4 | 2 |
| revelation | 1 | 2 | 12 | 1 (T10) |
| breathing_room | 0 | 0 | 2 | 0 |
| twist | 0 | 0 | 1 | 0 |
| escalation | 0 | 0 | 2 | 0 |
| setback | 0 | 0 | 0 | 0 |
| callback | 0 | 0 | 0 | 0 |
| null | 5 | 6 | 4 | 4 (T2, T7, T8, T9) |

V3 adds a combat-heavy profile with late-game diversity improvement. T10's `revelation(environmental)` is the first non-pressure/complication/opportunity beat from storytell output. Null rate increased to 40% as combat wound management shifts scene to healing/safe mode.

**Implication:** Still valid. The system doesn't control beat distribution across runs.

### Finding 0.2: `breathing_room` in "Recent Beats" section but NOT in storytell output [v3-update]
V2 produced `breathing_room` from LLM output (T2, T9). V3 shows `BREATHING ROOM (ambient)` in the "Recent Beats" section at T6-T7 but these appear to come from beat_locked override, not storyteller self-generation. Storytell's own gm_beat output on those turns was `pressure(environmental)` and `null`. This suggests beat_locked+floor relief IS now reachable but still not LLM-driven.

---

## Category 1: GM Beat System — Confirmed Broken (All Saves, Some Improvement)

### Finding 1.1: Beat type diversity is limited but improving
Across 85 combined turns, only 7 of 9 beat types were ever produced. V3 added late-game diversity: T10's `revelation(environmental)` is the first revelation from storytell in this save. This may be a post-combat narrative shift effect rather than improved governance.

**Root cause corrected:** `last_n_beats` IS in the storytell prompt (rendered as "Recent Beats" at `storytell_system.j2:195-203`), and `## GM Beat` shows the current pending beat (F1.8). The LLM sees both beat history and current beat but ignores diversity instructions. The previous analysis was wrong about data not being available — the LLM just doesn't follow the guidance. See Finding 1.8 below.

### Finding 1.2: Architectural 1-turn beat lag
Still architecturally true. V3 confirms: narrate receives previous turn's beat. No change.

### Finding 1.3: beat_locked fires for the first time [v3-improved]
V3 T6-T7 show directive suffix "Resolve a Threat" (only appended when beat_locked=True). This was 0/77 across prior saves. **Mechanism unclear**: momentum never hit floor (min 0), directives never included "Pressure"/"Overwhelm". Possibly from engine_mirror commit e5af4b8 or a config change.

**Status:** PARTIALLY ADDRESSED. beat_locked now reachable but mechanism uncertain. The original root cause (counter keyed to directives, not beat types — F5.5) is still structurally present unless the commit changed this.

### Finding 1.4: Floor relief beats structurally blocked
Three-way blocker:
1. ~~beat_locked never fires~~ — NOW FIRES (T6-T7 v3), partially addressed
2. `pending_gm_beat` is almost never `None` because storytell generates a beat on ~62% of turns
3. Even on null turns, old beats persist — no clear-on-null logic still confirmed

**Status:** PARTIALLY ADDRESSED (blocker 1 resolved, blockers 2-3 remain). In v3, the breathing_room in Recent Beats at T6-T7 likely came from beat_locked override working, suggesting floor relief IS now reachable.

### Finding 1.5: `surface_as` diversity is worse than type diversity
V3: 5 emitted beats used only `event`, `environmental`, `npc_behavior`. Same limited pool as prior saves. The prompt guidance about surface variety is still ignored.

### Finding 1.6: No mechanism to clear pending_gm_beat on null storytell output
Still confirmed in v3. T2 (null beat), T7 (null beat), T8 (null beat) show no clearance. The only clearance paths remain TTL expiry or overwrite.

Null beat rate: T1(beat) T2(null) T3(beat) T4(beat) T5(beat) T6(beat) T7(null) T8(null) = 3/8 null (37%). Higher than prior saves but small sample.

### Finding 1.7: Breathe + stale beat occasionally works by accident
No v3 data for this — only one Breathe directive (T1) which had an opportunity beat, so no stale carryover to test.

### Finding 1.8: [CORRECTED] GM Beat section IS in storytell prompts (two separate fields)
**The previous analysis was wrong for v3.** There are two separate fields in the storytell user prompt:

1. **`## GM Beat`** — current/latest pending beat (shows type, surface_as, expires turn, and guidance text). Renders as "No beat currently carried over" when null.
2. **`## Recent Beats`** — historical list of last N beats (rendered at `storytell_system.j2:195-203`).

In v3, BOTH fields render correctly. T8's storytell prompt shows:
```
## GM Beat
Type: **BREATHING ROOM**
Surface: `ambient`
Expires: Turn 9
```
T9's storytell prompt shows:
```
## GM Beat
No beat currently carried over from the previous turn. Choose freely.
```
And Recent Beats shows the historical list.

The original F1.8 finding was based on v2 where the section may have been absent (possibly a v2-specific template rendering issue). In v3, the data reaches the storyteller through both channels. The LLM still ignores diversity guidance even with both current beat + historical data available — same root cause as F1.1.

**Status:** CORRECTED. Both sections render in v3. The problem is LLM noncompliance, not missing prompt plumbing.

### Finding 1.9: Breathe → Scene Imperative whiplash [zombie-v2-only]
Not observed in v3 (only 8 turns). Still possible.

### Finding 1.10: Non-breather beats generated during Breathe directive
V3 T1: Breathe directive + `opportunity(environmental)` beat. Same pattern — LLM doesn't align beat type with directive.

---

## Category 2: Thread System — Progress Overwrite Persists, Bloat Controlled (Mixed)

### Finding 2.1: Thread progress is single-string replacement
**STILL CONFIRMED in v3.** `bounty_escalation` updated every turn with overwriting progress text. T6 and T7 have identical text: "convoy engagement has escalated into a three-way crossfire involving automated drone patrols." The LLM can't see what it wrote last turn and repeats itself.

### Finding 2.2: Thread resolution states are semantically wrong
No thread_resolve in v3 (8 turns, no scene threads to resolve). Can't verify.

### Finding 2.3: Thread scope is consistently misclassified
v3 has zero scene-scoped threads — all 4 are ARC-scoped. This avoids misclassification but creates a different problem: **scene thread starvation.** No short-term narrative tension tracking at all. The pendulum may have swung from bloat (v1/v2) to starvation (v3).

### Finding 2.4: Thread urgency never decays
**STILL CONFIRMED in v3.** All 4 threads (`bounty_escalation` NORMAL, `settlement_intelligence` BACKGROUND, `internal_schism` NORMAL, `resource_scarcity` BACKGROUND) maintain identical urgency across 8 turns. `bounty_escalation` is updated every turn with progress but never changes from NORMAL to URGENT despite active combat.

### Finding 2.5: Most thread_updates carry no meaningful change
**STILL CONFIRMED in v3.** Every turn emits thread_update but only changes progress text. No urgency, active status, or summary changes. Worse: T6 and T7 have identical progress text (wasted tokens).

**New variant in v3:** world_state_add overlap — `highway_combat_engagement` (T3), `highway_sector_seven_combat` (T7), `sector_seven_skirmish_aftermath` (T8) are different IDs for the same fact. Also `technical_wreckage_sector_seven` emitted twice (T4 and T5) with the same ID — the LLM didn't check existing entries before re-adding.

### Finding 2.6: Arc-scoped threads never resolve
**STILL CONFIRMED in v3.** Zero thread_resolve across 10 turns. 4 arc-scoped threads persist unchanged. However, the thread list does NOT grow because thread_add is also zero — the stagnation problem is split from the growth problem.

**Updated nuance:** Arc-scoped threads don't resolve AND LLM never emits thread_add. Combined result: a stable but static thread list that never reflects narrative change.

### Finding 2.7: Thread resolve + update in same turn [zombie-v2-only, new]
Not observed in v3 (no thread_resolve at all). Still possible.

### Finding 2.8: Thread section bloat [updated]
**PARTIALLY ADDRESSED in v3.** Thread count stable at 4 across 10 turns (zero growth). No thread_summary expansion. However, world_state entries still accumulate monotonically: 3 seed + 5 LLM-added across 10 turns, with some overlap (same fact, different IDs).

The original finding's conclusion ("prompt is O(n) in turns played") is now split: thread section O(1) in v3, but world_state section still O(n). At 10 turns, 8 world_state entries (3 seed + 5 LLM) is manageable, but at 50 turns this would be ~30 LLM-added entries without cleanup.

### Finding 2.9: LLM autonomously creates threads [updated]
**ADDRESSED in v3.** Zero thread_add across 8 turns. The seed-time hard limits (commit 1ddf22bf) + prompt restraint examples (commit 59c39e9) are working for **addition** frequency. The system now has effective governance over thread addition — but the LLM over-indexes on "don't add threads" and now adds zero.

**Status:** Fixed for over-generation. New problem: under-generation of scene-scoped threads.

### Finding 2.10: Turn 20 missing `## threads` section [zombie-v2-only, new]
Not observed in v3 (insufficient turns). Still possible.

---

## Category 3: Pacing Computation — Same Signals, New Improvement

### Finding 3.1: Pressure/Overwhelm directives never fire
**STILL CONFIRMED across all 87 turns.**

| Directive type | noir (17) | v1 (34) | v2 (26) | v3 (10) | Combined |
|---------------|:---:|:---:|:---:|:---:|:---:|
| "" (empty) | 11 | 16 | 12 | 1 | 40 |
| Breathe | 4 | 7 | 3 | 1 | 15 |
| Scene Imperative | 2 | 5 | 4 | 6 | 17 |
| Scene Pressure | 1 | 6 | 6 | 1 | 14 |
| **Pressure** | **0** | **0** | **0** | **0** | **0** |
| **Overwhelm** | **0** | **0** | **0** | **0** | **0** |
| none | 0 | 0 | 0 | 1 | 1 |

Despite combat intensity (T3-T7 active firefights), the directive system never outputs "Pressure" or "Overwhelm" — always "Scene Pressure" or "Scene Imperative" because urgency comes from scene staleness, not from scene urgency.

### Finding 3.2: "Breathe" fires during active tension
**STILL CONFIRMED in v3.** T1 is "Breathe" while the player is actively hiding from/setting up ambush against a hostile convoy. Same conflation of mechanical velocity drop and narrative relief.

### Finding 3.3: Scene Imperative is a label with no teeth
**STILL CONFIRMED in v3.** T4-T8 all have "Scene Imperative" but storytell behavior doesn't observably change — still emits thread updates for minor progress, still generates similar beat types. The recent commit (808e7709) forces `outcome_hint=transition` on Scene Imperative but this doesn't change LLM behavior.

### Finding 3.4: No hysteresis
Not enough data in v3 (8 turns with one Breathe→Scene Pressure→Scene Imperative ramp that feels organic). Still structurally possible.

---

## Category 4: Arc System — Never Resolves, Never Updates (All Saves)

### Finding 4.1: Zero arc progression across 85 combined turns
**STILL CONFIRMED.** V3 adds 8 more turns to the count: 0 arc_resolve, 0 goal_update. Visible goal unchanged from seed despite narrative progression from hidden ambush → open combat → drone fight → retreat.

### Finding 4.2: Thematic question is ignored
Can't verify from event data alone but no evidence of improvement. V3's zombie survival story is combat-driven with no thematic engagement.

### Finding 4.3: goal_context never updates
Not enough data in v3 (8 turns, same arc). Presumed still broken.

---

## Category 5: Cross-Cutting Infrastructure Issues

### Finding 5.1: NPC continuity is fragile — `last_seen` lacks context
Not enough data in v3 (8 turns of combat with no NPC presence changes). Unclear if improved.

### Finding 5.2: World state usage is improving but overlapping
**PARTIALLY ADDRESSED in v3.** LLM adds world_state entries consistently (5 entries across 8 turns, roughly 1 per actionable turn). But entries overlap: `highway_combat_engagement` → `highway_sector_seven_combat` → `sector_seven_skirmish_aftermath` are the same fact with different IDs, and `technical_wreckage_sector_seven` was emitted twice (T4 and T5) with same ID.

The LLM can use world_state now (improvement over v1's underuse) but doesn't check existing entries before adding (same problem as F2.5 thread overlap).

### Finding 5.3: Conditions system is NOT dead code [v3-corrected]
**CORRECTED.** V3 shows `bleeding arm` condition active from T5-T10 with proper lifecycle:
- T5: Added after shrapnel hit (combat consequence)
- T6-T8: Persisted through combat
- T9: Auto-expired (turns_remaining hit 0) then re-added by storyteller on failed stitch attempt
- T10: Removed after Darlene successfully stitched the wound

The previous analysis was based on v1 only, where conditions were unused despite being a zombie survival game. In v3's combat scenario, the LLM used conditions appropriately for injury tracking with correct TTL and renewal behavior.

**Status:** Should be updated to "context-dependent" or "works when LLM chooses to use it." The system is functional.

### Finding 5.4: Thread_add silently rejected by pacing gate
Not testable in v3 (zero thread_add emitted). Still possible.

### Finding 5.5: `consecutive_pressure_turns` counter is keyed to wrong signal
**Status UNCLEAR in v3.** The directive counter logic hasn't changed, but beat_locked fires at T6-T7 nonetheless. Either momentum_floor was reached (unlikely, min was 0) or the engine_mirror commit changed how beat_locked computes. Needs code investigation to determine if F5.5 is fixed or if beat_locked is firing through a separate path.

---

## Category 6: Potential Bugs (Code-Verified)

### Finding 6.1: `_merge_arc_update` replaces thread list unconditionally
Architecture unchanged. Not addressed.

### Finding 6.2: `apply_delta` runs before arc director — arc_update is retroactive
Architecture unchanged. Not addressed.

---

## New Findings from Cordyceps v3

### Finding 7.1: Scene thread starvation
After thread_add governance was added (commits 1ddf22bf, 59c39e9), the LLM stopped creating ANY scene-scoped threads. V3 has 0 scene threads across 8 turns. The system went from "too many threads" (v1/v2) to "zero scene threads" (v3). Without scene threads, short-term narrative tension has no structured tracking — everything stays at the arc level until the arc resolves (which it never does).

**Root cause:** The restraint guidance says "don't add threads unnecessarily" but doesn't distinguish between arc threads (long-term, should be rare) and scene threads (short-term, should be created per scene). The LLM applied the guidance universally.

### Finding 7.2: beat_locked IS reachable but mechanism uncertain
Pirate save showed beat_locked never fired. V3 shows it firing at T6-T7. Difference may be from engine_mirror imports (commit e5af4b8) or config changes. Needs investigation: if sequential pressure-type GM beats from storytell now increment the counter, F5.5 is partially fixed. If not, beat_locked fires through momentum_floor path.

### Finding 7.3: World state ID overlap
Three world state entries with different IDs describing the same combat engagement fact. Same problem as thread overlap (F2.5) but for world_state. The LLM isn't checking existing entries before adding, and the system has no dedup validation.

### Finding 7.4: Late-game beat diversity improvement [v3-new]
T10 produced `revelation(environmental)` — the first non-pressure/complication/opportunity beat from storytell output in this save. This may correlate with narrative shift (combat → healing → exploration) rather than improved governance. The existing beat diversity instructions DID eventually produce a varied type, suggesting the guidance works for narrative pivot moments even if it fails for steady-state scenes.

### Finding 7.5: Condition lifecycle works correctly [v3-new]
`bleeding arm` demonstrates full lifecycle: add (T5) → persist (T5-T8) → auto-expire + re-add on fail (T9) → remove on success (T10). The auto-expiration at `turn.py:1011-1030` correctly fires when turns_remaining hits 0, and the storyteller correctly re-adds on narrative failure. This contradicts F5.3's original conclusion that "conditions system is dead code."

---

## Data Sources

| Save | Turns | Model | Setting |
|:---|:---:|:---|:---|
| noir--1930s | 17 | (not recorded) | Detective noir |
| cordyceps-year-twenty (v1) | 34 | gemma-4-26b-a4b-it-mxfp8 | Zombie survival (original) |
| cordyceps-year-twenty (v2) | 26 | (not recorded, likely qwen3) | Zombie survival (fresh run) |
| cordyceps-year-twenty (v3) | 10 | qwen3-25b-4bit | Zombie survival (June 6) |

All saves used the same pipeline version except v3 which includes commits through June 5. Findings shared across all saves are system-level issues. Findings marked `[v3-new]` or `[v3-improved]` were first observed in the June 6 run.
