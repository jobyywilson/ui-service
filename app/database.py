"""PostgreSQL connection and query execution."""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Sequence

from app.config import ConfigurationError, get_database_settings


class DatabaseAccessError(RuntimeError):
    """Raised when PostgreSQL cannot execute a request."""


def _json_compatible(value: Any) -> Any:
    """Convert PostgreSQL-specific scalar values to JSON-compatible values."""

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    return value


def execute_query(
    statement: str, parameters: Sequence[object]
) -> List[Dict[str, Any]]:
    """Execute one parameterized SELECT and return JSON-compatible dictionaries.

    A new connection is opened per request. This is suitable for the prototype;
    a connection pool can replace this function without changing the service or
    route layers.

    Raises:
        ConfigurationError: If the driver or connection settings are missing.
        DatabaseAccessError: If PostgreSQL cannot execute the query.
    """

    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as error:
        raise ConfigurationError(
            "PostgreSQL driver is not installed. Run: pip install -r requirements.txt"
        ) from error

    settings = get_database_settings()
    try:
        if settings.database_url:
            connection = psycopg.connect(
                settings.database_url,
                row_factory=dict_row,
                connect_timeout=10,
            )
        else:
            connection = psycopg.connect(
                host=settings.host,
                port=settings.port,
                dbname=settings.database,
                user=settings.user,
                password=settings.password,
                sslmode=settings.sslmode,
                row_factory=dict_row,
                connect_timeout=10,
            )

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(statement, parameters)
                rows = cursor.fetchall()
        return [_json_compatible(dict(row)) for row in rows]
    except Exception as error:
        raise DatabaseAccessError("PostgreSQL query failed.") from error
