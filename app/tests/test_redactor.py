from app.services.redactor import redact, redact_obj


def test_redact_aws_access_keys():
    text = (
        "Error occurred with AWS key AKIAIOSFODNN7EXAMPLE and session ASIAROA1234567890ABC in pod"
    )
    result = redact(text)
    assert "AKIAIOSFODNN7EXAMPLE" not in result
    assert "ASIAROA1234567890ABC" not in result
    assert result == "Error occurred with AWS key [REDACTED] and session [REDACTED] in pod"


def test_redact_key_value_secrets():
    text = (
        'config: password=superSecretPassword123, "api_key": "mySecretApiKey456", '
        "secret: dbPassword789 token=testAuthToken999"
    )
    result = redact(text)
    assert "superSecretPassword123" not in result
    assert "mySecretApiKey456" not in result
    assert "dbPassword789" not in result
    assert "testAuthToken999" not in result
    assert "password=[REDACTED]" in result
    assert '"api_key": "[REDACTED]"' in result
    assert "secret: [REDACTED]" in result


def test_redact_bearer_tokens():
    text = "Request headers: Authorization: Bearer abcdef1234567890qwertyuiop"
    result = redact(text)
    assert "abcdef1234567890qwertyuiop" not in result
    assert "Authorization: Bearer [REDACTED]" in result


def test_redact_anthropic_and_openai_keys():
    text = (
        "Using Claude key sk-ant-api03-abcdef1234567890abcdef1234567890 and "
        "OpenAI key sk-1234567890abcdef1234567890abcdef for analysis"
    )
    result = redact(text)
    assert "sk-ant-api03" not in result
    assert "sk-1234567890abcdef" not in result
    assert result == "Using Claude key [REDACTED] and OpenAI key [REDACTED] for analysis"


def test_redact_slack_tokens_and_webhooks():
    text = (
        "Slack notification dispatched to https://hooks.slack.com/services/T0001/B0002/XYZ123456789 "
        "using bot token xoxb-1234567890-abcdef123456"
    )
    result = redact(text)
    assert "XYZ123456789" not in result
    assert "xoxb-1234567890-abcdef123456" not in result
    assert "https://hooks.slack.com/services/[REDACTED]" in result
    assert "using bot token [REDACTED]" in result


def test_redact_jwt_tokens():
    jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
        "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )
    text = f"User session token: {jwt} authenticated"
    result = redact(text)
    assert jwt not in result
    assert result == "User session token: [REDACTED] authenticated"


def test_redact_pem_private_key():
    pem = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Y1234567890FakeKeyDataHere\n"
        "ABCDEF1234567890ABCDEF1234567890==\n"
        "-----END RSA PRIVATE KEY-----"
    )
    text = f"Loaded private key:\n{pem}\nInitializing TLS socket."
    result = redact(text)
    assert "FakeKeyDataHere" not in result
    assert "[REDACTED_PRIVATE_KEY]" in result
    assert "Initializing TLS socket." in result


def test_redact_url_credentials():
    url_with_auth = (
        "Connecting to postgresql://postgres:mypassword123@postgres.default.svc:5432/incident_db"
    )
    result = redact(url_with_auth)
    assert "mypassword123" not in result
    assert "postgresql://postgres:[REDACTED]@postgres.default.svc:5432/incident_db" in result


def test_redact_leaves_normal_logs_unaltered():
    stack_trace = """Traceback (most recent call last):
  File "/app/main.py", line 45, in handle_request
    response = service.process(payload)
  File "/app/services/processor.py", line 12, in process
    raise ConnectionResetError("Connection reset by peer: 10.244.0.15:8080")
ConnectionResetError: Connection reset by peer: 10.244.0.15:8080"""

    k8s_event = "2026-10-04T12:00:00Z Warning BackOff pod/demo-app-7d9f8c6b5-x8z9q Back-off restarting failed container"
    prom_metric = 'container_memory_working_set_bytes{container="app",pod="demo-app-7d9f8c6b5-x8z9q"} 52428800'
    normal_url = "https://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up"
    uuid_str = "Incident UUID: 550e8400-e29b-41d4-a716-446655440000"

    assert redact(stack_trace) == stack_trace
    assert redact(k8s_event) == k8s_event
    assert redact(prom_metric) == prom_metric
    assert redact(normal_url) == normal_url
    assert redact(uuid_str) == uuid_str


def test_redact_obj_nested_structures():
    nested_data = {
        "alert": {
            "name": "HighMemoryUsage",
            "details": [
                {"pod": "demo-app-1", "token": "xoxb-1234567890-abcdef123456"},
                "Bearer abcdef1234567890qwertyuiop",
            ],
            "metadata": {"key": "AKIAIOSFODNN7EXAMPLE", "int_val": 42},
        }
    }
    redacted = redact_obj(nested_data)
    assert redacted["alert"]["name"] == "HighMemoryUsage"
    assert redacted["alert"]["details"][0]["token"] == "[REDACTED]"
    assert redacted["alert"]["details"][1] == "Bearer [REDACTED]"
    assert redacted["alert"]["metadata"]["key"] == "[REDACTED]"
    assert redacted["alert"]["metadata"]["int_val"] == 42


def test_redact_idempotence():
    text = (
        "AWS AKIAIOSFODNN7EXAMPLE Bearer abcdef1234567890qwertyuiop "
        "password=superSecret123 https://hooks.slack.com/services/T00/B00/ZZZ"
    )
    once = redact(text)
    twice = redact(once)
    assert once == twice


def test_redact_empty_and_primitives():
    assert redact("") == ""
    assert redact(None) is None
    assert redact_obj(123) == 123
    assert redact_obj({"key": {"nested_set": {"AKIAIOSFODNN7EXAMPLE"}}}) == {
        "key": {"nested_set": {"[REDACTED]"}}
    }


def test_redact_user_regression_samples():
    """Verify standard SRE logs/commands are not over-redacted and secrets are properly masked."""
    unaltered_samples = [
        (
            "OOMKilled exit code 137, memory limit 128Mi",
            "OOMKilled exit code 137, memory limit 128Mi",
        ),
        ("kubectl get secret db-secret -n prod", "kubectl get secret db-secret -n prod"),
        ("token_count=512 max_tokens=1000", "token_count=512 max_tokens=1000"),
        (
            "password rotation completed for user admin",
            "password rotation completed for user admin",
        ),
        (
            "GET https://example.com/api/v1/pods?limit=10 200",
            "GET https://example.com/api/v1/pods?limit=10 200",
        ),
    ]
    for sample, expected in unaltered_samples:
        assert redact(sample) == expected

    masked_samples = [
        ("password=hunter2", "password=[REDACTED]"),
        ("Authorization: Bearer abc123def456ghi789", "Authorization: Bearer [REDACTED]"),
        ("postgres://user:s3cret@db:5432/app", "postgres://user:[REDACTED]@db:5432/app"),
    ]
    for sample, expected in masked_samples:
        assert redact(sample) == expected
