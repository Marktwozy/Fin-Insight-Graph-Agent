from __future__ import annotations


def normalize_event(state: dict) -> dict:
    event_input = state.get("event_input", "").strip()
    normalized_event = " ".join(event_input.split())
    return {
        "normalized_event": normalized_event,
        "subquestions": [normalized_event] if normalized_event else [],
    }