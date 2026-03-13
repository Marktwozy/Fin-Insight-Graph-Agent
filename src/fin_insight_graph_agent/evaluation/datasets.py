from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    case_id: str
    question: str
    reference_answer: str
    response: str
    contexts: list[str] = Field(default_factory=list)
    citations: list[dict[str, str]] = Field(default_factory=list)
    batch_id: str = ""


SUITE_TO_FILE = {
    "research_smoke": "research_cases.jsonl",
    "event_smoke": "event_cases.jsonl",
}


def load_suite(dataset_root: str | Path, suite_name: str) -> list[EvaluationCase]:
    file_name = SUITE_TO_FILE[suite_name]
    suite_path = Path(dataset_root) / file_name
    rows: list[EvaluationCase] = []
    for line in suite_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(EvaluationCase.model_validate(json.loads(line)))
    return rows