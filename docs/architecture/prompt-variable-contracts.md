# Prompt Variable Contracts

Cross-reference mapping every user template to its section includes and context variables. This document catches context-variable mismatches — if a template includes a section but doesn't pass its required variables, the contract makes it obvious.

## Section Template Contracts

| Section template | Callers | Required vars | Optional vars | Emits header |
|---|---|---|---|---|
| `_pc_header.j2` | ruling, narrate, extract_state, storytell | `pc` (dict) | — | `## Player Character` |
| `_conditions.j2` | ruling, narrate, extract_state, storytell | — | `conditions`, `show_age`, `turn_no` | `## active_conditions` |
| `_inventory.j2` | ruling, narrate, extract_state, storytell | — | `inventory` (→`state.inventory`) | `## Inventory` |
| `_location.j2` | narrate, storytell | — | `location` (→`state.location`) | `## Location` |
| `_npc_roster.j2` | narrate, scene, storytell | `npc_roster` (list) | `turn_no`, `show_all_fields` (bool, defaults to present-only when absent) | `## Characters` |
| `_npc_names.j2` | storytell | `npc_roster` (list) | — | `## NPC Names` |
| `_thread_list.j2` | narrate, storytell | `threads` (list) | `turn_no` | `### Active Threads` / `### Dormant Threads` |
| `_arc.j2` | narrate, storytell | — | `current_arc`, `resolved_arcs` | `### Campaign Arc`, `### Previously Resolved Arcs`, `### Completed Threads` |
| `_recent_turns.j2` | ruling, narrate, storytell | — | `recent_turns` | `## Prior Turn` |
| `_world_state.j2` | narrate | `state` (dict) | — | none (caller provides) |

## Caller → Template Contracts

### `_ruling_messages()` → `ruling_user.j2`

**Context vars passed:** `pc`, `location`, `user_input`, `meta`, `npc_roster`, `inventory`, `recent_turns`, `scene_phase`, `urgent_threads`, `conditions`, `state`

**Section includes:** `_pc_header.j2`, `_conditions.j2`, `_inventory.j2`, `_recent_turns.j2`

**Inline (not section):** NPC roster loop, urgent threads loop, scene header

### `_narrate_messages()` → `narrate_user.j2`

**Context vars passed:** `state`, `pc`, `prior_history`, `recent_turns`, `rules_outcome`, `npc_name_pool`, `user_input`, `pending_beat`, `pacing_context`, `turn_no`, `meta`, `scene`, `ages`, `pc_allegiance`, `world_factions`, `npc_roster`, `current_arc`, `curtain_call`, `resolved_arcs`, `inventory`, `location`, `conditions`

**Section includes:** `_pc_header.j2`, `_conditions.j2`, `_inventory.j2`, `_location.j2`, `_npc_roster.j2`, `_thread_list.j2`, `_recent_turns.j2`, `_arc.j2`, `_world_state.j2`

**Inline (not section):** Scene context, immutable reference block, prior history, past resolutions, rules outcome, beat/outcome/spiral hints

### `_extract_scene_messages()` → `extract_scene_user.j2`

**Context vars passed:** `narration`, `location`, `npc_roster`, `pc_name`, `turn_no`, `show_all_fields`

**Section includes:** `_npc_roster.j2`

**Inline (not section):** Location header, player character header, narration blocks

### `_extract_state_messages()` → `extract_state_user.j2`

**Context vars passed:** `narration`, `conditions`, `inventory`, `intent`, `turn_no`, `pc_name`

**Section includes:** `_conditions.j2`, `_inventory.j2`

**Inline (not section):** Player character header, intent block, narration blocks

### `_storytell_messages()` → `storytell_user.j2`

**Context vars passed:** `narration`, `npc_roster`, `candidate_npcs`, `location`, `inventory`, `conditions`, `current_arc`, `all_threads`, `world_state`, `resolved_arcs`, `intent`, `pacing_context`, `recent_turns`, `prior_history`, `pending_beat`, `recent_beats`, `turn_no`, `band`, `scene_phase`, `curtain_call`, `allowed_beat_types`, `pc_name`

**Section includes:** `_inventory.j2`, `_conditions.j2`, `_npc_roster.j2`, `_npc_names.j2`, `_location.j2`, `_arc.j2`, `_thread_list.j2`, `_recent_turns.j2`

**Inline (not section):** Scene Input (candidate_npcs as formatted list), Threads section, world_state block, pacing_context, scene_phase, curtain_call, GM beat, recent beats, rules_outcome, prior_history, player_intent, narration blocks, beat type reminder
