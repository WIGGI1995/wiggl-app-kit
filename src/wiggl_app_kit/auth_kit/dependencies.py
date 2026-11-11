"""FastAPI route dependencies re-exported for backwards compatibility."""

from wiggl_app_kit.auth_kit.authentication import get_authenticated_user
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

get_current_user = get_authenticated_user

__all__ = [
    "AccessDeniedError",
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
