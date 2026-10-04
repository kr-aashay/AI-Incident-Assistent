import re
from collections.abc import Mapping, Sequence
from typing import Any

# Multi-line PEM private key blocks
_PEM_PRIVATE_KEY_REGEX = re.compile(
    r"-----BEGIN [A-Z0-9_\- ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9_\- ]*PRIVATE KEY-----",
    re.MULTILINE,
)

# AWS Access Key IDs
_AWS_KEY_ID_REGEX = re.compile(r"\b(?:AKIA|ASIA|AROA|AIPA|ANPA|ANVA)[A-Z0-9]{16}\b")

# Anthropic API Keys (sk-ant-...)
_ANTHROPIC_KEY_REGEX = re.compile(r"\bsk-ant-[a-zA-Z0-9_\-]{20,}\b")

# OpenAI and generic sk- keys
_OPENAI_KEY_REGEX = re.compile(r"\bsk-[a-zA-Z0-9_\-]{20,}\b")

# Slack Tokens (xoxb, xoxp, xoxa, xoxr, xoxs)
_SLACK_TOKEN_REGEX = re.compile(r"\bxox[baprs]-[a-zA-Z0-9_\-]{10,}\b")

# Slack Webhook URLs
_SLACK_WEBHOOK_REGEX = re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_\-]+")

# JSON Web Tokens (JWT)
_JWT_REGEX = re.compile(r"\beyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-.]{10,}\b")

# URLs containing credentials (e.g., postgresql://user:pass@hostname:5432/db)
_URL_CREDENTIALS_REGEX = re.compile(r"([a-zA-Z][a-zA-Z0-9+.\-]*://[^\s/@:]+):([^\s/@]+)@")

# Authorization Bearer headers or standalone tokens
_BEARER_TOKEN_REGEX = re.compile(r"(?i)\b(bearer\s+)(?!\[REDACTED\])[a-zA-Z0-9_\-\.]{12,}\b")

# Key-Value assignments for secrets (e.g. password=..., "api_key": "...", secret: ...)
_KV_SECRET_REGEX = re.compile(
    r"""(?i)(["']?(?:password|passwd|pwd|secret|token|api_key|apikey|access_key|auth_token|client_secret|private_key)["']?\s*[:=]\s*["']?)(?!\[REDACTED\])([^"'\s,;}\]]{4,})(["']?)"""
)


def redact(text: str) -> str:
    """Scrub sensitive credentials, tokens, keys, and secrets from arbitrary log text.

    Preserves structural context, key names, normal URLs, stack traces, and non-sensitive data.
    """
    if not text:
        return text

    # 1. Redact PEM blocks first (multiline replacement)
    redacted = _PEM_PRIVATE_KEY_REGEX.sub("[REDACTED_PRIVATE_KEY]", text)

    # 2. Redact Slack Webhook URLs
    redacted = _SLACK_WEBHOOK_REGEX.sub("https://hooks.slack.com/services/[REDACTED]", redacted)

    # 3. Redact URL embedded user:pass credentials
    redacted = _URL_CREDENTIALS_REGEX.sub(r"\1:[REDACTED]@", redacted)

    # 4. Redact Key-Value secret assignments (password: foo, "token": "bar")
    redacted = _KV_SECRET_REGEX.sub(r"\1[REDACTED]\3", redacted)

    # 5. Redact Bearer tokens
    redacted = _BEARER_TOKEN_REGEX.sub(r"\1[REDACTED]", redacted)

    # 6. Redact explicit token formats
    redacted = _AWS_KEY_ID_REGEX.sub("[REDACTED]", redacted)
    redacted = _ANTHROPIC_KEY_REGEX.sub("[REDACTED]", redacted)
    redacted = _OPENAI_KEY_REGEX.sub("[REDACTED]", redacted)
    redacted = _SLACK_TOKEN_REGEX.sub("[REDACTED]", redacted)
    redacted = _JWT_REGEX.sub("[REDACTED]", redacted)

    return redacted


def redact_obj(obj: Any) -> Any:
    """Recursively scrub sensitive information across nested dictionaries, lists, and primitives."""
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, Mapping):
        return {k: redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, Sequence) and not isinstance(obj, (bytes, bytearray)):
        return [redact_obj(elem) for elem in obj]
    if isinstance(obj, set):
        return {redact_obj(elem) for elem in obj}
    return obj
