"""OpenTelemetry, Metrics, and Structured Logging bootstrap."""

import json
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

DEFAULT_SERVICE_NAME = "wiggl-app"


class JsonLogFormatter(logging.Formatter):
    """Formats log records as JSON lines with trace context."""

    def __init__(self, service_name: str = DEFAULT_SERVICE_NAME) -> None:
        super().__init__()
        self._service_name = service_name

    def _extract_trace_context(self) -> tuple[str, str]:
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if not ctx.is_valid:
            return "", ""
        return format(ctx.trace_id, "032x"), format(ctx.span_id, "016x")

    def format(self, record: logging.LogRecord) -> str:
        trace_id, span_id = self._extract_trace_context()
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "app": self._service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id,
            "span_id": span_id,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"))


class HttpOtlpLogHandler(logging.Handler):
    """Direct HTTP OTLP log exporter targeting OTel Collector."""

    def __init__(self, endpoint_url: str, service_name: str) -> None:
        super().__init__()
        self._endpoint_url = endpoint_url.rstrip("/") + "/v1/logs"
        self._service_name = service_name
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import httpx
            self._client = httpx.Client(timeout=2.0)
        return self._client

    def emit(self, record: logging.LogRecord) -> None:
        span = trace.get_current_span()
        ctx = span.get_span_context()
        trace_id_hex = format(ctx.trace_id, "032x") if ctx.is_valid else ""
        span_id_hex = format(ctx.span_id, "016x") if ctx.is_valid else ""

        body_payload = {
            "resourceLogs": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": self._service_name}},
                        {"key": "app", "value": {"stringValue": self._service_name}},
                    ]
                },
                "scopeLogs": [{
                    "logRecords": [{
                        "timeUnixNano": str(time.time_ns()),
                        "severityText": record.levelname,
                        "body": {"stringValue": record.getMessage()},
                        "traceId": trace_id_hex,
                        "spanId": span_id_hex,
                    }]
                }]
            }]
        }
        try:
            client = self._get_client()
            client.post(self._endpoint_url, json=body_payload)
        except Exception as exc:  # noqa: BLE001
            logging.getLogger("wiggl_app_kit.telemetry").debug("OTLP log push failed: %s", exc)


def configure_telemetry(
    service_name: str,
    otlp_endpoint: str | None = None,
    log_level: int | str | None = None,
) -> None:
    """Initialize OpenTelemetry tracer, meter, and structured logging at configurable level."""
    resource = Resource.create({"service.name": service_name, "app": service_name})
    endpoint = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

    # Trace Provider
    trace_provider = TracerProvider(resource=resource)
    if endpoint:
        try:
            trace_exporter = OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")
            trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        except Exception as exc:  # noqa: BLE001
            logger = logging.getLogger("wiggl_app_kit.telemetry")
            logger.warning("Span exporter init failed: %s", exc)
    trace.set_tracer_provider(trace_provider)

    # Meter Provider
    readers = []
    if endpoint:
        try:
            metric_exporter = OTLPMetricExporter(endpoint=f"{endpoint.rstrip('/')}/v1/metrics")
            reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
            readers.append(reader)
        except Exception as exc:  # noqa: BLE001
            logger = logging.getLogger("wiggl_app_kit.telemetry")
            logger.warning("Metric exporter init failed: %s", exc)
    meter_provider = MeterProvider(resource=resource, metric_readers=readers)
    metrics.set_meter_provider(meter_provider)

    # Structured Logging & Loki OTLP Handler
    env_level = log_level or os.environ.get("LOG_LEVEL", "DEBUG")
    resolved_level = (
        getattr(logging, str(env_level).upper(), logging.DEBUG)
        if isinstance(env_level, str)
        else env_level
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(resolved_level)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonLogFormatter(service_name))
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    if endpoint:
        otlp_handler = HttpOtlpLogHandler(endpoint, service_name)
        root_logger.addHandler(otlp_handler)
