"""Keycloak Authentication and Authorization Kit for WIGGLIFICATION."""

from wiggl_app_kit.auth_kit.authentication import (
    DEFAULT_PUBLIC_PREFIXES,
    KeycloakAuthMiddleware,
    extract_bearer_token,
    get_authenticated_user,
)
from wiggl_app_kit.auth_kit.authorization import (
    AccessDeniedError,
    require_all_permissions,
    require_all_roles,
    require_any_role,
    require_client_role,
    require_permissions,
    require_realm_role,
    require_roles,
    require_scope,
)
from wiggl_app_kit.auth_kit.models import KeycloakUser
from wiggl_app_kit.auth_kit.verifier import KeycloakTokenVerifier, TokenVerificationError

get_current_user = get_authenticated_user

__all__ = [
    "DEFAULT_PUBLIC_PREFIXES",
    "AccessDeniedError",
    "KeycloakAuthMiddleware",
    "KeycloakTokenVerifier",
    "KeycloakUser",
    "TokenVerificationError",
    "extract_bearer_token",
    "get_authenticated_user",
    "get_current_user",
    "require_all_permissions",
    "require_all_roles",
    "require_any_role",
    "require_client_role",
    "require_permissions",
    "require_realm_role",
    "require_roles",
    "require_scope",
]
