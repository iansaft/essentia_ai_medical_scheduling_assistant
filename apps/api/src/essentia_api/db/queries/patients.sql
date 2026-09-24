-- name: GetPatientById :one
SELECT
    id,
    full_name,
    email,
    phone,
    is_active,
    created_at,
    updated_at
FROM patients
WHERE
    id = $1;

-- name: ListPatients :many
SELECT
    id,
    full_name,
    email,
    phone,
    is_active,
    created_at,
    updated_at
FROM patients
ORDER BY
    created_at,
    id;

-- name: GetPatientByEmail :one
SELECT
    id,
    full_name,
    email,
    phone,
    is_active,
    created_at,
    updated_at
FROM patients
WHERE
    lower(email) = lower(sqlc.arg ('email')::text);

-- name: CreatePatient :one
INSERT INTO
    patients (
        full_name,
        email,
        phone
    )
VALUES (
        sqlc.arg ('full_name')::text,
        sqlc.arg ('email')::text,
        sqlc.narg ('phone')::text
    )
RETURNING
    id,
    full_name,
    email,
    phone,
    is_active,
    created_at,
    updated_at;