# Consolidated EV Findings — Cross-Game Analysis

**Sources:**
- `NOIR-EV.md` — noir save (17 turns, 1930s detective)
- `cordyceps-v1` — original cordyceps save (34 turns, zombie survival, gemma-4-26b-a4b-it-mxfp8)
- `cordyceps-v2` — fresh cordyceps save (26 turns, zombie survival, model unknown)
- Code-level tracing from `turn.py`, `delta_builder.py`, `delta.py`

**Validation approach:** Every finding below was observed in BOTH saves unless marked `[noir-only]`, `[zombie-v1-only]`, `[zombie-v2-only]`, or `[new]`. Shared findings are real system issues, not save-specific noise.

Analysis covers **noir** (17), **cordyceps-v1** (34), and **cordyceps-v2** (26) — 77 combined turns across three runs with at least two different models and three different seeds.

---

## Category 0: Beat Distribution is Radically Seed-Dependent [new]

### Finding 0.1: Beat profile flips entirely between two cordyceps runs with the same system
| Beat type | noir (17) | cordyceps-v1 (34) | cordyceps-v2 (26) |
|-----------|:---:|:---:|:---:|
| complication | 0 | 11 | 1 |
| opportunity | 1 | 10 | 1 |
| pressure | 9 | 5 | 4 |
| revelation | 1 | 2 | 12 |
| breathing_room | 0 | 0 | 2 |
| twist | 0 | 0 | 1 |
| escalation | 0 | 0 | 2 |
| setback | 0 | 0 | 0 |
| callback | 0 | 0 | 0 |

Two runs of the same system (cordyceps setting) produced near-inverse beat profiles. V1 was complication+opportunity heavy (61% combined). V2 is revelation-heavy (54%). The beat engine's output is dominated by LLM seed/model variance, not by any control mechanism in the pipeline. The beat guidance in the prompt is essentially noise that each LLM interprets differently.

**Implication:** Any finding about "the system tends to produce X beat type" is untrustworthy across runs. The system doesn't control beat distribution at all.

### Finding 0.2: `breathing_room` finally appeared — twice [zombie-v2-only]
V2 is the first save across 77 turns to ever produce `breathing_room` beats (T2, T9). Both occurred early, both during low-tension dialogue scenes at the checkpoint gate. The beat engine is capable of producing breathers but only in the most obvious narrative conditions. Still 0 across noir and cordyceps-v1 — 51 turns with zero breathers.

---

## Category 1: GM Beat System — Confirmed Broken (All Saves)

### Finding 1.1: Beat type diversity is nonexistent
Across 77 combined turns, only 7 of 9 beat types were ever produced — about 5 of those from v2 alone. The `storytell_system.j2` diversity instructions (~50 lines) are entirely advisory with no enforcement and no history mechanism — the LLM literally cannot follow them because it has no data about prior beats.

**Root cause confirmed across all saves:** The storyteller prompt contains zero beat history. The LLM sees only current turn context and independently generates a beat each turn. Without `last_n_beats` in the prompt, the diversity instructions are untestable by the LLM.

### Finding 1.2: Architectural 1-turn beat lag
The pipeline order (narrate → extraction) means the narrator always reads the **previous** turn's beat. This is by design, but it means the narrator's beat signal is always one turn stale. When the storyteller emits null during a "Breathe" directive, the stale beat from the prior turn continues to reach the narrator.

**All saves confirm:** noir traced stale beats persisting through null turns at T10, T13, T16. V1 shows the same pattern. V2 shows the off-by-one carryover perfectly: narrate beat for turn N always shows the previous turn's generated beat (T1 generated complication → T2 narrate COMPLICATION, etc.) and carries over when current turn generates none.

### Finding 1.3: beat_locked never fires in any save
The dual-trigger mechanism requires:
- `momentum <= -3`: noir min was -1, v1 min was -1, v2 min was -1
- `consecutive_pressure_turns >= 3`: 0 across all 77 turns

The counter tracks **ruling directives** ("Pressure"/"Overwhelm"), not actual GM beat types. The ruling phase almost never output "Pressure" or "Overwhelm" directives in any save — the pacing computation produces "Breathe", "Scene Pressure", "Scene Imperative", or "" (empty). The storyteller independently generates pressure-type beats (~50% of all beats), but the counter doesn't see these because it tracks directives, not beat types.

