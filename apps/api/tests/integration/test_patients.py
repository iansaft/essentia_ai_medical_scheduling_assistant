import pytest
from fastapi.testclient import TestClient

from tests.support.constants import (
    APPOINTMENT_CANCELLED,
    APPOINTMENT_COMPLETED,
    APPOINTMENT_NO_SHOW,
    APPOINTMENT_SCHEDULED,
    NON_EXISTENT_UUID,
    PATIENT_ANA,
    PATIENT_CARLOS,
    PATIENT_LUCAS_INACTIVE,
    PATIENT_MARIA,
)


pytestmark = pytest.mark.integration


def test_list_patients_returns_all_seed_patients(client: TestClient) -> None:
    response = client.get("/v1/patients")

    assert response.status_code == 200
    body = response.json()
    patients_by_id = {patient["id"]: patient for patient in body}

    assert set(patients_by_id) == {
        str(PATIENT_MARIA),
        str(PATIENT_CARLOS),
        str(PATIENT_ANA),
        str(PATIENT_LUCAS_INACTIVE),
    }
    assert patients_by_id[str(PATIENT_MARIA)]["full_name"] == "Maria Silva"
    assert patients_by_id[str(PATIENT_MARIA)]["email"] == (
        "maria.silva@example.com"
    )
    assert patients_by_id[str(PATIENT_MARIA)]["is_active"] is True
    assert patients_by_id[str(PATIENT_LUCAS_INACTIVE)]["is_active"] is False


def test_get_existing_patient(client: TestClient) -> None:
    response = client.get(f"/v1/patients/{PATIENT_MARIA}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(PATIENT_MARIA)
    assert body["full_name"] == "Maria Silva"
    assert body["is_active"] is True


def test_get_nonexistent_patient_returns_404(client: TestClient) -> None:
    response = client.get(f"/v1/patients/{NON_EXISTENT_UUID}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found."


def test_get_patient_with_invalid_uuid_returns_422(client: TestClient) -> None:
    response = client.get("/v1/patients/not-a-uuid")

    assert response.status_code == 422


def test_list_patient_appointments_includes_all_statuses(
    client: TestClient,
) -> None:
    response = client.get(f"/v1/patients/{PATIENT_CARLOS}/appointments")

    assert response.status_code == 200
    body = response.json()
    statuses_by_id = {
        appointment["id"]: appointment["status"]
        for appointment in body
    }

    assert statuses_by_id[str(APPOINTMENT_CANCELLED)] == "cancelled"
    assert statuses_by_id[str(APPOINTMENT_NO_SHOW)] == "no_show"


def test_list_patient_appointments_returns_scheduled_appointment(
    client: TestClient,
) -> None:
    response = client.get(f"/v1/patients/{PATIENT_MARIA}/appointments")

    assert response.status_code == 200
    body = response.json()
    scheduled = next(
        appointment
        for appointment in body
        if appointment["id"] == str(APPOINTMENT_SCHEDULED)
    )

    assert scheduled["status"] == "scheduled"
    assert scheduled["patient_id"] == str(PATIENT_MARIA)


def test_list_patient_appointments_preserves_price_snapshot(
    client: TestClient,
) -> None:
    response = client.get(f"/v1/patients/{PATIENT_ANA}/appointments")

    assert response.status_code == 200
    body = response.json()
    completed = next(
        appointment
        for appointment in body
        if appointment["id"] == str(APPOINTMENT_COMPLETED)
    )

    assert completed["status"] == "completed"
    assert completed["price_amount"] == "300.00"
    assert completed["currency"] == "BRL"


def test_list_patient_appointments_orders_by_starts_at_desc(
    client: TestClient,
) -> None:
    response = client.get(f"/v1/patients/{PATIENT_CARLOS}/appointments")

    assert response.status_code == 200
    starts_at_values = [
        appointment["starts_at"]
        for appointment in response.json()
    ]

    assert starts_at_values == sorted(
        starts_at_values,
        reverse=True,
    )


def test_list_patient_appointments_returns_empty_list_without_appointments(
    client: TestClient,
) -> None:
    response = client.get(
        f"/v1/patients/{PATIENT_LUCAS_INACTIVE}/appointments",
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_patient_appointments_nonexistent_patient_returns_404(
    client: TestClient,
) -> None:
    response = client.get(
        f"/v1/patients/{NON_EXISTENT_UUID}/appointments",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found."


def test_list_patient_appointments_invalid_uuid_returns_422(
    client: TestClient,
) -> None:
    response = client.get("/v1/patients/not-a-uuid/appointments")

    assert response.status_code == 422
