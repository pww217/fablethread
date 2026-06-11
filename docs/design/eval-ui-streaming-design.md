# UI Streaming Improvements — Live Eval Streaming and Mid-Turn Pipeline Visibility

## Purpose

Design authority for how the web UI displays live eval progress and mid-turn pipeline state. Not a plan — decisions here are final and guide implementation plans.

## Problem Statement

The web UI has two gaps in eval visibility:

1. **No live eval streaming.** When running `ev.py eval run`, the user sees nothing until the entire eval completes. For a 41-minute full eval, this is unusable — there's no progress indicator, no per-scenario results, no way to interrupt.
2. **No mid-turn pipeline visibility.** During live gameplay (`ev.py play` or web UI interaction), the user cannot see the pipeline stages (ruling → extraction → narration → state) as they execute. There's no way to debug which stage produced an unexpected result.

## Constraints

- **Qwen3 35B at localhost:8080/v1 is the judge model.** ~5-10 tok/s on Apple Silicon.
- **Host model: same Qwen3 35B.** Engine and judge are the same model; they never run simultaneously.
- **FastAPI server already exists.** `ccya/server/routes.py` handles web UI routing. Streaming uses Server-Sent Events (SSE).
- **No WebSocket infrastructure.** SSE is sufficient for the streaming use case. WebSockets add complexity (connection management, reconnection logic) that SSE doesn't need.
- **No new backend services.** The FastAPI server handles all streaming. No separate streaming service or message queue.
- **ev.py is the survivor.** No new top-level CLI tools. The web UI uses the same `ccya/ev/` package for eval execution.
- **No backward compatibility with old streaming system.** Old streaming code is already deleted or unused.

## Non-goals

- **Real-time token streaming.** Streaming the LLM's output token-by-token is out of scope. This design covers eval progress and pipeline stage visibility, not token-level streaming.
- **Multi-user streaming.** Single-user only. No connection management for multiple concurrent users.
- **Streaming to CLI.** The CLI (`ev.py`) already produces output. This design covers the web UI only.
- **Historical streaming data.** No persistence of streaming events. Each streaming session is ephemeral.
- **Streaming for play command.** The play command (`ev.py play`) is CLI-only. Streaming is for eval and mid-turn pipeline visibility in the web UI.

## Decision Table

| Decision | What | Why |
|---|---|---|
| SSE for streaming | Server-Sent Events, not WebSockets | SSE is simpler: single connection, automatic reconnection, no message framing. The streaming use case is unidirectional (server → client), which is SSE's strength. |
| Streaming endpoint: `/api/eval/stream` | Single endpoint for all eval streaming | One endpoint to manage, one set of SSE logic. The endpoint accepts `scenario_id` and returns streaming events: `start`, `turn`, `checker`, `complete`, `error`. |
| Streaming events: structured JSON | Each SSE event is a JSON object with `type`, `data`, `timestamp` | Structured events allow the client to handle different event types (start, turn, checker, complete, error) without parsing text. |
| Mid-turn pipeline visibility: `/api/turn/pipeline` | Single endpoint for pipeline stage streaming during a turn | When the web UI sends a turn input, the pipeline stages execute sequentially. Each stage emits a streaming event: `ruling`, `extraction`, `narration`, `state`. The client displays each stage as it completes. |
| Pipeline stages: sequential, not parallel | Stages execute in order: ruling → extraction → narration → state | The engine pipeline is sequential by design. Streaming should reflect this: each stage's event is emitted only after the previous stage completes. |
| Streaming state: in-memory, not persistent | Streaming state is held in memory during the streaming session | No need to persist streaming events. Each streaming session is ephemeral. In-memory state is simpler and avoids database/Redis complexity. |
| Streaming timeout: 5 minutes | SSE connection times out after 5 minutes of inactivity | Prevents stale connections from consuming server resources. The client should reconnect if the streaming session exceeds 5 minutes. |
| Streaming cancellation: `/api/eval/cancel` | Single endpoint to cancel a running eval streaming session | The client can send a POST to this endpoint to cancel the streaming session. The server stops processing and sends a `cancelled` event. |

