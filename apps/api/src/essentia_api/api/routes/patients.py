from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from psycopg import Connection, errors

from essentia_api.api.dependencies import PatientIdentity, get_db_connection
from essentia_api.core.errors import (
    ForbiddenError,
    PatientEmailAlreadyExistsError,
    PatientNotFoundError,
    PatientPhoneAlreadyExistsError,
)
from essentia_api.db.generated import appointments as appointment_queries
from essentia_api.db.generated import patients as patient_queries
from essentia_api.schemas.appointments import AppointmentResponse
from essentia_api.schemas.patients import (
    CreatePatientRequest,
    PatientResponse,
)

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)

DatabaseConnection = Annotated[
    Connection,
    Depends(get_db_connection),
]


def _ensure_patient_access(
    path_patient_id: UUID,
    caller_patient_id: UUID,
) -> None:
    if path_patient_id != caller_patient_id:
        raise ForbiddenError("Patient access denied.")


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create patient",
    description=(
        "Registers a new patient. Open endpoint — no identity header"
        " required. Duplicate email (case-insensitive) or phone"
        " returns 409."
    ),
)
def create_patient(
    command: CreatePatientRequest,
    connection: DatabaseConnection,
) -> PatientResponse:
    existing = patient_queries.get_patient_by_email(
        connection,
        email=command.email,
    )
    if existing is not None:
        raise PatientEmailAlreadyExistsError(
            "Patient email already exists.",
        )

    try:
        with connection.transaction():
            patient = patient_queries.create_patient(
                connection,
                full_name=command.full_name,
                email=command.email,
                phone=command.phone,
            )
    except errors.UniqueViolation:
        existing = patient_queries.get_patient_by_email(
            connection,
            email=command.email,
        )
        if existing is not None:
            raise PatientEmailAlreadyExistsError(
                "Patient email already exists.",
            ) from None
        raise PatientPhoneAlreadyExistsError(
            "Patient phone already exists.",
        ) from None

    if patient is None:
        raise RuntimeError("Created patient could not be loaded.")

    return PatientResponse.model_validate(patient)


@router.get(
    "",
    response_model=list[PatientResponse],
    status_code=status.HTTP_200_OK,
    summary="List patients",
)
def list_patients(
    connection: DatabaseConnection,
) -> list[PatientResponse]:
    patients = patient_queries.list_patients(connection)

    return [
        PatientResponse.model_validate(patient)
        for patient in patients
    ]


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    status_code=status.HTTP_200_OK,
    summary="Get patient by ID",
)
def get_patient(
    patient_id: Annotated[
        UUID,
        Path(
            description="Unique patient identifier.",
            examples=[
                "3cdf666b-186d-44e6-bce9-5e572e7038f9",
            ],
        ),
    ],
    caller_patient_id: PatientIdentity,
    connection: DatabaseConnection,
) -> PatientResponse:
    _ensure_patient_access(patient_id, caller_patient_id)

    patient = patient_queries.get_patient_by_id(
        connection,
        id_=patient_id,
    )

    if patient is None:
        raise PatientNotFoundError("Patient not found.")

    return PatientResponse.model_validate(patient)


@router.get(
    "/{patient_id}/appointments",
    response_model=list[AppointmentResponse],
    status_code=status.HTTP_200_OK,
    summary="List patient appointments",
)
def list_patient_appointments(
    patient_id: Annotated[
        UUID,
        Path(
            description="Unique patient identifier.",
            examples=[
                "3cdf666b-186d-44e6-bce9-5e572e7038f9",
            ],
        ),
    ],
    caller_patient_id: PatientIdentity,
    connection: DatabaseConnection,
) -> list[AppointmentResponse]:
    _ensure_patient_access(patient_id, caller_patient_id)

    patient = patient_queries.get_patient_by_id(
        connection,
        id_=patient_id,
    )

    if patient is None:
        raise PatientNotFoundError("Patient not found.")

    appointments = appointment_queries.list_appointments_by_patient_id(
        connection,
        patient_id=patient_id,
    )

    return [
        AppointmentResponse.model_validate(appointment)
        for appointment in appointments
    ]
