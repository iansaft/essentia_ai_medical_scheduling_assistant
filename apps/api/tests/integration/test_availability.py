from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from psycopg import Connection

from tests.support.constants import (
    DOCTOR_HELENA,
    SERVICE_CARDIOLOGY,
    SLOT_HELENA_CARDIO_AVAILABLE,
    SLOT_HELENA_CARDIO_CANCELLED_HISTORY,
    SLOT_HELENA_CARDIO_D2,
    SLOT_HELENA_CARDIO_HISTORICAL,
    SLOT_HELENA_CARDIO_OCCUPIED,
    SLOT_HELENA_FOLLOW_UP_D2,
    SLOT_RAFAEL_DERMATOLOGY_BLOCKED,
)


pytestmark = pytest.mark.integration


def _slot_ids(response_body: list[dict]) -> set[str]:
    return {slot["id"] for slot in response_body}


def test_list_availability_returns_only_effectively_available_slots(
    client: TestClient,
) -> None:
    response = client.get("/v1/availability")

    assert response.status_code == 200
    slot_ids = _slot_ids(response.json())
    assert str(SLOT_HELENA_CARDIO_AVAILABLE) in slot_ids
    assert str(SLOT_HELENA_CARDIO_CANCELLED_HISTORY) in slot_ids
    assert str(SLOT_HELENA_CARDIO_OCCUPIED) not in slot_ids
    assert str(SLOT_RAFAEL_DERMATOLOGY_BLOCKED) not in slot_ids
    assert str(SLOT_HELENA_CARDIO_HISTORICAL) not in slot_ids


def test_filter_availability_by_doctor(client: TestClient) -> None:
    response = client.get(
        "/v1/availability",
        params={"doctor_id": str(DOCTOR_HELENA)},
    )

    assert response.status_code == 200
    slots = response.json()
    assert slots
    assert all(slot["doctor_id"] == str(DOCTOR_HELENA) for slot in slots)
    assert _slot_ids(slots) == {
        str(SLOT_HELENA_CARDIO_AVAILABLE),
        str(SLOT_HELENA_CARDIO_CANCELLED_HISTORY),
        str(SLOT_HELENA_CARDIO_D2),
        str(SLOT_HELENA_FOLLOW_UP_D2),
    }


def test_filter_availability_by_service(client: TestClient) -> None:
    response = client.get(
        "/v1/availability",
        params={"service_id": str(SERVICE_CARDIOLOGY)},
    )

    assert response.status_code == 200
    slots = response.json()
    assert slots
    assert all(slot["service_id"] == str(SERVICE_CARDIOLOGY) for slot in slots)
    assert _slot_ids(slots) == {
        str(SLOT_HELENA_CARDIO_AVAILABLE),
        str(SLOT_HELENA_CARDIO_CANCELLED_HISTORY),
        str(SLOT_HELENA_CARDIO_D2),
    }


def test_filter_availability_by_doctor_and_service(client: TestClient) -> None:
    response = client.get(
        "/v1/availability",
        params={
            "doctor_id": str(DOCTOR_HELENA),
            "service_id": str(SERVICE_CARDIOLOGY),
        },
    )

    assert response.status_code == 200
    assert _slot_ids(response.json()) == {
        str(SLOT_HELENA_CARDIO_AVAILABLE),
        str(SLOT_HELENA_CARDIO_CANCELLED_HISTORY),
        str(SLOT_HELENA_CARDIO_D2),
    }


def test_filter_availability_by_business_date(
    client: TestClient,
    db_connection: Connection,
) -> None:
    target_date = db_connection.execute(
        """
        SELECT (starts_at AT TIME ZONE 'America/Sao_Paulo')::date
        FROM appointment_slots
        WHERE id = %s
        """,
        (SLOT_HELENA_CARDIO_AVAILABLE,),
    ).fetchone()[0]

    response = client.get(
        "/v1/availability",
        params={"date": target_date.isoformat()},
    )

    assert response.status_code == 200
    slots = response.json()
    assert str(SLOT_HELENA_CARDIO_AVAILABLE) in _slot_ids(slots)

    for slot in slots:
        local_date = db_connection.execute(
            """
            SELECT (starts_at AT TIME ZONE 'America/Sao_Paulo')::date
            FROM appointment_slots
            WHERE id = %s
            """,
            (slot["id"],),
        ).fetchone()[0]
        assert local_date == target_date


def test_cancelled_appointment_does_not_keep_future_open_slot_occupied(
    client: TestClient,
) -> None:
    response = client.get("/v1/availability")

    assert response.status_code == 200
    assert str(SLOT_HELENA_CARDIO_CANCELLED_HISTORY) in _slot_ids(response.json())


def test_past_open_slot_is_not_available(
    client: TestClient,
    db_connection: Connection,
) -> None:
    past_slot_id = uuid4()
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
        (past_slot_id, DOCTOR_HELENA, SERVICE_CARDIOLOGY),
    )

    response = client.get("/v1/availability")

    assert response.status_code == 200
    assert str(past_slot_id) not in _slot_ids(response.json())


def test_slots_from_inactive_doctor_are_not_available(
    client: TestClient,
    db_connection: Connection,
) -> None:
    db_connection.execute(
        "UPDATE doctors SET is_active = FALSE WHERE id = %s",
        (DOCTOR_HELENA,),
    )

    response = client.get("/v1/availability")

    assert response.status_code == 200
    assert all(
        slot["doctor_id"] != str(DOCTOR_HELENA)
        for slot in response.json()
    )


def test_slots_from_inactive_service_are_not_available(
    client: TestClient,
    db_connection: Connection,
) -> None:
    db_connection.execute(
        "UPDATE services SET is_active = FALSE WHERE id = %s",
        (SERVICE_CARDIOLOGY,),
    )

    response = client.get("/v1/availability")

    assert response.status_code == 200
    assert all(
        slot["service_id"] != str(SERVICE_CARDIOLOGY)
        for slot in response.json()
    )


def test_invalid_availability_date_returns_422(client: TestClient) -> None:
    response = client.get(
        "/v1/availability",
        params={"date": "21-09-2026"},
    )

    assert response.status_code == 422
