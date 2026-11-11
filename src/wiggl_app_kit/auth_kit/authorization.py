"""Authorization module for role, permission, and scope enforcement."""

from collections.abc import Callable

from fastapi import HTTPException, Request, status

from wiggl_app_kit.auth_kit.authentication import get_authenticated_user
from wiggl_app_kit.auth_kit.models import KeycloakUser


class AccessDeniedError(HTTPException):
    """Raised when an authenticated user lacks required privileges."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def require_roles(*roles: str) -> Callable[[Request], KeycloakUser]:
    """Dependency enforcing that current user holds at least one specified role."""
    def dependency(request: Request) -> KeycloakUser:
        user = get_authenticated_user(request)
        if not user.has_any_role(*roles):
            raise AccessDeniedError(
                f"Missing required role. Need one of: {', '.join(roles)}",
            )
        return user
    return dependency


def require_all_roles(*roles: str) -> Callable[[Request], KeycloakUser]:
    """Dependency enforcing that current user holds every single specified role."""
    def dependency(request: Request) -> KeycloakUser:
        user = get_authenticated_user(request)
        if not user.has_all_roles(*roles):
            raise AccessDeniedError(
                f"Missing required roles. Must hold all of: {', '.join(roles)}",
            )
        return user
    return dependency


def require_realm_role(role: str) -> Callable[[Request], KeycloakUser]:
    """Dependency enforcing that current user holds a specific realm role."""
    def dependency(request: Request) -> KeycloakUser:
        user = get_authenticated_user(request)
        if role not in user.realm_roles:
            raise AccessDeniedError(f"Missing required realm role: {role}")
        return user
    return dependency


def require_client_role(role: str) -> Callable[[Request], KeycloakUser]:
    """Dependency enforcing that current user holds a specific client role."""
    def dependency(request: Request) -> KeycloakUser:
        user = get_authenticated_user(request)
        if role not in user.client_roles:
            raise AccessDeniedError(f"Missing required client role: {role}")
        return user
    return dependency


def require_permissions(*permissions: str) -> Callable[[Request], KeycloakUser]:
    """Dependency enforcing that current user possesses at least one permission."""
    def dependency(request: Request) -> KeycloakUser:
        user = get_authenticated_user(request)
        if not any(user.has_permission(p) for p in permissions):
            raise AccessDeniedError(
                f"Missing required permission. Need one of: {', '.join(permissions)}",
            )
        return user
    return dependency


def require_all_permissions(*permissions: str) -> Callable[[Request], KeycloakUser]:
    """Dependency enforcing that current user possesses all specified permissions."""
    def dependency(request: Request) -> KeycloakUser:
        user = get_authenticated_user(request)
        if not all(user.has_permission(p) for p in permissions):
            raise AccessDeniedError(
                f"Missing required permissions. Must possess all: {', '.join(permissions)}",
            )
        return user
    return dependency


def require_scope(scope: str) -> Callable[[Request], KeycloakUser]:
    """Dependency enforcing that current user's token possesses a specific scope."""
    def dependency(request: Request) -> KeycloakUser:
        user = get_authenticated_user(request)
        if not user.has_scope(scope):
            raise AccessDeniedError(f"Missing required token scope: {scope}")
        return user
    return dependency


require_any_role = require_roles

__all__ = [
    "AccessDeniedError",
    "require_all_permissions",
    "require_all_roles",
    "require_any_role",
    "require_client_role",
    "require_permissions",
    "require_realm_role",
    "require_roles",
    "require_scope",
]
