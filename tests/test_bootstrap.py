"""Unit tests for turnkey setup_wiggl_app bootstrap helper."""

import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient

from wiggl_app_kit import KeycloakUser, get_authenticated_user, observe, setup_wiggl_app

TEST_SECRET = "test-secret-key-32-chars-long-12345"


def create_token(username: str = "alice") -> str:
    payload = {
        "sub": "user-123",
        "preferred_username": username,
        "email": f"{username}@wiggl.net",
        "scope": "openid",
        "permissions": ["test:read"],
        "realm_access": {"roles": ["user"]},
        "resource_access": {"test-app": {"roles": ["viewer"]}},
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


def test_setup_wiggl_app_turnkey() -> None:
    app = FastAPI()
    setup_wiggl_app(
        app,
        service_name="turnkey-test-app",
        jwt_secret=TEST_SECRET,
        client_id="test-app",
        log_level="DEBUG",
    )

    @app.get("/items")
    @observe("items.list")
    def list_items() -> dict[str, str]:
        return {"result": "ok"}

    @app.get("/apps/turnkey-test-app/health")
    def app_health() -> dict[str, str]:
        return {"status": "healthy"}

    client = TestClient(app)

    # 1. Health check bypasses auth
    res_health = client.get("/apps/turnkey-test-app/health")
    assert res_health.status_code == 200

    # 2. Protected endpoint blocks unauthenticated
    res_blocked = client.get("/items")
    assert res_blocked.status_code == 401

    # 3. Protected endpoint accepts valid token
    token = create_token()
    res_auth = client.get("/items", headers={"Authorization": f"Bearer {token}"})
    assert res_auth.status_code == 200
    assert res_auth.json() == {"result": "ok"}
