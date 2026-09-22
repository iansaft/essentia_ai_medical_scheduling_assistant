BEGIN;


CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    patient_id UUID NOT NULL,
    slot_id UUID NOT NULL,

    status TEXT NOT NULL DEFAULT 'scheduled',

-- Immutable commercial snapshot captured at booking time.
-- The API must derive these values from the service associated
-- with the selected slot and must never trust client-supplied pricing.

price_amount NUMERIC(12, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'BRL',

    cancellation_reason TEXT,
    cancelled_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_appointments_patient
        FOREIGN KEY (patient_id)
        REFERENCES patients (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_appointments_slot
        FOREIGN KEY (slot_id)
        REFERENCES appointment_slots (id)
        ON DELETE RESTRICT,

    CONSTRAINT appointments_valid_status
        CHECK (
            status IN (
                'scheduled',
                'cancelled',
                'completed',
                'no_show'
            )
        ),

    CONSTRAINT appointments_price_non_negative
        CHECK (price_amount >= 0),

    CONSTRAINT appointments_currency_valid
        CHECK (currency ~ '^[A-Z]{3}$'),

    CONSTRAINT appointments_cancellation_reason_not_blank
        CHECK (
            cancellation_reason IS NULL
            OR btrim(cancellation_reason) <> ''
        ),

    CONSTRAINT appointments_cancellation_state_consistency
        CHECK (
            (
                status = 'cancelled'
                AND cancelled_at IS NOT NULL
            )
            OR
            (
                status <> 'cancelled'
                AND cancelled_at IS NULL
            )
        ),

    CONSTRAINT appointments_completion_state_consistency
        CHECK (
            (
                status = 'completed'
                AND completed_at IS NOT NULL
            )
            OR
            (
                status <> 'completed'
                AND completed_at IS NULL
            )
        ),

    CONSTRAINT appointments_terminal_timestamps_not_conflicting
        CHECK (
            NOT (
                cancelled_at IS NOT NULL
                AND completed_at IS NOT NULL
            )
        )
);

-- Prevents concurrent double booking at the database level.
--
-- Only scheduled appointments occupy a slot. Historical cancelled,
-- completed, or no-show appointments may coexist with a new booking.
CREATE UNIQUE INDEX uq_appointments_scheduled_slot ON appointments (slot_id)
WHERE
    status = 'scheduled';

CREATE INDEX idx_appointments_slot_id ON appointments (slot_id);

CREATE INDEX idx_appointments_patient_id ON appointments (patient_id);

CREATE INDEX idx_appointments_patient_status ON appointments (patient_id, status);

CREATE INDEX idx_appointments_created_at ON appointments (created_at DESC);

COMMIT;