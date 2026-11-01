import pytest
from pydantic import ValidationError

from app.config import Settings


def test_defaults_are_development_safe() -> None:
    settings = Settings()
    assert settings.app_env == "development"
    assert settings.cors_origin_list == ["http://localhost:3000"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"supabase_jwks_url": ""},
        {"supabase_jwks_url": "https://x.example/jwks", "cors_origins": "*"},
        {"supabase_jwks_url": "https://x.example/jwks"},  # still uses dev DB password
    ],
)
def test_production_rejects_unsafe_settings(overrides: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production", **overrides)


def test_production_accepts_safe_settings() -> None:
    Settings(
        app_env="production",
        supabase_jwks_url="https://x.example/jwks",
        cors_origins="https://app.example",
        database_url="postgresql+psycopg://app:strong@db.example/jobpilot",
    )
