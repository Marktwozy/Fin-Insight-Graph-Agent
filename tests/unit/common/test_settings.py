from fin_insight_graph_agent.common.settings import AppSettings


def test_settings_reads_service_name_from_env(monkeypatch):
    monkeypatch.setenv("FIGA_SERVICE_NAME", "fin-insight-api")
    settings = AppSettings()
    assert settings.service_name == "fin-insight-api"