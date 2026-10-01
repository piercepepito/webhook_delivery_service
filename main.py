from routers import subscriptions

from fastapi import FastAPI, HTTPException, status

import schemas
from uuid import UUID

app = FastAPI()

@app.post("/v1/subscriptions", 
          status_code=status.HTTP_201_CREATED,
          response_model=schemas.subscriptions.SubscriptionCreated)
def create_subscription_event(
    payload_subscription: schemas.subscriptions.SubscriptionCreate):

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



