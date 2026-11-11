"""Unit tests for OpenTelemetry decorators, sanitizer, and telemetry configuration."""

import pytest
from opentelemetry import trace

from wiggl_app_kit.otel_kit import (
    audit_event,
    configure_telemetry,
    error_tracker,
    log_endpoint,
    observe,
    quota_guard,
    sanitize_payload,
    track_metrics,
)


def test_sanitizer_masks_credentials() -> None:
    data = {
        "user": "test",
        "password": "my_password",
        "token": "secret_token",
        "api_key": "xyz123",
        "safe_int": 100,
    }
    sanitized = sanitize_payload(data)
    assert sanitized["user"] == "test"
    assert sanitized["password"] == "***REDACTED***"
    assert sanitized["token"] == "***REDACTED***"
    assert sanitized["api_key"] == "***REDACTED***"
    assert sanitized["safe_int"] == 100


def test_decorators_pipeline() -> None:
    configure_telemetry(service_name="test-service")

    @observe("test.full")
    @audit_event("test.audit")
    @quota_guard("test.quota")
    def sample_op(val: int) -> int:
        span = trace.get_current_span()
        assert span.get_span_context().is_valid
        return val * 3

    assert sample_op(4) == 12


def test_error_tracker_and_logging_on_failure() -> None:
    @error_tracker("test.err")
    @log_endpoint("test.fail")
    @track_metrics("test.fail_metrics")
    def fail_op() -> None:
        raise ValueError("Intentional test error")

    with pytest.raises(ValueError, match="Intentional test error"):
        fail_op()
