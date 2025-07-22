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
    """Get a database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_sync_session() -> Session:
    """Get a synchronous database session for direct use."""
    return SessionLocal()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an asynchronous database session."""
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "Async database session not available (only available for PostgreSQL)"
        )

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def test_database_connection() -> bool:
    """Test database connectivity for health checks."""
    try:
        with SessionLocal() as session:
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


def get_database_info() -> dict:
    """Get basic database information for monitoring."""
    try:
        with SessionLocal() as session:
            from sqlalchemy import text
            result = session.execute(text("SELECT version()")).scalar()
            return {
                "status": "connected",
                "version": result,
                "url_scheme": str(settings.DATABASE_URL).split("://")[0]
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "url_scheme": str(settings.DATABASE_URL).split("://")[0]
        }
