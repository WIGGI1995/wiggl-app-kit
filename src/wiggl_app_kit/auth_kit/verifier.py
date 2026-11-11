"""Cryptographic Keycloak JWT verifier with JWKS caching."""

from typing import Any

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm

from wiggl_app_kit.auth_kit.models import KeycloakUser


class TokenVerificationError(Exception):
    """Raised when token is expired, invalid or improperly signed."""


class KeycloakTokenVerifier:
    """Verifies Keycloak JWT tokens against cached JWKS public keys or secret."""

    def __init__(
        self,
        jwks_url: str | None = None,
        secret: str | None = None,
        client_id: str | None = None,
    ) -> None:
        self._jwks_url = jwks_url
        self._secret = secret
        self._client_id = client_id
        self._jwks_cache: dict[str, Any] = {}

    def _fetch_jwks(self) -> dict[str, Any]:
        if self._jwks_cache:
            return self._jwks_cache
        if not self._jwks_url:
            return {}
        try:
            resp = httpx.get(self._jwks_url, timeout=5.0)
            resp.raise_for_status()
            self._jwks_cache = resp.json()
            return self._jwks_cache
        except Exception as exc:
            raise TokenVerificationError(f"Failed to fetch JWKS: {exc}") from exc

    def _get_signing_key(self, token: str) -> Any:
        if self._secret:
            return self._secret
        jwks = self._fetch_jwks()
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return RSAAlgorithm.from_jwk(key)
        raise TokenVerificationError("Matching public key not found in JWKS")

    def _extract_roles(self, claims: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
        realm_roles = tuple(claims.get("realm_access", {}).get("roles", []))
        client_access = claims.get("resource_access", {})
        client_roles: tuple[str, ...] = ()
        if self._client_id and self._client_id in client_access:
            client_roles = tuple(client_access[self._client_id].get("roles", []))
        return realm_roles, client_roles

    def verify(self, token: str) -> KeycloakUser:
        """Decode and validate Keycloak JWT token."""
        key = self._get_signing_key(token)
        alg = "HS256" if self._secret else "RS256"
        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=[alg],
                options={"verify_aud": False},
            )
        except Exception as exc:
            raise TokenVerificationError(f"Token decode failed: {exc}") from exc

        realm_roles, client_roles = self._extract_roles(claims)
        username = claims.get("preferred_username") or claims.get("sub", "")
        return KeycloakUser(
            sub=claims.get("sub", ""),
            username=username,
            email=claims.get("email"),
            realm_roles=realm_roles,
            client_roles=client_roles,
        )
