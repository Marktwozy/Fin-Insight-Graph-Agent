from fin_insight_graph_agent.ingestion.connectors.alpha_vantage import AlphaVantageClient


class FakeTextTransport:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def get_text(self, url, *, headers=None, params=None):
        self.calls.append({"url": url, "headers": headers or {}, "params": params or {}})
        return self.text


def test_alpha_vantage_client_parses_daily_adjusted_csv():
    csv_text = (
        "timestamp,open,high,low,close,adjusted_close,volume,dividend_amount,"
        "split_coefficient\n"
        "2026-03-13,118.00,120.00,117.50,119.50,119.50,1200000,0.0000,1.0\n"
    )
    transport = FakeTextTransport(csv_text)
    client = AlphaVantageClient(transport=transport, api_key="demo")

    bars = client.fetch_daily_adjusted("NVDA")

    assert bars[0].ticker == "NVDA"
    assert str(bars[0].trade_date) == "2026-03-13"
    assert transport.calls[0]["params"]["function"] == "TIME_SERIES_DAILY_ADJUSTED"
    assert transport.calls[0]["params"]["datatype"] == "csv"