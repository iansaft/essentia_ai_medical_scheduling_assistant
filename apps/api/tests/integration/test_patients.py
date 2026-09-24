import pytest
from fastapi.testclient import TestClient
from psycopg import Connection

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
from tests.support.problem import assert_problem

pytestmark = pytest.mark.integration


def _identity_headers(patient_id) -> dict[str, str]:
    return {"X-Patient-Id": str(patient_id)}


def _create_patient(
    client: TestClient,
    payload: dict,
):
    return client.post("/v1/patients", json=payload)


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
    response = client.get(
        f"/v1/patients/{PATIENT_MARIA}",
        headers=_identity_headers(PATIENT_MARIA),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(PATIENT_MARIA)
    assert body["full_name"] == "Maria Silva"
    assert body["is_active"] is True


def test_get_patient_as_another_patient_returns_403(client: TestClient) -> None:
    response = client.get(
        f"/v1/patients/{PATIENT_MARIA}",
        headers=_identity_headers(PATIENT_CARLOS),
    )

    assert_problem(response, 403, detail="Patient access denied.")


def test_get_patient_requires_identity_header(client: TestClient) -> None:
    response = client.get(f"/v1/patients/{PATIENT_MARIA}")

    assert response.status_code == 422


def test_get_nonexistent_patient_returns_404(client: TestClient) -> None:
    response = client.get(
        f"/v1/patients/{NON_EXISTENT_UUID}",
        headers=_identity_headers(NON_EXISTENT_UUID),
    )

    assert_problem(response, 404, detail="Patient not found.")


def test_get_patient_with_invalid_uuid_returns_422(client: TestClient) -> None:
    response = client.get(
        "/v1/patients/not-a-uuid",
        headers=_identity_headers(PATIENT_MARIA),
    )

    assert response.status_code == 422


def test_list_patient_appointments_includes_all_statuses(
    client: TestClient,
) -> None:
    response = client.get(
        f"/v1/patients/{PATIENT_CARLOS}/appointments",
        headers=_identity_headers(PATIENT_CARLOS),
    )

    assert response.status_code == 200
    body = response.json()
    statuses_by_id = {
        appointment["id"]: appointment["status"]
        for appointment in body
    }

    assert statuses_by_id[str(APPOINTMENT_CANCELLED)] == "cancelled"
    assert statuses_by_id[str(APPOINTMENT_NO_SHOW)] == "no_show"


def test_list_patient_appointments_as_another_patient_returns_403(
    client: TestClient,
) -> None:
    response = client.get(
        f"/v1/patients/{PATIENT_MARIA}/appointments",
        headers=_identity_headers(PATIENT_CARLOS),
    )

    assert_problem(response, 403, detail="Patient access denied.")


def test_list_patient_appointments_requires_identity_header(
    client: TestClient,
) -> None:
    response = client.get(f"/v1/patients/{PATIENT_MARIA}/appointments")

    assert response.status_code == 422


def test_list_patient_appointments_returns_scheduled_appointment(
    client: TestClient,
) -> None:
    response = client.get(
        f"/v1/patients/{PATIENT_MARIA}/appointments",
        headers=_identity_headers(PATIENT_MARIA),
    )

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
    response = client.get(
        f"/v1/patients/{PATIENT_ANA}/appointments",
        headers=_identity_headers(PATIENT_ANA),
    )

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
    response = client.get(
        f"/v1/patients/{PATIENT_CARLOS}/appointments",
        headers=_identity_headers(PATIENT_CARLOS),
    )

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
        headers=_identity_headers(PATIENT_LUCAS_INACTIVE),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_patient_appointments_nonexistent_patient_returns_404(
    client: TestClient,
) -> None:
    response = client.get(
        f"/v1/patients/{NON_EXISTENT_UUID}/appointments",
        headers=_identity_headers(NON_EXISTENT_UUID),
    )

    assert_problem(response, 404, detail="Patient not found.")


def test_list_patient_appointments_invalid_uuid_returns_422(
    client: TestClient,
) -> None:
    response = client.get(
        "/v1/patients/not-a-uuid/appointments",
        headers=_identity_headers(PATIENT_MARIA),
    )

    assert response.status_code == 422


def test_create_patient_happy_path(
    client: TestClient,
    db_connection: Connection,
) -> None:
    response = _create_patient(
        client,
        {
            "full_name": "Joana Souza",
            "email": "joana.souza@example.com",
            "phone": "+5548999990009",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "Joana Souza"
    assert body["email"] == "joana.souza@example.com"
    assert body["phone"] == "+5548999990009"
    assert body["is_active"] is True
    assert body["id"]
    assert body["created_at"]
    assert body["updated_at"]

    row = db_connection.execute(
        """
        SELECT full_name, email, phone, is_active
        FROM patients
        WHERE id = %s
        """,
        (body["id"],),
    ).fetchone()
    assert row == (
        "Joana Souza",
        "joana.souza@example.com",
        "+5548999990009",
        True,
    )


def test_create_patient_without_phone(
    client: TestClient,
    db_connection: Connection,
) -> None:
    response = _create_patient(
        client,
        {
            "full_name": "Joana Souza",
            "email": "joana.souza@example.com",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["phone"] is None

    row = db_connection.execute(
        "SELECT phone FROM patients WHERE id = %s",
        (body["id"],),
    ).fetchone()
    assert row == (None,)


def test_create_patient_is_open_without_identity_header(
    client: TestClient,
) -> None:
    response = _create_patient(
        client,
        {
            "full_name": "Joana Souza",
            "email": "joana.souza@example.com",
            "phone": "+5548999990009",
        },
    )

    assert response.status_code == 201


def test_create_patient_duplicate_email_returns_409(
    client: TestClient,
) -> None:
    response = _create_patient(
        client,
        {
            "full_name": "Maria Duplicada",
            "email": "maria.silva@example.com",
        },
    )

    assert_problem(
        response,
        409,
        detail="Patient email already exists.",
        problem_type="/problems/patient-email-already-exists",
    )


def test_create_patient_duplicate_email_case_insensitive_returns_409(
    client: TestClient,
) -> None:
    response = _create_patient(
        client,
        {
            "full_name": "Maria Duplicada",
            "email": "MARIA.SILVA@EXAMPLE.COM",
        },
    )

    assert_problem(
        response,
        409,
        detail="Patient email already exists.",
        problem_type="/problems/patient-email-already-exists",
    )


def test_create_patient_duplicate_phone_returns_409(
    client: TestClient,
) -> None:
    response = _create_patient(
        client,
        {
            "full_name": "Telefone Duplicado",
            "email": "telefone.duplicado@example.com",
            "phone": "+5548999990001",
        },
    )

    assert_problem(
        response,
        409,
        detail="Patient phone already exists.",
        problem_type="/problems/patient-phone-already-exists",
    )


def test_create_patient_blank_full_name_returns_422(
    client: TestClient,
) -> None:
    response = _create_patient(
        client,
        {
            "full_name": "   ",
            "email": "joana.souza@example.com",
        },
    )

    assert response.status_code == 422


def test_create_patient_blank_phone_returns_422(
    client: TestClient,
) -> None:
    response = _create_patient(
        client,
        {
            "full_name": "Joana Souza",
            "email": "joana.souza@example.com",
            "phone": "   ",
        },
    )

    assert response.status_code == 422


def test_create_patient_missing_email_returns_422(
    client: TestClient,
) -> None:
    response = _create_patient(
        client,
        {"full_name": "Joana Souza"},
    )

    assert response.status_code == 422
