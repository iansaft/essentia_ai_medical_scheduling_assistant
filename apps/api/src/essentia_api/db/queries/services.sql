-- name: ListActiveServices :many
SELECT
    id,
    code,
    name,
    description,
    price,
    currency,
    duration_minutes
FROM services
WHERE
    is_active = TRUE
ORDER BY name;

-- name: GetActiveServiceById :one
SELECT
    id,
    code,
    name,
    description,
    price,
    currency,
    duration_minutes
FROM services
WHERE
    id = $1
    AND is_active = TRUE;