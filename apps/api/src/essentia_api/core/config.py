import json
from typing import Annotated

from pydantic import (
    AliasChoices,
    Field,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    NoDecode,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    app_env: str = Field(
        default="development",
        validation_alias=AliasChoices(
            "API_ENV",
            "NODE_ENV",
        ),
    )

    db_host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices(
            "API_DB_HOST",
        ),
    )
    db_port: int = Field(
        default=5432,
        validation_alias=AliasChoices(
            "API_DB_PORT",
        ),
    )
    db_name: str = Field(
        default="postgres",
        validation_alias=AliasChoices(
            "API_DB_NAME",
        ),
    )
    db_user: str = Field(
        validation_alias=AliasChoices(
            "API_DB_USER",
        ),
    )
    db_password: str = Field(
        validation_alias=AliasChoices(
            "API_DB_PW",
        ),
    )
    db_ssl_mode: str = Field(
        default="disable",
        validation_alias=AliasChoices(
            "API_DB_SSL_MODE",
        ),
    )

    db_pool_min_size: int = 1
    db_pool_max_size: int = 10
    db_pool_timeout: float = 5.0

    business_timezone: str = "America/Sao_Paulo"

    n8n_base_url: str = Field(
        default="http://localhost:5678",
        validation_alias=AliasChoices(
            "API_N8N_BASE_URL",
        ),
    )

    cors_origins: Annotated[
        list[str],
        NoDecode,
    ] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:4173",
            "http://localhost:8080",
        ],
        validation_alias=AliasChoices(
            "API_CORS_ORIGINS",
        ),
    )

    @field_validator(
        "cors_origins",
        mode="before",
    )
    @classmethod
    def parse_cors_origins(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            text = value.strip()

            if text.startswith("["):
                return json.loads(text)

            return [
                origin.strip()
                for origin in text.split(",")
                if origin.strip()
            ]

        return value

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )


def load_settings() -> Settings:
    """
    Build a fresh settings object from the current process environment.

    Configuration is intentionally not cached. Each FastAPI application
    instance owns the Settings object used to create its infrastructure.
    """
    return Settings()
