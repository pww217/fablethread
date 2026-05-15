## How the Arc System Wires Into the Engine

### 1. What exists now (relevant baselines)

The current pipeline already has the right shape for most of this. The narrator receives `state` in full, meaning `state.arc` will automatically flow through once it exists on `GameState` — `_narrate_messages()` passes `state` as a dict to `narrate_user.j2` directly, so any new top-level field appears in the template context with zero extra plumbing in `narrate.py` itself. The key additions are:

- Arc fields need to be **explicitly named and rendered** in `narrate_system.j2` and `narrate_user.j2` — they don't auto-appear in the system prompt
- Step 2c's `extraction.py` needs its quest inputs/outputs swapped for thread signal inputs/outputs
- A new Python tail (`arc.py`) runs after `apply_delta()` in `turn.py`

***

### 2. Seed time — where the arc is born

The seed LLM call (one call, same as today) generates a `SeedEnvelope`. Today that envelope includes `seed_state.quests`. After this plan, instead of quests, it generates `seed_state.arc: CampaignArc`.

**What the seed LLM produces for the arc:**

```
arc:
  visible_goal: "Find what happened to your sister, Lenne."
  thematic_question: "How much of who you were do you spend to find who was taken?"
  phase: setup
  hidden_truths:
    - "Lenne is alive, working as a healer in Valdrest under a false name."
    - "The caravan attack wasn't random — someone wanted your family scattered."
  active_threads:
    - id: "caravan_survivor"
      summary: >
        One survivor of the original caravan may still be in the city. A dockworker
        named Oss was seen in the lower quarters three days ago. He disappeared before
        the militia arrived. Whether he's hiding, fled, or was silenced is unknown.
      tags: ["lead", "survivor", "caravan", "city"]
      urgency: normal
  latent_threads:
    - id: "false_name_records"
      summary: >
        Church registries from the fever years contain alias records — names adopted
        by displaced persons during quarantine. If Lenne was moved east under assumed
        identity, a registry clerk with the right access could trace the thread. The
        records exist but accessing them carries political cost.
      tags: ["lead", "records", "church", "identity"]
      urgency: normal
      unlock_if: "player has pursued a records or paper trail lead at least once"
      promotes: []
    - id: "the_informant"
      summary: >
        Someone has been asking questions about your family before you started asking
        yours. The trail is cold but not gone — a fence in the market district got
        nervous when your name came up. Something or someone is running parallel.
      tags: ["threat", "shadow", "mystery", "family"]
      urgency: normal
      unlock_if: "player has been in the city for several turns"
      promotes: ["false_name_records"]
  pc_drive: "You promised your father you'd find her."
```

**Hidden truths** are never passed to the narrator. They live in Python state only. They are not extracted, not updated, and not shown to the player. They are the structural spine the human designer put there at seed time — the revealed truth that the whole arc leads toward. The narrator has no idea these exist. They surface only through thread promotions that gradually approach the truth (e.g. `false_name_records` eventually leads to `lenne_found`).

***

### 3. Narrator (Step 1) — what it sees and what it's told to do with it

**What flows in:**

From `narrate_user.j2`, the template already has access to the full `state` dict. The arc context is rendered as a dedicated block — not the raw arc object, but a pre-rendered summary built in `_narrate_messages()`:

```python
current_arc_ctx = {
    "visible_goal": arc.visible_goal,
    "thematic_question": arc.thematic_question,
    "phase": arc.phase.value,
    "active_threads": [
        {"summary": t.summary, "urgency": t.urgency, "tags": t.tags}
        for t in arc.active_threads
    ],
    "pc_drive": state["pc"].get("drive"),
}
```

This replaces the `active_quests` block entirely. The `active_threads` block contains the **full thread summary** (the 2–4 sentence paragraph), not just a title. That's the whole point — threads give the narrator a situation with texture, not a task to announce.

**What `narrate_system.j2` tells the narrator:**

```
## Campaign Arc

The player's visible goal: {{ current_arc.visible_goal }}
Thematic question (shapes the emotional register of this scene — never state it directly):
  {{ current_arc.thematic_question }}
Arc phase: {{ current_arc.phase }}

{% if current_arc.active_threads %}
## Active narrative threads (situations in play)

These are situations alive in the world right now. You do not announce them as objectives
or missions. You weave them into the scene through environment, NPC behavior, overheard
dialogue, atmosphere, or timing. The player may interact with a thread or ignore it. If
they deviate from all threads, let the scene breathe — but keep at least one thread subtly
present as a background pressure or detail.

{% for thread in current_arc.active_threads %}
[{{ thread.urgency | upper }}] {{ thread.summary }}

{% endfor %}
{% endif %}

{% if current_arc.pc_drive %}
The player character's personal drive: {{ current_arc.pc_drive }}
This shapes their emotional interior — grief, determination, guilt — not their stated
actions. Use it to color inner narration, dialogue subtext, or reactive detail.
{% endif %}
```

