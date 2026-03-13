from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FIGA_",
        extra="ignore",
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
    )

    service_name: str = "fin-insight-graph-agent"
    environment: str = "local"
    log_level: str = "INFO"
    sec_api_base_url: str = "https://data.sec.gov"
    sec_api_user_agent: str = "FinInsightGraphAgent/1.0 (research@example.com)"
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"
    alpha_vantage_api_key: str = "demo"
    evaluation_dataset_root: str = "D:/myAgent/.worktrees/fin-insight-v1/tests/fixtures/evaluation"
    graph_benchmark_suite: str = "graph_retrieval_smoke"
    model_api_base_url: str = "https://api.openai.com/v1"
    model_api_key: str = ""
    embedding_provider: str = "simple"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 16
    llm_provider: str = "heuristic"
    llm_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0.1
    reranker_provider: str = "heuristic"
    reranker_api_url: str = "http://127.0.0.1:8001/rerank"
    reranker_api_key: str = ""
    reranker_model: str = "bge-reranker-v2-m3"
    reranker_instruct: str = ""
    prompt_version: str = "prompt:v1"
    qdrant_collection_name: str = "chunks"