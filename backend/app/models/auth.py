"""+12 Monkeys — Auth models."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Request / Response schemas ──


class SendKeyRequest(BaseModel):
    """Body for POST /auth/send-key."""
    email: EmailStr


class SendKeyResponse(BaseModel):
    ok: bool = True
    message: str = "If that email is valid, a key has been sent."


class VerifyRequest(BaseModel):
    """Body for POST /auth/verify."""
    token: str


class VerifyResponse(BaseModel):
    ok: bool = True
    email: str


class MeResponse(BaseModel):
    email: str
    created_at: datetime
    usage_count: int = 0
    plan: str = "free"  # "free" or "pro"
    subscription_expires_at: datetime | None = None


# ── MongoDB document shapes (not exposed directly) ──


class UserDoc(BaseModel):
    """Shape of a user document in the `users` collection."""
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime | None = None
    usage_count: int = 0
    plan: str = "free"
    stripe_customer_id: str | None = None
    subscription_expires_at: datetime | None = None


class MagicTokenDoc(BaseModel):
    """Shape of a magic-link token in the `magic_tokens` collection."""
    token: str
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    used: bool = False

