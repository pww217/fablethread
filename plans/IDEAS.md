# IDEAS.md — Design change proposals

## 1. Break `run_turn()` into composable phases

**Problem.** `run_turn()` is ~1500 lines. `TurnContext` has 30+ mutable fields mixing phase inputs, outputs, and internal tracking (`_ruling_raw_response`, `_narr_trimmed_chars`, etc.). Phases can't be tested independently. Adding a step means editing the god function.

**Proposed structure.** Each phase is an async function with typed input/output. `TurnContext` shrinks to just the shared immutable reads (state, config, save_dir) plus a result bag.

```
Phase I:   RulingPhase(state, user_input, config) → RulingResult(intent, outcome, pacing_ctx, metrics)
Phase II:  NarratePhase(state, ruling_result, config) → NarrateResult(narrative, chunks, metrics)
Phase III: ExtractPhase(state, narrative, config) → ExtractResult(scene, state_delta, storyteller)
           └─ scene + state extraction run via asyncio.gather (two small local LLM calls)
Phase IV:  ApplyPhase(state, extract_result, config) → ApplyResult(applied, rejected, metrics)
Phase V:   PersistPhase(state, all_results, save_dir) → writes events/state/chronicle
```

**Key changes.**
- Drop `_ruling_raw_response`, `_narr_trimmed`, `_avoidance`, etc. from `TurnContext`. Each phase owns its transient state locally.
- Scene + state extraction parallelized via `asyncio.gather` — they're independent and both small (~20-line prompts). Storytell stays sequential (needs their results).
- `run_turn()` becomes a ~60-line orchestrator that chains phases and yields SSE events.
- Each phase is independently unit-testable with a mock LLM call.

**Migration path.** Extract phases one at a time from the existing `run_turn()` body. `_ruling_phase()` and `_narrate_setup()` already exist as separate functions — start by formalizing their signatures, then pull the remaining inline blocks into `ExtractPhase`, `ApplyPhase`, `PersistPhase`.

---

## 2. Typed state model with validation at load

**Problem.** State is `dict[str, Any]` throughout. Every access is `state.get("pc", {}).get("conditions", [])`. A malformed save silently produces `None` in pipeline logic. The delta system already has Pydantic models (`StateDelta`, `ConditionAdd`, `ConditionRemove`) but the base state they mutate is untyped. `_default_state()` defines the schema in a raw dict — the same shape duplicated ad-hoc in every access site.

**Proposed structure.** Core state maps to Pydantic models:

```python
class GameState(BaseModel):
    schema_version: int = CURRENT_SCHEMA_VERSION
    meta: MetaState
    pc: PCState
    location: LocationState
    inventory: list[InventoryItem]
    arc: CampaignArc          # already exists in models.py
    resolved_arcs: list[dict[str, Any]]
    scene: SceneState
    compendium: CompendiumState
    world: WorldState

class PCState(BaseModel):
    name: str = ""
    tagline: str = ""
    bio: str = ""
    stats: dict[str, int]       # keep dict for now — skill names are literal types in models.py
    conditions: list[Condition] # Condition already exists in models.py
    momentum: int = 0
    allegiance: str | None = None
```

**Key changes.**
- `load_state()` returns `GameState` with validation. Missing fields get defaults from model definitions, not `_default_state()`.
- `state.get("pc")` becomes `state.pc` — IDE autocomplete, mypy enforcement.
- `apply_delta()` mutates the `GameState` instance directly. Eliminates the double `deepcopy` (once in caller, once in `apply_delta`).
- Schema migration lives in `load_state()` as a version-gated transform: `if v < target, apply transform`.
- Prompt context builders read from typed fields instead of ad-hoc `dict.get` chains.

**Migration path.** Define models alongside existing dict code. `load_state()` wraps the raw YAML dict in `GameState(**raw)` with `model_config = ConfigDict(extra="allow")` for forward-compat. Switch call sites one module at a time: `state["pc"]["momentum"]` → `state.pc.momentum`. Delete `_default_state()` once all sites use the model.

---

## 3. Inventory remove existence guard

**Problem.** Engine allows `inventory_remove` of items that don't exist in the player's inventory. Eval run T7 tried to remove `ledger` and `merchant_seal` — neither was in inventory (ledger was never added by T3 extraction). The applied deltas show these passed through without rejection.

**Proposed.** Add a validation check in `validate_delta()` (or `apply_delta()`) that rejects `inventory_remove` for item IDs not present in current inventory. This mirrors the old durability gate concept but for removes. Should log a warning and skip the removal rather than crashing.

---

## 4. Arc thread expiry: no-action decay → latent → removal

**Problem.** Arc threads persist indefinitely with no automatic expiry or demotion. 4 out of 5 arc threads in the eval run were "INERT" — updated with urgency changes but never resolved in 13 turns. They sit in state forever unless explicitly resolved via `thread_resolve` or dropped via `arc_resolve` + `ThreadDirective.drop`.

**Proposed.** Implement a multi-stage thread lifecycle:
- **No action for N turns** (e.g. 5): auto-demote to `active=False` (latent). System stops rendering them in prompt context.
- **No mention for M additional turns** (e.g. 5 after latent): auto-remove from `arc.threads[]`.
- **TTL constants** in `engine_mirror.py` like the existing `THREAD_RESOLVED_ARC_TTL` and `THREAD_COMPLETED_THREAD_TTL`.
- Trigger decay pass during `_apply_thread_signals()` or as a new pipeline step between extraction and persist.
- Scene-scoped threads already purge on location change — this is for arc-scoped threads only.
