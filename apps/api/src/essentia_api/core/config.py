from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(
        default="development",
        validation_alias=AliasChoices(
            "APP_ENV",
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
