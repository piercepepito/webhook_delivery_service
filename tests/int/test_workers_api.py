import pytest

from worker import tasks
from routers import subscriptions, events, deliveries

import schemas

from main import app
from fastapi.testclient import TestClient
client = TestClient(app=app)

@pytest.mark.integration
def test_valid_input_data(clean_database, valid_subscription_payload):
    """
    Tests v1/events api using valid input data. Expected to have a 201 status code response
    """
    subscription_payload = schemas.subscriptions.SubscriptionCreate(**valid_subscription_payload[1])
    new_subscription = subscriptions.create_subscription(subscription_payload) 

    event_input = {
        "type": "asset.decommissioned",
        "occurred_at": "2026-09-18T06:00:00+08:00",
        "payload": {
            "lot_number": "CD-2026-0914",
            "sku": "BUTTER-UNSALTED-5KG",
            "expiry_date": "2026-09-25",
            "days_remaining": 7,
            "quantity": 24,
            "location": "COLD-02"
        }
    }

    response =client.post(
        "/v1/events",
        json=event_input
    )

    assert response.status_code == 201

@pytest.mark.integration
def test_invalid_input_data(clean_database, valid_subscription_payload):
    """
    Tests v1/events api using valid input data. Expected to have a 201 status code response
    """
    subscription_payload = schemas.subscriptions.SubscriptionCreate(**valid_subscription_payload[1])
    new_subscription = subscriptions.create_subscription(subscription_payload) 

    event_input = {
        "type": "asset.decommissioned",
        "payload": {
            "lot_number": "CD-2026-0914",
            "sku": "BUTTER-UNSALTED-5KG",
            "expiry_date": "2026-09-25",
            "days_remaining": 7,
            "quantity": 24,
            "location": "COLD-02"
        }
    }

    response = client.post(
        "/v1/events",
        json=event_input
    )

    assert response.status_code == 422

@pytest.mark.integration
def test_retry_valid_input(valid_create_subscription_payload, valid_event_type):
    """
    Testing the retry function
    """
    new_subscription = subscriptions.create_subscription(valid_create_subscription_payload)
    new_event = events.post_event_data(valid_event_type[0])

    delivery_payload = {
        "event_id": new_event.id,
        "subscription_id": new_subscription.id
        }

    new_delivery = deliveries.post_new_delivery(delivery_payload)

    url=f"/v1/deliveries/retry/{new_delivery.id}"
    response = client.post(url=url)

    assert response.status_code == 200

@pytest.mark.integration
def test_retry_succesful_delivery(valid_create_subscription_payload, valid_event_type):
    """
    Tests the retry function when a succesful delivery id has already been done. It should return a 406 error
    """
    new_subscription = subscriptions.create_subscription(valid_create_subscription_payload)
    new_event = events.post_event_data(valid_event_type[0])

    delivery_payload = {
        "event_id": new_event.id,
        "subscription_id": new_subscription.id,
        "status":"succeeded"
        }

    new_delivery = deliveries.post_new_delivery(delivery_payload)

    url=f"/v1/deliveries/retry/{new_delivery.id}"
    response = client.post(url=url)

    assert response.status_code == 406