from routers import subscriptions, exceptions, deliveries

import worker
from worker import tasks

from fastapi import FastAPI, HTTPException, status

import schemas
from schemas import tasks as task_schema
from uuid import UUID

app = FastAPI()

@app.post("/v1/subscriptions", 
          status_code=status.HTTP_201_CREATED,
          response_model=schemas.subscriptions.SubscriptionCreated)
def create_subscription_event(
    payload_subscription: schemas.subscriptions.SubscriptionCreate):
    """Create subscription"""

    return subscriptions.create_subscription(payload_subscription)


@app.get("/v1/subscriptions/{subscription_id}",
         status_code=status.HTTP_200_OK,
         response_model=schemas.subscriptions.SubscriptionRead)
def get_subscription_from_id(subscription_id: UUID):
    """Retrieve subscription from ID"""
    try:
        return subscriptions.get_subscription(subscription_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        ) from e

@app.post("/v1/events",
          status_code= status.HTTP_201_CREATED,
          response_model=list[task_schema.FanOutSent])
def send_payload(
     event_payload: schemas.events.post_event_payload):
    """
    Sends data to the destination url of the subscriber depending on the event type
    """
        
    return tasks.fan_out(event_payload.model_dump(mode="json"))

@app.patch(
    "/v1/subscriptions/{subscription_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.subscriptions.SubscriptionRead)
def update_subscription(
    subscription_id: UUID,
    subscription_data: schemas.subscriptions.SubscriptionUpdate
    ):
    """
    Updates a given subscription row given the subscription id
    """
    try:
        return subscriptions.update_subscription(subscription_id, subscription_data)
    except exceptions.SubscriptionNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

@app.get("/v1/deliveries/{delivery_id}",
         status_code=status.HTTP_200_OK,
         response_model=schemas.deliveries.DeliveryGet)
def get_delivery_status(
    delivery_id: UUID):
    """
    Get the delivery row from delivery id
    """
    try:
        return deliveries.get_delivery(delivery_id)
    
    except exceptions.DeliveryNotFoundError as e:
        raise HTTPException(
            status_code= 404,
            detail=str(e)
        )

@app.post("/v1/deliveries/retry/{delivery_id}",
        status_code=status.HTTP_200_OK,
        response_model=schemas.tasks.RetryDelivery)
def retry_failed_delivery(delivery_id: UUID):
    try:
        return tasks.retry_delivery(delivery_id)
    except worker.exceptions.InvalidDeliveryIdError as e:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail =str(e)
        ) from e