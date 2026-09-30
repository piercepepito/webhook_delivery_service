from db import LocalSession

from models import Events
from schemas import events

import event_catalog

def post_event_data(event_payload: events.post_event_payload) -> Events:
    """Add a new row to events table
    Args:
        event_payload
    Returns:
        payload inside the event_payload
    """
    new_event = Events(**event_payload)

    with LocalSession() as session:
        session.add(new_event)
        session.commit()

        session.refresh(new_event)

    return new_event
