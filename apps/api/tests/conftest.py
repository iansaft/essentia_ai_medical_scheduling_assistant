import os
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import Connection
from psycopg.conninfo import (
    conninfo_to_dict,
    make_conninfo,
)
from redis import Redis
from testcontainers.community.postgres import (
    PostgresContainer,
)
from testcontainers.community.redis import (
    RedisContainer,
)

from essentia_api.cache.availability import (
    AVAILABILITY_CACHE_NAMESPACE,
    AvailabilityCache,
)
from essentia_api.core.config import Settings
from essentia_api.main import create_app
from tests.support.database import (
    apply_up_sql,
    reset_to_seed_state,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIRECTORY = (
    REPOSITORY_ROOT
    / "db"
    / "migrations"
)
SEEDS_DIRECTORY = (
    REPOSITORY_ROOT
    / "db"
    / "seeds"
)

POSTGRES_IMAGE = os.getenv(
    "TEST_POSTGRES_IMAGE",
    "postgres:18.4-alpine",
)
REDIS_IMAGE = os.getenv(
    "TEST_REDIS_IMAGE",
    "redis:8.10.2-alpine3.23",
)

RedisAddress = tuple[str, int]


@pytest.fixture(scope="session")
def test_database() -> Iterator[str]:
    with PostgresContainer(
        POSTGRES_IMAGE,
        driver=None,
    ) as postgres:
        host = postgres.get_container_host_ip()
        port = int(
            postgres.get_exposed_port(5432)
        )

        conninfo = make_conninfo(
            host=host,
            port=port,
            dbname=postgres.dbname,
            user=postgres.username,
            password=postgres.password,
            sslmode="disable",
        )

        with psycopg.connect(
            conninfo,
            autocommit=True,
        ) as connection:
            apply_up_sql(
                connection,
                MIGRATIONS_DIRECTORY,
            )

        yield conninfo


@pytest.fixture(scope="session")
def test_redis() -> Iterator[RedisAddress]:
    with RedisContainer(
        REDIS_IMAGE,
    ) as redis:
        host = redis.get_container_host_ip()
        port = int(
            redis.get_exposed_port(6379)
        )

        yield host, port


def build_redis_client(
    test_redis: RedisAddress,
) -> Redis:
    host, port = test_redis

    return Redis(
        host=host,
        port=port,
        decode_responses=True,
        socket_timeout=2.0,
        socket_connect_timeout=2.0,
    )


def delete_availability_cache_keys(
    client: Redis,
) -> None:
    for key in client.scan_iter(
        match=f"{AVAILABILITY_CACHE_NAMESPACE}:*",
        count=100,
    ):
        client.delete(key)


@pytest.fixture(autouse=True)
def reset_database(
    test_database: str,
) -> Iterator[None]:
    with psycopg.connect(
        test_database,
        autocommit=True,
    ) as connection:
        reset_to_seed_state(
            connection,
            SEEDS_DIRECTORY,
        )

    yield


@pytest.fixture(autouse=True)
def reset_availability_cache(
    test_redis: RedisAddress,
) -> Iterator[None]:
    client = build_redis_client(test_redis)

    try:
        delete_availability_cache_keys(client)
        yield
    finally:
        client.close()


@pytest.fixture
def redis_client(
    test_redis: RedisAddress,
) -> Iterator[Redis]:
    client = build_redis_client(test_redis)

    try:
        yield client
    finally:
        client.close()


@pytest.fixture(scope="session")
def test_settings(
    test_database: str,
    test_redis: RedisAddress,
) -> Settings:
    database = conninfo_to_dict(
        test_database,
    )
    redis_host, redis_port = test_redis

    return Settings(
        app_env="test",
        db_host=database["host"],
        db_port=int(database["port"]),
        db_name=database["dbname"],
        db_user=database["user"],
        db_password=database["password"],
        db_ssl_mode=database.get(
            "sslmode",
            "disable",
        ),
        db_pool_min_size=1,
        db_pool_max_size=10,
        db_pool_timeout=5.0,
        redis_host=redis_host,
        redis_port=redis_port,
        redis_password=None,
        redis_db=0,
        redis_socket_timeout=2.0,
        redis_connect_timeout=2.0,
        availability_cache_enabled=True,
        availability_cache_ttl_seconds=30,
        availability_cache_ttl_jitter_seconds=10,
        business_timezone="America/Sao_Paulo",
        log_level="WARNING",
        log_json=False,
    )


@pytest.fixture(scope="session")
def app(
    test_settings: Settings,
) -> FastAPI:
    return create_app(
        settings=test_settings,
    )


@pytest.fixture(scope="session")
def client(
    app: FastAPI,
) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def availability_cache(
    app: FastAPI,
) -> AvailabilityCache:
    return cast(
        AvailabilityCache,
        app.state.availability_cache,
    )


@pytest.fixture
def db_connection(
    test_database: str,
) -> Iterator[Connection]:
    with psycopg.connect(
        test_database,
        autocommit=True,
    ) as connection:
        yield connection
