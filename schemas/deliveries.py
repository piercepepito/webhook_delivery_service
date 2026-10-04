from pydantic import BaseModel, ConfigDict
from datetime import datetime

from typing import Literal

from uuid import UUID


class DeliveryCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    subscription_id: UUID

class DeliveryGet(BaseModel):
    id: UUID
    event_id: UUID
    subscription_id: UUID
    status: Literal['pending', 'in_flight', 'succeeded', 'exhausted']
    attempt_count: int
    next_attempt_at: datetime | None
    created_at:datetime