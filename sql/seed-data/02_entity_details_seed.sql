INSERT INTO entity_details (
    id,
    entity_name,
    label,
    entity_description,
    is_standard,
    added_by,
    modified_by
)
VALUES
    (1001, 'PERSON', 'Person', 'An individual referenced in the source material.', 'Y', 'system', 'system'),
    (1002, 'ORGANIZATION', 'Organization', 'A company, agency, institution, or other organized group.', 'Y', 'system', 'system'),
    (1003, 'LOCATION', 'Location', 'A physical or geographic place.', 'Y', 'system', 'system'),
    (1004, 'DOCUMENT', 'Document', 'A physical or electronic document referenced by the case.', 'Y', 'system', 'system'),
    (1005, 'EVENT', 'Event', 'An occurrence associated with a date, time, or location.', 'Y', 'system', 'system'),
    (1006, 'WORK_OF_ART', 'Work of Art', 'A titled creative work, including a book, song, film, or painting.', 'Y', 'system', 'system'),
    (1007, 'CONSUMER_GOOD', 'Consumer Good', 'A product or other good intended for consumers.', 'Y', 'system', 'system'),
    (1008, 'PHONE_NUMBER', 'Phone Number', 'A telephone number found in the source material.', 'Y', 'system', 'system'),
    (1009, 'ADDRESS', 'Address', 'A postal or physical address found in the source material.', 'Y', 'system', 'system'),
    (1010, 'DATE', 'Date', 'A calendar date or date expression.', 'Y', 'system', 'system'),
    (1011, 'NUMBER', 'Number', 'A numeric value or numeric expression.', 'Y', 'system', 'system'),
    (1012, 'PRICE', 'Price', 'A monetary value with an optional currency.', 'Y', 'system', 'system'),
    (1013, 'FACILITY', 'Facility', 'A building, airport, highway, bridge, or other named facility.', 'Y', 'system', 'system'),
    (1014, 'GEOPOLITICAL_ENTITY', 'Geopolitical Entity', 'A country, city, state, or other geopolitical area.', 'Y', 'system', 'system'),
    (1015, 'NATIONALITY_RELIGIOUS_POLITICAL_GROUP', 'Nationality, Religious or Political Group', 'A nationality, religious group, or political group.', 'Y', 'system', 'system'),
    (1016, 'LAW', 'Law', 'A named law, regulation, statute, or legal instrument.', 'Y', 'system', 'system'),
    (1017, 'LANGUAGE', 'Language', 'A named natural or formal language.', 'Y', 'system', 'system'),
    (1018, 'PERCENT', 'Percent', 'A percentage value or expression.', 'Y', 'system', 'system'),
    (1019, 'QUANTITY', 'Quantity', 'A measured quantity with an optional unit.', 'Y', 'system', 'system'),
    (1020, 'TIME', 'Time', 'A time of day or time expression.', 'Y', 'system', 'system'),
    (1021, 'EMAIL_ADDRESS', 'Email Address', 'An email address found in the source material.', 'Y', 'system', 'system'),
    (1022, 'URL', 'URL', 'A web address or other uniform resource locator.', 'Y', 'system', 'system'),
    (1023, 'IP_ADDRESS', 'IP Address', 'An IPv4 or IPv6 network address.', 'Y', 'system', 'system'),
    (1024, 'VEHICLE', 'Vehicle', 'A vehicle identified by registration, make, model, or other details.', 'Y', 'system', 'system'),
    (1025, 'ACCOUNT', 'Account', 'A financial, online, customer, or other identifiable account.', 'Y', 'system', 'system'),
    (1026, 'TRANSACTION', 'Transaction', 'A transfer, payment, purchase, withdrawal, or other transaction.', 'Y', 'system', 'system'),
    (1027, 'USERNAME', 'Username', 'A username or account handle observed in an application or service.', 'Y', 'system', 'system'),
    (1028, 'DEVICE_IDENTIFIER', 'Device Identifier', 'A hardware, advertising, installation, SIM, or application device identifier.', 'Y', 'system', 'system'),
    (1029, 'WALLET_ADDRESS', 'Wallet Address', 'A cryptocurrency or distributed-ledger wallet address.', 'Y', 'system', 'system'),
    (1030, 'GROUP', 'Group', 'A chat group, channel, community, or other membership-based collection.', 'Y', 'system', 'system'),
    (1031, 'DEVICE', 'Device', 'A physical or virtual device from which identifiers or evidence were observed.', 'Y', 'system', 'system'),
    (1032, 'ARTEFACT', 'Artefact', 'A source file, record, message, database row, or other evidential artefact.', 'Y', 'system', 'system'),
    (1033, 'IDENTITY', 'Identity', 'A consolidated identity produced by resolving identifiers across sources.', 'Y', 'system', 'system')
ON CONFLICT (id) DO UPDATE
SET entity_name = EXCLUDED.entity_name,
    label = EXCLUDED.label,
    entity_description = EXCLUDED.entity_description,
    is_standard = EXCLUDED.is_standard,
    date_modified = CURRENT_TIMESTAMP,
    modified_by = EXCLUDED.modified_by;

SELECT setval(
    pg_get_serial_sequence('entity_details', 'id'),
    (SELECT MAX(id) FROM entity_details)
);
