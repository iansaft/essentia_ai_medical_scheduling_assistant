-- name: ListAvailableSlots :many
SELECT
    aps.id,
    aps.doctor_id,
    d.full_name AS doctor_name,
    aps.service_id,
    s.code AS service_code,
    s.name AS service_name,
    s.price,
    s.currency,
    aps.starts_at,
    aps.ends_at
FROM
    appointment_slots AS aps
    JOIN doctors AS d ON d.id = aps.doctor_id
    JOIN services AS s ON s.id = aps.service_id
WHERE
    aps.status = 'open'
    AND aps.starts_at > CURRENT_TIMESTAMP
    AND d.is_active = TRUE
    AND s.is_active = TRUE
    AND (
        sqlc.narg ('doctor_id')::uuid IS NULL
        OR aps.doctor_id = sqlc.narg ('doctor_id')
    )
    AND (
        sqlc.narg ('service_id')::uuid IS NULL
        OR aps.service_id = sqlc.narg ('service_id')
    )
    AND (
        sqlc.narg ('target_date')::date IS NULL
        OR (
            aps.starts_at AT TIME ZONE 'America/Sao_Paulo'
        )::date = sqlc.narg ('target_date')
    )
    AND NOT EXISTS (
        SELECT 1
        FROM appointments AS a
        WHERE
            a.slot_id = aps.id
            AND a.status = 'scheduled'
    )
ORDER BY aps.starts_at;