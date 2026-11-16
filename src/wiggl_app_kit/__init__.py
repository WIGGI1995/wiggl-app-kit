"""WIGGLIFICATION Platform App Kit: Keycloak Auth and OpenTelemetry SDK."""

from wiggl_app_kit import auth_kit, otel_kit
from wiggl_app_kit.auth_kit.authentication import (
    KeycloakAuthMiddleware,
    KeycloakTokenVerifier,
    extract_bearer_token,
    get_authenticated_user,
    get_current_user,
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
from wiggl_app_kit.bootstrap import get_app_logger, setup_wiggl_app
from wiggl_app_kit.otel_kit.decorators import (
    audit_action,
    audit_event,
    error_boundary,
    error_tracker,
    log_endpoint,
    logging_endpoint,
    metrics_endpoint,
    observe,
    quota_guard,
    trace_span,
    tracing_span,
    track_metrics,
)
from wiggl_app_kit.otel_kit.sanitizer import sanitize_payload
from wiggl_app_kit.otel_kit.telemetry import (
    DEFAULT_SERVICE_NAME,
    HttpOtlpLogHandler,
    JsonLogFormatter,
    configure_telemetry,
)

__version__ = "0.3.1"

__all__ = [
    "DEFAULT_SERVICE_NAME",
    "HttpOtlpLogHandler",
    "JsonLogFormatter",
    "KeycloakAuthMiddleware",
    "KeycloakTokenVerifier",
    "KeycloakUser",
    "audit_action",
    "audit_event",
    "auth_kit",
    "configure_telemetry",
    "error_boundary",
    "error_tracker",
    "extract_bearer_token",
    "get_app_logger",
    "get_authenticated_user",
    "get_current_user",
    "log_endpoint",
    "logging_endpoint",
    "metrics_endpoint",
    "observe",
    "otel_kit",
    "quota_guard",
    "require_all_permissions",
    "require_all_roles",
    "require_client_role",
    "require_permissions",
    "require_realm_role",
    "require_roles",
    "require_scope",
    "sanitize_payload",
    "setup_wiggl_app",
    "trace_span",
    "tracing_span",
    "track_metrics",
]
