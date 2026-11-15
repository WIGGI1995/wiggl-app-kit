"""Turnkey application bootstrap for WIGGLIFICATION tenant apps."""

import logging
import os
from collections.abc import Iterable
from typing import Any

from wiggl_app_kit.auth_kit.authentication import KeycloakAuthMiddleware, KeycloakTokenVerifier
from wiggl_app_kit.otel_kit.telemetry import configure_telemetry

logger = logging.getLogger("wiggl_app_kit.bootstrap")


def setup_wiggl_app(
    app: Any,
    service_name: str,
    keycloak_jwks_url: str | None = None,
    client_id: str | None = None,
    jwt_secret: str | None = None,
    otlp_endpoint: str | None = None,
    log_level: str | int | None = None,
    public_prefixes: Iterable[str] | None = None,
) -> None:
    """Universally bootstrap any FastAPI application for the WIGGLIFICATION platform.

    One-line call that sets up:
    1. Multi-level structured logging and OTLP / Loki telemetry shipping.
    2. Keycloak RS256 token verification with support for Bearer headers and cookies.
    3. Standard platform health-check public bypass whitelist.
    """
    resolved_level = log_level or os.environ.get("LOG_LEVEL", "DEBUG")
    configure_telemetry(
        service_name=service_name,
        otlp_endpoint=otlp_endpoint,
        log_level=resolved_level,
    )

    jwks = keycloak_jwks_url or os.environ.get("KEYCLOAK_JWKS_URL")
    if not jwks:
        base_url = os.environ.get("KEYCLOAK_URL", "http://keycloak:8080/auth").rstrip("/")
        realm = os.environ.get("KEYCLOAK_REALM", "platform")
        jwks = f"{base_url}/realms/{realm}/protocol/openid-connect/certs"

    cid = client_id or os.environ.get("KEYCLOAK_CLIENT_ID", f"app-{service_name}")
    sec = jwt_secret or os.environ.get("JWT_SECRET")

    verifier = KeycloakTokenVerifier(jwks_url=jwks, client_id=cid, secret=sec)

    default_public = {
        "/health",
        "/healthz",
        "/readyz",
        "/api/health",
        f"/apps/{service_name}/health",
        f"/apps/{service_name}/api/health",
        "/docs",
        "/openapi.json",
    }
    if public_prefixes:
        default_public.update(public_prefixes)

    app.add_middleware(
        KeycloakAuthMiddleware,
        verifier=verifier,
        public_prefixes=frozenset(default_public),
    )
    logging.getLogger(service_name).info(
        "WIGGLIFICATION tenant application bootstrapped successfully: service=%s, client_id=%s",
        service_name,
        cid,
    )


def get_app_logger(service_name: str) -> logging.Logger:
    """Retrieve standard logger for a tenant app."""
    return logging.getLogger(service_name)
