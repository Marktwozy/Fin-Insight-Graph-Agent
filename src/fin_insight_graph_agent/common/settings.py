from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FIGA_", extra="ignore")

    service_name: str = "fin-insight-graph-agent"
    environment: str = "local"
    log_level: str = "INFO"