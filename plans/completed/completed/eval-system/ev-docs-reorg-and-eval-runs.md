# EV Tooling Reorganization: Docs Consolidation + Eval Run Storage

## Purpose

Consolidate all ev.py documentation into `docs/ev/`, move interactive/automated game runs from `saves/ev/` to `evals/runs/` with a versioned directory structure, and document the prompt-audit workflow.

## Problem Statement

Three problems:
1. **Split docs**: ev.py command reference lives in `scripts/debug/README.md` while checker docs live in `docs/ev/CHECKERS.md`. The ev skill points to both. All ev docs should live in one place.
2. **No eval versioning**: Eval runs land in `saves/ev/<timestamp>_<random6>/` — no git SHA, no grouping by day/commit, no structured metadata for comparison.
3. **Prompt audit workflow**: The template-variable plumbing check I just did manually has no documented procedure. `prompt-eval dump` and `prompt-eval call` exist but aren't documented anywhere a user can find them.

## Constraints

- `saves/` continues to exist for web-UI-created games. Only automated/CLI runs move.
- Server's "show EV saves" checkbox must continue working.
- Existing saves in `saves/ev/` and `saves/default/` must remain loadable.
- The two-level eval dir layout must not break the server's save-switcher.
- `make check` must pass after every phase.

## Non-goals

- NOT rewriting ev.py commands or their internal logic (except save-path constants).
- NOT changing how the server's game-creation flow works (`saves/<pack-name>-<date>` stays).
- NOT migrating `saves/default/` to `evals/` — it's a different class of save.

## Solution

Five phases executed in order:

1. Scaffold `evals/ev-tooling/` (committed) + `evals/runs/` (gitignored).
2. Change ev.py's default save path from `saves/ev/` to `evals/runs/` with two-level versioned naming and `run-meta.yaml`.
3. Update the server to discover and load saves from both `saves/` and `evals/runs/`.
4. Consolidate all ev documentation from `scripts/debug/README.md` into `docs/ev/`, writing new docs for prompt-audit, eval workflow, and niche commands.
5. Migrate existing `saves/ev/` sessions into `evals/runs/` and stub the old path.

## Firm decisions

1. Two-level directory layout: `evals/runs/YYYY-MM-DD--{tag}--{sha:8}/HHMM--{pack}--{persona}--{turns}t/`.
2. `evals/runs/latest` symlink points to the most recent individual run dir.
3. Server scans both `saves/` and `evals/runs/` for the save-switcher.
4. The "show EV saves" checkbox in the UI changes to "show eval runs" and scans `evals/runs/`.
5. `run-meta.yaml` is auto-generated in each run dir with structured fields (git SHA, pack, persona, turns, duration, branch, pass-rate, etc.).
6. `evals/ev-tooling/` is committed; `evals/runs/` is gitignored.
7. `saves/ev/` symlink or dir stubbed to point to `evals/runs/` for backward compat during the transition.

## Risks, Ambiguities, and Blockers

- The server's `_save_rel_name()` and `switch_save()` hardcode `Path("saves")` as the root. Both need to accept `evals/runs/` paths too.
- The JS filter `s.name.startsWith('ev/')` needs to become kind-based or be updated to the new path structure.
- `_find_save_dirs()` in `app.py` already handles nested dirs one level deep (line 41-44) — the two-level `YYYY-MM-DD/HHMM` structure should work automatically.
- `saves/ev/latest` usage in `status.py` and `play.py --resume` must be redirected to `evals/runs/latest`.

### Resolved Ambiguities

1. **Git detection fallback:** When not in a git repo, git fields in `run-meta.yaml` default to `"no-repo"`.
2. **Latest save scan:** `_find_latest_save()` in `app.py` scans both `saves/` and `evals/runs/`. The server auto-resumes whatever was last touched.
3. **Checkbox behavior:** UI checkbox "Show eval runs" defaults to OFF. When checked, `evals/runs/` saves appear in the save-switcher alongside `saves/` ones.

## Status

`open`

## Phases

5 phases: [scaffold dirs → move save path → update server → consolidate docs → migrate old saves]

---

## Implementation — Phase 1: Scaffold `evals/` directory structure

### Context files to load

- `.gitignore` (check existing ignore patterns)
- `ccya/ev/play.py` (EV_SAVES_DIR constant line 25)

