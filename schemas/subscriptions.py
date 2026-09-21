from pydantic import BaseModel, Field, HttpUrl, field_validator

from datetime import datetime
from uuid import UUID

from event_catalog import EVENT_TYPES

from dotenv import load_dotenv
import os
load_dotenv()
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

class SubscriptionCreate(BaseModel):
    """Request body to create a subscription"""
    url: HttpUrl = Field(description="Must be HTTPS")
    event_types: list[str] = Field(description="e.g. ['stock.below_reorder_point', 'lot.expiring_soon']")

    @field_validator("url")
    @classmethod
    def check_url(cls, v: HttpUrl) -> HttpUrl:
        if (v.scheme == "https"):
            return v
        elif (ENVIRONMENT=="development") and (v.host in {"localhost", "127.0.0.1"}):
            return v
        else:
            raise ValueError("HTTPS scheme is required")

    @field_validator("event_types")
    @classmethod
    def validate_event_type(cls, v: list[str]) -> list[str]:
        unkown = set(v) - EVENT_TYPES
        if unkown:
            raise ValueError(f"The following events does not exist: {unkown}")
        return v

class SubscriptionRead(SubscriptionCreate):
    """Retrieves the entire row matching the id. Secret will not be given."""
    id: UUID
    active: bool
    created_at: datetime

class SubscriptionCreated(BaseModel):
    """
    A newly created subscription. The secret key will ONLY be given once during this phase.
    """
    secret: str = Field(description="Will only be given once")