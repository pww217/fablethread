# ev.py Command Reference

## Common pitfalls

1. Use `.venv/bin/python scripts/debug/ev.py` — never `python3` or `source .venv/bin/activate`
2. `ev.py play --llm --turns N` — set shell timeout to at least N×60000ms (~1 min/turn)
3. `--pack` required for new sessions; `--save-dir` for existing saves

## Save directory convention

All inspection commands require `--save-dir DIR`. There is no default or positional path support.

| Pattern | Command |
|---------|---------|
| Latest run | `ev.py turn 5 --save-dir evals/runs/latest` |
| Specific run | `ev.py turn 5 --save-dir evals/runs/YYYY-MM-DD_{tag}_{sha}/run-name/` |

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
| One-line overview | `ev.py summary --save-dir DIR` |
| Full timing + tokens | `ev.py timing --save-dir DIR` |
| Full dump of one turn | `ev.py turn <N> --save-dir DIR` |
| Specific stream prompt/output | `ev.py prompt <N> <stream> [--system] [--field FIELD] [--from-events] --save-dir DIR` |
| All JSON outputs for a turn | `ev.py turn <N> --json --save-dir DIR` |
| Sanitizer events for a turn | `ev.py sanitizer <N> --save-dir DIR` |

**Stream names:** `ruling` (or `rules`), `narrate`, `scene`, `state`, `record` (or `progress`), `world`. `storytell` is a deprecated alias for `record`.

## State & diff tracking

| If you want... | Command |
|---|---|
| Current game state | `ev.py state --save-dir DIR [--format full\|compact\|pc\|inventory\|location\|scene\|arc\|npcs\|compidx]` |
| What mutated on a turn | `ev.py deltas <N> --save-dir DIR` |
| Compare two turns' state | `ev.py diff [turnA] [turnB] [--section npcs\|inventory\|conditions\|location\|tags\|applied] --save-dir DIR` |
| Track one field across turns | `ev.py trace <field.path> [--from N] [--to N] [--show-unchanged] --save-dir DIR` |
| Find turns matching a pattern | `ev.py search <field>:<value> [--or <field>:<value>] --save-dir DIR` |
| Mechanics + beats + pacing | `ev.py mechanics <N> [--pacing] [--dice] [--sanitize] --save-dir DIR` |

## Thread, beat, and phase analysis

