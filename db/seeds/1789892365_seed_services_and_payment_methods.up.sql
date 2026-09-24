BEGIN;

-- Services

INSERT INTO
    services (
        id,
        code,
        name,
        description,
        price,
        currency,
        duration_minutes,
        is_active
    )
VALUES (
        'e2fb5edd-efbd-4d60-9de3-d6650e31562f',
        'cardiology_initial_consultation',
        'Consulta Inicial de Cardiologia',
        'Consulta inicial com cardiologista.',
        320.00,
        'BRL',
        45,
        TRUE
    ),
    (
        'b9d24a3f-45eb-48bf-9d48-1f075e4c40a3',
        'dermatology_consultation',
        'Consulta de Dermatologia',
        'Consulta geral com dermatologista.',
        250.00,
        'BRL',
        30,
        TRUE
    ),
    (
        '6640a42f-830c-4187-aacf-ed576b464b74',
        'general_medical_consultation',
        'Consulta Médica Geral',
        'Avaliação médica geral com médico de atenção primária.',
        180.00,
        'BRL',
        30,
        TRUE
    ),
    (
        '93391495-8729-48f7-86e7-b8052b53b868',
        'follow_up_consultation',
        'Consulta de Retorno',
        'Consulta de retorno após uma consulta médica anterior.',
        150.00,
        'BRL',
        30,
        TRUE
    );

-- Payment methods

INSERT INTO
    payment_methods (
        id,
        code,
        name,
        description,
        is_active
    )
VALUES (
        'a570a071-95f3-41ee-a8dc-8447ddf026b5',
        'pix',
        'PIX',
        'Pagamento instantâneo pelo sistema de pagamentos brasileiro PIX.',
        TRUE
    ),
    (
        'c7a8727c-c8bf-4964-8301-9ccfd3ab09ba',
        'credit_card',
        'Cartão de Crédito',
        'Pagamento com cartão de crédito.',
        TRUE
    ),
    (
        'ef967cb7-6a4d-4011-854b-a9408cc8c1d0',
        'debit_card',
        'Cartão de Débito',
        'Pagamento com cartão de débito.',
        TRUE
    ),
    (
        'e4b8c4d1-80cf-47f2-a271-627623e84be8',
        'cash',
        'Dinheiro',
        'Pagamento em dinheiro na clínica.',
        TRUE
    );

COMMIT;