## Current State — What Exists

### Web UI

- `ccya/server/routes.py` — FastAPI routes for web UI
- `_render()` helper for Jinja2 template rendering
- `sse_starlette.sse.EventSourceResponse` already imported/used in routes.py
- No dedicated streaming endpoints yet
- No eval streaming UI

### Eval command

- `ccya/ev/eval.py` `cmd_eval_run()` — runs eval synchronously, produces Markdown report
- No streaming output
- No progress events
- No cancellation support

### Play command

- `ccya/ev/play.py` — runs single turn synchronously
- No streaming output
- No pipeline stage visibility
- No cancellation support

### Pipeline execution

- Engine pipeline executes sequentially: ruling → extraction → narration → state
- No streaming during execution
- No way to observe which stage produced a result
- No way to interrupt mid-execution

### Server infrastructure

- FastAPI server on `localhost:8080`
- `_render()` helper for Jinja2 template rendering in `routes.py`
- `sse_starlette.sse.EventSourceResponse` already used in routes.py for streaming
- No dedicated SSE endpoints yet
- No streaming state management
- No cancellation infrastructure

## Proposed Solution

### Core Changes

#### 1. SSE streaming infrastructure: `ccya/server/streaming.py` (new)

```python
# ccya/server/streaming.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator

router = APIRouter()

# In-memory streaming state: session_id -> {active: bool, scenario: str, turn: int}
_streaming_state: dict[str, dict] = {}

class SSEEvent:
    def __init__(self, event_type: str, data: dict, event_id: str | None = None):
        self.event_type = event_type
        self.data = data
        self.event_id = event_id or str(datetime.now().timestamp())
        self.timestamp = datetime.now().isoformat()
    
    def format(self) -> str:
        lines = [f"id: {self.event_id}", f"event: {self.event_type}", f"data: {json.dumps(self.data)}", ""]
        if self.timestamp:
            lines.insert(3, f"retry: 5000")
        return "\n".join(lines)

async def stream_eval_events(scenario_id: str, session_id: str) -> AsyncGenerator[str, None]:
    """Stream eval events for a scenario."""
    _streaming_state[session_id] = {"active": True, "scenario": scenario_id, "turn": 0}
    
    yield SSEEvent("start", {"scenario_id": scenario_id, "session_id": session_id}).format()
    
    try:
        # Import here to avoid circular imports
        from ccya.ev.eval import run_scenario
        
        # Run the scenario, yielding events
        for turn_result in run_scenario(scenario_id):
            if not _streaming_state.get(session_id, {}).get("active", False):
                yield SSEEvent("cancelled", {"session_id": session_id}).format()
                break
            
            _streaming_state[session_id]["turn"] += 1
            
            # Stream turn start
            yield SSEEvent("turn", {
                "turn": _streaming_state[session_id]["turn"],
                "input": turn_result.input,
            }).format()
            
            # Stream pipeline stages
            for stage_name, stage_result in turn_result.pipeline_stages:
                yield SSEEvent("stage", {
                    "turn": _streaming_state[session_id]["turn"],
                    "stage": stage_name,
                    "status": stage_result.status,
                    "duration_ms": stage_result.duration_ms,
                }).format()
            
            # Stream checker results
            for checker_name, checker_result in turn_result.checker_results:
                yield SSEEvent("checker", {
                    "turn": _streaming_state[session_id]["turn"],
                    "checker": checker_name,
                    "passed": checker_result.passed,
                    "score": checker_result.score,
                    "findings": checker_result.findings,
                }).format()
        
        yield SSEEvent("complete", {
            "scenario_id": scenario_id,
            "turns": _streaming_state[session_id]["turn"],
        }).format()
    
    except Exception as e:
        yield SSEEvent("error", {
            "session_id": session_id,
            "error": str(e),
        }).format()
    finally:
        _streaming_state.pop(session_id, None)

@router.get("/api/eval/stream")
async def stream_eval(scenario_id: str, session_id: str):
    """SSE endpoint for eval streaming."""
    return StreamingResponse(
        stream_eval_events(scenario_id, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@router.post("/api/eval/cancel")
async def cancel_eval(session_id: str):
    """Cancel a running eval streaming session."""
    if session_id in _streaming_state:
        _streaming_state[session_id]["active"] = False
        return {"status": "cancelled", "session_id": session_id}
    return {"status": "not_found", "session_id": session_id}
```

