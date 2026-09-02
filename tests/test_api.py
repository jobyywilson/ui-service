import unittest

from fastapi.testclient import TestClient

from app.database import DatabaseAccessError
from app.main import app
from app.services import get_query_executor, get_upload_url_provider
from app.storage import StorageAccessError


CASE_ROWS = [
    {
        "id": 1001,
        "caseDescription": "Unauthorized card transaction",
        "caseCategory": "Fraud",
        "assignedOfficers": "Anita Rao",
        "status": "2026-09-01T10:00:00",
        "dateAdded": "2026-09-01T10:00:00",
        "dateModified": "2026-09-01T10:00:00",
        "addedBy": "admin",
        "modifiedBy": "admin",
    }
]

ENTITY_ROWS = [
    {
        "id": 1001,
        "entityName": "PERSON",
        "label": "Person",
        "entityDescription": "An individual.",
        "isStandard": "Y",
        "dateAdded": "2026-09-01T10:00:00",
        "dateModified": "2026-09-01T10:00:00",
        "addedBy": "system",
        "modifiedBy": "system",
    }
]

EXTRACTED_ROWS = [
    {
        "id": 5001,
        "caseId": 7001,
        "extractedDetails": {"identifiers": []},
        "isStandard": "Y",
        "dateAdded": "2026-09-01T10:00:00",
        "dateModified": "2026-09-01T10:00:00",
        "addedBy": "system",
        "modifiedBy": "system",
    }
]

class RecordingExecutor:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def __call__(self, statement, parameters):
        self.calls.append((statement, parameters))
        return self.rows


class RecordingUploadUrlProvider:
    def __init__(self, upload_url="https://storage.example/signed-upload"):
        self.upload_url = upload_url
        self.paths = []

    def __call__(self, object_path):
        self.paths.append(object_path)
        return self.upload_url


