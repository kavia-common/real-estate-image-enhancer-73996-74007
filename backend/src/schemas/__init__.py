from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    trial_images_remaining: int
    subscription_status: str
    created_at: datetime
    
    class Config:
        orm_mode = True

class ImageBase(BaseModel):
    edit_request: str

class ImageCreate(ImageBase):
    original_url: str

class Image(ImageBase):
    id: int
    user_id: int
    original_url: str
    enhanced_url: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class AuditLogCreate(BaseModel):
    action: str
    details: dict
    ip_address: str
    user_agent: str

class AuditLog(AuditLogCreate):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        orm_mode = True
