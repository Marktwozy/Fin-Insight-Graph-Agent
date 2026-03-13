from fin_insight_graph_agent.ingestion.connectors.alpha_vantage import AlphaVantageClient


class FakeJsonTransport:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get_json(self, url, *, headers=None, params=None):
        self.calls.append({"url": url, "headers": headers or {}, "params": params or {}})
        return self.payload


def test_alpha_vantage_client_fetches_news_sentiment_feed():
    payload = {
        "feed": [
            {
                "title": "NVIDIA supplier capacity tightens",
                "url": "https://example.com/news/nvda-supply",
                "time_published": "20260313T120000",
                "summary": "Capacity remains tight across packaging suppliers.",
                "source": "Reuters",
            }
        ]
    }
    transport = FakeJsonTransport(payload)
    client = AlphaVantageClient(transport=transport, api_key="demo")

    feed = client.fetch_news_sentiment(["NVDA"], limit=20)

    assert feed[0].title == "NVIDIA supplier capacity tightens"
    assert transport.calls[0]["params"]["function"] == "NEWS_SENTIMENT"
    assert transport.calls[0]["params"]["tickers"] == "NVDA"
    assert transport.calls[0]["params"]["limit"] == "20"