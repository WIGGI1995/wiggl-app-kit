"""OpenTelemetry and Structured Logging Kit for FastAPI tenant applications."""

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
from wiggl_app_kit.otel_kit.telemetry import configure_telemetry

__all__ = [
    "audit_action",
    "audit_event",
    "configure_telemetry",
    "error_boundary",
    "error_tracker",
    "log_endpoint",
    "logging_endpoint",
    "metrics_endpoint",
    "observe",
    "quota_guard",
    "sanitize_payload",
    "trace_span",
    "track_metrics",
    "tracing_span",
]
