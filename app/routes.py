"""FastAPI routes for case resources and upload actions."""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query, Response

from app.filters import CaseFilters
from app.models import CaseResponse, UploadUrlResponse
from app.resources import CASES
from app.services import (
    QueryExecutor,
    UploadUrlProvider,
    create_case_upload_url,
    get_query_executor,
    get_record,
    get_upload_url_provider,
    list_records,
)


router = APIRouter(prefix="/rest/v1")
action_router = APIRouter(prefix="/rest/v1")


@router.get(
    "/cases",
    response_model=List[CaseResponse],
    summary="List and search cases",
    description=(
        "Returns rows from `case_details`. Use `search` for a keyword search, "
        "or combine camelCase field filters using AND logic."
    ),
    responses={400: {"description": "Invalid search field or filter."}},
    tags=["Cases"],
)
def read_cases(
    filters: Annotated[CaseFilters, Query()],
    query_executor: QueryExecutor = Depends(get_query_executor),
):
    """List case records using validated, parameterized filters."""

    return list_records(CASES, filters.as_query_parameters(), query_executor)


@router.get(
    "/cases/{record_id}",
    response_model=CaseResponse,
    summary="Get a case by ID",
    description="Returns one `case_details` row using its numeric identifier.",
    responses={404: {"description": "Case not found."}},
    tags=["Cases"],
)
def read_case(
    record_id: int,
    query_executor: QueryExecutor = Depends(get_query_executor),
):
    """Return one case record by primary key."""

    return get_record(CASES, record_id, query_executor)


@action_router.get(
    "/cases/{case_id}/upload-url",
    response_model=UploadUrlResponse,
    summary="Get a case file upload URL",
    description=(
        "Verifies that the case exists, generates a unique object path under "
        "that case, and returns a short-lived Supabase Storage signed upload URL."
    ),
    responses={
        404: {"description": "Case not found."},
        502: {"description": "Supabase Storage could not sign the upload URL."},
        503: {"description": "Database or Storage configuration is unavailable."},
    },
    tags=["Uploads"],
)
def get_case_upload_url(
    case_id: int,
    response: Response,
    file_name: Optional[str] = Query(
        None,
        alias="fileName",
        description=(
            "Optional original file name. Path components and unsafe characters "
            "are removed before the object path is generated."
        ),
        examples=["evidence.pdf"],
    ),
    query_executor: QueryExecutor = Depends(get_query_executor),
    upload_url_provider: UploadUrlProvider = Depends(get_upload_url_provider),
):
    """Return a non-cacheable signed upload URL for an existing case."""

    upload_url = create_case_upload_url(
        case_id,
        file_name,
        query_executor,
        upload_url_provider,
    )
    response.headers["Cache-Control"] = "no-store"
    return {"uploadUrl": upload_url}
