"""Neo4j driver lifecycle and FastAPI dependencies."""

from fastapi import Request
from neo4j import GraphDatabase

from app.graph_analytics.config import get_neo4j_settings
from app.graph_analytics.repository import GraphRepository


def get_graph_repository(request: Request) -> GraphRepository:
    """Create the shared Neo4j driver lazily on the first graph request."""

    driver = getattr(request.app.state, "graph_driver", None)
    settings = get_neo4j_settings()
    if driver is None:
        driver = GraphDatabase.driver(
            settings.uri,
            auth=(settings.username, settings.password),
        )
        if settings.verify_connectivity:
            driver.verify_connectivity()
        request.app.state.graph_driver = driver
        request.app.state.graph_database = settings.database

    return GraphRepository(driver, request.app.state.graph_database)


def close_graph_driver(application) -> None:
    """Close the shared Neo4j driver when the UI service shuts down."""

    driver = getattr(application.state, "graph_driver", None)
    if driver is not None:
        driver.close()
        application.state.graph_driver = None
