from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Message(BaseModel):
    message: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(default=None, description="Full name")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password, minimum length 8")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class ImageOut(BaseModel):
    id: int
    original_url: str
    processed_url: Optional[str]
    filename: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class EditRequest(BaseModel):
    prompt: str = Field(..., description="Natural language edit description")


class EditHistoryOut(BaseModel):
    id: int
    image_id: int
    prompt: str
    result_url: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    plan: str = Field(..., description="Plan identifier: trial | basic | pro")


class SubscriptionOut(BaseModel):
    id: int
    plan: str
    status: str
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UsageSummary(BaseModel):
    total_uploaded: int
    total_edited: int
    trial_remaining: int


class DashboardSummary(BaseModel):
    user: UserOut
    usage: UsageSummary
    images: List[ImageOut]
    subscriptions: List[SubscriptionOut]
