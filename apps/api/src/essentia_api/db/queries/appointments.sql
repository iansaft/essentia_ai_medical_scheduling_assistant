-- name: GetAppointmentById :one
SELECT
    a.id,
    a.patient_id,
    p.full_name AS patient_name,
    a.slot_id,
    aps.doctor_id,
    d.full_name AS doctor_name,
    aps.service_id,
    s.name AS service_name,
    aps.starts_at,
    aps.ends_at,
    a.status,
    a.price_amount,
    a.currency,
    a.cancellation_reason,
    a.cancelled_at,
    a.completed_at,
    a.created_at,
    a.updated_at
FROM
    appointments AS a
    JOIN patients AS p ON p.id = a.patient_id
    JOIN appointment_slots AS aps ON aps.id = a.slot_id
    JOIN doctors AS d ON d.id = aps.doctor_id
    JOIN services AS s ON s.id = aps.service_id
WHERE
    a.id = sqlc.arg ('appointment_id')::uuid;

-- name: ListAppointmentsByPatientId :many
SELECT
    a.id,
    a.patient_id,
    p.full_name AS patient_name,
    a.slot_id,
    aps.doctor_id,
    d.full_name AS doctor_name,
    aps.service_id,
    s.name AS service_name,
    aps.starts_at,
    aps.ends_at,
    a.status,
    a.price_amount,
    a.currency,
    a.cancellation_reason,
    a.cancelled_at,
    a.completed_at,
    a.created_at,
    a.updated_at
FROM
    appointments AS a
    JOIN patients AS p ON p.id = a.patient_id
    JOIN appointment_slots AS aps ON aps.id = a.slot_id
    JOIN doctors AS d ON d.id = aps.doctor_id
    JOIN services AS s ON s.id = aps.service_id
WHERE
    a.patient_id = sqlc.arg ('patient_id')::uuid
ORDER BY
    aps.starts_at DESC;

-- name: GetPatientForBooking :one
SELECT id, full_name, email, is_active
FROM patients
WHERE
    id = sqlc.arg ('patient_id')::uuid
FOR SHARE;

-- name: GetSlotForBooking :one
SELECT
    aps.id,
    aps.doctor_id,
    aps.service_id,
    aps.starts_at,
    aps.ends_at,
    aps.status,
    d.is_active AS doctor_is_active,
    s.is_active AS service_is_active,
    s.price,
    s.currency,
    aps.starts_at > CURRENT_TIMESTAMP AS is_future
FROM
    appointment_slots AS aps
    JOIN doctors AS d ON d.id = aps.doctor_id
    JOIN services AS s ON s.id = aps.service_id
WHERE
    aps.id = sqlc.arg ('slot_id')::uuid
FOR UPDATE OF
    aps;

-- name: CreateAppointment :one
INSERT INTO
    appointments (
        patient_id,
        slot_id,
        status,
        price_amount,
        currency
    )
VALUES (
        sqlc.arg ('patient_id')::uuid,
        sqlc.arg ('slot_id')::uuid,
        'scheduled',
        sqlc.arg ('price_amount')::numeric,
        sqlc.arg ('currency')::text
    )
ON CONFLICT DO NOTHING
RETURNING
    id AS appointment_id;

-- name: GetAppointmentForCancellation :one
SELECT id, status
FROM appointments
WHERE
    id = sqlc.arg ('appointment_id')::uuid
FOR UPDATE;

-- name: CancelAppointment :exec
UPDATE appointments
SET
    status = 'cancelled',
    cancellation_reason = sqlc.arg ('cancellation_reason')::text,
    cancelled_at = clock_timestamp()
WHERE
    id = sqlc.arg ('appointment_id')::uuid
    AND status = 'scheduled';