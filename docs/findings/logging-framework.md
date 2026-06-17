# Engine Failure Points — Comprehensive Analysis

## Scope

Core engine only: turn pipeline (ruling → narrate → extract → validate → apply → persist),
LLM client, state I/O, delta application. Excludes: EV, turn viewer, UI, pack generation,
character creation, eval runner.

---

## Priority Tier 1 — Delta Application (Highest Priority)

These operations mutate canonical game state. Failures here corrupt or desync state.

### `apply_delta()` — `state/delta_builder.py:117–291`

**What it does:** Deep-copies state, applies inventory adds/removes/updates, condition
adds/removes, location change, scene_tagline, NPC compendium upserts, arc updates,
storyteller actions.

**Failure modes:**

| # | Operation | Failure | Current Log Level | Signal |
|---|---|---|---|---|
| # | Operation | Failure | Current Log Level | Signal |
|---|---|---|---|---|
| 1 | `inventory_add` — fuzzy match merges into existing | `_fuzzy_match_inventory()` resolves to existing ID, merges amount into wrong item | INFO | wrong item gets merged (game state desync) |
| 2 | `inventory_add` — canonical ID found, adds to existing | Amount merged correctly, no error | INFO | inventory count desync if LLM confused two items |
| 3 | `inventory_add` — no match, creates new entry | Adds new entry with mangled name (non-ASCII stripped) | INFO | wrong new item created |
| 4 | `inventory_remove` — `resolve_inventory_remove_target()` finds nothing | Returns `None` → `KeyError` at `by_id[canonical]` line 181 | DEBUG | **500** — most common crash source |
| 5 | `inventory_remove` — `rem.amount` non-numeric | `int()` raises `ValueError`, caught at line 192 — amount coerced silently | DEBUG | item not removed |
| 6 | `inventory_update` — canonical not found | `KeyError` at `by_id[canonical]` line 206 | DEBUG | **500** |
| 7 | `inventory_update` — canonical found, applies name/notes update | Works correctly | INFO | |
| 8 | `pc_condition_add` — condition ID already in state | Silently skipped at line 250 | WARNING via `reconcile_delta` | condition not added |
| 9 | `apply_npc_scene_management()` — `CompendiumNpcUpdate` with `str` aliases | `_coerce_scene_json()` handles string coercion at extraction parse time, so `aliases` arriving as `["foo"]` works. Dict aliases like `{"foo": "bar"}` from LLM cause `TypeError` in Pydantic → caught as extraction parse failure → stream skipped | WARNING | extraction skipped for that stream |
| 10 | `apply_npc_scene_management()` — group NPC quantity merging | `_strip_quantity_suffix()` + alias map can redirect to wrong NPC ID, merging entries | DEBUG | wrong NPC merged |
| 11 | `apply_npc_scene_management()` — `first_seen_turn` / `last_seen` | `first_seen_turn` is only set when `is_new=True` (line 254) — existing entries protected | DEBUG | correct |
| 12 | `location_change` — `LocationRef` Pydantic model missing `id` | Pydantic validation fails → extraction stream parse failure → retry | WARNING | |
| 13 | `location_change` — LLM returns dict without `id` field | `_coerce_scene_json()` does not coerce this → `LocationRef(**dict)` fails Pydantic → extraction stream parse failure | WARNING | |
| 14 | `location_change` — LLM returns `location_change` as non-`LocationRef` object (e.g., dict from malformed JSON) | `delta.location_change.id` raises `AttributeError` if object has no `.id` attr, or returns `None` if it's a model with optional `id=None` → sets `location.id = None` | DEBUG | **data corruption** — location ID becomes `None` |
| 15 | `arc_update` — `_merge_arc_update()` with non-`CampaignArc` object | `AttributeError` at `.model_dump()` or `.threads` access | DEBUG | **500** |
| 16 | `arc_update` — `CampaignArc` with thread that has no `id` field | Pydantic validation on model construction catches this upstream | WARNING | |
| 17 | `actions` rolling window — `delta.actions` is `None` | Impossible — `StateDelta.actions` has `default_factory=list`, Pydantic ensures it's always a list | N/A | |

