import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier
from typing import cast
from uuid import UUID

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import Connection
from redis import Redis

from essentia_api.cache.availability import (
    AvailabilityCache,
    build_availability_cache_key,
)
from essentia_api.db.generated import availability as availability_queries
from essentia_api.main import create_app
from tests.support.constants import (
    APPOINTMENT_SCHEDULED,
    DOCTOR_HELENA,
    DOCTOR_RAFAEL,
    PATIENT_ANA,
    PATIENT_CARLOS,
    PATIENT_LUCAS_INACTIVE,
    PATIENT_MARIA,
    SERVICE_CARDIOLOGY,
    SERVICE_DERMATOLOGY,
    SLOT_HELENA_CARDIO_AVAILABLE,
    SLOT_HELENA_CARDIO_D2,
    SLOT_HELENA_CARDIO_OCCUPIED,
)
from tests.support.problem import assert_problem

pytestmark = pytest.mark.integration


def _business_date(
    db_connection: Connection,
    slot_id: UUID,
) -> date:
    row = db_connection.execute(
        """
        SELECT (starts_at AT TIME ZONE 'America/Sao_Paulo')::date
        FROM appointment_slots
        WHERE id = %s
        """,
        (slot_id,),
    ).fetchone()
    assert row is not None
    return row[0]


def _slot_ids(payload: list[dict]) -> set[str]:
    return {slot["id"] for slot in payload}


@pytest.fixture
def availability_query_spy(
    monkeypatch: pytest.MonkeyPatch,
) -> list[dict]:
    calls: list[dict] = []
    original = availability_queries.list_available_slots

    def counting_list_available_slots(
        connection,
        **kwargs,
    ):
        calls.append(kwargs)
        return original(connection, **kwargs)

    monkeypatch.setattr(
        availability_queries,
        "list_available_slots",
        counting_list_available_slots,
    )
    return calls


def test_cache_miss_queries_postgres_and_populates_key(
    client: TestClient,
    redis_client: Redis,
    availability_query_spy: list[dict],
) -> None:
    params = {
        "doctor_id": str(DOCTOR_HELENA),
        "service_id": str(SERVICE_CARDIOLOGY),
    }

    response = client.get("/v1/availability", params=params)

    assert response.status_code == 200
    assert response.json()
    assert len(availability_query_spy) == 1

    key = build_availability_cache_key(
        service_id=SERVICE_CARDIOLOGY,
        doctor_id=DOCTOR_HELENA,
        target_date=None,
    )
    assert redis_client.exists(key) == 1

    ttl = redis_client.ttl(key)
    assert 0 < ttl <= 40

    raw = redis_client.get(key)
    assert raw is not None
    assert json.loads(raw) == response.json()


def test_cache_hit_serves_response_without_postgres(
    client: TestClient,
    availability_query_spy: list[dict],
) -> None:
    params = {
        "doctor_id": str(DOCTOR_HELENA),
        "service_id": str(SERVICE_CARDIOLOGY),
    }

    first = client.get("/v1/availability", params=params)
    assert first.status_code == 200
    assert len(availability_query_spy) == 1

    second = client.get("/v1/availability", params=params)
    assert second.status_code == 200
    assert second.json() == first.json()
    assert len(availability_query_spy) == 1


def test_empty_availability_result_is_cached_as_hit(
    client: TestClient,
    redis_client: Redis,
    availability_query_spy: list[dict],
) -> None:
    params = {"date": "2030-01-01"}

    first = client.get("/v1/availability", params=params)
    assert first.status_code == 200
    assert first.json() == []
    assert len(availability_query_spy) == 1

    key = build_availability_cache_key(
        service_id=None,
        doctor_id=None,
        target_date=date(2030, 1, 1),
    )
    assert redis_client.get(key) == "[]"

    second = client.get("/v1/availability", params=params)
    assert second.status_code == 200
    assert second.json() == []
    assert len(availability_query_spy) == 1


def test_expired_key_falls_back_to_postgres_and_repopulates(
    client: TestClient,
    redis_client: Redis,
    availability_query_spy: list[dict],
) -> None:
    params = {
        "doctor_id": str(DOCTOR_RAFAEL),
        "service_id": str(SERVICE_DERMATOLOGY),
    }

    first = client.get("/v1/availability", params=params)
    assert first.status_code == 200
    assert len(availability_query_spy) == 1

    key = build_availability_cache_key(
        service_id=SERVICE_DERMATOLOGY,
        doctor_id=DOCTOR_RAFAEL,
        target_date=None,
    )
    assert redis_client.exists(key) == 1
    assert redis_client.pexpire(key, 100) is True
    time.sleep(0.25)
    assert redis_client.exists(key) == 0

    second = client.get("/v1/availability", params=params)
    assert second.status_code == 200
    assert second.json() == first.json()
    assert len(availability_query_spy) == 2

    assert redis_client.exists(key) == 1
    assert redis_client.ttl(key) > 25


