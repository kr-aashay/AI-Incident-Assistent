import logging
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    DATABASE_URL: str = Field(
        ...,
        description="Database connection URL (PostgreSQL or SQLite)",
    )
    WEBHOOK_TOKEN: str = Field(
        ...,
        min_length=16,
        description="Shared bearer token for webhook authentication (minimum 16 chars)",
    )
    ANTHROPIC_API_KEY: str | None = Field(
        default=None,
        description="Anthropic API key for incident analysis",
    )
    ANTHROPIC_MODEL: str = Field(
        default="claude-sonnet-4-6",
        description="Claude model identifier to use for analysis",
    )
    SLACK_WEBHOOK_URL: str | None = Field(
        default=None,
        description="Slack Incoming Webhook URL for posting triage summaries",
    )
    PROMETHEUS_URL: str = Field(
        default="http://prometheus-operated.monitoring.svc:9090",
        description="Prometheus server base URL for metric queries",
    )
    LOG_TAIL_LINES: int = Field(
        default=100,
        description="Number of log lines to tail from affected pod containers",
    )
    MAX_LOG_CHARS: int = Field(
        default=6000,
        description="Maximum characters of log evidence preserved after tailing",
    )
    LLM_TIMEOUT_SECONDS: float = Field(
        default=30.0,
        description="Timeout for Anthropic API analysis requests in seconds",
    )
    ENABLE_K8S_COLLECTION: bool = Field(
        default=True,
        description="Whether to collect logs and events from the Kubernetes API",
    )
    DEDUPE_WINDOW_MINUTES: int = Field(
        default=10,
        description="Window in minutes to suppress duplicate alert processing",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings and log non-sensitive startup warnings."""
    settings = Settings()
    if not settings.ANTHROPIC_API_KEY:
        logger.warning(
            "ANTHROPIC_API_KEY is not configured; AI analysis will use fallback responses."
        )
    if not settings.SLACK_WEBHOOK_URL:
        logger.warning(
            "SLACK_WEBHOOK_URL is not configured; incident summaries will be logged only."
        )
    return settings
