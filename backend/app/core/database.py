from collections.abc import Generator
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Sync engine and session
engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine and session (only for PostgreSQL)
async_engine = None
AsyncSessionLocal = None

# Only create async engine if using PostgreSQL
if str(settings.DATABASE_URL).startswith("postgresql"):
    async_database_url = str(settings.DATABASE_URL).replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    async_engine = create_async_engine(async_database_url)
    AsyncSessionLocal = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_sync_session() -> Session:
    """Get a synchronous database session for direct use."""
    return SessionLocal()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an asynchronous database session."""
    if AsyncSessionLocal is None:
        raise RuntimeError("AsyncSessionLocal is not initialized")

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
