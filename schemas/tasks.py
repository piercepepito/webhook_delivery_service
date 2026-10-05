from pydantic import BaseModel

from uuid import UUID

from typing import Literal

class FanOutSent(BaseModel):
    delivery_id: UUID
    subscription_id: UUID
    event_id: UUID 
    status: str

class RetryDelivery(BaseModel):
    delivery_id: UUID
    status: Literal['pending', 'in_flight', 'succeeded', 'exhausted']