### Detailed steps

#### Step 1.1 — Create `evals/ev-tooling/` scaffolding

**File:** `evals/ev-tooling/`

**What:** Create the directory and its contents:
```
evals/
├── ev-tooling/
│   ├── README.md              # signpost — links to docs/ev/, explains the structure
│   └── templates/
│       ├── run-meta.yaml.j2   # Jinja2 template for auto-generated run metadata
│       └── report.md.j2       # Jinja2 template for evaluator report
└── runs/                      # gitignored — actual run data
```

**Why:** Separates tooling (committed) from artifacts (gitignored). Templates let ev.py generate consistent metadata.

**Validation:** `ls evals/ev-tooling/` shows the expected files.

#### Step 1.2 — Create `evals/runs/` and `evals/runs/latest`

**File:** `evals/runs/`

**What:** `mkdir -p evals/runs/`. Add `evals/runs/` to `.gitignore`. Create `evals/runs/latest` symlink placeholder (no target yet — auto-updated by ev.py).

**Why:** The ev.py play/init eval commands will write into this dir.

**Validation:** `ls evals/runs/` exists and is empty. `.gitignore` has the entry.

---

## Implementation — Phase 2: Change ev.py save path to `evals/runs/`

### Context files to load

- `ccya/ev/play.py` (EV_SAVES_DIR, _create_play_session, cmd_play resume path, latest symlink)
- `ccya/ev/init.py` (cmd_init save dir creation)
- `ccya/ev/eval.py` (EV_SAVES_DIR import, session_dir)
- `ccya/ev/status.py` (latest path)
- `ccya/ev/__init__.py` (DEFAULT_SAVE_DIR — NOT changing this, only saves/ev/ → evals/runs/)
- `ccya/ev/prompt_eval.py` (uses events, not save path directly)

### Detailed steps

#### Step 2.1 — Change EV_SAVES_DIR constant

**File:** `ccya/ev/play.py:25`

**What:** Change `EV_SAVES_DIR = Path("saves/ev")` to `EV_SAVES_DIR = Path("evals/runs")`.

**Why:** All CLI game sessions now write to `evals/runs/`.

**Validation:** `grep -r "saves/ev" ccya/ev/` returns no remaining hardcoded references in the ev module.

#### Step 2.2 — Update session naming to two-level versioned structure

**File:** `ccya/ev/play.py` (around lines 286-287, `_create_play_session()`)

**What:** Replace the single-level session name format. New format:
- Grouping dir: `YYYY-MM-DD--{latest_git_tag}--{sha8}/`
- Run dir: `HHMM--{pack}--{persona}--{turns}t/`

If git tag is unavailable, fall back to `YYYY-MM-DD--{branch}--{sha8}/` or `YYYY-MM-DD--unknown--{sha8}/`.

Use `.venv/bin/python -c "import subprocess; print(subprocess.check_output(['git','describe','--tags','--always']).decode().strip())"` or equivalent to determine the tag/version.

The run dir is created as `group_dir / run_dir`. `latest` symlink points to the full `group_dir / run_dir` path.

**Why:** Grouping by day+commit allows a glance to see "these 4 runs were on the same code." The HHMM disambiguates within a day.

**Validation:** Run `ev.py init --pack noir-1930s` and verify the directory structure matches `evals/runs/2026-06-16--v0.3.1--abc1234f/1615--noir1930s--explorer--20t/`.

#### Step 2.3 — Generate run-meta.yaml on session creation

**File:** `ccya/ev/play.py` (new function or inline after session dir creation)

**What:** After creating the session directory, write `run-meta.yaml` with:

```yaml
# auto-generated by ev.py
created_at: "2026-06-16T20:49:41"
git_sha: "abc1234f"  # "no-repo" if not a git repository
git_branch: "main"
git_tag: "v0.3.1"
git_dirty: false
pack: "noir-1930s"
personality: "explorer"
max_turns: 20
actual_turns: null  # filled after session ends
duration_ms: null   # filled after session ends
pass_rate: null     # filled by eval --check
```

**Why:** Structured metadata enables `ev.py eval list --format table` comparison across runs.

**Validation:** After `ev.py init --pack noir-1930s`, `run-meta.yaml` exists and has correct git SHA.

