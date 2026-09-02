"""Allowlisted API resources and database column mappings."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import FrozenSet, Mapping, Tuple


@dataclass(frozen=True)
class ResourceDefinition:
    """Maps a public REST resource to a fixed table and column allowlist."""

    table: str
    singular_name: str
    fields: Mapping[str, str]
    exact_fields: FrozenSet[str]

    @property
    def searchable_fields(self) -> Tuple[str, ...]:
        """Return public camelCase fields in response order."""

        return tuple(self.fields)


CASES = ResourceDefinition(
    table="case_details",
    singular_name="Case",
    fields=MappingProxyType(
        {
            "id": "id",
            "caseDescription": "case_description",
            "caseCategory": "case_category",
            "assignedOfficers": "assigned_officers",
            "status": "status",
            "dateAdded": "date_added",
            "dateModified": "date_modified",
            "addedBy": "added_by",
            "modifiedBy": "modified_by",
        }
    ),
    exact_fields=frozenset({"id"}),
)

ENTITIES = ResourceDefinition(
    table="entity_details",
    singular_name="Entity definition",
    fields=MappingProxyType(
        {
            "id": "id",
            "entityName": "entity_name",
            "label": "label",
            "entityDescription": "entity_description",
            "isStandard": "is_standard",
            "dateAdded": "date_added",
            "dateModified": "date_modified",
            "addedBy": "added_by",
            "modifiedBy": "modified_by",
        }
    ),
    exact_fields=frozenset({"id"}),
)

ENTITY_ATTRIBUTES = ResourceDefinition(
    table="entity_attribute_details",
    singular_name="Entity attribute definition",
    fields=MappingProxyType(
        {
            "id": "id",
            "attributeType": "attribute_type",
            "attributeDataType": "attribute_data_type",
            "attributeDescription": "attribute_description",
            "entityId": "entity_id",
            "dateAdded": "date_added",
            "dateModified": "date_modified",
            "addedBy": "added_by",
            "modifiedBy": "modified_by",
        }
    ),
    exact_fields=frozenset({"id", "entityId"}),
)

RELATIONSHIPS = ResourceDefinition(
    table="relationship_details",
    singular_name="Relationship definition",
    fields=MappingProxyType(
        {
            "id": "id",
            "relationshipName": "relationship_name",
            "relationshipDescription": "relationship_description",
            "isStandard": "is_standard",
            "dateAdded": "date_added",
            "dateModified": "date_modified",
            "addedBy": "added_by",
            "modifiedBy": "modified_by",
        }
    ),
    exact_fields=frozenset({"id"}),
)

RELATIONSHIP_ATTRIBUTES = ResourceDefinition(
    table="relationship_attribute_details",
    singular_name="Relationship attribute definition",
    fields=MappingProxyType(
        {
            "id": "id",
            "attributeType": "attribute_type",
            "relationshipId": "relationship_id",
            "attributeDescription": "attribute_description",
            "attributeDataType": "attribute_data_type",
            "dateAdded": "date_added",
            "dateModified": "date_modified",
            "addedBy": "added_by",
            "modifiedBy": "modified_by",
        }
    ),
    exact_fields=frozenset({"id", "relationshipId"}),
)

EXTRACTED_ENTITY_RELATIONSHIPS = ResourceDefinition(
    table="extracted_entity_relationship",
    singular_name="Extracted entity relationship",
    fields=MappingProxyType(
        {
            "id": "id",
            "caseId": "case_id",
            "extractedDetails": "extracted_details",
            "isStandard": "is_standard",
            "dateAdded": "date_added",
            "dateModified": "date_modified",
            "addedBy": "added_by",
            "modifiedBy": "modified_by",
        }
    ),
    exact_fields=frozenset({"id", "caseId"}),
)
