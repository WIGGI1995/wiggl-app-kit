"""Sensitive data and credential sanitizer for structured logging."""

from collections.abc import Mapping
from typing import Any

SENSITIVE_KEYS: frozenset[str] = frozenset({
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "key",
    "api_key",
    "content_base64",
    "payload",
})
REDACTED_VALUE: str = "***REDACTED***"


def sanitize_attribute_value(key: str, value: Any) -> Any:
    """Mask sensitive fields or return untouched value."""
    if key.lower() in SENSITIVE_KEYS:
        return REDACTED_VALUE
    if isinstance(value, Mapping):
        return sanitize_payload(value)
    return value


def sanitize_payload(data: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively scrub sensitive keys from log payload dictionary."""
    sanitized: dict[str, Any] = {}
    for key, value in data.items():
        sanitized[key] = sanitize_attribute_value(key, value)
    return sanitized
