"""Read-only graph analytics API routes backed by Neo4j."""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from app.graph_analytics.database import get_graph_repository
from app.graph_analytics.repository import GraphRepository


router = APIRouter(
    prefix="/rest/v1/cases/{case_id}/graph",
    tags=["Graph Analytics"],
)

Repository = Annotated[GraphRepository, Depends(get_graph_repository)]
CaseId = Annotated[str, Path(min_length=1, max_length=200)]


def collection(case_id, items):
    return {"caseId": case_id, "items": items, "count": len(items)}


def iso_timestamp(value, name):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=f"{name} must be an ISO 8601 timestamp",
        ) from error


def csv_values(value):
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def graph_filters(entity_type=None, relationship_type=None, device_id=None,
                  source_file_id=None, community_id=None, warning_status=None,
                  search=None, observed_from=None, observed_to=None):
    return {
        "entity_types": csv_values(entity_type),
        "relationship_types": csv_values(relationship_type),
        "device_id": device_id,
        "source_file_id": source_file_id,
        "community_id": community_id,
        "warning_status": warning_status,
        "search": search,
        "observed_from": observed_from,
        "observed_to": observed_to,
    }


@router.get("")
def graph(
    case_id: CaseId,
    repository: Repository,
    depth: Annotated[int, Query(ge=1, le=5)] = 1,
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
    minimum: Annotated[
        float, Query(alias="minConfidence", ge=0, le=1)
    ] = 0.8,
    entity_type: Annotated[Optional[str], Query(alias="entityType")] = None,
    relationship_type: Annotated[Optional[str], Query(alias="relationshipType")] = None,
    device_id: Annotated[Optional[str], Query(alias="deviceId")] = None,
    source_file_id: Annotated[Optional[str], Query(alias="sourceFileId")] = None,
    community_id: Annotated[Optional[str], Query(alias="communityId")] = None,
    warning_status: Annotated[
        Optional[str], Query(alias="warningStatus", pattern="^(warning|contradiction|clear)$")
    ] = None,
    search: Optional[str] = None,
    observed_from: Annotated[Optional[str], Query(alias="from")] = None,
    observed_to: Annotated[Optional[str], Query(alias="to")] = None,
    cursor: Optional[str] = None,
):
    filters = graph_filters(entity_type, relationship_type, device_id,
                           source_file_id, community_id, warning_status,
                           search, observed_from, observed_to)
    try:
        return repository.graph(case_id, depth, limit, minimum, filters, cursor)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/neighborhood")
def neighborhood(
    case_id: CaseId,
    repository: Repository,
    entity_id: Annotated[str, Query(alias="entityId", min_length=1)],
    depth: Annotated[int, Query(ge=1, le=5)] = 1,
    limit: Annotated[int, Query(ge=1, le=1000)] = 250,
    minimum: Annotated[
        float, Query(alias="minConfidence", ge=0, le=1)
    ] = 0.8,
    entity_type: Annotated[Optional[str], Query(alias="entityType")] = None,
    relationship_type: Annotated[Optional[str], Query(alias="relationshipType")] = None,
    device_id: Annotated[Optional[str], Query(alias="deviceId")] = None,
    source_file_id: Annotated[Optional[str], Query(alias="sourceFileId")] = None,
    community_id: Annotated[Optional[str], Query(alias="communityId")] = None,
    warning_status: Annotated[
        Optional[str], Query(alias="warningStatus", pattern="^(warning|contradiction|clear)$")
    ] = None,
    observed_from: Annotated[Optional[str], Query(alias="from")] = None,
    observed_to: Annotated[Optional[str], Query(alias="to")] = None,
    search: Optional[str] = None,
    cursor: Optional[str] = None,
):
    filters = graph_filters(entity_type, relationship_type, device_id,
                           source_file_id,
                           community_id=community_id,
                           warning_status=warning_status,
                           search=search,
                           observed_from=observed_from,
                           observed_to=observed_to)
    try:
        return repository.neighborhood(case_id, entity_id, depth, limit,
                                       minimum, filters, cursor)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/entities/{entity_id}")
def entity(case_id: CaseId, entity_id: str, repository: Repository):
    result = repository.entity(case_id, entity_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return result


@router.get("/entities/{entity_id}/source-records")
def entity_records(
    case_id: CaseId,
    entity_id: str,
    repository: Repository,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
):
    return collection(
        case_id, repository.entity_records(case_id, entity_id, limit)
    )


@router.get("/entities/{entity_id}/merge-history")
def merge_history(
    case_id: CaseId,
    entity_id: str,
    repository: Repository,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
):
    return collection(
        case_id, repository.merge_history(case_id, entity_id, limit)
    )


@router.get("/relationships/{relationship_id}")
def relationship(
    case_id: CaseId,
    relationship_id: str,
    repository: Repository,
):
    result = repository.relationship(case_id, relationship_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return result


@router.get("/relationships/{relationship_id}/evidence")
def relationship_evidence(
    case_id: CaseId,
    relationship_id: str,
    repository: Repository,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
):
    return collection(
        case_id,
        repository.relationship_evidence(case_id, relationship_id, limit),
    )


@router.get("/timeline")
def timeline(
    case_id: CaseId,
    repository: Repository,
    start: Annotated[str, Query(alias="from")],
    end: Annotated[str, Query(alias="to")],
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
):
    if iso_timestamp(start, "from") > iso_timestamp(end, "to"):
        raise HTTPException(status_code=422, detail="from must not be after to")
    return collection(
        case_id, repository.timeline(case_id, start, end, limit)
    )


@router.get("/communities")
def communities(
    case_id: CaseId,
    repository: Repository,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
):
    return collection(case_id, repository.communities(case_id, limit))


@router.get("/bridges")
def bridges(
    case_id: CaseId,
    repository: Repository,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    minimum: Annotated[
        float, Query(alias="minBridgeScore", ge=0)
    ] = 0,
):
    return collection(
        case_id, repository.bridges(case_id, limit, minimum)
    )
