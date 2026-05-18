# PacingContext

All pacing signals are collapsed into one Python-computed struct (`PacingContext`) passed to both the Narrator and Progress Extractor. This replaces six independent fields (`narration_directive`, `deescalate`, `narrative_velocity`, `pending_beat`, `beat_disposition` output, `quest_threshold_directive`). The narrator receives only `directive` and `beat_hint`; Progress receives the full struct.

## Struct definition

```
PacingContext:
  directive: str           # "" | "Breathe" | "Pressure" | "MoveOn" | "Escalate"
  beat_hint: str | None    # suggested gm_beat type, or None
  beat_locked: bool        # True: floor relief fired — Progress MUST emit breathing_room beat and gate is force-closed
  gate: str                # "block_add" | "block_escalate" | "allow" (controls thread_add)
  summary: str             # human-readable log string, never sent to LLM
```

`beat_locked: True` subsumes the old `_check_floor_relief()` side-channel — floor relief logic is computed inside `_compute_pacing_context()`. The `gate` field prevents Progress from adding new threads during de-escalation windows.

## Computation

`_compute_pacing_context()` in `engine/turn.py` consolidates all pacing computation (replacing the former scattered functions: `_compute_narration_directive`, `_compute_narrative_velocity`, `_check_floor_relief`). It takes inputs (`momentum`, `consecutive_floor_turns`, `arc.threads[] scope=scene urgency counts`, combat age, location age) and returns a single struct with directive derived from the same priority stack:

```mermaid
flowchart TD
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef decision fill:#3b0764,color:#e9d5ff,stroke:#7c3aed
    classDef output fill:#1e3a5f,color:#bfdbfe,stroke:#3b82f6

    M["momentum scalar"]:::pyNode
    T["arc.threads[] scope=scene<br>(urgency counts)"]:::pyNode
    CA["combat_age"]:::pyNode

    M --> D1{"momentum at floor<br>(consecutive_floor_turns threshold)"}:::decision
    D1 -- yes --> BL["beat_locked = True<br>→ directive='Breathe'"]:::output
    D1 -- no --> D2{"velocity < -0.3<br>(deescalation)"}:::decision
    D2 -- yes --> B1["directive='Breathe'"]:::output
    D2 -- no --> D3{"≥ 3 immediate<br>threads?"}:::decision
    D3 -- yes --> B2["directive='Escalate'"]:::output
    D3 -- no --> D4{"combat_age ≥ 4<br>(combat stalling)"}:::decision
    D4 -- yes --> B3["directive='Pressure'"]:::output
    D4 -- no --> D5{"≥ 1 non-immediate<br>thread?"}:::decision
    D5 -- yes --> B4["directive='Pressure'"]:::output
    D5 -- no --> D6{"threat_age ≥ pressure_at"}:::decision
    D6 -- yes --> B5["directive='Pressure'"]:::output
    D6 -- no --> B7["directive='' (empty)"]:::output

    BL --> G1["gate = 'block_add'<br>beat_hint = 'breathing_room'"]:::pyNode
    B3 --> S3{"≥ 1 building thread"}:::decision
    S3 -- yes --> SEC3["secondary append<br>(location imperative)"]:::output

    FINAL["PacingContext<br>directive · beat_hint · beat_locked · gate"]:::output
```

Priority order (highest to lowest): **Breathe > Escalate > Pressure > (empty)**. The `beat_locked` flag takes precedence — when floor relief fires, directive is forced to "Breathe" and gate is force-closed.

## Wiring: how PacingContext reaches the pipelines

```mermaid
flowchart LR
    classDef pyNode fill:#1f2937,color:#9ca3af,stroke:#4b5563
    classDef prompt fill:#0f172a,color:#7dd3fc,stroke:#1e40af
    classDef extractor fill:#500724,color:#fbcfe8,stroke:#ec4899

    TURN["engine/turn.py<br>_compute_pacing_context()"]:::pyNode
    PIPELINE["_run_extraction_pipeline()<br>pass PacingContext struct"]:::pyNode
    EXTRACT_FN["_extract_progress_messages()<br>extraction.py"]:::pyNode
    USER_TMPL["extract_progress_user.j2<br>pacing_context.directive + gate"]:::prompt
    SYS_TMPL["extract_progress_system.j2<br>PacingContext guidance"]:::prompt
    NARRATE_TMPL["narrate_user.j2<br>pacing_context.directive + beat_hint"]:::prompt

    TURN --> PIPELINE --> EXTRACT_FN --> USER_TMPL
    USER_TMPL --> SYS_TMPL --> EXTRACTOR["Progress Extractor LLM"]:::extractor
    TURN -. "also passed to" .-> NARRATE_TMPL
```

1. **Computed** once in `run_turn()` via `_compute_pacing_context()`.
2. **Passed through** `_run_extraction_pipeline()` → both `_narrate_messages()` and `_extract_progress_messages()`.
3. **Narrator template** (`narrate_user.j2`) renders only `directive` (tone/direction) and `beat_hint` when present. No Jinja2 directive computation remains — all directives computed by Python.
4. **Progress template** (`extract_progress_system.j2` + `user.j2`) receives the full struct; guidance maps each directive to appropriate thread/beat actions:

| Directive | Thread action | Beat hint | Gate |
|-----------|--------------|-----------|------|
| **"Breathe"** (floor relief) | Do NOT add new threads. Allow existing scene threads to persist without escalation. | `breathing_room` | `block_add` + force-closed |
| **"Escalate"** | Add thread if gate allows; advance active threads proactively. | `pressure` / `escalation` | Depends on momentum |
| **"Pressure"** | Advance relevant scene/arc threads. Add new thread only if gate permits. | `complication` / `pressure` | Varies by context |
| **"" (empty)** | No action required beyond normal aging of silent threads. | None | Allow |
