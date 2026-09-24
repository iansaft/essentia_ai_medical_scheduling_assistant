from uuid import uuid4

import pytest
from psycopg import Connection, errors

from tests.support.constants import (
    DOCTOR_HELENA,
    PATIENT_CARLOS,
    SERVICE_CARDIOLOGY,
    SERVICE_DERMATOLOGY,
    SLOT_HELENA_CARDIO_AVAILABLE,
)

pytestmark = pytest.mark.integration


def test_database_rejects_overlapping_slots_for_same_doctor(
    db_connection: Connection,
) -> None:
    starts_at, ends_at = db_connection.execute(
        "SELECT starts_at, ends_at FROM appointment_slots WHERE id = %s",
        (SLOT_HELENA_CARDIO_AVAILABLE,),
    ).fetchone()

    with pytest.raises(errors.ExclusionViolation):
        db_connection.execute(
            """
            INSERT INTO appointment_slots (
                id, doctor_id, service_id, starts_at, ends_at, status
            )
            VALUES (%s, %s, %s, %s, %s, 'open')
            """,
            (
                uuid4(),
                DOCTOR_HELENA,
                SERVICE_CARDIOLOGY,
                starts_at,
                ends_at,
            ),
        )


def test_database_rejects_slot_for_service_not_offered_by_doctor(
    db_connection: Connection,
) -> None:
    with pytest.raises(errors.ForeignKeyViolation):
        db_connection.execute(
            """
            INSERT INTO appointment_slots (
                id, doctor_id, service_id, starts_at, ends_at, status
            )
            VALUES (
                %s, %s, %s,
                CURRENT_TIMESTAMP + INTERVAL '20 days',
                CURRENT_TIMESTAMP + INTERVAL '20 days' + INTERVAL '30 minutes',
                'open'
            )
            """,
            (uuid4(), DOCTOR_HELENA, SERVICE_DERMATOLOGY),
        )


def test_database_rejects_second_scheduled_appointment_for_same_slot(
    db_connection: Connection,
) -> None:
    db_connection.execute(
        """
        INSERT INTO appointments (
            id, patient_id, slot_id, status, price_amount, currency
        )
        VALUES (%s, %s, %s, 'scheduled', 320.00, 'BRL')
        """,
        (uuid4(), PATIENT_CARLOS, SLOT_HELENA_CARDIO_AVAILABLE),
    )

    with pytest.raises(errors.UniqueViolation):
        db_connection.execute(
            """
            INSERT INTO appointments (
                id, patient_id, slot_id, status, price_amount, currency
            )
            VALUES (%s, %s, %s, 'scheduled', 320.00, 'BRL')
            """,
            (uuid4(), PATIENT_CARLOS, SLOT_HELENA_CARDIO_AVAILABLE),
        )
