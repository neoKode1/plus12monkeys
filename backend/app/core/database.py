"""+12 Monkeys — Async MongoDB connection via Motor."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_db() -> AsyncIOMotorDatabase:
    """Return the database handle, creating the client on first call."""
    global _client
    if _client is None:
        if not settings.mongodb_url:
            raise RuntimeError("MONGODB_URL is not set")
        _client = AsyncIOMotorClient(settings.mongodb_url)
    return _client[settings.mongodb_db]


async def close_db() -> None:
    """Close the MongoDB client (call on shutdown)."""
    global _client
    if _client is not None:
        _client.close()
        _client = None