#### Step 2.4 — Update `ev.py init` save dir creation

**File:** `ccya/ev/init.py` (around line 24)

**What:** The `init` command calls `_create_play_session()` from play.py, which is already updated in Step 2.2. No additional change needed — verify it inherits the new path.

**Validation:** `ev.py init --pack zombie-survival --personality cautious` creates dir under `evals/runs/`.

#### Step 2.5 — Update `ev.py eval` session dir creation

**File:** `ccya/ev/eval.py:50`

**What:** The eval command imports `EV_SAVES_DIR` from `play.py`. After Step 2.1, this automatically points to `evals/runs/`. Verify the eval session creation path.

**Validation:** `grep EV_SAVES_DIR ccya/ev/eval.py` and confirm it's imported from play.py (not hardcoded).

#### Step 2.6 — Update `status.py` latest path

**File:** `ccya/ev/status.py:18`

**What:** Change `Path("saves/ev/latest")` to `EV_SAVES_DIR / "latest"` (import from play.py).

**Why:** Avoids a second hardcoded path.

**Validation:** `ev.py status` works without --save-dir and finds `evals/runs/latest`.

#### Step 2.7 — Update `--resume` path in play.py

**File:** `ccya/ev/play.py` (cmd_play, around line 573)

**What:** The `--resume` fallback path `EV_SAVES_DIR / "latest"` already uses the constant, so it auto-updates. Verify there's no hardcoded `"saves/ev/latest"` string remaining.

**Validation:** `grep -rn "saves/ev" ccya/ev/` returns no results.

---

## Implementation — Phase 3: Update server to scan `evals/runs/`

### Context files to load

- `ccya/server/routes.py` (_list_saves, _save_rel_name, switch_save, delete_save)
- `ccya/server/app.py` (_find_save_dirs, _find_latest_save, SAVE_DIR)
- `ccya/templates/index.html` (filteredSaves JS, savePicker UI)

### Detailed steps

#### Step 3.1 — Update `_find_save_dirs()` to accept multiple root dirs

**File:** `ccya/server/app.py:31-45`

**What:** Refactor `_find_save_dirs()` to accept a list of root paths instead of a single one. Or create a new function `_find_all_save_dirs()` that calls it for both `saves/` and `evals/runs/`.

The function already handles nested dirs one level deep (lines 41-44), which matches the two-level evals/runs/YYYY-MM-DD/HHMM structure — it will find each individual run dir automatically.

```python
def _find_all_save_dirs() -> list[Path]:
    all_dirs: dict[str, Path] = {}
    for root in [Path("saves"), Path("evals/runs")]:
        if root.exists():
            for entry in root.iterdir():
                if not entry.is_dir() or entry.name == "default":
                    continue
                if (entry / "state.yaml").exists():
                    r = entry.resolve()
                    all_dirs.setdefault(str(r), r)
                else:
                    for sub in entry.iterdir():
                        if sub.is_dir() and (sub / "state.yaml").exists():
                            r = sub.resolve()
                            all_dirs.setdefault(str(r), r)
    return list(all_dirs.values())
```

**Why:** The server needs to discover both web-UI saves and CLI eval runs.

**Validation:** Create a dummy run dir at `evals/runs/2026-06-16--test--abc1234f/1615--test-pack/` with a state.yaml and verify it appears in the API response.

#### Step 3.2 — Update `_save_rel_name()` and `_list_saves()` for dual roots

**File:** `ccya/server/routes.py:113-119` and `122-142`

**What:** `_save_rel_name()` currently computes relative to `saves/`. Change it to compute relative to whichever root the path falls under:

```python
def _save_rel_name(save_dir: Path) -> str:
    for root in [Path("saves"), Path("evals/runs")]:
        root_resolved = root.resolve()
        try:
            return str(save_dir.resolve().relative_to(root_resolved))
        except ValueError:
            continue
    return save_dir.name
```

`_list_saves()` currently hardcodes `saves_dir = Path("saves")`. Change it to use `_find_all_save_dirs()` from Step 3.1 instead of `_find_save_dirs(saves_dir)`.

**Why:** The UI needs to show the correct relative path for both classes of save.

**Validation:** API returns runs from both `saves/` and `evals/runs/` with correct relative paths.

