INSERT INTO relationship_attribute_details (
    id,
    attribute_type,
    relationship_id,
    attribute_description,
    attribute_data_type,
    added_by,
    modified_by
)
VALUES
    (4001, 'job_title', 3001, 'Job title held by the person.', 'string', 'system', 'system'),
    (4002, 'start_date', 3001, 'Date on which the employment began.', 'date', 'system', 'system'),
    (4003, 'end_date', 3001, 'Date on which the employment ended.', 'date', 'system', 'system'),
    (4004, 'location_context', 3002, 'Reason or context for the location association.', 'string', 'system', 'system'),
    (4005, 'page_number', 3003, 'Page on which the entity is mentioned.', 'integer', 'system', 'system'),
    (4006, 'mention_text', 3003, 'Relevant text surrounding the mention.', 'string', 'system', 'system'),
    (4007, 'participant_role', 3004, 'Role of the entity in the event.', 'string', 'system', 'system'),
    (4008, 'confidence_score', 3005, 'Extraction confidence from zero to one.', 'decimal', 'system', 'system'),
    (4009, 'ownership_percentage', 3006, 'Percentage owned or controlled.', 'decimal', 'system', 'system'),
    (4010, 'start_date', 3006, 'Date on which ownership began.', 'date', 'system', 'system'),
    (4011, 'membership_role', 3007, 'Role held by the member.', 'string', 'system', 'system'),
    (4012, 'communication_date', 3008, 'Date and time of the communication.', 'timestamp', 'system', 'system'),
    (4013, 'communication_channel', 3008, 'Communication channel, such as email, phone, or messaging.', 'string', 'system', 'system'),
    (4014, 'amount', 3009, 'Amount transferred, when applicable.', 'decimal', 'system', 'system'),
    (4015, 'currency', 3009, 'ISO currency code for the transferred amount.', 'string', 'system', 'system'),
    (4016, 'transfer_date', 3009, 'Date and time of the transfer.', 'timestamp', 'system', 'system'),
    (4017, 'occurrence_date', 3010, 'Date and time of the occurrence.', 'timestamp', 'system', 'system'),
    (4018, 'association_type', 3012, 'Nature of the association.', 'string', 'system', 'system'),
    (4019, 'confidence_score', 3012, 'Extraction confidence from zero to one.', 'decimal', 'system', 'system'),
    (4020, 'confidence_score', 3013, 'Entity-resolution confidence from zero to one.', 'decimal', 'system', 'system'),
    (4021, 'resolution_method', 3013, 'Method or model that produced the resolution.', 'string', 'system', 'system'),
    (4022, 'resolution_status', 3013, 'Status such as proposed, confirmed, rejected, or conflicted.', 'string', 'system', 'system'),
    (4023, 'observed_at', 3014, 'Date and time when the identifier was observed.', 'timestamp', 'system', 'system'),
    (4024, 'first_seen_at', 3014, 'Earliest supported observation time.', 'timestamp', 'system', 'system'),
    (4025, 'last_seen_at', 3014, 'Latest supported observation time.', 'timestamp', 'system', 'system'),
    (4026, 'source_reference', 3015, 'Reference used to drill down to the source artefact.', 'string', 'system', 'system'),
    (4027, 'evidence_hash', 3015, 'Cryptographic hash of the supporting artefact.', 'string', 'system', 'system'),
    (4028, 'extraction_tool', 3015, 'Tool and version that created the evidence link.', 'string', 'system', 'system'),
    (4029, 'co_occurrence_count', 3016, 'Number of supported co-occurrences.', 'integer', 'system', 'system'),
    (4030, 'window_seconds', 3016, 'Maximum temporal window used to define co-occurrence.', 'integer', 'system', 'system'),
    (4031, 'valid_from', 3017, 'Start of the supported identifier-use interval.', 'timestamp', 'system', 'system'),
    (4032, 'valid_to', 3017, 'End of the supported identifier-use interval.', 'timestamp', 'system', 'system'),
    (4033, 'confidence_score', 3017, 'Ownership or usage confidence from zero to one.', 'decimal', 'system', 'system'),
    (4034, 'contradiction_type', 3018, 'Nature of the conflicting evidence.', 'string', 'system', 'system'),
    (4035, 'review_status', 3018, 'Investigator review status for the contradiction.', 'string', 'system', 'system')
ON CONFLICT (id) DO NOTHING;

SELECT setval(
    pg_get_serial_sequence('relationship_attribute_details', 'id'),
    (SELECT MAX(id) FROM relationship_attribute_details)
);
