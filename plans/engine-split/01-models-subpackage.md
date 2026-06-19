# Plan: Models Subpackage Split

## Purpose

Split `ccya/models.py` (604 lines, 24 models + 3 aliases + 2 functions) into a domain-aligned `ccya/models/` subpackage while preserving all import paths.

## Problem Statement

`ccya/models.py` is a flat file of 24 models spanning 5 unrelated domains (state data, extraction schemas, rules types, config helpers, dormant compactor stubs). Every consumer that imports one model imports the entire file, and LLM agents browsing by path must load all 604 lines to find the model they need.

## Constraints

- All existing `from ccya.models import X` statements must continue to work — `ccya/models/__init__.py` re-exports every symbol from submodules.
- No field, validator, or default value changes.
- No new external dependencies.

## Non-goals

- Behavioral changes, field renames, or validator logic changes.
- Splitting models already in other files (`pack.py` has its own model classes — `SeedPC`, `PlayerOverrides`, `SeedEnvelope`, etc.).
- Any changes to consumers of models (import statements stay identical).

## Solution

Replace the flat `ccya/models.py` with a `ccya/models/` subpackage. Five domain files + one `__init__.py` that re-exports every symbol. The single `_log` logger splits to one per file (standard Python pattern).

## Firm decisions

1. `ccya/models/__init__.py` re-exports every public symbol — no consumer import changes.
2. Models are grouped by domain: state data, extraction schemas, rules types, config types, compactor stubs.
3. Each sub-file uses `logging.getLogger(__name__)`.
4. The original `ccya/models.py` is deleted after the subpackage is created and verified.

## Risks, Ambiguities, and Blockers

- **Missed re-export:** A model not re-exported from `__init__.py` will cause `ImportError` at runtime. Mitigation: final validation step greps all `from ccya.models import` call sites and compares against the `__init__.py` re-export list.
- **No model-to-model imports exist within models.py** — all models import from stdlib only. No cross-file coupling risk.
- **Tests are temporarily removed** — validation relies on `make check` (lint + typecheck).

## Status
`open`

## Phases

Single phase.

---

## Implementation — Phase 1: Create subpackage, move models, delete old file

### Context files to load

- `ccya/models.py` — the full flat file; read all model definitions to extract into sub-files
- `docs/design/engine-file-splitting-design.md` — design authority; "Models subpackage" section

### Detailed steps

#### Step 1.1 — Create `ccya/models/` directory

**File:** `ccya/models/` (new directory)

**What:** Create the `ccya/models/` package directory and `__init__.py` with the full re-export block.

`__init__.py` template:
```python
from ccya.models.state import (
    ArcResolution, ArcThread, CampaignArc, Condition, ConditionAdd,
    ConditionRemove, InventoryItem, InventoryRemove, InventoryUpdate,
    LocationRef, NpcPresence, ProgressEntry, ThreadResolution,
    ThreadUpdate, WorldStateFact,
)
from ccya.models.extraction import (
    CompendiumNpcUpdate, GMBeat, SceneExtractResult,
    StateDelta, StateExtractResult, StorytellerResult,
)
from ccya.models.rules import IntentEnvelope, RulesCheck, RulesOutcome
from ccya.models.config import Band, Difficulty, SkillName, TurnResult, load_config, save_config
from ccya.models.compactor import (
    CompactorNpcMerge, CompactorSanitizationAction, CompactorSanitizationResult,
)
```

**Why:** The `__init__.py` is the public API of the subpackage — every consumer import passes through it.

**Validation:** Run `python -c "from ccya.models import *"` (will fail until sub-files exist — expected).

#### Step 1.2 — Create `ccya/models/state.py`

**File:** `ccya/models/state.py` (new)

