import os
import time
from collections.abc import Callable, Iterator
from uuid import UUID, uuid4

import jwt
import pytest
from alembic.config import Config
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from alembic import command
from app.config import Settings, get_settings
from app.core.auth import JWTVerifier
from app.main import create_app

OWNER_URL = os.environ.get(
    "TEST_OWNER_DATABASE_URL",
    "postgresql+psycopg://jobpilot_owner:dev_owner_pw@localhost:5432/jobpilot_test",
)
APP_URL = os.environ.get(
    "TEST_APP_DATABASE_URL",
    "postgresql+psycopg://jobpilot_app:dev_app_pw@localhost:5432/jobpilot_test",
)
AUDIENCE = "authenticated"
ISSUER = "https://test.supabase.example/auth/v1"


def reset_and_migrate(target: str = "head") -> None:
    """Drop everything in the test DB and apply migrations as the owner role."""
    engine = create_engine(OWNER_URL, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT USAGE ON SCHEMA public TO jobpilot_app"))
    engine.dispose()
    os.environ["MIGRATION_DATABASE_URL"] = OWNER_URL
    get_settings.cache_clear()
    command.upgrade(Config("alembic.ini"), target)


@pytest.fixture(scope="session")
def migrated_db() -> None:
    try:
        reset_and_migrate()
    except Exception as exc:  # pragma: no cover - environment problem, fail loudly
        pytest.fail(f"Test database not available ({exc!r}). Run scripts/dev-db.sh first.")


@pytest.fixture(autouse=False)
def clean_db(migrated_db: None) -> Iterator[None]:
    owner = create_engine(OWNER_URL, isolation_level="AUTOCOMMIT")
    with owner.connect() as conn:
        conn.execute(text("TRUNCATE users CASCADE"))
    owner.dispose()
    yield


@pytest.fixture(scope="session")
def rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def make_token(rsa_key: rsa.RSAPrivateKey) -> Callable[..., str]:
    def _make(
        sub: UUID | str | None = None,
        email: str | None = "user@example.test",
        expires_in: int = 300,
        audience: str = AUDIENCE,
        issuer: str = ISSUER,
        key: rsa.RSAPrivateKey | None = None,
        algorithm: str = "RS256",
    ) -> str:
        now = int(time.time())
        claims: dict[str, object] = {
            "sub": str(sub or uuid4()),
            "aud": audience,
            "iss": issuer,
            "iat": now,
            "exp": now + expires_in,
        }
        if email:
            claims["email"] = email
        return jwt.encode(claims, key or rsa_key, algorithm=algorithm)

    return _make


@pytest.fixture
def client(rsa_key: rsa.RSAPrivateKey, clean_db: None) -> Iterator[TestClient]:
    settings = Settings(database_url=APP_URL, jwt_audience=AUDIENCE, jwt_issuer=ISSUER)
    verifier = JWTVerifier(lambda _token: rsa_key.public_key(), AUDIENCE, ISSUER)
    with TestClient(create_app(settings, verifier)) as test_client:
        yield test_client


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
