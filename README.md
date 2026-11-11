# wiggl-app-kit

> Official FastAPI SDK for **WIGGLIFICATION**: Keycloak Authentication Middleware and OpenTelemetry Telemetry Suite.

Corporate Brand Color: `#10B981` / `#22C55E` / `#064E3B`

---

## Installation

```bash
pip install wiggl-app-kit
```

---

## Quickstart

### 1. Keycloak Authentication Middleware (`auth_kit`)

Protect all tenant application routes using `KeycloakAuthMiddleware`:

```python
from fastapi import Depends, FastAPI
from wiggl_app_kit.auth_kit import (
    KeycloakAuthMiddleware,
    KeycloakTokenVerifier,
    KeycloakUser,
    get_current_user,
    require_roles,
)

app = FastAPI(title="My Tenant App")

# Configure Keycloak verifier with JWKS endpoint
verifier = KeycloakTokenVerifier(
    jwks_url="http://keycloak:8080/auth/realms/platform/protocol/openid-connect/certs",
    client_id="my-tenant-app",
)

# Add middleware (public routes like /health bypass authentication automatically)
app.add_middleware(
    KeycloakAuthMiddleware,
    verifier=verifier,
    public_prefixes=frozenset({"/health", "/info", "/docs", "/openapi.json"}),
)

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/items")
def list_items(user: KeycloakUser = Depends(get_current_user)):
    return {"user": user.username, "roles": list(user.all_roles)}

@app.delete("/items/{item_id}")
def delete_item(
    item_id: str,
    user: KeycloakUser = Depends(require_roles("vault-admin")),
):
    return {"deleted": item_id, "by": user.username}
```

---

### 2. OpenTelemetry & Structured Logging (`otel_kit`)

Bootstrap tracing, metrics, and structured logs into OpenTelemetry Collector:

```python
from wiggl_app_kit.otel_kit import (
    configure_telemetry,
    log_endpoint,
    track_metrics,
    audit_event,
    error_tracker,
    quota_guard,
    observe,
)

# Bootstrap OpenTelemetry tracer, meter, and OTLP log exporter
configure_telemetry(
    service_name="my-tenant-app",
    otlp_endpoint="http://otel-collector:4318",
)

@app.post("/items")
@observe("items.create")  # Combines logging, metrics, and tracing
@audit_event("items.create")
def create_item(payload: dict):
    return {"status": "created"}
```

---

## Decorators Reference

| Decorator | Role | Telemetry Destination |
|:---|:---|:---|
| `@log_endpoint` (`@logging`) | Emits lifecycle events (start, checkpoints, finish) with duration and status | Loki (`{app="...", level="..."}`) |
| `@track_metrics` (`@metrics`) | Increments request counters and measures latency histograms (P50, P95, P99) | Prometheus (`wiggl_app_requests_total`, `wiggl_app_duration_seconds`) |
| `@trace_span` (`@tracing`) | Creates explicit child spans for Tempo waterfall visualization | Tempo |
| `@audit_event` (`@audit`) | Emits tamper-evident security audit actions (actor, action, target) | Loki & Platform Audit Store |
| `@error_tracker` (`@errors`) | Categorizes exceptions, increments error counters, extracts clean stack traces | Loki & Prometheus (`wiggl_app_errors_total`) |
| `@quota_guard` (`@quota`) | Monitors payload sizes and storage delta against tenant limits | Prometheus gauges |
| `@observe` | Composite convenience wrapper applying logging, metrics, and tracing in one line | Loki, Prometheus, Tempo |

---

## License
MIT
