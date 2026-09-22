BEGIN;

CREATE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Uses wall-clock time instead of transaction start time so that
    -- multiple updates within the same transaction receive accurate timestamps.
    NEW.updated_at = clock_timestamp();

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_patients_set_updated_at
BEFORE UPDATE ON patients
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_specialties_set_updated_at
BEFORE UPDATE ON specialties
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_doctors_set_updated_at
BEFORE UPDATE ON doctors
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_services_set_updated_at
BEFORE UPDATE ON services
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_payment_methods_set_updated_at
BEFORE UPDATE ON payment_methods
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_service_payment_methods_set_updated_at
BEFORE UPDATE ON service_payment_methods
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_appointment_slots_set_updated_at
BEFORE UPDATE ON appointment_slots
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_appointments_set_updated_at
BEFORE UPDATE ON appointments
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_idempotency_requests_set_updated_at
BEFORE UPDATE ON idempotency_requests
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

COMMIT;