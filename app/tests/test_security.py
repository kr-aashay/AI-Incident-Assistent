from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.security import require_webhook_token

app = FastAPI()


@app.get("/protected")
def protected_route(token: str = Depends(require_webhook_token)):
    return {"status": "authenticated", "token_verified": True}


client = TestClient(app)


def test_missing_authorization_header():
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    assert response.json()["detail"] == "Missing Authorization header"


def test_malformed_authorization_scheme():
    response = client.get("/protected", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    assert "Invalid authorization scheme" in response.json()["detail"]


def test_invalid_bearer_token():
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer wrong-token-value-here-12345"},
    )
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    assert response.json()["detail"] == "Invalid bearer token"


def test_valid_bearer_token():
    valid_token = "test-secret-token-min-16-chars-long"
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "authenticated", "token_verified": True}


def test_settings_warnings(monkeypatch):
    """Verify settings initialization without optional keys emits warnings without crashing."""
    import app.config

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    app.config.get_settings.cache_clear()
    settings = app.config.get_settings()
    assert settings.ANTHROPIC_API_KEY is None
    assert settings.SLACK_WEBHOOK_URL is None
