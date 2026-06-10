# ev.py — CCYA debug & play CLI

Inspect turn data, run game turns, and validate mechanics — all from the CLI.
No server required (except `play` which needs the LLM backend running).

```bash
# Always use the venv's Python — no exceptions
.venv/bin/python scripts/debug/ev.py <command> [args...]
```

> **Common mistakes:**
> - `python3 scripts/debug/ev.py` → fails with `SyntaxError: invalid syntax` (system Python is 3.9, ev.py requires 3.13+)
> - `source .venv/bin/activate && python3 scripts/debug/ev.py` → same error (activate doesn't work reliably)
> - `ev.py --help` → fails with `IndexError: list index out of range` (ev.py has no help command)

## Save directory convention

Commands that read events use the **last positional arg** as the `events.jsonl` path.
Commands that need full state also accept `--save-dir DIR`.

| Pattern | Example |
|---------|---------|
| Default save | `ev.py turn 5` → reads `saves/default/events.jsonl` |
| Specific save | `ev.py turn 5 saves/my-game/events.jsonl` |
| State access | Add `--save-dir saves/my-game` |

---

## Command reference

### See what happened — turn data inspection

| If you want... | Command |
|---|---|
| One-line overview of all turns | `ev.py summary [save-path]` |
| Full timing + token breakdown | `ev.py timing [save-path]` |
| See everything for one turn | `ev.py turn <N> [save-path]` |
| Just a single stream's prompt/output | `ev.py prompt <N> <stream> [--system] [--field FIELD] [save-path]` |
| See all JSON outputs for a turn | `ev.py outputs <N> [save-path]` |

**Stream names:** `ruling` (or `rules`), `narrate`, `scene`, `state`, `storytell` (or `progress`).

```bash
# Quick overview
.venv/bin/python scripts/debug/ev.py summary
.venv/bin/python scripts/debug/ev.py summary saves/outer-rim/events.jsonl

# Full pipeline dump for turn 5
.venv/bin/python scripts/debug/ev.py turn 5

# Raw JSON for mining specific fields
.venv/bin/python scripts/debug/ev.py turn 5 --json

# Just the storytell user prompt on turn 5
.venv/bin/python scripts/debug/ev.py prompt 5 storytell user

# Just the narrate output (the generated prose)
.venv/bin/python scripts/debug/ev.py prompt 5 narrate output

# Timing + tokens for budget analysis
.venv/bin/python scripts/debug/ev.py timing
```

### What changed — state & diff tracking

| If you want... | Command |
|---|---|
| Current game state (reads state.yaml) | `ev.py state --save-dir DIR [--format compact\|pc\|inventory\|location\|scene\|arc\|npcs\|compidx]` |
| What mutated on a turn | `ev.py deltas <N> [save-path]` |
| Compare two turns' state | `ev.py diff [turnA] [turnB] [--section npcs\|inventory\|conditions\|location] [save-path]` |
| Track one field across all turns | `ev.py trace <field.path> [--from N] [--to N] [save-path]` |
| Find turns where something happened | `ev.py search <pattern> [save-path]` |
| Mechanics + beats + pacing for a turn | `ev.py mechanics <N> [--pacing] [--dice] [--sanitize] [save-path]` |

```bash
# What's the PC's current momentum and inventory?
.venv/bin/python scripts/debug/ev.py state --save-dir saves/my-game --format pc
.venv/bin/python scripts/debug/ev.py state --save-dir saves/my-game --format inventory

# What state mutations happened on turn 8?
.venv/bin/python scripts/debug/ev.py deltas 8 saves/my-game/events.jsonl

# Did NPCs change between turns 5 and 10?
.venv/bin/python scripts/debug/ev.py diff 5 10 --section npcs saves/my-game/events.jsonl

# Track momentum trajectory across all turns
.venv/bin/python scripts/debug/ev.py trace pc.momentum saves/my-game/events.jsonl

# Track a specific NPC's notes over time
.venv/bin/python scripts/debug/ev.py trace compendium.npcs.blake_webb.notes --show-unchanged saves/my-game/events.jsonl

# Find turns where momentum dropped
.venv/bin/python scripts/debug/ev.py search momentum_delta saves/my-game/events.jsonl

# Full mechanics breakdown with pacing context
.venv/bin/python scripts/debug/ev.py mechanics 12 --pacing --dice saves/my-game/events.jsonl
```

### Play — run game turns

The `play` command feeds a player action through the full engine pipeline (ruling → narrate → extraction → storytell) and saves the result into a save directory. The LLM backend needs to be operational.

```bash
# Single turn into a new default game (requires --pack)
.venv/bin/python scripts/debug/ev.py play "I search the room." --pack zombie-survival

# Play into an EXISTING save (most common pattern)
.venv/bin/python scripts/debug/ev.py play "My action." --no-sanitize --save-dir saves/my-game saves/my-game/events.jsonl

# Interactive mode (prompts in a loop)
.venv/bin/python scripts/debug/ev.py play --interactive --pack zombie-survival

# Let the LLM play (automated testing, up to 20 turns)
.venv/bin/python scripts/debug/ev.py play --llm --turns 10 --pack zombie-survival

# LLM plays with a persona
.venv/bin/python scripts/debug/ev.py play --llm --persona "aggressive mercenary" --pack zombie-survival

# LLM plays with persona + auto-eval on all turns
.venv/bin/python scripts/debug/ev.py play --llm --persona "nice guy" --eval --pack zombie-survival
```

**Flags:**

| Flag | Effect |
|------|--------|
| `--save-dir DIR` | Use DIR for state.yaml (required for existing saves) |
| `--no-sanitize` | Skip thread sanitizer (~5-10s faster per turn) |
| `--model NAME` | Override LLM model |
| `--temp N` | Override temperature for all LLM calls |
| `--pack NAME` | Start with a pack from `packs/` (required for new sessions) |
| `--persona TEXT` | Persona for the LLM player (replaces generic prompt) |
| `--eval` | Run checkers on all turns after session ends |

> **Note:** `--pack` is required when creating a new session (no `--save-dir`). When `--save-dir` is provided, the pack is loaded from the save's stored state.

**Output anatomy:**

```
Turn 13  |  trace: 864cb7de
------------------------------------------------------
Ruling:    INTIMIDATE (skill: charisma, diff: hard)
           Roll: [9] -> Band: success (+0 momentum)
Narrative: "You thrust the rifle upward..." (1655 chars)

Momentum:   3 -> 3  (+0.0)
Actions:   Signal Elias to run., Hand over the rifle., Order Paul to cover.
Scene:     wasteland_surface, A Desperate Trade Struck, tense_negotiation

Deltas:
  inventory_remove: rifle_ammo
  compendium_npc_update: blake_webb

Errors:    none
Tokens:    in=15487  out=1077  ms=31700.0
```

**Common pitfalls:**
1. `Error: saves/default/events.jsonl not found` → Always pass the events file path as the last positional arg
2. Wrong Python → Use `.venv/bin/python` directly
3. Sanitizer is slow → Use `--no-sanitize` during testing
4. Full narrative not shown → `ev.py prompt <N> narrate output <save-path>`

### Validate — checker & eval infrastructure

```bash
# Check a single turn with all available checkers
.venv/bin/python scripts/debug/ev.py check 5 --all --save-dir saves/my-game

# Specific checkers only
.venv/bin/python scripts/debug/ev.py check 5 momentum_lifecycle gm_beat_lifecycle saves/my-game/events.jsonl

# LLM-based checkers (slower, uses the LLM to judge)
.venv/bin/python scripts/debug/ev.py check 5 --all --llm --save-dir saves/my-game

# Run a YAML scenario end-to-end with checkers
.venv/bin/python scripts/debug/ev.py eval run scenarios/my-scenario.yaml --report results.md

# List available eval scenarios
.venv/bin/python scripts/debug/ev.py eval list
```

**Registered checkers** (see `docs/ev/CHECKERS.md` for full docs):

| Checker ID | What it validates |
|---|---|
| `momentum_lifecycle` | Momentum tracking, floor streaks, band correctness |
| `gm_beat_lifecycle` | GM beat type transitions, pressure compliance |
| `inventory_integrity` | Inventory add/remove balance |
| `conditions_lifecycle` | Condition apply/expire timing |
| `npc_presence` | NPC presence field consistency |
| `location_change` | Location transition continuity |
| `sanitizer_lifecycle` | Thread sanitization events |
| `pacing_directives` | Pacing directive formatting |
| `directive_tone_match` | Narrative tone vs pacing directive |
| `state_fidelity` | State snapshot vs active state consistency |

---

## Real debugging workflows

**"The momentum jumped unexpectedly — why?"**
```bash
ev.py trace pc.momentum saves/my-game/events.jsonl
ev.py mechanics 12 --pacing --dice saves/my-game/events.jsonl
```
→ The trace shows the trajectory; mechanics shows the ruling + beat + pacing context.

**"The storyteller generated a wrong action"**
```bash
ev.py prompt 8 storytell user saves/my-game/events.jsonl   # what the LLM saw
ev.py prompt 8 storytell output saves/my-game/events.jsonl  # what it returned
```
→ Compare user prompt (system instructions + turn data) against raw LLM output.

**"An NPC disappeared from the compendium"**
```bash
ev.py diff 5 10 --section npcs saves/my-game/events.jsonl
ev.py deltas 7 saves/my-game/events.jsonl                  # find the exact turn
```
→ The diff shows NPC state before/after; deltas shows the mutation that caused it.

**"The checkers are all failing"**
```bash
ev.py check 5 --all --save-dir saves/my-game
```
→ Run all static checkers. If `requires_fields` errors appear, see `plans/findings/EVAL-FINDINGS-2026-06-09.md`.

**"I need to understand what the engine decided on turn N"**
```bash
ev.py turn 13 saves/my-game/events.jsonl                   # full dump
ev.py mechanics 13 --pacing --dice saves/my-game/events.jsonl  # condensed
```

---

## Stream name reference

The `prompt` command uses stream names. Aliases:

| Canonical | Aliases |
|-----------|---------|
| `ruling` | `rules` |
| `narrate` | — |
| `scene` | — |
| `state` | — |
| `storytell` | `progress` |

---

## Data structure reference

Events are one JSON line per turn in `events.jsonl`. Key fields:

| Field | Contents |
|-------|----------|
| `.turn` | Turn number |
| `.input` | Player's text input |
| `.ruling_prompt.*` | Ruling stream: system prompt, user prompt, LLM output |
| `.narrate_prompt.*` | Narrate stream: system, user, prose output |
| `.extraction.scene.*` | Scene extractor: system, user, NPC/location JSON output |
| `.extraction.state.*` | State extractor: system, user, inventory/condition JSON output |
| `.extraction.storytell.*` | Storyteller: system, user, GM beat + thread JSON output |
| `.applied` | State deltas that were applied (inventory, NPCs, scene tags, etc.) |
| `.rejected` | State deltas that were rejected with reasons |
| `.momentum_before` | PC momentum before ruling |
| `.momentum_after` | PC momentum after ruling |
| `.momentum_delta` | Computed momentum change |
| `.pacing_context` | Pacing directive, beat_locked, outcome_hint |
| `.state_snapshot` | Full state at **start** of turn (pre-turn, despite the name) |
| `.post_turn_pending_beat` | pending_gm_beat after turn processing |
| `.post_extraction_consecutive_pressure_turns` | Consecutive pressure counter |

### Non-turn events

Events with `kind != "turn"` (e.g., `sanitizer` events) have no prompts and are filtered by summary/timing/turn commands. The `sanitizer_lifecycle` checker requires them (`needs_non_turn_events=true`).

### Mechanics context sections

Embedded in `.extraction.storytell.rendered_user`:
- `## gm_beat` — beats generated by ruling step
- `## deescalate` — pressure resolution info
- `## Current Pressures` — active scene pressures
- `## rules_stakes` — band result and at-risk costs
- `## pending_beat` — beats carried forward
- `### Campaign Arc` — goal, phase, threads

### Play session storage

`ev.py play` without `--save-dir` creates sessions in `saves/ev/<timestamp>_<rand>/`.
A symlink `saves/ev/latest` points to the most recent session.
