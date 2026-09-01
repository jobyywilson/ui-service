# API reference

The UI Service exposes read-only access to the PostgreSQL `case_details` table
and generates signed case-file upload URLs. Database column names are converted
from snake_case to camelCase in both JSON responses and query parameters.

The default local base URL is `http://localhost:3000`. FastAPI also publishes
interactive Swagger documentation at `/docs` and the OpenAPI document at
`/openapi.json`.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/rest/v1/cases` | List or search case records. |
| `GET` | `/rest/v1/cases/{id}` | Return one case by its numeric ID. |
| `GET` | `/rest/v1/cases/{id}/upload-url` | Create a signed case upload URL. |

The API does not currently expose create, update, or delete operations.

## Case upload URL

Request a short-lived upload URL for an existing case:

```http
GET /rest/v1/cases/1001/upload-url?fileName=evidence.pdf
```

`fileName` is optional. The service removes path components and unsafe
characters, prefixes the name with a UUID, and stores it under
`cases/{caseId}/`. If omitted, the generated name ends in `upload.bin`.

Before calling Supabase Storage, the endpoint checks `case_details` for the
requested ID. A missing case returns `404` and no URL is generated.

Successful response:

```json
{
  "uploadUrl": "https://project.supabase.co/storage/v1/object/upload/sign/case-files/cases/1001/unique-evidence.pdf?token=..."
}
```

The response includes `Cache-Control: no-store`. Supabase signed upload URLs are
valid for approximately two hours. Upload the file using HTTP `PUT`:

```bash
curl --request PUT \
  --header "Content-Type: application/pdf" \
  --data-binary @evidence.pdf \
  "SIGNED_UPLOAD_URL"
```

Generating or using this URL does not insert a row into `file_details`; that
association must be created by a separate workflow after a successful upload.

## Search behavior

Use `search` by itself to perform a case-insensitive partial match across every
field exposed by that resource:

```http
GET /rest/v1/cases?search=fraud
```

Use `field` with `search` to restrict the keyword to one camelCase field:

```http
GET /rest/v1/cases?field=caseCategory&search=fraud
```

Use fields directly as filters. Multiple filters are joined using AND logic:

```http
GET /rest/v1/cases?caseCategory=fraud&addedBy=admin
```

`id` uses exact integer equality. Other filters use case-insensitive partial
matching. Percent signs and underscores in keywords are treated as literal
characters rather than SQL wildcard operators.

### Case fields

| API field | Database column | Matching |
| --- | --- | --- |
| `id` | `id` | Exact integer |
| `caseDescription` | `case_description` | Partial text |
| `caseCategory` | `case_category` | Partial text |
| `assignedOfficers` | `assigned_officers` | Partial text |
| `status` | `status` | Partial timestamp text |
| `dateAdded` | `date_added` | Partial timestamp text |
| `dateModified` | `date_modified` | Partial timestamp text |
| `addedBy` | `added_by` | Partial text |
| `modifiedBy` | `modified_by` | Partial text |

The supplied schema defines `status` as `TIMESTAMP`. The API preserves that
contract. If status is intended to contain labels such as `OPEN` or `CLOSED`,
change the database column and `CaseResponse.status` to a string type.

## Response examples

`GET /rest/v1/cases/1001`:

```json
{
  "id": 1001,
  "caseDescription": "Unauthorized card transaction",
  "caseCategory": "Fraud",
  "assignedOfficers": "Anita Rao",
  "status": "2026-09-01T10:00:00",
  "dateAdded": "2026-09-01T10:00:00",
  "dateModified": "2026-09-01T10:00:00",
  "addedBy": "admin",
  "modifiedBy": "admin"
}
```

Collection endpoints return a JSON array. A valid search with no matches returns
an empty array.

## Error responses

| Status | Meaning |
| --- | --- |
| `400` | The requested search field or filter value is invalid. |
| `404` | The endpoint or requested record does not exist. |
| `405` | The endpoint exists but does not support that HTTP method. |
| `422` | FastAPI could not validate a typed query or path parameter. |
| `503` | Database configuration is missing or PostgreSQL is unavailable. |
| `502` | Supabase Storage could not create a signed upload URL. |

Example application error:

```json
{
  "error": "Case not found."
}
```

## cURL examples

```bash
curl "http://localhost:3000/rest/v1/cases?search=fraud"
curl "http://localhost:3000/rest/v1/cases/1001"
```
