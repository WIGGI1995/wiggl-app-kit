"""Unit tests for Keycloak auth kit, middleware, and role dependencies."""

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from wiggl_app_kit.auth_kit import (
    KeycloakAuthMiddleware,
    KeycloakTokenVerifier,
    KeycloakUser,
    get_current_user,
    require_roles,
)

TEST_SECRET = "test-secret-key-32-chars-long-12345"


def create_test_token(
    username: str = "alice",
    realm_roles: tuple[str, ...] = ("user",),
    client_roles: tuple[str, ...] = ("vault-viewer",),
) -> str:
    payload = {
        "sub": "user-123",
        "preferred_username": username,
        "email": f"{username}@wiggl.net",
        "realm_access": {"roles": list(realm_roles)},
        "resource_access": {"test-app": {"roles": list(client_roles)}},
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


@pytest.fixture
def auth_app() -> FastAPI:
    app = FastAPI()
    verifier = KeycloakTokenVerifier(secret=TEST_SECRET, client_id="test-app")
    app.add_middleware(
        KeycloakAuthMiddleware,
        verifier=verifier,
        public_prefixes=frozenset({"/health", "/public"}),
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/profile")
    def profile(user: KeycloakUser = Depends(get_current_user)) -> dict[str, str]:
        return {"username": user.username}

    @app.get("/admin-only")
    def admin_area(
        _user: KeycloakUser = Depends(require_roles("vault-admin")),
    ) -> dict[str, str]:
        return {"status": "admin_granted"}

    return app


def test_public_endpoint_accessible_without_auth(auth_app: FastAPI) -> None:
    client = TestClient(auth_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_protected_endpoint_requires_token(auth_app: FastAPI) -> None:
    client = TestClient(auth_app)
    response = client.get("/profile")
    assert response.status_code == 401
    assert "Authorization" in response.json()["detail"]


def test_protected_endpoint_accepts_valid_token(auth_app: FastAPI) -> None:
    client = TestClient(auth_app)
    token = create_test_token(username="bob")
    response = client.get("/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"username": "bob"}


def test_role_enforcement_forbidden_when_role_missing(auth_app: FastAPI) -> None:
    client = TestClient(auth_app)
    token = create_test_token(username="charlie", client_roles=("vault-viewer",))
    response = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert "Missing required role" in response.json()["detail"]


def test_role_enforcement_granted_when_role_present(auth_app: FastAPI) -> None:
    client = TestClient(auth_app)
    token = create_test_token(username="admin_user", client_roles=("vault-admin",))
    response = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"status": "admin_granted"}
