from pathlib import Path

from fin_insight_graph_agent.ingestion.market_loader import load_daily_bars


def test_load_daily_bars_parses_symbol_and_trade_date():
    sample_path = Path(
        "D:/myAgent/.worktrees/fin-insight-v1/tests/fixtures/market/sample_daily_bars.csv"
    )
    bars = load_daily_bars(sample_path)
    assert bars[0].ticker == "NVDA"
    assert str(bars[0].trade_date) == "2026-03-12"