**What:** Move these model classes and their validators from `ccya/models.py`:
- `NpcPresence` (Enum, str)
- `ProgressEntry` → fields: `kind: str`, `text: str`
- `ArcThread` → fields: `id`, `summary`, `dormant`, `urgency`, `type`, `progress`, `resolution_state`, `outcome`, `resolved_turn`, `last_updated_turn`, `added_turn`, `urgency_set_turn`; includes `_coerce_active_to_dormant`, `_dormant_not_urgent`, `_coerce_progress` model/field validators
- `CampaignArc` → fields: `visible_goal`, `threads`, `completed_threads`, `last_thread_created_turn`
- `Condition` → fields: `id`, `label`, `description`, `added_turn`
- `ConditionAdd` → fields: `id`, `label`, `description`
- `ConditionRemove` → fields: `id`
- `InventoryItem` → fields: `id`, `name`, `notes`, `amount`, `aliases`
- `InventoryRemove` → fields: `id`
- `InventoryUpdate` → fields: `id`, `name`, `notes`, `amount`
- `LocationRef` → fields: `id`, `name`, `description`
- `WorldStateFact` → fields: `id`, `text`, `tier`
- `ThreadResolution` → fields: `id`, `resolution_state`, `outcome`, `promote_to_world_state`
- `ThreadUpdate` → fields: `id`, `dormant`, `urgency`, `type`, `progress`, `progress_kind`
- `ArcResolution` → fields: `resolution`, `visible_goal`, `goal_context`, `drop_threads`, `new_threads`

Imports: `from __future__ import annotations`, `from typing import Any, Literal`, `from enum import Enum`, `from pydantic import BaseModel, Field`.

**Why:** State/thread models are the most numerous group. They are imported by `thread_sanitizer`, `state/delta_builder`, `state/npcs`, `prompts/context`, and `pack`.

**Validation:** `python -c "from ccya.models.state import ArcThread; print(ArcThread.model_json_schema()['title'])"` prints "ArcThread".

#### Step 1.3 — Create `ccya/models/extraction.py`

**File:** `ccya/models/extraction.py` (new)

**What:** Move these model classes with their validators:
- `CompendiumNpcUpdate` → fields: `id`, `name`, `title`, `bio`, `aliases`, `presence`, `notes`, `position`, `motivation`, `fear`, `leverage`, `bond`, `personality`, `departed_reason`, `departed_turn`, `first_seen_turn`; includes `model_validator` for write-once `personality`
- `StateDelta` → fields: `inventory_change_reason`, `condition_change_reason`, `scene_tagline`, `location_change`, `location_description`, `compendium_npc_update`, `inventory_add`, `inventory_remove`, `inventory_update`, `pc_condition_add`, `pc_condition_remove`, `actions`, `arc_update`
- `SceneExtractResult` → fields: `scene_tagline`, `location_change`, `location_description`, `compendium_npc_update`
- `StateExtractResult` → fields: `inventory_add`, `inventory_remove`, `inventory_update`, `inventory_change_reason`, `pc_condition_add`, `pc_condition_remove`, `condition_change_reason`; includes `_validate_inventory_reason` and `_validate_condition_reason` model_validators
- `GMBeat` → fields: `type`, `surface_as`, `beat_expires_turn`
- `StorytellerResult` → fields: `thread_update`, `goal_update`, `arc_resolve`, `thread_resolve`, `thread_add`, `actions`, `outcome_summary`, `gm_beat`, `chapter_end`; includes `_nullify_invalid_gm_beat` model_validator

Imports: same as step 1.2 plus `from typing import Literal`.

**Why:** Extraction models form a cohesive domain — they are the output schemas of the 3-stream extraction pipeline, consumed by `turn.py`, `state/delta_builder`, and `state/npcs`.

**Validation:** `python -c "from ccya.models.extraction import StorytellerResult; print('ok')"` prints "ok".

#### Step 1.4 — Create `ccya/models/rules.py`

**File:** `ccya/models/rules.py` (new)

**What:** Move these model classes:
- `RulesCheck` → fields: `required`, `skill`, `difficulty`
- `IntentEnvelope` → fields: `intent`, `intent_verb`, `target`, `check`, `scene_motion`, `impossible`, `reason`; includes `model_validator` and `field_validator` for reason length
- `RulesOutcome` → fields: `rolled`, `band`, `directive`, `intent_verb`, `intent`, `skill`, `difficulty`, `reason`, `stat_value`, `stat_mod`, `diff_mod`, `dice`, `raw_total`, `final_total`, `impossible`

Imports: `from pydantic import BaseModel, Field` plus standard library.