**All saves confirm:** `beat_locked` is structurally unreachable at current thresholds. `consecutive_pressure_turns` was `0` across every turn in all three games.

### Finding 1.4: Floor relief beats structurally blocked
Three-way blocker:
1. `beat_locked` never fires (Finding 1.3)
2. Even if it did, `pending_gm_beat` is almost never `None` because storytell generates a beat on 80%+ of turns
3. Even on null turns, old beats persist — there is no clear-on-null logic

**Result:** The breathing_room floor relief mechanism is unreachable in practice. No save has ever seen a floor relief beat.

### Finding 1.5: `surface_as` diversity is worse than type diversity
- **noir:** 14 of 17 beats surface as `npc_behavior` or `event`
- **v1:** 18 of 28 beats surface as `npc_behavior` (64%)
- **v2:** surface_as tracking shows the narrate prompt surface_as matches the generated beat, but the storytell prompt never sees the surface_as value at all (Finding 1.8)

The prompt guidance about surface variety is ignored because the LLM has no history of previous surface_as values, and the repeated scene state (guards present, NPCs in scene) consistently suggests NPC-driven beats.

### Finding 1.6: No mechanism to clear pending_gm_beat on null storytell output
When storytell emits `null` (no beat), the old `pending_gm_beat` persists in state. The only clearance paths are:
- TTL expiry (`turn_no > beat_expires_turn`) — rarely fires because beats are usually replaced before expiry
- Overwrite by a new beat — doesn't happen on null turns

Null beat cadence is otherwise healthy: noir had 5 null beats, v1 had 6, v2 had 4 (15-18% of turns). But the null turns don't actually clear the stale signal.

### Finding 1.7: Breathe + stale beat occasionally works by accident
At v1 T26 and T33, v2 T14, T18: "Breathe" directive fires with a null storytell beat. The stale beat that persists happens to fit the narrative. The mechanism is broken but the output is occasionally acceptable. This is not a defense of the mechanism — it's luck.

