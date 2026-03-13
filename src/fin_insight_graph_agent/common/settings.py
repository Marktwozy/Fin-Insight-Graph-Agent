from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FIGA_", extra="ignore")

    service_name: str = "fin-insight-graph-agent"
    environment: str = "local"
    log_level: str = "INFO"
    sec_api_base_url: str = "https://data.sec.gov"
    sec_api_user_agent: str = "FinInsightGraphAgent/1.0 (research@example.com)"
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"
    alpha_vantage_api_key: str = "demo"