**Why:** Rules models are a small, self-contained domain consumed by `ruling.py`, `rules.py`, `_pacing.py`, `narrate.py`, `prompts/context.py`, and `extraction.py`.

**Validation:** `python -c "from ccya.models.rules import IntentEnvelope; print('ok')"` prints "ok".

#### Step 1.5 — Create `ccya/models/config.py`

**File:** `ccya/models/config.py` (new)

**What:** Move these:
- Type aliases: `SkillName`, `Difficulty`, `Band`
- `TurnResult` dataclass → fields: `turn`, `trace_id`, `narrative`, `state_delta`, `applied`, `rejected`, `actions`, `diff`, `changes`, `metrics`, `errors`, `ruling`, `outcome_summary`, `gm_beat`, `outcome_hint`, `scene_phase`, `summary`, `ts`
- `load_config(path)` function
- `save_config(path, config_dict)` function

Imports: `from dataclasses import dataclass, field`, `from pathlib import Path`, `from typing import Any, Literal`, `import logging`, `import os`, `import yaml`.

**Why:** Config/top-level types are consumed by `logging_setup`, `server/routes`, `server/app`, `ev/play`, `ev/eval`, `ev/check`.

**Validation:** `python -c "from ccya.models.config import load_config, TurnResult; print('ok')"` prints "ok".

#### Step 1.6 — Create `ccya/models/compactor.py`

**File:** `ccya/models/compactor.py` (new)

**What:** Move these (dormant) model classes:
- `CompactorNpcMerge` → fields: `source_id`, `target_id`, `reason`
- `CompactorSanitizationAction` → fields: `action`, `id`, `confidence`, `reason`; includes `_coerce_sanitization_actions` field_validator
- `CompactorSanitizationResult` → fields: `thread_updates`, `inventory_remove`, `pressure_remove`, `condition_remove`

**Why:** Compactor models are explicitly dormant and should not clutter active model files. Keeping them separate signals that they are not in use.

**Validation:** `python -c "from ccya.models.compactor import CompactorSanitizationResult; print('ok')"` prints "ok".

#### Step 1.7 — Delete `ccya/models.py`

**File:** `ccya/models.py` (delete)

**What:** Remove the original flat file now that all models have been moved to the subpackage.

**Why:** Single source of truth — models now live in `ccya/models/`.

**Validation:** `python -c "from ccya.models import TurnResult, load_config, ArcThread"` succeeds (imports resolve through `__init__.py`).

#### Step 1.8 — Verify all consumer imports

**What:** Check that every file that previously imported from `ccya.models` still resolves.

**Why:** The entire point of the re-export setup is zero consumer impact.

**Validation:**
```bash
for f in $(rg "^from ccya\.models import" ccya/ --type py -l); do
  python -c "import ast; ast.parse(open('$f').read())" || echo "Syntax error in $f"
done
# For each consumer, verify the import actually resolves at runtime:
grep "^from ccya\.models import" ccya/*.py ccya/**/*.py ccya/**/**/*.py 2>/dev/null | head -30
# Run each file's module through python -c "from ccya.models import <each symbol>"
python -c "
from ccya.models import (
    ArcThread, CampaignArc, Condition, ConditionAdd, ConditionRemove,
    InventoryItem, InventoryRemove, InventoryUpdate, LocationRef,
    NpcPresence, ProgressEntry, ThreadResolution, ThreadUpdate,
    ArcResolution, WorldStateFact, CompendiumNpcUpdate, GMBeat,
    SceneExtractResult, StateDelta, StateExtractResult, StorytellerResult,
    IntentEnvelope, RulesCheck, RulesOutcome, Band, Difficulty, SkillName,
    TurnResult, load_config, save_config,
    CompactorNpcMerge, CompactorSanitizationAction, CompactorSanitizationResult,
)
print('All models imported successfully')
"
```

### Tests to write or update

No tests — tests are temporarily removed. Validation relies on `make check` and import verification.

---

## Future work

After all 3 engine-split plans are complete, `docs/repomap.md` and `docs/architecture/OVERVIEW.md` must be updated to reflect new file paths. This is tracked in the turn-pipeline-split plan's final phase.
