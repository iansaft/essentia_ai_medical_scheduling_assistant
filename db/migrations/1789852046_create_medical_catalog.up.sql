BEGIN;

CREATE TABLE specialties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT specialties_code_not_blank CHECK (btrim (code) <> ''),
    CONSTRAINT specialties_name_not_blank CHECK (btrim (name) <> '')
);

CREATE UNIQUE INDEX uq_specialties_code_lower ON specialties (lower(code));


CREATE TABLE doctors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    full_name TEXT NOT NULL,
    email TEXT,

-- Simplified Brazilian medical professional registration.

registration_number TEXT NOT NULL,
    registration_state CHAR(2) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT doctors_full_name_not_blank
        CHECK (btrim(full_name) <> ''),

    CONSTRAINT doctors_email_not_blank
        CHECK (
            email IS NULL
            OR btrim(email) <> ''
        ),

    CONSTRAINT doctors_registration_number_not_blank
        CHECK (btrim(registration_number) <> ''),

    CONSTRAINT doctors_registration_state_valid
        CHECK (registration_state ~ '^[A-Z]{2}$'),

    CONSTRAINT uq_doctors_registration
        UNIQUE (
            registration_state,
            registration_number
        )
);

CREATE UNIQUE INDEX uq_doctors_email_lower ON doctors (lower(email))
WHERE
    email IS NOT NULL;

CREATE TABLE doctor_specialties (
    doctor_id UUID NOT NULL,
    specialty_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (doctor_id, specialty_id),
    CONSTRAINT fk_doctor_specialties_doctor FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE,
    CONSTRAINT fk_doctor_specialties_specialty FOREIGN KEY (specialty_id) REFERENCES specialties (id) ON DELETE CASCADE
);

CREATE INDEX idx_doctor_specialties_specialty_id ON doctor_specialties (specialty_id);

COMMIT;