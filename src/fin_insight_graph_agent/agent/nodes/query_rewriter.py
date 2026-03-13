from __future__ import annotations


def rewrite_query(state: dict) -> dict:
    question = state.get("question", "")
    return {"rewritten_question": question.strip()}