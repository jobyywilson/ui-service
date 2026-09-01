# UI Service

A FastAPI backend for the UI that reads case records from PostgreSQL and
creates signed Supabase Storage upload URLs. Database columns use snake_case,
while JSON responses and query parameters use camelCase.

## Documentation

- [API reference](docs/API.md)
- [Architecture and extension guide](docs/ARCHITECTURE.md)
- [Configuration and Supabase setup](docs/CONFIGURATION.md)
- Interactive Swagger UI: `http://localhost:3000/docs` while the API is running

## Project structure

```text
server.py              Uvicorn development entry point
app/config.py          Environment and validated settings
app/resources.py       API-to-database field allowlists
app/query_builder.py   Parameterized SELECT construction
app/database.py        PostgreSQL connection and serialization
app/services.py        Framework-independent resource services
app/models.py          Pydantic response contracts
app/filters.py         Validated camelCase query parameters
app/routes.py          FastAPI endpoint definitions
app/main.py            FastAPI application and error handling
tests/                 Unit tests grouped by layer
```

## Set up

Python 3.9 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
cp .env.example .env
```

Edit `.env` and replace `DB_PASSWORD` with the Supabase database password. You
may instead set one `DATABASE_URL` value. Environment variables already present
in the shell take precedence over values in `.env`.

The configured `db.<project-ref>.supabase.co` host is Supabase's direct
connection, which normally requires IPv6. On an IPv4-only network, set
`DATABASE_URL` to the Session pooler URI copied from the Supabase Connect dialog.

## Create the tables

Run the included PostgreSQL schema before starting the API:

```bash
psql "$DATABASE_URL" -f schema.sql
```

If you use separate `DB_*` variables rather than `DATABASE_URL`, run the schema
through Supabase's SQL Editor or construct the equivalent `psql` command.

Load the optional sample records after creating the tables:

```bash
psql "$DATABASE_URL" -f sample_data.sql
```

You can also paste [sample_data.sql](sample_data.sql) into the Supabase SQL
Editor. It inserts four cases and five associated files and is safe to rerun.

## Run

```bash
python3 server.py
```

The API listens at `http://localhost:3000` by default.

Alternatively, run Uvicorn directly with automatic reload during development:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

Interactive API documentation is available at `http://localhost:3000/docs`.

> The API currently has no caller authentication. Keep it on a trusted network
> until authentication and authorization have been added. For production,
> connect using a PostgreSQL role limited to `SELECT` on `case_details`.

## Endpoints

```http
GET /rest/v1/cases
GET /rest/v1/cases/{id}
GET /rest/v1/cases/{id}/upload-url
```

The case endpoints are read-only and query `case_details`. The upload action
creates a signed Supabase Storage URL but does not upload a file itself.

Generate a short-lived Supabase Storage upload URL for an existing case:

```http
GET /rest/v1/cases/1001/upload-url?fileName=evidence.pdf
```

```json
{
  "uploadUrl": "https://project.supabase.co/storage/v1/object/upload/sign/..."
}
```

Configure `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, and
`SUPABASE_STORAGE_BUCKET` in `.env`. The bucket must already exist. Keep the
secret key on the backend only; never include it in a client application.

Search every field using a case-insensitive keyword search:

```http
GET /rest/v1/cases?search=fraud
```

Search one field:

```http
GET /rest/v1/cases?field=caseCategory&search=fraud
```

Filter using camelCase field names. Multiple filters use AND logic:

```http
GET /rest/v1/cases?caseCategory=fraud&addedBy=admin
```

The `id` filter is exact. Other filters are case-insensitive partial matches.
Query values are parameterized, while table and column identifiers come from
fixed allowlists.

## Test

Tests use an in-memory database executor and do not require Supabase access:

```bash
python3 -m unittest discover -s tests -v
```
