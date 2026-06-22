from __future__ import annotations

from typing import Any


def cmd_compat(events: list[dict[str, Any]]) -> None:
    """Detect changes vs extraction_context format — identify which turns use which."""
    uses_changes: list[int] = []
    uses_extraction_context: list[int] = []
    uses_both: list[int] = []
    uses_neither: list[int] = []

    for ev in events:
        t = ev.get("turn")
        if t is None or not isinstance(t, int):
            continue

        extraction = ev.get("extraction") or {}
        if not isinstance(extraction, dict):
            uses_neither.append(t)
            continue

        has_changes = "changes" in extraction and extraction["changes"] is not None
        has_ec = "extraction_context" in extraction and extraction["extraction_context"] is not None

        if has_changes and has_ec:
            uses_both.append(t)
        elif has_changes:
            uses_changes.append(t)
        elif has_ec:
            uses_extraction_context.append(t)
        else:
            uses_neither.append(t)

    print("=== Format Compatibility ===")
    print(f"Uses 'changes' only:          {len(uses_changes)}")
    print(f"Uses 'extraction_context' only: {len(uses_extraction_context)}")
    print(f"Uses both:                     {len(uses_both)}")
    print(f"Uses neither:                  {len(uses_neither)}")
    print()

    if uses_changes:
        print(f"Turns using 'changes' ({len(uses_changes)}):")
        print(f"  {', '.join(str(t) for t in uses_changes)}")
        print()

    if uses_extraction_context:
        print(f"Turns using 'extraction_context' ({len(uses_extraction_context)}):")
        print(f"  {', '.join(str(t) for t in uses_extraction_context)}")
        print()

    if uses_both:
        print(f"Turns using both ({len(uses_both)}):")
        print(f"  {', '.join(str(t) for t in uses_both)}")
        print()

    if uses_neither:
        print(f"Turns using neither ({len(uses_neither)}):")
        print(f"  {', '.join(str(t) for t in uses_neither)}")
        print()

    # Check if checkers that need extraction_context will work
    if uses_changes and not uses_extraction_context:
        print("WARNING: This save uses 'changes' format exclusively.")
        print("Checkers that require 'extraction_context' will not find data:")
        print("  - conditions (needs extraction_context.conditions_this_turn)")
        print("  - inventory (needs extraction_context.inventory_this_turn, location_this_turn)")
        print("  - npc_presence (needs extraction_context)")
        print("  - pacing (needs extraction_context)")
        print("  - llm_checkers (needs extraction_context)")
