from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.db import get_db
from src.core.security import create_access_token, get_password_hash, verify_password
from src.models.models import User
from src.schemas.schemas import Token, UserCreate, UserLogin, UserOut

router = APIRouter()

settings = get_settings()


# PUBLIC_INTERFACE
@router.post("/register", response_model=UserOut, summary="Register a new user", description="Creates a new user account with email and password.")
async def register_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(email=payload.email, full_name=payload.full_name, password_hash=get_password_hash(payload.password))
    db.add(user)
    await db.flush()
    await db.commit()
    await db.refresh(user)
    return user


# PUBLIC_INTERFACE
@router.post("/login", response_model=Token, summary="Obtain JWT token", description="Authenticate using email and password and receive a Bearer token.")
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate a user and return an access token."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=user.email, expires_delta=access_token_expires)
    return Token(access_token=token)