#### 2. Mid-turn pipeline streaming: `ccya/server/routes.py` (update)

Add streaming endpoint for mid-turn pipeline visibility:

```python
# ccya/server/routes.py — new endpoint

@router.post("/api/turn/pipeline")
async def stream_turn_pipeline(turn_input: dict):
    """Stream pipeline stages for a single turn."""
    session_id = str(datetime.now().timestamp())
    
    async def stream_pipeline():
        yield SSEEvent("start", {"turn_input": turn_input}).format()
        
        # Execute pipeline stages sequentially
        for stage_name in ["ruling", "extraction", "narration", "state"]:
            stage_start = time.time()
            
            # Execute stage (call engine pipeline)
            stage_result = await execute_pipeline_stage(stage_name, turn_input)
            
            stage_duration = (time.time() - stage_start) * 1000
            
            yield SSEEvent("stage", {
                "stage": stage_name,
                "status": "complete" if stage_result else "empty",
                "duration_ms": round(stage_duration, 2),
                "output_summary": stage_result.summary if stage_result else None,
            }).format()
        
        yield SSEEvent("complete", {"turn_input": turn_input}).format()
    
    return StreamingResponse(
        stream_pipeline(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

#### 3. Web UI: streaming components

**Eval streaming UI:**
- Progress bar: shows current scenario, current turn, total turns
- Stage indicators: shows each pipeline stage as it completes (green = pass, red = fail, yellow = inconclusive)
- Checker results: shows each checker's pass/fail, score, and findings
- Cancel button: POST to `/api/eval/cancel`
- Report download: when streaming completes, download the Markdown report

**Mid-turn pipeline UI:**
- Pipeline visualization: shows ruling → extraction → narration → state as a horizontal flow
- Each stage lights up as it completes: green (pass), red (fail), yellow (inconclusive)
- Stage details: click on a stage to see its output (ruling text, extracted fields, narration, state changes)
- Timing: shows how long each stage took

#### 4. Streaming event format

```json
// Start event
{
  "event_id": "1698765432.123",
  "event": "start",
  "data": {
    "scenario_id": "ruling-momentum-basics",
    "session_id": "1698765432.123"
  },
  "timestamp": "2024-01-01T12:00:00.123Z"
}

// Turn event
{
  "event_id": "1698765432.456",
  "event": "turn",
  "data": {
    "turn": 1,
    "input": "Kick the door down with all your might"
  },
  "timestamp": "2024-01-01T12:00:00.456Z"
}

// Stage event
{
  "event_id": "1698765432.789",
  "event": "stage",
  "data": {
    "turn": 1,
    "stage": "ruling",
    "status": "complete",
    "duration_ms": 1250.5
  },
  "timestamp": "2024-01-01T12:00:01.234Z"
}

// Checker event
{
  "event_id": "1698765433.012",
  "event": "checker",
  "data": {
    "turn": 1,
    "checker": "momentum_lifecycle",
    "passed": true,
    "score": 1.0,
    "findings": []
  },
  "timestamp": "2024-01-01T12:00:01.567Z"
}

// Complete event
{
  "event_id": "1698765440.123",
  "event": "complete",
  "data": {
    "scenario_id": "ruling-momentum-basics",
    "turns": 8
  },
  "timestamp": "2024-01-01T12:00:40.123Z"
}

