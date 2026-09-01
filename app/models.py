"""Pydantic response contracts exposed in the OpenAPI schema."""

from datetime import datetime
from typing import Optional

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


class FileResponse(BaseModel):
    """Public camelCase representation of one ``file_details`` row."""

    id: int = Field(description="File identifier.")
    file_name: str = Field(alias="fileName", description="Stored file name.")
    case_id: int = Field(alias="caseId", description="Associated case identifier.")
    extracted_content: Optional[str] = Field(
        None,
        alias="extractedContent",
        description="Text, OCR content, or transcript extracted from the file.",
    )
    date_added: datetime = Field(
        alias="dateAdded", description="Time when the file was added."
    )
    date_modified: datetime = Field(
        alias="dateModified", description="Time when the file was last modified."
    )
    added_by: Optional[str] = Field(
        None, alias="addedBy", description="User who added the file."
    )
    modified_by: Optional[str] = Field(
        None, alias="modifiedBy", description="User who last modified the file."
    )


class UploadUrlResponse(BaseModel):
    """Short-lived Supabase Storage URL for one direct object upload."""

    upload_url: str = Field(
        alias="uploadUrl",
        description="Signed Supabase Storage upload URL, valid for about two hours.",
    )
