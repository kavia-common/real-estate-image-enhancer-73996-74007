from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import auth, users, images, payments, webhooks, admin
from src.models import Base, engine, SessionLocal
from src.utils.audit import log_audit_event
import os
from src.utils.config import validate_env_vars, get_settings

# Validate environment variables
missing_vars = validate_env_vars()
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Real Estate Image Enhancer API",
    description="API for enhancing real estate images using AI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["authentication"])
app.include_router(users.router, tags=["users"])
app.include_router(images.router, tags=["images"])
app.include_router(payments.router, prefix="/payment", tags=["payments"])
app.include_router(webhooks.router, tags=["webhooks"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/", tags=["health"])
def health_check():
    return {"message": "Healthy"}

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    """Middleware to handle database sessions"""
    db = SessionLocal()
    request.state.db = db
    try:
        response = await call_next(request)
        return response
    finally:
        db.close()

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Middleware to handle audit logging"""
    # Get request details
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    response = await call_next(request)
    
    # Log audit event for significant operations
    if request.url.path not in ["/", "/docs", "/openapi.json"]:
        try:
            await log_audit_event(
                db=request.state.db,
                user_id=getattr(request.state, "user_id", None),
                action=f"http_{request.method.lower()}",
                details={
                    "path": request.url.path,
                    "status_code": response.status_code
                },
                ip_address=ip,
                user_agent=user_agent
            )
        except Exception:
            # Log audit failures but don't break the request
            pass
    
    return response
