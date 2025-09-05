from typing import List
from pydantic import BaseSettings, PostgresDsn, HttpUrl
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: PostgresDsn

    # JWT
    JWT_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google API
    GOOGLE_API_KEY: str
    GOOGLE_API_ENDPOINT: HttpUrl

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_BASIC_PRICE_ID: str
    STRIPE_PRO_PRICE_ID: str
    STRIPE_ENTERPRISE_PRICE_ID: str

    # Frontend
    FRONTEND_URL: str = "*"

    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        case_sensitive = True

def validate_env_vars() -> List[str]:
    """Validate all required environment variables are set"""
    missing_vars = []
    
    try:
        Settings()
    except Exception as e:
        # Extract missing fields from validation error
        for error in e.errors():
            if error["type"] == "value_error.missing":
                missing_vars.append(error["loc"][0])
    
    return missing_vars

def get_settings() -> Settings:
    """Get validated settings"""
    return Settings()
