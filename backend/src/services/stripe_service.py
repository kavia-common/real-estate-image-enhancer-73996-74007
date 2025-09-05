from src.core.config import get_settings

settings = get_settings()


class StripeService:
    """Stubbed Stripe service. Replace with real stripe integration using stripe SDK."""

    def __init__(self):
        self.api_key = settings.STRIPE_API_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    # PUBLIC_INTERFACE
    def create_checkout_session(self, price_id: str, customer_email: str, success_url: str, cancel_url: str) -> dict:
        """Create a checkout session (stub)."""
        # Real implementation would call stripe.checkout.Session.create(...)
        return {
            "id": "cs_test_dummy",
            "url": f"{success_url}?session=cs_test_dummy",
            "price_id": price_id,
            "customer_email": customer_email,
        }

    # PUBLIC_INTERFACE
    def verify_webhook(self, payload: bytes, sig_header: str) -> dict:
        """Verify webhook signature and parse event (stub)."""
        # Real implementation would use stripe.Webhook.construct_event(...)
        return {"type": "invoice.paid", "data": {"object": {"id": "in_dummy"}}}
