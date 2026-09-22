BEGIN;

-- Doctor service offerings

INSERT INTO
    doctor_services (doctor_id, service_id)
VALUES (
        '0dfc6223-6a11-4d90-a979-bd511bc1d6a9',
        'e2fb5edd-efbd-4d60-9de3-d6650e31562f'
    ),
    (
        '0dfc6223-6a11-4d90-a979-bd511bc1d6a9',
        '93391495-8729-48f7-86e7-b8052b53b868'
    ),
    (
        '64a33ade-1719-4093-a6e1-2ea442e47e0b',
        'b9d24a3f-45eb-48bf-9d48-1f075e4c40a3'
    ),
    (
        '64a33ade-1719-4093-a6e1-2ea442e47e0b',
        '93391495-8729-48f7-86e7-b8052b53b868'
    ),
    (
        '0466ab03-bb89-4b4e-9326-78edb1fe6aa2',
        '6640a42f-830c-4187-aacf-ed576b464b74'
    ),
    (
        '0466ab03-bb89-4b4e-9326-78edb1fe6aa2',
        '93391495-8729-48f7-86e7-b8052b53b868'
    );

-- Cardiology payment methods

INSERT INTO
    service_payment_methods (
        service_id,
        payment_method_id,
        max_installments,
        notes
    )
VALUES (
        'e2fb5edd-efbd-4d60-9de3-d6650e31562f',
        'a570a071-95f3-41ee-a8dc-8447ddf026b5',
        1,
        NULL
    ),
    (
        'e2fb5edd-efbd-4d60-9de3-d6650e31562f',
        'c7a8727c-c8bf-4964-8301-9ccfd3ab09ba',
        6,
        'Interest-free installments supported up to six payments.'
    ),
    (
        'e2fb5edd-efbd-4d60-9de3-d6650e31562f',
        'ef967cb7-6a4d-4011-854b-a9408cc8c1d0',
        1,
        NULL
    );

-- Dermatology payment methods

INSERT INTO
    service_payment_methods (
        service_id,
        payment_method_id,
        max_installments,
        notes
    )
VALUES (
        'b9d24a3f-45eb-48bf-9d48-1f075e4c40a3',
        'a570a071-95f3-41ee-a8dc-8447ddf026b5',
        1,
        NULL
    ),
    (
        'b9d24a3f-45eb-48bf-9d48-1f075e4c40a3',
        'c7a8727c-c8bf-4964-8301-9ccfd3ab09ba',
        4,
        'Interest-free installments supported up to four payments.'
    ),
    (
        'b9d24a3f-45eb-48bf-9d48-1f075e4c40a3',
        'ef967cb7-6a4d-4011-854b-a9408cc8c1d0',
        1,
        NULL
    );

-- General consultation payment methods

INSERT INTO
    service_payment_methods (
        service_id,
        payment_method_id,
        max_installments,
        notes
    )
VALUES (
        '6640a42f-830c-4187-aacf-ed576b464b74',
        'a570a071-95f3-41ee-a8dc-8447ddf026b5',
        1,
        NULL
    ),
    (
        '6640a42f-830c-4187-aacf-ed576b464b74',
        'c7a8727c-c8bf-4964-8301-9ccfd3ab09ba',
        3,
        'Interest-free installments supported up to three payments.'
    ),
    (
        '6640a42f-830c-4187-aacf-ed576b464b74',
        'ef967cb7-6a4d-4011-854b-a9408cc8c1d0',
        1,
        NULL
    ),
    (
        '6640a42f-830c-4187-aacf-ed576b464b74',
        'e4b8c4d1-80cf-47f2-a271-627623e84be8',
        1,
        NULL
    );

-- Follow-up payment methods

INSERT INTO
    service_payment_methods (
        service_id,
        payment_method_id,
        max_installments,
        notes
    )
VALUES (
        '93391495-8729-48f7-86e7-b8052b53b868',
        'a570a071-95f3-41ee-a8dc-8447ddf026b5',
        1,
        NULL
    ),
    (
        '93391495-8729-48f7-86e7-b8052b53b868',
        'c7a8727c-c8bf-4964-8301-9ccfd3ab09ba',
        3,
        'Interest-free installments supported up to three payments.'
    ),
    (
        '93391495-8729-48f7-86e7-b8052b53b868',
        'ef967cb7-6a4d-4011-854b-a9408cc8c1d0',
        1,
        NULL
    );

COMMIT;