from fin_insight_graph_agent.ingestion.connectors.sec_edgar import SecEdgarClient


class FakeJsonTransport:
    def __init__(self):
        self.calls = []

    def get_json(self, url, *, headers=None, params=None):
        self.calls.append({"url": url, "headers": headers or {}, "params": params or {}})
        return {"name": "NVIDIA CORP", "cik": "0001045810"}


def test_sec_edgar_client_fetches_submissions_with_padded_cik_and_user_agent():
    transport = FakeJsonTransport()
    client = SecEdgarClient(transport=transport, user_agent="FinInsight/1.0 (ops@example.com)")

    payload = client.fetch_submissions("1045810")

    assert payload["cik"] == "0001045810"
    assert transport.calls[0]["url"].endswith("/submissions/CIK0001045810.json")
    assert transport.calls[0]["headers"]["User-Agent"] == "FinInsight/1.0 (ops@example.com)"