from redis import Redis

from essentia_api.core.config import Settings


def create_redis_client(
    settings: Settings,
) -> Redis | None:
    """
    Create a Redis client for one application instance, or ``None`` when the
    availability cache is disabled.

    Client lifecycle is owned by FastAPI's lifespan handler. Connections are
    pooled and reused by the client; no connection is opened until the first
    command is issued, so a missing Redis never blocks application startup.
    """
    if not settings.availability_cache_enabled:
        return None

    return Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password or None,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_connect_timeout,
        decode_responses=True,
    )
