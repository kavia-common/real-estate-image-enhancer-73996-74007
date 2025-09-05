import stripe
import os
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

async def create_customer(email: str, name: str):
    try:
        customer = stripe.Customer.create(
            email=email,
            name=name
        )
        return customer.id
    except stripe.error.StripeError as e:
        raise ValueError(f"Error creating Stripe customer: {str(e)}")

async def create_subscription(customer_id: str, price_id: str):
    try:
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"]
        )
        return subscription
    except stripe.error.StripeError as e:
        raise ValueError(f"Error creating subscription: {str(e)}")

async def cancel_subscription(subscription_id: str):
    try:
        stripe.Subscription.delete(subscription_id)
    except stripe.error.StripeError as e:
        raise ValueError(f"Error canceling subscription: {str(e)}")
