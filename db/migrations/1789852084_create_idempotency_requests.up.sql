BEGIN;

CREATE TABLE idempotency_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

-- Client-provided idempotency key scoped by operation.
idempotency_key TEXT NOT NULL, operation TEXT NOT NULL,

-- Hash of the canonical request payload.
-- Reusing the same key with a different payload must
-- be rejected by the application layer.
request_hash TEXT NOT NULL,

-- "processing" represents an in-flight request.
-- "completed" represents an operation whose response
-- may be safely replayed to subsequent retries.

state TEXT NOT NULL DEFAULT 'processing',

    resource_type TEXT,
    resource_id UUID,

    response_status SMALLINT,
    response_body JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,

    CONSTRAINT idempotency_requests_key_not_blank
        CHECK (btrim(idempotency_key) <> ''),

    CONSTRAINT idempotency_requests_operation_not_blank
        CHECK (btrim(operation) <> ''),

    CONSTRAINT idempotency_requests_request_hash_not_blank
        CHECK (btrim(request_hash) <> ''),

    CONSTRAINT idempotency_requests_valid_state
        CHECK (
            state IN (
                'processing',
                'completed'
            )
        ),

    CONSTRAINT idempotency_requests_resource_type_not_blank
        CHECK (
            resource_type IS NULL
            OR btrim(resource_type) <> ''
        ),

    CONSTRAINT idempotency_requests_response_status_valid
        CHECK (
            response_status IS NULL
            OR response_status BETWEEN 100 AND 599
        ),

    CONSTRAINT idempotency_requests_state_consistency
        CHECK (
            (
                state = 'processing'
                AND response_status IS NULL
                AND completed_at IS NULL
            )
            OR
            (
                state = 'completed'
                AND response_status IS NOT NULL
                AND completed_at IS NOT NULL
            )
        ),

    CONSTRAINT idempotency_requests_expiration_valid
        CHECK (
            expires_at IS NULL
            OR expires_at > created_at
        ),

    CONSTRAINT uq_idempotency_requests_operation_key
        UNIQUE (
            operation,
            idempotency_key
        )
);

CREATE INDEX idx_idempotency_requests_expires_at ON idempotency_requests (expires_at)
WHERE
    expires_at IS NOT NULL;

CREATE INDEX idx_idempotency_requests_resource ON idempotency_requests (resource_type, resource_id)
WHERE
    resource_id IS NOT NULL;

COMMIT;