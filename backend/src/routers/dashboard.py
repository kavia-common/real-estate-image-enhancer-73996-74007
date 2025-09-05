from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.security import get_current_user
from src.models.models import Image, Subscription, User
from src.schemas.schemas import DashboardSummary, ImageOut, SubscriptionOut, UsageSummary, UserOut
from src.services.usage import UsageService

router = APIRouter()


# PUBLIC_INTERFACE
@router.get("/summary", response_model=DashboardSummary, summary="Dashboard summary", description="Aggregated data for dashboard including user, usage, images, and subscriptions.")
async def dashboard_summary(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Return summary for the dashboard."""
    usage_service = UsageService(db, user.id)
    uploaded, edited = await usage_service.totals()
    trial_remaining = await usage_service.trial_remaining()

    # Recent images (limit 20)
    res_imgs = await db.execute(select(Image).where(Image.user_id == user.id).order_by(Image.created_at.desc()).limit(20))
    images = list(res_imgs.scalars().all())

    res_subs = await db.execute(select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.created_at.desc()))
    subscriptions = list(res_subs.scalars().all())

    return DashboardSummary(
        user=UserOut.model_validate(user, from_attributes=True),
        usage=UsageSummary(total_uploaded=uploaded, total_edited=edited, trial_remaining=trial_remaining),
        images=[ImageOut.model_validate(i, from_attributes=True) for i in images],
        subscriptions=[SubscriptionOut.model_validate(s, from_attributes=True) for s in subscriptions],
    )
