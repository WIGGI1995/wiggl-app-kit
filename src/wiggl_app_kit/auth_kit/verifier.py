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
        realm_roles_list: list[str] = []
        realm_access = claims.get("realm_access")
        if isinstance(realm_access, dict):
            raw = realm_access.get("roles")
            if isinstance(raw, list):
                realm_roles_list.extend(str(r) for r in raw)
        top_roles = claims.get("roles")
        if isinstance(top_roles, list):
            realm_roles_list.extend(str(r) for r in top_roles)
        realm_roles = tuple(dict.fromkeys(realm_roles_list))

        client_roles: tuple[str, ...] = ()
        client_access = claims.get("resource_access")
        if self._client_id and isinstance(client_access, dict) and self._client_id in client_access:
            c_raw = client_access[self._client_id].get("roles", [])
            if isinstance(c_raw, list):
                client_roles = tuple(str(r) for r in c_raw)
        return realm_roles, client_roles

    def verify(self, token: str) -> KeycloakUser:
        """Decode and validate Keycloak JWT token."""
        key = self._get_signing_key(token)
        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=["HS256", "RS256"],
                options={"verify_aud": False},
            )
        except Exception as exc:
            raise TokenVerificationError(f"Token decode failed: {exc}") from exc

        realm_roles, client_roles = self._extract_roles(claims)
        username = str(claims.get("preferred_username") or claims.get("sub", ""))
        return KeycloakUser(
            sub=str(claims.get("sub", "")),
            username=username,
            email=claims.get("email"),
            realm_roles=realm_roles,
            client_roles=client_roles,
        )
