import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set deterministic testing configuration before importing application components
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["WEBHOOK_TOKEN"] = "test-secret-token-min-16-chars-long"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-mock-api-key-for-tests"
os.environ["SLACK_WEBHOOK_URL"] = "https://hooks.slack.com/services/T00/B00/TESTHOOK"
os.environ["ENABLE_K8S_COLLECTION"] = "true"

from app.config import get_settings
from app.models import Base


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear cached settings before each test execution."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def sqlite_engine():
    """Provide an in-memory SQLite database engine with static connection pooling."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(sqlite_engine):
    """Provide a clean isolated database session for testing."""
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
