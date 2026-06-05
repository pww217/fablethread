# Domain Judge Scores

```yaml
narrative_interplay:
  pipeline_scores: {}
prompt_pipeline:
  pipeline_scores: {}
state_correctness:
  extraction_accuracy_score: 4
  mechanic_lifecycle_score: 3
  pipeline_scores: {}
  state_fidelity_rate: 0.625

```

# Judge Summaries

## state_correctness

### Actionable Issues

**Critical**
- **<Description>** Momentum state desynchronization between delta application and ruling/pacing computation causes `beat_locked` logic to fail repeatedly (Turns 6, 7, 10-13). The engine reads stale momentum values (often 0) while deltas correctly apply negative changes. This breaks floor relief injection and pacing directives.
    - **Tags:** `engine_bug`, `validation_rejection`.
    - **Fix:** Ensure `_compute_pacing_context()` reads the *post-delta* state or that delta application is atomic before ruling readback for subsequent turns. Debug why `pc.momentum` appears as 0 in auto-checker logs when it should be <=-3.

**Major**
- **<Description>** Location change at Turn 12 was emitted by Scene Extract but failed to update `state.location.id`. The delta was likely rejected or ignored during apply, leaving the player narratively at the docks but mechanically at the inn entrance.
    - **Tags:** `validation_rejection`, `engine_bug`.
    - **Fix:** Investigate why `location_change` delta for T12 was not applied to `state.location`. Check validation constraints on location IDs or merge logic in `_apply_delta()`.

- **<Description>** Storyteller pipeline fails to emit suggested actions (Turn 10) and duplicates thread progress entries (`clear_the_road_toughs`).
    - **Tags:** `extraction_miss`, `schema_drift`.
    - **Fix:** Add validation in Storytell output parser to enforce non-empty `actions` list. Prompt engineering update for storyteller to prevent repetitive progress appending; add a "unique only" instruction or post-process deduplication in `_apply_thread_updates()`.

**Minor**
- **<Description>** Conditions (`cornered`, `winded`, etc.) are flagged as orphaned because they lack defined modifiers in the engine config. This breaks condition-based dice roll calculations if these conditions were ever meant to affect stats.
    - **Tags:** `schema_drift`.
    - **Fix:** Define default or zero-value modifiers for narrative-only conditions, or update auto-checker to exclude non-mechanical conditions from modifier validation.

- **<Description>** Auto-checker false positive on Turn 4 regarding NPC mention "Marrow". Location names are being flagged as missing compendium entries.
    - **Tags:** `checker_noise`.
    - **Fix:** Update auto-checker logic to exclude location names and common nouns from the `npc_mention.extracted` assertion, or ensure all locations have a corresponding (dummy) NPC entry if required by schema.

### Issues

**Critical**
- **<Description>** Momentum state desynchronization between delta application and ruling/pacing computation causes `beat_locked` logic to fail repeatedly (Turns 6, 7, 10-13). The engine reads stale momentum values (often 0) while deltas correctly apply negative changes. This breaks floor relief injection and pacing directives.
    - **Tags:** `engine_bug`, `validation_rejection`.
    - **Fix:** Ensure `_compute_pacing_context()` reads the *post-delta* state or that delta application is atomic before ruling readback for subsequent turns. Debug why `pc.momentum` appears as 0 in auto-checker logs when it should be <=-3.

**Major**
- **<Description>** Location change at Turn 12 was emitted by Scene Extract but failed to update `state.location.id`. The delta was likely rejected or ignored during apply, leaving the player narratively at the docks but mechanically at the inn entrance.
    - **Tags:** `validation_rejection`, `engine_bug`.
    - **Fix:** Investigate why `location_change` delta for T12 was not applied to `state.location`. Check validation constraints on location IDs or merge logic in `_apply_delta()`.

- **<Description>** Storyteller pipeline fails to emit suggested actions (Turn 10) and duplicates thread progress entries (`clear_the_road_toughs`).
    - **Tags:** `extraction_miss`, `schema_drift`.
    - **Fix:** Add validation in Storytell output parser to enforce non-empty `actions` list. Prompt engineering update for storyteller to prevent repetitive progress appending; add a "unique only" instruction or post-process deduplication in `_apply_thread_updates()`.

**Minor**
- **<Description>** Conditions (`cornered`, `winded`, etc.) are flagged as orphaned because they lack defined modifiers in the engine config. This breaks condition-based dice roll calculations if these conditions were ever meant to affect stats.
    - **Tags:** `schema_drift`.
    - **Fix:** Define default or zero-value modifiers for narrative-only conditions, or update auto-checker to exclude non-mechanical conditions from modifier validation.

- **<Description>** Auto-checker false positive on Turn 4 regarding NPC mention "Marrow". Location names are being flagged as missing compendium entries.
    - **Tags:** `checker_noise`.
    - **Fix:** Update auto-checker logic to exclude location names and common nouns from the `npc_mention.extracted` assertion, or ensure all locations have a corresponding (dummy) NPC entry if required by schema.


## narrative_interplay

### Actionable Issues

