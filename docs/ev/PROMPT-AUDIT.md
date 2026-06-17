# Prompt Template Audit

Audit prompt templates to verify all Jinja2 variables are plumbed correctly. Three variants depending on scope.

## 1. User-Only Audit (Plumbing Check)

Render each `*_user.j2` against a real `state.yaml` (or constructed context) and verify all Jinja2 variables resolve. Catches:

- **Undefined variables** — silently render as empty strings (Jinja2 default `Undefined`)
- **Wrong nesting level** — variable exists in context but accessed at wrong depth (e.g. `completed_threads` at top level when it's inside `current_arc`)
- **Context keys declared but never passed** — boundary model declares a field but the pipeline never populates it
- **Section template scope issues** — shared sections like `_arc.j2` accessed from both narrate and storytell contexts with different variable layouts

### Workflow

Use `prompt-eval dump` (render only, no LLM):

```bash
# Render a single turn's user prompt
.venv/bin/python scripts/debug/ev.py prompt-eval dump <save-dir> --turn N --stream <stream>

# Or verify by rendering against state.yaml directly:
# (example script pattern)
.venv/bin/python -c "
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import yaml

state = yaml.safe_load(Path('state.yaml').read_text())
env = Environment(loader=FileSystemLoader('ccya/prompts'), keep_trailing_newline=True)

# Build context matching the pipeline's construction in narrate.py / extraction.py
ctx = {
    'state': state,
    'pc': state.get('pc') or {},
    'current_arc': {...},
    ...
}
rendered = env.get_template('narrate_user.j2').render(**ctx)
print(rendered)
"
```

### Check for

- **Silent Undefined**: search for empty sections where data should appear. In production Jinja2 (default `Undefined`), missing variables render as empty — no error. Compare against the boundary model in `ccya/prompts/context.py`.
- **Wrong-level access**: shared section templates (`_arc.j2`, `_thread_list.j2`) accessed from multiple parent prompts. Verify the variable is passed at the level the section expects.
- **Boundary alignment**: cross-reference `TEMPLATE_CONTRACTS` in `ccya/prompts/context.py` with the template's actual variable usage. The alignment test in `tests/test_alignment.py` does this via AST parsing.

### All user prompts (7 total)

| Prompt | Pipeline step |
|--------|--------------|
| `ruling_user.j2` | Step 0: Ruling |
| `narrate_user.j2` | Step 1: Narrate |
| `extract_scene_user.j2` | Step 2a: Extract Scene |
| `extract_state_user.j2` | Step 2b: Extract State |
| `storytell_user.j2` | Step 3: Storytell |
| `generate_seed_user.j2` | Seed generation |
| `generate_pack_user_wb.j2` | World build |

## 2. System-Only Audit

Same process for `*_system.j2` templates. These have fewer variables — mostly `narrator_rules`, `world_rules`, pacing directives. Render with `prompt-eval dump --system`:

```bash
.venv/bin/python scripts/debug/ev.py prompt-eval dump <save-dir> --turn N --stream <stream> --system
```

## 3. Full Eval (Render + LLM + Check)

Renders prompts, sends to LLM, validates output with checkers:

```bash
# Using a scenario YAML
.venv/bin/python scripts/debug/ev.py prompt-eval call <scenario.yaml>
.venv/bin/python scripts/debug/ev.py prompt-eval call <scenario.yaml> --from-events

# Or run a full game eval
.venv/bin/python scripts/debug/ev.py eval run scenarios/my-scenario.yaml --report results.md
```

The `--from-events` mode uses stored LLM output (no new LLM call) — useful for re-checking past runs.
