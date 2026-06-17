# ev.py Command Reference

## Common pitfalls

1. Use `.venv/bin/python scripts/debug/ev.py` — never `python3` or `source .venv/bin/activate`
2. `ev.py play --llm --turns N` — set shell timeout to at least N×60000ms (~1 min/turn)
3. `--pack` required for new sessions; `--save-dir` for existing saves

## Save directory convention

| Pattern | Command |
|---------|---------|
| Default (latest) | `ev.py turn 5` → reads from `evals/runs/latest` |
| Specific run | `ev.py turn 5 evals/runs/YYYY-MM-DD/run-name/events.jsonl` |
| State access | Add `--save-dir evals/runs/YYYY-MM-DD/run-name` |

## Session config (ev.yaml)

Every session directory can contain an `ev.yaml`. Resolution: CLI flags > `ev.yaml` > `ccya/config.yaml`.

| Field | Effect |
|-------|--------|
| `pack` | Default pack |
| `model` | Default LLM model |
| `temp` | Default temperature |
| `no_sanitize` | Skip thread sanitizer |
| `player.personality` | Preset: `aggressive`, `cautious`, `absurd`, `explorer`, `driven`, `custom` |

---

## Turn data inspection

| If you want... | Command |
|---|---|
| One-line overview | `ev.py summary [save-path]` |
| Full timing + tokens | `ev.py timing [save-path]` |
| Full dump of one turn | `ev.py turn <N> [save-path]` |
| Specific stream prompt/output | `ev.py prompt <N> <stream> [--system] [--field FIELD] [save-path]` |
| All JSON outputs for a turn | `ev.py turn <N> --json [save-path]` |

**Stream names:** `ruling` (or `rules`), `narrate`, `scene`, `state`, `storytell` (or `progress`).

## State & diff tracking

| If you want... | Command |
|---|---|
| Current game state | `ev.py state --save-dir DIR [--format compact\|pc\|inventory\|...]` |
| What mutated on a turn | `ev.py deltas <N> [save-path]` |
| Compare two turns' state | `ev.py diff [turnA] [turnB] [--section npcs\|...] [save-path]` |
| Track one field across turns | `ev.py trace <field.path> [--from N] [--to N] [save-path]` |
| Find turns matching a pattern | `ev.py search <pattern> [save-path]` |
| Mechanics + beats + pacing | `ev.py mechanics <N> [--pacing] [--dice] [--sanitize] [save-path]` |

## Thread, beat, and phase analysis

| If you want... | Command |
|---|---|
| Thread lifecycle | `ev.py threads [save-path]` |
| Thread resolution summary | `ev.py threads --summary [save-path]` |
| Beat type + surface | `ev.py beats [save-path]` |
| Roll bands per turn | `ev.py rolls [save-path]` |
| Roll distribution | `ev.py rolls --summary [save-path]` |
| Convergence score | `ev.py convergence [save-path]` |
| Phase transitions | `ev.py phase-transitions [save-path]` |
| Curtain Call compliance | `ev.py curtain-call [save-path]` |
| Goal changes | `ev.py goals [save-path]` |
| Beat TTL expiration | `ev.py beat-ttl [save-path]` |
| Scene effective age | `ev.py effective-age [save-path]` |

All tabular commands filter compaction events by default. Use `--include-compaction` to include them.

## Play — run game turns

| Flag | Effect |
|------|--------|
| `--save-dir DIR` | Use existing save |
| `--no-sanitize` | Skip thread sanitizer (~5-10s faster) |
| `--model NAME` | Override LLM model |
| `--temp N` | Override temperature |
| `--pack NAME` | Start with a pack (required for new sessions) |
| `--personality NAME` | Preset: aggressive, cautious, absurd, explorer, driven, custom |
| `--custom-persona TEXT` | Custom persona text (use with `--personality custom`) |
| `--resume` | Resume latest or `--save-dir` session |
| `--until-error` | Stop LLM mode on first error |
| `--turns N` | Max turns for `--llm` mode (default 20) |
| `--eval` | Run checkers after session ends |

```bash
ev.py play "I search the room." --pack noir-1930s
ev.py play "My action." --no-sanitize --save-dir evals/runs/latest
ev.py play --interactive --pack zombie-survival
ev.py play --llm --turns 10 --pack zombie-survival
ev.py play --llm --personality aggressive --pack noir-1930s --eval
```

## Session management

```bash
ev.py init --pack noir-1930s --personality cautious
ev.py status
ev.py status --save-dir evals/runs/latest
```

## Validate — checkers & eval

```bash
ev.py check --all --save-dir evals/runs/latest
ev.py check --all --verbose --save-dir evals/runs/latest
ev.py check --list
ev.py check 5 phase_transition --save-dir evals/runs/latest
ev.py check 5 --all --llm --save-dir evals/runs/latest
ev.py eval run scenarios/my-scenario.yaml --report results.md
ev.py eval list
```

## Warnings

```bash
ev.py warnings [save-path]
```

Signals: `extract.retries`, `retry_errors`, `rejected`, `reconcile_warnings`.

## Prompt size analysis

