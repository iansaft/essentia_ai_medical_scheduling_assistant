BEGIN;

DROP TRIGGER trg_idempotency_requests_set_updated_at ON idempotency_requests;

DROP TRIGGER trg_appointments_set_updated_at ON appointments;

DROP TRIGGER trg_appointment_slots_set_updated_at ON appointment_slots;

DROP TRIGGER trg_service_payment_methods_set_updated_at ON service_payment_methods;

DROP TRIGGER trg_payment_methods_set_updated_at ON payment_methods;

DROP TRIGGER trg_services_set_updated_at ON services;

DROP TRIGGER trg_doctors_set_updated_at ON doctors;

DROP TRIGGER trg_specialties_set_updated_at ON specialties;

DROP TRIGGER trg_patients_set_updated_at ON patients;

DROP FUNCTION set_updated_at ();

COMMIT;