"""Domain models representing Keycloak authenticated user identity."""

from pydantic import BaseModel, ConfigDict, Field


class KeycloakUser(BaseModel):
    """Immutable representation of an authenticated Keycloak user identity."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    sub: str
    username: str
    email: str | None = None
    realm_roles: tuple[str, ...] = Field(default_factory=tuple)
    client_roles: tuple[str, ...] = Field(default_factory=tuple)

    @property
    def all_roles(self) -> frozenset[str]:
        """Return combined unique set of realm and client roles."""
        return frozenset(self.realm_roles) | frozenset(self.client_roles)

    def has_role(self, role: str) -> bool:
        """Check if user has a specific realm or client role."""
        return role in self.all_roles

    def has_any_role(self, *roles: str) -> bool:
        """Check if user has at least one of the specified roles."""
        return bool(self.all_roles & set(roles))
