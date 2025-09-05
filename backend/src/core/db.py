from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import get_settings

_engine = None
_SessionFactory: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


async def init_db():
    """Initialize async DB engine and session factory."""
    global _engine, _SessionFactory
    settings = get_settings()
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is required.")
    # Ensure async driver is used (psycopg)
    db_url = settings.DATABASE_URL
    if "+psycopg" not in db_url and db_url.startswith("postgresql"):
        # Support both postgresql:// and postgresql+psycopg://
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

    _engine = create_async_engine(
        db_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        echo=False,
    )
    _SessionFactory = async_sessionmaker(bind=_engine, expire_on_commit=False)


async def dispose_db():
    """Dispose engine on shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a DB session for request scope."""
    if _SessionFactory is None:
        await init_db()
    assert _SessionFactory is not None
    async with _SessionFactory() as session:
        yield session