**Key gaps (verified):**
- **`inventory_remove` unresolved canonical → `KeyError` at line 181** — `resolve_inventory_remove_target()` returns `None` on no match. The code does `ex = by_id[canonical]` (not `.get()`) — a `KeyError` crashes the turn. This is the primary 500 error source. Add `if canonical is None: _log.warning(...); continue` or make `by_id[canonical]` safe.
- **Overdraw clamp silently succeeds** — `warn_overdraw` is non-blocking. The item removal is clamped and the turn succeeds. Player never knows. Currently logged at WARNING.
- **`location_change` corruption path** — if `delta.location_change` is a non-model object with a `None` or missing `id`, `location.id` gets set to `None` with no crash, no warning. The game continues with `location.id = None`.
- **`normalize_inventory_id(None)` → `"none"`** — passes `str(None)` = `"none"` through normalization. Creates garbage item ID `"none"` if `None` reaches inventory add. Should guard at source in extraction.

---

### `reconcile_delta()` — `state/delta_builder.py:71–114`

**What it does:** Coerces delta inventory/conditions, detects same-turn add+remove conflicts,
duplicate condition adds, internal condition duplicates.

**Note:** Items in `StateDelta` have Pydantic-required fields (`InventoryItem.id`, `InventoryRemove.id`,
etc.). Missing `.id` on inventory items causes Pydantic `ValidationError` at the
`StateDelta` constructor — this is caught by the extraction retry loop, not by `reconcile_delta`.
`reconcile_delta` only sees fully-validated Pydantic model instances.

| # | Operation | Failure | Current Log Level | Signal |
|---|---|---|---|---|
| 1 | Same-turn add+remove conflict — `add_ids & remove_ids` non-empty | De-duplicates by removing from add list, logs WARNING | WARNING | inventory silently loses the add |
| 2 | Duplicate condition add — already in state | Silently drops add at line 97 | WARNING | condition not added |
| 3 | Duplicate condition add within delta | Silently drops add at line 112 | WARNING | condition not added |

---

### `_validate()` — `engine/turn.py:1530–1582`

**What it does:** Pre-apply validation of `inventory_remove` against live inventory.
Returns rejection list; blocking rejections prevent `apply_delta()`.

**Verified actual crash path:**

| # | Operation | Failure | Current Log Level | Signal |
|---|---|---|---|---|
| 1 | `resolve_inventory_remove_target()` returns `None` → `canonical is None` | `inv_by_id[None]` raises `KeyError` at line 1547 — the code uses `inv_by_id[canonical]` NOT `.get(canonical, {})` | DEBUG | **500** — should be caught before here but isn't |
| 2 | `resolve_inventory_remove_target()` returns non-None but item not in `inv_by_id` | `inv_by_id[canonical]` → `KeyError` at line 1547 | DEBUG | **500** |
| 3 | `requested > current` overdraw | Correctly creates `warn_overdraw` rejection, logs WARNING | WARNING | clamped remove (non-blocking, player never knows) |
| 4 | `int(rem.amount)` raises `ValueError` | Silently skips at line 1562 | DEBUG | item not removed |

**Gap:** The `warn_overdraw` rejection is non-blocking — the turn succeeds and the item
removal is clamped. Player never knows unless they watch logs. Also, the `KeyError` at
line 1547 should be caught and turned into a rejection, not allowed to propagate as a 500.

---

## Priority Tier 2 — LLM Output Parsing and Extraction

All three extraction streams, plus ruling. These receive unstructured LLM text and must
parse it into typed Python objects.

### `extraction.py` — `_parse_stream_result()` at line 429

**What it does:** `strip_thinking()` → `_find_json()` → `_coerce_scene_json()` →
Pydantic model validation.

**Failure modes:**

