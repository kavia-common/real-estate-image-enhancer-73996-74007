from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.models.models import UsageLog

settings = get_settings()


class UsageService:
    """Usage tracking and trial computation."""

    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id

    # PUBLIC_INTERFACE
    async def add_usage(self, images_consumed: int, reason: str, notes: str | None = None) -> None:
        """Record usage for a user."""
        log = UsageLog(user_id=self.user_id, images_consumed=images_consumed, reason=reason, notes=notes)
        self.db.add(log)
        await self.db.flush()

    # PUBLIC_INTERFACE
    async def trial_remaining(self) -> int:
        """Compute remaining trial image credits based on total consumed."""
        total_consumed = await self._total_consumed()
        remaining = max(0, settings.TRIAL_IMAGE_CREDITS - total_consumed)
        return remaining

    # PUBLIC_INTERFACE
    async def totals(self) -> tuple[int, int]:
        """Return (uploaded_total, edited_total)."""
        uploaded = await self._sum_by_reason("upload")
        edited = await self._sum_by_reason("edit")
        return uploaded, edited

    async def _total_consumed(self) -> int:
        q = await self.db.execute(select(func.coalesce(func.sum(UsageLog.images_consumed), 0)).where(UsageLog.user_id == self.user_id))
        return int(q.scalar_one())

    async def _sum_by_reason(self, reason: str) -> int:
        q = await self.db.execute(
            select(func.coalesce(func.sum(UsageLog.images_consumed), 0)).where(
                UsageLog.user_id == self.user_id, UsageLog.reason == reason
            )
        )
        return int(q.scalar_one())
