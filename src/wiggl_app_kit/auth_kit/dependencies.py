"""FastAPI route dependencies for extracting user context and enforcing roles."""

from collections.abc import Callable

from fastapi import HTTPException, Request, status

from wiggl_app_kit.auth_kit.models import KeycloakUser


def get_current_user(request: Request) -> KeycloakUser:
    """Extract authenticated KeycloakUser from request state."""
    user = getattr(request.state, "user", None)
    if not isinstance(user, KeycloakUser):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


def require_roles(*roles: str) -> Callable[[Request], KeycloakUser]:
    """Dependency enforcing that current user holds at least one specified role."""
    def dependency(request: Request) -> KeycloakUser:
        user = get_current_user(request)
        if not user.has_any_role(*roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role. Need one of: {', '.join(roles)}",
            )
        return user
    return dependency
