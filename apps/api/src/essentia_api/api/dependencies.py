from collections.abc import Iterator
from typing import cast

from fastapi import Request
from psycopg import Connection
from psycopg_pool import ConnectionPool


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
