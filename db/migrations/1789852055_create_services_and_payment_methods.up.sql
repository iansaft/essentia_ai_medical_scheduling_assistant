BEGIN;

CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price NUMERIC(12, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'BRL',
    duration_minutes INTEGER NOT NULL DEFAULT 30,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT services_code_not_blank CHECK (btrim (code) <> ''),
    CONSTRAINT services_name_not_blank CHECK (btrim (name) <> ''),
    CONSTRAINT services_price_non_negative CHECK (price >= 0),
    CONSTRAINT services_currency_valid CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT services_duration_positive CHECK (duration_minutes > 0)
);

CREATE UNIQUE INDEX uq_services_code_lower ON services (lower(code));

CREATE TABLE doctor_services (
    doctor_id UUID NOT NULL,
    service_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (doctor_id, service_id),
    CONSTRAINT fk_doctor_services_doctor FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE,
    CONSTRAINT fk_doctor_services_service FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE
);

CREATE INDEX idx_doctor_services_service_id ON doctor_services (service_id);

CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT payment_methods_code_not_blank CHECK (btrim (code) <> ''),
    CONSTRAINT payment_methods_name_not_blank CHECK (btrim (name) <> '')
);

CREATE UNIQUE INDEX uq_payment_methods_code_lower ON payment_methods (lower(code));

CREATE TABLE service_payment_methods (
    service_id UUID NOT NULL,
    payment_method_id UUID NOT NULL,
    max_installments SMALLINT NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (service_id, payment_method_id),
    CONSTRAINT fk_service_payment_methods_service FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE,
    CONSTRAINT fk_service_payment_methods_payment_method FOREIGN KEY (payment_method_id) REFERENCES payment_methods (id) ON DELETE CASCADE,
    CONSTRAINT service_payment_methods_max_installments_valid CHECK (
        max_installments BETWEEN 1 AND 36
    ),
    CONSTRAINT service_payment_methods_notes_not_blank CHECK (
        notes IS NULL
        OR btrim (notes) <> ''
    )
);

CREATE INDEX idx_service_payment_methods_payment_method_id ON service_payment_methods (payment_method_id);

COMMIT;