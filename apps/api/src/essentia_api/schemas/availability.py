from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

class AvailableSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(validation_alias=AliasChoices("id_", "id"))
    doctor_id: UUID
    doctor_name: str
    service_id: UUID
    service_code: str
    service_name: str
    price: Decimal
    currency: str
    starts_at: datetime
    ends_at: datetime