from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.db import check_ready, init_db
from app.models import Incident


def test_init_db_idempotence():
    """Verify init_db can be called multiple times without failure."""
    init_db()
    init_db()
    assert check_ready() is True


def test_incident_creation_and_partial_unique_index(db_session):
    """Verify partial unique index on fingerprint for status='firing'."""
    now = datetime.now(UTC)

    # 1. First firing alert should insert successfully
    inc1 = Incident(
        fingerprint="fp-abc-1234567890",
        alertname="PodCrashLooping",
        namespace="default",
        pod="demo-app-7d9f8c6b5-x8z9q",
        severity="critical",
        status="firing",
        starts_at=now,
        received_at=now,
        raw_alert={"status": "firing", "alertname": "PodCrashLooping"},
        evidence={"pod_status": "CrashLoopBackOff"},
        analysis={"root_cause": "Null pointer exception on startup"},
        root_cause="Null pointer exception on startup",
        confidence=0.95,
        suggested_fix="Fix nil check in app.go:42",
        llm_model="claude-sonnet-4-6",
        llm_latency_ms=1200,
        slack_sent=True,
    )
    db_session.add(inc1)
    db_session.commit()
    assert inc1.id is not None

    # 2. Second firing alert with the identical fingerprint must trigger IntegrityError
    inc2 = Incident(
        fingerprint="fp-abc-1234567890",
        alertname="PodCrashLooping",
        namespace="default",
        pod="demo-app-7d9f8c6b5-x8z9q",
        severity="critical",
        status="firing",
        starts_at=now,
        received_at=now,
    )
    db_session.add(inc2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 3. Mark the first incident as 'resolved'
    existing = db_session.query(Incident).filter_by(fingerprint="fp-abc-1234567890").first()
    existing.status = "resolved"
    db_session.commit()

    # 4. Now a new 'firing' incident with the same fingerprint can be created
    inc3 = Incident(
        fingerprint="fp-abc-1234567890",
        alertname="PodCrashLooping",
        namespace="default",
        pod="demo-app-7d9f8c6b5-x8z9q",
        severity="critical",
        status="firing",
        starts_at=now,
        received_at=now,
    )
    db_session.add(inc3)
    db_session.commit()
    assert inc3.id is not None
    assert inc3.id != inc1.id


def test_get_session_yields_working_session():
    """Verify get_session generator yields an active session and closes cleanly."""
    from app.db import get_session

    gen = get_session()
    sess = next(gen)
    assert sess is not None
    with pytest.raises(StopIteration):
        next(gen)


def test_check_ready_failure(monkeypatch):
    """Verify check_ready returns False on database connectivity error."""
    import app.db

    def mock_connect():
        raise ConnectionRefusedError("Database unreachable")

    monkeypatch.setattr(app.db.engine, "connect", mock_connect)
    assert check_ready() is False


def test_init_db_postgres_advisory_lock(monkeypatch):
    """Verify init_db executes postgres advisory lock queries when postgres dialect is active."""
    import app.db

    executed_queries = []

    class MockConn:
        def execute(self, stmt):
            executed_queries.append(str(stmt))

        def commit(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    monkeypatch.setattr(app.db.engine.dialect, "name", "postgresql")
    monkeypatch.setattr(app.db.engine, "connect", lambda: MockConn())
    monkeypatch.setattr(app.db.Base.metadata, "create_all", lambda bind: None)

    init_db()
    assert any("pg_advisory_lock" in q for q in executed_queries)
    assert any("pg_advisory_unlock" in q for q in executed_queries)
