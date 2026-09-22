BEGIN;

DELETE FROM doctor_specialties
WHERE (doctor_id, specialty_id) IN (
        (
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
        )
    );

DELETE FROM doctors
WHERE
    id IN (
        '0dfc6223-6a11-4d90-a979-bd511bc1d6a9',
        '64a33ade-1719-4093-a6e1-2ea442e47e0b',
        '0466ab03-bb89-4b4e-9326-78edb1fe6aa2'
    );

DELETE FROM specialties
WHERE
    id IN (
        '694124aa-53a3-4021-9280-a404c0876c09',
        'cdcfe095-45e6-4d24-91b1-9efcc3f78835',
        'ef6ce6a2-102c-4447-8e38-6833a6ca463d'
    );

COMMIT;