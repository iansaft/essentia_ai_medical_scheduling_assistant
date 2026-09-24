from __future__ import annotations

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

PROBLEM_MEDIA_TYPE = "application/problem+json"


class AppError(Exception):
    """Base for errors rendered as RFC 7807 problem+json responses."""

    status_code: int = 500
    title: str = "Internal Server Error"
    problem_type: str = "/problems/internal-error"

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(AppError):
    status_code = 404
    title = "Not Found"
    problem_type = "/problems/not-found"


class ForbiddenError(AppError):
    status_code = 403
    title = "Forbidden"
    problem_type = "/problems/forbidden"


class ConflictError(AppError):
    status_code = 409
    title = "Conflict"
    problem_type = "/problems/conflict"


class InternalError(AppError):
    status_code = 500
    title = "Internal Server Error"
    problem_type = "/problems/internal-error"


class AppointmentNotFoundError(NotFoundError):
    problem_type = "/problems/appointment-not-found"


class PatientNotFoundError(NotFoundError):
    problem_type = "/problems/patient-not-found"


class ServiceNotFoundError(NotFoundError):
    problem_type = "/problems/service-not-found"


class SlotNotFoundError(NotFoundError):
    problem_type = "/problems/slot-not-found"


class PatientAccessDeniedError(ForbiddenError):
    problem_type = "/problems/patient-access-denied"


class PatientInactiveError(ConflictError):
    problem_type = "/problems/patient-inactive"


class SlotUnavailableError(ConflictError):
    problem_type = "/problems/slot-unavailable"


class DoctorInactiveError(ConflictError):
    problem_type = "/problems/doctor-inactive"


class ServiceInactiveError(ConflictError):
    problem_type = "/problems/service-inactive"


class AppointmentNotCancellableError(ConflictError):
    problem_type = "/problems/appointment-not-cancellable"


class IdempotencyConflictError(ConflictError):
    problem_type = "/problems/idempotency-conflict"


class IdempotencyInProgressError(ConflictError):
    problem_type = "/problems/idempotency-in-progress"


class IdempotencyStateError(InternalError):
    problem_type = "/problems/idempotency-state"


def problem_body(
    error: AppError,
    *,
    instance: str,
) -> dict[str, Any]:
    return {
        "type": error.problem_type,
        "title": error.title,
        "status": error.status_code,
        "detail": error.detail,
        "instance": instance,
    }


def _problem_response(
    *,
    status_code: int,
    problem_type: str,
    title: str,
    detail: str,
    instance: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "type": problem_type,
            "title": title,
            "status": status_code,
            "detail": detail,
            "instance": instance,
        },
        media_type=PROBLEM_MEDIA_TYPE,
    )


def register_exception_handlers(app: FastAPI) -> None:
    logger = structlog.get_logger("essentia_api.errors")

    @app.exception_handler(AppError)
    async def app_error_handler(
        request: Request,
        exc: AppError,
    ) -> JSONResponse:
        instance = str(request.url.path)
        log = logger.bind(
            status=exc.status_code,
            error_type=type(exc).__name__,
            path=instance,
            method=request.method,
        )
        if exc.status_code >= 500:
            log.error("application_error", detail=exc.detail)
        else:
            log.warning("application_error", detail=exc.detail)

        return JSONResponse(
            status_code=exc.status_code,
            content=problem_body(exc, instance=instance),
            media_type=PROBLEM_MEDIA_TYPE,
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        instance = str(request.url.path)
        logger.exception(
            "unhandled_error",
            error_type=type(exc).__name__,
            path=instance,
            method=request.method,
        )

        return _problem_response(
            status_code=500,
            problem_type="/problems/internal-error",
            title="Internal Server Error",
            detail="An unexpected error occurred.",
            instance=instance,
        )
