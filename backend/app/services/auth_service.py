"""+12 Monkeys — Auth service: magic-link tokens, JWT, email via Resend."""

import secrets
from datetime import datetime, timedelta, timezone

import jwt
import resend

from app.core.config import settings
from app.core.database import get_db


# ── Resend setup ──

def _init_resend() -> None:
    resend.api_key = settings.resend_api_key


# ── Token helpers ──


def _generate_token() -> str:
    return secrets.token_urlsafe(48)


def _create_jwt(email: str) -> str:
    payload = {
        "sub": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_jwt(token: str) -> dict | None:
    """Decode and validate a JWT. Returns payload dict or None."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ── Database operations ──


async def get_or_create_user(email: str) -> dict:
    """Find existing user or create a new one. Returns the user doc."""
    db = get_db()
    user = await db.users.find_one({"email": email})
    if user:
        return user
    doc = {
        "email": email,
        "created_at": datetime.now(timezone.utc),
        "last_login": None,
    }
    await db.users.insert_one(doc)
    return doc


async def create_magic_token(email: str) -> str:
    """Generate a magic-link token, store it, return the raw token."""
    db = get_db()
    token = _generate_token()
    doc = {
        "token": token,
        "email": email,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=settings.magic_link_expire_minutes),
        "used": False,
    }
    await db.magic_tokens.insert_one(doc)
    return token


async def verify_magic_token(token: str) -> str | None:
    """Verify a magic-link token. Returns the email if valid, else None."""
    db = get_db()
    doc = await db.magic_tokens.find_one({"token": token, "used": False})
    if not doc:
        return None
    if doc["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None
    # Mark as used
    await db.magic_tokens.update_one({"_id": doc["_id"]}, {"$set": {"used": True}})
    # Update last_login
    await db.users.update_one(
        {"email": doc["email"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}},
    )
    return doc["email"]


# ── Email ──


async def send_magic_email(email: str, token: str) -> None:
    """Send the 'Here's your key' email via Resend."""
    _init_resend()
    verify_url = f"{settings.frontend_url}/auth/verify?token={token}"
    resend.Emails.send({
        "from": settings.auth_from_email,
        "to": email,
        "subject": "Here's your key — +12 Monkeys",
        "html": _build_email_html(verify_url),
    })


def _build_email_html(verify_url: str) -> str:
    return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background-color:#f4f4f5;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f5;padding:40px 20px;">
    <tr><td align="center">
      <table width="420" cellpadding="0" cellspacing="0" style="background-color:#18181b;border-radius:8px;padding:40px 32px;">
        <tr><td align="center" style="padding-bottom:24px;">
          <span style="color:#a1a1aa;font-size:11px;letter-spacing:3px;text-transform:uppercase;font-family:monospace;">+12 MONKEYS</span>
        </td></tr>
        <tr><td align="center" style="padding-bottom:32px;">
          <span style="color:#e4e4e7;font-size:18px;">Here's your key.</span>
        </td></tr>
        <tr><td align="center" style="padding-bottom:32px;">
          <a href="{verify_url}"
             style="display:inline-block;padding:14px 40px;background-color:#3b82f6;color:#ffffff;
                    text-decoration:none;font-size:13px;letter-spacing:2px;text-transform:uppercase;
                    font-family:monospace;border-radius:4px;font-weight:bold;">
            ENTER &rarr;
          </a>
        </td></tr>
        <tr><td align="center">
          <span style="color:#71717a;font-size:11px;line-height:1.6;">
            Expires in {settings.magic_link_expire_minutes} minutes.<br/>
            If you didn't request this, ignore this transmission.
          </span>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