- **Critical: Intent Redirection on Impossible/Failed Actions** (Turns: T7) — Tag: `intent_redirect`. The engine narrated that Aren reached for a "phantom contact" and was pinned, ignoring the player's explicit intent to interact with Halden. Fix: If an action is impossible or fails due to state (NPC not present), narrate the failure of *that specific interaction* first ("You look around but Halden isn't there") before introducing other consequences like being pinned by thugs. Do not substitute a different scene event unless it's a direct consequence of the failed attempt.
- **Major: Condition Modifiers Not Applied** (Turns: T8, T10-T12) — Tag: `phantom_mechanic`. The `winded` condition was added but `cond_mod` remained 0 on relevant rolls. Fix: Ensure conditions that impair physical ability (`winded`, `cornered`) apply appropriate modifiers to Dexterity/Strength checks or impose narrative restrictions reflected in the ruling phase.
- **Major: NPC Presence Continuity Error** (Turns: T7, T12) — Tag: `npc_ghost`. Narration T7 implies Halden is absent ("phantom contact"), but Scene Extract T12 lists him as present. Fix: Align scene extraction with narration facts. If Halden wasn't seen in the inn during the struggle, he should not be marked `present` unless there's a narrative cue of his arrival.
- **Minor: Beat Type Misalignment** (Turns: T9) — Tag: `type_mismatch`. A `revelation` beat was generated for a scene where the primary outcome was rejection/mockery by an NPC, which fits `complication` or `setback` better. Fix: Improve Storyteller prompt guidance to align `revelation` beats with moments of new information discovery rather than social failures.

### Issues

- **Critical: Intent Redirection on Impossible/Failed Actions** (Turns: T7) — Tag: `intent_redirect`. The engine narrated that Aren reached for a "phantom contact" and was pinned, ignoring the player's explicit intent to interact with Halden. Fix: If an action is impossible or fails due to state (NPC not present), narrate the failure of *that specific interaction* first ("You look around but Halden isn't there") before introducing other consequences like being pinned by thugs. Do not substitute a different scene event unless it's a direct consequence of the failed attempt.
- **Major: Condition Modifiers Not Applied** (Turns: T8, T10-T12) — Tag: `phantom_mechanic`. The `winded` condition was added but `cond_mod` remained 0 on relevant rolls. Fix: Ensure conditions that impair physical ability (`winded`, `cornered`) apply appropriate modifiers to Dexterity/Strength checks or impose narrative restrictions reflected in the ruling phase.
- **Major: NPC Presence Continuity Error** (Turns: T7, T12) — Tag: `npc_ghost`. Narration T7 implies Halden is absent ("phantom contact"), but Scene Extract T12 lists him as present. Fix: Align scene extraction with narration facts. If Halden wasn't seen in the inn during the struggle, he should not be marked `present` unless there's a narrative cue of his arrival.
- **Minor: Beat Type Misalignment** (Turns: T9) — Tag: `type_mismatch`. A `revelation` beat was generated for a scene where the primary outcome was rejection/mockery by an NPC, which fits `complication` or `setback` better. Fix: Improve Storyteller prompt guidance to align `revelation` beats with moments of new information discovery rather than social failures.


## prompt_pipeline

### Actionable Issues

### Critical
-   **None.** No mechanical failures or data corruption observed that broke the game loop.

### Major
-   **<Storyteller World State Duplication>** (pipeline: storytell, turns: [9, 10]) — Tag: `<instruction_ignored>`. Fix: Add a concrete few-shot example in `storytell_system.j2` demonstrating how to update an existing `world_state_add` entry by ID rather than creating a new one when facts overlap. This prevents state bloat that inflates subsequent Narrator prompts.

### Minor
-   **<wasted_tokens>** (pipeline: extract_scene, turns: [1-13]) — Tag: `<cross_pipeline_redundancy>`. Fix: Pass only `location.id` and `location.name` to the Scene Extractor instead of the full location description block. The extractor does not need prose context for change detection.
-   **<wasted_tokens>** (pipeline: narrate, turns: [4-13]) — Tag: `<cross_pipeline_redundancy>`. Fix: Remove `last_seen` field from NPC roster entries in the Narrator user prompt. It adds token weight without influencing narrative generation for NPCs not currently interacting with the PC.
-   **<schema_drift>** (pipeline: storytell, turns: [10]) — Tag: `<instruction_ignored>`. Fix: Clarify `goal_update` triggers. The update on T10 ("Identify the true employer...") was a minor refinement based on one conversation turn. Guidance should emphasize that `goal_update` is for *significant* shifts in campaign direction, not incremental clarifications, to prevent goal churn.

### Issues

### Critical
-   **None.** No mechanical failures or data corruption observed that broke the game loop.

### Major
-   **<Storyteller World State Duplication>** (pipeline: storytell, turns: [9, 10]) — Tag: `<instruction_ignored>`. Fix: Add a concrete few-shot example in `storytell_system.j2` demonstrating how to update an existing `world_state_add` entry by ID rather than creating a new one when facts overlap. This prevents state bloat that inflates subsequent Narrator prompts.

### Minor
-   **<wasted_tokens>** (pipeline: extract_scene, turns: [1-13]) — Tag: `<cross_pipeline_redundancy>`. Fix: Pass only `location.id` and `location.name` to the Scene Extractor instead of the full location description block. The extractor does not need prose context for change detection.
-   **<wasted_tokens>** (pipeline: narrate, turns: [4-13]) — Tag: `<cross_pipeline_redundancy>`. Fix: Remove `last_seen` field from NPC roster entries in the Narrator user prompt. It adds token weight without influencing narrative generation for NPCs not currently interacting with the PC.
-   **<schema_drift>** (pipeline: storytell, turns: [10]) — Tag: `<instruction_ignored>`. Fix: Clarify `goal_update` triggers. The update on T10 ("Identify the true employer...") was a minor refinement based on one conversation turn. Guidance should emphasize that `goal_update` is for *significant* shifts in campaign direction, not incremental clarifications, to prevent goal churn.

