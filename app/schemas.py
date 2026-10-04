from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AlertItem(BaseModel):
    """Single alert entry within an Alertmanager webhook payload."""

    status: str = Field(..., description="Alert firing/resolved status")
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    startsAt: datetime | str = Field(..., description="Alert firing start timestamp")
    endsAt: datetime | str | None = Field(default=None, description="Alert end timestamp")
    generatorURL: str | None = Field(default="", description="Prometheus expression URL")
    fingerprint: str = Field(..., description="Unique hash identifying the active alert instance")

    model_config = ConfigDict(extra="ignore")


class AlertmanagerPayload(BaseModel):
    """Alertmanager v4 webhook request body schema."""

    version: str = Field(default="4")
    status: str = Field(..., description="Overall payload status (firing or resolved)")
    receiver: str = Field(default="")
    groupLabels: dict[str, str] = Field(default_factory=dict)
    commonLabels: dict[str, str] = Field(default_factory=dict)
    commonAnnotations: dict[str, str] = Field(default_factory=dict)
    externalURL: str | None = Field(default="")
    alerts: list[AlertItem] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class LLMResult(BaseModel):
    """Structured root cause analysis returned by the AI analyzer."""

    root_cause: Annotated[
        str,
        Field(max_length=2000, description="Concise explanation of the underlying failure"),
    ]
    severity: Literal["low", "medium", "high", "critical"] = Field(
        description="Assessed incident severity level"
    )
    confidence: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="Confidence score between 0.0 and 1.0 based on evidence strength",
        ),
    ]
    suggested_fix: Annotated[
        str,
        Field(max_length=4000, description="Actionable remediation steps or patch guidance"),
    ]
    next_steps: list[Annotated[str, Field(max_length=1000)]] = Field(
        default_factory=list,
        max_length=20,
        description="Recommended diagnostic or operational verification commands",
    )
    evidence_used: list[Annotated[str, Field(max_length=1000)]] = Field(
        default_factory=list,
        max_length=20,
        description="Specific logs, metrics, or events cited as basis for the conclusion",
    )

    model_config = ConfigDict(extra="ignore")


class IncidentSummaryResponse(BaseModel):
    """Lightweight summary model for incident list endpoints."""

    id: int
    fingerprint: str
    alertname: str
    namespace: str
    pod: str
    severity: str
    status: str
    starts_at: datetime
    received_at: datetime
    analyzed_at: datetime | None = None
    root_cause: str | None = None
    confidence: float | None = None
    suggested_fix: str | None = None
    slack_sent: bool = False
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class IncidentDetailResponse(IncidentSummaryResponse):
    """Comprehensive incident model including full telemetry and raw alert details."""

    raw_alert: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    analysis: dict[str, Any] | None = None
    llm_model: str | None = None
    llm_latency_ms: int | None = None

    model_config = ConfigDict(from_attributes=True)


class IncidentListResponse(BaseModel):
    """Paginated collection of incident summaries."""

    items: list[IncidentSummaryResponse]
    total: int
    limit: int
    offset: int


class WebhookResponse(BaseModel):
    """Acknowledgment payload returned immediately upon processing a webhook request."""

    received: int
    queued: int
    skipped: int
    resolved: int
