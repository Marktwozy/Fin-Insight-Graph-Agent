from __future__ import annotations


def apply_revision(state: dict) -> dict:
    report = state.get("reflection_report")
    final_response = state.get("draft_response") or state.get("final_response", "")
    if report and getattr(report, "requires_revision", False):
        revised = final_response
        replacements = {
            "definitely": "may",
            "proves": "suggests",
            "every": "some",
            "always": "often",
            "guarantee": "indicate",
            "certainly": "likely",
        }
        for source, target in replacements.items():
            revised = revised.replace(source, target)
            revised = revised.replace(source.capitalize(), target.capitalize())
        final_response = revised
    return {"final_response": final_response}