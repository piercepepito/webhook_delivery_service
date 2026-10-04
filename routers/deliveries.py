from db import LocalSession

from models import Deliveries

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound

from routers import exceptions
import schemas.deliveries
from typing import Literal
from uuid import UUID

def post_new_delivery(delivery_payload: schemas.deliveries.DeliveryCreate) -> Deliveries:
    """
    Creates a new delivery row

    Args:
    delivery_payload: a dictionary containing all the valid data used for the Deliveries table

    Returns:
    - the newly created delivery row
    """
    new_delivery = Deliveries(**delivery_payload)

    with LocalSession() as session:
        try:
            session.add(new_delivery)
            session.commit()
            session.refresh(new_delivery)

            return new_delivery
        except IntegrityError as e:
            session.rollback()
            raise

def get_delivery(delivery_id:UUID) -> Deliveries:
    """
    Querues the deliveries tabl, gets all the columns

    Returns:
    - the returned singular row with the Deliveries object being used
    """
    with LocalSession() as session:
        stmt = select(Deliveries).where(
            Deliveries.id==delivery_id
        )
        try:
            result = session.execute(stmt)
            delivery_data = result.scalar_one()
            return delivery_data

        except NoResultFound:
            raise exceptions.DeliveryNotFoundError("Invalid Delivery ID")
        
        except IntegrityError as e:
            session.rollback()
            raise
    
def patch_existing_delivery_id(delivery_id: str, 
                               new_status: Literal['pending', 'in_flight', 'succeeded', 'exhausted'], 
                               new_attempt_count: int,
                               next_attempt_at) -> Deliveries:
    """
    Updates a delivery row and changes the status, attempt_no, and next_attempt_at

    Args:
    delivery_id: the delivery id 
    new_status: Chooses between 1 of 4 choices: 'pending', 'in_flight', 'succeeded', 'exhausted'
    new_attempt_count: the number attempts been made
    next_attempt_at: datetime of when the next retry will occur

    Returns
    - a Deliveries object containing all the cells of the delivery table

    Raise
    - returns an integrity error when any of the Args have a validation error
    """
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