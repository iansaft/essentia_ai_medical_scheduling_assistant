from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(validation_alias=AliasChoices("id_", "id"))
    full_name: str
    email: str
    phone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime