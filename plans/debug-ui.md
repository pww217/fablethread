# Plan H — Turn Inspector Debug UI

## Status: Pending

---

## What This Is

A local web UI that shows a visual breakdown of every turn: what went into each prompt, what came out, and what changed in game state. The purpose is to make extraction bugs, prompt bloat, and template regressions visible without reading raw log files.

This is an MVP. Filtering, search, and advanced analysis are out of scope for now.

---

## Architecture

- **Separate FastAPI app** on its own port (default `8765`), independent of the game server
- **Feature-flagged** — only starts if `DEBUG_UI=true` is set in environment (or `.env`)
- **Reads from `events.jsonl`** — polls for new turns when the client requests them
- **No database** — `events.jsonl` is the source of truth
- **Single HTML file** served from FastAPI — no build step, no Node.js

---

## Feature Flag (Windows-Safe)

The debug server must not start automatically. Gate it behind an environment variable.

In `.env` (not committed):
```
DEBUG_UI=true
DEBUG_UI_PORT=8765
```

In engine startup code:
```python
import os

DEBUG_UI_ENABLED = os.getenv("DEBUG_UI", "false").lower() == "true"
DEBUG_UI_PORT = int(os.getenv("DEBUG_UI_PORT", "8765"))

if DEBUG_UI_ENABLED:
    import subprocess
    subprocess.Popen(
        ["python", "-m", "ccya.debug_server"],
        env={**os.environ, "DEBUG_UI_PORT": str(DEBUG_UI_PORT)}
    )
```

Or run it manually in a second terminal:
```bash
DEBUG_UI=true python -m ccya.debug_server
```

The game engine runs fine without it. The debug server has no write access to game state.

---

## Events.jsonl Changes

The current `events.jsonl` contains state deltas (outputs). The debug UI also needs the **rendered prompt inputs** and **timing**. Extend each turn event with new fields.

### Fields to ADD to each turn event

```python
turn_event["debug"] = {
    # Rendered prompt inputs (full strings, as sent to LLM)
    "prompts": {
        "rules": {
            "system": rendered_rules_system,   # string
            "user": rendered_rules_user,        # string
            "tokens_in": N,
            "tokens_out": N,
            "latency_ms": N
        },
        "narrate": {
            "system": rendered_narrate_system,
            "user": rendered_narrate_user,
            "tokens_in": N,
            "tokens_out": N,
            "latency_ms": N
        },
        # If using split extraction (Plan G):
        "extract_scene": {
            "system": rendered_extract_scene_system,
            "user": rendered_extract_scene_user,
            "tokens_in": N,
            "tokens_out": N,
            "latency_ms": N,
            "skipped": False
        },
        "extract_state": {
            "system": rendered_extract_state_system,
            "user": rendered_extract_state_user,
            "tokens_in": N,
            "tokens_out": N,
            "latency_ms": N,
            "skipped": False
        },
        "extract_progress": {
            "system": rendered_extract_progress_system,
            "user": rendered_extract_progress_user,
            "tokens_in": N,
            "tokens_out": N,
            "latency_ms": N,
            "skipped": False
        }
    },
    # Raw LLM outputs BEFORE _reasoning is stripped
    "raw_outputs": {
        "rules": rules_raw_string,
        "narrate": narrate_raw_string,
        "extract_scene": extract_scene_raw_string,
        "extract_state": extract_state_raw_string,
        "extract_progress": extract_progress_raw_string
    },
    # State snapshots for diff view
    "state_before": snapshot_before,   # deep copy of game_state BEFORE delta applied
    "state_after": snapshot_after      # deep copy of game_state AFTER delta applied
}
```

### How to capture token counts

If using Ollama, the response includes `prompt_eval_count` and `eval_count`. Capture them:

```python
response = ollama.chat(model=model, messages=messages)
tokens_in = response.get("prompt_eval_count", 0)
tokens_out = response.get("eval_count", 0)
```

### How to capture latency

```python
import time

start = time.monotonic()
response = ollama.chat(...)
latency_ms = int((time.monotonic() - start) * 1000)
```

### How to snapshot state

```python
import copy

snapshot_before = copy.deepcopy(game_state)  # before applying delta
# ... apply delta ...
snapshot_after = copy.deepcopy(game_state)   # after applying delta
```

**Important:** Do not snapshot the full game state if it is very large. Snapshot only the fields the UI needs:

```python
def state_snapshot(game_state: dict) -> dict:
    return {
        "inventory": copy.deepcopy(game_state.get("inventory", [])),
        "conditions": copy.deepcopy(game_state["pc"].get("conditions", [])),
        "quests": copy.deepcopy(game_state.get("quests", [])),
        "established_facts": copy.deepcopy(game_state.get("established_facts", [])),
        "present_npcs": copy.deepcopy(game_state.get("present_npcs", [])),
        "location": copy.deepcopy(game_state.get("location", {}))
    }
```

---

## Server: `ccya/debug_server.py`

Create a new file at `ccya/debug_server.py`.

