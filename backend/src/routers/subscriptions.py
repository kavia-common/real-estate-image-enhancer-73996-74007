from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.db import get_db
from src.core.security import get_current_user
from src.models.models import Subscription, User
from src.schemas.schemas import SubscriptionCreate, SubscriptionOut
from src.services.stripe_service import StripeService

router = APIRouter()
settings = get_settings()


# PUBLIC_INTERFACE
@router.post("", response_model=SubscriptionOut, summary="Create or update subscription", description="Create or update a subscription plan for the user and return the current subscription object.")
async def create_or_update_subscription(
    payload: SubscriptionCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Create or update a user subscription. In a real app, would integrate with Stripe subscriptions."""
    result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    sub = result.scalar_one_or_none()
    if sub:
        sub.plan = payload.plan
        sub.status = "active"
    else:
        sub = Subscription(user_id=user.id, plan=payload.plan, status="active")
        db.add(sub)
    await db.flush()
    await db.commit()
    await db.refresh(sub)
    return sub


# PUBLIC_INTERFACE
@router.get("", response_model=list[SubscriptionOut], summary="List subscriptions", description="List all subscriptions for the current user.")
async def list_subscriptions(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Return all subscriptions for the user."""
    res = await db.execute(select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.created_at.desc()))
    return list(res.scalars().all())


# PUBLIC_INTERFACE
@router.post("/checkout-session", response_model=dict, summary="Create Stripe checkout session", description="Create a checkout session for the given plan and return the session URL (stubbed).")
async def create_checkout_session(
    plan: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a checkout session (stub)."""
    price_id = settings.STRIPE_PRICE_BASIC if plan == "basic" else settings.STRIPE_PRICE_PRO
    if not price_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price not configured for plan")
    stripe = StripeService()
    success_url = (settings.SITE_URL or "http://localhost:3000") + "/billing/success"
    cancel_url = (settings.SITE_URL or "http://localhost:3000") + "/billing/cancel"
    session = stripe.create_checkout_session(price_id=price_id, customer_email=user.email, success_url=success_url, cancel_url=cancel_url)
    return session


# PUBLIC_INTERFACE
@router.post("/webhook", summary="Stripe webhook", description="Stripe webhook endpoint to process subscription events (stub).")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(default=None, alias="Stripe-Signature")):
    """Process Stripe webhooks (stub implementation)."""
    payload = await request.body()
    stripe = StripeService()
    try:
        event = stripe.verify_webhook(payload, stripe_signature or "")
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook")
    # Handle events (stub)
    return {"received": True, "event_type": event.get("type")}
