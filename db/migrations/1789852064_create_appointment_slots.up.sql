BEGIN;

CREATE TABLE appointment_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

-- A slot represents an explicit service offering
-- from a specific doctor at a specific time interval.
doctor_id UUID NOT NULL,
service_id UUID NOT NULL,
starts_at TIMESTAMPTZ NOT NULL,
ends_at TIMESTAMPTZ NOT NULL,

-- "open" means that the slot may be offered by the clinic.
-- Effective availability also requires that no scheduled
-- appointment currently occupies the slot.
status TEXT NOT NULL DEFAULT 'open',
status_reason TEXT,
created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

-- Ensures that a slot can only be created for a service
-- that is actually offered by the associated doctor.
CONSTRAINT fk_appointment_slots_doctor_service FOREIGN KEY (doctor_id, service_id) REFERENCES doctor_services (doctor_id, service_id) ON DELETE RESTRICT,
CONSTRAINT appointment_slots_valid_interval CHECK (ends_at > starts_at),
CONSTRAINT appointment_slots_valid_status CHECK (
    status IN ('open', 'blocked', 'closed')
),
CONSTRAINT appointment_slots_status_reason_not_blank CHECK (
    status_reason IS NULL
    OR btrim (status_reason) <> ''
),

-- Prevents overlapping slots for the same doctor,
-- regardless of the service associated with each slot.
--
-- Half-open intervals allow adjacent slots such as:
-- [14:00, 14:30) and [14:30, 15:00).
CONSTRAINT appointment_slots_doctor_time_no_overlap
        EXCLUDE USING gist (
            doctor_id WITH =,
            tstzrange(
                starts_at,
                ends_at,
                '[)'
            ) WITH &&
        )
);

CREATE INDEX idx_appointment_slots_doctor_starts_at ON appointment_slots (doctor_id, starts_at);

CREATE INDEX idx_appointment_slots_service_starts_at ON appointment_slots (service_id, starts_at);

CREATE INDEX idx_appointment_slots_open_lookup ON appointment_slots (
    doctor_id,
    service_id,
    starts_at
)
WHERE
    status = 'open';

COMMIT;