"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration – reads from env vars / .env file."""

    # +12 Monkeys
    app_name: str = "+12 Monkeys"
    app_version: str = "0.1.0"
    debug: bool = False

    # NANDA Index
    nanda_url: str = "http://localhost:6900"

    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"

    # CORS — comma-separated origins; "*" allows all (dev only)
    cors_origins: str = "*"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

