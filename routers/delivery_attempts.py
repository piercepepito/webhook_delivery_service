from db import LocalSession

from models import DeliveryAttempts

from sqlalchemy.exc import IntegrityError
import schemas.delivery_attempts

def create_new_delivery_attempt(delivery_attempt_payload: schemas.delivery_attempts.DeliveryAttemptCreate) -> DeliveryAttempts:
    """
    Creates a new row under the delivery_attempts table

    args:
    delivery_attempt_payload: Ensures that the data always has the columns under the DeliveryAttempt Object

    returns:
    - The newly created delivery_attempt row using the DeliveryAttempts 
    """
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

