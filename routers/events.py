from db import LocalSession

from sqlalchemy.exc import IntegrityError

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
        try:
            session.add(new_event)
            session.commit()

            session.refresh(new_event)
        except IntegrityError as e:
            session.rollback()
            raise 

    return new_event
