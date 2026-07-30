# Plan: I-42 — Pending Names in NPC Roster

## Design Reference

- Discussion with user (no formal design doc — approach decided in conversation)
- Ticket: `roadmap/improvements/narration-name-pool-directive.md`

## Problem Statement

The LLM ignores the name pool directive in the narration prompt. Despite explicit "MUST use these names" directives in both system and user prompts, the LLM generates generic Anglo names (Elias Thorne, Silas Vance, Mark Watkins) from its training distribution instead of using pool names (Giacinto Gotti, Logan Hicks, Brittany Cole). Across 3 test runs (37 NPCs total), zero pool names were used. The LLM reliably follows the NPC roster for naming — it uses roster names for existing NPCs without fail. The fix: present pool names AS roster entries with a new `pending` presence, leveraging the LLM's existing roster-following behavior instead of trying to override its training distribution with directives.

## Firm decisions

1. Pending names appear in the narrator's NPC roster with `presence: "pending"`, not in a separate "Name Pool" section
2. Pending entries are ephemeral — generated fresh each turn from the Faker pool, never stored in state/compendium
3. Pending entries are appended to the roster AFTER the present-NPC filter, so they appear alongside real present NPCs
4. The scene extractor never sees pending entries — they're not in the compendium, so `build_npc_roster()` on the compendium excludes them naturally
5. The old `npc_name_pool` template field and its rendering sections are removed from both narrate_user.j2 and narrate_system.j2
6. 3 male + 3 female pending entries per turn (matches current pool size)

## Scope

- **Phase 01:** Build pending roster entries from the name pool, inject into narrator roster
- **Phase 02:** Update narrator prompt directives — replace naming/forbidden/pool sections with [PENDING] explanation
- **Phase 03:** Clean up context boundaries and ev support

## Status

`scoping`

---

## Phase 01: Inject pending names into narrator roster

### Depends on

None

### Context files to load

- `ccya/engine/narrate.py:155-255` — `_narrate_setup()`: generates name pool (line 166-171), builds present-only roster (line 251), passes both to `_narrate_messages()`
- `ccya/engine/npc_roster.py:101-175` — `build_npc_roster()`: builds sorted roster dicts from compendium; output dict shape includes id, name, title, bio, disposition, presence, motivation, fear, leverage, tie, notes, last_presence_turn, last_seen_location, departed_reason, color
- `ccya/engine/names.py:148-170` — `generate_npc_names_split()`: returns `{"male": [...], "female": [...]}`

### What changes

Add a new function `build_pending_roster_entries()` to `ccya/engine/npc_roster.py` that converts a name pool dict into roster-shaped dicts with `presence="pending"`. Call it from `_narrate_setup()` in narrate.py, appending the result to the present-only roster before passing to `_narrate_messages()`.

### Where to change

**`ccya/engine/npc_roster.py`** — add new function after `build_npc_roster()` (after line 175):

```python
def build_pending_roster_entries(
    pool: dict[str, list[str]],
    *,
    turn_no: int = 0,
) -> list[dict[str, Any]]:
    """Build roster-shaped entries from a name pool with presence='pending'.

    Each entry matches the dict shape from build_npc_roster() but with all
    optional fields set to None and presence='pending'. IDs are derived from
    the name (snake_case). Colors are generated via generate_npc_color().
    """
```

Field values per entry:
- `id`: snake_case of the full name (e.g., "giacinto_gotti")
- `name`: the full name from the pool
- `title`: None
- `bio`: None
- `disposition`: None
- `presence`: "pending"
- `motivation`: None
- `fear`: None
- `leverage`: None
- `tie`: None
- `notes`: None
- `last_presence_turn`: None
- `last_seen_location`: None
- `departed_reason`: None
- `color`: `generate_npc_color(id)` (for consistency, not displayed)

Iterate over `pool["male"]` then `pool["female"]`.

**`ccya/engine/narrate.py`** — in `_narrate_setup()` (line 243-253), after building the present-only roster, append pending entries:

Before (current — line 251):
```python
npc_roster=[n for n in build_npc_roster(...) if n.get("presence") == "present"],
```

After:
```python
npc_roster=[n for n in build_npc_roster(...) if n.get("presence") == "present"] + build_pending_roster_entries(_npc_name_pool, turn_no=turn_no) if _npc_name_pool else [n for n in build_npc_roster(...) if n.get("presence") == "present"],
```

(Cleaner version: build the present roster into a variable, conditionally append pending, pass the combined list.)

### Why

The LLM reliably uses roster names for NPCs. By presenting pool names as roster entries, we sidestep the LLM's training-distribution bias. Pending entries look like roster entries, so the LLM's existing "use roster names" behavior applies.

### Validation

- `make check` passes
- Start a game, check the narrator prompt (`curl` against running server or inspect events) — roster should show `[PENDING]` entries with pool names
- Run 3-turn play: `ev.py play --llm --turns 3 --pack noir-1930s --persona driven`
- Check compendium: are any pending names used?

---

## Phase 02: Update narrator prompt directives

### Depends on

Phase 01

### Context files to load