**Key behavioral constraint**: The narrator is told the thread is a *situation*, not a *task*. A thread about a dockworker named Oss doesn't mean "find Oss this turn." It means the dockworker is in the world and could surface in a dozen ways — a rumor, a face in a crowd, a note slipped under a door. The urgency level (`normal` / `building` / `immediate`) tells the narrator how hard to push it into the foreground.

**NPC motivation/fear/leverage** flows through the existing `known_characters` / `compendium_bios` path into `narrate_user.j2`. `_known_characters_for_extract()` already builds a row list from `state.compendium.npcs`. That function needs one change: include `motivation`, `fear`, and `leverage` in the rows it emits, and the template renders them inline under each NPC entry. No other wiring needed.

***

### 4. Step 2c (Progress Extract) — what it extracts and how

**What goes in** (replacing quest inputs):

```python
active_threads_ctx = [
    {"id": t.id, "summary": t.summary[:200]}  # truncated — extractor doesn't need full prose
    for t in arc.active_threads
]
```

Inputs removed: `active_quests`, `quest_ages`, `quest_threshold_directive`.
Inputs added: `active_threads_ctx` (compact).

**What comes out** (replacing `quest_updates`):

```python
class ThreadSignal(BaseModel):
    id: str
    signal: ThreadSignalType  # advanced | blocked | failed | ignored

class ProgressExtractResult(BaseModel):
    # ... existing fields unchanged ...
    thread_signals: list[ThreadSignal] = []
    player_drift_signals: list[str] = []    # max 3 short phrases
    candidate_opportunity: str | None = None
    # quest_updates: REMOVED
```

**What `extract_progress_system.j2` tells the extractor:**

```
## thread_signals
Review the active threads listed below. For each thread that was meaningfully touched
by the narrative this turn, emit exactly one signal:

- "advanced": the narrative moved this thread clearly forward — a lead was followed,
  a relevant person was encountered, meaningful information was gained
- "blocked": an obstacle directly impeding this thread appeared in the narrative
- "failed": the thread was definitively closed with a negative outcome
- "ignored": the thread was not touched this turn

Only emit signals for threads directly relevant to this turn's events.
Do not emit a signal if the thread was only tangentially present.
Do not emit multiple signals for the same thread.
Emit nothing if no threads were touched.

## player_drift_signals
If the player's action suggests a new interest or direction not covered by any active thread,
emit up to 3 short descriptive phrases. Examples:
  "pursuing black market contacts"
  "suspicious of the militia captain"
  "focused on leaving the city quickly"
Leave empty if the player engaged with active threads normally.

## candidate_opportunity
If the narrative introduced a new hook — a person, object, place, or situation with
future narrative potential not covered by existing threads — describe it in one sentence.
Leave null otherwise.
```

**Why this is simpler than quests:** The extractor only needs to match thread IDs it already knows (from the input context) and emit one of four enum values. No index-based objective tracking, no deduplication, no new-quest creation. The LLM cannot invent new thread IDs — it can only signal on the IDs it was given, plus contribute `candidate_opportunity` as a free-text seed for Python to optionally store.

***

### 5. Python arc director (`arc.py`) — what runs after extraction

This runs in `turn.py` immediately after `apply_delta()`, before the final persist:

```python
# In turn.py, post-apply tail:
if state.arc and progress_result:
    state.arc = tick_arc(
        arc=state.arc,
        signals=progress_result.thread_signals,
        drift=progress_result.player_drift_signals,
        candidate=progress_result.candidate_opportunity,
        momentum=state.meta.momentum,
        turn_no=state.meta.turn,
    )
```

**What `tick_arc()` does, step by step:**

1. **Apply signals to threads.** For each `ThreadSignal`, find the matching `ArcThread` by ID and increment its `progress` counter (`advanced` → +1, `blocked` → no change, `failed` → mark `ThreadState.FAILED`, `ignored` → no change). Write `last_offered_turn = current_turn` on any thread that received a non-ignored signal.