| If you want... | Command |
|---|---|
| Thread lifecycle | `ev.py threads --save-dir DIR` |
| Thread resolution summary | `ev.py threads --summary --save-dir DIR` |
| Beat type + surface + candidates | `ev.py beats --save-dir DIR` |
| Roll bands per turn | `ev.py rolls --save-dir DIR` |
| Roll distribution | `ev.py rolls --summary --save-dir DIR` |
| Convergence score + threads | `ev.py convergence --save-dir DIR [--by-scene]` |
| Convergence threads list | `ev.py trace convergence_threads --save-dir DIR` |
| NPC updates per turn | `ev.py trace npc_updates --save-dir DIR` |
| Phase transitions | `ev.py phase-transitions --save-dir DIR [--by-scene]` |
| Curtain Call compliance | `ev.py curtain-call --save-dir DIR [--by-scene]` |
| Goal changes | `ev.py goals --save-dir DIR` |

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
| `--auto-report` | Generate `report.md` after session (requires `--eval` or runs checkers for report) |

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
ev.py status --save-dir evals/runs/latest
```

## Persona registry

```bash
ev.py personas
```

Shows user persona registry from `PERSONA_REGISTRY_FILE`.

## Validate — checkers & eval

```bash
ev.py check --all --save-dir evals/runs/latest
ev.py check --all --verbose --save-dir evals/runs/latest
ev.py check --list
ev.py check 5 phase_transition --save-dir evals/runs/latest
ev.py check 5 --all --llm --save-dir evals/runs/latest
ev.py eval run scenarios/my-scenario.yaml --report results.md
ev.py eval list
ev.py eval compare evals/runs/baseline evals/runs/current
```

`eval compare` runs deterministic checkers on both runs and produces a side-by-side table showing IMPROVED, REGRESSION, unchanged, added, or removed checkers. Handles both single-pack and multi-pack run directories.

## Warnings

```bash
ev.py warnings --save-dir DIR
```

Signals: `extract.retries`, `retry_errors`, `rejected`, `reconcile_warnings`, `thread_dedup_rejections`, `compendium_dedup_redirects`.

## Prompt size analysis

```bash
ev.py prompt-sizes --save-dir DIR
```

Stages: ruling, narrate, scene, state, record, world.

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
| `storyteller-audit` | Checks Record output: thread_update/thread_resolve/actions format compliance |
| `sanitizer` | Shows sanitizer events for a turn: thread changes, goal updates, world state candidates, progress dedup rejections |
| `ruling-audit` | Validates ruling.reason non-empty, condition IDs present, band distribution |
| `thread-audit` | Thread lifecycle across all turns: created by thread_add, updated, resolved, orphan detection |
| `npc-ghosting` | Detects NPC disappearance from compendium without departure tracking |
| `state-history` | Tracks conditions or inventory over time |
| `active-conditions` | Current conditions with max concurrent count |
| `compat` | Checks events.jsonl format compatibility (changes vs extraction_context) |

---

## Real debugging workflows

**"The phase isn't transitioning — why?"**
```bash
ev.py trace pacing_context.scene_phase --save-dir DIR
ev.py mechanics 12 --pacing --dice --save-dir DIR
```

**"The record extractor generated a wrong action"**
```bash
ev.py prompt 8 record user --save-dir DIR   # what the LLM saw
ev.py prompt 8 record output --save-dir DIR  # what it returned
```

**"An NPC disappeared from the compendium"**
```bash
ev.py diff 5 10 --section npcs --save-dir DIR
ev.py deltas 7 --save-dir DIR
```

---

## Data structure reference

Events are one JSON line per turn in `events.jsonl`. Key fields:

| Field | Contents |
|-------|----------|
| `.turn` | Turn number |
| `.input` | Player's text input |
| `.type` | Event type: `"turn"` for real turns, `"sanitizer"` for thread sanitizer events |
| `.ruling_prompt.*` | Ruling stream: system, user, output |
| `.narrate_prompt.*` | Narrate stream: system, user, prose output |
| `.extraction.scene.*` | Scene extractor: system, user, NPC/location JSON |
| `.extraction.state.*` | State extractor: system, user, inventory/condition JSON |
| `.extraction.record.*` | Record extractor: system, user, thread/actions JSON |
| `.extraction.world.*` | World step: system, user, beat suggestions |
| `.applied` | State deltas that were applied |
| `.rejected` | State deltas that were rejected with reasons |
| `.pacing_context` | scene_phase, directive, outcome_hint, convergence, convergence_threads |
| `.pacing_context.convergence_threads` | Thread IDs used for convergence computation |
| `.npc_updates` | Per-turn NPC updates from scene extraction |
| `.curtain_call` | Curtain call status: `"active"`, `"forced"`, or `""` |
| `.last_turn_state` | Full state at start of turn |
| `.post_turn_pending_beat` | pending_gm_beat after turn processing |

### Data sources

| Source | Events field | Used by |
|--------|-------------|---------|
| Turn data | `.turn`, `.input`, `.ruling_prompt`, `.narrate_prompt`, `.extraction.*` | summary, timing, turn, prompt |
| State deltas | `.applied`, `.rejected` | deltas, mechanics, diff, trace, search |
| Active state | `state.yaml` in save dir | state |
| Threads | `.extraction.record.output.*`, sanitizer events, `state.long_term_objective.threads` | threads, thread-audit |
| Beat data | `state.meta.pending_gm_beat`, `state.meta.beat_candidates`, `.pacing_context` | beats, mechanics |
| Pacing | `.pacing_context` | beats, mechanics --pacing, convergence |
| Convergence threads | `.pacing_context.convergence_threads` | convergence, trace |
| NPC updates | `.npc_updates` | trace |
| Curtain call | `.curtain_call` | curtain-call |
| Goal changes | sanitizer `changes_detail.goal`, `state.arc.long_term_objective` | goals, arc_goal_updates |
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