```python
"""
CCYA Debug UI server.
Run manually: DEBUG_UI=true python -m ccya.debug_server
Do NOT import this file from the main engine — it starts its own process.
"""

import os
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="CCYA Debug UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Path to events.jsonl — adjust if your save structure differs
SAVE_DIR = Path(os.getenv("CCYA_SAVE_DIR", "./saves"))


def get_events_path(save_id: str) -> Path:
    return SAVE_DIR / save_id / "events.jsonl"


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the single-page debug UI."""
    html_path = Path(__file__).parent / "debug_ui.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/api/saves")
def list_saves():
    """List available save directories."""
    if not SAVE_DIR.exists():
        return JSONResponse({"saves": []})
    saves = [d.name for d in SAVE_DIR.iterdir() if d.is_dir()]
    return JSONResponse({"saves": sorted(saves)})


@app.get("/api/turns/{save_id}")
def get_turns(save_id: str, after: int = 0):
    """
    Return all turn events for a save, optionally only turns after a given turn number.
    The client polls this endpoint to get new turns as the game progresses.
    """
    events_path = get_events_path(save_id)
    if not events_path.exists():
        return JSONResponse({"turns": [], "error": "Save not found"})

    turns = []
    with open(events_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if event.get("turn", 0) > after:
                    turns.append(event)
            except json.JSONDecodeError:
                continue

    return JSONResponse({"turns": turns})


@app.get("/api/turn/{save_id}/{turn_number}")
def get_turn(save_id: str, turn_number: int):
    """Return a single turn event by turn number."""
    events_path = get_events_path(save_id)
    if not events_path.exists():
        return JSONResponse({"error": "Save not found"}, status_code=404)

    with open(events_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if event.get("turn") == turn_number:
                    return JSONResponse(event)
            except json.JSONDecodeError:
                continue

    return JSONResponse({"error": "Turn not found"}, status_code=404)


if __name__ == "__main__":
    port = int(os.getenv("DEBUG_UI_PORT", "8765"))
    print(f"CCYA Debug UI running at http://localhost:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
```

---

## UI: `ccya/debug_ui.html`

Create a new file at `ccya/debug_ui.html`. This is a self-contained single-page app with no build step.

### Layout

Three columns:

```
┌─────────────────┬──────────────────────────────┬─────────────────┐
│   TURN LIST     │   PIPELINE VIEW              │   STATE DIFF    │
│                 │                              │                 │
│  Turn 1  ✓      │  ┌────────┐ ┌────────┐ ...  │  inventory:     │
│  Turn 2  ✓      │  │ RULES  │ │NARRATE │       │  + iron key     │
│  Turn 3  ⚠      │  │ 342 in │ │1847 in │       │  conditions:    │
│  Turn 4  ✓      │  │  89 out│ │ 412 out│       │  + sand_eyes    │
│  Turn 5  ✓      │  │  1.2s  │ │   8.4s │       │  quests:        │
│  ...            │  └────────┘ └────────┘       │  (no change)   │
│                 │                              │                 │
│                 │  Click a stage to expand     │                 │
│                 │  full prompt below           │                 │
└─────────────────┴──────────────────────────────┴─────────────────┘
```

### Turn list color coding
- Green dot: clean turn (no `_failed`, no parse errors)
- Yellow dot: `_failed` present in any stream
- Red dot: parse error or missing `debug` field

### Pipeline stage cards
Each stage card shows:
- Stage name (RULES / NARRATE / EXTRACT SCENE / EXTRACT STATE / EXTRACT PROGRESS)
- Token count in / out
- Latency in ms
- "SKIPPED" badge if the stream was skipped

Clicking a card expands a panel below showing:
- **System prompt** (full rendered text)
- **User prompt** (full rendered text)
- **Raw output** (full LLM response before stripping)

The two prompts are the most important thing to be able to read. Make them easy to scroll.

### State diff panel
For the selected turn, show what changed between `state_before` and `state_after`:
- `+` in green for additions
- `-` in red for removals
- `~` in yellow for updates

Categories shown: inventory, conditions, quests, established_facts, present_npcs, location.

### Polling
The UI polls `/api/turns/{save_id}?after={last_known_turn}` every 3 seconds while a save is selected. New turns appear in the turn list automatically as the game runs.

### Save selector
At the top of the turn list: a dropdown populated from `/api/saves`. Changing the selection reloads the turn list for that save.

---

## File Summary

| File | Action |
|------|--------|
| `ccya/debug_server.py` | Create new |
| `ccya/debug_ui.html` | Create new |
| `ccya/engine/*.py` (main engine file) | Add `debug` block to turn event logging |
| `.env.example` | Add `DEBUG_UI=false` and `DEBUG_UI_PORT=8765` |
| `.gitignore` | Ensure `.env` is already ignored (check) |

---

## Checklist

- [ ] Add `debug` block to turn event logging in engine (rendered prompts, raw outputs, state snapshots, token counts, latency)
- [ ] Capture `tokens_in`, `tokens_out`, `latency_ms` in each `llm_call` invocation
- [ ] Add `state_snapshot()` helper to engine
- [ ] Create `ccya/debug_server.py`
- [ ] Create `ccya/debug_ui.html` with three-column layout
- [ ] Add `DEBUG_UI` feature flag to engine startup
- [ ] Add `DEBUG_UI=false` and `DEBUG_UI_PORT=8765` to `.env.example`
- [ ] Verify `.env` is in `.gitignore`
- [ ] Test: start debug server, play 3 turns, confirm turns appear in UI
- [ ] Test: click a pipeline stage, confirm full rendered prompt is visible
- [ ] Test: state diff shows correct additions/removals for a known turn
