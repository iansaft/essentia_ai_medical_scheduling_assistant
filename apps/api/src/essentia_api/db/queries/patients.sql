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