| # | Phase | Failure | Current Log Level | Signal |
|---|---|---|---|---|
| 1 | All streams | `_find_json()` returns `None` (no JSON in response) | WARNING | retry loop enters |
| 2 | All streams | JSON found but Pydantic validation fails | WARNING | retry loop enters |
| 3 | All streams | After `max_llm_retries` exhausted | `ValueError` raised, caught at stream level | stream skipped, event marked `skipped=True` |
| 4 | Scene | `_coerce_scene_json()` — `CompendiumNpcUpdate` string→dict coercion fails | `TypeError`/`KeyError` inside coercion | crash |
| 5 | Scene | `_coerce_scene_json()` — `thread_add` dict missing required `{"id", "summary"}` | `del j["thread_add"]` silently drops thread_add | story incorrect |
| 6 | All streams | `model_cls(**_coerce_scene_json(j))` — field type mismatch (LLM returns wrong type for a field) | Pydantic `ValidationError` | retry loop |

**Key gap:** `_coerce_scene_json()` at line 399 is a hand-written coercion function.
It handles known cases (string→dict for npc_update, malformed thread_add) but is not
comprehensive. Any other shape mismatch from the LLM causes a crash through to the
stream-level `except Exception` at line 578/624/713, which marks the stream as skipped.

The `retry_errors` list is accumulated across retry attempts but is only used for
display in `ext_metrics["retry_errors_by_stream"]` — it is NOT added to `TurnResult.errors`
at the top level, so the UI never shows "scene extraction retried 3 times."

### `extraction.py` — `_build_extraction_context()` at line 92

**What it does:** Applies scene+state deltas to a copy of state to compute
this-turn derived context for storytell.

**Failure modes:**

| # | Operation | Failure | Current Log Level | Signal |
|---|---|---|---|---|
| 1 | `apply_delta()` on state_copy fails | `AttributeError`/`KeyError`/`TypeError` from any of the 15+ failure modes in `apply_delta` above | crash | entire extraction pipeline collapses |
| 2 | `StateDelta(...).model_validate()` fails on invalid combined delta | Pydantic validation error | crash | storytell never runs |

### `extraction.py` — `_dedup_compendium_update()` at line 191

**What it does:** Name-based NPC dedup and alias resolution for compendium updates.

**Failure modes:**

| # | Operation | Failure | Current Log Level | Signal |
|---|---|---|---|---|
| 1 | `proposed.name` is `None` | Returns `proposed` unchanged — not an error | DEBUG | wrong NPC merged |
| 2 | `existing_npcs` iteration — entry missing `.get()` | `AttributeError` if `npc` is not a dict | DEBUG | crash |
| 3 | `_extract_group_base_type()` — quantity word stripping on `None` | `TypeError` at `.lower()` on `None` | DEBUG | crash |

---

### `ruling.py` — `_call_ruling()` at line 69

**What it does:** LLM call + JSON parse + `IntentEnvelope` validation with retry loop.

**Failure modes:**

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `_find_json()` returns `None` after all retries | WARNING per attempt, ERROR at exhaustion | `_no_intent` returned, turn continues with no-roll |
| 2 | Pydantic validation fails | WARNING per attempt | retry loop |
| 3 | `reason` field empty after parse | ValueError at line 121 — retry loop | retry loop |
| 4 | `check.required=true` but `check.skill` is `None` | ValueError at line 123 — retry loop | retry loop |
| 5 | All retries exhausted | ERROR at line 146 | `_no_intent` returned, turn continues |

**Key gap:** When `_no_intent` is returned after ruling failure, the turn continues with
`intent.check.required=False` and `band="fail"`-equivalent. The parse_error is returned
as 4th tuple element but nowhere in `run_turn()` is it added to `TurnResult.errors` —
it's only stored in `ctx._ruling_parse_error` for the event record.

---

### `extraction.py` — `_call_stream()` at line 441

**What it does:** Wraps `llm_chat()` with retry loop, log_llm_io, and parse error
recovery messages.

**Failure modes:**

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | All retry attempts fail | ValueError raised to stream-level try/except | stream marked `skipped=True` |
| 2 | `retry_hint` injection for `inventory_change_reason` omission | Only partial — only handles one specific omission case | retry message may not help |
| 3 | After max retries, original `messages` list has grown with retry feedback — re-sending entire conversation to LLM on next call site's retry | Wrong prompt sent to next attempt | wrong extraction output |

**Key gap:** The retry feedback message at line 498–503 appends to `messages` list,
so if `_call_stream` is called again (e.g., multiple extraction streams retrying),
the accumulated feedback messages persist across turns. This is per-call, not global,
so it's contained — but the accumulated messages can be large.