#### Step 3.3 — Update switch_save/delete_save guards

**File:** `ccya/server/routes.py:822-829` and `875-881`

**What:** The path guard currently checks `target.relative_to(Path("saves").resolve())`. Change to check against both roots:

```python
def _is_valid_save_path(target: Path) -> bool:
    for root in [Path("saves"), Path("evals/runs")]:
        try:
            target.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False
```

Replace the inline `try/except` blocks with this function.

**Why:** Prevents path traversal attacks while allowing both save locations.

**Validation:** Switch to an evals/runs/ path works. Switch to `/etc/passwd` is rejected.

#### Step 3.4 — Update JS filter for show-eval-runs checkbox

**File:** `ccya/templates/index.html:2202-2206`

**What:** The existing `filteredSaves()` filters by `!s.name.startsWith('ev/')`. Since the path structure has changed, add a `kind` field to the save dict in `_list_saves()` (e.g. `"kind": "server"` or `"kind": "eval"`) and use that:

```javascript
filteredSaves() {
    const saves = this.savePicker.saves;
    if (this.savePicker.showEvGames) return saves;
    return saves.filter(s => s.kind !== 'eval');
},
```

Rename the checkbox label from "Show EV saves" to "Show eval runs".

**Why:** More robust than string prefix checking. The old `ev/` prefix no longer applies.

**Validation:** Toggle the checkbox in the UI — eval runs appear/disappear.

---

## Implementation — Phase 4: Consolidate docs to `docs/ev/`

### Context files to load

- `scripts/debug/README.md` (full 591-line reference)
- `docs/ev/CHECKERS.md`
- `docs/ev/RUBRIC.md`
- `docs/ev/consolidated-findings.md`
- `.opencode/skills/ev/SKILL.md` (signposts)
- `AGENTS.md` (signposts referencing scripts/debug/README.md)

### Detailed steps

#### Step 4.1 — Move `consolidated-findings.md` to `plans/completed/`

**File:** `docs/ev/consolidated-findings.md`

**What:** This is a one-off analysis report, not reference documentation. Move to `plans/completed/ev-session-findings.md`.

**Why:** Keeps `docs/ev/` focused on reference material.

**Validation:** File exists at the new path, not the old path.

#### Step 4.2 — Create `docs/ev/README.md` as the new entry point

**File:** `docs/ev/README.md`

**What:** Write a new README that serves as the entry point for all ev.py documentation. Structure:

```markdown
# ev.py — CCYA Debug & Eval CLI

## Quick Start
(condensed from scripts/debug/README.md — 1-2 paragraphs max)

## Command Reference
(link to the detailed command tables — the bulk content)

For the full command reference, see [COMMANDS.md](COMMANDS.md).
For the prompt audit workflow, see [PROMPT-AUDIT.md](PROMPT-AUDIT.md).
For the eval workflow and run storage, see [EVAL-RUNS.md](EVAL-RUNS.md).
For the checker library, see [CHECKERS.md](CHECKERS.md).
For the eval rubric, see [RUBRIC.md](RUBRIC.md).
```

**Why:** Single entry point instead of users needing to know about `scripts/debug/README.md`.

**Validation:** Renders correctly as markdown.

#### Step 4.3 — Create `docs/ev/COMMANDS.md` with full command reference

**File:** `docs/ev/COMMANDS.md`

**What:** Migrate the command reference tables from `scripts/debug/README.md` (lines 136-449 of the README: "See what happened", "What changed", "Thread, beat, and phase analysis", "Play", "Session management", "Validate", "Warnings", "Prompt size analysis"). Also add the currently-undocumented commands:

- `storyteller-audit` — checks storyteller output for thread_add/thread_resolve/arc_resolve consistency, missing goal_updates, GM beat validity against scene phase
- `ruling-audit` — validates ruling.reason non-empty, condition IDs present, band distribution
- `thread-audit` — thread lifecycle across all turns: created via thread_add, updated via thread_update, referenced by sanitizer
- `npc-ghosting` — detects NPC disappearance from compendium without departure tracking
- `state-history` — tracks conditions or inventory over time
- `active-conditions` — current conditions with turns_remaining
- `compat` — checks events.jsonl format compatibility (changes vs extraction_context)
- `prompt-eval` — fast prompt testing: `dump` (render only) and `call` (render + LLM + check)

