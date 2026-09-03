INSERT INTO relationship_details (
    id,
    relationship_name,
    relationship_description,
    is_standard,
    added_by,
    modified_by
)
VALUES
    (3001, 'EMPLOYED_BY', 'A person is or was employed by an organization.', 'Y', 'system', 'system'),
    (3002, 'LOCATED_AT', 'An entity is associated with a location.', 'Y', 'system', 'system'),
    (3003, 'MENTIONED_IN', 'An entity is mentioned in a document.', 'Y', 'system', 'system'),
    (3004, 'PARTICIPATED_IN', 'A person or organization participated in an event.', 'Y', 'system', 'system'),
    (3005, 'RELATED_TO', 'A general relationship exists between two entities.', 'Y', 'system', 'system'),
    (3006, 'OWNS', 'An entity owns or controls another entity or asset.', 'Y', 'system', 'system'),
    (3007, 'MEMBER_OF', 'A person or organization is a member of another organization or group.', 'Y', 'system', 'system'),
    (3008, 'COMMUNICATED_WITH', 'Two entities participated in a communication.', 'Y', 'system', 'system'),
    (3009, 'TRANSFERRED_TO', 'An asset, amount, or transaction was transferred to a target entity.', 'Y', 'system', 'system'),
    (3010, 'OCCURRED_AT', 'An event or transaction occurred at a location or facility.', 'Y', 'system', 'system'),
    (3011, 'PART_OF', 'An entity forms part of another entity.', 'Y', 'system', 'system'),
    (3012, 'ASSOCIATED_WITH', 'An entity has a meaningful association with another entity.', 'Y', 'system', 'system'),
    (3013, 'RESOLVED_TO', 'An identifier is resolved to a consolidated identity.', 'Y', 'system', 'system'),
    (3014, 'OBSERVED_ON', 'An identifier or entity was observed on a source device.', 'Y', 'system', 'system'),
    (3015, 'SUPPORTED_BY', 'A node or edge is supported by an evidential artefact.', 'Y', 'system', 'system'),
    (3016, 'CO_OCCURRED_WITH', 'Two entities occurred in the same artefact, conversation, event, or time window.', 'Y', 'system', 'system'),
    (3017, 'USED_IDENTIFIER', 'An identity or person used or controlled an identifier.', 'Y', 'system', 'system'),
    (3018, 'CONTRADICTS', 'Evidence conflicts with another resolution, ownership claim, or relationship.', 'Y', 'system', 'system')
ON CONFLICT (id) DO NOTHING;

SELECT setval(
    pg_get_serial_sequence('relationship_details', 'id'),
    (SELECT MAX(id) FROM relationship_details)
);
