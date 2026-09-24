from collections.abc import Iterator
from typing import Annotated, cast
from uuid import UUID

from fastapi import Depends, Header, Request
from psycopg import Connection
from psycopg_pool import ConnectionPool

from essentia_api.cache.availability import AvailabilityCache


def get_patient_identity(
    x_patient_id: Annotated[
        UUID,
        Header(
            alias="X-Patient-Id",
            description=(
                "Identifier of the patient on whose behalf the request "
                "is made. Must match the patient that owns the target "
                "resource."
            ),
            examples=["3cdf666b-186d-44e6-bce9-5e572e7038f9"],
        ),
    ],
) -> UUID:
    """
    Resolve the patient identity asserted by the caller via the
    ``X-Patient-Id`` header.
    """
    return x_patient_id


PatientIdentity = Annotated[
    UUID,
    Depends(get_patient_identity),
]


def get_db_pool(
    request: Request,
) -> ConnectionPool:
    """
    Resolve the database pool owned by the current FastAPI application.
    """
    pool = getattr(
        request.app.state,
        "db_pool",
        None,
    )

    if pool is None:
        raise RuntimeError(
            "Database pool is not initialized."
        )

    return cast(
        ConnectionPool,
        pool,
    )


def get_db_connection(
    request: Request,
) -> Iterator[Connection]:
    pool = get_db_pool(request)

    with pool.connection() as connection:
        yield connection


def get_availability_cache(
    request: Request,
) -> AvailabilityCache:
    """
    Resolve the availability cache owned by the current FastAPI
    application instance.
    """
    cache = getattr(
        request.app.state,
        "availability_cache",
        None,
    )

    if cache is None:
        raise RuntimeError(
            "Availability cache is not initialized."
        )

    return cast(
        AvailabilityCache,
        cache,
    )


AvailabilityCacheDependency = Annotated[
    AvailabilityCache,
    Depends(get_availability_cache),
]