### Finding 1.8: [CRITICAL] GM Beat section entirely absent from storytell prompts [new]
Across the entire 26-turn cordyceps-v2 run, the `## GM Beat` section with beat type, `## Current Pressures`, and `pending_beat` are **completely missing** from the storytell user prompt. The narrate prompt does receive a `**Beat:**` line (showing previous turn's beat with a one-turn lag), but the storyteller — the stream that generates the actual story content and should enact the beat — has no structural knowledge of what beat was requested.

The pipeline generates beats, stores them as deltas, shows them to the narrator (one turn late), but never injects them into the storyteller prompt that needs them most. Previous analysis (Finding 1.1) identified "zero beat history in the storyteller prompt" — this save confirms the section header doesn't even render.

### Finding 1.9: Breathe → Scene Imperative whiplash [zombie-v2-only]
V2 turn 18 is `Breathe` + `block_escalate` (suppress escalation, give breathing room), immediately followed by turn 19 `Scene Imperative` (the strongest pressure directive). The transition from "breathe" to "urgent combat imperative" in one turn with no ramp contradicts the breathe directive's intent. The pacing system has no hysteresis — each turn's directive is computed independently of the prior turn's directive.

### Finding 1.10: Non-breather beats generated during Breathe directive [zombie-v2-only]
During Breathe + block_escalate turns (v2 T6, T14, T18), the rules engine generated: `(none)`, `opportunity`, and `revelation`. Zero `breathing_room` beat types during any Breathe directive. The beat engine does not align its output with the pacing directive — the pacing system says "give the player a break" while the beat system generates "here's a new revelation."

---

## Category 2: Thread System — Progress Overwrite, Wrong Resolution States, LLM Self-Governance (All Saves)

### Finding 2.1: Thread progress is single-string replacement
`_apply_thread_updates` overwrites `thread.progress` on every update. There is no append or accumulation. `[zombie-v1]` `black_market_contact` was updated 8 times with near-identical summaries — the storyteller keeps re-emitting the same text because it can't see what was previously recorded. `[noir]` `clerk_murder_coverup` had T4's finding ("no blade among debris") overwritten by T5's progress ("transcribed details into notebook"). The investigative trail was lost. `[zombie-v2]` `lost_sibling` progress oscillates between vague and specific without building a coherent investigation log — each update overwrites the last.

### Finding 2.2: Thread resolution states are semantically wrong
Early turns (T1-T22) in v1 used "abandoned" as a catch-all for every resolved thread regardless of actual outcome. Later turns (T23-T34) show improvement. `[zombie-v2]` shows the same pattern then gets worse: `entity_in_the_truck` was simultaneously "abandoned" and "updated with new active state" in the same turn (T18) — the LLM emitted conflicting instructions (Finding 2.7).

### Finding 2.3: Thread scope is consistently misclassified across all saves
| Thread | Declared scope | Actual scope | Game |
|--------|:---:|:---:|:---:|
| `bureaucratic_intervention` | arc | scene (one visit to Moon) | v1 |
| `santana_collusion_risk` | arc | scene (Santana's clinic) | v1 |
| `black_market_contact` | arc | scene (perimeter district) | v1 |
| `elena_vance_leverage` | arc | scene (Vance office) | v1 |
| `negotiation_with_moon` | arc | scene (Moon's office) | v1 |
| `political_stability_trade` | arc | scene (Moon's office) | v1 |
| `the_vance_connection` | arc | scene (Vance's dock) | noir |
| `council_seal_evidence` | arc | scene (Aaron's apartment) | noir |
| `brown_suspicion` | scene | scene ✓ | v2 |
| `the_pulsing_threat` | scene | scene ✓ | v2 |
| `entity_in_the_truck` | scene | scene ✓ | v2 |
| `unknown_entity_encounter` | scene | scene ✓ | v2 |

Interesting divergence: v2 correctly classified 4 scene threads as `scene` scope. The previous analysis (v1) showed near-total misclassification. This may be a model difference (gemma vs current model) rather than a system fix — but it's the first evidence that the thread scope guidance can work.

### Finding 2.4: Thread urgency never decays
No thread in any save ever transitions from urgent → normal → background as time passes:
- `quarantine_spread` (v1): urgent for 34 turns, zero progress updates
- `david_betrayal` (v1): urgent since T5, David vanished after T6, unresolved for 29 turns
- `clerk_murder_coverup` (noir): urgent for all 17 turns
- `rebel_sabotage` / `fedra_internal_split` (v2): never updated after T1, still appear as active threads every turn

The storyteller only increases urgency or leaves it static. There's no prompt guidance about urgency decay over time or when the PC takes actions that partially address a thread.

### Finding 2.5: Most thread_updates carry no meaningful change
All games show thread_update calls with `active=None, urgency=None, summary=""` — the storyteller emits updates that change nothing. This wastes prompt tokens without advancing thread state. In v1's late turns, this pattern improved slightly. In v2, the majority of updates only change `progress` text (which overwrites) without touching urgency, active status, or summary.

### Finding 2.6: Arc-scoped threads never resolve; scene-scoped threads resolve well
All games confirm: scene-scoped threads are created and resolved within 1-3 turns. Arc-scoped threads persist indefinitely with no resolution path. In v2's final state, 6 of 11 active threads are the original arc-scoped threads from T1 — `rebel_sabotage` and `fedra_internal_split` have been dead weight for 26 turns with zero updates. The thread list grows monotonically because arc threads are never pruned.

### Finding 2.7: Thread resolve + update in same turn produces contradictory state [zombie-v2-only, new]
At v2 T18, the storyteller emitted both `thread_resolve` (abandon entity_in_the_truck) and `thread_update` (set active=true, new summary for entity_in_the_truck) for the same thread in a single output. The LLM simultaneously closed and reopened the same thread. The system stored both operations, leaving `entity_in_the_truck` in an ambiguous state — marked abandoned but also updated as active. The next turn's LLM must disambiguate these contradictory records.

This suggests the storyteller's thread governance prompt allows conflicting outputs without validation.

### Finding 2.8: Thread section bloat quantified — no upper bound [zombie-v2-only, new]
In v2, the `## threads` section grows from 781 chars (T1) to 2408 chars (T26), and the `<<<TRACE_IMMUTABLE>>>` section from 338 to 1578 chars. Combined: ~4000 chars (~1000 tokens) of pure thread/state overhead by turn 26.

Growth drivers:
- Thread summaries expand from one-liners to multi-sentence paragraphs
- Immutable trace gains ~50 chars per persistent fact (v2 T26 had 12 persistent facts vs 3 at T1)
- Dead threads (`rebel_sabotage`, `fedra_internal_split`) contribute description text with no narrative value

With no cleanup or truncation, prompt is O(n) in turns played. At 50 turns, the thread section alone would exceed 5000 chars.

### Finding 2.9: LLM autonomously creates threads with no governance [zombie-v2-only, new]
In v2, all 11 thread additions came from the storyteller LLM's own output (`storytell.thread_add`). The system has no mechanism to:
- Validate whether a new thread is needed (vs. updating an existing one)
- Detect thread overlap (v2's `containment_hub_collapse`, `sludge_outbreak_western_sector`, `johnson_complicity_discovery` all describe different facets of the same escalating entity threat)
- Reject thread creation when the thread pool is already saturated
- Ensure thread_add is properly categorized as scene vs arc (Finding 2.3)

The LLM writes its own thread list without any governance layer. The thread system is entirely LLM-driven with no structural oversight.

### Finding 2.10: Turn 20 missing `## threads` section [zombie-v2-only, new]
At v2 T20, the storytell prompt's `## threads` section rendered as empty string — the section header and all thread entries were absent. A retry succeeded on the next attempt. The root cause is unclear (possible template rendering race or state load issue), but it creates a turn where the LLM has zero thread context, which can produce disconnected narrative output.

---

## Category 3: Pacing Computation — Low Sensitivity, No Hysteresis (All Saves)

### Finding 3.1: Pressure/Overwhelm directives never fire — combined 0/77 turns
| Directive type | noir (17) | v1 (34) | v2 (26) | Combined |
|---------------|:---:|:---:|:---:|:---:|
| "" (empty) | 11 | 16 | 12 | 39 |
| Breathe | 4 | 7 | 3 | 14 |
| Scene Imperative | 2 | 5 | 4 | 11 |
| Scene Pressure | 1 | 6 | 6 | 13 |
| Pressure | 0 | 0 | 0 | 0 |
| Overwhelm | 0 | 0 | 0 | 0 |

Zero turns with "Pressure" or "Overwhelm" across 77 turns. The consecutive_pressure counter is keyed to these directives and therefore never incremented.

### Finding 3.2: "Breathe" fires during active tension
- **noir:** Breathe during police raids and door-knocking pressure sequences
- **v1:** Breathe while hiding in a clinic as guards tear the building apart (T11-T15)
- **v2:** Breathe during the creature-escape sequence (T6, T14, T18)

"Breathe" fires because `narrative_velocity < -0.3` (de-escalation), but it conflates **mechanical velocity drop** (player choosing stealth/patience) with **narrative relief** (GM should give them a break). The velocity calculation doesn't distinguish between "player is lying low" and "tension has actually dissipated."

### Finding 3.3: Scene Imperative is a label with no teeth
All saves eventually trigger Scene Imperative (effective_scene_age >= 5). But it doesn't change narrative behavior — the storyteller and narrator don't advance the story faster during Imperative turns. The directive is computed but has no observable effect.

### Finding 3.4: No hysteresis — Breathe → Scene Imperative in 1 turn [zombie-v2-only, new]
V2 T18 is `Breathe` + `block_escalate`, T19 is `Scene Imperative`. The pacing system computes each turn's directive independently with no memory of the prior turn's directive. This allows immediate flip from "give the player a break" to "urgent combat imperative" with no ramp. Add `last_directive` to pacing context to enforce minimum喘息/transition windows.

---

## Category 4: Arc System — Never Resolves, Never Updates (All Saves)

### Finding 4.1: Zero arc progression across 77 combined turns
- **noir (17):** Zero arc_resolve events
- **v1 (34):** Zero arc_resolve events
- **v2 (26):** Zero arc_resolve events

All saves never emitted a single `arc_resolve`. The arc's visible_goal and thematic_question are set at seed time and never updated regardless of how the narrative evolves.

In v1, the visible goal was "Secure the medical archives before the settlement council burns the hospital wing." The archives were secured at T3 and delivered at T29. By T34 the player is in service tunnels — the goal has been obsolete for 30 turns. The storyteller never updated it.

In v2, the goal is "Escaping the Austin QZ as the quarantine lines collapse" — identical text on T1 and T26 even though the player has already breached the walls, killed entities, and reached a containment hub. The arc doesn't respond to the story's events.

### Finding 4.2: Thematic question is ignored
V1's thematic question ("Do you save the knowledge of the old world or the people of the new one?") was never engaged. V2's question ("At what point does upholding the law become an act of betrayal?") was also never touched — the narrative became a creature-feature escape story with no engagement with the law/betrayal theme. The thematic question serves no function past T1 in any save.

### Finding 4.3: Arc guidance includes `goal_context` which also never updates [zombie-v2-only, new]
The storytell prompt includes a "Narrative guidance — goal context" field alongside the goal. In v2, this field reads: "The military crackdown is intensifying, and the lines between protector and occupier are blurring. Alexander cannot stay in a uniform that defines him as an enemy to the people he once called family." This was set at seed time and never changed across 26 turns, even though Alexander abandoned his post at T9, killed multiple entities, and left the QZ entirely — he's no longer wearing the uniform.

---

## Category 5: Cross-Cutting Infrastructure Issues

### Finding 5.1: NPC continuity is fragile — `last_seen` lacks context
`last_seen` renders as location name only. Both games show NPCs disappearing and reappearing with no narrative context bridging the gap:
- **zombie:** David Savage vanishes after T6, `david_betrayal` thread remains urgent for 29 turns with no narrative presence
- **noir:** dock runner returns at T17 after absence since T12; narrator has no structured memory of what happened last time

### Finding 5.2: World state usage improved in later turns [zombie-only]
Early game (T1-T22): 4 persistent facts added. Late game (T23-T34): 6 more added. Total: 10 world state entries. The storyteller is gradually learning to use the mechanism — service tunnels had `service_tunnels_pathway_active`, `service_tunnels_path_cleared`, `service_tunnels_instability`. Trend is positive.

### Finding 5.3: Conditions system is dead code
Zombie: 5 conditions added across 34 turns (5 total), zero present in final state. No injuries, no exhaustion, no contamination in a zombie survival game. The condition system is effectively unused — the storyteller doesn't impose or track physical consequences.

### Finding 5.4: Thread_add silently rejected by pacing gate
At T12, the storyteller emitted `thread_add: santana_collusion_risk`. The pacing gate (`block_escalate` from "Breathe" directive) silently dropped the thread at the Python level. The storyteller has no feedback loop — it emitted the thread thinking it would be added, but it was discarded. The storyteller might have built narrative logic around this thread's existence.

### Finding 5.5: `consecutive_pressure_turns` counter is keyed to wrong signal
The counter tracks `directive in ("Pressure", "Overwhelm")`. But the ruling phase almost never produces these directives (Finding 3.1). The actual pressure comes from the storyteller's independent beat generation. The counter saw `0` across every turn in both games because it's keyed to ruling directives, not to actual beat types emitted by storytell.

---

## Category 6: Potential Bugs (Code-Verified)

### Finding 6.1: `_merge_arc_update` replaces thread list unconditionally
Every call replaces the entire thread list. The location change purge at `delta_builder.py:246-248` removes scene-scoped threads from the deep-copied state, but then `_merge_arc_update` at line 310-311 re-applies `delta.arc_update` which was built from the **pre-purge** thread list. The net effect is correct (scene-scoped threads DO get purged because the arc director runs after apply_delta and works on the purged state), but the apply_delta purge is overwritten and the arc director re-derives the correct list. Unnecessarily fragile.

### Finding 6.2: `apply_delta` runs before arc director — arc_update is retroactive
`apply_delta(state, delta)` runs at line 1086. The arc director runs at lines 1119-1174. The arc director modifies both `state` (in-place) and `delta.arc_update` retroactively. State is saved correctly (line 1289 writes post-arc-director state), but `delta.arc_update` in events.jsonl is stale for any downstream consumer between line 1086 and 1119.

---

## Data Sources

| Save | Turns | Model | Setting |
|:---|:---:|:---|:---|
| noir--1930s | 17 | (not recorded) | Detective noir |
| cordyceps-year-twenty (v1) | 34 | gemma-4-26b-a4b-it-mxfp8 | Zombie survival (original) |
| cordyceps-year-twenty (v2) | 26 | (not recorded, likely qwen3) | Zombie survival (fresh run) |

All saves used the same pipeline version with dynamic seeds. Findings shared across all saves are system-level issues. Findings marked `[new]` were first observed in the v2 run and represent either regression or broader patterns that earlier runs didn't trigger. The dramatic beat profile difference between v1 and v2 (Finding 0.1) confirms that the system has no effective control over beat distribution — it's dominated by LLM seed-specific behavior.
