from pydantic import BaseModel

from uuid import UUID

class DeliveryAttemptCreate(BaseModel):
    delivery_id: UUID
    duration_ms: float
    attempt_no: int