# PROMPTING.md — ccya prompt-engineering rules

Rules of the road for every `.j2` prompt and every Python wrapper that builds messages for an LLM call. Apply these before adding, restructuring, or trimming a prompt. Last revision pinned to the prompt audit (May 2026).

PRIMARY DIRECTIVE: terse, model-agnostic, accuracy first, latency a close second.

---

## Core skeleton (every prompt)

```
System: [stable role / behavior / schema / static rules]
User:   [task] [context slice] [constraints] [output reminder]
```

Durable instructions live in `*_system.j2`. The actual job + per-turn state lives in `*_user.j2`. This split applies whether the call is rules, narrate, scene-extract, state-extract, progress-extract, or generate-seed.

---

## The twelve rules

### 1. System prompt = byte-stable across turns
Per-turn variability (rules outcome, scope, dynamic guidance, items_gained, quest threshold, faker name pool, last-turn-failed) MUST live in the user prompt. The system prompt should hash to the same bytes whether it's turn 1 or turn 50. Verified with `tests/test_prompt_cache_stability.py`.

Why it matters even though stock `mlx_lm.server` is single-slot today: it's the prerequisite for the per-stream `mlx_lm.cache_prompt` pinning follow-up (see `TODO.md`), it makes regression tests deterministic, and it forces a clean separation between "rules of the game" and "this turn's situation".

### 2. Skip-render — but say "absence ≠ removal"
Don't render empty sections (no `## Recent Events\nNone recorded yet.`, no `__HIDDEN__` sentinels). To prevent the model from inferring "section missing means state was deleted", every extract system prompt carries one stable line:

> Sections not shown still exist in the live game state; absence is not removal. Only emit removals you can justify from the narration.

User-prompt sections render only when they have content AND fall inside `scope.active_domains`.

### 3. Engine owns stateful and numerated reasoning
If something can be computed in Python — counts, thresholds, dedup, validation, TTL ticks, dice resolution, ammunition math — do it in code, not in a jinja `{% if x | length > 3 %}` ladder. Push the model toward fiction; let code own arithmetic.

Examples already applied: dice resolution in `rules.py`, condition TTL in `engine.py`, quest auto-completion in `state.py`, scene NPC dedup in `engine.py`, quest-threshold sentence chosen in `engine.py`.

### 4. Label inputs with output-field nouns
The user-prompt section feeding a `present_npcs` output field is titled `present_npcs` (not "Scene Characters"). The cheap noun-reinforcement reliably improves Gemma 4 field-name discipline.

### 5. One delimiter pair for untrusted long content
Use `=== NARRATION ===` / `=== END NARRATION ===` and `=== PLAYER INPUT ===` / `=== END PLAYER INPUT ===` everywhere. No `## CURRENT TURN NARRATION`, no bare unwrapped narration, no inconsistent `## Player's current input`.

### 6. Imperatives over role narration
"Extract scene state from narration. JSON only." beats "You are the scene extractor. Your only job is to extract scene cosmetics, location state, NPC presence…". Each preamble is one short verb-led line.

### 7. Schema near the imperative
Place the output schema directly under the verb. The model anchors on the most-recent schema mention. Don't bury it after 60 lines of guidance.

### 8. One home per directive
If a rule lives in `narrate_system.j2`, it does NOT also live in `narrate_user.j2`. No restating. If you're tempted to repeat for emphasis, the original phrasing was probably weak — fix it once.

### 9. Cross-stream surface is minimum-viable
Stream B receives only what stream A produced that B genuinely needs.
- Scene → State: `location_id`, `location_changed`, `present_npcs[id+name]` only.
- Scene+State → Progress: present NPC names + items gained (names) / items lost (ids) only.
No full-state re-sends, ever.

### 10. `_reasoning` only as a true scratchpad
A `_reasoning` JSON field is post-commit narration unless it is the **first** key in the schema. We currently do not use it (see audit) — the model emitted it last, which made it useless. If reintroduced, position it first and cap it at ≤25 words.

For real chain-of-thought, the right primitive is the model's native thinking mode (`<start_of_thought>` for Gemma, `<think>` for Qwen3, etc.). The current `apply_thinking` / `strip_thinking` helpers are Qwen3-specific and harmless while disabled — see `TODO.md` for the model-agnostic rebuild before re-enabling.

### 11. Faker provides names
`engine.names.generate_name_pool` / `generate_npc_names` already inject genre-and-locale-appropriate candidates from Faker. Don't lecture about generic Anglo names. Ship one short directive per prompt:

> Pick from the provided pool; favor names that fit the genre, role, and culture. Mix linguistic origins.

That's it. No "Marcus Cole / Clara Miller / Elias Thorne" anti-list, no triple repetition across narrate / generate_seed_system / generate_seed_user.

### 12. No commented-out prompt blocks
Same rule as `AGENTS.md` for code: if it's deferred, track it in `TODO.md` or `plans/`; don't leave it sitting in a `{# ... #}` block in the template. Same goes for legacy alternatives — delete in the PR that supersedes them.

---

## When in doubt: the test

Before merging a prompt change, render the system prompt with two distinct turn states and `diff` the output. Identical bytes? Good — system stayed stable. Different bytes? You leaked per-turn state into the system; move it to the user prompt.

---

## Where the wins actually come from

Latency on these calls is dominated by **prefill cost**, which scales linearly with input token count. Reducing system prompt size by 30% reduces prefill time by ~30%. That win lands the same on single-slot caching, multi-slot prefix caching, vLLM, mlx_lm, anything.

Cache stability (rule 1) is **architectural insurance**: it pays off the day mlx_lm gains prefix caching, or the day we swap to a multi-slot runtime. Until then, it's discipline that costs nothing and protects the upgrade path.

If you're tempted to add tokens, ask: does this content change the model's output? If you can't show it does, cut it.