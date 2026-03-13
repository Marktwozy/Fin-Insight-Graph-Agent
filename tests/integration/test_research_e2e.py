from fastapi.testclient import TestClient

from apps.api.main import create_app


class ResearchGraph:
    def invoke(self, payload):
        return {
            "citations": [{"doc_id": "doc-1", "chunk_id": "chunk-1"}],
            "final_response": f"Grounded answer for {payload['question']}",
        }


class EventGraph:
    def invoke(self, payload):
        return {
            "citations": [{"doc_id": "doc-2", "chunk_id": "chunk-2"}],
            "final_response": f"Event analysis for {payload['event_input']}",
        }


class E2EContainer:
    research_graph = ResearchGraph()
    event_graph = EventGraph()


def test_research_e2e_returns_grounded_answer():
    client = TestClient(create_app(E2EContainer()))
    response = client.post(
        "/v1/query",
        json={"question": "Compare the latest risks for TSMC", "batch_id": "batch-20260313"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["citations"]
    assert body["trace_id"]
    assert "Grounded answer" in body["final_response"]