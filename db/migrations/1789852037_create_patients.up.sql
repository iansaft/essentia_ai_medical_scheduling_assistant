BEGIN;

CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT patients_full_name_not_blank CHECK (btrim (full_name) <> ''),
    CONSTRAINT patients_email_not_blank CHECK (btrim (email) <> ''),
    CONSTRAINT patients_phone_not_blank CHECK (
        phone IS NULL
        OR btrim (phone) <> ''
    )
);

CREATE UNIQUE INDEX uq_patients_email_lower ON patients (lower(email));

CREATE UNIQUE INDEX uq_patients_phone ON patients (phone);

COMMIT;
