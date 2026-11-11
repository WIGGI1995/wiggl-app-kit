"""Keycloak authentication middleware re-exported for backwards compatibility."""

from wiggl_app_kit.auth_kit.authentication import (
    DEFAULT_PUBLIC_PREFIXES,
    KeycloakAuthMiddleware,
    extract_bearer_token,
)

__all__ = [
    "DEFAULT_PUBLIC_PREFIXES",
    "KeycloakAuthMiddleware",
    "extract_bearer_token",
]
