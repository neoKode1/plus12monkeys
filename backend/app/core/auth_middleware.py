"""+12 Monkeys — Auth dependency for protecting routes."""

from fastapi import HTTPException, Request

from app.services.auth_service import decode_jwt

_COOKIE = "twelve_monkeys_session"


async def require_auth(request: Request) -> str:
    """FastAPI dependency — returns the user email or raises 401."""
    token = request.cookies.get(_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired.")
    return payload["sub"]

