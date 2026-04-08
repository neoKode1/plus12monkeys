"""+12 Monkeys — Auth dependencies for protecting routes."""

import hashlib
import logging
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from app.services.auth_service import decode_jwt

logger = logging.getLogger(__name__)

_COOKIE = "twelve_monkeys_session"
_API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_auth(request: Request) -> str:
    """FastAPI dependency — returns the user email or raises 401."""
    token = request.cookies.get(_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired.")
    return payload["sub"]


async def require_api_key(
    api_key: str | None = Security(_API_KEY_HEADER),
) -> str:
    """FastAPI dependency — validates X-API-Key header against MongoDB.

    Returns the owner email associated with the key.
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header. Get one at https://plus12monkeys.com/settings/api-keys",
        )

    from app.core.database import get_db

    db = get_db()
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    doc = await db.api_keys.find_one({"key_hash": key_hash, "revoked": False})
    if not doc:
        raise HTTPException(status_code=403, detail="Invalid or revoked API key.")

    # Track last-used timestamp (fire-and-forget)
    await db.api_keys.update_one(
        {"_id": doc["_id"]},
        {"$set": {"last_used_at": datetime.now(timezone.utc)}, "$inc": {"use_count": 1}},
    )
    return doc["owner_email"]


def generate_api_key() -> str:
    """Generate a new API key with a recognizable prefix."""
    return f"p12m_{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    """Hash an API key for storage. Only the hash is stored in MongoDB."""
    return hashlib.sha256(key.encode()).hexdigest()

