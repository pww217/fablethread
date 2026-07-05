# Prompt Variable Contracts

Cross-reference mapping every user template to its section includes and context variables. This document catches context-variable mismatches — if a template includes a section but doesn't pass its required variables, the contract makes it obvious.

## Section Template Contracts

| Section template | Callers | Required vars | Optional vars | Emits header |
|---|---|---|---|---|
| `_pc_header.j2` | ruling, narrate, extract_state, record | `pc` (dict) | — | `## Player Character` |
| `_conditions.j2` | ruling, narrate, extract_state, record | — | `conditions`, `show_age`, `turn_no` | `## active_conditions` |
| `_inventory.j2` | ruling, narrate, extract_state, record | — | `inventory` (→`state.inventory`) | `## Inventory` |
| `_location.j2` | narrate, record | — | `location` (→`state.location`) | `## Location` |
| `_npc_roster.j2` | narrate, scene, record | `npc_roster` (list) | `turn_no`, `show_all_fields` (bool, defaults to present-only when absent) | `## Characters` |
| `_npc_names.j2` | record | `npc_roster` (list) | — | `## NPC Names` |
| `_thread_list.j2` | narrate, record | `threads` (list) | `turn_no` | `### Active Threads` / `### Dormant Threads` |
| `_arc.j2` | narrate, record | — | `current_arc`, `resolved_arcs` | `### Campaign Arc`, `### Previously Resolved Arcs`, `### Completed Threads` |
| `_recent_turns.j2` | ruling, narrate, record | — | `recent_turns` | `## Prior Turn` |
| `_world_state.j2` | narrate, record | `state` (dict) | — | none (caller provides) |

## Caller → Template Contracts

### `_ruling_messages()` → `ruling_user.j2`

**Context vars passed:** `pc`, `location`, `user_input`, `meta`, `npc_roster`, `inventory`, `recent_turns`, `scene_phase`, `urgent_threads`, `conditions`, `state`, `pc_situation` (filtered: persist=true only from `state.pc_situation_schema`), `beat_candidates`

**Section includes:** `_pc_header.j2`, `_conditions.j2`, `_inventory.j2`

**Inline (not section):** NPC roster loop, urgent threads loop, scene header, `pc_situation` section (conditional), `beat_candidates`

### `_narrate_messages()` → `narrate_user.j2`

**Context vars passed:** `state`, `pc`, `pc_situation` (filtered: persist=true only from `state.pc_situation_schema`), `prior_history`, `recent_turns`, `rules_outcome`, `npc_name_pool`, `user_input`, `pending_beat`, `pacing_context`, `turn_no`, `meta`, `scene`, `ages`, `pc_allegiance`, `world_factions`, `npc_roster`, `current_objective`, `arc_pressure_score`, `arc_hint_text`, `curtain_call`, `resolved_arcs`, `inventory`, `location`, `conditions`

**Section includes:** `_pc_header.j2`, `_conditions.j2`, `_inventory.j2`, `_location.j2`, `_npc_roster.j2`, `_thread_list.j2`, `_recent_turns.j2`, `_arc.j2`, `_world_state.j2`

**Inline (not section):** Scene context, immutable reference block, prior history, past resolutions, rules outcome, beat/outcome hints, `pc_situation` section (conditional)

### `_extract_scene_messages()` → `extract_scene_user.j2`

**Context vars passed:** `narration`, `npc_roster`, `turn_no`, `pc_name`, `show_all_fields`

**Section includes:** `_npc_roster.j2`

**Inline (not section):** Location header, player character header, narration blocks

### `_extract_state_messages()` → `extract_state_user.j2`

**Context vars passed:** `narration`, `conditions`, `inventory`, `location`, `intent`, `turn_no`, `pc_name`

**Section includes:** `_conditions.j2`, `_inventory.j2`

**Inline (not section):** Player character header, intent block, narration blocks

### `_record_messages()` → `record_user.j2`

**Context vars passed:** `narration`, `current_objective` (arc), `all_threads`, `world_state`, `resolved_arcs`, `recent_turns`, `prior_history`, `turn_no`, `band`, `pc_name`, `scene_phase`, `curtain_call`

**Section includes:** `_arc.j2`, `_thread_list.j2`, `_recent_turns.j2`

**Inline (not section):** Threads section, world_state block, rules_outcome (band), scene_phase, curtain_call, prior_history, narration block

**Note:** This contract replaces the old `_storytell_messages()` → `storytell_user.j2` contract. The forward-looking inputs (`candidate_npcs`, `pacing_context`, `intent`, `pending_beat`, `recent_beats`, `allowed_beat_types`, `comp_this_turn`) are no longer passed to Record; they moved to World (Step 2d) and Ruling (Step 0). `scene_phase` and `curtain_call` are still passed to Record.

### `_run_world_step()` → `world_user.j2`

**Context vars passed:** `npc_roster` (from compendium via `build_npc_roster()`), `arc` (threads), `pacing_context`, `recent_beats`, `allowed_beat_types`, `rules_outcome`, `narration`

**Section includes:** none (World is a self-contained prompt with no shared section includes)

**Inline (not section):** Present NPCs, active threads, pacing context, recent beats, allowed beat types, roll outcome, most recent narration
