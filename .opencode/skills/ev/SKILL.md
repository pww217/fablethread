---
name: ev
description: scripts/debug/ev.py reads saves/default/events.jsonl directly. No server required. Run from repo root. This is your primary tool for understanding what happened in a turn before reading any source code.
---

## Command reference

| Command | Args | What it shows |
|---|---|---|
| `ev.py summary [--format json]` | — | One-line overview of all turns: streams active, tokens, rules intent, delta count |
| `ev.py timing` | — | Token counts (in/out) and elapsed time per stream for every turn |
| `ev.py turn <N>` | turn | Full system + user + output for all five streams |
| `ev.py props <N> <stream>` | turn, stream | System + user + output for one stream |
| `ev.py compact <N> <stream>` | turn, stream | User prompt + output only (no system) |
| `ev.py prompt <N> <stream> <field>` | turn, stream, field | Single field: `system`, `user`, or `output` |
| `ev.py outputs <N>` | turn | JSON outputs from all five streams side by side |
| `ev.py deltas <N>` | turn | Applied state mutations and rejections with reasons |
| `ev.py mechanics <N>` | turn | Rules intent, GM beat, campaign arc, narrative, state deltas, connectors, summary |
| `ev.py connectors <N>` | turn | Inter-stream data: what each stream received from prior streams |
| `ev.py state [--format MODE] [--save-dir PATH]` | — | Current game state from `state.yaml` |
| `ev.py diff <A> <B> [--section SEC]` | turn A, turn B | Compare two turns: extraction_context snapshots + intermediate changes |
| `ev.py trace <field> [--from N] [--to M]` | field | Track a field's value across a turn range with change arrows |
| `ev.py search <expr>...` | expressions | Structured cross-turn AND-search |

**Streams:** `ruling` `narrate` `scene` `state` `storytell`

**Fields:** `system` `user` `output`

Append `saves/<name>/events.jsonl` as the last positional arg to read a different save file.

---

## events.jsonl — full event shape

Top-level keys per turn event (17 total):

```
.turn                       — turn number (int)
.input                      — player's text input
.ts                         — ISO-8601 timestamp of event creation
.trace_id                   — hex trace ID linking this turn across logs
.kind                       — (optional) "turn" for normal, "compaction" or "condition_expired" for aux events. Absent = "turn".

.ruling_prompt
  .rendered_system          — rules system prompt
  .rendered_user            — rules user prompt
  .context_meta             — {system_chars, user_chars, total_chars, est_tokens, trimmed, trimmed_chars}
  .output                   — rules LLM output (JSON string)
  .parse_error              — error text if output parsing failed

.narrate_prompt
  .rendered_system          — narrate system prompt
  .rendered_user            — narrate user prompt
  .context_meta             — same shape as ruling_prompt.context_meta
  .output                   — narrate LLM output (prose string)

.extraction
  .scene / .state / .storytell
    .rendered_system        — stream system prompt
    .rendered_user          — stream user prompt
    .context_meta           — same shape as above
    .output                 — stream LLM output (JSON string)
    .attempts               — retry count (int)
    .retry_errors           — error strings from retries (list[str])
    .skipped                — bool, true if stream was skipped
    .ms                     — elapsed wall time for this stream (float)
    .tokens_in / .tokens_out — per-stream token counts (int)

.ruling                     — metrics: intent, intent_verb, rolled, skill, difficulty, dice, band,
|                              final_total, outcome_summary, momentum_before, momentum_after,
|                              momentum_delta, tokens_in, tokens_out, total_ms

.narrate                    — metrics: tokens_in, tokens_out, total_ms, first_token_ms

.extract                    — aggregate extraction metrics: tokens_in, tokens_out, total_ms, retries
  .streams                  — per-stream {ms, tokens_in, tokens_out, skipped}

.rejected                   — list of rejection dicts {field, kind, value, reason}

.applied                    — dict of applied mutations, keyed by field name:
                               npc_add, npc_remove, npc_update, compendium_npc_update,
                               inventory_add, inventory_remove, inventory_update,
                               pc_condition_add, pc_condition_remove,
                               recent_events_add, recent_events_remove, recent_events_update,
                               scene_tags, scene_tagline, location_description
                               Each value is a list of mutation objects or a scalar string.

.changes                    — non-delta state changes: {facts, inventory, player, momentum}
                               facts: list of {kind: "added"|"removed", value: str}
                               momentum: list of {before, after, delta}

.extraction_context          — per-turn snapshot of the post-delta state the storyteller saw:
                                present_npcs_this_turn (list[dict])
                                inventory_this_turn (list[dict])
                                conditions_this_turn (list[dict])
                                location_this_turn (dict)
                                scene_tags_this_turn (list[str])

.pacing_context              — GM pacing decisions:
                                directive (str): PacingDirective enum value
                                beat_hint (str | null)
                                beat_locked (bool)
                                gate (str): "allow" | "gate" | "block"
                                summary (str): human-readable log line

.actions                    — list[str] of ruling intent action options shown to the player

.scene_tags                 — parsed scene tags from active scene state (list[str])

.state_diff                 — NOT stored in events. Generated on-the-fly by _build_state_diff()
                               from rejected + ruling + extraction sub-stream outputs.
```

---

## mechanics sections in rendered prompts

In `.extraction.storytell.rendered_user`:

| Header | Content |
|---|---|
| `## GM Beat` | GM beat instructions / pressure behavior from ruling engine |
| `## Current Pressures` | Active scene pressures passed to storytell |
| `## rules_stakes` | Band result, costs at risk |
| `## pending_beat` | Beats carried forward from prior turns |

