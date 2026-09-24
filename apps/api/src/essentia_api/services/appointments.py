import hashlib
import json
from typing import Any
from uuid import UUID

from psycopg import Connection
from psycopg.types.json import Jsonb

from essentia_api.cache.availability import AvailabilityCache
from essentia_api.core.errors import (
    AppointmentNotCancellableError,
    AppointmentNotFoundError,
    DoctorInactiveError,
    IdempotencyConflictError,
    IdempotencyInProgressError,
    IdempotencyStateError,
    PatientAccessDeniedError,
    PatientInactiveError,
    PatientNotFoundError,
    ServiceInactiveError,
    SlotNotFoundError,
    SlotUnavailableError,
)
from essentia_api.db.generated import appointments as appointment_queries
from essentia_api.db.generated import idempotency as idempotency_queries
from essentia_api.schemas.appointments import (
    AppointmentResponse,
    CancelAppointmentRequest,
    CreateAppointmentRequest,
)

CREATE_APPOINTMENT_OPERATION = "create_appointment"
CANCEL_APPOINTMENT_OPERATION = "cancel_appointment"

__all__ = [
    "CANCEL_APPOINTMENT_OPERATION",
    "CREATE_APPOINTMENT_OPERATION",
    "AppointmentNotCancellableError",
    "AppointmentNotFoundError",
    "DoctorInactiveError",
    "IdempotencyConflictError",
    "IdempotencyInProgressError",
    "IdempotencyStateError",
    "PatientAccessDeniedError",
    "PatientInactiveError",
    "PatientNotFoundError",
    "ServiceInactiveError",
    "SlotNotFoundError",
    "SlotUnavailableError",
    "cancel_appointment",
    "create_appointment",
    "get_appointment",
]


