BEGIN;

-- Cardiology appointment slots

INSERT INTO
    appointment_slots (
        id,
        doctor_id,
        service_id,
        starts_at,
        ends_at,
        status,
        status_reason
    )
VALUES (
        '8e06b231-a27f-4bf3-bc69-7565f20c3f7d',
        '0dfc6223-6a11-4d90-a979-bd511bc1d6a9',
        'e2fb5edd-efbd-4d60-9de3-d6650e31562f',
        (
            (CURRENT_DATE + 1) + TIME '09:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE + 1) + TIME '09:45'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'open',
        NULL
    ),
    (
        '26036bfd-3ba4-405d-9e7a-4df6a540ee1f',
        '0dfc6223-6a11-4d90-a979-bd511bc1d6a9',
        'e2fb5edd-efbd-4d60-9de3-d6650e31562f',
        (
            (CURRENT_DATE + 1) + TIME '10:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE + 1) + TIME '10:45'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'open',
        NULL
    ),
    (
        '51d9ec84-aa0a-46ca-a37b-4952a5e35cc7',
        '0dfc6223-6a11-4d90-a979-bd511bc1d6a9',
        'e2fb5edd-efbd-4d60-9de3-d6650e31562f',
        (
            (CURRENT_DATE + 1) + TIME '11:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE + 1) + TIME '11:45'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'open',
        NULL
    ),
    (
        'a834893e-8336-4c78-8c27-84e60256e3c7',
        '0dfc6223-6a11-4d90-a979-bd511bc1d6a9',
        'e2fb5edd-efbd-4d60-9de3-d6650e31562f',
        (
            (CURRENT_DATE + 2) + TIME '09:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE + 2) + TIME '09:45'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'open',
        NULL
    ),
    (
        '217c57f6-d78f-475d-8557-975d7af79d81',
        '0dfc6223-6a11-4d90-a979-bd511bc1d6a9',
        '93391495-8729-48f7-86e7-b8052b53b868',
        (
            (CURRENT_DATE + 2) + TIME '10:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE + 2) + TIME '10:30'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'open',
        NULL
    );

-- Dermatology appointment slots

INSERT INTO
    appointment_slots (
        id,
        doctor_id,
        service_id,
        starts_at,
        ends_at,
        status,
        status_reason
    )
VALUES (
        '7d25ff3c-b772-4b73-afa2-794071397b86',
        '64a33ade-1719-4093-a6e1-2ea442e47e0b',
        'b9d24a3f-45eb-48bf-9d48-1f075e4c40a3',
        (
            (CURRENT_DATE + 1) + TIME '14:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE + 1) + TIME '14:30'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'open',
        NULL
    ),
    (
        '7b983580-560d-42d5-a40a-8189b8035dbc',
        '64a33ade-1719-4093-a6e1-2ea442e47e0b',
        'b9d24a3f-45eb-48bf-9d48-1f075e4c40a3',
        (
            (CURRENT_DATE + 1) + TIME '14:30'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE + 1) + TIME '15:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'blocked',
        'Administrative block'
    ),
    (
        '63d4a85a-bf72-414a-a849-e11aedf0be59',
        '64a33ade-1719-4093-a6e1-2ea442e47e0b',
        'b9d24a3f-45eb-48bf-9d48-1f075e4c40a3',
        (
            (CURRENT_DATE + 2) + TIME '15:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE + 2) + TIME '15:30'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'open',
        NULL
    );

-- General practice appointment slots

INSERT INTO
    appointment_slots (
        id,
        doctor_id,
        service_id,
        starts_at,
        ends_at,
        status,
        status_reason
    )
VALUES (
        '3f28f670-d1f2-4279-bad8-a5c3af470764',
        '0466ab03-bb89-4b4e-9326-78edb1fe6aa2',
        '6640a42f-830c-4187-aacf-ed576b464b74',
        (
            (CURRENT_DATE + 1) + TIME '08:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE + 1) + TIME '08:30'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'open',
        NULL
    ),
    (
        '5c84f94d-07d4-48a0-8e43-a5409af6623c',
        '0466ab03-bb89-4b4e-9326-78edb1fe6aa2',
        '6640a42f-830c-4187-aacf-ed576b464b74',
        (
            (CURRENT_DATE + 1) + TIME '08:30'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE + 1) + TIME '09:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'open',
        NULL
    ),
    (
        'f9790797-1fef-47ac-9c90-d682a9aaa9d1',
        '0466ab03-bb89-4b4e-9326-78edb1fe6aa2',
        '6640a42f-830c-4187-aacf-ed576b464b74',
        (
            (CURRENT_DATE + 2) + TIME '08:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE + 2) + TIME '08:30'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'open',
        NULL
    );

-- Historical appointment slots

INSERT INTO
    appointment_slots (
        id,
        doctor_id,
        service_id,
        starts_at,
        ends_at,
        status,
        status_reason
    )
VALUES (
        '2d4a9c21-db19-40a7-a10e-6179921145cd',
        '0dfc6223-6a11-4d90-a979-bd511bc1d6a9',
        'e2fb5edd-efbd-4d60-9de3-d6650e31562f',
        (
            (CURRENT_DATE - 1) + TIME '10:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE - 1) + TIME '10:45'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'closed',
        'Historical completed slot'
    ),
    (
        'd59462db-a8f2-425e-9cdc-52c055f08c90',
        '64a33ade-1719-4093-a6e1-2ea442e47e0b',
        'b9d24a3f-45eb-48bf-9d48-1f075e4c40a3',
        (
            (CURRENT_DATE - 2) + TIME '15:00'
        ) AT TIME ZONE 'America/Sao_Paulo',
        (
            (CURRENT_DATE - 2) + TIME '15:30'
        ) AT TIME ZONE 'America/Sao_Paulo',
        'closed',
        'Historical no-show slot'
    );

COMMIT;