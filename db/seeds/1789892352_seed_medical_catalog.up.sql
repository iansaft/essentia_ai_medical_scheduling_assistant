BEGIN;

-- Specialties

INSERT INTO
    specialties (
        id,
        code,
        name,
        description,
        is_active
    )
VALUES (
        '694124aa-53a3-4021-9280-a404c0876c09',
        'cardiology',
        'Cardiology',
        'Medical specialty focused on cardiovascular health.',
        TRUE
    ),
    (
        'cdcfe095-45e6-4d24-91b1-9efcc3f78835',
        'dermatology',
        'Dermatology',
        'Medical specialty focused on skin, hair, and nail conditions.',
        TRUE
    ),
    (
        'ef6ce6a2-102c-4447-8e38-6833a6ca463d',
        'general_practice',
        'General Practice',
        'General medical consultations and primary care.',
        TRUE
    );

-- Doctors

INSERT INTO
    doctors (
        id,
        full_name,
        email,
        registration_number,
        registration_state,
        is_active
    )
VALUES (
        '0dfc6223-6a11-4d90-a979-bd511bc1d6a9',
        'Dr. Helena Costa',
        'helena.costa@example.com',
        '12345',
        'SC',
        TRUE
    ),
    (
        '64a33ade-1719-4093-a6e1-2ea442e47e0b',
        'Dr. Rafael Lima',
        'rafael.lima@example.com',
        '23456',
        'SC',
        TRUE
    ),
    (
        '0466ab03-bb89-4b4e-9326-78edb1fe6aa2',
        'Dr. Bruno Martins',
        'bruno.martins@example.com',
        '34567',
        'SC',
        TRUE
    );

-- Doctor specialty assignments

INSERT INTO
    doctor_specialties (doctor_id, specialty_id)
VALUES (
        '0dfc6223-6a11-4d90-a979-bd511bc1d6a9',
        '694124aa-53a3-4021-9280-a404c0876c09'
    ),
    (
        '64a33ade-1719-4093-a6e1-2ea442e47e0b',
        'cdcfe095-45e6-4d24-91b1-9efcc3f78835'
    ),
    (
        '0466ab03-bb89-4b4e-9326-78edb1fe6aa2',
        'ef6ce6a2-102c-4447-8e38-6833a6ca463d'
    );

COMMIT;