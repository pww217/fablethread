# Plan 3: Seed Generation Hardening

## Status
`completed`

## Phases

2 phases: (1) increase retry budget and improve feedback messages on parse/validation failures; (2) enforce first+last name format for seed-generated present_npcs.

## Issue

**Problem A — Too few retries with generic feedback:** `generate_seed()` only attempts 2 total calls (default: 1 retry, from config.py line 131). On failure, the LLM receives generic messages like "No JSON found in generate_seed response" or "SeedEnvelope validation failed: {error[:300]}" — no specifics on what was wrong. With strict constraints (`actions` exactly 4 items, `opening_narrative` min 50 chars, nested `present_npcs` list), a single structural error leaves only one more attempt to self-correct. Failure results in broken new game with empty opening and actions.

**Problem B — NPC last names not enforced:** The seed prompt (`generate_seed_system.j2:163-167`) instructs PC names must have "a given name and family name" but present_npcs only specifies `{name: string}` without the same constraint. `present_npcs` is typed as `list[dict[str, Any]]` (pack.py:56) — no Pydantic validation enforces first+last format for NPCs. `_sanitize_envelope()` strips non-ASCII from NPC names but does not split or append last names.

## Solution

Phase 1: Increase default retry budget to 3 total attempts and add structured feedback that tells the LLM exactly which field failed (parse vs validation) with specific constraint violations. Phase 2: Add post-processing in `_sanitize_envelope()` that detects single-word NPC names and appends a generated family name via `generate_name_pool()`.

## Firm decisions

1. Retry budget increased from default 1 to 3 total attempts (`max_retries=2` → config key `generate_seed_max_retries`). This is configurable — existing deployments can override via config.yaml under `llm.generate_seed_max_retries: N`.
2. Feedback messages distinguish between parse failure ("No JSON found") and validation failure (specific field constraint violations like "actions must have exactly 4 items" or "opening_narrative must be at least 50 characters"). The LLM can self-correct when given specific constraints rather than generic errors. With strict constraints (`actions` exactly 4 items, `opening_narrative` min 50 chars, nested `present_npcs` list), a single structural error leaves only one more attempt to self-correct — insufficient for reliable generation. Three total attempts (default retry=2) provides adequate recovery budget without excessive latency.
3. NPC last name enforcement uses a curated surname pool (`["Smith", "Jones", "Black", "Stone", "Fox", "Wolf", "Hawk", "Knight"]`) with SHA256-deterministic selection via hash of `f"{npc['name']}-{npc_id}"` for reproducibility. This avoids requiring locale/seed parameters in `_sanitize_envelope()` while still producing consistent results across runs. Single-word NPC names get a family name appended; multi-word names are left unchanged.

## Non-goals

- Does not add Pydantic validation to `present_npcs` dicts (they remain `list[dict[str, Any]]`).
- Does not modify the seed prompt template — enforcement is post-processing only.
- Does not change retry behavior for other LLM calls (ruling, extraction) — only generate_seed.

## Risks, Ambiguities, and Blockers

**Ambiguity:** Should feedback messages include the raw Pydantic error string or be reformatted into natural language? Reformatted is better for LLM comprehension but requires parsing the error to extract field names. Simplest approach: pass through the first 300 chars of the Pydantic error (current behavior) plus a one-line summary like "Check required fields and array lengths."

**Risk:** Increasing retries from 1 to 2 means longer seed generation time on failure. Default timeout is 180s per LLM call — with 3 attempts that's up to 9 minutes total. Acceptable for new-game creation which happens infrequently.

**Blocker:** None. Both phases touch only `seed.py` and optionally `config.yaml`. No cross-module contract changes.

---

## Implementation — Phase 1: Retry budget increase and structured feedback

### Context files to load
- `ccya/engine/seed.py` — retry loop at lines 267-305; feedback message construction
- `ccya/engine/config.py` — default value for `generate_seed_max_retries` (line 131)
- `config.yaml` — optional override location under `llm:` section

### Detailed steps

#### Step 3.1.1 — Increase default retry budget in config.py

**File:** `ccya/engine/config.py`

**What:** Change the default for `generate_seed_max_retries` from `1` to `2` on line 131:
```python
# Before:
generate_seed_max_retries=int(llm.get("generate_seed_max_retries", 1)),
# After:
generate_seed_max_retries=int(llm.get("generate_seed_max_retries", 2)),
```

**Why:** Default of 1 gives only 2 total attempts. With complex nested JSON structures, a single failure leaves one shot to self-correct — insufficient for reliable generation. Three total attempts (default retry=2) provides adequate recovery budget without excessive latency.

**Validation:** Run `make check`. Verify that existing config.yaml entries are not affected (they override the default). If no explicit key exists in user configs, new games get 3 attempts instead of 2.

#### Step 3.1.2 — Improve feedback messages on seed generation failure

**File:** `ccya/engine/seed.py`

