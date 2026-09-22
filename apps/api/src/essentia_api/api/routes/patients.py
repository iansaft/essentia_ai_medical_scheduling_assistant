from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from psycopg import Connection

from essentia_api.api.dependencies import get_db_connection
from essentia_api.db.generated import patients as patient_queries
from essentia_api.schemas.patients import PatientResponse


router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)

DatabaseConnection = Annotated[
    Connection,
    Depends(get_db_connection),
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
    connection: DatabaseConnection,
) -> PatientResponse:
    patient = patient_queries.get_patient_by_id(
        connection,
        id_=patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    return PatientResponse.model_validate(patient)