import unittest

import httpx

from app.config import StorageSettings
from app.storage import StorageAccessError, SupabaseStorageClient


class StorageClientTests(unittest.TestCase):
    def test_creates_absolute_signed_upload_url_with_secret_key(self):
        def handler(request):
            self.assertEqual(request.method, "POST")
            self.assertEqual(
                request.url.path,
                "/storage/v1/object/upload/sign/case-files/cases/1001/evidence.pdf",
            )
            self.assertEqual(request.headers["apikey"], "sb_secret_example")
            self.assertNotIn("authorization", request.headers)
            return httpx.Response(
                200,
                json={
                    "url": (
                        "/object/upload/sign/case-files/cases/1001/"
                        "evidence.pdf?token=signed-token"
                    )
                },
            )

        settings = StorageSettings(
            supabase_url="https://project.supabase.co",
            api_key="sb_secret_example",
            bucket="case-files",
        )
        storage = SupabaseStorageClient(settings)
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            upload_url = storage.create_signed_upload_url(
                "cases/1001/evidence.pdf", client
            )

        self.assertEqual(
            upload_url,
            (
                "https://project.supabase.co/storage/v1/object/upload/sign/"
                "case-files/cases/1001/evidence.pdf?token=signed-token"
            ),
        )

    def test_legacy_service_role_key_is_sent_as_bearer_token(self):
        def handler(request):
            self.assertEqual(request.headers["authorization"], "Bearer legacy-jwt")
            return httpx.Response(200, json={"url": "/object/upload/sign/example"})

        settings = StorageSettings(
            supabase_url="https://project.supabase.co",
            api_key="legacy-jwt",
            bucket="case-files",
        )
        storage = SupabaseStorageClient(settings)
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            storage.create_signed_upload_url("cases/1/file.bin", client)

    def test_rejects_invalid_storage_response(self):
        settings = StorageSettings(
            supabase_url="https://project.supabase.co",
            api_key="sb_secret_example",
            bucket="case-files",
        )
        storage = SupabaseStorageClient(settings)
        transport = httpx.MockTransport(
            lambda _request: httpx.Response(200, json={"unexpected": True})
        )

        with httpx.Client(transport=transport) as client:
            with self.assertRaises(StorageAccessError):
                storage.create_signed_upload_url("cases/1/file.bin", client)