class ApiTests(unittest.TestCase):
    def tearDown(self):
        app.dependency_overrides.clear()

    def _client(self, executor, upload_url_provider=None):
        app.dependency_overrides[get_query_executor] = lambda: executor
        if upload_url_provider is not None:
            app.dependency_overrides[get_upload_url_provider] = (
                lambda: upload_url_provider
            )
        return TestClient(app)

    def test_get_cases_reads_case_details(self):
        executor = RecordingExecutor(CASE_ROWS)
        client = self._client(executor)

        response = client.get(
            "/rest/v1/cases", headers={"Origin": "http://localhost"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), CASE_ROWS)
        self.assertIn("FROM case_details", executor.calls[0][0])
        self.assertIn('case_description AS "caseDescription"', executor.calls[0][0])
        self.assertEqual(response.headers["access-control-allow-origin"], "*")

    def test_returns_one_record_by_id(self):
        executor = RecordingExecutor(CASE_ROWS)
        client = self._client(executor)

        response = client.get("/rest/v1/cases/1001")

        statement, parameters = executor.calls[0]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), CASE_ROWS[0])
        self.assertIn("LIMIT 1", statement)
        self.assertEqual(parameters, (1001,))

    def test_get_entities_reads_entity_details(self):
        executor = RecordingExecutor(ENTITY_ROWS)
        response = self._client(executor).get(
            "/rest/v1/entities?isStandard=Y&entityName=PERSON"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ENTITY_ROWS)
        statement, parameters = executor.calls[0]
        self.assertIn("FROM entity_details", statement)
        self.assertIn('entity_name AS "entityName"', statement)
        self.assertEqual(parameters, ("%PERSON%", "%Y%"))

    def test_get_entity_attributes_filters_by_entity_id(self):
        executor = RecordingExecutor([])
        response = self._client(executor).get(
            "/rest/v1/entity-attributes?entityId=1028"
        )

        self.assertEqual(response.status_code, 200)
        statement, parameters = executor.calls[0]
        self.assertIn("FROM entity_attribute_details", statement)
        self.assertIn("entity_id = %s", statement)
        self.assertEqual(parameters, (1028,))

    def test_get_relationships_and_attributes_are_exposed(self):
        executor = RecordingExecutor([])
        client = self._client(executor)

        self.assertEqual(client.get("/rest/v1/relationships").status_code, 200)
        self.assertEqual(
            client.get(
                "/rest/v1/relationship-attributes?relationshipId=3013"
            ).status_code,
            200,
        )
        self.assertIn("FROM relationship_details", executor.calls[0][0])
        self.assertIn("FROM relationship_attribute_details", executor.calls[1][0])
        self.assertEqual(executor.calls[1][1], (3013,))

    def test_get_extracted_graph_payloads_filters_by_case(self):
        executor = RecordingExecutor(EXTRACTED_ROWS)
        response = self._client(executor).get(
            "/rest/v1/extracted-entity-relationships?caseId=7001"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), EXTRACTED_ROWS)
        statement, parameters = executor.calls[0]
        self.assertIn("FROM extracted_entity_relationship", statement)
        self.assertIn('extracted_details AS "extractedDetails"', statement)
        self.assertEqual(parameters, (7001,))

    def test_returns_404_when_record_does_not_exist(self):
        response = self._client(RecordingExecutor([])).get("/rest/v1/cases/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Case not found.")

    def test_rejects_unknown_search_field_without_database_call(self):
        executor = RecordingExecutor(CASE_ROWS)
        client = self._client(executor)

        response = client.get(
            "/rest/v1/cases?field=unknown&search=value"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown search field", response.json()["error"])
        self.assertEqual(executor.calls, [])

    def test_returns_503_when_database_is_unavailable(self):
        def unavailable_executor(_statement, _parameters):
            raise DatabaseAccessError("connection failed")

        client = self._client(unavailable_executor)
        with self.assertLogs("app.main", level="ERROR"):
            response = client.get("/rest/v1/cases")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"], "Database is unavailable.")

    def test_fastapi_returns_standard_route_errors(self):
        client = self._client(RecordingExecutor(CASE_ROWS))

        self.assertEqual(client.get("/cases").status_code, 404)
        self.assertEqual(client.get("/rest/v1/files").status_code, 404)
        self.assertEqual(client.get("/rest/v1/files/501").status_code, 404)
        self.assertEqual(
            client.get("/rest/v1/case/1001/action/getUploadUrl").status_code,
            404,
        )
        self.assertEqual(client.post("/rest/v1/cases").status_code, 405)

    def test_openapi_documentation_is_available(self):
        client = self._client(RecordingExecutor(CASE_ROWS))

        response = client.get("/openapi.json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["info"]["title"], "UI Service")
        self.assertIn("/rest/v1/cases", response.json()["paths"])
        self.assertIn("/rest/v1/entities", response.json()["paths"])
        self.assertIn("/rest/v1/entity-attributes", response.json()["paths"])
        self.assertIn("/rest/v1/relationships", response.json()["paths"])
        self.assertIn(
            "/rest/v1/relationship-attributes", response.json()["paths"]
        )
        self.assertIn(
            "/rest/v1/extracted-entity-relationships", response.json()["paths"]
        )
        self.assertFalse(
            any(
                path.startswith("/rest/v1/files")
                for path in response.json()["paths"]
            )
        )
        self.assertNotIn(
            "FileResponse", response.json().get("components", {}).get("schemas", {})
        )
        self.assertIn(
            "/rest/v1/cases/{case_id}/upload-url",
            response.json()["paths"],
        )
        case_parameters = response.json()["paths"]["/rest/v1/cases"]["get"][
            "parameters"
        ]
        parameter_names = {parameter["name"] for parameter in case_parameters}
        self.assertIn("search", parameter_names)
        self.assertIn("caseCategory", parameter_names)

    def test_get_case_upload_url(self):
        provider = RecordingUploadUrlProvider()
        client = self._client(RecordingExecutor(CASE_ROWS), provider)

        response = client.get(
            "/rest/v1/cases/1001/upload-url?fileName=../evidence%20copy.pdf"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"uploadUrl": "https://storage.example/signed-upload"},
        )
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertRegex(
            provider.paths[0],
            r"^cases/1001/[0-9a-f]{32}-evidence_copy\.pdf$",
        )

    def test_upload_url_requires_an_existing_case(self):
        provider = RecordingUploadUrlProvider()
        client = self._client(RecordingExecutor([]), provider)

        response = client.get("/rest/v1/cases/999/upload-url")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"error": "Case not found."})
        self.assertEqual(provider.paths, [])

    def test_returns_502_when_storage_is_unavailable(self):
        def unavailable_provider(_object_path):
            raise StorageAccessError("signing failed")

        client = self._client(RecordingExecutor(CASE_ROWS), unavailable_provider)
        with self.assertLogs("app.main", level="ERROR"):
            response = client.get("/rest/v1/cases/1001/upload-url")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json(), {"error": "Supabase Storage is unavailable."}
        )