---

## Priority Tier 3 — State I/O and Persistence

### `state/io.py` — `load_state()` at line 112

**What it does:** Load YAML, handle schema migrations, return default on corruption.

**Failure modes:**

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | YAML parse error | WARNING at line 122 | returns `_default_state()`, game starts fresh |
| 2 | Empty file | DEBUG at line 125 | returns `_default_state()` |
| 3 | Schema version > `CURRENT_SCHEMA_VERSION` | WARNING at line 131 | loaded anyway |
| 4 | `yaml.safe_load()` returns `None` (empty file) | handled at line 124 | returns `_default_state()` |

**Key gap:** When `load_state()` returns `_default_state()`, the game silently starts
fresh. No error is added to `TurnResult.errors`, no user-facing signal. If the player
was mid-game, their state just disappeared with no warning.

### `state/io.py` — `save_state()` at line 138

**What it does:** Atomic write via `tmp_path` → `os.replace()`.

**Failure modes:**

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `yaml.dump()` fails (unserializable object) | Exception propagates to `run_turn()` finally block | crash |
| 2 | `tmp_path.write_text()` succeeds but `os.replace()` fails (disk full, permissions) | `OSError` | crash — state.yaml may be corrupted |
| 3 | `os.replace()` fails leaving stale tmp file | DEBUG only | tmp file accumulates |

**Key gap:** `os.replace()` is atomic on POSIX if the dst exists — but if dst doesn't
exist (first write), it's a rename which is also atomic. However, if `os.replace()`
fails mid-operation, the tmp file is left behind and the canonical `state.yaml` is
unchanged. The game continues with stale state.

### `state/chronicle.py` — `append_event()` at line 16

**Failure modes:**

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `json.dumps()` fails (unserializable object in event) | Exception propagates to `run_turn()` finally block | crash |
| 2 | File write fails (disk full) | `OSError` | crash |

### `state/chronicle.py` — `append_chronicle()` at line 24

**Failure modes:**

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | File write fails | Exception propagates | crash |

---

## Priority Tier 3 — Engine/State Operations

### Thread operations in `turn.py`

#### `_apply_thread_updates()` at line 112

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `CampaignArc.model_validate(arc_raw)` fails | WARNING at line 134 | thread updates skipped |
| 2 | Thread ID not found in `arc.threads` | WARNING at line 150 | skipped |
| 3 | Progress dedup ≥70% similarity | WARNING at line 168 | skipped, added to `dedup_rejections` list |
| 4 | `model_copy()` on thread fails | `AttributeError` | skipped |
| 5 | Auto-latent demotion — `last_updated_turn` is `None` | Correctly skips at line 206 | silent skip |
| 6 | Urgency decay — `urgency_set_turn` is `None` | Correctly skips at line 223 | silent skip |
| 7 | Auto-latent or urgency demotion mutates thread | `mutated = True` but nothing added to `TurnResult.errors` | silent state change |

#### `_apply_arc_resolve()` at line 248

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `CampaignArc.model_validate(arc_raw)` fails | WARNING at line 274 | arc resolution skipped |
| 2 | `arc_resolve.drop_threads` ID not in current arc | `INFO` at line 287 | drop silently ignored |
| 3 | `arc_resolve.new_threads` contains invalid `ArcThread` | Pydantic validation on `CampaignArc()` constructor at line 310 | entire arc replacement fails, state unchanged |

#### `_apply_thread_resolutions()` at line 323

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `CampaignArc.model_validate(arc_raw)` fails | WARNING at line 351 | resolutions skipped |
| 2 | Thread ID not found | WARNING at line 370 | skipped |
| 3 | `promote_to_world_state=True` with no `outcome` | Silently skips promotion at line 386 | world_state not updated |
| 4 | `res.promote_to_world_state` with non-dict `res.outcome` | `TypeError`/`AttributeError` at line 387 | crash |

#### Thread add cap eviction at `turn.py:1276–1288`

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `evict.id` lookup in thread list fails | `ValueError` at line 1282 list comprehension | crash |
| 2 | No `config` passed | `AttributeError` on `config.thread_max_active` at line 1278 | crash |

