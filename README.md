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
app/routes.py          PostgreSQL-backed FastAPI endpoint definitions
app/ontology/          Entity and relationship ontology API routes
app/graph_analytics/   Neo4j routes, connection settings, and Cypher queries
app/main.py            FastAPI application and error handling
tests/                 Unit tests grouped by layer
sql/ddl/               Flat, ordered PostgreSQL DDL scripts
sql/seed-data/         Flat, ordered PostgreSQL development seed scripts
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

Graph endpoints use Neo4j Cloud. Add the following values to the same `.env`:

```dotenv
NEO4J_URI=neo4j+s://YOUR_INSTANCE_ID.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=YOUR_NEO4J_PASSWORD
NEO4J_VERIFY_CONNECTIVITY=true
```

`NEO4J_DATABASE` is optional. Leave it unset to use the Aura account's home
database.

To load development data into Neo4j Aura, open Aura Query, select the `neo4j`
database, then paste and run `sample_data.cypher`. This
development-only script deletes every existing node and relationship before it
creates case `1001` with eight entities, ten graph relationships, evidence records,
relationship evidence, merge history, communities, and bridge metrics.

Graph list endpoints support comma-separated `entityType` and
`relationshipType` filters plus `deviceId`, `sourceFileId`, `communityId`,
`warningStatus`, `from`, `to`, `search`, `minConfidence`, and an opaque
pagination `cursor`. Only canonical entities with stable `id` values and
relationships backed by evidence are returned.

## Create the tables

Run the included PostgreSQL schema before starting the API:

```bash
psql "$DATABASE_URL" -f sql/ddl/01_case_and_file.sql
```

If you use separate `DB_*` variables rather than `DATABASE_URL`, run the schema
through Supabase's SQL Editor or construct the equivalent `psql` command.

Load the optional sample records after creating the tables:

```bash
psql "$DATABASE_URL" -f sql/seed-data/01_case_and_file_seed.sql
```

You can also paste [01_case_and_file_seed.sql](sql/seed-data/01_case_and_file_seed.sql) into the Supabase SQL
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
GET /rest/v1/entities
GET /rest/v1/entities/{id}
GET /rest/v1/entity-attributes
GET /rest/v1/entity-attributes/{id}
GET /rest/v1/relationships
GET /rest/v1/relationships/{id}
GET /rest/v1/relationship-attributes
GET /rest/v1/relationship-attributes/{id}
GET /rest/v1/extracted-entity-relationships
GET /rest/v1/extracted-entity-relationships/{id}
GET /rest/v1/cases/{caseId}/graph
GET /rest/v1/cases/{caseId}/graph/neighborhood
GET /rest/v1/cases/{caseId}/graph/entities/{entityId}
GET /rest/v1/cases/{caseId}/graph/entities/{entityId}/source-records
GET /rest/v1/cases/{caseId}/graph/entities/{entityId}/merge-history
GET /rest/v1/cases/{caseId}/graph/relationships/{relationshipId}
GET /rest/v1/cases/{caseId}/graph/relationships/{relationshipId}/evidence
GET /rest/v1/cases/{caseId}/graph/timeline
GET /rest/v1/cases/{caseId}/graph/communities
GET /rest/v1/cases/{caseId}/graph/bridges
```

The case endpoints are read-only and query `case_details`. The upload action
creates a signed Supabase Storage URL but does not upload a file itself.

The entity-resolution endpoints are also read-only. Collection endpoints support
`search`, field-specific search, and direct camelCase filters. For example:

```http
GET /rest/v1/entities?isStandard=Y&search=identifier
GET /rest/v1/entity-attributes?entityId=1028
GET /rest/v1/relationships?relationshipName=RESOLVED_TO
GET /rest/v1/relationship-attributes?relationshipId=3013
GET /rest/v1/extracted-entity-relationships?caseId=7001
```

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
