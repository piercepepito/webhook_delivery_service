from celery import Celery, shared_task

from routers import subscriptions, events, deliveries, delivery_attempts

import schemas

from worker import webhook, celery_app, exceptions

from requests import RequestException
from database import delivery_and_attempts

@celery_app.celery_app.task
def fan_out(event_payload: schemas.events.post_event_payload) -> dict:
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
    for subscription in subscription_data:
        #we need event id and subscription id
        delivery_payload={
            "event_id":event.id,
            "subscription_id":subscription.id
        }
        delivery_response = deliveries.post_new_delivery(delivery_payload)
        #add deliver function
        deliver_data_response = delivery(subscription.url, event_payload, delivery_response)
    return deliver_data_response

@celery_app.celery_app.task(bind = True, max_retries = 5)
def delivery(self, destination_url: str, webhook_payload: dict, delivery_id, secret) -> dict:
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
        base_delay_seconds = 5
        wait = base_delay_seconds * 2 ** self.request.retries

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