**What:** Enhance retry feedback at two locations:
- Parse failure (lines 268-279): Keep the generic "No JSON found" message but append a structured hint listing common constraints. Example: `"Your output failed to parse: No JSON found in generate_seed response. Common issues: actions must be exactly 4 items; opening_narrative must be at least 50 characters; present_npcs must include id, name, title for each NPC. Re-emit a valid SeedEnvelope JSON only."`
- Validation failure (lines 291-305): Keep the Pydantic error string but add a one-line summary of what to check. Example: `"SeedEnvelope validation failed: {parse_error}. Check field types, required fields, and array length constraints. Re-emit corrected JSON matching the schema."`

**Why:** Generic feedback ("try again") doesn't help LLMs self-correct on structural errors. Specific constraint hints let the model identify which part of its output was wrong — especially critical for `actions: exactly 4 items` which is a common failure point. The Pydantic error already contains field-level details; wrapping it with actionable context improves recovery rate.

**Validation:** Run `make check`. No interface changes — only string literal updates in existing warning/feedback paths. Existing retry loop logic unchanged.

### Tests to write or update

- **Test: seed generation retries on parse failure with improved feedback**
  - Setup: Mock LLM that returns invalid JSON on first call, valid SeedEnvelope on second
  - Run `generate_seed()`
  - Assert: exactly 2 attempts made; second attempt receives enhanced feedback message containing constraint hints
  
- **Test: seed generation retries on validation failure with structured error**
  - Setup: Mock LLM that returns malformed JSON matching schema structure but wrong array lengths (e.g., actions has 3 items instead of 4)
  - Run `generate_seed()`
  - Assert: validation error caught; feedback includes Pydantic error string plus "Check field types, required fields" hint

### REPOMAP updates required

- `ccya/engine/config.py`: default for `generate_seed_max_retries` changed from 1 to 2 — update comment if present near line 131.
- No changes to public API or model shapes.

---

## Implementation — Phase 2: NPC last name enforcement via post-processing

### Context files to load
- `ccya/engine/seed.py` — `_sanitize_envelope()` function (lines 31-50)
- `ccya/engine/names.py` — `generate_name_pool()`, `generate_npc_names()` functions for family name generation
- `pack.py` — SeedScene present_npcs type definition at line 56

### Detailed steps

#### Step 3.2.1 — Add NPC last name enforcement to _sanitize_envelope()

**File:** `ccya/engine/seed.py`

**What:** After the existing non-ASCII stripping loop for present_npcs (lines 42-46), add a check: if an NPC's name contains only one word, append a randomly generated family name. Use `generate_name_pool()` from `ccya.engine.names` to get a pool of surnames and pick one deterministically via hash of the NPC ID for reproducibility.

Specifically:
- After line 46 (`npc["notes"] = _strip_non_ascii(npc.get("notes", ""))`), add:
```python
name_parts = npc["name"].split()
if len(name_parts) == 1 and name_parts[0]:
    surname_hash = sha256(f"{npc['name']}-{npc_id}".encode()).hexdigest()[:4]
    surnames_pool = ["Smith", "Jones", "Black", "Stone", "Fox", "Wolf", "Hawk", "Knight"]
    npc["name"] = f'{name_parts[0]} {surnames_pool[int(surname_hash, 16) % len(surnames_pool)]}'
```
- Apply same logic to compendium NPCs in the loop at lines 47-52.

**Why:** The seed prompt instructs PC names must have first+last name but present_npcs only specifies `{name: string}` without enforcement. Post-processing ensures all NPC names follow the expected format regardless of LLM output quality. Deterministic hashing via SHA256 ensures the same NPC always gets the same surname, avoiding randomness in generated seeds.

**Validation:** Run `make check`. Verify that multi-word NPC names are left unchanged. Single-word names get a family name appended deterministically. No model changes — present_npcs remains `list[dict[str, Any]]`.

### Tests to write or update

- **Test: single-word NPC name gets surname appended**
  - Setup: SeedEnvelope with present_npcs containing one entry: `{id: "npc1", name: "John"}`
  - Run `_sanitize_envelope()`
  - Assert: `envelope.seed_state.scene.present_npcs[0]["name"]` starts with "John " (two words)

- **Test: multi-word NPC name left unchanged**
  - Setup: SeedEnvelope with present_npcs containing one entry: `{id: "npc2", name: "Jane Doe"}`
  - Run `_sanitize_envelope()`
  - Assert: `envelope.seed_state.scene.present_npcs[0]["name"]` == `"Jane Doe"` (unchanged)

- **Test: same NPC always gets same surname (deterministic)**
  - Setup: Two identical SeedEnvelopes with `{id: "npc3", name: "Alex"}`
  - Run `_sanitize_envelope()` on both
  - Assert: both produce the same full name for npc3

### REPOMAP updates required

- `ccya/engine/seed.py`: `_sanitize_envelope()` now performs NPC last-name enforcement in addition to non-ASCII stripping — update docstring comment if present.
- No changes to public API or model shapes.
