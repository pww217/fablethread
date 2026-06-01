"""Re-export all state symbols so external import sites need no changes."""

from ccya.state.chronicle import (
    append_chronicle,
    append_event,
    load_last_narration,
    load_recent_turns,
    remove_last_chronicle_turn,
    remove_last_event,
)
from ccya.state.delta import (
    apply_delta,
    reconcile_delta,
)
from ccya.state.delta_builder import PC_CONDITIONS_MAX
from ccya.state.inventory import (
    normalize_inventory_id,
    resolve_inventory_canonical_id,
    resolve_inventory_remove_target,
)
from ccya.state.io import (
    init_save_dir,
    load_state,
    restore_snapshot_state,
    save_state,
    snapshot_state,
)
from ccya.state.npcs import (
    build_npc_alias_map,
    touch_compendium_order,
)
from ccya.state.momentum import apply_momentum

__all__ = [
    "append_chronicle",
    "append_event",
    "apply_delta",
    "apply_momentum",
    "build_npc_alias_map",
    "init_save_dir",
    "load_last_narration",
    "load_recent_turns",
    "load_state",
    "normalize_inventory_id",
    "PC_CONDITIONS_MAX",
    "remove_last_chronicle_turn",
    "remove_last_event",
    "reconcile_delta",
    "resolve_inventory_canonical_id",
    "resolve_inventory_remove_target",
    "restore_snapshot_state",
    "save_state",
    "snapshot_state",
    "touch_compendium_order",
]
