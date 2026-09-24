BEGIN;

-- Scheduled appointment.
-- This appointment occupies a future cardiology slot and must therefore
-- cause availability queries to exclude that slot.

INSERT INTO
    appointments (
        id,
        patient_id,
        slot_id,
        status,
        price_amount,
        currency
    )
VALUES (
        '8029d8d3-8fff-4dcc-a2ef-2ae0808bf95e',
        '3cdf666b-186d-44e6-bce9-5e572e7038f9',
        '26036bfd-3ba4-405d-9e7a-4df6a540ee1f',
        'scheduled',
        320.00,
        'BRL'
    );

-- Cancelled appointment.
-- The associated slot remains available because cancelled appointments
-- do not participate in the scheduled-slot uniqueness constraint.

INSERT INTO
    appointments (
        id,
        patient_id,
        slot_id,
        status,
        price_amount,
        currency,
        cancellation_reason,
        cancelled_at
    )
VALUES (
        'd6e99970-3b01-43c4-84a9-4042188262be',
        '9195382a-3a1c-44e7-94b6-6d55c8b9338f',
        '51d9ec84-aa0a-46ca-a37b-4952a5e35cc7',
        'cancelled',
        320.00,
        'BRL',
        'Cancelamento solicitado pelo paciente',
        CURRENT_TIMESTAMP - INTERVAL '1 hour'
    );

-- Completed historical appointment.
-- The price intentionally differs from the current service price to
-- demonstrate preservation of the commercial snapshot captured at booking.

INSERT INTO
    appointments (
        id,
        patient_id,
        slot_id,
        status,
        price_amount,
        currency,
        completed_at
    )
VALUES (
        '75adebb0-cff9-4a8c-9dfc-43bc321fabed',
        'e8fd74e7-b450-47fe-84e8-e34813bb4031',
        '2d4a9c21-db19-40a7-a10e-6179921145cd',
        'completed',
        300.00,
        'BRL',
        (
            DATE '2026-09-19' + TIME '10:50'
        ) AT TIME ZONE 'America/Sao_Paulo'
    );

-- Historical no-show appointment.

INSERT INTO
    appointments (
        id,
        patient_id,
        slot_id,
        status,
        price_amount,
        currency
    )
VALUES (
        '607179d5-2c1e-45ca-96bd-4a3593462caa',
        '9195382a-3a1c-44e7-94b6-6d55c8b9338f',
        'd59462db-a8f2-425e-9cdc-52c055f08c90',
        'no_show',
        250.00,
        'BRL'
    );

COMMIT;