### `_compute_scene_phase()` at line 492

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `ArcThread.model_validate(t)` fails on malformed thread dict | Exception caught at line 522, thread skipped | thread silently ignored |
| 2 | `state.get("scene")` returns `None` | `AttributeError` at line 508 `scene.setdefault()` | crash |

### `_narrate_setup()` arc thread iteration at line 759

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `ArcThread.model_validate(td)` fails | WARNING at line 765 | thread silently ignored, urgency count may be wrong |

### NPC scene management — `state/npcs.py:apply_npc_scene_management()`

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `normalize_inventory_id(comp_upd.id)` fails | `TypeError` on `str()` of non-string | crash |
| 2 | `_resolve_group_npc_id()` — alias map with non-string keys | `TypeError` at line 91 `nid_stripped in alias_map` | crash |
| 3 | `_find_npc_by_name()` — `npc.get("name")` is `None` | `TypeError` at `.lower()` on `None` | crash |
| 4 | Group NPC quantity merge — no canonical ID found | Creates new entry at wrong quantity | wrong NPC entry |
| 5 | `assign_personality()` fails | Exception at line 300 | personality not assigned, continues |

### Inventory normalization — `state/inventory.py`

| # | Function | Failure | Current Log Level | Signal |
|---|---|---|---|---|
| 1 | `normalize_inventory_id()` — `raw` is `None` | `TypeError` on `raw.lower()` at line 37 | crash |
| 2 | `resolve_inventory_canonical_id()` — no match | Returns `None` | silent, leads to `KeyError` in caller |
| 3 | `_fuzzy_match_inventory()` — no candidate has any tokens | Returns `None` | silent |
| 4 | `_fuzzy_match_inventory()` — `name` is `None` | `TypeError` at `name.lower()` | crash |

---

## Priority Tier 4 — API and HTTP Layer

Focusing on the flow from HTTP request to engine call, not UI rendering.

### `routes.py` — `/turn` SSE endpoint at line 211

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `run_turn()` raises `LlmcTimeout` | caught at line 301, `_app_mod.logger.exception("Turn failed")` | SSE `turn_error` event |
| 2 | `run_turn()` raises `LlmcError` | caught at line 301 | SSE `turn_error` event |
| 3 | `run_turn()` raises generic `Exception` | caught at line 301 | SSE `turn_error` event |
| 4 | `result.errors` contains errors but not all-streams-failed | errors looped at line 252 with `_log.error()` but no SSE event sent | silent in JSONL |
| 5 | All 3 streams failed — line 262 detection | yields `turn_error` SSE event | user sees error in UI |
| 6 | `is_turn_in_progress()` race condition | Two concurrent `/turn` calls both see `False` | both start, `_inflight` semaphore handles |
| 7 | `load_state()` called in `event_stream()` generator | Exception at line 288 `_load_current_state()` | SSE `turn_error` event |

**Key gap:** The error loop at line 252 iterates `result.errors` but only logs them
— does not yield a `turn_error` SSE event. The user never sees per-stream errors in
the UI, only the top-level exception case. Errors in `TurnResult.errors` are the
primary structured error signal from the engine and they're mostly invisible to users.

### `routes.py` — `/new-game` at line 373

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `load_pack()` fails | logger.exception at line 452 | 400 HTML response |
| 2 | `generate_seed()` fails | logger.exception at line 452 | 500 HTML response |
| 3 | `_apply_seed_to_save_dir()` — `init_save_dir()` fails | exception propagates | 500 |
| 4 | Pack switching — `load_pack()` fails | logger.error at line 385 | 400 JSON response |

### Narrate streaming — client disconnect during SSE stream

`llm_chat_stream()` at `turn.py:956` iterates and yields tokens. If the client disconnects,
the SSE connection drops and the `async for` loop exits. `run_turn()` continues processing
(upstream LLM call completes, extraction runs, state saves). No error is logged —
the turn succeeds in the background. The player sees a truncated or missing narrative.

This is a known SSE limitation: the generator exits silently on client disconnect.
No `errors` entry is added. The turn is persisted with whatever narrative was accumulated.

