from sqlalchemy import select

from uuid import UUID

from db import LocalSession
from models import Deliveries, Events, Subscriptions
from sqlalchemy.exc import NoResultFound, MultipleResultsFound

def pull_for_retry_func(delivery_id: UUID):
    with LocalSession() as session:
        stmt = (
            select(Deliveries, Events, Subscriptions)
            .join(Events, Deliveries.event_id == Events.id)
            .join(Subscriptions, Deliveries.subscription_id == Subscriptions.id)
            .where(Deliveries.id == delivery_id)
        ) 

        result = session.execute(stmt)
        return result.one()