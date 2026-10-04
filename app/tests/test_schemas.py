from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.metrics import (
    incidents_analyzed_total,
    incidents_received_total,
    llm_latency_seconds,
    slack_notifications_total,
)
from app.schemas import (
    AlertmanagerPayload,
    IncidentDetailResponse,
    IncidentListResponse,
    IncidentSummaryResponse,
    LLMResult,
    WebhookResponse,
)


def test_alertmanager_schemas_valid():
    payload_data = {
        "version": "4",
        "status": "firing",
        "receiver": "incident-assistant",
        "groupLabels": {"alertname": "PodCrashLooping"},
        "commonLabels": {"namespace": "default", "pod": "demo-app-1"},
        "commonAnnotations": {"summary": "Pod is crash looping"},
        "externalURL": "http://alertmanager:9093",
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "PodCrashLooping", "pod": "demo-app-1"},
                "annotations": {"summary": "CrashLoopBackOff"},
                "startsAt": "2026-10-04T12:00:00Z",
                "endsAt": None,
                "generatorURL": "http://prometheus:9090",
                "fingerprint": "fp-12345",
                "extraFieldIgnored": "val",
            }
        ],
    }

    parsed = AlertmanagerPayload.model_validate(payload_data)
    assert parsed.version == "4"
    assert parsed.status == "firing"
    assert len(parsed.alerts) == 1
    assert parsed.alerts[0].fingerprint == "fp-12345"


def test_llm_result_schema():
    valid_data = {
        "root_cause": "OOMKilled due to memory leak in /allocate",
        "severity": "high",
        "confidence": 0.92,
        "suggested_fix": "Increase container memory limits to 256Mi and fix slice growth in handler.",
        "next_steps": ["kubectl top pod demo-app", "Check memory profile in pprof"],
        "evidence_used": ["Exit code 137 (OOMKilled)", "Memory reached 50Mi limit"],
    }
    result = LLMResult.model_validate(valid_data)
    assert result.severity == "high"
    assert result.confidence == 0.92

    # Confidence must be between 0.0 and 1.0
    with pytest.raises(ValidationError):
        LLMResult.model_validate({**valid_data, "confidence": 1.5})

    # Severity must match allowed literals
    with pytest.raises(ValidationError):
        LLMResult.model_validate({**valid_data, "severity": "super-critical"})


def test_incident_response_schemas():
    now = datetime.now(UTC)
    summary = IncidentSummaryResponse(
        id=1,
        fingerprint="fp-123",
        alertname="PodCrashLooping",
        namespace="default",
        pod="demo-app-1",
        severity="critical",
        status="firing",
        starts_at=now,
        received_at=now,
        root_cause="Null pointer exception",
        confidence=0.9,
        suggested_fix="Fix nil check",
        slack_sent=True,
    )
    assert summary.id == 1
    assert summary.status == "firing"

    detail = IncidentDetailResponse(
        **summary.model_dump(),
        raw_alert={"status": "firing"},
        evidence={"pod_status": "CrashLoopBackOff"},
        analysis={"root_cause": "NPE"},
        llm_model="claude-sonnet-4-6",
        llm_latency_ms=850,
    )
    assert detail.llm_model == "claude-sonnet-4-6"
    assert detail.llm_latency_ms == 850

    list_resp = IncidentListResponse(
        items=[summary],
        total=1,
        limit=10,
        offset=0,
    )
    assert list_resp.total == 1
    assert len(list_resp.items) == 1

    webhook_resp = WebhookResponse(received=1, queued=1, skipped=0, resolved=0)
    assert webhook_resp.queued == 1


def test_prometheus_metrics_instruments():
    """Verify metrics instruments can record observations without error."""
    incidents_received_total.inc()
    incidents_analyzed_total.labels(status="success").inc()
    llm_latency_seconds.observe(1.25)
    slack_notifications_total.labels(status="sent").inc()