---

### Narrate streaming — `strip_thinking()` on accumulated chunks

`turn.py:976`: `narrative = strip_thinking("".join(narrative_chunks))`

If the LLM emits a very large response, `join()` could fail with `MemoryError` —
theoretically possible but practically unlikely given `max_tokens` limits.

---

### Narrate streaming — streaming completes but `narrative` is empty

If `strip_thinking()` removes all content (LLM emitted only `<thinking>` tags),
`narrative` becomes `""`. No crash — empty narrative is persisted and displayed.
Not logged at any level. The turn succeeds with blank narration.

---

### `routes.py` — `/new-game/reroll` at line 461

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `generate_seed()` fails | logger.exception at line 473 | HTML error response |
| 2 | `_apply_seed_to_save_dir()` fails | exception propagates | HTML error response |

### `routes.py` — `/turn/cancel` at line 308

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `await_turn_done()` timeout (30s) | WARNING at line 319 | continues, cancel flag still set |
| 2 | `pre_turn_state` missing from last event | WARNING at line 332 | state not reverted, event still removed |
| 3 | `remove_last_chronicle_turn()` fails | WARNING | event removed but chronicle not reverted |

### `routes.py` — `/turn/delete` at line 340

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `pre_turn_state` missing | WARNING at line 363 | state not reverted |
| 2 | `save_state()` fails after `remove_last_event()` | exception | state.yaml may be corrupted |
| 3 | `remove_last_event()` fails | exception | chronicle has extra entry |

### `routes.py` — `/api/switch-save` at line 834

| # | Failure | Current Log Level | Signal |
|---|---|---|---|
| 1 | `load_state(target)` fails | `_log.error()` at line 869 | 500 JSON |
| 2 | Path traversal guard passes but path is outside allowed tree | `ValueError` on `relative_to()` | 400 JSON |

---

## Summary of Error-to-Log Alignment Issues

### Current: ERROR/WARNING混用 — no structured error classification

| Error Type | Where It Occurs | Current Level | Should Be (per user requirement) |
|---|---|---|---|
| `inventory_remove` target not found | `delta_builder.py:181` | DEBUG | INFO (visible to operator, blocks state change) |
| `apply_delta` KeyError on missing inventory ID | `delta_builder.py:181` | DEBUG (crashes) | INFO (500s are the common case) |
| `CompendiumNpcUpdate` field type mismatch | `npcs.py` | DEBUG (crashes) | INFO |
| `location_change.id` is None | `delta_builder.py:217` | DEBUG (crashes) | INFO |
| `actions` is None in delta | `delta_builder.py:284` | INFO (crashes) | INFO |
| YAML parse error on `load_state` | `io.py:122` | WARNING | INFO (player lost their game) |
| Empty file on `load_state` | `io.py:125` | DEBUG | INFO |
| Overdraw clamp (warn_overdraw) | `turn.py:1157` | WARNING | INFO |
| Stream all-retry-exhausted | `extraction.py` | WARNING per stream | INFO |
| Ruling parse failure exhausted | `ruling.py:146` | ERROR | WARNING |
| `TurnResult.errors` not shown to user | `routes.py:252` | ERROR (log only) | INFO (should yield SSE event) |
| `state.yaml` write failure | `io.py` | Exception propagates | ERROR |
| `events.jsonl` write failure | `chronicle.py` | Exception propagates | ERROR |

### Current: DEBUG-only but crashes (verified 500 sources)

These crash the turn or return 500 and are currently logged at DEBUG:

