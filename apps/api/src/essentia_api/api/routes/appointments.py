from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Path,
    status,
)
from psycopg import Connection

from essentia_api.api.dependencies import get_db_connection
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


def _translate_domain_error(error: Exception) -> HTTPException:
    if isinstance(
        error,
        (
            appointment_service.AppointmentNotFoundError,
            appointment_service.PatientNotFoundError,
            appointment_service.SlotNotFoundError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )

    if isinstance(
        error,
        (
            appointment_service.PatientInactiveError,
            appointment_service.SlotUnavailableError,
            appointment_service.DoctorInactiveError,
            appointment_service.ServiceInactiveError,
            appointment_service.AppointmentNotCancellableError,
            appointment_service.IdempotencyConflictError,
            appointment_service.IdempotencyInProgressError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

    if isinstance(error, appointment_service.IdempotencyStateError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid idempotency state.",
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unexpected appointment operation error.",
    )


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
    connection: DatabaseConnection,
) -> AppointmentResponse:
    try:
        return appointment_service.get_appointment(
            connection,
            appointment_id=appointment_id,
        )
    except appointment_service.AppointmentNotFoundError as error:
        raise _translate_domain_error(error) from error


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
    connection: DatabaseConnection,
) -> AppointmentResponse:
    try:
        return appointment_service.create_appointment(
            connection,
            command=command,
            idempotency_key=idempotency_key,
        )
    except (
        appointment_service.PatientNotFoundError,
        appointment_service.PatientInactiveError,
        appointment_service.SlotNotFoundError,
        appointment_service.SlotUnavailableError,
        appointment_service.DoctorInactiveError,
        appointment_service.ServiceInactiveError,
        appointment_service.IdempotencyConflictError,
        appointment_service.IdempotencyInProgressError,
        appointment_service.IdempotencyStateError,
    ) as error:
        raise _translate_domain_error(error) from error


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
    connection: DatabaseConnection,
) -> AppointmentResponse:
    try:
        return appointment_service.cancel_appointment(
            connection,
            appointment_id=appointment_id,
            command=command,
            idempotency_key=idempotency_key,
        )
    except (
        appointment_service.AppointmentNotFoundError,
        appointment_service.AppointmentNotCancellableError,
        appointment_service.IdempotencyConflictError,
        appointment_service.IdempotencyInProgressError,
        appointment_service.IdempotencyStateError,
    ) as error:
        raise _translate_domain_error(error) from error
