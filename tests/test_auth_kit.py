"""Unit tests for Keycloak auth kit, authentication, and authorization policies."""

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from wiggl_app_kit.auth_kit.authentication import (
    KeycloakAuthMiddleware,
    KeycloakTokenVerifier,
    get_authenticated_user,
)
from wiggl_app_kit.auth_kit.authorization import (
    require_all_permissions,
    require_all_roles,
    require_client_role,
    require_permissions,
    require_realm_role,
    require_roles,
    require_scope,
)
from wiggl_app_kit.auth_kit.models import KeycloakUser

TEST_SECRET = "test-secret-key-32-chars-long-12345"


def create_test_token(
    username: str = "alice",
    realm_roles: tuple[str, ...] = ("user",),
    client_roles: tuple[str, ...] = ("vault-viewer",),
    scopes: tuple[str, ...] = ("read", "openid"),
    permissions: tuple[str, ...] = ("vault:read",),
) -> str:
    payload = {
        "sub": "user-123",
        "preferred_username": username,
        "email": f"{username}@wiggl.net",
        "scope": " ".join(scopes),
        "permissions": list(permissions),
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
    def profile(user: KeycloakUser = Depends(get_authenticated_user)) -> dict[str, str]:
        return {"username": user.username}

    @app.get("/admin-only")
    def admin_area(
        _user: KeycloakUser = Depends(require_roles("vault-admin")),
    ) -> dict[str, str]:
        return {"status": "admin_granted"}

    @app.get("/super-admin")
    def super_admin(
        _user: KeycloakUser = Depends(require_all_roles("admin", "vault-admin")),
    ) -> dict[str, str]:
        return {"status": "super_admin_granted"}

    @app.get("/realm-operator")
    def realm_op(
        _user: KeycloakUser = Depends(require_realm_role("operator")),
    ) -> dict[str, str]:
        return {"status": "realm_op_granted"}

    @app.get("/client-editor")
    def client_ed(
        _user: KeycloakUser = Depends(require_client_role("vault-editor")),
    ) -> dict[str, str]:
        return {"status": "client_ed_granted"}

    @app.get("/sensitive-data")
    def sensitive(
        _user: KeycloakUser = Depends(require_permissions("vault:read")),
    ) -> dict[str, str]:
        return {"status": "permission_granted"}

    @app.get("/write-data")
    def write_data(
        _user: KeycloakUser = Depends(require_all_permissions("vault:read", "vault:write")),
    ) -> dict[str, str]:
        return {"status": "all_perms_granted"}

    @app.get("/scoped-data")
    def scoped_data(
        _user: KeycloakUser = Depends(require_scope("admin_scope")),
    ) -> dict[str, str]:
        return {"status": "scope_granted"}

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


def test_protected_endpoint_accepts_cookie_token(auth_app: FastAPI) -> None:
    client = TestClient(auth_app)
    token = create_test_token(username="cookiebob")
    client.cookies.set("wiggl_session_token", token)
    response = client.get("/profile")
    assert response.status_code == 200
    assert response.json() == {"username": "cookiebob"}


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


def test_require_all_roles_enforcement(auth_app: FastAPI) -> None:
    client = TestClient(auth_app)
    partial_token = create_test_token(realm_roles=("admin",), client_roles=("vault-viewer",))
    resp = client.get("/super-admin", headers={"Authorization": f"Bearer {partial_token}"})
    assert resp.status_code == 403

    full_token = create_test_token(realm_roles=("admin",), client_roles=("vault-admin",))
    resp_ok = client.get("/super-admin", headers={"Authorization": f"Bearer {full_token}"})
    assert resp_ok.status_code == 200
    assert resp_ok.json() == {"status": "super_admin_granted"}


def test_require_realm_and_client_roles(auth_app: FastAPI) -> None:
    client = TestClient(auth_app)
    token = create_test_token(realm_roles=("operator",), client_roles=("vault-editor",))
    resp_realm = client.get("/realm-operator", headers={"Authorization": f"Bearer {token}"})
    assert resp_realm.status_code == 200

    resp_client = client.get("/client-editor", headers={"Authorization": f"Bearer {token}"})
    assert resp_client.status_code == 200


def test_permission_and_scope_enforcement(auth_app: FastAPI) -> None:
    client = TestClient(auth_app)
    token = create_test_token(
        permissions=("vault:read",),
        scopes=("read",),
    )
    # has vault:read
    resp_perm = client.get("/sensitive-data", headers={"Authorization": f"Bearer {token}"})
    assert resp_perm.status_code == 200

    # missing vault:write
    resp_all_perm = client.get("/write-data", headers={"Authorization": f"Bearer {token}"})
    assert resp_all_perm.status_code == 403

    # missing admin_scope
    resp_scope = client.get("/scoped-data", headers={"Authorization": f"Bearer {token}"})
    assert resp_scope.status_code == 403

    # with admin_scope
    scoped_token = create_test_token(scopes=("admin_scope",))
    resp_scope_ok = client.get("/scoped-data", headers={"Authorization": f"Bearer {scoped_token}"})
    assert resp_scope_ok.status_code == 200
