from __future__ import annotations

from typing import Any

from fin_insight_graph_agent.common.settings import AppSettings
from fin_insight_graph_agent.ingestion.connectors.http_transport import HttpTransport
from fin_insight_graph_agent.retrieval.embeddings import _authorization_headers


class OpenAICompatibleChatClient:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str = "",
        temperature: float = 0.1,
        transport: HttpTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self.model = model
        self._api_key = api_key
        self._temperature = temperature
        self._transport = transport or HttpTransport()

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._transport.post_json(
            f"{self._base_url}/chat/completions",
            payload={
                "model": self.model,
                "temperature": self._temperature,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            headers=_authorization_headers(self._api_key),
        )
        message = response["choices"][0]["message"]["content"]
        if isinstance(message, list):
            return "\n".join(str(part.get("text", "")) for part in message)
        return str(message)


class HeuristicResponseGenerator:
    def __init__(self, *, prompt_version: str = "prompt:v1") -> None:
        self.prompt_version = prompt_version
        self.model_version = "heuristic"

    def generate_research_answer(self, *, question: str, evidence_texts: list[str]) -> str:
        if evidence_texts:
            return " ".join(evidence_texts[:2])
        return "No grounded evidence found."

    def generate_event_answer(self, *, event_input: str, evidence_texts: list[str]) -> str:
        if evidence_texts:
            lead = evidence_texts[0].strip()
            prefix = "Based on the retrieved evidence, this event may affect downstream exposure."
            return f"{prefix} {lead}"
        return "No grounded evidence found for this event yet."


class OpenAICompatibleResponseGenerator:
    def __init__(self, *, client: OpenAICompatibleChatClient, prompt_version: str) -> None:
        self._client = client
        self.prompt_version = prompt_version
        self.model_version = f"openai-compatible:{client.model}"

    def generate_research_answer(self, *, question: str, evidence_texts: list[str]) -> str:
        evidence_block = _format_evidence(evidence_texts)
        return self._client.complete(
            system_prompt=(
                "You are a grounded financial research assistant. Answer only from the "
                "provided evidence and stay cautious when evidence is incomplete."
            ),
            user_prompt=(
                f"Question: {question}\n\n"
                f"Evidence:\n{evidence_block}\n\n"
                "Provide a concise grounded answer."
            ),
        )

    def generate_event_answer(self, *, event_input: str, evidence_texts: list[str]) -> str:
        evidence_block = _format_evidence(evidence_texts)
        return self._client.complete(
            system_prompt=(
                "You are a grounded event-impact analyst. Use only the supplied evidence "
                "and explain impacts cautiously."
            ),
            user_prompt=(
                f"Event: {event_input}\n\n"
                f"Evidence:\n{evidence_block}\n\n"
                "Summarize likely downstream impact using only this evidence."
            ),
        )


def build_response_generator(settings: AppSettings) -> Any:
    if settings.llm_provider == "openai_compatible":
        client = OpenAICompatibleChatClient(
            base_url=settings.model_api_base_url,
            model=settings.llm_model,
            api_key=settings.model_api_key,
            temperature=settings.llm_temperature,
        )
        return OpenAICompatibleResponseGenerator(
            client=client,
            prompt_version=settings.prompt_version,
        )
    return HeuristicResponseGenerator(prompt_version=settings.prompt_version)


def _format_evidence(evidence_texts: list[str]) -> str:
    if not evidence_texts:
        return "- No evidence retrieved."
    return "\n".join(f"- {text}" for text in evidence_texts[:6])