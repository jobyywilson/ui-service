# Architecture

The application separates HTTP concerns from database and query logic so each
layer can be tested or replaced independently.

## Request flow

```text
HTTP request
  -> FastAPI route and Pydantic query validation
  -> resource service
  -> allowlisted, parameterized query builder
  -> psycopg database adapter
  -> Pydantic response validation
  -> camelCase JSON response
```

## Modules

| Module | Responsibility |
| --- | --- |
| `app/main.py` | Builds FastAPI, configures CORS, and registers error handlers. |
| `app/routes.py` | Declares the four read endpoints and response contracts. |
| `app/filters.py` | Defines typed, camelCase query parameters for OpenAPI. |
| `app/models.py` | Defines the case and file response schemas. |
| `app/services.py` | Coordinates query construction and database execution. |
| `app/query_builder.py` | Validates filters and produces parameterized SELECTs. |
| `app/resources.py` | Holds the fixed API-to-database identifier allowlists. |
| `app/database.py` | Opens PostgreSQL connections and serializes result values. |
| `app/storage.py` | Calls Supabase Storage to create signed upload URLs. |
| `app/config.py` | Loads `.env` and validates database/server configuration. |
| `server.py` | Starts the application with Uvicorn for local development. |

## Security boundaries

- Query values are always sent separately to psycopg as parameters.
- Table and column identifiers can only come from the mappings in
  `app/resources.py`; request values are never interpolated as identifiers.
- `.env` is ignored by Git. `.env.example` contains placeholders only.
- The API is read-only at the route and SQL layers.
- Upload URLs are non-cacheable, scoped to one generated object path, and the
  Supabase secret key never leaves the backend.
- The API currently has no caller authentication. Do not expose it publicly
  until an authentication and authorization policy has been added.
- For production, connect with a dedicated PostgreSQL role that has only
  `SELECT` access to `case_details` and `file_details`, rather than the Supabase
  `postgres` administrator role.

## Database connections

The prototype opens one database connection per request. FastAPI executes the
synchronous route functions in its thread pool, so blocking psycopg calls do not
block the event loop. For sustained production traffic, replace
`app.database.execute_query` with a connection-pool-backed executor. The service
and route layers already receive the executor through dependency injection.

## Adding another read resource

1. Add a `ResourceDefinition` to `app/resources.py`.
2. Add its response model to `app/models.py`.
3. Add its query filter model to `app/filters.py`.
4. Add collection and item routes to `app/routes.py`.
5. Add query-builder and API tests.
6. Document the endpoint and public field mapping in `docs/API.md`.

## Tests

API tests override the FastAPI database dependency with an in-memory recording
executor. This verifies routing, validation, response schemas, CORS, generated
SQL, and error handling without requiring database credentials. Query-builder
and configuration tests run separately.
