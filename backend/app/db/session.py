from typing import Generator, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields an async-safe synchronous SQLAlchemy session per request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> Dict[str, Any]:
    """
    Utility function to verify database connectivity and pgvector extension status.
    Returns a dictionary status object or raises an Exception.
    """
    with engine.connect() as connection:
        # Verify basic query execution
        connection.execute(text("SELECT 1"))
        
        # Check if pgvector extension is installed
        result = connection.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).fetchone()
        
        has_vector = result is not None
        
        return {
            "connected": True,
            "pgvector_extension": has_vector,
        }
