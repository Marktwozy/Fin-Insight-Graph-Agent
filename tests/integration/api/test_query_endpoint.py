from fastapi.testclient import TestClient

from apps.api.main import create_app


class FakeGraph:
    def __init__(self, response):
        self._response = response

    def invoke(self, payload):
        return self._response | payload


class FakeContainer:
    def __init__(self):
        self.research_graph = FakeGraph(
            {
                "citations": [{"doc_id": "doc-1", "chunk_id": "chunk-1"}],
                "final_response": "TSMC risks may affect packaging capacity.",
            }
        )
        self.event_graph = FakeGraph(
            {
                "citations": [{"doc_id": "doc-2", "chunk_id": "chunk-2"}],
                "final_response": "Event impact may spread to downstream firms.",
            }
        )


def test_query_endpoint_returns_trace_metadata():
    app = create_app(FakeContainer())
    client = TestClient(app)
    response = client.post(
        "/v1/query",
        json={"question": "Summarize TSMC risks", "batch_id": "batch-20260313"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["trace_id"]
    assert body["citations"] == [{"doc_id": "doc-1", "chunk_id": "chunk-1"}]