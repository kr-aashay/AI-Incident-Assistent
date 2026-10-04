import logging
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base

logger = logging.getLogger(__name__)

settings = get_settings()

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

_ADVISORY_LOCK_ID = 82461973  # Deterministic 32-bit key for schema initialization locking


def get_session() -> Generator[Session, None, None]:
    """Provide a transactional database session scope for FastAPI request lifecycles."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def check_ready() -> bool:
    """Execute a lightweight probe query to verify active database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Database readiness check failed: %s", exc)
        return False


def init_db() -> None:
    """Initialize database schemas with multi-replica concurrency protection."""
    is_postgres = engine.dialect.name == "postgresql"

    if is_postgres:
        with engine.connect() as conn:
            logger.info(
                "Acquiring PostgreSQL advisory lock %d for schema migration...",
                _ADVISORY_LOCK_ID,
            )
            conn.execute(text(f"SELECT pg_advisory_lock({_ADVISORY_LOCK_ID})"))
            conn.commit()
            try:
                Base.metadata.create_all(bind=conn)
                conn.commit()
                logger.info("Database schemas verified/created successfully.")
            finally:
                conn.execute(text(f"SELECT pg_advisory_unlock({_ADVISORY_LOCK_ID})"))
                conn.commit()
                logger.info("PostgreSQL advisory lock %d released.", _ADVISORY_LOCK_ID)
    else:
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite/Generic database schemas verified/created successfully.")
