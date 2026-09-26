from celery import Celery

from routers import subscriptions, events, deliveries, delivery_attempts

import schemas

from worker import webhook

def fan_out(event_payload: schemas.events.post_event_payload):
    """
    
    """
    #create new event
    print("Creating New Event")
    event = events.post_event_data(event_payload)
    #check for returned rows in subscription based on event
    print('Finding destination urls')
    subscription_data = subscriptions.get_subscription_url(event.type)
    for subscription in subscription_data[:2]:
        #we need event id and subscription id
        delivery_payload={
            "event_id":event.id,
            "subscription_id":subscription.id
        }
        delivery_response = deliveries.post_new_delivery(delivery_payload)
        #add deliver function
    return #event id, subscription id, destination url, status


def delivery(destination_url, webhook_payload, delivery_response):
    #http request to url destination
    webhook_response, duration_ms = webhook.deliver_webhook(destination_url, webhook_payload)

    #create new delivery attempt row
    delivery_attempt_payload = {
        "delivery_id":delivery_response.id,
        "duration_ms":duration_ms,
        "attempt_no":1 #assuming no retries
    }

    delivery_attempt_response = delivery_attempts.create_new_delivery_attempt(delivery_attempt_payload)
    #update delivery table
    updated_delivery = deliveries.patch_existing_delivery_id(delivery_response.id, "succeeded", new_attempt_count=1)
    #if succesful, then update delivery and delivery_attempts table
    #if not, wait for exponential backoff and jitter, and update...

    response = {
        "delivery_id":delivery_response.id,
        "event_id":delivery_response.event_id,
        "status":"succeeded"
    }

    return response

#create hmac from secret and payload
#create signature