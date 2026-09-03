-- Sample data for case_details and file_details.
--
-- This script is safe to run more than once: rows with the same primary key
-- are left unchanged. The status values are timestamps because the supplied
-- schema defines case_details.status as TIMESTAMP.

BEGIN;

INSERT INTO case_details (
    id,
    case_description,
    case_category,
    assigned_officers,
    status,
    date_added,
    date_modified,
    added_by,
    modified_by
)
VALUES
    (
        1001,
        'Customer reported an unauthorized card transaction.',
        'Fraud',
        'Anita Rao, David Thomas',
        TIMESTAMP '2026-08-29 11:15:00',
        TIMESTAMP '2026-08-25 09:30:00',
        TIMESTAMP '2026-08-29 11:15:00',
        'system.admin',
        'anita.rao'
    ),
    (
        1002,
        'Address verification documents require review.',
        'KYC',
        'Meera Nair',
        TIMESTAMP '2026-08-30 13:20:00',
        TIMESTAMP '2026-08-26 07:45:00',
        TIMESTAMP '2026-08-30 13:20:00',
        'case.intake',
        'meera.nair'
    ),
    (
        1003,
        'Duplicate payment dispute resolved with the customer.',
        'Payment Dispute',
        'David Thomas',
        TIMESTAMP '2026-08-28 15:40:00',
        TIMESTAMP '2026-08-20 12:10:00',
        TIMESTAMP '2026-08-28 15:40:00',
        'support.agent',
        'david.thomas'
    ),
    (
        1004,
        'Potential account takeover flagged by monitoring.',
        'Fraud',
        'Anita Rao',
        TIMESTAMP '2026-09-01 05:25:00',
        TIMESTAMP '2026-08-31 18:05:00',
        TIMESTAMP '2026-09-01 05:25:00',
        'fraud.monitor',
        'anita.rao'
    )
ON CONFLICT (id) DO NOTHING;

INSERT INTO file_details (
    id,
    file_name,
    case_id,
    extracted_content,
    date_added,
    date_modified,
    added_by,
    modified_by
)
VALUES
    (
        501,
        'transaction-statement.pdf',
        1001,
        'Statement shows an unrecognized card transaction for INR 24,500.',
        TIMESTAMP '2026-08-25 10:15:00',
        TIMESTAMP '2026-08-25 10:15:00',
        'system.admin',
        'system.admin'
    ),
    (
        502,
        'identity-proof.png',
        1002,
        'OCR extracted the customer name, address, and document number.',
        TIMESTAMP '2026-08-26 08:30:00',
        TIMESTAMP '2026-08-27 09:10:00',
        'case.intake',
        'meera.nair'
    ),
    (
        503,
        'customer-call.mp3',
        1003,
        'Transcript confirms that the duplicate payment dispute was resolved.',
        TIMESTAMP '2026-08-27 14:20:00',
        TIMESTAMP '2026-08-28 15:40:00',
        'support.agent',
        'david.thomas'
    ),
    (
        504,
        'account-activity.csv',
        1004,
        'Login activity includes multiple attempts from an unfamiliar location.',
        TIMESTAMP '2026-09-01 05:10:00',
        TIMESTAMP '2026-09-01 05:25:00',
        'fraud.monitor',
        'anita.rao'
    ),
    (
        505,
        'investigation-notes.txt',
        1004,
        'Officer notes recommend escalating the account-takeover investigation.',
        TIMESTAMP '2026-09-01 06:00:00',
        TIMESTAMP '2026-09-01 06:00:00',
        'anita.rao',
        'anita.rao'
    )
ON CONFLICT (id) DO NOTHING;

-- Explicit seed IDs do not automatically advance identity sequences.
SELECT setval(
    pg_get_serial_sequence('case_details', 'id'),
    GREATEST(COALESCE((SELECT MAX(id) FROM case_details), 1), 1),
    true
);

SELECT setval(
    pg_get_serial_sequence('file_details', 'id'),
    GREATEST(COALESCE((SELECT MAX(id) FROM file_details), 1), 1),
    true
);

COMMIT;
