from pydantic import BaseModel

from uuid import UUID

class FanOutSent(BaseModel):
    delivery_id: UUID
    subscription_id: UUID
    event_id: UUID 
    status: str
    