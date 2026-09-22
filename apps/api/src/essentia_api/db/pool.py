from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool

from essentia_api.core.config import Settings


def create_connection_pool(
    settings: Settings,
) -> ConnectionPool:
    """
    Create a closed PostgreSQL connection pool for one application instance.

    Pool lifecycle is owned by FastAPI's lifespan handler.
    """
    conninfo = make_conninfo(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        sslmode=settings.db_ssl_mode,
    )

    return ConnectionPool(
        conninfo=conninfo,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        timeout=settings.db_pool_timeout,
        open=False,
        check=ConnectionPool.check_connection,
        name="essentia-api-pool",
    )
