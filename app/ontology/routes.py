"""PostgreSQL-backed ontology catalog routes."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from app.filters import (
    EntityAttributeFilters,
    EntityFilters,
    RelationshipAttributeFilters,
    RelationshipFilters,
)
from app.models import (
    EntityAttributeResponse,
    EntityResponse,
    RelationshipAttributeResponse,
    RelationshipResponse,
)
from app.resources import (
    ENTITIES,
    ENTITY_ATTRIBUTES,
    RELATIONSHIPS,
    RELATIONSHIP_ATTRIBUTES,
)
from app.services import QueryExecutor, get_query_executor, get_record, list_records


router = APIRouter(prefix="/rest/v1", tags=["Ontology"])


@router.get("/entities", response_model=List[EntityResponse], tags=["Entities"])
def read_entities(
    filters: Annotated[EntityFilters, Query()],
    query_executor: QueryExecutor = Depends(get_query_executor),
):
    """List and search standard and custom entity definitions."""

    return list_records(ENTITIES, filters.as_query_parameters(), query_executor)


@router.get("/entities/{record_id}", response_model=EntityResponse, tags=["Entities"])
def read_entity(
    record_id: int,
    query_executor: QueryExecutor = Depends(get_query_executor),
):
    """Return one entity definition by ID."""

    return get_record(ENTITIES, record_id, query_executor)


@router.get(
    "/entity-attributes",
    response_model=List[EntityAttributeResponse],
    tags=["Entities"],
)
def read_entity_attributes(
    filters: Annotated[EntityAttributeFilters, Query()],
    query_executor: QueryExecutor = Depends(get_query_executor),
):
    """List and search entity attribute definitions."""

    return list_records(
        ENTITY_ATTRIBUTES, filters.as_query_parameters(), query_executor
    )


@router.get(
    "/entity-attributes/{record_id}",
    response_model=EntityAttributeResponse,
    tags=["Entities"],
)
def read_entity_attribute(
    record_id: int,
    query_executor: QueryExecutor = Depends(get_query_executor),
):
    """Return one entity attribute definition by ID."""

    return get_record(ENTITY_ATTRIBUTES, record_id, query_executor)


@router.get(
    "/relationships",
    response_model=List[RelationshipResponse],
    tags=["Relationships"],
)
def read_relationships(
    filters: Annotated[RelationshipFilters, Query()],
    query_executor: QueryExecutor = Depends(get_query_executor),
):
    """List and search relationship definitions."""

    return list_records(RELATIONSHIPS, filters.as_query_parameters(), query_executor)


@router.get(
    "/relationships/{record_id}",
    response_model=RelationshipResponse,
    tags=["Relationships"],
)
def read_relationship(
    record_id: int,
    query_executor: QueryExecutor = Depends(get_query_executor),
):
    """Return one relationship definition by ID."""

    return get_record(RELATIONSHIPS, record_id, query_executor)


@router.get(
    "/relationship-attributes",
    response_model=List[RelationshipAttributeResponse],
    tags=["Relationships"],
)
def read_relationship_attributes(
    filters: Annotated[RelationshipAttributeFilters, Query()],
    query_executor: QueryExecutor = Depends(get_query_executor),
):
    """List and search relationship attribute definitions."""

    return list_records(
        RELATIONSHIP_ATTRIBUTES,
        filters.as_query_parameters(),
        query_executor,
    )


@router.get(
    "/relationship-attributes/{record_id}",
    response_model=RelationshipAttributeResponse,
    tags=["Relationships"],
)
def read_relationship_attribute(
    record_id: int,
    query_executor: QueryExecutor = Depends(get_query_executor),
):
    """Return one relationship attribute definition by ID."""

    return get_record(RELATIONSHIP_ATTRIBUTES, record_id, query_executor)
