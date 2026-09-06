"""
SQLAlchemy PostgreSQL connection management for ULPF.
"""
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from app.config import DATABASE_URL

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

_engine = None
_SessionLocal = None

if DATABASE_URL:
    try:
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False,
        )
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    except Exception as e:
        logger.warning("Failed to initialize database engine from DATABASE_URL: %s", e)
        _engine = None
        _SessionLocal = None

def get_engine():
    return _engine

def is_db_available() -> bool:
    """Check if database is configured and reachable."""
    if _engine is None:
        return False
    try:
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

def init_db():
    """Create all database tables if engine is configured and database is available."""
    if _engine is not None and is_db_available():
        Base.metadata.create_all(bind=_engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining a database session."""
    if _SessionLocal is None:
        raise RuntimeError("Database is not configured (DATABASE_URL missing or invalid)")
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
