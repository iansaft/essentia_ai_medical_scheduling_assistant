from datetime import date
from uuid import UUID

from psycopg import Connection

from essentia_api.cache.availability import AvailabilityCache
from essentia_api.db.generated import availability as availability_queries
from essentia_api.schemas.availability import AvailableSlotResponse

__all__ = [
    "list_availability",
]


def list_availability(
    connection: Connection,
    *,
    cache: AvailabilityCache,
    doctor_id: UUID | None,
    service_id: UUID | None,
    target_date: date | None,
) -> list[AvailableSlotResponse]:
    """
    Resolve available slots through Cache-Aside.

    A cache hit returns the stored result without querying PostgreSQL.
    A cache miss consults PostgreSQL (the authoritative source), stores
    the outcome — including an empty list — and returns it. Redis being
    unavailable never prevents the PostgreSQL fallback from answering.
    """
    cached_slots = cache.get(
        service_id=service_id,
        doctor_id=doctor_id,
        target_date=target_date,
    )
    if cached_slots is not None:
        return cached_slots

    slots = [
        AvailableSlotResponse.model_validate(
            slot,
        )
        for slot in availability_queries.list_available_slots(
            connection,
            doctor_id=doctor_id,
            service_id=service_id,
            target_date=target_date,
        )
    ]

    cache.set(
        service_id=service_id,
        doctor_id=doctor_id,
        target_date=target_date,
        slots=slots,
    )

    return slots
