from celery import Celery

from routers import subscriptions, events, deliveries, delivery_attempts

import schemas
from uuid import UUID

from worker import webhook, celery_app, exceptions

from requests import RequestException
from database import delivery_and_attempts, data_retrieval

@celery_app.celery_app.task
def fan_out(event_payload: schemas.events.post_event_payload) -> list[dict]:
    """
    From the given payload, creates a new event, finds the desintation urls from the subscriptions table, and individually sends the message
    based on the returned number of rows from subscriptions
    Args:
    event_payload: a dictionary with the message to be sent along with the event type
    
    Returns:
    - a dictionary of the event id, subscription id, and status
    """
    #create new event
    print("Creating New Event")
    event = events.post_event_data(event_payload)
    #check for returned rows in subscription based on event
    print('Finding destination urls')
    subscription_data = subscriptions.get_subscription_url(event.type)

    delivery_output=[]
    for subscription in subscription_data:
        #we need event id and subscription id
        delivery_payload={
            "event_id":event.id,
            "subscription_id":subscription.id
        }
        delivery_response = deliveries.post_new_delivery(delivery_payload)
        #add deliver function
        deliver_task = delivery.delay(subscription.url, event_payload, str(delivery_response.id), str(subscription.secret))
        #update the output
        delivery_payload["status"] = "pending"
        delivery_payload["delivery_id"] = delivery_response.id
        delivery_payload["task_id"] = deliver_task.id

        delivery_output.append(delivery_payload)
    return delivery_output

@celery_app.celery_app.task(bind = True, max_retries = 5)
def delivery(self, destination_url: str, webhook_payload: dict, delivery_id, secret) -> dict:
    """
    Send the payload data to the reciever. Whenever the 1st attepmt fails, there will be retries (a maximum of 5).
    Once the attempt goes beyond the maximum allowable retries, then it will return an exhausted status under the deliveries row.
    
    Args:
    destination_url: the URL used to send the data payload
    webhook_payload: the data being sent to the reciever
    delivery_id:
    secret: secret key

    Returns:
        - available initial status of the payload

    Raises:
        WebDeliveryError: raises when a webhook failed to post
    
    """
    try:
        delivery_attempt_payload = {
            "delivery_id": str(delivery_id),
            "attempt_no": self.request.retries + 1
        }

        webhook_response, duration_ms = webhook.deliver_webhook(destination_url, webhook_payload, secret)

        delivery_attempt_payload["duration_ms"] = duration_ms
        
        if 200 <= webhook_response.status_code < 300:
            deliver_status = "succeeded"
            seconds = 0

        return delivery_and_attempts.message_sent_attempt(delivery_attempt_payload, deliver_status, seconds)

    except exceptions.WebDeliveryError as error:
        base_delay_seconds = 2
        wait = base_delay_seconds * 2 ** self.request.retries
        print(f"retrying in: {wait} seconds")

        response = error.original_error.response
        error_response = {
                "status_code": response.status_code if response else None,
                "error":str(error.original_error),
                "duration_ms":error.duration_ms
            }
        input_payload = delivery_attempt_payload | error_response

        if self.request.retries < self.max_retries:
            deliver_status = "in_flight"
            seconds = wait
            
            delivery_and_attempts.message_sent_attempt(input_payload, deliver_status, seconds) 

            raise self.retry(exc=error, countdown = wait)
        else:
            deliver_status = "exhausted"
            seconds = wait

            return  delivery_and_attempts.message_sent_attempt(input_payload, deliver_status, seconds) 

def retry_delivery(delivery_id: UUID) -> dict:
    """
    Retries sending a failed delivery
    """
    delivery_return, event_return, subscription_return = data_retrieval.pull_for_retry_func(delivery_id)

    if delivery_return.status == "succeeded":
        raise exceptions.InvalidDeliveryIdError(f"Delivery ID: {delivery_return.id}, has already been sent succesfully")

    webhook_response, duration_ms = webhook.deliver_webhook(subscription_return.url, 
                                                            event_return.payload, 
                                                            subscription_return.secret)
    
    delivery_attempt_payload = {
        "delivery_id":delivery_return.id,
        "attempt_no":delivery_return.attempt_count + 1,
        "duration_ms": duration_ms

    }
    
    if 200 <= webhook_response.status_code < 300:
        deliver_status = "succeeded"
        seconds = 0
    else:
        deliver_status = "exhausted"
        seconds = 0

    return delivery_and_attempts.message_sent_attempt(delivery_attempt_payload, deliver_status, seconds)
