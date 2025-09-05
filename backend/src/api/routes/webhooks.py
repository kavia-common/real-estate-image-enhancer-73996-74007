from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.orm import Session
from src.utils.security import get_db
from src.models.user import User
from src.utils.audit import log_audit_event
import stripe
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events for subscription management"""
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    signature = request.headers.get("stripe-signature")
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
    except:
        return Response(status_code=400)

    # Handle subscription events
    if event.type == "customer.subscription.updated":
        subscription = event.data.object
        user = db.query(User).filter(
            User.stripe_customer_id == subscription.customer
        ).first()
        
        if user:
            user.subscription_status = "active" if subscription.status == "active" else "inactive"
            db.commit()
            
            await log_audit_event(
                db=db,
                user_id=user.id,
                action="subscription_updated",
                details={"status": subscription.status}
            )
    
    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        user = db.query(User).filter(
            User.stripe_customer_id == subscription.customer
        ).first()
        
        if user:
            user.subscription_status = "inactive"
            db.commit()
            
            await log_audit_event(
                db=db,
                user_id=user.id,
                action="subscription_cancelled",
                details={"subscription_id": subscription.id}
            )
    
    return Response(status_code=200)
