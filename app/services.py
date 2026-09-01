"""Framework-independent resource access services."""

import re
from pathlib import PurePosixPath
from typing import Any, Callable, List, Mapping, Optional, Sequence
from uuid import uuid4

from app.database import execute_query
from app.query_builder import build_select_query
from app.resources import CASES, ResourceDefinition
from app.storage import create_signed_upload_url


QueryExecutor = Callable[[str, Sequence[object]], List[Mapping[str, Any]]]
UploadUrlProvider = Callable[[str], str]


class RecordNotFoundError(LookupError):
    """Raised when an individual resource record does not exist."""


def get_query_executor() -> QueryExecutor:
    """FastAPI dependency that provides the production query executor."""
    return execute_query


def get_upload_url_provider() -> UploadUrlProvider:
    """FastAPI dependency that provides the Supabase Storage signer."""

    return create_signed_upload_url


def list_records(
    resource: ResourceDefinition,
    query_parameters: Mapping[str, Sequence[str]],
    query_executor: QueryExecutor,
) -> List[Mapping[str, Any]]:
    """Return collection records matching validated API query parameters."""

    query = build_select_query(resource, query_parameters)
    return query_executor(query.statement, query.parameters)


def get_record(
    resource: ResourceDefinition,
    record_id: int,
    query_executor: QueryExecutor,
) -> Mapping[str, Any]:
    """Return one record or raise ``RecordNotFoundError``."""

    query = build_select_query(resource, {}, record_id=str(record_id))
    rows = query_executor(query.statement, query.parameters)
    if not rows:
        raise RecordNotFoundError(f"{resource.singular_name} not found.")
    return rows[0]


def _safe_file_name(file_name: Optional[str]) -> str:
    """Remove path components and unsafe characters from a client file name."""

    raw_name = (file_name or "upload.bin").replace("\\", "/")
    base_name = PurePosixPath(raw_name).name
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", base_name).strip("._")
    return (safe_name or "upload.bin")[:180]


def create_case_upload_url(
    case_id: int,
    file_name: Optional[str],
    query_executor: QueryExecutor,
    upload_url_provider: UploadUrlProvider,
) -> str:
    """Validate a case and create a unique signed object-upload URL for it."""

    get_record(CASES, case_id, query_executor)
    object_path = f"cases/{case_id}/{uuid4().hex}-{_safe_file_name(file_name)}"
    return upload_url_provider(object_path)
