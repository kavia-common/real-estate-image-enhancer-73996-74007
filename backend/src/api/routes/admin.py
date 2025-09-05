from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.utils.security import get_db, get_current_active_user
from src.models.user import User
from src.models.image import Image
from src.models.audit_log import AuditLog
from src.schemas import User as UserSchema, AuditLog as AuditLogSchema
from typing import List, Dict
from datetime import datetime, timedelta

router = APIRouter()

async def get_admin_user(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.get("/users", response_model=List[UserSchema])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all users with pagination"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/stats/usage", response_model=Dict)
async def get_usage_stats(
    days: int = 30,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get platform usage statistics"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Get total users
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.subscription_status == "active").count()
    trial_users = db.query(User).filter(User.subscription_status == "trial").count()
    
    # Get image processing stats
    total_images = db.query(Image).filter(Image.created_at >= since_date).count()
    pending_images = db.query(Image).filter(
        Image.status == "pending",
        Image.created_at >= since_date
    ).count()
    completed_images = db.query(Image).filter(
        Image.status == "completed",
        Image.created_at >= since_date
    ).count()
    failed_images = db.query(Image).filter(
        Image.status == "failed",
        Image.created_at >= since_date
    ).count()
    
    return {
        "users": {
            "total": total_users,
            "active_subscriptions": active_users,
            "trial": trial_users
        },
        "images": {
            "total_processed": total_images,
            "pending": pending_images,
            "completed": completed_images,
            "failed": failed_images
        }
    }

@router.get("/audit-logs", response_model=List[AuditLogSchema])
async def get_audit_logs(
    user_id: int = None,
    action: str = None,
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit logs with optional filtering"""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs

@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Toggle user active status"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    db.commit()
    
    return {"message": f"User status updated. Active: {user.is_active}"}
