from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables (and a local .env in development)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    # Runtime role (subject to RLS). Migrations use migration_database_url when set.
    database_url: str = "postgresql+psycopg://jobpilot_app:dev_app_pw@localhost:5432/jobpilot"
    migration_database_url: str | None = None

    # Supabase Auth: the API only verifies JWTs, it never handles passwords.
    supabase_url: str = ""
    supabase_jwks_url: str = ""
    jwt_audience: str = "authenticated"
    jwt_issuer: str | None = None

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @model_validator(mode="after")
    def _check_production(self) -> "Settings":
        if self.app_env == "production":
            if not self.supabase_jwks_url:
                raise ValueError("SUPABASE_JWKS_URL is required in production")
            if "*" in self.cors_origin_list:
                raise ValueError("CORS_ORIGINS must not contain '*' in production")
            if "dev_app_pw" in self.database_url:
                raise ValueError("DATABASE_URL still uses the development password")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
