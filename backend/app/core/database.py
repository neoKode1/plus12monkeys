"""+12 Monkeys — Async MongoDB connection via Motor."""

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


def get_db() -> AsyncIOMotorDatabase:
    """Return the database handle, creating the client on first call."""
    global _client
    if _client is None:
        if not settings.mongodb_url:
            raise RuntimeError("MONGODB_URL is not set")
        _client = AsyncIOMotorClient(settings.mongodb_url)
    return _client[settings.mongodb_db]


async def ensure_indexes() -> None:
    """Create required MongoDB indexes (idempotent)."""
    db = get_db()
    try:
        await db.users.create_index("email", unique=True)
        await db.magic_tokens.create_index("token", unique=True)
        # TTL index — auto-delete expired tokens
        await db.magic_tokens.create_index("expires_at", expireAfterSeconds=0)
        # Idempotency index for processed Stripe events
        await db.stripe_events.create_index("session_id", unique=True)
        # API key lookup by hash
        await db.api_keys.create_index("key_hash", unique=True)
        await db.api_keys.create_index("owner_email")
        logger.info("MongoDB indexes ensured")
    except Exception as exc:
        logger.warning("Failed to create indexes: %s", exc)


async def close_db() -> None:
    """Close the MongoDB client (call on shutdown)."""
    global _client
    if _client is not None:
        _client.close()
        _client = None