def test_booking_invalidates_populated_availability_keys(
    client: TestClient,
    redis_client: Redis,
    db_connection: Connection,
    availability_query_spy: list[dict],
) -> None:
    business_date = _business_date(
        db_connection,
        SLOT_HELENA_CARDIO_AVAILABLE,
    )
    exact_key = build_availability_cache_key(
        service_id=SERVICE_CARDIOLOGY,
        doctor_id=DOCTOR_HELENA,
        target_date=business_date,
    )
    no_date_key = build_availability_cache_key(
        service_id=SERVICE_CARDIOLOGY,
        doctor_id=DOCTOR_HELENA,
        target_date=None,
    )
    unfiltered_key = build_availability_cache_key(
        service_id=None,
        doctor_id=None,
        target_date=None,
    )

    with_date = client.get(
        "/v1/availability",
        params={
            "doctor_id": str(DOCTOR_HELENA),
            "service_id": str(SERVICE_CARDIOLOGY),
            "date": business_date.isoformat(),
        },
    )
    without_date = client.get(
        "/v1/availability",
        params={
            "doctor_id": str(DOCTOR_HELENA),
            "service_id": str(SERVICE_CARDIOLOGY),
        },
    )
    unfiltered = client.get("/v1/availability")
    assert with_date.status_code == 200
    assert without_date.status_code == 200
    assert unfiltered.status_code == 200
    assert str(SLOT_HELENA_CARDIO_AVAILABLE) in _slot_ids(with_date.json())

    assert redis_client.exists(exact_key) == 1
    assert redis_client.exists(no_date_key) == 1
    assert redis_client.exists(unfiltered_key) == 1

    booking = client.post(
        "/v1/appointments",
        headers={
            "X-Patient-Id": str(PATIENT_MARIA),
            "Idempotency-Key": "cache-booking-invalidation",
        },
        json={
            "patient_id": str(PATIENT_MARIA),
            "slot_id": str(SLOT_HELENA_CARDIO_AVAILABLE),
        },
    )
    assert booking.status_code == 201

    assert redis_client.exists(exact_key) == 0
    assert redis_client.exists(no_date_key) == 0
    assert redis_client.exists(unfiltered_key) == 0

    queries_before = len(availability_query_spy)
    after = client.get(
        "/v1/availability",
        params={
            "doctor_id": str(DOCTOR_HELENA),
            "service_id": str(SERVICE_CARDIOLOGY),
            "date": business_date.isoformat(),
        },
    )
    assert after.status_code == 200
    assert (
        str(SLOT_HELENA_CARDIO_AVAILABLE)
        not in _slot_ids(after.json())
    )
    assert len(availability_query_spy) == queries_before + 1


def test_cancellation_invalidates_key_and_releases_slot(
    client: TestClient,
    redis_client: Redis,
    db_connection: Connection,
) -> None:
    business_date = _business_date(
        db_connection,
        SLOT_HELENA_CARDIO_OCCUPIED,
    )
    params = {
        "doctor_id": str(DOCTOR_HELENA),
        "service_id": str(SERVICE_CARDIOLOGY),
        "date": business_date.isoformat(),
    }
    key = build_availability_cache_key(
        service_id=SERVICE_CARDIOLOGY,
        doctor_id=DOCTOR_HELENA,
        target_date=business_date,
    )

    before = client.get("/v1/availability", params=params)
    assert before.status_code == 200
    assert (
        str(SLOT_HELENA_CARDIO_OCCUPIED)
        not in _slot_ids(before.json())
    )
    assert redis_client.exists(key) == 1

    cancellation = client.post(
        f"/v1/appointments/{APPOINTMENT_SCHEDULED}/cancel",
        headers={
            "X-Patient-Id": str(PATIENT_MARIA),
            "Idempotency-Key": "cache-cancel-invalidation",
        },
        json={
            "cancellation_reason": "Cache invalidation test.",
        },
    )
    assert cancellation.status_code == 200
    assert redis_client.exists(key) == 0

    after = client.get("/v1/availability", params=params)
    assert after.status_code == 200
    assert str(SLOT_HELENA_CARDIO_OCCUPIED) in _slot_ids(after.json())


