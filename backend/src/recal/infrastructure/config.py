from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "recal-api"
    app_version: str = "0.1.0"
    log_level: str = "INFO"

    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-haiku-4-5-20251001-v1:0"
    tavily_api_key: str = ""
    tavily_max_results: int = 5

    dynamodb_table_opportunities: str = "recal-opportunities-dev"
    dynamodb_table_profiles: str = "recal-profiles-dev"
    dynamodb_table_runs: str = "recal-runs-dev"

    agent_max_tool_calls: int = 3
    agent_timeout_seconds: int = 60
    relevance_threshold_default: float = 70

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