**Why:** One authoritative reference for all ev.py commands, including the ones that were only discoverable via `--help`.

**Validation:** Every command from `ev.py --help` has a documented entry.

#### Step 4.4 — Create `docs/ev/PROMPT-AUDIT.md`

**File:** `docs/ev/PROMPT-AUDIT.md`

**What:** Document the prompt audit workflow with three variants:

1. **User-only audit (plumbing check)**: Render each `*_user.j2` against a real `state.yaml` (or constructed context) and verify all Jinja2 variables resolve. Use `prompt-eval dump` or a standalone script like the one in this session. Check for:
   - Undefined variables (silently render as empty strings)
   - Variables accessed at wrong nesting level
   - Context keys that are declared but never passed
   - Section templates (`_arc.j2`, `_thread_list.j2`) that access variables at the wrong scope
2. **System-only audit**: Same process for `*_system.j2` templates (fewer variables — narrator_rules, world_rules mostly).
3. **Full eval (render + LLM + check)**: Use `prompt-eval call <scenario.yaml>` to render prompts, send to LLM, and run checkers on the output. Or run a full `ev.py eval run` scenario.

Include:
- Example commands (`prompt-eval dump <save-dir> --turn N --stream <stream>`)
- The template-vs-boundary alignment test approach (AST-parsing the Jinja2 template and comparing against the boundary model)
- What to look for: silent `Undefined`, wrong-level access, missing context keys

**Why:** The pipeline has 7 user prompts + 6 system prompts with complex context construction. This is the workflow to catch variable plumbing bugs.

**Validation:** A developer can follow the doc and replicate the audit I just did.

#### Step 4.5 — Create `docs/ev/EVAL-RUNS.md`

**File:** `docs/ev/EVAL-RUNS.md`

**What:** Document the eval run storage structure, naming convention, metadata format, rubric-based report, focused eval workflow, and comparison workflow.

```markdown
# Eval Run Storage

## Directory Structure
evals/runs/
├── YYYY-MM-DD--{git-tag}--{sha:8}/   # day-group by commit
│   ├── HHMM--{pack}--{persona}--{turns}t/   # individual run
│   │   ├── state.yaml
│   │   ├── events.jsonl
│   │   ├── chronicle.md
│   │   ├── ev.yaml
│   │   ├── run-meta.yaml
│   │   └── report.md                  # auto-generated: rubric-grouped report
│   └── HHMM--{pack2}--{persona2}--{turns}t/
└── latest -> .../latest-run/

## Metadata (run-meta.yaml)
(field table)

## Report (report.md)
Reports are grouped by rubric area. Each area section shows:
- Which checkers apply (linked to CHECKERS.md)
- PASS/FAIL counts per checker
- Red flags per area (from RUBRIC.md)
- Trend indicator vs previous run

Example:
```
## 1. Phase Engine [3/4 pass]
  - phase_transition: PASS
  - climax_turn_counting: FAIL
  - breather_enforcement: PASS
  - scene_age_tracking: PASS
  ⚠ Red flag: CLIMAX exit without resolution

## 2. GM Beats [2/2 pass]
  ...
```

## Focused Evals (future)
Run only specific rubric areas with `--rubric 1,3,5` (Phase Engine + Inventory + NPC Presence).
This maps rubric area numbers to their checker list from RUBRIC.md and runs only those checkers.
Report shows only the selected rubric sections.

Rubric area → checker mapping (from RUBRIC.md):
| Area | Checkers |
|------|----------|
| 1. Phase Engine | phase_transition, climax_turn_counting, breather_enforcement, scene_age_tracking |
| 2. GM Beats | gm_beat_lifecycle, beat_phase_validity, beat_narrative_chain |
| 3. Inventory | inventory_integrity, state-fidelity (inventory) |
| ... | ... |

## Comparison
ev.py eval diff evals/runs/A/ evals/runs/B/
```

**Why:** Central reference for how evals are stored, reported, and compared. Rubric grouping focuses attention on problem areas.

**Validation:** File exists and accurately describes the structure.

#### Step 4.5b — Update `evals/ev-tooling/templates/report.md.j2` to mirror rubric

**File:** `evals/ev-tooling/templates/report.md.j2`

