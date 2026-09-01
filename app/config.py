"""Environment and application configuration."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional


BASE_DIRECTORY = Path(__file__).resolve().parent.parent


class ConfigurationError(ValueError):
    """Raised when required application configuration is missing."""


@dataclass(frozen=True)
class DatabaseSettings:
    """Validated PostgreSQL connection settings.

    ``database_url`` takes precedence over the individual connection fields.
    """

    database_url: Optional[str]
    host: Optional[str]
    port: str
    database: str
    user: Optional[str]
    password: Optional[str]
    sslmode: str


@dataclass(frozen=True)
class ServerSettings:
    """Host and port used by the local Uvicorn entry point."""

    host: str
    port: int


@dataclass(frozen=True)
class StorageSettings:
    """Supabase Storage API settings used to sign upload URLs."""

    supabase_url: str
    api_key: str
    bucket: str


def load_env_file(env_path: Path = BASE_DIRECTORY / ".env") -> None:
    """Load a simple .env file without overriding existing environment values."""
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def get_database_settings(
    environment: Optional[Mapping[str, str]] = None,
) -> DatabaseSettings:
    """Return validated database settings from a supplied or process environment.

    Raises:
        ConfigurationError: If neither ``DATABASE_URL`` nor all required
            individual connection values are available.
    """

    source = environment if environment is not None else os.environ
    settings = DatabaseSettings(
        database_url=source.get("DATABASE_URL"),
        host=source.get("DB_HOST"),
        port=source.get("DB_PORT", "5432"),
        database=source.get("DB_NAME", "postgres"),
        user=source.get("DB_USER"),
        password=source.get("DB_PASSWORD"),
        sslmode=source.get("DB_SSLMODE", "require"),
    )

    if settings.database_url:
        return settings

    required_values = {
        "DB_HOST": settings.host,
        "DB_USER": settings.user,
        "DB_PASSWORD": settings.password,
    }
    missing = [name for name, value in required_values.items() if not value]
    if missing:
        raise ConfigurationError(
            "Missing database environment variables: " + ", ".join(missing)
        )

    return settings


def get_server_settings(
    environment: Optional[Mapping[str, str]] = None,
) -> ServerSettings:
    """Return server settings and validate that ``PORT`` is usable."""

    source = environment if environment is not None else os.environ
    try:
        port = int(source.get("PORT", "3000"))
    except ValueError as error:
        raise ConfigurationError("PORT must be an integer.") from error

    if not 1 <= port <= 65535:
        raise ConfigurationError("PORT must be between 1 and 65535.")

    return ServerSettings(host=source.get("HOST", "0.0.0.0"), port=port)


def get_storage_settings(
    environment: Optional[Mapping[str, str]] = None,
) -> StorageSettings:
    """Return validated Supabase Storage settings.

    ``SUPABASE_SECRET_KEY`` is preferred. The legacy service-role key remains
    supported during migration to Supabase's current secret-key format.
    """

    source = environment if environment is not None else os.environ
    supabase_url = source.get("SUPABASE_URL", "").rstrip("/")
    api_key = source.get("SUPABASE_SECRET_KEY") or source.get(
        "SUPABASE_SERVICE_ROLE_KEY"
    )
    bucket = source.get("SUPABASE_STORAGE_BUCKET", "case-files")

    missing = []
    if not supabase_url:
        missing.append("SUPABASE_URL")
    if not api_key:
        missing.append("SUPABASE_SECRET_KEY or SUPABASE_SERVICE_ROLE_KEY")
    if missing:
        raise ConfigurationError(
            "Missing Supabase Storage environment variables: " + ", ".join(missing)
        )
    if not supabase_url.startswith(("https://", "http://")):
        raise ConfigurationError("SUPABASE_URL must start with http:// or https://.")
    if not bucket or "/" in bucket:
        raise ConfigurationError(
            "SUPABASE_STORAGE_BUCKET must be a non-empty bucket name."
        )

    return StorageSettings(
        supabase_url=supabase_url,
        api_key=api_key,
        bucket=bucket,
    )
