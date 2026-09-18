import secrets

from models import Subscriptions
from db import LocalSession

def create_subscription(payload: dict) -> dict:
    """
    Creates a subscription

    Args:
        payload: it should contain the url, and the event types associated
    Returns:
        a dictionary containing the response and the secret key
    """
    plain_secret = secrets.token_urlsafe(32)

    new_sub=Subscriptions(
        url=payload["url"],
        event_types=payload["event_types"],
        secret=plain_secret 
    )

    with LocalSession() as session:
        session.add(new_sub)
        session.commit()

        session.refresh(new_sub)

    body_response = {
        "id":str(new_sub.id),
        "url":new_sub.url,
        "event_types":new_sub.event_types,
        "secret":new_sub.secret,
        "active":bool(new_sub.active),
        "created_at":new_sub.created_at.isoformat()
    }

    return body_response 