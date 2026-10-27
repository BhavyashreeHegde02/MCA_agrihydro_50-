"""Application settings, read from the environment.

Nothing is hard-coded that differs between a laptop and a server, and no secret
has a usable production default. The one deliberate convenience is the database
URL: it falls back to a local SQLite file so the API starts with no
infrastructure at all, which is what makes ``uvicorn app.main:app`` work
immediately after a clone. PostgreSQL is used whenever ``DATABASE_URL`` is set,
and Docker Compose sets it.
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# backend/app/core/config.py -> backend/app/core -> backend/app -> backend -> repo
REPO_ROOT = Path(__file__).resolve().parents[3]

#: Origins the API accepts browser calls from when nothing is configured.
#: The local frontend in both spellings a developer might use.
DEFAULT_CORS_ORIGINS: tuple[str, ...] = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


class Settings(BaseSettings):
    """Everything the service needs to run."""

    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", REPO_ROOT / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # -- identity ---------------------------------------------------------
    app_name: str = "Jalachakra API"
    api_v1_prefix: str = "/api/v1"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)

    # -- security ---------------------------------------------------------
    # Generated per process when unset, which keeps development frictionless
    # while guaranteeing that a deployment without SECRET_KEY invalidates its
    # own tokens on restart rather than shipping a known key.
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 7 * 24 * 60

    # -- database ---------------------------------------------------------
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{(REPO_ROOT / 'backend' / 'jalachakra.db').as_posix()}"
    )
    sql_echo: bool = False

    # -- machine learning -------------------------------------------------
    model_registry_dir: Path = Field(default=REPO_ROOT / "artifacts" / "models")
    processed_data_dir: Path = Field(default=REPO_ROOT / "datasets" / "processed")
    require_active_model: bool = Field(
        default=False,
        description=(
            "When true the service refuses to start without a promoted model. "
            "Left false so the physics baseline remains usable on its own, with "
            "the ML fields reported as unavailable rather than fabricated."
        ),
    )

    # -- weather provider -------------------------------------------------
    weather_provider: str = Field(default="none")
    weather_api_key: str | None = Field(default=None)
    weather_cache_ttl_seconds: int = 1800
    weather_request_timeout_seconds: float = 8.0

    # -- CORS -------------------------------------------------------------
    #: Origins allowed to call this API from a browser.
    #:
    #: The default is the local frontend, not "*". A wildcard cannot be
    #: combined with credentialed requests: the CORS specification forbids
    #: returning `Access-Control-Allow-Origin: *` alongside
    #: `Allow-Credentials: true`, and browsers drop the response. Since this
    #: API is called with cookies, "*" would not have worked in a browser
    #: anyway - it would only have looked permissive.
    #: ``NoDecode`` is load-bearing, not decoration.
    #:
    #: pydantic-settings JSON-decodes any complex-typed field coming from the
    #: environment *before* validators run. A comma-separated list is not JSON,
    #: so "CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000" raised a
    #: SettingsError at import and the process died before serving anything.
    #: The same was true of the "*" that docker-compose shipped, which meant the
    #: container could never have started with that variable set. NoDecode
    #: hands the raw string to the validator below instead.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: list(DEFAULT_CORS_ORIGINS)
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            origins = [origin.strip() for origin in value.split(",") if origin.strip()]
            # An empty or whitespace-only value falls back to the default
            # rather than to no origins at all. An empty allow-list is a
            # miserable thing to debug: the server logs nothing, and every
            # request simply fails inside the browser. Returning None here
            # would not reach the default -- pydantic would validate None
            # against list[str] and reject it -- so the default is returned
            # explicitly.
            return origins or list(DEFAULT_CORS_ORIGINS)
        return value

    @property
    def cors_allows_wildcard(self) -> bool:
        return "*" in self.cors_origins

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
