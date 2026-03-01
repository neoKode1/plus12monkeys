"""+12 Monkeys — Stripe webhook handler."""

from datetime import datetime, timezone, timedelta

import stripe
from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["webhook"])


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    stripe.api_key = settings.stripe_secret_key

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    db = get_db()

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")

        # Idempotency check — skip if already processed
        if session_id:
            existing = await db.stripe_events.find_one({"session_id": session_id})
            if existing:
                return {"received": True}
            await db.stripe_events.insert_one({
                "session_id": session_id,
                "event_type": event["type"],
                "processed_at": datetime.now(timezone.utc),
            })

        email = session.get("metadata", {}).get("email")
        payment_type = session.get("metadata", {}).get("type", "")

        if email and payment_type == "single_use":
            # One-time $1 payment — grant 1 additional use
            await db.users.update_one(
                {"email": email},
                {
                    "$inc": {"purchased_uses": 1},
                    "$set": {"stripe_customer_id": session.get("customer")},
                },
            )
        elif email:
            # Subscription — set plan to pro
            await db.users.update_one(
                {"email": email},
                {"$set": {
                    "plan": "pro",
                    "subscription_expires_at": datetime.now(timezone.utc) + timedelta(days=365),
                    "stripe_customer_id": session.get("customer"),
                }},
            )

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        customer_id = sub.get("customer")
        if customer_id:
            await db.users.update_one(
                {"stripe_customer_id": customer_id},
                {"$set": {"plan": "free"}},
            )

    return {"received": True}

