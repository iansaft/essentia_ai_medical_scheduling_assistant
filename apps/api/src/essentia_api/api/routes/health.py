from typing import cast
from urllib.error import URLError
from urllib.request import Request, urlopen

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from fastapi import Request as FastAPIRequest

from essentia_api.core.config import Settings

N8N_READINESS_TIMEOUT_SECONDS = 2.0


router = APIRouter(
    tags=["Health"],
)


def get_settings(
    request: FastAPIRequest,
) -> Settings:
    settings = getattr(
        request.app.state,
        "settings",
        None,
    )

    if settings is None:
        raise RuntimeError(
            "Application settings are not initialized."
        )

    return cast(
        Settings,
        settings,
    )


def probe_n8n_readiness(
    base_url: str,
) -> bool:
    probe_url = f"{base_url.rstrip('/')}/healthz/readiness"
    request = Request(
        probe_url,
        method="GET",
        headers={
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(
            request,
            timeout=N8N_READINESS_TIMEOUT_SECONDS,
        ) as response:
            return 200 <= response.status < 300
    except (URLError, TimeoutError, OSError, ValueError):
        return False


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
)
def get_health() -> dict[str, str]:
    return {
        "status": "ok",
    }


@router.get(
    "/health/n8n",
    status_code=status.HTTP_200_OK,
)
def get_n8n_health(
    request: FastAPIRequest,
) -> dict[str, str]:
    settings = get_settings(request)

    if not probe_n8n_readiness(
        settings.n8n_base_url,
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
            },
        )

    return {
        "status": "ok",
    }
