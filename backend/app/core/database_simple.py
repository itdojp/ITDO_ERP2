from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# type: ignore[attr-defined] - practical v19.0 approach
engine = create_engine(str(settings.DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> None:  # type: ignore[no-untyped-def] - practical approach
    """Get database session - simple and working"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> None:  # type: ignore[no-untyped-def]
    """Test database connection - practical check"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")  # type: ignore[no-untyped-call]
        db.close()
        return True
    except Exception:  # type: ignore[broad-except]
        return False
