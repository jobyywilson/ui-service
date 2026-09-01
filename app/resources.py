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
