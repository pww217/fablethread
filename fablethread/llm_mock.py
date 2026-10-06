"""Mock LLM data and classes for MOCK_MODE testing."""
from __future__ import annotations

import json
from typing import Any


_MOCK_NARRATE = (
    "You step forward into the low-grav berth. The air is thin, the lights flicker. "
    "Your hand terminal buzzes again -- that encrypted pinger won't stop. "
    "A hauler drifts past, its cargo bay open to the ring. "
    "You need to find the signal source. The terminal buzzes insistently."
)

_MOCK_EXTRACT_NARRATE = {
    "state_delta": {
    },
    "actions": [
        "Open the encrypted pinger",
        "Drift toward the cargo bay",
        "Check the terminal for sender info",
        "Scan the berth for threats",
    ],
}

_MOCK_EXTRACT_EXAMINE = {
    "state_delta": {
    },
    "actions": [
        "Trace the shell company",
        "Contact the sender",
        "Ignore the pinger",
        "Step back from the terminal",
    ],
}

_MOCK_EXTRACT_CARGO = {
    "state_delta": {
        "location_change": {
            "id": "cargo-bay-7",
            "name": "Cargo Bay 7",
            "description": "Open cargo bay, crates stacked along the walls, smelling of lubricant.",
        },
    },
    "actions": [
        "Accept the hauler's offer",
        "Use the cargo bay terminal",
        "Rest and observe",
        "Decline and leave",
    ],
}


class _mock_stream:
    def __aiter__(self) -> _mock_stream:
        self._texts = list(_MOCK_NARRATE.split(". "))
        self._idx = 0
        return self

    async def __anext__(self) -> str:
        if self._idx >= len(self._texts):
            raise StopAsyncIteration
        val = self._texts[self._idx] + (
            ". " if self._idx < len(self._texts) - 1 else ""
        )
        self._idx += 1
        return val


def _mock_extract_chat(messages: list[dict[str, str]]) -> dict[str, Any]:
    narrative = ""
    for msg in messages:
        narrative += msg.get("content", "")

    if (
        "examine" in narrative.lower()
        or "terminal" in narrative.lower()
        or "pinger" in narrative.lower()
    ):
        body = _MOCK_EXTRACT_EXAMINE
    elif (
        "cargo" in narrative.lower()
        or "bay" in narrative.lower()
        or "haul" in narrative.lower()
    ):
        body = _MOCK_EXTRACT_CARGO
    else:
        body = _MOCK_EXTRACT_NARRATE
    return {
        "response": json.dumps(body),
        "done": True,
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }
