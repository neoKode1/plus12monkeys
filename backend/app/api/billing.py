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

    purchased_uses = user.get("purchased_uses", 0)
    effective_limit = settings.free_usage_limit + purchased_uses

    return {
        "usage_count": usage_count,
        "plan": plan,
        "free_limit": effective_limit,
        "needs_upgrade": plan == "free" and usage_count >= effective_limit,
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

    # Admin users: unlimited, no usage tracking
    admin_list = [e.strip().lower() for e in settings.admin_emails.split(",") if e.strip()]
    if email.lower() in admin_list:
        return {"allowed": True, "usage_count": usage_count, "plan": "admin"}

    # Pro users: unlimited
    if plan == "pro":
        await db.users.update_one(
            {"email": email}, {"$inc": {"usage_count": 1}}
        )
        return {"allowed": True, "usage_count": usage_count + 1, "plan": "pro"}

    # Free users: check limit (include purchased single uses)
    purchased_uses = user.get("purchased_uses", 0)
    effective_limit = settings.free_usage_limit + purchased_uses
    if usage_count >= effective_limit:
        return {"allowed": False, "usage_count": usage_count, "plan": "free",
                "message": "Free limit reached. Upgrade to Pro or buy another use."}

    await db.users.update_one(
        {"email": email}, {"$inc": {"usage_count": 1}}
    )
    return {
        "allowed": True,
        "usage_count": usage_count + 1,
        "plan": "free",
        "remaining": settings.free_usage_limit - usage_count - 1,
    }


@router.post("/single-use-checkout")
async def create_single_use_checkout(request: Request):
    """Create a Stripe Checkout session for a one-time $1 use."""
    email = _get_user_email(request)
    s = _get_stripe()
    db = get_db()

    if not settings.stripe_single_use_price_id:
        raise HTTPException(status_code=500, detail="Single-use price not configured.")

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
        mode="payment",
        line_items=[{"price": settings.stripe_single_use_price_id, "quantity": 1}],
        success_url=f"{settings.frontend_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.frontend_url}/billing/cancel",
        metadata={"email": email, "type": "single_use"},
    )
    return {"url": session.url}


@router.post("/sync-usage")
async def sync_anonymous_usage(request: Request):
    """Transfer anonymous usage count to the authenticated user's record."""
    email = _get_user_email(request)
    db = get_db()

    body = await request.json()
    anon_count = int(body.get("anonymous_usage_count", 0))
    if anon_count < 0:
        anon_count = 0

    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    current_usage = user.get("usage_count", 0)
    # Only set if anonymous count is higher (don't decrease)
    new_count = max(current_usage, anon_count)
    await db.users.update_one(
        {"email": email},
        {"$set": {"usage_count": new_count}},
    )
    return {"usage_count": new_count}

