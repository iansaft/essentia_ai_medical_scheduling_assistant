import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import Connection
from psycopg.conninfo import (
    conninfo_to_dict,
    make_conninfo,
)
from testcontainers.community.postgres import (
    PostgresContainer,
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


@pytest.fixture(scope="session")
def test_settings(
    test_database: str,
) -> Settings:
    database = conninfo_to_dict(
        test_database,
    )

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
        business_timezone="America/Sao_Paulo",
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
def db_connection(
    test_database: str,
) -> Iterator[Connection]:
    with psycopg.connect(
        test_database,
        autocommit=True,
    ) as connection:
        yield connection
