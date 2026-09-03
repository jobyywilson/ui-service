"""FastAPI application configuration."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from app.config import ConfigurationError, load_env_file
from app.database import DatabaseAccessError
from app.graph_analytics.database import close_graph_driver
from app.graph_analytics.routes import router as graph_router
from app.ontology.routes import router as ontology_router
from app.query_builder import QueryValidationError
from app.routes import action_router, router
from app.services import RecordNotFoundError
from app.storage import StorageAccessError


LOGGER = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    load_env_file()
    application = FastAPI(
        title="UI Service",
        description=(
            "Backend APIs for the UI to read case metadata, entity-resolution "
            "catalogs and extracted graph payloads, and obtain signed case-file "
            "upload URLs. Database columns are returned as camelCase JSON "
            "properties. Collection endpoints support keyword, field-specific, "
            "and direct filtering."
        ),
        version="1.0.0",
        openapi_tags=[
            {
                "name": "Cases",
                "description": "Read and search existing case metadata.",
            },
            {
                "name": "Uploads",
                "description": "Create short-lived case file upload URLs.",
            },
            {
                "name": "Entities",
                "description": "Read entity and entity-attribute definitions.",
            },
            {
                "name": "Relationships",
                "description": "Read relationship and attribute definitions.",
            },
            {
                "name": "Entity Resolution",
                "description": "Read extracted Track 7 graph payloads.",
            },
            {
                "name": "Graph Analytics",
                "description": "Explore the case knowledge graph in Neo4j.",
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
    application.include_router(ontology_router)
    application.include_router(graph_router)

    @application.on_event("shutdown")
    def close_neo4j_driver() -> None:
        close_graph_driver(application)

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

    @application.exception_handler(ServiceUnavailable)
    @application.exception_handler(Neo4jError)
    async def graph_database_error_handler(
        _request: Request, error: Neo4jError
    ) -> JSONResponse:
        LOGGER.error("Neo4j request failed: %s", error)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/problem+json",
            content={
                "title": "Graph database unavailable",
                "status": 503,
                "code": "GRAPH_DATABASE_UNAVAILABLE",
            },
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
