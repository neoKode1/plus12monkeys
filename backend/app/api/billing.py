"""+12 Monkeys — Billing endpoints (Stripe integration)."""

from datetime import datetime, timezone

import stripe
from fastapi import APIRouter, HTTPException, Request, Response

from app.core.config import settings
from app.core.database import get_db
from app.services.auth_service import decode_jwt

router = APIRouter(prefix="/billing", tags=["billing"])

_COOKIE = "twelve_monkeys_session"


def _get_stripe():
    """Initialize and return stripe module."""
    stripe.api_key = settings.stripe_secret_key
    return stripe


def _get_user_email(request: Request) -> str:
    """Extract email from session cookie."""
    token = request.cookies.get(_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Session expired.")
    return payload["sub"]


@router.post("/checkout")
async def create_checkout_session(request: Request):
    """Create a Stripe Checkout session for the $10/year Pro plan."""
    email = _get_user_email(request)
    s = _get_stripe()
    db = get_db()

    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Get or create Stripe customer
    customer_id = user.get("stripe_customer_id")
    if not customer_id:
        customer = s.Customer.create(email=email)
        customer_id = customer.id
        await db.users.update_one(
            {"email": email},
            {"$set": {"stripe_customer_id": customer_id}},
        )

    session = s.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        success_url=f"{settings.frontend_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.frontend_url}/billing/cancel",
        metadata={"email": email},
    )
    return {"url": session.url}


@router.get("/status")
async def billing_status(request: Request):
    """Return current usage and billing status."""
    email = _get_user_email(request)
    db = get_db()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    usage_count = user.get("usage_count", 0)
    plan = user.get("plan", "free")
    expires = user.get("subscription_expires_at")

    # Check if pro subscription has expired
    if plan == "pro" and expires and expires < datetime.now(timezone.utc):
        await db.users.update_one(
            {"email": email},
            {"$set": {"plan": "free"}},
        )
        plan = "free"

    return {
        "usage_count": usage_count,
        "plan": plan,
        "free_limit": settings.free_usage_limit,
        "needs_upgrade": plan == "free" and usage_count >= settings.free_usage_limit,
        "subscription_expires_at": expires.isoformat() if expires else None,
    }


@router.post("/use")
async def increment_usage(request: Request):
    """Increment usage count. Returns whether the user can continue."""
    email = _get_user_email(request)
    db = get_db()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    plan = user.get("plan", "free")
    usage_count = user.get("usage_count", 0)

    # Pro users: unlimited
    if plan == "pro":
        await db.users.update_one(
            {"email": email}, {"$inc": {"usage_count": 1}}
        )
        return {"allowed": True, "usage_count": usage_count + 1, "plan": "pro"}

    # Free users: check limit
    if usage_count >= settings.free_usage_limit:
        return {"allowed": False, "usage_count": usage_count, "plan": "free",
                "message": "Free limit reached. Upgrade to Pro."}

    await db.users.update_one(
        {"email": email}, {"$inc": {"usage_count": 1}}
    )
    return {
        "allowed": True,
        "usage_count": usage_count + 1,
        "plan": "free",
        "remaining": settings.free_usage_limit - usage_count - 1,
    }

