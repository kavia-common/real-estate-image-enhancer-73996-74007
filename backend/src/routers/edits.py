from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.security import get_current_user
from src.models.models import EditHistory, Image, User
from src.schemas.schemas import EditHistoryOut, EditRequest
from src.services.usage import UsageService

router = APIRouter()


# PUBLIC_INTERFACE
@router.post("/{image_id}/request", response_model=EditHistoryOut, summary="Request an edit", description="Create a natural language edit request for an image.")
async def request_edit(
    image_id: int, payload: EditRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """Create an edit history entry for an image and record usage."""
    res = await db.execute(select(Image).where(Image.id == image_id, Image.user_id == user.id))
    img = res.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    edit = EditHistory(image_id=image_id, prompt=payload.prompt, status="queued")
    db.add(edit)
    usage = UsageService(db, user.id)
    await usage.add_usage(images_consumed=1, reason="edit", notes=f"image:{image_id}")
    await db.flush()
    await db.commit()
    await db.refresh(edit)
    return edit


# PUBLIC_INTERFACE
@router.get("/{image_id}/history", response_model=list[EditHistoryOut], summary="Get edit history", description="List all edit history records for an image.")
async def edit_history(image_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """List edit history for an image, validating ownership."""
    res = await db.execute(select(Image).where(Image.id == image_id, Image.user_id == user.id))
    img = res.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    res2 = await db.execute(select(EditHistory).where(EditHistory.image_id == image_id).order_by(EditHistory.created_at.desc()))
    return list(res2.scalars().all())
