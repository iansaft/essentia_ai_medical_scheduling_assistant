from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

AppointmentStatus = Literal[
    "scheduled",
    "cancelled",
    "completed",
    "no_show",
]


class CreateAppointmentRequest(BaseModel):
    patient_id: UUID = Field(
        examples=["3cdf666b-186d-44e6-bce9-5e572e7038f9"],
        json_schema_extra={
            "example": "3cdf666b-186d-44e6-bce9-5e572e7038f9",
        },
    )
    slot_id: UUID = Field(
        examples=["8e06b231-a27f-4bf3-bc69-7565f20c3f7d"],
        json_schema_extra={
            "example": "8e06b231-a27f-4bf3-bc69-7565f20c3f7d",
        },
    )


class CancelAppointmentRequest(BaseModel):
    cancellation_reason: str = Field(
        min_length=3,
        max_length=500,
        examples=["Patient requested cancellation."],
        json_schema_extra={
            "example": "Patient requested cancellation.",
        },
    )


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(validation_alias=AliasChoices("id_", "id"))
    patient_id: UUID
    patient_name: str
    slot_id: UUID
    doctor_id: UUID
    doctor_name: str
    service_id: UUID
    service_name: str
    starts_at: datetime
    ends_at: datetime
    status: AppointmentStatus
    price_amount: Decimal
    currency: str
    cancellation_reason: str | None
    cancelled_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
