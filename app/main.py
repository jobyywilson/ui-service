"""FastAPI application configuration."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import ConfigurationError, load_env_file
from app.database import DatabaseAccessError
from app.query_builder import QueryValidationError
from app.routes import action_router, router
from app.services import RecordNotFoundError
from app.storage import StorageAccessError


LOGGER = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    load_env_file()
    application = FastAPI(
        title="Case Storage Read API",
        description=(
            "Read-only access to `case_details` and `file_details`. Database "
            "columns are returned as camelCase JSON properties. Collection "
            "endpoints support keyword, field-specific, and direct filtering."
        ),
        version="1.0.0",
        openapi_tags=[
            {
                "name": "Cases",
                "description": "Read and search existing case metadata.",
            },
            {
                "name": "Files",
                "description": "Read and search file metadata and extracted content.",
            },
            {
                "name": "Uploads",
                "description": "Create short-lived case file upload URLs.",
            },
        ],
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )
    application.include_router(router)
    application.include_router(action_router)

    @application.exception_handler(QueryValidationError)
    async def query_validation_error_handler(
        _request: Request, error: QueryValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": str(error),
                "searchableFields": list(error.searchable_fields),
            },
        )

    @application.exception_handler(RecordNotFoundError)
    async def record_not_found_error_handler(
        _request: Request, error: RecordNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": str(error)},
        )

    @application.exception_handler(ConfigurationError)
    async def configuration_error_handler(
        _request: Request, error: ConfigurationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": str(error)},
        )

    @application.exception_handler(DatabaseAccessError)
    async def database_error_handler(
        _request: Request, error: DatabaseAccessError
    ) -> JSONResponse:
        LOGGER.error("Database request failed: %s", error)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "Database is unavailable."},
        )

    @application.exception_handler(StorageAccessError)
    async def storage_error_handler(
        _request: Request, error: StorageAccessError
    ) -> JSONResponse:
        LOGGER.error("Supabase Storage request failed: %s", error)
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"error": "Supabase Storage is unavailable."},
        )

    return application


app = create_app()
