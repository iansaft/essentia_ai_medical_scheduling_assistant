BEGIN;

DELETE FROM patients
WHERE
    id IN (
        '3cdf666b-186d-44e6-bce9-5e572e7038f9',
        '9195382a-3a1c-44e7-94b6-6d55c8b9338f',
        'e8fd74e7-b450-47fe-84e8-e34813bb4031',
        '2338a014-ec7f-4585-a519-c15e9c20b11c'
    );

COMMIT;