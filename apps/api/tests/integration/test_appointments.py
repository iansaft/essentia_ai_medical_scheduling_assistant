from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import Connection

from tests.support.constants import (
    APPOINTMENT_CANCELLED,
    APPOINTMENT_COMPLETED,
    APPOINTMENT_NO_SHOW,
    APPOINTMENT_SCHEDULED,
    DOCTOR_HELENA,
    NON_EXISTENT_UUID,
    PATIENT_ANA,
    PATIENT_CARLOS,
    PATIENT_LUCAS_INACTIVE,
    PATIENT_MARIA,
    SERVICE_CARDIOLOGY,
    SLOT_HELENA_CARDIO_AVAILABLE,
    SLOT_HELENA_CARDIO_D2,
    SLOT_HELENA_CARDIO_OCCUPIED,
    SLOT_RAFAEL_DERMATOLOGY_BLOCKED,
)


pytestmark = pytest.mark.integration


def _create_appointment(
    client: TestClient,
    *,
    patient_id: UUID = PATIENT_CARLOS,
    slot_id: UUID = SLOT_HELENA_CARDIO_AVAILABLE,
    idempotency_key: str | None = None,
):
    headers = {}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key

    return client.post(
        "/v1/appointments",
        headers=headers,
        json={
            "patient_id": str(patient_id),
            "slot_id": str(slot_id),
        },
    )


def _cancel_appointment(
    client: TestClient,
    *,
    appointment_id: UUID,
    reason: str,
    idempotency_key: str | None = None,
):
    headers = {}
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key

    return client.post(
        f"/v1/appointments/{appointment_id}/cancel",
        headers=headers,
        json={"cancellation_reason": reason},
    )


