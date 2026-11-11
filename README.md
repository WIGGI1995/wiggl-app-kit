# wiggl-app-kit

> Official FastAPI SDK for WIGGLIFICATION: Keycloak Authentication, Authorization, and OpenTelemetry Observability.

[![CI/CD](https://github.com/WIGGI1995/wiggl-app-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/WIGGI1995/wiggl-app-kit/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)

---

## Installation

```bash
# Direct Git installation (stable main)
pip install "wiggl-app-kit @ git+https://github.com/WIGGI1995/wiggl-app-kit.git@main"

# Or install from GitHub Release Wheel / PyPI:
pip install wiggl-app-kit
```

---

## 1. Authentication Kit (`auth_kit.authentication`)

Validates Keycloak JWT bearer tokens using cached JWKS (RS256) or symmetric secrets (HS256) with zero boilerplate.

```python
from fastapi import FastAPI
from wiggl_app_kit.auth_kit.authentication import KeycloakAuthMiddleware, KeycloakTokenVerifier

app = FastAPI()

verifier = KeycloakTokenVerifier(
    jwks_url="http://keycloak:8080/auth/realms/platform/protocol/openid-connect/certs",
    client_id="app-my-app",
)

# Protect all routes by default while whitelisting public health/docs endpoints
app.add_middleware(KeycloakAuthMiddleware, verifier=verifier)
```

---

## 2. Authorization Kit (`auth_kit.authorization`)

Enforce Role-Based Access Control (RBAC), client roles, fine-grained permissions, and OAuth scopes as declarative FastAPI dependencies.

```python
from fastapi import APIRouter, Depends
from wiggl_app_kit.auth_kit.authorization import (
    require_roles,
    require_all_roles,
    require_realm_role,
    require_client_role,
    require_permissions,
    require_scope,
)
from wiggl_app_kit.auth_kit.models import KeycloakUser

router = APIRouter()

# Enforce at least one role
@router.get("/items")
def list_items(user: KeycloakUser = Depends(require_roles("vault-viewer", "vault-editor"))):
    return {"user": user.username}

# Enforce strict multi-role requirements
@router.post("/items")
def create_item(user: KeycloakUser = Depends(require_all_roles("vault-editor", "platform-user"))):
    return {"created_by": user.username}

# Enforce fine-grained permission or OAuth scope
@router.delete("/items/{item_id}")
def delete_item(user: KeycloakUser = Depends(require_permissions("vault:delete"))):
    return {"status": "deleted"}
```

---

## 3. Observability Kit (`otel_kit`)

Standardized decorator suite for OpenTelemetry traces (Tempo), metrics (Prometheus), and structured logs (Loki).

```python
from fastapi import FastAPI
from wiggl_app_kit.otel_kit import (
    configure_telemetry,
    observe,
    log_endpoint,
    track_metrics,
    audit_event,
    error_tracker,
    quota_guard,
)

app = FastAPI()

# Single-line OTLP bootstrap (reads OTEL_EXPORTER_OTLP_ENDPOINT automatically)
configure_telemetry(service_name="my-service")

@app.get("/compute")
@observe("service.compute")          # Traces, logs and tracks metrics in 1 line
@audit_event("service.action")       # Emits tamper-evident audit log
@error_tracker("service.backend")    # Categorizes exceptions into error meters
def compute_data():
    return {"result": 42}
```

---

## 4. Release & Versioning

Releases follow [Semantic Versioning](https://semver.org/).
Every push to the `main` branch:
1. Validates strict quality gates (Ruff, Mypy strict, Pytest).
2. Reads the `VERSION` file.
3. Automatically creates a Git tag (`vX.Y.Z`).
4. Builds release wheels (`.whl`) and tarballs (`.tar.gz`).
5. Publishes a GitHub Release with assets and changelog notes.
