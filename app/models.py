"""Pydantic response contracts exposed in the OpenAPI schema."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CaseResponse(BaseModel):
    """Public camelCase representation of one ``case_details`` row."""

    id: int = Field(description="Case identifier.")
    case_description: Optional[str] = Field(
        None, alias="caseDescription", description="Description of the case."
    )
    case_category: Optional[str] = Field(
        None, alias="caseCategory", description="Category assigned to the case."
    )
    assigned_officers: Optional[str] = Field(
        None,
        alias="assignedOfficers",
        description="Comma-separated officers assigned to the case.",
    )
    status: Optional[datetime] = Field(
        None,
        description="Status timestamp, preserved from the supplied schema.",
    )
    date_added: datetime = Field(
        alias="dateAdded", description="Time when the case was added."
    )
    date_modified: datetime = Field(
        alias="dateModified", description="Time when the case was last modified."
    )
    added_by: Optional[str] = Field(
        None, alias="addedBy", description="User who added the case."
    )
    modified_by: Optional[str] = Field(
        None, alias="modifiedBy", description="User who last modified the case."
    )
class UploadUrlResponse(BaseModel):
    """Short-lived Supabase Storage URL for one direct object upload."""

    upload_url: str = Field(
        alias="uploadUrl",
        description="Signed Supabase Storage upload URL, valid for about two hours.",
    )


class AuditFields(BaseModel):
    """Audit columns shared by entity-resolution resources."""

    date_added: datetime = Field(alias="dateAdded")
    date_modified: datetime = Field(alias="dateModified")
    added_by: Optional[str] = Field(None, alias="addedBy")
    modified_by: Optional[str] = Field(None, alias="modifiedBy")


class EntityResponse(AuditFields):
    id: int
    entity_name: Optional[str] = Field(None, alias="entityName")
    label: Optional[str] = None
    entity_description: Optional[str] = Field(None, alias="entityDescription")
    is_standard: Optional[str] = Field(None, alias="isStandard")


class EntityAttributeResponse(AuditFields):
    id: int
    attribute_type: Optional[str] = Field(None, alias="attributeType")
    attribute_data_type: Optional[str] = Field(None, alias="attributeDataType")
    attribute_description: Optional[str] = Field(
        None, alias="attributeDescription"
    )
    entity_id: int = Field(alias="entityId")


class RelationshipResponse(AuditFields):
    id: int
    relationship_name: Optional[str] = Field(None, alias="relationshipName")
    relationship_description: Optional[str] = Field(
        None, alias="relationshipDescription"
    )
    is_standard: Optional[str] = Field(None, alias="isStandard")


class RelationshipAttributeResponse(AuditFields):
    id: int
    attribute_type: Optional[str] = Field(None, alias="attributeType")
    relationship_id: int = Field(alias="relationshipId")
    attribute_description: Optional[str] = Field(
        None, alias="attributeDescription"
    )
    attribute_data_type: Optional[str] = Field(None, alias="attributeDataType")


class ExtractedEntityRelationshipResponse(AuditFields):
    id: int
    case_id: int = Field(alias="caseId")
    extracted_details: Any = Field(alias="extractedDetails")
    is_standard: Optional[str] = Field(None, alias="isStandard")
