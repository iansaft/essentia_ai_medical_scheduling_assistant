from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from psycopg import Connection

from essentia_api.api.dependencies import get_db_connection
from essentia_api.db.generated import availability as availability_queries
from essentia_api.schemas.availability import AvailableSlotResponse


router = APIRouter(
    prefix="/availability",
    tags=["Availability"],
)

DatabaseConnection = Annotated[
    Connection,
    Depends(get_db_connection),
]


@router.get(
    "",
    response_model=list[AvailableSlotResponse],
    status_code=status.HTTP_200_OK,
    summary="List available appointment slots",
)
def list_availability(
    connection: DatabaseConnection,

    doctor_id: Annotated[
        UUID | None,
        Query(
            description="Filter slots by doctor.",
            example="0dfc6223-6a11-4d90-a979-bd511bc1d6a9",
            examples=[
                "0dfc6223-6a11-4d90-a979-bd511bc1d6a9",
            ],
        ),
    ] = None,

    service_id: Annotated[
        UUID | None,
        Query(
            description="Filter slots by medical service.",
            example="e2fb5edd-efbd-4d60-9de3-d6650e31562f",
            examples=[
                "e2fb5edd-efbd-4d60-9de3-d6650e31562f",
            ],
        ),
    ] = None,

    target_date: Annotated[
        date | None,
        Query(
            alias="date",
            description=(
                "Filter slots by business date "
                "in America/Sao_Paulo timezone."
            ),
            example="2027-04-12",
            examples=["2027-04-12"],
        ),
    ] = None,
) -> list[AvailableSlotResponse]:
    slots = availability_queries.list_available_slots(
        connection,
        doctor_id=doctor_id,
        service_id=service_id,
        target_date=target_date,
    )

    return [
        AvailableSlotResponse.model_validate(slot)
        for slot in slots
    ]