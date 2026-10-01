from pydantic import BaseModel, ConfigDict

from uuid import UUID

class DeliveryCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    subscription_id: UUID