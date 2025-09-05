import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.config import Settings, get_settings
from src.core.db import init_db, dispose_db
from src.routers import auth, images, edits, subscriptions, dashboard

# LIFESPAN MANAGEMENT
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context.
    Initializes database connections and any startup tasks.
    Ensures proper cleanup on shutdown.
    """
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    await init_db()
    yield
    await dispose_db()


app = FastAPI(
    title="Real Estate Image Enhancer API",
    description="APIs for user management, image upload/editing, usage tracking, and subscriptions.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Health", "description": "Health check and service information."},
        {"name": "Auth", "description": "User registration, login, and token management."},
        {"name": "Images", "description": "Image upload, metadata, and retrieval."},
        {"name": "Edits", "description": "Natural language edit requests and history."},
        {"name": "Usage", "description": "Trial usage and metering."},
        {"name": "Subscriptions", "description": "Stripe payment, plan linking, and subscription CRUD."},
        {"name": "Dashboard", "description": "Aggregated data for the user dashboard."},
    ],
)

# CORS
settings: Settings = get_settings()
allow_origins: List[str] = settings.CORS_ALLOW_ORIGINS.split(",") if settings.CORS_ALLOW_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROUTERS
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(images.router, prefix="/api/images", tags=["Images", "Usage"])
app.include_router(edits.router, prefix="/api/edits", tags=["Edits"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["Subscriptions"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


# PUBLIC_INTERFACE
@app.get("/", tags=["Health"], summary="Health check", description="Simple health check endpoint to verify the server is running.")
def health_check():
    """Root health check endpoint."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get("/api/health", tags=["Health"], summary="Detailed health status", description="Returns service details including environment and version.")
def detailed_health():
    """Detailed health endpoint with environment metadata."""
    return JSONResponse(
        {
            "status": "ok",
            "version": app.version,
            "environment": settings.ENV,
            "db_url_set": bool(settings.DATABASE_URL),
        }
    )