**What:** Replace the placeholder template with one that groups checkers by rubric area:

```jinja2
# Eval Report — {{ pack }} / {{ personality }}

- **Date:** {{ created_at }}
- **Git SHA:** {{ git_sha }}
- **Branch:** {{ git_branch }}
- **Pack:** {{ pack }}
- **Persona:** {{ personality }}
- **Turns:** {{ actual_turns }} / {{ max_turns }}
- **Duration:** {{ duration_ms }} ms
- **Pass rate:** {{ pass_rate }}

## Results by Rubric Area

{% for area in rubric_areas %}
### {{ area.number }}. {{ area.name }} [{{ area.passed }}/{{ area.total }}]
{% for checker in area.checkers %}
  - {{ checker.name }}: {{ checker.status }}{% if checker.detail %} — {{ checker.detail }}{% endif %}
{% endfor %}
{% if area.red_flags %}
  ⚠ Red flags: {{ area.red_flags | join("; ") }}
{% endif %}
{% endfor %}

## Comparison vs Previous Run

{% if prev_run %}
- **Previous:** {{ prev_run.path }} ({{ prev_run.date }})
- **Pass rate change:** {{ "%+d" | format(pass_rate_delta) }}%
{% else %}
No previous run to compare.
{% endif %}
```

**Why:** Mirrors the eval rubric structure so readers focus on problem areas, not a flat list.

**Validation:** Template renders without Jinja2 errors when given rubric_areas data.

#### Step 4.6 — Add `kind` field to save listing in routes.py

**File:** `ccya/server/routes.py` (inside `_list_saves()` loop)

**What:** After computing the relative `name`, add a `kind` field to each save dict:

```python
kind = "eval" if name.startswith("runs/") else "server"
```

This is used by the UI filter.

**Why:** The JS needs a reliable way to distinguish save types.

**Validation:** API returns `kind` field for every save.

#### Step 4.7 — Update ev skill signpost

**File:** `.opencode/skills/ev/SKILL.md`

**What:** Change the signpost from pointing to `scripts/debug/README.md` to pointing to `docs/ev/README.md`.

**Validation:** Skill doc references `docs/ev/` paths only.

#### Step 4.8 — Update AGENTS.md signposts

**File:** `AGENTS.md`

**What:** Find and update any references to `scripts/debug/README.md` to point to `docs/ev/`.

**Validation:** `grep "scripts/debug/README" AGENTS.md` returns no results.

#### Step 4.9 — Stub `scripts/debug/README.md`

**File:** `scripts/debug/README.md`

**What:** Replace the 591-line README with a short stub:

```markdown
# ev.py CLI

Full documentation has moved to `docs/ev/README.md`.

This directory is the ev.py source code. The command entry points are:
- `scripts/debug/ev.py` — main CLI entry point
- `ccya/ev/` — command implementations (play, check, eval, prompt-eval, etc.)
```

Optionally keep the "Common mistakes" section since those are deployment notes about the venv.

**Why:** Eliminates the split-brain documentation. Single source of truth.

**Validation:** Stub is readable and links to `docs/ev/`.

---

## Implementation — Phase 5: Migrate existing `saves/ev/` content

### Context files to load

- `saves/ev/` (list existing sessions to migrate)

### Detailed steps

#### Step 5.1 — Detect and migrate existing sessions

**File:** (one-time migration script, e.g. `scripts/tools/migrate-ev-saves.sh`)

**What:** For each session dir in `saves/ev/`, compute the new path under `evals/runs/` by:
1. Parsing the `run-meta.yaml` or `ev.yaml` for git SHA, pack, personality
2. Falling back to reading `state.yaml` meta if no config files exist
3. Moving the directory to `evals/runs/<YYYY-MM-DD>--<tag>--<sha>/<original-name>/`

If no metadata can be extracted, use `unknown` for tag/sha/pack/persona.

**Why:** Ensures existing eval sessions are not orphaned.

**Validation:** `ls evals/runs/*/*/state.yaml` shows the migrated sessions. `ls saves/ev/` is empty (or has only a README explaining where they went).

#### Step 5.2 — Create `saves/ev/` README stub

**File:** `saves/ev/README.md`

**What:** Brief note that eval sessions have moved to `evals/runs/`.

**Validation:** File exists with clear migration notice.