2. **Thread completion.** If a thread's `progress >= 2`, mark it `ThreadState.COMPLETE`. Move it from `active_threads` to `completed_threads`. For each ID in `thread.promotes`, find the matching latent thread and promote it to `active`.

3. **Thread expiry.** For each active thread where `last_offered_turn` is set and `current_turn - last_offered_turn >= 8`, and all its signals were `ignored`: mark `ThreadState.EXPIRED`. Move to `completed_threads` (expired). Trigger salience-based latent promotion.

4. **Salience scoring for promotion.** When a promotion slot opens (cap is 3 active), score all `latent` threads:
   - Tag overlap with the last 3 turns' `player_drift_signals` (accumulated on arc: `arc.recent_drift_tags`) → +2 per overlap
   - Tag overlap with currently active thread tags → +1 per overlap
   - Momentum bias: if `momentum >= 2`, prefer tags `["cost", "deadline", "complication", "betrayal_risk"]`; if `momentum <= -1`, prefer tags `["aid", "breathing_room", "ally", "resource"]`
   - Not recently offered (`last_offered_turn is None or current_turn - last_offered_turn > 5`) → +1
   
   Promote the highest-scoring latent thread.

5. **Arc engagement.** If any `player_drift_signals` overlap with any active thread tag: `arc.arc_engagement = min(3, arc.arc_engagement + 1)`. If all drift signals are entirely unrelated: `arc.arc_engagement = max(-3, arc.arc_engagement - 1)`. This metric isn't used yet but will bias salience scoring in the future.

6. **Store `candidate_opportunity`.** If `progress_result.candidate_opportunity` is not None, create a new `ArcThread` with `state=LATENT`, `progress=0`, `urgency=normal`, `unlock_if=None`, auto-generated ID (`slug(candidate[:40])`), and a one-sentence summary equal to the candidate string. Append to `arc.latent_threads`. This lets LLM-noticed hooks organically enter the thread pool without Python having to hardcode them.

7. **PC expressed stances.** After arc tick, run stance keyword scan on `user_input`:
   ```python
   STANCE_KEYWORDS = {
       "compassionate": ["help", "heal", "protect", "comfort", "save", "trust"],
       "ruthless":      ["threaten", "kill", "steal", "betray", "abandon", "use"],
       "defiant":       ["refuse", "resist", "defy", "challenge", "reject"],
       "cautious":      ["hide", "wait", "observe", "avoid", "sneak", "plan"],
   }
   ```
   Increment the matching stance counter in `state.pc.expressed_stances`. These flow to the narrator as flavor via `state.pc` already — no extra wiring needed, since `narrate_user.j2` already renders `pc`.

***

### 6. What the UI sees (for your design purposes)

The UI-relevant state after this plan, per turn:

**From `state.arc` (persistent, written by arc director):**
```yaml
arc:
  visible_goal: "Find what happened to your sister, Lenne."
  thematic_question: "..."   # never shown to player
  phase: pursuit
  active_threads:
    - id: caravan_survivor
      summary: "..."
      urgency: building
      progress: 1
      state: active
    - id: false_name_records
      summary: "..."
      urgency: normal
      progress: 0
      state: active
  latent_threads: [...]       # never shown to player
  completed_threads: [...]    # can be shown as history
  hidden_truths: [...]        # never shown
  arc_engagement: 1
```

**From `state.pc` (persistent):**
```yaml
pc:
  drive: "You promised your father you'd find her."
  expressed_stances:
    compassionate: 3
    cautious: 5
    defiant: 1
```

**From `ProgressExtractResult` in `events.jsonl` (per-turn, for turn viewer):**
```json
{
  "thread_signals": [{"id": "caravan_survivor", "signal": "advanced"}],
  "player_drift_signals": ["interested in the harbor district"],
  "candidate_opportunity": "A letter in the innkeeper's desk was addressed to a name matching Lenne's description."
}
```

For **UI display**, the player-facing elements are:
- `arc.visible_goal` — always shown in a persistent header/sidebar panel
- `arc.active_threads[*].summary` — shown as a "leads" panel (optional, you could hide these to preserve mystery, or show as "things you're tracking")
- `arc.phase` — can map to a visual phase indicator
- `pc.drive` — shown in character sheet
- `pc.expressed_stances` — optional flavor display ("you've acted cautiously 5 times")
- `arc.completed_threads` — optional log of resolved threads

The player **never sees**: `hidden_truths`, `latent_threads`, `thematic_question`, or thread `tags`.