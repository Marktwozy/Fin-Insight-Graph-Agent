from fastapi.testclient import TestClient

from apps.api.main import create_app


class FakeGraph:
    def invoke(self, payload):
        return {
            "citations": [{"doc_id": "doc-1", "chunk_id": "chunk-1"}],
            "final_response": f"Response for {payload.get('question', '')}".strip(),
        }


class FakeContainer:
    research_graph = FakeGraph()
    event_graph = FakeGraph()


def test_trace_id_propagates_through_query_response():
    app = create_app(FakeContainer())
    client = TestClient(app)
    response = client.post(
        "/v1/query",
        json={"question": "Summarize TSMC risks", "batch_id": "batch-20260313"},
    )
    body = response.json()

    assert response.status_code == 200
    assert response.headers["x-trace-id"] == body["trace_id"]