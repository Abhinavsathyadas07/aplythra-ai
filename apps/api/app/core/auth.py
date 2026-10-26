"""Supabase JWT verification. The API trusts only tokens signed by the project's JWKS."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import jwt
from jwt import PyJWKClient

# Key lookup: token -> verification key. Production uses the JWKS; tests inject a static key.
KeyProvider = Callable[[str], Any]

ALLOWED_ALGORITHMS = ["RS256", "ES256"]


class AuthError(Exception):
    """Token missing/invalid. The message is safe to return; it never echoes the token."""


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    email: str | None


class JWTVerifier:
    def __init__(self, key_provider: KeyProvider, audience: str, issuer: str | None = None) -> None:
        self._key_provider = key_provider
        self._audience = audience
        self._issuer = issuer

    @classmethod
    def from_jwks(cls, jwks_url: str, audience: str, issuer: str | None = None) -> "JWTVerifier":
        client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600, timeout=5)
        return cls(lambda token: client.get_signing_key_from_jwt(token).key, audience, issuer)

    def verify(self, token: str) -> AuthenticatedUser:
        try:
            key = self._key_provider(token)
            claims = jwt.decode(
                token,
                key,
                algorithms=ALLOWED_ALGORITHMS,
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "sub"], "verify_iss": self._issuer is not None},
            )
            return AuthenticatedUser(id=UUID(str(claims["sub"])), email=claims.get("email"))
        except (jwt.PyJWTError, ValueError) as exc:
            raise AuthError("Invalid or expired token") from exc
