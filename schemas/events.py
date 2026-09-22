from pydantic import BaseModel, Field, field_validator, AwareDatetime

import event_catalog

class post_event_payload(BaseModel):
    type: str = Field(description="an actual event that is part of the event catalog")
    payload: dict = Field(description="the data that should be sent to the subscription")
    occurred_at: AwareDatetime = Field(description="when the event happened")

    @field_validator("type")
    @classmethod
    def type_validation(cls, v:str) -> str:
        if v in event_catalog.EVENT_TYPES:
            return v
        else:
            raise ValueError(f"{v} not part of event catalog")



