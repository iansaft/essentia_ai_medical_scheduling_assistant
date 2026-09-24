from datetime import datetime
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class CreatePatientRequest(BaseModel):
    full_name: str = Field(
        min_length=1,
        max_length=200,
        examples=["Joana Souza"],
        json_schema_extra={
            "example": "Joana Souza",
        },
    )
    email: str = Field(
        min_length=3,
        max_length=320,
        examples=["joana.souza@example.com"],
        json_schema_extra={
            "example": "joana.souza@example.com",
        },
    )
    phone: str | None = Field(
        default=None,
        min_length=1,
        max_length=32,
        examples=["+5548999990009"],
        json_schema_extra={
            "example": "+5548999990009",
        },
    )

    @field_validator("full_name", "email", "phone", mode="after")
    @classmethod
    def strip_blank_values(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")

        return stripped


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(validation_alias=AliasChoices("id_", "id"))
    full_name: str
    email: str
    phone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime