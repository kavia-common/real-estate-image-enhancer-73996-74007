from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.utils.security import get_db, get_current_active_user
from src.models.user import User
from src.utils.stripe_api import create_customer, create_subscription, cancel_subscription
from typing import Dict
import os
import stripe
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

SUBSCRIPTION_PRICES = {
    "basic": os.getenv("STRIPE_BASIC_PRICE_ID"),
    "pro": os.getenv("STRIPE_PRO_PRICE_ID"),
    "enterprise": os.getenv("STRIPE_ENTERPRISE_PRICE_ID")
}

@router.post("/subscription/create/{plan_type}")
async def create_subscription_payment(
    plan_type: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict:
    """Create a new subscription payment intent"""
    if plan_type not in SUBSCRIPTION_PRICES:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")

    try:
        # Create or get Stripe customer
        if not current_user.stripe_customer_id:
            customer_id = await create_customer(current_user.email, current_user.full_name)
            current_user.stripe_customer_id = customer_id
            db.commit()
        
        # Create subscription
        subscription = await create_subscription(
            current_user.stripe_customer_id,
            SUBSCRIPTION_PRICES[plan_type]
        )
        
        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/subscription/cancel")
async def cancel_user_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel user's current subscription"""
    if current_user.subscription_status != "active":
        raise HTTPException(status_code=400, detail="No active subscription found")

    try:
        # Get active subscription from Stripe
        stripe_subscriptions = stripe.Subscription.list(
            customer=current_user.stripe_customer_id,
            status="active"
        )

        if not stripe_subscriptions.data:
            raise HTTPException(status_code=400, detail="No active subscription found")

        # Cancel the subscription
        await cancel_subscription(stripe_subscriptions.data[0].id)

        # Update user status
        current_user.subscription_status = "inactive"
        db.commit()

        return {"message": "Subscription cancelled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/subscription/status")
async def get_subscription_status(
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """Get current user's subscription status"""
    return {
        "status": current_user.subscription_status,
        "trial_images_remaining": current_user.trial_images_remaining
    }
