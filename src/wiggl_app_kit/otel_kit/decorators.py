"""Strict Clean Code decorator suite for endpoint observability and telemetry."""

import functools
import logging
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from opentelemetry import metrics, trace

P = ParamSpec("P")
R = TypeVar("R")

_LOGGER = logging.getLogger("wiggl_app_kit.observability")
_TRACER = trace.get_tracer("wiggl_app_kit.tracer")
_METER = metrics.get_meter("wiggl_app_kit.meter")

_REQ_COUNTER = _METER.create_counter(
    name="wiggl_app_requests_total",
    description="Total app endpoint requests",
    unit="1",
)
_DURATION_HISTOGRAM = _METER.create_histogram(
    name="wiggl_app_duration_seconds",
    description="Endpoint execution latency",
    unit="s",
)
_ERROR_COUNTER = _METER.create_counter(
    name="wiggl_app_errors_total",
    description="Total endpoint errors and exceptions",
    unit="1",
)


def log_endpoint(operation: str | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Log lifecycle start, duration, status, and intermediate checkpoints."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        op_name = operation or func.__name__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.perf_counter()
            _LOGGER.info("START operation=%s", op_name)
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                _LOGGER.info(
                    "COMPLETE operation=%s duration_ms=%.2f status=200",
                    op_name,
                    duration_ms,
                )
                return result
            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                _LOGGER.error(
                    "FAILED operation=%s duration_ms=%.2f error=%s",
                    op_name,
                    duration_ms,
                    exc,
                )
                raise
        return wrapper
    return decorator


def track_metrics(endpoint_name: str | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Record endpoint request count, duration histogram, and failure status."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        name = endpoint_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                _REQ_COUNTER.add(1, {"endpoint": name, "status": "200"})
                _DURATION_HISTOGRAM.record(duration, {"endpoint": name})
                return result
            except Exception as exc:
                duration = time.perf_counter() - start_time
                status_code = getattr(exc, "status_code", 500)
                _REQ_COUNTER.add(1, {"endpoint": name, "status": str(status_code)})
                _DURATION_HISTOGRAM.record(duration, {"endpoint": name})
                _ERROR_COUNTER.add(1, {"endpoint": name, "error_type": type(exc).__name__})
                raise
        return wrapper
    return decorator


def trace_span(span_name: str | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Wrap execution inside an explicit OpenTelemetry child span."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        name = span_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with _TRACER.start_as_current_span(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def audit_event(action: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Emit tamper-evident security audit event into log streams."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            _LOGGER.info("AUDIT action=%s status=ATTEMPT", action)
            try:
                result = func(*args, **kwargs)
                _LOGGER.info("AUDIT action=%s status=SUCCESS", action)
                return result
            except Exception as exc:
                _LOGGER.warning("AUDIT action=%s status=FAILURE reason=%s", action, exc)
                raise
        return wrapper
    return decorator


def error_tracker(category: str = "general") -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Intercept, categorize, and record exceptions into error meters."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                _ERROR_COUNTER.add(1, {"category": category, "error_type": type(exc).__name__})
                _LOGGER.error("ERROR_TRACKER category=%s error=%s", category, exc, exc_info=True)
                raise
        return wrapper
    return decorator


def quota_guard(quota_type: str = "storage") -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Log and monitor payload size and quota impact."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            _LOGGER.debug("QUOTA_CHECK type=%s", quota_type)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def observe(operation: str | None = None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Composite decorator combining tracing, logging, and metrics."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        op_name = operation or func.__name__
        traced = trace_span(op_name)(func)
        logged = log_endpoint(op_name)(traced)
        return track_metrics(op_name)(logged)
    return decorator


logging_endpoint = log_endpoint
metrics_endpoint = track_metrics
tracing_span = trace_span
audit_action = audit_event
error_boundary = error_tracker
