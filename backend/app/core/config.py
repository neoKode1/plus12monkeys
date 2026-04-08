"""Application configuration via environment variables."""

import logging
import secrets

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Central configuration – reads from env vars / .env file."""

    # +12 Monkeys
    app_name: str = "+12 Monkeys"
    app_version: str = "0.2.0"
    debug: bool = False

    # NANDA Index
    nanda_url: str = "http://localhost:6900"

    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"

    # CORS — comma-separated origins (locked to production + local dev)
    cors_origins: str = "https://plus12monkeys.com,http://localhost:3000"

    # Sessions
    session_ttl_minutes: int = 1440  # 24 hours
    session_max_count: int = 500     # evict oldest when exceeded

    # Redis (optional — sessions persist across deploys when set)
    redis_url: str = ""  # e.g. redis://default:password@host:port

    # MongoDB
    mongodb_url: str = ""
    mongodb_db: str = "twelve_monkeys"

    # Auth
    resend_api_key: str = ""
    jwt_secret: str = ""  # REQUIRED — set JWT_SECRET env var (use: openssl rand -hex 32)
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 72  # 3 days
    magic_link_expire_minutes: int = 15
    auth_from_email: str = "keys@plus12monkeys.com"
    frontend_url: str = "https://plus12monkeys.com"

    # Admin — comma-separated list of admin emails
    admin_emails: str = "1deeptechnology@gmail.com"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = "price_1T5BZ0AwlxbzciUiqk8NALPG"
    stripe_single_use_price_id: str = ""
    free_usage_limit: int = 10

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# Guard: JWT secret must be set in production
if not settings.jwt_secret:
    if settings.debug:
        settings.jwt_secret = secrets.token_hex(32)
        logger.warning("JWT_SECRET not set — generated ephemeral secret (debug mode)")
    else:
        raise RuntimeError(
            "JWT_SECRET env var is required in production. "
            "Generate one with: openssl rand -hex 32"
        )