In `.narrate_prompt.rendered_user`:

| Header | Content |
|---|---|
| `### Campaign Arc` | Goal, thematic question, active threads |

Other sections parsed for `ev.py mechanics` output include `## deescalate`.

---

## Choosing the right command

**Start here for any investigation:**
- Unknown turn number → `ev.py summary` first
- Pipeline logic bug (beats, pressures, arc, connectors) → `ev.py mechanics <turn>`
- Wrong or missing state field → `ev.py deltas <turn>`, then `ev.py outputs <turn>`
- Bad LLM output → `ev.py compact <turn> <stream>` to read prompt + response
- Token or latency problem → `ev.py timing`
- What one stream received from another → `ev.py connectors <turn>`
- Exact system prompt for a stream → `ev.py prompt <turn> <stream> system`
- Current game state → `ev.py state` (or `--format pc`, `inventory`, `scene`, etc.)
- What changed between two turns → `ev.py diff <A> <B> [--section npcs|inventory|...]`
- Track a field across turns → `ev.py trace inventory --from 1 --to 20`
- Find turns matching criteria → `ev.py search npc:trevor_riddle`

---

## state command format modes

| Mode | What it shows |
|---|---|
| `full` (default) | All sections: PC, inventory, location, scene, arc, NPCs |
| `compact` | Single line: turn + PC name @ location |
| `pc` | PC name, stats, momentum, conditions |
| `inventory` | Inventory items with amounts |
| `location` | Location name + description |
| `scene` | Tags, tagline, present NPCs, recently left |
| `arc` | Goal, thematic question, active/completed threads, truths |
| `npcs` | Compendium NPCs with IDs |
| `compidx` | NPC index table (ID padded) |

---

## diff command section filters

| Filter | What it compares |
|---|---|
| (none) | All sections |
| `--section npcs` | NPC presence |
| `--section inventory` | Item amounts and presence |
| `--section conditions` | Active PC conditions |
| `--section location` | Location ID/name |
| `--section tags` | Scene tags |
| `--section applied` | Intermediate mutations between turns |

---

## trace command tracked fields

| Field path | Data source | Shows |
|---|---|---|
| `inventory` | extraction_context | Full item list with amounts |
| `inventory.<id>` | extraction_context | Single item dict |
| `conditions` | extraction_context | Active condition labels |
| `conditions.<id>` | extraction_context | Single condition dict |
| `npcs` | extraction_context | NPC IDs present in scene |
| `npcs.<id>` | extraction_context | Single NPC entry |
| `location` | extraction_context | Location ID + name |
| `scene.tags` | extraction_context | Scene tag list |
| `scene.tagline` | applied | Tagline (only when changed) |
| `pc.momentum` | changes + ruling fallback | Momentum integer |

---

## search command expressions

Syntax: `<field>:<value>` (exact) or `<field>~<regex>` (regex) or bare `rejected` (boolean).

| Expression | Matches |
|---|---|
| `npc:trevor_riddle` | Turns where trevor_riddle is present or mutated |
| `npc_add:trevor_riddle` | Turns where trevor_riddle was added |
| `item:lockpick_set` | Turns where item is in inventory or mutated |
| `condition:injured` | Turns where condition is active or mutated |
| `band:fail` | Turns where ruling band is "fail" |
| `rejected` | Turns with any rejection |
| `input~stolen` | Turns where input text matches regex `stolen` |

Multiple expressions AND together (all must match).

---

## Reading output

**ev.py summary columns:**
`streams=` active streams | `user=` truncated input | `tokens: in= out= tt=` | `ruling_intent:` | `deltas:` count

**ev.py deltas format:**
```
[from_stream] domain.field = value
--- Rejections ---
  field: reason
```

**ev.py mechanics sections:**
Each section header (`--- Rules Intent ---`, `--- GM Beat ---`, etc.) is followed by its content or `(none)` / `(empty)`. The `--- Summary ---` line shows streams active, rejection/retry/error flags, and token totals.

**ev.py connectors format:**
```
before_stage: <stream>
  from=<prior_stream> label=<prior_stream> → <stream>
    k = v
    k = v
```

Long values are truncated at 150 characters with `…`.

**ev.py trace format:**
```
trace inventory
Turn | Inventory
─────┼────────────────────────────────────────────────
  1 | lockpick_set×1, compact_pistol×1, pistol_rounds×12 ← +lockpick_set, +compact_pistol, +pistol_rounds
  2 | (same)
  3 | lockpick_set×1, compact_pistol×1, pistol_rounds×11, stim_pack×2 ← +stim_pack
```

**ev.py search format:**
```
turn 3: npc_add trevor_riddle — "Try to talk your way past Riddle..."
turn 7: (present in scene) — "Ask Matthew about his brother's location"
```

---

## Token estimation

When reasoning about prompt token budgets:
- `len(text) / 4` ≈ token count (rough but useful for order-of-magnitude)
- `ev.py timing` shows actual `tokens_in` and `tokens_out` per stream per turn
- System prompts are the dominant cost; user prompts vary by turn
- `ev.py prompt <turn> <stream> system | wc -c` → divide by 4 for token estimate

---

## extraction_context caveats

The `extraction_context` snapshot is captured during the pipeline (after scene+state extraction but before storytell), not at the turn boundary. `ev.py diff` uses it and shows this intermediate state — not the final post-turn state. For fields not covered by extraction_context (pc.stats, compendium bios, arc threads), see the `--- Not tracked ---` section in diff output.

---

## Legacy script names

These still work as thin wrappers over `ev.py`:
```
./get-turn.sh <turn>
./get-deltas.sh <turn>
```
