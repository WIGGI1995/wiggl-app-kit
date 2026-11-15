# Changelog

All notable changes to the `wiggl-app-kit` SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-11-15
### Added
- One-line turnkey bootstrap function `setup_wiggl_app(app, service_name)` configuring authentication, telemetry across all log levels, and health-check public bypass.
- Top-level re-exports for all decorators, verifiers, and middleware directly from `wiggl_app_kit`.
- Multi-level logging formatting (`[LEVEL] logger: message`) with clean severity tagging for Loki and Grafana.
- Optional / safe fallback imports for OTLP span and metric exporters.
- Empty traceId/spanId omission guard preventing OTel Collector 400 Bad Request errors outside active spans.

## [0.2.0] - 2026-11-11
### Added
- Explicit modularization into `auth_kit.authentication` (JWT verification, KeycloakAuthMiddleware, public paths, bearer extraction) and `auth_kit.authorization` (RBAC, ABAC, permissions, scopes, `AccessDeniedError`).
- Expanded authorization dependency suite: `require_roles`, `require_all_roles`, `require_realm_role`, `require_client_role`, `require_permissions`, `require_all_permissions`, `require_scope`.
- OpenTelemetry automated OTLP wiring for Traces (`OTLPSpanExporter`), Metrics (`OTLPMetricExporter`), and Logs (`HttpOtlpLogHandler`).
- Automated GitHub Actions release pipeline with SemVer tagging, `.whl` and `.tar.gz` package generation, GitHub Releases, and optional PyPI publishing.
- PEP 561 `py.typed` marker for full strict typing support in downstream apps.

## [0.1.0] - 2026-11-11
### Added
- Initial release of `wiggl-app-kit`.
- `auth_kit`: `KeycloakTokenVerifier`, `KeycloakAuthMiddleware`, and `KeycloakUser`.
- `otel_kit`: 7-decorator observability suite (`@observe`, `@log_endpoint`, `@track_metrics`, `@trace_span`, `@audit_event`, `@error_tracker`, `@quota_guard`).
