"""+12 Monkeys — Auth endpoints."""

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.auth_middleware import generate_api_key, hash_api_key, require_auth
from app.models.auth import (
    SendKeyRequest,
    SendKeyResponse,
    VerifyRequest,
    VerifyResponse,
    MeResponse,
)
from app.services.auth_service import (
    get_or_create_user,
    create_magic_token,
    verify_magic_token,
    send_magic_email,
    _create_jwt,
    decode_jwt,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE = "twelve_monkeys_session"
_COOKIE_MAX_AGE = 60 * 60 * 72  # 3 days

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

limiter = Limiter(key_func=get_remote_address)


@router.post("/send-key", response_model=SendKeyResponse)
@limiter.limit("5/minute")
async def send_key(request: Request, body: SendKeyRequest):
    """Send a magic-link email. Always returns 200 (no email enumeration)."""
    if not _EMAIL_RE.match(body.email):
        return SendKeyResponse()  # fail silently — no enumeration
    try:
        await get_or_create_user(body.email)
        token = await create_magic_token(body.email)
        await send_magic_email(body.email, token)
    except Exception:
        pass  # Fail silently — don't leak whether the email exists
    return SendKeyResponse()


@router.post("/verify", response_model=VerifyResponse)
async def verify(body: VerifyRequest, response: Response):
    """Verify a magic-link token and set a session cookie."""
    email = await verify_magic_token(body.token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired key.")
    jwt_token = _create_jwt(email)
    response.set_cookie(
        key=_COOKIE,
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        path="/",
    )
    return VerifyResponse(email=email)


@router.get("/me", response_model=MeResponse)
async def me(request: Request):
    """Return the current authenticated user."""
    token = request.cookies.get(_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired.")
    from app.core.database import get_db
    from app.core.config import settings
    db = get_db()
    user = await db.users.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    admin_list = [e.strip().lower() for e in settings.admin_emails.split(",") if e.strip()]
    return MeResponse(
        email=user["email"],
        created_at=user["created_at"],
        is_admin=user["email"].lower() in admin_list,
        usage_count=user.get("usage_count", 0),
        plan=user.get("plan", "free"),
        subscription_expires_at=user.get("subscription_expires_at"),
    )


@router.post("/logout")
async def logout(response: Response):
    """Clear the session cookie."""
    response.delete_cookie(key=_COOKIE, path="/", samesite="lax", secure=True)
    return {"ok": True}


# ── API Key Management ──


class CreateApiKeyRequest(BaseModel):
    name: str = "default"


class ApiKeyResponse(BaseModel):
    key: str
    name: str
    created_at: datetime


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    body: CreateApiKeyRequest,
    email: str = Depends(require_auth),
):
    """Create a new API key for the authenticated user.

    The raw key is returned ONCE. Only the hash is stored.
    """
    from app.core.database import get_db

    db = get_db()
    raw_key = generate_api_key()
    now = datetime.now(timezone.utc)
    await db.api_keys.insert_one({
        "key_hash": hash_api_key(raw_key),
        "owner_email": email,
        "name": body.name,
        "created_at": now,
        "last_used_at": None,
        "use_count": 0,
        "revoked": False,
    })
    return ApiKeyResponse(key=raw_key, name=body.name, created_at=now)


@router.delete("/api-keys/{key_hash}")
async def revoke_api_key(
    key_hash: str,
    email: str = Depends(require_auth),
):
    """Revoke an API key (soft delete)."""
    from app.core.database import get_db

    db = get_db()
    result = await db.api_keys.update_one(
        {"key_hash": key_hash, "owner_email": email, "revoked": False},
        {"$set": {"revoked": True, "revoked_at": datetime.now(timezone.utc)}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="API key not found.")
    return {"ok": True}


@router.get("/api-keys")
async def list_api_keys(email: str = Depends(require_auth)):
    """List all API keys for the authenticated user (hashes only, not raw keys)."""
    from app.core.database import get_db

    db = get_db()
    cursor = db.api_keys.find(
        {"owner_email": email, "revoked": False},
        {"_id": 0, "key_hash": 1, "name": 1, "created_at": 1, "last_used_at": 1, "use_count": 1},
    )
    keys = await cursor.to_list(length=50)
    return {"keys": keys}