// Error event
{
  "event_id": "1698765435.456",
  "event": "error",
  "data": {
    "session_id": "1698765432.123",
    "error": "LLM call failed: connection refused"
  },
  "timestamp": "2024-01-01T12:00:35.456Z"
}
```

### Alternatives Considered and Rejected

1. **WebSockets for streaming.**
   Rejected: WebSockets add connection management, reconnection logic, and message framing complexity. SSE is sufficient for unidirectional streaming (server → client) and has automatic reconnection built in.

2. **Polling instead of streaming.**
   Rejected: Polling (`GET /api/eval/status`) creates unnecessary server load and latency. Streaming is real-time and efficient.

3. **Streaming to CLI instead of web UI.**
   Rejected: The CLI (`ev.py`) already produces output. This design covers the web UI only.

4. **Token-level streaming.**
   Rejected: Streaming the LLM's output token-by-token is out of scope. This design covers eval progress and pipeline stage visibility, not token-level streaming.

5. **Persistent streaming state (database/Redis).**
   Rejected: Streaming sessions are ephemeral. No need to persist streaming events. In-memory state is simpler and avoids database/Redis complexity.

## Failure Modes and Risks

1. **SSE connection drops.** The browser's EventSource API automatically reconnects with exponential backoff. The server should handle reconnection gracefully: if the streaming session is still active, resume from the last event_id. If the session has ended, send a `complete` or `error` event.

2. **Streaming timeout: 5 minutes.** If a streaming session exceeds 5 minutes of inactivity, the server closes the connection. The client should reconnect and resume. This prevents stale connections from consuming server resources.

3. **Streaming cancellation: race condition.** If the client sends a cancel request while the server is processing a turn, the server may complete the turn before checking the `active` flag. This is acceptable: the turn is already executed, and the cancellation takes effect for the next turn.

4. **Streaming state: memory leak.** If the server crashes or the streaming session ends without cleanup, the in-memory state may retain stale entries. Mitigation: periodic cleanup of stale entries (entries older than 10 minutes with no activity).

5. **Streaming: server overload.** If multiple users stream evals simultaneously, the server may become overloaded. Mitigation: limit concurrent streaming sessions to 5. Additional sessions are queued or rejected with a 503 error.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| No streaming infrastructure | (none) | N/A — no streaming exists to remove |
| No SSE endpoints | (none) | N/A — no SSE endpoints exist to remove |

## What Is Unchanged

- `ccya/server/routes.py` — existing routes unchanged (new streaming endpoints added)
- `ccya/ev/eval.py` — eval command logic unchanged (streaming wraps existing logic)
- `ccya/ev/play.py` — play command logic unchanged
- `ccya/engine/turn.py` — turn pipeline execution unchanged (streaming wraps existing execution)
- Web UI templates (`ccya/templates/`) — new streaming components added, existing templates unchanged

## New Model Shapes

```python
# ccya/server/streaming.py — new module

class SSEEvent:
    event_id: str
    event_type: str
    data: dict
    timestamp: str
    
    def format(self) -> str:
        """Format as SSE event string."""

# Streaming state: in-memory dict
_streaming_state: dict[str, dict] = {
    "session_id": {
        "active": bool,
        "scenario": str,
        "turn": int,
    }
}

# Streaming event types:
# - start: streaming session started
# - turn: new turn started
# - stage: pipeline stage completed
# - checker: checker result emitted
# - complete: streaming session completed
# - error: streaming session errored
# - cancelled: streaming session cancelled
```

## Context for Implementing LLMs

- `ccya/server/streaming.py` — new module for SSE streaming infrastructure. Creates `SSEEvent` class, streaming endpoints (`/api/eval/stream`, `/api/eval/cancel`), and streaming state management.
- `ccya/server/routes.py` — add `/api/turn/pipeline` endpoint for mid-turn pipeline streaming.
- `ccya/ev/eval.py` — update `run_scenario()` to yield streaming events (turn, stage, checker) instead of producing a single Markdown report.
- `ccya/engine/turn.py` — update turn pipeline execution to yield streaming events for each stage (ruling, extraction, narration, state).
- Web UI templates (`ccya/templates/`) — add streaming components: progress bar, stage indicators, checker results, cancel button, pipeline visualization.
- No changes to LLM infrastructure (`ccya/ev/checkers/_llm.py`). Streaming wraps existing LLM checker execution.
