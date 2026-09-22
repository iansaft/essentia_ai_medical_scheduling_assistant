-- name: DeleteExpiredIdempotencyRequest :exec
DELETE FROM idempotency_requests
WHERE operation = sqlc.arg('operation')::text
  AND idempotency_key = sqlc.arg('idempotency_key')::text
  AND expires_at <= CURRENT_TIMESTAMP;

-- name: TryCreateIdempotencyRequest :one
INSERT INTO idempotency_requests (
    idempotency_key,
    operation,
    request_hash,
    state,
    expires_at
)
VALUES (
    sqlc.arg('idempotency_key')::text,
    sqlc.arg('operation')::text,
    sqlc.arg('request_hash')::text,
    'processing',
    CURRENT_TIMESTAMP + INTERVAL '24 hours'
)
ON CONFLICT (operation, idempotency_key) DO NOTHING
RETURNING id AS idempotency_request_id;

-- name: GetIdempotencyRequest :one
SELECT
    id,
    idempotency_key,
    operation,
    request_hash,
    state,
    resource_type,
    resource_id,
    response_status,
    response_body,
    completed_at,
    expires_at
FROM idempotency_requests
WHERE operation = sqlc.arg('operation')::text
  AND idempotency_key = sqlc.arg('idempotency_key')::text
FOR UPDATE;

-- name: CompleteIdempotencyRequest :exec
UPDATE idempotency_requests
SET
    state = 'completed',
    resource_type = 'appointment',
    resource_id = sqlc.arg('resource_id')::uuid,
    response_status = sqlc.arg('response_status')::integer,
    response_body = sqlc.arg('response_body')::jsonb,
    completed_at = clock_timestamp()
WHERE operation = sqlc.arg('operation')::text
  AND idempotency_key = sqlc.arg('idempotency_key')::text
  AND request_hash = sqlc.arg('request_hash')::text
  AND state = 'processing';
