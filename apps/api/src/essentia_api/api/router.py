from fastapi import APIRouter

from essentia_api.api.routes import (
    appointments,
    availability,
    patients,
    services,
)


api_router = APIRouter(
    prefix="/v1",
)

api_router.include_router(patients.router)
api_router.include_router(services.router)
api_router.include_router(availability.router)
api_router.include_router(appointments.router)