def test_failed_booking_does_not_invalidate_cache(
    client: TestClient,
    redis_client: Redis,
    db_connection: Connection,
) -> None:
    business_date = _business_date(
        db_connection,
        SLOT_HELENA_CARDIO_AVAILABLE,
    )
    params = {
        "doctor_id": str(DOCTOR_HELENA),
        "service_id": str(SERVICE_CARDIOLOGY),
        "date": business_date.isoformat(),
    }
    key = build_availability_cache_key(
        service_id=SERVICE_CARDIOLOGY,
        doctor_id=DOCTOR_HELENA,
        target_date=business_date,
    )

    populated = client.get("/v1/availability", params=params)
    assert populated.status_code == 200
    assert redis_client.exists(key) == 1

    failed_booking = client.post(
        "/v1/appointments",
        headers={
            "X-Patient-Id": str(PATIENT_LUCAS_INACTIVE),
            "Idempotency-Key": "cache-failed-booking",
        },
        json={
            "patient_id": str(PATIENT_LUCAS_INACTIVE),
            "slot_id": str(SLOT_HELENA_CARDIO_AVAILABLE),
        },
    )
    assert_problem(
        failed_booking,
        409,
        detail="Inactive patients cannot book appointments.",
    )

    assert redis_client.exists(key) == 1


def test_availability_survives_total_redis_outage(
    test_settings,
    db_connection: Connection,
) -> None:
    outage_settings = test_settings.model_copy(
        update={
            "redis_host": "127.0.0.1",
            "redis_port": 1,
            "redis_connect_timeout": 0.5,
            "redis_socket_timeout": 0.5,
        },
    )
    outage_app = create_app(settings=outage_settings)
    params = {
        "doctor_id": str(DOCTOR_HELENA),
        "service_id": str(SERVICE_CARDIOLOGY),
    }

    with TestClient(outage_app) as outage_client:
        first = outage_client.get("/v1/availability", params=params)
        second = outage_client.get("/v1/availability", params=params)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert str(SLOT_HELENA_CARDIO_AVAILABLE) in _slot_ids(first.json())

    expected = {
        row[0]
        for row in db_connection.execute(
            """
            SELECT aps.id
            FROM appointment_slots aps
            JOIN doctors d ON d.id = aps.doctor_id
            JOIN services s ON s.id = aps.service_id
            WHERE aps.status = 'open'
              AND aps.starts_at > CURRENT_TIMESTAMP
              AND d.is_active
              AND s.is_active
              AND aps.doctor_id = %s
              AND aps.service_id = %s
              AND NOT EXISTS (
                  SELECT 1 FROM appointments a
                  WHERE a.slot_id = aps.id
                    AND a.status = 'scheduled'
              )
            """,
            (DOCTOR_HELENA, SERVICE_CARDIOLOGY),
        )
    }
    assert _slot_ids(first.json()) == {
        str(slot_id) for slot_id in expected
    }


