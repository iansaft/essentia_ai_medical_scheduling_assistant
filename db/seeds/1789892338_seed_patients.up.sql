BEGIN;

INSERT INTO
    patients (
        id,
        full_name,
        email,
        phone,
        is_active
    )
VALUES (
        '3cdf666b-186d-44e6-bce9-5e572e7038f9',
        'Maria Silva',
        'maria.silva@example.com',
        '+5548999990001',
        TRUE
    ),
    (
        '9195382a-3a1c-44e7-94b6-6d55c8b9338f',
        'Carlos Souza',
        'carlos.souza@example.com',
        '+5548999990002',
        TRUE
    ),
    (
        'e8fd74e7-b450-47fe-84e8-e34813bb4031',
        'Ana Oliveira',
        'ana.oliveira@example.com',
        '+5548999990003',
        TRUE
    ),
    (
        '2338a014-ec7f-4585-a519-c15e9c20b11c',
        'Lucas Ferreira',
        'lucas.ferreira@example.com',
        '+5548999990004',
        FALSE
    );

COMMIT;