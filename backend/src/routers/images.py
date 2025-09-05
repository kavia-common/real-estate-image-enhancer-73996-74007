from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.config import get_settings
from src.core.db import get_db
from src.core.security import get_current_user
from src.models.models import Image, User
from src.schemas.schemas import ImageOut
from src.services.storage import StorageService
from src.services.usage import UsageService

router = APIRouter()
settings = get_settings()


# PUBLIC_INTERFACE
@router.post(
    "/upload",
    response_model=List[ImageOut],
    summary="Batch upload images",
    description="Upload up to MAX_BATCH_UPLOAD images. Saves metadata and returns stored objects.",
)
async def upload_images(
    files: List[UploadFile] = File(..., description="Image files"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Upload multiple images, store via storage backend, and record usage."""
    if len(files) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")
    if len(files) > settings.MAX_BATCH_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Batch too large. Max {settings.MAX_BATCH_UPLOAD}"
        )
    storage = StorageService()
    created: list[Image] = []
    for f in files:
        original_url = storage.save(await f.read().__await__(), f.filename)  # type: ignore
        # Since we used await f.read() we need to pass a bytes-like into save; wrap via memory
        # Quick fix: reopen bytes
        # Better: adjust save to accept bytes. For now, emulate a file-like.
        import io

        buf = io.BytesIO(await f.read())
        buf.seek(0)
        original_url = storage.save(buf, f.filename, subdir=str(user.id))
        image = Image(user_id=user.id, original_url=original_url, filename=f.filename, status="uploaded")
        db.add(image)
        created.append(image)
    usage = UsageService(db, user.id)
    await usage.add_usage(images_consumed=len(created), reason="upload")
    await db.flush()
    await db.commit()
    # refresh
    for img in created:
        await db.refresh(img)
    return created


# PUBLIC_INTERFACE
@router.get("", response_model=List[ImageOut], summary="List images", description="List images for the current user.")
async def list_images(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """List all images owned by the current user."""
    res = await db.execute(select(Image).where(Image.user_id == user.id).order_by(Image.created_at.desc()))
    return list(res.scalars().all())


# PUBLIC_INTERFACE
@router.get("/{image_id}", response_model=ImageOut, summary="Get image by id", description="Retrieve a single image metadata by id.")
async def get_image(image_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Get a single image ensuring it belongs to the current user."""
    res = await db.execute(select(Image).where(Image.id == image_id, Image.user_id == user.id))
    img = res.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return img
