"""FastAPI middleware for seamless Keycloak token verification and user context."""

from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from wiggl_app_kit.auth_kit.verifier import KeycloakTokenVerifier, TokenVerificationError

DEFAULT_PUBLIC_PREFIXES: frozenset[str] = frozenset({
    "/health",
    "/info",
    "/docs",
    "/openapi.json",
    "/metrics",
    "/favicon.ico",
})


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

    def _extract_token(self, request: Request) -> str | None:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        return auth_header.removeprefix("Bearer ").strip()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Any],
    ) -> Response:
        """Inspect authorization header and inject verified user context."""
        if request.method == "OPTIONS" or self._is_public_path(request.url.path):
            response: Response = await call_next(request)
            return response

        token = self._extract_token(request)
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
