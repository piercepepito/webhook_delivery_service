from db import LocalSession

from models import DeliveryAttempts

from sqlalchemy.exc import IntegrityError

def create_new_delivery_attempt(delivery_attempt_payload: DeliveryAttempts) -> DeliveryAttempts:
    new_delivery_attempt = DeliveryAttempts(**delivery_attempt_payload)

    with LocalSession() as session:
        try:
            session.add(new_delivery_attempt)
            session.commit()

            session.refresh(new_delivery_attempt)
        except IntegrityError:
            session.rollback()
            raise
        
    return new_delivery_attempt

