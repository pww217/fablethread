***
compaction_score: <int 1-5>
sanitization_fidelity_rate: <float 0.0-1.0>
***

# ccya Eval — Compaction Judge

You are evaluating the quality and correctness of the ccya compactor.
Compaction fires every N turns (typically every 6 turns in a 13-turn run, at T6 and T12).

You receive:
- State snapshots at and around compaction turns (full JSON, not diffs)
- Progress extractor outputs at compaction turns (which include chronicle bullets)
- Compaction signals block from the harness (per-capability observability)

If no compaction occurred in this run, state that and score 3/5 (neutral — cannot assess).

***

## SECTION 1 — Chronicle Quality

For each compaction pass (identify turns from the state_snapshot changes):

### Pass at Turn N
- List the chronicle bullets generated and the turns they cover.
- For each bullet:
  - Does it accurately represent named entities (NPCs, items, locations, thread IDs) from that turn?
  - Is it specific enough to distinguish this turn from any other?
  - Flag: `GENERIC` (could describe any turn), `INACCURATE` (wrong entity or inverted event), `MISSING_ENTITY` (named entity from turn omitted).

Score each pass: `[OK]` / `[PARTIAL]` / `[FAIL]`.

***

## SECTION 2 — Sanitization Fidelity

After each compaction pass, check:

| Field | Expected | Actual | Score |
|-------|----------|--------|-------|
| `npc_merge` | duplicate NPCs merged per compendium | | `[OK]`/`[FAIL]`/`[NA]` |
| `condition_remove` | resolved/expired conditions removed | | |
| `pressure_remove` | resolved pressures removed | | |
| `inventory_remove` | depleted items cleaned | | |
| `recent_events_compact` | recent_events entries for compacted turns consolidated | | |

**Sanitization Fidelity Rate:** (fields scored OK) / (fields scored OK + FAIL). Show arithmetic.
This value goes in YAML front matter.

***

## SECTION 3 — Compaction Score (1–5)

- 5: All bullets accurate, all sanitization fields OK.
- 4: Bullets OK, one sanitization miss.
- 3: Bullets partially generic or one PARTIAL pass, sanitization mostly OK.
- 2: Bullets inaccurate on ≥1 pass OR sanitization has ≥2 FAILs.
- 1: Bullets entirely inaccurate OR sanitization entirely absent.

***

## SECTION 4 — Actionable Issues

- **<description>** (turn: <N>) — Tag: `<generic_bullet|missing_entity|sanitization_miss|compaction_absent>`. Fix: <what to change in the compactor prompt or sanitization logic>.
