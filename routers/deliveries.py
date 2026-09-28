from db import LocalSession

from models import Deliveries

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

def post_new_delivery(delivery_payload):
    new_delivery = Deliveries(**delivery_payload)

    with LocalSession() as session:
        session.add(new_delivery)
        session.commit()
        session.refresh(new_delivery)

    return new_delivery

    
def patch_existing_delivery_id(delivery_id, new_status, new_attempt_count, next_attempt_at):
    with LocalSession() as session:
        try:
            stmt = select(Deliveries).where(
                Deliveries.id == delivery_id
            )

            attempt = session.execute(stmt).scalar_one()
            
            attempt.status = new_status
            attempt.attempt_count = new_attempt_count
            attempt.next_attempt_at = next_attempt_at

            session.commit()

            session.refresh(attempt)
        except IntegrityError:
            session.rollback()
            raise
        
    return attempt