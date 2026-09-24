from decimal import Decimal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(validation_alias="id_")
    code: str
    name: str
    description: str | None
    price: Decimal
    currency: str
    duration_minutes: int


class PaymentMethodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(validation_alias=AliasChoices("id_", "id"))
    code: str
    name: str
    description: str | None
    max_installments: int
    notes: str | None