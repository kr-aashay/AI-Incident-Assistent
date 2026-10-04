from prometheus_client import Counter, Histogram

incidents_received_total = Counter(
    "incidents_received_total",
    "Total count of incoming Alertmanager webhook alerts received",
)

incidents_analyzed_total = Counter(
    "incidents_analyzed_total",
    "Total count of incidents processed through root cause analysis",
    ["status"],
)

llm_latency_seconds = Histogram(
    "llm_latency_seconds",
    "Latency duration for Anthropic Claude analysis invocations in seconds",
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 15.0, 30.0, 60.0],
)

slack_notifications_total = Counter(
    "slack_notifications_total",
    "Total count of Slack triage summaries dispatched",
    ["status"],
)
