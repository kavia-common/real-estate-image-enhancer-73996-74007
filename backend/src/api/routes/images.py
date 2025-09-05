from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from src.utils.security import get_db, get_current_active_user
from src.models.user import User
from src.models.image import Image
from src.schemas import Image as ImageSchema
from typing import List
from datetime import datetime
import asyncio
from src.utils.google_api import process_image
from src.utils.audit import log_audit_event
from src.utils.file_handler import save_upload_file, delete_file
from src.utils.config import get_settings

router = APIRouter()
settings = get_settings()

@router.post("/images/upload", response_model=ImageSchema)
async def upload_image(
    file: UploadFile = File(...),
    edit_request: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and process a new image"""
    # Check trial/subscription status
    if current_user.subscription_status == "trial" and current_user.trial_images_remaining <= 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trial image limit reached. Please upgrade to continue."
        )
    elif current_user.subscription_status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required."
        )

    try:
        # Save the uploaded file
        file_path = await save_upload_file(file, current_user.id)

        # Create image record
        db_image = Image(
            user_id=current_user.id,
            original_url=file_path,
            edit_request=edit_request,
            status="pending"
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)

        # Update trial image count if applicable
        if current_user.subscription_status == "trial":
            current_user.trial_images_remaining -= 1
            db.commit()

        # Start async processing
        asyncio.create_task(process_image(db_image.id, file_path, edit_request))

        # Log audit event
        await log_audit_event(
            db=db,
            user_id=current_user.id,
            action="image_upload",
            details={"image_id": db_image.id, "original_filename": file.filename}
        )

        return db_image

    except HTTPException:
        raise
    except Exception as e:
        # Log the error and cleanup any uploaded file
        await delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/images", response_model=List[ImageSchema])
async def list_images(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List images for the current user with pagination"""
    return db.query(Image).filter(
        Image.user_id == current_user.id
    ).order_by(Image.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/images/{image_id}", response_model=ImageSchema)
async def get_image(
    image_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific image by ID"""
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == current_user.id
    ).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@router.delete("/images/{image_id}")
async def delete_image(
    image_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an image and its associated files"""
    image = db.query(Image).filter(
        Image.id == image_id,
        Image.user_id == current_user.id
    ).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        # Delete physical files
        await delete_file(image.original_url)
        if image.enhanced_url:
            await delete_file(image.enhanced_url)

        # Delete database record
        db.delete(image)
        db.commit()

        # Log audit event
        await log_audit_event(
            db=db,
            user_id=current_user.id,
            action="image_delete",
            details={"image_id": image_id}
        )

        return {"message": "Image deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image: {str(e)}"
        )
