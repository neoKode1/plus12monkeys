"""+12 Monkeys — Auth endpoints."""

from fastapi import APIRouter, HTTPException, Response, Request

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


@router.post("/send-key", response_model=SendKeyResponse)
async def send_key(body: SendKeyRequest):
    """Send a magic-link email. Always returns 200 (no email enumeration)."""
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
    db = get_db()
    user = await db.users.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")
    return MeResponse(email=user["email"], created_at=user["created_at"])


@router.post("/logout")
async def logout(response: Response):
    """Clear the session cookie."""
    response.delete_cookie(key=_COOKIE, path="/")
    return {"ok": True}

