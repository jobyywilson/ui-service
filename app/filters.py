"""Validated FastAPI query-parameter models."""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class QueryFilters(BaseModel):
    """Search controls shared by every collection endpoint."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    search: Optional[str] = Field(
        None,
        description="Case-insensitive keyword matched across all exposed fields.",
        examples=["fraud"],
    )
    field: Optional[str] = Field(
        None,
        description="Restrict `search` to one camelCase response field.",
        examples=["caseCategory"],
    )

    def as_query_parameters(self) -> Dict[str, List[str]]:
        """Convert validated filters into the query builder's multivalue form."""

        values = self.model_dump(by_alias=True, exclude_none=True)
        return {name: [str(value)] for name, value in values.items()}


class CaseFilters(QueryFilters):
    """Filters accepted by ``GET /rest/v1/cases``."""

    id: Optional[int] = Field(None, description="Exact case identifier.")
    case_description: Optional[str] = Field(
        None,
        alias="caseDescription",
        description="Partial, case-insensitive description match.",
    )
    case_category: Optional[str] = Field(
        None,
        alias="caseCategory",
        description="Partial, case-insensitive category match.",
        examples=["fraud"],
    )
    assigned_officers: Optional[str] = Field(
        None,
        alias="assignedOfficers",
        description="Partial, case-insensitive officer match.",
    )
    status: Optional[str] = Field(
        None,
        description="Partial textual match against the TIMESTAMP status column.",
    )
    date_added: Optional[str] = Field(
        None,
        alias="dateAdded",
        description="Partial textual timestamp match.",
    )
    date_modified: Optional[str] = Field(
        None,
        alias="dateModified",
        description="Partial textual timestamp match.",
    )
    added_by: Optional[str] = Field(
        None,
        alias="addedBy",
        description="Partial, case-insensitive username match.",
    )
    modified_by: Optional[str] = Field(
        None,
        alias="modifiedBy",
        description="Partial, case-insensitive username match.",
    )
