from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    Path,
    status,
)
from psycopg import Connection

from essentia_api.api.dependencies import (
    AvailabilityCacheDependency,
    PatientIdentity,
    get_db_connection,
)
from essentia_api.schemas.appointments import (
    AppointmentResponse,
    CancelAppointmentRequest,
    CreateAppointmentRequest,
)
from essentia_api.services import appointments as appointment_service

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"],
)

DatabaseConnection = Annotated[
    Connection,
    Depends(get_db_connection),
]

IdempotencyKey = Annotated[
    str,
    Header(
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
        description=(
            "Unique key used to safely retry mutating requests "
            "without duplicating their effects."
        ),
        examples=["7ff768c5-8f88-4554-8ae6-afcf3b6f1e01"],
    ),
]


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get appointment by ID",
)
def get_appointment(
    appointment_id: Annotated[
        UUID,
        Path(
            description="Unique appointment identifier.",
            examples=[
                "8029d8d3-8fff-4dcc-a2ef-2ae0808bf95e",
            ],
        ),
    ],
    caller_patient_id: PatientIdentity,
    connection: DatabaseConnection,
) -> AppointmentResponse:
    return appointment_service.get_appointment(
        connection,
        appointment_id=appointment_id,
        caller_patient_id=caller_patient_id,
    )


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create appointment",
    description=(
        "Creates a scheduled appointment for an available slot. "
        "Price and currency are derived by the server from the service "
        "associated with the selected slot."
    ),
)
def create_appointment(
    command: CreateAppointmentRequest,
    idempotency_key: IdempotencyKey,
    caller_patient_id: PatientIdentity,
    connection: DatabaseConnection,
    cache: AvailabilityCacheDependency,
) -> AppointmentResponse:
    return appointment_service.create_appointment(
        connection,
        command=command,
        idempotency_key=idempotency_key,
        caller_patient_id=caller_patient_id,
        cache=cache,
    )


@router.post(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel appointment",
)
def cancel_appointment(
    appointment_id: Annotated[
        UUID,
        Path(
            description="Unique appointment identifier.",
            examples=[
                "8029d8d3-8fff-4dcc-a2ef-2ae0808bf95e",
            ],
        ),
    ],
    command: CancelAppointmentRequest,
    idempotency_key: IdempotencyKey,
    caller_patient_id: PatientIdentity,
    connection: DatabaseConnection,
    cache: AvailabilityCacheDependency,
) -> AppointmentResponse:
    return appointment_service.cancel_appointment(
        connection,
        appointment_id=appointment_id,
        command=command,
        idempotency_key=idempotency_key,
        caller_patient_id=caller_patient_id,
        cache=cache,
    )
