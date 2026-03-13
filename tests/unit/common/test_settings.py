import shutil
from pathlib import Path

from fin_insight_graph_agent.common.settings import AppSettings


def test_settings_reads_service_name_from_env(monkeypatch):
    monkeypatch.setenv("FIGA_SERVICE_NAME", "fin-insight-api")
    settings = AppSettings()
    assert settings.service_name == "fin-insight-api"


def test_settings_prefers_dot_env_local_over_dot_env():
    temp_root = Path("D:/myAgent/.worktrees/fin-insight-v1/tests/.tmp/settings-env")
    if temp_root.exists():
        shutil.rmtree(temp_root)
    temp_root.mkdir(parents=True)

    env_file = temp_root / ".env"
    env_local_file = temp_root / ".env.local"
    env_file.write_text("FIGA_LLM_PROVIDER=heuristic\n", encoding="utf-8")
    env_local_file.write_text("FIGA_LLM_PROVIDER=openai_compatible\n", encoding="utf-8")

    try:
        settings = AppSettings(_env_file=(env_file, env_local_file))
        assert settings.llm_provider == "openai_compatible"
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