```bash
ev.py prompt-sizes [save-path]
```

Stages: ruling, narrate, scene, state, storytell.

## Prompt testing

```bash
# Render only (no LLM)
ev.py prompt-eval dump <save-dir> --turn N --stream <stream>
ev.py prompt-eval dump <save-dir> --turn N --stream <stream> --from-events

# Render + LLM + check
ev.py prompt-eval call <scenario.yaml>
ev.py prompt-eval call <scenario.yaml> --from-events
```

## Audit commands (specialized)

| Command | What it does |
|---|---|
| `storyteller-audit` | Checks storyteller output: thread_add/thread_resolve/arc_resolve consistency, missing goal_updates, GM beat validity against scene phase |
| `ruling-audit` | Validates ruling.reason non-empty, condition IDs present, band distribution |
| `thread-audit` | Thread lifecycle across all turns: created by thread_add, updated, referenced by sanitizer |
| `npc-ghosting` | Detects NPC disappearance from compendium without departure tracking |
| `state-history` | Tracks conditions or inventory over time |
| `active-conditions` | Current conditions with turns_remaining |
| `compat` | Checks events.jsonl format compatibility (changes vs extraction_context) |

---

## Real debugging workflows

**"The phase isn't transitioning — why?"**
```bash
ev.py trace pacing_context.scene_phase [save-path]
ev.py mechanics 12 --pacing --dice [save-path]
```

**"The storyteller generated a wrong action"**
```bash
ev.py prompt 8 storytell user [save-path]   # what the LLM saw
ev.py prompt 8 storytell output [save-path]  # what it returned
```

**"An NPC disappeared from the compendium"**
```bash
ev.py diff 5 10 --section npcs [save-path]
ev.py deltas 7 [save-path]
```

---

## Data structure reference

Events are one JSON line per turn in `events.jsonl`. Key fields:

| Field | Contents |
|-------|----------|
| `.turn` | Turn number |
| `.input` | Player's text input |
| `.ruling_prompt.*` | Ruling stream: system, user, output |
| `.narrate_prompt.*` | Narrate stream: system, user, prose output |
| `.extraction.scene.*` | Scene extractor: system, user, NPC/location JSON |
| `.extraction.state.*` | State extractor: system, user, inventory/condition JSON |
| `.extraction.storytell.*` | Storyteller: system, user, GM beat + thread JSON |
| `.applied` | State deltas that were applied |
| `.rejected` | State deltas that were rejected with reasons |
| `.pacing_context` | scene_phase, directive, outcome_hint, convergence |
| `.state_snapshot` | Full state at start of turn |
| `.post_turn_pending_beat` | pending_gm_beat after turn processing |

### Data sources

| Source | Events field | Used by |
|--------|-------------|---------|
| Turn data | `.turn`, `.input`, `.ruling_prompt`, `.narrate_prompt`, `.extraction.*` | summary, timing, turn, prompt |
| State deltas | `.applied`, `.rejected` | deltas, mechanics, diff, trace, search |
| Active state | `state.yaml` in save dir | state |
| Threads | `.extraction.storytell.output.*`, sanitizer events | threads, thread-audit |
| Beat data | `.extraction.storytell.output.gm_beat`, `.pacing_context` | beats, mechanics |
| Pacing | `.pacing_context` | beats, mechanics --pacing, convergence |
| Goals | `.extraction.storytell.output.goal_update`, `.state_snapshot` | goals, arc_goal_updates |
| Sanitizer | `kind="sanitizer"` events | thread-audit, sanitizer_lifecycle |

---

## Rubric quick reference

| Rubric area | Commands | What to look for |
|-------------|----------|-----------------|
| 1. Phase transitions | `beats`, `mechanics <N> --pacing`, `convergence` | scene_phase follows state machine, convergence_score drives CLIMAX |
| 2. GM Beats | `beats`, `mechanics <N> --pacing` | No 3+ consecutive pressure |
| 3. Inventory | `state-history`, `deltas <N>` | Add/remove balance |
| 4. Conditions | `active-conditions`, `deltas <N>` | Max 5 concurrent |
| 5. NPC Presence | `npc-ghosting`, `diff <A> <B> --section npcs` | No unexplained disappearance |
| 6. Location | `trace pc.location`, `diff <A> <B> --section location` | Continuous transitions |
| 7. Sanitizer | `thread-audit`, `check <N> sanitizer_lifecycle` | Thread ID consistency |
| 8. Pacing | `beats`, `check <N> pacing_directives` | Directives match tone |
| 9. State Fidelity | `state`, `check <N> state_fidelity` | Snapshot matches state |
| 10. Arc Goals | `goals`, `check <N> arc_goal_updates` | Structured goal updates |
| 11. Rulings | `ruling-audit`, `mechanics <N>`, `rolls --summary` | reason non-empty, band distribution |
| 12. Format | `compat` | extraction_context present |
| 13. Threads | `threads --summary`, `thread-audit` | Resolution rate, hallucinated threads |

For detailed checker docs see [CHECKERS.md](CHECKERS.md). For the full rubric see [RUBRIC.md](RUBRIC.md).
