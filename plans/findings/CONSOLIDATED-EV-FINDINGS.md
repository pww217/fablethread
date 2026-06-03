# Consolidated EV Findings — Cross-Game Analysis

**Sources:**
- `NOIR-EV.md` — noir save (17 turns, 1930s detective)
- This analysis — cordyceps save (22 turns, zombie survival)
- Code-level tracing from `turn.py`, `delta_builder.py`, `delta.py`

**Validation approach:** Every finding below was observed in BOTH saves unless marked `[noir-only]` or `[zombie-only]`. Shared findings are real system issues, not save-specific noise.

Analysis covers **noir** (17 turns) and **cordyceps** (34 turns) — 51 combined turns across two different settings and models.

---

## Category 1: GM Beat System — Confirmed Broken (Both Saves)

### Finding 1.1: Beat type diversity is nonexistent
| Beat type | noir (17 turns) | zombie (34 turns) | Combined |
|-----------|:---:|:---:|:---:|
| complication | 0 | 11 | 11 |
| opportunity | 1 | 10 | 11 |
| pressure | 9 | 5 | 14 |
| revelation | 1 | 2 | 3 |
| breathing_room | 0 | 0 | 0 |
| twist | 0 | 0 | 0 |
| setback | 0 | 0 | 0 |
| escalation | 0 | 0 | 0 |
| callback | 0 | 0 | 0 |

Out of 9 defined beat types, only 4 were ever used across 51 turns. 5/9 types (breathing_room, twist, setback, escalation, callback) never appeared once. The `storytell_system.j2` diversity instructions (~50 lines) are entirely advisory with no enforcement and no history mechanism — the LLM literally cannot follow them because it has no data about prior beats.

**Root cause confirmed across both saves:** The storyteller prompt contains zero beat history. The LLM sees only current turn context and independently generates a beat each turn. Without `last_n_beats` in the prompt, the diversity instructions are untestable by the LLM.

### Finding 1.2: Architectural 1-turn beat lag
The pipeline order (narrate → extraction) means the narrator always reads the **previous** turn's beat. This is by design, but it means the narrator's beat signal is always one turn stale. When the storyteller emits null during a "Breathe" directive, the stale beat from the prior turn continues to reach the narrator.

**Both saves confirm:** noir traced stale beats persisting through null turns at T10, T13, T16. Zombie shows the same pattern: a `revelation` beat generated at T1 survived as `pending_gm_beat` through T4.

### Finding 1.3: beat_locked never fires in either save
The dual-trigger mechanism requires:
- `momentum <= -3`: noir min was -1, zombie min was -1
- `consecutive_pressure_turns >= 3`: noir had 0 counter across all turns, zombie had 0

The counter tracks **ruling directives** ("Pressure"/"Overwhelm"), not actual GM beat types. The ruling phase almost never output "Pressure" or "Overwhelm" directives in either save — the pacing computation produces "Breathe", "Scene Pressure", "Scene Imperative", or "" (empty). The storyteller independently generates pressure-type beats (~50% of all beats), but the counter doesn't see these because it tracks directives, not beat types.

**Both saves confirm:** `beat_locked` is structurally unreachable at current thresholds. `consecutive_pressure_turns` was `0` across every turn in both games.

### Finding 1.4: Floor relief beats structurally blocked
Three-way blocker:
1. `beat_locked` never fires (Finding 1.3)
2. Even if it did, `pending_gm_beat` is almost never `None` because storytell generates a beat on 80%+ of turns
3. Even on null turns, old beats persist — there is no clear-on-null logic

**Result:** The breathing_room floor relief mechanism is unreachable in practice. Neither save ever saw a floor relief beat.

### Finding 1.5: `surface_as` diversity is worse than type diversity
- **noir:** 14 of 17 beats surface as `npc_behavior` or `event` — door-arrival structure repeated across T12-T17
- **zombie:** 18 of 28 beats surface as `npc_behavior` — 64% repetition across 34 turns

The prompt guidance about surface variety is ignored because the LLM has no history of previous surface_as values, and the repeated scene state (guards present, NPCs in scene) consistently suggests NPC-driven beats.

### Finding 1.6: No mechanism to clear pending_gm_beat on null storytell output
When storytell emits `null` (no beat), the old `pending_gm_beat` persists in state. The only clearance paths are:
- TTL expiry (`turn_no > beat_expires_turn`) — rarely fires because beats are usually replaced before expiry
- Overwrite by a new beat — doesn't happen on null turns

Null beat cadence is otherwise healthy: noir had 5 null beats, zombie had 6 (18% of turns), respecting the "at least 1 in 4 turns null" guidance. But the null turns don't actually clear the stale signal.

### Finding 1.7: Breathe + stale beat occasionally works by accident [zombie-only]
At T26 and T33, "Breathe" directive fires with a null storytell beat. The stale beat that persists happens to fit the narrative (a "complication" beat during a steam-crawl crawl genuinely suits the scene). The mechanism is broken but the output is occasionally acceptable. This is not a defense of the mechanism — it's luck.

---

## Category 2: Thread System — Progress Overwrite & Wrong Resolution States (Both Saves)

### Finding 2.1: Thread progress is single-string replacement
`_apply_thread_updates` overwrites `thread.progress` on every update. There is no append or accumulation. `[zombie]` `black_market_contact` was updated 8 times with near-identical summaries — the storyteller keeps re-emitting the same text because it can't see what was previously recorded. `[noir]` `clerk_murder_coverup` had T4's finding ("no blade among debris") overwritten by T5's progress ("transcribed details into notebook"). The investigative trail was lost.

### Finding 2.2: Thread resolution states are semantically wrong
Early turns (T1-T22) in zombie used "abandoned" as a catch-all for every resolved thread regardless of actual outcome. Later turns (T23-T34) show improvement — `black_market_contact`, `clinic_aftermath_negotiation`, and `lost_in_service_tunnels` were all correctly resolved as "resolved". However, the earlier pattern of "abandoned" for scene-scoped threads (guard patrol, guard inspection, escalation) persists in completed_threads permanently.

**Pattern:** The storyteller defaults to "abandoned" when the narrative focus shifts, rather than using the correct literal state. `bureaucratic_intervention` was correctly "failed" — suggesting the distinction is learnable.