def test_cache_write_failure_still_returns_postgres_payload(
    client: TestClient,
    app: FastAPI,
    redis_client: Redis,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = cast(
        AvailabilityCache,
        app.state.availability_cache,
    )
    assert cache.client is not None

    def failing_set(*args, **kwargs) -> None:
        raise ConnectionError("write failed")

    monkeypatch.setattr(cache.client, "set", failing_set)

    params = {
        "doctor_id": str(DOCTOR_HELENA),
        "service_id": str(SERVICE_CARDIOLOGY),
    }
    response = client.get("/v1/availability", params=params)

    assert response.status_code == 200
    assert str(SLOT_HELENA_CARDIO_AVAILABLE) in _slot_ids(response.json())

    key = build_availability_cache_key(
        service_id=SERVICE_CARDIOLOGY,
        doctor_id=DOCTOR_HELENA,
        target_date=None,
    )
    assert redis_client.exists(key) == 0


def test_invalidation_failure_keeps_successful_booking(
    client: TestClient,
    app: FastAPI,
    redis_client: Redis,
    db_connection: Connection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    business_date = _business_date(
        db_connection,
        SLOT_HELENA_CARDIO_AVAILABLE,
    )
    key = build_availability_cache_key(
        service_id=SERVICE_CARDIOLOGY,
        doctor_id=DOCTOR_HELENA,
        target_date=business_date,
    )

    populated = client.get(
        "/v1/availability",
        params={
            "doctor_id": str(DOCTOR_HELENA),
            "service_id": str(SERVICE_CARDIOLOGY),
            "date": business_date.isoformat(),
        },
    )
    assert populated.status_code == 200
    assert redis_client.exists(key) == 1

    cache = cast(
        AvailabilityCache,
        app.state.availability_cache,
    )
    assert cache.client is not None

    def failing_delete(*args, **kwargs) -> int:
        raise ConnectionError("del failed")

    monkeypatch.setattr(cache.client, "delete", failing_delete)

    booking = client.post(
        "/v1/appointments",
        headers={
            "X-Patient-Id": str(PATIENT_MARIA),
            "Idempotency-Key": "cache-invalidation-failure",
        },
        json={
            "patient_id": str(PATIENT_MARIA),
            "slot_id": str(SLOT_HELENA_CARDIO_AVAILABLE),
        },
    )
    assert booking.status_code == 201
    appointment_id = booking.json()["id"]

    row = db_connection.execute(
        "SELECT status FROM appointments WHERE id = %s",
        (appointment_id,),
    ).fetchone()
    assert row is not None
    assert row[0] == "scheduled"

    detail = client.get(
        f"/v1/appointments/{appointment_id}",
        headers={"X-Patient-Id": str(PATIENT_MARIA)},
    )
    assert detail.status_code == 200
    assert detail.json()["status"] == "scheduled"

    assert redis_client.exists(key) == 1


def test_distinct_queries_use_distinct_cache_keys(
    client: TestClient,
    redis_client: Redis,
    db_connection: Connection,
) -> None:
    day_1 = _business_date(
        db_connection,
        SLOT_HELENA_CARDIO_AVAILABLE,
    )
    day_2 = _business_date(
        db_connection,
        SLOT_HELENA_CARDIO_D2,
    )

    combos = [
        {
            "doctor_id": str(DOCTOR_HELENA),
            "service_id": str(SERVICE_CARDIOLOGY),
            "date": day_1.isoformat(),
        },
        {
            "doctor_id": str(DOCTOR_RAFAEL),
            "service_id": str(SERVICE_CARDIOLOGY),
            "date": day_1.isoformat(),
        },
        {
            "doctor_id": str(DOCTOR_HELENA),
            "service_id": str(SERVICE_CARDIOLOGY),
            "date": day_2.isoformat(),
        },
        {
            "doctor_id": str(DOCTOR_HELENA),
            "service_id": str(SERVICE_DERMATOLOGY),
            "date": day_1.isoformat(),
        },
    ]

    for params in combos:
        response = client.get("/v1/availability", params=params)
        assert response.status_code == 200

    keys = list(
        redis_client.scan_iter(match="availability:*"),
    )
    assert len(keys) == 4
    assert len(set(keys)) == 4


def test_concurrent_booking_with_cached_availability_allows_exactly_one(
    test_database: str,
    availability_cache: AvailabilityCache,
    client: TestClient,
    redis_client: Redis,
    db_connection: Connection,
) -> None:
    from essentia_api.schemas.appointments import CreateAppointmentRequest
    from essentia_api.services.appointments import (
        SlotUnavailableError,
        create_appointment,
    )

    business_date = _business_date(
        db_connection,
        SLOT_HELENA_CARDIO_AVAILABLE,
    )
    key = build_availability_cache_key(
        service_id=SERVICE_CARDIOLOGY,
        doctor_id=DOCTOR_HELENA,
        target_date=business_date,
    )

    cached = client.get(
        "/v1/availability",
        params={
            "doctor_id": str(DOCTOR_HELENA),
            "service_id": str(SERVICE_CARDIOLOGY),
            "date": business_date.isoformat(),
        },
    )
    assert cached.status_code == 200
    assert redis_client.exists(key) == 1

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
                    caller_patient_id=patient_id,
                    cache=availability_cache,
                )
                return "created"
            except SlotUnavailableError:
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                attempt,
                PATIENT_CARLOS,
                "cache-concurrent-1",
            ),
            executor.submit(
                attempt,
                PATIENT_ANA,
                "cache-concurrent-2",
            ),
        ]
        outcomes = [
            future.result(timeout=10) for future in futures
        ]

    assert sorted(outcomes) == ["conflict", "created"]
    assert redis_client.exists(key) == 0


def test_disabled_cache_bypasses_redis_completely(
    test_settings,
    redis_client: Redis,
    availability_query_spy: list[dict],
) -> None:
    disabled_settings = test_settings.model_copy(
        update={"availability_cache_enabled": False},
    )
    disabled_app = create_app(settings=disabled_settings)
    params = {
        "doctor_id": str(DOCTOR_HELENA),
        "service_id": str(SERVICE_CARDIOLOGY),
    }

    with TestClient(disabled_app) as disabled_client:
        first = disabled_client.get("/v1/availability", params=params)
        second = disabled_client.get("/v1/availability", params=params)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert len(availability_query_spy) == 2

    keys = list(
        redis_client.scan_iter(match="availability:*"),
    )
    assert keys == []
