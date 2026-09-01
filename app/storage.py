"""Supabase Storage signed-upload URL integration."""

from typing import Optional
from urllib.parse import quote

import httpx

from app.config import StorageSettings, get_storage_settings


class StorageAccessError(RuntimeError):
    """Raised when Supabase Storage cannot create an upload URL."""


class SupabaseStorageClient:
    """Small client for the Supabase signed-upload REST operation."""

    def __init__(self, settings: StorageSettings):
        self._settings = settings

    def create_signed_upload_url(
        self,
        object_path: str,
        client: Optional[httpx.Client] = None,
    ) -> str:
        """Create a signed URL for uploading one object.

        The caller owns an injected client. When no client is supplied, this
        method opens and closes a short-lived client for the request.
        """

        storage_base_url = f"{self._settings.supabase_url}/storage/v1"
        encoded_path = quote(
            f"{self._settings.bucket}/{object_path}", safe="/"
        )
        endpoint = f"{storage_base_url}/object/upload/sign/{encoded_path}"
        headers = {
            "apikey": self._settings.api_key,
            "Content-Type": "application/json",
            "User-Agent": "case-storage-api/1.0",
        }

        # Legacy service_role keys are JWTs and must also be sent as bearer
        # tokens. Current sb_secret_* keys belong only in the apikey header.
        if not self._settings.api_key.startswith("sb_"):
            headers["Authorization"] = f"Bearer {self._settings.api_key}"

        owns_client = client is None
        request_client = client or httpx.Client(timeout=10.0)
        try:
            response = request_client.post(endpoint, headers=headers, json={})
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise StorageAccessError(
                "Supabase Storage could not create a signed upload URL."
            ) from error
        finally:
            if owns_client:
                request_client.close()

        relative_url = payload.get("url")
        if not isinstance(relative_url, str) or not relative_url:
            raise StorageAccessError(
                "Supabase Storage returned an invalid signed-upload response."
            )
        if relative_url.startswith(("https://", "http://")):
            return relative_url
        if relative_url.startswith("/storage/v1/"):
            return f"{self._settings.supabase_url}{relative_url}"
        return f"{storage_base_url}/{relative_url.lstrip('/')}"


def create_signed_upload_url(object_path: str) -> str:
    """Create a signed upload URL using environment-backed settings."""

    return SupabaseStorageClient(get_storage_settings()).create_signed_upload_url(
        object_path
    )
