"""Keycloak Authentication Kit for FastAPI tenant applications."""

from wiggl_app_kit.auth_kit.dependencies import get_current_user, require_roles
from wiggl_app_kit.auth_kit.middleware import DEFAULT_PUBLIC_PREFIXES, KeycloakAuthMiddleware
from wiggl_app_kit.auth_kit.models import KeycloakUser
from wiggl_app_kit.auth_kit.verifier import KeycloakTokenVerifier, TokenVerificationError

__all__ = [
    "DEFAULT_PUBLIC_PREFIXES",
    "KeycloakAuthMiddleware",
    "KeycloakTokenVerifier",
    "KeycloakUser",
    "TokenVerificationError",
    "get_current_user",
    "require_roles",
]