def _request_hash(*, operation: str, payload: dict[str, Any]) -> str:
    canonical_payload = json.dumps(
        {"operation": operation, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _load_replayed_response(
    connection: Connection,
    *,
    operation: str,
    idempotency_key: str,
    request_hash: str,
) -> AppointmentResponse | None:
    idempotency_queries.delete_expired_idempotency_request(
        connection,
        operation=operation,
        idempotency_key=idempotency_key,
    )

    created_request_id = idempotency_queries.try_create_idempotency_request(
        connection,
        idempotency_key=idempotency_key,
        operation=operation,
        request_hash=request_hash,
    )

    if created_request_id is not None:
        return None

    existing = idempotency_queries.get_idempotency_request(
        connection,
        operation=operation,
        idempotency_key=idempotency_key,
    )

    if existing is None:
        raise IdempotencyStateError(
            "Idempotency request could not be resolved."
        )

    if existing.request_hash != request_hash:
        raise IdempotencyConflictError(
            "The Idempotency-Key was already used with a different request."
        )

    if existing.state == "processing":
        raise IdempotencyInProgressError(
            "A request with this Idempotency-Key is already being processed."
        )

    if existing.state != "completed" or existing.response_body is None:
        raise IdempotencyStateError(
            "The stored idempotency request is in an invalid state."
        )

    return _validate_replayed_response(existing.response_body)


def _validate_replayed_response(
    response_body: object,
) -> AppointmentResponse:
    if isinstance(response_body, str):
        return AppointmentResponse.model_validate_json(
            response_body
        )

    return AppointmentResponse.model_validate(
        response_body
    )

def _complete_idempotency_request(
    connection: Connection,
    *,
    operation: str,
    idempotency_key: str,
    request_hash: str,
    resource_id: UUID,
    response_status: int,
    response: AppointmentResponse,
) -> None:
    response_body = response.model_dump(mode="json")

    idempotency_queries.complete_idempotency_request(
        connection,
        operation=operation,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        resource_id=resource_id,
        response_status=response_status,
        response_body=Jsonb(response_body),
    )


def get_appointment(
    connection: Connection,
    *,
    appointment_id: UUID,
    caller_patient_id: UUID,
) -> AppointmentResponse:
    appointment = appointment_queries.get_appointment_by_id(
        connection,
        appointment_id=appointment_id,
    )

    if appointment is None:
        raise AppointmentNotFoundError("Appointment not found.")

    if appointment.patient_id != caller_patient_id:
        raise PatientAccessDeniedError("Patient access denied.")

    return _validate_replayed_response(appointment)


def create_appointment(
    connection: Connection,
    *,
    command: CreateAppointmentRequest,
    idempotency_key: str,
    caller_patient_id: UUID,
    cache: AvailabilityCache,
) -> AppointmentResponse:
    if command.patient_id != caller_patient_id:
        raise PatientAccessDeniedError("Patient access denied.")

    request_hash = _request_hash(
        operation=CREATE_APPOINTMENT_OPERATION,
        payload={
            "patient_id": str(command.patient_id),
            "slot_id": str(command.slot_id),
        },
    )

    with connection.transaction():
        replayed_response = _load_replayed_response(
            connection,
            operation=CREATE_APPOINTMENT_OPERATION,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replayed_response is not None:
            return replayed_response

        patient = appointment_queries.get_patient_for_booking(
            connection,
            patient_id=command.patient_id,
        )
        if patient is None:
            raise PatientNotFoundError("Patient not found.")
        if not patient.is_active:
            raise PatientInactiveError(
                "Inactive patients cannot book appointments."
            )

        slot = appointment_queries.get_slot_for_booking(
            connection,
            slot_id=command.slot_id,
        )
        if slot is None:
            raise SlotNotFoundError("Appointment slot not found.")
        if slot.status != "open":
            raise SlotUnavailableError("Appointment slot is not open.")
        if not slot.is_future:
            raise SlotUnavailableError(
                "Past appointment slots cannot be booked."
            )
        if not slot.doctor_is_active:
            raise DoctorInactiveError(
                "The doctor assigned to this slot is inactive."
            )
        if not slot.service_is_active:
            raise ServiceInactiveError(
                "The service assigned to this slot is inactive."
            )

        appointment_id = appointment_queries.create_appointment(
            connection,
            patient_id=command.patient_id,
            slot_id=command.slot_id,
            price_amount=slot.price,
            currency=slot.currency,
        )
        if appointment_id is None:
            raise SlotUnavailableError(
                "Appointment slot is already booked."
            )

        appointment = appointment_queries.get_appointment_by_id(
            connection,
            appointment_id=appointment_id,
        )
        if appointment is None:
            raise RuntimeError(
                "Created appointment could not be loaded."
            )

        response = AppointmentResponse.model_validate(appointment)

        _complete_idempotency_request(
            connection,
            operation=CREATE_APPOINTMENT_OPERATION,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            resource_id=appointment_id,
            response_status=201,
            response=response,
        )

    # The transaction committed successfully above: only now is it
    # correct to drop the availability entries that may show the slot.
    cache.invalidate_for_appointment(
        service_id=response.service_id,
        doctor_id=response.doctor_id,
        starts_at=response.starts_at,
    )
    return response


def cancel_appointment(
    connection: Connection,
    *,
    appointment_id: UUID,
    command: CancelAppointmentRequest,
    idempotency_key: str,
    caller_patient_id: UUID,
    cache: AvailabilityCache,
) -> AppointmentResponse:
    request_hash = _request_hash(
        operation=CANCEL_APPOINTMENT_OPERATION,
        payload={
            "appointment_id": str(appointment_id),
            "cancellation_reason": command.cancellation_reason,
            "caller_patient_id": str(caller_patient_id),
        },
    )

    with connection.transaction():
        appointment_owner = appointment_queries.get_appointment_by_id(
            connection,
            appointment_id=appointment_id,
        )
        if appointment_owner is None:
            raise AppointmentNotFoundError("Appointment not found.")
        if appointment_owner.patient_id != caller_patient_id:
            raise PatientAccessDeniedError("Patient access denied.")

        replayed_response = _load_replayed_response(
            connection,
            operation=CANCEL_APPOINTMENT_OPERATION,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if replayed_response is not None:
            return replayed_response

        appointment_for_cancellation = (
            appointment_queries.get_appointment_for_cancellation(
                connection,
                appointment_id=appointment_id,
            )
        )
        if appointment_for_cancellation is None:
            raise AppointmentNotFoundError("Appointment not found.")
        if appointment_for_cancellation.status != "scheduled":
            raise AppointmentNotCancellableError(
                "Only scheduled appointments can be cancelled."
            )

        appointment_queries.cancel_appointment(
            connection,
            appointment_id=appointment_id,
            cancellation_reason=command.cancellation_reason,
        )

        appointment = appointment_queries.get_appointment_by_id(
            connection,
            appointment_id=appointment_id,
        )
        if appointment is None:
            raise RuntimeError(
                "Cancelled appointment could not be loaded."
            )

        response = AppointmentResponse.model_validate(appointment)

        _complete_idempotency_request(
            connection,
            operation=CANCEL_APPOINTMENT_OPERATION,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            resource_id=appointment_id,
            response_status=200,
            response=response,
        )

    # Cancellation releases the slot for the availability query; drop
    # the affected cache entries only after the commit succeeded.
    cache.invalidate_for_appointment(
        service_id=response.service_id,
        doctor_id=response.doctor_id,
        starts_at=response.starts_at,
    )
    return response