- **`inventory_remove` canonical unresolved** → `KeyError` at `delta_builder.py:181` (should be caught and rejected, but isn't — primary 500)
- **`inventory_update` canonical not in `by_id`** → `KeyError` at `delta_builder.py:206`
- **`_merge_arc_update()` with non-model object** → `AttributeError` at `delta_builder.py:62` (only if `delta.arc_update` is passed a non-CampaignArc; normally `CampaignArc` from Pydantic model)
- **`location_change` with non-`LocationRef` object** → `AttributeError` or silent `None` assignment at `delta_builder.py:217` (data corruption, not crash)
- **`normalize_inventory_id(None)` → `"none"`** → leads to garbage inventory item with id `"none"` if `None` reaches `_item_to_dict` (inventory.py:37 — `str(None) = "None"` → normalized to `"none"`)
- **`_fuzzy_match_inventory(None, inv)`** → `TypeError` at `name.lower()` if name is `None`
- **`ArcThread.model_validate()` on malformed thread dict** — caught at multiple call sites (turn.py:132, 272, 349, 761), logs WARNING, skips gracefully
- **`_resolve_group_npc_id()` with non-string keys in alias map** — alias map built from `npcs.py:35–72` with `result[alias] = npc_id` where alias could be non-string if a non-string alias was stored

### What the User Actually Sees on 500s

`routes.py:301`: `_app_mod.logger.exception("Turn failed")` → bare `str(e)` in SSE
`turn_error` event → user sees: `"An error occurred. Trace ... — try rephrasing."`

The trace ID is logged with `{"error_kind": "TURN_PROCESSING_FAILED"}` in the JSONL
file, but the specific error kind (which of the 15+ failure modes it was) is NOT
included in the SSE event payload. The operator must grep the JSONL log to know
what actually happened.

### TurnResult.errors Accumulation Points

`errors` list is appended to at:
1. `turn.py:1044` — extraction pipeline exception → `TURN_PROCESSING_FAILED`
2. `turn.py:1138–1143` — delta validation blocking rejections → raw string only (no `kind`)
3. `turn.py:1477` — `LlmcTimeout` → `ErrorKind.LLM_TIMEOUT`
4. `turn.py:1483` — `LlmcError` → `exc.kind`
5. `turn.py:1491` — generic Exception → `TURN_PROCESSING_FAILED`

Gap: Validation blocking rejections at step 2 use raw strings with no `ErrorKind`.
Gap: `TurnResult.errors` is never sent to the UI via SSE — only the top-level
exception path (step 3–5) surfaces as a `turn_error` SSE event.

---

## Current Log Level Inventory (What Gets INFO vs DEBUG)

### INFO level (visible on stdout)
- `run_turn` start/end per turn
- Ruling call start
- Thread updates applied, auto-latent, urgency decay
- Arc resolve applied
- Thread cap eviction
- `goal_update` visible_goal changes
- `inventory fuzzy merge`
- `Applied N Storyteller Actions`
- `archived_departed_npcs`
- Server app startup (pack loaded, model warmup, save resumed)
- Server routes errors: pack load failure, new_game failure, generate_seed reroll failure

### DEBUG level (file-only, not visible)
- `load_state` default state returns
- All inventory resolution (canonical ID lookups, fuzzy matches)
- `strip_npcs_notes`
- `build_npc_alias_map`
- `touch_compendium_order`
- `apply_npc_scene_management` details
- Per-stream extraction results
- Per-stream merge/dedup
- Condition aging passes
- Persist calls (append_event, append_chronicle)

### WARNING level
- Delta reconciliation conflicts
- Thread progress dedup rejections
- Stream parse failures (per attempt)
- Ruling parse failures (per attempt)
- Stream timeout/LLM errors (per stream)
- Ruling failure exhausted
- `resolve_check` failure
- Config warnings
- `thread_sanitizer` failures
- `cancel_turn` state_snapshot missing
- `delete_last_turn` state_snapshot missing
- YAML parse errors
- Schema version mismatch
- Prompts log write failure

### ERROR level
- `run_turn` extraction pipeline error (top-level)
- `run_turn` LLM timeout
- `run_turn` LLM error
- `run_turn` generic exception
- Routes: Turn failed (exception)
- Routes: Pack load failed
- Routes: new_game failed
- Routes: generate_seed reroll failed
- `turn_result.errors` loop iteration (route level)
- Switch_save load failure
- Delete_save OSError

---

## Executive Summary — What to Fix First

### Most Game-Breaking

1. **`inventory_remove` unresolved canonical → 500** (`delta_builder.py:181`)
   - `resolve_inventory_remove_target()` returns `None` → `by_id[canonical]` raises `KeyError`
   - `KeyError` is caught at the `except Exception` wrapping `apply_delta()` in `run_turn()`
   - Turn fails with generic `TURN_PROCESSING_FAILED`, player sees "An error occurred. Trace …"
   - **Fix**: Add `if canonical is None: _log.info(...); continue` before `ex = by_id[canonical]`

2. **`inventory_update` canonical not found → 500** (`delta_builder.py:206`)
   - Same pattern — `KeyError` propagates through `apply_delta` → caught at top level
   - **Fix**: Guard with `if canonical not in by_id: _log.info(...); continue`

3. **`location_change` with non-`LocationRef` object → silent data corruption** (`delta_builder.py:217`)
   - If `delta.location_change` is a dict or model with `None` id, sets `location.id = None`
   - No crash, no warning — game continues with broken location state
   - **Fix**: Validate `delta.location_change.id` before assignment; log at ERROR level

4. **`load_state()` returns `_default_state()` silently** (`io.py:122`)
   - Player loses entire game state, turn continues as if starting fresh
   - Only a WARNING logged — operator never sees it without grep
   - **Fix**: Log at ERROR level, add to `TurnResult.errors`

### Most Common Operational Pain (Non-Crashing)

5. **Overdraw clamp silently succeeds** — `warn_overdraw` rejection is non-blocking
   - Player tries to use an item they don't have enough of, it gets removed anyway
   - Only visible in JSONL log at WARNING level
    - **Fix**: Either block the turn (return rejection) or promote to INFO

7. **`TurnResult.errors` never sent to UI** (`routes.py:252`)
   - Per-stream errors and validation rejections are logged but invisible to player
   - Only top-level exception surfaces as SSE `turn_error` event
   - **Fix**: Yield SSE `turn_error` event for each item in `result.errors`

### Quick Wins

8. Add `INVENTORY_REMOVE_FAILED`, `INVENTORY_UPDATE_FAILED`, `LOCATION_CHANGE_INVALID`,
   `DELTA_VALIDATION_FAILED`, `STATE_LOAD_FAILED` to `ccya/errors.py`
9. Promote DEBUG-level delta failures to INFO (they're operator-visible failures, not diagnostics)
10. `_validate()` `KeyError` at line 1547 should be caught and turned into a rejection, not propagated

---

## Gap: Missing ErrorKinds in `ccya/errors.py`

`ccya/errors.py` exists with `LLM_TIMEOUT`, `LLM_RATE_LIMIT`, `LLM_API_ERROR`,
`PARSE_ERROR`, `VALIDATION_ERROR`, `PACK_LOAD_FAILED`, `SEED_GENERATION_FAILED`,
`PACK_GENERATION_FAILED`, `SERVER_ERROR`, `TURN_PROCESSING_FAILED`.

Missing for the failure modes catalogued above:
- `INVENTORY_REMOVE_FAILED` — canonical not found, amount error
- `INVENTORY_UPDATE_FAILED` — target not found
- `INVENTORY_ADD_FAILED` — type error in item_to_dict
- `DELTA_VALIDATION_FAILED` — blocking rejections
- `NPC_SCENE_MANAGEMENT_FAILED` — type error in compendium update
- `CONDITION_AGING_FAILED` — turns_remaining type error
- `LOCATION_CHANGE_INVALID` — None id/name
- `STATE_SAVE_FAILED` — yaml dump/replace error
- `EVENT_APPEND_FAILED` — JSON serialization error
- `CHRONICLE_APPEND_FAILED` — file write error
- `THREAD_UPDATE_INVALID` — model_validate fails
- `ARC_RESOLVE_INVALID` — model_validate fails
- `EXTRACTION_CONTEXT_BUILD_FAILED` — apply_delta fails in _build_extraction_context
- `SCENE_DEDUP_FAILED` — group base type extraction error
- `THREAD_RESOLVE_INVALID` — promote_to_world_state type error
- `INVENTORY_NORMALIZE_FAILED` — None input to normalize
- `FUZZY_MATCH_FAILED` — None input
- `NPC_NAME_LOOKUP_FAILED` — None name
- `RULING_PARSE_FAILED` — after all retries
- `EXTRACTION_PARSE_FAILED` — after all retries
