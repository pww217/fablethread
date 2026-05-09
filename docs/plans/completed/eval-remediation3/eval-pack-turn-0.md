# Plan: Fix Eval Pack Turn-0 Start

**Problem:** Eval pack `seed_state.yaml` has `meta.turn: 1` instead of `meta.turn: 0`. This causes the first eval turn to be labeled as turn 2 (since `turn_no = state.meta.turn + 1` in `run_turn()` line 362).

**Root cause:** The seed state was authored with `turn: 1` — likely a copy-paste error or misunderstanding of the turn counter semantics.

**Goal:** Ensure eval packs start at turn 0 for a clean evaluation baseline.

---

## 1. Fix — `evals/packs/eval-pack/seed_state.yaml`

Change line 3 from:
```yaml
  turn: 1
```
to:
```yaml
  turn: 0
```

That's the only change needed. The engine's `run_turn()` does `turn_no = state.get("meta", {}).get("turn", 0) + 1`, so with `turn: 0` the first turn will be `turn_no = 1`, which is the correct first turn.

---

## 2. Verification

After the fix:
- First eval turn should be labeled as turn 1 (not turn 2)
- `state.meta.turn` after first turn should be 1
- `state.meta.turn` after N turns should be N
- Chronological ordering of events should be correct (turn 1, 2, 3, ...)

---

## 3. Summary of Changes

| File | Change |
|---|---|
| `evals/packs/eval-pack/seed_state.yaml` | Change `meta.turn: 1` to `meta.turn: 0` |