- `ccya/prompts/narrate_system.j2:37-51` — current NPC naming directives: NEW CHARACTER NAMING (line 43), FORBIDDEN NAMES (line 45), REQUIRED NAME POOL (line 47-51)
- `ccya/prompts/narrate_user.j2:54-67` — current "### Required Name Pool for New Characters" section

### What changes

Replace the three naming-related sections in `narrate_system.j2` (NEW CHARACTER NAMING, FORBIDDEN NAMES, REQUIRED NAME POOL) with a single clean directive explaining `[PENDING]` entries. Remove the pool rendering section from `narrate_user.j2`.

### Where to change

**`ccya/prompts/narrate_system.j2`** — replace lines 43-51 (the three naming sections) with:

```
**NEW CHARACTER NAMING:** When introducing a new character (or revealing the name of an unnamed character such as "the shadowy figure"), you MUST use a name from the Characters roster marked [PENDING]. These are available names, not active characters. Pick one [PENDING] name and use it. Do not invent names outside the roster.

Do NOT use these overused names: Elias, Silas, Arthur, Vance, Thorne, Brooks, Hill, Benson, Coleman, Hayes, Mercer, Shaw, Porter, Caldwell, Whitfield, Prescott, Harrington, Ashford, Blackwood, Sterling, Montgomery, Ashworth, Lockwood, Harriman, Winthrop, Cabot, Stirling, Pendleton, Worthington.
```

Remove the `{% if npc_name_pool %}` block entirely (lines 47-51).

**`ccya/prompts/narrate_user.j2`** — remove lines 54-67 (the `{% if npc_name_pool %}...{% endif %}` block that renders the pool section).

### Why

The old directives told the LLM to use a separate name pool. The LLM ignored them. The new directive points to roster entries with [PENDING], which the LLM already treats as authoritative. The forbidden names list stays as a guardrail against the most common training-distribution names.

### Validation

- `make check` passes
- Render the narrate system prompt via `curl` — no `{% if %}` artifacts, directive reads cleanly
- Render the narrate user prompt — no "Required Name Pool" section
- 3-turn play test: LLM uses pending names from roster

---

## Phase 03: Clean up context boundaries and ev support

### Depends on

Phase 02

### Context files to load

- `ccya/prompts/context.py:238-262` — `NarratorBoundary` (has `npc_name_pool: dict[str, list[str]]` field at line 261)
- `ccya/prompts/context.py:294-302` — `NarratorSystemBoundary` (does not have `npc_name_pool` but `_render` call passes it)
- `ccya/engine/narrate.py:99-130` — `user_ctx` dict and `system_text` _render call both pass `npc_name_pool`
- `ccya/ev/prompt_context.py:206-228` — narrate stream context dict passes `npc_name_pool: {}`

### What changes

Remove `npc_name_pool` from the narrator template context (both system and user prompts no longer reference it). Clean up the Python-side passing. Update ev prompt context to stop passing the field.

### Where to change

**`ccya/prompts/context.py`** — remove `npc_name_pool` field from `NarratorBoundary` (line 261). The field is no longer consumed by `narrate_user.j2`.

**`ccya/engine/narrate.py`**:
- Remove `npc_name_pool` from `user_ctx` dict (line 106)
- Remove `npc_name_pool` from `system_text` _render call (line 129)
- Remove `npc_name_pool` parameter from `_narrate_messages()` signature (line 41) — OR keep it for internal pool generation but stop passing it to templates. The pool is still generated in `_narrate_setup` and used to build pending entries, so the parameter stays but is no longer passed to `user_ctx` or `system_text`.

Decision: keep `npc_name_pool` as a parameter to `_narrate_messages()` (it's used to build pending entries in Phase 01), but remove it from the template context dicts (`user_ctx` and the `_render` system call). The function receives the pool, builds pending entries appended to the roster, and the roster is what goes to the template.

Wait — the pending entries are appended in `_narrate_setup()`, not in `_narrate_messages()`. So `_narrate_messages()` receives the roster with pending entries already appended. The `npc_name_pool` parameter to `_narrate_messages()` is no longer needed at all — the pool is consumed in `_narrate_setup()` to build pending entries, and the combined roster is passed via `npc_roster`.

So: remove `npc_name_pool` parameter from `_narrate_messages()`. Remove it from `user_ctx` and `system_text`. Remove from `NarratorBoundary`.

**`ccya/ev/prompt_context.py`** — remove `npc_name_pool` key from narrate stream context dict (line 212). Pending entries are generated at play-time and not stored in events; ev re-rendering will show the roster without pending entries. This is acceptable for prompt inspection.

### Why

Dead template variables are a maintenance hazard. The pool is now consumed by the engine to build roster entries — templates don't need to know about it.

### Validation

- `make check` passes (typecheck confirms removed fields don't break anything)
- `ev.py prompt-eval dump <save-dir> --turn N --stream narrate` renders without error
- Full 3-turn play test passes

---

## Documentation updates

- `docs/architecture/` — update the NPC roster / prompt architecture subdoc to document the `pending` presence value and how pending names are injected
- `docs/repomap.md` — add `build_pending_roster_entries()` to the npc_roster module entry
- `AGENTS.md` — add note about `pending` presence in the NPC roster section if one exists; otherwise no changes needed