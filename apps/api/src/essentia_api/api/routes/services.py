from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from psycopg import Connection

from essentia_api.api.dependencies import get_db_connection
from essentia_api.core.errors import ServiceNotFoundError
from essentia_api.db.generated import payment_methods as payment_method_queries
from essentia_api.db.generated import services as service_queries
from essentia_api.schemas.catalog import (
    PaymentMethodResponse,
    ServiceResponse,
)

router = APIRouter(
    prefix="/services",
    tags=["Services"],
)

DatabaseConnection = Annotated[
    Connection,
    Depends(get_db_connection),
]


@router.get(
    "",
    response_model=list[ServiceResponse],
    status_code=status.HTTP_200_OK,
)
def list_services(
    connection: DatabaseConnection,
) -> list[ServiceResponse]:
    services = service_queries.list_active_services(connection)

    return [
        ServiceResponse.model_validate(service)
        for service in services
    ]


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    status_code=status.HTTP_200_OK,
)
def get_service(
    service_id: Annotated[
        UUID,
        Path(
            description="Unique medical service identifier.",
            examples=[
                "e2fb5edd-efbd-4d60-9de3-d6650e31562f",
            ],
        ),
    ],
    connection: DatabaseConnection,
) -> ServiceResponse:
    service = service_queries.get_active_service_by_id(
        connection,
        id_=service_id,
    )

    if service is None:
        raise ServiceNotFoundError("Service not found.")

    return ServiceResponse.model_validate(service)


@router.get(
    "/{service_id}/payment-methods",
    response_model=list[PaymentMethodResponse],
    status_code=status.HTTP_200_OK,
)
def list_service_payment_methods(
    service_id: Annotated[
        UUID,
        Path(
            description="Unique medical service identifier.",
            examples=[
                "e2fb5edd-efbd-4d60-9de3-d6650e31562f",
            ],
        ),
    ],
    connection: DatabaseConnection,
) -> list[PaymentMethodResponse]:
    service = service_queries.get_active_service_by_id(
        connection,
        id_=service_id,
    )

    if service is None:
        raise ServiceNotFoundError("Service not found.")

    payment_methods = (
        payment_method_queries.list_payment_methods_by_service_id(
            connection,
            service_id=service_id,
        )
    )

    return [
        PaymentMethodResponse.model_validate(payment_method)
        for payment_method in payment_methods
    ]