# Configuration

The application reads process environment variables and then falls back to a
local `.env` file. Existing process values are never overwritten.

## Variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DATABASE_URL` | No | None | Complete PostgreSQL URI; overrides all `DB_*` values. |
| `DB_HOST` | Yes* | None | PostgreSQL or Supabase pooler host. |
| `DB_PORT` | No | `5432` | PostgreSQL port. |
| `DB_NAME` | No | `postgres` | Database name. |
| `DB_USER` | Yes* | None | Database username. |
| `DB_PASSWORD` | Yes* | None | Database password. |
| `DB_SSLMODE` | No | `require` | psycopg SSL mode. |
| `SUPABASE_URL` | For uploads | None | Project URL such as `https://PROJECT_REF.supabase.co`. |
| `SUPABASE_SECRET_KEY` | For uploads | None | Backend-only `sb_secret_...` API key. |
| `SUPABASE_SERVICE_ROLE_KEY` | No | None | Legacy fallback for the secret key. |
| `SUPABASE_STORAGE_BUCKET` | No | `case-files` | Existing Storage bucket name. |
| `HOST` | No | `0.0.0.0` | Local Uvicorn bind address. |
| `PORT` | No | `3000` | Local Uvicorn port. |

`DB_HOST`, `DB_USER`, and `DB_PASSWORD` are required only when `DATABASE_URL` is
not set.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
cp .env.example .env
```

Edit `.env` and replace the password placeholder. Never commit `.env` or send
the database password in chat, logs, screenshots, or issue reports.

## Supabase connection choices

Direct connection:

```env
DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres?sslmode=require
```

Supabase direct hosts normally require IPv6. If the machine or deployment is
IPv4-only, copy the Session pooler URI from the project's **Connect** dialog:

```env
DATABASE_URL=postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?sslmode=require
```

When a password is placed in a URI, percent-encode reserved characters such as
`@`, `:`, `/`, `?`, and `#`. Separate `DB_*` variables avoid URI-encoding the
password.

## Supabase Storage

Create a Storage bucket named `case-files` in the Supabase dashboard, or set
`SUPABASE_STORAGE_BUCKET` to another existing bucket. Private buckets are
recommended for case files.

Create a backend secret key under **Settings → API Keys**, then configure:

```env
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_SECRET_KEY=sb_secret_REPLACE_ME
SUPABASE_STORAGE_BUCKET=case-files
```

The secret key bypasses Row Level Security and must never be returned to clients,
committed to Git, or used in browser code. The API uses it only to request a
short-lived signed upload URL. Legacy JWT-based service-role keys are supported
through `SUPABASE_SERVICE_ROLE_KEY` while migrating to current secret keys.

## Create the schema

With `DATABASE_URL` exported in the shell:

```bash
psql "$DATABASE_URL" -f sql/ddl/01_case_and_file.sql
```

Alternatively, paste the files under `sql/ddl/` into the Supabase SQL Editor
in numeric order.

## Load sample data

After creating the schema, load the optional sample cases and files:

```bash
psql "$DATABASE_URL" -f sql/seed-data/01_case_and_file_seed.sql
```

`sql/seed-data/01_case_and_file_seed.sql` inserts four cases and five files. It uses fixed IDs, skips
rows that already exist, and updates both identity sequences afterward. The same
script can be pasted into the Supabase SQL Editor.

## Troubleshooting

- `PostgreSQL driver is not installed`: activate `.venv` and install
  `requirements.txt` or `requirements-dev.txt`.
- `Database is unavailable`: verify the host, password, SSL mode, and network
  support for IPv4 or IPv6.
- `relation ... does not exist`: run the files under `sql/ddl/` in numeric order in the same database used by
  the API.
- Port validation failure: set `PORT` to an integer from `1` through `65535`.
