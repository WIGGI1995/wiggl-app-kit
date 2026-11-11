"""Authentication module for Keycloak JWT verification and request credentials."""

from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from wiggl_app_kit.auth_kit.models import KeycloakUser
from wiggl_app_kit.auth_kit.verifier import KeycloakTokenVerifier, TokenVerificationError

DEFAULT_PUBLIC_PREFIXES: frozenset[str] = frozenset({
    "/health",
    "/info",
    "/docs",
    "/openapi.json",
    "/metrics",
    "/favicon.ico",
})


def extract_bearer_token(request: Request) -> str | None:
    """Extract raw bearer token string from request Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.removeprefix("Bearer ").strip()


def get_authenticated_user(request: Request) -> KeycloakUser:
    """Retrieve authenticated KeycloakUser from request state or raise 401."""
    from fastapi import HTTPException, status
    user = getattr(request.state, "user", None)
    if not isinstance(user, KeycloakUser):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


class KeycloakAuthMiddleware(BaseHTTPMiddleware):
    """Enforces valid Keycloak JWT bearer authentication on protected routes."""

    def __init__(
        self,
        app: Any,
        verifier: KeycloakTokenVerifier,
        public_prefixes: frozenset[str] = DEFAULT_PUBLIC_PREFIXES,
    ) -> None:
        super().__init__(app)
        self._verifier = verifier
        self._public_prefixes = public_prefixes

    def _is_public_path(self, path: str) -> bool:
        return any(path.endswith(prefix) or prefix in path for prefix in self._public_prefixes)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        """Inspect authorization header and inject verified user context."""
        if request.method == "OPTIONS" or self._is_public_path(request.url.path):
            response: Response = await call_next(request)
            return response

        token = extract_bearer_token(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        try:
            user = self._verifier.verify(token)
            request.state.user = user
        except TokenVerificationError as exc:
            return JSONResponse(
                status_code=401,
                content={"detail": f"Unauthorized: {exc}"},
            )

        res: Response = await call_next(request)
        return res


__all__ = [
    "DEFAULT_PUBLIC_PREFIXES",
    "KeycloakAuthMiddleware",
    "KeycloakTokenVerifier",
    "TokenVerificationError",
    "extract_bearer_token",
    "get_authenticated_user",
]
