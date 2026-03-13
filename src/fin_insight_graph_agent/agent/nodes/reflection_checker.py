from __future__ import annotations

from pydantic import BaseModel, Field

ABSOLUTE_CLAIM_MARKERS = (
    "definitely",
    "proves",
    "every",
    "always",
    "guarantee",
    "certainly",
)


class ReflectionReport(BaseModel):
    requires_revision: bool = False
    unsupported_claims: list[str] = Field(default_factory=list)


class ReflectionChecker:
    def check(self, draft_text: str, evidence_texts: list[str]) -> ReflectionReport:
        draft_lower = draft_text.lower()
        evidence_lower = " ".join(text.lower() for text in evidence_texts)
        unsupported_claims: list[str] = []

        for marker in ABSOLUTE_CLAIM_MARKERS:
            if marker in draft_lower and marker not in evidence_lower:
                unsupported_claims.append(marker)

        return ReflectionReport(
            requires_revision=bool(unsupported_claims),
            unsupported_claims=unsupported_claims,
        )