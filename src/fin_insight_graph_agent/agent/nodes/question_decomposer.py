from __future__ import annotations


def decompose_question(state: dict) -> dict:
    rewritten_question = state.get("rewritten_question") or state.get("question", "")
    return {"subquestions": [rewritten_question] if rewritten_question else []}