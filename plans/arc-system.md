# Arc System

## Status
`open`

## Context
Broad scope, needs clarification from user before proceeding.

## Issue
The arc/thread system has accumulated several rough edges: unused fields, poorly calibrated objective durations, and thematic question / goal context leaking into narration prompts where they don't belong.

## Proposed Work

### 7a. Remove unused arc fields
- `promotes: list[str]` on CampaignArc (models.py:46) — not used much anymore
- `unlocked_if` / `unlock_if` on ArcThread (models.py:45) — legacy field, check if still referenced

### 7b. Arc objectives too short/few turns
Current arc objectives resolve in too few turns to be readable/meaningful. Increase minimum turn count for objective completion or add evolution mechanics so completed objectives spawn new ones rather than ending the arc entirely. The objective should be "largely [unspecified — needs clarification from user]."

### 7c. Thematic question + goal context
- Remove `thematic_question` from user-facing prompts (keep it in CampaignArc model for now)
- Keep `goal_context` but move to UI-only display, not fed into narration prompts
- Remove `pc_drive` from prompts (likely remove entirely if unused)

## Files
- `ccya/models.py` (CampaignArc, ArcThread)
- `ccya/engine/turn.py` (_apply_thread_resolutions)
- Prompt templates