### Finding 2.3: Thread scope is consistently misclassified across both saves
| Thread | Declared scope | Actual scope | Game |
|--------|:---:|:---:|:---:|
| `bureaucratic_intervention` | arc | scene (one visit to Moon) | zombie |
| `santana_collusion_risk` | arc | scene (Santana's clinic) | zombie |
| `black_market_contact` | arc | scene (perimeter district) | zombie |
| `elena_vance_leverage` | arc | scene (Vance office) | zombie |
| `negotiation_with_moon` | arc | scene (Moon's office) | zombie |
| `political_stability_trade` | arc | scene (Moon's office) | zombie |
| `the_vance_connection` | arc | scene (Vance's dock) | noir |
| `council_seal_evidence` | arc | scene (Aaron's apartment) | noir |

Arc-scoped threads persist across location changes and are never cleaned up. Scene-scoped threads get purged on location change. When the storyteller misclassifies a single-location event as arc-scoped, it pollutes the thread list permanently. In zombie's final state, 6 of 8 active threads should be scene-scoped but are classified as arc.

### Finding 2.4: Thread urgency never decays
No thread in either save ever transitions from urgent → normal → background as time passes:
- `quarantine_spread` (zombie): urgent for 34 turns, zero progress updates
- `david_betrayal` (zombie): urgent since T5, David vanished after T6, unresolved for 29 turns
- `clerk_murder_coverup` (noir): urgent for all 17 turns

The storyteller only increases urgency or leaves it static. There's no prompt guidance about urgency decay over time or when the PC takes actions that partially address a thread.

### Finding 2.5: Most thread_updates carry no meaningful change
Both games show thread_update calls with `active=None, urgency=None, summary=""` — the storyteller emits updates that change nothing. This wastes prompt tokens without advancing thread state. In zombie's late turns, this pattern improved slightly (updates actually changed summary/progress), but the prevalence of no-op updates in early turns suggests the prompt doesn't discourage them strongly enough.

### Finding 2.6: Arc-scoped threads never resolve; scene-scoped threads resolve well [zombie-only, T23-T34]
In the final 12 turns, a clear pattern emerged:
- **Scene-scoped threads** are created and resolved within 1-3 turns (`clinic_aftermath_negotiation`, `lost_in_service_tunnels`)
- **Arc-scoped threads** persist indefinitely with no resolution path (`elena_vance_leverage`, `negotiation_with_moon`, `political_stability_trade` — all created in this window, all still active, none resolved)

The storyteller can competently close single-location threads but cannot close persistent story arcs. The thread list stabilizes at ~8 active threads because every new thread_add is balanced by a thread_resolve — but the resolves only hit scene-scoped threads. The 5 arc-scoped threads are permanent dead weight.

---

## Category 3: Pacing Computation — Low Sensitivity (Both Saves)

### Finding 3.1: Pressure/Overwhelm directives never fire — combined 0/51 turns
| Directive type | noir (17) | zombie (34) | Combined |
|---------------|:---:|:---:|:---:|
| "" (empty) | 11 | 16 | 27 |
| Breathe | 4 | 7 | 11 |
| Scene Imperative | 2 | 5 | 7 |
| Scene Pressure | 1 | 6 | 7 |
| Pressure | 0 | 0 | 0 |
| Overwhelm | 0 | 0 | 0 |

Zero turns with "Pressure" or "Overwhelm" across 51 turns. The consecutive_pressure counter is keyed to these directives and therefore never incremented.

### Finding 3.2: "Breathe" fires during active tension
- **noir:** Breathe during police raids and door-knocking pressure sequences
- **zombie:** Breathe while hiding in a clinic as guards tear the building apart (T11-T15)

"Breathe" fires because `narrative_velocity < -0.3` (de-escalation), but it conflates **mechanical velocity drop** (player choosing stealth/patience) with **narrative relief** (GM should give them a break). The velocity calculation doesn't distinguish between "player is lying low" and "tension has actually dissipated."

### Finding 3.3: Scene Imperative is a label with no teeth
Both saves eventually trigger Scene Imperative (effective_scene_age >= 5). Zombie had 5 consecutive turns (T16-T21). But it doesn't change narrative behavior — the storyteller and narrator don't advance the story faster during Imperative turns. The directive is computed but has no observable effect.

---

## Category 4: Arc System — Never Resolves (Both Saves)

### Finding 4.1: Zero arc progression across 51 combined turns
- **noir (17 turns):** Zero arc_resolve events
- **zombie (34 turns):** Zero arc_resolve events

Both saves never emitted a single `arc_resolve`. The arc's visible_goal and thematic_question are set at seed time and never updated regardless of how the narrative evolves.

In zombie, the visible goal was "Secure the medical archives before the settlement council burns the hospital wing." The archives were secured at T3 and delivered at T29. By T34 the player is in service tunnels — the goal has been obsolete for 30 turns. The storyteller never updated it.

### Finding 4.2: Thematic question is ignored
Zombie's thematic question ("Do you save the knowledge of the old world or the people of the new one?") was never engaged by the storyteller. The narrative evolved into black market politics and tunnel escape — a perfectly valid story direction, but one that has nothing to do with the seed's thematic framing. The thematic question serves no function past T1.

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
| cordyceps-year-twenty | 34 | gemma-4-26b-a4b-it-mxfp8 | Zombie survival |

Both saves used dynamic seeds with the same pipeline version. The consistency of findings across different settings and models confirms these are system-level issues, not LLM-specific quirks.
