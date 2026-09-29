from routers import deliveries, delivery_attempts

from datetime import datetime, timedelta, timezone

from typing import Literal
from models import Deliveries, DeliveryAttempts

def message_sent_attempt(delivery_attempt_payload: DeliveryAttempts, 
                         deliver_status: Literal['pending', 'in_flight', 'succeeded', 'exhausted'], 
                         seconds:int = 0) -> dict:
    """
    Creates a new delivery attempt row and updates the delivery row depending on the delivery id

    Args:
    delivery_attempt_payload: delivery attempt object used as input to create a new row for delivery attempt table
    deliver_status:
    seconds: the number of seconds for the next queue. only used when an error occurs

    Returns:
    - the newly updated delivery object based on the delivery id
    """
    delivery_attempt_response = delivery_attempts.create_new_delivery_attempt(delivery_attempt_payload)

    future_attempt = datetime.now(timezone.utc) + timedelta(seconds=seconds)

    delivery_patch = deliveries.patch_existing_delivery_id(delivery_attempt_response.delivery_id, 
                                          deliver_status, 
                                          delivery_attempt_payload["attempt_no"],
                                          next_attempt_at = future_attempt)

    
    return {
        "delivery_id":str(delivery_patch.id),
        "status":str(delivery_patch.status)
    }