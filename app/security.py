import logging
import secrets

from fastapi import Header, HTTPException, status

from app.config import get_settings

logger = logging.getLogger(__name__)


def require_webhook_token(
    authorization: str | None = Header(None, alias="Authorization"),
) -> str:
    """Validate incoming HTTP request Authorization header against the configured webhook secret.

    Raises:
        HTTPException: 401 Unauthorized if the header is missing, malformed, or invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme; Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1].strip()
    configured_token = get_settings().WEBHOOK_TOKEN

    if not secrets.compare_digest(token, configured_token):
        logger.warning("Rejected webhook request with invalid bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token
