"""Validated PostgreSQL SELECT query construction."""

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Tuple

from app.resources import ResourceDefinition


CONTROL_PARAMETERS = {"field", "search"}


class QueryValidationError(ValueError):
    """Raised when API query parameters cannot produce a valid SQL query."""

    def __init__(self, message: str, searchable_fields: Sequence[str]):
        super().__init__(message)
        self.searchable_fields = searchable_fields


@dataclass(frozen=True)
class SelectQuery:
    """A SQL statement plus values that must be passed separately to psycopg."""

    statement: str
    parameters: Tuple[object, ...]


def _contains_pattern(value: str) -> str:
    escaped = (
        value.strip()
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{escaped}%"


def _integer_value(field: str, value: str, searchable_fields: Sequence[str]) -> int:
    try:
        return int(value.strip())
    except ValueError as error:
        raise QueryValidationError(
            f"{field} must be an integer.", searchable_fields
        ) from error


def _field_condition(
    resource: ResourceDefinition, api_field: str, value: str
) -> Tuple[str, object]:
    database_field = resource.fields[api_field]
    if api_field in resource.exact_fields:
        parameter = _integer_value(api_field, value, resource.searchable_fields)
        return f"{database_field} = %s", parameter
    return (
        f"CAST({database_field} AS TEXT) ILIKE %s ESCAPE E'\\\\'",
        _contains_pattern(value),
    )


def build_select_query(
    resource: ResourceDefinition,
    query_parameters: Mapping[str, Sequence[str]],
    record_id: Optional[str] = None,
) -> SelectQuery:
    """Build a parameterized SELECT using only allowlisted identifiers.

    Exact numeric fields use equality so PostgreSQL can use their indexes. Text
    fields use case-insensitive partial matching. Values always remain separate
    from the SQL statement and are passed to psycopg as parameters.
    """

    select_columns = ", ".join(
        f'{database_field} AS "{api_field}"'
        for api_field, database_field in resource.fields.items()
    )
    statement = f"SELECT {select_columns} FROM {resource.table}"
    conditions = []
    parameters = []

    if record_id is not None:
        conditions.append("id = %s")
        parameters.append(
            _integer_value("id", record_id, resource.searchable_fields)
        )
    else:
        requested_field = query_parameters.get("field", [None])[0]
        search_value = query_parameters.get("search", [None])[0]

        if requested_field and requested_field not in resource.fields:
            raise QueryValidationError(
                f"Unknown search field: {requested_field}",
                resource.searchable_fields,
            )
        if requested_field and search_value is None:
            raise QueryValidationError(
                "The search query parameter is required when field is provided.",
                resource.searchable_fields,
            )

        if requested_field:
            condition, parameter = _field_condition(
                resource, requested_field, search_value
            )
            conditions.append(condition)
            parameters.append(parameter)
        elif search_value is not None:
            pattern = _contains_pattern(search_value)
            search_conditions = [
                f"CAST({database_field} AS TEXT) ILIKE %s ESCAPE E'\\\\'"
                for database_field in resource.fields.values()
            ]
            conditions.append("(" + " OR ".join(search_conditions) + ")")
            parameters.extend([pattern] * len(search_conditions))

        for api_field, values in query_parameters.items():
            if api_field in CONTROL_PARAMETERS:
                continue
            if api_field not in resource.fields:
                raise QueryValidationError(
                    f"Unknown query parameter: {api_field}",
                    resource.searchable_fields,
                )

            for value in values:
                condition, parameter = _field_condition(resource, api_field, value)
                conditions.append(condition)
                parameters.append(parameter)

    if conditions:
        statement += " WHERE " + " AND ".join(conditions)
    statement += " ORDER BY id"
    if record_id is not None:
        statement += " LIMIT 1"

    return SelectQuery(statement=statement, parameters=tuple(parameters))