def test_get_existing_appointment(client: TestClient) -> None:
    response = client.get(f"/v1/appointments/{APPOINTMENT_SCHEDULED}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(APPOINTMENT_SCHEDULED)
    assert body["patient_id"] == str(PATIENT_MARIA)
    assert body["slot_id"] == str(SLOT_HELENA_CARDIO_OCCUPIED)
    assert body["status"] == "scheduled"
    assert Decimal(str(body["price_amount"])) == Decimal("320.00")
    assert body["currency"] == "BRL"


def test_get_nonexistent_appointment_returns_404(client: TestClient) -> None:
    response = client.get(f"/v1/appointments/{NON_EXISTENT_UUID}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Appointment not found."


def test_historical_appointment_keeps_price_snapshot(client: TestClient) -> None:
    response = client.get(f"/v1/appointments/{APPOINTMENT_COMPLETED}")

    assert response.status_code == 200
    assert Decimal(str(response.json()["price_amount"])) == Decimal("300.00")


def test_create_appointment_happy_path(
    client: TestClient,
    db_connection: Connection,
) -> None:
    response = _create_appointment(
        client,
        idempotency_key="create-happy-path",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["patient_id"] == str(PATIENT_CARLOS)
    assert body["slot_id"] == str(SLOT_HELENA_CARDIO_AVAILABLE)
    assert body["doctor_id"] == str(DOCTOR_HELENA)
    assert body["service_id"] == str(SERVICE_CARDIOLOGY)
    assert body["status"] == "scheduled"
    assert Decimal(str(body["price_amount"])) == Decimal("320.00")
    assert body["currency"] == "BRL"

    row = db_connection.execute(
        """
        SELECT patient_id, slot_id, status, price_amount, currency
        FROM appointments
        WHERE id = %s
        """,
        (body["id"],),
    ).fetchone()

    assert row == (
        PATIENT_CARLOS,
        SLOT_HELENA_CARDIO_AVAILABLE,
        "scheduled",
        Decimal("320.00"),
        "BRL",
    )


def test_create_appointment_derives_price_from_service(client: TestClient) -> None:
    response = _create_appointment(
        client,
        idempotency_key="derived-price",
    )

    assert response.status_code == 201
    body = response.json()
    assert Decimal(str(body["price_amount"])) == Decimal("320.00")
    assert body["currency"] == "BRL"


def test_created_appointment_keeps_price_snapshot_after_catalog_change(
    client: TestClient,
    db_connection: Connection,
) -> None:
    create_response = _create_appointment(
        client,
        idempotency_key="price-snapshot",
    )
    assert create_response.status_code == 201
    appointment_id = create_response.json()["id"]

    db_connection.execute(
        "UPDATE services SET price = 999.99 WHERE id = %s",
        (SERVICE_CARDIOLOGY,),
    )

    response = client.get(f"/v1/appointments/{appointment_id}")

    assert response.status_code == 200
    assert Decimal(str(response.json()["price_amount"])) == Decimal("320.00")


def test_create_appointment_rejects_inactive_patient(client: TestClient) -> None:
    response = _create_appointment(
        client,
        patient_id=PATIENT_LUCAS_INACTIVE,
        idempotency_key="inactive-patient",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Inactive patients cannot book appointments."


def test_create_appointment_returns_404_for_unknown_slot(client: TestClient) -> None:
    response = _create_appointment(
        client,
        slot_id=NON_EXISTENT_UUID,
        idempotency_key="unknown-slot",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Appointment slot not found."


def test_create_appointment_rejects_blocked_slot(client: TestClient) -> None:
    response = _create_appointment(
        client,
        slot_id=SLOT_RAFAEL_DERMATOLOGY_BLOCKED,
        idempotency_key="blocked-slot",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Appointment slot is not open."


def test_create_appointment_rejects_past_open_slot(
    client: TestClient,
    db_connection: Connection,
) -> None:
    slot_id = uuid4()
    db_connection.execute(
        """
        INSERT INTO appointment_slots (
            id, doctor_id, service_id, starts_at, ends_at, status
        )
        VALUES (
            %s, %s, %s,
            CURRENT_TIMESTAMP - INTERVAL '10 days',
            CURRENT_TIMESTAMP - INTERVAL '10 days' + INTERVAL '45 minutes',
            'open'
        )
        """,
        (slot_id, DOCTOR_HELENA, SERVICE_CARDIOLOGY),
    )

    response = _create_appointment(
        client,
        slot_id=slot_id,
        idempotency_key="past-slot",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Past appointment slots cannot be booked."


def test_create_appointment_rejects_inactive_doctor(
    client: TestClient,
    db_connection: Connection,
) -> None:
    db_connection.execute(
        "UPDATE doctors SET is_active = FALSE WHERE id = %s",
        (DOCTOR_HELENA,),
    )

    response = _create_appointment(
        client,
        idempotency_key="inactive-doctor",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "The doctor assigned to this slot is inactive."


def test_create_appointment_rejects_inactive_service(
    client: TestClient,
    db_connection: Connection,
) -> None:
    db_connection.execute(
        "UPDATE services SET is_active = FALSE WHERE id = %s",
        (SERVICE_CARDIOLOGY,),
    )

    response = _create_appointment(
        client,
        idempotency_key="inactive-service",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "The service assigned to this slot is inactive."


def test_create_appointment_prevents_double_booking(client: TestClient) -> None:
    first = _create_appointment(
        client,
        patient_id=PATIENT_CARLOS,
        idempotency_key="double-booking-first",
    )
    second = _create_appointment(
        client,
        patient_id=PATIENT_ANA,
        idempotency_key="double-booking-second",
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == "Appointment slot is already booked."


def test_create_appointment_replays_same_idempotency_key(
    client: TestClient,
    db_connection: Connection,
) -> None:
    first = _create_appointment(
        client,
        idempotency_key="create-replay",
    )
    second = _create_appointment(
        client,
        idempotency_key="create-replay",
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json() == first.json()

    count = db_connection.execute(
        "SELECT COUNT(*) FROM appointments WHERE id = %s",
        (first.json()["id"],),
    ).fetchone()[0]
    assert count == 1


def test_create_appointment_rejects_idempotency_key_reused_with_new_payload(
    client: TestClient,
) -> None:
    first = _create_appointment(
        client,
        slot_id=SLOT_HELENA_CARDIO_AVAILABLE,
        idempotency_key="create-conflicting-payload",
    )
    second = _create_appointment(
        client,
        slot_id=SLOT_HELENA_CARDIO_D2,
        idempotency_key="create-conflicting-payload",
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert "different request" in second.json()["detail"]


def test_create_appointment_requires_idempotency_key(client: TestClient) -> None:
    response = _create_appointment(client, idempotency_key=None)

    assert response.status_code == 422


def test_concurrent_booking_allows_exactly_one_appointment(
    test_database: str,
) -> None:
    from essentia_api.schemas.appointments import CreateAppointmentRequest
    from essentia_api.services.appointments import (
        SlotUnavailableError,
        create_appointment,
    )

    barrier = Barrier(2)

    def attempt(patient_id: UUID, idempotency_key: str) -> str:
        with psycopg.connect(test_database) as connection:
            barrier.wait(timeout=5)
            try:
                create_appointment(
                    connection,
                    command=CreateAppointmentRequest(
                        patient_id=patient_id,
                        slot_id=SLOT_HELENA_CARDIO_AVAILABLE,
                    ),
                    idempotency_key=idempotency_key,
                )
                return "created"
            except SlotUnavailableError:
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(attempt, PATIENT_CARLOS, "concurrent-1"),
            executor.submit(attempt, PATIENT_ANA, "concurrent-2"),
        ]
        outcomes = [future.result(timeout=10) for future in futures]

    assert sorted(outcomes) == ["conflict", "created"]


def test_cancel_scheduled_appointment(
    client: TestClient,
    db_connection: Connection,
) -> None:
    response = _cancel_appointment(
        client,
        appointment_id=APPOINTMENT_SCHEDULED,
        reason="Patient requested cancellation.",
        idempotency_key="cancel-happy-path",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(APPOINTMENT_SCHEDULED)
    assert body["status"] == "cancelled"
    assert body["cancellation_reason"] == "Patient requested cancellation."
    assert body["cancelled_at"] is not None

    row = db_connection.execute(
        """
        SELECT status, cancellation_reason, cancelled_at, COUNT(*) OVER ()
        FROM appointments
        WHERE id = %s
        """,
        (APPOINTMENT_SCHEDULED,),
    ).fetchone()
    assert row[0] == "cancelled"
    assert row[1] == "Patient requested cancellation."
    assert row[2] is not None
    assert row[3] == 1


def test_cancel_nonexistent_appointment_returns_404(client: TestClient) -> None:
    response = _cancel_appointment(
        client,
        appointment_id=NON_EXISTENT_UUID,
        reason="Patient requested cancellation.",
        idempotency_key="cancel-nonexistent",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Appointment not found."


def test_cancel_already_cancelled_appointment_returns_409(client: TestClient) -> None:
    response = _cancel_appointment(
        client,
        appointment_id=APPOINTMENT_CANCELLED,
        reason="Second cancellation attempt.",
        idempotency_key="cancel-already-cancelled",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Only scheduled appointments can be cancelled."


@pytest.mark.parametrize("appointment_id", [APPOINTMENT_COMPLETED, APPOINTMENT_NO_SHOW])
def test_cancel_historical_appointment_returns_409(
    client: TestClient,
    appointment_id: UUID,
) -> None:
    response = _cancel_appointment(
        client,
        appointment_id=appointment_id,
        reason="Invalid historical cancellation.",
        idempotency_key=f"cancel-{appointment_id}",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Only scheduled appointments can be cancelled."


def test_cancel_replays_same_idempotency_key(client: TestClient) -> None:
    first = _cancel_appointment(
        client,
        appointment_id=APPOINTMENT_SCHEDULED,
        reason="Patient requested cancellation.",
        idempotency_key="cancel-replay",
    )
    second = _cancel_appointment(
        client,
        appointment_id=APPOINTMENT_SCHEDULED,
        reason="Patient requested cancellation.",
        idempotency_key="cancel-replay",
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()


def test_cancel_rejects_idempotency_key_reused_with_new_payload(
    client: TestClient,
) -> None:
    first = _cancel_appointment(
        client,
        appointment_id=APPOINTMENT_SCHEDULED,
        reason="Patient requested cancellation.",
        idempotency_key="cancel-conflicting-payload",
    )
    second = _cancel_appointment(
        client,
        appointment_id=APPOINTMENT_SCHEDULED,
        reason="Different cancellation reason.",
        idempotency_key="cancel-conflicting-payload",
    )

    assert first.status_code == 200
    assert second.status_code == 409
    assert "different request" in second.json()["detail"]


def test_cancel_requires_idempotency_key(client: TestClient) -> None:
    response = _cancel_appointment(
        client,
        appointment_id=APPOINTMENT_SCHEDULED,
        reason="Patient requested cancellation.",
        idempotency_key=None,
    )

    assert response.status_code == 422


def test_cancelled_appointment_releases_future_open_slot(client: TestClient) -> None:
    params = {
        "doctor_id": str(DOCTOR_HELENA),
        "service_id": str(SERVICE_CARDIOLOGY),
    }

    before = client.get("/v1/availability", params=params)
    assert before.status_code == 200
    before_ids = {slot["id"] for slot in before.json()}
    assert str(SLOT_HELENA_CARDIO_OCCUPIED) not in before_ids

    cancellation = _cancel_appointment(
        client,
        appointment_id=APPOINTMENT_SCHEDULED,
        reason="Patient requested cancellation.",
        idempotency_key="cancel-release-slot",
    )
    assert cancellation.status_code == 200

    after = client.get("/v1/availability", params=params)
    assert after.status_code == 200
    after_ids = {slot["id"] for slot in after.json()}
    assert str(SLOT_HELENA_CARDIO_OCCUPIED) in after_ids
