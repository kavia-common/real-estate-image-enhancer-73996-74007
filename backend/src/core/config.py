import functools
import os
from typing import Optional

from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    ENV: str = Field(default=os.getenv("ENV", "development"), description="Environment name")
    LOG_LEVEL: str = Field(default=os.getenv("LOG_LEVEL", "INFO"), description="Logging level")

    # Database
    DATABASE_URL: Optional[str] = Field(
        default=os.getenv("DATABASE_URL"),
        description="SQLAlchemy Database URL (e.g., postgresql+psycopg://user:pass@host:port/dbname)",
    )
    DB_POOL_SIZE: int = Field(default=int(os.getenv("DB_POOL_SIZE", "5")))
    DB_MAX_OVERFLOW: int = Field(default=int(os.getenv("DB_MAX_OVERFLOW", "10")))

    # Auth / Security
    JWT_SECRET_KEY: str = Field(default=os.getenv("JWT_SECRET_KEY", "change-me"))
    JWT_ALGORITHM: str = Field(default=os.getenv("JWT_ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")))
    PASSWORD_HASH_SCHEME: str = Field(default=os.getenv("PASSWORD_HASH_SCHEME", "bcrypt"))

    # File storage (stubbed S3/local)
    STORAGE_BACKEND: str = Field(default=os.getenv("STORAGE_BACKEND", "local"))  # local | s3
    LOCAL_STORAGE_PATH: str = Field(default=os.getenv("LOCAL_STORAGE_PATH", "./data/uploads"))
    S3_BUCKET_NAME: Optional[str] = Field(default=os.getenv("S3_BUCKET_NAME"))
    S3_REGION: Optional[str] = Field(default=os.getenv("S3_REGION"))
    S3_ENDPOINT_URL: Optional[str] = Field(default=os.getenv("S3_ENDPOINT_URL"))
    S3_ACCESS_KEY_ID: Optional[str] = Field(default=os.getenv("S3_ACCESS_KEY_ID"))
    S3_SECRET_ACCESS_KEY: Optional[str] = Field(default=os.getenv("S3_SECRET_ACCESS_KEY"))

    # Stripe (stub integration)
    STRIPE_API_KEY: Optional[str] = Field(default=os.getenv("STRIPE_API_KEY"))
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=os.getenv("STRIPE_WEBHOOK_SECRET"))
    STRIPE_PRICE_BASIC: Optional[str] = Field(default=os.getenv("STRIPE_PRICE_BASIC"))
    STRIPE_PRICE_PRO: Optional[str] = Field(default=os.getenv("STRIPE_PRICE_PRO"))

    # Trials and limits
    TRIAL_IMAGE_CREDITS: int = Field(default=int(os.getenv("TRIAL_IMAGE_CREDITS", "10")))
    MAX_BATCH_UPLOAD: int = Field(default=int(os.getenv("MAX_BATCH_UPLOAD", "30")))

    # CORS
    CORS_ALLOW_ORIGINS: str = Field(default=os.getenv("CORS_ALLOW_ORIGINS", "*"))

    # Site URL for redirects (frontend)
    SITE_URL: Optional[str] = Field(default=os.getenv("SITE_URL"))


@functools.lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
