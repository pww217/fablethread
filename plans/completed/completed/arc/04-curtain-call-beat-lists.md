# Convergence Scoring — Phase 4: Curtain Call + Beat List Updates

## Purpose

Update the storytell system prompt with Curtain Call tiers, update `derive_allowed_beat_types()` Scene Imperative list (`twist`→`setback`, add `breathing_room` to override only), and update `_pacing.py` Scene Imperative entry. Phase 3 must be complete (CLIMAX phase name exists in state, phase machine transitions finalized).

## Firm decisions

- Scene Imperative allowed list: `[revelation, hazard, callback, opportunity, setback]` + `breathing_room` (override only).
- `twist` excluded from Scene Imperative — was the primary source of infinite escalation.
- `breathing_room` added to Scene Imperative override list only, NOT to `BEAT_PHASE_MAP["CLIMAX"]` base list.
- Curtain Call tier 1 (turn 1 of CLIMAX): `curtain_call: "active"` in user prompt. System prompt: "CLIMAX phase — you MUST resolve the active thread this scene. Include at least one `thread_resolve` entry in your output."
- Curtain Call tier 2 (turn >= `climax_turn_limit - 1`): `curtain_call: "forced"` in user prompt. System prompt: "This is the final climactic turn. This thread MUST resolve now, for better or worse. The engine will force a transition if you don't."
- Hard cutoff at `climax_turn_limit` unchanged (phase machine already handles this).
- `breathing_room` NOT added to `BEAT_PHASE_MAP["CLIMAX"]` — base CLIMAX list stays `["pressure", "escalation", "complication"]`.

## Status

`completed`

## Dependencies

- Phase 3 complete (CLIMAX state keys and phase machine working).

## Implementation — Phase 4: Curtain Call + Beat List Updates

### Context files to load

- `ccya/prompts/storytell_system.j2` — full file (112 lines)
- `ccya/engine/_pacing.py` — `derive_allowed_beat_types()` (58-89), BEAT_BUCKETS (15-19), BEAT_PHASE_MAP (21-27)
- `ccya/engine/extraction.py` — `_storytell_messages()` (310-389), extract storytelling context and how pacing_context/scene_phase/climax_turn_count reach the prompt

### Detailed steps

#### Step 4.1 — Update Scene Imperative allowed list in derive_allowed_beat_types

**File:** `ccya/engine/_pacing.py`

**What:** Change line 75:
```python
# Old:
if directive == "Scene Imperative":
    return BEAT_BUCKETS["situation"] + ["opportunity"]

# New:
if directive == "Scene Imperative":
    return ["revelation", "hazard", "callback", "opportunity", "setback", "breathing_room"]
```

`twist` removed, `setback` added, `breathing_room` added. Reason: `twist` was the primary source of infinite escalation; `setback` and `breathing_room` provide resolution-compatible pressure and relief.

**Why:** Scene Imperative fires when a scene is stale — the beat list should support resolution, not escalation.

**Validation:** `.venv/bin/python -c "from ccya.engine._pacing import derive_allowed_beat_types; beats = derive_allowed_beat_types('CLIMAX', directive='Scene Imperative'); assert 'twist' not in beats; assert 'setback' in beats; assert 'breathing_room' in beats"`

#### Step 4.2 — Update storytell_system.j2 Scene Imperative beat list

**File:** `ccya/prompts/storytell_system.j2`

**What:** Change line 71:
```diff
-- **Scene Imperative** — only: `revelation`, `twist`, `hazard`, `callback`, `opportunity`. **NEVER** `pressure`, `complication`, `escalation`.
++ **Scene Imperative** — only: `revelation`, `hazard`, `callback`, `opportunity`, `setback`, `breathing_room`. **NEVER** `pressure`, `complication`, `escalation`, `twist`.
```

**Why:** Consistent with `derive_allowed_beat_types()`.

**Validation:** `grep 'Scene Imperative' ccya/prompts/storytell_system.j2` — verify text.

#### Step 4.3 — Add Curtain Call guidance to storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2`

**What:** Add a new section below "## Beat types" (after line 65) or after "## Outcome summary" (after line 97) — whichever reads naturally. Recommended placement: after the "Beat types" section but before "Outcome summary":

```
## Curtain Call — CLIMAX phase

When `curtain_call` is `"active"` (turn 1 of CLIMAX): you MUST resolve the active thread this scene. Include at least one `thread_resolve` entry in your output. This turn sets the stakes — the next turns drive toward conclusion.

When `curtain_call` is `"forced"` (final climactic turn before hard cutoff): This thread MUST resolve now, for better or worse. The engine will force a transition if you don't. Prefer decisive resolution.
```

**Why:** Two-tier soft close gives the LLM guidance without mechanical force.

**Validation:** Check rendered prompt for correct `curtain_call` template variable.

#### Step 4.4 — Pass Curtain Call signal to storytell prompt

**File:** `ccya/engine/extraction.py` — `_storytell_messages()` (lines 310-389)

**What:** Add `curtain_call` context variable to user prompt when phase is CLIMAX:
- If `climax_turn_count == 1`: `"curtain_call": "active"`
- If `climax_turn_count >= config.climax_turn_limit - 1`: `"curtain_call": "forced"`
- Otherwise: omit or `"curtain_call": ""`

```python
curtain_call = ""
if scene_phase == "CLIMAX":
    if climax_turn_count >= climax_turn_limit - 1:
        curtain_call = "forced"
    elif climax_turn_count == 1:
        curtain_call = "active"
```

Note: `"forced"` check first so it wins when `climax_turn_limit <= 2` (turn 1 is both first and final). For default limit=4: turn 1→active, turn 2→none, turn 3→forced, turn 4→forced.

Pass `curtain_call` in the user context dict for `storytell_user.j2`.

Also pass to the narrate prompt for the "forced" tier:
- In `ccya/engine/narrate.py`: add `curtain_call: str = ""` keyword parameter to `_narrate_messages()`.
- In `ccya/engine/turn.py` line 822 call to `_narrate_messages()`: pass `curtain_call=curtain_call`.
- In `ccya/prompts/narrate_user.j2`: add the same `{{ curtain_call }}` rendering as `storytell_user.j2` (Step 4.5).

**Why:** The storytell prompt renders `curtain_call` in the Curtain Call section. The narrate prompt needs the "forced" tier for scene transition narration.

**Validation:** After running a turn in CLIMAX, check both logged prompts for the `curtain_call` field.

#### Step 4.5 — Add curtain_call to storytell_user.j2

**File:** `ccya/prompts/storytell_user.j2`

**What:** Add rendering of the curtain_call signal, if present. Below the "## Scene phase" line (line 31):
```
{% if curtain_call and curtain_call != "" %}
## Curtain Call: {{ curtain_call | upper }}
{% endif %}
```

**Why:** This is how the LLM receives the Curtain Call tier information.

**Validation:** Rendered prompt should show `## Curtain Call: ACTIVE` or `## Curtain Call: FORCED` when applicable.

### Tests to write or update

No tests exist. Final validation: run `make check`. Then run an EV playtest with `--llm --turns 10` and verify in events.jsonl that CLIMAX phase shows Curtain Call tiers in rendered prompts.
